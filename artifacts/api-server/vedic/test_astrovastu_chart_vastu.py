"""Chart + floor plan = per-user AstroVastu (not universal-only)."""
from astrovastu_chart_vastu import evaluate_chart_stress_hits, enrich_chart_vastu_context
from astrovastu_pro_engine import analyze_room, build_kundli_context


def test_mars_in_4_amplifies_kitchen_se():
    planets = [
        {"name": "Mars", "sign": "Cancer", "house": 4, "longitude": 100.0},
        {"name": "Sun", "sign": "Aries", "house": 10, "longitude": 15.0},
    ]
    hits = evaluate_chart_stress_hits(planets, [])
    assert any("Mars in 4" in (h.get("condition") or "") for h in hits)

    ctx = enrich_chart_vastu_context(
        build_kundli_context({
            "ascendant": "Libra",
            "planets": planets,
            "currentDasha": {"maha": "Venus"},
        }),
        planets,
    )
    r = analyze_room({"room_type": "kitchen", "direction": "SE"}, ctx)
    assert r["chart_stress_layer"].get("applied") is True
    assert "chart" in (r["chart_stress_layer"].get("chart_note_en") or "").lower()


def test_different_lagna_changes_bhava_lord_note():
    p = [{"name": "Sun", "sign": "Leo", "house": 1, "longitude": 120.0}]
    ctx_a = enrich_chart_vastu_context(
        build_kundli_context({"ascendant": "Aries", "planets": p, "currentDasha": {"maha": "Sun"}}),
        p,
    )
    ctx_b = enrich_chart_vastu_context(
        build_kundli_context({"ascendant": "Libra", "planets": p, "currentDasha": {"maha": "Sun"}}),
        p,
    )
    from astrovastu_astro_rules import get_effective_room_rule
    ra = get_effective_room_rule("bedroom", ctx_a)
    rb = get_effective_room_rule("bedroom", ctx_b)
    assert ra.get("astro_note_en") != rb.get("astro_note_en")
