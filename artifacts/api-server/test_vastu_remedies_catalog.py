"""Catalog size + lookup merge smoke tests."""
from remedies_db import lookup_remedies, merge_remedies
from vastu_remedies_catalog import catalog_stats, expand_catalog


def test_catalog_has_hundreds_of_picks():
    st = catalog_stats()
    assert st["templates"] >= 80
    assert st["total_picks"] >= 500


def test_tape_remedy_in_toilet_avoid_pool():
    hits = expand_catalog("toilet", "Avoid")
    actions = {h["action"] for h in hits}
    assert "red_tape_threshold" in actions
    assert "rock_salt_bowl" in actions


def test_lookup_merge_caps_to_three_on_screen():
    kundli = [
        {
            "action": "yantra",
            "english": "Kundli yantra",
            "hindi": "Kundli yantra",
            "priority": 1,
        }
    ]
    merged = merge_remedies(kundli, "kitchen", "Avoid", max_total=3, max_db_classical=2)
    assert len(merged) <= 3
    assert merged[0]["action"] == "yantra"


def test_basement_avoid_has_dehumidify():
    actions = {r["action"] for r in lookup_remedies("basement", "Avoid")}
    assert "basement_dehumidify" in actions
