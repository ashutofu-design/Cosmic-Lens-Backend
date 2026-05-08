"""Tests for d9_marriage compute_d9_marriage."""
from vedic.compat.d9_marriage import compute_d9_marriage


def _k(asc, planets, d9_planets, d9_asc="Pisces"):
    return {
        "ascendant": asc,
        "planets": planets,
        "divisionalCharts": {"D9": {"ascendant": d9_asc,
                                     "planets": d9_planets}},
    }


def test_returns_required_shape():
    k1 = _k("Leo",
            [{"name": "Venus", "sign": "Taurus", "longitude": 45.0}],
            [{"name": "Venus", "sign": "Pisces"}])
    k2 = _k("Aquarius",
            [{"name": "Venus", "sign": "Aries", "longitude": 25.0}],
            [{"name": "Venus", "sign": "Taurus"}], d9_asc="Sagittarius")
    out = compute_d9_marriage(k1, k2)
    assert "p1" in out and "p2" in out and "sync" in out
    for side in ("p1", "p2"):
        sc = out[side].get("marriage_maturity_0_10")
        assert sc is not None and 0 <= float(sc) <= 10
    sync_sc = out["sync"].get("score_0_10")
    assert sync_sc is not None and 0 <= float(sync_sc) <= 10


def test_never_raises_on_empty_input():
    out = compute_d9_marriage({}, {})
    assert "p1" in out and "p2" in out and "sync" in out
