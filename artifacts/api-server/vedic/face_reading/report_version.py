"""
Cache invalidation versions — bump to invalidate stale artifacts only.

- NARRATION_VERSION / INSIGHTS_VERSION: AI prompt or bundle schema change
- PDF_RENDER_VERSION: ReportLab layout change (rerender only, no AI)
"""
from __future__ import annotations

import os

# Bump when Pass A/B prompts, bundle, or 12-block mapping changes
NARRATION_VERSION = os.environ.get("FACE_NARRATION_VERSION", "face-v8-artifact")
INSIGHTS_VERSION = os.environ.get("FACE_INSIGHTS_VERSION", NARRATION_VERSION)

# Bump when pdf_report.py layout changes — invalidates L4 PDF only
PDF_RENDER_VERSION = os.environ.get("FACE_PDF_RENDER_VERSION", "pdf-12block-v1")

# Legacy alias used by disk narration_cache keys
PROMPT_VERSION = NARRATION_VERSION


def narration_cache_valid(stored: str | None) -> bool:
    return (stored or "").strip() == NARRATION_VERSION


def insights_cache_valid(stored: str | None) -> bool:
    return (stored or "").strip() == INSIGHTS_VERSION


def pdf_render_cache_valid(stored: str | None) -> bool:
    return (stored or "").strip() == PDF_RENDER_VERSION
