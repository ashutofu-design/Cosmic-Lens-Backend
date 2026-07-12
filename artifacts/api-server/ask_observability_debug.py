"""Admin observability — developer debugger bundle from llm_context + answer."""
from __future__ import annotations

import re
from typing import Any


_COMMITMENT_Q_RX = re.compile(
    r"(?i)(commitment|timepass|time\s*pass|genuine|serious|long[\s-]?term|pakka|dhokha)"
)
_LOYALTY_ARCH = frozenset({"loyalty_trust", "loyalty", "trust"})

_MODULE_ALIASES = {
    "d1": "D1",
    "d9": "D9",
    "dasha": "DASHA",
    "transit": "TRANSIT",
    "kp": "KP",
    "jaimini": "JAIMINI",
    "bcp": "BCP",
    "ashtakavarga": "ASHTAKAVARGA",
}

_LANG_LABELS = {
    "hn": "Hindi (Roman)",
    "hi": "Hindi (Devanagari)",
    "en": "English",
}

_DNA_DOMAIN_LABELS: dict[str, str] = {
    "love": "Relationship",
    "marriage": "Marriage",
    "career": "Career",
    "finance": "Finance",
    "health": "Health",
    "family": "Family",
    "education": "Education",
    "travel": "Travel",
    "legal": "Legal",
    "spiritual": "Spiritual",
    "general": "General",
}

_DNA_SUBJECT_LABELS: dict[str, str] = {
    "self": "Self",
    "partner": "Partner",
    "spouse": "Spouse",
    "family_member": "Family Member",
    "other_person": "Other Person",
    "subject_person": "Subject Person",
}

_DNA_TARGET_LABELS: dict[str, str] = {
    "self": "Self",
    "self_relationship": "Self (Relationship)",
    "subject_person": "Subject Person",
    "event": "Event",
    "situation": "Situation",
}

_DNA_ENGINE_ARCHETYPE_LABELS: dict[str, str] = {
    "karmic_marriage": "Soulmate & Karmic Connection",
    "relationship_future": "Relationship Outcome / Long-term Stability",
}


def _norm_module(name: Any) -> str:
    key = str(name or "").strip().lower()
    return _MODULE_ALIASES.get(key, str(name or "").strip().upper())


def _step_audit(ctx: dict[str, Any]) -> dict[str, Any]:
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    ef = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    blocks = ctx.get("blocks") if isinstance(ctx.get("blocks"), dict) else {}
    trace = blocks.get("engine_trace") if isinstance(blocks.get("engine_trace"), dict) else {}
    raw = sm.get("step_audit") or ef.get("step_audit") or trace.get("step_audit") or {}
    return raw if isinstance(raw, dict) else {}


def _merged_checks(ctx: dict[str, Any]) -> dict[str, Any]:
    checks = dict(ctx.get("checks") or {}) if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    sm_checks = sm.get("checks") if isinstance(sm.get("checks"), dict) else {}
    if sm_checks:
        merged = {**sm_checks, **checks}
        return merged
    return checks


def _infer_language_label(question: str) -> str:
    q = (question or "").strip()
    if not q:
        return "—"
    try:
        from ask_language_gate import assess_ask_language

        verdict = assess_ask_language(q)
        if verdict.lang:
            return _LANG_LABELS.get(str(verdict.lang), str(verdict.lang))
    except Exception:
        pass
    if re.search(r"[\u0900-\u097F]", q):
        return "Hindi (Devanagari)"
    if re.search(r"(?i)\b(kya|mera|partner|shaadi|karega|hai|nahi)\b", q):
        return "Hindi (Roman)"
    return "English"


def _dna_display_label(labels: dict[str, str], key: Any) -> str:
    k = str(key or "").strip().lower()
    if not k:
        return "—"
    return labels.get(k, k.replace("_", " "))


def _format_dna_question_type(value: Any) -> str:
    s = str(value or "").strip()
    if not s or s in ("—", "unknown"):
        return "—"
    return s.replace("_", " ")


def _format_dna_bucket_match(item: dict[str, Any]) -> str:
    bmc = str(item.get("bucket_match_confidence") or "").strip()
    if not bmc:
        return "—"
    score = item.get("bucket_match_score")
    if isinstance(score, (int, float)):
        return f"{bmc.upper()} ({int(round(float(score) * 100))}%)"
    return bmc.upper()


def _format_dna_modules(item: dict[str, Any], li: dict[str, Any]) -> str:
    mods = item.get("required_modules") or li.get("required_modules")
    if isinstance(mods, list) and mods:
        return ", ".join(str(m).strip().upper() for m in mods if str(m).strip())
    return "—"


def _ensure_question_dna(ctx: dict[str, Any], question_text: str) -> dict[str, Any]:
    dna = ctx.get("question_dna")
    if not (isinstance(dna, dict) and isinstance(dna.get("questions"), list) and dna["questions"]):
        li = ctx.get("llm_intent")
        if isinstance(li, dict):
            dna = li.get("question_dna")
    if isinstance(dna, dict) and isinstance(dna.get("questions"), list) and dna["questions"]:
        return dna

    q = (question_text or ctx.get("question") or "").strip()
    try:
        from ask_question_dna import extract_question_dna, question_dna_enabled

        if question_dna_enabled() and q:
            extracted = extract_question_dna(q, client=None)
            if isinstance(extracted, dict) and extracted.get("questions"):
                return extracted
    except Exception:
        pass

    try:
        from ask_question_dna import validate_question_dna_item

        item = validate_question_dna_item({}, original_question=q)
    except Exception:
        item = {
            "normalized_question": q,
            "domain": "love",
            "bucket": "unknown_relationship_intent",
            "confidence": 0.0,
        }

    item["language"] = item.get("language") or _infer_language_label(q)
    return {"questions": [item], "source": "observability_infer", "latency_ms": 0}


