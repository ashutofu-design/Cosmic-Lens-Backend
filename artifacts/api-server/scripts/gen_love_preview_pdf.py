#!/usr/bin/env python3
"""
Generate full Love Reality Pro PDF for local preview (ReportLab = production).

Output:
  artifacts/love-reality-report/public/preview-report.pdf
  artifacts/love-reality-report/public/preview-report-meta.json

No OpenAI — fixed sample pro_premium + engine bundle only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_API = Path(__file__).resolve().parents[1]
_REPO = _API.parent / "love-reality-report" / "public"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))


def _count_pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf))


def _rich_pro() -> dict:
    body = (
        "Chart signals for this theme are active between both partners. "
        "Daily rhythm and repair style shape how this score lands in real life. "
        "When stress rises, the pattern repeats unless named within 24 hours."
    )
    keys = [
        "love_connection",
        "breakup",
        "loyalty",
        "will_return",
        "future_outcome",
        "red_flags",
    ]
    return {
        "hidden_truth": "Something unspoken still binds you — naming it changes the tone.",
        "verdict": (
            "Cosmic verdict: This bond is worth conscious effort — not blind hope. "
            "Chemistry is real; sustainability depends on repair speed and dasha-aware timing. "
            "Use this report as a timing map, not a final sentence on the relationship."
        ),
        "practical": [
            "Repair within 24 hours after any fight — chart shows delay stacks resentment",
            "Weekly 20-minute check-in without phones",
            "No major relationship decisions during communication-heavy retrogrades",
            "Name one hidden fear per month — reduces 12th-house pressure",
            "Track dasha dates — avoid ultimatums in down windows",
        ],
        "chapters": [
            {
                "key": k,
                "title": k.replace("_", " ").title(),
                "score_0_10": 7.2,
                "chapter_body": body,
                "full_read": body,
            }
            for k in keys
        ],
        "special": ["Emotional magnetism runs high under calm conditions."],
        "damage": ["Silence beyond 48 hours erodes loyalty scores fastest."],
    }


def sample_preview_payload() -> dict:
    """Fixed payload for local PDF preview — no LLM."""
    return {
        "report_id": "LR-PREVIEW",
        "p1": {"name": "Aarav", "nakshatra": "Ashwini", "rashi": "Aries"},
        "p2": {"name": "Riya", "nakshatra": "Pushya", "rashi": "Cancer"},
        "pro_premium": _rich_pro(),
        "love_compatibility": {
            "score": 72,
            "insight": "Strong mutual pull with uneven emotional pacing.",
            "emotional_summary": (
                "Strong mutual pull with uneven emotional pacing. Attraction is authentic; "
                "friction spikes when silence replaces repair. Next 90 days favor honest conversations."
            ),
            "reasons": [
                "Moon rhythm mismatch — emotional pacing differs between partners.",
                "Venus–Mars axis drives attraction but also jealousy triggers.",
            ],
            "score_ledger": [
                {"label": "Base synastry", "base": 52, "note": "Moon–Venus anchor"},
                {"label": "Dasha alignment", "delta": 12, "note": "Favorable window"},
                {"label": "Repair bonus", "delta": 8, "note": "Communication potential"},
            ],
        },
        "breakup_chances": {
            "score": 58,
            "reasons": ["Mercury stress windows amplify misread signals."],
        },
        "loyalty_check": {"score": 64},
        "will_return": {"score": 41},
        "future_outcome": {"score": 61},
        "narrative_bridge": "Repair within 48 hours — silence beyond that is the highest-risk behavior.",
        "chart_snapshot": {"lines": ["Moon: Aries", "Venus: Taurus house 7"]},
        "chapter_groundings": {"love_connection": "Engine score 72/100."},
    }


def main() -> None:
    from love_reality_pdf import render_love_reality_pro_pdf

    _REPO.mkdir(parents=True, exist_ok=True)
    payload = sample_preview_payload()
    pdf = render_love_reality_pro_pdf(payload, lang="en")
    pdf_path = _REPO / "preview-report.pdf"
    meta_path = _REPO / "preview-report-meta.json"
    pages = _count_pages(pdf)
    pdf_path.write_bytes(pdf)
    meta = {
        "pages": pages,
        "report_id": payload["report_id"],
        "couple": f"{payload['p1']['name']} & {payload['p2']['name']}",
        "description": (
            "Full Love Reality Pro report (~14 sections). "
            "Same ReportLab renderer as production. No LLM — sample data only."
        ),
        "generated_by": "artifacts/api-server/scripts/gen_love_preview_pdf.py",
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"OK: {pages} PDF page(s) -> {pdf_path}")
    print(f"Meta: {meta_path}")


if __name__ == "__main__":
    main()
