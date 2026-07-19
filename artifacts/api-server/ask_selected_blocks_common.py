"""Global helpers for LLM Selected JSON Blocks — every domain (finance/health/MR/travel).

Rules (user contract):
1. Selection follows the Question DNA — jo user ne maanga wahi blocks aayen.
2. "Sab chahiye" (full/complete analysis) → give the FULL general pack, not a narrow focus.
3. Dasha asked → dasha block must be in the selected set (never invented by LLM).
4. Coverage check flags misses in the debugger (focus mismatch / empty / dasha missing).
"""

from __future__ import annotations

import re
from typing import Any

# "Give me everything" — full chart study / complete analysis asks.
# Deliberately tight: needs an explicit ALL-word + object ("sab kuch batao",
# "full analysis", "puri kundli dekho"). A topic-specific "detailed study of
# wealth" must NOT land here — DNA label wins first in every _detect_focus.
_WANTS_ALL_RX = re.compile(
    r"(?ix)\b("
    r"sab\s*(?:kuch|kuchh)|sabkuch|sab\s*(?:bata|batao|dekho|check\s*karo)|"
    r"(?:full|complete|pura|poora|puri|poori|detailed|in[-\s]?depth)\s*"
    r"(?:analysis|study|report|chart|kundli|detail|overview)|"
    r"everything|a\s*to\s*z|"
    r"detail\s*(?:me|mein|se)\s*(?:sab|pura|poora|batao)"
    r")\b"
)

# User explicitly asked to consider dasha (even without a "kab/when").
_WANTS_DASHA_RX = re.compile(
    r"(?ix)\b("
    r"dasha|dasa|antardasha|antar\s*dasha|mahadasha|maha\s*dasha|"
    r"pratyantar|vimshottari|dasha\s*period|dasha\s*bhi|dasha\s*dekh|"
    r"period\s*ke\s*hisaab|time\s*period"
    r")\b|(?:दशा|महादशा|अंतर्दशा)"
)

_META_TEXT_KEYS = ("intent", "user_wants", "normalized_question", "question_summary")


def _meta_texts(meta: dict[str, Any] | None) -> list[str]:
    if not isinstance(meta, dict):
        return []
    out: list[str] = []
    for key in _META_TEXT_KEYS:
        val = meta.get(key)
        if isinstance(val, str) and val.strip():
            out.append(val)
    return out


def question_wants_everything(question: str, meta: dict[str, Any] | None = None) -> bool:
    """True when the user asks for a full/complete study — serve the whole pack."""
    for text in [question or ""] + _meta_texts(meta):
        if text and _WANTS_ALL_RX.search(text):
            return True
    return False


def question_wants_dasha(question: str, meta: dict[str, Any] | None = None) -> bool:
    """True when the user explicitly asks for dasha context."""
    for text in [question or ""] + _meta_texts(meta):
        if text and _WANTS_DASHA_RX.search(text):
            return True
    return False


def dasha_blocks_from_pack(
    pack: dict[str, Any] | None,
    *,
    focus: str = "",
) -> list[dict[str, Any]]:
    """Selected-blocks rows from a `dasha_timing_compact` pack (real dasha, no invention)."""
    if not isinstance(pack, dict):
        return []
    out: list[dict[str, Any]] = []
    cur = pack.get("current")
    if isinstance(cur, dict) and (cur.get("md") or cur.get("ad")):
        parts = [str(cur.get(k) or "") for k in ("md", "ad", "pd") if cur.get(k)]
        win = str(cur.get("window") or "").strip()
        out.append({
            "id": "dasha.current",
            "label": "Dasha · current (running NOW)",
            "why": f"User asked dasha — focus={focus or 'timing'}",
            "detail": " → ".join(parts) + (f" · {win}" if win else ""),
            "priority": 88,
            "role": "support",
        })
    for i, w in enumerate((pack.get("top_windows") or [])[:3]):
        if not isinstance(w, dict):
            continue
        parts = [str(w.get(k) or "") for k in ("md", "ad", "pd") if w.get(k)]
        win = str(w.get("window") or "").strip()
        out.append({
            "id": f"dasha.window.{i}",
            "label": "Dasha · upcoming window",
            "why": str(w.get("why") or "sensitive lords active"),
            "detail": " → ".join(parts) + (f" · {win}" if win else ""),
            "priority": 62,
            "role": "support",
        })
    return out


