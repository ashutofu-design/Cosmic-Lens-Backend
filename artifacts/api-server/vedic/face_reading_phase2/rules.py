"""Versioned, isolated traditional face-reading rule registries."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

RULE_FORMAT_VERSION = "1.0"


@dataclass(frozen=True)
class Condition:
    path: str
    feature_path: str
    operator: str
    value: Any


@dataclass(frozen=True)
class Rule:
    rule_id: str
    system_id: str
    domain: str
    category: str
    signal_name: str
    conditions: tuple[Condition, ...]
    feature_families: tuple[str, ...]
    zones: tuple[str, ...]
    minimum_confidence: float
    weight: float
    polarity: int
    rule_confidence: float
    priority: int
    scope: str
    interpretation: str
    evidence_requirements: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuleSystem:
    system_id: str
    namespace: str
    version: str
    display_name: str
    rules: tuple[Rule, ...]
    disclaimer: str


def c(path: str, feature: str, operator: str, value: Any) -> Condition:
    return Condition(path, feature, operator, value)


def r(
    rule_id: str,
    system_id: str,
    domain: str,
    category: str,
    signal_name: str,
    conditions: tuple[Condition, ...],
    families: tuple[str, ...],
    zones: tuple[str, ...],
    interpretation: str,
    *,
    minimum: float = .55,
    weight: float = 1.0,
    polarity: int = 1,
    confidence: float = .78,
    priority: int = 3,
    scope: str = "single",
) -> Rule:
    return Rule(
        rule_id=f"{system_id}.{rule_id}",
        system_id=system_id,
        domain=domain,
        category=category,
        signal_name=signal_name,
        conditions=conditions,
        feature_families=families,
        zones=zones,
        minimum_confidence=minimum,
        weight=weight,
        polarity=polarity,
        rule_confidence=confidence,
        priority=priority,
        scope=scope,
        interpretation=interpretation,
        evidence_requirements=tuple(condition.path for condition in conditions),
    )


S = "indian_samudrik_v1"
SAMUDRIK_RULES = (
    r("FACE_OVAL", S, "personality", "adaptability", "balanced_face_contour",
      (c("face_shape.label", "face_shape", "eq", "oval"),),
      ("face_structure",), ("upper", "middle", "lower"),
      "Traditional Samudrik-style reading associates an oval measured contour with adaptable presentation.",
      priority=4),
    r("FACE_SQUARE", S, "leadership_recognition", "leadership", "angular_face_contour",
      (c("face_shape.label", "face_shape", "in", ("square", "rectangular")),),
      ("face_structure",), ("lower", "chin"),
      "Traditional Samudrik-style reading associates a more angular measured contour with direct outward presentation.",
      priority=4),
    r("FACE_LONG", S, "personality", "temperament", "elongated_proportion",
      (c("face_geometry.aspect_ratio.value", "face_geometry.aspect_ratio", "gte", 1.45),),
      ("face_proportion",), ("upper", "middle", "lower"),
      "Traditional Samudrik-style reading associates a relatively elongated face proportion with a measured, deliberate presentation.",
      priority=4),
    r("THIRDS_BALANCED", S, "traditional_life_profile", "regional_balance",
      "balanced_facial_thirds",
      (c("face_geometry.facial_thirds", "face_geometry", "balanced_measurements", .12),),
      ("face_proportion",), ("upper", "middle", "lower"),
      "Traditional Samudrik-style reading treats relatively balanced facial thirds as a symbol of regional balance.",
      priority=4),
    r("SYMMETRY_LOW_ERROR", S, "social_communication", "social_presentation",
      "low_measured_asymmetry",
      (c("symmetry.overall_error_normalized", "symmetry", "lte", .035),),
      ("symmetry",), ("left_face", "right_face"),
      "Traditional Samudrik-style reading associates low measured left-right asymmetry with even social presentation.",
      priority=4),
    r("SYMMETRY_HIGH_ERROR", S, "social_communication", "challenges",
      "visible_asymmetry_variation",
      (c("symmetry.overall_error_normalized", "symmetry", "gte", .075),),
      ("symmetry",), ("left_face", "right_face"),
      "Traditional Samudrik-style reading records stronger measured asymmetry as varied outward expression, not a defect.",
      polarity=-1, priority=4),
    r("FOREHEAD_RELATIVE_HIGH", S, "personality", "decision_making",
      "relatively_high_forehead",
      (c("forehead.height_to_face_ratio.value", "forehead.height_to_face_ratio", "gte", .17),),
      ("forehead_structure",), ("forehead", "upper"),
      "Traditional Samudrik-style reading associates a relatively high measured forehead region with reflective decision symbolism."),
    r("BROW_SPACING_OPEN", S, "personality", "independence", "open_brow_spacing",
      (c("eyebrows.inner_spacing.normalized", "eyebrows.inner_spacing", "gte", .08),),
      ("eyebrow_structure",), ("eyebrow_eye",),
      "Traditional Samudrik-style reading associates wider measured brow spacing with independent presentation."),
    r("BROW_ARCH_DEFINED", S, "social_communication", "communication",
      "defined_brow_arch",
      (c("eyebrows.right.arch_position.value", "eyebrows.right.arch_position", "between", (.25, .75)),
       c("eyebrows.left.arch_position.value", "eyebrows.left.arch_position", "between", (.25, .75))),
      ("eyebrow_structure",), ("eyebrow_eye",),
      "Traditional Samudrik-style reading associates bilaterally measured brow arches with deliberate expressive presentation."),
    r("BROW_THICKNESS_VISIBLE", S, "personality", "temperament",
      "measured_brow_thickness",
      (c("eyebrows.right.thickness.value", "eyebrows.right.thickness", "gte", .02),
       c("eyebrows.left.thickness.value", "eyebrows.left.thickness", "gte", .02)),
      ("eyebrow_structure",), ("eyebrow_eye",),
      "Traditional Samudrik-style reading has a symbolic association for reliably measured bilateral brow thickness."),
    r("EYE_SPACING_OPEN", S, "personality", "adaptability", "open_eye_spacing",
      (c("eyes.interocular_distance.normalized", "eyes.interocular_distance", "gte", .10),),
      ("eye_structure",), ("eyebrow_eye",),
      "Traditional Samudrik-style reading associates relatively wider measured eye spacing with broad attentional symbolism."),
    r("EYE_ASPECT_NARROW", S, "personality", "challenges", "narrow_eye_aperture",
      (c("eyes.right.aspect_ratio.value", "eyes.right.aspect_ratio", "gte", 3.2),
       c("eyes.left.aspect_ratio.value", "eyes.left.aspect_ratio", "gte", 3.2)),
      ("eye_structure",), ("eyebrow_eye",),
      "Traditional Samudrik-style reading records a relatively narrow measured eye aperture as reserved expressive symbolism.",
      polarity=-1),
    r("EYELID_VISIBLE", S, "relationships", "emotional_expression",
      "visible_eyelid_structure",
      (c("eyes.right.eyelid_visibility.value", "eyes.right.eyelid_visibility", "eq", "visible"),
       c("eyes.left.eyelid_visibility.value", "eyes.left.eyelid_visibility", "eq", "visible")),
      ("eye_structure",), ("eyebrow_eye",),
      "Traditional Samudrik-style reading has a symbolic association for reliably observed bilateral eyelid structure."),
    r("NOSE_RELATIVE_WIDE", S, "career", "work_style", "substantial_nose_width",
      (c("nose.nose_to_face_ratio.value", "nose.nose_to_face_ratio", "gte", .17),),
      ("nose_structure",), ("nose", "middle"),
      "Traditional Samudrik-style reading associates a relatively substantial measured nose width with practical work symbolism."),
    r("NOSE_LENGTH", S, "money", "financial_discipline", "defined_nose_length",
      (c("nose.length.normalized", "nose.length", "gte", .18),),
      ("nose_structure",), ("nose", "middle"),
      "Traditional Samudrik-style reading associates a relatively long measured nose region with deliberate resource symbolism."),
    r("NOSE_BRIDGE_DEFINED", S, "career", "work_style",
      "defined_nose_bridge",
      (c("nose.bridge_width.value", "nose.bridge_width", "gte", .02),),
      ("nose_structure",), ("nose", "middle"),
      "Traditional Samudrik-style reading has a symbolic association for a reliably measured nose bridge."),
    r("NOSE_TIP_DEFINED", S, "money", "stability", "defined_nose_tip",
      (c("nose.tip_width.value", "nose.tip_width", "gte", .02),),
      ("nose_structure",), ("nose", "middle"),
      "Traditional Samudrik-style reading has a symbolic association for a reliably measured nose tip."),
    r("MOUTH_RELATIVE_WIDE", S, "social_communication", "communication",
      "wide_mouth_proportion",
      (c("mouth.mouth_to_face_ratio.value", "mouth.mouth_to_face_ratio", "gte", .30),),
      ("mouth_structure",), ("mouth", "lower"),
      "Traditional Samudrik-style reading associates a relatively wide measured mouth proportion with outward communication symbolism."),
    r("LIP_BALANCE", S, "relationships", "emotional_expression",
      "balanced_lip_proportion",
      (c("mouth.upper_lower_lip_ratio.value", "mouth.upper_lower_lip_ratio", "between", (.65, 1.35)),),
      ("mouth_structure",), ("mouth", "lower"),
      "Traditional Samudrik-style reading associates balanced measured upper-lower lip proportions with even expressive symbolism."),
    r("JAW_RELATIVE_WIDE", S, "personality", "independence", "wide_jaw_proportion",
      (c("face_geometry.ratios.jaw_to_cheek_width", "face_geometry.ratios", "gte", .78),),
      ("jaw_structure",), ("right_cheek", "left_cheek", "lower"),
      "Traditional Samudrik-style reading associates a relatively broad measured jaw with firm outward presentation.",
      priority=4),
    r("JAW_ANGLE_DEFINED", S, "leadership_recognition", "leadership",
      "defined_jaw_angle",
      (c("jaw.angle.degrees", "jaw.angle", "between", (95, 145)),),
      ("jaw_structure",), ("right_cheek", "left_cheek", "lower"),
      "Traditional Samudrik-style reading has a symbolic association for a reliably measured jaw angle.",
      priority=4),
    r("CHIN_RELATIVE_HIGH", S, "leadership_recognition", "persistence",
      "substantial_chin_height",
      (c("chin.chin_to_face_ratio.value", "chin.chin_to_face_ratio", "gte", .16),),
      ("chin_structure",), ("chin", "lower"),
      "Traditional Samudrik-style reading associates a relatively substantial measured chin region with persistence symbolism."),
    r("COGNITIVE_COMBINATION", S, "personality", "decision_making",
      "structured_attention_pattern",
      (c("forehead.height_to_face_ratio.value", "forehead.height_to_face_ratio", "gte", .16),
       c("eyebrows.inner_spacing.normalized", "eyebrows.inner_spacing", "gte", .07),
       c("eyes.interocular_distance.normalized", "eyes.interocular_distance", "gte", .09)),
      ("forehead_structure", "eyebrow_structure", "eye_structure"),
      ("forehead", "eyebrow_eye", "upper"),
      "Together, these measured forehead, brow, and eye proportions are traditionally associated with a structured but open attentional style.",
      confidence=.74, priority=4, scope="cross"),
    r("CAREER_RESOURCE_COMBINATION", S, "career", "ambition",
      "structured_resource_pattern",
      (c("nose.nose_to_face_ratio.value", "nose.nose_to_face_ratio", "gte", .15),
       c("face_geometry.ratios.jaw_to_cheek_width", "face_geometry.ratios", "gte", .70),
       c("chin.chin_to_face_ratio.value", "chin.chin_to_face_ratio", "gte", .14)),
      ("nose_structure", "jaw_structure", "chin_structure"),
      ("nose", "right_cheek", "left_cheek", "chin", "middle", "lower"),
      "Together, these measured nose, jaw, and chin proportions are traditionally associated with sustained practical effort.",
      confidence=.72, priority=4, scope="cross"),
    r("RELATIONSHIP_SOCIAL_COMBINATION", S, "relationships", "relationship_style",
      "coordinated_social_expression",
      (c("symmetry.overall_error_normalized", "symmetry", "lte", .05),
       c("mouth.mouth_to_face_ratio.value", "mouth.mouth_to_face_ratio", "gte", .25),
       c("eyebrows.inner_spacing.normalized", "eyebrows.inner_spacing", "gte", .06)),
      ("symmetry", "mouth_structure", "eyebrow_structure"),
      ("left_face", "right_face", "mouth", "eyebrow_eye"),
      "Together, these measured symmetry, mouth, and brow features are traditionally associated with coordinated social expression.",
      confidence=.72, priority=4, scope="cross"),
    r("VERIFIED_FOREHEAD_MARK", S, "traditional_life_profile", "visible_markings",
      "verified_forehead_marking",
      (c("skin_surface_features.visible_marks_or_moles.items",
         "skin_surface_features.visible_marks_or_moles",
         "contains_verified_marking", "forehead"),),
      ("visible_marking",), ("forehead",),
      "A verified visible forehead marking has a tradition-specific symbolic association; no medical meaning is inferred.",
      minimum=.70, weight=.25, confidence=.60, priority=1),
    r("VERIFIED_SCAR", S, "traditional_life_profile", "visible_markings",
      "verified_visible_scar",
      (c("skin_surface_features.scars.items", "skin_surface_features.scars",
         "contains_verified_marking", "forehead"),),
      ("visible_marking",), ("forehead",),
      "A verified visible scar may be recorded in the selected tradition, without medical or life-event inference.",
      minimum=.70, weight=.20, confidence=.58, priority=1),
    r("VERIFIED_CREASE", S, "traditional_life_profile", "visible_markings",
      "verified_visible_crease",
      (c("skin_surface_features.fine_lines_or_creases.candidates",
         "skin_surface_features.fine_lines_or_creases",
         "contains_verified_marking", "forehead"),),
      ("visible_marking",), ("forehead",),
      "A verified visible crease may be recorded as tradition-specific symbolism, not as a health or future claim.",
      minimum=.70, weight=.20, confidence=.58, priority=1),
)


C = "chinese_mian_xiang_v1"
MIAN_XIANG_RULES = (
    r("THREE_REGIONS_BALANCED", C, "traditional_life_profile", "regional_balance",
      "three_regions_balanced",
      (c("face_geometry.facial_thirds", "face_geometry", "balanced_measurements", .12),),
      ("face_proportion",), ("upper", "middle", "lower"),
      "Traditional Mian Xiang associates relatively balanced measured upper, middle, and lower regions with regional harmony.",
      priority=4),
    r("FOREHEAD_REGION_HIGH", C, "personality", "temperament",
      "prominent_upper_region",
      (c("forehead.height_to_face_ratio.value", "forehead.height_to_face_ratio", "gte", .17),),
      ("forehead_structure",), ("forehead", "upper"),
      "Traditional Mian Xiang associates a relatively high measured upper region with contemplative symbolism."),
    r("BROW_EYE_OPEN", C, "social_communication", "social_presentation",
      "open_brow_eye_region",
      (c("eyebrows.inner_spacing.normalized", "eyebrows.inner_spacing", "gte", .07),
       c("eyes.interocular_distance.normalized", "eyes.interocular_distance", "gte", .09)),
      ("eyebrow_structure", "eye_structure"), ("eyebrow_eye",),
      "Traditional Mian Xiang associates an open measured brow-eye region with receptive social presentation.",
      scope="cross"),
    r("NOSE_CENTER_DEFINED", C, "money", "stability",
      "defined_center_region",
      (c("nose.nose_to_face_ratio.value", "nose.nose_to_face_ratio", "between", (.13, .22)),
       c("nose.length.normalized", "nose.length", "gte", .16)),
      ("nose_structure",), ("nose", "middle"),
      "Traditional Mian Xiang associates a proportionate measured central nose region with resource-stability symbolism."),
    r("MOUTH_BALANCED", C, "relationships", "communication",
      "balanced_mouth_region",
      (c("mouth.upper_lower_lip_ratio.value", "mouth.upper_lower_lip_ratio", "between", (.65, 1.35)),
       c("symmetry.regions.mouth.mean_error_normalized", "symmetry.regions.mouth", "lte", .04)),
      ("mouth_structure", "symmetry"), ("mouth", "lower"),
      "Traditional Mian Xiang associates balanced measured lip proportion and mouth symmetry with even communication symbolism.",
      scope="cross"),
    r("LOWER_REGION_FIRM", C, "career", "stability_change",
      "firm_lower_region",
      (c("face_geometry.ratios.jaw_to_cheek_width", "face_geometry.ratios", "gte", .76),
       c("chin.chin_to_face_ratio.value", "chin.chin_to_face_ratio", "gte", .15)),
      ("jaw_structure", "chin_structure"),
      ("right_cheek", "left_cheek", "chin", "lower"),
      "Traditional Mian Xiang associates a relatively substantial measured lower region with continuity symbolism.",
      scope="cross", priority=4),
    r("FACE_LEFT_RIGHT_EVEN", C, "social_communication", "interpersonal_style",
      "even_left_right_regions",
      (c("symmetry.overall_error_normalized", "symmetry", "lte", .035),),
      ("symmetry",), ("left_face", "right_face"),
      "Traditional Mian Xiang associates low measured left-right asymmetry with even interpersonal presentation.",
      priority=4),
    r("CENTER_LOWER_COMBINATION", C, "leadership_recognition", "recognition",
      "center_lower_continuity",
      (c("nose.length.normalized", "nose.length", "gte", .16),
       c("face_geometry.ratios.jaw_to_cheek_width", "face_geometry.ratios", "gte", .70),
       c("chin.chin_to_face_ratio.value", "chin.chin_to_face_ratio", "gte", .14)),
      ("nose_structure", "jaw_structure", "chin_structure"),
      ("nose", "middle", "right_cheek", "left_cheek", "chin", "lower"),
      "Traditional Mian Xiang combines the measured center and lower regions as a symbol of sustained public effort.",
      scope="cross", priority=4),
)


SYSTEMS = {
    S: RuleSystem(
        S, "indian.samudrik", "1.0", "Indian Samudrik-style",
        SAMUDRIK_RULES,
        "Traditional Samudrik-style associations are cultural interpretations, not scientific findings.",
    ),
    C: RuleSystem(
        C, "chinese.mian_xiang", "1.0", "Chinese Mian Xiang-style",
        MIAN_XIANG_RULES,
        "Traditional Mian Xiang associations are cultural interpretations, not scientific findings.",
    ),
}
DEFAULT_SYSTEM_ID = S


DOMAINS = {
    "personality": (
        "temperament", "emotional_expression", "decision_making",
        "independence", "social_behaviour", "adaptability", "ambition",
        "leadership", "strengths", "challenges",
    ),
    "relationships": (
        "emotional_expression", "attachment_tendencies", "communication",
        "relationship_style", "social_interaction", "commitment_tendencies",
    ),
    "career": (
        "work_style", "ambition", "leadership", "independence",
        "stability_change", "recognition", "entrepreneurial",
    ),
    "money": (
        "financial_discipline", "earning_orientation", "risk_tendency",
        "spending_tendencies", "stability",
    ),
    "social_communication": (
        "communication", "social_presentation", "interpersonal_style",
        "leadership", "challenges",
    ),
    "leadership_recognition": (
        "leadership", "recognition", "persistence", "social_indicators",
    ),
    "traditional_life_profile": (
        "regional_balance", "combined_profile", "visible_markings",
    ),
}
