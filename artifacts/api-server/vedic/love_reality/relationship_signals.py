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
    venus_mars_conjunct_tight: bool = False
    venus_surface_strong_only: bool = False
    loyalty_risk_high: bool = False
    moon_dual_flip_risk: bool = False
    venus_dual_flip_risk: bool = False
    saturn_moon_duty_bound: bool = False
    moon_rahu_afflicted: bool = False
    fifth_lord_in_twelfth: bool = False
    twelfth_lord_in_fifth: bool = False
    d9_seventh_lord_weak: bool = False
    lagna_lord_weak_or_combust: bool = False
    venus_d9_exalted: bool = False
    moon_d9_exalted: bool = False
    saturn_on_7th_not_lord: bool = False
    saturn_on_7th_as_lord: bool = False
    venus_combust: bool = False
    venus_afflicted: bool = False
    mercury_debil: bool = False
    mercury_afflicted: bool = False
    mercury_combust: bool = False
    venus_degree: float | None = None
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
            s.venus_afflicted = True
            s.notes.append(f"{k.name}'s Venus in dusthana — romance meets duty, guilt, or secrecy.")
        if "Rahu" in k.aspects_planet("Venus") or "Ketu" in k.aspects_planet("Venus"):
            w += 7
            s.emotional_instability = True
            s.venus_afflicted = True
            s.notes.append(f"{k.name}'s Venus under nodal pull — attraction mixed with confusion.")
        v9_si = k.d9_sign_index("Venus")
        if v9_si is not None and k.dignity("Venus", v9_si) >= 2:
            s.venus_d9_exalted = True
        if k.is_combust("Venus"):
            s.venus_combust = True
            s.venus_afflicted = True
        s.venus_degree = k.planet_deg_in_sign("Venus")
        venus_aff = s.venus_debil or s.venus_afflicted
        if k.is_dual_sign(venus.get("sign")) and venus_aff:
            s.venus_dual_flip_risk = True
            s.notes.append(
                f"{k.name}'s Venus in dual sign under affliction — love intent can flip quickly."
            )

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
        if k.planets_within_degrees("Venus", "Mars", max_deg=10.0):
            s.venus_mars_conjunct_tight = True
            s.notes.append(
                f"{k.name}'s Venus-Mars conjunction (≤10°) — passion impulse can override loyalty; "
                f"do NOT read as 'naturally loyal'."
            )
        else:
            s.notes.append(
                f"{k.name}'s Venus-Mars share a house but orb is wide — impulse risk is milder."
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
        elif m9_si is not None and k.dignity("Moon", m9_si) >= 2:
            s.moon_d9_exalted = True
        asp_m = k.aspects_planet("Moon")
        if "Rahu" in asp_m:
            s.moon_rahu_afflicted = True
        if "Saturn" in asp_m or "Rahu" in asp_m:
            s.moon_afflicted = True
            w += 9
            s.notes.append(f"{k.name}'s Moon under Saturn/Rahu — feelings held in, then erupt or detach.")
        if k.saturn_moon_connected():
            s.saturn_moon_duty_bound = True
            s.notes.append(
                f"{k.name}'s Saturn-Moon link (Punahoo) — duty-bound loyalty; may suffer in silence "
                f"without cheating pattern."
            )
        if moon.get("house") in DUSTHANA:
            w += 5
            s.notes.append(f"{k.name}'s Moon in dusthana — emotional peace hard to sustain in love.")
        if k.is_dual_sign(moon.get("sign")) and (s.moon_afflicted or s.moon_debil or s.moon_rahu_afflicted):
            s.moon_dual_flip_risk = True
            s.notes.append(
                f"{k.name}'s Moon in dual sign under affliction — mind flips quickly under stress."
            )

    merc = k.planet("Mercury")
    if merc:
        merc_d = k.dignity("Mercury", k.sidx(merc["sign"]))
        if merc_d <= -2:
            s.mercury_debil = True
            w += 8
            s.notes.append(f"{k.name}'s Mercury debilitated — words land wrong under stress.")
        if k.is_combust("Mercury"):
            s.mercury_combust = True
            w += 5
            s.notes.append(f"{k.name}'s Mercury combust — clarity drops in heated moments.")
        merc_asp = k.aspects_planet("Mercury")
        if (
            "Rahu" in merc_asp
            or "Ketu" in merc_asp
            or k.share_house("Mercury", "Rahu")
            or k.share_house("Mercury", "Ketu")
        ):
            s.mercury_afflicted = True
            w += 7
            s.notes.append(
                f"{k.name}'s Mercury under nodal pull — mixed signals, hard to read intent."
            )

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
        if p5.get("house") == 12:
            s.fifth_lord_in_twelfth = True
            w += 8
            s.notes.append(
                f"{k.name}'s 5th lord in 12th — hidden desires can blur romantic intention."
            )

    h12l = k.house_lord(12)
    p12 = k.planet(h12l)
    if p12:
        if p12.get("house") == 7:
            s.third_person_risk = True
            w += 6
            s.notes.append(f"{k.name}'s 12th lord in 7th — hidden ties, secrecy, parallel attention.")
        if p12.get("house") == 5:
            s.twelfth_lord_in_fifth = True
            w += 8
            s.notes.append(
                f"{k.name}'s 12th lord in 5th — secret parallel lines risk on love axis."
            )
            if "Rahu" in k.occupants(5) or "Rahu" in k.aspects_house(5):
                w += 4
                s.notes.append(
                    f"{k.name}'s 12th lord in 5th with Rahu — extramarital / secret pull amplified."
                )

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
        if k.saturn_in_seventh_house() and k.saturn_is_seventh_lord():
            s.saturn_on_7th_as_lord = True
            s.notes.append(
                f"{k.name}'s Saturn as 7th lord in 7th — duty-bound partnership; loyalty through obligation."
            )
        else:
            s.saturn_on_7th_not_lord = True
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

    h7l_d9 = k.d9_house_lord(7)
    p7_d9 = k.d9_planet(h7l_d9)
    if p7_d9:
        si_d9 = p7_d9.get("signIndex")
        if si_d9 is None and isinstance(p7_d9.get("sign"), str):
            si_d9 = k.sidx(p7_d9["sign"])
        if si_d9 is not None:
            si_d9 = int(si_d9)
            if k.dignity(h7l_d9, si_d9) <= -2 or p7_d9.get("house") in DUSTHANA:
                s.d9_seventh_lord_weak = True
                w += 10
                s.notes.append(
                    f"{k.name}'s Navamsa 7th lord weak — inner commitment cracks over long term."
                )

    lagna_lord = k.house_lord(1)
    pl_lagna = k.planet(lagna_lord)
    if pl_lagna:
        ll_weak = (
            k.dignity(lagna_lord, k.sidx(pl_lagna["sign"])) <= -2
            or k.is_combust(lagna_lord)
            or pl_lagna.get("house") in DUSTHANA
        )
        if ll_weak:
            s.lagna_lord_weak_or_combust = True
            w += 7
            s.notes.append(
                f"{k.name}'s Lagna lord weak/combust — easily swayed by external attention."
            )

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