# ── DNA-driven block boost (global — every domain) ──────────────────────────
# Question + DNA (bucket/intent/user_wants) me jo planets, houses aur topic
# words hain, unse match karne wale blocks ko top pe lao. Regex focus akela
# kabhi kabhi galat pick karta tha — yeh layer selection ko question se
# directly bind karti hai.

_PLANET_ALIASES: dict[str, str] = {
    "sun": "Sun", "surya": "Sun", "ravi": "Sun",
    "moon": "Moon", "chandra": "Moon", "chandrama": "Moon",
    "mars": "Mars", "mangal": "Mars", "kuja": "Mars",
    "mercury": "Mercury", "budh": "Mercury", "budha": "Mercury",
    "jupiter": "Jupiter", "guru": "Jupiter", "brihaspati": "Jupiter",
    "venus": "Venus", "shukra": "Venus",
    "saturn": "Saturn", "shani": "Saturn",
    "rahu": "Rahu", "ketu": "Ketu",
}
_PLANET_ALIAS_RX = re.compile(
    r"(?i)\b(" + "|".join(sorted(_PLANET_ALIASES, key=len, reverse=True)) + r")\b"
)

_HOUSE_RX = re.compile(
    r"(?ix)\b(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:house|bhav|bhaav|ghar)\b"
)
_HOUSE_ORDINAL = {
    "pehla": 1, "pehle": 1, "first": 1, "lagna": 1,
    "doosra": 2, "dusra": 2, "second": 2,
    "teesra": 3, "tisra": 3, "third": 3,
    "chautha": 4, "fourth": 4,
    "paanchva": 5, "pancham": 5, "fifth": 5,
    "chhatha": 6, "sixth": 6,
    "saatva": 7, "saptam": 7, "seventh": 7,
    "aathva": 8, "ashtam": 8, "eighth": 8,
    "nauva": 9, "navam": 9, "ninth": 9,
    "dasva": 10, "dasham": 10, "dasam": 10, "tenth": 10,
    "gyarahva": 11, "ekadash": 11, "eleventh": 11,
    "barahva": 12, "dwadash": 12, "twelfth": 12,
}

# Filler words that must never count as topic-match signal.
_SIGNAL_STOPWORDS = frozenset({
    "user", "wants", "want", "know", "detail", "detailed", "details", "study",
    "analysis", "analyse", "analyze", "chart", "charts", "kundli", "kundali",
    "please", "batao", "bataye", "bataiye", "dekho", "dekhe", "karo", "karke",
    "kare", "karna", "mera", "mere", "meri", "mujhe", "aap", "apna", "apne",
    "will", "with", "from", "into", "about", "what", "when", "which", "whether",
    "kaisa", "kaise", "kaisi", "hoga", "hogi", "honge", "chahiye", "specific",
    "question", "answer", "based", "focus", "focusing", "perspective",
    "including", "impact", "periods", "period", "their", "them", "self",
    "general", "engine", "make", "like", "life", "your", "also", "regarding",
})


def _mentioned_planets(question: str, meta: dict[str, Any] | None = None) -> list[str]:
    """Canonical planet names the user (or DNA intent) explicitly mentioned."""
    found: list[str] = []
    for text in [question or ""] + _meta_texts(meta):
        for m in _PLANET_ALIAS_RX.finditer(text or ""):
            canon = _PLANET_ALIASES.get((m.group(1) or "").lower())
            if canon and canon not in found:
                found.append(canon)
    return found


