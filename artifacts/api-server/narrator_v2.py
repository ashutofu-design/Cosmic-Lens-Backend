"""
narrator_v2.py — "AI Mouth" conversational diagnostic narrator (P3)
====================================================================

Takes a single card's:
  • intent_summary  (1-line paraphrase of what the user is asking)
  • intent_bucket   (e.g. partnership_exit, debt_recovery)
  • intent_facts    (verbatim numbers/durations/persons/places/dates from user)
  • raw_engine_text (the existing engine narrator's verbose output)
  • language        ("hn" | "hi" | "en")
  • emotional_tone  ("anxious" | "hopeful" | …)

…and rewrites it into a **conversational diagnostic micro-card** with this
fixed shape:

    {
      "verdict_tag":  "🟠 SLOW BURN"  |  "🟢 GREEN GO"  |  "🟡 WAIT" |
                      "🔴 RED FLAG"   |  "⚪️ NEUTRAL"   |  "🔮 DIAGNOSE",
      "narrative":    50-80 words of single-paragraph conversational prose
                      following the 5 voice rules below.
      "remedy_line":  optional 1-line remedy (≤12 words). May be empty string.
      "advisor_line": optional 1-line professional advisor cite (≤14 words).
                      MANDATORY for wealth/health/legal buckets.
      "_internal": {  // validator-only, stripped before client receives
        "echoed_facts":   [...],
        "echoed_pivots":  [...],
        "voice_opener":   "...",
        "covered_root_cause":     bool,
        "covered_manifestation":  bool,
        "covered_forward_promise":bool,
        "covered_action":         bool,
      }
    }

THE 5 VOICE RULES (hardcoded in the system prompt; validator enforces #1, #2,
#3 explicitly via regex; #4 and #5 are heuristic checks):

  1. Opener filler — must start with one of: "Dekho", "Dekho na", "Suno",
     "Haan", "Bilkul" (case-insensitive). Formal namaste / sir / madam → reject.
  2. Soft hedging — must contain at least one of: "thoda", "halki si",
     "zyada nahi", "dheere", "kuch hi". Absolute statements without hedge → reject.
  3. Suggestion-not-command — must use "ruk jao" / "kar sakte ho" /
     "mat karo" / "le lo" form. Imperative drill-sergeant tone → reject.
  4. House → real-life metaphor — narrative MUST NOT contain raw chart
     jargon: "combust", "L lord", "7L", "10L", "dasha", "antardasha",
     "aspect", "conjunction", "retrograde", "retro", "exalted", "debilitated",
     "rashi", "nakshatra", "navamsa", "D9", "varga". Real-life metaphors only:
     "partnership wala ghar", "paisa wala area", etc.
  5. Forward warmth — narrative must close with a hopeful / forward-looking
     phrase: "dheere clear hogi", "window khulta hai", "raasta banega",
     "behtar hota jaayega", "Ke baad easier", etc.

Brand-safety rules (per-bucket, also baked into the prompt):
  • wealth/* + stock/* → MUST mention CA / SEBI advisor in advisor_line
  • health/*           → MUST mention doctor / specialist in advisor_line;
                         NEVER predict death; mental_health/addiction → mention
                         qualified counselor or helpline.
  • litigation         → MUST mention lawyer in advisor_line.
  • marriage/love      → NEVER predict spouse death, NEVER endorse divorce
                         without "consult a relationship counselor" cite.

NO FALLBACKS — on validator failure, retries up to 2× then raises
NarratorV2Error. Caller (ai_ask_v2) wraps each card so siblings still render.
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Optional


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
VERDICT_TAGS = (
    "🟢 GREEN GO",
    "🟡 WAIT",
    "🟠 SLOW BURN",
    "🔴 RED FLAG",
    "⚪️ NEUTRAL",
    "🔮 DIAGNOSE",
)

# Buckets that REQUIRE a professional-advisor cite in advisor_line.
_REQUIRE_ADVISOR_BUCKETS = {
    # wealth
    "salary_growth", "business_profit", "loan_emi", "property",
    "inheritance", "savings_corpus", "debt_recovery", "foreign_income",
    "partnership_finance", "sudden_windfall", "tax_compliance",
    "expense_leakage", "partnership_exit", "business_continuation",
    "general_wealth",
    # stock
    "real_time", "intraday", "loss_recovery", "career_path",
    "instrument_risk", "sector", "strategy", "outcome", "suitability",
    # health
    "chronic_illness", "acute_illness", "surgery_recovery", "mental_health",
    "addiction", "parent_health", "reproductive", "skin_beauty", "longevity",
    "general_wellness",
}

# Domains that REQUIRE a professional-advisor cite regardless of bucket
# (covers cases where AI Ear emits domain="litigation"/"health"/"wealth"
# but bucket="general"). The narrator caller passes intent_domain in.
_REQUIRE_ADVISOR_DOMAINS = {"wealth", "stock", "health", "litigation"}

_BANNED_JARGON_RX = re.compile(
    r"\b(combust|combustion|combusted|"
    r"\d+l\b|\d+l\s*(lord|hai|mein)|"
    r"l\s*lord|lord\s+of\s+\d|"
    r"dasha|antardasha|antar dasha|pratyantar|mahadasha|"
    r"aspect(s|ed)?|conjunct(ion|s)?|retrograde|retro\b|"
    r"exalt(ed|ation)?|debilitat(ed|ion)?|"
    r"rashi|nakshatra|nakshatr|navamsa|navamsha|"
    r"d-?9|d-?10|d-?7|varga|vargas|"
    r"saturn|jupiter|mars|venus|mercury|rahu|ketu|sun|moon|"
    r"shani|guru|mangal|shukra|budh|surya|chandra)\b",
    re.IGNORECASE,
)

# Voice rule regexes (validator).
_OPENER_RX = re.compile(
    r"^\s*(dekho(\s+na)?|suno|haan(\s|,)|bilkul|chalo|achha)\b",
    re.IGNORECASE,
)
_HEDGE_RX = re.compile(
    r"\b(thoda|thodi|halki(\s+si)?|zyada\s+nahi|dheere|kuch\s+hi|"
    r"halka|ek\s+baar|jaldbaazi\s+mat|jaldi\s+mat)\b",
    re.IGNORECASE,
)
_FORWARD_RX = re.compile(
    r"\b(clear\s+hog|window\s+khul|raasta\s+ban|behtar\s+hota|"
    r"ke\s+baad\s+easier|aage\s+chal|saath\s+aayeg|theek\s+ho\s+jaayeg|"
    r"dheere(\s+dheere)?\s+(clear|theek|aayeg|ban)|asar\s+kam|"
    r"smooth\s+hog|relief\s+aayeg|positive\s+ban|growth\s+aayeg|"
    r"khul(eg|jaayeg)|sambhal\s+jaayeg|stable\s+ho)",
    re.IGNORECASE,
)
# Voice rule #3 — suggestion (not command). Must contain at least one
# softened-action phrase. Pure imperatives ("karo!", "mat karo!") without
# a softener trip the rejection.
_SUGGESTION_RX = re.compile(
    r"\b(ruk\s+jao|kar\s+sakte\s+ho|kar\s+sakti\s+ho|le\s+lo|"
    r"consult\s+kar(o|\s+lo|\s+lijiye)?|soch\s+lo|soch(\s+kar)?\s+lijiye|"
    r"dekh\s+lo|dekh\s+lijiye|dhyan\s+(do|rakho|de\s+dena|rakhna)|"
    r"behtar\s+hoga|behtar\s+rahega|sambhal\s+lo|wait\s+kar(o|\s+lo)|"
    r"plan\s+kar(o|\s+lo|na)|samay\s+(do|de\s+do|le\s+lo)|"
    r"aaram\s+se\s+(le|karo)|jaldi\s+mat|jaldbaazi\s+mat|"
    r"halki(\s+si)?\s+(rukawat|der)|ek\s+baar\s+(soch|consult)|"
    r"talna\s+behtar|postpone\s+kar|hold\s+karo|step\s+by\s+step)",
    re.IGNORECASE,
)
_AI_BRAND_LEAK_RX = re.compile(
    r"\b(AI|GPT|OpenAI|ChatGPT|language\s+model|llm|gemini|claude|anthropic)\b",
    re.IGNORECASE,
)

# Banned absolute / financial-prediction phrases (brand-safety).
_BANNED_BRAND_RX = re.compile(
    r"\b(\d+\s*(lakh|crore|cr|rupees|rs\.?)\s+(milega|aayega|kamayega|hoga))|"
    r"\b(guarantee|guaranteed|100%\s*sure|definitely\s+will|"
    r"never\s+lose|always\s+win|bankruptcy|"
    r"divorce|marriage\s+will\s+break|spouse\s+will\s+die|"
    r"will\s+die|death\s+is\s+near|fatal|terminal\s+illness)\b",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# DATA TYPES
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class NarratorCard:
    verdict_tag:   str
    narrative:     str
    remedy_line:   str = ""
    advisor_line:  str = ""
    _internal:     dict = field(default_factory=dict)
    latency_ms:    int = 0

    def to_client_dict(self) -> dict:
        d = asdict(self)
        d.pop("_internal", None)
        d.pop("latency_ms", None)
        return d


class NarratorV2Error(RuntimeError):
    pass


# ─────────────────────────────────────────────────────────────────────────────
# JSON SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
_NARRATOR_SCHEMA = {
    "name": "diagnostic_card",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdict_tag", "narrative", "remedy_line",
                     "advisor_line", "_internal"],
        "properties": {
            "verdict_tag": {"type": "string", "enum": list(VERDICT_TAGS)},
            "narrative": {
                "type": "string",
                "minLength": 80,
                "maxLength": 700,
                "description": "Single paragraph, 50-80 words. Conversational. No bullets.",
            },
            "remedy_line": {
                "type": "string",
                "maxLength": 120,
                "description": "≤12 words. Optional. Empty string if no remedy applies.",
            },
            "advisor_line": {
                "type": "string",
                "maxLength": 160,
                "description": "≤14 words. Mention CA/SEBI/doctor/lawyer/counselor as applicable.",
            },
            "_internal": {
                "type": "object",
                "additionalProperties": False,
                "required": ["echoed_facts", "echoed_pivots", "voice_opener",
                             "covered_root_cause", "covered_manifestation",
                             "covered_forward_promise", "covered_action"],
                "properties": {
                    "echoed_facts":  {"type": "array", "items": {"type": "string"}},
                    "echoed_pivots": {"type": "array", "items": {"type": "string"}},
                    "voice_opener":  {"type": "string"},
                    "covered_root_cause":      {"type": "boolean"},
                    "covered_manifestation":   {"type": "boolean"},
                    "covered_forward_promise": {"type": "boolean"},
                    "covered_action":          {"type": "boolean"},
                },
            },
        },
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────────────────────────────────────
_VOICE_RULES = """\
YOU ARE Acharya Vidyasagar — a senior Vedic acharya answering a chart-question
DIRECTLY, like a doctor handing over a prescription. Warm but FIRM. Specific,
not vague. NO beating around the bush. NO restating the user's question.

