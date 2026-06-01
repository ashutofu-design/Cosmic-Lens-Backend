"""Post-polish validation for Milan Pro PDF — ban filler, inject chart bridges."""
from __future__ import annotations

import re
from typing import Any

from vedic.compat.premium_chapters import CHAPTER_BODY_KEY, THERAPY_CLICHES
from vedic.compat.milan_chart_facts import (
    PDF_CHAPTER_TO_SCORE_KEY,
    build_chapter_groundings,
    build_narrative_bridge,
)
from vedic.compat.premium_chapters import normalize_pro_pdf_lang

# PDF keys from pro_chapter_rows; polish may emit ch1..ch7
_CH_INDEX_TO_PDF = {v: k for k, v in PDF_CHAPTER_TO_SCORE_KEY.items()}


def _scrub_cliches(text: str) -> str:
    t = text
    for phrase in THERAPY_CLICHES:
        if len(phrase) < 8:
            continue
        t = re.sub(re.escape(phrase), "", t, flags=re.I)
    t = re.sub(r"\bengine\b", "chart", t, flags=re.I)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def _pdf_key_for_chapter(c: dict) -> str | None:
    key = str(c.get("key") or "").strip().lower()
    if key in PDF_CHAPTER_TO_SCORE_KEY:
        return key
    if key in _CH_INDEX_TO_PDF:
        return _CH_INDEX_TO_PDF[key]
    m = re.match(r"ch(\d)", key)
    if m:
        return _CH_INDEX_TO_PDF.get(f"ch{m.group(1)}")
    return None


def apply_milan_premium_validation(
    parsed: dict,
    bundle: dict | None,
    lang: str = "en",
) -> dict:
    lang = normalize_pro_pdf_lang(lang)
    for c in parsed.get("chapters") or []:
        if not isinstance(c, dict):
            continue
        for field in (CHAPTER_BODY_KEY, "full_read", "grounding"):
            if c.get(field):
                c[field] = _scrub_cliches(str(c[field]))
    for field in ("hidden_truth", "verdict"):
        if parsed.get(field):
            parsed[field] = _scrub_cliches(str(parsed[field]))
    for list_key in ("special", "damage", "practical"):
        items = parsed.get(list_key)
        if isinstance(items, list):
            parsed[list_key] = [_scrub_cliches(str(x)) for x in items if x]

    if bundle:
        bridge = bundle.get("narrative_bridge") or build_narrative_bridge(bundle, lang)
        verdict = str(parsed.get("verdict") or "").strip()
        if bridge and bridge[:40].lower() not in verdict.lower():
            parsed["verdict"] = (verdict + "\n\n" + bridge).strip() if verdict else bridge
        groundings = bundle.get("chapter_groundings") or build_chapter_groundings(bundle)
        for c in parsed.get("chapters") or []:
            if not isinstance(c, dict):
                continue
            if str(c.get("grounding") or "").strip():
                continue
            pk = _pdf_key_for_chapter(c)
            if pk and groundings.get(pk):
                c["grounding"] = groundings[pk]
    return parsed
