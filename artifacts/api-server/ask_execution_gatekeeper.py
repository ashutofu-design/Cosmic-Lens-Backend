"""Execution Gatekeeper — hard STOP when DNA, engine, narrator, or answer disagree.

Flow:
  DNA → Routing → [gate: routing] → Engine → [gate: engine output] →
  Narrator → [gate: final answer]

When any gate fails the user must NOT receive a hallucinated LLM answer.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from ask_intent_llm import CAREER_ARCHETYPES, HEALTH_ARCHETYPES
from engine_collision_registry import DOMAIN_PRIMARY_ENGINE

_SLICE_DOMAIN: dict[str, str] = {
    "health_engine_v1": "health",
    "career_engine_v1": "career",
    "finance_engine_v1": "finance",
    "education_engine_v1": "education",
    "children_engine_v1": "children",
    "property_engine_v1": "property",
    "vehicle_engine_v1": "vehicle",
    "travel_engine_v1": "travel",
    "litigation_engine_v1": "litigation",
    "mr_engine_v1": "love",
    "network_engine_v1": "network",
    "luck_engine_v1": "luck",
}

_DOMAIN_ARCHETYPE_SET: dict[str, frozenset[str]] = {
    "health": frozenset(HEALTH_ARCHETYPES),
    "career": frozenset(CAREER_ARCHETYPES),
}

_NARRATOR_ALLOWED_KEYS = frozenset({
    "reason",
    "warnings",
    "strongest",
    "weakest",
    "scorecard",
    "direct_answer",
    # Health narrator aliases (mapped internally)
    "reason_summary",
    "risk_indicators",
    "positive_indicators",
    "practical_guidance",
    "confidence_explanation",
    "final_verdict",
})

_HALLUCINATION_RX = re.compile(
    r"(?ix)\b("
    r"shayad|ho sakta hai|lagta hai|possibly|maybe|might|perhaps|"
    r"i think|mujhe lagta hai|according to me"
    r")\b"
)

_CAREER_LEAK_RX = re.compile(
    r"(?ix)\b("
    r"job|naukri|promotion|salary|boss|office|business|startup|"
    r"career|profession|government\s+job|private\s+job"
    r")\b"
)

_HEALTH_LEAK_RX = re.compile(
    r"(?ix)\b("
    r"blood pressure|\bbp\b|heart|dil ki sehat|cardio|immunity|"
    r"digestion|acidity|diabetes|cancer|surgery|hospital|doctor"
    r")\b"
)


@dataclass
class DnaExpectation:
    trusted: bool
    domain: str
    archetype: str
    bucket: str
    source: str = ""

    @property
    def engine_key(self) -> str | None:
        dom = (self.domain or "").strip().lower()
        return DOMAIN_PRIMARY_ENGINE.get(dom)


@dataclass
class GatekeeperResult:
    ok: bool
    stage: str  # routing | engine | narrator | final
    reason: str
    rule: str
    failed_checks: list[str] = field(default_factory=list)
    retry_engine_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def gatekeeper_enabled() -> bool:
    return (os.environ.get("ASK_EXECUTION_GATEKEEPER") or "1").strip() != "0"


def _primary_item(admin: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(admin, dict):
        return {}
    dna = admin.get("question_dna")
    if not isinstance(dna, dict):
        return {}
    items = dna.get("questions")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return items[0]
    return {}


def _legacy_engine_facts_block(chart_text: str) -> bool:
    ct = chart_text or ""
    return "VERDICT:" in ct and "ARCHETYPE:" in ct


def _question_health_archetype(question: str) -> str | None:
    try:
        from ask_health.health_registry import (
            classify_health_archetype,
            is_health_static_question,
        )

        q = (question or "").strip()
        if not q or not is_health_static_question(q):
            return None
        return classify_health_archetype(q)
    except Exception:
        return None


def _question_health_expectation(question: str) -> DnaExpectation | None:
    arch = _question_health_archetype(question)
    if not arch:
        return None
    return DnaExpectation(
        trusted=True,
        domain="health",
        archetype=arch,
        bucket=arch,
        source="question_regex",
    )


def dna_expectation(admin: dict[str, Any] | None, *, question: str = "") -> DnaExpectation:
    if not isinstance(admin, dict):
        return DnaExpectation(False, "", "", "")
    item = _primary_item(admin)
    try:
        from ask_question_dna import (
            dna_item_trusted_for_routing,
            resolve_engine_archetype_from_dna_item,
        )

        trusted = dna_item_trusted_for_routing(
            item,
            dna_source=str((admin.get("question_dna") or {}).get("source") or ""),
        )
    except Exception:
        trusted = bool(admin.get("dna_routing_applied"))
    domain = str(
        item.get("domain")
        or admin.get("routed_domain")
        or admin.get("domain")
        or ""
    ).strip().lower()
    bucket = str(item.get("bucket") or admin.get("bucket") or "").strip().lower()
    archetype = str(
        admin.get("dna_engine_archetype")
        or admin.get("routed_archetype")
        or admin.get("health_archetype")
        or admin.get("career_archetype")
        or ""
    ).strip().lower()
    if not archetype and item:
        try:
            from ask_question_dna import resolve_engine_archetype_from_dna_item

            archetype = str(resolve_engine_archetype_from_dna_item(item) or "").strip().lower()
        except Exception:
            archetype = bucket
    if not archetype:
        archetype = bucket
    if not trusted and admin.get("dna_routing_applied") and (archetype or bucket):
        trusted = True
    exp = DnaExpectation(
        trusted=trusted,
        domain=domain,
        archetype=archetype,
        bucket=bucket,
        source=str((admin.get("question_dna") or {}).get("source") or ""),
    )
    if exp.trusted and exp.engine_key:
        return exp
    qexp = _question_health_expectation(question)
    if qexp:
        return qexp
    return exp


def enforce_dna_routing_flags(
    flags: dict[str, bool],
    admin: dict[str, Any] | None,
    route: Any | None = None,
    *,
    question: str = "",
) -> tuple[dict[str, bool], str | None]:
    """When trusted DNA domain disagrees with resolver winner, force primary engine."""
    if not gatekeeper_enabled():
        return flags, None
    exp = dna_expectation(admin, question=question)
    if not exp.trusted or not exp.engine_key:
        return flags, None
    primary = exp.engine_key
    out = {k: bool(v) for k, v in (flags or {}).items()}
    active = [k for k, v in out.items() if v]
    if len(active) == 1 and active[0] == primary:
        return out, None
    if out.get(primary):
        return out, None
    # Force DNA domain engine — e.g. health over career
    for k in list(out.keys()):
        out[k] = k == primary
    note = f"dna_force_engine:{primary}"
    if route is not None and hasattr(route, "engine_key"):
        try:
            route.engine_key = primary
            route.domain = exp.domain or route.domain
            route.archetype = exp.archetype or route.archetype
            route.reason = note
        except Exception:
            pass
    return out, note


def _rules_fired_count(meta: dict[str, Any]) -> int:
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    fired = checks.get("rules_fired")
    if isinstance(fired, list):
        return len(fired)
    sm = meta if isinstance(meta, dict) else {}
    if isinstance(sm.get("rules_fired"), list):
        return len(sm["rules_fired"])
    return 0


def _evidence_count(meta: dict[str, Any]) -> int:
    ev = list(meta.get("evidence") or [])
    pos = list(meta.get("evidence_positive") or [])
    neg = list(meta.get("evidence_negative") or [])
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    if checks.get("positive_count") or checks.get("negative_count"):
        return int(checks.get("positive_count") or 0) + int(checks.get("negative_count") or 0) + len(ev)
    return len(ev) or len(pos) + len(neg)


def _narrator_json(meta: dict[str, Any]) -> dict[str, Any] | None:
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    raw = checks.get("narrator_input")
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            return json.loads(raw)
        except Exception:
            return None
    return None


def _slice_domain(meta: dict[str, Any]) -> str:
    sl = str(meta.get("slice") or "").strip()
    return _SLICE_DOMAIN.get(sl, "")


def _archetype_domain(archetype: str) -> str:
    arch = (archetype or "").strip().lower()
    if arch in HEALTH_ARCHETYPES:
        return "health"
    if arch in CAREER_ARCHETYPES:
        return "career"
    return ""


def check_routing_gate(
    admin: dict[str, Any] | None,
    *,
    engine_route: Any | None = None,
    flags: dict[str, bool] | None = None,
    question: str = "",
) -> GatekeeperResult:
    if not gatekeeper_enabled():
        return GatekeeperResult(True, "routing", "disabled", "gate_off")
    exp = dna_expectation(admin, question=question)
    if not exp.trusted or not exp.engine_key:
        return GatekeeperResult(True, "routing", "dna_not_trusted", "skip")
    winner = None
    if engine_route is not None and getattr(engine_route, "engine_key", None):
        winner = str(engine_route.engine_key).strip().lower()
    elif flags:
        winner = next((k for k, v in flags.items() if v), None)
    if winner and winner != exp.engine_key:
        return GatekeeperResult(
            ok=False,
            stage="routing",
            reason="routing_error",
            rule="rule_1_routing_mismatch",
            failed_checks=[f"dna_engine={exp.engine_key}", f"winner={winner}"],
            retry_engine_key=exp.engine_key,
        )
    if exp.archetype and engine_route is not None:
        routed_arch = str(getattr(engine_route, "archetype", "") or "").strip().lower()
        if routed_arch and routed_arch not in (exp.archetype, exp.bucket, "general", ""):
            if _archetype_domain(routed_arch) == _archetype_domain(exp.archetype):
                pass  # same domain, different sub-archetype OK at routing stage
            elif routed_arch != exp.archetype:
                return GatekeeperResult(
                    ok=False,
                    stage="routing",
                    reason="routing_archetype_mismatch",
                    rule="rule_1_dna_archetype",
                    failed_checks=[f"dna={exp.archetype}", f"route={routed_arch}"],
                    retry_engine_key=exp.engine_key,
                )
    return GatekeeperResult(True, "routing", "ok", "routing_ok")


def check_engine_output_gate(
    admin: dict[str, Any] | None,
    *,
    slice_meta: dict[str, Any] | None,
    question: str = "",
) -> GatekeeperResult:
    if not gatekeeper_enabled():
        return GatekeeperResult(True, "engine", "disabled", "gate_off")
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    exp = dna_expectation(admin, question=question)
    executed = str(meta.get("archetype") or "").strip().lower()
    slice_id = str(meta.get("slice") or "").strip()
    failed: list[str] = []

    # Rule 1 — DNA archetype vs executed archetype
    if exp.trusted and exp.archetype and executed and exp.archetype != executed:
        dom_dna = _archetype_domain(exp.archetype) or exp.domain
        dom_exec = _archetype_domain(executed) or _slice_domain(meta)
        if dom_dna and dom_exec and dom_dna != dom_exec:
            return GatekeeperResult(
                ok=False,
                stage="engine",
                reason="routing_error",
                rule="rule_1_dna_executed_mismatch",
                failed_checks=[f"dna={exp.archetype}", f"executed={executed}"],
                retry_engine_key=exp.engine_key,
            )
        if dom_dna == dom_exec == "health" and exp.archetype != executed:
            return GatekeeperResult(
                ok=False,
                stage="engine",
                reason="routing_error",
                rule="rule_1_health_archetype_mismatch",
                failed_checks=[f"dna={exp.archetype}", f"executed={executed}"],
                retry_engine_key=exp.engine_key,
            )

    # Rule 6 — health DNA + career engine
    if exp.trusted and (exp.domain == "health" or exp.archetype in HEALTH_ARCHETYPES):
        if slice_id == "career_engine_v1" or executed in CAREER_ARCHETYPES:
            return GatekeeperResult(
                ok=False,
                stage="engine",
                reason="routing_error",
                rule="rule_6_health_question_career_engine",
                failed_checks=[f"dna={exp.archetype}", f"executed={executed}", f"slice={slice_id}"],
                retry_engine_key="health",
            )

    # Rule 7 — career DNA + health engine (symmetric)
    if exp.trusted and (exp.domain == "career" or exp.archetype in CAREER_ARCHETYPES):
        if slice_id == "health_engine_v1" or executed in HEALTH_ARCHETYPES:
            return GatekeeperResult(
                ok=False,
                stage="engine",
                reason="routing_error",
                rule="rule_7_career_question_health_engine",
                failed_checks=[f"dna={exp.archetype}", f"executed={executed}"],
                retry_engine_key="career",
            )

    skip_llm = bool(meta.get("skip_llm"))
    template = str(meta.get("template_text") or "").strip()
    fired = _rules_fired_count(meta)
    evidence = _evidence_count(meta)

    # Rule 2 — insufficient evidence
    if not skip_llm and not template:
        if fired == 0 and evidence == 0:
            return GatekeeperResult(
                ok=False,
                stage="engine",
                reason="insufficient_evidence",
                rule="rule_2_zero_rules_fired",
                failed_checks=["rules_fired=0", "evidence=0"],
                retry_engine_key=exp.engine_key if exp.trusted else None,
            )

    # Rule 3 — narrator JSON checked in run_post_engine_gate (may live in chart_text)

    return GatekeeperResult(True, "engine", "ok", "engine_ok", failed_checks=failed)


def check_narrator_json_gate(narrator_json: dict[str, Any] | None) -> GatekeeperResult:
    if not gatekeeper_enabled():
        return GatekeeperResult(True, "narrator", "disabled", "gate_off")
    if not narrator_json:
        return GatekeeperResult(
            ok=False,
            stage="narrator",
            reason="missing_narrator_json",
            rule="rule_3_narrator_json_missing",
        )
    # Rule 4 — content fields must include direct_answer + at least one evidence list
    if not str(
        narrator_json.get("direct_answer")
        or narrator_json.get("final_verdict")
        or narrator_json.get("verdict")
        or ""
    ).strip():
        return GatekeeperResult(
            ok=False,
            stage="narrator",
            reason="invalid_narrator_json",
            rule="rule_4_missing_direct_answer",
        )
    has_support = any(
        narrator_json.get(k)
        for k in (
            "strongest",
            "weakest",
            "positive_indicators",
            "risk_indicators",
            "evidence",
            "evidence_positive",
            "evidence_negative",
            "answer_plan",
            "reason",
            "reason_summary",
            "warnings",
        )
    )
    if not has_support:
        return GatekeeperResult(
            ok=False,
            stage="narrator",
            reason="invalid_narrator_json",
            rule="rule_4_missing_evidence_fields",
        )
    return GatekeeperResult(True, "narrator", "ok", "narrator_json_ok")


def check_final_answer_gate(
    answer: str,
    *,
    slice_meta: dict[str, Any] | None,
    narrator_json: dict[str, Any] | None = None,
    admin: dict[str, Any] | None = None,
    question: str = "",
) -> GatekeeperResult:
    if not gatekeeper_enabled():
        return GatekeeperResult(True, "final", "disabled", "gate_off")
    text = (answer or "").strip()
    if not text:
        return GatekeeperResult(
            ok=False,
            stage="final",
            reason="empty_answer",
            rule="rule_8_empty",
        )
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    nj = narrator_json or _narrator_json(meta)
    engine_verdict = str(meta.get("verdict") or "").strip()
    exp = dna_expectation(admin, question=question)

    # Rule 5 — banned hedging / obvious hallucination tone
    if _HALLUCINATION_RX.search(text):
        return GatekeeperResult(
            ok=False,
            stage="final",
            reason="hallucination_detected",
            rule="rule_5_hedging_language",
        )

    # Rule 7 — domain leak in final text
    sl_dom = _slice_domain(meta)
    if sl_dom == "health" and _CAREER_LEAK_RX.search(text) and not _HEALTH_LEAK_RX.search(text):
        return GatekeeperResult(
            ok=False,
            stage="final",
            reason="hallucination_detected",
            rule="rule_7_career_leak_in_health_answer",
        )
    if sl_dom == "career" and _HEALTH_LEAK_RX.search(text) and not _CAREER_LEAK_RX.search(text):
        return GatekeeperResult(
            ok=False,
            stage="final",
            reason="hallucination_detected",
            rule="rule_7_health_leak_in_career_answer",
        )

    # Rule 8 — verdict alignment (soft: skip when answer is gatekeeper block text)
    if "execution_gatekeeper" in str(meta.get("source") or ""):
        return GatekeeperResult(True, "final", "ok", "blocked_message_ok")
    ref_verdict = str(
        (nj or {}).get("final_verdict")
        or (nj or {}).get("direct_answer")
        or engine_verdict
        or ""
    ).strip()
    if ref_verdict and len(ref_verdict) > 12 and sl_dom == "health":
        chunk = ref_verdict[:32].lower()
        if chunk and chunk not in text.lower():
            words = [w for w in re.split(r"\s+", chunk) if len(w) > 3][:2]
            if words and not any(w in text.lower() for w in words):
                return GatekeeperResult(
                    ok=False,
                    stage="final",
                    reason="verdict_mismatch",
                    rule="rule_8_verdict_not_in_answer",
                    failed_checks=[f"engine={ref_verdict[:60]}"],
                )

    return GatekeeperResult(True, "final", "ok", "final_ok")


def build_blocked_user_message(result: GatekeeperResult, *, lang: str = "hn") -> str:
    reason = (result.reason or "").strip().lower()
    if reason == "insufficient_evidence":
        return (
            "Is sawal ke liye chart se kaafi strong signals nahi mile. "
            "Thodi der baad dobara puchhein ya sawal thoda specific likhein."
        )
    if reason in ("routing_error", "routing_archetype_mismatch"):
        return (
            "Internal routing error — sahi health/career engine load nahi ho paaya. "
            "Kripya 1 minute baad wahi sawal dobara puchhein."
        )
    if reason == "hallucination_detected":
        return (
            "Answer quality check fail ho gaya — dubara try karein. "
            "Agar issue repeat ho to hume batayein."
        )
    if reason == "verdict_mismatch":
        return (
            "Engine aur final answer match nahi kiye — answer block kiya gaya. "
            "Kripya sawal dobara puchhein."
        )
    return (
        "Abhi is sawal ka verified jawab generate nahi ho paaya. "
        "Thodi der baad dobara try karein."
    )


def build_blocked_response(
    result: GatekeeperResult,
    *,
    question: str = "",
    qtype: str = "STATIC",
    lang: str = "hn",
    slice_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    topic = str(meta.get("topic") or "general").lower()
    return {
        "text": build_blocked_user_message(result, lang=lang),
        "topic": topic,
        "question_type": qtype,
        "confidence": 0.0,
        "source": "execution_gatekeeper_blocked",
        "engine_tag": "ans-gate",
        "follow_ups": [],
        "gatekeeper": result.to_dict(),
    }


def extract_narrator_json_from_chart_text(chart_text: str) -> dict[str, Any] | None:
    raw = chart_text or ""
    if "VERIFIED_HEALTH_CONTEXT_JSON:" in raw:
        try:
            payload = json.loads(raw.split("VERIFIED_HEALTH_CONTEXT_JSON:", 1)[1].strip())
            engine = payload.get("engine") if isinstance(payload, dict) else None
            if isinstance(engine, dict):
                return {
                    "direct_answer": engine.get("verdict"),
                    "final_verdict": engine.get("verdict"),
                    "positive_indicators": (
                        engine.get("evidence_positive") or engine.get("evidence") or []
                    ),
                    "risk_indicators": engine.get("evidence_negative") or [],
                    "reason": engine.get("answer_plan") or "",
                    **engine,
                }
        except Exception:
            return None
    if "ENGINE_JSON:" not in raw:
        return None
    try:
        blob = raw.split("ENGINE_JSON:", 1)[1].strip()
        return json.loads(blob)
    except Exception:
        return None


def run_post_engine_gate(
    admin: dict[str, Any] | None,
    *,
    slice_meta: dict[str, Any] | None,
    chart_text: str = "",
    question: str = "",
) -> GatekeeperResult:
    eng = check_engine_output_gate(admin, slice_meta=slice_meta, question=question)
    if not eng.ok:
        return eng
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    skip_llm = bool(meta.get("skip_llm"))
    template = str(meta.get("template_text") or "").strip()
    if skip_llm or template:
        return GatekeeperResult(True, "engine", "ok", "post_engine_template_ok")
    nj = _narrator_json(meta) or extract_narrator_json_from_chart_text(chart_text)
    if nj:
        nar = check_narrator_json_gate(nj)
        if not nar.ok:
            return nar
    elif _legacy_engine_facts_block(chart_text) and _evidence_count(meta) > 0:
        return GatekeeperResult(True, "engine", "ok", "legacy_engine_facts_ok")
    else:
        return GatekeeperResult(
            ok=False,
            stage="engine",
            reason="missing_narrator_json",
            rule="rule_3_narrator_json_missing",
        )
    return GatekeeperResult(True, "engine", "ok", "post_engine_ok")


def try_recover_engine_from_dna(
    question: str,
    kundli: dict[str, Any],
    admin: dict[str, Any] | None,
    *,
    wants_explain: bool = False,
) -> tuple[dict[str, Any], str] | None:
    """One-shot recovery: re-run the DNA-locked engine when wrong engine executed."""
    q = (question or "").strip()
    exp = dna_expectation(admin, question=q)
    if not exp.engine_key:
        qexp = _question_health_expectation(q)
        if qexp:
            exp = qexp
    if not exp.archetype and exp.engine_key == "health":
        exp = DnaExpectation(
            trusted=True,
            domain="health",
            archetype=_question_health_archetype(q) or "general_health",
            bucket=_question_health_archetype(q) or "general_health",
            source="question_regex",
        )
    if not exp.engine_key:
        return None
    if exp.engine_key == "health" and exp.archetype:
        try:
            from ask_health import run_health_static_engine
            from ask_health.presenter import to_health_llm_payload

            res = run_health_static_engine(
                kundli,
                q,
                wants_explain=wants_explain,
                archetype=exp.archetype,
            )
            chart_text = to_health_llm_payload(res, question=q)
            checks = dict(res.checks or {})
            checks["narrator_input"] = {
                "archetype": res.archetype,
                "verdict": res.verdict,
                "confidence": res.confidence,
                "evidence": list(res.evidence or []),
                "evidence_positive": list(res.evidence_positive or []),
                "evidence_negative": list(res.evidence_negative or []),
                "answer_plan": res.answer_plan,
                "ignore": list(res.ignore or []),
                "d1_health_facts": checks.get("d1_health_facts") or {},
                "d9_health_facts": checks.get("d9_health_facts") or {},
                "health_engine_execution": checks.get("health_engine_execution") or {},
            }
            checks["gatekeeper_recovered"] = True
            meta = {
                "slice": "health_engine_v1",
                "topic": "health",
                "archetype": res.archetype,
                "verdict": res.verdict,
                "summary": list(res.summary or []),
                "evidence": list(res.evidence or []),
                "evidence_positive": list(res.evidence_positive or []),
                "evidence_negative": list(res.evidence_negative or []),
                "ignore": list(res.ignore or []),
                "checks": checks,
                "skip_llm": bool(res.skip_llm),
                "word_budget": int(res.word_budget or 95),
                "narrator_mode": "adaptive_d1_health_context",
            }
            return meta, chart_text
        except Exception:
            return None
    return None
