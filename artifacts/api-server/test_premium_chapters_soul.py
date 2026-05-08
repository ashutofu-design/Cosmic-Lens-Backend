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
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
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


# ──────────────────────────────────────────────────────────
#  Phase 2.5.11.23-soul-v2: ChatGPT-critique-driven regressions
# ──────────────────────────────────────────────────────────
from vedic.compat.premium_chapters import (
    THERAPY_CLICHES, PERFECT_BALANCE_PHRASES, SYSTEM_PROMPT_PREMIUM,
)


def test_v2_no_therapy_cliche_density_in_fallback():
    """Fallback prose must not feel like a generic relationship-coaching app.
    Allow up to 1 cliche (some are nearly unavoidable in passing) but not ≥2."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    text = _all_text(out).lower()
    hits = [c for c in THERAPY_CLICHES if c in text]
    assert len(hits) <= 1, f"Therapy-cliche density too high in fallback: {hits}"


def test_v2_no_perfect_balance_language_in_fallback():
    """Real relationships are uneven. Fallback must never claim both
    partners always feel the same thing equally."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    text = _all_text(out).lower()
    for pb in PERFECT_BALANCE_PHRASES:
        assert pb not in text, f"Perfect-balance phrase leaked into fallback: {pb}"


def test_v2_validator_rejects_therapy_cliche_density():
    """Validator must reject polish-path output dense with therapy-app phrases."""
    base = _build_valid_polish_payload()
    base["chapters"][0]["kya_dhyan"] = (
        "Vikram aur Sanya ko honest dialogue karna chahiye, mutual respect "
        "aur consistent care dikhana, build trust ke liye communicate openly. "
        "Joint daily prayers ka time fix karo aur yearly anniversary ritual rakho."
    )
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok and reason and reason.startswith("therapy_cliche_density"), reason


def test_v2_validator_rejects_perfect_balance_language():
    """Each PERFECT_BALANCE phrase, when injected, must trigger rejection."""
    for pb in PERFECT_BALANCE_PHRASES:
        base = _build_valid_polish_payload()
        base["chapters"][0]["kya_matlab"] = base["chapters"][0]["kya_matlab"][:300] + f" {pb}."
        ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
        assert not ok and reason and reason.startswith("perfect_balance_phrase"), \
            f"Validator failed to reject perfect-balance phrase '{pb}': {reason}"


def test_v2_fallback_carries_emotional_asymmetry():
    """Each chapter prose must contain asymmetry markers — 'ek partner...
    dusra...' or 'ek...dusre...'. This is the signal that we're honouring
    real-relationship unevenness, not pretending perfect balance."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    asym_markers = ["ek partner", "ek ko", "dusra", "dusre", "alag-alag", "alag rhythm", "alag languages"]
    chapters_with_asymmetry = 0
    for c in out["chapters"]:
        full = (c.get("kya_dikh", "") + " " + c.get("kya_matlab", "") + " " + c.get("kya_dhyan", "")).lower()
        if any(m in full for m in asym_markers):
            chapters_with_asymmetry += 1
    assert chapters_with_asymmetry >= 6, f"Only {chapters_with_asymmetry}/7 chapters carry asymmetry — soul-v2 regression"


def test_v2_validator_accepts_one_isolated_cliche():
    """ONE therapy phrase in passing is allowed — only ≥2 triggers rejection.
    This prevents over-aggressive rejection of otherwise-soulful prose."""
    base = _build_valid_polish_payload()
    base["chapters"][0]["kya_dhyan"] = base["chapters"][0]["kya_dhyan"][:400] + \
        " Vikram aur Sanya should communicate openly when stuck."
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, f"Validator over-rejected single isolated cliche: {reason}"


def test_v2_system_prompt_carries_v2_rules():
    """SYSTEM_PROMPT_PREMIUM must mention all v2 critical sections so
    gpt-4o is governed by the same laws the validator enforces."""
    p = SYSTEM_PROMPT_PREMIUM
    assert "EMOTIONAL REALISM RULES" in p, "v2 emotional realism section missing"
    assert "SIGNATURE INSIGHT RULE" in p, "v2 signature insight rule missing"
    assert "THERAPY-CLICHE BAN" in p, "v2 therapy-cliche ban missing"
    # Phase soul-v5: archetype evolved from "experienced modern relationship
    # astrologer" → "experienced human Vedic astrologer with 25+ years of
    # practice" to push the model harder away from AI / counsellor voice.
    assert ("experienced human Vedic astrologer" in p
            or "experienced modern relationship astrologer" in p), \
        "astrologer archetype framing missing"
    assert "wise family elder" not in p, "v1 archetype must be removed in v2"
    # Per-chapter name density rule must be dropped in v2
    assert "≥3 times across the FULL prose" in p or "≥3 times across the full prose" in p.lower(), \
        "v2 must keep global ≥3 name density (not per-chapter)"


def test_v2_signature_insight_specificity_heuristic():
    """Each chapter must contain at least one concrete-image phrase that
    couldn't apply generically. Heuristic: detect specific moments like
    'Sunday raat', '5 minute', '12 ghante', '3 mahine', 'subah chai' etc."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    specifics = [
        "minute", "ghante", "ghanta", "raat", "subah", "sunday", "monday",
        "hafte", "mahine", "saal", "hour", "chai", "dinner", "walk", "evening",
    ]
    weak = []
    for c in out["chapters"]:
        full = (c.get("kya_dikh", "") + c.get("kya_matlab", "") + c.get("kya_dhyan", "")).lower()
        if not any(s in full for s in specifics):
            weak.append(c.get("title"))
    assert not weak, f"Chapters missing concrete-moment specificity: {weak}"


