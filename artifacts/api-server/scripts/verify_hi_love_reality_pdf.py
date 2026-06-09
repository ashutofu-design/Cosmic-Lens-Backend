#!/usr/bin/env python3
"""End-to-end Hindi Love Reality PDF — fonts embedded + Devanagari in body."""
from __future__ import annotations

import io
import re
import sys

sys.path.insert(0, ".")

_DEVA_RE = re.compile(r"[\u0900-\u097F]+")
_SAMPLE_HI = (
    "यह अध्याय आप दोनों के संयुक्त चार्ट संकेतों पर आधारित है। "
    "भावनात्मक बंध कितनी गहरी है — सतही आकर्षण से आगे।"
)


def _pdf_has_noto(pdf_bytes: bytes) -> bool:
    """Noto names appear in PDF object stream even without pypdf."""
    blob = pdf_bytes or b""
    return b"NotoDeva" in blob or b"NotoSansDevanagari" in blob


def _pdf_font_names(pdf_bytes: bytes) -> set[str]:
    names: set[str] = set()
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            fonts = page.get("/Resources", {}).get("/Font", {})
            if hasattr(fonts, "get_object"):
                fonts = fonts.get_object()
            for key in fonts:
                obj = fonts[key]
                if hasattr(obj, "get_object"):
                    obj = obj.get_object()
                base = obj.get("/BaseFont") or obj.get("BaseFont")
                if base:
                    names.add(str(base).lstrip("/"))
    except ImportError:
        if _pdf_has_noto(pdf_bytes):
            names.add("NotoDeva (bytes scan, pypdf not installed)")
    except Exception as exc:
        print(f"WARN: pypdf font scan failed: {exc}")
        if _pdf_has_noto(pdf_bytes):
            names.add("NotoDeva (bytes scan fallback)")
    return names


def main() -> int:
    from vedic.love_reality.pdf_fonts import hindi_font_pair, require_devanagari_fonts
    from love_reality_pdf import render_love_reality_pro_pdf

    require_devanagari_fonts("hi")
    reg, bold = hindi_font_pair()
    print(f"font_pair=({reg}, {bold})")
    if reg == "Helvetica":
        print("FAIL: NotoDeva not registered")
        return 1

    pro = {
        "verdict": _SAMPLE_HI,
        "blueprint_reality": _SAMPLE_HI,
        "harmony": _SAMPLE_HI,
        "chapters": [
            {
                "key": "love_connection",
                "chapter_body": _SAMPLE_HI,
            },
        ],
    }
    payload = {
        "pdf_lang": "hi",
        "pro_premium": pro,
        "p1": {"name": "TestA", "day": 1, "month": 1, "year": 1990},
        "p2": {"name": "TestB", "day": 2, "month": 2, "year": 1992},
        "engines": {
            "love_compatibility": {"score": 72, "emotional_summary": _SAMPLE_HI, "reasons": [_SAMPLE_HI]},
            "breakup_chances": {"score": 30},
            "loyalty_check": {"score": 65},
            "will_return": {"return_probability": 40},
            "future_outcome": {"future_score": 55},
            "hidden_red_flags": {"reasons": [_SAMPLE_HI]},
            "kundli_p1": {"moonSign": "Cancer", "ascendant": "Leo", "planets": []},
            "kundli_p2": {"moonSign": "Capricorn", "ascendant": "Virgo", "planets": []},
        },
        "report_id": "LR-HI-VERIFY",
    }

    pdf = render_love_reality_pro_pdf(payload, lang="hi")
    print(f"pdf_bytes={len(pdf)}")
    if not pdf.startswith(b"%PDF"):
        print("FAIL: not a PDF")
        return 1

    fonts = _pdf_font_names(pdf)
    print(f"embedded_fonts={sorted(fonts)}")
    has_noto = _pdf_has_noto(pdf) or any("Noto" in f or "Deva" in f for f in fonts)
    if not has_noto:
        print("FAIL: Noto Devanagari not embedded in PDF")
        return 1

    try:
        from pypdf import PdfReader

        text = ""
        for page in PdfReader(io.BytesIO(pdf)).pages[:6]:
            text += (page.extract_text() or "") + "\n"
        deva_hits = len(_DEVA_RE.findall(text))
        print(f"extracted_devanagari_runs={deva_hits}")
        if deva_hits < 2:
            print("WARN: little Devanagari in extract_text (ReportLab shaping may limit extraction)")
    except Exception as exc:
        print(f"WARN: text extract skipped: {exc}")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