═══ STRUCTURE — every narrative is ONE paragraph, 50-80 words, with FOUR
beats woven together (not labelled, not bulleted — just flowing prose):

  Beat 1 — DIRECT DIAGNOSIS. State the WHY in one line. Open with the
           answer itself (e.g. "Saving rukhne ka asli reason yeh hai ki…",
           "Iska core issue hai ki…", "Pehli baat — chart bata raha hai…").
           NEVER echo the user's own question back at them.

  Beat 2 — REAL-LIFE MANIFESTATION. How this is showing up in their day-to-
           day, in metaphor (NO chart jargon). Be concrete: "kharch wali
           energy zyada haavi hai", "partnership wala ghar abhi shaky phase
           mein hai".

  Beat 3 — SPECIFIC TIMING PIVOT. Name a real month/year/period when the
           shift happens. Examples: "Mar 2026 ke baad", "agle 4-6 mahine
           mein", "Diwali 2025 ke aas-paas", "Q2 2026 se". Vague phrases
           like "dheere clear hoga" alone are NOT acceptable.

  Beat 4 — CONCRETE ACTION. ONE actionable next step with a specific
           number, frequency, or named instrument. Examples: "30% salary
           pe auto-debit SIP", "monthly 5k RD start karo", "next 90 days
           mein 3 mahine ka emergency fund build karo", "saptah mein 2
           din meditation 20-min". NOT vague "soch lo" or "dhyan rakho".

