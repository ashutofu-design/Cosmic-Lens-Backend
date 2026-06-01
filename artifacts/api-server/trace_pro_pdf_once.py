#!/usr/bin/env python3
"""Execute one Pro PDF polish + render path with COMPAT_PREMIUM_TRACE logs.

Run from repo: artifacts/api-server (venv activated recommended):

  set COMPAT_PREMIUM_TRACE=1
  set COMPAT_PREMIUM_CACHE_DISABLE=1
  set TRACE_LANG=hi
  set COMPAT_PREMIUM_POLISH=1   # plus OPENAI_API_KEY for live GPT path

  python trace_pro_pdf_once.py

Writes trace lines prefixed [prem_trace] and existing [premium_chapters] prints.
"""
from __future__ import annotations

import os
import sys

# ── cwd / imports ───────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_OUT_TXT = os.path.join(_ROOT, "_prem_trace_last_run.txt")

os.environ.setdefault("COMPAT_PREMIUM_TRACE", "1")
os.environ.setdefault("COMPAT_PREMIUM_CACHE_DISABLE", "1")

from milan_pdf import render_milan_pro_pdf  # noqa: E402
from test_milan_pro_pdf import _milan  # noqa: E402
from vedic.compat.chapter_scores import compute_chapter_scores  # noqa: E402
from vedic.compat.d9_marriage import compute_d9_marriage  # noqa: E402
from vedic.compat.kp_marriage_promise import compute_kp_couple_promise  # noqa: E402
from vedic.compat.premium_chapters import (  # noqa: E402
    normalize_pro_pdf_lang,
    polish_premium_chapters,
)
from vedic.compat.synastry_7l import compute_synastry_7l  # noqa: E402

LANG = normalize_pro_pdf_lang(os.environ.get("TRACE_LANG") or "hi")


def _kundli(name: str, asc: str) -> dict:
    return {
        "name": name,
        "ascendant": asc,
        "moonSign": asc,
        "sunSign": asc,
        "nakshatra": "Ashwini",
        "nakshatraPada": 1,
        "planets": [
            {"name": "Sun", "sign": "Taurus"},
            {"name": "Moon", "sign": "Sagittarius"},
            {"name": "Mars", "sign": "Aquarius"},
        ],
        "divisionalCharts": {
            "D9": {
                "ascendant": asc,
                "planets": [{"name": "Venus", "sign": "Libra"}],
            }
        },
    }


def main() -> None:
    print(f"[trace_pro_pdf_once] TRACE_LANG effective={LANG!r}", flush=True)
    milan = _milan("Vikram", "Sanya", 28)
    k1 = _kundli("Vikram", "Cancer")
    k2 = _kundli("Sanya", "Libra")
    d9 = compute_d9_marriage(k1, k2)
    syn = compute_synastry_7l(k1, k2)
    kp = compute_kp_couple_promise(k1, k2)
    marriage_llm_facts = {
        "source": "trace_pro_pdf_once",
        "version": "v1",
        "d1": {"p1": {"name": k1.get("name"), "ascendant": k1.get("ascendant")}, "p2": {}},
        "d9_marriage": d9,
        "synastry_7l": syn,
        "kp_couple_promise": kp,
    }
    cs = compute_chapter_scores(milan, d9, syn, kp)
    pro = polish_premium_chapters(
        milan,
        cs,
        d9,
        syn,
        kp,
        lang=LANG,
        marriage_llm_facts=marriage_llm_facts,
    )
    merged = dict(milan)
    merged["pro_premium"] = pro
    merged["kundli_p1"] = k1
    merged["kundli_p2"] = k2
    merged["marriage_llm_facts"] = marriage_llm_facts
    pdf = render_milan_pro_pdf(merged, lang=LANG)
    print(
        f"[trace_pro_pdf_once] DONE pdf_bytes={len(pdf)} "
        f"meta_model={(pro.get('_meta') or {}).get('model')!r}",
        flush=True,
    )


if __name__ == "__main__":
    _tee_f = open(_OUT_TXT, "w", encoding="utf-8")

    class _StdoutTee:
        __slots__ = ()

        def write(self, data: str) -> None:
            sys.__stdout__.write(data)
            _tee_f.write(data)

        def flush(self) -> None:
            sys.__stdout__.flush()
            _tee_f.flush()

    sys.stdout = _StdoutTee()
    try:
        main()
    finally:
        sys.stdout = sys.__stdout__
        _tee_f.close()
