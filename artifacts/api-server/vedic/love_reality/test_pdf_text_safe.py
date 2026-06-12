"""PDF text sanitization for Love Reality."""
from vedic.love_reality.pdf_text_safe import (
    has_devanagari,
    love_pro_payload_matches_lang,
    polish_content_lang,
    prose_lane_ok,
    prose_matches_lang,
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


def test_sanitize_hi_short_chapter_not_replaced_with_english_engine():
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
                "chapter_body": "छोटा",
            },
        ],
    }
    fixed = sanitize_love_reality_pro_premium(pro, bundle, lang="hi")
    body = fixed["chapters"][0]["chapter_body"]
    assert has_devanagari(body)
    assert "mixed" not in body.lower()


def test_prose_matches_lang_en_rejects_devanagari():
    english = "Your emotional bond runs deep when trust is steady and communication stays open."
    hindi = "आपका भावनात्मक बंध गहरा है जब विश्वास स्थिर रहता है।"
    assert prose_matches_lang(english, "en")
    assert not prose_matches_lang(hindi, "en")
    assert prose_lane_ok(english, "en")
    assert not prose_lane_ok(hindi, "en")


def test_prose_matches_lang_en_rejects_hinglish():
    hinglish = (
        "Aapke rishte me emotional pull strong hai lekin communication ke beech "
        "tension barhti hai jab dono alag rhythm me chalte hain."
    )
    assert not prose_matches_lang(hinglish, "en")


def test_love_pro_payload_matches_lang_en_rejects_hindi_deep_analysis():
    mixed = {
        "page1": {"relationship_summary": "Your charts show a complex bond with strong pull."},
        "pro_premium": {
            "deep_analysis": [
                {
                    "key": "emotional",
                    "explanation": "आपके चार्ट में गहरा भावनात्मक बंध दिखता है जो समय के साथ परिपक्व होता है।",
                },
            ],
        },
    }
    assert not love_pro_payload_matches_lang(mixed, "en")


def test_love_pro_payload_matches_lang_hi():
    english = {
        "page1": {
            "relationship_summary": "Your charts show a complex bond with strong pull.",
            "verdict": "Use this report as a timing map.",
        },
        "pro_premium": {"verdict": "Complex bond ahead."},
    }
    hindi = {
        "page1": {
            "relationship_summary": "आपके चार्ट में गहरा भावनात्मक बंध दिखता है।",
            "verdict": "इस रिपोर्ट को समय-मानचित्र की तरह पढ़ें।",
        },
        "pro_premium": {"verdict": "आगे का रास्ता स्पष्टता से खुलेगा।"},
    }
    assert not love_pro_payload_matches_lang(english, "hi")
    assert love_pro_payload_matches_lang(hindi, "hi")


def test_sanitize_refills_chapter_from_engine_en():
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
