"""Part B narrative helpers (no OpenAI call)."""
from astrovastu_pro_narrative import (
    _build_prompts,
    _compact_facts,
    _fingerprint,
    _normalize_lang,
    generate_pro_narrative,
)


def _sample_report():
    return {
        "overall": {"score": 62, "grade": "C", "counts": {"ideal": 1, "acceptable": 2, "adjustment_needed": 2, "avoid": 1}},
        "kundli_summary": {"lagna": "Virgo", "mahadasha": "Saturn", "sade_sati": False},
        "priority_actions": [
            {
                "room_type": "kitchen",
                "direction": "NW",
                "verdict": "Avoid",
                "ideal_directions_short": "SE",
                "action_label_en": "Relocate or remedy",
                "why": "Kitchen in NW conflicts with fire zone.",
            }
        ],
        "rooms": [
            {
                "room_type": "kitchen",
                "direction": "NW",
                "verdict": "Avoid",
                "ideal_directions_short": "SE",
                "action_label_en": "Relocate or remedy",
            }
        ],
        "executive_fixes": [{"en": "Shift kitchen toward SE if possible."}],
    }


def test_normalize_lang():
    assert _normalize_lang("hn") == "hinglish"
    assert _normalize_lang("hi") == "hinglish"
    assert _normalize_lang("en") == "en"


def test_fingerprint_stable():
    r = _sample_report()
    a = _fingerprint(r, "en", "gpt-4o-mini")
    b = _fingerprint(r, "en", "gpt-4o-mini")
    assert a == b
    assert a.startswith("avp_narr_")


def test_compact_facts_contains_rooms():
    text = _compact_facts(_sample_report())
    assert "kitchen" in text
    assert "NW" in text
    assert "SE" in text


def test_generate_off_without_openai(monkeypatch):
    monkeypatch.setenv("ASTROVASTU_PRO_NARRATIVE", "0")
    out = generate_pro_narrative(_sample_report(), lang="en")
    assert out["_meta"]["ok"] is False
    assert out["_meta"]["reason"] == "narrative_off"


def test_light_prompt_shorter():
    _, user_full = _build_prompts(_compact_facts(_sample_report()), "en", light=False)
    _, user_light = _build_prompts(_compact_facts(_sample_report()), "en", light=True)
    assert "SHORT" in user_light
    assert "2-3 short paragraphs" in user_full
