"""Health reply builder (3 modes — supportive tone).

Modes:
  WARNING   -> locked safe-template (0 LLM tokens)
  DIRECT    -> format engine 5-dim facts as Hinglish (0 LLM tokens)
  NARRATIVE -> engine facts + 60-80w LLM polish (cached)
  HYBRID    -> DIRECT picture + short LLM narrative tailored to question

Tone discipline (per user directive):
  - SUPPORTIVE + CALM + NON-ALARMING (NEVER blunt finance-tone)
  - No fear amplification — "dhyan dena chahiye" not "danger"
  - Sensitive buckets (mental/repro/parent/addiction) get extra soft
    closing + bucket-specific helpline/specialist mention
  - Doctor disclaimer ALWAYS appended (validator enforces)

Public:
  handle_health_question(question, kundli, birth) -> dict | None
"""
from __future__ import annotations
import os
import time as _time
from typing import Any, Dict, Optional

from health_static.health_facts import compute_health_facts
from health_static.health_routing import (is_health_question,
                                           route_health_question,
                                           detect_sensitive_bucket)
from health_static.health_warnings import WARNINGS
from health_static.answer_cache import (make_cache_key, get_cached,
                                         put_cached, _chart_fingerprint)
from health_static.telemetry import log_event as _telemetry_log
from health_static.validator import (validate_health_llm_output,
                                      apply_safety_tail,
                                      DOCTOR_DISCLAIMER)


_PATH_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}

# Standard dims: GREEN=strong/good. INVERTED dims: GREEN=low risk (still good).
_DIM_LABEL = {
    "vitality":           "Vitality (body strength)",
    "disease_resistance": "Recovery power",
    "chronic_risk":       "Chronic risk zone",
    "mental_health":      "Mental peace",
    "accident_risk":      "Accident risk zone",
}

# Hinglish translation for verdict words. INVERTED dims get inverted
# language so user reads it correctly (GREEN chronic_risk = "low risk").
_VERDICT_HINGLISH_STD = {
    "GREEN":  "Strong",
    "YELLOW": "Mixed",
    "RED":    "Weak — dhyan dena chahiye",
}
_VERDICT_HINGLISH_INV = {
    "GREEN":  "Low — basic care kaafi",
    "YELLOW": "Mixed — periodic checkup useful",
    "RED":    "Elevated — preventive care important",
}
_TIER_HINGLISH = {
    "high":     "strong support",
    "moderate": "moderate support",
    "low":      "weak / borderline",
    "none":     "support absent",
}


def _verdict_word(dim: dict) -> str:
    table = (_VERDICT_HINGLISH_INV if dim.get("inverted")
             else _VERDICT_HINGLISH_STD)
    return table.get(dim.get("verdict", "?"), dim.get("verdict", "?"))


# ── DIRECT formatters ──────────────────────────────────────────────
def _direct_vitality_check(facts: dict) -> str:
    dims = facts.get("dimensions") or {}
    yogas = facts.get("yogas") or []
    sub = facts.get("sub_flags") or {}

    lines = ["💚 Aapki health picture (5 dimensions):"]
    for key in ("vitality", "disease_resistance", "chronic_risk",
                 "mental_health", "accident_risk"):
        d = dims.get(key) or {}
        v = d.get("verdict", "?")
        emoji = _PATH_EMOJI.get(v, "")
        lines.append(f"  • {_DIM_LABEL[key]}: {emoji} {_verdict_word(d)}")
        if d.get("reason"):
            lines.append(f"      └ {d['reason']}")

    if yogas:
        lines.append(f"\nHealth yogas noted: {', '.join(yogas)}")
    else:
        lines.append("\nKoi major Arishta / Balarishta yog active nahi mila.")

    final = _vitality_one_liner(dims, sub, yogas)
    if final:
        lines.append(f"\nFinal: {final}")
    return "\n".join(lines)


