"""
Narrator — assembles Face Intelligence report for PDF.

Default layout: 12 dense blocks (v1). Legacy 21-section layout via FACE_REPORT_LAYOUT=21.

Artifact pipeline uses build_report_skeleton() + enrich_report_narration() separately
so L3 cache never re-enters assemble_report().
"""
from __future__ import annotations

from typing import Dict, List, Optional


# Legacy 21-section template (FACE_REPORT_LAYOUT=21)
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


def _normalize_lang(language: str) -> str:
    _lang = (language or "hinglish").strip().lower()
    if _lang in ("english", "eng"):
        return "en"
    if _lang in ("hindi", "hin"):
        return "hi"
    if _lang in ("hg", "hinglish"):
        return "hinglish"
    if _lang not in ("en", "hi", "hinglish"):
        return "hinglish"
    return _lang


def build_report_skeleton(
    sections: Dict,
    engines: Dict,
    person: Dict | None = None,
    front_quality: Dict | None = None,
    front_image_bytes: bytes | None = None,
    front_points_norm: list | None = None,
    language: str = "hinglish",
) -> Dict:
    """Template-only report structure — no OpenAI."""
    from .face_report_blocks import (
        REPORT_TEMPLATE_VERSION,
        appendix_sections,
        build_ordered_blocks,
        use_12_block_layout,
    )

    person = person or {}
    cover = {
        "name":             person.get("name") or "Insan",
        "gender":           person.get("gender") or "U",
        "age":              person.get("age"),
        "report_title":     "Face Intelligence Report",
        "report_subtitle":  "Tumhare Chehre Mein Likhi Tumhari Kahaani",
        "archetype":        (engines.get("personality") or {}).get("archetype", {}).get("name", "Balanced Soul"),
        "dominant_element": (lambda _e: {
            "agni": "Fire", "jal": "Water", "vayu": "Air",
            "akash": "Space", "prithvi": "Earth",
        }.get(((_e or "")).strip().lower(), (_e or "Balanced").strip().title()))(
            (engines.get("samudrika") or {}).get("element_profile", {}).get("dominant_element", "Balanced")
        ),
        "face_shape":       (engines.get("anthropometry") or {}).get("face_shape_7", {}).get("class", "balanced"),
        "complexion":       (engines.get("samudrika") or {}).get("complexion", ""),
        "perceived_age":    (engines.get("first_impression") or {}).get("perceived_age", {}).get("value"),
    }

    use_12 = use_12_block_layout()
    if use_12:
        ordered = build_ordered_blocks(sections, engines, person)
        template_version = REPORT_TEMPLATE_VERSION
    else:
        from .narrative_writer import write_narrative
        ordered = []
        for spec in SECTION_TITLES:
            content = sections.get(spec["key"])
            if content is None:
                continue
            narrative = ""
            if isinstance(content, dict):
                narrative = write_narrative(spec["key"], content, engines, person)
            ordered.append({
                "no": spec["no"],
                "key": spec["key"],
                "title_hi": spec["title_hi"],
                "title_en": spec["title_en"],
                "narrative": narrative,
                "content": content,
            })
        template_version = "21_section_v1"

    try:
        from .report_intro import build_hook, build_tldr, build_final_truth_v2
        _hook = build_hook(sections, engines, person)
        _tldr = build_tldr(sections, engines)
        _ft2 = build_final_truth_v2(sections, engines, _tldr)
    except Exception:
        _hook, _tldr, _ft2 = {}, {}, {}

    appendix = appendix_sections(sections) if use_12 else []

    return {
        "cover":             cover,
        "hook":              _hook,
        "tldr":              _tldr,
        "final_truth_v2":    _ft2,
        "front_quality":     front_quality or {},
        "front_image_bytes": front_image_bytes,
        "front_points_norm": front_points_norm,
        "engines":           engines,
        "sections_count":    len(ordered),
        "sections":          ordered,
        "appendix_sections": appendix,
        "synthesis":         sections.get("synthesis") or {},
        "_language":         _normalize_lang(language),
        "_ai_narration":     False,
        "footer_disclaimer": (
            "Yeh report educational aur self-awareness ke liye hai. "
            "Hiring, medical, ya legal nirnay ke liye use mat karo. "
            "Computer-vision aur statistical pattern matching par based hai. "
            "— Cosmic Lens · Face Intelligence v2"
        ),
        "report_template_version": template_version,
    }


