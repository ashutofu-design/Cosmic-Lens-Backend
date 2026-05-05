"""Post-LLM validator — Phase 2 (trust lock).

LLM ke output me kabhi-kabhi engine jargon, planet names, house numbers,
ya verdict codes leak ho jate hain — even with strict system prompt.
Yeh validator us output ko clean karta hai engine truth se contradict
kiye bina, project rule "no engine jargon unless explicitly asked"
enforce karta hai, aur sab violations telemetry ke liye flag karta hai.

Public:
  validate_finance_llm_output(text, user_question, allowed_yogas)
      -> (cleaned_text, flags_list, action)

Action values:
  - 'none'       — no violations, text unchanged
  - 'soft_clean' — minor strips, text still usable
  - 'hard_clean' — major scrub, may look terse
  - 'fallback'   — text mangled beyond repair, caller should use direct
                   format instead
"""
from __future__ import annotations
import re
from typing import List, Optional, Tuple


# ── Forbidden patterns (high-confidence, hard strip) ────────────────
# Engine verdict codes — never user-facing
_ENGINE_CODES = re.compile(
    r"\b(RED|YELLOW|GREEN|verdict|tier|sub[_-]?flags?|"
    r"composite[_-]?score|dimension[s]?|reliability)\b",
    re.IGNORECASE,
)

# Replacement map for verdict colours so message stays readable
_CODE_REPLACEMENTS = [
    (re.compile(r"\bRED\b",    re.IGNORECASE), "weak"),
    (re.compile(r"\bGREEN\b",  re.IGNORECASE), "strong"),
    (re.compile(r"\bYELLOW\b", re.IGNORECASE), "mixed"),
    (re.compile(r"\bverdict\b", re.IGNORECASE), "picture"),
    (re.compile(r"\btier\b", re.IGNORECASE), "level"),
    (re.compile(r"\b(sub[_-]?flags?|composite[_-]?score|"
                r"dimensions?|reliability)\b", re.IGNORECASE), ""),
]

# Planet names (English + common Hindi). Stripped unless user asked WHY/
# technical detail in their question.
_PLANET_RX = re.compile(
    r"\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|"
    r"Surya|Chandra|Mangal|Budh|Guru|Brihaspati|Shukra|Shani)\b",
    re.IGNORECASE,
)

# House refs: H1..H12, "1st/2nd/.../12th house", "house 1..12"
_HOUSE_RX = re.compile(
    r"\b(H\s?1[0-2]|H\s?[1-9]|"
    r"(1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th)\s+house|"
    r"house\s+(1[0-2]|[1-9]))\b",
    re.IGNORECASE,
)

# Sign names (English + Hindi). Stripped unless user asked.
_SIGN_RX = re.compile(
    r"\b(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|"
    r"Sagittarius|Capricorn|Aquarius|Pisces|"
    r"Mesh|Vrishabh|Mithun|Kark|Singh|Kanya|Tula|Vrischik|"
    r"Dhanu|Makar|Kumbh|Meen)\b",
    re.IGNORECASE,
)

# Dignity / technical terms
_DIGNITY_RX = re.compile(
    r"\b(exalted|debilitated|debilitate|retrograde|retro|combust|"
    r"dusthana|dushthana|kendra|trikona|upachaya|parivartana|"
    r"swarashi|moolatrikona|own\s+sign|enemy\s+sign|friend\s+sign)\b",
    re.IGNORECASE,
)

# Indicators that the user explicitly asked for technical detail —
# in that case we don't strip planet/house/dignity terms.
_TECH_REQUEST_RX = re.compile(
    r"\b(why|kyun|kyon|kaise|how|reason|because|technically|"
    r"planet[s]?|graha|house[s]?|sign[s]?|kundli\s+(detail|bata|"
    r"dikhao|me\s+kya)|chart\s+(detail|me\s+kya)|"
    r"explain|samjha[oe]?|deep|detailed?|"
    # Phase 2.8.80: KP-specific requests unlock CSL/cusp/sub-lord vocab
    r"kp|cusp|csl|sub[\s-]?lord|signification|nakshatra)\b",
    re.IGNORECASE,
)

# Numeric rupee amount predictions — engine policy says NEVER
_RUPEE_AMOUNT_RX = re.compile(
    r"(₹\s?\d|rs\.?\s?\d|rupee[s]?\s?\d|"
    r"\d+\s?(lakh|crore|cr|lac|lakhs|crores))",
    re.IGNORECASE,
)

# Specific date / year predictions (timing leak — non-timing engine)
_TIMING_LEAK_RX = re.compile(
    r"\b(20[2-9]\d|in\s+\d+\s+(months?|years?|mahine|saal)|"
    r"by\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))\b",
    re.IGNORECASE,
)


def _user_asked_for_tech(question: str) -> bool:
    return bool(_TECH_REQUEST_RX.search(question or ""))


def _scrub_runs(text: str) -> str:
    """Clean leftover whitespace / dangling punctuation after strips."""
    # Collapse multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Remove leftover empty parens / brackets
    text = re.sub(r"\(\s*\)|\[\s*\]", "", text)
    # Fix " ," " ." " ;" patterns after strips
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    # Collapse triple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Clean dangling commas/dashes at line starts/ends
    text = re.sub(r"(?m)^[\s,;:\-—]+", "", text)
    text = re.sub(r"(?m)[\s,;:\-—]+$", "", text)
    return text.strip()


