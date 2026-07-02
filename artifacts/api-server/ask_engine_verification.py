"""Verify static engine + archetype matches question subject and evidence quality."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from ask_intent_fidelity import (
    _PARTNER_SUBJECT_RX,
    archetype_allowed_for_question,
    is_dyadic_couple_question,
    is_partner_relationship_question,
)

# Gap / personality engines — native self only.
_NATIVE_SELF_ARCHETYPES = frozenset({
    "personality_nature",
    "self_appearance",
    "general_personality",
})

_PARTNER_PERSONALITY_RX = re.compile(
    r"(?ix)"
    r"(?:\b(partner|spouse|pati|patni|biwi|husband|wife|jeevan\s*sathi|boyfriend|girlfriend)\b"
    r".{0,80}\b(personality|nature|swabhav|express|reserved|style|kaisa|kaisi|kaise)\b)"
    r"|(?:\b(expressive|reserved)\b.{0,60}\b(partner|spouse|pati|patni)\b)"
    r"|(?:\b(personality|nature|swabhav|style)\b.{0,60}\b(partner|spouse|pati|patni)\b)"
)

_NATIVE_SELF_FOCUS_RX = re.compile(
    r"(?ix)\b(mera\s+swabhav|meri?\s+nature|main\s+kaisa|who\s+am\s+i|kaun\s+hu|about\s+me)\b"
)


@dataclass
class EngineVerificationResult:
    ok: bool
    action: str  # keep | reroute_mr | d1_open_chart
    reason: str
    mr_archetype: str | None = None
    failed_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_partner_personality_question(question: str) -> bool:
    q = (question or "").strip()
    if not q or not _PARTNER_SUBJECT_RX.search(q):
        return False
    return bool(_PARTNER_PERSONALITY_RX.search(q))


def should_suppress_gap_for_question(
    question: str,
    *,
    gap_key: str | None = None,
) -> bool:
    """Partner / spouse subject must not use native-only gap engines (personality, etc.)."""
    q = (question or "").strip()
    if not q:
        return False
    if not _PARTNER_SUBJECT_RX.search(q):
        return False
    if gap_key == "personality":
        return True
    if is_partner_personality_question(q):
        return True
    if gap_key and gap_key in ("anger", "dreams", "wellness") and _PARTNER_PERSONALITY_RX.search(q):
        return True
    return False


def suggest_mr_archetype_for_question(question: str) -> str | None:
    """Best MR archetype when verification reroutes from wrong engine."""
    q = (question or "").strip()
    if not q:
        return None
    if is_partner_relationship_question(q):
        try:
            from ask_mr.classifier import classify_mr_archetype

            return classify_mr_archetype(q) or "partner_nature"
        except Exception:
            return "partner_nature"
    if is_dyadic_couple_question(q) and re.search(
        r"(?ix)\b(chemistry|attraction|spark|passion|romance|romantic|intense)\b",
        q,
    ):
        return "general_mr"
    if is_partner_personality_question(q):
        return "partner_nature"
    if _PARTNER_SUBJECT_RX.search(q):
        try:
            from ask_mr.classifier import classify_mr_archetype

            return classify_mr_archetype(q) or "partner_nature"
        except Exception:
            return "partner_nature"
    return None


def apply_partner_relationship_static_flags(
    question: str,
    *,
    is_mr_static: bool,
    is_health_static: bool,
    llm_intent: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    """Partner-fit questions → MR on, health off."""
    try:
        from ask_intent_fidelity import is_partner_relationship_question

        if is_partner_relationship_question(question or ""):
            if isinstance(llm_intent, dict):
                llm_intent["health_archetype"] = None
                if str(llm_intent.get("domain") or "general").strip().lower() in ("", "general", "health"):
                    llm_intent["domain"] = "love"
                    llm_intent["mr_archetype"] = llm_intent.get("mr_archetype") or "partner_nature"
            return True, False
    except Exception:
        pass
    return is_mr_static, is_health_static


def apply_love_life_area_static_flags(
    question: str,
    *,
    is_mr_static: bool,
    is_health_static: bool,
    llm_intent: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    """Love/career meaning from placement — open chart QA or MR; never health/skin."""
    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question
        from ask_chart_open_qa import is_native_self_chart_interpretation_question

        if is_domain_life_area_interpretation_question(question or ""):
            if isinstance(llm_intent, dict):
                llm_intent["health_archetype"] = None
                llm_intent["is_timing"] = False
                if is_native_self_chart_interpretation_question(question or ""):
                    llm_intent["open_chart_qa"] = True
                    llm_intent["mr_archetype"] = "open_chart_qa"
                    dom = str(llm_intent.get("domain") or "").strip().lower()
                    if dom in ("", "general", "health"):
                        llm_intent["domain"] = "love"
                    return False, False
                from ask_mr.classifier import classify_mr_archetype

                dom = str(llm_intent.get("domain") or "").strip().lower()
                if dom in ("", "general", "health"):
                    llm_intent["domain"] = "love"
                llm_intent["mr_archetype"] = (
                    llm_intent.get("mr_archetype")
                    or classify_mr_archetype(question or "")
                    or "partner_nature"
                )
            return True, False
    except Exception:
        pass
    return is_mr_static, is_health_static


def apply_pre_route_guards(
    flags: dict[str, bool],
    question: str,
    *,
    gap_key: str | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> tuple[dict[str, bool], list[str]]:
    """Correct flags before resolver picks winner."""
    out = {k: bool(v) for k, v in (flags or {}).items()}
    notes: list[str] = []

    if should_suppress_gap_for_question(question, gap_key=gap_key):
        if out.get("gap"):
            out["gap"] = False
            notes.append("gap:suppressed_partner_subject")
        out["mr"] = True
        notes.append("mr:forced_partner_subject")

    if is_partner_personality_question(question):
        out["mr"] = True
        out["gap"] = False
        notes.append("mr:partner_personality")

    if is_partner_relationship_question(question):
        if out.get("health"):
            out["health"] = False
            notes.append("health:suppressed_partner_relationship")
        for wrong in ("career", "finance", "education", "children", "property", "vehicle", "travel", "litigation"):
            if out.get(wrong):
                out[wrong] = False
                notes.append(f"{wrong}:suppressed_partner_relationship")
        out["mr"] = True
        notes.append("mr:forced_partner_relationship")

    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question

        if is_domain_life_area_interpretation_question(question):
            out["health"] = False
            try:
                from ask_chart_open_qa import is_native_self_chart_interpretation_question

                if is_native_self_chart_interpretation_question(question):
                    for k in list(out.keys()):
                        out[k] = False
                    notes.append("open_chart_qa:native_self_interpretation")
                    return out, notes
            except Exception:
                pass
            out["mr"] = True
            notes.append("mr:love_life_area_interpretation")
    except Exception:
        pass

    if _NATIVE_SELF_FOCUS_RX.search(question or "") and not _PARTNER_SUBJECT_RX.search(question or ""):
        if out.get("mr") and not out.get("gap"):
            pass
        elif out.get("gap") or gap_key == "personality":
            out["gap"] = True
            out["mr"] = False
            notes.append("gap:native_self_focus")

  # Love/marriage domain from intent
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("love", "marriage") and _PARTNER_SUBJECT_RX.search(question or ""):
            out["mr"] = True
            out["gap"] = False
            notes.append(f"mr:llm_domain_{dom}")

    return out, notes


def verify_static_engine_selection(
    question: str,
    *,
    engine_key: str | None,
    archetype: str | None = None,
    gap_key: str | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> EngineVerificationResult:
    """Pre-run: is this engine key appropriate for the question?"""
    q = (question or "").strip()
    arch = str(archetype or "").strip().lower()
    failed: list[str] = []

    if not engine_key:
        return EngineVerificationResult(
            ok=False,
            action="d1_open_chart",
            reason="no_engine_selected",
            failed_checks=["no_engine"],
        )

    ek = str(engine_key or "").strip().lower()
    if ek in ("timing", "love_timing") or arch == "timing":
        try:
            from ask_mr.timing_registry import (
                mr_static_overrides_llm_timing,
                question_requests_timing,
                resolve_mr_static_archetype,
            )

            if not question_requests_timing(q, llm_intent) or mr_static_overrides_llm_timing(
                q, llm_intent
            ):
                return EngineVerificationResult(
                    ok=False,
                    action="reroute_mr",
                    reason="timing_without_kab_when",
                    mr_archetype=resolve_mr_static_archetype(q),
                    failed_checks=["timing_without_when_anchor"],
                )
        except Exception:
            pass

    if engine_key == "gap" and should_suppress_gap_for_question(q, gap_key=gap_key):
        failed.append("gap_on_partner_subject")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="partner_question_not_gap",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    if arch in _NATIVE_SELF_ARCHETYPES and _PARTNER_SUBJECT_RX.search(q):
        failed.append("native_archetype_on_partner_question")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="native_archetype_partner_mismatch",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    if arch == "chemistry" and is_dyadic_couple_question(q):
        failed.append("chemistry_on_dyad_couple_question")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="chemistry_native_on_dyad_question",
            mr_archetype=suggest_mr_archetype_for_question(q) or "general_mr",
            failed_checks=failed,
        )

    if engine_key in ("health", "career", "finance", "education", "children", "property", "vehicle", "travel", "litigation", "gap") and is_partner_relationship_question(q):
        failed.append(f"{engine_key}_on_partner_question")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="partner_question_wrong_domain_engine",
            mr_archetype=suggest_mr_archetype_for_question(q) or "partner_nature",
            failed_checks=failed,
        )

    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question

        if engine_key == "health" and is_domain_life_area_interpretation_question(q):
            return EngineVerificationResult(
                ok=False,
                action="d1_open_chart",
                reason="health_on_love_life_interpretation",
                failed_checks=["health_on_love_style_question"],
            )
    except Exception:
        pass

    if engine_key == "mr" and arch and not archetype_allowed_for_question(q, arch):
        try:
            from ask_chart_open_qa import should_use_open_chart_qa

            if should_use_open_chart_qa(q):
                failed.append("mr_archetype_not_allowed")
                return EngineVerificationResult(
                    ok=False,
                    action="d1_open_chart",
                    reason="mr_archetype_mismatch_open_chart",
                    failed_checks=failed,
                )
        except Exception:
            pass
        failed.append("mr_archetype_not_allowed")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="mr_archetype_mismatch",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    return EngineVerificationResult(
        ok=True,
        action="keep",
        reason="selection_ok",
        mr_archetype=arch or None,
        failed_checks=[],
    )


def verify_engine_output(
    question: str,
    *,
    engine_key: str | None,
    archetype: str | None,
    slice_meta: dict[str, Any] | None,
    gap_key: str | None = None,
) -> EngineVerificationResult:
    """Post-run: evidence + subject focus match question."""
    q = (question or "").strip()
    arch = str(archetype or "").strip().lower()
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    failed: list[str] = []

    pre = verify_static_engine_selection(
        q,
        engine_key=engine_key,
        archetype=arch,
        gap_key=gap_key,
    )
    if not pre.ok:
        return pre

    summary = " ".join(meta.get("summary") or [])
    if "native self only" in summary.lower() and _PARTNER_SUBJECT_RX.search(q):
        failed.append("native_focus_on_partner_q")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="output_focus_native_on_partner_q",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    evidence = list(meta.get("evidence") or [])
    pos = list(meta.get("evidence_positive") or [])
    neg = list(meta.get("evidence_negative") or [])
    neu = list(meta.get("evidence_neutral") or [])
    ev_count = len(evidence) or len(pos) + len(neg) + len(neu)

    if engine_key in ("gap", "mr", "health", "career", "finance") and ev_count == 0:
        if not meta.get("skip_llm") and not meta.get("template_text"):
            failed.append("empty_evidence")
            mr_arch = suggest_mr_archetype_for_question(q)
            if mr_arch and engine_key != "mr":
                return EngineVerificationResult(
                    ok=False,
                    action="reroute_mr",
                    reason="empty_evidence_reroute",
                    mr_archetype=mr_arch,
                    failed_checks=failed,
                )
            return EngineVerificationResult(
                ok=False,
                action="d1_open_chart",
                reason="empty_evidence_d1_fallback",
                failed_checks=failed,
            )

    return EngineVerificationResult(
        ok=True,
        action="keep",
        reason="output_ok",
        failed_checks=[],
    )


_SLICE_TO_ENGINE_KEY: dict[str, str] = {
    "mr_engine_v1": "mr",
    "personality_engine_v1": "gap",
    "siblings_engine_v1": "gap",
    "parents_engine_v1": "gap",
    "spiritual_engine_v1": "gap",
    "fame_engine_v1": "gap",
    "dreams_engine_v1": "gap",
    "anger_engine_v1": "gap",
    "remedy_engine_v1": "gap",
    "charity_engine_v1": "gap",
    "settlement_engine_v1": "gap",
    "vastu_engine_v1": "gap",
    "pets_engine_v1": "gap",
    "wellness_engine_v1": "gap",
    "health_engine_v1": "health",
    "career_engine_v1": "career",
    "finance_engine_v1": "finance",
    "education_engine_v1": "education",
    "children_engine_v1": "children",
    "property_engine_v1": "property",
    "vehicle_engine_v1": "vehicle",
    "travel_engine_v1": "travel",
    "litigation_engine_v1": "litigation",
    "network_engine_v1": "network",
    "luck_engine_v1": "luck",
}


def _engine_key_from_slice(slice_id: str | None) -> str | None:
    sl = (slice_id or "").strip()
    if not sl:
        return None
    return _SLICE_TO_ENGINE_KEY.get(sl, sl.replace("_engine_v1", ""))


def build_engine_verification_admin_summary(
    question: str,
    *,
    llm_intent: dict[str, Any] | None = None,
    slice_meta: dict[str, Any] | None = None,
    engine_route: dict[str, Any] | None = None,
    is_timing: bool = False,
) -> dict[str, Any]:
    """Admin one-liner: correct | wrong | doubt | unknown."""
    intent = llm_intent if isinstance(llm_intent, dict) else {}
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    route = engine_route if isinstance(engine_route, dict) else {}

    stored = intent.get("engine_verification")
    recovered = str(intent.get("engine_verification_recovered") or "").strip()
    ran_key = str(
        intent.get("engine_ran")
        or route.get("engine_key")
        or ""
    ).strip() or None
    ran_arch = str(meta.get("archetype") or "").strip() or None
    selected_arch = str(
        intent.get("routed_archetype")
        or route.get("archetype")
        or intent.get("mr_archetype")
        or ""
    ).strip() or None
    route_reason = str(
        intent.get("engine_route_reason") or route.get("reason") or ""
    ).strip()
    gap_key = str(intent.get("gap_static_key") or "").strip() or None

    def _with_engine_no(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            from ask_engine_catalog import resolve_engine_display

            disp = resolve_engine_display(
                slice_id=str(meta.get("slice") or intent.get("engine_ran_slice") or ""),
                engine_key=ran_key or payload.get("selected_engine"),
                archetype=ran_arch,
                is_timing=is_timing or bool(intent.get("routed_timing")),
                gap_static_key=gap_key,
            )
            payload["engine_no"] = disp.engine_no
            payload["engine_slice"] = disp.slice_id
            payload["engine_admin_line"] = disp.admin_line
        except Exception:
            pass
        return payload

    if recovered:
        return _with_engine_no({
            "status": "wrong",
            "label": "Wrong engine (corrected)",
            "reason": f"First pick was wrong — recovered via {recovered}",
            "selected_engine": ran_key,
            "ran_archetype": ran_arch,
            "recovered": True,
        })

    if isinstance(stored, dict):
        engine_key = ran_key or _engine_key_from_slice(str(meta.get("slice") or ""))
        live_crosscheck = None
        if engine_key and meta:
            live_crosscheck = verify_engine_output(
                question or "",
                engine_key=engine_key,
                archetype=ran_arch,
                slice_meta=meta,
                gap_key=gap_key,
            )
        if stored.get("ok") and stored.get("action") == "keep":
            if live_crosscheck and not live_crosscheck.ok:
                status = "wrong"
                label = "Wrong engine"
                if live_crosscheck.action == "d1_open_chart":
                    status = "doubt"
                    label = "Doubt"
                return _with_engine_no({
                    "status": status,
                    "label": label,
                    "reason": live_crosscheck.reason,
                    "selected_engine": ran_key,
                    "ran_archetype": ran_arch,
                    "recovered": False,
                })
            return _with_engine_no({
                "status": "correct",
                "label": "Correct engine",
                "reason": str(stored.get("reason") or "verification passed"),
                "selected_engine": ran_key,
                "ran_archetype": ran_arch,
                "recovered": False,
            })
        if not stored.get("ok"):
            return _with_engine_no({
                "status": "wrong",
                "label": "Wrong engine",
                "reason": str(stored.get("reason") or "verification failed"),
                "selected_engine": ran_key,
                "ran_archetype": ran_arch,
                "recovered": False,
            })

    # Live verify when snapshot missing (older rows or pre-save)
    engine_key = ran_key or _engine_key_from_slice(str(meta.get("slice") or ""))
    if engine_key and meta:
        live = verify_engine_output(
            question or "",
            engine_key=engine_key,
            archetype=ran_arch,
            slice_meta=meta,
            gap_key=gap_key,
        )
        if live.ok:
            status = "correct"
            label = "Correct engine"
        else:
            status = "wrong"
            label = "Wrong engine"
        if live.action == "d1_open_chart":
            status = "doubt"
            label = "Doubt"
        return _with_engine_no({
            "status": status,
            "label": label,
            "reason": live.reason,
            "selected_engine": engine_key,
            "ran_archetype": ran_arch,
            "recovered": False,
        })

    if selected_arch and ran_arch and selected_arch != ran_arch:
        return _with_engine_no({
            "status": "doubt",
            "label": "Doubt",
            "reason": f"Selected {selected_arch} but ran {ran_arch}",
            "selected_engine": ran_key,
            "ran_archetype": ran_arch,
            "recovered": False,
        })

    if route_reason in ("pipeline_order", "single_candidate") and route.get("suppressed"):
        return _with_engine_no({
            "status": "doubt",
            "label": "Doubt",
            "reason": f"Resolver picked via {route_reason} — multiple engines matched",
            "selected_engine": ran_key,
            "ran_archetype": ran_arch,
            "recovered": False,
        })

    if not meta.get("evidence") and not meta.get("archetype"):
        return _with_engine_no({
            "status": "doubt",
            "label": "Doubt",
            "reason": "No engine evidence in snapshot",
            "selected_engine": ran_key,
            "ran_archetype": ran_arch,
            "recovered": False,
        })

    return _with_engine_no({
        "status": "unknown",
        "label": "Unknown",
        "reason": "No verification snapshot (re-ask after deploy)",
        "selected_engine": ran_key,
        "ran_archetype": ran_arch,
        "recovered": False,
    })