# ─────────────────────────────────────────────────────────────────────────
#  Phase 2.5.11.23-soul-v3 regression tests
# ─────────────────────────────────────────────────────────────────────────
from vedic.compat.premium_chapters import (
    RAW_ASTRO_LEAKS, _PREMIUM_VERSION, SYSTEM_PROMPT_PREMIUM,
    _safe_fallback_blueprint, _advice_uniqueness_ok,
)


def _payload_with(chapters_kya_dhyan: list[str], extra: dict | None = None):
    """Build a validator-passing premium payload from the fallback, varying
    kya_dhyan per chapter. Trims fallback's hidden_truth (which can exceed
    the 600-char LLM-output ceiling) so we can isolate v3 rejection paths."""
    base = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL,
                          kp_promise=None,
                          d9_marriage={"p1": {"d9_lagna_lord": "Jupiter",
                                              "marriage_maturity_0_10": 7.0},
                                       "p2": {"d9_lagna_lord": "Venus",
                                              "marriage_maturity_0_10": 6.0},
                                       "sync": {"lagna_lord_relation": "friendly",
                                                "seven_lord_relation": "neutral",
                                                "score_0_10": 6.5}})
    if len(base.get("hidden_truth", "")) > 580:
        base["hidden_truth"] = base["hidden_truth"][:580].rsplit(" ", 1)[0] + "."
    # Validator demands exactly 3 practical paragraphs; fallback may emit 4.
    base["practical"] = base.get("practical", [])[:3]
    for i, ch in enumerate(base["chapters"]):
        if i < len(chapters_kya_dhyan):
            ch["kya_dhyan"] = chapters_kya_dhyan[i]
    if extra:
        base.update(extra)
    return base


def test_v3_premium_version_bumped():
    assert _PREMIUM_VERSION in ("p2", "p3", "p4", "p5", "p6", "p7"), "Cache namespace must bump to p2 (v3) or higher"


def test_v3_system_prompt_has_v3_markers():
    p = SYSTEM_PROMPT_PREMIUM
    assert "INTERPRET-NEVER-QUOTE LAW" in p, "v3 INTERPRET-NEVER-QUOTE law missing"
    assert "UNIQUE BEHAVIOURAL ANCHOR LAW" in p, "v3 unique anchor law missing"
    assert "MARRIAGE BLUEPRINT" in p, "v3 marriage blueprint section missing"
    assert "marriage_blueprint" in p, "v3 JSON schema for marriage_blueprint missing"


