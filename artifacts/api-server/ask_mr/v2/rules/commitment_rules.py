"""Commitment engine rules — factor-based COM-xxx (v1.1.0)."""
from __future__ import annotations

from .types import EngineRule
from ._module_helpers import has_factor, mod_score
from ._commitment_ctx import (
    _house7_evidence,
    _jupiter_supports_commitment,
    _jupiter_weak_commitment,
    _planet_evidence,
    _seventh_lord_strong,
    is_timing,
    reader,
    sig,
)

RULE_PREFIX = "COM"
RULES_VERSION = "1.1.0"


def _core_rules() -> list[EngineRule]:
    return [
        # --- D1: 7th lord ---
        EngineRule(
            rule_id="COM-001",
            module="d1",
            priority=10,
            polarity="positive",
            weight=2.8,
            label="7th lord structurally strong",
            condition=lambda b, c: _seventh_lord_strong(c),
            evidence=lambda b, c: _house7_evidence(c),
        ),
        EngineRule(
            rule_id="COM-002",
            module="d1",
            priority=10,
            polarity="negative",
            weight=2.8,
            label="7th lord in dusthana",
            condition=lambda b, c: bool(sig(c) and sig(c).seventh_lord_dusthana),
            evidence=lambda b, c: (
                f"7th lord in dusthana — partnership may survive emotionally but commitment stability weak; "
                f"{_house7_evidence(c)}"
            ),
        ),
        EngineRule(
            rule_id="COM-003",
            module="d1",
            priority=10,
            polarity="negative",
            weight=2.6,
            label="7th lord debilitated",
            condition=lambda b, c: bool(sig(c) and sig(c).seventh_lord_debil),
            evidence=lambda b, c: (
                f"7th lord debilitated — long-term commitment structure needs patience and repair; "
                f"{_house7_evidence(c)}"
            ),
        ),
        # --- Venus ---
        EngineRule(
            rule_id="COM-004",
            module="d1",
            priority=12,
            polarity="positive",
            weight=2.4,
            label="Venus supports commitment karaka",
            condition=lambda b, c: bool(
                sig(c)
                and (sig(c).venus_d9_exalted or (not sig(c).venus_debil and not sig(c).venus_afflicted))
            ),
            evidence=lambda b, c: _planet_evidence(c, "Venus", role="love/commitment karak"),
        ),
        EngineRule(
            rule_id="COM-005",
            module="d1",
            priority=12,
            polarity="negative",
            weight=2.5,
            label="Venus afflicted for commitment",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).venus_debil or sig(c).venus_afflicted or sig(c).venus_combust)
            ),
            evidence=lambda b, c: _planet_evidence(c, "Venus", role="afflicted love karak"),
        ),
        # --- Jupiter ---
        EngineRule(
            rule_id="COM-006",
            module="d1",
            priority=12,
            polarity="positive",
            weight=2.2,
            label="Jupiter supports marriage promise",
            condition=lambda b, c: _jupiter_supports_commitment(c),
            evidence=lambda b, c: _planet_evidence(c, "Jupiter", role="faith/long-term growth"),
        ),
        EngineRule(
            rule_id="COM-007",
            module="d1",
            priority=12,
            polarity="negative",
            weight=2.0,
            label="Jupiter weak for promise",
            condition=lambda b, c: _jupiter_weak_commitment(c),
            evidence=lambda b, c: _planet_evidence(c, "Jupiter", role="weak promise karak"),
        ),
        # --- 5th–7th–11th romance → commitment linkage ---
        EngineRule(
            rule_id="COM-008",
            module="d1",
            priority=14,
            polarity="positive",
            weight=2.0,
            label="5th–7th romance linkage supports commitment",
            condition=lambda b, c: bool(
                sig(c)
                and sig(c).reconnection_yoga
                and not sig(c).fifth_lord_weak
                and not sig(c).seventh_lord_debil
            ),
            evidence=lambda b, c: (
                "5th lord strong with workable 7th axis — romance can mature into commitment "
                f"(5–7 linkage); {_house7_evidence(c)}"
            ),
        ),
        # --- Saturn: delay vs stability ---
        EngineRule(
            rule_id="COM-009",
            module="d1",
            priority=11,
            polarity="positive",
            weight=2.0,
            label="Saturn as 7th lord — duty-bound stability",
            condition=lambda b, c: bool(sig(c) and sig(c).saturn_on_7th_as_lord),
            evidence=lambda b, c: _planet_evidence(c, "Saturn", role="7th lord duty-bound partnership"),
        ),
        EngineRule(
            rule_id="COM-010",
            module="d1",
            priority=11,
            polarity="negative",
            weight=2.3,
            label="Saturn on 7th (not lord) — delay/cooling",
            condition=lambda b, c: bool(sig(c) and sig(c).saturn_on_7th_not_lord),
            evidence=lambda b, c: _planet_evidence(c, "Saturn", role="delay on 7th axis"),
        ),
        # --- Rahu/Ketu ---
        EngineRule(
            rule_id="COM-011",
            module="d1",
            priority=8,
            polarity="negative",
            weight=2.6,
            label="Rahu/Ketu on 7th — confusion on commitment",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).rahu_on_7th_axis or sig(c).ketu_detachment)
            ),
            evidence=lambda b, c: (
                "Nodes on 7th axis — karmic pull / detachment can blur commitment clarity; "
                f"{_house7_evidence(c)}"
            ),
        ),
        # --- Moon readiness ---
        EngineRule(
            rule_id="COM-012",
            module="d1",
            priority=13,
            polarity="positive",
            weight=2.0,
            label="Moon emotionally ready for bonding",
            condition=lambda b, c: bool(
                sig(c)
                and not sig(c).moon_debil
                and not sig(c).moon_in_8th
                and not sig(c).moon_afflicted
            ),
            evidence=lambda b, c: _planet_evidence(c, "Moon", role="emotional bonding"),
        ),
        EngineRule(
            rule_id="COM-013",
            module="d1",
            priority=13,
            polarity="negative",
            weight=2.2,
            label="Moon afflicted — emotional readiness low",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).moon_debil or sig(c).moon_in_8th or sig(c).moon_afflicted)
            ),
            evidence=lambda b, c: _planet_evidence(c, "Moon", role="emotional instability"),
        ),
        # --- D9 marriage promise ---
        EngineRule(
            rule_id="COM-014",
            module="d9",
            priority=20,
            polarity="negative",
            weight=2.4,
            label="Navamsa 7th lord weak",
            condition=lambda b, c: bool(sig(c) and sig(c).d9_seventh_lord_weak),
            evidence=lambda b, c: (
                "D9 7th lord weak/debilitated — inner marriage promise cracks over long term"
            ),
        ),
        EngineRule(
            rule_id="COM-015",
            module="d9",
            priority=20,
            polarity="positive",
            weight=2.2,
            label="D9 Venus strong",
            condition=lambda b, c: bool(sig(c) and sig(c).venus_d9_exalted),
            evidence=lambda b, c: "D9 Venus exalted/strong — Navamsa supports love commitment",
        ),
        EngineRule(
            rule_id="COM-016",
            module="d9",
            priority=20,
            polarity="negative",
            weight=2.0,
            label="D9 Venus/Moon weak",
            condition=lambda b, c: bool(
                sig(c) and (sig(c).venus_d9_weak or sig(c).moon_d9_debil)
            ),
            evidence=lambda b, c: (
                "D9 Venus or Moon weak — emotional sustainment in marriage needs extra care"
            ),
        ),
        # --- Dasha: positive / negative / neutral ---
        EngineRule(
            rule_id="COM-017",
            module="dasha",
            priority=40,
            polarity="positive",
            weight=1.8,
            label="Benefic dasha supports commitment",
            condition=lambda b, c: has_factor(b, "dasha", "positive"),
            evidence=lambda b, c: "Current dasha (MD/AD) supports seriousness and follow-through",
        ),
        EngineRule(
            rule_id="COM-018",
            module="dasha",
            priority=40,
            polarity="negative",
            weight=1.8,
            label="Malefic dasha tests commitment",
            condition=lambda b, c: has_factor(b, "dasha", "negative"),
            evidence=lambda b, c: "Current dasha (MD/AD) adds distance, test, or delay on commitment",
        ),
        EngineRule(
            rule_id="COM-019",
            module="dasha",
            priority=40,
            polarity="neutral",
            weight=0.8,
            label="Mixed/neutral dasha phase",
            condition=lambda b, c: has_factor(b, "dasha", "mixed"),
            evidence=lambda b, c: "Current dasha mixed — commitment grows through consistent effort",
        ),
        # --- Transit: positive + negative ---
        EngineRule(
            rule_id="COM-020",
            module="transit",
            priority=50,
            polarity="positive",
            weight=1.5,
            label="Transit supports 7th house",
            condition=lambda b, c: has_factor(b, "transit", "positive"),
            evidence=lambda b, c: "Transit phase supportive on partnership axis — good window for clarity",
        ),
        EngineRule(
            rule_id="COM-021",
            module="transit",
            priority=50,
            polarity="negative",
            weight=1.6,
            label="Transit stress on bond",
            condition=lambda b, c: has_factor(b, "transit", "negative"),
            evidence=lambda b, c: "Transit stress on 7th — temporary commitment friction, not permanent denial",
        ),
        # --- KP: positive + denial ---
        EngineRule(
            rule_id="COM-022",
            module="kp",
            priority=60,
            polarity="positive",
            weight=1.4,
            label="KP 7th cusp supportive",
            condition=lambda b, c: has_factor(b, "kp", "positive"),
            evidence=lambda b, c: "KP 7th cusp sub-lord links to commitment/marriage gain",
        ),
        EngineRule(
            rule_id="COM-023",
            module="kp",
            priority=60,
            polarity="negative",
            weight=1.5,
            label="KP 7th cusp denial/weak",
            condition=lambda b, c: has_factor(b, "kp", "negative"),
            evidence=lambda b, c: "KP 7th cusp weak/denial tone — commitment needs stronger practical proof",
        ),
        # --- Ashtakavarga ---
        EngineRule(
            rule_id="COM-024",
            module="ashtakavarga",
            priority=25,
            polarity="positive",
            weight=1.6,
            label="SAV 7th bindus strong",
            condition=lambda b, c: mod_score(b, "ashtakavarga", 68, "gte"),
            evidence=lambda b, c: (
                f"Ashtakavarga 7th-house bindus supportive (score {b.get('ashtakavarga').score})"
                if b.get("ashtakavarga") and b.get("ashtakavarga").loaded
                else "SAV 7th bindus supportive for partnership"
            ),
        ),
        EngineRule(
            rule_id="COM-025",
            module="ashtakavarga",
            priority=25,
            polarity="negative",
            weight=1.6,
            label="SAV 7th bindus weak",
            condition=lambda b, c: mod_score(b, "ashtakavarga", 45, "lte"),
            evidence=lambda b, c: (
                f"Ashtakavarga 7th bindus weak (score {b.get('ashtakavarga').score})"
                if b.get("ashtakavarga") and b.get("ashtakavarga").loaded
                else "SAV 7th bindus weak — partnership house needs effort"
            ),
        ),
        # --- Third-person (single rule — no duplicate D1 factor scoring) ---
        EngineRule(
            rule_id="COM-026",
            module="d1",
            priority=5,
            polarity="negative",
            weight=3.0,
            label="Third-person / parallel attention risk",
            condition=lambda b, c: bool(sig(c) and sig(c).third_person_risk),
            evidence=lambda b, c: (
                "Third-person / hidden-ties risk on love axis — clarify exclusivity before assuming commitment"
            ),
        ),
    ]


