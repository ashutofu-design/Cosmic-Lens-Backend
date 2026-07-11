"""Admin observability — developer debugger bundle from llm_context + answer."""
from __future__ import annotations

import re
from typing import Any


_COMMITMENT_Q_RX = re.compile(
    r"(?i)(commitment|timepass|time\s*pass|genuine|serious|long[\s-]?term|pakka|dhokha)"
)
_LOYALTY_ARCH = frozenset({"loyalty_trust", "loyalty", "trust"})


def _dig(*sources: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    for src in sources:
        if not isinstance(src, dict):
            continue
        if key in src and src[key] not in (None, ""):
            return src[key]
        checks = src.get("checks")
        if isinstance(checks, dict) and key in checks and checks[key] not in (None, ""):
            return checks[key]
    return default


def _pipeline_step(label: str, value: Any) -> dict[str, str]:
    if value is None or value == "":
        return {"label": label, "value": "—"}
    if isinstance(value, bool):
        return {"label": label, "value": "yes" if value else "no"}
    if isinstance(value, (list, dict)):
        import json

        try:
            text = json.dumps(value, ensure_ascii=False)
        except Exception:
            text = str(value)
        return {"label": label, "value": text[:500]}
    return {"label": label, "value": str(value)}


def _question_dna_pipeline(
    ctx: dict[str, Any],
    question_text: str,
) -> list[dict[str, str]]:
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    dna = ctx.get("question_dna") if isinstance(ctx.get("question_dna"), dict) else {}
    dna_item = {}
    if isinstance(dna.get("questions"), list) and dna["questions"]:
        dna_item = dna["questions"][0] if isinstance(dna["questions"][0], dict) else {}

    domain = dna_item.get("domain") or li.get("domain") or li.get("routed_domain") or "—"
    bucket = dna_item.get("bucket") or li.get("bucket") or li.get("mr_bucket") or "—"
    archetype = (
        sm.get("archetype")
        or ctx.get("routed_archetype")
        or li.get("mr_archetype")
        or li.get("routed_archetype")
        or "—"
    )
    secondary = (
        _dig(checks, sm, key="secondary_engine")
        or (li.get("orchestrator") or {}).get("secondary_engine")
        if isinstance(li.get("orchestrator"), dict)
        else None
    ) or _dig(checks, sm, key="orchestrator_secondary") or "—"

    is_timing = dna_item.get("timing") if "timing" in dna_item else ctx.get("is_timing")
    timing_label = "Timing" if is_timing else "Non-Timing"

    steps = [
        _pipeline_step("Domain", domain),
        _pipeline_step("Bucket", bucket),
        _pipeline_step("Intent", dna_item.get("intent") or li.get("intent") or li.get("question_intent") or "—"),
        _pipeline_step("Subject", dna_item.get("subject") or li.get("subject") or "—"),
        _pipeline_step("Target", dna_item.get("target") or li.get("target") or "—"),
        _pipeline_step("Question Type", dna_item.get("question_type") or ctx.get("question_type") or "—"),
        _pipeline_step("Timing / Non-Timing", timing_label),
        _pipeline_step("Emotion", dna_item.get("emotion") or li.get("emotion") or "—"),
        _pipeline_step("Risk", dna_item.get("risk") or li.get("risk") or "—"),
        _pipeline_step("Primary Engine", archetype),
        _pipeline_step("Secondary Engine", secondary),
        _pipeline_step("DNA Confidence", dna_item.get("confidence") or li.get("confidence") or "—"),
    ]
    return steps


def _routing_warning(question_text: str, archetype: str) -> str | None:
    q = (question_text or "").strip()
    arch = (archetype or "").strip().lower()
    if not q or not arch:
        return None
    if _COMMITMENT_Q_RX.search(q) and arch in _LOYALTY_ARCH:
        return (
            "Question looks commitment/timepass-focused but primary engine is "
            f"{arch}. Expected primary: commitment (loyalty may be secondary)."
        )
    return None


def _modules_loaded(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("checks") if isinstance(ctx.get("slice_meta"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else sm
    used = _dig(checks, sm, key="modules_used") or []
    required = _dig(ctx.get("question_dna") or {}, key="required_modules") or []
    if not isinstance(used, list):
        used = []
    if not isinstance(required, list):
        required = []
    catalog = ["D1", "D9", "DASHA", "TRANSIT", "KP", "JAIMINI", "BCP"]
    names = {str(x).upper().replace("DASHA", "DASHA") for x in (used or required)}
    out: list[dict[str, Any]] = []
    for mod in catalog:
        key = mod
        ok = any(key in str(u).upper() for u in names) or mod in names
        out.append({"module": mod, "loaded": ok})
    if used:
        for u in used:
            label = str(u).upper()
            if not any(m["module"] == label for m in out):
                out.append({"module": label, "loaded": True})
    return out


def _modules_skipped(modules: list[dict[str, Any]]) -> list[str]:
    return [str(m.get("module") or "") for m in modules if not m.get("loaded")]


def _execution_time_ms(ctx: dict[str, Any]) -> int | None:
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    for key in ("execution_time_ms", "latency_ms", "understand_latency_ms", "total_latency_ms"):
        val = ctx.get(key) if key in ctx else li.get(key)
        if val is not None:
            try:
                return int(val)
            except (TypeError, ValueError):
                continue
    return None


def _rules_sections(ctx: dict[str, Any]) -> dict[str, Any]:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm_checks = {}
    sm = ctx.get("slice_meta")
    if isinstance(sm, dict) and isinstance(sm.get("checks"), dict):
        sm_checks = sm["checks"]
    fired = _dig(checks, sm_checks, key="rules_fired") or []
    if not isinstance(fired, list):
        fired = []
    ignore = list(_dig(checks, sm, key="ignore") or [])
    if isinstance(sm, dict):
        ignore = ignore or list(sm.get("ignore") or [])
    ignored_rules = []
    for item in ignore:
        ignored_rules.append({"rule_id": str(item)[:40], "reason": "Engine ignore list / not applicable"})
    score = _dig(checks, sm_checks, key="primary_score") or _dig(checks, sm_checks, key="love_score")
    level = _dig(checks, sm_checks, key="level") or _dig(checks, sm_checks, key="commitment_level")
    verdict = (
        _dig(ctx.get("engine_facts") or {}, sm or {}, key="verdict")
        or _dig(sm or {}, key="verdict")
        or "—"
    )
    return {
        "fired": fired,
        "ignored": ignored_rules,
        "final_score": score,
        "verdict_level": level,
        "verdict": verdict,
    }


def _planet_evidence(ctx: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    ef = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    pos = list(ef.get("evidence_positive") or sm.get("evidence_positive") or [])
    neg = list(ef.get("evidence_negative") or sm.get("evidence_negative") or [])
    neu = list(ef.get("evidence_neutral") or sm.get("evidence_neutral") or [])
    if not pos and not neg and not neu:
        pool = list(ef.get("evidence") or sm.get("evidence") or [])
        for line in pool:
            s = str(line)
            low = s.lower()
            if any(w in low for w in ("neutral", "mixed", "average", "moderate")):
                neu.append(s)
            elif any(w in low for w in ("weak", "delay", "afflict", "risk", "negative", "❌")):
                neg.append(s)
            else:
                pos.append(s)

    def _parse(lines: list[Any], polarity: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for raw in lines[:20]:
            s = str(raw).strip()
            if not s:
                continue
            weight = 0
            m = re.search(r"([+-]?\d+)\s*$", s)
            if m:
                weight = int(m.group(1))
            elif polarity == "positive":
                weight = 10
            elif polarity == "negative":
                weight = -5
            label = re.sub(r"\s*[+-]?\d+\s*$", "", s).strip()
            out.append({"label": label[:120], "weight": weight, "polarity": polarity})
        return out

    return {
        "positive": _parse(pos, "positive"),
        "negative": _parse(neg, "negative"),
        "neutral": _parse(neu, "neutral"),
    }


def _polarity_pair(module_pol: dict[str, Any], left: str, right: str) -> str:
    lp = str(module_pol.get(left) or module_pol.get(left.lower()) or "—")
    rp = str(module_pol.get(right) or module_pol.get(right.lower()) or "—")
    if lp == "—" and rp == "—":
        return "—"
    if lp == rp:
        return f"{left} {lp} · {right} {rp} — aligned"
    return f"{left} {lp} vs {right} {rp}"


def _conflict_resolution(ctx: dict[str, Any]) -> dict[str, Any]:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm_checks = {}
    sm = ctx.get("slice_meta")
    if isinstance(sm, dict) and isinstance(sm.get("checks"), dict):
        sm_checks = sm["checks"]
    detail = _dig(checks, sm_checks, key="contradiction_detail") or {}
    if not isinstance(detail, dict):
        detail = {}
    detected = bool(
        detail.get("detected")
        or _dig(checks, sm_checks, key="contradiction")
    )
    module_pol = detail.get("module_polarity") if isinstance(detail.get("module_polarity"), dict) else {}
    modules = []
    for mod, pol in module_pol.items():
        modules.append({"module": mod, "polarity": pol})
    if not modules:
        for mod in ("D1", "D9", "Dasha", "Transit"):
            modules.append({"module": mod, "polarity": "—"})
    final_result = detail.get("summary") or detail.get("pattern") or ("Conflict resolved — minor stress" if detected else "No conflict — modules aligned")
    return {
        "modules": modules,
        "d1_vs_d9": _polarity_pair(module_pol, "D1", "D9"),
        "dasha_vs_transit": _polarity_pair(module_pol, "Dasha", "Transit"),
        "conflict": "Minor" if detected else "None",
        "final_result": str(final_result)[:300],
        "reason": detail.get("summary") or detail.get("pattern") or ("Temporary stress in dasha" if detected else "—"),
        "detected": detected,
    }


def _scorecard(ctx: dict[str, Any]) -> dict[str, int]:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta")
    sm_checks = sm.get("checks") if isinstance(sm, dict) and isinstance(sm.get("checks"), dict) else {}
    sc = _dig(checks, sm_checks, key="scorecard") or {}
    if not isinstance(sc, dict):
        return {}
    out: dict[str, int] = {}
    for k, v in sc.items():
        if k == "primary":
            continue
        try:
            out[str(k).title()] = int(v)
        except (TypeError, ValueError):
            continue
    return out


def _user_question_section(ctx: dict[str, Any], question_text: str) -> list[dict[str, str]]:
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    return [
        _pipeline_step("Original Question", ctx.get("question_raw") or question_text),
        _pipeline_step("Normalized Question", ctx.get("question_normalized") or ctx.get("question")),
        _pipeline_step("Language", li.get("language") or li.get("reply_lang") or "—"),
        _pipeline_step("Answer Language", li.get("reply_lang") or li.get("language") or "—"),
    ]


def _routing_decision(ctx: dict[str, Any], question_text: str) -> dict[str, Any]:
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    archetype = str(
        sm.get("archetype") or ctx.get("routed_archetype") or li.get("mr_archetype") or ""
    ).strip()
    selected = archetype or "—"
    reason_parts: list[str] = []
    if ctx.get("engine_route_reason"):
        reason_parts.append(str(ctx.get("engine_route_reason")))
    if li.get("routing_override"):
        reason_parts.append(f"Override: {li.get('routing_override')}")
    if li.get("repair_note"):
        reason_parts.append(str(li.get("repair_note")))
    if not reason_parts:
        reason_parts.append(f"Primary engine {selected} from intent routing.")

    rejected: list[str] = []
    warning = _routing_warning(question_text, archetype)
    if warning:
        rejected.append("loyalty_trust — commitment/timepass signals in raw question")
    try:
        from ask_mr.classifier import classify_mr_archetype

        classified = classify_mr_archetype(question_text or "")
        if classified and classified != archetype:
            rejected.append(f"{classified} — regex classifier on raw question")
    except Exception:
        pass

    return {
        "selected_engine": selected,
        "why_selected": " ".join(reason_parts)[:500],
        "rejected_engines": rejected,
        "routing_warning": warning,
    }


def _astrology_checks(ctx: dict[str, Any]) -> dict[str, list[str]]:
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    ef = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    step_audit = (
        sm.get("step_audit")
        or ef.get("step_audit")
        or (ctx.get("blocks") or {}).get("engine_trace", {}).get("step_audit")
        or {}
    )
    step3 = step_audit.get("step3") if isinstance(step_audit, dict) else {}
    if not isinstance(step3, dict):
        step3 = {}
    return {
        "d1": list(step3.get("d1") or [])[:10],
        "d9": list(step3.get("d9") or [])[:10],
        "dasha": list(step3.get("dasha") or [])[:8],
        "transit": list(step3.get("transit") or [])[:8],
        "kp": list(step3.get("kp") or [])[:8],
        "jaimini": list(step3.get("jaimini") or [])[:6],
        "ashtakavarga": list(step3.get("bcp") or step3.get("ashtakavarga") or [])[:6],
    }


def _performance_section(ctx: dict[str, Any], row_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    sizes = ctx.get("sizes") if isinstance(ctx.get("sizes"), dict) else {}
    row_meta = row_meta if isinstance(row_meta, dict) else {}
    cached = row_meta.get("cached_tokens")
    cache_hit = bool(cached) if cached is not None else None
    return {
        "model": row_meta.get("llm_model") or ctx.get("model"),
        "max_tokens": ctx.get("max_tokens"),
        "chart_chars": sizes.get("chart_chars"),
        "system_prompt_chars": sizes.get("system_prompt_chars"),
        "llm_called": ctx.get("llm_called"),
        "cache_hit": cache_hit,
        "total_tokens": row_meta.get("total_tokens"),
        "prompt_tokens": row_meta.get("prompt_tokens"),
        "completion_tokens": row_meta.get("completion_tokens"),
        "cached_tokens": cached,
        "cost_inr": row_meta.get("cost_inr"),
        "cost_usd": row_meta.get("cost_usd"),
        "response_time_ms": _execution_time_ms(ctx),
    }


def _engine_verdict_extras(ctx: dict[str, Any], evidence: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    sm_checks = sm.get("checks") if isinstance(sm.get("checks"), dict) else {}
    explanation = _dig(checks, sm_checks, key="explanation") or {}
    if not isinstance(explanation, dict):
        explanation = {}
    ni = _narrator_input(ctx) or {}
    timing = _dig(checks, sm_checks, key="timing") or ni.get("timing") or {}
    timing_text = "—"
    if isinstance(timing, dict):
        windows = timing.get("windows") or []
        if windows:
            timing_text = ", ".join(str(w) for w in windows[:3])
        elif timing.get("window"):
            timing_text = str(timing.get("window"))
        elif timing.get("applicable") is False:
            timing_text = "Not applicable (static question)"
    elif isinstance(timing, str) and timing.strip():
        timing_text = timing.strip()
    warnings: list[str] = []
    for pool in (ni.get("warnings"), checks.get("warnings"), sm_checks.get("warnings")):
        if isinstance(pool, list):
            for item in pool:
                s = str(item).strip()
                if s and s not in warnings:
                    warnings.append(s[:160])
    strongest = explanation.get("strongest_factor") or ni.get("strongest") or ni.get("strongest_factor")
    weakest = explanation.get("weakest_factor") or ni.get("weakest") or ni.get("weakest_factor")
    if isinstance(strongest, list):
        strongest_items = [str(x) for x in strongest[:5]]
    elif strongest:
        strongest_items = [str(strongest)]
    else:
        strongest_items = [e.get("label", "") for e in evidence.get("positive", [])[:3] if e.get("label")]
    if isinstance(weakest, list):
        weakest_items = [str(x) for x in weakest[:5]]
    elif weakest:
        weakest_items = [str(weakest)]
    else:
        weakest_items = [e.get("label", "") for e in evidence.get("negative", [])[:2] if e.get("label")]
    return {
        "timing": timing_text,
        "warnings": warnings[:5],
        "strongest": strongest_items,
        "weakest": weakest_items,
    }


def _structured_final_trace(ctx: dict[str, Any], question_text: str, answer_text: str) -> list[dict[str, str]]:
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    ni = _narrator_input(ctx)
    rules = _rules_sections(ctx)
    steps = [
        ("Question", question_text or ctx.get("question") or "—"),
        ("DNA", str((ctx.get("llm_intent") or {}).get("domain") or "—")),
        ("Routing", str(sm.get("archetype") or "—")),
        ("Engine", str(sm.get("slice") or "—")),
        ("Modules", str(len(_modules_loaded(ctx)))),
        ("Rules", str(len(rules.get("fired") or []))),
        ("Evidence", str(
            len((ctx.get("engine_facts") or {}).get("evidence_positive") or [])
            + len((ctx.get("engine_facts") or {}).get("evidence_negative") or [])
        )),
        ("Score", str(rules.get("final_score") or "—")),
        ("Verdict", str(rules.get("verdict") or "—")),
        ("Narrator JSON", "saved" if ni else "—"),
        ("LLM Answer", "saved" if (answer_text or "").strip() else "—"),
    ]
    return [{"label": label, "value": value} for label, value in steps]


def _narrator_input(ctx: dict[str, Any]) -> dict[str, Any] | None:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta")
    sm_checks = sm.get("checks") if isinstance(sm, dict) and isinstance(sm.get("checks"), dict) else {}
    ni = _dig(checks, sm_checks, key="narrator_input")
    if isinstance(ni, dict) and ni:
        return ni
    return None


def _hallucination_checks(answer_text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    answer = (answer_text or "").lower()
    if not answer:
        return []
    sc = _scorecard(ctx)
    ef = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    engine_terms: set[str] = set()
    for k in sc:
        engine_terms.add(k.lower())
    for pool in (
        ef.get("evidence_positive") or [],
        ef.get("evidence_negative") or [],
        ef.get("evidence") or [],
    ):
        for line in pool:
            for word in re.findall(r"[a-zA-Z]{4,}", str(line).lower()):
                engine_terms.add(word)
    ni = _narrator_input(ctx) or {}
    for k in ("strongest", "weakest", "strongest_factor", "weakest_factor", "reason", "warnings"):
        val = ni.get(k)
        if isinstance(val, list):
            for item in val:
                for word in re.findall(r"[a-zA-Z]{4,}", str(item).lower()):
                    engine_terms.add(word)
        elif isinstance(val, str):
            for word in re.findall(r"[a-zA-Z]{4,}", val.lower()):
                engine_terms.add(word)

    axis_aliases = {
        "communication": ("communication", "baat", "communicat", "boundaries", "boundary"),
        "trust": ("trust", "vishwas", "loyal", "trust challenge"),
        "commitment": ("commitment", "commit", "pakka"),
        "chemistry": ("chemistry", "attraction", "spark"),
        "family": ("family", "ghar", "parivar"),
        "clarity": ("clarity", "emotional investment"),
    }
    rows: list[dict[str, Any]] = []
    for axis, aliases in axis_aliases.items():
        in_engine = axis in sc or axis in engine_terms
        mentioned = any(a in answer for a in aliases)
        if mentioned and not in_engine:
            rows.append({
                "field": axis.title(),
                "engine": "NOT FOUND",
                "narrator": f"{axis.title()} mentioned",
                "ok": False,
            })
        elif mentioned and in_engine:
            rows.append({
                "field": axis.title(),
                "engine": f"score {sc.get(axis.title(), sc.get(axis, '—'))}",
                "narrator": "Mentioned",
                "ok": True,
            })
    return rows


def _hallucination_summary(answer_text: str, ctx: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    ef = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    evidence_count = (
        len(ef.get("evidence_positive") or [])
        + len(ef.get("evidence_negative") or [])
        + len(ef.get("evidence_neutral") or [])
        + len(ef.get("evidence") or [])
    )
    rules_count = len(_rules_sections(ctx).get("fired") or [])
    engine_facts_used = evidence_count > 0 or rules_count > 0 or bool(_narrator_input(ctx))
    extra = [c for c in checks if not c.get("ok")]
    missing = [c for c in checks if not c.get("ok") and c.get("engine") == "NOT FOUND"]
    return {
        "engine_facts_used": {
            "ok": engine_facts_used,
            "detail": f"{evidence_count} evidence lines · {rules_count} rules fired",
        },
        "extra_llm_assumptions": {
            "ok": len(extra) == 0,
            "items": [f"{c.get('field')}: narrator mentioned, engine silent" for c in extra[:6]],
        },
        "missing_engine_evidence": {
            "ok": len(missing) == 0,
            "items": [f"{c.get('field')}: no engine backing" for c in missing[:6]],
        },
    }


def build_observability_debug(
    ctx: dict[str, Any] | None,
    *,
    question_text: str = "",
    answer_text: str = "",
    row_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured debugger payload for admin Ask detail."""
    if not isinstance(ctx, dict):
        ctx = {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    archetype = str(sm.get("archetype") or ctx.get("routed_archetype") or "—")
    rules = _rules_sections(ctx)
    modules = _modules_loaded(ctx)
    evidence = _planet_evidence(ctx)
    verdict_extras = _engine_verdict_extras(ctx, evidence)
    hallucination_rows = _hallucination_checks(answer_text, ctx)
    trace_labels = [
        "Question",
        "DNA",
        "Routing",
        "Engine",
        "Modules",
        "Rules",
        "Evidence",
        "Score",
        "Verdict",
        "Narrator JSON",
        "LLM Answer",
    ]
    return {
        "user_question": _user_question_section(ctx, question_text),
        "question_dna_pipeline": _question_dna_pipeline(ctx, question_text),
        "routing_decision": _routing_decision(ctx, question_text),
        "routing_warning": _routing_warning(question_text, archetype),
        "engine_execution": {
            "engine_name": archetype,
            "engine_version": _dig(ctx.get("checks") or {}, sm or {}, key="engine_version"),
            "modules": modules,
            "modules_skipped": _modules_skipped(modules),
            "execution_time_ms": _execution_time_ms(ctx),
            **rules,
        },
        "astrology_checks": _astrology_checks(ctx),
        "planet_evidence": evidence,
        "conflict_resolution": _conflict_resolution(ctx),
        "scorecard": _scorecard(ctx),
        "engine_verdict": {
            "verdict": rules.get("verdict"),
            "level": rules.get("verdict_level"),
            "confidence": rules.get("final_score"),
            "strongest": verdict_extras.get("strongest") or [],
            "weakest": verdict_extras.get("weakest") or [],
            "timing": verdict_extras.get("timing"),
            "warnings": verdict_extras.get("warnings") or [],
        },
        "narrator_input": _narrator_input(ctx),
        "narrator_output": (answer_text or "").strip() or None,
        "hallucination_checks": hallucination_rows,
        "hallucination_summary": _hallucination_summary(answer_text, ctx, hallucination_rows),
        "performance": _performance_section(ctx, row_meta),
        "final_trace": _structured_final_trace(ctx, question_text, answer_text),
        "final_trace_labels": trace_labels,
        "has_v2_rules": bool(rules.get("fired")),
        "has_step_audit": bool(_astrology_checks(ctx).get("d1") or rules.get("fired")),
    }


def attach_observability_to_context(
    ctx: dict[str, Any],
    *,
    question_text: str = "",
    answer_text: str = "",
    row_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(ctx)
    out["observability"] = build_observability_debug(
        out,
        question_text=question_text,
        answer_text=answer_text,
        row_meta=row_meta,
    )
    return out