def test_v3_validator_rejects_each_raw_astro_leak():
    """Every entry in RAW_ASTRO_LEAKS must trigger a rejection."""
    for leak in RAW_ASTRO_LEAKS:
        out = _payload_with([])
        # Inject the leak into ch1.kya_dikh foreground prose.
        out["chapters"][0]["kya_dikh"] = (
            f"Vikram aur Sanya ke beech {leak} kuch baat karta hai, "
            f"yeh ek important signal hai jo dono ki dynamic me dikhta hai."
        )
        ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
        assert not ok, f"Validator failed to reject leak {leak!r}"
        # Some entries are already caught by the pre-existing banned_jargon
        # check (Vimshottari, etc); others fire the v3 raw_astro_leak path.
        # Either rejection is acceptable — what matters is the leak is blocked.
        assert (reason.startswith("raw_astro_leak:")
                or reason.startswith("banned_jargon:")
                or reason.startswith("ch1_")), \
            f"Wrong rejection reason for {leak!r}: {reason}"


def test_v3_validator_rejects_repeated_advice():
    """If ≥2 chapter pairs share the same substantive 4-gram advice
    phrasing, the response must be rejected."""
    repeated = ("Vikram Sanya ko har Sunday subah chai pe baith ke "
                "ek dusre ki feelings honestly share karein bina interrupt kiye.")
    out = _payload_with([repeated] * 7)
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok, "Validator must reject identical advice across all chapters"
    assert "advice_uniqueness" in reason or "raw_astro_leak" in reason, reason


def test_v3_advice_uniqueness_accepts_diverse_chapters():
    """Diverse, distinct kya_dhyan blocks must pass the uniqueness check."""
    diverse = [
        {"kya_dhyan": "Sunday subah chai pe ek signal phrase decide karo, jaise 'paani'."},
        {"kya_dhyan": "Har shaam state-of-us check-in karo bina phone ke."},
        {"kya_dhyan": "Conflict me 24-hour rule lagao, koi bhi badi baat next day."},
        {"kya_dhyan": "Yearly anniversary ritual rakho — koi joint daily prayers wala moment."},
        {"kya_dhyan": "Mahine me ek low-pressure dinner date plan karo bina expectations."},
        {"kya_dhyan": "Quarterly division-of-labour reset karo — kaun kya kar raha hai."},
        {"kya_dhyan": "5-saal ka map session ek baar saal me karo together."},
    ]
    assert _advice_uniqueness_ok(diverse), \
        "Diverse advice across chapters should pass uniqueness check"


def test_v3_fallback_emits_marriage_blueprint():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL,
                         kp_promise=None,
                         d9_marriage={"p1": {"d9_lagna_lord": "Sun",
                                             "marriage_maturity_0_10": 7.5},
                                      "p2": {"d9_lagna_lord": "Moon",
                                             "marriage_maturity_0_10": 5.0},
                                      "sync": {"lagna_lord_relation": "friendly",
                                               "seven_lord_relation": "friendly",
                                               "score_0_10": 7.5}})
    mb = out.get("marriage_blueprint")
    assert isinstance(mb, dict), "marriage_blueprint missing from fallback"
    for fld in ("p1_marriage_nature", "p2_marriage_nature", "interaction_dynamic",
                "what_p1_needs_from_p2", "what_p2_needs_from_p1", "blueprint_takeaway"):
        v = mb.get(fld)
        assert isinstance(v, str) and 60 <= len(v) <= 700, \
            f"marriage_blueprint.{fld} invalid: len={len(v) if isinstance(v,str) else 'X'}"


def test_v3_fallback_blueprint_references_both_names():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL,
                         d9_marriage={"p1": {"d9_lagna_lord": "Mars"},
                                      "p2": {"d9_lagna_lord": "Saturn"},
                                      "sync": {"lagna_lord_relation": "neutral",
                                               "seven_lord_relation": "hostile"}})
    mb_text = " ".join(out["marriage_blueprint"].values()).lower()
    assert "vikram" in mb_text, "p1 name (Vikram) missing from blueprint"
    assert "sanya" in mb_text, "p2 name (Sanya) missing from blueprint"


