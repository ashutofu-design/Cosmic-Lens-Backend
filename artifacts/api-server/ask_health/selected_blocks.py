"""LLM Selected JSON Blocks — question-relevant subset FROM Engine Execution only.

- Source of truth: health_engine_execution (D1/D9)
- Never invents planets/houses outside EE
- Does NOT dump entire EE — only question-relevant keys that exist in EE
"""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_TRAVEL_RX = re.compile(
    r"(?ix)\b(travel|yatra|trip|tour|safar|videsh|abroad|flight|journey)\b"
)
_STRESS_RX = re.compile(
    r"(?ix)\b(stress|anxiety|tension|mann|mental|depression|neend|sleep)\b"
)
_SURGERY_RX = re.compile(
    r"(?ix)\b(operation|surgery|shastra[\s-]?kriya|hospital)\b"
)
_RESP_RX = re.compile(
    r"(?ix)\b(thand|thandi|sardi|cold|khansi|saans|breath|chest|zukam|flu|allerg)\b"
)
_CHRONIC_RX = re.compile(
    r"(?ix)\b(chronic|lambi|baar\s+baar|recurring|persistent)\b"
)
_OVERVIEW_RX = re.compile(
    r"(?ix)(health ke bare|health ke baare|meri sehat|mere health|overall health|"
    r"health overview|sehat ke bare)"
)
_HOUSE_RX = re.compile(
    r"(?ix)\b(?:(?:(\d{1,2})(?:st|nd|rd|th)?)\s*(?:ghar|house)|(?:ghar|house|h)\s*(\d{1,2})|"
    r"h\s*(\d{1,2}))\b"
)
_PLANET_IN_HOUSE_RX = re.compile(
    r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
    r".{0,40}?(?:(?:ghar|house|h)\s*(\d{1,2})|(\d{1,2})(?:st|nd|rd|th)?\s*(?:ghar|house))"
)

# Question focus → preferred EE block id suffixes / patterns (must exist in EE).
_FOCUS_WANT: dict[str, dict[str, Any]] = {
    "travel_health": {
        "label": "Travel + health — question-relevant EE blocks",
        "lords": ("h3", "h6", "h9", "h12"),
        "houses": (3, 6, 9, 12),
        "dims": ("preventive_risk", "chronic_tendency", "overall_vitality"),
        "want_keys": ("afflictions", "health_houses", "lagnesh", "sub_flags"),
    },
    "surgery_risk": {
        "label": "Surgery risk — question-relevant EE blocks",
        "lords": ("h6", "h8"),
        "houses": (6, 8, 12),
        "dims": ("surgery_risk_tone", "chronic_tendency", "recovery_capacity"),
        "want_keys": ("afflictions", "health_houses"),
        "planets": ("Mars", "Saturn"),
    },
    "mental_stress": {
        "label": "Mental stress — question-relevant EE blocks",
        "lords": ("h4", "h6"),
        "houses": (4, 6),
        "dims": ("mental_stress", "overall_vitality"),
        "want_keys": ("afflictions", "sub_flags", "lagnesh"),
        "planets": ("Moon",),
    },
    "respiratory": {
        "label": "Cold / respiratory — question-relevant EE blocks",
        "lords": ("h6",),
        "houses": (3, 6),
        "dims": ("preventive_risk", "chronic_tendency"),
        "want_keys": ("afflictions", "health_houses"),
        "planets": ("Moon", "Saturn", "Venus"),
    },
    "chronic": {
        "label": "Chronic — question-relevant EE blocks",
        "lords": ("h6", "h8"),
        "houses": (6, 8, 12),
        "dims": ("chronic_tendency", "recovery_capacity"),
        "want_keys": ("afflictions", "health_houses"),
    },
    "overview": {
        "label": "Overview — question-relevant EE blocks",
        "lords": ("h1",),
        "houses": (1, 6),
        "dims": ("overall_vitality", "mental_stress", "chronic_tendency"),
        "want_keys": ("sub_flags", "lagnesh", "vitality_score"),
    },
    "cause": {
        "label": "Why / cause — question-relevant EE blocks",
        "lords": ("h6", "h8"),
        "houses": (6, 8, 12),
        "dims": ("preventive_risk", "chronic_tendency", "overall_vitality"),
        "want_keys": ("afflictions", "health_houses", "lagnesh"),
    },
    "general_health": {
        "label": "General health — question-relevant EE blocks",
        "lords": ("h1", "h6", "h8", "h12"),
        "houses": (1, 6, 8, 12),
        "dims": ("overall_vitality", "chronic_tendency", "preventive_risk"),
        "want_keys": ("afflictions", "health_houses", "lagnesh", "sub_flags"),
    },
}


