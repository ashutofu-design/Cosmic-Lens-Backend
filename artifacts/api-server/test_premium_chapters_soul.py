"""Regression tests for the soul fallback (Phase 2.5.11.23-soul).
Locks: no audit-report template phrases, no engine-vocab leaks, every
chapter has 3-layer prose + name-anchoring + minimum word density.
Also locks: validator rejects polish-path output that regresses tone,
and fallback never raises on malformed inputs.
"""
import copy
from vedic.compat.premium_chapters import (
    _safe_fallback, CHAPTER_KEYS, _validate_premium, SOUL_BAN_PHRASES,
)

BANNED_PHRASES = [
    "engine driver", "engine drivers", "Engine driver", "Engine drivers",
    "engine score", "Based on engine score", "engine signals",
    "No significant friction", "no significant friction",
    "natural baseline compatibility",
    "stable and well within", "drivers indicate practical compatibility",
    "Chapter not generated", "Detailed reading was not generated",
    # KP/Vedic backend jargon must never leak
    "Sub-Lord", "sub-lord", "CSL", "7CSL", "signifies house",
    "Vimshottari", "Antardasha",
]

MILAN_FACTS = {
    "p1": {"name": "Vikram"}, "p2": {"name": "Sanya"},
    "total": 22, "max": 36,
}
CH_SCORES_FULL = {
    "chapters": {
        "ch1": {"title": "Emotional Compatibility",  "score_0_10": 8.2, "drivers": ["x"], "cautions": [], "key_facts": {}},
        "ch2": {"title": "Trust & Loyalty",          "score_0_10": 7.5, "drivers": [],    "cautions": ["y"], "key_facts": {}},
        "ch3": {"title": "Communication & Conflict", "score_0_10": 5.0, "drivers": [],    "cautions": [], "key_facts": {}},
        "ch4": {"title": "Marriage Stability",       "score_0_10": 3.2, "drivers": [],    "cautions": ["z"], "key_facts": {}},
        "ch5": {"title": "Chemistry",                "score_0_10": 6.8, "drivers": [],    "cautions": [], "key_facts": {}},
        "ch6": {"title": "Family + Practical Life",  "score_0_10": 2.5, "drivers": [],    "cautions": [], "key_facts": {}},
        "ch7": {"title": "Future Direction",         "score_0_10": 7.9, "drivers": [],    "cautions": [], "key_facts": {}},
    }
}

def _all_text(payload: dict) -> str:
    parts = [payload.get("hidden_truth", ""), payload.get("verdict", "")]
    parts += payload.get("special", []) + payload.get("damage", []) + payload.get("practical", [])
    for c in payload.get("chapters", []):
        parts += [c.get("kya_dikh", ""), c.get("kya_matlab", ""), c.get("kya_dhyan", ""), c.get("grounding", "")]
    return " ".join(parts)


def test_no_banned_phrases_full_payload():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise={"couple_verdict": "PARTIAL"})
    text = _all_text(out)
    for phrase in BANNED_PHRASES:
        assert phrase not in text, f"Banned phrase leaked into soul fallback: {phrase!r}"


def test_no_banned_phrases_empty_chapters():
    """Even with zero chapter data, fallback must not emit template phrases."""
    out = _safe_fallback(MILAN_FACTS, {"chapters": {}}, kp_promise=None)
    text = _all_text(out)
    for phrase in BANNED_PHRASES:
        assert phrase not in text, f"Banned phrase leaked in empty-chapter case: {phrase!r}"


def test_every_chapter_has_three_layers():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    chapters = out["chapters"]
    assert len(chapters) == 7
    for c in chapters:
        for fld in ("kya_dikh", "kya_matlab", "kya_dhyan"):
            v = c.get(fld, "")
            assert len(v) >= 80, f"{c['key']}.{fld} too short ({len(v)} chars): {v!r}"
            # must not be the old generic template
            assert "engine drivers are stable" not in v
            assert "No significant friction" not in v


def test_partner_names_anchored_throughout():
    """Both names must appear MULTIPLE times across the prose — premium reports
    must feel personal, not generic."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise={"couple_verdict": "STRONG"})
    text = _all_text(out)
    assert text.count("Vikram") >= 5, f"P1 name only mentioned {text.count('Vikram')}× — too impersonal"
    assert text.count("Sanya") >= 5, f"P2 name only mentioned {text.count('Sanya')}× — too impersonal"


def test_total_score_appears_in_hidden_or_verdict():
    """Score must surface (replit.md anti-hallucination policy)."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    score_str = "22"
    combined = out["hidden_truth"] + " " + out["verdict"]
    assert score_str in combined


