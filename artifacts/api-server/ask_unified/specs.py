"""Shared Ask unified stack — Engine Execution + selected blocks + DNA judge.

Used by remaining domains (career, education, children, property, vehicle,
litigation, luck, network, and gap topics) to mirror health/finance/travel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class DomainSpec:
    key: str
    slice: str
    schema_version: str
    json_label: str
    focus_houses: tuple[int, ...]
    focus_planets: tuple[str, ...]
    dimensions: tuple[str, ...]
    default_archetype: str
    topic_label: str
    divisional: str = "D9"
    banned: str = "exact date, guarantee, invented placements"
    dim_house_map: dict[str, tuple[int, ...]] = field(default_factory=dict)


# ── Domain registry ─────────────────────────────────────────────────────────

_DOMAINS: dict[str, DomainSpec] = {}


def _reg(spec: DomainSpec) -> DomainSpec:
    _DOMAINS[spec.key] = spec
    return spec


_reg(DomainSpec(
    key="career", slice="career_engine_v1",
    schema_version="career_engine_execution_v1",
    json_label="CAREER_ENGINE_EXECUTION_JSON",
    focus_houses=(10, 6, 2, 11),
    focus_planets=("Sun", "Saturn", "Mercury", "Jupiter"),
    dimensions=("career_strength", "job_stability", "growth", "obstacles"),
    default_archetype="general_career", topic_label="career/job",
    divisional="D10",
    dim_house_map={
        "career_strength": (10, 1), "job_stability": (10, 6),
        "growth": (11, 2), "obstacles": (6, 8, 12),
    },
))
_reg(DomainSpec(
    key="education", slice="education_engine_v1",
    schema_version="education_engine_execution_v1",
    json_label="EDUCATION_ENGINE_EXECUTION_JSON",
    focus_houses=(4, 5, 9),
    focus_planets=("Mercury", "Jupiter", "Moon"),
    dimensions=("learning_ability", "exam_support", "higher_studies", "focus"),
    default_archetype="general_education", topic_label="education/studies",
    divisional="D24",
    dim_house_map={
        "learning_ability": (4, 5), "exam_support": (5, 9),
        "higher_studies": (9, 4), "focus": (5, 1),
    },
))
_reg(DomainSpec(
    key="children", slice="children_engine_v1",
    schema_version="children_engine_execution_v1",
    json_label="CHILDREN_ENGINE_EXECUTION_JSON",
    focus_houses=(5, 9, 11),
    focus_planets=("Jupiter", "Venus", "Moon"),
    dimensions=("progeny_promise", "bond", "child_success", "obstacles"),
    default_archetype="general_children", topic_label="children/santaan",
    divisional="D7",
    banned="exact gender guarantee, medical diagnosis, exact conception date",
    dim_house_map={
        "progeny_promise": (5, 9), "bond": (5, 4),
        "child_success": (5, 11), "obstacles": (5, 6, 8),
    },
))
_reg(DomainSpec(
    key="property", slice="property_engine_v1",
    schema_version="property_engine_execution_v1",
    json_label="PROPERTY_ENGINE_EXECUTION_JSON",
    focus_houses=(4, 2, 11, 12),
    focus_planets=("Mars", "Saturn", "Moon", "Venus"),
    dimensions=("property_yog", "capacity", "risk", "gains"),
    default_archetype="general_property", topic_label="property/ghar-zameen",
    divisional="D4",
    dim_house_map={
        "property_yog": (4, 11), "capacity": (2, 11),
        "risk": (6, 8, 12), "gains": (11, 2),
    },
))
_reg(DomainSpec(
    key="vehicle", slice="vehicle_engine_v1",
    schema_version="vehicle_engine_execution_v1",
    json_label="VEHICLE_ENGINE_EXECUTION_JSON",
    focus_houses=(4, 11, 3),
    focus_planets=("Venus", "Mars", "Moon"),
    dimensions=("vehicle_yog", "affordability", "safety", "growth"),
    default_archetype="general_vehicle", topic_label="vehicle/gaadi",
    divisional="D4",
    dim_house_map={
        "vehicle_yog": (4, 11), "affordability": (2, 11),
        "safety": (3, 8), "growth": (11, 4),
    },
))
_reg(DomainSpec(
    key="litigation", slice="litigation_engine_v1",
    schema_version="litigation_engine_execution_v1",
    json_label="LITIGATION_ENGINE_EXECUTION_JSON",
    focus_houses=(6, 7, 8, 12),
    focus_planets=("Saturn", "Mars", "Rahu", "Jupiter"),
    dimensions=("case_strength", "delay_risk", "relief", "enemy_pressure"),
    default_archetype="general_litigation", topic_label="litigation/court",
    divisional="D6",
    banned="legal advice as lawyer, guaranteed acquittal, exact court date",
    dim_house_map={
        "case_strength": (6, 7), "delay_risk": (8, 12),
        "relief": (9, 11), "enemy_pressure": (6, 8),
    },
))
_reg(DomainSpec(
    key="luck", slice="luck_engine_v1",
    schema_version="luck_engine_execution_v1",
    json_label="LUCK_ENGINE_EXECUTION_JSON",
    focus_houses=(9, 5, 11),
    focus_planets=("Jupiter", "Venus", "Sun"),
    dimensions=("overall_luck", "fortune_flow", "opportunity", "blocks"),
    default_archetype="general_luck", topic_label="luck/bhagya",
    dim_house_map={
        "overall_luck": (9, 1), "fortune_flow": (9, 11),
        "opportunity": (5, 11), "blocks": (6, 8, 12),
    },
))
_reg(DomainSpec(
    key="network", slice="network_engine_v1",
    schema_version="network_engine_execution_v1",
    json_label="NETWORK_ENGINE_EXECUTION_JSON",
    focus_houses=(11, 3, 7),
    focus_planets=("Mercury", "Jupiter", "Venus"),
    dimensions=("circle_quality", "support", "influence", "friction"),
    default_archetype="general_network", topic_label="network/friends",
    divisional="D11",
    dim_house_map={
        "circle_quality": (11, 3), "support": (11, 7),
        "influence": (11, 10), "friction": (6, 8),
    },
))
_reg(DomainSpec(
    key="siblings", slice="siblings_engine_v1",
    schema_version="siblings_engine_execution_v1",
    json_label="SIBLINGS_ENGINE_EXECUTION_JSON",
    focus_houses=(3, 11), focus_planets=("Mars", "Mercury", "Jupiter"),
    dimensions=("sibling_bond", "support", "friction"),
    default_archetype="general_siblings", topic_label="siblings",
    dim_house_map={"sibling_bond": (3, 11), "support": (11, 3), "friction": (6, 8)},
))
_reg(DomainSpec(
    key="parents", slice="parents_engine_v1",
    schema_version="parents_engine_execution_v1",
    json_label="PARENTS_ENGINE_EXECUTION_JSON",
    focus_houses=(4, 9, 10), focus_planets=("Moon", "Sun", "Jupiter"),
    dimensions=("parent_bond", "father_theme", "mother_theme"),
    default_archetype="general_parents", topic_label="parents",
    dim_house_map={"parent_bond": (4, 9), "father_theme": (9, 10), "mother_theme": (4,)},
))
_reg(DomainSpec(
    key="enemies", slice="enemies_engine_v1",
    schema_version="enemies_engine_execution_v1",
    json_label="ENEMIES_ENGINE_EXECUTION_JSON",
    focus_houses=(6, 8, 12), focus_planets=("Mars", "Saturn", "Rahu"),
    dimensions=("enemy_pressure", "protection", "conflict_risk"),
    default_archetype="general_enemies", topic_label="enemies/shatru",
    dim_house_map={"enemy_pressure": (6, 8), "protection": (1, 9), "conflict_risk": (6, 12)},
))
_reg(DomainSpec(
    key="fame", slice="fame_engine_v1",
    schema_version="fame_engine_execution_v1",
    json_label="FAME_ENGINE_EXECUTION_JSON",
    focus_houses=(1, 10, 11), focus_planets=("Sun", "Jupiter", "Venus"),
    dimensions=("fame_potential", "reputation", "visibility"),
    default_archetype="general_fame", topic_label="fame/reputation",
    divisional="D10",
    dim_house_map={"fame_potential": (1, 10), "reputation": (10, 11), "visibility": (11, 1)},
))
_reg(DomainSpec(
    key="personality", slice="personality_engine_v1",
    schema_version="personality_engine_execution_v1",
    json_label="PERSONALITY_ENGINE_EXECUTION_JSON",
    focus_houses=(1, 5), focus_planets=("Sun", "Moon", "Ascendant"),
    dimensions=("self_nature", "expression", "confidence"),
    default_archetype="general_personality", topic_label="personality",
    dim_house_map={"self_nature": (1,), "expression": (5, 3), "confidence": (1, 10)},
))
_reg(DomainSpec(
    key="dreams", slice="dreams_engine_v1",
    schema_version="dreams_engine_execution_v1",
    json_label="DREAMS_ENGINE_EXECUTION_JSON",
    focus_houses=(12, 4), focus_planets=("Moon", "Ketu", "Mercury"),
    dimensions=("dream_activity", "restlessness", "insight"),
    default_archetype="general_dreams", topic_label="dreams",
    dim_house_map={"dream_activity": (12, 4), "restlessness": (12, 8), "insight": (9, 12)},
))
_reg(DomainSpec(
    key="anger", slice="anger_engine_v1",
    schema_version="anger_engine_execution_v1",
    json_label="ANGER_ENGINE_EXECUTION_JSON",
    focus_houses=(1, 6, 8), focus_planets=("Mars", "Sun", "Saturn"),
    dimensions=("temper", "impulse", "control"),
    default_archetype="general_anger", topic_label="anger/temper",
    dim_house_map={"temper": (1, 6), "impulse": (8, 3), "control": (1, 10)},
))
_reg(DomainSpec(
    key="charity", slice="charity_engine_v1",
    schema_version="charity_engine_execution_v1",
    json_label="CHARITY_ENGINE_EXECUTION_JSON",
    focus_houses=(9, 12), focus_planets=("Jupiter", "Venus"),
    dimensions=("daan_yog", "punya_flow", "service"),
    default_archetype="general_charity", topic_label="charity/daan",
    dim_house_map={"daan_yog": (9, 12), "punya_flow": (9, 11), "service": (6, 12)},
))
_reg(DomainSpec(
    key="remedy", slice="remedy_engine_v1",
    schema_version="remedy_engine_execution_v1",
    json_label="REMEDY_ENGINE_EXECUTION_JSON",
    focus_houses=(9, 12, 5), focus_planets=("Jupiter", "Sun", "Moon"),
    dimensions=("remedy_receptivity", "faith_support", "practice"),
    default_archetype="general_remedy", topic_label="remedy/upay",
    banned="guaranteed cure, replace medical/legal advice",
    dim_house_map={"remedy_receptivity": (9, 5), "faith_support": (9, 12), "practice": (5, 1)},
))
_reg(DomainSpec(
    key="settlement", slice="settlement_engine_v1",
    schema_version="settlement_engine_execution_v1",
    json_label="SETTLEMENT_ENGINE_EXECUTION_JSON",
    focus_houses=(12, 9, 4), focus_planets=("Rahu", "Saturn", "Jupiter"),
    dimensions=("settle_support", "home_anchor", "visa_luck"),
    default_archetype="general_settlement", topic_label="settlement/abroad basna",
    dim_house_map={"settle_support": (12, 9), "home_anchor": (4,), "visa_luck": (9, 12)},
))
_reg(DomainSpec(
    key="vastu", slice="vastu_engine_v1",
    schema_version="vastu_engine_execution_v1",
    json_label="VASTU_ENGINE_EXECUTION_JSON",
    focus_houses=(4, 2), focus_planets=("Mars", "Saturn", "Moon"),
    dimensions=("home_harmony", "space_stress", "remedy_openness"),
    default_archetype="general_vastu", topic_label="vastu",
    dim_house_map={"home_harmony": (4,), "space_stress": (4, 8), "remedy_openness": (9, 4)},
))
_reg(DomainSpec(
    key="pets", slice="pets_engine_v1",
    schema_version="pets_engine_execution_v1",
    json_label="PETS_ENGINE_EXECUTION_JSON",
    focus_houses=(6, 3), focus_planets=("Mercury", "Moon", "Venus"),
    dimensions=("pet_suitability", "care_capacity", "bond"),
    default_archetype="general_pets", topic_label="pets",
    dim_house_map={"pet_suitability": (6, 3), "care_capacity": (2, 6), "bond": (4, 6)},
))
_reg(DomainSpec(
    key="wellness", slice="wellness_engine_v1",
    schema_version="wellness_engine_execution_v1",
    json_label="WELLNESS_ENGINE_EXECUTION_JSON",
    focus_houses=(1, 6), focus_planets=("Moon", "Sun", "Saturn"),
    dimensions=("vitality", "habits", "sleep_rest"),
    default_archetype="general_wellness", topic_label="wellness/lifestyle",
    divisional="D30",
    banned="medical diagnosis, cure guarantee",
    dim_house_map={"vitality": (1, 6), "habits": (6, 2), "sleep_rest": (12, 4)},
))
_reg(DomainSpec(
    key="spiritual", slice="spiritual_engine_v1",
    schema_version="spiritual_engine_execution_v1",
    json_label="SPIRITUAL_ENGINE_EXECUTION_JSON",
    focus_houses=(9, 12, 8), focus_planets=("Jupiter", "Ketu", "Saturn"),
    dimensions=("spiritual_path", "detachment", "guru_support"),
    default_archetype="general_spiritual", topic_label="spiritual",
    divisional="D20",
    dim_house_map={"spiritual_path": (9, 12), "detachment": (12, 8), "guru_support": (9, 5)},
))


def get_domain_spec(key: str) -> Optional[DomainSpec]:
    return _DOMAINS.get((key or "").strip().lower())


def all_domain_keys() -> list[str]:
    return sorted(_DOMAINS.keys())


def slice_to_domain(slice_id: str) -> Optional[str]:
    s = (slice_id or "").strip()
    for key, spec in _DOMAINS.items():
        if spec.slice == s:
            return key
    return None


def is_unified_slice(slice_id: str) -> bool:
    return slice_to_domain(slice_id) is not None
