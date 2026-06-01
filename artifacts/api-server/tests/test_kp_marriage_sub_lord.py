"""KP marriage Step 4 — Sub-Lord (sb_houses) must deliver; NL alone must not approve."""

from event_timing._shared.kp_significator_scan import (
    kp_marriage_cusp_verdict,
    kp_marriage_planet_verdict,
)
from event_timing.marriage.marriage_spec_pipeline import _step4_kp_validate


_KP = {
    "cusps": [{"house": 7, "sb": "Saturn"}],
    "significations": {
        "Mercury": {
            "nl_lord": "Mercury",
            "sb_lord": "Saturn",
            "ss_lord": "Mars",
            "pl": [6, 7, 9, 10],
            "sl": [6, 7, 9, 10],
            "sb_houses": [1, 6, 12],
            "ss_houses": [4],
        },
        "Moon": {
            "nl_lord": "Ketu",
            "sb_lord": "Venus",
            "pl": [7],
            "sl": [2, 7, 11],
            "sb_houses": [2, 7, 11],
            "ss_houses": [5],
        },
        "Mars": {
            "nl_lord": "Saturn",
            "sb_lord": "Saturn",
            "pl": [1],
            "sl": [2, 7, 11],
            "sb_houses": [4, 8],
            "ss_houses": [],
        },
        "Saturn": {
            "nl_lord": "Moon",
            "sb_lord": "Rahu",
            "pl": [2, 4],
            "sl": [7],
            "sb_houses": [2, 4],
            "ss_houses": [],
        },
    },
}


def test_nl_seven_does_not_auto_approve_mercury():
    v = kp_marriage_planet_verdict(_KP, "Mercury")
    assert 7 in v["houses_nl"]
    assert v["verdict"] == "DENIES"
    assert not v["kp_valid"]
    assert v["promise_hits"] == []


def test_sb_clean_promise_confirms_moon():
    v = kp_marriage_planet_verdict(_KP, "Moon")
    assert v["verdict"] == "CONFIRMS"
    assert v["kp_valid"]
    assert set(v["promise_hits"]) == {2, 7, 11}


def test_sb_only_negation_denies_mars():
    v = kp_marriage_planet_verdict(_KP, "Mars")
    assert v["verdict"] == "DENIES"
    assert 7 in v["houses_nl"]


def test_csl_uses_pl_not_union():
    c = kp_marriage_cusp_verdict(_KP, 7)
    assert c["csl_planet"] == "Saturn"
    assert c["verdict"] == "CONFIRMS"
    assert 2 in c["promise_hits"]


def test_step4_no_points_when_sb_denies_even_7l():
    merged = {
        "Mercury": {"natal_points": 14},
        "Moon": {"natal_points": 4},
    }
    details, summary = _step4_kp_validate(_KP, merged, "Mercury", "Mercury")
    assert details["Mercury"]["kp_valid"] is True
    assert details["Mercury"]["kp_points"] == 0
    assert details["Mercury"]["verdict"] == "DENIES"
    assert details["Moon"]["kp_points"] > 6
    assert details["Moon"]["verdict"] == "CONFIRMS"
    assert "Moon" in summary["valid_planets"]
    assert "Mercury" not in summary["valid_planets"]


def test_step4_weighted_kp_scores_7h_more_than_2h():
    kp = {
        "cusps": [{"house": 7, "sb": "Moon"}],
        "significations": {
            "Moon": {"pl": [7], "sl": [], "sb_houses": [7]},
            "Saturn": {"pl": [2], "sl": [], "sb_houses": [2]},
        },
    }
    merged = {"Moon": {"natal_points": 5}, "Saturn": {"natal_points": 5}}

    details, _summary = _step4_kp_validate(kp, merged, "Venus", None)

    assert details["Moon"]["kp_points"] > details["Saturn"]["kp_points"]
    assert any("SB promise 7H" in n for n in details["Moon"]["kp_score_notes"])


def test_step4_partial_keeps_points_but_penalizes_negation():
    kp = {
        "cusps": [{"house": 7, "sb": "Moon"}],
        "significations": {
            "Moon": {"pl": [7], "sl": [], "sb_houses": [7]},
            "Mars": {"pl": [7], "sl": [7], "sb_houses": [7, 8, 12]},
        },
    }
    merged = {"Moon": {"natal_points": 5}, "Mars": {"natal_points": 12}}

    details, _summary = _step4_kp_validate(kp, merged, "Venus", None)

    assert details["Mars"]["verdict"] == "PARTIAL"
    assert details["Mars"]["kp_points"] > 0
    assert details["Mars"]["kp_points"] < details["Moon"]["kp_points"]


def test_step4_kp_unavailable_is_unknown_not_supported():
    merged = {"Venus": {"natal_points": 10}}

    details, summary = _step4_kp_validate({}, merged, "Venus", None)

    assert details["Venus"]["kp_valid"] is True
    assert details["Venus"]["kp_points"] == 0
    assert summary["marriage_supported"] is False
    assert summary["support_confidence"] == "unknown"
