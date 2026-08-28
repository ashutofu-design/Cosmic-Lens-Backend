"""Shared helpers for engine-execution packs (D1/D9 module visibility)."""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_D1_EXPLICIT_RX = re.compile(r"(?ix)\b(d1|birth\s*chart|rashi\s*chart|lagna)\b")
_D9_EXPLICIT_RX = re.compile(r"(?ix)\b(d9|navamsa|navamsha|vargottama)\b")
_DASHA_RX = re.compile(
    r"(?ix)\b(dasha|mahadasha|antardasha|pratyantar|\bmd\b|\bad\b|\bpd\b)\b"
)
_TRANSIT_RX = re.compile(r"(?ix)\b(transit|gochar)\b")
_DIVISIONAL_RX = re.compile(r"(?ix)\b(d\d{1,2})\b")
_TIME_REF_RX = re.compile(
    r"(?ix)\b("
    r"20\d\d|19\d\d|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
    r"mahin[ae]|mahino|saal|varsh|month|year|week|window|period|phase|"
    r"jald|soon|currently|running"
    r")\b"
)
_PLANET_IN_HOUSE_RX = re.compile(
    r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
    r".{0,48}?(?:(?:ghar|house|h)\s*(\d{1,2})|(\d{1,2})(?:st|nd|rd|th)?\s*(?:ghar|house))"
)


def chart_module_ok(facts: Any) -> bool:
    """True when a D1/D9 chart slice has usable data (not error-only)."""
    if not isinstance(facts, dict):
        return False
    if facts.get("error"):
        return False
    if facts.get("planets"):
        return True
    if facts.get("house_lords"):
        return True
    if facts.get("karakas"):
        return True
    if facts.get("domain_houses"):
        return True
    if facts.get("health_houses") or facts.get("relationship_houses"):
        return True
    return bool(facts.get("ascendant"))


def _chart_planet_houses(chart: Any) -> dict[str, set[int]]:
    out: dict[str, set[int]] = {}
    if not chart_module_ok(chart):
        return out
    for row in chart.get("planets") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip().lower()
        try:
            house = int(row.get("house") or 0)
        except (TypeError, ValueError):
            house = 0
        if name and 1 <= house <= 12:
            out.setdefault(name, set()).add(house)
    return out


def _extract_planet_house_cites(answer: str) -> list[tuple[str, int]]:
    cites: list[tuple[str, int]] = []
    for m in _PLANET_IN_HOUSE_RX.finditer(answer or ""):
        planet = str(m.group(1) or "").strip()
        house_s = m.group(2) or m.group(3)
        if not planet or not house_s:
            continue
        house = int(house_s)
        if 1 <= house <= 12:
            cites.append((planet, house))
    return cites


def _default_modules(pack: dict[str, Any]) -> list[str]:
    charts = pack.get("charts_used")
    if isinstance(charts, list) and charts:
        return [str(c).strip().upper() for c in charts if str(c).strip()]
    mods = ["D1"]
    if chart_module_ok(pack.get("d9")):
        mods.append("D9")
    if isinstance(pack.get("dasha_timing_compact"), dict) and (
        pack["dasha_timing_compact"].get("current")
        or pack["dasha_timing_compact"].get("top_windows")
    ):
        mods.append("DASHA")
    div = str(pack.get("divisional_chart_tag") or "").strip().upper()
    if div and div not in mods and div != "D9":
        mods.append(div)
    return mods


def _module_engine_loaded(module: str, pack: dict[str, Any]) -> bool:
    mod = module.strip().upper()
    if mod == "D1":
        return chart_module_ok(pack.get("d1"))
    if mod == "D9":
        return chart_module_ok(pack.get("d9"))
    if mod == "DASHA":
        dc = pack.get("dasha_timing_compact")
        if isinstance(dc, dict):
            return bool(dc.get("current") or dc.get("top_windows")) and not dc.get("error")
        return False
    if mod == "TRANSIT":
        return bool(pack.get("transit") or pack.get("transit_facts"))
    if re.fullmatch(r"D\d{1,2}", mod):
        div = pack.get("divisional_chart")
        if isinstance(div, dict) and str(div.get("chart") or "").upper() == mod:
            return chart_module_ok(div)
        if mod == str(pack.get("divisional_chart_tag") or "").upper():
            return chart_module_ok(div)
    return False


