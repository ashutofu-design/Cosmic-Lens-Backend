#!/usr/bin/env python3
"""Generate local Hindi mixed-script PDF sample for visual check."""
from __future__ import annotations

import io
import sys

sys.path.insert(0, ".")

_SAMPLE = (
    "यह रिश्ता Moon Gemini और Taurus के बीच emotional rhythm दिखाता है। "
    "7th house lord Mercury Scorpio में है — communication gap बढ़ सकता है।\n\n"
    "अगले 24 घंटे में repair करें; silence 48 घंटे से ज्यादा न रखें।"
)


def main() -> int:
    from love_reality_pdf import render_love_reality_pro_pdf

    pro = {
        "verdict": _SAMPLE,
        "blueprint_reality": _SAMPLE,
        "harmony": _SAMPLE,
        "chapters": [{"key": "love_connection", "chapter_body": _SAMPLE}],
    }
    payload = {
        "pdf_lang": "hi",
        "pro_premium": pro,
        "p1": {"name": "A", "day": 1, "month": 1, "year": 1990},
        "p2": {"name": "R", "day": 2, "month": 2, "year": 1992},
        "engines": {
            "love_compatibility": {"score": 13, "emotional_summary": _SAMPLE, "reasons": [_SAMPLE]},
            "breakup_chances": {"score": 30},
            "loyalty_check": {"score": 65},
            "will_return": {"return_probability": 40},
            "future_outcome": {"future_score": 55},
            "hidden_red_flags": {"reasons": [_SAMPLE]},
            "kundli_p1": {"moonSign": "Gemini", "ascendant": "Sagittarius", "planets": []},
            "kundli_p2": {"moonSign": "Taurus", "ascendant": "Gemini", "planets": []},
        },
        "report_id": "LR-HI-MIXED-TEST",
    }
    pdf = render_love_reality_pro_pdf(payload, lang="hi")
    out = "hi_mixed_test.pdf"
    with open(out, "wb") as f:
        f.write(pdf)
    print(f"wrote {out} bytes={len(pdf)} has_NotoDeva={b'NotoDeva' in pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
