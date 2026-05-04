"""
translator_lock.py — Phase 2.10.2 STEP 7 (M1-M5) + 2.10.3 STEP 7B (M6-M10) ADD-ONLY
═══════════════════════════════════════════════════════════════════════════
Goal: Demote LLM from "free narrator" to "strict renderer".
      Engine = Truth | Renderer = Locked Template | LLM = Optional Polish

Architecture role per project_goal:
  Engine = Truth(frozen) | LLM = Translator | Validator = Guard

Phase 2.10.2 STEP 7 — Core Control (locked):
  M1 — Post-output fact check (LLM text MUST match engine facts)
  M2 — CRITICAL/FAIL severity → code-level hard block (skip LLM entirely)
  M3 — Locked Hinglish template (no free text drift)
  M4 — Allowed-fields whitelist (LLM can only mention engine-known facts)
  M5 — Mismatch → reject LLM output → fallback to deterministic Path A

Phase 2.10.3 STEP 7B — Quality Lift:
  M6  — Engine-result snapshot hash + in-process LRU cache (same input = same output)
  M7  — Severity-driven auto-disclaimer (now explicit, structurally guaranteed)
  M8  — Top-3 windows always rendered (already in template, formalized)
  M9  — Validator severity badge in UI payload (color/icon for frontend)
  M10 — Provenance footer (renderer version + validator status in text + payload)

ADD-ONLY: This module does NOT modify existing format_marriage_response,
ask_engine, openai_helper, or marriage_timing.  It is a wrapper that
callers may opt into.

Public API:
  render_marriage_output(engine_result, lang="hinglish",
                         llm_polish_fn=None, use_cache=True) -> dict
    Returns: {
      "text":            <final Hinglish text — guaranteed fact-locked>,
      "path_used":       "BLOCKED" | "TEMPLATE" | "LLM_POLISHED" | "CACHED",
      "severity":        "OK" | "WARN" | "FAIL" | "CRITICAL",
      "llm_rejected":    bool,
      "rejection_reason": str | None,
      "provenance":      dict (engine version, validator status, hash),
      "ui_badge":        {severity, color, icon, label}    # M9
      "snapshot_hash":   str  # M6
    }
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS — frozen single source of truth
# ═══════════════════════════════════════════════════════════════════════

PHASE_TAG = "Phase 2.10.3 STEP 7B"
RENDERER_VERSION = "translator_lock-v1.1"

# M6 — In-process LRU cache size (per-process, no external dep)
# Phase 2.10.3 STEP 7B fix-up: thread-safe via _CACHE_LOCK; deep-copy on
# get/put so callers can never mutate cached nested dicts (provenance,
# ui_badge, etc.) and corrupt future CACHED responses.
_CACHE_MAX_ENTRIES = 256
_RENDER_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_CACHE_LOCK = threading.Lock()

# M9 — UI severity badge spec (frontend reads this verbatim)
_SEVERITY_BADGE_MAP: Dict[str, Dict[str, str]] = {
    "OK":       {"color": "green",  "icon": "✅", "label": "Verified"},
    "WARN":     {"color": "yellow", "icon": "⚠️", "label": "Minor Warning"},
    "FAIL":     {"color": "orange", "icon": "❌", "label": "Low Confidence"},
    "CRITICAL": {"color": "red",    "icon": "🛑", "label": "Blocked"},
}

# M4 — Allowed fields whitelist. LLM output may only reference these
# engine-known fact keys. Anything outside this set is suspect.
ALLOWED_ENGINE_FIELDS: Tuple[str, ...] = (
    "verdict",
    "band",
    "primary_window",
    "backup_window",
    "key_trigger",
    "confluence_strength",
    "risk_flag",
    "risk_flags",
    "top_3_windows",
    "step0_tendency",
    "validator_report",
)

# Severity tiers (mirror of validator.py STEP 6)
SEVERITY_OK = "OK"
SEVERITY_WARN = "WARN"
SEVERITY_FAIL = "FAIL"
SEVERITY_CRITICAL = "CRITICAL"

# M2 — Severities that MUST hard-block LLM (code-level, not LLM-trusted)
_HARD_BLOCK_SEVERITIES = frozenset({SEVERITY_CRITICAL})

# M2 — Severities that allow rendering but require disclaimer
_DISCLAIMER_SEVERITIES = frozenset({SEVERITY_FAIL, SEVERITY_WARN})

# M1 — Months for date extraction (English + common Hindi/Hinglish forms)
_MONTH_TOKENS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

# Verdict vocabulary (must match engine)
_VERDICT_VOCAB = frozenset({
    "PROMISED", "DELAYED", "DENIED", "PREMATURE", "UNKNOWN", "BALANCED"
})


# ═══════════════════════════════════════════════════════════════════════
# M2 — SEVERITY GATE (code-level hard-block, pre-LLM)
# ═══════════════════════════════════════════════════════════════════════

def gate_by_severity(engine_result: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    Pure code-level gate. Read validator severity. Decide:
      - allow LLM call?
      - inject disclaimer?

    Returns:
      (allow_llm: bool, severity: str, disclaimer: str)
        disclaimer is "" when severity == OK
        allow_llm is False when severity in HARD_BLOCK set
    """
    vr = engine_result.get("validator_report") or {}
    severity = (vr.get("severity") or SEVERITY_OK).upper()
    if severity not in (SEVERITY_OK, SEVERITY_WARN,
                        SEVERITY_FAIL, SEVERITY_CRITICAL):
        # Unknown severity → treat as FAIL (defensive)
        severity = SEVERITY_FAIL

    if severity in _HARD_BLOCK_SEVERITIES:
        return (False, severity,
                "⚠️ Validator ne CRITICAL issue detect kiya — prediction "
                "narration block kar diya. Chart inputs verify karo.")

    if severity == SEVERITY_FAIL:
        return (True, severity,
                "⚠️ Validator: low-confidence (FAIL) — yeh prediction "
                "indicative hai, decision se pehle re-verify karo.")

    if severity == SEVERITY_WARN:
        return (True, severity,
                "ℹ️ Validator: minor warning — output reliable hai, "
                "but cross-check recommended.")

    return (True, severity, "")


