"""Tests for swe_core, daily muhurat, festival/vrat, and gochar engines."""
from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("swisseph")

from vedic.panchang.daily_muhurat import (
    compute_day_muhuratas,
    detect_sankrantis,
    get_tarabala_and_chandrabala,
)
from vedic.panchang.festival_vrat import festivals_on_date, get_monthly_festivals
from vedic.panchang.gochar import get_current_gochar
from vedic.panchang.marriage_muhurta import scan_vivah_muhurat
from vedic.panchang.swe_core import SWE_OK, sunrise_sunset, tithi_from_longitudes


DELHI = {"lat": 28.6139, "lng": 77.2090, "tz_h": 5.5}


def test_swe_ok():
    assert SWE_OK is True


def test_sunrise_sunset_delhi():
    sr, ss, sn = sunrise_sunset(date(2026, 6, 3), **DELHI)
    assert sr < ss
    assert sr.date() == date(2026, 6, 3)


def test_day_muhuratas_structure():
    out = compute_day_muhuratas(date(2026, 6, 3), **DELHI)
    assert "sunrise" in out
    assert "rahu_kaal" in out
    assert "abhijit_muhurat" in out
    assert out["rahu_kaal"]["start"] and out["rahu_kaal"]["end"]


def test_tarabala_chandrabala():
    r = get_tarabala_and_chandrabala("Karka", "Rohini", date(2026, 6, 3), tz_h=5.5)
    assert "tarabala" in r
    assert "chandrabala" in r
    assert "strength_score" in r


def test_sankranti_detection_year():
    events = detect_sankrantis(date(2026, 1, 1), date(2026, 12, 31), tz_h=5.5)
    assert len(events) >= 10
    assert events[0]["from_rashi"] and events[0]["to_rashi"]


def test_monthly_festivals_has_ekadashi():
    rows = get_monthly_festivals(3, 2026, tz_h=5.5)
    names = [r["festival_name"] for r in rows]
    assert any("Ekadashi" in n for n in names)


def test_festivals_purnima_tithi_15():
    # scan March 2026 for Purnima rows
    rows = get_monthly_festivals(3, 2026, tz_h=5.5)
    purnima = [r for r in rows if r["festival_name"] == "Purnima"]
    assert purnima
    assert all(r["tithi"] == 15 for r in purnima)


def test_gochar_nine_planets():
    g = get_current_gochar(**DELHI)
    assert set(g["planets"].keys()) == {
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    }
    j = g["planets"]["jupiter"]
    assert "rashi" in j
    assert "degree" in j
    assert "is_retrograde" in j
    assert j.get("status") in ("Uday", "Asta", None) or "status" in j


def test_vivah_muhurat_scan_windows():
    """Geo + sunrise + lagna engine returns tiered days with optional windows."""
    out = scan_vivah_muhurat(date(2026, 6, 1), days=45, **DELHI)
    assert out["engine_version"]
    assert "highly_favorable" in out
    for key in ("highly_favorable", "favorable"):
        for row in out[key][:3]:
            assert row["date"]
            assert row["tier"] == key
            assert "tithi" in row
            if row.get("best_windows"):
                w = row["best_windows"][0]
                assert w["start"] and w["end"]
