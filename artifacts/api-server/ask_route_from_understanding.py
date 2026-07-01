"""Route Ask questions to the right engine AFTER LLM meaning is known.

Rule #1: understand what the user wants → then pick static vs timing engine + archetype.
"""
from __future__ import annotations

import re
from typing import Any

_TIMING_RX = re.compile(
    r"(?ix)\b(kab|when|kitne\s+saal|kis\s+saal|kis\s+umar|"
    r"milega|milegi|hoga|hogi|timing|muhurat|date|month|year)\b"
)

_NATIVE_LOVE_CHART_RX = re.compile(
    r"(?ix)\b("
    r"true\s*love|sach+a\s*pyaar|sach+a\s*pyar|sachchi\s*mohabbat|"
    r"milne\s+ka\s+yog|pyaar\s+milne|pyar\s+milne|prem\s+milne|"
    r"love\s+life|prem\s+sambandh"
    r")\b"
)


def is_native_love_chart_question(text: str) -> bool:
    """Native's own love capacity / true love yog — not partner-spouse subject."""
    return bool(_NATIVE_LOVE_CHART_RX.search(text or ""))


def is_domain_outcome_yoga_love(text: str) -> bool:
    try:
        from chart_fact_answer import is_domain_outcome_yoga_question

        return bool(is_domain_outcome_yoga_question(text or "")) and bool(
            re.search(r"(?ix)\b(love|pyaar|pyar|prem|true\s*love|sach)\b", text or "")
        )
    except Exception:
        return False


def _combined_text(question: str, summary: str) -> str:
    parts = [question or "", summary or ""]
    return " ".join(p for p in parts if p).strip()


def apply_understanding_routing(
    question: str,
    understanding: dict[str, Any] | None,
    intent: dict[str, Any] | None,
) -> dict[str, Any]:
    """Align domain / timing / archetype with understood meaning + question text."""
    out: dict[str, Any] = dict(intent) if isinstance(intent, dict) else {}
    summary = str((understanding or {}).get("question_summary") or out.get("question_summary") or "").strip()
    combined = _combined_text(question, summary)

    try:
        from chart_fact_answer import is_domain_outcome_yoga_question

        if is_domain_outcome_yoga_question(combined):
            out["is_timing"] = False
    except Exception:
        pass

    try:
        from ask_love.timing_registry import is_love_static_loyalty_question

        if is_love_static_loyalty_question(combined):
            out["is_timing"] = False
            out["domain"] = "love"
            out["mr_archetype"] = out.get("mr_archetype") or "loyalty_trust"
    except Exception:
        pass

    if is_native_love_chart_question(combined):
        out["domain"] = "love"
        out["is_timing"] = False
        # Force true-love engine — never keep LLM guess chemistry/general_mr here.
        out["mr_archetype"] = "dating_courtship"
    elif is_domain_outcome_yoga_love(combined):
        out["domain"] = "love"
        out["is_timing"] = False
        out["mr_archetype"] = "dating_courtship"

    if _TIMING_RX.search(combined):
        try:
            from ask_love.timing_registry import is_love_timing_question

            if is_love_timing_question(combined, out):
                out["domain"] = out.get("domain") or "love"
                out["is_timing"] = True
        except Exception:
            pass

    try:
        from ask_intent_fidelity import infer_primary_domain, _upgrade_domain_archetypes

        dom = str(out.get("domain") or "general").strip().lower()
        inferred = infer_primary_domain(combined)
        if dom == "general" and inferred:
            out["domain"] = inferred
            _upgrade_domain_archetypes(combined, inferred, out)
        elif dom in ("marriage", "love") and not out.get("mr_archetype"):
            from ask_mr.classifier import classify_mr_archetype

            out["mr_archetype"] = classify_mr_archetype(combined)
        elif dom in ("marriage", "love") and is_native_love_chart_question(combined):
            out["mr_archetype"] = "dating_courtship"
    except Exception:
        pass

    if summary:
        out["question_summary"] = summary
        out["question_meaning"] = summary
    out["routing_from"] = "understanding"
    return out


def classify_and_route_ask(
    question: str,
    *,
    client: Any = None,
    understanding: dict[str, Any] | None = None,
    question_raw: str = "",
) -> dict[str, Any]:
    """Understand → classify intent → apply routing patches. Never raises."""
    q = (question or "").strip()
    understanding = understanding if isinstance(understanding, dict) else {}
    summary = str(understanding.get("question_summary") or "").strip()

    intent_q = q
    if summary and summary.lower() not in q.lower():
        intent_q = f"{q}\n\n[Understood meaning: {summary}]"

    res: dict[str, Any] = {}
    try:
        from ask_intent_llm import classify_ask_intent

        res = classify_ask_intent(intent_q, client=client) or {}
    except Exception as exc:
        res = {"source": "llm_error", "error": str(exc)[:120], "domain": "general"}

    res = apply_understanding_routing(q, understanding, res)

    src = str(res.get("source") or "")
    llm_intent = res if src in ("llm", "llm_repaired", "llm_low_conf") else None
    llm_intent_record = res if src not in ("llm_error", "llm_unavailable", "") else None
    intent_source = src if src in ("llm", "llm_repaired", "llm_low_conf") else "regex"

    admin: dict[str, Any] = {**understanding, **{k: v for k, v in res.items() if v is not None}}
    try:
        from ask_question_understand import ensure_question_understanding

        admin = ensure_question_understanding(
            q,
            admin,
            client=client,
            force_llm=not bool(str(admin.get("question_summary") or "").strip()),
            question_raw=question_raw or q,
        )
    except Exception:
        pass

    admin["routed_domain"] = res.get("domain")
    admin["routed_archetype"] = (
        res.get("mr_archetype")
        or res.get("career_archetype")
        or res.get("finance_archetype")
        or res.get("health_archetype")
    )
    admin["routed_timing"] = bool(res.get("is_timing"))

    return {
        "llm_intent": llm_intent,
        "llm_intent_record": llm_intent_record,
        "llm_intent_admin": admin,
        "intent_source": intent_source,
        "is_timing": bool(res.get("is_timing")),
        "mr_archetype": res.get("mr_archetype"),
        "career_archetype": res.get("career_archetype"),
        "finance_archetype": res.get("finance_archetype"),
        "health_archetype": res.get("health_archetype"),
        "education_archetype": res.get("education_archetype"),
        "children_archetype": res.get("children_archetype"),
        "property_archetype": res.get("property_archetype"),
        "travel_archetype": res.get("travel_archetype"),
        "litigation_archetype": res.get("litigation_archetype"),
    }
