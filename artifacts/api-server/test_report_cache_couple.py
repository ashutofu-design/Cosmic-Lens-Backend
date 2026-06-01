"""Couple PDF report_cache — repeat download should not regenerate."""
import report_cache as rc


def test_couple_cache_roundtrip():
    p1 = {"name": "A", "day": 1, "month": 5, "year": 1990, "hour": 10, "minute": 30, "ampm": "AM", "lat": 19.0, "lon": 72.8, "tz": 5.5, "place": "Mumbai"}
    p2 = {"name": "B", "day": 15, "month": 8, "year": 1992, "hour": 14, "minute": 0, "ampm": "PM", "lat": 28.6, "lon": 77.2, "tz": 5.5, "place": "Delhi"}
    params = rc.couple_cache_params("en", p1, p2)
    fake = b"%PDF-1.4 test"
    rid = rc.save(42, "milan_pro", "Milan Pro", params, fake, "test.pdf")
    assert rid
    hit = rc.find(42, "milan_pro", params)
    assert hit == fake
    miss = rc.find(99, "milan_pro", params)
    assert miss is None
