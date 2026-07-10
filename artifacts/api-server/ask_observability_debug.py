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

    lang = (
        dna_item.get("language")
        or li.get("language")
        or li.get("reply_lang")
        or "—"
    )
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

    steps = [
        _pipeline_step("Question", question_text or ctx.get("question_raw") or ctx.get("question")),
        _pipeline_step("Language Detection", lang),
        _pipeline_step("Normalized Question", ctx.get("question_normalized") or ctx.get("question")),
        _pipeline_step("Domain", domain),
        _pipeline_step("Bucket", bucket),
        _pipeline_step("Intent", dna_item.get("intent") or li.get("intent") or li.get("question_intent") or "—"),
        _pipeline_step("Subject", dna_item.get("subject") or li.get("subject") or "—"),
        _pipeline_step("Target", dna_item.get("target") or li.get("target") or "—"),
        _pipeline_step("Question Type", dna_item.get("question_type") or ctx.get("question_type") or "—"),
        _pipeline_step("Timing?", dna_item.get("timing") if "timing" in dna_item else ctx.get("is_timing")),
        _pipeline_step("Emotion", dna_item.get("emotion") or li.get("emotion") or "—"),
        _pipeline_step("Risk", dna_item.get("risk") or li.get("risk") or "—"),
        _pipeline_step("Primary Engine", archetype),
        _pipeline_step("Secondary Engine", secondary),
        _pipeline_step("Confidence", dna_item.get("confidence") or li.get("confidence") or "—"),
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
    if not pos and not neg:
        pool = list(ef.get("evidence") or sm.get("evidence") or [])
        for line in pool:
            s = str(line)
            if any(w in s.lower() for w in ("weak", "delay", "afflict", "risk", "negative", "❌")):
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
    }


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
    return {
        "modules": modules,
        "conflict": "Minor" if detected else "None",
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
    for k in ("strongest_factor", "weakest_factor", "warnings"):
        val = ni.get(k)
        if isinstance(val, list):
            for item in val:
                for word in re.findall(r"[a-zA-Z]{4,}", str(item).lower()):
                    engine_terms.add(word)
        elif isinstance(val, str):
            for word in re.findall(r"[a-zA-Z]{4,}", val.lower()):
                engine_terms.add(word)

    axis_aliases = {
        "communication": ("communication", "baat", "communicat"),
        "trust": ("trust", "vishwas", "loyal"),
        "commitment": ("commitment", "commit", "pakka"),
        "chemistry": ("chemistry", "attraction", "spark"),
        "family": ("family", "ghar", "parivar"),
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


def build_observability_debug(
    ctx: dict[str, Any] | None,
    *,
    question_text: str = "",
    answer_text: str = "",
) -> dict[str, Any]:
    """Structured debugger payload for admin Ask detail."""
    if not isinstance(ctx, dict):
        ctx = {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    archetype = str(sm.get("archetype") or ctx.get("routed_archetype") or "—")
    rules = _rules_sections(ctx)
    trace_labels = [
        "Question",
        "DNA",
        "Engine",
        "Modules",
        "Rules Fired",
        "Evidence",
        "Score",
        "Verdict",
        "Narrator JSON",
        "LLM Answer",
    ]
    return {
        "question_dna_pipeline": _question_dna_pipeline(ctx, question_text),
        "routing_warning": _routing_warning(question_text, archetype),
        "engine_execution": {
            "modules": _modules_loaded(ctx),
            **rules,
        },
        "planet_evidence": _planet_evidence(ctx),
        "conflict_resolution": _conflict_resolution(ctx),
        "scorecard": _scorecard(ctx),
        "narrator_input": _narrator_input(ctx),
        "narrator_output": (answer_text or "").strip() or None,
        "hallucination_checks": _hallucination_checks(answer_text, ctx),
        "final_trace": trace_labels,
        "has_v2_rules": bool(rules.get("fired")),
    }


def attach_observability_to_context(ctx: dict[str, Any], *, question_text: str = "", answer_text: str = "") -> dict[str, Any]:
    out = dict(ctx)
    out["observability"] = build_observability_debug(
        out,
        question_text=question_text,
        answer_text=answer_text,
    )
    return out
