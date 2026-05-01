"""
marriage_engine package
=======================
Top-level package for marriage chart analysis.

Phase 2.8.23 (1 May 2026) — converted from single file `marriage_engine.py`
to a package with sub-engines per user direction:
  "marriage engine ke andar aur 2 engine rakho ya folder rakho —
   ek marriage timing, ek love or arrange marriage"

Sub-engines:
  - marriage_timing.py    : TIMING window math (Dasha ∩ Jupiter)
  - love_or_arrange.py    : LOVE vs ARRANGED marriage classifier

This __init__.py re-exports the 4 PUBLIC FUNCTIONS that openai_helper.py
imports, so backward compatibility is fully preserved:
  - assess_marriage(kundli, intel, kp, birth)        -> dict
  - format_verdict_for_prompt(v)                     -> str
  - extract_window_str(v)                            -> str
  - extract_alt_window_str(v)                        -> str

Architecture:
  openai_helper.py
        │
        ▼
   marriage_engine.assess_marriage()    ← top-level orchestrator
        │
        ├──> marriage_timing.compute_timing_window()
        │       (returns timing dict: next_window, refined window)
        │
        └──> love_or_arrange.classify_marriage_type()
                (returns classification dict: type, scores, reasons)
        │
        ▼
   verdict_dict (merged) -> openai_helper -> LLM prompt

CURRENT STATE: all sub-engines are stubs returning {}.
Result: assess_marriage() returns merged empty dict {},
        format_verdict_for_prompt({}) returns "",
        openai_helper gracefully falls back to LLM-only mode.

User will populate sub-engines incrementally.
"""

from __future__ import annotations

from typing import Any, Optional

from .marriage_timing import compute_timing_window
from .love_or_arrange import classify_marriage_type


# ════════════════════════════════════════════════════════════════════
# PUBLIC API — must match the contract openai_helper.py imports
# ════════════════════════════════════════════════════════════════════

