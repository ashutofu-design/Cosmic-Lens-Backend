"""Sprint-26 — AI-only Question Understanding.

ONE LLM call → {intent, topic, confidence}.
This is the SOLE source of truth for routing every user question.
No regex pipeline, no AI-Ear merge, no multi-source override layers.

Fallback:
    If AI confidence < 0.6 OR the call fails, a minimal regex fires
    purely as a safety-net so the request still lands somewhere sane.

Routing contract:
    intent ∈ {problem, timing, decision, planet, analysis}
    topic  ∈ {finance, career, marriage, love, health, general}

Downstream code maps `intent` → narrator supertype via `supertype_for(intent)`.
Topic carries domain flavour but does NOT pick the engine.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional


# ── Allowed values ──────────────────────────────────────────────────────────
INTENTS = ("problem", "timing", "decision", "planet", "analysis")
TOPICS  = ("finance", "career", "marriage", "love", "health", "general")


# ── Prompt ──────────────────────────────────────────────────────────────────
# Sprint-26 base prompt + boundary definitions added after empirical
# evaluation showed the AI confused: (a) planet-status questions naming
# "vargottam"/"exalted"/etc as decisions, (b) "bachhe" (children) as a
# marriage topic, (c) "dosh" (defect) as analysis instead of problem.
# The base structure (input shape, output shape, rules block) is unchanged
# — we only added two short DEFINITIONS sections and three EDGE-CASE
# examples. Output budget (max_tokens=80) is untouched.
_PROMPT_TEMPLATE = (
    "You are a question understanding module.\n\n"
    "Your job is ONLY to understand what the user is asking.\n\n"
    "User question:\n"
    "\"{question}\"\n\n"
    "Return STRICT JSON only:\n\n"
    "{{\n"
    "  \"intent\": \"problem | timing | decision | planet | analysis\",\n"
    "  \"topic\": \"finance | career | marriage | love | health | general\",\n"
    "  \"intents_ranked\": [\"<primary>\", \"<secondary?>\", \"<tertiary?>\"],\n"
    "  \"topics_all\": [\"<primary>\", \"<secondary?>\"],\n"
    "  \"hidden_intent\": \"<≤8 words underlying ask, no psychology guessing>\",\n"
    "  \"cross_domain_root_cause\": true | false,\n"
    "  \"confidence\": 0.0 to 1.0\n"
    "}}\n\n"
    "MULTI-INTENT RANKING (intents_ranked):\n"
    "- Always include the PRIMARY intent first (same value as the `intent` field).\n"
    "- Add SECONDARY only if the question genuinely carries a second ask "
    "(e.g. 'why is this happening AND when will it end' = problem + timing).\n"
    "- Add TERTIARY only if a third ask is clearly present.\n"
    "- Pick the PRIMARY by what the user MOST wants answered:\n"
    "  • analysis > problem when the user asks 'same reason or different' / "
    "'kya dono ek hi reason se' / 'compare these two' (the comparison IS the ask).\n"
    "  • problem > timing when the user is venting frustration first and asking "
    "'kab' as a follow-on (e.g. 'paisa nahi ruk raha, kab control hoga' → "
    "primary=problem, secondary=timing).\n"
    "  • timing > problem when 'kab' is the lead and the problem is just context.\n"
    "  • decision is always primary when 'should I X or Y' is the lead.\n\n"
    "MULTI-DOMAIN (topics_all):\n"
    "- Include EVERY domain the question genuinely spans (max 2). Do NOT add a "
    "second domain just because a word brushes past it — the user must be "
    "actually asking about both areas.\n"
    "- 'finance + career', 'marriage + love', 'health + career' are common pairs.\n"
    "- IMPORTANT: the singular `topic` field MUST be ONE single value (the "
    "PRIMARY domain — same as topics_all[0]). Never put 'finance | career' or "
    "any combined string in `topic` — that field accepts ONE enum value only.\n"
    "- Same rule for the singular `intent`: ONE value (= intents_ranked[0]).\n\n"
    "HIDDEN INTENT (hidden_intent):\n"
    "- ≤8 words capturing the underlying ASK in plain language. NO psychology, "
    "NO behavioural guessing, NO speculation about user's mindset.\n"
    "- Good: 'savings/retention issue', 'common root cause vs separate', "
    "'phase exit timing', 'compatibility check'.\n"
    "- Bad: 'user wants validation', 'looking for external fix', "
    "'avoiding accountability'.\n"
    "- If no hidden layer beyond the surface ask, return null (JSON null).\n\n"
    "CROSS-DOMAIN ROOT CAUSE (cross_domain_root_cause):\n"
    "- TRUE only when topics_all has ≥2 entries AND the user explicitly asks "
    "whether the two issues share a single cause — phrases like 'ek hi reason "
    "se', 'same reason', 'connected hai', 'related hain', 'dono ek saath', "
    "'because of the same thing'.\n"
    "- Otherwise FALSE.\n\n"
    "INTENT definitions (pick the most specific that fits):\n"
    "- planet   → ANY question that NAMES a graha (Sun, Moon, Mars, Mercury, "
    "Jupiter, Venus, Saturn, Rahu, Ketu / Surya, Chandra, Mangal, Budh, Guru, "
    "Shukra, Shani) — even if phrased as 'X kaisa hai' or 'X mera kaisi hai' "
    "(asking about a single named graha = planet intent, not analysis). "
    "ALSO planet: strong / weak / strongest / weakest / vargottam / exalted "
    "/ debilitated / combust / retrograde status. Words like 'kaunsa planet', "
    "'konsa graha', 'sabse powerful grah' ALWAYS mean planet — NOT decision.\n"
    "- problem  → dosha / dosh / defect / affliction, 'kyun nahi', 'why not', "
    "delay, stuck, suffering, complaint, kharab, bura. 'X dosh hai kya' is "
    "ALWAYS problem — NOT analysis.\n"
    "- timing   → 'when', 'kab', 'kab hoga', 'kitne saal', 'how long', a "
    "future date or period.\n"
    "- decision → 'should I', 'karu ya nahi', 'chahiye', 'sahi hai kya', "
    "choosing between options or asking for a recommendation.\n"
    "- analysis → THREE flavours, all map here:\n"
    "    (a) general overview / lifecycle questions — 'kaisa hai', "
    "'kaisi rahegi', overall theme.\n"
    "    (b) DEFINITIONAL or EXPLANATORY questions — 'X kya hai', "
    "'X ka matlab kya hai', 'X ke baare mein bata', 'X samjhao', "
    "'remedy bata', 'kya farak hai', concept / comparison. CRITICAL: "
    "'X kya hai' / 'what is X' is ALWAYS analysis even when X is a "
    "doshic or problem-flavoured noun (e.g. 'Kaal sarp dosh kya hai', "
    "'Manglik kya hai', 'Pitra dosh kya hai' — all analysis, NOT problem).\n"
    "    (c) CONDITIONAL or IMPLICATION questions — 'X hai to Y ho "
    "jayega?', 'Agar A hai to B hoga?', 'X strong hai to Y automatically "
    "strong?' (even when a graha is named in the condition — the "
    "QUESTION is about the implication, not the planet status).\n"
    "  Also the fallback when none of intent above fits.\n\n"
    "TOPIC definitions (be strict — do NOT bleed across topics):\n"
    "- marriage → ONLY spouse / wedding / partner / vivah / shaadi / "
    "kalatra. Children, parents, family in general → 'general', NOT marriage.\n"
    "- career   → job, business, work, promotion, profession, naukri, kaam.\n"
    "- finance  → money, paisa, wealth, savings, loan, income, dhan.\n"
    "- love     → romantic relationship, girlfriend / boyfriend / crush "
    "(NOT marriage).\n"
    "- health   → illness, body, disease, bimari, sehat.\n"
    "- general  → anything not in the above five (children, parents, life "
    "overview, concepts, planet status without a domain).\n\n"
    "Rules:\n"
    "- Do NOT answer the question\n"
    "- Do NOT explain anything\n"
    "- No extra text, only JSON\n"
    "- Choose the closest intent even if question is vague\n"
    "- Keep it simple and accurate"
)


# ── Minimal regex fallback (only used when AI fails / low conf) ─────────────
# Order matters — first-match wins. Patterns kept short on purpose; this is
# a safety-net, NOT a routing layer.
_FALLBACK_INTENT_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("planet",   re.compile(
        r"\b(strong|weak|powerful|kamzor|kamjor|vargottam|"
        r"shakti|balwan|exalt|debilit|planet|grah|graha)\b", re.I)),
    ("timing",   re.compile(
        r"\b(when|kab|kab tak|kitne din|kitne saal|timing|date|year|month|"
        r"saal|mahina|samay)\b", re.I)),
    ("problem",  re.compile(
        r"\b(problem|dosh|dosha|bura|kharab|delay|stuck|why.*not|"
        r"kyun|kyu|nahi ho|nahi mil)\b", re.I)),
    ("decision", re.compile(
        r"\b(should i|kya karu|kya karoon|chahiye|sahi hai|right time|"
        r"karna chahi|sahi rahega)\b", re.I)),
    # 'analysis' is the implicit default
)

_FALLBACK_TOPIC_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("marriage", re.compile(
        r"\b(shaadi|shadi|vivah|marriage|spouse|wife|husband|patni|pati)\b", re.I)),
    ("career",   re.compile(
        r"\b(career|naukri|job|business|kaam|work|profession|promotion)\b", re.I)),
    ("finance",  re.compile(
        r"\b(money|paisa|paise|wealth|finance|dhan|loan|kamai|income|salary)\b", re.I)),
    ("health",   re.compile(
        r"\b(health|sehat|swasth|illness|disease|bimari|rog)\b", re.I)),
    ("love",     re.compile(
        # Sprint-26 Step 4 Phase 2 (architect-recommended fix): added
        # rishta / rishtey / rishton / partner / breakup so the topic
        # recovery post-pass can lift these out of 'general' to match
        # what detect_domain_anchor() already recognises. Without these,
        # a question like "rishtey mein problem hi problem" correctly
        # bypasses the clarification gate (anchor found) but its topic
        # would stay 'general' downstream — inconsistent.
        r"\b(love|pyaar|pyar|relationship|girlfriend|boyfriend|crush|ishq|"
        r"rishta|rishtey|rishton|partner|breakup)\b", re.I)),
)


def _fallback_classify(question: str) -> dict:
    """Last-resort regex classification. Returns confidence=0.5."""
    q = question or ""
    intent = "analysis"
    topic  = "general"
    for name, rx in _FALLBACK_INTENT_RX:
        if rx.search(q):
            intent = name
            break
    for name, rx in _FALLBACK_TOPIC_RX:
        if rx.search(q):
            topic = name
            break
    # Sprint-26 Fix-M: minimal multi-intent shape so downstream code can rely
    # on the new fields even when the LLM call failed. We only seed the
    # primary entries — the AI is the one that ranks secondaries.
    # Sprint-26 Fix-Q (post-architect-review): `has_recovery_subask` is now
    # part of the canonical contract emitted by every code path of
    # understand_question() (AI success, AI low-conf, AI error, regex
    # fallback, empty input). Putting it inside the function instead of
    # only in ai_ask() removes the silent-failure risk where a future
    # refactor of question_understanding callers would lose the flag.
    # Sprint-26 Step 4 Phase 2 — emit the deterministic safety flags from
    # the regex fallback path too, so downstream gate logic in
    # openai_helper.py never sees a missing key regardless of which return
    # path fired.
    _fb_anchor    = detect_domain_anchor(q) if q else False
    _fb_sustained = detect_sustained_problem(q) if q else False
    return {
        "intent":     intent,
        "topic":      topic,
        "intents_ranked":          [intent],
        "topics_all":              [topic],
        "hidden_intent":           None,
        "cross_domain_root_cause": False,
        "has_recovery_subask":     bool(_RECOVERY_SUBASK_RX.search(q)) if q else False,
        "domain_anchor_found":      _fb_anchor,
        "sustained_problem_pattern": _fb_sustained,
        "clarification_needed":      _fb_sustained and not _fb_anchor,
        "confidence":              0.5,
        "source":                  "regex_fallback",
    }


def _normalise_multi_fields(data: dict, intent: str, topic: str) -> dict:
    """Sanitise the new multi-intent fields against the allowed enums.
    Falls back to the primary intent/topic if the AI emitted garbage."""
    raw_intents = data.get("intents_ranked")
    if isinstance(raw_intents, list):
        cleaned: list[str] = []
        for v in raw_intents[:3]:
            if isinstance(v, str):
                vv = v.strip().lower()
                if vv in INTENTS and vv not in cleaned:
                    cleaned.append(vv)
        intents_ranked = cleaned or [intent]
    else:
        intents_ranked = [intent]
    if intent not in intents_ranked:
        intents_ranked = [intent] + [x for x in intents_ranked if x != intent]
        intents_ranked = intents_ranked[:3]

    raw_topics = data.get("topics_all")
    if isinstance(raw_topics, list):
        cleaned_t: list[str] = []
        for v in raw_topics[:2]:
            if isinstance(v, str):
                vv = v.strip().lower()
                if vv in TOPICS and vv not in cleaned_t:
                    cleaned_t.append(vv)
        topics_all = cleaned_t or [topic]
    else:
        topics_all = [topic]
    if topic not in topics_all:
        topics_all = [topic] + [x for x in topics_all if x != topic]
        topics_all = topics_all[:2]

    raw_hidden = data.get("hidden_intent")
    if isinstance(raw_hidden, str):
        hidden = raw_hidden.strip()
        # Cap at 12 words, drop when empty/null-ish or when AI hallucinated
        # psychology language we explicitly told it to avoid.
        if hidden.lower() in ("", "null", "none", "n/a"):
            hidden = None
        else:
            hidden = " ".join(hidden.split()[:12])
    else:
        hidden = None

    raw_cross = data.get("cross_domain_root_cause")
    cross = bool(raw_cross) and len(topics_all) >= 2

    return {
        "intents_ranked":          intents_ranked,
        "topics_all":              topics_all,
        "hidden_intent":           hidden,
        "cross_domain_root_cause": cross,
    }


# ── Sprint-26 Fix-N — "Why-leading" intent promoter ──────────────────────────
# When a question explicitly asks WHY (kyun/why) or names a CONTRADICTION /
# MISMATCH between expectation and reality, the user is asking for
# root-cause REASONING, not just complaint description. The classifier
# sometimes picks `problem` (the surface complaint) as primary; we must
# promote `analysis` to PRIMARY in that case so the narrator routes through
# GENERAL_ANALYSIS and explains MD/AD/transit reasoning instead of just
# acknowledging the pain.
import re as _re_why
_WHY_LEADING_RX = _re_why.compile(
    r"\b(kyun|kyo+n|kyu+|why|क्यों|क्यूँ|"
    r"contradiction|contradict|"
    r"mismatch|mismatched|"
    r"opposite|ulta|ulti|"
    r"clash(?:ing)?|conflict(?:ing)?)\b",
    _re_why.IGNORECASE,
)


# ── Sprint-26 Fix-O — Personal-chart-anchor detector ─────────────────────────
# When a question contains a personal possessive ("mera/meri/mere/my") next
# to a chart-anchor noun (dasha/kundli/lagna/chart/horoscope/etc.), it is
# UNAMBIGUOUSLY a personal astrology question that MUST go through the chart
# pipeline — even when the AI classifier marks topic=general (which would
# normally route to concept-explainer mode and skip the chart entirely).
# Without this override, "Mera dasha bolte hain achha chal raha hai…" loses
# access to the user's actual MD/AD lord names and the answer goes shallow.
# Sprint-26 Fix-O hardening (architect-found regression):
# DO NOT allow arbitrary filler words between possessive and anchor — that
# matched third-person ownership chains ("mere dost ki kundli", "meri maa
# ki dasha", "मेरी माँ की कुंडली") which are NOT the user's own chart and
# must not force astro mode. Instead, require either:
#   (a) direct adjacency: possessive + chart-noun, OR
#   (b) an OPTIONAL astro-qualifier word between them (janma/janam/navamsa/
#       navmansh/chalit/moon/sun/birth) — these are pure astrology vocabulary
#       and cannot be mistaken for relationship nouns ("dost", "maa", "pati").
# Roman compound forms (janamkundli, janmakundli, janampatri/patrika) are
# added explicitly to the anchor list so they remain detectable.
_PERSONAL_CHART_RX = _re_why.compile(
    r"\b(?:mera|meri|mere|apna|apni|apne|my)\s+"
    r"(?:(?:janma|janam|navamsa|navmansh|chalit|moon|sun|birth)\s+)?"
    r"(?:dasha|maha\s*dasha|mahadasha|antar\s*dasha|antardasha|"
    r"pratyantar|bhukti|"
    r"kundli|kundali|kundli|chart|"
    r"janamkundli|janmakundli|janampatri|janampatrika|"
    r"lagna|ascendant|"
    r"rashi|moon\s*sign|sun\s*sign|"
    r"nakshatra|"
    r"janma|janm|birth\s*chart|birth|horoscope|"
    r"saturn|shani|mars|mangal|jupiter|guru|brihaspati|"
    r"venus|shukra|mercury|budh|rahu|ketu|sun|surya|moon|chandra)\b",
    _re_why.IGNORECASE,
)
# Devanagari forms — same hardening: direct adjacency or optional
# astro-qualifier (जन्म/जनम/नवमांश), no arbitrary fillers, so genitive
# ownership chains like "मेरे दोस्त की कुंडली" / "मेरी माँ की कुंडली"
# (which contain "की" + a kinship noun before the anchor) do NOT match.
_PERSONAL_CHART_DEVA_RX = _re_why.compile(
    r"(?:मेरा|मेरी|मेरे|अपना|अपनी|अपने)\s+"
    r"(?:(?:जन्म|जनम|नवमांश|चलित)\s+)?"
    r"(?:दशा|महादशा|अंतरदशा|अन्तर्दशा|कुंडली|कुण्डली|"
    r"जन्मकुंडली|जन्मकुण्डली|जन्मपत्री|जन्मपत्रिका|"
    r"लग्न|राशि|नक्षत्र|जन्म|चार्ट|"
    r"शनि|मंगल|गुरु|बृहस्पति|शुक्र|बुध|राहु|केतु|सूर्य|चंद्र|चन्द्र)"
)


def is_personal_chart_question(question: str) -> bool:
    """True when the question has a personal-possessive next to a chart noun.
    Used by openai_helper to FORCE mode=astro even when topic=general."""
    if not question:
        return False
    return bool(_PERSONAL_CHART_RX.search(question)
                or _PERSONAL_CHART_DEVA_RX.search(question))


# ── Sprint-26 Fix-Q — Recovery sub-ask detector ──────────────────────────────
# Some questions carry a SECONDARY ask about whether the loss / damage / drop
# can be RECOVERED — independent of the primary intent (which is usually
# decision or problem). Examples:
#   • decision + recovery: "exit karu ya continue? agar continue karu to paisa
#                           recover hoga ya nahi?"
#   • problem  + recovery: "paisa stuck hai, kya wapas milega?"
#   • timing   + recovery: "kab tak nuksan recover hoga?"
# Until Fix-Q, the classifier collapsed these into [decision, problem] and
# the wealth/narrator output answered only the primary, dropping the
# recovery sub-question entirely.
#
# Fix-Q is a deterministic regex post-pass — does NOT add a new INTENTS enum
# value (which would ripple through supertype routing, fallback regex, etc.).
# Instead it sets a separate boolean flag `has_recovery_subask` on the
# returned dict so downstream code can:
#   • inject a `recovery_outlook` field into the wealth structured-output
#     schema and prompt, and
#   • add a "Recovery line" instruction to the GENERAL_ANALYSIS narrator
#     contract so V→Recovery→Timing replaces V→Reason→Timing for these
#     questions.
_RECOVERY_SUBASK_RX = _re_why.compile(
    # English / Hinglish recovery vocabulary — direct verbs and noun forms.
    # Anchored on "recover", "recoup", "vasool" so we don't false-positive
    # on every "wapas" (which can also mean "back" in non-money contexts —
    # we restrict it to combos like "wapas aayega/milega/aana/milna").
    #
    # Sprint-26 Fix-Q (post-architect-review patch) — added the following
    # high-frequency Hinglish phrasings flagged as missed by the architect:
    #   • "paisa kab tak aayega"      → "(paisa|paise|amount|funds) kab tak"
    #   • "loss/nuksan bharne mein"   → "(loss|nuksan|nuksaan) bharne"
    #   • "wapis" (vs only "wapas")   → added "wapis" alongside "wapas"
    #   • "vasooli kab"               → "vasooli|vasuli" already covered by
    #                                   the existing "vasool(?:i|na)?" stem
    #                                   but added "kab" trigger pair to be
    #                                   exhaustive on the timing-asking form.
    #   • "kitna time lagega" + loss / paise context → covered by the new
    #     "kab tak" + "(paisa|loss|nuksan|funds)" combos.
    r"\b("
    r"recover(?:y|ed|ing)?|recoup(?:ed|ing)?|"
    r"recoverable|recovery|"
    r"vasool(?:i|na)?|vasul(?:i|na)?|vasooli|vasuli|"
    r"(?:wapas|wapis)\s+(?:aayega|aana|aaye(?:gi|ga)?|milega|milegi|milna|"
    r"paayega|laana|le(?:na|kar))|"
    r"(?:paisa|paise|paisey|amount|funds?)\s+(?:wapas|wapis|laut|return|"
    r"aayega|aayegi|recover|vasool|kab\s+tak)|"
    r"(?:loss|nuksan|nuksaan)\s+(?:cover|recover|wapas|wapis|recoup|"
    r"patega|patta|bhar(?:ne|ega|egi|ne\s+me(?:in)?)?)|"
    r"(?:loss|nuksan|nuksaan)\s+(?:bharne|recover|cover)\s+"
    r"(?:me(?:in)?|mein)\s+kitna(?:\s+time|\s+samay)?|"
    r"vasooli\s+kab|"
    r"recoup|"
    # Devanagari forms
    r"वसूल(?:ी|ना)?|वापस\s+(?:आएगा|आना|मिलेगा|मिलना|पाएगा)|"
    r"नुकसान\s+(?:भर|वापस|कवर)"
    r")\b",
    _re_why.IGNORECASE,
)


def has_recovery_subask(question: str) -> bool:
    """True when the question carries a secondary recovery ask.
    Used by openai_helper to inject `recovery_outlook` into wealth
    structured output and to add a Recovery line in the GENERAL_ANALYSIS
    narrator contract."""
    if not question:
        return False
    return bool(_RECOVERY_SUBASK_RX.search(question))


# ── Sprint-26 Step 4 Phase 2 (Apr 28 2026) — DETERMINISTIC SAFETY DETECTORS ─
# Phase 1 (prompt-side) failed to make the model ask for clarification on
# domain-ambiguous "problem hi problem" questions — even with verbatim-MUST +
# explicit override of "open with answer" + ban on domain inference, the LLM
# still inferred relationship from KP cusp signals. Phase 2 makes the
# detection deterministic so the gate in openai_helper.py can short-circuit
# to a clarification template BEFORE calling the LLM. The classifier surfaces
# three new flags that downstream consumers (gate, narrator, validators) can
# trust without recomputing.
#
# Anchor list mirrors GUARD-2 wording in _NARRATOR_SAFE_FALLBACK at
# openai_helper.py:5685 — keeping the two in sync is critical: if a word
# becomes an anchor here, the prompt-side guard must also recognise it,
# otherwise a fall-through to the LLM (e.g. when the gate is bypassed) would
# get inconsistent behaviour.
_DOMAIN_ANCHOR_RX = re.compile(
    r"\b("
    # Career / work
    r"career|job|naukri|nokri|kaam|work|business|biznes|profession|"
    r"promotion|interview|office|"
    # Money / finance
    r"paisa|paise|paisey|money|wealth|finance|financial|dhan|loan|"
    r"income|salary|kamai|savings|investment|stock|share|trading|"
    r"property|investment|mutual\s*fund|"
    # Relationships (non-marriage)
    r"rishta|rishtey|rishton|relationship|partner|breakup|"
    # Marriage
    r"shaadi|shadi|vivah|marriage|spouse|wife|husband|patni|pati|"
    r"kalatra|engagement|engaged|"
    # Romantic
    r"love|pyar|pyaar|girlfriend|boyfriend|crush|ishq|"
    # Health
    r"sehat|swasth|health|illness|disease|bimari|rog|body|"
    r"medical|hospital|doctor|"
    # Home / property
    r"ghar|home|makaan|makan|"
    # Children / family
    r"child|children|santaan|santan|bachhe|bachche|bachhon|baby|"
    r"family|parents|maa|maan|baap|pita|mata|"
    # Education
    r"study|studies|education|exam|padhai|college|university|school"
    r")\b",
    re.IGNORECASE,
)


# Sustained-problem pattern — the exact triggers GUARD-2 was supposed to
# catch. Keeping it tight on purpose: false positives here would over-fire
# the clarification gate on perfectly clear questions, which would feel
# more annoying than helpful.
_SUSTAINED_PROBLEM_RX = re.compile(
    r"("
    # "problem hi problem" / "samasya hi samasya"
    r"problem\s+hi\s+problem|samasya\s+hi\s+samasya|"
    # "sab kuch ulta" / "sab kuch galat" / "sab kuch bura"
    r"sab\s+(?:kuch\s+)?(?:ulta|galat|bura|kharab)|"
    # "kuch theek nahi" / "kuch bhi theek nahi"
    r"kuch\s+(?:bhi\s+)?theek\s+nahi|"
    # "X-Y mahine" or "X-Y months" or "X to Y mahine"
    r"\d+\s*(?:[-–to]+\s*)\d+\s+(?:mahine|months?|saal|years?)\s+se|"
    # "pichle X mahine" / "last X months"
    r"(?:pichle|pichhle|piche|last)\s+\d+\s+(?:mahine|months?|saal|years?)|"
    # Explicit contradiction wording
    r"contradiction|paradox|inconsistency|virodhabhas|"
    # "phir bhi" + negative — classic Hinglish contradiction marker
    r"phir\s+bhi.+?(?:problem|nahi|nahin|kharab|galat|bura|stuck)"
    r")",
    re.IGNORECASE,
)


def detect_domain_anchor(question: str) -> bool:
    """True when the question explicitly names a life-area anchor.

    Used by the Phase-2 safe-narration gate to decide whether the GUARD-2
    domain-clarification short-circuit should fire. A `True` here means the
    user told us where to look (career / paisa / rishtey / sehat / ghar /
    child / study / etc.) — no clarification needed.
    """
    return bool(_DOMAIN_ANCHOR_RX.search(question or ""))


def detect_sustained_problem(question: str) -> bool:
    """True when the question describes a sustained / recurring negative
    state pattern. Tight on purpose — false positives over-fire the
    clarification gate."""
    return bool(_SUSTAINED_PROBLEM_RX.search(question or ""))


def needs_domain_clarification(question: str) -> bool:
    """Composite signal — sustained problem AND no explicit domain anchor.
    This is the precondition the Phase-2 gate uses to short-circuit to a
    clarification template instead of calling the LLM."""
    if not question:
        return False
    return (detect_sustained_problem(question)
            and not detect_domain_anchor(question))


def _maybe_promote_analysis_for_why(question: str,
                                    intents_ranked: list[str],
                                    intent: str) -> tuple[list[str], str, bool]:
    """If the question is WHY-leading or describes a contradiction, promote
    `analysis` to PRIMARY. Demote whatever was primary down to secondary.
    Returns (new_intents_ranked, new_intent, promoted_flag).
    """
    if not question or not _WHY_LEADING_RX.search(question):
        return intents_ranked, intent, False
    if not intents_ranked:
        intents_ranked = [intent] if intent in INTENTS else ["analysis"]
    # Already analysis-primary? Nothing to do.
    if intents_ranked[0] == "analysis":
        return intents_ranked, intent, False
    # Build new ranking: analysis first, then keep the rest in order
    # (de-duped). Cap at 3.
    new_ranked = ["analysis"] + [i for i in intents_ranked if i != "analysis"]
    new_ranked = new_ranked[:3]
    return new_ranked, "analysis", True


# ── Main API ────────────────────────────────────────────────────────────────
# ── Phase 4.1 Fix-P: Classifier Sanity Layer ───────────────────────────────
# Deterministic post-classification override. The AI sometimes returns
# `intent="timing"` with confidence ≥ 0.9 for questions that are pure
# CHART-FACT lookups ("Nth house ka swami kaun hai", "Mangal dosh hai
# kya"). These questions have no temporal answer; routing them through the
# TIMING_QUERY narrator forces the model to invent dates. This sanity
# layer detects unambiguous lookup/yes-no patterns and re-tags such
# requests as `analysis` (the most flexible factual narrator). It runs
# AFTER the AI verdict and is confidence-blind — even 0.95 verdicts get
# corrected when the pattern is decisive. Every override is recorded on
# the returned dict (`intent_overridden_from`, `intent_override_reason`,
# `intent_override_phase`) so callers can trace it via the `1b.CLASSIFIER
# _OVERRIDE` telemetry hook in openai_helper.py.

# "Nth house ka swami / lord / malik / adhipati / owner"
_LOOKUP_LORD_RX = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:house|ghar|bhava|bhav)\s+"
    r"(?:k[ae]\s+)?(?:swami|lord|malik|adhipati|owner)\b",
    re.IGNORECASE,
)
# Karaka lookups
_LOOKUP_KARAKA_RX = re.compile(
    r"\b(?:atmakaraka|amatyakaraka|yogakaraka|darakaraka|"
    r"bhratrukaraka|matrukaraka|putrakaraka|gnati[\s\-]?karaka)\b",
    re.IGNORECASE,
)
# Yes/no dosha questions
_LOOKUP_DOSHA_YESNO_RX = re.compile(
    r"\b(?:manglik|mangal\s+dosh[ai]?|mangalik|nadi\s+dosh[ai]?|"
    r"bhakoot\s+dosh[ai]?|kaal\s+sarp|kalsarp|sade\s+sati|"
    r"kemdrum|chandal|guru\s+chandal|grahan\s+dosh)\b"
    r"[^.?!\n]{0,40}?\b(?:hai|hu|hain|ho|kya|hoon|hain\s+kya|hai\s+kya)\b",
    re.IGNORECASE,
)
# Generic yes/no chart-fact lookups ("kya mera 5th house strong hai", "5th
# house strong hai kya"). Phase 4.1 architect-required tightening: the
# bare "hai kya" / "kya mera" trigger was over-broad and would misroute
# legitimate decision asks like "ye decision sahi hai kya" or "invest
# karu ya nahi, sahi hai kya". The pattern now requires a CHART-FACT
# anchor (house/ghar/bhav, lord/swami/malik, graha/planet, dosh, karaka,
# rashi, nakshatra, dasha, lagna, kundli/kundali, bhagya, nadi, bhakoot,
# ascendant, horoscope, chart) within ±50 chars of the yes/no marker
# before the override is allowed to fire.
#
# Architect review-2 refinements:
#   - bare "yoga|yog" REMOVED — collided with non-astro usage ("yoga
#     class sahi hai kya"). Astrology yoga lookups ALWAYS pair with a
#     chart noun (kundli, house, lagna, dasha, planet, raj+yog compound)
#     so other anchors still catch them. The qualified compound forms
#     `rajyog|rajyoga|dhanyog|dhanyoga|gajakesari` are kept as discrete
#     tokens because they're unambiguously astrological.
#   - Added "kundali" spelling variant alongside "kundli" (also "janam
#     kundali") to recover Hindi-spelling lookup recall.
_LOOKUP_ANCHORS = (
    r"\b(?:house|ghar|bhav[ae]?|lord|swami|malik|adhipati|graha|grah|"
    r"planet|dosh[ai]?|karaka|rashi|nakshatra|dasha|antardasha|"
    r"mahadasha|lagna|kundli|kundali|bhagya|nadi|bhakoot|ascendant|"
    r"horoscope|chart|"
    r"raj\s*yog[a]?|dhan\s*yog[a]?|gajakesari|gaja\s*kesari)\b"
)
_LOOKUP_YESNO_MARKERS = (
    r"(?:\bkya\s+mer[ae]\b|\bkya\s+meri\b|"
    r"\b(?:hu|hoon|hai|hain|ho)\s+kya\b)"
)
_LOOKUP_GENERIC_YESNO_RX = re.compile(
    # anchor-then-yesno OR yesno-then-anchor, both within ±50 chars
    r"(?:" + _LOOKUP_ANCHORS + r"[^.?!\n]{0,50}?" + _LOOKUP_YESNO_MARKERS
    + r"|" + _LOOKUP_YESNO_MARKERS + r"[^.?!\n]{0,50}?" + _LOOKUP_ANCHORS
    + r")",
    re.IGNORECASE,
)


def _apply_classifier_sanity_layer(out: dict, question: str) -> dict:
    """Phase 4.1 Fix-P. Mutates and returns `out`.

    Override rule (conservative):
      - Trigger ONLY when the question matches a hard lookup pattern AND
        the AI returned `intent in {"timing", "decision"}` (the two most
        common false positives for lookup queries). Other intents are
        left alone — they're either already correct (`analysis`,
        `planet`) or domain-meaningful (`problem`).
      - Override target is always `analysis` (GENERAL_ANALYSIS narrator
        — flexible, doesn't force date prediction or remedy commitment).
      - Diagnostic fields added on the dict for telemetry tracing.
    """
    if not isinstance(out, dict) or not question:
        return out
    intent = (out.get("intent") or "").lower()
    if intent not in ("timing", "decision"):
        return out

    matched = None
    if _LOOKUP_LORD_RX.search(question):
        matched = "lookup_lord"
    elif _LOOKUP_KARAKA_RX.search(question):
        matched = "lookup_karaka"
    elif _LOOKUP_DOSHA_YESNO_RX.search(question):
        matched = "lookup_dosha_yesno"
    elif _LOOKUP_GENERIC_YESNO_RX.search(question):
        matched = "lookup_generic_yesno"

    if not matched:
        return out

    out["intent_overridden_from"] = intent
    out["intent_override_reason"] = matched
    out["intent_override_phase"]  = "4.1_fix_p"
    out["intent"] = "analysis"
    # Keep intents_ranked consistent so downstream multi-intent logic
    # doesn't see a stale primary at index 0.
    ranked = list(out.get("intents_ranked") or [])
    if not ranked or ranked[0] != "analysis":
        # Demote the original primary to secondary; promote analysis.
        new_ranked = ["analysis"] + [r for r in ranked if r != "analysis"]
        out["intents_ranked"] = new_ranked[:3]
    return out


def understand_question(question: str,
                        *,
                        client: Any = None,
                        model: Optional[str] = None) -> dict:
    """Public entry — Phase 4.1: applies classifier sanity layer (Fix-P)
    on top of the inner AI/regex classifier. Always returns the same dict
    shape; adds `intent_overridden_from`, `intent_override_reason`,
    `intent_override_phase` keys when an override fires."""
    q = (question or "").strip()
    out = _understand_question_inner(question, client=client, model=model)
    return _apply_classifier_sanity_layer(out, q)


def _understand_question_inner(question: str,
                        *,
                        client: Any = None,
                        model: Optional[str] = None) -> dict:
    """Single source of truth for question routing.

    Args:
        question: raw user text (1 line to a long paragraph).
        client:   optional pre-built OpenAI client (else we lazy-import).
        model:    optional model override (else env OPENAI_MODEL or 4.1-mini).

    Returns:
        {
          "intent":     one of INTENTS,
          "topic":      one of TOPICS,
          "confidence": float ∈ [0.0, 1.0],
          "source":     "ai" | "ai_low_conf_regex_fallback" |
                        "ai_error_regex_fallback" | "regex_fallback" | "empty",
          "latency_ms": int (when AI was called),
          # plus diagnostic echo when we fell back from AI:
          "ai_intent": ..., "ai_topic": ..., "ai_confidence": ..., "error": ...
        }

    Never raises — the caller can always trust the dict shape.
    """
    q = (question or "").strip()
    if not q:
        return {
            "intent":     "analysis",
            "topic":      "general",
            "confidence": 0.0,
            "source":     "empty",
            # Sprint-26 Fix-Q (post-architect-review): always emit the flag
            # so callers never see KeyError on the canonical contract.
            "has_recovery_subask": False,
        }

    if model is None:
        model = os.environ.get("QU_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-4.1-mini")

    # Lazy-import the shared OpenAI client from openai_helper so we don't
    # double-init proxies / API-keys.
    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore
            client = _get_client()
        except Exception:
            client = None

    if client is None:
        return _fallback_classify(q)

    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=220,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": _PROMPT_TEMPLATE.format(question=q)}
            ],
        )
        latency_ms = int((time.time() - t0) * 1000)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)

        intent = (data.get("intent") or "").strip().lower()
        topic  = (data.get("topic")  or "").strip().lower()
        try:
            conf = float(data.get("confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        # Clamp
        if conf < 0.0:
            conf = 0.0
        if conf > 1.0:
            conf = 1.0

        # Schema validation — bad enum value normally = fallback.
        # BUT if the AI returned a malformed singular `intent` / `topic`
        # (e.g. "finance | career") AND the corresponding ranked list has a
        # valid first element, recover from that. This keeps multi-intent
        # answers usable when the AI just confuses the singular field.
        if intent not in INTENTS:
            raw_ir = data.get("intents_ranked") or []
            for v in raw_ir:
                if isinstance(v, str) and v.strip().lower() in INTENTS:
                    intent = v.strip().lower()
                    break
        if topic not in TOPICS:
            raw_tp = data.get("topics_all") or []
            for v in raw_tp:
                if isinstance(v, str) and v.strip().lower() in TOPICS:
                    topic = v.strip().lower()
                    break
        if intent not in INTENTS or topic not in TOPICS:
            fb = _fallback_classify(q)
            fb["source"] = "ai_error_regex_fallback"
            fb["error"] = f"bad enum: intent={intent!r} topic={topic!r}"
            fb["latency_ms"] = latency_ms
            return fb

        # Confidence floor — under 0.6 we still return AI's view but mark it
        # as fallback so any threshold checks downstream can act.
        if conf < 0.6:
            fb = _fallback_classify(q)
            fb["source"] = "ai_low_conf_regex_fallback"
            fb["ai_intent"] = intent
            fb["ai_topic"] = topic
            fb["ai_confidence"] = conf
            fb["latency_ms"] = latency_ms
            # Keep AI's ranked extras even at low confidence — they're useful
            # diagnostics even if the engine routing uses regex primaries.
            fb.update(_normalise_multi_fields(data, intent, topic))
            return fb

        out = {
            "intent":     intent,
            "topic":      topic,
            "confidence": conf,
            "source":     "ai",
            "latency_ms": latency_ms,
        }
        out.update(_normalise_multi_fields(data, intent, topic))
        # Sprint-26 Fix-N: deterministic post-pass — promote `analysis` to
        # PRIMARY when the question is WHY-leading or names a contradiction.
        new_ranked, new_intent, promoted = _maybe_promote_analysis_for_why(
            q, out.get("intents_ranked") or [], out["intent"])
        if promoted:
            out["intents_ranked"] = new_ranked
            out["intent"] = new_intent
            out["why_promoted"] = True
        # Sprint-26 Fix-Q (post-architect-review): canonical recovery
        # sub-ask flag — emitted by every successful AI return path so
        # downstream consumers (wealth structured-output prompt, narrator
        # contract, post-validator) can rely on it without re-computing.
        out["has_recovery_subask"] = bool(_RECOVERY_SUBASK_RX.search(q))
        # ── Sprint-26 Step 4 Phase 2 — deterministic safety detectors ──
        # Three new flags surfaced on every AI-success return so the
        # downstream gate in openai_helper.py can short-circuit without
        # recomputing. Names are stable across all return paths (AI ok,
        # AI low-conf fallback, AI error fallback, regex fallback, empty).
        domain_anchor = detect_domain_anchor(q)
        sustained = detect_sustained_problem(q)
        out["domain_anchor_found"]      = domain_anchor
        out["sustained_problem_pattern"] = sustained
        out["clarification_needed"]      = sustained and not domain_anchor
        # Topic recovery — when the AI returned topic="general" but the
        # question text contains a clear life-area anchor, override using
        # the regex fallback so downstream domain-specific paths fire.
        # ONLY applies when topic was the catch-all 'general' AND a
        # specific anchor is found — never overrides an explicit AI
        # choice between two specific topics.
        if out.get("topic") == "general" and domain_anchor:
            for tname, rx in _FALLBACK_TOPIC_RX:
                if rx.search(q):
                    out["topic_recovered_from_general"] = True
                    out["topic_original_ai"] = "general"
                    out["topic"] = tname
                    existing = [t for t in (out.get("topics_all") or [])
                                if t != tname and t != "general"]
                    out["topics_all"] = [tname] + existing
                    break
        return out
    except Exception as exc:
        latency_ms = int((time.time() - t0) * 1000)
        fb = _fallback_classify(q)
        fb["source"] = "ai_error_regex_fallback"
        fb["error"] = str(exc)[:200]
        fb["latency_ms"] = latency_ms
        return fb


# ── intent → narrator supertype mapping ─────────────────────────────────────
# Drives which strict contract block is injected into the system prompt.
# Keys MUST match the canonical supertype identifiers used by
# `_SUPERTYPE_CONTRACT_BLOCKS` and `_validate_supertype_contract` in
# openai_helper.py — i.e. the `*_QUERY` suffix for timing/problem/decision.
_INTENT_TO_SUPERTYPE = {
    "planet":   "STRENGTH_SUMMARY",   # strong/weak/vargottam grounded answer
    "timing":   "TIMING_QUERY",       # when / kab / how-long
    "problem":  "PROBLEM_QUERY",      # dosha / why-not-working
    "decision": "DECISION_QUERY",     # should-I / chahiye / muhurat
    "analysis": "GENERAL_ANALYSIS",   # default narrator
}


def supertype_for(intent: str) -> str:
    """Map AI intent → narrator supertype used by the contract system."""
    return _INTENT_TO_SUPERTYPE.get((intent or "").lower(), "GENERAL_ANALYSIS")