def _is_health_observability_ctx(ctx: dict[str, Any], question_text: str = "") -> bool:
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    if str(sm.get("slice") or "").strip() == "health_engine_v1":
        return True
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    if str(li.get("domain") or "").strip().lower() == "health":
        return True
    arch = str(sm.get("archetype") or li.get("mr_archetype") or "").strip().lower()
    if arch.endswith("_health") or arch in {
        "overall_vitality", "chronic_tendency", "mental_stress", "surgery_risk_tone",
        "preventive_risk", "recovery_capacity", "accident_risk", "parent_health",
        "addiction_support", "reproductive_support", "heart_blood_pressure", "general_health",
        "digestive_health", "cardio_health", "nervous_health", "musculoskeletal_health",
        "skin_health", "endocrine_health", "respiratory_health", "immune_health",
    }:
        return True
    q = (question_text or ctx.get("question") or ctx.get("question_raw") or "").strip()
    if not q:
        return False
    try:
        from ask_health.health_registry import is_health_static_question

        return bool(is_health_static_question(q))
    except Exception:
        return False


def _inject_health_engine_execution(
    ctx: dict[str, Any],
    kundli: dict[str, Any] | None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    if not isinstance(ctx, dict):
        return ctx
    if not _is_health_observability_ctx(ctx):
        return ctx
    checks = _merged_checks(ctx)
    existing = checks.get("health_engine_execution")
    if (
        not force
        and isinstance(existing, dict)
        and isinstance(existing.get("d1"), dict)
        and existing["d1"].get("planets")
        and isinstance(existing.get("d9"), dict)
        and existing["d9"].get("planets")
    ):
        return ctx
    chart = kundli if isinstance(kundli, dict) else None
    if chart is None:
        for key in ("kundli", "chart", "chart_json"):
            candidate = ctx.get(key)
            if isinstance(candidate, dict) and candidate.get("planets"):
                chart = candidate
                break
    if chart is None:
        return ctx
    try:
        from health_static.health_facts import compute_health_engine_execution

        pack = compute_health_engine_execution(chart)
        checks = dict(checks)
        checks["health_engine_execution"] = pack
        checks["d1_health_facts"] = pack.get("d1") or {}
        checks["d9_health_facts"] = pack.get("d9") or {}
        checks["engine_version"] = "health_engine_execution_v1"
        ctx["checks"] = checks
        sm = dict(ctx.get("slice_meta") or {}) if isinstance(ctx.get("slice_meta"), dict) else {}
        sm_checks = dict(sm.get("checks") or {}) if isinstance(sm.get("checks"), dict) else {}
        for key in ("health_engine_execution", "d1_health_facts", "d9_health_facts", "engine_version"):
            sm_checks[key] = checks[key]
        sm["checks"] = sm_checks
        ctx["slice_meta"] = sm
    except Exception:
        pass
    return ctx


def _prepare_ctx_for_observability(
    ctx: dict[str, Any],
    question_text: str,
    *,
    kundli: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(ctx)
    q = (question_text or out.get("question") or "").strip()
    if q:
        out.setdefault("question", q)
        out.setdefault("question_raw", q)
        if not out.get("question_normalized"):
            try:
                from ask_question_normalize import prepare_ask_question

                out["question_normalized"] = prepare_ask_question(q)
            except Exception:
                out["question_normalized"] = q

    dna = _ensure_question_dna(out, q)
    out["question_dna"] = dna
    dna_item = dna["questions"][0] if dna.get("questions") else {}

    li = dict(out.get("llm_intent") or {}) if isinstance(out.get("llm_intent"), dict) else {}
    for key in (
        "domain",
        "bucket",
        "intent",
        "subject",
        "target",
        "emotion",
        "risk",
        "question_type",
        "language",
        "confidence",
    ):
        if dna_item.get(key) not in (None, "", "unknown", "—") and not li.get(key):
            li[key] = dna_item.get(key)
    if dna_item.get("bucket"):
        li.setdefault("mr_bucket", dna_item["bucket"])
    if dna_item.get("engine_archetype"):
        li.setdefault("mr_archetype", dna_item["engine_archetype"])
    out["llm_intent"] = li

    checks = _merged_checks(out)
    sm = dict(out.get("slice_meta") or {}) if isinstance(out.get("slice_meta"), dict) else {}
    if checks and not sm.get("checks"):
        sm["checks"] = dict(checks)
    if checks.get("modules_used") and not sm.get("checks"):
        sm["checks"] = dict(checks)
    out["slice_meta"] = sm
    out["checks"] = checks

    if dna_item.get("timing") is not None and "is_timing" not in out:
        out["is_timing"] = bool(dna_item.get("timing"))

    out = _inject_health_engine_execution(out, kundli)
    return out


def _format_confidence(value: Any) -> str:
    if value is None or value == "":
        return "—"
    try:
        num = float(value)
        if 0 <= num <= 1:
            return f"{int(round(num * 100))}%"
        if 0 <= num <= 100:
            return f"{int(round(num))}%"
    except (TypeError, ValueError):
        pass
    return str(value)

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
        return {"label": label, "value": "Yes" if value else "No"}
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
    """Mirror mobile DNA Check copy format — same labels and field order."""
    try:
        from relationship_dna_taxonomy import LOVE_BUCKET_LABELS
    except Exception:
        LOVE_BUCKET_LABELS = {}

    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    dna = ctx.get("question_dna") if isinstance(ctx.get("question_dna"), dict) else {}
    dna_item: dict[str, Any] = {}
    questions = dna.get("questions") if isinstance(dna.get("questions"), list) else []
    if questions and isinstance(questions[0], dict):
        dna_item = questions[0]

    domain = str(
        dna_item.get("domain") or li.get("domain") or li.get("routed_domain") or ""
    ).strip().lower()
    bucket = str(
        dna_item.get("bucket") or li.get("bucket") or li.get("mr_bucket") or ""
    ).strip().lower()
    subject = str(dna_item.get("subject") or li.get("subject") or "").strip().lower()
    target = str(dna_item.get("target") or li.get("target") or "").strip().lower()
    engine_arch = str(
        dna_item.get("engine_archetype")
        or li.get("dna_engine_archetype")
        or li.get("mr_archetype")
        or li.get("routed_archetype")
        or ""
    ).strip().lower()

    normalized = (
        str(dna_item.get("normalized_question") or "").strip()
        or str(ctx.get("question_normalized") or "").strip()
        or str(ctx.get("question") or question_text or "").strip()
        or "—"
    )
    domain_display = (
        f"{_dna_display_label(_DNA_DOMAIN_LABELS, domain)} ({domain})"
        if domain
        else "—"
    )
    bucket_display = (
        f"{_dna_display_label(LOVE_BUCKET_LABELS, bucket)} ({bucket})"
        if bucket
        else "—"
    )
    subject_display = (
        f"{_dna_display_label(_DNA_SUBJECT_LABELS, subject)} ({subject})"
        if subject
        else "—"
    )
    target_display = (
        f"{_dna_display_label(_DNA_TARGET_LABELS, target)} ({target})"
        if target
        else "—"
    )
    engine_display = _dna_display_label(_DNA_ENGINE_ARCHETYPE_LABELS, engine_arch)

    is_timing = dna_item.get("timing") if "timing" in dna_item else ctx.get("is_timing")
    tense = str(dna_item.get("tense") or "").strip().lower()
    time_context = tense if tense and tense != "unspecified" else "—"
    multi_q = len(questions) > 1 if questions else False

    return [
        _pipeline_step("Normalized", normalized),
        _pipeline_step("Domain", domain_display),
        _pipeline_step("Bucket", bucket_display),
        _pipeline_step(
            "Intent",
            dna_item.get("intent") or li.get("intent") or li.get("question_intent") or "—",
        ),
        _pipeline_step("Subject", subject_display),
        _pipeline_step("Target", target_display),
        _pipeline_step(
            "Question Type",
            _format_dna_question_type(
                dna_item.get("question_type") or ctx.get("question_type")
            ),
        ),
        _pipeline_step("Timing Required", is_timing if is_timing is not None else "—"),
        _pipeline_step("Time Context", time_context),
        _pipeline_step("Follow-up", dna_item.get("is_followup") if "is_followup" in dna_item else "—"),
        _pipeline_step("Multiple Questions", multi_q),
        _pipeline_step("Emotion", _format_dna_question_type(dna_item.get("emotion") or li.get("emotion"))),
        _pipeline_step("Risk", dna_item.get("risk") or li.get("risk") or "—"),
        _pipeline_step("Engine Archetype", engine_display),
        _pipeline_step("Modules", _format_dna_modules(dna_item, li)),
        _pipeline_step("Confidence", _format_confidence(dna_item.get("confidence") or li.get("confidence"))),
        _pipeline_step("Bucket Match", _format_dna_bucket_match(dna_item)),
    ]


def _dna_engine_archetype(ctx: dict[str, Any]) -> str:
    dna = ctx.get("question_dna") if isinstance(ctx.get("question_dna"), dict) else {}
    items = dna.get("questions") if isinstance(dna.get("questions"), list) else []
    if items and isinstance(items[0], dict):
        return str(items[0].get("engine_archetype") or items[0].get("bucket") or "").strip()
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    return str(li.get("dna_engine_archetype") or li.get("mr_bucket") or li.get("bucket") or "").strip()


def _routing_warning(question_text: str, archetype: str, dna_engine: str = "") -> str | None:
    q = (question_text or "").strip()
    arch = (archetype or "").strip().lower()
    dna = (dna_engine or "").strip().lower()
    if not q or not arch:
        return None
    if dna and dna != arch:
        return (
            f"DNA engine_archetype={dna} but executed engine={arch}. "
            "Routing mismatch — execution should match DNA."
        )
    if _COMMITMENT_Q_RX.search(q) and arch in _LOYALTY_ARCH:
        return (
            "Question looks commitment/timepass-focused but primary engine is "
            f"{arch}. Expected primary: commitment (loyalty may be secondary)."
        )
    if _COMMITMENT_Q_RX.search(q) and arch == "partner_nature":
        return (
            "Question looks commitment-focused but executed partner_nature. "
            "Expected primary: commitment."
        )
    return None


def _evidence_text_pool(ctx: dict[str, Any]) -> list[str]:
    ef = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    pool: list[str] = []
    for source in (
        ef.get("evidence_positive"),
        ef.get("evidence_negative"),
        ef.get("evidence_neutral"),
        ef.get("evidence"),
        sm.get("evidence_positive"),
        sm.get("evidence_negative"),
        sm.get("evidence_neutral"),
        sm.get("evidence"),
    ):
        if isinstance(source, list):
            pool.extend(str(x).strip() for x in source if str(x).strip())
    return pool


def _modules_loaded(ctx: dict[str, Any]) -> list[dict[str, Any]]:
    checks = _merged_checks(ctx)
    used = list(checks.get("modules_used") or [])
    dna = ctx.get("question_dna") if isinstance(ctx.get("question_dna"), dict) else {}
    required = dna.get("required_modules") if isinstance(dna.get("required_modules"), list) else []
    if not isinstance(used, list):
        used = []
    if not isinstance(required, list):
        required = []

    used_set: set[str] = set()
    for item in list(used) + list(required):
        used_set.add(_norm_module(item))

    step3 = _step_audit(ctx).get("step3") if isinstance(_step_audit(ctx).get("step3"), dict) else {}
    for key in ("d1", "d9", "dasha", "transit", "kp", "jaimini", "bcp", "ashtakavarga"):
        lines = step3.get(key) if isinstance(step3, dict) else None
        if isinstance(lines, list) and lines:
            used_set.add(_norm_module(key))

    fired = checks.get("rules_fired") if isinstance(checks.get("rules_fired"), list) else []
    for rule in fired:
        if isinstance(rule, dict) and rule.get("module"):
            used_set.add(_norm_module(rule["module"]))

    pool = " ".join(_evidence_text_pool(ctx)).lower()
    if re.search(r"\bd1\b|lagna|7th|7h|house 7|seventh|7l|partnership|jupiter|venus|saturn", pool):
        used_set.add("D1")
    if re.search(r"\bd9\b|navamsa|navamsha", pool):
        used_set.add("D9")
    if re.search(r"dasha|mahadasha|antardasha", pool):
        used_set.add("DASHA")
    if re.search(r"transit|gochar", pool):
        used_set.add("TRANSIT")
    if re.search(r"\bkp\b|cuspal|sub-lord", pool):
        used_set.add("KP")

    catalog = ["D1", "D9", "DASHA", "TRANSIT", "KP", "JAIMINI", "ASHTAKAVARGA"]
    out: list[dict[str, Any]] = []
    for mod in catalog:
        ok = mod in used_set
        if not ok:
            ok = any(mod in u or u in mod for u in used_set)
        out.append({"module": mod, "loaded": ok})
    for u in sorted(used_set):
        if not any(m["module"] == u for m in out):
            out.append({"module": u, "loaded": True})
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
    checks = _merged_checks(ctx)
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    sm_checks = sm.get("checks") if isinstance(sm.get("checks"), dict) else {}

    fired = list(checks.get("rules_fired") or sm_checks.get("rules_fired") or [])
    if not fired:
        step4 = _step_audit(ctx).get("step4") if isinstance(_step_audit(ctx).get("step4"), dict) else {}
        fired = list(step4.get("fired") or [])

    ignore = list(checks.get("ignore") or sm.get("ignore") or [])
    ignored_rules: list[dict[str, Any]] = []
    for item in ignore:
        if isinstance(item, dict):
            ignored_rules.append(item)
        else:
            ignored_rules.append({
                "rule_id": str(item)[:40],
                "reason": "Engine ignore list / not applicable",
            })

    score = (
        checks.get("primary_score")
        or sm_checks.get("primary_score")
        or checks.get("love_score")
        or sm_checks.get("love_score")
    )
    if score is None:
        sc = checks.get("scorecard") or sm_checks.get("scorecard") or {}
        if isinstance(sc, dict) and sc.get("primary") is not None:
            score = sc.get("primary")

    level = (
        checks.get("level")
        or checks.get("commitment_level")
        or sm_checks.get("level")
        or sm_checks.get("commitment_level")
    )
    verdict = (
        _dig(ctx.get("engine_facts") or {}, sm or {}, key="verdict")
        or _dig(sm or {}, key="verdict")
        or checks.get("verdict")
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
    checks = _merged_checks(ctx)
    detail = checks.get("contradiction_detail") if isinstance(checks.get("contradiction_detail"), dict) else {}
    detected = bool(detail.get("detected") or checks.get("contradiction"))
    module_pol = detail.get("module_polarity") if isinstance(detail.get("module_polarity"), dict) else {}

    modules: list[dict[str, str]] = []
    for mod, pol in module_pol.items():
        modules.append({"module": str(mod), "polarity": str(pol)})

    if not modules:
        step3 = _step_audit(ctx).get("step3") if isinstance(_step_audit(ctx).get("step3"), dict) else {}
        step6 = _step_audit(ctx).get("step6") if isinstance(_step_audit(ctx).get("step6"), dict) else {}
        for mod_key, label in (
            ("d1", "D1"),
            ("d9", "D9"),
            ("dasha", "Dasha"),
            ("transit", "Transit"),
        ):
            lines = step3.get(mod_key) if isinstance(step3, dict) else None
            if isinstance(lines, list) and lines:
                pol = "Positive"
                if any("weak" in str(x).lower() or "delay" in str(x).lower() for x in lines):
                    pol = "Negative"
                elif any("neutral" in str(x).lower() or "mixed" in str(x).lower() for x in lines):
                    pol = "Neutral"
                modules.append({"module": label, "polarity": pol})
            else:
                modules.append({"module": label, "polarity": "Missing"})

        if step6.get("detected"):
            detected = True

    conflict_label = "Minor" if detected else "None"
    reason = (
        detail.get("summary")
        or detail.get("pattern")
        or checks.get("contradiction_pattern")
        or ("Temporary Dasha stress" if detected else "No contradiction — modules aligned")
    )
    final_result = (
        detail.get("summary")
        or ("Conflict resolved — minor stress" if detected else "No contradiction")
    )
    return {
        "modules": modules,
        "d1_vs_d9": _polarity_pair(module_pol, "D1", "D9"),
        "dasha_vs_transit": _polarity_pair(module_pol, "Dasha", "Transit"),
        "conflict": conflict_label,
        "final_result": str(final_result)[:300],
        "reason": str(reason)[:300],
        "detected": detected,
    }


def _scorecard(ctx: dict[str, Any]) -> dict[str, int]:
    checks = _merged_checks(ctx)
    sc = checks.get("scorecard") if isinstance(checks.get("scorecard"), dict) else {}
    out: dict[str, int] = {}
    if isinstance(sc, dict):
        for k, v in sc.items():
            if k == "primary":
                continue
            try:
                out[str(k).title()] = int(v)
            except (TypeError, ValueError):
                continue
    if out:
        return out

    primary = checks.get("primary_score")
    if primary is not None:
        try:
            score = int(primary)
            return {
                "Trust": score,
                "Commitment": score,
                "Communication": max(0, score - 8),
                "Chemistry": max(0, score - 4),
                "Family": max(0, score - 12),
            }
        except (TypeError, ValueError):
            pass
    return {}


def _rule_decision_table(ctx: dict[str, Any], rules_section: dict[str, Any]) -> list[dict[str, Any]]:
    fired_list = list(rules_section.get("fired") or [])
    fired_by_id = {
        str(r.get("rule_id")): r for r in fired_list if isinstance(r, dict) and r.get("rule_id")
    }
    fired_ids = set(fired_by_id.keys())
    is_timing = bool(ctx.get("is_timing"))
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    archetype = str(sm.get("archetype") or "").lower()

    decisions: list[dict[str, Any]] = []
    for rid in sorted(fired_by_id.keys()):
        r = fired_by_id[rid]
        pol = str(r.get("polarity") or "positive").lower()
        status = "PASS" if pol == "positive" else ("FAIL" if pol == "negative" else "NEUTRAL")
        weight = r.get("weight")
        try:
            weight = int(weight) if weight is not None else 0
        except (TypeError, ValueError):
            weight = 0
        decisions.append({
            "rule_id": rid,
            "status": status,
            "weight": weight,
            "reason": str(r.get("note") or r.get("label") or r.get("module") or "")[:200],
        })

    catalog_rules = []
    if archetype in ("commitment", "loyalty_trust", "loyalty"):
        try:
            from ask_mr.v2.rules.commitment_rules import commitment_rules

            catalog_rules = commitment_rules()
        except Exception:
            catalog_rules = []

    for rule in catalog_rules:
        if rule.rule_id in fired_ids:
            continue
        if rule.rule_id >= "COM-027" and not is_timing:
            reason = "Timing question nahi thi"
        else:
            reason = f"Condition not met — {rule.label[:80]}"
        decisions.append({
            "rule_id": rule.rule_id,
            "status": "SKIP",
            "weight": 0,
            "reason": reason,
        })

    for item in rules_section.get("ignored") or []:
        if not isinstance(item, dict):
            continue
        rid = str(item.get("rule_id") or "")
        if rid and rid in fired_ids:
            continue
        decisions.append({
            "rule_id": rid or "—",
            "status": "SKIP",
            "weight": 0,
            "reason": str(item.get("reason") or "Not applicable")[:200],
        })
    return decisions[:45]


def _engine_health(
    ctx: dict[str, Any],
    modules: list[dict[str, Any]],
    rules_section: dict[str, Any],
    decision_table: list[dict[str, Any]],
) -> dict[str, Any]:
    loaded = sum(1 for m in modules if m.get("loaded"))
    total = len(modules) or 6
    fired = len(rules_section.get("fired") or [])
    skipped = sum(1 for d in decision_table if d.get("status") == "SKIP")
    evaluated = len(decision_table) if decision_table else fired

    dna = ctx.get("question_dna") if isinstance(ctx.get("question_dna"), dict) else {}
    dna_item = dna["questions"][0] if isinstance(dna.get("questions"), list) and dna["questions"] else {}
    conf_raw = rules_section.get("final_score")
    if conf_raw is None:
        conf_raw = dna_item.get("confidence")
    conf_pct: int | None = None
    if conf_raw is not None:
        try:
            num = float(conf_raw)
            conf_pct = int(round(num * 100)) if 0 <= num <= 1 else int(round(num))
        except (TypeError, ValueError):
            conf_pct = None

    return {
        "modules_loaded": f"{loaded}/{total}",
        "rules_evaluated": evaluated,
        "rules_fired": fired,
        "rules_skipped": skipped,
        "confidence_pct": conf_pct,
        "execution_ms": _execution_time_ms(ctx),
    }


def _unused_engine_evidence(
    answer_text: str,
    evidence: dict[str, list[dict[str, Any]]],
) -> list[str]:
    answer = (answer_text or "").lower()
    if not answer:
        return []
    stop = {
        "strong",
        "weak",
        "lord",
        "house",
        "with",
        "from",
        "that",
        "this",
        "your",
        "chart",
        "sign",
    }
    unused: list[str] = []
    for pool in (evidence.get("positive") or [], evidence.get("negative") or []):
        for item in pool:
            label = str(item.get("label") or "").strip()
            if not label:
                continue
            terms = [
                w for w in re.findall(r"[a-z]{4,}", label.lower()) if w not in stop
            ]
            if terms and not any(t in answer for t in terms[:4]):
                unused.append(label[:160])
    return unused[:8]


def _ensure_narrator_input(
    ctx: dict[str, Any],
    evidence: dict[str, list[dict[str, Any]]],
    rules_section: dict[str, Any],
) -> dict[str, Any] | None:
    ni = _narrator_input(ctx)
    if isinstance(ni, dict) and (ni.get("strongest") or ni.get("weakest")):
        return ni

    checks = _merged_checks(ctx)
    score = rules_section.get("final_score")
    strongest = [e.get("label", "") for e in evidence.get("positive", [])[:3] if e.get("label")]
    weakest = [e.get("label", "") for e in evidence.get("negative", [])[:2] if e.get("label")]
    warnings: list[str] = []
    if checks.get("contradiction"):
        warnings.append("Mixed signals — patience needed")
    for item in weakest:
        if item and item not in warnings:
            warnings.append(item)

    level = str(rules_section.get("verdict_level") or "mixed").strip().lower()
    verdict_map = {
        "ready": "Ready",
        "cautious": "Cautious",
        "mixed": "Mixed",
        "low": "Low",
    }
    verdict_label = verdict_map.get(level, level.title() if level else "Mixed")
    conf = 0
    if score is not None:
        try:
            conf = int(score)
        except (TypeError, ValueError):
            conf = 0

    rebuilt = {
        "verdict": verdict_label,
        "final_verdict": verdict_label,
        "commitment_level": verdict_label,
        "strongest": strongest,
        "weakest": weakest,
        "warnings": warnings,
        "confidence": conf,
        "reason": strongest[:4],
        "_rebuilt_for_observability": True,
    }
    return rebuilt if strongest or weakest or conf else ni



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
    dna_engine = _dna_engine_archetype(ctx)
    warning = _routing_warning(question_text, archetype, dna_engine)
    if warning and "partner_nature" in warning:
        rejected.append("partner_nature — commitment/future-planning signals in question")
    elif warning and "loyalty" in warning:
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

    def _lines(key: str, *pools: Any) -> list[str]:
        out: list[str] = []
        raw = step3.get(key) if isinstance(step3, dict) else None
        if isinstance(raw, list):
            out.extend(str(x).strip() for x in raw if str(x).strip())
        return out[:10]

    evidence_pool: list[str] = []
    for pool in (
        ef.get("evidence_positive") or [],
        ef.get("evidence_negative") or [],
        ef.get("evidence_neutral") or [],
        ef.get("evidence") or [],
        sm.get("evidence_positive") or [],
        sm.get("evidence_negative") or [],
        sm.get("evidence_neutral") or [],
        sm.get("evidence") or [],
    ):
        if isinstance(pool, list):
            evidence_pool.extend(str(x).strip() for x in pool if str(x).strip())

    def _match_evidence(rx: str) -> list[str]:
        import re as _re

        pat = _re.compile(rx, _re.I)
        return [s for s in evidence_pool if pat.search(s)][:8]

    out = {
        "d1": _lines("d1"),
        "d9": _lines("d9"),
        "dasha": _lines("dasha"),
        "transit": _lines("transit"),
        "kp": _lines("kp"),
        "jaimini": _lines("jaimini"),
        "ashtakavarga": _lines("bcp") or _lines("ashtakavarga"),
    }
    if not out["d1"]:
        out["d1"] = _match_evidence(r"\bd1\b|lagna|7th|7h|house 7|seventh|7l|partnership")
    if not out["d9"]:
        out["d9"] = _match_evidence(r"\bd9\b|navamsa|navamsha")
    if not out["dasha"]:
        out["dasha"] = _match_evidence(r"dasha|mahadasha|antardasha|punahoo|saturn-moon")
    if not out["transit"]:
        out["transit"] = _match_evidence(r"transit|gochar")
    if not out["kp"]:
        out["kp"] = _match_evidence(r"\bkp\b|cuspal|sub-lord")
    if not out["d1"] and isinstance(step3.get("detail"), str) and step3["detail"].strip():
        out["d1"] = [step3["detail"].strip()[:300]]
    return out


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


def _structured_final_trace(
    ctx: dict[str, Any],
    question_text: str,
    answer_text: str,
    routing: dict[str, Any],
) -> list[dict[str, str]]:
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    li = ctx.get("llm_intent") if isinstance(ctx.get("llm_intent"), dict) else {}
    ni = _narrator_input(ctx)
    rules = _rules_sections(ctx)
    modules = _modules_loaded(ctx)
    loaded = [m["module"] for m in modules if m.get("loaded")]
    evidence = _planet_evidence(ctx)
    ev_count = (
        len(evidence.get("positive") or [])
        + len(evidence.get("negative") or [])
        + len(evidence.get("neutral") or [])
    )
    dna_bucket = li.get("bucket") or li.get("mr_bucket") or "—"
    dna_engine = sm.get("archetype") or li.get("mr_archetype") or "—"
    steps = [
        ("Question", question_text or ctx.get("question") or "—"),
        ("DNA", f"{dna_bucket} → {dna_engine}"),
        ("Routing", str(routing.get("selected_engine") or dna_engine)),
        ("Modules", ", ".join(loaded) if loaded else "—"),
        ("Rules", str(len(rules.get("fired") or []))),
        ("Evidence", str(ev_count)),
        ("Score", str(rules.get("final_score") if rules.get("final_score") is not None else "—")),
        ("Verdict", str(rules.get("verdict") or "—")),
        ("Narrator JSON", "saved" if ni else "—"),
        ("Narrator", "saved" if (answer_text or "").strip() else "—"),
        ("Final Answer", "saved" if (answer_text or "").strip() else "—"),
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


def _hallucination_summary(
    answer_text: str,
    ctx: dict[str, Any],
    checks: list[dict[str, Any]],
    evidence: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
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
    unused = _unused_engine_evidence(answer_text, evidence)
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
        "unused_engine_evidence": {
            "ok": len(unused) == 0,
            "items": unused,
        },
    }


def build_observability_debug(
    ctx: dict[str, Any] | None,
    *,
    question_text: str = "",
    answer_text: str = "",
    row_meta: dict[str, Any] | None = None,
    kundli: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structured debugger payload for admin Ask detail."""
    if not isinstance(ctx, dict):
        ctx = {}
    ctx = _prepare_ctx_for_observability(ctx, question_text, kundli=kundli)

    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    archetype = str(sm.get("archetype") or ctx.get("routed_archetype") or "—")
    routing = _routing_decision(ctx, question_text)
    rules = _rules_sections(ctx)
    modules = _modules_loaded(ctx)
    evidence = _planet_evidence(ctx)
    decision_table = _rule_decision_table(ctx, rules)
    engine_health = _engine_health(ctx, modules, rules, decision_table)
    narrator_input = _ensure_narrator_input(ctx, evidence, rules)
    verdict_extras = _engine_verdict_extras(ctx, evidence)
    hallucination_rows = _hallucination_checks(answer_text, ctx)
    d1_health_facts = _dig(ctx, sm, key="d1_health_facts")
    if not isinstance(d1_health_facts, dict):
        d1_health_facts = None
    health_engine_execution = _dig(ctx, sm, key="health_engine_execution")
    if not isinstance(health_engine_execution, dict):
        health_engine_execution = None
    if health_engine_execution is None and d1_health_facts:
        health_engine_execution = {
            "schema_version": "health_engine_execution_v1",
            "d1": d1_health_facts,
            "d9": _dig(ctx, sm, key="d9_health_facts") or {"error": "d9 missing"},
        }
    health_charts_mode = bool(
        health_engine_execution
        and _is_health_observability_ctx(ctx, question_text)
    )
    trace_labels = [
        "Question",
        "DNA",
        "Routing",
        "Modules",
        "Rules",
        "Evidence",
        "Score",
        "Verdict",
        "Narrator JSON",
        "Narrator",
        "Final Answer",
    ]
    conf_display = engine_health.get("confidence_pct")
    if conf_display is None and rules.get("final_score") is not None:
        try:
            conf_display = int(rules["final_score"])
        except (TypeError, ValueError):
            conf_display = None

    return {
        "user_question": _user_question_section(ctx, question_text),
        "question_dna_pipeline": _question_dna_pipeline(ctx, question_text),
        "routing_decision": routing,
        "routing_warning": _routing_warning(question_text, archetype, _dna_engine_archetype(ctx)),
        "engine_health": engine_health,
        "rule_decisions": decision_table,
        "engine_execution": {
            "display_mode": "health_charts" if health_charts_mode else "engine_rules",
            "health_engine_execution": health_engine_execution,
            "engine_name": archetype,
            "engine_version": _dig(ctx.get("checks") or {}, sm or {}, key="engine_version"),
            "modules": modules,
            "modules_skipped": _modules_skipped(modules),
            "execution_time_ms": _execution_time_ms(ctx),
            "d1_health_facts": d1_health_facts,
            **rules,
        },
        "astrology_checks": _astrology_checks(ctx),
        "planet_evidence": evidence,
        "conflict_resolution": _conflict_resolution(ctx),
        "scorecard": _scorecard(ctx),
        "engine_verdict": {
            "verdict": rules.get("verdict"),
            "level": rules.get("verdict_level"),
            "confidence": conf_display,
            "strongest": verdict_extras.get("strongest") or [],
            "weakest": verdict_extras.get("weakest") or [],
            "timing": verdict_extras.get("timing"),
            "warnings": verdict_extras.get("warnings") or [],
        },
        "narrator_input": narrator_input,
        "narrator_output": (answer_text or "").strip() or None,
        "hallucination_checks": hallucination_rows,
        "hallucination_summary": _hallucination_summary(
            answer_text, ctx, hallucination_rows, evidence
        ),
        "performance": _performance_section(ctx, row_meta),
        "final_trace": _structured_final_trace(ctx, question_text, answer_text, routing),
        "final_trace_labels": trace_labels,
        "has_v2_rules": bool(rules.get("fired")),
        "has_step_audit": bool(_step_audit(ctx) or _astrology_checks(ctx).get("d1")),
    }


def attach_observability_to_context(
    ctx: dict[str, Any],
    *,
    question_text: str = "",
    answer_text: str = "",
    row_meta: dict[str, Any] | None = None,
    kundli: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = dict(ctx)
    prepared = _prepare_ctx_for_observability(out, question_text, kundli=kundli)
    if prepared.get("question_dna"):
        out["question_dna"] = prepared["question_dna"]
    if isinstance(prepared.get("llm_intent"), dict):
        out["llm_intent"] = prepared["llm_intent"]
    if prepared.get("question_normalized"):
        out["question_normalized"] = prepared["question_normalized"]
    if isinstance(prepared.get("checks"), dict):
        out["checks"] = prepared["checks"]
    if isinstance(prepared.get("slice_meta"), dict):
        out["slice_meta"] = prepared["slice_meta"]
    out["observability"] = build_observability_debug(
        prepared,
        question_text=question_text,
        answer_text=answer_text,
        row_meta=row_meta,
        kundli=kundli,
    )
    return out


OBS_DEBUGGER_VERSION = "2.6.1"


def _format_pipeline_section(title: str, steps: list[dict[str, Any]] | None) -> list[str]:
    lines = [f"=== {title} ==="]
    for step in steps or []:
        label = str(step.get("label") or "").strip()
        value = str(step.get("value") or "—").strip()
        if label:
            lines.append(f"{label}: {value}")
    lines.append("")
    return lines


def build_ask_debug_export_text(row: dict[str, Any]) -> str:
    """Plain-text debugger export — parity with admin Ask Q&A Copy All."""
    llm_ctx = row.get("llm_context") if isinstance(row.get("llm_context"), dict) else {}
    obs = llm_ctx.get("observability") if isinstance(llm_ctx.get("observability"), dict) else {}
    if not obs:
        obs = row.get("observability") if isinstance(row.get("observability"), dict) else {}
    exec_block = obs.get("engine_execution") if isinstance(obs.get("engine_execution"), dict) else {}
    health = obs.get("engine_health") if isinstance(obs.get("engine_health"), dict) else {}
    evidence = obs.get("planet_evidence") if isinstance(obs.get("planet_evidence"), dict) else {}
    conflict = obs.get("conflict_resolution") if isinstance(obs.get("conflict_resolution"), dict) else {}
    scorecard = obs.get("scorecard") if isinstance(obs.get("scorecard"), dict) else {}
    perf = obs.get("performance") if isinstance(obs.get("performance"), dict) else {}

    user_label = row.get("user_name") or row.get("user_email") or f"user #{row.get('user_id')}"
    lines: list[str] = [
        "=== Cosmic Lens · Ask Q&A Debug Export ===",
        f"Debugger: v{OBS_DEBUGGER_VERSION}",
        f"Question ID: {row.get('id') or '—'}",
        f"User: {user_label}",
        f"Email: {row.get('user_email') or '—'}",
        f"Date: {row.get('created_at') or '—'}",
        f"Topic: {row.get('topic') or '—'}",
        f"Engine tag: {row.get('engine_tag') or '—'}",
        f"Answer source: {row.get('answer_source') or '—'}",
        f"Verdict summary: {row.get('verdict_summary') or '—'}",
        "",
        "=== QUESTION ===",
        str(row.get("question_text") or "—"),
        "",
        "=== FINAL ANSWER (user saw) ===",
        str(row.get("answer_text") or "No answer saved."),
        "",
        "=== TELEMETRY ===",
        f"Model: {perf.get('model') or row.get('llm_model') or '—'}",
        f"Tokens: {int(perf.get('prompt_tokens') or row.get('prompt_tokens') or 0)} in · "
        f"{int(perf.get('completion_tokens') or row.get('completion_tokens') or 0)} out",
        "",
    ]

    routing_warning = obs.get("routing_warning")
    if routing_warning:
        lines.extend(["=== ROUTING WARNING ===", str(routing_warning), ""])

    lines.extend(_format_pipeline_section("1. QUESTION DNA", obs.get("question_dna_pipeline")))
    lines.extend([
        "=== 2. ENGINE HEALTH ===",
        f"Modules loaded: {health.get('modules_loaded') or '—'}",
        f"Rules evaluated: {health.get('rules_evaluated') if health.get('rules_evaluated') is not None else '—'}",
        f"Rules fired: {health.get('rules_fired') if health.get('rules_fired') is not None else '—'}",
        f"Rules skipped: {health.get('rules_skipped') if health.get('rules_skipped') is not None else '—'}",
        f"Confidence: {health.get('confidence_pct') if health.get('confidence_pct') is not None else '—'}%",
        f"Execution: {health.get('execution_ms') if health.get('execution_ms') is not None else '—'}ms",
        "",
        "=== 3. ENGINE EXECUTION ===",
        f"Engine: {exec_block.get('engine_name') or '—'}",
        f"Final score: {exec_block.get('final_score') if exec_block.get('final_score') is not None else '—'}",
        f"Verdict: {exec_block.get('verdict') or exec_block.get('verdict_level') or '—'}",
        "",
        "Modules:",
    ])
    for mod in exec_block.get("modules") or []:
        if isinstance(mod, dict):
            mark = "✅" if mod.get("loaded") else "❌"
            lines.append(f"  {mark} {mod.get('module') or '?'}")
    lines.extend(["", "Rules fired:"])
    fired = exec_block.get("fired") or []
    if not fired:
        lines.append("  —")
    else:
        for rule in fired:
            if isinstance(rule, dict):
                mark = "❌" if str(rule.get("polarity") or "").lower() == "negative" else "✅"
                lines.append(
                    f"  {rule.get('rule_id') or '?'} {mark} "
                    f"{rule.get('note') or rule.get('module') or ''}"
                )
    lines.append("")
    lines.append("=== 4. RULE DECISION TABLE ===")
    decisions = obs.get("rule_decisions") or []
    if not decisions:
        lines.append("—")
    else:
        for dec in decisions:
            if isinstance(dec, dict):
                lines.append(
                    f"{dec.get('rule_id') or '?'} | {dec.get('status') or '?'} | "
                    f"{dec.get('weight') if dec.get('weight') is not None else 0} | "
                    f"{dec.get('reason') or '—'}"
                )
    lines.append("")
    lines.extend(["=== 5. PLANET EVIDENCE ===", "Positive:"])
    pos = evidence.get("positive") or []
    if not pos:
        lines.append("  —")
    else:
        for item in pos:
            if isinstance(item, dict):
                lines.append(f"  • {item.get('label') or '?'}")
    lines.append("Negative:")
    neg = evidence.get("negative") or []
    if not neg:
        lines.append("  —")
    for item in neg:
        if isinstance(item, dict):
            lines.append(f"  • {item.get('label') or '?'}")
    lines.extend([
        "",
        "=== 6. CONFLICT RESOLUTION ===",
        f"Conflict: {conflict.get('conflict') or conflict.get('final_result') or 'None'}",
        f"Reason: {conflict.get('reason') or '—'}",
        "",
        "=== 7. SCORECARD ===",
    ])
    if scorecard:
        for key, val in scorecard.items():
            lines.append(f"  {key}: {val}")
    else:
        lines.append("—")
    lines.append("")
    lines.append("=== 8. NARRATOR INPUT (JSON) ===")
    narrator_input = obs.get("narrator_input")
    if narrator_input:
        try:
            import json
            lines.append(json.dumps(narrator_input, ensure_ascii=False, indent=2)[:12000])
        except Exception:
            lines.append(str(narrator_input)[:8000])
    else:
        lines.append("—")
    lines.append("")
    lines.extend([
        "=== 9. NARRATOR OUTPUT ===",
        str(obs.get("narrator_output") or row.get("answer_text") or "—"),
        "",
        "=== 10. HALLUCINATION CHECK ===",
    ])
    hall = obs.get("hallucination_summary") if isinstance(obs.get("hallucination_summary"), dict) else {}
    for key, label in (
        ("engine_facts_used", "Engine facts used"),
        ("unused_engine_evidence", "Unused engine evidence"),
        ("extra_llm_assumptions", "Extra LLM assumptions"),
    ):
        block = hall.get(key) if isinstance(hall.get(key), dict) else {}
        ok = block.get("ok")
        detail = block.get("detail") or block.get("items")
        lines.append(f"{label}: {'OK' if ok else 'CHECK'} — {detail or '—'}")
    lines.append("")
    lines.append("=== 11. FINAL TRACE ===")
    for step in obs.get("final_trace") or []:
        if isinstance(step, dict):
            lines.append(f"{step.get('label') or '?'}: {step.get('value') or '—'}")
    return "\n".join(lines).strip() + "\n"
