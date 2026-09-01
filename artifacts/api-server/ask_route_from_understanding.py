"""Route Ask questions to the right engine AFTER LLM meaning is known.

Rule #1: understand what the user wants → then pick static vs timing engine + archetype.
"""
from __future__ import annotations

import re
from typing import Any

_TIMING_RX = re.compile(
    r"(?ix)\b(kab|when|kitne\s+saal|kis\s+saal|kis\s+umar|"
    r"milega|milegi|hoga|hogi|timing|muhurat|date|month|year|"
    r"samay|shubh\s*samay|abhi|chal\s+raha|chalega|phase|window|period)\b"
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

    try:
        from ask_mr.timing_registry import (
            mr_static_overrides_llm_timing,
            repair_llm_intent_mr_static_timing,
            resolve_mr_static_archetype,
        )

        if repair_llm_intent_mr_static_timing(combined, out):
            pass
        elif mr_static_overrides_llm_timing(combined, out):
            out["is_timing"] = False
            out["domain"] = "love"
            out["mr_archetype"] = out.get("mr_archetype") or resolve_mr_static_archetype(combined)
    except Exception:
        pass

    try:
        from ask_mr.timing_registry import is_marriage_timing_question

        if is_marriage_timing_question(combined, out):
            out["domain"] = "marriage"
            out["is_timing"] = True
            out["mr_archetype"] = out.get("mr_archetype") or "marriage_timing"
            out["routing_label"] = out.get("routing_label") or "marriage_timing"
    except Exception:
        pass

    try:
        from ask_love.timing_registry import is_love_timing_question

        if is_love_timing_question(combined, out):
            out["domain"] = out.get("domain") or "love"
            out["is_timing"] = True
            if str(out.get("mr_archetype") or "").strip().lower() in (
                "one_sided_love",
                "general_mr",
                "partner_nature",
            ):
                out["mr_archetype"] = "dating_courtship"
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

    if re.search(
        r"(?ix)\b(kya\s+wo\s+bhi|utna\s+hi\s+pyaar|jitna\s+main|love\s+me\s+back)\b",
        combined,
    ) and re.search(r"(?ix)\b(pyaar|pyar|prem|love|dil)\b", combined):
        out["domain"] = "love"
        out["is_timing"] = False
        out["mr_archetype"] = "one_sided_love"

    try:
        from ask_mr.timing_registry import mr_static_overrides_llm_timing

        if not mr_static_overrides_llm_timing(combined, out):
            from ask_love.timing_registry import is_love_timing_question

            if is_love_timing_question(combined, out):
                out["domain"] = out.get("domain") or "love"
                out["is_timing"] = True
    except Exception:
        pass

    try:
        from ask_travel.timing_registry import is_travel_timing_question

        if is_travel_timing_question(combined, out):
            out["domain"] = out.get("domain") or "travel"
            out["is_timing"] = True
    except Exception:
        pass

    try:
        from ask_property.timing_registry import is_property_timing_question

        if is_property_timing_question(combined, out):
            out["domain"] = out.get("domain") or "property"
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

    try:
        from ask_mr.timing_registry import repair_llm_intent_mr_static_timing

        repair_llm_intent_mr_static_timing(combined, out)
        from ask_mr.timing_registry import clear_timing_without_when_anchor

        clear_timing_without_when_anchor(combined, out)
    except Exception:
        pass

    try:
        from ask_intent_fidelity import enforce_commitment_archetype_from_question

        enforce_commitment_archetype_from_question(question, out)
    except Exception:
        pass

    if summary:
        out["question_summary"] = summary
        out["question_meaning"] = summary
    out["routing_from"] = "understanding"
    try:
        from ask_intent_fidelity import reconcile_question_type

        _rec = reconcile_question_type(combined, out, mutate=True)
        out = _rec["intent"]
    except Exception:
        pass
    return out


def classify_and_route_ask(
    question: str,
    *,
    client: Any = None,
    understanding: dict[str, Any] | None = None,
    question_raw: str = "",
) -> dict[str, Any]:
    """Understand → classify intent → apply routing patches. Never raises.

    When Question DNA is already trusted, skip the extra intent + understand
    LLM calls (those were stacking to 1–3 minutes on mobile).
    """
    q = (question or "").strip()
    understanding = understanding if isinstance(understanding, dict) else {}
    summary = str(understanding.get("question_summary") or "").strip()

    # ── Fast path: trusted Question DNA already extracted upstream ─────
    _dna_fast = understanding.get("question_dna") if isinstance(understanding.get("question_dna"), dict) else None
    if _dna_fast:
        try:
            from ask_question_dna import (
                apply_question_dna_to_routing,
                dna_item_trusted_for_routing,
                dna_primary_item,
            )

            _item = dna_primary_item(_dna_fast)
            if dna_item_trusted_for_routing(
                _item,
                dna_source=str(_dna_fast.get("source") or ""),
            ):
                admin: dict[str, Any] = dict(understanding)
                res: dict[str, Any] = {
                    "domain": str((_item or {}).get("domain") or "general"),
                    "is_timing": bool((_item or {}).get("timing")),
                    "source": "question_dna",
                }
                apply_question_dna_to_routing(
                    q,
                    admin,
                    _dna_fast,
                    llm_intent=res,
                )
                # Prefer DNA intent/user_wants as the question summary — no
                # second understand LLM call.
                _uw = str((_item or {}).get("user_wants") or (_item or {}).get("intent") or "").strip()
                if _uw:
                    admin["question_summary"] = _uw
                    admin["question_meaning"] = _uw
                    res["question_summary"] = _uw
                admin["routed_domain"] = res.get("domain") or admin.get("routed_domain")
                admin["routed_archetype"] = (
                    admin.get("routed_archetype")
                    or admin.get("mr_archetype")
                    or admin.get("dna_engine_archetype")
                )
                admin["routed_timing"] = bool(res.get("is_timing"))
                try:
                    from ask_master_router import finalize_ask_route

                    _mr = finalize_ask_route(
                        q,
                        understanding=admin,
                        llm_intent=res,
                        llm_intent_admin=admin,
                    )
                    res["is_timing"] = bool(_mr.is_timing)
                    admin["routed_timing"] = bool(_mr.is_timing)
                    admin["master_route"] = _mr.to_dict()
                except Exception:
                    pass
                print(
                    f"[route] DNA_FAST_PATH skip_intent_llm "
                    f"domain={admin.get('routed_domain')} "
                    f"archetype={admin.get('routed_archetype')}",
                    flush=True,
                )
                return {
                    "llm_intent": res,
                    "llm_intent_record": res,
                    "llm_intent_admin": admin,
                    "intent_source": "question_dna",
                    "is_timing": bool(res.get("is_timing")),
                    "mr_archetype": admin.get("mr_archetype"),
                    "career_archetype": admin.get("career_archetype"),
                    "finance_archetype": admin.get("finance_archetype"),
                    "health_archetype": admin.get("health_archetype"),
                    "education_archetype": admin.get("education_archetype"),
                    "children_archetype": admin.get("children_archetype"),
                    "property_archetype": admin.get("property_archetype"),
                    "travel_archetype": admin.get("travel_archetype"),
                    "litigation_archetype": admin.get("litigation_archetype"),
                }
        except Exception as _dna_fast_exc:
            print(f"[route] DNA_FAST_PATH skipped: {_dna_fast_exc}", flush=True)

    intent_q = q
    if summary and summary.lower() not in q.lower():
        intent_q = f"{q}\n\n[Understood meaning: {summary}]"

    res = {}
    try:
        from ask_intent_llm import classify_ask_intent

        res = classify_ask_intent(intent_q, client=client) or {}
    except Exception as exc:
        res = {"source": "llm_error", "error": str(exc)[:120], "domain": "general"}

    res = apply_understanding_routing(q, understanding, res)
    try:
        from ask_mr.timing_registry import (
            clear_timing_without_when_anchor,
            repair_llm_intent_mr_static_timing,
        )

        repair_llm_intent_mr_static_timing(q, res)
        clear_timing_without_when_anchor(q, res)
    except Exception:
        pass

    src = str(res.get("source") or "")
    llm_intent = res if src in ("llm", "llm_repaired", "llm_low_conf") else None
    llm_intent_record = res if src not in ("llm_error", "llm_unavailable", "") else None
    intent_source = src if src in ("llm", "llm_repaired", "llm_low_conf") else "regex"

    admin = {**understanding, **{k: v for k, v in res.items() if v is not None}}
    try:
        from ask_question_understand import ensure_question_understanding

        # DNA already provides meaning — don't force a second understand call.
        _force = not bool(admin.get("question_dna"))
        admin = ensure_question_understanding(
            q,
            admin,
            client=client,
            force_llm=_force,
            question_raw=question_raw or q,
        )
    except Exception:
        pass
    # Keep intent routing source on llm_intent fields, not as understanding provenance
    admin.pop("source", None)

    admin["routed_domain"] = res.get("domain")
    admin["routed_archetype"] = (
        res.get("mr_archetype")
        or res.get("career_archetype")
        or res.get("finance_archetype")
        or res.get("health_archetype")
    )
    admin["routed_timing"] = bool(res.get("is_timing"))

    try:
        from ask_master_router import finalize_ask_route

        _mr = finalize_ask_route(
            q,
            understanding=admin,
            llm_intent=res,
            llm_intent_admin=admin,
        )
        res["is_timing"] = bool(_mr.is_timing)
        admin["routed_timing"] = bool(_mr.is_timing)
        admin["master_route"] = _mr.to_dict()
    except Exception:
        pass

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
