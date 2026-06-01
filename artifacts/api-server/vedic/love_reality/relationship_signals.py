"""Extract honest relationship affliction signals from D1 + D9."""
from __future__ import annotations

from dataclasses import dataclass, field

from vedic.love_reality.scoring_core import (
    DUSTHANA,
    KundliReader,
    MALEFIC,
    ROMANCE_HOUSES,
)


@dataclass
class PersonSignals:
    name: str
    venus_debil: bool = False
    moon_debil: bool = False
    venus_d9_weak: bool = False
    moon_afflicted: bool = False
    fifth_lord_weak: bool = False
    seventh_lord_dusthana: bool = False
    seventh_lord_debil: bool = False
    saturn_on_7th: bool = False
    rahu_on_7th_axis: bool = False
    mars_on_7th: bool = False
    ketu_detachment: bool = False
    third_person_risk: bool = False
    separation_yoga: bool = False
    reconnection_yoga: bool = False
    emotional_instability: bool = False
    moon_in_8th: bool = False
    moon_d9_debil: bool = False
    venus_mars_conjunct: bool = False
    venus_surface_strong_only: bool = False
    loyalty_risk_high: bool = False
    affliction_weight: int = 0
    notes: list[str] = field(default_factory=list)


@dataclass
class CoupleSignals:
    p1: PersonSignals
    p2: PersonSignals
    moon_mismatch: bool = False
    cross_rahu_venus: bool = False
    combined_affliction: int = 0
    synastry_notes: list[str] = field(default_factory=list)


def _analyze_person(k: KundliReader) -> PersonSignals:
    s = PersonSignals(name=k.name)
    w = 0

    venus = k.planet("Venus")
    moon = k.planet("Moon")
    if venus:
        vd = k.dignity("Venus", k.sidx(venus["sign"]))
        if vd <= -2:
            s.venus_debil = True
            w += 14
            s.notes.append(f"{k.name}'s Venus debilitated — love nature unstable, validation-seeking.")
        elif vd < 0:
            w += 6
            s.notes.append(f"{k.name}'s Venus in enemy territory — affection inconsistent under stress.")
        elif vd >= 1:
            s.venus_surface_strong_only = True
            w += 2
        if venus.get("house") in DUSTHANA:
            w += 8
            s.notes.append(f"{k.name}'s Venus in dusthana — romance meets duty, guilt, or secrecy.")
        if "Rahu" in k.aspects_planet("Venus") or "Ketu" in k.aspects_planet("Venus"):
            w += 7
            s.emotional_instability = True
            s.notes.append(f"{k.name}'s Venus under nodal pull — attraction mixed with confusion.")

    v9 = k.d9("Venus")
    if v9 is not None:
        si = v9.get("signIndex", v9.get("sign", 0))
        if isinstance(si, str):
            si = k.sidx(si)
        if k.dignity("Venus", int(si)) <= -1:
            s.venus_d9_weak = True
            w += 6
            s.notes.append(f"{k.name}'s Navamsa Venus weak — inner commitment layer fragile.")

    if k.share_house("Venus", "Mars"):
        s.venus_mars_conjunct = True
        s.loyalty_risk_high = True
        w += 14
        s.notes.append(
            f"{k.name}'s Venus-Mars conjunction — passion impulse can override loyalty; "
            f"do NOT read as 'naturally loyal'."
        )

    if moon:
        if moon.get("house") == 8:
            s.moon_in_8th = True
            s.loyalty_risk_high = True
            w += 12
            s.notes.append(
                f"{k.name}'s Moon in 8th — hidden emotional layers; secrecy and loyalty tests likely."
            )
        md = k.dignity("Moon", k.sidx(moon["sign"]))
        if md <= -2:
            s.moon_debil = True
            w += 12
            s.notes.append(f"{k.name}'s Moon debilitated — emotional reactions unpredictable.")
        m9_si = k.d9_sign_index("Moon")
        if m9_si is not None and k.dignity("Moon", m9_si) <= -2:
            s.moon_d9_debil = True
            s.loyalty_risk_high = True
            w += 10
            s.notes.append(
                f"{k.name}'s Navamsa Moon debilitated — inner commitment wavers under stress."
            )
        asp_m = k.aspects_planet("Moon")
        if "Saturn" in asp_m or "Rahu" in asp_m:
            s.moon_afflicted = True
            w += 9
            s.notes.append(f"{k.name}'s Moon under Saturn/Rahu — feelings held in, then erupt or detach.")
        if moon.get("house") in DUSTHANA:
            w += 5
            s.notes.append(f"{k.name}'s Moon in dusthana — emotional peace hard to sustain in love.")

    h5l = k.house_lord(5)
    p5 = k.planet(h5l)
    if p5:
        if p5.get("house") in DUSTHANA or k.dignity(h5l, k.sidx(p5["sign"])) <= -2:
            s.fifth_lord_weak = True
            w += 10
            s.notes.append(f"{k.name}'s 5th lord {h5l} weakened — romance spark fades under pressure.")
        elif k.dignity(h5l, k.sidx(p5["sign"])) >= 1 and p5.get("house") in ROMANCE_HOUSES:
            s.reconnection_yoga = True
            s.notes.append(f"{k.name}'s 5th lord strong — emotional reconnection capacity present.")

    h7l = k.house_lord(7)
    p7 = k.planet(h7l)
    if p7:
        if p7.get("house") in DUSTHANA:
            s.seventh_lord_dusthana = True
            w += 12
            s.notes.append(f"{k.name}'s 7th lord in dusthana — partnership survives attachment, not stability.")
        if k.dignity(h7l, k.sidx(p7["sign"])) <= -2:
            s.seventh_lord_debil = True
            w += 10
            s.notes.append(f"{k.name}'s 7th lord debilitated — commitment structure weak.")

    occ7 = k.occupants(7)
    asp7 = k.aspects_house(7)
    if "Saturn" in occ7 or "Saturn" in asp7:
        s.saturn_on_7th = True
        s.separation_yoga = True
        w += 11
        s.notes.append(f"{k.name}'s Saturn on 7th axis — distance, delay, emotional cooling.")
    if "Mars" in occ7 or "Mars" in asp7:
        s.mars_on_7th = True
        w += 9
        s.notes.append(f"{k.name}'s Mars on 7th — fights, sharp words, impulsive breaks.")
    if "Rahu" in occ7 or "Rahu" in asp7 or "Ketu" in occ7:
        s.rahu_on_7th_axis = True
        w += 10
        s.notes.append(f"{k.name}'s nodes on 7th — karmic obsession, unclear loyalty lines.")
    if "Ketu" in asp7 and "Ketu" not in occ7:
        s.ketu_detachment = True
        w += 7
        s.notes.append(f"{k.name}'s Ketu influence on 7th — quiet withdrawal, ghosting pattern.")

  # 3rd person / external pull: Rahu in 5 or 7, or 12th lord linked to 7th
    if "Rahu" in k.occupants(5) or "Rahu" in k.occupants(7):
        s.third_person_risk = True
        w += 8
        s.notes.append(f"{k.name}'s chart shows third-person / external validation risk on love axis.")
    h12l = k.house_lord(12)
    p12 = k.planet(h12l)
    if p12 and p12.get("house") == 7:
        s.third_person_risk = True
        w += 6
        s.notes.append(f"{k.name}'s 12th lord in 7th — hidden ties, secrecy, parallel attention.")

    md, ad, _ = k.dasha_triple()
    for pl in (md, ad):
        if pl in ("Saturn", "Rahu", "Ketu"):
            s.separation_yoga = True
            w += 5
            s.notes.append(f"{k.name} in {pl} dasha — timing favors distance over repair.")
        if pl in ("Venus", "Moon") and not s.venus_debil and not s.moon_debil:
            s.reconnection_yoga = True
            s.notes.append(f"{k.name} in {pl} dasha — window for emotional reopening.")

    if s.venus_surface_strong_only and (
        s.loyalty_risk_high
        or s.moon_in_8th
        or s.moon_d9_debil
        or s.venus_mars_conjunct
        or s.third_person_risk
        or s.seventh_lord_dusthana
    ):
        s.notes.append(
            f"{k.name}: Venus may look 'strong' on paper (e.g. own sign) but loyalty risk flags dominate — "
            f"surface warmth ≠ faithful behavior."
        )

    if s.loyalty_risk_high or s.third_person_risk or s.venus_mars_conjunct or s.moon_in_8th:
        s.loyalty_risk_high = True

    s.affliction_weight = w
    return s


