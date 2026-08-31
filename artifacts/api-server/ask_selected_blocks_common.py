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


_DEFAULT_FOCUS_HOUSES = (1, 10, 7, 9)
_DEFAULT_FOCUS_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


def _execution_substantive(execution: dict[str, Any]) -> bool:
    if not isinstance(execution, dict) or not execution:
        return False
    if execution.get("schema_version") or execution.get("domain"):
        return True
    d1 = execution.get("d1")
    if isinstance(d1, dict) and not d1.get("error"):
        return True
    return bool(
        execution.get("d9")
        or execution.get("dimensions")
        or execution.get("composite_score") is not None
        or execution.get("strength_label")
        or execution.get("afflictions")
    )


def _d1_from_execution(execution: dict[str, Any]) -> dict[str, Any]:
    d1 = execution.get("d1")
    if isinstance(d1, dict) and not d1.get("error"):
        return d1
    return {}


def format_priority_facts_for_llm_common(
    blocks: list[dict[str, Any]],
    *,
    limit: int = 5,
    header: str = "",
) -> str:
    """Compact ranked facts for narrator — weak / question-relevant first."""
    if not blocks:
        return ""
    lines = [
        header
        or "QUESTION_PRIORITY_FACTS (from Engine Execution only — use in this order):",
        "Rules: #1 = main reason + MUST include its natural chart proof in the answer",
        "(planet + house/dignity, e.g. Saturn 6th debilitated). Max 2–3 facts total.",
        "Weak/dignity pressure > exalted support; exalted/strong = support only.",
        "Do not invent planets outside this list; do not dump every fact.",
    ]
    for b in blocks[: max(1, limit)]:
        rank = b.get("rank") or "?"
        role = b.get("role") or "neutral"
        proof_hint = ""
        if rank == 1 or rank == "1":
            proof_hint = " ← CITE THIS as proof"
        detail = b.get("detail") or b.get("why") or ""
        lines.append(
            f"#{rank} [{role}] {b.get('label')}: {detail}{proof_hint}"
        )
    return "\n".join(lines)


