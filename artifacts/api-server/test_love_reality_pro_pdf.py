"""Smoke tests for Love Reality Pro PDF (~14-16 pages)."""
import re

from love_reality_pdf import render_love_reality_pro_pdf


def _count_pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf))


def _bundle(p1n="A", p2n="B", score=72):
    return {
        "p1": {"name": p1n, "nakshatra": "Ashwini", "rashi": "Aries"},
        "p2": {"name": p2n, "nakshatra": "Pushya", "rashi": "Cancer"},
        "love_compatibility": {
            "score": score,
            "insight": "A warm pull with honest friction points.",
            "score_ledger": [
                {"label": "Base", "base": 52, "note": "Anchor"},
                {"label": "Sample bonus", "delta": 20, "note": "Test"},
            ],
        },
        "chart_snapshot": {"lines": ["Moon: Aries", "Venus: Taurus house 7"]},
        "narrative_bridge": "Timing split note for tests.",
        "chapter_groundings": {"love_connection": "Engine score 72/100. Test grounding."},
    }


def _pro(score=7.5):
    keys = [
        "love_connection",
        "breakup",
        "loyalty",
        "will_return",
        "future_outcome",
        "red_flags",
    ]
    body = (
        "Chart signals for this theme are active between both partners. "
        "Daily rhythm and repair style shape how this score lands in real life."
    )
    return {
        "hidden_truth": "Something unspoken still binds you — naming it changes the tone.",
        "chapters": [
            {
                "key": k,
                "title": k.replace("_", " ").title(),
                "score_0_10": score,
                "chapter_body": body,
                "full_read": body,
            }
            for k in keys
        ],
        "special": ["Strength one.", "Strength two."],
        "damage": ["Risk one."],
        "practical": ["Practical one."],
        "verdict": "A bond worth honest work — not fantasy, not doom.",
    }


def test_love_reality_pro_pdf_bytes_and_page_band_en():
    payload = _bundle()
    payload["pro_premium"] = _pro()
    pdf = render_love_reality_pro_pdf(payload, lang="en")
    assert pdf.startswith(b"%PDF-")
    pages = _count_pages(pdf)
    assert 15 <= pages <= 24


def test_love_reality_pro_pdf_empty_pro_still_renders():
    payload = _bundle()
    payload["pro_premium"] = {}
    pdf = render_love_reality_pro_pdf(payload, lang="en")
    assert pdf.startswith(b"%PDF-")
    assert _count_pages(pdf) >= 15


def test_love_reality_pro_pdf_hi_render_uses_hn_font_lane():
    """hi content lane stays hi for polish; PDF render maps to hn (Helvetica-safe)."""
    from vedic.love_reality.pdf_locale import (
        love_reality_pdf_render_lang,
        normalize_love_reality_pdf_lang,
    )

    assert normalize_love_reality_pdf_lang("hi") == "hi"
    assert love_reality_pdf_render_lang("hi") == "hn"
    payload = _bundle()
    payload["pro_premium"] = _pro()
    pdf = render_love_reality_pro_pdf(payload, lang="hi")
    assert pdf.startswith(b"%PDF-")
