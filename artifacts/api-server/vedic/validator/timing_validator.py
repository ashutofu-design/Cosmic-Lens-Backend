"""
Sprint 51 — TIMING VALIDATOR (anti-hallucination hard layer)

Enforces the absolute rule: AI has ZERO permission to invent dates,
months, years, or dasha-windows in any "kab hoga" (when) question.

Public API:
  is_timing_question(text)            → bool
  detect_question_topic(text)         → topic string or None
  extract_date_tokens(text)           → list of date-like substrings
  validate_ai_response(question, ai_text, engine_facts) → ValidationResult
  scrub_invented_dates(ai_text, engine_facts) → cleaned text

Strategy:
  1. Detect timing question via keyword router (Hindi+English)
  2. Extract every date-token from AI response (years, months, dashas)
  3. Cross-check each token exists VERBATIM in engine_facts
  4. If any unauthorised token → REJECT (validator returns ok=False)
  5. scrub mode strips invented dates and replaces with engine window
"""
from __future__ import annotations
import re
from typing import Any
from dataclasses import dataclass, field

# ── Detection -----------------------------------------------------------------
TIMING_CUES_EN = [
    "when ", "when will", "how soon", "how long", "by when",
    "next time", "what year", "what month", "which month", "which year",
    "timing of", "date of", "year of",
]
TIMING_CUES_HI = [
    "kab", "kab hoga", "kab hogi", "kab hogi shaadi", "kab milega",
    "kab milegi", "kab tak", "kis saal", "kis mahine", "konse saal",
    "kaunse mahine", "kitne saal me", "kitne saal mein", "kitne din",
]

TOPIC_KEYWORDS = {
    "marriage": ["marriage","shaadi","shadi","wedding","sagai","engagement","life partner"],
    "child":    ["child","baby","santaan","santan","bachcha","pregnancy","conceive"],
    "career":   ["career","job","naukri","kaam","work","employment"],
    "promotion":["promotion","raise","increment","appraisal","bigger role"],
    "wealth":   ["wealth","money","paisa","dhan","income","rich","amir"],
    "foreign":  ["foreign","videsh","abroad","overseas","nri","visa","settle abroad"],
    "property": ["property","ghar","makaan","house","flat","land","plot","real-estate","real estate"],
    "health":   ["health","swasthya","disease","illness","bimari"],
    "spiritual":["spiritual","moksha","awakening","enlightenment","sanyas"],
}


def is_timing_question(text: str) -> bool:
    """P1.2.8: Delegates to unified question_type gate (single source
    of truth across the whole codebase). Killswitch UNIFIED_QTYPE_GATE=off
    reverts to the legacy substring body byte-identically.
    """
    try:
        from question_type import classify_question_type, _gate_enabled
        if _gate_enabled():
            return classify_question_type(text) == "TIMING"
    except Exception:
        pass
    if not text: return False
    t = text.lower()
    for c in TIMING_CUES_EN + TIMING_CUES_HI:
        if c in t: return True
    return False


def detect_question_topic(text: str) -> str | None:
    if not text: return None
    t = text.lower()
    for topic, kws in TOPIC_KEYWORDS.items():
        for kw in kws:
            if kw in t: return topic
    return None


# ── Date extraction -----------------------------------------------------------
MONTHS_EN = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
MONTHS_HI = r"(?:janu|farv|maa?rch|aprai|aprail|apreil|mai|jun|jul|agas|setem|sitamb|aktoo|nove|disam)[a-z]*"
YEAR_RE   = re.compile(r"\b(19[5-9]\d|20[0-9]\d|21[0-5]\d)\b")  # 1950-2159
MONTH_RE  = re.compile(rf"\b(?:{MONTHS_EN}|{MONTHS_HI})\s*[-/ ]?\s*(?:19|20|21)?\d{{2,4}}\b", re.I)
WINDOW_RE = re.compile(
    rf"\b(?:{MONTHS_EN})\s*\d{{4}}\s*(?:to|-|–|se|tak)\s*(?:{MONTHS_EN})\s*\d{{4}}\b", re.I)
DASHA_RE  = re.compile(r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)"
                       r"[\s-]*(?:MD|AD|PD|maha|antar|pratyantar|dasha)[\s\-]?"
                       r"(?:[\s-]*(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu))?", re.I)
