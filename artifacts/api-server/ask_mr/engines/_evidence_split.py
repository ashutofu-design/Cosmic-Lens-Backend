"""Split chart evidence into positive vs negative for balanced LLM narration."""
from __future__ import annotations

import re

_NEGATIVE_RX = re.compile(
    r"(?ix)\b("
    r"love\s+challenge|red\s*flag|affliction|debilitat|enemy[\s-]?sign|enemy\s+territory|"
    r"malefic|dusthana|unstable|inconsistent|delay|cooling|distance|withdraw|ghost|"
    r"fight|separation|betray|dhokha|nodal|combust|weak|cool|seriousness|"
    r"tests?\s+before|inconsistent|validation[\s-]?seeking|secrecy|guilt|"
    r"emotional\s+cooling|impulsive\s+breaks|unclear\s+loyalty|afflicted"
    r")\b"
)

_POSITIVE_RX = re.compile(
    r"(?ix)\b("
    r"true[\s-]?love\s*marker|dharmic|green\s*flag|reconnection\s+yoga|"
    r"exalted|own[\s-]?sign|deep\s+heartfelt|growth[\s-]?oriented|charming|sincere|"
    r"not\s+heavily\s+afflicted|honest\s+growth|positive\s+dating|strong\s+green|"
    r"playful\s+bold|magnetic|blessing|trust\s+and\s+blessing|affectionate\s+sincere"
    r")\b"
)

# House-axis lines with malefics only (no benefic co-tenant) → negative tilt
_MALEFIC_IN_LINE_RX = re.compile(r"(?ix)malefics?\s+in\s+house\s*=\s*\[.+\]")
_BENEFIC_OCCUPANT_RX = re.compile(
    r"(?ix)occupants=\[[^\]]*?\b(Jupiter|Venus|Moon|Mercury)\b"
)


def classify_evidence_line(line: str) -> str:
    """Return 'positive' | 'negative' | 'neutral'."""
    t = (line or "").strip()
    if not t:
        return "neutral"
    low = t.lower()
    if low.startswith("love challenge:") or low.startswith("red flag"):
        return "negative"
    if _POSITIVE_RX.search(t):
        return "positive"
    if "dignity exalted" in low or "dignity own-sign" in low:
        return "positive"
    if _MALEFIC_IN_LINE_RX.search(t) and not _BENEFIC_OCCUPANT_RX.search(t):
        return "negative"
    if _NEGATIVE_RX.search(t):
        return "negative"
    if "dignity debilitated" in low or "dignity enemy" in low:
        return "negative"
    return "neutral"


def split_evidence_polarity(
    lines: list[str] | None,
) -> tuple[list[str], list[str], list[str]]:
    """Return (positive, negative, neutral) — every input line kept in exactly one bucket."""
    pos: list[str] = []
    neg: list[str] = []
    neu: list[str] = []
    for raw in lines or []:
        line = (raw or "").strip()
        if not line:
            continue
        kind = classify_evidence_line(line)
        if kind == "negative":
            neg.append(line)
        elif kind == "positive":
            pos.append(line)
        else:
            neu.append(line)
    return pos, neg, neu


def narrator_balance_instruction(
    positive: list[str],
    negative: list[str],
    *,
    neutral: list[str] | None = None,
) -> str:
    """Tell narrator how strict vs hopeful to be from evidence balance."""
    p, n = len(positive), len(negative)
    neu = len(neutral or [])
    total = p + n + neu
    if total == 0:
        return "BALANCE: no split evidence — use VERDICT only."

    if n >= 3 and n > p:
        return (
            "BALANCE: chart leans challenging — open STRICT/CAUTIOUS. "
            "First line = qualified or mixed (zyada negative). "
            "Name 2–3 negative points; positives only as thin silver lining. "
            "NO pakka guarantee / seedha strong haan."
        )
    if n >= 2 and p >= 2:
        return (
            "BALANCE: MIXED chart — sentence 1 = honest mixed (haan lekin tests/delay/affliction). "
            "Use BOTH positive and negative lists; do not hide Saturn/Venus afflictions."
        )
    if n == 1 and p >= 2:
        return (
            "BALANCE: mostly supportive with one caveat — positive tone OK but "
            "MUST mention the single negative/affliction point."
        )
    if n == 0 and p >= 1:
        return (
            "BALANCE: supportive evidence dominates — positive answer OK; "
            "still avoid absolute guarantee language."
        )
    if n >= 1 and p <= 1:
        return (
            "BALANCE: more affliction than support — cautious tone; "
            "patience/tests/delay emphasis."
        )
    return (
        "BALANCE: weigh both lists — mirror VERDICT; never stronger than evidence."
    )


def format_split_evidence_block(
    lines: list[str] | None,
    *,
    open_chart_qa: bool = False,
) -> list[str]:
    """Build narrator lines: all positive + all negative (+ neutral as chart context)."""
    pos, neg, neu = split_evidence_polarity(lines)
    out: list[str] = []

    if open_chart_qa:
        out.append(
            "D1 CHART EVIDENCE — use question-relevant factors only; "
            "split into positive vs negative:"
        )
    else:
        out.append(
            "CHART EVIDENCE — use ALL listed points that apply (do not invent new ones):"
        )

    out.append(f"POSITIVE EVIDENCE ({len(pos)} points):")
    if pos:
        out.extend(f"+ {e}" for e in pos)
    else:
        out.append("+ (none tagged positive — use neutral chart context carefully)")

    out.append(f"NEGATIVE / AFFLICTION EVIDENCE ({len(neg)} points):")
    if neg:
        out.extend(f"− {e}" for e in neg)
    else:
        out.append("− (none — do not invent afflictions)")

    if neu:
        out.append(f"CHART CONTEXT / NEUTRAL ({len(neu)} points):")
        out.extend(f"• {e}" for e in neu)

    out.append(narrator_balance_instruction(pos, neg, neutral=neu))
    return out
