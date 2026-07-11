"""Loyalty / trust engine rules — factor-based TRUST-xxx (v1.1.0)."""
from __future__ import annotations

import re

from .types import EngineRule
from ._module_helpers import has_factor, mod_score
from ._commitment_ctx import _planet_evidence, _seventh_lord_strong, is_timing, sig
from ._trust_ctx import (
    house5_evidence,
    house7_evidence,
    house8_evidence,
    loyalty_safe_bonus,
    venus_surface_risk_dominates,
)

RULE_PREFIX = "TRUST"
RULES_VERSION = "1.1.0"


def _note_has(ctx: dict, key: str) -> bool:
    s = sig(ctx)
    if not s:
        return False
    return any(key.lower() in str(n).lower() for n in (getattr(s, "notes", []) or []))


def _core_rules() -> list[EngineRule]:
    return [
        # --- 7th lord / partnership structure ---
        EngineRule(
            rule_id="TRUST-001",
            module="d1",
            priority=10,
            polarity="positive",
            weight=2.6,
            label="7th lord supports trust structure",
            condition=lambda b, c: _seventh_lord_strong(c),
            evidence=lambda b, c: house7_evidence(c),
        ),
        EngineRule(
            rule_id="TRUST-002",
            module="d1",
            priority=10,
            polarity="negative",
            weight=2.8,
            label="7th lord in dusthana — trust strain",
            condition=lambda b, c: bool(sig(c) and sig(c).seventh_lord_dusthana),
            evidence=lambda b, c: (
                f"7th lord in dusthana — attachment may survive but trust stability weak; {house7_evidence(c)}"
            ),
        ),
        EngineRule(
            rule_id="TRUST-003",
            module="d1",
            priority=10,
            polarity="negative",
            weight=2.6,
            label="7th lord debilitated — weak trust backbone",
            condition=lambda b, c: bool(sig(c) and sig(c).seventh_lord_debil),
            evidence=lambda b, c: f"7th lord debilitated — loyalty structure needs boundaries; {house7_evidence(c)}",
        ),
        # --- Venus affliction / loyalty karak ---
        EngineRule(
            rule_id="TRUST-004",
            module="d1",
            priority=12,
            polarity="negative",
            weight=2.8,
            label="Venus debilitated — love nature unstable",
            condition=lambda b, c: bool(sig(c) and sig(c).venus_debil),
            evidence=lambda b, c: _planet_evidence(c, "Venus", role="debilitated love karak"),
        ),
        EngineRule(
            rule_id="TRUST-005",
            module="d1",
            priority=12,
            polarity="negative",
            weight=2.5,
            label="Venus afflicted/combust — trust blur risk",
            condition=lambda b, c: bool(sig(c) and (sig(c).venus_afflicted or sig(c).venus_combust)),
            evidence=lambda b, c: _planet_evidence(c, "Venus", role="afflicted/combust"),
        ),
        EngineRule(
            rule_id="TRUST-006",
            module="d1",
            priority=12,
            polarity="positive",
            weight=2.0,
            label="Venus clean enough for steady affection",
            condition=lambda b, c: loyalty_safe_bonus(c),
            evidence=lambda b, c: _planet_evidence(c, "Venus", role="steady affection when chart is clean"),
        ),
        # --- Venus-Mars impulse ---
        EngineRule(
            rule_id="TRUST-007",
            module="d1",
            priority=8,
            polarity="negative",
            weight=3.0,
            label="Venus-Mars tight — passion over loyalty",
            condition=lambda b, c: bool(sig(c) and sig(c).venus_mars_conjunct_tight),
            evidence=lambda b, c: (
                "Venus-Mars conjunction (tight orb) — impulse can override loyalty; "
                "do not read as naturally faithful"
            ),
        ),
        EngineRule(
            rule_id="TRUST-008",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.0,
            label="Venus-Mars wide — mild impulse risk",
            condition=lambda b, c: bool(
                sig(c) and sig(c).venus_mars_conjunct and not sig(c).venus_mars_conjunct_tight
            ),
            evidence=lambda b, c: "Venus-Mars share a house (wider orb) — mild impulse/loyalty blur risk",
        ),
        # --- Moon / 8th / emotional trust ---
        EngineRule(
            rule_id="TRUST-009",
            module="d1",
            priority=8,
            polarity="negative",
            weight=2.8,
            label="Moon in 8th — secrecy and loyalty tests",
            condition=lambda b, c: bool(sig(c) and sig(c).moon_in_8th),
            evidence=lambda b, c: f"Moon in 8th — hidden emotional layers test vishwas; {house8_evidence(c)}",
        ),
        EngineRule(
            rule_id="TRUST-010",
            module="d1",
            priority=12,
            polarity="negative",
            weight=2.4,
            label="Moon debilitated — emotional unpredictability",
            condition=lambda b, c: bool(sig(c) and sig(c).moon_debil),
            evidence=lambda b, c: _planet_evidence(c, "Moon", role="debilitated emotional trust"),
        ),
        EngineRule(
            rule_id="TRUST-011",
            module="d1",
            priority=12,
            polarity="negative",
            weight=2.3,
            label="Moon under Saturn/Rahu affliction",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).moon_afflicted or sig(c).moon_rahu_afflicted)
            ),
            evidence=lambda b, c: _planet_evidence(c, "Moon", role="afflicted emotional trust"),
        ),
        EngineRule(
            rule_id="TRUST-012",
            module="d1",
            priority=13,
            polarity="positive",
            weight=1.8,
            label="Moon emotionally steady",
            condition=lambda b, c: bool(
                sig(c)
                and not sig(c).moon_debil
                and not sig(c).moon_in_8th
                and not sig(c).moon_afflicted
            ),
            evidence=lambda b, c: _planet_evidence(c, "Moon", role="emotional trust"),
        ),
        # --- Rahu/Ketu on 7th ---
        EngineRule(
            rule_id="TRUST-013",
            module="d1",
            priority=8,
            polarity="negative",
            weight=2.7,
            label="Rahu on 7th axis — obsession/external pull",
            condition=lambda b, c: bool(sig(c) and sig(c).rahu_on_7th_axis),
            evidence=lambda b, c: f"Rahu on 7th axis — loyalty lines can blur; {house7_evidence(c)}",
        ),
        EngineRule(
            rule_id="TRUST-014",
            module="d1",
            priority=9,
            polarity="negative",
            weight=2.2,
            label="Ketu detachment on 7th",
            condition=lambda b, c: bool(sig(c) and sig(c).ketu_detachment),
            evidence=lambda b, c: "Ketu influence on 7th — withdrawal/ghosting can test trust",
        ),
        # --- Secret ties 12th↔5th/7th ---
        EngineRule(
            rule_id="TRUST-015",
            module="d1",
            priority=7,
            polarity="negative",
            weight=2.5,
            label="12th lord in 7th — hidden partnership ties",
            condition=lambda b, c: _note_has(c, "12th lord in 7th"),
            evidence=lambda b, c: "12th lord in 7th — hidden ties and parallel attention risk on loyalty axis",
        ),
        EngineRule(
            rule_id="TRUST-016",
            module="d1",
            priority=7,
            polarity="negative",
            weight=2.6,
            label="5th–12th lord link — secret desire lines",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).fifth_lord_in_twelfth or sig(c).twelfth_lord_in_fifth)
            ),
            evidence=lambda b, c: f"5th–12th link can erode loyalty through hidden desire; {house5_evidence(c)}",
        ),
        EngineRule(
            rule_id="TRUST-017",
            module="d1",
            priority=9,
            polarity="negative",
            weight=2.4,
            label="Surface Venus strong but loyalty risk dominates",
            condition=lambda b, c: venus_surface_risk_dominates(c),
            evidence=lambda b, c: (
                "Venus may look strong on paper but loyalty risk flags dominate — "
                "surface warmth ≠ faithful behaviour"
            ),
        ),
        # --- Dual-sign flip risk ---
        EngineRule(
            rule_id="TRUST-018",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.2,
            label="Moon/Venus dual-sign flip risk",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).moon_dual_flip_risk or sig(c).venus_dual_flip_risk)
            ),
            evidence=lambda b, c: "Dual-sign affliction on Moon/Venus — intent can flip under stress",
        ),
        EngineRule(
            rule_id="TRUST-019",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.0,
            label="Lagna lord weak — external influence on loyalty",
            condition=lambda b, c: bool(sig(c) and sig(c).lagna_lord_weak_or_combust),
            evidence=lambda b, c: "Lagna lord weak/combust — outside influence can sway commitment",
        ),
        # --- D9 inner loyalty ---
        EngineRule(
            rule_id="TRUST-020",
            module="d9",
            priority=20,
            polarity="negative",
            weight=2.6,
            label="Navamsa 7th lord weak",
            condition=lambda b, c: bool(sig(c) and sig(c).d9_seventh_lord_weak),
            evidence=lambda b, c: "D9 7th lord weak — inner loyalty cracks over long term",
        ),
        EngineRule(
            rule_id="TRUST-021",
            module="d9",
            priority=20,
            polarity="negative",
            weight=2.4,
            label="Navamsa Moon debilitated",
            condition=lambda b, c: bool(sig(c) and sig(c).moon_d9_debil),
            evidence=lambda b, c: "D9 Moon debilitated — inner emotional loyalty wavers under stress",
        ),
        EngineRule(
            rule_id="TRUST-022",
            module="d9",
            priority=20,
            polarity="negative",
            weight=2.2,
            label="Navamsa Venus weak",
            condition=lambda b, c: bool(sig(c) and sig(c).venus_d9_weak),
            evidence=lambda b, c: "D9 Venus weak — inner affection layer fragile",
        ),
        EngineRule(
            rule_id="TRUST-023",
            module="d9",
            priority=20,
            polarity="positive",
            weight=2.0,
            label="D9 Venus/Moon strong inner layer",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).venus_d9_exalted or sig(c).moon_d9_exalted)
            ),
            evidence=lambda b, c: "D9 Venus or Moon strong — inner loyalty sustainment support",
        ),
        # --- Duty-bound loyalty support ---
        EngineRule(
            rule_id="TRUST-024",
            module="d1",
            priority=14,
            polarity="positive",
            weight=2.0,
            label="Saturn-Moon duty-bound loyalty",
            condition=lambda b, c: bool(sig(c) and sig(c).saturn_moon_duty_bound),
            evidence=lambda b, c: _planet_evidence(c, "Saturn", role="duty-bound loyalty with Moon"),
        ),
        EngineRule(
            rule_id="TRUST-025",
            module="d1",
            priority=14,
            polarity="positive",
            weight=1.8,
            label="Saturn as 7th lord — obligation loyalty",
            condition=lambda b, c: bool(sig(c) and sig(c).saturn_on_7th_as_lord),
            evidence=lambda b, c: "Saturn as 7th lord in 7th — loyalty through duty and obligation",
        ),
        # --- Dasha ---
        EngineRule(
            rule_id="TRUST-026",
            module="dasha",
            priority=40,
            polarity="positive",
            weight=1.7,
            label="Benefic dasha supports trust",
            condition=lambda b, c: has_factor(b, "dasha", "positive"),
            evidence=lambda b, c: "Current dasha supports emotional honesty and trust repair",
        ),
        EngineRule(
            rule_id="TRUST-027",
            module="dasha",
            priority=40,
            polarity="negative",
            weight=1.8,
            label="Malefic dasha tests loyalty",
            condition=lambda b, c: has_factor(b, "dasha", "negative"),
            evidence=lambda b, c: "Current dasha (Saturn/Rahu/Ketu tone) tests trust and transparency",
        ),
        EngineRule(
            rule_id="TRUST-028",
            module="dasha",
            priority=40,
            polarity="neutral",
            weight=0.8,
            label="Mixed dasha on trust",
            condition=lambda b, c: has_factor(b, "dasha", "mixed"),
            evidence=lambda b, c: "Mixed dasha — trust needs consistent behaviour, not assumptions",
        ),
        # --- Transit ---
        EngineRule(
            rule_id="TRUST-029",
            module="transit",
            priority=50,
            polarity="positive",
            weight=1.5,
            label="Transit supports partnership trust",
            condition=lambda b, c: has_factor(b, "transit", "positive"),
            evidence=lambda b, c: "Transit supportive on 7th — better phase for honest trust talks",
        ),
        EngineRule(
            rule_id="TRUST-030",
            module="transit",
            priority=50,
            polarity="negative",
            weight=1.6,
            label="Transit stress on trust",
            condition=lambda b, c: has_factor(b, "transit", "negative"),
            evidence=lambda b, c: "Transit stress on 7th — temporary distance/friction can test vishwas",
        ),
        # --- KP ---
        EngineRule(
            rule_id="TRUST-031",
            module="kp",
            priority=60,
            polarity="positive",
            weight=1.4,
            label="KP 7th cusp supports trust/fidelity",
            condition=lambda b, c: has_factor(b, "kp", "positive"),
            evidence=lambda b, c: "KP 7th cusp sub-lord supportive — fidelity themes can hold",
        ),
        EngineRule(
            rule_id="TRUST-032",
            module="kp",
            priority=60,
            polarity="negative",
            weight=1.5,
            label="KP 7th cusp denial/weak",
            condition=lambda b, c: has_factor(b, "kp", "negative"),
            evidence=lambda b, c: "KP 7th cusp weak — trust needs proof, not promises",
        ),
        # --- Ashtakavarga ---
        EngineRule(
            rule_id="TRUST-033",
            module="ashtakavarga",
            priority=25,
            polarity="positive",
            weight=1.5,
            label="SAV 7th bindus supportive",
            condition=lambda b, c: mod_score(b, "ashtakavarga", 68, "gte"),
            evidence=lambda b, c: (
                f"SAV 7th bindus supportive (score {b.get('ashtakavarga').score})"
                if b.get("ashtakavarga") and b.get("ashtakavarga").loaded
                else "SAV 7th bindus supportive for partnership trust"
            ),
        ),
        EngineRule(
            rule_id="TRUST-034",
            module="ashtakavarga",
            priority=25,
            polarity="negative",
            weight=1.5,
            label="SAV 7th bindus weak",
            condition=lambda b, c: mod_score(b, "ashtakavarga", 45, "lte"),
            evidence=lambda b, c: (
                f"SAV 7th bindus weak (score {b.get('ashtakavarga').score})"
                if b.get("ashtakavarga") and b.get("ashtakavarga").loaded
                else "SAV 7th bindus weak — trust needs active repair"
            ),
        ),
        # --- Emotional instability / mercury noise ---
        EngineRule(
            rule_id="TRUST-035",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.0,
            label="Emotional instability blurs trust",
            condition=lambda b, c: bool(sig(c) and sig(c).emotional_instability),
            evidence=lambda b, c: "Nodal/Venus affliction themes — emotional instability can blur loyalty",
        ),
        EngineRule(
            rule_id="TRUST-036",
            module="d1",
            priority=13,
            polarity="negative",
            weight=1.6,
            label="Mercury debilitated — mixed signals",
            condition=lambda b, c: bool(sig(c) and (sig(c).mercury_debil or sig(c).mercury_afflicted)),
            evidence=lambda b, c: _planet_evidence(c, "Mercury", role="communication/trust signals"),
        ),
        # --- Mars/Saturn friction on 7th ---
        EngineRule(
            rule_id="TRUST-037",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.2,
            label="Mars on 7th — fights test trust",
            condition=lambda b, c: bool(sig(c) and sig(c).mars_on_7th),
            evidence=lambda b, c: _planet_evidence(c, "Mars", role="7th-axis conflict"),
        ),
        EngineRule(
            rule_id="TRUST-038",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.0,
            label="Saturn on 7th (not lord) — distance tests vishwas",
            condition=lambda b, c: bool(sig(c) and sig(c).saturn_on_7th_not_lord),
            evidence=lambda b, c: _planet_evidence(c, "Saturn", role="distance on 7th"),
        ),
        EngineRule(
            rule_id="TRUST-043",
            module="d1",
            priority=5,
            polarity="negative",
            weight=3.0,
            label="Third-person / external validation risk",
            condition=lambda b, c: bool(sig(c) and sig(c).third_person_risk),
            evidence=lambda b, c: (
                "Third-person / external pull on love axis — verify exclusivity before assuming loyalty"
            ),
        ),
    ]


