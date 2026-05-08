"""Tests for the Phase 2.5.11.23 24-page Pro PDF renderer."""
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


def test_pro_pdf_emits_exactly_24_pages_en():
    payload = _milan(); payload["pro_premium"] = _pro()
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert pdf.startswith(b"%PDF-")
    assert _count_pages(pdf) == 24


def test_pro_pdf_emits_exactly_24_pages_with_empty_pro():
    payload = _milan(); payload["pro_premium"] = {}
    pdf = render_milan_pro_pdf(payload, lang="en")
    assert _count_pages(pdf) == 24


def test_pro_pdf_emits_exactly_24_pages_hi_devanagari():
    payload = _milan("Arjun", "Meera", 26); payload["pro_premium"] = _pro(7.2)
    pdf = render_milan_pro_pdf(payload, lang="hi")
    assert _count_pages(pdf) == 24


def test_pro_pdf_never_raises_on_completely_empty_payload():
    pdf = render_milan_pro_pdf({}, lang="en")
    assert _count_pages(pdf) == 24


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
    assert any(s in text for s in (
        "Honest dialogue", "mutual respect", "feel the same things",
        "count on each other", "fight",
    ))
    # Plain-language KP signature reaches P3; jargon must not.
    assert "CSL" not in text
    assert "signifies houses" not in text
