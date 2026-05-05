"""Property reply layer — Signal-Pack → LLM → Sanitizer → Force-Verdict.

Architecture (mirrors health_static H2.7.20):
  Engine    = compute_property_facts() = TRUTH
  SignalPack= compact JSON (NO raw kundli, NO planets, NO houses)
  LLM       = expression layer (strict sys-prompt + temperature 0.5)
  Sanitizer = post-LLM regex sweep (strip planet/house/timing/jargon)
  ForceFinal= mandatory '👉 Final:' verdict (engine-built, verbatim)

Killswitches:
  PROPERTY_STATIC_BYPASS=1   → handle_property_question returns None
  PROPERTY_SIGNAL_PACK=1     → use signal-pack path (default)
  PROPERTY_FINAL_VERDICT=1   → force-append engine verdict
  PROPERTY_REPLY_SANITIZER=1 → run regex sweep
"""
from __future__ import annotations
import json
import os
import re
from typing import Any, Dict, Optional

from property_static.property_engine import compute_property_facts, SCOPE as _SCOPE
from property_static.property_routing import (
    is_property_question,
    is_timing_property_question,
    route_property_question,
    TIMING_REJECT_TEMPLATE,
)


# ──────────────────────────────────────────────────────────────────────
# Signal-pack builder — compact JSON for LLM (NO raw kundli)
# ──────────────────────────────────────────────────────────────────────
_DIM_TO_STATE = {
    # yog
    "STRONG":    "strong",
    "MODERATE":  "moderate",
    "WEAK":      "weak",
    # risk
    "CLEAN":     "clean",
    "CAUTION":   "caution",
    "HIGH_RISK": "high_risk",
    # failsafe
    "UNKNOWN":   "unknown",
}

_TYPE_LABEL = {
    "plot":      "plot or land",
    "new_home":  "new home or flat",
    "luxury":    "luxury or spacious home",
    "rental":    "rental or old property",
    "ancestral": "ancestral or family home",
}


def _build_signal_pack(facts: dict) -> dict:
    """Build the compact signal-pack JSON sent to LLM.

    Strict: NO planet names, NO house numbers, NO sign names, NO
    dasha info — only verdict states + plain-Hinglish reasons.
    """
    dims = facts.get("dimensions") or {}
    yog      = dims.get("yog") or {}
    capacity = dims.get("capacity") or {}
    risk     = dims.get("risk") or {}
    type_fit = dims.get("type_fit") or {}

    pack = {
        "topic": "property",
        "dims": {
            "yog": {
                "state":  _DIM_TO_STATE.get(yog.get("verdict", ""), "unknown"),
                "reason": yog.get("reason", ""),
            },
            "capacity": {
                "state":  _DIM_TO_STATE.get(capacity.get("verdict", ""), "unknown"),
                "reason": capacity.get("reason", ""),
            },
            "risk": {
                "state":  _DIM_TO_STATE.get(risk.get("verdict", ""), "unknown"),
                "reason": risk.get("reason", ""),
            },
            "type_fit": {
                "best": _TYPE_LABEL.get(type_fit.get("best", ""),
                                        type_fit.get("best", "new home")),
                "alt":  _TYPE_LABEL.get(type_fit.get("alt", ""),
                                        type_fit.get("alt", "")),
                "reason": type_fit.get("reason", ""),
            },
        },
        "overall_snapshot": _build_overall_snapshot(yog, capacity, risk),
        "engine_verdict":   _build_final_verdict_from_dims(yog, capacity, risk),
        "remedy_focus":     _pick_remedy_focus(yog, capacity, risk),
    }
    return pack


def _build_overall_snapshot(yog: dict, cap: dict, risk: dict) -> str:
    yv = _DIM_TO_STATE.get(yog.get("verdict", ""), "unknown")
    cv = _DIM_TO_STATE.get(cap.get("verdict", ""), "unknown")
    rv = _DIM_TO_STATE.get(risk.get("verdict", ""), "unknown")
    return (f"Property yog {yv}, capacity {cv}, risk {rv}.")


def _pick_remedy_focus(yog: dict, cap: dict, risk: dict) -> str:
    rv = _DIM_TO_STATE.get(risk.get("verdict", ""), "")
    yv = _DIM_TO_STATE.get(yog.get("verdict", ""), "")
    cv = _DIM_TO_STATE.get(cap.get("verdict", ""), "")
    if rv == "high_risk":         return "verification"
    if rv == "caution":            return "documentation"
    if cv == "weak":               return "saving"
    if yv == "weak":               return "stability"
    return "planning"