def test_high_chapters_drive_special_low_chapters_drive_damage():
    """HIGH-scored chapters (≥7) seed special[]; LOW (<4) seed damage[]."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    # ch1(8.2), ch2(7.5), ch7(7.9) are HIGH → special bullets must be rich
    assert len(out["special"]) >= 3
    # ch4(3.2), ch6(2.5) are LOW → damage bullets must exist (not empty)
    assert len(out["damage"]) >= 2
    # damage must be framed as patterns, not "no friction"
    for d in out["damage"]:
        assert "no friction" not in d.lower()
        assert "Vikram" in d or "Sanya" in d, "damage bullet must be name-anchored"


def test_minimum_word_density():
    """Whole payload must have substantial word count — premium expectation."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    words = len(_all_text(out).split())
    assert words >= 1400, f"Soul fallback only {words} words — too thin for a 24-page premium PDF"


def test_kya_dhyan_includes_concrete_practice():
    """Layer 3 must name an actual practice, not vague advice."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    # at least 4 of 7 chapters must reference a concrete ritual/practice keyword
    practice_keywords = ["minute", "ritual", "prayer", "walk", "check-in",
                         "anniversary", "monthly", "weekly", "daily", "calendar"]
    hits = sum(
        1 for c in out["chapters"]
        if any(k in c["kya_dhyan"].lower() for k in practice_keywords)
    )
    assert hits >= 4, f"Only {hits}/7 chapters name a concrete practice in kya_dhyan"


# ──────────────────────────────────────────────────────────
#  Phase 2.5.11.23-soul: validator hardening regression tests
# ──────────────────────────────────────────────────────────

def _build_valid_polish_payload():
    """Build a minimal-but-valid polish-path payload that passes the validator,
    so we can mutate single fields and assert rejection."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    # ensure each chapter has a non-empty grounding (validator requires 10-240 chars)
    for c in out["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = f"Reading anchored to {c['title']}, score band derived from chart."
    # validator caps damage bullets at 5 + each 15-320 chars; trim if needed
    out["damage"] = [d[:300] for d in out["damage"][:5]]
    # ensure we have exactly 3 special bullets within 15-220 chars
    out["special"] = [s[:200] for s in out["special"][:3]]
    out["practical"] = [p[:580] for p in out["practical"][:3]]
    return out


def test_validator_accepts_valid_soul_payload():
    out = _build_valid_polish_payload()
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, f"Soul payload should pass validator, got: {reason}"


def test_validator_rejects_each_soul_banned_phrase():
    """Mirror of SOUL_BAN_PHRASES — every entry must trigger rejection."""
    base = _build_valid_polish_payload()
    for phrase in SOUL_BAN_PHRASES:
        polluted = copy.deepcopy(base)
        polluted["chapters"][0]["kya_dikh"] = (
            polluted["chapters"][0]["kya_dikh"][:200] + " " + phrase
        )
        ok, reason = _validate_premium(polluted, MILAN_FACTS, CH_SCORES_FULL)
        assert not ok, f"Validator failed to reject banned phrase: {phrase!r}"
        assert reason.startswith("soul_banned:"), f"Wrong reject reason: {reason}"


def test_validator_rejects_low_name_density():
    """Polish path that drops names below threshold must be rejected."""
    base = _build_valid_polish_payload()
    # strip P2's name everywhere except one mention (validator requires ≥3)
    for c in base["chapters"]:
        for fld in ("kya_dikh", "kya_matlab", "kya_dhyan", "grounding"):
            c[fld] = c[fld].replace("Sanya", "she")
    base["hidden_truth"] = base["hidden_truth"].replace("Sanya", "she")
    base["verdict"] = "Sanya, " + base["verdict"].replace("Sanya", "she")  # 1 mention only
    base["special"] = [s.replace("Sanya", "she") for s in base["special"]]
    base["damage"] = [d.replace("Sanya", "she") for d in base["damage"]]
    base["practical"] = [p.replace("Sanya", "she") for p in base["practical"]]
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok, "Validator should reject low name density"
    assert "name_density_low" in reason or "name_missing" in reason, f"Wrong reason: {reason}"


# ──────────────────────────────────────────────────────────
#  Phase 2.5.11.23-soul: defensive normalization tests
# ──────────────────────────────────────────────────────────

def test_fallback_never_raises_on_malformed_chapter_scores():
    """chapter_scores can be: None, [], list, str, dict-without-chapters, etc."""
    for bad in (None, [], [1, 2], "garbage", {"chapters": "not-a-dict"},
                {"chapters": None}, 42, {"chapters": [1, 2]}):
        out = _safe_fallback(MILAN_FACTS, bad)  # must not raise
        assert isinstance(out, dict)
        assert len(out["chapters"]) == 7


def test_fallback_never_raises_on_malformed_milan_facts():
    """Numeric coercion + dict guards must absorb any caller weirdness."""
    cases = [
        {},
        None,
        {"total": "22", "max": "36", "p1": "Vikram", "p2": "Sanya"},  # strings
        {"total": None, "max": None, "p1": {"name": None}, "p2": {}},
        {"total": "garbage", "max": "garbage"},
        {"p1": ["Vikram"], "p2": "Sanya"},  # wrong types
        "completely wrong",
        42,
    ]
    for bad in cases:
        out = _safe_fallback(bad, CH_SCORES_FULL)
        assert isinstance(out, dict)
        assert "verdict" in out and "hidden_truth" in out
        assert len(out["chapters"]) == 7