def _vitality_one_liner(dims: dict, sub: dict, yogas: list) -> str:
    vt = dims.get("vitality", {}).get("verdict", "")
    cr = dims.get("chronic_risk", {}).get("verdict", "")
    mh = dims.get("mental_health", {}).get("verdict", "")
    ar = dims.get("accident_risk", {}).get("verdict", "")
    dr = dims.get("disease_resistance", {}).get("verdict", "")

    if vt == "GREEN" and cr == "GREEN" and mh == "GREEN":
        return ("Overall health channels supportive — basic discipline "
                "(neend, paani, exercise) maintain karte raho.")
    if cr == "RED":
        return ("Chronic-risk zone elevated hai — periodic checkup aur "
                "preventive lifestyle (saad khana, regular sleep) "
                "mukhya priority hai.")
    if mh == "RED":
        return ("Mental peace zone stressed dikh raha — meditation / "
                "talking to someone trusted / professional support "
                "consider karna helpful rahega.")
    if vt == "RED":
        return ("Vitality channel weak — proper neend, paani aur "
                "balanced diet pe focus karo, body ko build karne ka "
                "time dena hai.")
    if ar == "RED":
        return ("Accident risk zone elevated — driving, sports, sharp "
                "objects me extra mindfulness rakho, jaldbaazi avoid.")
    if dr == "RED":
        return ("Recovery power kam dikh raha — chhoti illness ko bhi "
                "ignore mat karo, time pe doctor consult karo.")
    if "Vipreet-Recovery" in yogas:
        return ("Mixed picture par Vipreet-Recovery yog active hai — "
                "setbacks ke baad bounce-back ki capacity strong hai.")
    return ("Mixed picture — preventive care + regular checkup aapki "
            "health ke liye sabse achchha plan hai.")


def _direct_yoga_check(facts: dict) -> str:
    yogas = facts.get("yogas") or []
    sub = facts.get("sub_flags") or {}
    lines = ["✨ Health-yoga audit (chart se):"]
    if yogas:
        for y in yogas:
            tag = ""
            if y == "Vipreet-Recovery":
                tag = " (recovery / bounce-back power)"
            elif y == "Arishta":
                tag = " (vitality caution marker)"
            elif y == "Balarishta":
                tag = " (early-life vulnerability marker)"
            lines.append(f"  ✓ {y}{tag}")
    else:
        lines.append("  Koi major Arishta / Balarishta / Vipreet "
                      "yog active nahi.")

    missing = [y for y in ("Arishta", "Balarishta", "Vipreet-Recovery")
               if y not in yogas]
    if missing:
        lines.append(f"\nNot active: {', '.join(missing)}")

    if sub.get("vipreet_recovery_active"):
        final = ("Vipreet-Recovery active hai — setbacks ke baad "
                 "recovery ki capacity classical strong yog hai.")
    elif sub.get("arishta_present") or sub.get("balarishta_present"):
        final = ("Caution-marker yog active hai — preventive lifestyle + "
                 "periodic doctor checkup aapki neend chain me rakhega.")
    elif yogas:
        final = ("Kuch supportive yog hain — par alone enough nahi, "
                 "lifestyle discipline + checkup zaroori.")
    else:
        final = ("Major health-yog absent — yeh neutral hai (na bahut "
                 "achcha na bahut bura), regular care pe focus karo.")
    lines.append(f"\nFinal: {final}")
    return "\n".join(lines)


_DIRECT_FORMATTERS = {
    "vitality_check": _direct_vitality_check,
    "yoga_check":     _direct_yoga_check,
}