# ──────────────────────────────────────────────────────────────────────
# Engine-built MANDATORY '👉 Final:' verdict (deterministic)
# ──────────────────────────────────────────────────────────────────────
_RISK_ACTION = {
    "high_risk": "Legal verification aur documentation pehle complete karein.",
    "caution":   "Documentation aur legal check ke baad hi aage badho.",
    "clean":     "Structured planning ke saath aage badho.",
    "unknown":   "Pehle base data clear karein.",
}


def _build_final_verdict_from_dims(yog: dict, cap: dict, risk: dict) -> str:
    yv = _DIM_TO_STATE.get(yog.get("verdict", ""), "unknown")
    cv = _DIM_TO_STATE.get(cap.get("verdict", ""), "unknown")
    rv = _DIM_TO_STATE.get(risk.get("verdict", ""), "unknown")

    if yv == "unknown" and cv == "unknown":
        return ("👉 Final: Signals incomplete hain — pehle birth chart "
                "data complete karein, fir clear property analysis ho payegi.")

    action = _RISK_ACTION.get(rv, _RISK_ACTION["caution"])
    return (f"👉 Final: Property yog {yv} hai aur capacity {cv} hai. "
            f"{action}")


_FINAL_LINE_RX = re.compile(r"(?i)\s*👉\s*Final\s*:[^\n]*(?:\n|$)")


def _force_final_verdict(text: str, pack: dict) -> str:
    """Strip ALL existing '👉 Final:' lines anywhere; force-append
    EXACTLY ONE engine-built canonical at EOF.
    Killswitch: PROPERTY_FINAL_VERDICT=0 → return untouched."""
    if os.environ.get("PROPERTY_FINAL_VERDICT", "1") == "0":
        return text
    if not text:
        return text
    stripped = _FINAL_LINE_RX.sub("", text).rstrip()
    verdict = pack.get("engine_verdict") or _build_final_verdict_from_dims(
        {}, {}, {})
    return f"{stripped}\n\n{verdict}"


# ──────────────────────────────────────────────────────────────────────
# Sanitizer — strip planet/house/timing/jargon leaks
# ──────────────────────────────────────────────────────────────────────
_PLANET_RX = re.compile(
    r"\b(sun|surya|moon|chandra|mars|mangal|mangala|"
    r"mercury|budh|budha|jupiter|guru|brihaspati|"
    r"venus|shukra|saturn|shani|"
    r"rahu|ketu)\b",
    re.IGNORECASE,
)
_HOUSE_RX = re.compile(
    r"\b(\d{1,2}(st|nd|rd|th)\s*(house|bhav|bhaav|ghar))\b|"
    r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|"
    r"ninth|tenth|eleventh|twelfth)\s+(house|bhav)\b|"
    r"\b(lagna|ascendant|kendra|trikona|dusthana)\b|"
    r"\b(\dh|h\d)\b",
    re.IGNORECASE,
)
_SIGN_RX = re.compile(
    r"\b(aries|mesh|mesha|taurus|vrish|vrishabh|gemini|mithun|"
    r"cancer|kark|karka|leo|singh|simha|virgo|kanya|"
    r"libra|tula|scorpio|vrishchik|vrischik|sagittarius|dhanu|"
    r"capricorn|makar|aquarius|kumbh|pisces|meen)\b",
    re.IGNORECASE,
)
_JARGON_RX = re.compile(
    # NOTE: bare "yog" is intentionally NOT banned — it is the user-facing
    # word in "property yog kaisa hai" and appears in engine final verdict.
    # Compound jargon (dhana-yog, raj-yog, gajakesari) IS banned.
    r"\b(yoga|dasha|mahadasha|antardasha|antar[\s-]?dasha|"
    r"nakshatra|nakshatr|pada|"
    r"karaka|karak|"
    r"aspect|drishti|dristi|conjunction|conjunct|"
    r"retrograde|retrogression|combust|combustion|"
    r"navamsha|navamsh|d9|d10|"
    r"sub[\s-]?lord|csl|kp|"
    r"dhana[\s-]?yog|lakshmi[\s-]?yog|raj[\s-]?yog|gajakesari)\b",
    re.IGNORECASE,
)
_TIMING_RX = re.compile(
    r"\b(coming|next|upcoming|aane\s+wale|aane\s+wala|aane\s+wali|"
    r"aage\s+chal\s+ke|"
    r"\d+\s*(saal|saalon|year|years|month|months|mahine|mahino|"
    r"din|days|week|weeks|hafte)|"
    r"is\s+(saal|year|month|mahine|mahina|hafte|week)|"
    r"agle\s+(saal|year|mahine|month|hafte|week)|"
    r"jaldi|soon|kuch\s+(din|mahine|saal)|"
    r"abhi\s+(jaldi|nahi)|"
    r"upcoming\s+(months|years|phase|window|period)|"
    r"good\s+(period|phase|window|time)|"
    r"favou?rable\s+(period|phase|window|time)|"
    r"lucky\s+(window|phase|period))\b",
    re.IGNORECASE,
)
_FEAR_RX = re.compile(
    r"\b(danger|khatra|khatarnak|ghatak|fatal|"
    r"loss\s+confirm|guaranteed\s+loss|destruction|"
    r"sure\s+(loss|fail|disaster))\b",
    re.IGNORECASE,
)
_ABSTRACT_RX = re.compile(
    r"\b(fuel|reserve|baseline|channel|axis|framework)\b",
    re.IGNORECASE,
)


