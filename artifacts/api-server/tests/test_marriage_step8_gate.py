"""Marriage Step 8 — weighted final gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_timing.marriage.marriage_engine_v2 import (  # noqa: E402
    _derive_verdict,
    _risk_severity_score,
)


def test_step8_risk_severity_weights_stronger_flags():
    score, notes = _risk_severity_score([
        "7th cusp sub-lord DENIES marriage promise (KP)",
        "Saturn in 7H (delay-pattern)",
        "Manglik mild (compatibility care needed)",
    ])

    assert score == 9.5
    assert any("DENIES" in n for n in notes)


def test_step8_strong_dasha_kp_and_double_transit_promises():
    verdict, band, gate = _derive_verdict(
        11.0,
        "CONFIRMS",
        [],
        natal_promise=True,
        kp_supported=True,
        has_qualified_window=True,
        final_transit_support=True,
        final_double_transit=True,
        timing_appropriate=True,
    )

    assert verdict == "PROMISED"
    assert band == "STRONG"
    assert gate["gate_score"] > 12


def test_step8_missing_transit_does_not_auto_kill_very_strong_case():
    verdict, band, gate = _derive_verdict(
        14.0,
        "CONFIRMS",
        [],
        natal_promise=True,
        kp_supported=True,
        has_qualified_window=True,
        final_transit_support=False,
        final_double_transit=False,
        timing_appropriate=True,
    )

    assert verdict == "PROMISED"
    assert band in ("MEDIUM", "STRONG")
    assert gate["gate_score"] >= 8


def test_step8_high_risk_caps_promise_to_delayed():
    verdict, band, gate = _derive_verdict(
        13.0,
        "CONFIRMS",
        [
            "Saturn in 7H (delay-pattern)",
            "Rahu in 7H (1-7 axis — unconventional choice / sudden shifts)",
            "Venus debilitated (relationship-dignity weak)",
        ],
        natal_promise=True,
        kp_supported=True,
        has_qualified_window=True,
        final_transit_support=True,
        final_double_transit=False,
        timing_appropriate=True,
    )

    assert verdict == "DELAYED"
    assert band in ("MEDIUM", "WEAK")
    assert gate["risk_score"] >= 6


def test_step8_kp_denies_prevents_promised_claim():
    verdict, band, gate = _derive_verdict(
        15.0,
        "DENIES",
        [],
        natal_promise=True,
        kp_supported=True,
        has_qualified_window=True,
        final_transit_support=True,
        final_double_transit=True,
        timing_appropriate=True,
    )

    assert verdict == "DELAYED"
    assert band in ("MEDIUM", "WEAK")
    assert any("DENIES" in n for n in gate["notes"])
