"""Chart-personalized room ideals (AstroVastu blend)."""
from astrovastu_astro_rules import get_effective_room_rule
from astrovastu_pro_engine import analyze_floor_plan, analyze_room, build_kundli_context
from astrovastu_pro_response import build_pro_response


def test_effective_room_rule_with_lagna_does_not_crash():
    """Regression: lagna must be read before bhava-lord block (was UnboundLocalError)."""
    ctx = build_kundli_context({
        "ascendant": "Leo",
        "planets": [{"name": "Sun", "house": 1, "sign": "Leo"}],
        "currentDasha": {"maha": "Jupiter"},
    })
    rule = get_effective_room_rule("kitchen", ctx)
    assert isinstance(rule.get("ideal"), list)


def test_full_pro_scan_multi_room_no_engine_failure():
    ctx = build_kundli_context({
        "ascendant": "Cancer",
        "moonSign": "Cancer",
        "planets": [
            {"name": "Moon", "house": 1, "sign": "Cancer"},
            {"name": "Mars", "house": 10, "sign": "Taurus"},
        ],
        "currentDasha": {"maha": "Moon"},
    })
    rooms = [
        {"room_type": "kitchen", "direction": "SE"},
        {"room_type": "bedroom", "direction": "SW"},
        {"room_type": "living", "direction": "N"},
        {"room_type": "bathroom", "direction": "NW"},
        {"room_type": "main_door", "direction": "E"},
    ]
    scan = analyze_floor_plan(rooms, ctx)
    report = build_pro_response(scan, plan="pro", extras={"floor_plan": rooms})
    assert report["overall"]["score"] >= 0
    assert len(report["rooms"]) == 5


def test_mars_mahadasha_boosts_kitchen_south():
    ctx = build_kundli_context({
        "ascendant": "Virgo",
        "planets": [],
        "currentDasha": {"maha": "Mars"},
    })
    rule = get_effective_room_rule("kitchen", ctx)
    ideals = rule.get("ideal") or []
    assert "South" in ideals or "South-East" in ideals
    assert rule.get("astro_personalized") is True
    assert "Mars" in (rule.get("astro_note_en") or "")


def test_different_mahadasha_changes_kitchen_ideal_order():
    ctx_mars = build_kundli_context({"ascendant": "Virgo", "currentDasha": {"maha": "Mars"}})
    ctx_venus = build_kundli_context({"ascendant": "Virgo", "currentDasha": {"maha": "Venus"}})
    r_mars = get_effective_room_rule("kitchen", ctx_mars)
    r_venus = get_effective_room_rule("kitchen", ctx_venus)
    assert r_mars.get("ideal") != r_venus.get("ideal") or r_mars.get("astro_note_en") != r_venus.get("astro_note_en")


def test_weak_mars_kitchen_does_not_idealize_south():
    ctx = build_kundli_context({
        "ascendant": "Virgo",
        "planets": [
            {"name": "Mars", "sign": "Cancer", "house": 6, "longitude": 100.0},
            {"name": "Sun", "sign": "Aries", "house": 10, "longitude": 15.0},
        ],
        "currentDasha": {"maha": "Mars"},
    })
    if "Mars" not in ctx.get("weak_planets", []):
        ctx["weak_planets"] = list(ctx.get("weak_planets") or []) + ["Mars"]
    rule = get_effective_room_rule("kitchen", ctx)
    assert "South-East" in (rule.get("ideal") or [])
    assert "South" not in (rule.get("ideal") or [])
    assert any("South-East" in n or "Agni" in n for n in (rule.get("astro_note_en") or "").split(". "))


def test_bhava_note_uses_placement_sign_not_only_house_sign():
    """Sagittarius 4th = Pisces lord Jupiter; Jupiter in Aries must say 'placed in Aries'."""
    ctx = build_kundli_context({
        "ascendant": "Sagittarius",
        "planets": [
            {"name": "Jupiter", "sign": "Aries", "house": 5, "longitude": 1.0},
        ],
        "currentDasha": {"maha": "Jupiter"},
    })
    rule = get_effective_room_rule("bedroom", ctx)
    note = (rule.get("astro_note_en") or "").lower()
    assert "placed in aries" in note
    assert "jupiter in pisces" not in note


def test_bedroom_mahadasha_jupiter_does_not_add_ne_to_ideal():
    ctx = build_kundli_context({
        "ascendant": "Sagittarius",
        "planets": [{"name": "Jupiter", "sign": "Aries", "house": 5}],
        "currentDasha": {"maha": "Jupiter"},
    })
    rule = get_effective_room_rule("bedroom", ctx)
    assert "North-East" not in (rule.get("ideal") or [])


def test_analyze_room_exposes_astro_fields():
    ctx = build_kundli_context({"ascendant": "Libra", "currentDasha": {"maha": "Jupiter"}})
    r = analyze_room({"room_type": "pooja", "direction": "NE"}, ctx)
    assert "placement" in r
    assert r.get("astro_personalized") in (True, False)