def classify_health_question_focus(question: str) -> str:
    q = (question or "").strip()
    if not q:
        return "general_health"
    if _TRAVEL_RX.search(q) and re.search(
        r"(?ix)\b(health|sehat|issue|problem|bimari|beemar|sick|tabiyat|immunity)\b", q
    ):
        return "travel_health"
    if _SURGERY_RX.search(q):
        return "surgery_risk"
    if _STRESS_RX.search(q):
        return "mental_stress"
    if _RESP_RX.search(q):
        return "respiratory"
    if _CHRONIC_RX.search(q):
        return "chronic"
    if _OVERVIEW_RX.search(q):
        return "overview"
    if re.search(r"(?ix)\b(kyun|kyon|why|kaise|how)\b", q):
        return "cause"
    return "general_health"


def _execution_from_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = checks.get("health_engine_execution")
    if isinstance(pack, dict) and pack:
        return pack
    if meta.get("d1") or meta.get("d9"):
        return {"d1": meta.get("d1") or {}, "d9": meta.get("d9") or {}}
    return {
        "d1": checks.get("d1_health_facts") or {},
        "d9": checks.get("d9_health_facts") or {},
    }


def _chart_ok(chart: Any) -> dict[str, Any]:
    if not isinstance(chart, dict) or chart.get("error"):
        return {}
    return chart


def _planet_house_map(execution: dict[str, Any]) -> dict[str, set[int]]:
    out: dict[str, set[int]] = {}
    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        for row in chart.get("planets") or []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            house = int(row.get("house") or 0)
            if name and house:
                out.setdefault(name.lower(), set()).add(house)
    return out


def _shadbala_pct(row: dict[str, Any]) -> str:
    sb = row.get("shadbala")
    if not isinstance(sb, dict):
        return ""
    pct = sb.get("strength_pct")
    if pct is None and sb.get("total") is not None and sb.get("required"):
        try:
            pct = round(100.0 * float(sb["total"]) / float(sb["required"]), 1)
        except (TypeError, ValueError, ZeroDivisionError):
            pct = None
    return f"shadbala={pct}%" if pct is not None else ""


def _planet_strength_detail(row: dict[str, Any]) -> tuple[str, int]:
    """Human detail + priority score (higher = speak first; weak > strong)."""
    dignity = str(row.get("dignity") or "").strip().lower() or "?"
    score = int(row.get("strength_score") or 0)
    parts = [
        str(row.get("sign") or ""),
        f"dignity={dignity}",
        f"strength_score={score}",
    ]
    sb = _shadbala_pct(row)
    if sb:
        parts.append(sb)
    if row.get("retrograde"):
        parts.append("retrograde")
    if row.get("combust"):
        parts.append("combust")
    # Weak first for health "kyun" answers
    priority = 50 - (score * 12)
    dig = dignity
    if dig in ("debilitated", "debility", "enemy", "fall"):
        priority += 40
    elif dig in ("exalted", "exaltation", "own", "moolatrikona", "friend"):
        priority -= 25
    if row.get("combust"):
        priority += 15
    if row.get("retrograde"):
        priority += 8
    return " | ".join(p for p in parts if p), priority