def _timing_rules() -> list[EngineRule]:
    return [
        EngineRule(
            rule_id="COM-027",
            module="jaimini",
            priority=30,
            polarity="neutral",
            weight=1.0,
            label="Jaimini AK/DK snapshot for timing",
            condition=lambda b, c: is_timing(c) and bool(b.get("jaimini") and b.get("jaimini").loaded),
            evidence=lambda b, c: (
                f"Jaimini timing layer: {', '.join(b.get('jaimini').notes[:2])}"
                if b.get("jaimini") and b.get("jaimini").notes
                else "Jaimini AK/DK considered for commitment timing"
            ),
        ),
        EngineRule(
            rule_id="COM-028",
            module="bcp",
            priority=28,
            polarity="positive",
            weight=1.4,
            label="BCP marriage linkage supportive (timing)",
            condition=lambda b, c: (
                is_timing(c) and bool(b.get("bcp") and b.get("bcp").loaded and b.get("bcp").polarity == "positive")
            ),
            evidence=lambda b, c: (
                f"BCP marriage linkage: {b.get('bcp').factors[0]['label']}"
                if b.get("bcp") and b.get("bcp").factors
                else "BCP supports marriage/commitment linkage in this phase"
            ),
        ),
        EngineRule(
            rule_id="COM-029",
            module="bcp",
            priority=28,
            polarity="negative",
            weight=1.4,
            label="BCP marriage linkage weak (timing)",
            condition=lambda b, c: (
                is_timing(c) and bool(b.get("bcp") and b.get("bcp").loaded and b.get("bcp").polarity == "negative")
            ),
            evidence=lambda b, c: "BCP marriage linkage weak — formal commitment may need more time",
        ),
        EngineRule(
            rule_id="COM-030",
            module="dasha",
            priority=35,
            polarity="positive",
            weight=1.6,
            label="Timing: benefic dasha window for commitment talk",
            condition=lambda b, c: is_timing(c) and has_factor(b, "dasha", "positive"),
            evidence=lambda b, c: "Timing: current dasha favours serious commitment conversations",
        ),
        EngineRule(
            rule_id="COM-031",
            module="transit",
            priority=45,
            polarity="positive",
            weight=1.4,
            label="Timing: supportive transit window",
            condition=lambda b, c: is_timing(c) and has_factor(b, "transit", "positive"),
            evidence=lambda b, c: "Timing: transit window supportive — better phase to seek clarity/commitment",
        ),
    ]


def commitment_rules() -> list[EngineRule]:
    return _core_rules() + _timing_rules()
