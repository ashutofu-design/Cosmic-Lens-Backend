"""Marriage Step 6 — strength-weighted dasha scoring."""

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.marriage.marriage_engine_v2 import (  # noqa: E402
    _build_dasha_lord_profiles,
    _step5_5_future_cascade,
    _step5_dasha_activation,
)


def test_step6_strong_ranked_lord_scores_higher_than_weak_lord():
    now = datetime(2030, 1, 1)
    chain = [
        {
            "md": "Venus", "ad": "Moon", "pd": "Moon",
            "start": now + timedelta(days=20),
            "end": now + timedelta(days=80),
        },
        {
            "md": "Venus", "ad": "Mars", "pd": "Mars",
            "start": now + timedelta(days=100),
            "end": now + timedelta(days=160),
        },
    ]
    profiles = _build_dasha_lord_profiles([
        {
            "name": "Moon", "score": 22, "kp_verdict": "CONFIRMS",
            "kp_points": 8, "d9_points": 6, "both_divisions": True,
        },
        {
            "name": "Mars", "score": 9, "kp_verdict": "UNKNOWN",
            "kp_points": 0, "d9_points": 0, "both_divisions": False,
        },
    ])

    cands = _step5_5_future_cascade(
        chain, {"Moon", "Mars"}, now, None, lord_profiles=profiles,
    )

    assert cands[0]["ad"] == "Moon"
    assert cands[0]["score"] > cands[1]["score"]
    assert cands[0]["ad_pd_confluence"]
    assert any("AD+PD confluence" in x for x in cands[0]["dasha_score_detail"])


def test_step6_kp_denied_lord_is_demoted_in_dasha_score():
    now = datetime(2030, 1, 1)
    chain = [
        {
            "md": "Venus", "ad": "Moon", "pd": "Moon",
            "start": now + timedelta(days=20),
            "end": now + timedelta(days=80),
        },
        {
            "md": "Venus", "ad": "Mars", "pd": "Mars",
            "start": now + timedelta(days=100),
            "end": now + timedelta(days=160),
        },
    ]
    profiles = _build_dasha_lord_profiles([
        {"name": "Moon", "score": 14, "kp_verdict": "CONFIRMS"},
        {"name": "Mars", "score": 14, "kp_verdict": "DENIES"},
    ])

    cands = _step5_5_future_cascade(
        chain, {"Moon", "Mars"}, now, None, lord_profiles=profiles,
    )

    moon = next(c for c in cands if c["ad"] == "Moon")
    mars = next(c for c in cands if c["ad"] == "Mars")
    assert moon["score"] > mars["score"]


def test_step6_current_activation_uses_ranked_strength():
    now = datetime(2030, 1, 15)
    chain = [{
        "md": "Venus", "ad": "Moon", "pd": "Moon",
        "start": datetime(2030, 1, 1),
        "end": datetime(2030, 2, 1),
    }]
    profiles = _build_dasha_lord_profiles([
        {
            "name": "Moon", "score": 22, "kp_verdict": "CONFIRMS",
            "d9_points": 6, "both_divisions": True,
        },
    ])

    activation = _step5_dasha_activation(
        chain, {"Moon"}, now, lord_profiles=profiles,
    )

    assert activation["active_score"] > 11
    assert any("x" in x for x in activation["active_lords"])