def _lord_strength_detail(st: dict[str, Any]) -> tuple[str, int]:
    lord = str(st.get("lord") or "").strip()
    lord_h = st.get("lord_house")
    dig = str(st.get("lord_dignity") or "").strip().lower() or "?"
    score = int(st.get("lord_strength_score") or 0)
    parts = [lord]
    if lord_h:
        parts.append(f"in H{lord_h}")
    parts.append(f"dignity={dig}")
    parts.append(f"strength_score={score}")
    if st.get("lord_in_dusthana"):
        parts.append("lord_in_dusthana")
    sb = st.get("lord_shadbala")
    if isinstance(sb, dict) and sb.get("strength_pct") is not None:
        parts.append(f"shadbala={sb.get('strength_pct')}%")
    priority = 50 - (score * 12)
    if dig in ("debilitated", "debility", "enemy", "fall"):
        priority += 40
    elif dig in ("exalted", "exaltation", "own", "moolatrikona", "friend"):
        priority -= 25
    if st.get("lord_in_dusthana"):
        priority += 30
    return " | ".join(str(p) for p in parts if p), priority


def question_relevant_blocks_from_execution(
    question: str,
    execution: dict[str, Any],
) -> tuple[str, str, list[dict[str, Any]]]:
    """
    Question-specific blocks that EXIST in Engine Execution only,
    enriched with dignity/strength and sorted weak-first for LLM priority.
    """
    focus = classify_health_question_focus(question)
    want = _FOCUS_WANT.get(focus) or _FOCUS_WANT["general_health"]
    label = str(want["label"])
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        block_id: str,
        block_label: str,
        why: str,
        detail: str = "",
        *,
        priority: int = 0,
        role: str = "neutral",
    ) -> None:
        if block_id in seen:
            return
        seen.add(block_id)
        row: dict[str, Any] = {
            "id": block_id,
            "label": block_label,
            "why": why,
            "priority": int(priority),
            "role": role,
        }
        if detail:
            row["detail"] = detail
        out.append(row)

    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        if not chart:
            continue
        prefix = chart_key.upper()

        lords = chart.get("house_lords") if isinstance(chart.get("house_lords"), dict) else {}
        for hk in want.get("lords") or ():
            st = lords.get(hk)
            if not isinstance(st, dict):
                continue
            detail, pr = _lord_strength_detail(st)
            role = "weak" if pr >= 60 else ("strong" if pr <= 20 else "neutral")
            add(
                f"{chart_key}.house_lords.{hk}",
                f"{prefix} · {hk.upper()} lord",
                f"Question focus={focus}; lord dignity/strength from EE",
                detail,
                priority=pr + 10,
                role=role,
            )

        planets = chart.get("planets") if isinstance(chart.get("planets"), list) else []
        want_houses = set(want.get("houses") or ())
        want_planets = {str(p).lower() for p in (want.get("planets") or ())}
        for row in planets:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            house = int(row.get("house") or 0)
            if not name:
                continue
            if house in want_houses or name.lower() in want_planets:
                detail, pr = _planet_strength_detail(row)
                role = "weak" if pr >= 60 else ("strong" if pr <= 20 else "neutral")
                add(
                    f"{chart_key}.planet.{name}.H{house}",
                    f"{prefix} · {name} in H{house}",
                    f"Question focus={focus}; planet dignity/strength from EE",
                    detail,
                    priority=pr,
                    role=role,
                )

        for key in want.get("want_keys") or ():
            val = chart.get(key)
            if val is None or val == "" or val == [] or val == {}:
                continue
            detail = ""
            pr = 40
            if key == "afflictions" and isinstance(val, list):
                detail = "; ".join(str(x) for x in val[:3])
                pr = 70
            elif key == "health_houses" and isinstance(val, list):
                hs = [str(r.get("house")) for r in val if isinstance(r, dict) and r.get("house")]
                detail = "H" + ", H".join(hs) if hs else ""
                pr = 45
            elif key == "lagnesh" and isinstance(val, dict):
                detail, pr = _lord_strength_detail(val)
            add(
                f"{chart_key}.{key}",
                f"{prefix} · {key}",
                f"Question focus={focus}; present in EE",
                detail,
                priority=pr,
                role="weak" if pr >= 60 else "neutral",
            )

        dims = chart.get("dimensions") if isinstance(chart.get("dimensions"), dict) else {}
        for dim in want.get("dims") or ():
            if dim not in dims:
                continue
            st = dims.get(dim) if isinstance(dims.get(dim), dict) else {}
            verdict = str(st.get("verdict") or "").upper()
            detail = f"verdict={verdict}"
            if st.get("reason"):
                detail += f" | {str(st.get('reason'))[:80]}"
            pr = 55 if verdict == "RED" else (45 if verdict == "YELLOW" else 25)
            add(
                f"{chart_key}.dimensions.{dim}",
                f"{prefix} · Dimension · {dim}",
                f"Question focus={focus}; dimension from EE",
                detail,
                priority=pr,
                role="weak" if verdict in ("RED", "YELLOW") else "strong",
            )

    out.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
    for i, block in enumerate(out, start=1):
        block["rank"] = i
    return focus, label, out


