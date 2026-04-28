"""Phase 4.3 tests — nakshatra fact-checking + inverted-syntax MD/AD recall.

Self-contained. Run from artifacts/api-server: `python test_phase43.py`.
Asserts that _post_logic_check correctly emits / suppresses violations for
the new nakshatra and inverted-syntax dasha claim shapes.
"""
from __future__ import annotations

import sys
import traceback


def _setup():
    """Import openai_helper without triggering swisseph etc."""
    import openai_helper as oh
    return oh


def _kundli_fixture():
    """Synthetic kundli mirroring engine output. Moon = Bharani, pada 2,
    Mahadasha = Saturn, Antardasha = Mercury."""
    return {
        # Top-level Moon nakshatra fields (engine schema)
        "nakshatra": "Bharani",
        "nakshatraPada": 2,
        "nakshatraRuler": "Venus",
        # Ascendant
        "ascendant": {"sign": "Aries"},
        # Planets — Saturn 7th in Libra, Krittika nakshatra pada 3
        "planets": [
            {"name": "Sun", "house": 10, "sign": "Capricorn",
             "nakshatra": "Shravana", "nakshatraPada": 1},
            {"name": "Moon", "house": 2, "sign": "Taurus",
             "nakshatra": "Bharani", "nakshatraPada": 2},
            {"name": "Mars", "house": 5, "sign": "Leo",
             "nakshatra": "Magha", "nakshatraPada": 4},
            {"name": "Mercury", "house": 11, "sign": "Aquarius",
             "nakshatra": "Shatabhisha", "nakshatraPada": 1},
            {"name": "Jupiter", "house": 9, "sign": "Sagittarius",
             "nakshatra": "Mula", "nakshatraPada": 2},
            {"name": "Venus", "house": 12, "sign": "Pisces",
             "nakshatra": "Revati", "nakshatraPada": 3},
            {"name": "Saturn", "house": 7, "sign": "Libra",
             "nakshatra": "Chitra", "nakshatraPada": 3,
             "retrograde": False},
            {"name": "Rahu", "house": 3, "sign": "Gemini",
             "nakshatra": "Ardra"},
            {"name": "Ketu", "house": 9, "sign": "Sagittarius",
             "nakshatra": "Mula"},
        ],
        # Current dasha — Saturn MD / Mercury AD
        "currentDasha": {
            "mahadasha": {"planet": "Saturn",
                          "startDate": "2023-01-01",
                          "endDate":   "2042-01-01"},
            "antardasha": {"planet": "Mercury",
                           "startDate": "2025-06-01",
                           "endDate":   "2028-02-15"},
        },
    }


# ─── test runner ─────────────────────────────────────────────────────────────
_PASS = 0
_FAIL = 0
_FAIL_MSGS: list[str] = []


def _run(name: str, fn):
    global _PASS, _FAIL
    try:
        fn()
        _PASS += 1
        print(f"  PASS  {name}")
    except AssertionError as e:
        _FAIL += 1
        msg = f"  FAIL  {name}: {e}"
        _FAIL_MSGS.append(msg)
        print(msg)
    except Exception as e:
        _FAIL += 1
        msg = f"  ERR   {name}: {e!r}"
        _FAIL_MSGS.append(msg)
        traceback.print_exc()
        print(msg)


def _has_kind(violations, kind, **fields):
    for v in violations:
        if v.get("kind") != kind:
            continue
        if all(v.get(k) == val for k, val in fields.items()):
            return True
    return False


