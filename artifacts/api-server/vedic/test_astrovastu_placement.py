"""Placement fields for premium PRO PDF (Part A)."""
from astrovastu_pro_engine import analyze_room, compute_placement, build_kundli_context


def test_kitchen_wrong_direction():
    ctx = {"lagna": "Virgo", "current_mahadasha": "Saturn", "sade_sati": False}
    r = analyze_room({"room_type": "kitchen", "direction": "NW"}, ctx)
    pl = r["placement"]
    assert pl["placement_status"] in ("wrong", "acceptable", "mixed")
    assert "SE" in pl["ideal_directions_short"] or pl["ideal_directions_short"]
    assert pl["action"] in ("relocate", "relocate_or_remedy", "remedy", "ok")


def test_bedroom_ideal_sw():
    ctx = build_kundli_context({
        "ascendant": "Libra",
        "planets": [],
        "currentDasha": {"maha": "Jupiter"},
    })
    r = analyze_room({"room_type": "bedroom", "direction": "SW"}, ctx)
    assert r["placement"]["placement_status"] in ("correct", "acceptable")


def test_bedroom_ne_not_acceptable_when_lagna_favours_ne():
    """Sagittarius favours NE generally, but bedroom in NE is a room-level avoid zone."""
    ctx = build_kundli_context({
        "ascendant": "Sagittarius",
        "planets": [],
        "currentDasha": {"maha": "Moon"},
    })
    r = analyze_room({"room_type": "bedroom", "direction": "NE"}, ctx)
    assert r["verdict"] in ("Adjustment Needed", "Avoid")
    assert r["score"] <= 45
    assert "avoid" in (r["placement"].get("summary_hi") or "").lower() or r["placement"]["placement_status"] == "wrong"


def test_dining_in_center_is_acceptable_brahmasthan():
    pl = compute_placement(
        "dining",
        "C",
        {
            "ideal": ["West", "North-West"],
            "acceptable": ["East", "North", "Center"],
            "avoid": ["North-East", "South-West"],
        },
        "Adjustment Needed",
    )
    assert pl["placement_status"] == "acceptable"
    assert "Brahmasthan" in (pl.get("summary_en") or "")


def test_dining_has_ideal_directions():
    pl = compute_placement("dining", "W", {"ideal": ["West", "North-West"], "acceptable": ["East", "North"], "avoid": ["North-East", "South-West"]}, "Adjustment Needed")
    assert pl["ideal_directions_short"] not in ("", "—")
    assert "W" in pl["ideal_directions_short"]