# ── NARRATIVE: build engine fact pack for LLM (lean) ────────────────
def _build_llm_fact_block(facts: dict, route: str) -> str:
    dims = facts.get("dimensions") or {}
    sub = facts.get("sub_flags") or {}
    bs = facts.get("brand_safety") or {}
    lines = [
        "═══════════════════════════════════════════════",
        "🔒 HEALTH ENGINE — LOCKED FACTS (do not invent)",
        "═══════════════════════════════════════════════",
    ]
    for key in ("vitality", "disease_resistance", "chronic_risk",
                 "mental_health", "accident_risk"):
        d = dims.get(key) or {}
        inv = " [INVERTED]" if d.get("inverted") else ""
        lines.append(
            f"{_DIM_LABEL[key]}{inv}: {d.get('verdict','?')} "
            f"[severity={d.get('severity','?')}, "
            f"confidence={d.get('confidence','?')}] — "
            f"{d.get('reason','')}"
        )
    lines.append(f"Sub-flags: {sub}")

    yogas = facts.get("yogas") or []
    lines.append(f"Health yogas: {', '.join(yogas) if yogas else 'NONE'}")

    lines.append(
        "BRAND-SAFETY (must obey): doctor_disclaimer_required="
        f"{bs.get('doctor_disclaimer_required')}, "
        f"diagnosis_ban_active={bs.get('diagnosis_ban_active')}, "
        f"death_prediction_blocked={bs.get('death_prediction_blocked')}"
    )
    lines.append("═══════════════════════════════════════════════")
    return "\n".join(lines)


_NARRATIVE_INSTRUCTIONS = {
    "disease_risk": (
        "User asking 'baar-baar beemar / immunity weak / recovery slow'. "
        "Use disease_resistance dimension + Mars/Mercury health + 6L "
        "vipreet logic. SUPPORTIVE tone — never alarming.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Recovery / immunity picture:'\n"
        "Line 2: '• Current channel strength: <one-phrase>'\n"
        "Line 3: '• Mukhya theme: <one-phrase, no disease names>'\n"
        "Line 4: '• Practical step: <one-phrase, lifestyle/diet/checkup>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one calm sentence>'.\n"
        "NO disease names, NO planet names, NO house numbers, "
        "NO 'tumhe X hai' phrasing. Use 'risk indication' not "
        "'tumhe yeh hai'."
    ),
    "chronic_risk": (
        "User asking about chronic / long-term / lambi bimari / "
        "hereditary risk. Use chronic_risk dimension (INVERTED — "
        "GREEN means LOW risk). SUPPORTIVE tone, preventive framing.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Chronic-risk zone picture:'\n"
        "Line 2: '• Current zone level: <one-phrase>'\n"
        "Line 3: '• Mukhya theme: <one-phrase generic>'\n"
        "Line 4: '• Preventive plan: <one-phrase concrete action>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one calm sentence>'.\n"
        "NO disease names, NO 'tumhe X hai', NO fear words."
    ),
    "mental_health": (
        "User asking about stress / anxiety / depression / mood / sleep / "
        "mental peace. EXTREMELY GENTLE tone — this is sensitive bucket. "
        "Use mental_health dimension. Never diagnose, never name "
        "specific disorder.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Mental peace picture:'\n"
        "Line 2: '• Current state: <one-phrase, gentle>'\n"
        "Line 3: '• Mukhya theme: <one-phrase, generic — Moon/peace etc.>'\n"
        "Line 4: '• Supportive step: <one concrete action — meditation, "
        "walk, journaling, professional talk>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one warm calm sentence>'.\n"
        "NO disease/disorder names (depression/anxiety as conditions), "
        "NO 'tumhe X hai', NO fear words. Reply layer will append "
        "helpline mention automatically."
    ),
    "accident_risk": (
        "User asking about accident / injury / sudden harm risk. "
        "INVERTED dim (GREEN = low risk). CALM tone, mindful framing.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Accident-risk zone picture:'\n"
        "Line 2: '• Current zone level: <one-phrase>'\n"
        "Line 3: '• Mukhya theme: <one-phrase generic — Mars/Ketu energy etc>'\n"
        "Line 4: '• Mindful step: <one concrete — driving care, sports "
        "warmup, sharp object care>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one calm sentence>'.\n"
        "NO disease names, NO planet names, NO fear words like 'danger'."
    ),
    "general_health_overview": (
        "User ne general health/swasthya related question pucha hai jo "
        "specific pattern (vitality/disease/chronic/mental/accident) me "
        "fit nahi hota. Engine ne already 5-dimension picture DIRECT "
        "format me upar print kar di hai. Aapka kaam: us picture ke "
        "neeche 50-70 word ka short Hinglish narrative add karo jo:\n"
        "  1. User ki actual question ko address kare (paraphrase mat "
        "     karo, direct supportive answer do)\n"
        "  2. 5-dim verdict ke 1-2 strongest signals ko plain language "
        "     me concrete preventive guidance me convert kare\n"
        "  3. Ek practical takeaway de\n"
        "Format:\n"
        "  Line 1: blank\n"
        "  Line 2: '✏️ Aapke sawal pe focus:'\n"
        "  Line 3-5: 50-70 word narrative\n"
        "  Line 6: blank\n"
        "  Line 7: 'Final: <one calm direct sentence>'\n"
        "NO disease names, NO planet names, NO house numbers, "
        "NO RED/YELLOW/GREEN words, NO 'tumhe X hai' phrasing, "
        "NO fear words (danger/serious/khatarnak), NO timing/date "
        "predictions, NO cure-guarantees."
    ),
}


