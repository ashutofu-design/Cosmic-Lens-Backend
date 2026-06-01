"""
12-block Face Intelligence report layout.

Engines still produce legacy section_* keys at analyze time; narrator/PDF
map them into 12 denser consumer blocks. Fewer narrative slots, less repetition.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Toggle: default 12-block layout for new reports
def use_12_block_layout() -> bool:
    import os
    return (os.environ.get("FACE_REPORT_LAYOUT") or "12_v1").strip().lower() not in (
        "21", "legacy", "21_section", "off", "0",
    )


def report_layout_meta() -> Dict[str, Any]:
    """API/PDF metadata for analyze + dedup responses."""
    if use_12_block_layout():
        return {
            "report_template_version": REPORT_TEMPLATE_VERSION,
            "sections_ready": len(REPORT_BLOCKS),
            "sections_total": len(REPORT_BLOCKS),
            "narrative_slots": len(REPORT_BLOCKS),
            "pass_b_slots": len(PASS_B_BLOCKS) - 3,
        }
    return {
        "report_template_version": "21_section_v1",
        "sections_ready": 22,
        "sections_total": 22,
        "narrative_slots": 21,
        "pass_b_slots": 0,
    }


REPORT_TEMPLATE_VERSION = "12_block_v1"

# ── 12 premium blocks (ordered) ─────────────────────────────────────────────
REPORT_BLOCKS: List[Dict[str, str]] = [
    {
        "key": "block_01_screen",
        "no": "01",
        "title_hi": "Ek Nazar Mein Tumhara Pattern",
        "title_en": "Your Pattern at a Glance",
        "goal": "Core pattern + how others read you in the first 10 seconds",
    },
    {
        "key": "block_02_inner_drive",
        "no": "02",
        "title_hi": "Andar Ki Drive",
        "title_en": "Inner Drive",
        "goal": "Motivation and what actually energizes you",
    },
    {
        "key": "block_03_emotional_wiring",
        "no": "03",
        "title_hi": "Emotional Wiring",
        "title_en": "Emotional Wiring",
        "goal": "Mask vs real self + how feelings move under the surface",
    },
    {
        "key": "block_04_strengths_stress",
        "no": "04",
        "title_hi": "Strengths Under Pressure",
        "title_en": "Strengths Under Stress",
        "goal": "What holds up when life gets heavy",
    },
    {
        "key": "block_05_blind_spots",
        "no": "05",
        "title_hi": "Blind Spots (Gentle)",
        "title_en": "Blind Spots",
        "goal": "Non-judgmental friction patterns — no diagnosis",
    },
    {
        "key": "block_06_love_attachment",
        "no": "06",
        "title_hi": "Love & Attachment",
        "title_en": "Love & Attachment",
        "goal": "Bonding style, repair, intimacy friction",
    },
    {
        "key": "block_07_work_money",
        "no": "07",
        "title_hi": "Work & Money Rhythm",
        "title_en": "Work & Money",
        "goal": "Career pace, risk, money habits",
    },
    {
        "key": "block_08_communication",
        "no": "08",
        "title_hi": "Communication Blueprint",
        "title_en": "Communication",
        "goal": "How you register in conversation — clarity vs warmth",
    },
    {
        "key": "block_09_contradictions",
        "no": "09",
        "title_hi": "Tumhari Contradictions",
        "title_en": "Your Contradictions",
        "goal": "Two true patterns that coexist — builds trust",
    },
    {
        "key": "block_10_experiments",
        "no": "10",
        "title_hi": "30-Day Experiments",
        "title_en": "30-Day Experiments",
        "goal": "Five practical micro-experiments",
    },
    {
        "key": "block_11_confidence_limits",
        "no": "11",
        "title_hi": "Confidence & Limits",
        "title_en": "Confidence & Limits",
        "goal": "Signal strength + what this report cannot claim",
    },
    {
        "key": "block_12_closing_truth",
        "no": "12",
        "title_hi": "Closing Truth",
        "title_en": "Closing Truth",
        "goal": "One direction + grounded closing — no prophecy",
    },
]

# Legacy engine sections merged into each block (no duplicate PDF slots)
LEGACY_SOURCES: Dict[str, List[str]] = {
    "block_01_screen": ["section_1_power_summary", "section_4_first_impression", "section_7_personality_synthesis"],
    "block_02_inner_drive": ["section_2_psychological_type", "section_13_archetype"],
    "block_03_emotional_wiring": ["section_3_mask_vs_real", "section_5_core_foundation"],
    "block_04_strengths_stress": ["section_7_personality_synthesis", "section_11_attraction_charisma"],
    "block_05_blind_spots": ["section_10_red_flags"],
    "block_06_love_attachment": ["section_8_love_relationship_dna", "section_20_compatibility"],
    "block_07_work_money": ["section_9_career_money", "section_12_decision_style"],
    "block_08_communication": ["section_4_first_impression", "section_12_decision_style"],
    "block_09_contradictions": ["section_3_mask_vs_real", "section_21_final_truth"],
    "block_10_experiments": ["section_18_action_plan", "section_19_improvement_hacks"],
    "block_11_confidence_limits": ["section_16_health_scan"],
    "block_12_closing_truth": ["section_21_final_truth"],
}

# Word targets — denser than old 21-section report
BLOCK_WORD_TARGETS: Dict[str, int] = {
    "block_01_screen": 165,
    "block_02_inner_drive": 120,
    "block_03_emotional_wiring": 155,
    "block_04_strengths_stress": 115,
    "block_05_blind_spots": 110,
    "block_06_love_attachment": 150,
    "block_07_work_money": 140,
    "block_08_communication": 120,
    "block_09_contradictions": 95,
    "block_10_experiments": 100,
    "block_11_confidence_limits": 75,
    "block_12_closing_truth": 155,
    "faceread.hook_identity": 40,
    "faceread.hook_shock": 38,
    "faceread.tldr": 100,
}

# Pass A: all 12 blocks in one mini call
PASS_A_KEYS: List[str] = [b["key"] for b in REPORT_BLOCKS]

# Pass B: premium gpt-4o prose (subset)
PASS_B_BLOCKS = frozenset({
    "block_01_screen",
    "block_03_emotional_wiring",
    "block_06_love_attachment",
    "block_07_work_money",
    "block_09_contradictions",
    "block_12_closing_truth",
    "faceread.hook_identity",
    "faceread.hook_shock",
    "faceread.tldr",
})

PASS_A_BLOCK_HINTS: Dict[str, str] = {b["key"]: b["goal"] for b in REPORT_BLOCKS}


def _g(d: Any, *path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def synthesize_block_content(
    block_key: str,
    legacy_sections: Dict[str, Any],
    engines: Dict[str, Any],
    person: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge legacy section dicts into one block content payload."""
    merged: Dict[str, Any] = {"block": block_key, "sources": []}
    for sk in LEGACY_SOURCES.get(block_key, []):
        raw = legacy_sections.get(sk)
        if isinstance(raw, dict):
            merged["sources"].append(sk)
            for k, v in raw.items():
                if k.startswith("_"):
                    continue
                if k not in merged:
                    merged[k] = v
    fs = legacy_sections.get("final_scores") or engines.get("final_scores") or {}
    if fs:
        merged["final_scores"] = fs
    return merged