# ═══════════════════════════════════════════════════════════════════════
# M3 — LOCKED HINGLISH TEMPLATE (deterministic slot-fill, no free text)
# ═══════════════════════════════════════════════════════════════════════

def _safe(v: Any, default: str = "—") -> str:
    """None / empty → placeholder."""
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def _format_top3(top_3: List[Dict[str, Any]]) -> str:
    """Render top-3 windows as bullet list (M9 pre-cursor)."""
    if not top_3:
        return "  (no alternative windows computed)"
    lines = []
    for i, w in enumerate(top_3[:3], 1):
        # Window dict shape varies — render whatever's available
        label = w.get("window") or w.get("label")
        if not label:
            start = w.get("start_str") or w.get("start") or "?"
            end = w.get("end_str") or w.get("end") or "?"
            label = f"{start} → {end}"
        score = w.get("score")
        score_str = f" (score={score})" if score is not None else ""
        lines.append(f"  {i}. {label}{score_str}")
    return "\n".join(lines)


def _format_risk_flags(engine_result: Dict[str, Any]) -> str:
    flags = engine_result.get("risk_flags") or []
    single = engine_result.get("risk_flag")
    all_flags = list(flags)
    if single and single not in all_flags:
        all_flags.insert(0, single)
    if not all_flags:
        return "  (none)"
    return "\n".join(f"  • {f}" for f in all_flags[:5])


