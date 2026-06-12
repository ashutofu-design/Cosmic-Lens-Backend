"""Unit tests for orb penalty scaling (no kundli required)."""
from vedic.love_reality.scoring_core import (
    ORB_SIGN_ONLY_WEIGHT,
    ORB_TIGHT_DEG,
    angular_distance_deg,
    orb_penalty_multiplier,
    scaled_penalty,
)


def test_angular_distance_wraps():
    assert angular_distance_deg(359.0, 1.0) == 2.0
    assert angular_distance_deg(10.0, 350.0) == 20.0


def test_orb_multiplier_tight_full():
    assert orb_penalty_multiplier(ORB_TIGHT_DEG) == 1.0
    assert orb_penalty_multiplier(3.0) == 1.0


def test_orb_multiplier_wide_half():
    assert orb_penalty_multiplier(ORB_TIGHT_DEG + 0.1) == ORB_SIGN_ONLY_WEIGHT
    assert orb_penalty_multiplier(25.0) == ORB_SIGN_ONLY_WEIGHT


def test_orb_multiplier_sign_only():
    assert orb_penalty_multiplier(None, sign_only=True) == ORB_SIGN_ONLY_WEIGHT


def test_orb_multiplier_missing_degrees_defaults_full():
    assert orb_penalty_multiplier(None) == 1.0


def test_scaled_penalty_rounds():
    assert scaled_penalty(-9.0, 0.5) == -4.5
    assert scaled_penalty(-8.0, 1.0) == -8.0
