"""
Post-LLM human-quality gate — repetition, hedge words, placement dumps, therapy filler.
"""
from __future__ import annotations

import re
from typing import Any

HEDGE_PHRASES = (
    "may ",
    "might ",
    "potentially",
    "it is important to note",
    "it is worth noting",
    "both partners will benefit",
    "mutual understanding",
    "with effort",
    "navigate challenges",
    "healthy communication",
    "open communication",
    "emotional pacing",
    "underlying tension",
    "key takeaway",
    "what to do next",
    "dynamics between",
    "leverage ",
    "testament to",
)

THERAPY_SYMMETRY = (
    "both of you should",
    "both partners should",
    "each partner should",
    "you both need to",
    "dono ko ",
    "दोनों को ",
)

THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "communication": (
        "communication", "reply", "text", "message", "whatsapp", "silent", "chup", "bolna",
    ),
    "timing": (
        "timing", "fast", "slow", "pace", "delay", "jaldi", "wait", "space",
    ),
    "trust": (
        "trust", "loyal", "consistency", "doubt", "bharosa", "faith",
    ),
    "conflict": (
        "ultimatum", "fight", "argument", "gussa", "conflict", "jhagda",
    ),
    "commitment": (
        "marriage", "shaadi", "commitment", "long-term",
    ),
}

_PLACEMENT_DUMP_RE = re.compile(
    r"(?:moon|venus|mercury|mars|jupiter|saturn)\s+(?:in\s+)?[a-z]+",
    re.IGNORECASE,
)
_SCORE_PERCENT_RE = re.compile(r"\b\d{1,3}\s*(?:%|/100|out of 100)\b", re.IGNORECASE)


def _lower(text: str) -> str:
    return (text or "").lower()


def count_theme_hits(text: str, theme: str) -> int:
    blob = _lower(text)
    words = THEME_KEYWORDS.get(theme, ())
    return sum(blob.count(w) for w in words)


def count_all_themes(text: str) -> dict[str, int]:
    return {theme: count_theme_hits(text, theme) for theme in THEME_KEYWORDS}


def count_hedge_hits(text: str) -> int:
    blob = _lower(text)
    return sum(1 for p in HEDGE_PHRASES if p in blob)


def has_therapy_symmetry(text: str) -> bool:
    blob = _lower(text)
    return any(p in blob for p in THERAPY_SYMMETRY)


def has_placement_dump(text: str) -> bool:
    return len(_PLACEMENT_DUMP_RE.findall(text or "")) >= 3


def count_score_mentions(text: str) -> int:
    return len(_SCORE_PERCENT_RE.findall(text or ""))


def has_human_mirror(text: str, p1_name: str = "") -> bool:
    blob = _lower(text)
    markers = (
        "you feel", "you read", "your mind", "aapko lagta", "aap padhte",
        "tum padhte", "dimag", "galat story", "wrong story", "lagta hai ignore",
        "feel ignored", "feel shut out", "sochte hain", "पढ़ते हैं",
    )
    if any(m in blob for m in markers):
        return True
    if p1_name and p1_name.lower() in blob:
        return True
    return False


def check_section_human_quality(
    text: str,
    lang: str,
    *,
    section_key: str = "",
    forbidden_themes: list[str] | None = None,
    prior_text: str = "",
    p1_name: str = "",
    min_words: int = 40,
) -> str | None:
    """
    Return rejection reason for LLM retry, or None if OK.
    """
    body = (text or "").strip()
    if not body:
        return "empty_body"
    if len(body.split()) < min_words:
        return "too_short"

    hedges = count_hedge_hits(body)
    if hedges >= 2:
        return f"hedge_phrases_{hedges}"

    if has_therapy_symmetry(body):
        return "therapy_symmetry_both_partners"

    if has_placement_dump(body):
        return "placement_list_dump"

    scores = count_score_mentions(body)
    if scores > 2:
        return f"too_many_scores_{scores}"

    forbid = forbidden_themes or []
    if forbid:
        blob = _lower(body)
        for w in forbid:
            needle = w.lower().strip()
            if needle and blob.count(needle) >= 3:
                return f"forbidden_word_{needle}"

    if prior_text:
        prior_themes = count_all_themes(prior_text)
        body_themes = count_all_themes(body)
        for theme, prior_hits in prior_themes.items():
            if prior_hits >= 2 and body_themes.get(theme, 0) >= 2:
                return f"repeats_prior_theme_{theme}"

    if section_key in ("verdict", "breakup", "blueprint_reality", "moon_sync"):
        if not has_human_mirror(body, p1_name):
            return "missing_mirror_scene"

    return None


def human_quality_retry_note(reason: str, lang: str) -> str:
    lane = (lang or "en").strip().lower()
    if lane == "hn":
        return (
            f"RETRY: human narrative gate rejected ({reason}). "
            "Real-life scene se shuru karo. Planet list mat do — combined story use karo. "
            "Wrong story mirror karo. Hedge words / 'both partners should' mat likho. "
            "p1-first voice — reader relate kare."
        )
    if lane == "hi":
        return (
            f"RETRY: human narrative gate rejected ({reason}). "
            "वास्तविक दृश्य से शुरू करें। ग्रह सूची नहीं — संयुक्त कथा। "
            "गलत कहानी दर्शाएँ। दोनों को सलाह नहीं — p1-प्रथम स्वर।"
        )
    return (
        f"RETRY: human narrative gate rejected ({reason}). "
        "Open with a real-life scene. No planet list — use the combined chart story. "
        "Mirror the wrong-story pair. No hedge words or 'both partners should'. "
        "p1-first voice so the reader relates."
    )


def audit_report_narrative(pro: dict[str, Any], lang: str = "en") -> dict[str, Any]:
    """Post-assembly audit — warnings only, never raises."""
    warnings: list[str] = []
    chunks: list[str] = []

    verdict = str(pro.get("verdict") or "").strip()
    if verdict:
        chunks.append(verdict)
    for row in pro.get("deep_analysis") or []:
        if isinstance(row, dict):
            chunks.append(str(row.get("explanation") or row.get("body") or ""))
    for key in (
        "blueprint_reality",
        "moon_sync_narrative",
        "remedies_action_narrative",
        "red_flags_narrative",
        "dasha_narrative",
        "roadmap_narrative",
        "harmony",
    ):
        t = str(pro.get(key) or "").strip()
        if t:
            chunks.append(t)
    for ch in pro.get("chapters") or []:
        if isinstance(ch, dict):
            chunks.append(str(ch.get("chapter_body") or ch.get("full_read") or ""))

    full = "\n".join(chunks)
    theme_totals = count_all_themes(full)
    for theme, total in theme_totals.items():
        if total >= 8:
            warnings.append(f"overused_theme:{theme}:{total}")

    if count_hedge_hits(full) >= 5:
        warnings.append("excess_hedge_phrases")

    if count_score_mentions(full) > 6:
        warnings.append("excess_score_mentions")

    return {"warnings": warnings, "theme_totals": theme_totals}