def render_locked_template(engine_result: Dict[str, Any],
                           disclaimer: str = "",
                           lang: str = "hinglish") -> str:
    """
    M3 — Deterministic Hinglish template. No LLM. Pure slot-fill.

    Currently supports lang="hinglish" (primary). Other langs fall
    through to Hinglish for now (M15 will extend in Phase 2.10.4).
    """
    verdict = _safe(engine_result.get("verdict"))
    band = _safe(engine_result.get("band"))
    primary = _safe(engine_result.get("primary_window"),
                    default="(no primary window)")
    backup = _safe(engine_result.get("backup_window"),
                   default="(no backup)")
    trigger = _safe(engine_result.get("key_trigger"),
                    default="(trigger not specified)")
    conf_strength = _safe(engine_result.get("confluence_strength"))
    top3_block = _format_top3(engine_result.get("top_3_windows") or [])
    risks_block = _format_risk_flags(engine_result)

    vr = engine_result.get("validator_report") or {}
    severity = (vr.get("severity") or SEVERITY_OK).upper()
    severity_badge = {
        SEVERITY_OK:       "✅ OK",
        SEVERITY_WARN:     "⚠️ WARN",
        SEVERITY_FAIL:     "❌ FAIL",
        SEVERITY_CRITICAL: "🛑 CRITICAL",
    }.get(severity, severity)

    parts = [
        "════════════════════════════════════════════",
        "📿 SHADI KA SAMAY — Astrology Reading",
        "════════════════════════════════════════════",
        "",
        f"Verdict: {verdict} ({band} band, {conf_strength} confluence)",
        "",
        f"PRIMARY WINDOW: {primary}",
        f"Trigger: {trigger}",
        "",
        f"BACKUP WINDOW: {backup}",
        "",
        "TOP 3 WINDOWS:",
        top3_block,
        "",
        "RISK FLAGS:",
        risks_block,
        "",
        f"Validator: {severity_badge}",
    ]

    if disclaimer:
        parts.extend(["", disclaimer])

    parts.extend([
        "",
        "════════════════════════════════════════════",
    ])

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════
# M1 — POST-OUTPUT FACT CHECK (extract + compare)
# ═══════════════════════════════════════════════════════════════════════

def _extract_verdicts(text: str) -> List[str]:
    """Find all known verdict tokens in text (case-insensitive)."""
    hits = []
    upper = text.upper()
    for v in _VERDICT_VOCAB:
        if v in upper:
            hits.append(v)
    return hits


def _extract_year_month_pairs(text: str) -> List[Tuple[int, int]]:
    """
    Extract (year, month) pairs from text.
    Patterns supported:
      "May 2026", "May-July 2026", "May - July 2026",
      "September 2032", etc.
    Returns deduped list.
    """
    pairs: List[Tuple[int, int]] = []
    lower = text.lower()
    # Pattern: month_token + (optional second month) + 4-digit year
    rx = re.compile(
        r"\b([a-z]{3,9})(?:\s*[-–to]+\s*([a-z]{3,9}))?\s+"
        r"(\d{4})\b"
    )
    for m in rx.finditer(lower):
        m1, m2, yr = m.group(1), m.group(2), m.group(3)
        try:
            year = int(yr)
        except ValueError:
            continue
        if year < 1900 or year > 2200:
            continue
        if m1 in _MONTH_TOKENS:
            pairs.append((year, _MONTH_TOKENS[m1]))
        if m2 and m2 in _MONTH_TOKENS:
            pairs.append((year, _MONTH_TOKENS[m2]))
    # Dedup preserve order
    seen = set()
    out = []
    for p in pairs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _engine_window_pairs(engine_result: Dict[str, Any]) -> List[Tuple[int, int]]:
    """Collect all (year, month) pairs the engine considers valid."""
    texts: List[str] = []
    for k in ("primary_window", "backup_window"):
        v = engine_result.get(k)
        if v:
            texts.append(str(v))
    for w in (engine_result.get("top_3_windows") or []):
        for kk in ("window", "label", "start_str", "end_str", "start", "end"):
            vv = w.get(kk)
            if vv:
                texts.append(str(vv))
    blob = " ".join(texts)
    return _extract_year_month_pairs(blob)


