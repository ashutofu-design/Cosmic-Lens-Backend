"""Post-LLM validator — Health engine (Phase H2 trust lock).

LLM ke output me kabhi-kabhi disease-names, diagnosis phrasing, ya
engine jargon leak ho jata hai — even with strict system prompt.
This validator cleans it without contradicting engine truth, enforces
project's HEALTH-specific safety rules, and flags every violation
for telemetry.

KEY DIFFERENCES from finance validator (per user directive — health
brand-safety zyada critical hai):

  1. DIAGNOSIS-BAN: any disease name (diabetes / cancer / tumour /
     depression / asthma etc.) → replaced with neutral 'health zone'
     phrasing.
  2. "tumhe X hai" / "you have X" / "aap X se peedit" → converted to
     "X risk hai" / "X zone elevated" — never assertive diagnosis.
  3. DEATH / longevity language → stripped (engine never predicts).
  4. CURE-GUARANTEE language ("100%", "guaranteed cure") → softened.
  5. MANDATORY: doctor disclaimer line ALWAYS appended at end (even
     if LLM didn't include it).
  6. FEAR-AMPLIFY words ("danger", "serious problem", "deadly",
     "fatal", "khatarnak", "ghatak") → replaced with calm phrasing
     ("dhyan dena chahiye", "preventive care useful").

Public:
  validate_health_llm_output(text, user_question, sensitive_bucket=None,
                             allowed_yogas=None, direct_fallback_text='')
      -> (cleaned_text, flags_list, action)
"""
from __future__ import annotations
import re
from typing import List, Optional, Tuple


# ── Doctor disclaimer (mandatory tail, project rule) ────────────────
DOCTOR_DISCLAIMER = (
    "Yeh astrological guidance hai — proper diagnosis aur treatment "
    "ke liye doctor consult zaroor karein."
)

# Sensitive-bucket extra disclaimers (appended BEFORE doctor line)
_SENSITIVE_EXTRA = {
    "mental_health": (
        "Agar man bahut bhaari lag raha ho to mental-health professional "
        "ya helpline (iCall 9152987821) se baat karna sabse helpful hai."
    ),
    "reproductive": (
        "Reproductive health ek specialised area hai — fertility "
        "specialist / gynecologist se baat karna sabse sahi rasta hai."
    ),
    "parent_health": (
        "Parent ki tabiyat ke liye family physician + relevant specialist "
        "se time pe consult lena sabse zaroori kaam hai."
    ),
    "addiction": (
        "Addiction recovery me trained counsellor + medical support "
        "milkar best result deti hai — ek professional se zaroor milein."
    ),
}