def format_priority_facts_for_llm(blocks: list[dict[str, Any]], *, limit: int = 5) -> str:
    """Compact ranked facts for narrator — weak / question-relevant first."""
    if not blocks:
        return ""
    lines = [
        "QUESTION_PRIORITY_FACTS (from Engine Execution only — use in this order):",
        "Rules: #1 = main reason for this question; max 2–3 facts; weak/dignity pressure > exalted support;",
        "do not invent planets outside this list; exalted/strong = support only, not illness claim.",
    ]
    for b in blocks[: max(1, limit)]:
        rank = b.get("rank") or "?"
        role = b.get("role") or "neutral"
        lines.append(
            f"#{rank} [{role}] {b.get('label')}: {b.get('detail') or b.get('why')}"
        )
    return "\n".join(lines)


def used_blocks_from_execution(
    answer: str,
    execution: dict[str, Any],
    *,
    relevant_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Answer cites that match EE — prefer highlighting ones in question-relevant set."""
    text = (answer or "").strip()
    planet_houses = _planet_house_map(execution)
    relevant_ids = relevant_ids or set()

    planets: list[str] = []
    for name in _PLANET_NAMES:
        if re.search(rf"\b{re.escape(name)}\b", text, re.I) and name.lower() in planet_houses:
            planets.append(name)

    houses: list[int] = []
    for m in _HOUSE_RX.finditer(text):
        for g in m.groups():
            if g:
                h = int(g)
                if 1 <= h <= 12 and any(h in hs for hs in planet_houses.values()):
                    houses.append(h)
    houses = sorted(set(houses))

    cites: list[str] = []
    for m in _PLANET_IN_HOUSE_RX.finditer(text):
        planet = str(m.group(1) or "").strip()
        house_s = m.group(2) or m.group(3)
        if not planet or not house_s:
            continue
        house = int(house_s)
        allowed = planet_houses.get(planet.lower()) or set()
        if house in allowed:
            cites.append(f"{planet} H{house}")

    dim_keys: set[str] = set()
    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        dims = chart.get("dimensions") if isinstance(chart.get("dimensions"), dict) else {}
        dim_keys.update(str(k) for k in dims.keys())

    dim_hits: list[str] = []
    for key, words in (
        ("overall_vitality", r"(?ix)vitality|energy|foundation"),
        ("mental_stress", r"(?ix)\bstress\b|mann|mental|tension|neend"),
        ("chronic_tendency", r"(?ix)chronic|lambi|baar\s+baar"),
        ("preventive_risk", r"(?ix)immunity|prevent|recurr"),
        ("surgery_risk_tone", r"(?ix)operation|surgery|procedure"),
        ("recovery_capacity", r"(?ix)recover|recovery|heal"),
    ):
        if key in dim_keys and re.search(words, text):
            dim_hits.append(key)

    used_blocks: list[dict[str, str]] = []
    if cites:
        used_blocks.append({
            "id": "execution.planet_house_cites",
            "label": "Planet + house (from EE)",
            "detail": ", ".join(cites),
            "why": "Matched Engine Execution placements",
        })
    if planets and not cites:
        used_blocks.append({
            "id": "execution.planets",
            "label": "Planets named (from EE)",
            "detail": ", ".join(planets),
            "why": "Planet exists in Engine Execution",
        })
    if houses:
        used_blocks.append({
            "id": "execution.houses",
            "label": "Houses (from EE)",
            "detail": ", ".join(f"H{h}" for h in houses),
            "why": "House exists in Engine Execution",
        })
    for dim in dim_hits:
        used_blocks.append({
            "id": f"d1.dimensions.{dim}",
            "label": f"Dimension · {dim}",
            "detail": dim,
            "why": "Dimension present in Engine Execution",
        })
    if not used_blocks and text:
        used_blocks.append({
            "id": "execution.plain_language",
            "label": "Plain-language answer",
            "detail": "No explicit EE planet/house cite in text",
            "why": "Full EE still available to LLM",
        })

    # Mark overlap with question-relevant set
    relevant_hit = False
    for c in cites:
        # "Saturn H6" → look for planet.Saturn.H6
        m = re.match(r"(\w+)\s+H(\d+)$", c)
        if m and any(
            f".planet.{m.group(1)}.H{m.group(2)}" in rid for rid in relevant_ids
        ):
            relevant_hit = True
            break
    return {
        "planets": planets,
        "houses": houses,
        "planet_house_cites": cites,
        "dimension_themes": dim_hits,
        "blocks": used_blocks,
        "source": "health_engine_execution",
        "matched_question_relevant": relevant_hit,
    }


def build_health_selected_blocks(
    question: str,
    answer: str = "",
    *,
    meta: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Step-4: question-specific EE blocks only (not full EE dump)."""
    meta = meta if isinstance(meta, dict) else {}
    pack = execution if isinstance(execution, dict) and execution else _execution_from_meta(meta)
    focus, focus_label, relevant = question_relevant_blocks_from_execution(question, pack)
    used = used_blocks_from_execution(
        answer, pack, relevant_ids={b["id"] for b in relevant},
    )
    priority_text = format_priority_facts_for_llm(relevant, limit=5)

    contract: dict[str, str] = {}
    for key in ("user_wants", "intent", "normalized_question", "question_type"):
        val = str(meta.get(key) or "").strip()
        if val:
            contract[key] = val

    notes = [
        "Source: Engine Execution only — dignity/strength included; ranked weak-first.",
        f"Question focus={focus}: top facts are for LLM priority reading (not full EE dump).",
        "LLM still receives full D1/D9; QUESTION_PRIORITY_FACTS tell pehle kya bolna.",
    ]
    if not relevant:
        notes.append("No matching question-relevant keys found inside Engine Execution.")

    return {
        "applies": True,
        "source": "health_engine_execution",
        "focus": focus,
        "focus_label": focus_label,
        "available_blocks": relevant,
        "expected_blocks": relevant,
        "used_in_answer": used,
        "priority_facts_for_llm": priority_text,
        "overlap_notes": notes,
        "contract": contract,
        "expected_block_ids": sorted({b["id"] for b in relevant}),
        "has_d1": bool(_chart_ok(pack.get("d1"))),
        "has_d9": bool(_chart_ok(pack.get("d9"))),
        "question": (question or "").strip()[:200],
    }