# ─── tests ───────────────────────────────────────────────────────────────────
def main():
    oh = _setup()
    kundli = _kundli_fixture()
    truth = oh._build_truth_facts(kundli)

    # Sanity checks on truth-facts construction
    print("\n[1/5] _build_truth_facts — schema population")
    _run("nakshatra dict has moon=Bharani",
         lambda: (lambda v=truth["nakshatra"]:
                  v["moon"] == "Bharani" or
                  (_ for _ in ()).throw(AssertionError(f"got {v}")))())
    _run("nakshatra dict has saturn=Chitra",
         lambda: (lambda v=truth["nakshatra"]:
                  v["saturn"] == "Chitra" or
                  (_ for _ in ()).throw(AssertionError(f"got {v}")))())
    _run("nakshatra_pada dict has moon=2",
         lambda: (lambda v=truth["nakshatra_pada"]:
                  v["moon"] == 2 or
                  (_ for _ in ()).throw(AssertionError(f"got {v}")))())
    _run("nakshatra_pada dict has saturn=3",
         lambda: (lambda v=truth["nakshatra_pada"]:
                  v["saturn"] == 3 or
                  (_ for _ in ()).throw(AssertionError(f"got {v}")))())

    # ─── nakshatra positive (correct claims should not violate) ──────────
    print("\n[2/5] Nakshatra POSITIVE cases (no violation)")

    pos_nak_cases = [
        "Aapka nakshatra Bharani hai.",
        "Your nakshatra is Bharani — strong Venus influence.",
        "Tumhara janm nakshatra Bharani hai bhai.",
        "Moon's nakshatra is Bharani in your chart.",
        "Chandra ka nakshatra Bharani hai.",
        "Saturn ka nakshatra Chitra hai (7th house).",
        "Saturn's nakshatra is Chitra.",
        "nakshatra Bharani hai aapka.",
        # Spelling variants
        "Aapka nakshatra Bharani hai (ruler: Shukra).",
        # Moon + correct
        "Moon nakshatra Bharani.",
    ]
    for i, txt in enumerate(pos_nak_cases):
        def _t(t=txt):
            v = oh._post_logic_check(t, truth)
            assert not any(x.get("kind", "").startswith("nakshatra") for x in v), \
                f"unexpected violation for {t!r}: {v}"
        _run(f"pos[{i}] {txt[:50]!r}", _t)

    # ─── nakshatra negative (invented claims should violate) ─────────────
    print("\n[3/5] Nakshatra NEGATIVE cases (violation expected)")

    neg_nak_cases = [
        ("Aapka nakshatra Rohini hai.", "moon", "Rohini"),
        ("Your nakshatra is Ashwini.", "moon", "Ashwini"),
        ("Tumhara janm nakshatra Krittika hai.", "moon", "Krittika"),
        ("Moon's nakshatra is Magha.", "moon", "Magha"),
        ("Chandra ka nakshatra Pushya hai.", "moon", "Pushya"),
        ("Saturn ka nakshatra Mula hai.", "saturn", "Mula"),
        ("Saturn's nakshatra is Anuradha.", "saturn", "Anuradha"),
        ("nakshatra Vishakha hai aapka.", "moon", "Vishakha"),
        # Spelling variant — Anushada → Anuradha → mismatch (truth=Bharani)
        ("Aapka nakshatra Anushada hai.", "moon", "Anuradha"),
        # Multi-word
        ("Your nakshatra is Purva Phalguni.", "moon", "Purva Phalguni"),
    ]
    for i, (txt, planet, claimed) in enumerate(neg_nak_cases):
        def _t(t=txt, p=planet, c=claimed):
            v = oh._post_logic_check(t, truth)
            assert _has_kind(v, "nakshatra_mismatch", planet=p,
                             claimed_nakshatra=c), \
                f"missing nakshatra_mismatch for {t!r} (planet={p}, " \
                f"claimed={c}): got {v}"
        _run(f"neg[{i}] {txt[:50]!r}", _t)

    # ─── negation guard ──────────────────────────────────────────────────
    print("\n[4a/5] Nakshatra NEGATION (no violation when negated)")

    neg_guard_cases = [
        "Aapka nakshatra Rohini nahi hai.",
        "Your nakshatra is not Ashwini.",
        "Moon's nakshatra is not Magha.",
        "Tumhara janm nakshatra Krittika nahi hai bhai.",
    ]
    for i, txt in enumerate(neg_guard_cases):
        def _t(t=txt):
            v = oh._post_logic_check(t, truth)
            assert not any(x.get("kind", "").startswith("nakshatra") for x in v), \
                f"unexpected violation under negation for {t!r}: {v}"
        _run(f"neg-guard[{i}] {txt[:50]!r}", _t)

    # ─── pada cases ──────────────────────────────────────────────────────
    print("\n[4b/5] Pada cases (correct + invented + ordinal)")

    # Correct (truth=2)
    pada_pos = [
        "Pada 2 mein hai.",
        "Aapka 2nd pada hai.",
        "Pada is 2 for Moon.",
    ]
    for i, txt in enumerate(pada_pos):
        def _t(t=txt):
            v = oh._post_logic_check(t, truth)
            assert not _has_kind(v, "nakshatra_pada_mismatch"), \
                f"unexpected pada violation for {t!r}: {v}"
        _run(f"pada-pos[{i}] {txt[:50]!r}", _t)

    # Invented (truth=2). All cases now include a Moon-context anchor
    # (aapka/janm/your/moon/nakshatra) — Phase 4.3 architect-review fix
    # requires this; truly anchor-less cases ("Pada is 3.") would correctly
    # be skipped as ambiguous and are tested under pada-fp[] instead.
    pada_neg = [
        ("Pada 4 hai aapka.", 4),                       # trailing anchor
        ("Aapka 1st pada hai.", 1),                     # leading anchor
        ("Janm pada is 3.", 3),                         # leading anchor
        ("Your nakshatra ka 3rd pada mein.", 3),        # leading anchor
    ]
    for i, (txt, claimed) in enumerate(pada_neg):
        def _t(t=txt, c=claimed):
            v = oh._post_logic_check(t, truth)
            assert _has_kind(v, "nakshatra_pada_mismatch", claimed_pada=c), \
                f"missing pada violation for {t!r} (claimed={c}): got {v}"
        _run(f"pada-neg[{i}] {txt[:50]!r}", _t)

    # ─── inverted-syntax MD/AD ───────────────────────────────────────────
    print("\n[5/5] Inverted-syntax MD/AD recall")

    # Truth: MD=Saturn, AD=Mercury

    # Forward syntax (already covered, sanity)
    forward_cases = [
        ("Abhi Saturn ki Mahadasha chal rahi hai.", False),  # correct
        ("Abhi Jupiter ki Mahadasha chal rahi hai.", True),  # wrong
    ]
    for i, (txt, should_violate) in enumerate(forward_cases):
        def _t(t=txt, sv=should_violate):
            v = oh._post_logic_check(t, truth)
            has = _has_kind(v, "dasha_md_mismatch")
            assert has == sv, \
                f"forward MD: expected violate={sv} for {t!r}, got {v}"
        _run(f"md-fwd[{i}] {txt[:50]!r}", _t)

    # Inverted syntax — the new shape
    inverted_md_cases = [
        ("Abhi Mahadasha Saturn ki chal rahi hai.", False),  # correct
        ("Abhi Mahadasha Jupiter ki chal rahi hai.", True),  # wrong
        ("Currently Maha-dasha Saturn hai.", False),         # correct (hyphen)
        ("Currently Maha dasha Mars hai.", True),            # wrong
        ("Abhi MD Saturn ki chal rahi hai.", False),         # correct (MD abbr)
        ("Abhi MD Sun chal raha hai.", True),                # wrong
    ]
    for i, (txt, should_violate) in enumerate(inverted_md_cases):
        def _t(t=txt, sv=should_violate):
            v = oh._post_logic_check(t, truth)
            has = _has_kind(v, "dasha_md_mismatch")
            assert has == sv, \
                f"inv MD: expected violate={sv} for {t!r}, got {v}"
        _run(f"md-inv[{i}] {txt[:50]!r}", _t)

    inverted_ad_cases = [
        ("Abhi Antardasha Mercury ki chal rahi hai.", False),  # correct
        ("Abhi Antardasha Venus ki chal rahi hai.", True),     # wrong
        ("Currently Antar-dasha Mercury hai.", False),         # correct
        ("Bhukti Mars chal rahi.", True),                      # wrong
        ("Bhukti Mercury hai abhi.", False),                   # correct
    ]
    for i, (txt, should_violate) in enumerate(inverted_ad_cases):
        def _t(t=txt, sv=should_violate):
            v = oh._post_logic_check(t, truth)
            has = _has_kind(v, "dasha_ad_mismatch")
            assert has == sv, \
                f"inv AD: expected violate={sv} for {t!r}, got {v}"
        _run(f"ad-inv[{i}] {txt[:50]!r}", _t)

    # ─── architect Phase-4.3-review adversarials ─────────────────────────
    print("\n[6/5] Architect-review adversarial false-positive guards")

    # Pada FPs — non-Moon planet pada must NOT fire Moon-pada violation.
    # Truth.moon.pada = 2 in fixture; Saturn.pada = 3 in fixture.
    pada_fp_cases = [
        "Saturn ka pada 3 hai chart mein.",         # planet-anchored — skip
        "Rahu pada 1 mein hai.",                    # planet-anchored — skip
        "Mars 4th pada mein placed hai.",           # planet-anchored — skip
        "Jupiter ke 2 pada hain.",                  # ambiguous, no moon-anchor → skip
        "Pada 4 calculated.",                       # no moon-anchor → skip
        # Architect re-review: multi-clause distant planet veto (38-char gap)
        "Saturn ka nakshatra Chitra mein aapka 1st pada hai.",
    ]
    for i, txt in enumerate(pada_fp_cases):
        def _t(t=txt):
            v = oh._post_logic_check(t, truth)
            assert not _has_kind(v, "nakshatra_pada_mismatch"), \
                f"FALSE POS: pada-mismatch fired on planet-pada / no-anchor " \
                f"text {t!r}: {v}"
        _run(f"pada-fp[{i}] {txt[:50]!r}", _t)

    # Pada TPs (Moon-anchored, wrong pada) — must STILL fire after the guard.
    pada_tp_cases = [
        ("Aapka nakshatra Bharani pada 4 hai.", 4),
        ("Your janm pada is 1.", 1),
        ("Moon's pada is 3.", 3),
        ("Tumhara nakshatra Bharani 1st pada mein.", 1),
    ]
    for i, (txt, claimed) in enumerate(pada_tp_cases):
        def _t(t=txt, c=claimed):
            v = oh._post_logic_check(t, truth)
            assert _has_kind(v, "nakshatra_pada_mismatch", claimed_pada=c), \
                f"missed Moon-pada mismatch for {t!r} (claimed={c}): {v}"
        _run(f"pada-tp[{i}] {txt[:50]!r}", _t)

    # Inverted MD/AD precision — "Mahadasha Jupiter ke yog" must NOT fire
    # (Jupiter is not the current MD; truth=Saturn; "ke yog" is not a
    # continuation token).
    md_precision_cases = [
        # Should NOT fire (these are textbook/contextual, not current claim)
        ("Mahadasha Jupiter ke yog ban rahe hain.", False),
        ("Antardasha Mars ke effects acche nahi hote.", False),
        ("Mahadasha Mars pe discussion baad mein.", False),
        # Architect re-review FPs — possessive without chal* must NOT fire
        ("Currently Mahadasha Jupiter ki details samjho.", False),
        ("Abhi Mahadasha Jupiter ki wajah se pressure hai.", False),
        ("Antardasha Mars ki baat karte hain.", False),
        # Should still fire (genuine current-claim with valid tail token)
        ("Mahadasha Jupiter ki chal rahi hai.", True),  # wrong (truth=Saturn)
        ("Antardasha Venus hai abhi.", True),           # wrong (truth=Mercury)
        ("Mahadasha Jupiter ki bahut tough chal rahi hai.", True),  # ki+chal w/ filler
    ]
    for i, (txt, should_violate) in enumerate(md_precision_cases):
        def _t(t=txt, sv=should_violate):
            v = oh._post_logic_check(t, truth)
            md_fired = _has_kind(v, "dasha_md_mismatch")
            ad_fired = _has_kind(v, "dasha_ad_mismatch")
            fired = md_fired or ad_fired
            assert fired == sv, \
                f"inverted-precision {t!r}: expected violate={sv}, got " \
                f"md_fired={md_fired} ad_fired={ad_fired}, all_v={v}"
        _run(f"md-prec[{i}] {txt[:50]!r}", _t)

    # ─── summary ─────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"Phase 4.3 test summary:  PASS={_PASS}  FAIL={_FAIL}")
    print("=" * 60)
    if _FAIL:
        print("\nFailures:")
        for m in _FAIL_MSGS:
            print(m)
        sys.exit(1)


if __name__ == "__main__":
    main()