def analyze_couple(k1: KundliReader, k2: KundliReader) -> CoupleSignals:
    p1 = _analyze_person(k1)
    p2 = _analyze_person(k2)
    notes: list[str] = []

    m1, m2 = k1.planet("Moon"), k2.planet("Moon")
    moon_mismatch = False
    if m1 and m2:
        d = abs(k1.sidx(m1["sign"]) - k2.sidx(m2["sign"]))
        d = min(d, 12 - d)
        moon_mismatch = d in (6, 7)
        if moon_mismatch:
            notes.append("Moon-Moon rhythm clashes — one holds in, the other pushes out.")
        elif d in (0, 3, 4, 9):
            notes.append("Moon-Moon supportive — emotional language can align when willing.")

    cross_rahu = False
    for label, own, other in (
        (k1.name, k1, k2),
        (k2.name, k2, k1),
    ):
        v = own.planet("Venus")
        r = other.planet("Rahu")
        if v and r and own.sidx(v["sign"]) == other.sidx(r["sign"]):
            cross_rahu = True
            notes.append(f"{other.name}'s Rahu on {label}'s Venus — obsession, pull, loyalty blur.")

    combined = p1.affliction_weight + p2.affliction_weight
    if moon_mismatch:
        combined += 8
    if cross_rahu:
        combined += 10

    return CoupleSignals(
        p1=p1,
        p2=p2,
        moon_mismatch=moon_mismatch if m1 and m2 else False,
        cross_rahu_venus=cross_rahu,
        combined_affliction=combined,
        synastry_notes=notes,
    )