# ── Disease names → neutral terms (HARD strip — diagnosis-ban) ──────
# Comprehensive list: anything that names a specific medical condition.
_DISEASE_REPLACE = [
    (r"\bdiabetes\b",            "metabolic stress zone"),
    (r"\bdiabetic\b",            "metabolic-stress affected"),
    (r"\bsugar\s+(disease|level\s+high|problem)\b", "metabolic stress zone"),
    (r"\bcancer\b",              "serious health zone"),
    (r"\btumou?r\b",             "serious health zone"),
    (r"\bheart\s+attack\b",      "cardiac stress zone"),
    (r"\bcardiac\s+arrest\b",    "cardiac stress zone"),
    (r"\bheart\s+disease\b",     "cardiac stress zone"),
    (r"\bstroke\b",              "neuro stress zone"),
    (r"\bparalysis\b",           "neuro stress zone"),
    (r"\bdepression\b",          "low-mood zone"),
    (r"\bbipolar\b",             "mental stress zone"),
    (r"\bschizophrenia\b",       "mental stress zone"),
    (r"\banxiety\s+disorder\b",  "mental stress zone"),
    (r"\bpanic\s+disorder\b",    "mental stress zone"),
    (r"\bocd\b",                 "mental stress zone"),
    (r"\bptsd\b",                "mental stress zone"),
    (r"\btuberculosis\b",        "respiratory stress zone"),
    (r"\bt\.?b\.?\b",            "respiratory stress zone"),
    (r"\basthma\b",              "respiratory zone"),
    (r"\bbronchitis\b",          "respiratory zone"),
    (r"\bpneumonia\b",           "respiratory zone"),
    (r"\bcovid(?:-?19)?\b",      "respiratory zone"),
    (r"\barthritis\b",           "joint stress zone"),
    (r"\brheumatism\b",          "joint stress zone"),
    (r"\bkidney\s+failure\b",    "kidney stress zone"),
    (r"\bliver\s+failure\b",     "liver stress zone"),
    (r"\bcirrhosis\b",           "liver stress zone"),
    (r"\bhepatitis\b",           "liver stress zone"),
    (r"\bhiv\b",                 "immunity zone"),
    (r"\baids\b",                "immunity zone"),
    (r"\bepilepsy\b",            "neuro stress zone"),
    (r"\bmigraine\b",            "head stress zone"),
    (r"\bulcer\b",               "digestive stress zone"),
    (r"\bgastritis\b",           "digestive stress zone"),
    (r"\bibs\b",                 "digestive stress zone"),
    (r"\bthyroid\s+(problem|disease|disorder)\b", "endocrine stress zone"),
    (r"\bhypertension\b",        "BP-stress zone"),
    (r"\bhigh\s+blood\s+pressure\b", "BP-stress zone"),
    (r"\bblood\s+pressure\s+problem\b", "BP-stress zone"),
    (r"\bcholesterol\s+(high|problem)\b", "lipid stress zone"),
    (r"\bobesity\b",             "weight stress zone"),
    (r"\binfertility\b",         "fertility zone"),
    (r"\bautism\b",              "neuro-developmental zone"),
    (r"\balzheimer'?s?\b",       "neuro stress zone"),
    (r"\bdementia\b",            "neuro stress zone"),
    (r"\bparkinson'?s?\b",       "neuro stress zone"),
    # Hindi disease words
    (r"\bshakar\s+(ki\s+bimari|disease)\b", "metabolic stress zone"),
    (r"\bdil\s+ki\s+bimari\b",   "cardiac stress zone"),
    (r"\bdimaag\s+ki\s+bimari\b","neuro stress zone"),
    (r"\bjigar\s+ki\s+bimari\b", "liver stress zone"),
    (r"\bgurde\s+ki\s+bimari\b", "kidney stress zone"),
    (r"\bdama\b",                "respiratory zone"),
]

_DISEASE_RX_LIST = [(re.compile(p, re.IGNORECASE), r) for p, r in _DISEASE_REPLACE]


# ── "tumhe X hai" diagnosis-assert phrasing → "risk hai" ────────────
_DIAGNOSIS_ASSERT_PATTERNS = [
    # "tumhe / aapko / tujhe diabetes hai" → "metabolic stress risk hai"
    (re.compile(
        r"\b(tumhe|tumhein|aapko|tujhe|aapke?\s+(?:paas|andar))\s+"
        r"(?:ek\s+|koi\s+)?([a-z\s]+?)\s+(hai|hogi|hoga|ho\s+gayi|ho\s+gaya)\b",
        re.IGNORECASE),
     lambda m: f"{m.group(2).strip()} ka risk indicate ho raha hai"),
    # "you have X" / "you suffer from X"
    (re.compile(r"\byou\s+(have|suffer\s+from|are\s+suffering\s+from)\s+",
                re.IGNORECASE),
     "risk indication present hai for "),
    # "aap X se peedit"
    (re.compile(r"\baap\s+([a-z\s]+?)\s+se\s+peedit\b", re.IGNORECASE),
     lambda m: f"{m.group(1).strip()} risk zone elevated hai"),
    # "X confirm hai" / "X pakka hai"
    (re.compile(r"\b([a-z\s]{3,30}?)\s+(confirm|pakka|definitely)\s+hai\b",
                re.IGNORECASE),
     lambda m: f"{m.group(1).strip()} risk indication hai"),
]


# ── Fear-amplification words → calm phrasing ────────────────────────
_FEAR_REPLACE = [
    (r"\bdanger(?:ous)?\b",         "dhyan-yogya"),
    (r"\bserious\s+problem\b",      "important matter"),
    (r"\bdeadly\b",                 "significant"),
    (r"\bfatal\b",                  "important"),
    (r"\blife[\s-]?threatening\b",  "important"),
    (r"\bkhatarnak\b",              "dhyan-yogya"),
    (r"\bghatak\b",                 "important"),
    (r"\bbhayanak\b",               "important"),
    (r"\bbahut\s+(buri|bura)\s+(haalat|condition)\b",
                                    "dhyan dene wali condition"),
    (r"\bjaan\s+(?:ka\s+)?khatra\b","dhyan-yogya zone"),
    (r"\bcrisis\b",                 "important phase"),
]
_FEAR_RX_LIST = [(re.compile(p, re.IGNORECASE), r) for p, r in _FEAR_REPLACE]