def _ensure_final_line(text: str) -> Tuple[str, bool]:
    """Append 'Final: ...' if missing anywhere. Returns (text, was_added).

    Detects 'Final:' / 'final:' both at line-start and mid-text, so we
    don't double-append. If found mid-text, also promotes it to its own
    line for visual clarity.
    """
    if re.search(r"(?i)\bfinal\s*:", text):
        # Already has a Final marker somewhere — promote it to its own
        # line if it's currently inline (no preceding newline).
        text = re.sub(r"(?i)([^\n])\s+(final\s*:)", r"\1\n\n\2", text, count=1)
        return text, False
    parts = [p.strip() for p in re.split(r"[.!?\n]+", text) if p.strip()]
    final_line = parts[-1] if parts else "Chart picture upar di hai."
    # Strip stray "Final:" prefix from last sentence (safety)
    final_line = re.sub(r"(?i)^final\s*:\s*", "", final_line)
    if len(final_line) > 120:
        final_line = final_line[:117].rsplit(" ", 1)[0] + "..."
    return text.rstrip() + f"\n\nFinal: {final_line}", True


def validate_finance_llm_output(
    text: str,
    user_question: str = "",
    allowed_yogas: Optional[List[str]] = None,
    direct_fallback_text: str = "",
) -> Tuple[str, List[str], str]:
    """Clean + validate LLM finance output.

    Returns (cleaned_text, flags, action).

    `direct_fallback_text` is used only if the cleaning leaves the text
    unusable (very short / mostly stripped) — in that case the caller's
    deterministic DIRECT formatter output is returned as-is.
    """
    if not isinstance(text, str) or not text.strip():
        return (direct_fallback_text or "Engine truth upar di hai.",
                ["empty_llm_output"], "fallback")

    flags: List[str] = []
    cleaned = text
    user_wants_tech = _user_asked_for_tech(user_question)

    # 1) Engine codes — ALWAYS strip / replace (highest severity)
    if _ENGINE_CODES.search(cleaned):
        flags.append("engine_codes")
        for rx, repl in _CODE_REPLACEMENTS:
            cleaned = rx.sub(repl, cleaned)

    # 2) Planet names — strip unless user asked for tech detail
    if _PLANET_RX.search(cleaned):
        flags.append("planet_names" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _PLANET_RX.sub("", cleaned)

    # 3) House refs — strip unless user asked for tech detail
    if _HOUSE_RX.search(cleaned):
        flags.append("house_refs" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _HOUSE_RX.sub("", cleaned)

    # 4) Sign names — strip unless user asked
    if _SIGN_RX.search(cleaned):
        flags.append("sign_names" + ("_allowed" if user_wants_tech else ""))
        if not user_wants_tech:
            cleaned = _SIGN_RX.sub("", cleaned)

    # 5) Dignity / dusthana / kendra etc. — always strip (pure jargon)
    if _DIGNITY_RX.search(cleaned):
        flags.append("dignity_jargon")
        cleaned = _DIGNITY_RX.sub("", cleaned)

    # 6) Rupee amount predictions — engine policy violation, ALWAYS scrub
    if _RUPEE_AMOUNT_RX.search(cleaned):
        flags.append("rupee_prediction")
        cleaned = _RUPEE_AMOUNT_RX.sub("[amount predict nahi]", cleaned)

    # 7) Timing leaks — non-timing engine, dates/years should not appear
    if _TIMING_LEAK_RX.search(cleaned):
        flags.append("timing_leak")
        cleaned = _TIMING_LEAK_RX.sub("[timing alag engine ka]", cleaned)

    # 8) Yoga hallucination — LLM mentioned a yoga not in engine list
    if allowed_yogas is not None:
        # Detect generic mentions of common yogas in text
        yoga_mentions = re.findall(
            r"\b(Dhana|Lakshmi|Kubera|Chandra[\s-]?Mangal|"
            r"Gaja[\s-]?Kesari|Adhi|Vipreet[\s-]?Raja|"
            r"Neecha[\s-]?Bhanga|Pancha[\s-]?Mahapurusha|"
            r"Ruchaka|Bhadra|Hamsa|Malavya|Sasa)\b",
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

    # Scrub trailing whitespace / dangling punctuation from strips
    cleaned = _scrub_runs(cleaned)

    # 9) Ensure Final: line exists
    cleaned, added_final = _ensure_final_line(cleaned)
    if added_final:
        flags.append("final_line_added")

    # Decide action level
    if not flags:
        action = "none"
    else:
        # If we stripped so much the result is too short, fall back
        if len(cleaned) < 40:
            return (direct_fallback_text or cleaned,
                    flags + ["mangled_after_clean"], "fallback")
        hard_flags = {"engine_codes", "rupee_prediction", "timing_leak",
                      "dignity_jargon"}
        if any(f in hard_flags or f.startswith("hallucinated_yoga")
               for f in flags):
            action = "hard_clean"
        else:
            action = "soft_clean"

    return cleaned, flags, action