def ensure_minimum_selected_blocks(
    blocks: list[dict[str, Any]],
    execution: dict[str, Any] | None,
    *,
    question: str = "",
    focus: str = "",
    domain: str = "",
    focus_houses: tuple[int, ...] | None = None,
    focus_planets: tuple[str, ...] | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """When engine execution exists, always return ≥1 selected block."""
    if blocks:
        return blocks, False
    if not isinstance(execution, dict) or not _execution_substantive(execution):
        return blocks, False

    houses = focus_houses
    planets = focus_planets
    if domain and (not houses or not planets):
        try:
            from ask_unified.specs import get_domain_spec

            spec = get_domain_spec(domain.strip().lower())
            if spec:
                if not houses:
                    houses = tuple(spec.focus_houses[:4])
                if not planets:
                    planets = tuple(
                        p for p in spec.focus_planets if p != "Ascendant"
                    )[:6]
        except Exception:
            pass
    houses = houses or _DEFAULT_FOCUS_HOUSES
    planets = planets or _DEFAULT_FOCUS_PLANETS

    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        bid: str,
        label: str,
        detail: str,
        *,
        priority: int,
        role: str = "neutral",
        why: str = "",
    ) -> None:
        if bid in seen:
            return
        seen.add(bid)
        row: dict[str, Any] = {
            "id": bid,
            "label": label,
            "detail": detail,
            "priority": priority,
            "role": role,
        }
        if why:
            row["why"] = why
        out.append(row)

    why_prefix = f"Focus={focus or domain or 'engine'}; minimum EE fallback"

    for row in dasha_blocks_from_pack(execution, focus=focus):
        if isinstance(row, dict) and row.get("id"):
            add(
                str(row["id"]),
                str(row.get("label") or row["id"]),
                str(row.get("detail") or row.get("why") or ""),
                priority=int(row.get("priority") or 85),
                role=str(row.get("role") or "support"),
                why=str(row.get("why") or why_prefix),
            )

    d1 = _d1_from_execution(execution)
    dims = execution.get("dimensions") or d1.get("dimensions") or {}
    if isinstance(dims, dict):
        for dim_key, row in list(dims.items())[:4]:
            if not isinstance(row, dict):
                continue
            verdict = str(row.get("verdict") or "")
            role = (
                "weak" if verdict == "RED"
                else ("support" if verdict == "GREEN" else "neutral")
            )
            pr = 90 if verdict == "RED" else (70 if verdict == "YELLOW" else 55)
            add(
                f"dim.{dim_key}",
                f"Dimension · {dim_key}",
                f"{verdict} — {row.get('reason') or ''}".strip(" —"),
                priority=pr,
                role=role,
                why=why_prefix,
            )

    asc = d1.get("ascendant") or execution.get("ascendant")
    if asc:
        add("d1.lagna", "D1 · Lagna", str(asc), priority=86, role="neutral", why=why_prefix)

    lords = d1.get("house_lords") if isinstance(d1.get("house_lords"), dict) else {}
    for h in houses:
        st = lords.get(f"h{h}") if isinstance(lords, dict) else None
        if not isinstance(st, dict) or not st.get("lord"):
            continue
        dig = str(st.get("lord_dignity") or "")
        role = (
            "weak"
            if dig in ("debilitated", "enemy") or st.get("lord_in_dusthana")
            else "neutral"
        )
        if dig in ("exalted", "own"):
            role = "support"
        add(
            f"lord.h{h}",
            f"House lord · h{h}",
            (
                f"{st.get('lord')} → H{st.get('lord_house')} · "
                f"{st.get('lord_sign')} · {dig}"
            ),
            priority=80 if role == "weak" else 50,
            role=role,
            why=why_prefix,
        )

    karakas = d1.get("karakas") if isinstance(d1.get("karakas"), dict) else {}
    for pname in planets:
        k = karakas.get(pname) if isinstance(karakas, dict) else None
        if not isinstance(k, dict) or not k.get("house"):
            continue
        dig = str(k.get("dignity") or "")
        role = (
            "weak" if dig in ("debilitated", "enemy")
            else ("support" if dig in ("exalted", "own") else "neutral")
        )
        add(
            f"planet.{pname}",
            f"Planet · {pname}",
            f"{pname} · {k.get('sign')} · H{k.get('house')} · {dig}",
            priority=75 if role == "weak" else 48,
            role=role,
            why=why_prefix,
        )

    for i, row in enumerate((d1.get("domain_houses") or [])[:4]):
        if not isinstance(row, dict):
            continue
        h = row.get("house")
        if not h:
            continue
        add(
            f"domain_house.{h}",
            f"Domain house · H{h}",
            (
                f"lord={row.get('lord')} · H{row.get('lord_house')} · "
                f"{row.get('lord_dignity') or ''}"
            ).strip(),
            priority=58,
            role="neutral",
            why=why_prefix,
        )

    lagnesh_pack = execution.get("lagnesh")
    if isinstance(lagnesh_pack, dict):
        d1_ln = lagnesh_pack.get("d1")
        if isinstance(d1_ln, dict) and d1_ln.get("lord"):
            dig = str(d1_ln.get("lord_dignity") or d1_ln.get("dignity") or "")
            add(
                "d1.lagnesh",
                "D1 · Lagnesh",
                (
                    f"{d1_ln.get('lord')} → H{d1_ln.get('lord_house')} · "
                    f"{d1_ln.get('lord_sign') or d1_ln.get('sign')} · {dig}"
                ),
                priority=82,
                role="neutral",
                why=why_prefix,
            )

    afflictions = execution.get("afflictions") or d1.get("afflictions") or []
    for i, line in enumerate(list(afflictions)[:3]):
        add(f"affliction.{i}", "Affliction", str(line), priority=72, role="weak", why=why_prefix)

    if execution.get("strength_label") or execution.get("composite_score") is not None:
        add(
            "pack.composite",
            "Theme strength",
            (
                f"score={execution.get('composite_score')}/100 — "
                f"{execution.get('strength_label') or ''}"
            ).strip(" —"),
            priority=40,
            role="neutral",
            why=why_prefix,
        )

    if not out and isinstance(karakas, dict):
        for pname, k in list(karakas.items())[:6]:
            if not isinstance(k, dict) or not k.get("house"):
                continue
            add(
                f"planet.{pname}",
                f"Planet · {pname}",
                f"{pname} · {k.get('sign')} · H{k.get('house')}",
                priority=45,
                role="neutral",
                why=why_prefix,
            )

    if not out:
        add(
            "execution.present",
            "Engine execution",
            "Engine execution ran — use full EE JSON + D1 positions for this question.",
            priority=30,
            role="neutral",
            why=why_prefix,
        )

    out.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
    for i, b in enumerate(out, start=1):
        b["rank"] = i
    return out, True


