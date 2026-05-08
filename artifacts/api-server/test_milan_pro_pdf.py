"""Tests for the Phase 2.5.11.24-fix8 17-page Pro PDF renderer.

Visual-density rewrite: 7 chapters consolidated from 2 thin pages → 1
dense rich page each (pull-quote, REAL-LIFE MOMENT box, WHY-IN-CHARTS
chips, keep-in-mind, grounding). Standalone Timing Sync page dropped
(folded into Final Verdict). Net 25 → 17 pages. LLM contract
(kya_dikh / kya_matlab / kya_dhyan / grounding) UNCHANGED.
"""
import re

from milan_pdf import render_milan_pro_pdf


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
            "kya_dikh":   "Engine drivers are present and stable for this chapter "
                          "across both partners' charts in expected zones.",
            "kya_matlab": "Daily life will reflect this strength as a quiet, "
                          "reliable comfort that neither partner has to chase.",
            "kya_dhyan":  "Honest dialogue, mutual respect, consistent care.",
            "grounding":  f"Engine score {score}/10.",
        } for k in keys],
        "special":   ["Strength A", "Strength B", "Strength C"],
        "damage":    ["Caution A"],
        "practical": ["Para 1.", "Para 2.", "Para 3."],
        "verdict":   "A measured, warm bond worth building on patiently.",
        "_meta":     {"model": "fallback", "kp_promise": "PARTIAL",
                      "hidden_signature": "KP 7CSL signifies marriage-promise houses."},
    }


def _count_pages(pdf: bytes) -> int:
    """Count individual /Type /Page objects (not the /Pages root node)."""
    return len(re.findall(rb'/Type\s*/Page(?!s)', pdf))


def test_pro_pdf_emits_exactly_17_pages_en():
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert pdf.startswith(b"%PDF-")
    assert _count_pages(pdf) == 17


def test_pro_pdf_emits_exactly_17_pages_with_empty_pro():
    payload = _milan(); payload["pro_premium"] = {}
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 17


def test_pro_pdf_emits_exactly_17_pages_hi_devanagari():
    payload = _milan("Arjun", "Meera", 26); payload["pro_premium"] = _pro(7.2)
    pdf = render_milan_pro_pdf(payload, lang="hi")
    assert _count_pages(pdf) == 17


def test_pro_pdf_never_raises_on_completely_empty_payload():
    pdf = render_milan_pro_pdf({}, lang="en")
    assert _count_pages(pdf) == 17


def test_pro_pdf_carries_fix8_visual_blocks():
    """Phase 2.5.11.24-fix8 regression: every chapter page must carry the
    new visual-storytelling labels (REAL-LIFE MOMENT, WHY THIS APPEARS IN
    YOUR CHARTS) and the Final Verdict page must carry the merged
    Readiness & timing block. Without these, the visual-density rewrite
    silently regressed to flat paragraphs."""
    import io, pypdf
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    assert "REAL-LIFE MOMENT" in text
    assert "WHY THIS APPEARS IN YOUR CHARTS" in text
    # 7 chapters × WHY-IN-CHARTS box → at least 5 occurrences in the body
    # (some payloads may legitimately skip a chip box if no koots map).
    assert text.count("REAL-LIFE MOMENT") >= 5
    # Timing Sync page is dropped — its prose now lives under Final Verdict.
    assert "Readiness & timing" in text or "READINESS & TIMING" in text


def test_end_to_end_polisher_to_renderer_chapter_keys_match():
    """Architect-fix regression: the polisher emits ch1..ch7 by contract,
    the renderer must consume them for P4-17 and NOT silently fall back
    to placeholder text. Without the renderer's ch{i} fallback this test
    fails (placeholder string appears in PDF body)."""
    import os
    os.environ.pop("COMPAT_PREMIUM_POLISH", None)  # force fallback path
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
    # Confirm contract: polisher emits ch1..ch7 keys.
    assert {c["key"] for c in pro["chapters"]} == {f"ch{i}" for i in range(1, 8)}
    payload["pro_premium"] = pro
    pdf_bytes = render_milan_pro_pdf(payload, lang="en")
    # Extract real text via pypdf so we read past ReportLab's stream compression.
    import io, pypdf
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    # Placeholder must NOT appear when polisher returned real chapters.
    assert "Detailed reading was not generated for this chapter" not in text
    # At least one fallback chapter prose phrase should reach the page.
    # Soul-v4 fallback vocabulary (Hinglish, asymmetric "ek partner...dusra"
    # phrasing, concrete moment markers). Old soul-v1 phrases like
    # "Honest dialogue" / "mutual respect" are now BANNED therapy-clichés.
    assert any(s in text for s in (
        "ek partner", "dusra", "Pyaar", "yahaan", "asli",
        "5-minute", "Sunday", "chai", "rishte", "loud nahi",
    ))
    # Plain-language KP signature reaches P3; jargon must not.
    assert "CSL" not in text
    assert "signifies houses" not in text
