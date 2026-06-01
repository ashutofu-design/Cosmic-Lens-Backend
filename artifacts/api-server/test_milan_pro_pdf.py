"""Tests for the 18-page Pro PDF renderer.

Premium chapter pages use **p64** structured subsections when the payload
includes the seven section fields; legacy payloads still render as one
flowing body. Astrology data tables remain where structurally necessary.
"""
import re

from milan_pdf import render_milan_pro_pdf


def test_premium_chapter_dense_segments_splits_for_vertical_rhythm():
    """Short single-blob chapter_body re-chunks into more PDF rows (no invented words)."""
    from milan_pdf import _premium_chapter_dense_segments

    blob = ("Same sentence repeated for length. " * 90).strip()
    segs = _premium_chapter_dense_segments(blob)
    assert len(segs) >= 4
    joined = "\n\n".join(segs)
    assert "Same sentence" in joined


def test_premium_prose_markup_escapes_then_paragraph_breaks():
    from milan_pdf import _premium_prose_markup

    s = "Line A\nLine B\n\nSecond para"
    m = _premium_prose_markup(s)
    assert "<br/><br/>" in m
    assert "<br/>" in m
    assert "&lt;" in _premium_prose_markup("x < y")
    assert "Line A" in m


def test_noto_font_search_includes_bundled_repo_dir():
    """Bundled fonts/noto must be on the search path for Windows deployments."""
    from milan_pdf import _bundled_noto_font_dir, _collect_noto_search_dirs

    bundled = _bundled_noto_font_dir()
    assert bundled in _collect_noto_search_dirs()


def _milan(p1n="A", p2n="B", total=33):
    return {
        "p1": {"name": p1n, "nakshatra": "Ashwini",
               "rashi": "Aries", "manglik": False},
        "p2": {"name": p2n, "nakshatra": "Pushya",
               "rashi": "Cancer", "manglik": False},
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
        "total": total, "max": 36, "manglik_dosh": False,
        "grade": {"label": "Excellent", "color": "#047857"},
    }


def _pro(score=8.0):
    keys = ["emotional_compatibility", "trust_loyalty",
            "communication_conflict", "marriage_stability",
            "physical_chemistry", "family_practical", "future_direction"]
    return {
        "hidden_truth": "A grounded bond carrying genuine compatibility.",
        "chapters": [{
            "key": k, "title": k.replace("_", " ").title(),
            "score_0_10": score,
            "chapter_body": (
                "Engine drivers are present and stable for this chapter "
                "across both partners' charts in expected zones. "
                "Daily life will reflect this strength as a quiet, "
                "reliable comfort that neither partner has to chase. "
                "Honest dialogue, mutual respect, consistent care."
            ),
            "full_read": (
                "Engine drivers are present and stable for this chapter "
                "across both partners' charts in expected zones. "
                "Daily life will reflect this strength as a quiet, "
                "reliable comfort that neither partner has to chase. "
                "Honest dialogue, mutual respect, consistent care."
            ),
            "grounding":  f"Engine score {score}/10.",
        } for k in keys],
        "special":   ["Strength A", "Strength B", "Strength C"],
        "damage":    ["Caution A", "Caution B"],
        "practical": ["Para 1.", "Para 2.", "Para 3."],
        "verdict":   "A measured, warm bond worth building on patiently.",
        "_meta":     {"model": "fallback", "kp_promise": "PARTIAL",
                      "hidden_signature": "KP 7CSL signifies marriage-promise houses."},
    }


def _count_pages(pdf: bytes) -> int:
    """Count individual /Type /Page objects (not the /Pages root node)."""
    return len(re.findall(rb'/Type\s*/Page(?!s)', pdf))


def test_pro_pdf_emits_exactly_21_pages_en():
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert pdf.startswith(b"%PDF-")
    assert _count_pages(pdf) == 21


