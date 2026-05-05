"""LLM-based question classifier — fallback router for finance_engine.

Per user directive (Option A + gpt-5-nano):
  - Regex tries first (fast, 0-cost) in finance_routing.py
  - When regex falls back to HYBRID/general_finance_overview, this
    classifier kicks in to deeply understand the question and re-route
    to a specific sub-route if confidence is high.

Returns a tuple (mode, route, confidence, reason). If LLM call fails or
confidence is low, returns (None, None, 0.0, '...') so caller keeps HYBRID.

Cached on a normalised question hash (no chart needed — pure NLU).
"""
from __future__ import annotations
import json
import os
from typing import Optional, Tuple

from finance_engine.answer_cache import (_normalise_question, get_cached,
                                          put_cached, make_cache_key)


# Authoritative catalog of routes the classifier may pick.
# Keep descriptions tight — they form the LLM prompt.
_ROUTE_CATALOG = [
    # WARNINGs — locked templates (re-route ONLY if classifier is sure)
    ("WARNING",   "GUARANTEE_AMOUNT",
     "User maang raha hai ki exact rupee/lakh/crore amount predict karein."),
    ("WARNING",   "LOTTERY_NUMBER",
     "User specific lottery/satta number ya jackpot pick maang raha hai."),
    ("WARNING",   "DEBT_TRAP",
     "User loan se loan / EMI ke liye loan / credit-card se EMI puchh raha."),
    ("WARNING",   "GET_RICH_QUICK",
     "User raato-raat ameer / overnight rich / MLM / scheme puchh raha."),
    ("WARNING",   "FRIENDS_LOAN",
     "User dost/family ko paisa udhaar dene ka jyotish puchh raha."),
    # DIRECTs — engine-only, no LLM polish needed for output
    ("DIRECT",    "wealth_verdict",
     "Overall wealth/dhana/financial picture, will-I-be-rich type Q."),
    ("DIRECT",    "sudden_wealth",
     "Achanak paisa, windfall, inheritance, lottery YOG (haa/na, no number)."),
    ("DIRECT",    "dhana_yoga_check",
     "Specifically chart me dhana/lakshmi/kubera/gaja-kesari yoga audit."),
    # NARRATIVEs — engine + LLM polish for tailored advice
    ("NARRATIVE", "saving_capacity",
     "Saving / bachat kyun nahi hoti, kaise improve karein."),
    ("NARRATIVE", "expense_pattern",
     "Kharcha control, fizul kharch, paisa kharch ho jata hai."),
    ("NARRATIVE", "loan_debt",
     "Loan le sakta hu, karz clear kab, EMI bojh, debt strategy."),
    ("NARRATIVE", "income_source",
     "Salary vs business, naukri vs kaarobaar, kaun sa career-money path."),
    ("NARRATIVE", "business_profit",
     "Business profit/fayda, partnership, startup, apna kaam chalega."),
    ("NARRATIVE", "loss_reasons",
     "Paisa nahi tikta / ud jata / drain / leak — KYUN behaviorally."),
    # HYBRID — ultimate fallback (catch-all general finance)
    ("HYBRID",    "general_finance_overview",
     "Koi general money/dhan/abundance/property/gold Q jo upar fit nahi."),
]


def _build_catalog_block() -> str:
    lines = []
    for mode, route, desc in _ROUTE_CATALOG:
        lines.append(f'  "{route}" ({mode}) — {desc}')
    return "\n".join(lines)


_VALID_ROUTES = {r: m for (m, r, _d) in _ROUTE_CATALOG}


def _model_name() -> str:
    return os.environ.get("FINANCE_ROUTER_MODEL", "gpt-5-nano")


def _classify_via_llm(question: str) -> Optional[dict]:
    """Single LLM call. Returns parsed JSON dict or None on failure."""
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return None
    except Exception:
        return None

    catalog = _build_catalog_block()
    sys_prompt = (
        "Aap ek question-classifier ho ek Vedic-astrology personal-finance "
        "engine ke liye. Aapka kaam: user ke money-related question ko "
        "samajhke us par best-fit sub-route choose karna.\n\n"
        "RULES:\n"
        "1. ONLY pick a route from the catalog below.\n"
        "2. Output STRICT JSON only — no prose, no markdown.\n"
        "3. Schema: {\"route\":\"<route_name>\",\"mode\":\"<mode>\","
        "\"confidence\":<0.0-1.0>,\"reason\":\"<one short Hinglish phrase>\"}\n"
        "4. confidence: 0.9+ if Q clearly fits one route; 0.7-0.9 if "
        "fits but compound; below 0.7 if uncertain (in that case, return "
        "route='general_finance_overview', mode='HYBRID').\n"
        "5. WARNING routes ONLY if user explicitly asks for the dangerous "
        "thing (exact amount / lottery number / loan-on-loan / overnight "
        "rich / friend-loan jyotish). For mere mention, do NOT use WARNING.\n"
        "6. Compound Q (e.g. 'paisa kyun nahi tikta aur saving kaise') — "
        "pick the dominant intent (jo zyada actionable hai).\n"
        "7. Timing Qs (kab/when/year) won't reach you — they are filtered "
        "earlier. So don't worry about timing.\n\n"
        f"CATALOG:\n{catalog}"
    )
    try:
        # gpt-5 family: openai_helper auto-patches max_tokens →
        # max_completion_tokens. Omit temperature (rejected by gpt-5).
        resp = client.chat.completions.create(
            model=_model_name(),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": question},
            ],
            # gpt-5-nano burns ~1500 reasoning tokens internally before
            # producing the final JSON. Budget must comfortably cover both.
            max_tokens=2500,
            response_format={"type": "json_object"},
        )
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            return None
        return json.loads(raw)
    except Exception as e:
        print(f"[finance_engine.llm_router] classify failed: {e}",
              flush=True)
        return None


def classify_finance_question(question: str
                               ) -> Tuple[Optional[str], Optional[str],
                                          float, str]:
    """Returns (mode, route, confidence, reason).

    On any failure or low-confidence output, returns (None, None, 0.0,
    '...') so caller falls back to HYBRID flow.
    """
    if not question or not question.strip():
        return (None, None, 0.0, "empty question")

    # Cache lookup — per-question (chart-independent NLU)
    q_norm = _normalise_question(question)
    if not q_norm:
        return (None, None, 0.0, "empty after normalise")
    cache_key = make_cache_key(birth=None, kundli={}, topic="finance_router",
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

    mode = _VALID_ROUTES[route]   # canonical mode from catalog
    try:
        conf = float(parsed.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    reason = str(parsed.get("reason") or "")[:200]

    # Persist for repeat Qs (chart-independent so very high reuse)
    put_cached(cache_key, raw_text(parsed), {
        "mode": mode, "route": route,
        "confidence": conf, "reason": reason,
    })
    return (mode, route, conf, reason)


def raw_text(d: dict) -> str:
    """Tiny helper — store JSON as the cache 'reply_text' field."""
    try:
        return json.dumps(d, ensure_ascii=False)
    except Exception:
        return ""