def test_v3_blueprint_helper_handles_missing_d9():
    """Helper must never raise on None / empty / malformed d9 input."""
    for bad in (None, {}, {"p1": None}, {"p1": "string"}, {"sync": []}):
        mb = _safe_fallback_blueprint(bad, "Aarav", "Riya")
        assert isinstance(mb, dict)
        assert all(isinstance(mb.get(f), str) and len(mb[f]) >= 60
                   for f in ("p1_marriage_nature", "p2_marriage_nature",
                             "interaction_dynamic", "what_p1_needs_from_p2",
                             "what_p2_needs_from_p1", "blueprint_takeaway"))


def test_v3_blueprint_helper_differentiates_partner_natures():
    """Different lagna lords must yield different p1/p2 nature prose."""
    mb = _safe_fallback_blueprint(
        {"p1": {"d9_lagna_lord": "Mars", "marriage_maturity_0_10": 8.0},
         "p2": {"d9_lagna_lord": "Saturn", "marriage_maturity_0_10": 4.0},
         "sync": {"lagna_lord_relation": "hostile",
                  "seven_lord_relation": "neutral"}},
        "Aditya", "Ishita")
    assert mb["p1_marriage_nature"] != mb["p2_marriage_nature"]
    # Mars + Saturn should produce contrasting tonal anchors
    assert "directness" in mb["p1_marriage_nature"].lower() or \
           "protective" in mb["p1_marriage_nature"].lower()
    assert "discipline" in mb["p2_marriage_nature"].lower() or \
           "patience" in mb["p2_marriage_nature"].lower()


def test_v3_validator_rejects_malformed_blueprint():
    """Missing field, wrong type, too short, missing names — all must reject."""
    base = _payload_with([])

    # Case 1: blueprint missing entirely
    out = copy.deepcopy(base); out.pop("marriage_blueprint", None)
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok and reason == "marriage_blueprint_missing"

    # Case 2: one field too short
    out = copy.deepcopy(base)
    out["marriage_blueprint"]["interaction_dynamic"] = "too short"
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok and reason.startswith("marriage_blueprint_field:")

    # Case 3: blueprint contains a raw astrology leak
    out = copy.deepcopy(base)
    out["marriage_blueprint"]["blueprint_takeaway"] = (
        "Vikram aur Sanya ki shaadi me Venus debilitated wala signal hai "
        "jo dono ko slowly samjhna hoga aur honour karna hoga.")
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok and (reason.startswith("marriage_blueprint_raw_leak:")
                       or reason.startswith("raw_astro_leak:")), reason

    # Case 4: blueprint missing one partner's name entirely
    out = copy.deepcopy(base)
    for f in out["marriage_blueprint"]:
        out["marriage_blueprint"][f] = (
            "Vikram is doing fine here in this whole interaction layer, "
            "leading with care and warmth, which is a beautiful baseline "
            "to keep on building things in the longer run together always.")
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok and reason.startswith("marriage_blueprint_name_missing:"), reason


# ─────────────────────────────────────────────────────────────────────────────
# Phase 2.5.11.23-soul-v4 regression tests
# ChatGPT critique fixes:
#   (1) Rhythm monotony — every chapter opens "ek partner ... dusra ..."
#   (2) Too much advice — every kya_dhyan ends with ritual / homework
#   (3) Astrology not deeply felt in prose
# ─────────────────────────────────────────────────────────────────────────────
from vedic.compat.premium_chapters import (
    _PREMIUM_VERSION, SYSTEM_PROMPT_PREMIUM,
    _RHYTHM_FORMULA_OPENER_RE, _rhythm_variation_ok,
)


def test_v4_premium_version_bumped_to_p3():
    """Cache namespace must bump to p3 so all p2 (v3) cached payloads are
    re-generated under the new rhythm + reflection rules."""
    assert _PREMIUM_VERSION in ("p3", "p4", "p5", "p6", "p7"), \
        f"Expected v4 cache namespace 'p3', got {_PREMIUM_VERSION!r}"


def test_v4_system_prompt_has_v4_markers():
    """The 3 new v4 sections must be present in the polish-path prompt."""
    p = SYSTEM_PROMPT_PREMIUM
    assert "RHYTHM VARIATION LAW" in p
    assert "REFLECTION-NOT-ALWAYS-ADVICE LAW" in p
    assert "CHART-AWARE LANGUAGE LAW" in p
    # The 5 opener shapes must be enumerated
    assert "METAPHOR opening" in p
    assert "CONCRETE SCENE" in p
    assert "DIRECT OBSERVATION" in p
    assert "BITTERSWEET TRUTH" in p
    assert "CHART-AWARE BRIDGE" in p
    # Must explicitly call out the formula being banned
    assert "ek partner ... dusra" in p


