"""Regression tests for premium soul fallback + technical-only validator shim.

``_validate_premium`` is a dict-type check only; PDF bounds are enforced in
``_sanitize_premium_parsed_dict_in_place`` on the polish path.
"""
import copy

from vedic.compat.premium_chapters import (
    CHAPTER_BODY_KEY,
    CHAPTER_SECTION_KEYS,
    SYSTEM_PROMPT_PREMIUM,
    _PREMIUM_FULL_READ_MAX_CP,
    _PREMIUM_VERSION,
    _RHYTHM_FORMULA_OPENER_RE,
    _finalize_chapter_narrative_for_pdf,
    _parse_premium_llm_json,
    _rhythm_variation_ok,
    _safe_fallback,
    _safe_fallback_blueprint,
    _premium_narrative_word_count,
    _truncate_full_read_to_max_words,
    _validate_premium,
)

BANNED_PHRASES = [
    "engine driver", "engine drivers", "Engine driver", "Engine drivers",
    "engine score", "Based on engine score", "engine signals",
    "No significant friction", "no significant friction",
    "natural baseline compatibility",
    "stable and well within", "drivers indicate practical compatibility",
    "Chapter not generated", "Detailed reading was not generated",
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
        parts += [
            c.get(CHAPTER_BODY_KEY, ""),
            c.get("full_read", ""),
            c.get("grounding", ""),
        ]
        for sk in CHAPTER_SECTION_KEYS:
            parts.append(c.get(sk, ""))
    return " ".join(parts)


def test_finalize_prefers_chapter_body_and_clears_legacy_slots():
    body = "\n\n".join(f"Block {i}. " + ("word " * 18) for i in range(5))
    parsed = {
        "chapters": [
            {
                "key": "ch1",
                CHAPTER_BODY_KEY: body,
                "core_dynamic": "thin legacy slot",
            }
        ]
    }
    _finalize_chapter_narrative_for_pdf(parsed)
    c0 = parsed["chapters"][0]
    assert "Block 0" in c0[CHAPTER_BODY_KEY]
    assert not (c0.get("core_dynamic") or "").strip()


def test_finalize_merges_legacy_slots_when_no_chapter_body():
    parsed = {
        "chapters": [
            {
                "key": "ch1",
                "core_dynamic": "Alpha sentence here.",
                "chart_bridge": "Omega closing here.",
            }
        ]
    }
    _finalize_chapter_narrative_for_pdf(parsed)
    c0 = parsed["chapters"][0]
    assert "Alpha" in c0[CHAPTER_BODY_KEY]
    assert "Omega" in c0[CHAPTER_BODY_KEY]


def test_no_banned_phrases_full_payload():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    text = _all_text(out)
    for phrase in BANNED_PHRASES:
        assert phrase not in text, f"Banned phrase leaked into soul fallback: {phrase!r}"


def test_every_chapter_has_substantive_chapter_body():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    chapters = out["chapters"]
    assert len(chapters) == 7
    for c in chapters:
        v = (c.get(CHAPTER_BODY_KEY) or c.get("full_read") or "").strip()
        wc = len(v.split())
        assert wc >= 40, f"{c['key']}.chapter_body too thin ({wc} words): {v[:120]!r}…"


def test_partner_names_present():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise={"couple_verdict": "STRONG"})
    text = _all_text(out)
    assert text.count("Vikram") >= 2
    assert text.count("Sanya") >= 2


def test_total_score_appears_in_hidden_or_verdict():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    combined = out["hidden_truth"] + " " + out["verdict"]
    assert "22" in combined


def test_high_chapters_drive_special_low_chapters_drive_damage():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    assert len(out["special"]) >= 3
    assert len(out["damage"]) >= 1
    for d in out["damage"]:
        assert "no friction" not in d.lower()
        assert "Vikram" in d or "Sanya" in d


def test_fallback_word_count_sane_without_padding():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL)
    words = len(_all_text(out).split())
    assert words >= 1200, f"Soul fallback unexpectedly thin: {words} words"