def finalize_selected_blocks_audit(
    audit: dict[str, Any],
    execution: dict[str, Any] | None,
    *,
    question: str = "",
    meta: dict[str, Any] | None = None,
    priority_header: str = "",
) -> dict[str, Any]:
    """Guarantee selected blocks + priority_facts whenever engine execution exists."""
    audit = dict(audit or {})
    blocks = list(audit.get("expected_blocks") or audit.get("available_blocks") or [])
    focus = str(audit.get("focus") or "").strip()
    domain = str(audit.get("domain") or "").strip()

    blocks, fallback_used = ensure_minimum_selected_blocks(
        blocks,
        execution if isinstance(execution, dict) else None,
        question=question or "",
        focus=focus,
        domain=domain,
    )
    audit["expected_blocks"] = blocks
    audit["available_blocks"] = blocks
    audit["expected_block_ids"] = sorted({str(b.get("id") or "") for b in blocks if b.get("id")})
    audit["priority_facts_for_llm"] = format_priority_facts_for_llm_common(
        blocks,
        header=priority_header or None,
    )
    if fallback_used:
        audit["selection_fallback"] = "minimum_from_engine_execution"
        notes = audit.get("overlap_notes")
        if not isinstance(notes, list):
            notes = [str(notes)] if notes else []
        notes.append(
            "Auto-selected minimum blocks from Engine Execution "
            "(never empty when EE present)."
        )
        audit["overlap_notes"] = notes
    return audit


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


# ── Deterministic DNA judge (no LLM — runs on EVERY question) ────────────────
# LLM judge default OFF hai (cost/latency). Yeh free checker contract se answer
# verify karta hai taaki debugger me verdict kabhi "—" na aaye:
#   timing pucha → answer me period/date hai?   multi-part → har part covered?
#   answer_style → length match?   Observability only — kabhi block nahi karta.

_TIME_REF_RX = re.compile(
    r"(?ix)\b("
    r"20\d\d|19\d\d|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
    r"mahin[ae]|mahino|saal|varsh|hafte|hafta|din(?:on)?|"
    r"month|year|week|window|period|phase|"
    r"dasha|antardasha|mahadasha|pratyantar|transit|gochar|"
    r"abhi\s*se|tak|ke\s*(?:beech|baad|andar)|jald|soon|currently|running"
    r")\b|(?:दशा|महीन|साल|वर्ष)"
)

_PART_SPLIT_RX = re.compile(r"(?i)\s+(?:and|aur|या|&)\s+|\?|;|।")

_SENT_SPLIT_RX = re.compile(r"[.!?।]+")


def _content_words(text: str) -> list[str]:
    return [
        w for w in re.findall(r"[a-z]+", (text or "").lower())
        if len(w) >= 4 and w not in _SIGNAL_STOPWORDS
    ]


def _answer_mostly_devanagari(answer: str) -> bool:
    body = (answer or "").strip()
    if not body:
        return False
    dev = sum(1 for ch in body if "\u0900" <= ch <= "\u097F")
    return dev > len(body) * 0.35


