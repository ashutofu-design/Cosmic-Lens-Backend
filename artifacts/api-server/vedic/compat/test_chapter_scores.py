"""Tests for chapter_scores."""
from vedic.compat.chapter_scores import compute_chapter_scores


_MILAN = {
    "p1": {"name": "A", "manglik": False},
    "p2": {"name": "B", "manglik": False},
    "koots": [
        {"key": "nadi",   "label": "Nadi",   "score": 8, "max": 8},
        {"key": "gana",   "label": "Gana",   "score": 6, "max": 6},
        {"key": "bhakut", "label": "Bhakut", "score": 7, "max": 7},
        {"key": "maitri", "label": "Maitri", "score": 4, "max": 5},
        {"key": "yoni",   "label": "Yoni",   "score": 2, "max": 4},
        {"key": "tara",   "label": "Tara",   "score": 3, "max": 3},
        {"key": "vasya",  "label": "Vasya",  "score": 2, "max": 2},
        {"key": "varna",  "label": "Varna",  "score": 1, "max": 1},
    ],
    "total": 33, "max": 36,
}


def test_emits_seven_chapters_each_with_score():
    out = compute_chapter_scores(_MILAN, {}, {}, {})
    chs = out.get("chapters") or {}
    assert len(chs) == 7
    for k, v in chs.items():
        sc = v.get("score_0_10")
        assert sc is not None and 0 <= float(sc) <= 10


def test_never_raises_on_empty_input():
    out = compute_chapter_scores({}, {}, {}, {})
    assert out.get("chapters")