def test_pro_pdf_sdp_consultation_multi_paragraph_smoke():
    """Premium ``special`` / ``damage`` / ``practical`` may use ``\\n\\n``; renderer stacks paragraphs."""
    payload = _milan()
    pro = _pro()
    para = (
        "Venus and seventh-house combinations in both kundlis show warmth that is "
        "earned through effort, not instant fusion.\n\n"
        "A navigates closeness through Moon-ruled domestic cues while B balances "
        "harmony with quiet boundaries — same bond, different repair scripts.\n\n"
        "In marriage this becomes timing: cooling hours versus same-evening debriefs, "
        "because chart-led defences differ for each map — lord aspects tie back to how "
        "money talks and in-law weekends actually feel at home."
    )
    pro["special"] = [para, para, para]
    pro["damage"] = [para, para]
    pro["practical"] = [para, para, para]
    payload["pro_premium"] = pro
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert pdf.startswith(b"%PDF-")
    assert _count_pages(pdf) >= 21


def test_pro_pdf_emits_exactly_21_pages_with_empty_pro():
    payload = _milan(); payload["pro_premium"] = {}
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 21


def test_pro_pdf_emits_exactly_21_pages_hi_devanagari():
    payload = _milan("Arjun", "Meera", 26); payload["pro_premium"] = _pro(7.2)
    pdf = render_milan_pro_pdf(payload, lang="hi")
    assert _count_pages(pdf) == 21


def test_pro_pdf_never_raises_on_completely_empty_payload():
    pdf = render_milan_pro_pdf({}, lang="en")
    assert _count_pages(pdf) == 21


def test_pro_pdf_chapter_pages_are_flowing_observation_not_segmented_ui():
    """Premium chapter pages must not reintroduce fix8 segmentation UI."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    _tu = text.upper()
    assert "DAY-TO-DAY ATMOSPHERE" not in text
    assert "QUIET EMOTIONAL READ" not in _tu
    assert "THE LONGER ARC" not in _tu
    assert "CLASSICAL MATCH NOTES (REFERENCE)" not in text
    # Chapter chrome + merged body still present (first map title).
    assert "EMOTIONAL COMPATIBILITY" in _tu
    # Timing context remains but must not appear as a labeled subsection.
    assert "READINESS & TIMING" not in _tu


def test_pro_pdf_chapter_body_renders_long_narrative_without_subsection_headings():
    """Premium chapter pages render ``chapter_body`` as one narrative — no seven slot headings."""
    import io, pypdf

    body = (
        "Chart read: Moon Venus Mars Jupiter Saturn Rahu Ketu D1 D9 navamsa synastry "
        "7th house lord nakshatra behaviour friction repair timing. "
    )
    pro = _pro(8.0)
    para = (body * 10).strip()
    for c in pro["chapters"]:
        c["chapter_body"] = "\n\n".join([para, para, para, para])
        c["full_read"] = c["chapter_body"]
        c["grounding"] = (
            "Grounding: 7th lord + Venus tone cross-read from structured chart JSON — "
            "behaviour-first, not a score paraphrase. "
            "Observational tail stays compact: this line is the remainder for the bottom card."
        )
    payload = _milan()
    payload["pro_premium"] = pro
    pdf = render_milan_pro_pdf(payload, lang="en")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert "Core Dynamic" not in text
    assert "Chart Bridge" not in text
    assert "Chart read" in text or "Moon Venus Mars" in text
    assert "Chart insight" in text
    assert "Observational notes" in text


def test_pro_pdf_unknown_koot_keys_must_not_crash():
    """Architect-flagged fix9 regression: payload with unknown koot
    canonical keys must not raise (previous bug: _derive_attraction_line
    indexed empty list when no koot key resolved into the curated map)."""
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["koots"] = [
        {"key": "foo_unknown", "score": 5, "max": 6},
        {"key": "bar_unknown", "score": 4, "max": 7},
        {"key": "baz_unknown", "score": 0, "max": 8},
    ]
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 21


def test_pro_pdf_non_latin_lang_keeps_latin_chip_text_readable():
    """Architect-flagged fix9 regression: Latin-only deterministic
    blocks (Hidden Truth / attraction / verdict) must use body_latin font
    even in non-Latin lang reports — otherwise the script font drops Latin glyphs."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="bn")
    assert _count_pages(pdf) == 21
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    # Snapshot page uses Latin eyebrow — must stay readable in non-Latin PDF font lane.
    assert "SNAPSHOT" in text.upper() or "CHAPTER 02" in text.upper()