# ── Referral / doctor-mention scrub (Phase H2.2 backup tone-guard) ──
# Catches LLM tone-drift like "professional se baat karo" /
# "expert guidance lo" / "therapist consult karein" that bypass the
# doctor-disclaimer policy. Active ONLY when add_doctor=False.
# Strategy: drop the entire referral SENTENCE (cleaner than swapping
# noun mid-sentence which often produces awkward "trusted person ke
# saath consult karein" output).
_REFERRAL_TRIGGER_WORDS = (
    # Always-referral nouns (unambiguous)
    r"doctor|physician|therapist|counsell?or|"
    r"psychiatrist|psychologist|"
    # Mental-health professional is a fixed phrase — keep it
    r"mental[\s-]?health\s+professional|"
    # Bare "professional" / "specialist" require referral-action context
    # (otherwise "professional life" / "specialist topic" false-fire).
    # Phase H2.2.2 tightening per architect review.
    r"professional\s+(?:se\s+(?:baat|consult|milein|milna|milo|raabta)|"
    r"talk|support|help|guidance|advice|consultation|opinion|ki\s+madad)|"
    r"specialist\s+(?:se\s+(?:baat|consult|milein|milna|milo|raabta)|"
    r"consult|consultation|opinion|advice|dikhaiye|dikhao|ki\s+madad)|"
    # "expert" only as referral verb
    r"expert\s+(?:guidance|advice|consult|consultation|opinion)|"
    # Medical / clinical referral phrases
    r"medical\s+(?:advice|consultation|help|professional|opinion)|"
    r"clinical\s+(?:help|consult|advice|consultation|opinion)"
)
# Match a complete sentence (start-of-string|after . ! ? \n up to next
# . ! ? \n) that contains any trigger word. Trim trailing whitespace.
_REFERRAL_SENTENCE_RX = re.compile(
    rf"(?:(?<=^)|(?<=[\.!?\n]))\s*[^\.!?\n]*?\b(?:{_REFERRAL_TRIGGER_WORDS})\b[^\.!?\n]*[\.!?]?",
    re.IGNORECASE,
)
# Looser scan to flag (telemetry) even if scrub fails to remove cleanly
_REFERRAL_TRIGGER_RX = re.compile(
    rf"\b(?:{_REFERRAL_TRIGGER_WORDS})\b", re.IGNORECASE,
)


# ── Cure / guarantee language → soften ──────────────────────────────
_CURE_RX = re.compile(
    r"\b(100\s*%|guaranteed?|definitely\s+cure|surely\s+cure|"
    r"pakka\s+thik|guarantee\s+thik|cure\s+ho\s+jayega\s+pakka)\b",
    re.IGNORECASE,
)


# ── Death / longevity leakage ───────────────────────────────────────
_DEATH_RX = re.compile(
    r"\b(death\s+(date|time|year)|kab\s+marenge|kab\s+marungi|"
    r"life\s+span\s+(is|hoga)|umar\s+\d+|"
    r"\d+\s+saal\s+jiyenge|will\s+die\s+(in|by))\b",
    re.IGNORECASE,
)


# ── Engine codes / verdict colours / jargon (same as finance) ───────
_ENGINE_CODES = re.compile(
    r"\b(RED|YELLOW|GREEN|verdict|tier|sub[_-]?flags?|"
    r"composite[_-]?score|dimension[s]?|reliability|"
    r"raw[_-]?score|severity|conflict[_-]?flag|inverted)\b",
    re.IGNORECASE,
)
_CODE_REPLACEMENTS = [
    (re.compile(r"\bRED\b",    re.IGNORECASE), "weak"),
    (re.compile(r"\bGREEN\b",  re.IGNORECASE), "strong"),
    (re.compile(r"\bYELLOW\b", re.IGNORECASE), "mixed"),
    (re.compile(r"\bverdict\b", re.IGNORECASE), "picture"),
    (re.compile(r"\btier\b", re.IGNORECASE), "level"),
    (re.compile(r"\bseverity\b", re.IGNORECASE), "level"),
    (re.compile(r"\b(sub[_-]?flags?|composite[_-]?score|dimensions?|"
                r"reliability|raw[_-]?score|conflict[_-]?flag|inverted)\b",
                re.IGNORECASE), ""),
]

