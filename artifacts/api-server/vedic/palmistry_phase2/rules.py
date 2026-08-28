"""Versioned traditional-palmistry rules expressed as independent records."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

RULESET_VERSION = "1.0"


@dataclass(frozen=True)
class Condition:
    path: str
    operator: str
    value: Any


@dataclass(frozen=True)
class Rule:
    rule_id: str
    domain: str
    category: str
    family: str
    conditions: tuple[Condition, ...]
    required_confidence: float
    polarity: int
    weight: float
    rule_confidence: float
    interpretation: str
    evidence_paths: tuple[str, ...]
    priority: int
    source_tradition: str = "traditional_palmistry"

    def to_dict(self) -> dict:
        return asdict(self)


def _rule(
    rule_id: str, domain: str, category: str, family: str, path: str,
    operator: str, value: Any, interpretation: str, *,
    polarity: int = 1, weight: float = 1.0, required: float = .55,
    confidence: float = .82, priority: int = 2,
) -> Rule:
    return Rule(
        rule_id, domain, category, family, (Condition(path, operator, value),),
        required, polarity, weight, confidence, interpretation, (path,),
        priority,
    )


# Priority: 3 major line, 2 mount/hand/thumb/finger, 1 minor marking.
RULES: tuple[Rule, ...] = (
    _rule("heart_clear", "love_relationships", "emotional_expression", "major_line",
          "major_lines.heart_line.measurements.clarity", "gte", .65,
          "Traditional reading associates a clear heart line with direct emotional expression.", priority=3),
    _rule("heart_broken", "love_relationships", "emotional_consistency", "major_line",
          "major_lines.heart_line.measurements.break_candidates", "nonempty", True,
          "Break candidates traditionally suggest uneven emotional expression.", polarity=-1, priority=3),
    _rule("heart_branches", "love_relationships", "communication_style", "major_line",
          "major_lines.heart_line.measurements.branch_candidates", "nonempty", True,
          "Detected heart-line branch observations are traditionally read as varied emotional expression.", priority=3),
    _rule("heart_islands", "love_relationships", "challenges", "major_line",
          "major_lines.heart_line.measurements.island_candidates", "nonempty", True,
          "Detected heart-line island observations are traditionally recorded as emotional complexity, not a prediction.",
          polarity=-1, priority=3),
    _rule("head_clear", "personality", "thinking_style", "major_line",
          "major_lines.head_line.measurements.clarity", "gte", .65,
          "A clear head line is traditionally associated with focused thought.", priority=3),
    _rule("head_curved", "personality", "thinking_style", "major_line",
          "major_lines.head_line.measurements.curvature", "gte", .20,
          "A curved head line is traditionally associated with imaginative thinking.", priority=3),
    _rule("head_fork", "personality", "adaptability", "major_line",
          "major_lines.head_line.measurements.fork_candidates", "nonempty", True,
          "A detected head-line fork is traditionally associated with considering more than one perspective.", priority=3),
    _rule("life_continuous", "traditional_vitality", "steadiness", "major_line",
          "major_lines.life_line.measurements.continuity", "gte", .70,
          "Traditional palmistry links continuity of the life line with steadiness; this is not a health or lifespan claim.", priority=3),
    _rule("fate_clear", "career", "direction", "major_line",
          "major_lines.fate_line.measurements.clarity", "gte", .65,
          "A clear fate line is traditionally associated with a consistent vocational direction.", priority=3),
    _rule("fate_fork", "career", "stability_change", "major_line",
          "major_lines.fate_line.measurements.fork_candidates", "nonempty", True,
          "A detected fate-line fork is traditionally recorded as more than one work-direction tendency, not a future event.", priority=3),
    _rule("sun_clear", "recognition_success", "visibility", "major_line",
          "major_lines.sun_apollo_line.measurements.clarity", "gte", .65,
          "A clear Sun/Apollo line is traditionally associated with visibility for one's work.", priority=3),
    _rule("mercury_clear", "money", "commercial_style", "major_line",
          "major_lines.mercury_line.measurements.clarity", "gte", .65,
          "A clear Mercury line is traditionally associated with communication in practical affairs.", priority=3),
    _rule("mars_support", "traditional_vitality", "resilience_symbolism", "major_line",
          "major_lines.mars_support_line.measurements.continuity", "gte", .65,
          "A continuous Mars support line traditionally symbolizes persistence.", priority=3),

    _rule("jupiter_developed", "career", "leadership", "mount",
          "mounts.Jupiter.development.value", "gte", .60,
          "A developed Jupiter mount is traditionally associated with leadership inclination."),
    _rule("saturn_developed", "personality", "responsibility", "mount",
          "mounts.Saturn.development.value", "gte", .60,
          "A developed Saturn mount is traditionally associated with deliberation and responsibility."),
    _rule("apollo_developed", "recognition_success", "creative_visibility", "mount",
          "mounts.Sun/Apollo.development.value", "gte", .60,
          "A developed Apollo mount is traditionally associated with creative visibility."),
    _rule("mercury_mount_developed", "money", "commercial_style", "mount",
          "mounts.Mercury.development.value", "gte", .60,
          "A developed Mercury mount is traditionally associated with communication and commerce."),
    _rule("upper_mars_developed", "personality", "assertiveness", "mount",
          "mounts.Upper Mars.development.value", "gte", .60,
          "A developed Upper Mars mount traditionally symbolizes assertiveness."),
    _rule("lower_mars_developed", "traditional_vitality", "resilience_symbolism", "mount",
          "mounts.Lower Mars.development.value", "gte", .60,
          "A developed Lower Mars mount traditionally symbolizes persistence."),
    _rule("venus_developed", "love_relationships", "warmth", "mount",
          "mounts.Venus.development.value", "gte", .60,
          "A developed Venus mount is traditionally associated with warmth and sociability."),
    _rule("moon_developed", "personality", "imagination", "mount",
          "mounts.Moon/Luna.development.value", "gte", .60,
          "A developed Moon/Luna mount is traditionally associated with imagination."),

    _rule("palm_broad", "personality", "temperament", "hand_structure",
          "palm_geometry.aspect_ratio.raw_ratio", "gte", .90,
          "A relatively broad palm is traditionally associated with a practical style."),
    _rule("index_long", "career", "leadership", "finger_structure",
          "fingers.index.relative_length", "relative_long", .78,
          "A relatively long index finger is traditionally associated with leadership inclination."),
    _rule("ring_long", "recognition_success", "creative_visibility", "finger_structure",
          "fingers.ring.relative_length", "relative_long", .78,
          "A relatively long ring finger is traditionally associated with expressive risk tolerance."),
    _rule("little_long", "money", "communication", "finger_structure",
          "fingers.little.relative_length", "relative_long", .70,
          "A relatively long little finger is traditionally associated with communication confidence."),
    _rule("middle_long", "personality", "responsibility", "finger_structure",
          "fingers.middle.relative_length", "relative_long", .95,
          "A relatively long middle finger is traditionally associated with seriousness."),
    _rule("index_tip_tapered", "personality", "adaptability", "finger_structure",
          "fingers.index.tip_shape.classification", "eq", "tapered",
          "A reliably measured tapered index fingertip is traditionally associated with an adaptive expressive style."),
    _rule("finger_spacing_open", "personality", "social_behaviour", "finger_structure",
          "fingers.index.spacing_normalized", "gte", .18,
          "Reliably measured wider index-to-middle spacing is traditionally associated with an independent social style."),
    _rule("thumb_spread", "personality", "independence", "thumb_structure",
          "thumb.spread_angle.raw_degrees", "gte", 45,
          "A wider thumb spread is traditionally associated with independence."),
    _rule("thumb_balanced", "career", "decision_style", "thumb_structure",
          "thumb.phalanx_proportions.values", "balanced_proportions", .25,
          "Balanced thumb phalanges are traditionally associated with balancing will and reasoning."),
    _rule("union_readable_multiple", "marriage", "union", "union_line",
          "union_lines.visible_major_line_count", "gte", 2,
          "Multiple readable union-line candidates are recorded as a traditional relationship-pattern symbol.", required=.60),
    _rule("union_readable_single", "marriage", "commitment", "union_line",
          "union_lines.visible_major_line_count", "eq", 1,
          "One readable union-line candidate is recorded as a traditional relationship-pattern symbol.", required=.60),

    _rule("apollo_star", "recognition_success", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking", ("star", "Sun/Apollo"),
          "A verified star near Apollo is traditionally treated as a visibility symbol.",
          weight=.55, required=.65, confidence=.70, priority=1),
    _rule("jupiter_cross", "marriage", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking", ("cross", "Jupiter"),
          "A verified cross near Jupiter has a traditional relationship symbolism.",
          weight=.45, required=.65, confidence=.68, priority=1),
    _rule("venus_grille", "love_relationships", "emotional_consistency", "marking",
          "special_markings.candidates", "contains_marking", ("grille", "Venus"),
          "A verified grille near Venus is traditionally associated with diffused emotional focus.",
          polarity=-1, weight=.4, required=.65, confidence=.65, priority=1),
    _rule("triangle_marking", "career", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "triangle",
          "A verified triangle is recorded as a traditional concentration symbol.",
          weight=.35, required=.65, confidence=.62, priority=1),
    _rule("square_marking", "traditional_vitality", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "square",
          "A verified square is recorded as a traditional protection symbol, not a health claim.",
          weight=.35, required=.65, confidence=.62, priority=1),
    _rule("trident_marking", "recognition_success", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "trident",
          "A verified trident is recorded as a traditional amplification symbol.",
          weight=.35, required=.65, confidence=.62, priority=1),
    _rule("island_marking", "personality", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "island",
          "A verified island is recorded as a traditional interruption symbol.",
          polarity=-1, weight=.3, required=.65, confidence=.60, priority=1),
    _rule("fork_marking", "career", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "fork",
          "A verified fork is recorded as a traditional branching symbol.",
          weight=.3, required=.65, confidence=.60, priority=1),
    _rule("dot_marking", "personality", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "dot",
          "A verified dot is recorded as a traditional point-of-emphasis symbol.",
          weight=.25, required=.65, confidence=.58, priority=1),
    _rule("vertical_marking", "career", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "vertical_line",
          "A verified minor vertical line is recorded as a traditional supporting symbol.",
          weight=.25, required=.65, confidence=.58, priority=1),
    _rule("horizontal_marking", "career", "traditional_marking", "marking",
          "special_markings.candidates", "contains_marking_type", "horizontal_line",
          "A verified minor horizontal line is recorded as a traditional interrupting symbol.",
          polarity=-1, weight=.25, required=.65, confidence=.58, priority=1),
)

DOMAINS = {
    "personality": (
        "emotional_nature", "thinking_style", "decision_making", "confidence",
        "independence", "social_behaviour", "ambition", "adaptability",
        "risk_tendency", "strengths", "challenges", "responsibility",
        "assertiveness", "imagination", "temperament", "traditional_marking",
    ),
    "love_relationships": (
        "emotional_attachment", "trust_tendency", "commitment_tendency",
        "communication_style", "relationship_stability",
        "attachment_patterns", "challenges", "emotional_expression",
        "emotional_consistency", "warmth",
    ),
    "marriage": (
        "union", "commitment", "stability", "supporting", "contradicting",
        "union_line_observation", "traditional_marking",
    ),
    "career": (
        "work_style", "ambition", "leadership", "independence",
        "stability_change", "recognition", "entrepreneurial", "direction",
        "decision_style", "traditional_marking",
    ),
    "money": (
        "discipline", "risk", "earning", "saving_spending", "stability",
        "commercial_style", "communication",
    ),
    "recognition_success": (
        "recognition", "visibility", "creative_visibility", "traditional_marking",
    ),
    "traditional_vitality": (
        "vitality", "steadiness", "resilience_symbolism", "traditional_marking",
    ),
}