def test_pro_pdf_carries_fix10_blueprint_depth_blocks():
    """Phase 2.5.11.24-fix10 regression: Marriage Blueprint must carry
    the 4 deterministic D1+D9 depth blocks (7th-lord meaning, affection
    style, conflict instinct, daily emotional rhythm). p64 may restore
    chapter grounding cards when `grounding` is present. The verdict closer
    must use the sharper Hinglish phrasing — together these address the
    critique that the blueprint was 'gold but too short' and chapter
    even-pages looked empty."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["d9_marriage"] = {
        "p1": {"d9_lagna_lord": "Mars",  "marriage_maturity_0_10": 6},
        "p2": {"d9_lagna_lord": "Venus", "marriage_maturity_0_10": 7},
        "sync": {"lagna_lord_relation": "friend",
                 "seven_lord_relation": "neutral"},
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    # 4 new depth labels.
    assert "DEEPER MARRIAGE LAYER" in text
    assert "What marriage means to" in text
    assert "How affection actually shows up" in text
    assert "How conflict actually plays out" in text
    assert "daily emotional rhythm" in text
    # 7th-lord translation surfaces (soul-v6 Hinglish maps).
    assert "lade jaane ka jazba" in text       # Mars → "...jiske liye lade jaane ka jazba"
    assert "private sanctuary" in text          # Venus → "ek private sanctuary..."
    # Friend relation translates to the repair-within-48h line.
    assert "repair within 24-48 hours" in text
    # Sharper Hinglish closer (any band variant).
    assert any(p in text for p in [
        "Is shaadi ki strength", "Yeh shaadi isliye",
        "Yeh bond tab tikega",   "Yeh shaadi tab gehri",
    ])


def test_pro_pdf_blueprint_uses_7th_lord_not_lagna_lord_for_marriage_meaning():
    """Phase 2.5.11.24-fix10 architect-flagged correctness regression:
    'What marriage means to X' MUST be keyed by `d9_7h_lord` (7th-lord),
    NOT `d9_lagna_lord`. Previous version incorrectly used lagna lord
    for both the affection block and the marriage-meaning block."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    # 7th lord = Saturn (long-horizon construction project), lagna lord =
    # Mars (direct, protective intensity affection). The two MUST surface
    # on different blocks — proves correct field separation.
    payload["d9_marriage"] = {
        "p1": {"d9_lagna_lord": "Mars",  "d9_7h_lord": "Saturn",
               "marriage_maturity_0_10": 6},
        "p2": {"d9_lagna_lord": "Venus", "d9_7h_lord": "Mercury",
               "marriage_maturity_0_10": 6},
        "sync": {"lagna_lord_relation": "neutral",
                 "seven_lord_relation": "neutral"},
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    # Marriage-meaning block (driven by d9_7h_lord = Saturn / Mercury) —
    # soul-v6 Hinglish maps.
    assert "lambi-chodi imaarat banane jaisi" in text       # Saturn marriage
    assert "lambi, kabhi khatam na hone wali baatcheet" in text  # Mercury marriage
    # Affection block (driven by d9_lagna_lord = Mars / Venus) still works.
    assert "seedha, protective intensity" in text   # Mars affection
    assert "narm, sundar warmth" in text            # Venus affection


def test_pro_pdf_blueprint_handles_malformed_nested_d9_marriage():
    """Phase 2.5.11.24-fix10 architect-flagged robustness regression:
    `d9_marriage` may arrive with non-dict nested values (lists, strings,
    numbers) from a malformed payload — renderer must NEVER crash."""
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["d9_marriage"] = {
        "p1": [1, 2, 3],          # list, not dict
        "p2": "broken",           # string, not dict
        "sync": 42,               # int, not dict
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 21


def test_pro_pdf_blueprint_accepts_engine_native_relation_friendly():
    """Phase 2.5.11.24-fix10 architect-flagged regression: the engine
    `compute_d9_marriage` emits `lagna_lord_relation='friendly'` (not
    `friend`) — the conflict-instinct block must recognise that variant
    and emit the repair-within-48h line, not the neutral fallback."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["d9_marriage"] = {
        "p1": {"d9_lagna_lord": "Jupiter", "marriage_maturity_0_10": 6},
        "p2": {"d9_lagna_lord": "Moon",    "marriage_maturity_0_10": 6},
        "sync": {"lagna_lord_relation": "Friendly",  # engine variant + caps
                 "seven_lord_relation": "neutral"},
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    assert "repair within 24-48 hours" in text


def test_pro_pdf_blueprint_depth_uses_astrologer_voice_soul_v5():
    """Phase 2.5.11.24-soul-v5 regression: the deterministic blueprint
    depth blocks (which fire whenever the LLM polish doesn't write them)
    MUST read in human astrologer-notes voice — first-person, hesitant,
    lived-practice anchored — NOT in AI / audit-report tone. User-flagged:
    'PDF padhne ke baad real astrologer ne likha lagna chahiye'."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["d9_marriage"] = {
        "p1": {"d9_lagna_lord": "Mars",  "d9_7h_lord": "Saturn",
               "marriage_maturity_0_10": 6},
        "p2": {"d9_lagna_lord": "Venus", "d9_7h_lord": "Mercury",
               "marriage_maturity_0_10": 6},
        "sync": {"lagna_lord_relation": "friendly",
                 "seven_lord_relation": "neutral"},
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages).lower()
    # Astrologer-voice markers MUST appear at least 3 times across
    # the 4 deterministic depth blocks (one per block ideally).
    voice_markers = [
        "maine",                    # first-person (Hinglish)
        "meri practice",            # lived-practice anchor
        "believe me",               # human aside
        "honestly bol",             # direct astrologer voice
        "main yeh",                 # first-person stem
        "kayi aise",                # "many such" — pattern recognition
        "is jodi me",               # direct address to the couple
    ]
    hits = sum(1 for m in voice_markers if m in text)
    assert hits >= 3, f"Astrologer voice too thin: only {hits} markers found"
    # AI-tell phrases MUST be absent from deterministic depth prose.
    for ai_tell in ["The chart shows", "Analysis reveals",
                    "It is observed that", "Studies show",
                    "data indicates"]:
        assert ai_tell not in text, f"AI-tell leaked: {ai_tell!r}"


def test_premium_prompt_carries_astrologer_voice_law_soul_v5():
    """p79: chapter_body primary narrative; PDF is single-flow."""
    from vedic.compat.premium_chapters import (
        SYSTEM_PROMPT_PREMIUM,
        _PREMIUM_VERSION,
        build_premium_system_prompt,
        build_premium_regen_chapter_system_prompt,
    )
    assert _PREMIUM_VERSION == "p79"
    assert "PREMIUM PDF — MACHINE CONTRACT" in SYSTEM_PROMPT_PREMIUM
    assert "AUTHORING (high intelligence, chart-grounded)" in SYSTEM_PROMPT_PREMIUM
    assert "CONSULTATION VOICE — LIVED MARRIAGE" in SYSTEM_PROMPT_PREMIUM
    assert "marriage_blueprint" in SYSTEM_PROMPT_PREMIUM
    assert "chapter_body" in SYSTEM_PROMPT_PREMIUM
    assert "LANGUAGE LOCK" in SYSTEM_PROMPT_PREMIUM
    assert "CROSS-LANE NARRATIVE QUALITY" in SYSTEM_PROMPT_PREMIUM

    ph_hn = build_premium_system_prompt("hn")
    assert "LANGUAGE=hn" in ph_hn
    assert "Hinglish" in ph_hn or "hinglish" in ph_hn.lower()

    ph_hi = build_premium_system_prompt("hi")
    assert "LANGUAGE=hi" in ph_hi
    assert "देवनागरी" in ph_hi

    # Pro PDF lane only supports en | hn | hi; other codes coerce to English.
    assert build_premium_system_prompt("bn") == build_premium_system_prompt("en")
    assert len(build_premium_regen_chapter_system_prompt("en")) < len(SYSTEM_PROMPT_PREMIUM)


def test_pro_pdf_chapter_grounding_card_restored_p64():
    """p64: chapter pages show grounding bridge again when `grounding` is set."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert text.count("Why we say this") + text.count("Observational notes") >= 7


def test_pro_pdf_carries_fix9_depth_blocks():
    """Phase 2.5.11.24-fix9 regression: report must carry dedicated koot decode
    page, quiet-patterns callout, attraction + core-challenge page, and
    the verdict closer. (Methodology checklist page removed.)"""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert "What shaped this reading" not in text
    assert "UNDER THE HOOD (BRIEF)" not in text
    # Koot scores still decoded on their own page (not inside chapter prose).
    assert "Compatibility Numbers Decoded" in text
    # Hidden Truth page still carries extra realism lines (no boxed label).
    assert "WHAT'S HIDDEN UNDERNEATH" in text or "WHATS HIDDEN UNDERNEATH" in text.upper()
    # Attraction + Core Challenge page remains, but without report-style labels.
    assert "WHAT DRAWS YOU" in text
    # Verdict closer — observational band-keyed prose (ratio tiers).
    assert ("meri practice" in text.lower() or
            "silent resentment" in text.lower() or
            "uneven rhythm" in text.lower() or
            "avoidance" in text.lower())


def test_end_to_end_polisher_to_renderer_chapter_keys_match():
    """Architect-fix regression: the polisher emits ch1..ch7 by contract,
    the renderer must consume them for the seven-chapter band (P4–P10
    after cover/snapshot/hidden-truth) and NOT silently fall back
    to placeholder text. Without the renderer's ch{i} fallback this test
    fails (placeholder string appears in PDF body)."""
    import os
    os.environ.pop("COMPAT_PREMIUM_POLISH", None)  # polish off → empty shell + PDF placeholders
    from vedic.compat.d9_marriage import compute_d9_marriage
    from vedic.compat.synastry_7l import compute_synastry_7l
    from vedic.compat.kp_marriage_promise import compute_kp_couple_promise
    from vedic.compat.chapter_scores import compute_chapter_scores
    from vedic.compat.premium_chapters import polish_premium_chapters

    k = {"ascendant": "Leo", "ascendantLongitude": 130.0,
         "planets": [{"name": "Venus", "sign": "Taurus", "longitude": 45.0},
                     {"name": "Jupiter", "sign": "Sagittarius",
                      "longitude": 255.0}]}
    payload = _milan()
    cs  = compute_chapter_scores(payload, {}, {}, {})
    pro = polish_premium_chapters(
        payload, cs,
        compute_d9_marriage(k, k),
        compute_synastry_7l(k, k),
        compute_kp_couple_promise(k, k),
        lang="en",
    )
    # Polish off: polisher returns an empty shell; renderer uses milan_pdf placeholders.
    assert pro["chapters"] == []
    assert (pro.get("_meta") or {}).get("openai_skipped") is True
    payload["pro_premium"] = pro
    pdf_bytes = render_milan_pro_pdf(payload, lang="en")
    # Extract real text via pypdf so we read past ReportLab's stream compression.
    import io, pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert "Detailed reading was not generated for this chapter" not in text
    assert "Yahan chart me signal medium range me pada hai" in text
    # Plain-language KP signature reaches Hidden Truth page; jargon must not.
    assert "CSL" not in text
    assert "signifies houses" not in text


# ── Phase 2.5.11.24-soul-v6 regressions ───────────────────────────────

def test_pro_pdf_has_no_d1_d9_chart_insert_page():
    """Standalone Rāśi/Navāmśa diamond chart page was removed — PDF must not carry CHARTS chapter."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["kundli_p1"] = {
        "name": "Vikram", "ascendant": "Cancer",
        "planets": [{"name": "Sun", "sign": "Taurus"}],
    }
    payload["kundli_p2"] = {
        "name": "Sanya", "ascendant": "Libra",
        "planets": [{"name": "Venus", "sign": "Libra"}],
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 21
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    tu = text.upper()
    assert "CHARTS" not in tu
    assert "NORTH INDIAN" not in tu
    assert "WHAT'S HIDDEN UNDERNEATH" in tu or "WHATS HIDDEN UNDERNEATH" in tu.replace("'", "")


def test_pro_pdf_renders_without_kundli_payload_no_crash():
    """Renderer must not require kundli_p1 / kundli_p2 (chart page removed)."""
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 21


def test_pro_pdf_carries_koot_action_strip_for_weak_koots_soul_v6():
    """soul-v6: weak koots (score/max < 0.5) must each surface a
    practical 1-line action below the koot decoded table."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    # Override koots so a couple are weak — should trigger action lines.
    payload["koots"] = [
        {"label": "Bhakoot", "score": 0, "max": 7},   # weak → trigger
        {"label": "Nadi",    "score": 0, "max": 8},   # weak → trigger
        {"label": "Gana",    "score": 6, "max": 6},   # strong → silent
        {"label": "Yoni",    "score": 1, "max": 4},   # weak → trigger
    ]
    pdf = render_milan_pro_pdf(payload, lang="en")
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    assert "WEAK SPOTS" in text and "PRACTICAL" in text
    # Bhakoot weak → 5-year-goals action line.
    assert "agle 5 saal ke 3 specific goals" in text
    # Nadi weak → morning rituals action line.
    assert "Subah" in text and "rituals" in text
    # Yoni weak → pressure-free closeness line.
    assert "Pressure-free physical closeness" in text


def test_pro_pdf_drops_dikhata_dikhati_slash_hack_soul_v6():
    """soul-v6: the awkward 'dikhata/dikhati' gender-slash hack from
    the affection block has been replaced with a gender-neutral phrasing
    'ka pyaar aata hai ... ke roop me'. The slash form must NOT appear
    anywhere in the rendered PDF."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    payload["d9_marriage"] = {
        "p1": {"d9_lagna_lord": "Mars",  "d9_7h_lord": "Saturn",
               "marriage_maturity_0_10": 6},
        "p2": {"d9_lagna_lord": "Venus", "d9_7h_lord": "Mercury",
               "marriage_maturity_0_10": 6},
        "sync": {"lagna_lord_relation": "neutral",
                 "seven_lord_relation": "neutral"},
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    assert "dikhata/dikhati" not in text
    # New gender-neutral phrasing must surface.
    assert "ka pyaar aata hai" in text
    assert "ke roop me" in text


def test_pro_pdf_planet_meaning_maps_are_hinglish_soul_v6():
    """soul-v6: planet maps were rewritten English → Hinglish so the
    deterministic depth blocks read like a real human astrologer's
    notes instead of code-mixed 'AI translator' output."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    # Cover all 9 planets across both partners' 7th-lord + lagna-lord.
    payload["d9_marriage"] = {
        "p1": {"d9_lagna_lord": "Jupiter", "d9_7h_lord": "Moon",
               "marriage_maturity_0_10": 6},
        "p2": {"d9_lagna_lord": "Saturn",  "d9_7h_lord": "Sun",
               "marriage_maturity_0_10": 6},
        "sync": {"lagna_lord_relation": "neutral",
                 "seven_lord_relation": "neutral"},
    }
    pdf = render_milan_pro_pdf(payload, lang="en")
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    # Marriage meaning — Moon → "emotional ghar"; Sun → "identity-anchor".
    # PDF text extraction can split "ek " across line boundaries; assert
    # only the distinctive Hinglish noun phrase.
    assert "emotional ghar" in text
    assert "identity-anchor" in text
    # Affection — Jupiter → "udaar, bada-dil"; Saturn → "shaant bharosa".
    assert "udaar, bada-dil" in text
    assert "shaant bharosa-driven" in text


def test_pro_pdf_lang_hn_chrome_is_roman_hindi_not_english_template():
    """``lang=hn`` must swap deterministic PDF chrome (not LLM chapter bodies)."""
    import io

    import pypdf

    payload = _milan()
    payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="hn")
    assert pdf.startswith(b"%PDF-")
    assert _count_pages(pdf) == 21
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
    assert "ADHYAY" in text
    assert "Prishth" in text
    assert "Final Verdict" not in text
    assert "Relationship Snapshot" not in text
    assert "CHAPTER " not in text
    assert "This bond forms" not in text
    assert "The single thing most likely" not in text
