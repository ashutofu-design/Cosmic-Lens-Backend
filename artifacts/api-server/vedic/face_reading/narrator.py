"""
Narrator — assembles all 22 sections into final ordered ₹1499 report
with proper Hinglish titles, ordering (1→21 + bonus), and metadata.

This is a thin layer: section_mapper + new_sections do the data work,
narrator just produces the final consumer-facing structure.
"""
from __future__ import annotations
from typing import Dict, List


# 21-section ordered template (with Hinglish titles matching the user's spec)
SECTION_TITLES: List[Dict[str, str]] = [
    {"key": "section_1_power_summary",          "no": "01", "title_hi": "Power Summary",                "title_en": "Power Summary"},
    {"key": "section_2_psychological_type",     "no": "02", "title_hi": "Manovigyan Prakar",            "title_en": "Psychological Type"},
    {"key": "section_3_mask_vs_real",           "no": "03", "title_hi": "Mukhauta vs Asli Tum",         "title_en": "Mask vs Real Self"},
    {"key": "section_4_first_impression",       "no": "04", "title_hi": "Pehli Nazar Ka Asar",          "title_en": "First Impression"},
    {"key": "section_5_core_foundation",        "no": "05", "title_hi": "Tumhari Mool Buniyaad",        "title_en": "Core Foundation"},
    {"key": "section_6_feature_analysis",       "no": "06", "title_hi": "Chehre Ke Lakshanon Ka Vishleshan", "title_en": "Feature Analysis"},
    {"key": "section_7_personality_synthesis",  "no": "07", "title_hi": "Vyaktitva Sankalan",           "title_en": "Personality Synthesis"},
    {"key": "section_8_love_relationship_dna",  "no": "08", "title_hi": "Prem aur Sambandh DNA",        "title_en": "Love & Relationship DNA"},
    {"key": "section_9_career_money",           "no": "09", "title_hi": "Career aur Dhan-Yog",          "title_en": "Career & Money"},
    {"key": "section_10_red_flags",             "no": "10", "title_hi": "Khatre Ki Ghanti (Red Flags)", "title_en": "Red Flags"},
    {"key": "section_11_attraction_charisma",   "no": "11", "title_hi": "Akarshan aur Charisma",        "title_en": "Attraction & Charisma"},
    {"key": "section_12_decision_style",        "no": "12", "title_hi": "Nirnay Lene Ka Tareeka",       "title_en": "Decision Style"},
    {"key": "section_13_archetype",             "no": "13", "title_hi": "Tumhara Archetype",            "title_en": "Archetype"},
    {"key": "section_14_life_flow",             "no": "14", "title_hi": "Jeevan Ki Dhaara",             "title_en": "Life Flow (Past · Present · Future)"},
    {"key": "section_15_age_wise_map",          "no": "15", "title_hi": "Aayu-anusaar Bhagya-Map",      "title_en": "Age-wise Fortune Map"},
    {"key": "section_16_health_scan",           "no": "16", "title_hi": "Swasthya Scan",                "title_en": "Health Scan"},
    {"key": "section_17_secret_markings",       "no": "17", "title_hi": "Gupt Chinha (Mole Reading)",   "title_en": "Secret Markings"},
    {"key": "section_18_action_plan",           "no": "18", "title_hi": "Karya-Yojana",                 "title_en": "Action Plan"},
    {"key": "section_19_improvement_hacks",     "no": "19", "title_hi": "Sudhaar Ke Nuskhe (Hacks)",    "title_en": "Improvement Hacks"},
    {"key": "section_20_compatibility",         "no": "20", "title_hi": "Saath Ki Anukulta",            "title_en": "Compatibility Snapshot"},
    {"key": "section_21_final_truth",           "no": "21", "title_hi": "Antim Satya",                  "title_en": "Final Truth Page"},
    {"key": "bonus_personality_score",          "no": "★", "title_hi": "Bonus: Tumhare 5 Score (out of 10)", "title_en": "Bonus: 5 Personality Scores"},
]


def assemble_report(sections: Dict,
                    engines: Dict,
                    person: Dict | None = None,
                    front_quality: Dict | None = None) -> Dict:
    """Build the final ordered report structure."""
    person = person or {}

    # Cover-page metadata
    cover = {
        "name":             person.get("name") or "Insan",
        "gender":           person.get("gender") or "U",
        "age":              person.get("age"),
        "report_title":     "Face Intelligence Report",
        "report_subtitle":  "Tumhare Chehre Mein Likhi Tumhari Kahaani",
        "archetype":        (engines.get("personality") or {}).get("archetype", {}).get("name", "Balanced Soul"),
        "dominant_element": (engines.get("samudrika") or {}).get("element_profile", {}).get("dominant_element", "Balanced"),
        "face_shape":       (engines.get("anthropometry") or {}).get("face_shape_7", {}).get("class", "balanced"),
        "complexion":       (engines.get("samudrika") or {}).get("complexion", ""),
        "perceived_age":    (engines.get("first_impression") or {}).get("perceived_age", {}).get("value"),
    }

    # Inject rich Hinglish narrative paragraphs per section
    from .narrative_writer import write_narrative
    person_for_writer = dict(person)

    # Ordered list of sections with titles + content + narrative
    ordered: List[Dict] = []
    for spec in SECTION_TITLES:
        content = sections.get(spec["key"])
        if content is None:
            continue
        narrative = ""
        if isinstance(content, dict):
            narrative = write_narrative(spec["key"], content, engines, person_for_writer)
        ordered.append({
            "no":         spec["no"],
            "key":        spec["key"],
            "title_hi":   spec["title_hi"],
            "title_en":   spec["title_en"],
            "narrative":  narrative,
            "content":    content,
        })

    return {
        "cover":           cover,
        "front_quality":   front_quality or {},
        "sections_count":  len(ordered),
        "sections":        ordered,
        "footer_disclaimer": (
            "Yeh report educational aur self-awareness ke liye hai. "
            "Hiring, medical, ya legal nirnay ke liye use mat karo. "
            "Computer-vision aur statistical pattern matching par based hai. "
            "— Cosmic Lens · Face Intelligence v1"
        ),
        "report_template_version": "21_section_v1",
    }
