"""LLM Selected JSON Blocks — ONLY from health Engine Execution (D1/D9).

Admin Step 4 lists blocks that exist in health_engine_execution.
LLM still receives the full pack and picks itself; this module never invents
blocks outside Engine Execution.
"""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_HOUSE_RX = re.compile(
    r"(?ix)\b(?:(?:(\d{1,2})(?:st|nd|rd|th)?)\s*(?:ghar|house)|(?:ghar|house|h)\s*(\d{1,2})|"
    r"h\s*(\d{1,2}))\b"
)
_PLANET_IN_HOUSE_RX = re.compile(
    r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
    r".{0,40}?(?:(?:ghar|house|h)\s*(\d{1,2})|(\d{1,2})(?:st|nd|rd|th)?\s*(?:ghar|house))"
)

# Top-level chart keys we surface when present in Engine Execution.
_CHART_BLOCK_KEYS: tuple[tuple[str, str], ...] = (
    ("ascendant", "Ascendant"),
    ("lagnesh", "Lagnesh (1st lord)"),
    ("planets", "Planets"),
    ("houses", "All houses"),
    ("health_houses", "Health houses (1/6/8/12)"),
    ("house_lords", "House lords (h1–h12)"),
    ("karakas", "Karakas"),
    ("shadbala", "Shadbala"),
    ("aspects", "Aspects"),
    ("afflictions", "Afflictions"),
    ("dimensions", "Health dimensions"),
    ("sub_flags", "Sub flags"),
    ("vitality_score", "Vitality score"),
    ("vitality_risk", "Vitality risk"),
)


def _execution_from_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = checks.get("health_engine_execution")
    if isinstance(pack, dict) and pack:
        return pack
    # Direct pack passed as execution=
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


def _block_present(chart: dict[str, Any], key: str) -> bool:
    val = chart.get(key)
    if val is None:
        return False
    if isinstance(val, (list, dict)):
        return bool(val)
    if isinstance(val, (int, float)):
        return True
    return bool(str(val).strip())


def available_blocks_from_execution(execution: dict[str, Any]) -> list[dict[str, str]]:
    """Only keys that exist in Engine Execution D1/D9."""
    out: list[dict[str, str]] = []
    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        if not chart:
            continue
        prefix = chart_key.upper()
        for key, label in _CHART_BLOCK_KEYS:
            if not _block_present(chart, key):
                continue
            detail = ""
            raw = chart.get(key)
            if key == "dimensions" and isinstance(raw, dict):
                detail = ", ".join(sorted(raw.keys()))
            elif key == "house_lords" and isinstance(raw, dict):
                detail = f"{len(raw)} lords"
            elif key == "planets" and isinstance(raw, list):
                names = [str(p.get("name") or "") for p in raw if isinstance(p, dict) and p.get("name")]
                detail = ", ".join(n for n in names if n)[:120]
            elif key == "afflictions" and isinstance(raw, list):
                detail = f"{len(raw)} lines"
            elif key == "health_houses" and isinstance(raw, list):
                hs = [str(r.get("house")) for r in raw if isinstance(r, dict) and r.get("house")]
                detail = "H" + ", H".join(hs) if hs else ""
            block: dict[str, str] = {
                "id": f"{chart_key}.{key}",
                "label": f"{prefix} · {label}",
                "why": "Present in Engine Execution",
            }
            if detail:
                block["detail"] = detail
            out.append(block)
        # Dimension sub-keys as separate selectable rows when present
        dims = chart.get("dimensions") if isinstance(chart.get("dimensions"), dict) else {}
        for dim_key in sorted(dims.keys()):
            out.append({
                "id": f"{chart_key}.dimensions.{dim_key}",
                "label": f"{prefix} · Dimension · {dim_key}",
                "why": "Present in Engine Execution",
            })
        # House lord rows that exist
        lords = chart.get("house_lords") if isinstance(chart.get("house_lords"), dict) else {}
        for hk in ("h1", "h6", "h8", "h12", "h3", "h4", "h9"):
            if hk in lords:
                out.append({
                    "id": f"{chart_key}.house_lords.{hk}",
                    "label": f"{prefix} · {hk.upper()} lord",
                    "why": "Present in Engine Execution",
                    "detail": str((lords.get(hk) or {}).get("lord") or ""),
                })
    return out


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