def deterministic_dna_judge(
    question: str,
    answer: str,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Free (no-LLM) verdict: did the answer honour the DNA contract?

    Returns {passed, issues, notes, checks_run} — observability only.
    """
    contract = contract if isinstance(contract, dict) else {}
    ans = (answer or "").strip()
    issues: list[str] = []
    notes: list[str] = []
    checks_run: list[str] = []

    if not ans:
        return {
            "passed": False,
            "issues": ["answer_empty — koi final answer record nahi hua"],
            "notes": [],
            "checks_run": ["answer_present"],
        }
    checks_run.append("answer_present")

    qtype = str(contract.get("question_type") or "").strip().lower()
    timing_flag = bool(contract.get("timing"))
    norm_q = str(contract.get("normalized_question") or question or "").strip()
    user_wants = str(contract.get("user_wants") or contract.get("intent") or "").strip()

    # 1) Timing contract — WHEN pucha to answer me time reference hona chahiye.
    if qtype == "timing" or timing_flag or re.search(
        r"(?i)\b(kab|when\s+will|kis\s+(saal|year|month|mahine))\b", norm_q
    ):
        checks_run.append("timing_reference")
        if _TIME_REF_RX.search(ans):
            notes.append("timing reference present (period/date/dasha in answer)")
        else:
            issues.append(
                "timing_missing — user ne WHEN pucha, par answer me koi "
                "period/date/dasha window nahi mila"
            )

    # 2) Multi-part coverage — "X and Y" pucha to dono parts ka jawab ho.
    if _answer_mostly_devanagari(ans):
        notes.append("answer Devanagari me — part-coverage word check skipped")
    else:
        src = user_wants or norm_q
        parts = [p.strip() for p in _PART_SPLIT_RX.split(src) if p and p.strip()]
        strong_parts = [p for p in parts if len(_content_words(p)) >= 2]
        if len(strong_parts) >= 2:
            checks_run.append("multi_part_coverage")
            ans_low = ans.lower()
            for p in strong_parts:
                words = _content_words(p)
                if words and not any(w in ans_low for w in words):
                    issues.append(
                        f"part_missed — is hisse ka jawab answer me nahi mila: “{p[:70]}”"
                    )
            if "part_missed" not in " ".join(issues):
                notes.append(f"all {len(strong_parts)} question parts covered in answer")

    # 3) Style contract — DNA ke answer_style ke against length check.
    style = str(contract.get("answer_style") or "").strip().lower()
    if style:
        checks_run.append("answer_style_length")
        sentences = [s for s in _SENT_SPLIT_RX.split(ans) if s.strip()]
        n = len(sentences)
        if style in ("short_paragraph",) and n < 2:
            issues.append(
                f"style_short — DNA ne short_paragraph (4-6 lines) bola, answer sirf {n} sentence ka hai"
            )
        elif style in ("detailed_explain", "detailed") and n < 3:
            issues.append(
                f"style_short — DNA ne detailed explain bola, answer sirf {n} sentence ka hai"
            )
        elif style in ("short_2_3_lines",) and n > 8:
            notes.append(f"style note — short_2_3_lines expected, answer {n} sentences ka hai")
        else:
            notes.append(f"style ok — {style} vs {n} sentences")

    return {
        "passed": not issues,
        "issues": issues,
        "notes": notes,
        "checks_run": checks_run,
    }


_DOMAIN_ANSWER_RX: dict[str, re.Pattern[str]] = {
    "finance": re.compile(
        r"(?ix)\b(paisa|paise|money|wealth|dhan|dhhan|income|profit|loss|invest|"
        r"saving|loan|debt|finance|salary|kamai|business|garib|amiri|paisa)\b"
    ),
    "health": re.compile(
        r"(?ix)\b(health|swasthya|sehat|bimari|disease|body|treatment|doctor|"
        r"pain|energy|vitality|mental|hospital|illness)\b"
    ),
    "love": re.compile(
        r"(?ix)\b(love|pyar|prem|rishta|relationship|partner|bf|gf|dil|feelings|"
        r"mohabbat|affair|crush)\b"
    ),
    "marriage": re.compile(
        r"(?ix)\b(shaadi|shadi|marriage|vivah|wedding|husband|wife|pati|patni|spouse)\b"
    ),
    "career": re.compile(
        r"(?ix)\b(career|job|naukri|promotion|office|work|profession|business|salary)\b"
    ),
    "education": re.compile(
        r"(?ix)\b(education|padhai|study|exam|degree|college|school|learning)\b"
    ),
    "travel": re.compile(
        r"(?ix)\b(travel|abroad|visa|foreign|yatra|trip|migration|settle)\b"
    ),
    "children": re.compile(
        r"(?ix)\b(child|children|baby|pregnancy|conceive|baccha|santaan|putra|putri)\b"
    ),
    "property": re.compile(
        r"(?ix)\b(property|ghar|house|land|real\s*estate|flat|home|makaan)\b"
    ),
    "spiritual": re.compile(
        r"(?ix)\b(spiritual|adhyatm|meditation|moksha|guru|bhakti|dharma)\b"
    ),
}

_SUBJECT_ANSWER_RX: dict[str, re.Pattern[str]] = {
    "partner": re.compile(
        r"(?ix)\b(partner|bf|gf|spouse|husband|wife|pati|patni|rishta|relationship|woh|unke|unki)\b"
    ),
    "self": re.compile(r"(?ix)\b(aap|tum|aapka|mera|meri|main|mai|you|your|aapke|mujhe)\b"),
    "family": re.compile(r"(?ix)\b(family|parivar|maa|papa|parent|bhai|behen|sibling)\b"),
}

_EMOTION_REASSURING_RX = re.compile(
    r"(?ix)\b(support|calm|reassur|gentle|hope|positive|better|manage|care|"
    r"sambhal|thik|theek|fikar|chinta\s*mat|don't\s*worry|samjho)\b"
)


def _dna_value_present(value: Any) -> bool:
    s = str(value or "").strip()
    return bool(s and s not in ("—", "-", "unknown", "unspecified"))


def _word_hits(words: list[str], answer_low: str, *, min_ratio: float = 0.25) -> tuple[bool, str]:
    if not words:
        return True, "seen in DNA"
    hits = [w for w in words if w in answer_low]
    ok = len(hits) >= max(1, int(len(words) * min_ratio))
    detail = f"{len(hits)}/{len(words)} keywords in answer"
    return ok, detail if ok else f"weak — {detail}"


def _dna_field_followed(
    label: str,
    value: Any,
    contract: dict[str, Any],
    answer: str,
) -> tuple[bool, str]:
    val = str(value or "").strip()
    if not _dna_value_present(val):
        return False, "DNA value missing"
    ans = (answer or "").strip()
    if not ans:
        return False, "no final answer"
    ans_low = ans.lower()
    key = label.strip().lower()

    if key == "normalized":
        words = _content_words(val)[:8]
        if _answer_mostly_devanagari(ans):
            return True, "Devanagari answer — keyword check skipped"
        return _word_hits(words, ans_low, min_ratio=0.2)

    if key == "domain":
        dom = str(contract.get("domain") or "").strip().lower()
        m = re.search(r"\(([^)]+)\)\s*$", val)
        if m:
            dom = m.group(1).strip().lower()
        pat = _DOMAIN_ANSWER_RX.get(dom)
        if pat and pat.search(ans):
            return True, f"{dom} theme in answer"
        if pat:
            return False, f"{dom} theme not detected in answer"
        return True, "domain seen in DNA"

    if key in ("intent", "llm understand question"):
        words = _content_words(val)[:10]
        if not words:
            return True, "seen in DNA"
        return _word_hits(words, ans_low, min_ratio=0.2)

    if key == "llm answer plan":
        words = _content_words(val)[:12]
        return _word_hits(words, ans_low, min_ratio=0.15)

    if key == "bucket":
        bucket = str(contract.get("bucket") or "").strip().lower()
        m = re.search(r"\(([^)]+)\)", val)
        if m:
            bucket = m.group(1).strip().lower()
        parts = [p for p in re.split(r"[_\s]+", bucket) if len(p) >= 3]
        if parts and any(p in ans_low for p in parts):
            return True, "bucket theme in answer"
        return False, "bucket theme weak in answer"

    if key == "subject":
        subj = str(contract.get("subject") or "").strip().lower()
        pat = _SUBJECT_ANSWER_RX.get(subj)
        if pat and pat.search(ans):
            return True, f"subject={subj} addressed"
        if pat:
            return False, f"subject={subj} not clear in answer"
        return True, "subject seen in DNA"

    if key == "target":
        return True, "target seen in DNA"

    if key == "question type":
        qtype = str(contract.get("question_type") or val).strip().lower()
        if qtype == "timing" or contract.get("timing"):
            ok = bool(_TIME_REF_RX.search(ans))
            return ok, "timing type honored" if ok else "timing answer missing"
        if qtype == "decision":
            ok = bool(re.search(
                r"(?ix)\b(yes|no|maybe|haan|nahi|shayad|possible|unlikely|better|avoid|"
                r"kar\s*sak|na\s*kar)\b",
                ans,
            ))
            return ok, "decision tone present" if ok else "decision unclear"
        return True, f"type={qtype}"

    if key == "timing required":
        if val.lower() in ("yes", "true"):
            ok = bool(_TIME_REF_RX.search(ans))
            return ok, "WHEN answered" if ok else "WHEN missing in answer"
        return True, "timing not required"

    if key == "time context":
        tense = str(contract.get("tense") or "").strip().lower()
        if tense == "present":
            ok = bool(re.search(r"(?ix)\b(abhi|currently|now|chal\s*raha|present|running)\b", ans))
            return ok or True, "present context" if ok else "present tense soft"
        if tense == "future":
            ok = bool(re.search(r"(?ix)\b(aage|future|hoga|hogi|milega|coming|next)\b", ans))
            return ok or True, "future context" if ok else "future tense soft"
        if tense == "past":
            ok = bool(re.search(r"(?ix)\b(past|pehle|tha|thi|hua|hui|already)\b", ans))
            return ok or True, "past context" if ok else "past tense soft"
        return True, "time context seen"

    if key == "answer style":
        style = str(contract.get("answer_style") or "").strip().lower()
        if not style:
            return True, "style seen"
        sentences = [s for s in _SENT_SPLIT_RX.split(ans) if s.strip()]
        n = len(sentences)
        if style in ("short_paragraph",) and n < 2:
            return False, f"too short ({n} sentences)"
        if style in ("detailed_explain", "detailed") and n < 3:
            return False, f"not detailed enough ({n} sentences)"
        return True, f"style ok ({n} sentences)"

    if key == "emotion":
        emo = str(contract.get("emotion") or "").strip().lower()
        if emo in ("fear", "anxiety", "sadness", "anger"):
            ok = bool(_EMOTION_REASSURING_RX.search(ans))
            return ok, "gentle tone" if ok else "emotion tone not reassuring"
        return True, "emotion seen"

    if key == "risk":
        if str(contract.get("risk") or "").strip().lower() == "high":
            harsh = bool(re.search(r"(?ix)\b(guaranteed|certain|pakka\s*100|definitely\s*fail|doom)\b", ans))
            return not harsh, "high-risk wording ok" if not harsh else "too harsh for high risk"
        return True, "risk seen"

    if key in (
        "confidence", "bucket match", "understanding confidence",
        "engine archetype", "modules", "follow-up", "multiple questions",
    ):
        return True, "seen in DNA contract"

    return True, "seen in DNA"


def enrich_dna_pipeline_followed(
    pipeline: list[dict[str, Any]],
    contract: dict[str, Any] | None,
    answer: str,
) -> dict[str, Any]:
    """Add followed ✅/❌ per DNA row for admin debugger."""
    contract = contract if isinstance(contract, dict) else {}
    steps: list[dict[str, Any]] = []
    followed_count = 0
    for row in pipeline or []:
        if not isinstance(row, dict):
            continue
        label = str(row.get("label") or "").strip()
        value = row.get("value")
        ok, reason = _dna_field_followed(label, value, contract, answer)
        if ok:
            followed_count += 1
        steps.append({
            **row,
            "followed": ok,
            "follow_reason": reason,
        })
    total = len(steps)
    return {
        "steps": steps,
        "summary": {
            "total": total,
            "followed_count": followed_count,
            "pct": int(round(100 * followed_count / total)) if total else 0,
        },
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
