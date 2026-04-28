"""Phase 4.4 — lookup_engine extension tests.

Covers the two new detector families added to `_post_logic_check`:
  * lagna_mismatch       — wrong ascendant sign claim
  * dasha_end_year_mismatch — wrong end-year for the CURRENT Mahadasha

Other detectors (planet-house, planet-sign, retrograde, manglik, nakshatra,
pada, MD, AD) are covered by test_phase43.py.

Each detector is exercised across:
  * positive (mismatch detected)
  * negative (correct claim → no violation)
  * variant (Sanskrit/Hinglish form normalizes correctly)
  * negation (suppressed by "nahi"/"not")
  * planet-disambiguation (dasha-end only — wrong-planet skip)
  * retry-correction-msg (round-trip into _post_logic_correction_msg)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai_helper import (  # noqa: E402
    _build_truth_facts,
    _post_logic_check,
    _post_logic_correction_msg,
)


# ──────────────────────────────────────────────────────────────────────────────
# Test fixtures
# ──────────────────────────────────────────────────────────────────────────────
_KUNDLI_ARIES_LAGNA_SATURN_MD = {
    "ascendant": "Aries",
    "planets": [
        {"name": "Sun",     "house": 1, "sign": "Aries",   "retro": False},
        {"name": "Moon",    "house": 4, "sign": "Cancer",  "retro": False,
         "nakshatra": "Pushya", "pada": 2},
        {"name": "Mars",    "house": 7, "sign": "Libra",   "retro": False},
        {"name": "Mercury", "house": 2, "sign": "Taurus",  "retro": False},
        {"name": "Jupiter", "house": 5, "sign": "Leo",     "retro": False},
        {"name": "Venus",   "house": 3, "sign": "Gemini",  "retro": False},
        {"name": "Saturn",  "house": 10, "sign": "Capricorn", "retro": False},
        {"name": "Rahu",    "house": 6, "sign": "Virgo",   "retro": False},
        {"name": "Ketu",    "house": 12, "sign": "Pisces", "retro": False},
    ],
    "currentDasha": {
        "mahadasha": {"planet": "Saturn",  "startDate": "2020-01-01",
                       "endDate": "2039-01-01"},
        "antardasha": {"planet": "Mercury", "startDate": "2025-06-01",
                        "endDate": "2028-02-01"},
    },
}


def _truth():
    return _build_truth_facts(_KUNDLI_ARIES_LAGNA_SATURN_MD)


# ──────────────────────────────────────────────────────────────────────────────
# Pre-flight: truth fixture sanity
# ──────────────────────────────────────────────────────────────────────────────
def test_truth_fixture_carries_lagna():
    # Post-architect-hotfix: _lagna is canonicalized to lowercase English
    # via _tf_canon_sign so the detector can compare directly without
    # additional normalization.
    t = _truth()
    assert t.get("_lagna") == "aries", t.get("_lagna")


def test_truth_fixture_carries_md_end():
    t = _truth()
    assert (t.get("current_md") or {}).get("end") == "2039-01-01"


# ──────────────────────────────────────────────────────────────────────────────
# LAGNA_MISMATCH detector
# ──────────────────────────────────────────────────────────────────────────────
def test_lagna_wrong_english_forward():
    text = "Aapki lagna Taurus hai, isliye aap stable nature ke hain."
    v = _post_logic_check(text, _truth())
    kinds = [x["kind"] for x in v]
    assert "lagna_mismatch" in kinds, v
    m = next(x for x in v if x["kind"] == "lagna_mismatch")
    assert m["claimed_lagna"] == "taurus"
    assert m["actual_lagna"] == "aries"


def test_lagna_wrong_sanskrit_forward():
    text = "Aapki lagna Vrishabh hai, isliye stability mil rahi hai."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_wrong_inverted():
    text = "Aap Taurus lagna ke jatak hain — bahut steady hain."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_wrong_ascendant_english():
    text = "Your ascendant is Gemini, which gives you communication skills."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_correct_english_no_violation():
    text = "Aapki lagna Aries hai — leadership qualities prabal hain."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_correct_sanskrit_no_violation():
    text = "Aapki lagna Mesh hai — dynamic energy aap me hai."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_correct_inverted_no_violation():
    text = "Aap Aries lagna ke jatak hain."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_negation_suppressed():
    text = "Aapki lagna Taurus nahi hai, balki Aries hai."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_truth_handles_dict_ascendant():
    # ARCHITECT-FOUND GAP: ascendant can also be a dict {"sign": "Aries"}.
    # _build_truth_facts must extract the lagna in that shape too.
    kundli_dict_asc = dict(_KUNDLI_ARIES_LAGNA_SATURN_MD)
    kundli_dict_asc["ascendant"] = {"sign": "Aries", "degree": 12.5}
    truth = _build_truth_facts(kundli_dict_asc)
    assert truth["_lagna"] == "aries", truth["_lagna"]
    text = "Aapki lagna Taurus hai."
    v = _post_logic_check(text, truth)
    assert any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_truth_handles_sanskrit_dict_ascendant():
    # Dict-shaped ascendant whose .sign is itself Sanskrit (Mesh) must
    # canonicalize to "aries" via _tf_canon_sign.
    kundli_sanskrit = dict(_KUNDLI_ARIES_LAGNA_SATURN_MD)
    kundli_sanskrit["ascendant"] = {"sign": "Mesh"}
    truth = _build_truth_facts(kundli_sanskrit)
    assert truth["_lagna"] == "aries", truth["_lagna"]


def test_lagna_truth_falls_back_to_lagna_field():
    # ARCHITECT-FOLLOWUP: when ascendant is a dict that LACKS a usable
    # .sign field but kundli has a top-level "lagna" string, we must
    # fall back to that rather than silently disabling lagna validation.
    kundli_fallback = dict(_KUNDLI_ARIES_LAGNA_SATURN_MD)
    kundli_fallback["ascendant"] = {"degree": 12.5}  # no .sign
    kundli_fallback["lagna"] = "Aries"
    truth = _build_truth_facts(kundli_fallback)
    assert truth["_lagna"] == "aries", truth["_lagna"]


def test_lagna_regional_alias_brish_recognized():
    # "Brish" / "Vrush" are regional Hindi spellings of Vrishabh/Taurus.
    # Architect recommended these be handled — they are now via
    # _SIGN_VARIANT_LC explicit additions.
    text = "Aapki lagna Brish hai, isliye stable hain."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "lagna_mismatch" for x in v), v
    text2 = "Aapki lagna Vrush hai."
    v2 = _post_logic_check(text2, _truth())
    assert any(x["kind"] == "lagna_mismatch" for x in v2), v2


def test_lagna_engine_alias_singh_recognized():
    # "Singh" is the standard Hindi alias for Simha/Leo, present in the
    # engine alias table — pulling _TF_SIGN_ALIASES_LC into _SIGN_VARIANT_LC
    # gives us this alias for free.
    text = "Aapki lagna Singh hai."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "lagna_mismatch" for x in v), v


def test_lagna_one_violation_per_regex_max():
    # Two contradictory claims — we only emit at most one per regex pass
    # (the corrective system message is the same regardless of count).
    text = ("Aapki lagna Taurus hai. Aapki lagna Gemini bhi hai. "
            "Aapki lagna Cancer bhi.")
    v = _post_logic_check(text, _truth())
    lagna_violations = [x for x in v if x["kind"] == "lagna_mismatch"]
    # Forward regex fires once; inverted regex doesn't match this text.
    assert len(lagna_violations) == 1, lagna_violations


def test_lagna_disabled_via_env(monkeypatch=None):
    # No pytest fixture — manually set+restore env.
    prev = os.environ.get("LOOKUP_ENGINE")
    os.environ["LOOKUP_ENGINE"] = "0"
    try:
        text = "Aapki lagna Taurus hai."
        v = _post_logic_check(text, _truth())
        assert not any(x["kind"] == "lagna_mismatch" for x in v), v
    finally:
        if prev is None:
            os.environ.pop("LOOKUP_ENGINE", None)
        else:
            os.environ["LOOKUP_ENGINE"] = prev


# ──────────────────────────────────────────────────────────────────────────────
# DASHA_END_YEAR_MISMATCH detector
# ──────────────────────────────────────────────────────────────────────────────
def test_dasha_end_year_wrong_forward():
    text = "Aapki Saturn Mahadasha 2055 tak chalegi, dheeraj rakhiye."
    v = _post_logic_check(text, _truth())
    kinds = [x["kind"] for x in v]
    assert "dasha_end_year_mismatch" in kinds, v
    m = next(x for x in v if x["kind"] == "dasha_end_year_mismatch")
    assert m["claimed_year"] == 2055
    assert m["actual_year"] == 2039
    assert m["actual_md"] == "Saturn"


def test_dasha_end_year_wrong_inverted():
    text = "Mahadasha Saturn ki 2050 tak chalegi."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_correct_no_violation():
    text = "Saturn Mahadasha 2039 tak chalegi, fir Mercury MD shuru hogi."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_one_year_slack_no_violation():
    # ±1 year tolerance for ayanamsa drift / calendar straddle.
    text = "Saturn Mahadasha 2040 tak chalegi."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v
    text2 = "Saturn Mahadasha 2038 tak chalegi."
    v2 = _post_logic_check(text2, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v2), v2


def test_dasha_end_year_two_year_drift_does_violate():
    text = "Saturn Mahadasha 2041 tak chalegi."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_other_planet_skipped():
    # AI describes a FUTURE Mahadasha (Mercury after Saturn) — different
    # planet from current MD; must not fire even though the year doesn't
    # match Saturn's end.
    text = ("Saturn ke baad Mercury Mahadasha 2056 tak chalegi, "
            "bahut productive period hoga.")
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_cross_md_bridging_no_fp():
    # ARCHITECT-FOUND FP: with a non-tempered gap, the FWD pattern would
    # bridge "Saturn Mahadasha" → "...Mercury Mahadasha 2056 tak", capture
    # planet=Saturn + year=2056, and false-fire vs Saturn's actual 2039.
    # The tempered gap (no second dasha-token allowed) must prevent this.
    text = "Saturn Mahadasha ke baad Mercury Mahadasha 2056 tak chalegi."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_cross_md_bridging_no_fp_english():
    # Same FP class via English leading-keyword form.
    text = "Saturn Mahadasha is followed by Mercury Mahadasha which ends in 2056."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_benign_filler_gap_still_fires():
    # ARCHITECT-FOLLOWUP: lock recall — the tempered gap must still
    # detect mismatches when there's plenty of benign filler text between
    # "<planet> Mahadasha" and the year-keyword pair, as long as no
    # second dasha-token bridges the clauses.
    text = ("Saturn Mahadasha jo abhi chal rahi hai, kaafi tough phase laayegi, "
            "aur 2055 tak chalegi pretty intensely.")
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_negation_suppressed():
    text = "Saturn Mahadasha 2055 tak nahi chalegi, balki 2039 tak."
    v = _post_logic_check(text, _truth())
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_english_form():
    text = "Your Saturn Mahadasha ends in 2055, so plan accordingly."
    v = _post_logic_check(text, _truth())
    assert any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


def test_dasha_end_year_no_md_in_truth_skipped():
    # Defensive: missing current_md must not crash.
    kundli_no_dasha = dict(_KUNDLI_ARIES_LAGNA_SATURN_MD)
    kundli_no_dasha.pop("currentDasha", None)
    truth = _build_truth_facts(kundli_no_dasha)
    text = "Saturn Mahadasha 2055 tak chalegi."
    v = _post_logic_check(text, truth)
    assert not any(x["kind"] == "dasha_end_year_mismatch" for x in v), v


# ──────────────────────────────────────────────────────────────────────────────
# Integration: violations round-trip through the corrective-msg builder
# ──────────────────────────────────────────────────────────────────────────────
def test_correction_msg_includes_lagna_correction():
    text = "Aapki lagna Taurus hai."
    truth = _truth()
    v = _post_logic_check(text, truth)
    msg = _post_logic_correction_msg(v, truth)
    assert "Lagna" in msg or "lagna" in msg.lower(), msg
    assert "Aries" in msg, msg
    assert "Taurus" in msg, msg


def test_correction_msg_includes_dasha_end_correction():
    text = "Saturn Mahadasha 2055 tak chalegi."
    truth = _truth()
    v = _post_logic_check(text, truth)
    msg = _post_logic_correction_msg(v, truth)
    assert "2039" in msg, msg
    assert "2055" in msg, msg
    assert "Saturn" in msg, msg


def test_correction_msg_handles_combined_violations():
    text = ("Aapki lagna Taurus hai aur Saturn Mahadasha 2055 tak chalegi.")
    truth = _truth()
    v = _post_logic_check(text, truth)
    kinds = {x["kind"] for x in v}
    assert "lagna_mismatch" in kinds
    assert "dasha_end_year_mismatch" in kinds
    msg = _post_logic_correction_msg(v, truth)
    # Both correction lines present
    assert "Aries" in msg and "Taurus" in msg
    assert "2039" in msg and "2055" in msg


# ──────────────────────────────────────────────────────────────────────────────
# Backward-compat: existing detectors still fire alongside Phase 4.4
# ──────────────────────────────────────────────────────────────────────────────
def test_existing_planet_house_still_fires_alongside_lagna():
    # AI gets BOTH lagna and a planet-house wrong in one sentence.
    text = ("Aapki lagna Taurus hai aur Mars 5th house mein hai, "
            "bahut energetic hain aap.")
    v = _post_logic_check(text, _truth())
    kinds = {x["kind"] for x in v}
    assert "lagna_mismatch" in kinds, v
    assert "planet_house_mismatch" in kinds, v


# ──────────────────────────────────────────────────────────────────────────────
# Quick CLI runner — `python test_phase44_lookup.py` prints PASS/FAIL.
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import traceback
    tests = [
        (n, fn) for n, fn in sorted(globals().items())
        if n.startswith("test_") and callable(fn)
    ]
    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL  {name}: {exc}")
        except Exception:
            failed += 1
            print(f"  ERROR {name}")
            traceback.print_exc()
    print(f"\n{passed}/{passed + failed} passed")
    sys.exit(0 if failed == 0 else 1)