_PLANET_RX = re.compile(
    r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|"
    r"Surya|Chandra|Mangal|Budh|Guru|Brihaspati|Shukra|Shani)\b",
    re.IGNORECASE,
)
_HOUSE_RX = re.compile(
    r"\b(H\s?1[0-2]|H\s?[1-9]|"
    r"(1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th)\s+house|"
    r"house\s+(1[0-2]|[1-9]))\b",
    re.IGNORECASE,
)
_SIGN_RX = re.compile(
    r"\b(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|"
    r"Sagittarius|Capricorn|Aquarius|Pisces|"
    r"Mesh|Vrishabh|Mithun|Kark|Singh|Kanya|Tula|Vrischik|"
    r"Dhanu|Makar|Kumbh|Meen)\b",
    re.IGNORECASE,
)
_DIGNITY_RX = re.compile(
    r"\b(exalted|debilitated|debilitate|retrograde|retro|combust|"
    r"dusthana|dushthana|kendra|trikona|upachaya|parivartana|"
    r"swarashi|moolatrikona|own\s+sign|enemy\s+sign|friend\s+sign)\b",
    re.IGNORECASE,
)
_TECH_REQUEST_RX = re.compile(
    r"\b(why|kyun|kyon|kaise|how|reason|because|technically|"
    r"planet[s]?|graha|house[s]?|sign[s]?|kundli\s+(detail|bata|"
    r"dikhao|me\s+kya)|chart\s+(detail|me\s+kya)|"
    r"explain|samjha[oe]?|deep|detailed?|"
    r"kp|cusp|csl|sub[\s-]?lord|signification|nakshatra)\b",
    re.IGNORECASE,
)
_TIMING_LEAK_RX = re.compile(
    r"\b(20[2-9]\d|in\s+\d+\s+(months?|years?|mahine|saal)|"
    r"by\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b",
    re.IGNORECASE,
)


def _user_asked_for_tech(question: str) -> bool:
    return bool(_TECH_REQUEST_RX.search(question or ""))


