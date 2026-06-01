"""Regression harness for vivah muhurta engine."""
from __future__ import annotations

from datetime import date

import pytest

from vedic.panchang.marriage_muhurta import scan_vivah_muhurat
from vedic.panchang.vivah_nakshatra import normalize_nakshatra, tarabala


DELHI = {"lat": 28.6139, "lng": 77.2090, "tz_h": 5.5}


pytest.importorskip("swisseph")


def test_scan_returns_structure():
    r = scan_vivah_muhurat(date(2026, 6, 1), days=14, **DELHI)
    assert r["engine_version"].startswith("vivah-3")
    assert "highly_favorable" in r
    assert "disclaimer" in r


def test_response_lists_include_all_bucket_days():
    r = scan_vivah_muhurat(date(2026, 5, 1), days=60, **DELHI)
    assert len(r["highly_favorable"]) == r["highly_favorable_count"]
    assert len(r["favorable"]) == r["favorable_count"]
    assert len(r["conditional"]) == r["conditional_count"]


def test_highly_favorable_has_time_windows():
    r = scan_vivah_muhurat(date(2026, 5, 1), days=60, **DELHI)
    for bucket in ("highly_favorable", "favorable"):
        for day in r.get(bucket, [])[:3]:
            if day.get("best_windows"):
                w = day["best_windows"][0]
                assert "start" in w and "end" in w
                assert w.get("lagna")


def test_nakshatra_normalize():
    assert normalize_nakshatra("Uttara Phalguni") == "U.Phalguni"
    assert normalize_nakshatra("Rohini") == "Rohini"


def test_tarabala_sampat_ok():
    tb = tarabala("Rohini", "Mrigashira")
    assert tb["ok"] is True


def test_tarabala_janma_bad():
    tb = tarabala("Rohini", "Rohini")
    assert tb["ok"] is False
