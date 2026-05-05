"""LLM-based question classifier — fallback router for health_static.

Mirror of finance_static.llm_router. When regex falls back to
HYBRID/general_health_overview, this classifier kicks in to deeply
understand the question and re-route to a specific sub-route if
confidence is high.

Cached on a normalised question hash (chart-independent NLU).
"""
from __future__ import annotations
import json
import os
from typing import Optional, Tuple

from health_static.answer_cache import (_normalise_question, get_cached,
                                         put_cached, make_cache_key)


_ROUTE_CATALOG = [
    # WARNINGs — locked safe templates
    ("WARNING",   "CRISIS_REDIRECT",
     "User suicide / self-harm / 'jeena nahi chahta' bol raha hai."),
    ("WARNING",   "DEATH_PREDICTION_BLOCKED",
     "User 'kab marunga' / death-date / longevity prediction maang raha."),
    ("WARNING",   "TIMING_HEALTH_DECLINE",
     "User 'kab beemar honga' / 'kis saal bimari aayegi' puchh raha."),
    ("WARNING",   "TIMING_RECOVERY",
     "User 'kab thik honga' / cure-date / recovery exact date maang raha."),
    ("WARNING",   "TIMING_SURGERY",
     "User operation / surgery muhurat / shastra-kriya date puchh raha."),
    ("WARNING",   "DIAGNOSIS_DEMAND",
     "User 'mujhe kya bimari hai chart se' specific disease name maang raha."),
    ("WARNING",   "CURE_GUARANTEE_BLOCKED",
     "User 100% cure / guarantee thik / specific disease cure puchh raha."),
    # DIRECTs — engine-only
    ("DIRECT",    "vitality_check",
     "Overall health/vitality/sehat verdict — 'meri sehat kaisi' type Q."),
    ("DIRECT",    "yoga_check",
     "Specifically chart me Arishta / Balarishta / Vipreet-Recovery yoga audit."),
    # NARRATIVEs — engine + LLM polish
    ("NARRATIVE", "disease_risk",
     "Baar-baar beemar, immunity weak, recovery slow type behavioural Q."),
    ("NARRATIVE", "chronic_risk",
     "Long-term / chronic / lambi bimari / hereditary risk Q."),
    ("NARRATIVE", "mental_health",
     "Stress, anxiety, depression, mood, sleep, mental peace Q."),
    ("NARRATIVE", "accident_risk",
     "Accident chance, injury risk, sudden physical-harm Q."),
    # HYBRID — ultimate fallback
    ("HYBRID",    "general_health_overview",
     "Koi general health/swasthya Q jo upar fit nahi hota."),
]


def _build_catalog_block() -> str:
    return "\n".join(
        f'  "{r}" ({m}) — {d}' for (m, r, d) in _ROUTE_CATALOG
    )


_VALID_ROUTES = {r: m for (m, r, _d) in _ROUTE_CATALOG}


def _model_name() -> str:
    return os.environ.get("HEALTH_ROUTER_MODEL", "gpt-5-nano")


def _classify_via_llm(question: str) -> Optional[dict]:
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return None
    except Exception:
        return None

    catalog = _build_catalog_block()
    sys_prompt = (
        "Aap ek question-classifier ho ek Vedic-astrology HEALTH "
        "(non-timing) engine ke liye. Aapka kaam: user ke health-related "
        "question ko samajhke best-fit sub-route choose karna.\n\n"
        "RULES:\n"
        "1. ONLY pick a route from the catalog below.\n"
        "2. Output STRICT JSON only — no prose, no markdown.\n"
        "3. Schema: {\"route\":\"<route_name>\",\"mode\":\"<mode>\","
        "\"confidence\":<0.0-1.0>,\"reason\":\"<one short Hinglish phrase>\"}\n"
        "4. confidence: 0.9+ if Q clearly fits one route; 0.7-0.9 if "
        "fits but compound; below 0.7 → return route='general_health_overview', "
        "mode='HYBRID'.\n"
        "5. WARNING routes ONLY if user explicitly asks the dangerous / "
        "blocked thing (death-date / specific disease diagnosis / cure "
        "guarantee / surgery muhurat / suicide phrasing / kab beemar "
        "honga). For mere mention of the topic, do NOT use WARNING.\n"
        "6. CRISIS_REDIRECT has highest priority — if ANY hint of "
        "self-harm / suicide / 'jeena nahi chahta' phrasing, pick it "
        "with confidence 1.0.\n"
        "7. Sensitive topics (mental/reproductive/parent-health/addiction) "
        "still go to NARRATIVE routes (mental_health / disease_risk / "
        "chronic_risk) — softening happens at reply layer.\n\n"
        f"CATALOG:\n{catalog}"
    )
    try:
        resp = client.chat.completions.create(
            model=_model_name(),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": question},
            ],
            max_tokens=2500,
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            return None
        return json.loads(raw)
    except Exception as e:
        print(f"[health_static.llm_router] classify failed: {e}",
              flush=True)
        return None


def classify_health_question(question: str
                              ) -> Tuple[Optional[str], Optional[str],
                                         float, str]:
    """Returns (mode, route, confidence, reason)."""
    if not question or not question.strip():
        return (None, None, 0.0, "empty question")

    q_norm = _normalise_question(question)
    if not q_norm:
        return (None, None, 0.0, "empty after normalise")
    cache_key = make_cache_key(birth=None, kundli={}, topic="health_router",
                                route="classify", question=q_norm)
    cached = get_cached(cache_key)
    if cached:
        meta = cached.get("meta") or {}
        return (meta.get("mode"), meta.get("route"),
                float(meta.get("confidence") or 0.0),
                meta.get("reason") or "cached")

    parsed = _classify_via_llm(question)
    if not isinstance(parsed, dict):
        return (None, None, 0.0, "llm classify returned non-dict")

    route = (parsed.get("route") or "").strip()
    if route not in _VALID_ROUTES:
        return (None, None, 0.0, f"invalid route '{route}'")

    mode = _VALID_ROUTES[route]
    try:
        conf = float(parsed.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    reason = str(parsed.get("reason") or "")[:200]

    put_cached(cache_key, _raw_text(parsed), {
        "mode": mode, "route": route,
        "confidence": conf, "reason": reason,
    })
    return (mode, route, conf, reason)


def _raw_text(d: dict) -> str:
    try:
        return json.dumps(d, ensure_ascii=False)
    except Exception:
        return ""