def test_validator_accepts_valid_soul_payload():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in out["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = f"Reading anchored to {c['title']}, score band derived from chart."
    out["damage"] = out["damage"][:5]
    out["special"] = out["special"][:3]
    out["practical"] = out["practical"][:3]
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, f"Soul payload should pass premium validator, got: {reason}"


def test_p65_render_wall_does_not_fail_validator():
    """p65-style walls are no longer prose-rejected; PDF path may still wrap."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in out["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = "g"
    out["damage"] = out["damage"][:5]
    out["special"] = out["special"][:3]
    out["practical"] = out["practical"][:3]
    base = (
        "moon venus mars 7th navamsa chart house lord aspect synastry d9 d1 kp nakshatra "
        "money bill chore family inlaw work home kitchen schedule rent parent child "
        "react withdraw silence pace tension conflict emotional hurt resent avoid trigger "
    )
    blob = (base * 30).strip()
    assert "\n\n" not in blob and len(blob) >= 3200, len(blob)
    c0 = out["chapters"][0]
    for sk in CHAPTER_SECTION_KEYS:
        c0[sk] = blob
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_p66_list_blob_does_not_fail_validator():
    """Bullet-heavy sections are not validator-rejected under technical-only mode."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in out["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = "g"
    out["damage"] = out["damage"][:5]
    out["special"] = out["special"][:3]
    out["practical"] = out["practical"][:3]
    bullets = "\n".join(
        f"• moon venus mars navamsa synastry house lord aspect kp chart line {i}" for i in range(10)
    )
    c0 = out["chapters"][0]
    c0["core_dynamic"] = bullets
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_validator_allows_p63_style_trope_span_gpt_first():
    """Cross-chapter trope phrases are not fatal under GPT-first shipping."""
    base = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in base["chapters"]:
        for sk in CHAPTER_SECTION_KEYS:
            c.pop(sk, None)
        fr = (c.get("full_read") or "") + " pace mismatch tail."
        if c["key"] in ("ch4", "ch7"):
            fr = fr.rstrip() + " joint daily prayers"
        c["full_read"] = fr
    base["damage"] = base["damage"][:5]
    base["special"] = base["special"][:3]
    base["practical"] = base["practical"][:3]
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_validate_premium_rejects_non_dict():
    ok, reason = _validate_premium([], MILAN_FACTS, CH_SCORES_FULL)
    assert not ok and reason == "not_dict"


def test_premium_narrative_word_count_includes_blueprint():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    w0 = _premium_narrative_word_count(out)
    mb = dict(out.get("marriage_blueprint") or {})
    mb["blueprint_takeaway"] = (mb.get("blueprint_takeaway") or "") + " " + ("word " * 120)
    out["marriage_blueprint"] = mb
    w1 = _premium_narrative_word_count(out)
    assert w1 >= w0 + 120


def test_validator_accepts_empty_practical_slot():
    base = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    base["practical"] = ["x" * 50, "", "y" * 50]
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_validator_accepts_catastrophic_duplicate_chapter_reads():
    base = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    blob = "Vikram aur Sanya " + ("ke beech yeh chapter ek hi lambi copy-paste body repeat ho rahi hai. " * 80)
    dup = blob[: _PREMIUM_FULL_READ_MAX_CP - 1]
    for c in base["chapters"]:
        for sk in CHAPTER_SECTION_KEYS:
            c.pop(sk, None)
        fr = dup
        if c["key"] in ("ch4", "ch7"):
            fr = fr.rstrip() + " joint daily prayers"
        c["full_read"] = fr
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_validator_accepts_layout_noise_tokens():
    base = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    base["hidden_truth"] = base["hidden_truth"] + " (beat-1.)"
    ok, reason = _validate_premium(base, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_fallback_never_raises_on_malformed_chapter_scores():
    for bad in (None, [], [1, 2], "garbage", {"chapters": "not-a-dict"},
                {"chapters": None}, 42, {"chapters": [1, 2]}):
        out = _safe_fallback(MILAN_FACTS, bad)
        assert isinstance(out, dict)
        assert len(out["chapters"]) == 7


def test_fallback_never_raises_on_malformed_milan_facts():
    cases = [
        {},
        None,
        {"total": "22", "max": "36", "p1": "Vikram", "p2": "Sanya"},
        {"total": None, "max": None, "p1": {"name": None}, "p2": {}},
        {"total": "garbage", "max": "garbage"},
        {"p1": ["Vikram"], "p2": "Sanya"},
        "completely wrong",
        42,
    ]
    for bad in cases:
        out = _safe_fallback(bad, CH_SCORES_FULL)
        assert isinstance(out, dict)
        assert "verdict" in out and "hidden_truth" in out
        assert len(out["chapters"]) == 7


def test_premium_version_is_p79_namespace():
    assert _PREMIUM_VERSION == "p79"


def test_chapter_body_depth_failure_reason_flags_shallow_text():
    from vedic.compat.premium_chapters import _chapter_body_depth_failure_reason

    mf = {"p1": {"name": "Vikram"}, "p2": {"name": "Sanya"}}
    assert _chapter_body_depth_failure_reason("", mf, "en") == "empty"
    assert _chapter_body_depth_failure_reason("Too short.", mf, "en") is not None


def test_chapter_body_depth_failure_reason_accepts_consultation_grade_blob():
    from vedic.compat.premium_chapters import _chapter_body_depth_failure_reason

    mf = {"p1": {"name": "Vikram"}, "p2": {"name": "Sanya"}}
    para = (
        "Vikram's Moon in the fourth house and seventh lord aspects from Saturn in the D1 "
        "map show one nervous system for safety, while Sanya's Venus dignity in the navamsa "
        "feeds marriage timing differently because lord strength is not mirrored between the "
        "two kundlis. This is why weekend repair windows matter for each other in daily married "
        "life together when money and kitchen logistics spike tension at home. "
    )
    body = "\n\n".join([para] * 5)
    assert _chapter_body_depth_failure_reason(body, mf, "en") is None


def test_premium_polish_payload_depth_complete_requires_all_seven_keys():
    from vedic.compat.premium_chapters import (
        CHAPTER_BODY_KEY,
        _premium_polish_payload_depth_complete,
    )

    mf = {"p1": {"name": "Vikram"}, "p2": {"name": "Sanya"}}
    para = (
        "Vikram's chart shows Moon and seventh house lord aspects in D1 while Sanya's "
        "Venus and navamsa story differ because marriage is fed by effort not shortcut, "
        "which means repair after conflict must be behavioural at home together daily for "
        "each other when money and family schedules collide. "
    )
    deep = "\n\n".join([para] * 5)
    chs = [{"key": f"ch{i}", CHAPTER_BODY_KEY: deep} for i in range(1, 8)]
    assert _premium_polish_payload_depth_complete({"chapters": chs}, mf, "en") is True
    chs6 = chs[:6]
    assert _premium_polish_payload_depth_complete({"chapters": chs6}, mf, "en") is False


def test_user_prompt_mentions_pro_pdf_chapter_pages():
    from vedic.compat.premium_chapters import _build_user_prompt

    u = _build_user_prompt(MILAN_FACTS, CH_SCORES_FULL, {}, {}, {}, "en", None)
    assert "Pro PDF layout" in u
    assert "one A4 page" in u


def test_system_prompt_has_contract_headers():
    p = SYSTEM_PROMPT_PREMIUM
    assert "MACHINE CONTRACT" in p
    assert "primary source of truth" in p.lower()
    assert "=== AUTHORING (high intelligence, chart-grounded) ===" in p
    assert "=== LONG-FORM PROSE TARGET" in p
    assert "=== DEPTH & COMPLETENESS (balanced) ===" in p
    assert "=== OUTPUT SHAPE (required JSON) ===" in p
    assert "chapter_body" in p
    assert "Cross-chapter parity" in p
    assert "Pro PDF page fill" in p
    assert "one A4 page" in p
    assert "placeholder ellipses" in p.lower()
    assert "FINAL RULE" not in p
    assert "=== PDF + JSON SAFETY (minimal) ===" in p
    assert "COMPAT_PREMIUM_REMEDY_TAIL_VALIDATE" in p


def test_remedy_tail_not_required_by_default():
    """ch4/ch7 ``chapter_body`` may close naturally without verbatim ALLOWED_REMEDIES suffix."""
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in out["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = "g"
    out["damage"] = out["damage"][:5]
    out["special"] = out["special"][:3]
    out["practical"] = out["practical"][:3]
    organic = (
        "Moon Venus Mars navamsa D9 synastry 7th house lord aspect; continuity strain shows as "
        "timing friction, not moral failure — organic close without verbatim whitelist tail."
    )
    for c in out["chapters"]:
        if c.get("key") in ("ch4", "ch7"):
            base = (c.get(CHAPTER_BODY_KEY) or "").strip()
            c[CHAPTER_BODY_KEY] = (base + "\n\n" + organic).strip()
            c["full_read"] = c[CHAPTER_BODY_KEY]
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_v3_fallback_emits_marriage_blueprint():
    out = _safe_fallback(
        MILAN_FACTS,
        CH_SCORES_FULL,
        kp_promise=None,
        d9_marriage={"p1": {"d9_lagna_lord": "Jupiter", "marriage_maturity_0_10": 7.0},
                     "p2": {"d9_lagna_lord": "Venus", "marriage_maturity_0_10": 6.0},
                     "sync": {"lagna_lord_relation": "friendly",
                              "seven_lord_relation": "neutral",
                              "score_0_10": 6.5}})
    mb = out.get("marriage_blueprint")
    assert isinstance(mb, dict)
    for fld in ("p1_marriage_nature", "p2_marriage_nature", "interaction_dynamic",
                "what_p1_needs_from_p2", "what_p2_needs_from_p1", "blueprint_takeaway"):
        v = mb.get(fld)
        assert isinstance(v, str) and len(v.strip()) >= 40


def test_v3_fallback_blueprint_references_both_names():
    out = _safe_fallback(
        MILAN_FACTS,
        CH_SCORES_FULL,
        d9_marriage={"p1": {"d9_lagna_lord": "Mars"},
                     "p2": {"d9_lagna_lord": "Saturn"},
                     "sync": {"lagna_lord_relation": "neutral",
                              "seven_lord_relation": "hostile"}})
    mb_text = " ".join(out["marriage_blueprint"].values()).lower()
    assert "vikram" in mb_text
    assert "sanya" in mb_text


def test_v3_blueprint_helper_handles_missing_d9():
    for bad in (None, {}, {"p1": None}, {"p1": "string"}, {"sync": []}):
        mb = _safe_fallback_blueprint(bad, "Aarav", "Riya")
        assert isinstance(mb, dict)
        assert all(
            isinstance(mb.get(f), str) and len((mb.get(f) or "").strip()) >= 40
            for f in ("p1_marriage_nature", "p2_marriage_nature", "interaction_dynamic",
                      "what_p1_needs_from_p2", "what_p2_needs_from_p1", "blueprint_takeaway")
        )


def test_validator_accepts_malformed_blueprint_dict():
    base = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in base["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = "x"
    base["damage"] = base["damage"][:5]
    base["special"] = base["special"][:3]
    base["practical"] = base["practical"][:3]

    out = copy.deepcopy(base)
    out.pop("marriage_blueprint", None)
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason

    out = copy.deepcopy(base)
    out["marriage_blueprint"]["interaction_dynamic"] = ""
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, reason


def test_v3_validator_allows_chart_technical_language():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    for c in out["chapters"]:
        if not c.get("grounding"):
            c["grounding"] = "g"
    out["damage"] = out["damage"][:5]
    out["special"] = out["special"][:3]
    out["practical"] = out["practical"][:3]
    base_txt = out["chapters"][0]["core_dynamic"]
    out["chapters"][0]["core_dynamic"] = (
        base_txt + " "
        "Vikram aur Sanya ke beech 7th house axis par Saturn ka slow guard dikhta hai; "
        "D9 me marriage maturity alag hai — yeh timing mismatch ka chart-backed reason hai."
    )
    ok, reason = _validate_premium(out, MILAN_FACTS, CH_SCORES_FULL)
    assert ok, f"Expected chart-technical prose to pass: {reason}"


def test_fallback_rhythm_varies_across_chapters():
    out = _safe_fallback(MILAN_FACTS, CH_SCORES_FULL, kp_promise=None)
    ok, formula_count = _rhythm_variation_ok(out["chapters"])
    assert ok, f"Fallback opens {formula_count}/7 chapters with formula opener"


def test_truncate_full_read_respects_max_words():
    s = "word " * 2000
    cap = 1500
    t = _truncate_full_read_to_max_words(s, cap)
    assert len(t.split()) <= cap


def test_parse_premium_llm_json_markdown_fence_native_script():
    raw = '```json\n{"hidden_truth":"ଅ","chapters":[]}\n```'
    obj, err = _parse_premium_llm_json(raw)
    assert err is None and obj is not None and obj["hidden_truth"] == "ଅ"


def test_parse_premium_llm_json_embedded_object_with_trailing_noise():
    raw = 'Sure:\n{"hidden_truth":"x","chapters":[]}\ntrailing noise'
    obj, err = _parse_premium_llm_json(raw)
    assert err is None and obj is not None and obj["hidden_truth"] == "x"


def test_parse_premium_llm_json_braces_inside_escaped_string():
    raw = r'{"hidden_truth":"a \"quote\" { ok","chapters":[]}'
    obj, err = _parse_premium_llm_json(raw)
    assert err is None and obj is not None and obj["hidden_truth"] == r'a "quote" { ok'


def test_parse_premium_llm_json_unterminated_string_returns_none():
    raw = '{"hidden_truth":"broken'
    obj, err = _parse_premium_llm_json(raw)
    assert obj is None and err is not None


def test_rhythm_regex_matches_doosra_variant():
    assert _RHYTHM_FORMULA_OPENER_RE.search(
        "Ek partner zyada dikhata hai, doosra silently andar process karta hai"
    )