def _scrub_runs(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\(\s*\)|\[\s*\]", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"(?m)^[\s,;:\-—]+", "", text)
    text = re.sub(r"(?m)[\s,;:\-—]+$", "", text)
    return text.strip()


def _ensure_doctor_disclaimer(text: str, sensitive_bucket: Optional[str]
                               ) -> Tuple[str, bool]:
    """Append doctor disclaimer + (if sensitive) bucket-specific extra
    line. Returns (text, was_added).
    Idempotent: detects existing 'doctor consult' phrasing — if found,
    we still ensure the canonical wording at end.
    """
    has_doctor = bool(re.search(
        r"doctor\s+(consult|se\s+(milein|baat)|advice|appointment)|"
        r"medical\s+(professional|advice|consultation)",
        text, re.IGNORECASE))
    out = text.rstrip()
    added = False
    # Sensitive-bucket extra (added once, BEFORE doctor line)
    if sensitive_bucket and sensitive_bucket in _SENSITIVE_EXTRA:
        sx = _SENSITIVE_EXTRA[sensitive_bucket]
        # Only add if a near-duplicate isn't already present
        # (rough check on key phrase from each)
        if sx[:30] not in out:
            out = f"{out}\n\n{sx}"
            added = True
    if not has_doctor:
        out = f"{out}\n\n{DOCTOR_DISCLAIMER}"
        added = True
    return out, added


def _ensure_final_line(text: str) -> Tuple[str, bool]:
    # Phase H2.4: locked verdict block ("🎯 Final Verdict / Primary
    # factor / Focus") is the new contract — if present, skip adding
    # any legacy "Final:" line (would otherwise duplicate / mangle).
    if "Final Verdict" in text or "Primary factor:" in text:
        return text, False
    if re.search(r"(?i)\bfinal\s*:", text):
        text = re.sub(r"(?i)([^\n])\s+(final\s*:)", r"\1\n\n\2", text, count=1)
        return text, False
    parts = [p.strip() for p in re.split(r"[.!?\n]+", text) if p.strip()]
    final_line = parts[-1] if parts else "Chart picture upar di hai."
    final_line = re.sub(r"(?i)^final\s*:\s*", "", final_line)
    if len(final_line) > 120:
        final_line = final_line[:117].rsplit(" ", 1)[0] + "..."
    return text.rstrip() + f"\n\nFinal: {final_line}", True


def apply_safety_tail(text: str,
                      sensitive_bucket: Optional[str] = None,
                      add_doctor: bool = False,
                      ) -> Tuple[str, List[str]]:
    """Light-touch safety tail for engine-deterministic DIRECT output.

    Per user policy (Phase H2.1): default-OFF doctor disclaimer.
    Static engine = preventive insight, NOT doctor replacement.
    Doctor mention reserved for WARNING (timing/serious) routes only.

    Always:
      - guarantee a 'Final:' tail (if missing)
    Only when `add_doctor=True` (WARNING path):
      - sensitive-bucket helpline / specialist note
      - mandatory doctor disclaimer line
    """
    flags: List[str] = []
    cleaned = text
    cleaned, added_final = _ensure_final_line(cleaned)
    if added_final:
        flags.append("final_line_added")
    if add_doctor:
        cleaned, added_doc = _ensure_doctor_disclaimer(
            cleaned, sensitive_bucket)
        if added_doc:
            flags.append("doctor_disclaimer_added")
    return cleaned, flags


def validate_health_llm_output(
    text: str,
    user_question: str = "",
    sensitive_bucket: Optional[str] = None,
    allowed_yogas: Optional[List[str]] = None,
    direct_fallback_text: str = "",
    add_doctor: bool = False,
    allow_vedic_terms: bool = False,
) -> Tuple[str, List[str], str]:
    """Clean + validate LLM health output.

    Returns (cleaned_text, flags, action).
    Action: 'none' | 'soft_clean' | 'hard_clean' | 'fallback'.

    Per Phase H2.1 user policy: doctor disclaimer + sensitive-bucket
    extras gated behind `add_doctor` flag (default OFF). Only WARNING
    routes pass `add_doctor=True`. Diagnosis-ban / fear-softener /
    death-strip / cure-softener / hallucinated-yoga / disease-name
    scrubbing remain ALWAYS-ON regardless of flag.

    Phase H2.7.1: `allow_vedic_terms=True` (passed by simple-mode H2.7
    Path B+ caller) keeps planet names, house numbers, sign names, and
    dignity words intact — these are user-friendly Vedic vocabulary the
    LLM is explicitly instructed to use for attribution. The H2.2-era
    auto-strip remains ON for any caller that doesn't opt-in (back-
    compat: structured-mode, marriage, etc. behave identically).
    Disease-name / doctor / fear / death / cure / fake-yoga scrubs are
    always ON regardless.
    """
    if not isinstance(text, str) or not text.strip():
        fb = direct_fallback_text or "Engine truth upar di hai."
        if add_doctor:
            fb, _ = _ensure_doctor_disclaimer(fb, sensitive_bucket)
        return (fb, ["empty_llm_output"], "fallback")

    flags: List[str] = []
    cleaned = text
    # H2.7.1: opt-in flag overrides per-question heuristic. Simple-mode
    # always permits Vedic vocab (planet/house/sign/dignity).
    user_wants_tech = allow_vedic_terms or _user_asked_for_tech(user_question)

    # 1) Engine codes — ALWAYS strip / replace
    if _ENGINE_CODES.search(cleaned):
        flags.append("engine_codes")
        for rx, repl in _CODE_REPLACEMENTS:
            cleaned = rx.sub(repl, cleaned)

    # 2) Disease-name strip (HEALTH-specific HARD rule, ALWAYS on)
    for rx, repl in _DISEASE_RX_LIST:
        if rx.search(cleaned):
            flags.append("disease_name_stripped")
            cleaned = rx.sub(repl, cleaned)

    # 3) Diagnosis-assert phrasing → risk language (HARD rule)
    for rx, repl in _DIAGNOSIS_ASSERT_PATTERNS:
        if rx.search(cleaned):
            flags.append("diagnosis_assert_softened")
            cleaned = rx.sub(repl, cleaned)

    # 4) Fear-amplification words → calm
    for rx, repl in _FEAR_RX_LIST:
        if rx.search(cleaned):
            flags.append("fear_softened")
            cleaned = rx.sub(repl, cleaned)

    # 5) Cure-guarantee language → softened
    if _CURE_RX.search(cleaned):
        flags.append("cure_guarantee_softened")
        cleaned = _CURE_RX.sub("supportive indication", cleaned)

    # 6) Death / longevity leakage → strip
    if _DEATH_RX.search(cleaned):
        flags.append("death_prediction_stripped")
        cleaned = _DEATH_RX.sub("[longevity prediction nahi]", cleaned)

    # 7) Planet names — strip unless user asked for tech
    if _PLANET_RX.search(cleaned):
        flags.append("planet_names" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _PLANET_RX.sub("", cleaned)

    # 8) House refs — strip unless tech requested
    if _HOUSE_RX.search(cleaned):
        flags.append("house_refs" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _HOUSE_RX.sub("", cleaned)

    # 9) Signs — strip unless tech requested
    if _SIGN_RX.search(cleaned):
        flags.append("sign_names" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _SIGN_RX.sub("", cleaned)

    # 10) Dignity / dusthana — strip unless Vedic terms allowed
    # (H2.7.1: simple-mode keeps "debilitated"/"exalted"/"dusthana" —
    # these are part of the attribution LLM forms from the full pack)
    if _DIGNITY_RX.search(cleaned):
        flags.append("dignity_jargon" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _DIGNITY_RX.sub("", cleaned)

    # 11) Timing leaks (years / month names) — strip (non-timing engine)
    if _TIMING_LEAK_RX.search(cleaned):
        flags.append("timing_leak")
        cleaned = _TIMING_LEAK_RX.sub("[timing alag engine ka]", cleaned)

    # 11.5) Referral / doctor-mention scrub (Phase H2.2 tone-guard)
    #       Active only when add_doctor=False. Drops sentences that
    #       suggest doctor / professional / therapist / expert / etc.
    #       — these would silently bypass the H2.1 default-OFF doctor
    #       policy. WARNING path (add_doctor=True) keeps such language.
    if not add_doctor and _REFERRAL_TRIGGER_RX.search(cleaned):
        flags.append("referral_scrubbed")
        cleaned = _REFERRAL_SENTENCE_RX.sub("", cleaned)
        # Tidy trailing/leading punctuation noise
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
        # Belt-and-suspenders: if any trigger word still remains
        # (e.g. embedded mid-clause), neutralise it inline.
        if _REFERRAL_TRIGGER_RX.search(cleaned):
            cleaned = _REFERRAL_TRIGGER_RX.sub("trusted person", cleaned)
            flags.append("referral_neutralised_inline")

    # 12) Yoga hallucination check (small list — only the 3 we expose)
    if allowed_yogas is not None:
        yoga_mentions = re.findall(
            r"\b(Arishta|Balarishta|Vipreet[\s-]?(?:Recovery|Rajyoga|Raja)|"
            r"Mahapurusha|Gaja[\s-]?Kesari)\b",
            cleaned, flags=re.IGNORECASE,
        )
        norm_allowed = {y.lower().replace("-", "").replace(" ", "")
                        for y in allowed_yogas}
        for y in yoga_mentions:
            ynorm = y.lower().replace("-", "").replace(" ", "")
            if ynorm not in norm_allowed and not any(
                ynorm.startswith(a[:5]) for a in norm_allowed
            ):
                flags.append(f"hallucinated_yoga:{y}")
                cleaned = re.sub(
                    rf"\b{re.escape(y)}\b", "[yoga not in chart]",
                    cleaned, flags=re.IGNORECASE,
                )

    # Scrub leftover whitespace
    cleaned = _scrub_runs(cleaned)

    # 13) Final line
    cleaned, added_final = _ensure_final_line(cleaned)
    if added_final:
        flags.append("final_line_added")

    # 14) Doctor disclaimer (Phase H2.1: gated, default OFF — only WARNING
    #     path opts in via add_doctor=True). Sensitive-bucket extras share
    #     the same gate (they are also doctor-mention by nature).
    if add_doctor:
        cleaned, added_doc = _ensure_doctor_disclaimer(
            cleaned, sensitive_bucket)
        if added_doc:
            flags.append("doctor_disclaimer_added")

    # Decide action
    if not flags:
        action = "none"
    elif flags == ["doctor_disclaimer_added"]:
        # disclaimer-only addition is the baseline path — count as soft
        action = "soft_clean"
    else:
        if len(cleaned) < 60:
            fb = direct_fallback_text or cleaned
            if add_doctor:
                fb, _ = _ensure_doctor_disclaimer(fb, sensitive_bucket)
            return (fb, flags + ["mangled_after_clean"], "fallback")
        hard_flags = {"disease_name_stripped", "diagnosis_assert_softened",
                       "death_prediction_stripped", "engine_codes",
                       "cure_guarantee_softened", "timing_leak",
                       "dignity_jargon", "referral_scrubbed",
                       "referral_neutralised_inline"}
        if any(f in hard_flags or f.startswith("hallucinated_yoga")
               for f in flags):
            action = "hard_clean"
        else:
            action = "soft_clean"

    return cleaned, flags, action