def assess_marriage(kundli: dict, intel: dict, kp: dict,
                    birth: Optional[Any] = None,
                    question: str = "") -> dict:
    """Top-level orchestrator. Calls each sub-engine and merges results.

    Returns merged verdict dict. While all sub-engines are stubs,
    returns {} so openai_helper falls back to LLM-only mode.

    `question` is forwarded to the love-or-arrange classifier so
    Trust Layer 1 (self-disclosure honoring) can detect statements
    like "mera love marriage hua tha" and switch to EXPLAIN mode
    instead of contradicting the user. Defaults to "" so existing
    callsites stay backward-compatible.
    """
    timing = compute_timing_window(kundli, intel, kp, birth) or {}
    classify = classify_marriage_type(kundli, intel, kp, birth, question) or {}

    if not timing and not classify:
        return {}

    verdict: dict = {}
    if timing:
        verdict.update(timing)
    if classify:
        verdict["marriage_type"] = classify
    return verdict


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict dict as authoritative prompt block for LLM.

    Empty / falsy verdict -> empty string (openai_helper skips the block).

    Phase 2.8.25 — populates the LOCKED FACTS block for the marriage_type
    classifier so the LLM actually sees engine output (was empty stub before,
    making the whole 25-rule + 3-trust-layer engine invisible to production).

    Block contract (matches existing openai_helper.py expectations):
      - Opens with a ════ separator (so narrator-mode prefix can detect it)
      - Renders mode (PREDICT / EXPLAIN / VERIFY / GENERAL) so LLM tone-shifts
      - Renders self-disclosure trigger (so LLM never contradicts the devotee)
      - Renders final verdict + confidence + band + verdict_text
      - Renders top 3 reasons per side from each engine
      - Renders consensus state and individual engine verdicts
      - Includes authority directive (LLM must restate, not contradict)
      - Closes with the SAME ════ marker so Jaimini UL line can be injected
        before it (openai_helper.py L3837 looks for this exact marker)
    """
    if not v:
        return ""
    mt = v.get("marriage_type") or {}
    if not mt:
        # marriage_type engine produced nothing — fall back to whatever the
        # timing engine put in v (currently still stub) without a block.
        return ""

    bar = "═" * 68
    lines: list[str] = []
    lines.append(bar)
    lines.append("MARRIAGE TYPE ENGINE — LOCKED FACTS (do not contradict)")
    lines.append(bar)

    # ── Mode awareness ──────────────────────────────────────────────────
    mode = (mt.get("mode") or "PREDICT").upper()
    sd   = mt.get("self_disclosure") or {}
    stated = sd.get("stated_type")
    trigger = sd.get("trigger") or ""
    if mode == "EXPLAIN" and stated:
        lines.append(
            f"MODE: EXPLAIN  —  devotee ne KHUD bataya '{stated}' marriage hua."
        )
        if trigger:
            lines.append(f"  Trigger phrase: \"{trigger}\"")
        lines.append(
            "  ★ HARD RULE: tum apne se LOVE/ARRANGED predict mat karo. "
            "Devotee ki batayi hui type maan lo aur uske karak/yog explain karo. ★"
        )
    elif mode == "VERIFY":
        lines.append(
            f"MODE: VERIFY  —  devotee ne '{stated}' bataya, chart cross-check."
        )
        if trigger:
            lines.append(f"  Trigger phrase: \"{trigger}\"")
    elif mode == "GENERAL":
        lines.append(
            "MODE: GENERAL  —  devotee educational sawaal puch raha (specific chart predict mat karo)."
        )
    else:
        lines.append("MODE: PREDICT  —  chart se LOVE / ARRANGED / MIXED nikalo.")

    lines.append("")

    # ── Final verdict ────────────────────────────────────────────────────
    vtype = mt.get("type") or "MIXED"
    conf  = mt.get("confidence", 0)
    band  = mt.get("band") or "MIXED"
    vtext = mt.get("verdict_text") or ""
    lines.append(f"VERDICT TYPE   : {vtype}")
    lines.append(f"CONFIDENCE     : {conf}/100  (band: {band})")
    if vtext:
        lines.append(f"VERDICT TEXT   : {vtext}")

    # ── Engine breakdown ────────────────────────────────────────────────
    engines = mt.get("engines") or {}
    if engines:
        lines.append("")
        lines.append("ENGINE BREAKDOWN (3 independent engines):")
        for ekey, label, weight in (
            ("d1", "Parashari D1",  "30%"),
            ("d9", "D9 Navamsha",   "25%"),
            ("kp", "KP CSL",        "45%"),
        ):
            e = engines.get(ekey) or {}
            if not e:
                continue
            ev   = e.get("verdict") or "UNKNOWN"
            els  = e.get("love_score", 0)
            eas  = e.get("arr_score", 0)
            avail = e.get("available", True)
            if not avail:
                lines.append(f"  • {label} ({weight}): NOT AVAILABLE — skipped")
            else:
                lines.append(
                    f"  • {label} ({weight}): {ev}  (love={els}, arr={eas})"
                )

    # ── Top reasons (Hinglish, devotee-facing) ───────────────────────────
    rl = (mt.get("reasons_love") or [])[:3]
    ra = (mt.get("reasons_arr")  or [])[:3]
    if rl or ra:
        lines.append("")
        lines.append("TOP SUPPORTING FACTORS (cite verbatim — do not invent new ones):")
        if rl:
            lines.append("  LOVE-side:")
            for r in rl:
                lines.append(f"    - {r}")
        if ra:
            lines.append("  ARRANGED-side:")
            for r in ra:
                lines.append(f"    - {r}")

    # ── Consensus state ─────────────────────────────────────────────────
    cons = mt.get("consensus") or {}
    if cons:
        lines.append("")
        lines.append(
            f"CONSENSUS      : {cons.get('consensus','UNCERTAIN')} "
            f"(boost x{cons.get('boost', 1.0)})"
        )

    # ── Trust Layer 4: Sannyasi yoga (META OVERRIDE) ────────────────────
    sann = mt.get("sannyasi") or {}
    if sann.get("triggered"):
        lines.append("")
        lines.append(
            f"⚠ META FLAG — SANNYASI YOGA (intensity {sann.get('intensity', 0)}/100):"
        )
        for r in (sann.get("reasons") or [])[:3]:
            lines.append(f"    - {r}")
        if sann.get("qualifier_text"):
            lines.append(f"  Qualifier: {sann['qualifier_text']}")
        lines.append(
            "  ★ HARD OVERRIDE: bolne se pehle yeh meta-flag devotee ko gently surface karo. "
            "Confidence already capped — false certainty mat do. ★"
        )

    # ── Trust Layer 5: Multi-marriage qualifier ─────────────────────────
    multi = mt.get("multi_marriage") or {}
    if multi.get("triggered"):
        lines.append("")
        lines.append(
            f"⚠ META FLAG — MULTI-MARRIAGE INDICATOR (intensity {multi.get('intensity', 0)}/100):"
        )
        for r in (multi.get("reasons") or [])[:3]:
            lines.append(f"    - {r}")
        if multi.get("qualifier_text"):
            lines.append(f"  Qualifier: {multi['qualifier_text']}")
        lines.append(
            "  ★ SOFT QUALIFIER: verdict ke baad ek line me yeh nuance add karo "
            "(do not overwhelm devotee, but do not hide it either). ★"
        )

    # ── Trust Layer 6: Era cohort context ───────────────────────────────
    era = mt.get("era") or {}
    if era.get("applied") and era.get("note"):
        lines.append("")
        lines.append(
            f"CONTEXT — ERA CALIBRATION (cohort: {era.get('cohort','?')}, "
            f"shift {era.get('shift', 0):+d}):"
        )
        lines.append(f"  {era['note']}")
        lines.append(
            "  Note: yeh confidence mein already apply ho gaya. Verdict ke tone me "
            "implicitly era-aware raho (jaise pre-1990 cohort ko 'modern love marriage common hai' mat bolo)."
        )

    # ── Authority directive ─────────────────────────────────────────────
    lines.append("")
    if mode == "EXPLAIN":
        lines.append(
            "★ AUTHORITY: tum '" + (stated or "") + "' marriage ko EXPLAIN karo, "
            "predict mat karo. Devotee ki personal disclosure SACRED hai. ★"
        )
    elif vtype == "MIXED" or band == "MIXED":
        lines.append(
            "★ AUTHORITY: chart MIXED signals de raha hai. Honestly bolo — koi "
            "ek side force mat karo. \"Dono possibilities khuli hain\" type natural verdict do. ★"
        )
    else:
        lines.append(
            f"★ AUTHORITY: '{vtype}' verdict ko RESTATE karo (apni reasoning add mat karo). "
            "Engine reasons hi cite karo. Verdict text ko Hinglish me natural-flow me likho. ★"
        )

    lines.append(bar)
    # Trailing newline so the marker matches the existing
    # `marker = "..." + "\n"` check in openai_helper.py L3835
    return "\n".join(lines) + "\n"


def extract_window_str(v: dict) -> str:
    """Extract human-readable timing window string from verdict.

    Used by openai_helper to surface the engine's locked window
    (e.g. "April 2027 to August 2028"). Empty when timing engine
    has not yet computed a window.
    """
    if not v:
        return ""
    nw = v.get("next_window") or {}
    if not nw:
        return ""
    # User will fill in the human-readable formatter (e.g. _ym_to_human).
    return ""


def extract_alt_window_str(v: dict) -> str:
    """Extract alternate (fallback) window string from verdict.

    Empty when no alternate window is available.
    """
    if not v:
        return ""
    return ""


# Make these names importable via `from marriage_engine import ...`
__all__ = [
    "assess_marriage",
    "format_verdict_for_prompt",
    "extract_window_str",
    "extract_alt_window_str",
]