def legacy_template_narrative(
    block_key: str,
    legacy_sections: Dict[str, Any],
    engines: Dict[str, Any],
    person: Dict[str, Any],
    *,
    max_chars: int = 900,
) -> str:
    """Deterministic template prose from legacy writers (pre-AI fallback)."""
    from .narrative_writer import write_narrative

    chunks: List[str] = []
    for sk in LEGACY_SOURCES.get(block_key, []):
        content = legacy_sections.get(sk)
        if not isinstance(content, dict):
            continue
        txt = write_narrative(sk, content, engines, person)
        if txt and txt.strip():
            chunks.append(txt.strip())
    if not chunks:
        return ""
    out = "\n\n".join(chunks[:2])
    if len(out) > max_chars:
        out = out[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return out


def narrative_from_pass_a_insight(block_key: str, insight: Dict[str, Any]) -> str:
    """Turn Pass A JSON into readable prose without a second LLM call."""
    if not insight:
        return ""
    parts: List[str] = []
    one = (insight.get("one_liner") or "").strip()
    if one:
        parts.append(one)
    for b in (insight.get("bullets") or [])[:4]:
        if b and str(b).strip():
            parts.append(f"• {str(b).strip()}")
    obs = (insight.get("observation") or "").strip()
    if obs and obs not in one:
        parts.append(obs)
    impl = (insight.get("implication") or "").strip()
    if impl:
        parts.append(impl)
    return "\n\n".join(parts).strip()


def build_ordered_blocks(
    legacy_sections: Dict[str, Any],
    engines: Dict[str, Any],
    person: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Build 12 ordered block rows for narrator/PDF."""
    person = person or {}
    ordered: List[Dict[str, Any]] = []
    for spec in REPORT_BLOCKS:
        key = spec["key"]
        content = synthesize_block_content(key, legacy_sections, engines, person)
        narrative = legacy_template_narrative(key, legacy_sections, engines, person)
        ordered.append({
            "no": spec["no"],
            "key": key,
            "title_hi": spec["title_hi"],
            "title_en": spec["title_en"],
            "goal": spec["goal"],
            "narrative": narrative,
            "content": content,
        })
    return ordered


def appendix_sections(legacy_sections: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Non-narrative PDF appendix (scores, features table) — not AI slots."""
    out: List[Dict[str, Any]] = []
    bonus = legacy_sections.get("bonus_personality_score")
    if bonus:
        out.append({
            "no": "A",
            "key": "bonus_personality_score",
            "title_hi": "5 Personality Scores",
            "title_en": "Score Grid",
            "narrative": "",
            "content": bonus,
            "appendix": True,
        })
    feat = legacy_sections.get("section_6_feature_analysis")
    if feat:
        out.append({
            "no": "B",
            "key": "section_6_feature_analysis",
            "title_hi": "Feature Table",
            "title_en": "Feature Analysis",
            "narrative": "",
            "content": feat,
            "appendix": True,
        })
    return out