def _timing_rules() -> list[EngineRule]:
    return [
        EngineRule(
            rule_id="TRUST-039",
            module="jaimini",
            priority=30,
            polarity="neutral",
            weight=1.0,
            label="Jaimini AK/DK timing snapshot",
            condition=lambda b, c: is_timing(c) and bool(b.get("jaimini") and b.get("jaimini").loaded),
            evidence=lambda b, c: (
                f"Jaimini timing: {', '.join(b.get('jaimini').notes[:2])}"
                if b.get("jaimini") and b.get("jaimini").notes
                else "Jaimini AK/DK considered for trust-timing questions"
            ),
        ),
        EngineRule(
            rule_id="TRUST-040",
            module="bcp",
            priority=28,
            polarity="positive",
            weight=1.3,
            label="BCP linkage supportive (timing)",
            condition=lambda b, c: (
                is_timing(c) and bool(b.get("bcp") and b.get("bcp").loaded and b.get("bcp").polarity == "positive")
            ),
            evidence=lambda b, c: "BCP marriage linkage supportive — trust can deepen with formal bond",
        ),
        EngineRule(
            rule_id="TRUST-041",
            module="dasha",
            priority=35,
            polarity="negative",
            weight=1.7,
            label="Timing: dasha phase exposes loyalty test",
            condition=lambda b, c: (
                is_timing(c)
                and _cheating_intent(c)
                and has_factor(b, "dasha", "negative")
            ),
            evidence=lambda b, c: "Timing: malefic dasha window — higher need for transparency on loyalty",
        ),
        EngineRule(
            rule_id="TRUST-042",
            module="transit",
            priority=45,
            polarity="negative",
            weight=1.5,
            label="Timing: transit stress during suspicion phase",
            condition=lambda b, c: (
                is_timing(c) and _cheating_intent(c) and has_factor(b, "transit", "negative")
            ),
            evidence=lambda b, c: "Timing: transit stress — avoid jumping to conclusions; verify behaviour",
        ),
    ]


def _cheating_intent(ctx: dict) -> bool:
    intent = (ctx.get("intent") or "").strip().lower()
    if intent in ("cheating_suspicion", "betrayal"):
        return True
    q = (ctx.get("question") or "").lower()
    return bool(re.search(r"(?ix)\b(cheat|dhokha|dhoka|betray|affair|beimaan|unfaithful)\b", q))


def trust_rules() -> list[EngineRule]:
    return _core_rules() + _timing_rules()
