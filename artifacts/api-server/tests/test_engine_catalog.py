"""Tests for stable admin engine numbers."""

from ask_engine_catalog import resolve_engine_display


def test_occult_learning_maps_to_spiritual_timing_44():
    disp = resolve_engine_display(
        archetype="occult_learning",
        is_timing=True,
    )
    assert disp.engine_no == 44
    assert disp.slice_id == "spiritual_timing_v1"
    assert "Engine #44" in disp.admin_line
    assert "occult_learning" in disp.admin_line


def test_mr_static_engine_12():
    disp = resolve_engine_display(
        slice_id="mr_engine_v1",
        archetype="partner_nature",
        is_timing=False,
    )
    assert disp.engine_no == 12
    assert "mr_engine_v1" in disp.admin_line


def test_spiritual_static_vs_timing():
    static = resolve_engine_display(slice_id="spiritual_engine_v1", is_timing=False)
    timing = resolve_engine_display(slice_id="spiritual_timing_v1", is_timing=True)
    assert static.engine_no == 14
    assert timing.engine_no == 44
