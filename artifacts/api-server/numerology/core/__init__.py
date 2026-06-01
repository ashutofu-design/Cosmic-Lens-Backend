"""Pure numerology core — canonical implementation."""

from numerology.core.digits import (
    ARCHETYPE_BY_DRIVER,
    ARCHETYPE_SHORT,
    DIGIT_TRAITS,
    archetype_for,
    digit_trait,
    reduce_number,
)
from numerology.core.compatibility import (
    compat_label,
    compatibility_row,
    deep_compatibility_pack,
    number_relationship,
    rel_code,
)
from numerology.core.scope import (
    ai_section_allowed,
    include_celebrity_match,
    include_extended_extras,
    report_product_subtitle,
    report_product_title,
)
from numerology.core.toolkit import LUCKY, affirmations_pack
from numerology.core.colours import lucky_colours_pack
from numerology.core.weekdays import weekday_productivity_pack
from numerology.core.number_analysis import (
    analyze_identifier,
    digit_position_rows,
    detect_digit_pairs,
    why_impact_action_for_number,
)
from numerology.core.asset_analysis import (
    analyze_number_string,
    normalize_input,
    normalize_phone_input,
    normalize_vehicle_input,
    normalize_house_input,
)
from numerology.core.pure_numerology import (
    AFFIRMATIONS_BY_DRIVER,
    PRACTICAL_BY_DRIVER,
    affirmations_pack,
    mantras_pack,
)
from numerology.core.sanitize import sanitize_mapping, sanitize_text

__all__ = [
    "ARCHETYPE_BY_DRIVER",
    "ARCHETYPE_SHORT",
    "DIGIT_TRAITS",
    "LUCKY",
    "affirmations_pack",
    "ai_section_allowed",
    "AFFIRMATIONS_BY_DRIVER",
    "PRACTICAL_BY_DRIVER",
    "analyze_identifier",
    "analyze_number_string",
    "normalize_input",
    "normalize_phone_input",
    "normalize_vehicle_input",
    "normalize_house_input",
    "affirmations_pack",
    "mantras_pack",
    "archetype_for",
    "compat_label",
    "compatibility_row",
    "deep_compatibility_pack",
    "detect_digit_pairs",
    "digit_position_rows",
    "digit_trait",
    "include_celebrity_match",
    "include_extended_extras",
    "lucky_colours_pack",
    "number_relationship",
    "reduce_number",
    "rel_code",
    "report_product_subtitle",
    "report_product_title",
    "sanitize_mapping",
    "sanitize_text",
    "weekday_productivity_pack",
    "why_impact_action_for_number",
]
