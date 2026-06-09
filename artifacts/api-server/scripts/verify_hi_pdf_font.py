#!/usr/bin/env python3
"""Quick check: Noto Devanagari registered + sample Hindi PDF bytes."""
from __future__ import annotations

import io
import sys

sys.path.insert(0, ".")


def main() -> int:
    from vedic.love_reality.pdf_fonts import devanagari_fonts_ready, hindi_font_pair
    from milan_pdf import register_indic_fonts

    register_indic_fonts(force=True)
    ready = devanagari_fonts_ready()
    reg, bold = hindi_font_pair()
    print(f"devanagari_ready={ready}")
    print(f"font_pair=({reg}, {bold})")

    if not ready or reg == "Helvetica":
        print("FAIL: NotoDeva not loaded — check fonts/noto/*.ttf")
        return 1

    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import Paragraph, SimpleDocTemplate
    from milan_pdf import _pick_body_premium, _premium_body_markup, _styles

    sample = (
        "पूरे वाक्य लिखना · Moon Gemini vs Taurus — emotional rhythm check। "
        "यह अध्याय chart signals पर आधारित है।"
    )
    s = _styles("hi")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    doc.build([
        Paragraph(
            _premium_body_markup(sample, "hi"),
            _pick_body_premium(sample, s, "hi", relax=True),
        )
    ])
    pdf = buf.getvalue()
    print(f"sample_pdf_bytes={len(pdf)}")
    if not pdf.startswith(b"%PDF"):
        print("FAIL: sample PDF not generated")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
