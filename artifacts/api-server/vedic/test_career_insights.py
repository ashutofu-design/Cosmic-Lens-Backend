"""Career basic/pro insights builder tests."""
from vedic.life_specifics import build_career_basic_insights, build_career_pro_insights


def _deep_sample():
    return {
        "suitable_fields": [
            {"field": "Tech / Software", "score": 92, "driver": "Mercury in 10th house (Virgo)"},
            {"field": "Finance / Banking", "score": 78, "driver": "Mercury in 10th house (Virgo)"},
        ],
        "income_paths": [
            {"label": "Software engineer", "strength": 88},
            {"label": "IT company job", "strength": 82},
        ],
        "job_pct": 62,
        "business_pct": 38,
        "path_verdict": "Job path is stronger for steady growth.",
        "career_inclination": {
            "job_pct": 62,
            "business_pct": 38,
            "career_mode": "Structured Career",
            "confidence": "High",
            "reasoning_summary": ["Mercury in 10th supports analytical work."],
        },
        "peak_growth_period": {"rating": "Very Good", "ends": "2028-05-01"},
        "tenth_lord": {"planet": "Mercury", "sign_10": "Virgo", "strength_pct": 72, "status": "exalted"},
        "tenth_house": {"occupants": "Mercury"},
        "atmakaraka": {"planet": "Mercury", "meaning": "Soul wants intellect."},
        "amatyakaraka": {"planet": "Saturn", "meaning": "Career through discipline."},
        "classical_summary": "D1 10th Virgo — Mercury strong.",
    }


def test_basic_uses_micro_niche_income_paths():
    out = build_career_basic_insights(72, "Good", _deep_sample(), {"maha": "Jupiter"})
    labels = [p["label"] for p in out.get("income_paths") or []]
    assert any("software" in lb.lower() or "it" in lb.lower() for lb in labels)


def test_basic_business_pct_from_deep_not_derived():
    out = build_career_basic_insights(72, "Good", _deep_sample(), {})
    assert out.get("job_pct") == 62
    assert out.get("business_pct") == 38


def test_basic_verdict_when_suitable_fields():
    out = build_career_basic_insights(72, "Good", _deep_sample(), {})
    assert out.get("verdict")
    assert "tech" in out["verdict"].lower() or "analytical" in out["verdict"].lower()


def test_basic_has_hook_and_phase_fields():
    out = build_career_basic_insights(
        72, "Good", _deep_sample(), {},
        score_meta={"score_label": "Strong", "summary": "Good phase.", "score_context": "Chart + dasha"},
    )
    assert out.get("hook")
    assert out.get("current_phase")
    assert out.get("score_label") == "Strong"


def test_pro_block_has_houses_and_dasha():
    planets = [{"name": "Mercury", "sign": "Virgo", "house": 10}]
    pro = build_career_pro_insights(
        planets, 8, _deep_sample(),
        {"reasons": ["Mercury in 10th — career support"], "transit_notes": ["Jupiter transiting 11th"]},
        {"maha": "Jupiter", "antar": "Mercury", "endDate": "2028-05-01"},
    )
    assert pro.get("houses", {}).get("h10")
    assert pro.get("dasha", {}).get("mahadasha") == "Jupiter"
    assert pro.get("suitable_fields")