def _dimension_keys(execution: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        dims = chart.get("dimensions") if isinstance(chart.get("dimensions"), dict) else {}
        keys.update(str(k) for k in dims.keys())
    return keys


def used_blocks_from_execution(
    answer: str,
    execution: dict[str, Any],
) -> dict[str, Any]:
    """Only report answer cites that match planets/houses/dims in Engine Execution."""
    text = (answer or "").strip()
    planet_houses = _planet_house_map(execution)
    dim_keys = _dimension_keys(execution)
    available_ids = {b["id"] for b in available_blocks_from_execution(execution)}

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
            "label": "Planet + house (from Engine Execution)",
            "detail": ", ".join(cites),
            "why": "Matched D1/D9 planets in Engine Execution",
        })
    if planets and not cites:
        used_blocks.append({
            "id": "execution.planets",
            "label": "Planets named (from Engine Execution)",
            "detail": ", ".join(planets),
            "why": "Planet exists in Engine Execution",
        })
    if houses:
        used_blocks.append({
            "id": "execution.houses",
            "label": "Houses referenced (from Engine Execution)",
            "detail": ", ".join(f"H{h}" for h in houses),
            "why": "House placement exists in Engine Execution",
        })
    for dim in dim_hits:
        bid = f"d1.dimensions.{dim}"
        if bid in available_ids or f"d9.dimensions.{dim}" in available_ids:
            used_blocks.append({
                "id": bid if bid in available_ids else f"d9.dimensions.{dim}",
                "label": f"Dimension · {dim}",
                "detail": dim,
                "why": "Dimension present in Engine Execution",
            })
    if not used_blocks and text and available_ids:
        used_blocks.append({
            "id": "execution.plain_language",
            "label": "Plain-language answer",
            "detail": "No explicit planet/house cite — LLM may still have used Engine Execution internally",
            "why": "Full Engine Execution was available to LLM",
        })

    return {
        "planets": planets,
        "houses": houses,
        "planet_house_cites": cites,
        "dimension_themes": dim_hits,
        "blocks": used_blocks,
        "source": "health_engine_execution",
    }


def build_health_selected_blocks(
    question: str,
    answer: str = "",
    *,
    meta: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Step-4 payload: available + used blocks — Engine Execution only."""
    meta = meta if isinstance(meta, dict) else {}
    pack = execution if isinstance(execution, dict) and execution else _execution_from_meta(meta)
    available = available_blocks_from_execution(pack)
    used = used_blocks_from_execution(answer, pack)

    contract: dict[str, str] = {}
    for key in ("user_wants", "intent", "normalized_question", "question_type"):
        val = str(meta.get(key) or "").strip()
        if val:
            contract[key] = val

    notes: list[str] = [
        "Source: health Engine Execution only (D1/D9). No blocks from outside this pack.",
        "LLM receives full Engine Execution; it picks relevant parts for the question.",
    ]
    if not available:
        notes.append("Engine Execution empty or missing — no blocks to list.")

    return {
        "applies": True,
        "source": "health_engine_execution",
        "focus": "engine_execution",
        "focus_label": "Engine Execution (D1 + D9) — LLM picks for the question",
        # Prefer "available_blocks"; keep expected_blocks alias for older admin UI
        "available_blocks": available,
        "expected_blocks": available,
        "used_in_answer": used,
        "overlap_notes": notes,
        "contract": contract,
        "expected_block_ids": sorted({b["id"] for b in available}),
        "has_d1": bool(_chart_ok(pack.get("d1"))),
        "has_d9": bool(_chart_ok(pack.get("d9"))),
        "question": (question or "").strip()[:200],
    }