def _mentioned_houses(question: str, meta: dict[str, Any] | None = None) -> list[int]:
    """House numbers the user (or DNA intent) explicitly mentioned (1..12)."""
    found: list[int] = []
    for text in [question or ""] + _meta_texts(meta):
        low = (text or "").lower()
        for m in _HOUSE_RX.finditer(low):
            try:
                h = int(m.group(1))
            except (TypeError, ValueError):
                continue
            if 1 <= h <= 12 and h not in found:
                found.append(h)
        for word, h in _HOUSE_ORDINAL.items():
            if word in low and re.search(rf"\b{word}\b.{{0,12}}(house|bhav|bhaav|ghar)", low):
                if h not in found:
                    found.append(h)
    return found


def _dna_signal_tokens(question: str, meta: dict[str, Any] | None = None) -> set[str]:
    """Topic words from question + DNA bucket/intent/user_wants (stopwords out)."""
    texts = [question or ""] + _meta_texts(meta)
    if isinstance(meta, dict):
        for key in ("bucket", "routing_label", "archetype"):
            val = meta.get(key)
            if isinstance(val, str) and val.strip():
                texts.append(val.replace("_", " "))
    tokens: set[str] = set()
    for t in texts:
        for w in re.findall(r"[a-z]+", (t or "").lower()):
            if len(w) >= 4 and w not in _SIGNAL_STOPWORDS:
                tokens.add(w)
    return tokens


