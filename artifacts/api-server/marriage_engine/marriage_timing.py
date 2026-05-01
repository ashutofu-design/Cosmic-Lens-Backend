"""
marriage_engine/marriage_timing.py
==================================
TIMING sub-engine — locked Dasha window math for marriage prediction.

Responsibility (1 of 3 irreducible engine cores):
  Compute the next favourable marriage window using:
    - Vimshottari Dasha calendar (which MD/AD supports 2H/7H/11H?)
    - Jupiter transit trigger (classical timing)
    - Intersection of (favourable Dasha) ∩ (Jupiter transit window)

Why engine and not LLM?
  LLM hallucinates dates. Date arithmetic across multi-year Dasha tree +
  Jupiter sign transit cycles is deterministic math the engine MUST own.

Public function:
  compute_timing_window(kundli, intel, kp, birth) -> dict

Returns dict shape (when populated):
  {
    "next_window": {"dasha": "Jupiter-Venus", "start": "2027-04",
                    "end": "2028-08", "reason": "Jupiter MD + 7L AD"},
    "refined_start": "2027-06",   # Dasha ∩ Jupiter transit narrow window
    "refined_end":   "2027-11",
    "jupiter_sign":  "Cancer",
    "jupiter_hits":  3,
  }

CURRENT STATE: stub returning {} — user will populate.
"""

from __future__ import annotations

from typing import Any, Optional


def compute_timing_window(kundli: dict, intel: dict, kp: dict,
                          birth: Optional[Any] = None) -> dict:
    """Stub — returns empty timing dict.

    User will fill in:
      1. Find favourable Dasha periods (significators of 2/7/11)
      2. Find Jupiter transit windows through marriage-supporting signs
      3. Intersect the two -> refined locked window
    """
    return {}