def _llm_narrative(facts: dict, route: str, question: str,
                    sensitive_bucket: Optional[str]) -> str:
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return _direct_vitality_check(facts)
    except Exception:
        return _direct_vitality_check(facts)

    fact_block = _build_llm_fact_block(facts, route)
    instruction = _NARRATIVE_INSTRUCTIONS.get(
        route, "Summarise the 5-dim health picture in 60-80 words "
               "Hinglish supportive tone. End with 'Final: <one-line>'.")

    bucket_note = ""
    if sensitive_bucket:
        bucket_note = (
            f"\nSENSITIVE BUCKET ACTIVE: {sensitive_bucket} — extra "
            "gentle tone, no labels, no fear words, no diagnosis "
            "phrasing. Reply layer will append a bucket-specific "
            "support line + doctor disclaimer automatically.")

    sys_prompt = (
        "You are a Vedic-astrology HEALTH translator. Tone is "
        "SUPPORTIVE, CALM, NON-ALARMING — never blunt or fear-inducing.\n\n"
        "RULES:\n"
        "1. Use ONLY the LOCKED FACTS below. Never invent planets, "
        "houses, dignities, or yogas not listed.\n"
        "2. Reply in Hinglish, warm and direct.\n"
        "3. End with a line starting 'Final: '.\n"
        "4. No 'Beta', 'Pranam', 'I sense', 'I understand'.\n"
        "5. NEVER write engine codes like 'RED', 'YELLOW', 'GREEN', "
        "'verdict', 'tier', 'severity', 'confidence', 'sub_flags'.\n"
        "6. NEVER mention specific planets, houses, signs, dignities "
        "UNLESS the user explicitly asked WHY / technical / planet name.\n"
        "7. ⚠️ NEVER name a specific disease (diabetes / cancer / "
        "depression / asthma / heart disease etc.) — use generic "
        "phrasing like 'metabolic stress zone', 'cardiac stress zone', "
        "'low-mood zone', 'respiratory zone'.\n"
        "8. ⚠️ NEVER write 'tumhe X hai' / 'aapko X hai' / 'you have X' "
        "— use 'X risk indication present' / 'X zone elevated'.\n"
        "9. ⚠️ NEVER use fear words: 'danger', 'serious problem', "
        "'khatarnak', 'ghatak', 'fatal', 'deadly', 'life-threatening'. "
        "Use 'dhyan dena chahiye', 'preventive care useful', "
        "'important matter' instead.\n"
        "10. ⚠️ NEVER predict death, longevity end, or specific dates "
        "— this engine is NON-TIMING.\n"
        "11. ⚠️ NEVER guarantee cure — use 'supportive indication'.\n"
        "12. Follow the per-route format EXACTLY.\n\n"
        f"{fact_block}{bucket_note}\n\n"
        f"INSTRUCTION: {instruction}"
    )
    try:
        resp = client.chat.completions.create(
            model=os.environ.get("HEALTH_LLM_MODEL", "gpt-5.4"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
            max_tokens=350,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return _direct_vitality_check(facts)
        return text
    except Exception as e:
        print(f"[health_static.llm] narrative call failed: {e}", flush=True)
        return _direct_vitality_check(facts)


# ── Public entry point ──────────────────────────────────────────────
_ENGINE_SCOPE = "non_timing"


def handle_health_question(question: str, kundli: dict,
                            birth: dict | None = None
                            ) -> Optional[Dict[str, Any]]:
    """Route + serve a NON-TIMING general health question."""
    t_start = _time.time()
    chart_fp = _chart_fingerprint(kundli) if isinstance(kundli, dict) else ""
    sensitive = detect_sensitive_bucket(question or "")

    tele_state = {
        "regex_mode": None, "regex_route": None,
        "llm_mode": None, "llm_route": None,
        "llm_confidence": None, "llm_reason": None,
        "validator_flags": [], "validator_action": "none",
        "facts": None,
        "brand_safety_action": None,
        "sensitive_bucket": sensitive,
    }

    def _emit(mode_f: str, route_f: str, cache_hit: bool) -> None:
        try:
            f = tele_state.get("facts") or {}
            dims = (f.get("dimensions") or {}) if isinstance(f, dict) else {}
            kp = (f.get("kp_csl") or {}) if isinstance(f, dict) else {}
            vt = dims.get("vitality") or {}
            dr = dims.get("disease_resistance") or {}
            cr = dims.get("chronic_risk") or {}
            mh = dims.get("mental_health") or {}
            ar = dims.get("accident_risk") or {}
            h1 = (kp.get("h1") or {}) if isinstance(kp, dict) else {}
            h6 = (kp.get("h6") or {}) if isinstance(kp, dict) else {}
            h8 = (kp.get("h8") or {}) if isinstance(kp, dict) else {}
            conflict_flag = any(
                d.get("conflict_flag") for d in (vt, dr, cr, mh, ar)
            ) if dims else None
            low_conf = sum(
                1 for d in (vt, dr, cr, mh, ar)
                if d.get("confidence") == "LOW"
            ) if dims else None

            _telemetry_log({
                "ts": int(t_start),
                "question": question or "",
                "chart_fp": chart_fp,
                "regex_mode": tele_state["regex_mode"],
                "regex_route": tele_state["regex_route"],
                "llm_mode": tele_state["llm_mode"],
                "llm_route": tele_state["llm_route"],
                "llm_confidence": tele_state["llm_confidence"],
                "llm_reason": tele_state["llm_reason"],
                "final_mode": mode_f,
                "final_route": route_f,
                "cache_hit": cache_hit,
                "latency_ms": int((_time.time() - t_start) * 1000),
                "validator_flags": tele_state["validator_flags"],
                "validator_action": tele_state["validator_action"],
                "vitality_v": vt.get("verdict") if dims else None,
                "disease_v": dr.get("verdict") if dims else None,
                "chronic_v": cr.get("verdict") if dims else None,
                "mental_v": mh.get("verdict") if dims else None,
                "accident_v": ar.get("verdict") if dims else None,
                "kp_h1_v": (
                    f"{h1.get('csl_planet','?')}/{h1.get('verdict','?')}"
                    if h1 else None),
                "kp_h6_v": (
                    f"{h6.get('csl_planet','?')}/{h6.get('verdict','?')}"
                    if h6 else None),
                "kp_h8_v": (
                    f"{h8.get('csl_planet','?')}/{h8.get('verdict','?')}"
                    if h8 else None),
                "kp_engine_ver": kp.get("engine_version") if kp else None,
                "conflict_flag": conflict_flag,
                "confidence_low_count": low_conf,
                "brand_safety_action": tele_state["brand_safety_action"],
                "sensitive_bucket": tele_state["sensitive_bucket"],
            })
        except Exception:
            pass

    if not is_health_question(question or ""):
        return None
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        out = {
            "text": ("Health analysis aapki janm-kundli ke bina possible "
                      "nahi. Pehle birth details save karein.\n\n"
                      f"{DOCTOR_DISCLAIMER}\n\n"
                      "Final: Pehle kundli, fir health analysis."),
            "mode": "FAILSAFE", "route": "no_kundli",
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": None,
        }
        _emit("FAILSAFE", "no_kundli", False)
        return out

    mode, route = route_health_question(question)
    tele_state["regex_mode"] = mode
    tele_state["regex_route"] = route

    # ── WARNING — locked safe template (no engine, no LLM, no cache) ──
    if mode == "WARNING":
        raw_text = WARNINGS.get(route, "")
        # MANDATORY doctor disclaimer guarantee on every WARNING reply
        # (architect H2 fix — CRISIS_REDIRECT lacked it before). Other
        # warnings already include disclaimer text so apply_safety_tail
        # detects it and is a no-op.
        text, w_flags = apply_safety_tail(raw_text,
                                           sensitive_bucket=sensitive)
        bs = [f"warning:{route}"]
        if "doctor_disclaimer_added" in w_flags:
            bs.append("doctor_disclaimer_added")
        tele_state["validator_flags"] = w_flags
        tele_state["validator_action"] = "warning_tail"
        tele_state["brand_safety_action"] = ",".join(bs)
        out = {
            "text": text, "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": None,
            "router": None,
            "sensitive_bucket": sensitive,
        }
        _emit(mode, route, False)
        return out

    # ── HYBRID re-route via LLM classifier (Option A — runs BEFORE cache) ──
    router_meta = None
    if mode == "HYBRID" and route == "general_health_overview":
        try:
            from health_static.llm_router import classify_health_question
            cls_mode, cls_route, conf, reason = classify_health_question(
                question)
        except Exception as _re:
            print(f"[health_static] llm_router error: {_re}", flush=True)
            cls_mode = cls_route = None
            conf = 0.0
            reason = "router exception"
        tele_state["llm_mode"] = cls_mode
        tele_state["llm_route"] = cls_route
        tele_state["llm_confidence"] = conf
        tele_state["llm_reason"] = reason
        router_meta = {"cls_mode": cls_mode, "cls_route": cls_route,
                        "confidence": conf, "reason": reason}
        if (cls_mode and cls_route and conf >= 0.75
                and not (cls_mode == "HYBRID"
                         and cls_route == "general_health_overview")):
            mode, route = cls_mode, cls_route
            if mode == "WARNING":
                raw_w = WARNINGS.get(route, "")
                text_w, w_flags = apply_safety_tail(
                    raw_w, sensitive_bucket=sensitive)
                bs = [f"warning:{route}", "via_llm_router"]
                if "doctor_disclaimer_added" in w_flags:
                    bs.append("doctor_disclaimer_added")
                tele_state["validator_flags"] = w_flags
                tele_state["validator_action"] = "warning_tail"
                tele_state["brand_safety_action"] = ",".join(bs)
                out = {
                    "text": text_w, "mode": mode, "route": route,
                    "scope": _ENGINE_SCOPE,
                    "dimensions": None, "cache_hit": False,
                    "engine_facts": None, "router": router_meta,
                    "sensitive_bucket": sensitive,
                }
                _emit(mode, route, False)
                return out

    # ── Cache check ──
    _q_for_key = question if mode == "HYBRID" else None
    cache_key = make_cache_key(birth, kundli, "health_static", route,
                                question=_q_for_key)
    cached = get_cached(cache_key)
    if cached:
        out = {
            "text": cached["text"], "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": cached.get("meta", {}).get("dimensions"),
            "cache_hit": True, "engine_facts": None,
            "router": router_meta,
            "sensitive_bucket": sensitive,
        }
        _emit(mode, route, True)
        return out

    # ── Compute facts ──
    facts = compute_health_facts(kundli)
    tele_state["facts"] = facts
    if facts.get("error"):
        out = {
            "text": (f"Engine error: {facts['error']}\n\n"
                      f"{DOCTOR_DISCLAIMER}\n\n"
                      "Final: Kundli check karein."),
            "mode": "FAILSAFE", "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": facts,
            "router": router_meta,
            "sensitive_bucket": sensitive,
        }
        _emit("FAILSAFE", route, False)
        return out

    # ── Build text per mode (validator runs on every LLM-touched mode) ──
    if mode == "DIRECT":
        formatter = _DIRECT_FORMATTERS.get(route, _direct_vitality_check)
        raw_text = formatter(facts)
        # DIRECT text is engine-controlled deterministic — MUST NOT pass
        # through LLM-scrubbing validator (it would strip legitimate
        # words like 'dimensions' and 'Arishta'). Only attach safety
        # tail (final-line + sensitive-bucket extra + doctor disclaimer).
        text, v_flags = apply_safety_tail(raw_text,
                                           sensitive_bucket=sensitive)
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = (
            "soft_tail" if v_flags else "none"
        )
    elif mode == "HYBRID":
        direct_text = _direct_vitality_check(facts)
        narrative_raw = _llm_narrative(facts, route, question, sensitive)
        narrative, v_flags, v_action = validate_health_llm_output(
            narrative_raw,
            user_question=question,
            sensitive_bucket=sensitive,
            allowed_yogas=facts.get("yogas") or [],
            direct_fallback_text="",
        )
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = v_action
        # Strip 'Final:' from direct so combined text has only one
        direct_clean = "\n".join(
            ln for ln in direct_text.splitlines()
            if not ln.strip().lower().startswith("final:")
        )
        text = direct_clean.rstrip() + "\n\n" + narrative.lstrip()
    else:  # NARRATIVE
        narrative_raw = _llm_narrative(facts, route, question, sensitive)
        fallback_for_validator = _direct_vitality_check(facts)
        text, v_flags, v_action = validate_health_llm_output(
            narrative_raw,
            user_question=question,
            sensitive_bucket=sensitive,
            allowed_yogas=facts.get("yogas") or [],
            direct_fallback_text=fallback_for_validator,
        )
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = v_action

    # Set brand_safety_action telemetry tag (compact summary)
    bs_actions = []
    if "doctor_disclaimer_added" in tele_state["validator_flags"]:
        bs_actions.append("doctor_disclaimer_added")
    if any(f.startswith("disease_name") for f in tele_state["validator_flags"]):
        bs_actions.append("diagnosis_ban_triggered")
    if "diagnosis_assert_softened" in tele_state["validator_flags"]:
        bs_actions.append("assert_softened")
    if "fear_softened" in tele_state["validator_flags"]:
        bs_actions.append("fear_softened")
    if "cure_guarantee_softened" in tele_state["validator_flags"]:
        bs_actions.append("cure_softened")
    if "death_prediction_stripped" in tele_state["validator_flags"]:
        bs_actions.append("death_stripped")
    if sensitive:
        bs_actions.append(f"sensitive:{sensitive}")
    tele_state["brand_safety_action"] = ",".join(bs_actions) or "none"

    put_cached(cache_key, text, {
        "dimensions": facts.get("dimensions"),
        "composite": facts.get("composite_score"),
        "mode": mode, "route": route,
        "sensitive_bucket": sensitive,
    })

    out = {
        "text": text, "mode": mode, "route": route,
        "scope": _ENGINE_SCOPE,
        "dimensions": facts.get("dimensions"),
        "cache_hit": False, "engine_facts": facts,
        "router": router_meta,
        "sensitive_bucket": sensitive,
    }
    _emit(mode, route, False)
    return out