def _module_llm_used(module: str, answer: str, pack: dict[str, Any]) -> tuple[bool, str]:
    text = (answer or "").strip()
    if not text:
        return False, "no final answer"
    mod = module.strip().upper()
    cites = _extract_planet_house_cites(text)
    d1_map = _chart_planet_houses(pack.get("d1"))
    d9_map = _chart_planet_houses(pack.get("d9"))

    if mod == "D1":
        if _D1_EXPLICIT_RX.search(text):
            return True, "D1/lagna cited in answer"
        for planet, house in cites:
            if house in d1_map.get(planet.lower(), set()):
                return True, f"{planet} H{house} matches D1"
        for planet in _PLANET_NAMES:
            if re.search(rf"\b{re.escape(planet)}\b", text, re.I):
                if planet.lower() in d1_map:
                    return True, f"{planet} cited (D1 chart)"
        return False, "D1 not used in answer"

    if mod == "D9":
        if _D9_EXPLICIT_RX.search(text):
            return True, "D9/navamsa cited in answer"
        for planet, house in cites:
            pl = planet.lower()
            if house in d9_map.get(pl, set()):
                if house not in d1_map.get(pl, set()):
                    return True, f"{planet} H{house} matches D9 only"
                return True, f"{planet} H{house} matches D9"
        for row in pack.get("vargottama_details") or []:
            if not isinstance(row, dict):
                continue
            pname = str(row.get("planet") or "")
            if pname and re.search(rf"\b{re.escape(pname)}\b", text, re.I):
                if row.get("vargottama") and re.search(r"(?ix)vargottama", text):
                    return True, "vargottama cited"
        return False, "D9 not used in answer"

    if mod == "DASHA":
        if _DASHA_RX.search(text):
            return True, "dasha cited in answer"
        if _TIME_REF_RX.search(text):
            return True, "timing period cited (dasha window)"
        return False, "dasha not used in answer"

    if mod == "TRANSIT":
        if _TRANSIT_RX.search(text):
            return True, "transit/gochar cited"
        return False, "transit not used in answer"

    if re.fullmatch(r"D\d{1,2}", mod):
        if re.search(rf"(?ix)\b{re.escape(mod.lower())}\b", text):
            return True, f"{mod} cited in answer"
        div = str(pack.get("divisional_chart_tag") or "").upper()
        if mod == div:
            div_map = _chart_planet_houses(pack.get("divisional_chart"))
            for planet, house in cites:
                if house in div_map.get(planet.lower(), set()):
                    return True, f"{planet} H{house} matches {mod}"
        return False, f"{mod} not used in answer"

    return False, f"{mod} usage not detected"


def build_modules_checked(
    pack: dict[str, Any],
    *,
    answer: str = "",
    required_modules: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Per-module engine_loaded + llm_used flags for admin."""
    if not isinstance(pack, dict):
        return []
    mods = [
        str(m).strip().upper()
        for m in (required_modules or _default_modules(pack))
        if str(m).strip()
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for m in mods:
        if m not in seen:
            seen.add(m)
            ordered.append(m)

    rows: list[dict[str, Any]] = []
    for mod in ordered:
        loaded = _module_engine_loaded(mod, pack)
        used, reason = _module_llm_used(mod, answer, pack) if loaded else (False, "engine data missing")
        if not loaded:
            reason = "not loaded in engine"
        elif not used:
            reason = reason or "not cited in LLM answer"
        rows.append({
            "module": mod,
            "engine_loaded": loaded,
            "llm_used": used,
            "checked": used,
            "reason": reason,
        })
    return rows


def attach_modules_checked(
    pack: dict[str, Any],
    *,
    answer: str = "",
    required_modules: list[str] | None = None,
) -> dict[str, Any]:
    """Annotate engine execution — ticks mean LLM used module in final answer."""
    if not isinstance(pack, dict):
        return pack
    rows = build_modules_checked(pack, answer=answer, required_modules=required_modules)
    pack["modules_checked"] = rows
    d1_row = next((r for r in rows if r.get("module") == "D1"), None)
    d9_row = next((r for r in rows if r.get("module") == "D9"), None)
    pack["d1_checked"] = bool(d1_row.get("llm_used")) if d1_row else chart_module_ok(pack.get("d1"))
    pack["d9_checked"] = bool(d9_row.get("llm_used")) if d9_row else chart_module_ok(pack.get("d9"))
    pack["d1_engine_loaded"] = bool(d1_row.get("engine_loaded")) if d1_row else chart_module_ok(pack.get("d1"))
    pack["d9_engine_loaded"] = bool(d9_row.get("engine_loaded")) if d9_row else chart_module_ok(pack.get("d9"))
    used = [str(r["module"]) for r in rows if r.get("llm_used")]
    pack["modules_llm_used"] = used
    return pack
