"""Tests for Swiss Ephemeris marriage-date engine."""
from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("swisseph")

from vedic.panchang.generate_marriage_dates import (
    _panchang_anga,
    _step1_passes,
    _sun_longitude_allowed,
    generate_marriage_dates,
    generateMarriageDates,
)


def test_alias_matches():
    assert generateMarriageDates is generate_marriage_dates


def test_sun_longitude_windows():
    assert _sun_longitude_allowed(15.0) is True
    assert _sun_longitude_allowed(75.0) is True
    assert _sun_longitude_allowed(120.0) is False
    assert _sun_longitude_allowed(220.0) is True
    assert _sun_longitude_allowed(285.0) is True
    assert _sun_longitude_allowed(340.0) is False


def test_scan_returns_required_fields():
    rows = generate_marriage_dates(date(2026, 6, 3), years=1)
    assert isinstance(rows, list)
    for row in rows[:5]:
        assert set(row.keys()) == {
            "date", "tithi", "nakshatra", "jupiter_status", "venus_status",
        }
        assert row["jupiter_status"] in ("Uday", "Asta")
        assert row["venus_status"] in ("Uday", "Asta")
        assert row["jupiter_status"] == "Uday"
        assert row["venus_status"] == "Uday"


def test_five_year_window_end_exclusive():
    start = date(2026, 6, 3)
    rows = generate_marriage_dates(start, years=5)
    if rows:
        assert rows[0]["date"] >= start.isoformat()
        assert all(r["date"] < "2031-06-03" for r in rows)


def test_step1_rejects_amavasya_tithi():
    # Construct synthetic anga at Amavasya index
    anga = {
        "tithi_idx": 29,
        "tithi_num": 15,
        "tithi_name": "Amavasya",
        "paksha": "Krishna",
        "nak_idx": 3,
        "nak_name": "Rohini",
        "yoga_name": "Siddhi",
        "karana_name": "Bava",
        "tithi_label": "Krishna Amavasya",
    }
    assert _step1_passes(anga) is False


def test_step1_rejects_vishti_karana():
    anga = {
        "tithi_idx": 1,
        "tithi_num": 2,
        "tithi_name": "Dwitiya",
        "paksha": "Shukla",
        "nak_idx": 3,
        "nak_name": "Rohini",
        "yoga_name": "Siddhi",
        "karana_name": "Vishti (Bhadra)",
        "tithi_label": "Shukla Dwitiya",
    }
    assert _step1_passes(anga) is False