def enrich_report_narration(
    report: Dict,
    *,
    sections: Dict,
    engines: Dict,
    person: Dict,
    lang: str,
    session_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    user_id: int = 0,
    user_plan: Optional[str] = None,
    force_template: bool = False,
) -> bool:
    """Budgeted AI layer — never called when L3 narration cache hits."""
    from .face_report_blocks import use_12_block_layout
    from .token_budget import AIMode, resolve_ai_mode

    _lang = _normalize_lang(lang)
    ordered = report.get("sections") or []
    _hook = report.get("hook") or {}
    _tldr = report.get("tldr") or {}

    snap = resolve_ai_mode(
        user_id,
        analysis_id=analysis_id,
        lang=_lang,
        plan=user_plan,
        force_template=force_template,
    )
    report["_ai_mode"] = snap.mode.value
    report["_budget_reason"] = snap.reason

    if snap.mode == AIMode.TEMPLATE_ONLY:
        return False

    _ai_applied = False
    try:
        if use_12_block_layout():
            from .face_ai_orchestrator import enrich_12_blocks, use_two_pass, ai_enabled as orch_ai
            if orch_ai() and use_two_pass():
                _ai_applied = enrich_12_blocks(
                    ordered,
                    engines=engines,
                    legacy_sections=sections,
                    person=person,
                    hook=_hook,
                    tldr=_tldr,
                    lang=_lang,
                    session_id=session_id,
                    analysis_id=analysis_id,
                    user_id=user_id,
                    ai_mode=snap.mode,
                )
            else:
                from .ai_narrator import ai_enabled, enrich_face_narratives
                if ai_enabled() and snap.mode != AIMode.TEMPLATE_ONLY:
                    _ai_applied = enrich_face_narratives(
                        ordered,
                        engines=engines,
                        person=person,
                        hook=_hook,
                        tldr=_tldr,
                        lang=_lang,
                        session_id=session_id,
                        analysis_id=analysis_id,
                        legacy_sections=sections,
                    )
        else:
            from .ai_narrator import ai_enabled, enrich_face_narratives
            if ai_enabled():
                _ai_applied = enrich_face_narratives(
                    ordered,
                    engines=engines,
                    person=person,
                    hook=_hook,
                    tldr=_tldr,
                    lang=_lang,
                    session_id=session_id,
                    analysis_id=analysis_id,
                    legacy_sections=sections,
                )
    except Exception as _ai_exc:
        print(f"[narrator] enrich skipped: {_ai_exc}")

    try:
        from .consistency_layer import clean_internal_labels
        for sec in ordered:
            narr = sec.get("narrative")
            if isinstance(narr, str) and narr.strip():
                sec["narrative"] = clean_internal_labels(narr)
        for block in (_hook, _tldr):
            if isinstance(block, dict):
                for field, val in list(block.items()):
                    if isinstance(val, str) and val.strip():
                        block[field] = clean_internal_labels(val)
        ft2 = report.get("final_truth_v2")
        if isinstance(ft2, dict):
            for field, val in list(ft2.items()):
                if isinstance(val, str) and val.strip():
                    ft2[field] = clean_internal_labels(val)
    except Exception:
        pass

    report["_ai_narration"] = _ai_applied
    report["hook"] = _hook
    report["tldr"] = _tldr

    if not _ai_applied and snap.mode != AIMode.TEMPLATE_ONLY:
        try:
            from .translator import translate_report
            translate_report(report, lang)
        except Exception:
            pass
    return _ai_applied


def assemble_report(
    sections: Dict,
    engines: Dict,
    person: Dict | None = None,
    front_quality: Dict | None = None,
    front_image_bytes: bytes | None = None,
    front_points_norm: list | None = None,
    language: str = "hinglish",
    session_id: str | None = None,
    analysis_id: str | None = None,
    *,
    skip_ai: bool = False,
    user_id: int = 0,
    user_plan: Optional[str] = None,
) -> Dict:
    """
    Full assemble (skeleton + AI). Prefer artifact_pipeline for PDF paths.
    When skip_ai=True, only templates (render-only / L3 replay).
    """
    person = person or {}
    report = build_report_skeleton(
        sections,
        engines,
        person=person,
        front_quality=front_quality,
        front_image_bytes=front_image_bytes,
        front_points_norm=front_points_norm,
        language=language,
    )
    if not skip_ai:
        enrich_report_narration(
            report,
            sections=sections,
            engines=engines,
            person=person,
            lang=language,
            session_id=session_id,
            analysis_id=analysis_id,
            user_id=user_id,
            user_plan=user_plan,
        )
    return report
