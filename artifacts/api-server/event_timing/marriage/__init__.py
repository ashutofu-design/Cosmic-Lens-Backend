"""
event_timing.marriage package
=============================
Marriage event timing — answers "kab shaadi hogi" + "love ya arrange".

Phase 2.8.33 (May 2 2026) — moved from `marriage_engine/` to
`event_timing/marriage/` per user direction:
  "timing event ek alag folder uske andar sirf event timing hoga
   aur kuch bhi nehi"

Originally split in Phase 2.8.23 (1 May 2026) per user direction:
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
   event_timing.marriage.assess_marriage()    ← top-level orchestrator
        │
        ├──> marriage_timing.compute_timing_window()
        │       (returns timing dict: next_window, refined window)
        │
        └──> love_or_arrange.classify_marriage_type()
                (returns classification dict: type, scores, reasons)
        │
        ▼
   verdict_dict (merged) -> openai_helper -> LLM prompt
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


def _format_timing_locked_facts(v: dict) -> str:
    """Timing-only LOCKED FACTS (Steps 0–8) for LLM / narrator paths."""
    primary = (v.get("primary_window") or "").strip()
    if not primary:
        top3 = v.get("top_3_windows") or []
        if top3 and isinstance(top3[0], dict):
            primary = (top3[0].get("window") or "").strip()
    if not primary and not v.get("verdict"):
        return ""

    bar = "═" * 68
    lines = [
        "",
        bar,
        "🔒 MARRIAGE TIMING ENGINE — LOCKED FACTS (Steps 0–8)",
        bar,
        f"VERDICT        : {v.get('verdict') or 'UNKNOWN'}  (band: {v.get('band') or '?'})",
        f"PRIMARY WINDOW : {primary or 'none'}",
    ]
    backup = (v.get("backup_window") or "").strip()
    if backup:
        lines.append(f"BACKUP WINDOW  : {backup}")
    step0 = v.get("step0_tendency") or {}
    if step0:
        lines.append(
            f"STEP0          : {step0.get('verdict')} | pace={step0.get('combined_pace')} "
            f"| delay_vs_late={step0.get('delay_vs_late')}"
        )
    if v.get("chart_late_marriage"):
        lines.append("CHART LATE     : yes — near-term current-PD mat bolo agar PRIMARY door ho")
    ref = (v.get("step0a") or v.get("step0") or {}).get(
        "dasha_scan_plan", {}
    ).get("primary_reference_age")
    if ref is not None:
        lines.append(f"BCP PRIMARY AGE: {ref}")
    if v.get("final_transit_support") is not None:
        lines.append(
            f"TRANSIT (final): support={v.get('final_transit_support')} "
            f"double={v.get('final_double_transit')} "
            f"({v.get('final_transit_detail') or ''})"
        )
    directive = (
        (v.get("step0a") or {}).get("llm_directive")
        or (v.get("step0") or {}).get("llm_directive")
        or ""
    )
    if directive:
        lines.append(f"DIRECTIVE      : {directive[:400]}")
    lines.append(
        "★ TIMING AUTHORITY: PRIMARY WINDOW ko verbatim bolo; apne se 2026 mat invent karo "
        "jab PRIMARY 2030+ ho. ★"
    )
    lines.append(bar)
    lines.append("")
    return "\n".join(lines)


def format_verdict_for_prompt(v: dict) -> str:
    """Render verdict dict as authoritative prompt block for LLM.

    Empty / falsy verdict -> empty string (openai_helper skips the block).

    Phase 2.8.25 — marriage_type block + timing LOCKED FACTS (Steps 0–8).

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

    timing_block = _format_timing_locked_facts(v)

    mt = v.get("marriage_type") or {}
    if not mt:
        return timing_block

    bar = "═" * 68
    lines: list[str] = []
    if timing_block.strip():
        lines.append(timing_block.strip())
        lines.append("")
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
    w = (v.get("primary_window") or "").strip()
    if w:
        return w
    top3 = v.get("top_3_windows") or []
    if top3 and isinstance(top3[0], dict):
        return (top3[0].get("window") or "").strip()
    nw = v.get("next_window") or {}
    if isinstance(nw, dict):
        return (nw.get("window") or nw.get("label") or "").strip()
    return ""


def extract_alt_window_str(v: dict) -> str:
    """Extract alternate (fallback) window string from verdict.

    Empty when no alternate window is available.
    """
    if not v:
        return ""
    w = (v.get("backup_window") or "").strip()
    if w:
        return w
    top3 = v.get("top_3_windows") or []
    if len(top3) > 1 and isinstance(top3[1], dict):
        return (top3[1].get("window") or "").strip()
    return ""


# Make these names importable via `from event_timing.marriage import ...`
__all__ = [
    "assess_marriage",
    "format_verdict_for_prompt",
    "extract_window_str",
    "extract_alt_window_str",
]