def _sanitize_property_reply(text: str) -> str:
    """Strip leaks: planets, houses, signs, jargon, timing, fear,
    abstract metaphors. Replace with safe equivalents."""
    if os.environ.get("PROPERTY_REPLY_SANITIZER", "1") == "0":
        return text
    if not text:
        return text

    # Drop planet names entirely (they shouldn't be there)
    text = _PLANET_RX.sub("indicator", text)
    # Drop house references
    text = _HOUSE_RX.sub("area", text)
    # Drop sign names
    text = _SIGN_RX.sub("", text)
    # Drop jargon
    text = _JARGON_RX.sub("pattern", text)
    # Drop timing words/phrases
    text = _TIMING_RX.sub("", text)
    # Soften fear words
    text = _FEAR_RX.sub("caution", text)
    # Replace abstract metaphors
    text = _ABSTRACT_RX.sub(
        lambda m: {
            "fuel": "energy", "reserve": "saving", "baseline": "base",
            "channel": "support", "axis": "side", "framework": "pattern",
        }.get(m.group(0).lower(), m.group(0)),
        text,
    )
    # Collapse double-spaces left by substitutions
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    return text.strip()


# ──────────────────────────────────────────────────────────────────────
# Word cap (cap-then-final order — body first, verdict appended)
# ──────────────────────────────────────────────────────────────────────
def _enforce_word_cap(text: str, max_words: int = 110) -> str:
    if not text:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",;:") + "."


# ──────────────────────────────────────────────────────────────────────
# LLM call — Signal-Pack → narrative
# ──────────────────────────────────────────────────────────────────────
_SYS_PROMPT = (
    "You are a Vedic-astrology PROPERTY translator. The ENGINE has "
    "already done all chart analysis and given you a SIGNAL PACK "
    "(JSON) with 4 dims: yog, capacity, risk, type_fit — each "
    "pre-classified with a state and a plain-Hinglish reason. "
    "Your job: read the user's question, pick the relevant dims, "
    "and answer in 4 short beats using ONLY the signals.\n\n"
    "🛑 STRICT INPUT DISCIPLINE:\n"
    "• USE ONLY signals in the JSON. The JSON is the COMPLETE truth.\n"
    "• Do NOT infer new astrological relationships.\n"
    "• If a dim is not relevant, IGNORE it (don't stuff every dim).\n"
    "• If signals are insufficient, say so honestly in 1 calm line.\n\n"
    "MANDATORY 4-BEAT STRUCTURE:\n"
    "1. SNAPSHOT — 1 line: overall property picture (use overall_snapshot).\n"
    "2. CAPACITY — 1-2 lines: acknowledge wealth/saving capacity from "
    "capacity.reason.\n"
    "3. RISK / CAUTION — 1-2 lines: documentation/legal/dispute "
    "caution from risk.reason. If risk=clean, say so calmly.\n"
    "4. TYPE-FIT — 1 line: best property type for them from "
    "type_fit.best (use the plain label, e.g. 'plot or land').\n\n"
    "Length: 80-110 words target, 110 hard cap (engine post-injector "
    "appends Final line separately — do NOT count Final in your budget).\n\n"
    "BANS (sanitizer will strip these — do not produce them):\n"
    "✘ NEVER name planets (Mars/Mangal/Jupiter/Guru/Saturn/Shani/Sun/"
    "Surya/Moon/Chandra/Mercury/Budh/Venus/Shukra/Rahu/Ketu).\n"
    "✘ NEVER name houses (4th house, 11th bhav, lagna, kendra, dusthana).\n"
    "✘ NEVER name signs (Aries/Mesh/Vrishabh/Mithun etc.).\n"
    "✘ NEVER use jargon (yog, dasha, karaka, aspect, drishti, "
    "navamsha, KP, sub-lord, gajakesari, raj-yog, dhana-yog).\n"
    "✘ NEVER predict TIMING ('coming months', 'next year', 'jaldi', "
    "'abhi', 'kuch mahino me', 'aane wale saal', 'agle mahine', "
    "any month/year/date numbers, 'lucky window', 'good period', "
    "'favorable phase'). This is a STATIC engine.\n"
    "✘ NEVER use abstract metaphors (fuel, reserve, baseline, "
    "channel, axis, framework).\n"
    "✘ NEVER use fear words (danger, khatarnak, ghatak, fatal, "
    "destruction, sure loss).\n"
    "✘ NEVER write your own '👉 Final:' line — engine appends it. "
    "If you write one, it will be stripped and replaced.\n\n"
    "TONE: warm, grounded, like a knowledgeable friend. Direct. "
    "Hinglish (Hindi-English mix). NO greetings (Beta/Pranam). "
    "NO 'I sense', 'I feel'."
)