═══ ABSOLUTE RULES (validator will reject):

  R1. NO PROBLEM-RESTATEMENT in the opening. Don't start by paraphrasing
      the user's own words ("Pichle 1 saal se savings nahi…"). Start with
      the answer/diagnosis instead.

  R2. SPECIFIC TIMING token MUST appear (month name + year, "agle N
      mahine/saal", "Diwali", "Q1/Q2/Q3/Q4 20XX", or similar).

  R3. CONCRETE ACTION token MUST appear (verb paired with a number,
      percentage, instrument like SIP/RD/FD/EMI/auto-debit, or specific
      frequency like daily/weekly/monthly + duration).

  R4. NO CHART JARGON in narrative — combust, dasha, antardasha,
      pratyantar, aspect, conjunction, retrograde, exalted, debilitated,
      rashi, nakshatra, navamsa, D9, D10, varga, OR planet names
      (Saturn/Jupiter/Mars/Venus/Mercury/Rahu/Ketu/Sun/Moon and Hindi
      equivalents Shani/Guru/Mangal/Shukra/Budh/Surya/Chandra) are ALL
      FORBIDDEN in the narrative body. Translate to real-life metaphor.

  R5. NO AI/LLM brand leak — never say AI, GPT, OpenAI, language model,
      Claude, Gemini, etc. You are "Cosmic Intelligence" / "Acharya".

  R6. NO RUPEE GUARANTEES, NO DEATH PREDICTIONS, NO DIVORCE/BANKRUPTCY
      assertions. Use directional language ("paisa flow stable hoga",
      NOT "25 lakh milega").

  R7. NO ABSOLUTE CLAIMS — avoid "100% sure", "guaranteed", "definitely
      will". Use "strong indicator hai", "high probability hai", "naturally
      start hoga".

  R8. ADVISOR CITE in advisor_line:
      • wealth/stock → qualified CA / SEBI-registered advisor
      • health      → qualified doctor / specialist (mental_health /
                      addiction → counselor or helpline)
      • litigation  → qualified lawyer / advocate

═══ TONE NOTES (style guidance, not strict-rejection):

  • Optional soft openers ("Dekho", "Suno", "Saaf kehna hai", "Asli baat")
    are FINE if they precede a direct statement. SKIP them entirely if the
    diagnosis is strong enough on its own.

  • Soft hedges ("thoda", "halki si", "dheere") are allowed but use ONLY
    to qualify a SPECIFIC claim — never to dilute the whole answer.

  • Tone = warm doctor giving prescription. NOT therapist asking how user
    feels. NOT friend rambling.

  • Last sentence should leave the user with a CLEAR next step + timeline,
    not a vague "sab clear ho jayega".

LANGUAGE — write narrative + remedy_line + advisor_line in the language
specified (hn = Hinglish in Roman script, hi = Hindi-Devanagari, en = English).

LENGTH — narrative is 50-80 words, single paragraph, NO bullets, NO section
headings, NO emoji inside the narrative body (emoji only in verdict_tag).
"""


def _build_user_prompt(
    intent_summary: str,
    intent_bucket: str,
    intent_facts: dict,
    raw_engine_text: str,
    language: str,
    emotional_tone: str,
    require_advisor: bool,
) -> str:
    facts_lines = []
    for k in ("numbers", "durations", "persons", "places", "dates"):
        v = intent_facts.get(k) or []
        if v:
            facts_lines.append(f"  {k}: {v}")
    facts_block = "\n".join(facts_lines) if facts_lines else "  (none)"

    advisor_note = (
        "MANDATORY: advisor_line MUST contain a professional-advisor cite "
        f"(CA / SEBI advisor / doctor / lawyer / counselor) appropriate "
        f"for bucket={intent_bucket!r}."
        if require_advisor else
        "advisor_line is OPTIONAL for this bucket; leave empty string if "
        "not applicable."
    )

    lang_note = {
        "hn": "Write in Hinglish (Hindi in Roman script).",
        "hi": "Write in Hindi (Devanagari script).",
        "en": "Write in English.",
    }.get(language, "Write in Hinglish (Hindi in Roman script).")

    return f"""\
INTENT SUMMARY:    {intent_summary}
INTENT BUCKET:     {intent_bucket}
EMOTIONAL TONE:    {emotional_tone}
USER FACTS (must echo at least 1 verbatim in narrative if non-empty):
{facts_block}

ENGINE REASONING (your raw source — DO NOT quote jargon, ONLY use it to
shape the metaphor and timing pivots):
\"\"\"
{raw_engine_text[:1800]}
\"\"\"

{advisor_note}

{lang_note}

Produce the strict JSON object. The narrative MUST be 50-80 words, follow ALL
5 voice rules, and weave in user's verbatim facts where present."""


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATOR
# ─────────────────────────────────────────────────────────────────────────────
def _word_count(text: str) -> int:
    return len([w for w in text.strip().split() if w.strip()])


def _last_sentence(text: str) -> str:
    """Return the trailing sentence of `text` for forward-warmth check.
    Splits on . / ! / ? / Devanagari danda. Falls back to last 12 words if no
    terminal punctuation found."""
    parts = re.split(r"[.!?।]+", text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    if parts:
        return parts[-1]
    words = text.strip().split()
    return " ".join(words[-12:]) if words else ""


def _validate_card(card: dict,
                   intent_facts: dict,
                   intent_bucket: str,
                   require_advisor: bool) -> Optional[str]:
    """Return None if all checks pass, else a semicolon-separated string of
    ALL failures so the caller's retry path can show the model every issue
    in one shot (improves retry success vs surfacing one issue at a time)."""
    narrative = (card.get("narrative") or "").strip()
    advisor   = (card.get("advisor_line") or "").strip()

    failures: list[str] = []

    if not narrative:
        failures.append("narrative is empty")
        return "; ".join(failures)

    wc = _word_count(narrative)
    # Spec: 50-80 words. Allow tiny slack (45-90) so single-word puncuation
    # quirks don't reject otherwise compliant cards.
    if wc < 45 or wc > 90:
        failures.append(
            f"narrative word count {wc} out of spec range [45-90] "
            f"(target 50-80)"
        )

    if not _OPENER_RX.search(narrative):
        failures.append(
            "missing voice opener — narrative MUST start with Dekho / "
            "Dekho na / Suno / Haan / Bilkul / Chalo"
        )

    if not _HEDGE_RX.search(narrative):
        failures.append(
            "missing soft hedge — must contain thoda / halki si / dheere / "
            "kuch hi / jaldbaazi mat / etc."
        )

    if not _SUGGESTION_RX.search(narrative):
        failures.append(
            "missing suggestion-not-command phrasing — must contain ruk jao "
            "/ kar sakte ho / consult kar lo / soch lo / dekh lo / wait karo "
            "/ behtar hoga / etc. (drill-sergeant imperatives are forbidden)"
        )

    # Forward warmth must close the narrative — search ONLY the last sentence.
    last_sent = _last_sentence(narrative)
    if not _FORWARD_RX.search(last_sent):
        failures.append(
            "missing forward-warmth closer in the LAST sentence — closing "
            "sentence must end with dheere clear hogi / window khulega / "
            "raasta banega / behtar hota jaayega / etc."
        )

    jm = _BANNED_JARGON_RX.search(narrative)
    if jm:
        failures.append(
            f"jargon leak in narrative: {jm.group(0)!r} — translate to "
            f"real-life metaphor"
        )

    if _AI_BRAND_LEAK_RX.search(narrative + " " + advisor):
        failures.append(
            "AI/LLM brand leak — never mention AI / GPT / OpenAI / "
            "language model"
        )

    if _BANNED_BRAND_RX.search(narrative + " " + advisor):
        failures.append(
            "banned brand-safety phrase — no rupee guarantees, no death "
            "predictions, no divorce/bankruptcy assertions"
        )

    # Advisor cite enforcement.
    if require_advisor:
        adv_lower = advisor.lower()
        cite_present = any(w in adv_lower for w in (
            "ca ", " ca,", " ca.", " ca:", "chartered accountant",
            "sebi", "advisor", "advisor",
            "doctor", "specialist", "physician", "counselor", "counsellor",
            "therapist", "lawyer", "advocate", "attorney", "helpline",
        )) or adv_lower.startswith("ca ") or adv_lower.endswith(" ca")
        if not cite_present:
            failures.append(
                f"advisor_line missing required professional cite for "
                f"bucket={intent_bucket} — must include CA / SEBI advisor "
                f"/ doctor / specialist / lawyer / counselor / helpline"
            )

    # Fact echo — at least 1 verbatim user number/duration/person/date if any provided.
    user_strings: list[str] = []
    for k in ("numbers", "durations", "persons", "dates"):
        for s in (intent_facts.get(k) or []):
            if isinstance(s, str) and s.strip():
                user_strings.append(s.strip())
    if user_strings:
        echoed = any(s.lower() in narrative.lower() for s in user_strings)
        if not echoed:
            failures.append(
                f"narrative did not echo any user fact verbatim — must "
                f"include at least one of: {user_strings}"
            )

    return "; ".join(failures) if failures else None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
def compose_card_narrative(
    intent_summary:  str,
    intent_bucket:   str,
    intent_facts:    dict,
    raw_engine_text: str,
    language:        str = "hn",
    emotional_tone:  str = "neutral",
    *,
    intent_domain: str = "",
    timeout_s: float = 20.0,
    model:     Optional[str] = None,
    max_retries: int = 2,
) -> NarratorCard:
    """Compose a single conversational diagnostic card. Raises NarratorV2Error
    on persistent failure. Caller should catch and surface a per-card error."""
    if not intent_summary.strip():
        raise NarratorV2Error("empty intent_summary")

    # Lazy import to avoid circular dependency.
    try:
        from openai_helper import _get_client  # type: ignore
    except Exception as exc:
        raise NarratorV2Error(f"openai_helper unavailable: {exc}") from exc

    client = _get_client()
    if client is None:
        raise NarratorV2Error("OpenAI client not configured")

    chosen_model = (model
                    or os.environ.get("NARRATOR_V2_MODEL")
                    or os.environ.get("OPENAI_MODEL")
                    or "gpt-4.1-mini")

    require_advisor = (
        intent_bucket in _REQUIRE_ADVISOR_BUCKETS
        or (intent_domain or "").lower() in _REQUIRE_ADVISOR_DOMAINS
    )

    user_prompt = _build_user_prompt(
        intent_summary=intent_summary,
        intent_bucket=intent_bucket,
        intent_facts=intent_facts,
        raw_engine_text=raw_engine_text or "(no engine context — answer "
                                            "from the intent summary only)",
        language=language,
        emotional_tone=emotional_tone,
        require_advisor=require_advisor,
    )

    last_error: Optional[str] = None
    started = time.time()

    for attempt in range(max_retries + 1):
        retry_hint = ""
        if attempt > 0 and last_error:
            retry_hint = (
                f"\n\nPREVIOUS ATTEMPT FAILED VALIDATION: {last_error}\n"
                f"Fix the failure on this attempt while keeping all other rules."
            )

        try:
            resp = client.chat.completions.create(
                model=chosen_model,
                temperature=0,
                timeout=timeout_s,
                messages=[
                    {"role": "system", "content": _VOICE_RULES},
                    {"role": "user",   "content": user_prompt + retry_hint},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": _NARRATOR_SCHEMA,
                },
            )
        except Exception as exc:
            last_error = f"openai_call_failed: {type(exc).__name__}: {exc}"
            print(f"[narrator_v2] attempt {attempt + 1} call failed: {last_error}",
                  flush=True)
            continue

        try:
            raw_content = (resp.choices[0].message.content or "").strip()
            if not raw_content:
                last_error = "empty response"
                continue
            data = json.loads(raw_content)
        except Exception as exc:
            last_error = f"parse_failed: {exc}"
            continue

        # Validate against voice rules.
        fail = _validate_card(data, intent_facts, intent_bucket, require_advisor)
        if fail is None:
            elapsed = int((time.time() - started) * 1000)
            return NarratorCard(
                verdict_tag  = data["verdict_tag"],
                narrative    = data["narrative"].strip(),
                remedy_line  = (data.get("remedy_line")  or "").strip(),
                advisor_line = (data.get("advisor_line") or "").strip(),
                _internal    = data.get("_internal") or {},
                latency_ms   = elapsed,
            )

        last_error = fail
        print(f"[narrator_v2] attempt {attempt + 1} validation failed: {fail}",
              flush=True)

    elapsed = int((time.time() - started) * 1000)
    raise NarratorV2Error(
        f"failed after {max_retries + 1} attempts in {elapsed}ms: {last_error}"
    )
