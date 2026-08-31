"""LLM Selected JSON Blocks — question-relevant subset FROM travel Engine Execution."""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_FOCUS_WANT: dict[str, dict[str, Any]] = {
    "travel_yog": {
        "label": "Foreign travel yog — question-relevant EE blocks",
        "lords": ("h9", "h12", "h3"),
        "houses": (9, 12, 3),
        "planets": ("Rahu", "Jupiter"),
        "want_keys": ("dimensions", "travel_yogas", "sub_flags"),
        "dims": ("foreign_travel", "visa_luck"),
    },
    "foreign_settlement": {
        "label": "Foreign settlement — question-relevant EE blocks",
        "lords": ("h12", "h9", "h4"),
        "houses": (12, 9, 4),
        "planets": ("Rahu", "Saturn", "Jupiter"),
        "want_keys": ("dimensions", "afflictions", "sub_flags"),
        "dims": ("settlement", "foreign_travel"),
    },
    "visa_theme": {
        "label": "Visa theme — question-relevant EE blocks",
        "lords": ("h9", "h12"),
        "houses": (9, 12),
        "planets": ("Jupiter", "Rahu", "Mercury"),
        "want_keys": ("dimensions", "travel_yogas"),
        "dims": ("visa_luck", "foreign_travel"),
    },
    "relocation_abroad": {
        "label": "Relocation abroad — question-relevant EE blocks",
        "lords": ("h12", "h4", "h9"),
        "houses": (12, 4, 9),
        "planets": ("Rahu", "Saturn", "Moon"),
        "want_keys": ("dimensions", "sub_flags", "afflictions"),
        "dims": ("settlement", "foreign_travel", "travel_risk"),
    },
    "return_india": {
        "label": "Return India — question-relevant EE blocks",
        "lords": ("h4", "h12", "h9"),
        "houses": (4, 12, 9),
        "planets": ("Moon", "Saturn", "Ketu"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("settlement", "foreign_travel"),
    },
    "travel_obstacles": {
        "label": "Travel obstacles — question-relevant EE blocks",
        "lords": ("h9", "h12", "h6"),
        "houses": (9, 12, 6, 8),
        "planets": ("Saturn", "Rahu", "Mars"),
        "want_keys": ("afflictions", "dimensions"),
        "dims": ("travel_risk", "foreign_travel"),
    },
    "short_travel": {
        "label": "Short travel — question-relevant EE blocks",
        "lords": ("h3", "h9"),
        "houses": (3, 9),
        "planets": ("Mercury", "Moon", "Venus"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("short_travel", "travel_risk"),
    },
    "pilgrimage_travel": {
        "label": "Pilgrimage — question-relevant EE blocks",
        "lords": ("h9", "h12"),
        "houses": (9, 12),
        "planets": ("Jupiter", "Ketu", "Sun"),
        "want_keys": ("dimensions", "travel_yogas"),
        "dims": ("foreign_travel", "short_travel"),
    },
    "passport_travel": {
        "label": "Passport / travel capacity — question-relevant EE blocks",
        "lords": ("h9", "h3"),
        "houses": (9, 3, 12),
        "planets": ("Mercury", "Jupiter", "Rahu"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("visa_luck", "foreign_travel"),
    },
    "immigration": {
        "label": "Immigration / PR — question-relevant EE blocks",
        "lords": ("h12", "h9", "h10"),
        "houses": (12, 9, 10),
        "planets": ("Saturn", "Rahu", "Jupiter"),
        "want_keys": ("dimensions", "afflictions", "sub_flags"),
        "dims": ("settlement", "visa_luck", "travel_risk"),
    },
    "business_travel": {
        "label": "Business travel — question-relevant EE blocks",
        "lords": ("h10", "h7", "h9"),
        "houses": (10, 7, 9, 3),
        "planets": ("Mercury", "Sun", "Jupiter"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("short_travel", "foreign_travel", "visa_luck"),
    },
    "travel_risk": {
        "label": "Travel risk — question-relevant EE blocks",
        "lords": ("h3", "h8", "h12"),
        "houses": (3, 8, 12, 6),
        "planets": ("Mars", "Saturn", "Rahu"),
        "want_keys": ("afflictions", "dimensions"),
        "dims": ("travel_risk",),
    },
    "travel_country_fit": {
        "label": "Country fit — question-relevant EE blocks",
        "lords": ("h9", "h12", "h4"),
        "houses": (9, 12, 4),
        "planets": ("Rahu", "Jupiter", "Saturn"),
        "want_keys": ("dimensions", "travel_yogas", "sub_flags"),
        "dims": ("foreign_travel", "settlement", "visa_luck"),
    },
    "general_travel": {
        "label": "General travel — question-relevant EE blocks",
        "lords": ("h9", "h12", "h3"),
        "houses": (9, 12, 3, 4),
        "planets": ("Rahu", "Jupiter", "Mercury", "Saturn"),
        "want_keys": ("dimensions", "afflictions", "travel_yogas", "sub_flags"),
        "dims": ("foreign_travel", "settlement", "visa_luck", "short_travel", "travel_risk"),
    },
}


def _detect_focus(question: str, routing_label: str = "") -> str:
    # DNA routing label is boss; "sab chahiye" widens only when DNA gave no focus.
    label = (routing_label or "").strip().lower()
    if label in _FOCUS_WANT:
        return label
    try:
        from ask_selected_blocks_common import question_wants_everything

        if question_wants_everything(question or ""):
            return "general_travel"
    except Exception:
        pass
    try:
        from ask_travel.classifier import classify_travel_archetype

        arch = classify_travel_archetype(question or "")
        if arch in _FOCUS_WANT:
            return arch
    except Exception:
        pass
    return "general_travel"


def _d1(execution: dict[str, Any]) -> dict[str, Any]:
    d1 = execution.get("d1")
    return d1 if isinstance(d1, dict) else {}


def question_relevant_blocks_from_execution(
    question: str,
    execution: dict[str, Any],
    *,
    routing_label: str = "",
) -> tuple[str, str, list[dict[str, Any]]]:
    focus = _detect_focus(question, routing_label)
    want = _FOCUS_WANT.get(focus) or _FOCUS_WANT["general_travel"]
    label = str(want.get("label") or focus)
    d1 = _d1(execution)
    lords = d1.get("house_lords") or {}
    karakas = d1.get("karakas") or {}
    dims = execution.get("dimensions") or d1.get("dimensions") or {}
    afflictions = execution.get("afflictions") or d1.get("afflictions") or []
    yogas = execution.get("travel_yogas") or d1.get("travel_yogas") or []
    flags = execution.get("sub_flags") or d1.get("sub_flags") or {}

    out: list[dict[str, Any]] = []

    def add(
        bid: str,
        blabel: str,
        why: str,
        detail: str,
        *,
        priority: int = 0,
        role: str = "neutral",
    ) -> None:
        out.append({
            "id": bid,
            "label": blabel,
            "why": why,
            "detail": detail,
            "priority": int(priority),
            "role": role,
        })

    for dim_key in want.get("dims") or ():
        row = dims.get(dim_key) if isinstance(dims, dict) else None
        if not isinstance(row, dict):
            continue
        verdict = str(row.get("verdict") or "")
        # For travel_risk, RED = weak/caution; for others RED = weak support
        if dim_key == "travel_risk":
            role = "weak" if verdict == "RED" else ("support" if verdict == "GREEN" else "neutral")
        else:
            role = "weak" if verdict == "RED" else ("support" if verdict == "GREEN" else "neutral")
        pr = 90 if verdict == "RED" else (70 if verdict == "YELLOW" else 55)
        add(
            f"dim.{dim_key}",
            f"Dimension · {dim_key}",
            f"Question focus={focus}",
            f"{verdict} — {row.get('reason') or row.get('tier') or ''}".strip(" —"),
            priority=pr,
            role=role,
        )

    for hk in want.get("lords") or ():
        st = lords.get(hk) if isinstance(lords, dict) else None
        if not isinstance(st, dict) or not st.get("lord"):
            continue
        dig = str(st.get("lord_dignity") or "")
        role = "weak" if dig in ("debilitated", "enemy") or st.get("lord_in_dusthana") else "neutral"
        if dig in ("exalted", "own") or st.get("lord_in_foreign"):
            role = "support"
        add(
            f"lord.{hk}",
            f"House lord · {hk}",
            f"Focus={focus}",
            f"{st.get('lord')} → H{st.get('lord_house')} · {st.get('lord_sign')} · {dig}",
            priority=80 if role == "weak" else 50,
            role=role,
        )

    for pname in want.get("planets") or ():
        k = karakas.get(pname) if isinstance(karakas, dict) else None
        if not isinstance(k, dict):
            continue
        dig = str(k.get("dignity") or "")
        role = "weak" if dig in ("debilitated", "enemy") else (
            "support" if dig in ("exalted", "own") else "neutral"
        )
        house = int(k.get("house") or 0)
        if house in (3, 9, 12) and role == "neutral":
            role = "support"
        add(
            f"planet.{pname}",
            f"Planet · {pname}",
            f"Focus={focus}",
            f"{pname} · {k.get('sign')} · H{k.get('house')} · {dig}",
            priority=75 if role == "weak" else 48,
            role=role,
        )

    if "afflictions" in (want.get("want_keys") or ()) and afflictions:
        for i, line in enumerate(list(afflictions)[:4]):
            add(
                f"affliction.{i}",
                "Affliction",
                f"Focus={focus}",
                str(line),
                priority=72,
                role="weak",
            )

    if "travel_yogas" in (want.get("want_keys") or ()) and yogas:
        add(
            "pack.travel_yogas",
            "Travel yogas",
            f"Focus={focus}",
            ", ".join(str(y) for y in yogas[:6]),
            priority=65,
            role="support",
        )

    if "sub_flags" in (want.get("want_keys") or ()) and isinstance(flags, dict):
        for fk in (
            "foreign_yog_active", "settlement_strong", "visa_supportive",
            "travel_strong", "risk_elevated", "home_anchor_strong",
        ):
            if fk not in flags or flags.get(fk) in (None, False, ""):
                continue
            add(
                f"flag.{fk}",
                f"Flag · {fk}",
                f"Focus={focus}",
                f"{fk}={flags.get(fk)}",
                priority=60,
                role="weak" if fk in ("risk_elevated", "home_anchor_strong") else "support",
            )

    strength = execution.get("strength_label") or d1.get("strength_label")
    score = execution.get("composite_score")
    if score is None:
        score = d1.get("composite_score")
    if strength or score is not None:
        add(
            "pack.composite",
            "Travel strength",
            f"Focus={focus}",
            f"score={score}/100 — {strength or ''}".strip(" —"),
            priority=40,
            role="neutral",
        )

    out.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
    for i, block in enumerate(out, start=1):
        block["rank"] = i
    return focus, label, out


def format_priority_facts_for_llm(blocks: list[dict[str, Any]], *, limit: int = 5) -> str:
    if not blocks:
        return ""
    lines = [
        "QUESTION_PRIORITY_FACTS (from Engine Execution only — use in this order):",
        "Rules: #1 = main reason + MUST include its natural chart proof in the answer",
        "(planet + house/dignity). Max 2–3 facts total. Do not invent planets outside this list.",
    ]
    for b in blocks[: max(1, limit)]:
        rank = b.get("rank") or "?"
        role = b.get("role") or "neutral"
        proof_hint = " ← CITE THIS as proof" if rank in (1, "1") else ""
        lines.append(
            f"#{rank} [{role}] {b.get('label')}: {b.get('detail') or b.get('why')}{proof_hint}"
        )
    return "\n".join(lines)


def build_travel_selected_blocks(
    question: str,
    answer: str = "",
    *,
    meta: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = meta if isinstance(meta, dict) else {}
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = execution
    if not isinstance(pack, dict):
        pack = checks.get("travel_engine_execution")
    if not isinstance(pack, dict):
        pack = {}
    label = str(
        meta.get("routing_label")
        or meta.get("archetype")
        or checks.get("routing_label")
        or pack.get("routing_label")
        or ""
    ).strip().lower()
    focus, focus_label, blocks = question_relevant_blocks_from_execution(
        question or "", pack, routing_label=label,
    )
    _boost_applied: list[str] = []
    try:
        from ask_selected_blocks_common import dna_boost_selected_blocks

        blocks, _boost_applied = dna_boost_selected_blocks(
            question or "", blocks, meta=meta, pack=pack,
        )
    except Exception:
        pass
    priority_text = format_priority_facts_for_llm(blocks, limit=5)
    used_planets = [
        n for n in _PLANET_NAMES
        if re.search(rf"(?i)\b{re.escape(n)}\b", answer or "")
    ]
    audit = {
        "applies": True,
        "source": "travel_engine_execution",
        "focus": focus,
        "focus_label": focus_label,
        "known_focuses": sorted(_FOCUS_WANT.keys()),
        "expected_blocks": blocks,
        "available_blocks": blocks,
        "priority_facts_for_llm": priority_text,
        "used_in_answer": {"planets": used_planets},
        "note": (
            f"Question focus={focus}: top facts are for LLM priority reading (not full EE dump)."
        ),
        "domain": "travel",
    }
    try:
        from ask_selected_blocks_common import (
            coverage_check_selected_blocks,
            coverage_note_lines,
            finalize_selected_blocks_audit,
        )

        audit = finalize_selected_blocks_audit(
            audit,
            pack,
            question=question or "",
            meta=meta,
        )
        blocks = audit.get("expected_blocks") or blocks

        coverage = coverage_check_selected_blocks(
            question or "",
            meta=meta,
            audit=audit,
            execution=pack,
            general_focus="general_travel",
        )
        audit["coverage"] = coverage
        from ask_selected_blocks_common import dna_boost_note_lines

        audit["overlap_notes"] = (
            coverage_note_lines(coverage) + dna_boost_note_lines(_boost_applied)
        )
    except Exception:
        pass
    return audit