def _render_signal_based_narrative_llm(signal_pack: dict,
                                        question: str) -> str:
    """Call LLM with signal-pack JSON. Returns sanitized + capped text
    WITHOUT final verdict (force_final_verdict appends it after)."""
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return _render_static_fallback(signal_pack)
    except Exception:
        return _render_static_fallback(signal_pack)

    pack_json = json.dumps(signal_pack, ensure_ascii=False, indent=2)
    user_msg = (
        f"USER QUESTION: {question}\n\n"
        f"ENGINE SIGNAL PACK:\n{pack_json}\n\n"
        "Now write the answer per rules above (4 beats, ≤110 words, "
        "do NOT write a Final line)."
    )

    try:
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": _SYS_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=600,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return _render_static_fallback(signal_pack)
        text = _sanitize_property_reply(text)
        # Cap body BEFORE final verdict is appended (cap-then-final)
        body_only = _FINAL_LINE_RX.sub("", text).rstrip()
        return _enforce_word_cap(body_only, max_words=110)
    except Exception as e:
        print(f"[property_static.signal] llm failed: {e}", flush=True)
        return _render_static_fallback(signal_pack)


def _render_static_fallback(signal_pack: dict) -> str:
    """Pure-static fallback (no LLM) — used if LLM unavailable.
    4 beats from signal-pack data only."""
    dims = signal_pack.get("dims") or {}
    yog  = (dims.get("yog") or {}).get("reason", "")
    cap  = (dims.get("capacity") or {}).get("reason", "")
    risk = (dims.get("risk") or {}).get("reason", "")
    tf   = dims.get("type_fit") or {}
    snapshot = signal_pack.get("overall_snapshot", "")
    return (
        f"{snapshot}\n\n"
        f"{cap}\n\n"
        f"{risk}\n\n"
        f"Aapke chart me {tf.get('best', 'new home')} ka indication "
        f"sabse strong hai."
    )


# ──────────────────────────────────────────────────────────────────────
# Public entry — handle_property_question
# ──────────────────────────────────────────────────────────────────────
def handle_property_question(question: str, kundli: dict,
                              birth: dict | None = None
                              ) -> Optional[Dict[str, Any]]:
    """Entry point. Returns reply dict or None.

    Returns None if:
      - PROPERTY_STATIC_BYPASS=1
      - Question is not a property Q
      - Question is a TIMING property Q (refused with safe template)
        — actually returned with text, not None, because we own the
        topic and we want to give the polite refusal.
    """
    if os.environ.get("PROPERTY_STATIC_BYPASS", "0") == "1":
        return None
    if not isinstance(question, str) or not question.strip():
        return None

    # Timing property Q → polite static refusal (engine owns it)
    if is_timing_property_question(question):
        return {
            "text":   TIMING_REJECT_TEMPLATE,
            "mode":   "WARNING",
            "route":  "TIMING_PROPERTY_BLOCKED",
            "scope":  _SCOPE,
            "dimensions": None,
            "cache_hit":  False,
        }

    if not is_property_question(question):
        return None

    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {
            "text": ("Property analysis aapki janm-kundli ke bina "
                     "possible nahi. Pehle birth details save karein.\n\n"
                     "👉 Final: Pehle kundli, fir property analysis."),
            "mode":  "FAILSAFE",
            "route": "no_kundli",
            "scope": _SCOPE,
            "dimensions": None,
            "cache_hit":  False,
        }

    # ── Engine compute ──────────────────────────────────────────────
    facts = compute_property_facts(kundli)
    pack  = _build_signal_pack(facts)

    # ── LLM expression (or static fallback) ─────────────────────────
    if os.environ.get("PROPERTY_SIGNAL_PACK", "1") == "0":
        body = _render_static_fallback(pack)
        # Architect-flagged: sanitizer must run on fallback path too
        body = _sanitize_property_reply(body)
        body = _enforce_word_cap(body, max_words=110)
    else:
        body = _render_signal_based_narrative_llm(pack, question)

    # ── Force-final-verdict (mandatory) ─────────────────────────────
    final_text = _force_final_verdict(body, pack)

    mode, route = route_property_question(question)
    return {
        "text":       final_text,
        "mode":       mode,
        "route":      route,
        "scope":      _SCOPE,
        "dimensions": facts.get("dimensions"),
        "cache_hit":  False,
        "signal_pack_used": True,
    }
