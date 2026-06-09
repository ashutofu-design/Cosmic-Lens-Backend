"""PDF text sanitization for Love Reality."""
from vedic.love_reality.pdf_text_safe import (
    has_devanagari,
    polish_content_lang,
    sanitize_love_reality_pro_premium,
    strip_devanagari,
)


def test_polish_content_lang_hi_stays_hi():
    assert polish_content_lang("hi") == "hi"
    assert polish_content_lang("hn") == "hn"


def test_strip_devanagari_removes_boxes_source_chars():
    raw = "यह loyalty check strong nahi hai — pattern clear hai."
    out = strip_devanagari(raw)
    assert not has_devanagari(out)
    assert "loyalty" in out.lower()


def test_sanitize_hi_preserves_devanagari():
    pro = {
        "verdict": "यह एक परीक्षण वाक्य है जो देवनागरी में लिखा गया है और पर्याप्त लंबा है ताकि sanitize इसे रखे।",
        "chapters": [],
    }
    fixed = sanitize_love_reality_pro_premium(pro, None, lang="hi")
    assert has_devanagari(fixed["verdict"])


def test_sanitize_refills_chapter_from_engine():
    bundle = {
        "loyalty_check": {
            "emotional_summary": "Loyalty is mixed — warmth on surface, breaks under stress.",
            "reasons": ["Moon afflicted — secrecy risk."],
        },
    }
    pro = {
        "chapters": [
            {
                "key": "loyalty",
                "chapter_body": "केवल हिंदी में लिखा गया पूरा अध्याय।",
            },
        ],
    }
    fixed = sanitize_love_reality_pro_premium(pro, bundle, lang="en")
    body = fixed["chapters"][0]["chapter_body"]
    assert not has_devanagari(body)
    assert len(body) > 40
    assert "loyalty" in body.lower() or "mixed" in body.lower()
