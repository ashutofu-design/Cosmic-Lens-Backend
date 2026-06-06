"""
Love Compatibility v2 — tiered dimension scoring with shared affliction registry.

Six dimensions (max sum = 100):
  emotional (20), attraction (20), communication (15), karmic (10),
  stability (20), trust_alignment (15)

Afflictions register once for cap-tier math and dimension deltas (no double-count).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kundli_engine import calculate_kundli

from vedic.love_reality.relationship_signals import CoupleSignals, analyze_couple
from vedic.love_reality.scoring_core import DUSTHANA, KundliReader, clamp

DIMENSION_MAX: dict[str, int] = {
    "emotional": 20,
    "attraction": 20,
    "communication": 15,
    "karmic": 10,
    "stability": 20,
    "trust_alignment": 15,
}

# Moon rashi lords for maitri (0=Sun … 6=Saturn)
_RASHI_LORD = [2, 5, 3, 1, 0, 3, 5, 2, 4, 6, 6, 4]
_PLN_FRIEND = [
    [1, 2, 2, 1, 2, 0, 0],
    [2, 1, 0, 1, 2, 2, 0],
    [2, 0, 1, 1, 2, 0, 2],
    [2, 0, 2, 1, 0, 2, 0],
    [2, 1, 2, 1, 1, 0, 0],
    [2, 2, 0, 2, 1, 1, 0],
    [0, 0, 2, 2, 2, 0, 1],
]

_COMBUST_ORB = {
    "Moon": 12.0,
    "Mars": 17.0,
    "Mercury": 14.0,
    "Jupiter": 11.0,
    "Venus": 10.0,
    "Saturn": 15.0,
}

CAP_HEAVY_THRESHOLD = 55
CAP_MEDIUM_THRESHOLD = 35
CAP_HEAVY_MAX = 32
CAP_MEDIUM_MAX = 48


def _sign_gap(a: int, b: int) -> int:
    """Minimal arc distance between two sign indices (0–11), zodiac wrap-safe."""
    d = abs(int(a) - int(b)) % 12
    return min(d, 12 - d)


def _is_shad_ashtaka(sign_a: int, sign_b: int) -> bool:
    """True when signs sit in mutual 6th / 8th (shad-ashtaka) relationship."""
    forward = (int(sign_b) - int(sign_a) + 12) % 12
    return forward in (5, 7)


def _planet_longitude(planet: dict | None) -> float | None:
    if not planet:
        return None
    for key in ("longitude", "lon"):
        val = planet.get(key)
        if isinstance(val, (int, float)):
            return float(val)
    return None


def _angular_distance(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return 360.0 - d if d > 180.0 else d


def _is_combust(planet_name: str, reader: KundliReader) -> bool:
    if planet_name not in _COMBUST_ORB:
        return False
    pl = reader.planet(planet_name)
    sun = reader.planet("Sun")
    plon = _planet_longitude(pl)
    slon = _planet_longitude(sun)
    if plon is None or slon is None:
        return False
    return _angular_distance(plon, slon) <= _COMBUST_ORB[planet_name]


def _is_retrograde(planet_name: str, reader: KundliReader) -> bool:
    pl = reader.planet(planet_name)
    return bool(pl and pl.get("retrograde"))


def _d9_chart(reader: KundliReader) -> dict[str, Any]:
    return (reader.k.get("divisionalCharts") or {}).get("D9") or {}


def _d9_nodes_on_1_7_axis(reader: KundliReader) -> bool:
    """Rahu/Ketu occupying or aspecting D9 houses 1 / 7 (navamsa marriage axis)."""
    d9 = _d9_chart(reader)
    asc_idx = d9.get("ascendantSignIndex")
    if asc_idx is None and d9.get("ascendant"):
        asc_idx = reader.sidx(str(d9["ascendant"]))
    if asc_idx is None:
        return False

    target_houses = {1, 7}
    for p in d9.get("planets") or []:
        if p.get("name") not in ("Rahu", "Ketu"):
            continue
        house = p.get("house")
        if house in target_houses:
            return True
        ps = p.get("signIndex")
        if ps is None and p.get("sign"):
            ps = reader.sidx(str(p["sign"]))
        if ps is None:
            continue
        for h in target_houses:
            tgt_sign = (int(asc_idx) + h - 1) % 12
            d = (int(tgt_sign) - int(ps) + 12) % 12
            if d in (4, 8):  # 5th / 9th aspects for nodes
                return True
    return False


def _moon_maitri_points(r1: int, r2: int) -> float:
    l1, l2 = _RASHI_LORD[r1 % 12], _RASHI_LORD[r2 % 12]
    t = _PLN_FRIEND[l1][l2] + _PLN_FRIEND[l2][l1]
    if t >= 4:
        return 5.0
    if t == 3:
        return 4.0
    if t == 2:
        return 2.5
    return 0.0


def _moon_rhythm_points(r1: int, r2: int) -> float:
    d = _sign_gap(r1, r2)
    if d in (0, 3, 4, 9):
        return 4.0
    if d in (6, 7):
        return 0.0
    return 2.0


def _mars_venus_synastry_bonus(r1: KundliReader, r2: KundliReader) -> float:
    """Cross-chart Mars↔Venus alignment bonus (0–6)."""
    bonus = 0.0
    checks = (
        (r1, r1.planet("Mars"), r2, r2.planet("Venus")),
        (r2, r2.planet("Mars"), r1, r1.planet("Venus")),
    )
    for mars_reader, mars, venus_reader, venus in checks:
        if not mars or not venus:
            continue
        ms = mars_reader.sidx(mars["sign"])
        vs = venus_reader.sidx(venus["sign"])
        if ms == vs:
            bonus = max(bonus, 6.0)
            continue
        gap = (vs - ms + 12) % 12
        if gap in (4, 8):
            bonus = max(bonus, 4.0)
        elif gap in (3, 9):
            bonus = max(bonus, 2.0)
    return bonus


def _mercury_sync_points(r1: KundliReader, r2: KundliReader) -> float:
    m1, m2 = r1.planet("Mercury"), r2.planet("Mercury")
    if not m1 or not m2:
        return 4.0
    s1, s2 = r1.sidx(m1["sign"]), r2.sidx(m2["sign"])
    if s1 == s2:
        return 6.0
    l1, l2 = _RASHI_LORD[s1], _RASHI_LORD[s2]
    t = _PLN_FRIEND[l1][l2] + _PLN_FRIEND[l2][l1]
    if t >= 3:
        return 5.0
    if t == 2:
        return 3.0
    return 1.0


def _seventh_lord_strength_points(reader: KundliReader) -> float:
    """0–10 stability contribution from D1 + D9 seventh lord."""
    pts = 0.0
    h7l = reader.house_lord(7)
    p7 = reader.planet(h7l)
    if not p7:
        return 3.0
    d1 = reader.dignity(h7l, reader.sidx(p7["sign"]))
    if p7.get("house") in DUSTHANA:
        pts += 1.0
    elif d1 <= -2:
        pts += 2.0
    elif d1 >= 1:
        pts += 5.0
    else:
        pts += 3.5

    si9 = reader.d9_sign_index(h7l)
    if si9 is not None:
        d9 = reader.dignity(h7l, si9)
        if d9 <= -2:
            pts += 1.0
        elif d9 >= 1:
            pts += 5.0
        else:
            pts += 3.0
    else:
        pts += 2.0
    return min(10.0, pts)


def _saturn_stabilizing_bonus(reader: KundliReader) -> float:
    """Saturn aspect on Venus or 7th house → trust/stability support."""
    bonus = 0.0
    if "Saturn" in reader.aspects_planet("Venus"):
        bonus += 2.0
    if "Saturn" in reader.aspects_house(7) and "Saturn" not in reader.occupants(7):
        bonus += 1.5
    return bonus


@dataclass
class AfflictionRegistry:
    """Register each affliction once — drives cap tier + dimension deltas."""

    _seen: set[str] = field(default_factory=set)
    dimension_deltas: dict[str, float] = field(default_factory=lambda: {k: 0.0 for k in DIMENSION_MAX})
    applied_deductions_log: list[dict[str, Any]] = field(default_factory=list)
    total_affliction: int = 0
    karmic_red_flag: bool = False

    def register(
        self,
        signal_id: str,
        label: str,
        affliction_weight: int,
        dimension_deltas: dict[str, float],
        *,
        karmic_red_flag: bool = False,
    ) -> bool:
        if signal_id in self._seen:
            return False
        self._seen.add(signal_id)
        self.total_affliction += max(0, int(affliction_weight))
        if karmic_red_flag:
            self.karmic_red_flag = True
        row: dict[str, Any] = {
            "signal_id": signal_id,
            "label": label,
            "affliction_weight": affliction_weight,
            "dimension_deltas": {k: round(v, 2) for k, v in dimension_deltas.items() if v},
        }
        self.applied_deductions_log.append(row)
        for dim, delta in dimension_deltas.items():
            if dim in self.dimension_deltas:
                self.dimension_deltas[dim] += delta
        return True


def _populate_registry(
    r1: KundliReader,
    r2: KundliReader,
    sig: CoupleSignals,
    registry: AfflictionRegistry,
) -> None:
    """Detect chart signals once; primary dimension owns the affliction weight."""

    for prefix, person in (("p1", sig.p1), ("p2", sig.p2)):
        name = person.name
        if person.moon_debil:
            registry.register(
                f"{prefix}_moon_debil",
                f"{name}: Moon debilitated",
                11,
                {"emotional": -4.0},
            )
        if person.moon_afflicted:
            registry.register(
                f"{prefix}_moon_afflicted",
                f"{name}: Moon afflicted by Saturn/Rahu",
                9,
                {"emotional": -3.0, "communication": -1.5},
            )
        if person.moon_in_8th:
            registry.register(
                f"{prefix}_moon_8th",
                f"{name}: Moon in 8th house",
                12,
                {"emotional": -3.0, "trust_alignment": -3.0},
            )
        if person.moon_d9_debil:
            registry.register(
                f"{prefix}_moon_d9_debil",
                f"{name}: Navamsa Moon debilitated",
                10,
                {"emotional": -2.0, "trust_alignment": -2.0},
            )
        if person.venus_debil:
            registry.register(
                f"{prefix}_venus_debil",
                f"{name}: Venus debilitated",
                14,
                {"attraction": -5.0, "trust_alignment": -4.0},
            )
        if person.venus_d9_weak:
            registry.register(
                f"{prefix}_venus_d9_weak",
                f"{name}: Navamsa Venus weak",
                6,
                {"attraction": -2.0, "trust_alignment": -1.5},
            )
        if person.venus_mars_conjunct:
            registry.register(
                f"{prefix}_venus_mars_conjunct",
                f"{name}: Venus–Mars conjunction",
                14,
                {"attraction": -3.0, "trust_alignment": -4.0},
            )
        if person.seventh_lord_dusthana:
            registry.register(
                f"{prefix}_7th_lord_dusthana",
                f"{name}: 7th lord in dusthana",
                12,
                {"stability": -6.0},
            )
        if person.seventh_lord_debil:
            registry.register(
                f"{prefix}_7th_lord_debil",
                f"{name}: 7th lord debilitated",
                10,
                {"stability": -4.0},
            )
        if person.saturn_on_7th:
            registry.register(
                f"{prefix}_saturn_7th",
                f"{name}: Saturn on 7th axis",
                8,
                {"stability": -4.0},
            )
        if person.separation_yoga:
            registry.register(
                f"{prefix}_separation_yoga",
                f"{name}: Separation yoga active",
                6,
                {"stability": -3.0},
            )
        if person.third_person_risk:
            registry.register(
                f"{prefix}_third_person",
                f"{name}: Third-person / secrecy risk on love axis",
                8,
                {"trust_alignment": -5.0},
            )
        if person.rahu_on_7th_axis:
            registry.register(
                f"{prefix}_rahu_7th",
                f"{name}: Nodes on 7th axis (D1)",
                10,
                {"karmic": -3.0, "trust_alignment": -2.0},
            )

    if sig.moon_mismatch:
        registry.register(
            "moon_mismatch",
            "Moon–Moon rhythm clash",
            8,
            {"emotional": -4.0, "communication": -2.0},
        )

    if sig.cross_rahu_venus:
        registry.register(
            "cross_rahu_venus",
            "Partner Rahu on your Venus (synastry)",
            10,
            {"attraction": -4.0, "karmic": -3.0, "trust_alignment": -3.0},
        )

    for prefix, reader in (("p1", r1), ("p2", r2)):
        if _d9_nodes_on_1_7_axis(reader):
            registry.register(
                f"{prefix}_d9_nodes_17",
                f"{reader.name}: Rahu/Ketu on D9 1st/7th axis",
                8,
                {"karmic": -5.0},
                karmic_red_flag=True,
            )

    m1, m2 = r1.planet("Mercury"), r2.planet("Mercury")
    if m1 and m2:
        s1, s2 = r1.sidx(m1["sign"]), r2.sidx(m2["sign"])
        if _is_shad_ashtaka(s1, s2):
            registry.register(
                "mercury_shad_ashtaka",
                "Mercury signs in mutual 6/8 (shad-ashtaka)",
                6,
                {"communication": -6.0},
            )

    merc_afflict = 0.0
    merc_labels: list[str] = []
    for prefix, reader in (("p1", r1), ("p2", r2)):
        if _is_retrograde("Mercury", reader):
            merc_afflict += 2.0
            merc_labels.append(f"{reader.name} Mercury retrograde")
        if _is_combust("Mercury", reader):
            merc_afflict += 2.0
            merc_labels.append(f"{reader.name} Mercury combust")
    if merc_afflict:
        registry.register(
            "mercury_retro_combust",
            "; ".join(merc_labels),
            5,
            {"communication": -min(6.0, merc_afflict + 2.0)},
        )


def _score_dimensions(
    r1: KundliReader,
    r2: KundliReader,
    sig: CoupleSignals,
    registry: AfflictionRegistry,
) -> dict[str, dict[str, Any]]:
    m1, m2 = r1.planet("Moon"), r2.planet("Moon")
    rashi1 = r1.sidx(m1["sign"]) if m1 else 0
    rashi2 = r2.sidx(m2["sign"]) if m2 else 0

    emotional_base = 6.0 + _moon_maitri_points(rashi1, rashi2) + _moon_rhythm_points(rashi1, rashi2)
    emotional = emotional_base + registry.dimension_deltas["emotional"]

    attraction_base = 8.0 + _mars_venus_synastry_bonus(r1, r2)
    for person in (sig.p1, sig.p2):
        if not person.venus_debil and not person.venus_d9_weak:
            attraction_base += 2.0
    if sig.cross_rahu_venus:
        pass  # already in registry
    else:
        attraction_base += 2.0
    attraction = attraction_base + registry.dimension_deltas["attraction"]

    communication_base = _mercury_sync_points(r1, r2) + 4.0
    if not sig.moon_mismatch:
        communication_base += 2.0
    communication = communication_base + registry.dimension_deltas["communication"]

    karmic_base = 6.0
    if not registry.karmic_red_flag:
        karmic_base += 2.0
    if sig.cross_rahu_venus or sig.p1.rahu_on_7th_axis or sig.p2.rahu_on_7th_axis:
        karmic_base -= 1.0
    karmic = karmic_base + registry.dimension_deltas["karmic"]

    stability_base = _seventh_lord_strength_points(r1) + _seventh_lord_strength_points(r2)
    stability_base = stability_base * 0.55 + 4.0
    if not sig.p1.separation_yoga and not sig.p2.separation_yoga:
        stability_base += 2.0
    stability = stability_base + registry.dimension_deltas["stability"]

    trust_base = 7.0
    trust_base += _saturn_stabilizing_bonus(r1) + _saturn_stabilizing_bonus(r2)
    if sig.p1.reconnection_yoga or sig.p2.reconnection_yoga:
        trust_base += 2.0
    trust = trust_base + registry.dimension_deltas["trust_alignment"]

    raw_dims = {
        "emotional": emotional,
        "attraction": attraction,
        "communication": communication,
        "karmic": karmic,
        "stability": stability,
        "trust_alignment": trust,
    }

    breakdown: dict[str, dict[str, Any]] = {}
    for key, mx in DIMENSION_MAX.items():
        score = clamp(raw_dims[key], 0, mx)
        breakdown[key] = {"score": score, "max": mx}
    return breakdown


def _apply_honesty_cap(
    dimension_total: int,
    total_affliction: int,
) -> tuple[int, int, bool, str]:
    raw = dimension_total
    if total_affliction >= CAP_HEAVY_THRESHOLD:
        final = min(raw, CAP_HEAVY_MAX)
        return final, raw, final < raw, "heavy"
    if total_affliction >= CAP_MEDIUM_THRESHOLD:
        final = min(raw, CAP_MEDIUM_MAX)
        return final, raw, final < raw, "medium"
    final = clamp(raw, 0, 100)
    return final, raw, False, "none"


def _risk_level(score: int) -> str:
    if score >= 72:
        return "low"
    if score >= 52:
        return "medium"
    if score >= 35:
        return "high"
    return "very high"


def _emotional_summary(score: int) -> str:
    if score >= 62:
        return "Real compatibility exists, but it needs emotional honesty — not fantasy."
    if score >= 45:
        return "The bond runs on attachment and memory more than stable peace."
    return "This chart shows emotional instability and repeated separation patterns — not an easy-flow love."


def run_love_compatibility_v2(
    p1: dict,
    p2: dict,
    *,
    skip_chart_proof: bool = False,
) -> dict[str, Any]:
    """
    Compute Love Compatibility v2 for two birth profiles.

    Returns expanded JSON with dimension breakdown, affliction log, and cap metadata.
    """
    k1 = calculate_kundli({**p1, "name": p1.get("name") or "You"})
    k2 = calculate_kundli({**p2, "name": p2.get("name") or "Partner"})
    r1, r2 = KundliReader(k1), KundliReader(k2)
    sig = analyze_couple(r1, r2)

    registry = AfflictionRegistry()
    _populate_registry(r1, r2, sig, registry)

    dimensions_breakdown = _score_dimensions(r1, r2, sig, registry)
    dimension_total = sum(d["score"] for d in dimensions_breakdown.values())

    final_score, raw_score_before_cap, cap_applied, cap_tier = _apply_honesty_cap(
        dimension_total,
        registry.total_affliction,
    )

    reasons = list(sig.p1.notes[:4]) + list(sig.p2.notes[:4]) + sig.synastry_notes

    payload: dict[str, Any] = {
        "engine": "love_compat_v2",
        "score": final_score,
        "final_score": final_score,
        "raw_score_before_cap": raw_score_before_cap,
        "dimension_total": dimension_total,
        "is_honesty_cap_applied": cap_applied,
        "cap_tier": cap_tier,
        "total_affliction": registry.total_affliction,
        "applied_deductions_log": registry.applied_deductions_log,
        "dimensions_breakdown": dimensions_breakdown,
        "karmic_red_flag": registry.karmic_red_flag,
        "risk_level": _risk_level(final_score),
        "emotional_summary": _emotional_summary(final_score),
        "reasons": reasons[:14],
        # Flat breakdown keys for legacy mobile bars (0–100 normalized)
        "breakdown": {
            dim: clamp(int(round(d["score"] / d["max"] * 100)), 0, 100)
            for dim, d in dimensions_breakdown.items()
        },
    }

    if not skip_chart_proof:
        try:
            from vedic.love_reality.chart_proof import build_chart_proof

            payload["chart_proof"] = build_chart_proof(r1, r2, sig)
        except Exception:
            payload["chart_proof"] = None

    return payload