def dna_boost_selected_blocks(
    question: str,
    blocks: list[dict[str, Any]],
    *,
    meta: dict[str, Any] | None = None,
    pack: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Re-rank blocks so question/DNA-matched facts land on top. Global for all domains.

    Boosts (stack):
    - +30  block mentions a planet the user named (shani/saturn/venus...)
    - +25  block is the lord/planet of a house the user named (7th house / saptam bhav)
    - +6/token (max +18) block text overlaps DNA bucket/intent/user_wants words
    Also guarantees a dasha block when the user asked dasha and the pack has real data.
    Returns (blocks re-sorted + re-ranked, applied-boost notes for the debugger).
    """
    if not isinstance(blocks, list):
        return [], []
    applied: list[str] = []
    planets = _mentioned_planets(question, meta)
    houses = _mentioned_houses(question, meta)
    tokens = _dna_signal_tokens(question, meta)

    for b in blocks:
        if not isinstance(b, dict):
            continue
        bid = str(b.get("id") or "")
        # NOTE: "why" excluded — it carries Focus=<label> on every block, which
        # would give a uniform (useless) boost to the whole set.
        hay = " ".join(
            str(b.get(k) or "") for k in ("id", "label", "detail")
        ).lower()
        boost = 0
        for p in planets:
            if re.search(rf"(?i)\b{p}\b", hay):
                boost += 30
        for h in houses:
            if (
                f".h{h}" in bid.lower()
                or re.search(rf"(?i)\bh{h}\b", hay)
                or f"h{h} lord" in hay
            ):
                boost += 25
        hits = sum(1 for t in tokens if t in hay)
        if hits:
            boost += min(hits * 6, 18)
        if boost:
            b["priority"] = int(b.get("priority") or 0) + boost
            b["why"] = (str(b.get("why") or "").strip() + f" · DNA match +{boost}").strip(" ·")
            applied.append(f"{bid}+{boost}")

    # Dasha guarantee: user asked dasha → real dasha rows must be in the set.
    if isinstance(pack, dict) and question_wants_dasha(question, meta):
        has_dasha = any(
            str(b.get("id") or "").startswith("dasha.")
            for b in blocks
            if isinstance(b, dict)
        )
        if not has_dasha:
            extra = dasha_blocks_from_pack(
                pack.get("dasha_timing_compact")
                if isinstance(pack.get("dasha_timing_compact"), dict)
                else None,
                focus="dna",
            )
            if extra:
                blocks.extend(extra)
                applied.append(f"dasha.inserted x{len(extra)}")

    blocks.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
    for i, b in enumerate(blocks, start=1):
        if isinstance(b, dict):
            b["rank"] = i
    return blocks, applied


def dna_boost_note_lines(applied: list[str]) -> list[str]:
    """Debugger note lines describing which blocks got DNA-match boosts."""
    if not applied:
        return []
    return ["DNA MATCH BOOST → " + ", ".join(applied[:8])]


def coverage_check_selected_blocks(
    question: str,
    *,
    meta: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
    general_focus: str = "",
) -> dict[str, Any]:
    """Did selection give the user what they asked? PASS/FAIL for the debugger.

    Issues:
    - blocks_empty: engine ran but no question-relevant blocks were selected
    - focus_mismatch: DNA routing_label maps to a known focus but a different one was used
    - dasha_missing: user asked dasha but no dasha block and no dasha data in execution
    - wants_all_narrow: user asked for everything but selection stayed narrow
    """
    audit = audit if isinstance(audit, dict) else {}
    meta = meta if isinstance(meta, dict) else {}
    execution = execution if isinstance(execution, dict) else {}
    issues: list[str] = []
    notes: list[str] = []

    focus = str(audit.get("focus") or "").strip().lower()
    blocks = audit.get("expected_blocks") or audit.get("available_blocks") or []

    if execution and not blocks:
        issues.append("blocks_empty — engine execution present but no blocks selected")

    dna_label = str(
        meta.get("routing_label") or meta.get("archetype") or ""
    ).strip().lower()
    if dna_label and focus and dna_label != focus and focus != (general_focus or ""):
        # Only a real miss when the DNA label itself was a known focus that got ignored.
        known = audit.get("known_focuses")
        if not isinstance(known, (list, tuple)) or dna_label in [
            str(k).strip().lower() for k in known
        ]:
            issues.append(f"focus_mismatch — DNA label={dna_label} but selected focus={focus}")

    if question_wants_dasha(question, meta):
        has_dasha_block = any(
            str(b.get("id") or "").startswith("dasha.")
            for b in blocks
            if isinstance(b, dict)
        )
        has_dasha_data = isinstance(execution.get("dasha_timing_compact"), dict) and (
            (execution.get("dasha_timing_compact") or {}).get("current")
            or (execution.get("dasha_timing_compact") or {}).get("top_windows")
        )
        if not has_dasha_block and not has_dasha_data:
            issues.append(
                "dasha_missing — user asked dasha but no dasha block/data in selection"
            )
        elif has_dasha_block:
            notes.append("dasha block included (real MD/AD/PD, LLM invention blocked)")

    if question_wants_everything(question, meta):
        if general_focus and focus and focus != general_focus:
            if dna_label and dna_label == focus:
                # DNA scoped it to a topic — that wins over the "sab" word.
                notes.append(
                    f"full-study words present but DNA scoped to {focus} — DNA wins"
                )
            else:
                issues.append(
                    f"wants_all_narrow — user asked FULL study but focus stayed {focus}"
                )
        else:
            notes.append("full-study ask → general focus (whole pack) served")

    return {
        "applies": True,
        "passed": not issues,
        "issues": issues,
        "notes": notes,
    }


def coverage_note_lines(coverage: dict[str, Any]) -> list[str]:
    """Human-readable lines for overlap_notes (renders in existing debugger UI)."""
    if not isinstance(coverage, dict) or not coverage.get("applies"):
        return []
    if coverage.get("passed"):
        lines = ["COVERAGE ✅ PASS — selection matches what the user asked"]
    else:
        lines = [
            "COVERAGE ❌ FAIL — " + "; ".join(coverage.get("issues") or ["unknown"])
        ]
    lines.extend(str(n) for n in (coverage.get("notes") or []))
    return lines
