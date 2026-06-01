"""Structured chart proof for Love Reality mobile UI (D1 + D9 + aspects)."""
from __future__ import annotations

from typing import Any

from vedic.love_reality.relationship_signals import CoupleSignals
from vedic.love_reality.scoring_core import KundliReader


def _fmt_deg(p: dict | None) -> str:
    if not p:
        return "—"
    d = p.get("degrees")
    if d:
        return str(d).replace(" ", "")
    lon = p.get("longitude")
    if lon is not None:
        deg = float(lon) % 30
        d_i = int(deg)
        m_i = int((deg - d_i) * 60)
        return f"{d_i}°{m_i:02d}'"
    return "—"


def _dignity_tag(k: KundliReader, planet: str, sign: str) -> str | None:
    d = k.dignity(planet, k.sidx(sign))
    if d <= -2:
        return "Debilitated"
    if d >= 2:
        return "Exalted"
    if d == 1:
        return "Own Sign"
    if d < 0:
        return "Enemy Sign"
    return None


def _planet_row(k: KundliReader, name: str, *, d9: bool = False) -> dict[str, Any] | None:
    p = k.d9(name) if d9 else k.planet(name)
    if not p:
        return None
    sign = str(p.get("sign") or "?")
    tag = _dignity_tag(k, name, sign) if not d9 else None
    if d9:
        si = p.get("signIndex")
        if si is not None:
            try:
                d9_d = k.dignity(name, int(si))
                if d9_d <= -2:
                    tag = "D9 Debilitated"
                elif d9_d >= 1:
                    tag = "D9 Strong"
            except (TypeError, ValueError):
                pass
    prefix = "D9 " if d9 else ""
    line = f"{prefix}{name}: {sign} ({_fmt_deg(p)})"
    if tag:
        line += f" — {tag}"
    return {"planet": name, "line": line, "tag": tag}


def _seventh_lord_row(k: KundliReader) -> dict[str, Any]:
    h7l = k.house_lord(7)
    p7 = k.planet(h7l)
    if not p7:
        return {"planet": "7th Lord", "line": f"7th Lord: {h7l} (—)", "tag": None}
    sign = str(p7.get("sign") or "?")
    house = p7.get("house")
    tag = _dignity_tag(k, h7l, sign)
    line = f"7th Lord {h7l}: {sign} ({_fmt_deg(p7)})"
    if house:
        line += f" · H{house}"
    if tag:
        line += f" — {tag}"
    return {"planet": "7th Lord", "line": line, "tag": tag}


def _aspect_badges(sig: CoupleSignals) -> list[dict[str, str]]:
    badges: list[dict[str, str]] = []

    def add(icon: str, label: str) -> None:
        if len(badges) < 4 and label not in [b["label"] for b in badges]:
            badges.append({"icon": icon, "label": label})

    if sig.cross_rahu_venus:
        add("🔒", "Cross-Chart Rahu–Venus Alignment Found")
    if sig.p1.saturn_on_7th or sig.p2.saturn_on_7th:
        add("⚡", "Saturn 7th House Aspect Active")
    if sig.p1.mars_on_7th or sig.p2.mars_on_7th:
        add("🔥", "Mars 7th Axis Pressure Detected")
    if sig.p1.rahu_on_7th_axis or sig.p2.rahu_on_7th_axis:
        add("🌀", "Rahu/Ketu on 7th — Karmic Pull")
    if sig.p1.venus_mars_conjunct or sig.p2.venus_mars_conjunct:
        add("💫", "Venus–Mars Conjunction — Passion Surge")
    if sig.p1.moon_in_8th or sig.p2.moon_in_8th:
        add("🌙", "Moon in 8th — Hidden Emotional Layer")
    if sig.p1.seventh_lord_dusthana or sig.p2.seventh_lord_dusthana:
        add("⚠️", "7th Lord in Dusthana (6/8/12)")
    if sig.moon_mismatch:
        add("🌓", "Moon–Moon Rhythm Clash Between Charts")
    if sig.p1.third_person_risk or sig.p2.third_person_risk:
        add("👁", "Third-Person / Secrecy Risk on Love Axis")

    if len(badges) < 2:
        for note in sig.synastry_notes[:2]:
            add("✦", note[:72] + ("…" if len(note) > 72 else ""))
    return badges[:2]


def _cosmic_hook(sig: CoupleSignals) -> str:
    d9_weak = sum(1 for p in (sig.p1, sig.p2) if p.venus_d9_weak or p.moon_d9_debil)
    d9_strong = sum(
        1
        for p in (sig.p1, sig.p2)
        if not p.venus_d9_weak and not p.moon_d9_debil and not p.venus_debil
    )
    flags = sum(
        1
        for p in (sig.p1, sig.p2)
        for flag in (
            p.seventh_lord_dusthana,
            p.saturn_on_7th,
            p.third_person_risk,
            p.venus_mars_conjunct,
            p.moon_in_8th,
        )
        if flag
    )
    if sig.cross_rahu_venus:
        flags += 1

    if d9_strong >= 1 and flags >= 2:
        return (
            "Your core commitment layers (D9) show real alignment, but "
            f"{flags} hidden chart red flags are creating immediate risks."
        )
    if d9_weak >= 2:
        return (
            "Navamsa (D9) commitment layers are strained on both charts — "
            "surface chemistry may outrun long-term stability."
        )
    if flags >= 2:
        return (
            f"Vedic engines flagged {flags} active afflictions on the 7th/Venus/Moon axis — "
            "timing and behavior will decide the next chapter."
        )
    if sig.moon_mismatch:
        return (
            "Moon rhythms clash between charts — emotional language differs even when love feels strong."
        )
    return (
        "D1 + D9 snapshots below match our scoring engines — "
        "full aspect math and remedies sit in the Pro PDF."
    )


def build_chart_proof(r1: KundliReader, r2: KundliReader, sig: CoupleSignals) -> dict[str, Any]:
    def rows_for(k: KundliReader) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for pl in ("Venus", "Moon"):
            row = _planet_row(k, pl)
            if row:
                out.append(row)
        out.append(_seventh_lord_row(k))
        v9 = _planet_row(k, "Venus", d9=True)
        if v9:
            out.append(v9)
        return out[:4]

    return {
        "p1_name": r1.name,
        "p2_name": r2.name,
        "p1_rows": rows_for(r1),
        "p2_rows": rows_for(r2),
        "aspect_badges": _aspect_badges(sig),
        "cosmic_hook": _cosmic_hook(sig),
        "combined_affliction": sig.combined_affliction,
    }


def attach_chart_proof(payload: dict[str, Any], p1: dict, p2: dict) -> dict[str, Any]:
    """Mutate and return payload with chart_proof block."""
    from kundli_engine import calculate_kundli
    from vedic.love_reality.relationship_signals import analyze_couple

    k1 = calculate_kundli({**p1, "name": p1.get("name") or "You"})
    k2 = calculate_kundli({**p2, "name": p2.get("name") or "Partner"})
    r1, r2 = KundliReader(k1), KundliReader(k2)
    sig = analyze_couple(r1, r2)
    out = dict(payload)
    out["chart_proof"] = build_chart_proof(r1, r2, sig)
    return out