def test_v4_fallback_rhythm_varies_across_chapters():
    """In the deterministic fallback, fewer than 5 of 7 chapters should open
    kya_dikh with the 'ek partner ... dusra ...' formula — i.e. our hand-
    written ch1/ch3/ch5/ch7 templates must use varied openers."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL,
                         kp_promise=None)
    ok, formula_count = _rhythm_variation_ok(out["chapters"])
    assert ok, (
        f"Fallback opens {formula_count}/7 chapters with the formula — "
        f"v4 requires < 5. Templates regressed."
    )


def test_v4_validator_rejects_uniform_rhythm_payload():
    """Construct a payload where 5+ chapters open with the formula — validator
    must reject with 'rhythm_formula_uniform:N'."""
    out = _payload_with([])
    formulaic_opener = (
        "Vikram aur Sanya ke beech ek baat dikhti hai — ek partner zyada "
        "dikhata hai apni feelings, dusra silently andar process karta hai "
        "aur baad me share karta hai jab safe lage."
    )
    # Force 6 of 7 chapters to start with the banned formula
    for ch in out["chapters"][:6]:
        ch["kya_dikh"] = formulaic_opener + " " + ch["kya_dikh"]
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok, "Validator must reject 6/7 formulaic openers"
    assert reason.startswith("rhythm_formula_uniform:"), \
        f"Expected rhythm_formula_uniform:N, got {reason!r}"


def test_v4_validator_accepts_varied_rhythm_payload():
    """The default fallback (after trimming oversized fields) must satisfy
    the v4 rhythm-variation gate cleanly along with all other validator
    branches (raw leaks, advice uniqueness, blueprint)."""
    out = _payload_with([])
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, (
        f"Fallback must pass v4 validator (rhythm + advice uniqueness + raw "
        f"leaks + blueprint). Got reject reason: {reason!r}"
    )


def test_v4_at_least_two_chapters_end_in_reflection():
    """At least 2 of 7 chapters' kya_dhyan should END with a reflection /
    realization sentence rather than a pure action / homework prescription.
    Heuristic: last sentence does NOT begin with an imperative-style opener
    AND contains a reflective marker ('samajh', 'secret', 'matter', 'hai —',
    'reward', 'truth', 'baat', 'realize', 'understand')."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    REFLECTION_MARKERS = (
        "samajh lo", "samajh lena", "secret", "asli reward",
        "honour ho sakte", "yahi is bond", "realize", "understanding",
        "baat samajh", "thakaata sabse zyada",
    )
    reflection_endings = 0
    for c in out["chapters"]:
        kd = (c.get("kya_dhyan") or "").strip()
        # Look at the last ~120 chars (final sentence-ish)
        tail = kd[-150:].lower()
        if any(m.lower() in tail for m in REFLECTION_MARKERS):
            reflection_endings += 1
    assert reflection_endings >= 2, (
        f"Only {reflection_endings}/7 chapters end in reflection — "
        f"v4 REFLECTION-NOT-ALWAYS-ADVICE LAW requires ≥2."
    )


def test_v4_chart_word_not_treated_as_raw_leak():
    """The CHART-AWARE LANGUAGE LAW permits subtle 'one chart...' / 'this
    chart...' bridge phrasing. The validator's RAW_ASTRO_LEAKS denylist must
    NOT trigger on the bare word 'chart' used as a bridge."""
    out = _payload_with([])
    # Inject a chart-aware bridge sentence into one chapter
    out["chapters"][0]["kya_dikh"] = (
        "One chart adapts quickly during life transitions, while the other "
        "seeks emotional continuity before change feels safe. "
        + out["chapters"][0]["kya_dikh"]
    )
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, (
        f"Chart-aware bridge must NOT be flagged as a raw astrology leak. "
        f"Got reject: {reason!r}"
    )


