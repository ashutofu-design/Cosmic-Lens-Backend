"""Aspect + Antardasha (TB2b) coverage for AstroVastu engines."""
from astrovastu_chart_vastu import aspects_on_bhava, direction_grid_stress_for_direction
from astrovastu_dasha_layer import dasha_activation_check, tie_breaker_dasha_notes
from astrovastu_engine import apply_tie_breakers, build_kundli_context
from astrovastu_pro_engine import dasha_activation_check as pro_dasha_check


def test_saturn_aspects_fourth_bhava_from_cancer_lagna():
    planets = [
        {"name": "Saturn", "sign": "Libra", "house": 4, "longitude": 190.0},
        {"name": "Moon", "sign": "Cancer", "house": 1, "longitude": 95.0},
    ]
    # Cancer Lagna → 4th house = Libra; Saturn in Libra aspects its own sign (7th aspect)
    hits = aspects_on_bhava("Cancer", 4, planets)
    assert "Saturn" in hits


def test_direction_grid_flags_malefic_on_linked_bhava():
    planets = [
        {"name": "Mars", "sign": "Cancer", "house": 4, "longitude": 100.0},
    ]
    notes = direction_grid_stress_for_direction("Libra", "South-East", planets)
    assert any(n.get("aspector") == "Mars" for n in notes)


def test_tb2b_antardasha_reinforces_direction():
    ctx = build_kundli_context({
        "ascendant": "Virgo",
        "planets": [],
        "currentDasha": {"maha": "Saturn", "antar": "Mars"},
    })
    tb = apply_tie_breakers("kitchen", "South", ctx)
    assert "TB2b" in tb.get("applied_tie_breakers", [])
    notes = tie_breaker_dasha_notes(ctx, "South")
    assert any("TB2b" in n for n in notes)


def test_dasha_activation_merges_md_and_ad():
    ctx = build_kundli_context({
        "ascendant": "Libra",
        "planets": [
            {"name": "Mars", "sign": "Cancer", "house": 4, "longitude": 100.0},
        ],
        "currentDasha": {"maha": "Venus", "antar": "Mars"},
    })
    act = dasha_activation_check(ctx)
    assert act["lords"]["maha"] == "Venus"
    assert act["lords"]["antar"] == "Mars"
    assert pro_dasha_check(ctx)["active"] is True