AGE_RE    = re.compile(r"\b(?:age|umar|umra)\s+(?:of\s+)?(\d{1,2})\b", re.I)
# ISO-style or DD/MM/YYYY day-precise dates that the AI tends to invent
# when the engine only emitted month-year resolution. We scrub these
# unless the EXACT day-precise date appears in engine_facts.
ISO_DATE_RE = re.compile(
    r"\b("
    r"(?:19|20|21)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])"
    r"|"
    r"(?:0?[1-9]|[12]\d|3[01])[-/.](?:0?[1-9]|1[0-2])[-/.](?:19|20|21)\d{2}"
    r")\b"
)


def extract_date_tokens(text: str) -> dict[str, list[str]]:
    if not text: return {"years":[], "month_year":[], "windows":[],
                         "dashas":[], "ages":[], "iso_dates":[]}
    return {
        "years":      YEAR_RE.findall(text),
        "month_year": MONTH_RE.findall(text),
        "windows":    WINDOW_RE.findall(text),
        "dashas":     [m.group(0) for m in DASHA_RE.finditer(text)],
        "ages":       AGE_RE.findall(text),
        "iso_dates":  [m.group(0) for m in ISO_DATE_RE.finditer(text)],
    }


# ── Validation result ---------------------------------------------------------
@dataclass
class ValidationResult:
    ok: bool = True
    is_timing: bool = False
    topic: str | None = None
    invented_tokens: list[str] = field(default_factory=list)
    authorised_tokens: list[str] = field(default_factory=list)
    rejection_reason: str = ""
    severity: str = "INFO"   # INFO | WARN | REJECT

    def to_dict(self) -> dict:
        return {
            "ok": self.ok, "is_timing": self.is_timing, "topic": self.topic,
            "invented_tokens": self.invented_tokens,
            "authorised_tokens": self.authorised_tokens,
            "rejection_reason": self.rejection_reason,
            "severity": self.severity,
        }


def validate_ai_response(question: str, ai_text: str,
                         engine_facts: str = "") -> ValidationResult:
    """
    Hard-validate that AI did not invent any timing token absent from engine_facts.
    For non-timing questions, returns ok=True with severity=INFO.
    """
    res = ValidationResult()
    res.is_timing = is_timing_question(question)
    res.topic = detect_question_topic(question)

    if not res.is_timing:
        return res  # opinion question — validator passes

    if not ai_text:
        res.ok = False; res.severity = "REJECT"
        res.rejection_reason = "Empty AI response on timing question"
        return res

    tokens = extract_date_tokens(ai_text)
    facts_lower = (engine_facts or "").lower()

    invented, authorised = [], []
    # Years — must appear in engine facts
    for y in tokens["years"]:
        (authorised if y in (engine_facts or "") else invented).append(y)
    # Month-year combos
    for my in tokens["month_year"]:
        (authorised if my.lower() in facts_lower else invented).append(my)
    # Windows
    for w in tokens["windows"]:
        (authorised if w.lower() in facts_lower else invented).append(w)
    # Dashas — at least the MD-AD pair must appear in engine facts
    for d in tokens["dashas"]:
        (authorised if d.lower() in facts_lower else invented).append(d)
    # ISO / DD-MM day-precise dates — must appear VERBATIM in engine facts.
    # Engines emit month-year resolution by default, so any day-precise
    # date the AI prints is almost always invented.
    for iso in tokens["iso_dates"]:
        (authorised if iso.lower() in facts_lower else invented).append(iso)

    res.authorised_tokens = authorised
    res.invented_tokens   = invented

    if invented:
        res.ok = False
        res.severity = "REJECT"
        res.rejection_reason = (
            f"Timing question — AI invented {len(invented)} unauthorised "
            f"date/dasha tokens not present in engine facts: "
            f"{invented[:5]}{'...' if len(invented)>5 else ''}"
        )
    else:
        res.severity = "INFO"
    return res