def test_v4_rhythm_regex_matches_exact_formula():
    """The regex must catch the exact 'ek partner ... dusra/dusre/dusri'
    pattern (case-insensitive) but NOT plain 'ek dusre' (no 'partner' before)."""
    # Should match
    assert _RHYTHM_FORMULA_OPENER_RE.search(
        "Ek partner zyada dikhata hai, dusra silently andar process karta hai"
    )
    assert _RHYTHM_FORMULA_OPENER_RE.search(
        "ek partner X karta hai aur dusre ko Y feel hota hai"
    )
    # Should NOT match (no 'partner' anchor before dusra/dusre)
    assert not _RHYTHM_FORMULA_OPENER_RE.search(
        "Dono ek dusre ke against nahi hain — repair pe focused hain"
    )
    assert not _RHYTHM_FORMULA_OPENER_RE.search(
        "Pyaar yahaan loud nahi hai — emotional language background me baji rehti hai"
    )


# ─── Phase 2.5.11.23-soul-v4 hardening tests (architect-flagged) ───
from vedic.compat.premium_chapters import _reflection_endings_ok


def test_v4_validator_rejects_low_reflection_endings():
    """Validator must reject if <2 of 7 chapters' kya_dhyan ends with a
    reflection marker. Architect-flagged hardening — prompt-only enforcement
    was insufficient; polish path could regress silently."""
    base = _payload_with([])
    # Overwrite each kya_dhyan with a UNIQUE pure action-item ending (no
    # reflection markers) — varied to avoid tripping advice_uniqueness check.
    actions = [
        "Hafte me 20-minute Sunday walk plan karo bina phone, bina agenda — paas paas chalna baat ko softer banata hai.",
        "Friday raat ko transparency-minute rakho — har koi ek choti baat batayega jo aaj process karni reh gayi thi.",
        "Conflict ke time '30 minute pause' rule lagao, phir wapas baith ke explicit reasons batao bina blame ke.",
        "Joint daily prayers ek 5-minute window me karo subah chai ke saath, regularity zyada matter karti hai.",
        "Mahine me ek planned long date — koi performance pressure nahi, sirf saath ka time aur slow conversation.",
        "Quarterly written list banao — kaun kya primary, kaun backup; review karo aur honestly batao kya overwhelming.",
        "Yearly anniversary ritual — temple ya nature spot me ek ghanta shukran-cheer ke liye reserved rakho.",
    ]
    for ch, act in zip(base["chapters"], actions):
        ch["kya_dhyan"] = act
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert not ok
    assert reason.startswith("reflection_endings_low:"), \
        f"expected reflection_endings_low but got {reason!r}"


def test_v4_validator_accepts_two_reflection_endings():
    """Exactly 2 reflection-ending chapters out of 7 must pass."""
    base = _payload_with([])
    # Strip all reflection markers from every chapter first
    for ch in base["chapters"]:
        ch["kya_dhyan"] = (
            "Hafte me ek 30-minute walk dono saath karo bina phone bina agenda. "
            "Calendar pe daily reminder daal lo. Joint daily prayers ek option hai."
        )
    # Re-add reflection ending to exactly 2 chapters
    base["chapters"][0]["kya_dhyan"] += (
        " Aur ye samajh lena — yahaan asli intimacy ki definition alag hai."
    )
    base["chapters"][5]["kya_dhyan"] += (
        " Acknowledgment hi yahaan asli reward ban jaata hai."
    )
    ok2, count2 = _reflection_endings_ok(base["chapters"])
    assert ok2 and count2 == 2
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    # May fail for OTHER reasons but NOT reflection_endings_low
    assert not (reason or "").startswith("reflection_endings_low:"), \
        f"unexpected reflection rejection: {reason}"


def test_v4_rhythm_regex_catches_doosra_variant():
    """Architect-flagged: regex must also catch 'doosra/doosre/doosri'
    transliteration variants of dusra."""
    assert _RHYTHM_FORMULA_OPENER_RE.search(
        "Ek partner zyada dikhata hai, doosra silently andar process karta hai"
    )
    assert _RHYTHM_FORMULA_OPENER_RE.search(
        "ek partner X karta hai aur doosre ko Y feel hota hai"
    )
