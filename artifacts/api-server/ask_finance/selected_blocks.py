"""LLM Selected JSON Blocks — question-relevant subset FROM finance Engine Execution."""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_FOCUS_WANT: dict[str, dict[str, Any]] = {
    "income_source": {
        "label": "Income source — question-relevant EE blocks",
        "lords": ("h2", "h10", "h11"),
        "houses": (2, 10, 11),
        "planets": ("Sun", "Mercury", "Jupiter", "Saturn"),
        "want_keys": ("dimensions", "sub_flags", "afflictions"),
        "dims": ("income_stability", "wealth_potential"),
    },
    "savings_capacity": {
        "label": "Savings — question-relevant EE blocks",
        "lords": ("h2", "h11"),
        "houses": (2, 11, 12),
        "planets": ("Saturn", "Jupiter", "Venus"),
        "want_keys": ("dimensions", "afflictions"),
        "dims": ("saving_ability", "risk_leak"),
    },
    "save_vs_spend": {
        "label": "Save vs spend — question-relevant EE blocks",
        "lords": ("h2", "h12"),
        "houses": (2, 12),
        "planets": ("Saturn", "Venus", "Moon"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("saving_ability", "risk_leak"),
    },
    "expense_pattern": {
        "label": "Expense pattern — question-relevant EE blocks",
        "lords": ("h12", "h2"),
        "houses": (12, 2, 6),
        "planets": ("Venus", "Rahu", "Saturn"),
        "want_keys": ("dimensions", "afflictions"),
        "dims": ("risk_leak", "saving_ability"),
    },
    "spending_personality": {
        "label": "Spending personality — question-relevant EE blocks",
        "lords": ("h12", "h2"),
        "houses": (12, 2),
        "planets": ("Venus", "Moon", "Mars"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("risk_leak", "saving_ability"),
    },
    "financial_discipline": {
        "label": "Financial discipline — question-relevant EE blocks",
        "lords": ("h2", "h6"),
        "houses": (2, 6, 10),
        "planets": ("Saturn", "Mercury"),
        "want_keys": ("dimensions", "afflictions"),
        "dims": ("saving_ability", "income_stability"),
    },
    "investment_risk": {
        "label": "Investment risk — question-relevant EE blocks",
        "lords": ("h5", "h8", "h11"),
        "houses": (5, 8, 11),
        "planets": ("Mercury", "Jupiter", "Rahu", "Saturn"),
        "want_keys": ("dimensions", "afflictions"),
        "dims": ("risk_leak", "wealth_potential"),
    },
    "debt_loan": {
        "label": "Debt / loan — question-relevant EE blocks",
        "lords": ("h6", "h2", "h8"),
        "houses": (6, 2, 8, 12),
        "planets": ("Saturn", "Mars", "Rahu"),
        "want_keys": ("dimensions", "sub_flags", "afflictions"),
        "dims": ("risk_leak", "saving_ability"),
    },
    "property_money": {
        "label": "Property money — question-relevant EE blocks",
        "lords": ("h4", "h2", "h11"),
        "houses": (4, 2, 11),
        "planets": ("Mars", "Saturn", "Venus", "Jupiter"),
        "want_keys": ("dimensions", "wealth_yogas"),
        "dims": ("wealth_potential", "income_stability"),
    },
    "sudden_gain_loss": {
        "label": "Sudden gain/loss — question-relevant EE blocks",
        "lords": ("h8", "h11", "h12"),
        "houses": (8, 11, 12),
        "planets": ("Rahu", "Ketu", "Jupiter"),
        "want_keys": ("dimensions", "sub_flags", "wealth_yogas"),
        "dims": ("wealth_potential", "risk_leak"),
    },
    "business_profit": {
        "label": "Business profit — question-relevant EE blocks",
        "lords": ("h7", "h10", "h11"),
        "houses": (7, 10, 11, 2),
        "planets": ("Mercury", "Saturn", "Jupiter", "Sun"),
        "want_keys": ("dimensions", "sub_flags"),
        "dims": ("income_stability", "wealth_potential"),
    },
    "loss_reasons": {
        "label": "Loss reasons — question-relevant EE blocks",
        "lords": ("h12", "h8", "h6"),
        "houses": (12, 8, 6, 2),
        "planets": ("Saturn", "Rahu", "Ketu", "Mars"),
        "want_keys": ("afflictions", "dimensions"),
        "dims": ("risk_leak",),
    },
    "wealth_potential": {
        "label": "Wealth potential — question-relevant EE blocks",
        "lords": ("h2", "h11", "h9"),
        "houses": (2, 11, 9, 5),
        "planets": ("Jupiter", "Venus", "Mercury"),
        "want_keys": ("dimensions", "wealth_yogas"),
        "dims": ("wealth_potential", "income_stability"),
    },
    "dhana_yoga": {
        "label": "Dhana yoga — question-relevant EE blocks",
        "lords": ("h2", "h11", "h9"),
        "houses": (2, 11, 9),
        "planets": ("Jupiter", "Venus"),
        "want_keys": ("wealth_yogas", "dimensions"),
        "dims": ("wealth_potential",),
    },
    "general_finance": {
        "label": "General finance — question-relevant EE blocks",
        "lords": ("h2", "h11", "h10"),
        "houses": (2, 11, 10, 12),
        "planets": ("Jupiter", "Venus", "Mercury", "Saturn"),
        "want_keys": ("dimensions", "afflictions", "wealth_yogas"),
        "dims": ("wealth_potential", "income_stability", "saving_ability", "risk_leak"),
    },
}


def _detect_focus(question: str, routing_label: str = "") -> str:
    # DNA label is boss — it already scoped the question. Only when DNA gave no
    # specific focus does "sab chahiye / full study" widen to the general pack.
    label = (routing_label or "").strip().lower()
    if label in _FOCUS_WANT:
        return label
    try:
        from ask_selected_blocks_common import question_wants_everything

        if question_wants_everything(question or ""):
            return "general_finance"
    except Exception:
        pass
    try:
        from ask_finance.classifier import classify_finance_archetype

        arch = classify_finance_archetype(question or "")
        if arch in _FOCUS_WANT:
            return arch
    except Exception:
        pass
    return "general_finance"


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
    want = _FOCUS_WANT.get(focus) or _FOCUS_WANT["general_finance"]
    label = str(want.get("label") or focus)
    d1 = _d1(execution)
    lords = d1.get("house_lords") or {}
    karakas = d1.get("karakas") or {}
    dims = execution.get("dimensions") or d1.get("dimensions") or {}
    afflictions = execution.get("afflictions") or d1.get("afflictions") or []
    yogas = execution.get("wealth_yogas") or d1.get("wealth_yogas") or []
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
        if dig in ("exalted", "own"):
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

    if "wealth_yogas" in (want.get("want_keys") or ()) and yogas:
        add(
            "pack.wealth_yogas",
            "Wealth yogas",
            f"Focus={focus}",
            ", ".join(str(y) for y in yogas[:6]),
            priority=65,
            role="support",
        )

    if "sub_flags" in (want.get("want_keys") or ()) and isinstance(flags, dict):
        for fk in (
            "leak_active", "saving_strong", "wealth_strong",
            "debt_burden_high", "sudden_wealth_yog", "business_friendly",
        ):
            if fk not in flags or flags.get(fk) in (None, False, ""):
                continue
            add(
                f"flag.{fk}",
                f"Flag · {fk}",
                f"Focus={focus}",
                f"{fk}={flags.get(fk)}",
                priority=60,
                role="weak" if fk in ("leak_active", "debt_burden_high") else "support",
            )

    # Real dasha rows when the user asked for dasha — LLM cites THIS, never invents.
    try:
        from ask_selected_blocks_common import dasha_blocks_from_pack, question_wants_dasha

        if question_wants_dasha(question or ""):
            out.extend(
                dasha_blocks_from_pack(
                    execution.get("dasha_timing_compact"), focus=focus,
                )
            )
    except Exception:
        pass

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


def build_finance_selected_blocks(
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
        pack = checks.get("finance_engine_execution")
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
    _limit = 5
    try:
        from ask_selected_blocks_common import question_wants_everything

        if question_wants_everything(question or "", meta):
            _limit = 9  # full-study ask → serve more facts, LLM explains all of them
    except Exception:
        pass
    priority_text = format_priority_facts_for_llm(blocks, limit=_limit)
    used_planets = [
        n for n in _PLANET_NAMES
        if re.search(rf"(?i)\b{re.escape(n)}\b", answer or "")
    ]
    audit = {
        "applies": True,
        "source": "finance_engine_execution",
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
    }
    try:
        from ask_selected_blocks_common import (
            coverage_check_selected_blocks,
            coverage_note_lines,
        )

        coverage = coverage_check_selected_blocks(
            question or "",
            meta=meta,
            audit=audit,
            execution=pack,
            general_focus="general_finance",
        )
        audit["coverage"] = coverage
        from ask_selected_blocks_common import dna_boost_note_lines

        audit["overlap_notes"] = (
            coverage_note_lines(coverage) + dna_boost_note_lines(_boost_applied)
        )
    except Exception:
        pass
    return audit