# ── Scrubbing ----------------------------------------------------------------
def scrub_invented_dates(ai_text: str, engine_facts: str = "",
                         engine_window: str = "") -> str:
    """
    Replace invented year/month tokens with the engine's authorised window.
    If engine_window is empty, replace with '[engine: window pending]'.
    """
    if not ai_text: return ai_text
    facts_lower = (engine_facts or "").lower()
    placeholder = engine_window or "[engine: window pending]"

    def _replace_year(m: re.Match) -> str:
        return m.group(0) if m.group(0) in (engine_facts or "") else placeholder
    def _replace_month(m: re.Match) -> str:
        return m.group(0) if m.group(0).lower() in facts_lower else placeholder
    # Planet-aware dasha replacer: an exact substring match is the
    # happy path, but if the AI used a generic phrasing
    # ("Saturn dasha" / "Saturn MD") for a planet that the engine
    # facts authoritatively place in SOME dasha role
    # ("Saturn Mahadasha" / "Saturn Antardasha" / "Saturn AD" / etc.),
    # we accept it. This avoids over-scrubbing legitimate references
    # to engine-cited dashas that the narrator phrased loosely.
    _PLANETS_RX = re.compile(
        r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b", re.I)
    # A planet is "authorised in a dasha role" iff a string of the form
    # "<Planet> [optional whitespace/dash/slash/connector word] <role-token>"
    # appears in engine_facts, with NO OTHER planet name between the
    # planet and its role token. This prevents false positives like
    # "Mars aspects 10th house. Saturn Mahadasha begins..."
    _DASHA_ROLE_RX = re.compile(
        r"\b(?:mahadasha|antardasha|pratyantardasha|maha|antar|pratyantar"
        r"|md|ad|pd)\b", re.I)
    def _planet_in_authorised_dasha(planet: str) -> bool:
        """Does the engine cite this planet IMMEDIATELY in a dasha role?"""
        p = planet.lower()
        if not p: return False
        # Find every occurrence of the planet name as a whole word.
        for pm in re.finditer(rf"\b{re.escape(p)}\b", facts_lower):
            tail = facts_lower[pm.end(): pm.end()+30]  # short look-ahead
            # Must be immediately followed (within 30 chars) by a role
            # token, AND no other planet name between planet and role.
            rm = _DASHA_ROLE_RX.search(tail)
            if not rm:
                continue
            between = tail[:rm.start()]
            other_planet = re.search(
                r"\b(sun|moon|mars|mercury|jupiter|venus|saturn|rahu|ketu)\b",
                between)
            if other_planet:
                continue
            return True
        return False
    def _replace_dasha(m: re.Match) -> str:
        full = m.group(0)
        if full.lower() in facts_lower:
            return full
        pm = _PLANETS_RX.search(full)
        if pm and _planet_in_authorised_dasha(pm.group(1)):
            return full
        return "[engine: dasha not cited]"

    def _replace_iso(m: re.Match) -> str:
        return m.group(0) if m.group(0).lower() in facts_lower else placeholder

    # Run ISO-date scrub FIRST so we replace whole "2025-07-25" tokens
    # before YEAR_RE has a chance to mangle the embedded year.
    cleaned = ISO_DATE_RE.sub(_replace_iso, ai_text)
    cleaned = YEAR_RE.sub(_replace_year, cleaned)
    cleaned = MONTH_RE.sub(_replace_month, cleaned)
    cleaned = DASHA_RE.sub(_replace_dasha, cleaned)
    return cleaned


# ── End-to-end enforcement helper --------------------------------------------
def enforce_timing_lock(question: str, ai_text: str, engine_facts: str,
                        engine_window: str = "") -> dict[str, Any]:
    """
    Single-call wrapper. Use in openai_helper.py after AI generation.
      result = enforce_timing_lock(q, ai_text, locked_facts, engine_window)
      if not result['ok']: return result['safe_text']
    """
    val = validate_ai_response(question, ai_text, engine_facts)
    if val.ok or not val.is_timing:
        return {"ok": True, "safe_text": ai_text, "validation": val.to_dict()}

    # Scrub & return safe text + rejection reason for logging.
    # The engine_window string typically arrives as the engine's own
    # heading line (e.g. "▸ Current Career window: Jul 2025 → Jun 2026
    # — Rahu Mahadasha / Sun Antardasha"). Strip the leading bullet +
    # "<X> window:" prefix so the user-facing caption reads cleanly.
    cleaned = scrub_invented_dates(ai_text, engine_facts, engine_window)
    pretty_window = (engine_window or "").strip()
    if pretty_window:
        # Drop common engine bullet glyphs.
        for glyph in ("▸ ", "• ", "▶ ", "▪ ", "→ "):
            if pretty_window.startswith(glyph):
                pretty_window = pretty_window[len(glyph):]
                break
        # Drop "<topic> window:" / "<topic>-window:" heading prefix.
        pretty_window = re.sub(
            r"^[A-Za-z][A-Za-z\- ]*?window\s*:\s*",
            "",
            pretty_window,
            flags=re.IGNORECASE,
        )
    safe = (
        f"{cleaned}\n\n"
        f"⚐ Note: precise dates ONLY from engine output. "
        f"Authoritative window: {pretty_window or 'engine data insufficient'}"
    )
    return {"ok": False, "safe_text": safe, "validation": val.to_dict()}
