"""LLM Selected JSON Blocks for general chart — DNA intent picks focus houses/planets."""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

# Soft topic → houses / planets (DNA intent / question words)
_TOPIC_HINTS: tuple[tuple[str, tuple[int, ...], tuple[str, ...]], ...] = (
    (r"career|job|naukri|office|promotion|work|profession", (10, 6, 2, 11), ("Sun", "Saturn", "Mercury")),
    (r"money|wealth|paisa|dhan|finance|income|salary|loan", (2, 11, 5, 9), ("Jupiter", "Venus", "Mercury")),
    (r"love|marriage|shaadi|partner|relationship|pati|patni", (7, 5, 2, 11), ("Venus", "Jupiter", "Moon")),
    (r"health|sehat|bimari|disease|body", (1, 6, 8, 12), ("Moon", "Mars", "Saturn")),
    (r"travel|yatra|videsh|abroad|foreign|visa", (3, 9, 12, 7), ("Rahu", "Moon", "Jupiter")),
    (r"education|padhai|study|exam|degree", (4, 5, 9), ("Mercury", "Jupiter", "Moon")),
    (r"child|santaan|baby|pregnancy", (5, 9, 11), ("Jupiter", "Venus", "Moon")),
    (r"property|ghar|house|land|flat", (4, 2, 11), ("Mars", "Moon", "Venus")),
    (r"spiritual|moksha|dharma|puja|guru", (9, 12, 5), ("Jupiter", "Ketu", "Sun")),
    (r"luck|bhagya|fortune|kismat", (9, 5, 11, 1), ("Jupiter", "Sun", "Venus")),
)


def _focus_from_text(text: str) -> tuple[tuple[int, ...], tuple[str, ...], str]:
    t = (text or "").strip().lower()
    for rx, houses, planets in _TOPIC_HINTS:
        if re.search(rx, t, re.I):
            return houses, planets, rx
    # Default general: Lagna + Moon + key houses
    return (1, 5, 7, 9, 10), ("Sun", "Moon", "Jupiter", "Saturn"), "general"


def build_general_selected_blocks(
    question: str,
    answer: str = "",
    *,
    meta: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = meta if isinstance(meta, dict) else {}
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = execution if isinstance(execution, dict) else checks.get("general_chart_engine_execution")
    if not isinstance(pack, dict):
        pack = {}

    dna_bits = " ".join(
        str(meta.get(k) or "")
        for k in ("intent", "user_wants", "normalized_question", "bucket")
    )
    focus_text = f"{question or ''} {dna_bits}".strip()
    houses, planets, hint = _focus_from_text(focus_text)

    d1 = pack.get("d1") if isinstance(pack.get("d1"), dict) else {}
    lords = d1.get("house_lords") or {}
    karakas = d1.get("karakas") or {}
    afflictions = pack.get("afflictions") or d1.get("afflictions") or []
    dasha = pack.get("dasha_timing_compact") if isinstance(pack.get("dasha_timing_compact"), dict) else {}

    blocks: list[dict[str, Any]] = []

    def add(bid: str, label: str, detail: str, *, priority: int, role: str) -> None:
        blocks.append({
            "id": bid,
            "label": label,
            "why": f"DNA/general focus hint={hint}",
            "detail": detail,
            "priority": priority,
            "role": role,
        })

    # Current dasha first — general chart always has it
    cur = dasha.get("current") if isinstance(dasha, dict) else None
    if isinstance(cur, dict) and (cur.get("md") or cur.get("ad")):
        parts = [str(cur.get(k)) for k in ("md", "ad", "pd") if cur.get(k)]
        win = str(cur.get("window") or "").strip()
        add(
            "dasha.current",
            "Dasha · current (running NOW)",
            " → ".join(parts) + (f" · {win}" if win else ""),
            priority=92,
            role="support",
        )

    lagna = str(d1.get("ascendant") or "")
    if lagna:
        add("d1.lagna", "D1 · Lagna", lagna, priority=88, role="neutral")

    for h in houses:
        st = lords.get(f"h{h}") if isinstance(lords, dict) else None
        if not isinstance(st, dict) or not st.get("lord"):
            continue
        dig = str(st.get("lord_dignity") or "")
        role = "weak" if dig in ("debilitated", "enemy") or st.get("lord_in_dusthana") else "neutral"
        if dig in ("exalted", "own"):
            role = "support"
        add(
            f"lord.h{h}",
            f"House lord · h{h}",
            f"{st.get('lord')} → H{st.get('lord_house')} · {st.get('lord_sign')} · {dig}",
            priority=80 if role == "weak" else 55,
            role=role,
        )

    for pname in planets:
        k = karakas.get(pname) if isinstance(karakas, dict) else None
        if not isinstance(k, dict):
            continue
        dig = str(k.get("dignity") or "")
        role = "weak" if dig in ("debilitated", "enemy") else (
            "support" if dig in ("exalted", "own") else "neutral"
        )
        add(
            f"planet.{pname}",
            f"Planet · {pname}",
            f"{pname} · {k.get('sign')} · H{k.get('house')} · {dig}",
            priority=75 if role == "weak" else 50,
            role=role,
        )

    for i, line in enumerate(list(afflictions)[:3]):
        add(f"affliction.{i}", "Affliction", str(line), priority=70, role="weak")

    _boost_applied: list[str] = []
    try:
        from ask_selected_blocks_common import dna_boost_selected_blocks

        blocks, _boost_applied = dna_boost_selected_blocks(
            question or "", blocks, meta=meta, pack=pack,
        )
    except Exception:
        blocks.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
        for i, b in enumerate(blocks, start=1):
            b["rank"] = i

    lines = [
        "QUESTION_PRIORITY_FACTS (from General Chart Execution — use in this order):",
        "Rules: #1 = main reason + MUST include natural chart proof (planet + house/dignity).",
        "Study full D1+D9 in GENERAL_CHART_ENGINE_EXECUTION_JSON; these are priority cites only.",
    ]
    for b in blocks[:6]:
        hint_c = " ← CITE THIS as proof" if b.get("rank") == 1 else ""
        lines.append(
            f"#{b.get('rank')} [{b.get('role')}] {b.get('label')}: {b.get('detail')}{hint_c}"
        )
    priority_text = "\n".join(lines) if blocks else ""
    used = [n for n in _PLANET_NAMES if re.search(rf"(?i)\b{re.escape(n)}\b", answer or "")]

    audit = {
        "applies": True,
        "source": "general_chart_engine_execution",
        "focus": "general_chart",
        "focus_label": f"General chart — hint={hint}",
        "expected_blocks": blocks,
        "available_blocks": blocks,
        "priority_facts_for_llm": priority_text,
        "used_in_answer": {"planets": used},
        "domain": "general",
        "note": "DNA domain=general → LLM studies full D1+D9+dasha; priority facts guide cite order.",
    }
    try:
        from ask_selected_blocks_common import (
            coverage_check_selected_blocks,
            coverage_note_lines,
            dna_boost_note_lines,
        )

        coverage = coverage_check_selected_blocks(
            question or "",
            meta=meta,
            audit=audit,
            execution=pack,
            general_focus="general_chart",
        )
        audit["coverage"] = coverage
        audit["overlap_notes"] = (
            coverage_note_lines(coverage) + dna_boost_note_lines(_boost_applied)
        )
    except Exception:
        pass
    return audit
