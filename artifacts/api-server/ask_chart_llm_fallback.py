"""D1-first LLM fallback when domain engine / selected blocks do not link.

Contract:
  • D1 always present for personal chart answers.
  • Selected domain blocks when engine links; else full structured D1 block.
  • Never return generic engine_required refusal when D1 exists + in-scope question.
"""
from __future__ import annotations

from typing import Any

_SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
_SIGN_ALIASES = {
    "mesh": "Aries", "mesha": "Aries", "vrishabh": "Taurus", "mithun": "Gemini",
    "kark": "Cancer", "karka": "Cancer", "simha": "Leo", "kanya": "Virgo",
    "tula": "Libra", "vrishchik": "Scorpio", "dhanu": "Sagittarius",
    "makar": "Capricorn", "kumbh": "Aquarius", "meen": "Pisces",
}
_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def chart_has_d1(kundli: Any) -> bool:
    if not isinstance(kundli, dict):
        return False
    planets = kundli.get("planets")
    return isinstance(planets, list) and len(planets) > 0


def in_ask_scope(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    try:
        from ask_scope_gate import assess_ask_scope

        return bool(assess_ask_scope(q).allowed)
    except Exception:
        return True


def d1_llm_fallback_allowed(
    question: str,
    kundli: Any,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    """Personal in-scope question with saved D1 → always allow chart+LLM answer."""
    if not chart_has_d1(kundli):
        return False
    if not in_ask_scope(question):
        return False
    branch = str((llm_intent or {}).get("branch") or "engine").strip().lower()
    if branch == "knowledge":
        return True
    return True


def build_basic_d1_full_block(
    kundli: Any,
    *,
    question: str = "",
    birth: Any = None,
) -> str:
    """Structured full D1 block for LLM when no domain selected sections linked."""
    if not chart_has_d1(kundli):
        return "(no D1 chart data available)"

    lines: list[str] = [
        "=== D1 FULL BLOCK (LLM — analyze question + these positions) ===",
    ]
    if (question or "").strip():
        lines.append(f"Question lock: {(question or '').strip()[:400]}")

    asc = kundli.get("ascendant") or kundli.get("lagna")
    asc_deg = kundli.get("ascendantDeg")
    if asc:
        deg = f" {asc_deg:.2f}°" if isinstance(asc_deg, (int, float)) else ""
        lines.append(f"Ascendant (Lagna): {asc}{deg}")

    try:
        asc_key = str(asc or "").strip()
        asc_canon = _SIGN_ALIASES.get(asc_key.lower(), asc_key.title())
        if asc_canon in _SIGNS:
            ai = _SIGNS.index(asc_canon)
            pairs = []
            for h in range(1, 13):
                sg = _SIGNS[(ai + h - 1) % 12]
                pairs.append(f"{h}H={sg} lord {_SIGN_LORDS[sg]}")
            lines.append("House lords (D1): " + "; ".join(pairs))
    except Exception:
        pass

    for key, label in (
        ("moonSign", "Moon sign (Rashi)"),
        ("sunSign", "Sun sign"),
        ("nakshatra", "Janma Nakshatra"),
    ):
        val = kundli.get(key)
        if val:
            lines.append(f"{label}: {val}")

    planets = kundli.get("planets") or []
    lines.append("\nPlanets in D1 (all):")
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = p.get("name", "?")
        sign = p.get("sign", "?")
        house = p.get("house", "?")
        deg = p.get("degrees", "")
        retro = " [R]" if p.get("retrograde") else ""
        dig = p.get("dignity") or p.get("dignityName") or ""
        dig_s = f" [{dig}]" if dig else ""
        lines.append(f"  • {name}: {sign} House {house} {deg}{retro}{dig_s}")

    if isinstance(birth, dict):
        place = birth.get("place") or birth.get("pob")
        if place:
            lines.append(f"\nBirth place: {place}")

    lines.append(
        "\nINSTRUCTION: Answer ONLY from these D1 facts + the user's question. "
        "Do not invent placements. If signal is weak, say so clearly."
    )
    return "\n".join(lines)


def build_chart_text_for_llm_answer(
    kundli: Any,
    *,
    question: str = "",
    birth: Any = None,
    selected_block_text: str = "",
) -> str:
    """Prefer domain selected blocks; else full D1 block (D1 always included)."""
    sel = (selected_block_text or "").strip()
    if sel and sel != "(no chart data available)":
        d1 = build_basic_d1_full_block(kundli, question=question, birth=birth)
        return f"{sel.strip()}\n\n--- D1 BASE (always) ---\n{d1}"
    return build_basic_d1_full_block(kundli, question=question, birth=birth)


def extract_selected_block_text(
    *,
    checks: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
    marriage_block: str = "",
    career_block: str = "",
    domain_timing_block: str = "",
) -> str:
    """Collect domain engine blocks + DNA selected priority facts for LLM context."""
    parts: list[str] = []

    for raw in (marriage_block, career_block):
        b = (raw or "").strip()
        if b and b != "(no chart data available)":
            parts.append(b)

    dt = (domain_timing_block or "").strip()
    if dt:
        try:
            from ask_hard_guards import is_real_timing_engine_block

            if is_real_timing_engine_block(dt):
                parts.append(dt)
        except Exception:
            parts.append(dt)

    merged: dict[str, Any] = {}
    if isinstance(checks, dict):
        merged.update(checks)
    sm = slice_meta if isinstance(slice_meta, dict) else {}
    sm_checks = sm.get("checks") if isinstance(sm.get("checks"), dict) else {}
    for k, v in sm_checks.items():
        merged.setdefault(k, v)

    seen_pf: set[str] = set()
    for key, val in merged.items():
        if not isinstance(val, dict):
            continue
        if not (
            key.endswith("_selected_blocks")
            or key.endswith("_selected_blocks_preview")
        ):
            continue
        pf = (val.get("priority_facts_for_llm") or "").strip()
        if not pf:
            exp = val.get("expected_blocks") or val.get("available_blocks") or []
            if isinstance(exp, list) and exp:
                try:
                    from ask_selected_blocks_common import format_priority_facts_for_llm_common

                    pf = format_priority_facts_for_llm_common(exp)
                except Exception:
                    pf = ""
        if pf and pf not in seen_pf:
            seen_pf.add(pf)
            parts.append(pf)

    return "\n\n".join(parts).strip()
