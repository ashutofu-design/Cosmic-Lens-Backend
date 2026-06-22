#!/usr/bin/env python3
"""Cross-domain timing master audit — routing + spec coverage."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from event_timing.domain_specs import DOMAIN_TIMING_SPECS, list_domains_by_status
from event_timing.timing_router import resolve_timing_domain, detect_timing_intent

CASES: list[tuple[str, str, bool]] = [
    # (question, expected_domain, is_timing)
    ("Shaadi kab hogi?", "marriage", True),
    ("Job kab lagegi?", "career", True),
    ("Promotion kab hoga?", "career", True),
    ("Videsh kab jaunga?", "travel", True),
    ("Foreign settlement kab hoga?", "travel", True),
    ("Visa kab milega?", "travel", True),
    ("Ghar kab lun?", "property", True),
    ("Registry kab hogi?", "property", True),
    ("Court case kab khatam hoga?", "litigation", True),
    ("Bail kab milegi?", "litigation", True),
    ("Exam result kab aayega?", "education", True),
    ("Bachcha kab hoga?", "children", True),
    ("Patchup kab hoga?", "love", True),
    ("Love marriage kab hogi?", "marriage", True),
    ("Mere liye job better hai ya business?", "career", False),
    ("Travel yog strong hai?", "travel", False),
    ("Kaunsi field best rahegi?", "career", False),
    ("Biwi kaisi hogi?", "marriage", False),
    ("Nifty intraday kab?", "general", False),
]

BULK = [
    ("Abroad shift kab hoga?", "travel", True),
    ("PR kab milega?", "travel", True),
    ("Possession kab milegi?", "property", True),
    ("Case verdict kab aayega?", "litigation", True),
    ("Admission kab hogi?", "education", True),
    ("Conceive kab ho sakta hai?", "children", True),
    ("Transfer kab hoga office?", "career", True),
    ("Sarkari naukri kab milegi?", "career", True),
    ("Main 65 saal ka job kab lagega?", "career", True),
    ("Partner support karega career me?", "general", False),
]
CASES.extend(BULK)


def main() -> int:
    gaps: list[str] = []
    for i, (q, exp_dom, exp_timing) in enumerate(CASES, 1):
        got_dom, _, got_timing = resolve_timing_domain(q)
        det_timing = detect_timing_intent(q)
        if got_timing != exp_timing:
            gaps.append(
                f"#{i} TIMING {q!r} want={exp_timing} got={got_timing} detect={det_timing}"
            )
        if exp_timing and got_dom != exp_dom:
            gaps.append(f"#{i} DOMAIN {q!r} want={exp_dom} got={got_dom}")

    ready = list_domains_by_status("ready")
    partial = list_domains_by_status("partial")
    print(f"TOTAL={len(CASES)} GAPS={len(gaps)}")
    print(f"ENGINES_READY={ready}")
    print(f"ENGINES_PARTIAL={partial}")
    print(f"DOMAIN_COUNT={len(DOMAIN_TIMING_SPECS)}")
    for g in gaps[:30]:
        print(g.encode("ascii", "replace").decode("ascii"))
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
