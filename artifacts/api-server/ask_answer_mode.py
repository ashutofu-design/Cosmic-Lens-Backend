"""Decide how Cosmo should answer: engine vs LLM vs chart-fact.

Product brain (locked):
  chart_fact   — atomic placement lookup only ("Mars kis house me?")
  engine       — personal life outcome with a dedicated engine (shaadi/career/health…)
  llm_chart    — meaning of THEIR chart (no dedicated engine / interpretive)
  llm_knowledge — general astrology education (theory, rules, "X better ya Y")

Understand LLM may set answer_mode; this module validates + falls back deterministically.
"""
from __future__ import annotations

import re
from typing import Any

_VALID_MODES = frozenset({"chart_fact", "engine", "llm_chart", "llm_knowledge"})

_PERSONAL_RX = re.compile(
    r"(?ix)\b("
    r"mera|meri|mere|mujhe|mujhko|main|mai|me|hum|ham|hamari|hamara|"
    r"my|i\s+am|our|myself|kundli\s+me|chart\s+me"
    r")\b",
)

_LIFE_OUTCOME_RX = re.compile(
    r"(?ix)\b("
    r"career|naukri|job|business|promotion|interview|"
        r"shaadi|shadi|marriage|vivah|rishta|partner|boyfriend|girlfriend|"
    r"sehat|health|bimari|illness|disease|hospital|"
    r"santan|santaan|child|children|pregnancy|"
    r"paisa|paise|money|wealth|finance|income|loan|"
    r"property|ghar\s+kharid|flat|visa|abroad|videsh|travel|"
    r"court|case|litigation|education|padhai|exam"
    r")\b",
)

_THEORY_RX = re.compile(
    r"(?ix)\b("
    r"general|theory|concept|definition|rule|rules|usually|normally|"
    r"in\s+astrology|jyotish\s+me|vedic\s+me|"
    r"kya\s+(?:hai|he)|matlab|meaning|explain|samjha|"
    r"acha\s+he\s+ya|accha\s+(?:hai|he)\s+ya|better\s+ya|or\s+exalt|"
    r"ya\s+exalt|vs\.?|versus|compare"
    r")\b",
)


def normalize_answer_mode(raw: Any) -> str | None:
    m = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        # chart_fact path disabled — remap legacy labels to llm_chart
        "chartfact": "llm_chart",
        "chart_fact": "llm_chart",
        "fact": "llm_chart",
        "lookup": "llm_chart",
        "static": "engine",
        "timing": "engine",
        "engine_static": "engine",
        "engine_timing": "engine",
        "dedicated_engine": "engine",
        "llm": "llm_chart",
        "chart_llm": "llm_chart",
        "open_qa": "llm_chart",
        "knowledge": "llm_knowledge",
        "concept": "llm_knowledge",
        "education": "llm_knowledge",
        "general_llm": "llm_knowledge",
    }
    m = aliases.get(m, m)
    if m == "chart_fact":
        m = "llm_chart"
    return m if m in _VALID_MODES else None


def infer_answer_mode(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Deterministic fallback when understand LLM omits / errs on answer_mode."""
    q = (question or "").strip()
    if not q:
        return "llm_knowledge"

    intent = llm_intent if isinstance(llm_intent, dict) else {}
    raw_am = str(intent.get("answer_mode") or "").strip().lower().replace("-", "_").replace(" ", "_")
    from_llm = normalize_answer_mode(intent.get("answer_mode"))

    # chart_fact disabled: never return it; map LLM/legacy chart_fact → llm path.
    if raw_am in ("chart_fact", "chartfact", "fact", "lookup") or from_llm == "chart_fact":
        return "llm_chart" if _PERSONAL_RX.search(q) else "llm_knowledge"

    # Personal life-outcome (career/shaadi/health…) → engine before chart-interpret heuristics.
    if _PERSONAL_RX.search(q) and _LIFE_OUTCOME_RX.search(q):
        return "engine"

    # Interpretive / theory / combo → LLM before engine classifiers (e.g. "house me").
    try:
        from chart_fact_answer import needs_llm_chart_answer

        if needs_llm_chart_answer(q):
            if _THEORY_RX.search(q) or not _PERSONAL_RX.search(q):
                return "llm_knowledge"
            return "llm_chart"
    except Exception:
        pass

    # Classifier-confirmed engines (also covers some non-"mera" phrasings).
    if _personal_engine_match(q, intent):
        return "engine"

    if from_llm in ("engine", "llm_chart", "llm_knowledge"):
        return from_llm

    if _PERSONAL_RX.search(q):
        return "llm_chart"
    return "llm_knowledge"


def _personal_engine_match(question: str, intent: dict[str, Any]) -> bool:
    """True only when a domain classifier matches — not bare domain string."""
    q = (question or "").strip()
    if not q or not _PERSONAL_RX.search(q):
        return False
    _probe = (
        ("ask_marriage_relationship_slice", "is_marriage_relationship_static_question"),
        ("ask_career.classifier", "is_career_static_question"),
        ("ask_children.children_registry", "is_children_static_question"),
        ("ask_health.classifier", "is_health_static_question"),
        ("ask_finance.finance_registry", "is_finance_static_question"),
        ("ask_education.education_registry", "is_education_static_question"),
        ("ask_property.property_registry", "is_property_static_question"),
        ("ask_vehicle.vehicle_registry", "is_vehicle_static_question"),
        ("ask_travel.travel_registry", "is_travel_static_question"),
        ("ask_litigation.litigation_registry", "is_litigation_static_question"),
        ("ask_luck.luck_registry", "is_luck_static_question"),
        ("ask_network.network_registry", "is_network_static_question"),
    )
    for mod_path, fn_name in _probe:
        try:
            import importlib

            if getattr(importlib.import_module(mod_path), fn_name)(q):
                return True
        except Exception:
            continue
    try:
        from ask_gap_dispatch import is_any_gap_static_question

        if is_any_gap_static_question(q, llm_intent=intent):
            return True
    except Exception:
        pass
    return False


def resolve_answer_mode(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Final answer_mode used by router (understand → validate → infer)."""
    intent = llm_intent if isinstance(llm_intent, dict) else {}
    raw = normalize_answer_mode(intent.get("answer_mode"))
    inferred = infer_answer_mode(question, intent)
    # Hard overrides that understand must never break.
    if raw == "engine" and inferred in ("llm_chart", "llm_knowledge"):
        # Understand said engine but Q is interpretive/theory — trust infer.
        mode = inferred
    elif raw in _VALID_MODES:
        mode = raw
    else:
        mode = inferred
    # chart_fact path disabled — always remap to llm_chart.
    if mode == "chart_fact":
        mode = "llm_chart"
    if isinstance(intent, dict):
        intent["answer_mode"] = mode
        intent["answer_mode_source"] = (
            "understand" if raw == mode else "infer_override" if raw else "infer"
        )
    return mode


def is_llm_answer_mode(mode: str | None) -> bool:
    return normalize_answer_mode(mode) in ("llm_chart", "llm_knowledge")