def fact_check_llm_output(llm_text: str,
                          engine_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    M1 — Compare LLM text vs engine facts.

    Checks:
      1. Verdict mentioned in LLM matches engine.verdict (no contradiction)
      2. Every (year, month) pair in LLM appears within engine windows
         (primary, backup, top_3)

    Returns (is_match, mismatch_reasons[])
      is_match=True  → safe to use LLM text
      is_match=False → reject LLM text, fall back to template
    """
    reasons: List[str] = []

    # ── Verdict check (Phase 2.10.2 STEP 7 fix-up: fail closed) ──────
    engine_verdict = (engine_result.get("verdict") or "").upper()
    llm_verdicts = _extract_verdicts(llm_text)
    if not engine_verdict:
        # Engine verdict missing/empty → schema drift. If LLM mentions
        # any verdict token, we cannot validate it → reject.
        if llm_verdicts:
            reasons.append(
                f"engine verdict missing but LLM asserts {llm_verdicts} "
                f"— cannot validate, fail closed"
            )
    elif llm_verdicts:
        contradicting = [v for v in llm_verdicts
                         if v != engine_verdict and v in _VERDICT_VOCAB]
        # If LLM only mentions engine_verdict → fine.
        # If it adds a contradicting one → mismatch.
        if contradicting:
            reasons.append(
                f"verdict mismatch: LLM mentioned {contradicting} "
                f"but engine={engine_verdict}"
            )

    # ── Date check (Phase 2.10.2 STEP 7 fix-up: fail closed when engine
    # has windows BUT we couldn't parse them) ────────────────────────
    engine_pairs = set(_engine_window_pairs(engine_result))
    llm_pairs = _extract_year_month_pairs(llm_text)

    # Detect whether engine *should* have windows (so missing-parse = bug)
    engine_has_window_text = any(
        engine_result.get(k) for k in ("primary_window", "backup_window")
    ) or bool(engine_result.get("top_3_windows"))

    if engine_pairs:
        invented = [p for p in llm_pairs if p not in engine_pairs]
        if invented:
            invented_str = ", ".join(f"{y}-{m:02d}" for y, m in invented[:5])
            reasons.append(
                f"invented date(s) not in engine windows: {invented_str}"
            )
    elif engine_has_window_text and llm_pairs:
        # Engine claims it has windows but we couldn't parse them — and LLM
        # is asserting dates. Cannot validate → fail closed.
        llm_str = ", ".join(f"{y}-{m:02d}" for y, m in llm_pairs[:5])
        reasons.append(
            f"engine windows unparseable but LLM asserts {llm_str} "
            f"— cannot validate, fail closed"
        )

    return (len(reasons) == 0, reasons)


# ═══════════════════════════════════════════════════════════════════════
# M4 — WHITELIST SANITIZER (drop unknown claims)
# ═══════════════════════════════════════════════════════════════════════

# Phase 2.10.2 STEP 7 fix-up: Broadened M4 — generalized planet+house and
# planet+sign claim detection (covers Saturn/Rahu/Ketu/Mars/Jupiter/Venus/
# Mercury/Sun/Moon, English+Sanskrit names). Drift-by-default: any specific
# planetary placement claim not present verbatim in engine text → reject.
_PLANET_NAMES = (
    "sun|surya|ravi|moon|chandra|chandrama|"
    "mars|mangal|mangala|kuja|"
    "mercury|budh|budha|"
    "jupiter|guru|brihaspati|"
    "venus|shukra|sukra|"
    "saturn|shani|sani|"
    "rahu|ketu"
)
_FORBIDDEN_CLAIM_PATTERNS = (
    # planet + house (e.g. "Saturn in 7th house", "Mars 8H", "Jupiter me 5 ghar")
    re.compile(rf"\b(?:{_PLANET_NAMES})\b[^.!?\n]{{0,30}}?"
               r"\b\d+\s*(?:st|nd|rd|th)?\s*(?:house|ghar|h)\b", re.I),
    re.compile(rf"\b(?:{_PLANET_NAMES})\b\s+(?:in|me|main)\s+"
               r"\d+(?:st|nd|rd|th)?\s*(?:house|ghar|h)\b", re.I),
    # planet + sign placement (e.g. "Saturn in Scorpio")
    re.compile(rf"\b(?:{_PLANET_NAMES})\b\s+(?:in|me)\s+"
               r"(?:aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|"
               r"sagittarius|capricorn|aquarius|pisces|"
               r"mesh|vrish|mithun|kark|simh|kanya|tula|vrishchik|"
               r"dhanu|makar|kumbh|meen)\w*", re.I),
    # specific dosha claims (kuja/mangal/kaal-sarp/pitru)
    re.compile(r"\b(?:kuja|mangal|mars|kaal[\s-]*sarp|pitru|nadi|"
               r"bhakoot|gun)\s+dosh", re.I),
    # nakshatra-specific claims (e.g. "Mool nakshatra", "Anuradha pada")
    re.compile(r"\b(?:ashwini|bharani|krittika|rohini|mrigashira|ardra|"
               r"punarvasu|pushya|ashlesha|magha|purva\s*phalguni|"
               r"uttara\s*phalguni|hasta|chitra|swati|vishakha|anuradha|"
               r"jyeshtha|mool|moola|purva\s*ashadha|uttara\s*ashadha|"
               r"shravana|dhanishta|shatabhisha|purva\s*bhadra|"
               r"uttara\s*bhadra|revati)\s+(?:nakshatra|pada)", re.I),
    # specific dasha/bhukti period claims (e.g. "Saturn mahadasha")
    re.compile(rf"\b(?:{_PLANET_NAMES})\s+"
               r"(?:mahadasha|mahadasa|antardasha|antardasa|bhukti|"
               r"pratyantar|md|ad|pd)\b", re.I),
)


def whitelist_check(llm_text: str,
                    engine_result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    M4 — Reject LLM if it asserts specific astrological facts (planet
    placements, doshas, nakshatras, dasha periods) NOT present in
    engine_result.

    Strategy: detect a fixed vocabulary of specific-claim patterns. For
    each match, require ALL substantive tokens to appear in the engine
    text blob. If not → drift.

    This is broader than v1 (now covers ~all 9 grahas + signs +
    nakshatras + dosha types + dasha periods).
    """
    drift: List[str] = []

    # Build a haystack of all engine-known textual content
    engine_text_parts: List[str] = []
    for k in ("verdict", "band", "primary_window", "backup_window",
              "key_trigger", "confluence_strength", "risk_flag"):
        v = engine_result.get(k)
        if v:
            engine_text_parts.append(str(v))
    for f in (engine_result.get("factors") or []):
        engine_text_parts.append(str(f))
    for f in (engine_result.get("risk_flags") or []):
        engine_text_parts.append(str(f))
    # Also include serialized top_3_windows (often holds trigger details)
    for w in (engine_result.get("top_3_windows") or []):
        for vv in w.values():
            if vv:
                engine_text_parts.append(str(vv))
    engine_blob_lower = " ".join(engine_text_parts).lower()

    seen_claims: set = set()
    for rx in _FORBIDDEN_CLAIM_PATTERNS:
        for m in rx.finditer(llm_text):
            claim = m.group(0).lower().strip()
            if claim in seen_claims:
                continue
            seen_claims.add(claim)
            # Allow if engine itself mentions this claim's substantive tokens
            tokens = [t for t in re.split(r"[\s\-]+", claim)
                      if len(t) > 2 and t.isalnum()]
            if not tokens:
                continue
            if not all(t in engine_blob_lower for t in tokens):
                drift.append(f"unsupported claim: '{m.group(0)}'")

    return (len(drift) == 0, drift)


# ═══════════════════════════════════════════════════════════════════════
# M6 — SNAPSHOT HASH + LRU CACHE (same input → same output, no jitter)
# ═══════════════════════════════════════════════════════════════════════

def snapshot_hash(engine_result: Dict[str, Any], lang: str = "hinglish") -> str:
    """
    Deterministic SHA-256 over the whitelisted engine fields + lang.

    Only ALLOWED_ENGINE_FIELDS contribute to the hash — debug/trace
    fields (factors, d1_d9_planet_scan, etc.) are ignored so that
    irrelevant changes don't bust the cache.

    Note: List ordering inside engine fields IS significant. The engine is
    expected to produce stable ordering (e.g. top_3_windows in score
    order, risk_flags in detection order). If a downstream change
    reorders an inherently-unordered list, callers should normalize
    BEFORE calling render_marriage_output to keep cache hits stable.
    """
    payload: Dict[str, Any] = {"_lang": lang, "_renderer": RENDERER_VERSION}
    for k in ALLOWED_ENGINE_FIELDS:
        v = engine_result.get(k)
        if v is not None:
            payload[k] = v
    try:
        blob = json.dumps(payload, sort_keys=True, default=str,
                          ensure_ascii=False)
    except Exception:
        # Defensive: fall back to repr if json fails
        blob = repr(sorted(payload.items()))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    """Thread-safe get; returns a deep copy so callers cannot mutate cache."""
    with _CACHE_LOCK:
        if key in _RENDER_CACHE:
            _RENDER_CACHE.move_to_end(key)
            # Deep copy: nested dicts (provenance, ui_badge) MUST be
            # isolated so caller mutation can't corrupt future hits.
            return copy.deepcopy(_RENDER_CACHE[key])
        return None


def _cache_put(key: str, value: Dict[str, Any]) -> None:
    """Thread-safe put; stores a deep copy so subsequent caller mutations
    of `value` cannot corrupt the cached entry."""
    with _CACHE_LOCK:
        _RENDER_CACHE[key] = copy.deepcopy(value)
        _RENDER_CACHE.move_to_end(key)
        while len(_RENDER_CACHE) > _CACHE_MAX_ENTRIES:
            _RENDER_CACHE.popitem(last=False)


def clear_render_cache() -> None:
    """Test/debug helper. Resets the LRU. Thread-safe."""
    with _CACHE_LOCK:
        _RENDER_CACHE.clear()


# ═══════════════════════════════════════════════════════════════════════
# M9 — UI SEVERITY BADGE PAYLOAD
# ═══════════════════════════════════════════════════════════════════════

def build_ui_badge(severity: str) -> Dict[str, str]:
    """Frontend-ready badge spec for the given severity."""
    sev = (severity or SEVERITY_OK).upper()
    spec = _SEVERITY_BADGE_MAP.get(sev, _SEVERITY_BADGE_MAP[SEVERITY_OK])
    return {
        "severity": sev,
        "color":    spec["color"],
        "icon":     spec["icon"],
        "label":    spec["label"],
    }


# ═══════════════════════════════════════════════════════════════════════
# M10 — PROVENANCE FOOTER (text + structured)
# ═══════════════════════════════════════════════════════════════════════

def _provenance_footer_text(provenance: Dict[str, Any],
                            snapshot_hash_str: str) -> str:
    """
    M10 — Compact one-liner footer appended to text output for
    transparency / debug trail. Format:
      ─── Computed by translator_lock-v1.1 (Phase 2.10.3 STEP 7B) ·
          Validator: OK · hash:abc12345 ───
    """
    sev = provenance.get("validator_severity", "?")
    short_hash = snapshot_hash_str[:8] if snapshot_hash_str else "—"
    return (f"─── Computed by {provenance.get('renderer','?')} "
            f"({provenance.get('phase','?')}) · "
            f"Validator: {sev} · hash:{short_hash} ───")


# ═══════════════════════════════════════════════════════════════════════
# M7 — EXPLICIT DISCLAIMER PREPEND HELPER (structurally guaranteed)
# ═══════════════════════════════════════════════════════════════════════

def ensure_disclaimer(text: str, severity: str, disclaimer: str) -> str:
    """
    M7 — Always append disclaimer for FAIL/WARN. Pure helper; no substring
    fuzziness — severity-driven, structurally guaranteed.
    """
    if not disclaimer:
        return text
    if severity not in _DISCLAIMER_SEVERITIES:
        return text
    body = text.rstrip()
    return body + "\n\n" + disclaimer


# ═══════════════════════════════════════════════════════════════════════
# M5 — ORCHESTRATOR (gate → template → optional LLM polish → fact-check
#                    → fallback if mismatch)
# Phase 2.10.3 STEP 7B: integrates M6 cache, M9 badge, M10 footer
# ═══════════════════════════════════════════════════════════════════════

def render_marriage_output(
    engine_result: Dict[str, Any],
    lang: str = "hinglish",
    llm_polish_fn: Optional[Callable[[str, Dict[str, Any]], str]] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    Public entry point. Single source of truth for marriage narration.

    Pipeline:
      0. M6 snapshot_hash → check cache → return CACHED if hit
      1. M2 gate_by_severity → CRITICAL? return blocked response (no LLM)
      2. M3 render_locked_template → deterministic Hinglish base text
      3. If llm_polish_fn provided AND severity allows:
           a. Call llm_polish_fn(template_text, engine_result)
           b. M1 fact_check_llm_output → mismatch? reject
           c. M4 whitelist_check → drift? reject
           d. If both pass → use LLM output
           e. Else fall back to template (M5)
      4. M7 ensure_disclaimer → guarantee for FAIL/WARN
      5. M9 build_ui_badge → attach UI payload
      6. M10 append provenance footer to text
      7. Cache + return

    NOTE: When llm_polish_fn is provided, cache is bypassed (LLM may be
    non-deterministic). Cache only applies to TEMPLATE / BLOCKED paths.
    """
    # ── M6 hash + cache lookup (only for deterministic paths) ────────
    hash_key = snapshot_hash(engine_result, lang)
    if use_cache and llm_polish_fn is None:
        cached = _cache_get(hash_key)
        if cached is not None:
            cached["path_used"] = "CACHED"
            return cached

    allow_llm, severity, disclaimer = gate_by_severity(engine_result)

    provenance: Dict[str, Any] = {
        "renderer":         RENDERER_VERSION,
        "phase":            PHASE_TAG,
        "validator_severity": severity,
        "validator_pass":   bool((engine_result.get("validator_report")
                                  or {}).get("pass", True)),
        "snapshot_hash":    hash_key,
    }
    ui_badge = build_ui_badge(severity)

    def _finalize(text: str, path: str, llm_rejected: bool,
                  rejection_reason: Optional[str]) -> Dict[str, Any]:
        # M10 — append provenance footer
        footer = _provenance_footer_text(provenance, hash_key)
        text_with_footer = text.rstrip() + "\n\n" + footer
        result = {
            "text":             text_with_footer,
            "path_used":        path,
            "severity":         severity,
            "llm_rejected":     llm_rejected,
            "rejection_reason": rejection_reason,
            "provenance":       provenance,
            "ui_badge":         ui_badge,        # M9
            "snapshot_hash":    hash_key,        # M6
        }
        # Cache only deterministic paths (TEMPLATE / BLOCKED), never
        # LLM_POLISHED outputs (LLM may be non-deterministic across calls)
        if use_cache and path in ("TEMPLATE", "BLOCKED"):
            _cache_put(hash_key, result)
        return result

    # ── M2 hard block ─────────────────────────────────────────────────
    if not allow_llm:
        blocked_text = (
            "════════════════════════════════════════════\n"
            "🛑 PREDICTION BLOCKED — Validator CRITICAL\n"
            "════════════════════════════════════════════\n\n"
            f"{disclaimer}\n\n"
            "Detailed validator report:\n"
            f"  Severity: {severity}\n"
            f"  Pass: {provenance['validator_pass']}\n\n"
            "Action: re-verify chart inputs (DOB, TOB, place) and re-run.\n"
            "════════════════════════════════════════════"
        )
        return _finalize(blocked_text, "BLOCKED", False, None)

    # ── M3 deterministic template (always first) ──────────────────────
    template_text = render_locked_template(engine_result, disclaimer, lang)

    # ── No LLM polish requested → return template directly ────────────
    if llm_polish_fn is None:
        return _finalize(template_text, "TEMPLATE", False, None)

    # ── LLM polish path: try, validate, fallback on mismatch ──────────
    llm_text = None
    rejection_reason: Optional[str] = None
    try:
        llm_text = llm_polish_fn(template_text, engine_result)
    except Exception as exc:
        rejection_reason = f"llm_polish_fn raised: {exc}"

    if llm_text is None or not str(llm_text).strip():
        rejection_reason = rejection_reason or "llm returned empty"
        return _finalize(template_text, "TEMPLATE", True, rejection_reason)

    facts_ok, fact_reasons = fact_check_llm_output(llm_text, engine_result)
    clean_ok, drift_reasons = whitelist_check(llm_text, engine_result)

    if not facts_ok or not clean_ok:
        all_reasons = fact_reasons + drift_reasons
        return _finalize(template_text, "TEMPLATE", True,
                         "; ".join(all_reasons))

    # All checks passed — M7 ensure disclaimer (structurally guaranteed)
    final = ensure_disclaimer(str(llm_text), severity, disclaimer)
    return _finalize(final, "LLM_POLISHED", False, None)
