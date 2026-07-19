"""Unified LLM payload + selected blocks + DNA judge + attach helper."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from ask_mr.types import EngineResult
from ask_unified.facts import compute_domain_engine_execution
from ask_unified.specs import DomainSpec, get_domain_spec, slice_to_domain

_JUDGE_JSON_RX = re.compile(r"\{[\s\S]*\}")
_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


def attach_domain_engine_execution(
    result: EngineResult,
    kundli: dict,
    *,
    domain: str,
    question: str = "",
    llm_intent: dict | None = None,
) -> EngineResult:
    spec = get_domain_spec(domain)
    if not spec:
        return result
    try:
        pack = compute_domain_engine_execution(
            kundli if isinstance(kundli, dict) else {},
            domain=domain,
            question=question or "",
            routing_label=result.archetype or "",
            llm_intent=llm_intent,
        )
        checks = dict(result.checks or {})
        key = f"{domain}_engine_execution"
        checks[key] = pack
        checks[f"d1_{domain}_facts"] = pack.get("d1") or {}
        checks[f"d9_{domain}_facts"] = pack.get("d9") or {}
        checks[f"{domain}_divisional_facts"] = pack.get("divisional_chart") or {}
        checks["charts_used"] = pack.get("charts_used") or ["D1", "D9"]
        checks["engine_version"] = spec.schema_version
        checks["unified_execution"] = True
        checks["routing_label"] = result.archetype
        checks["unified_domain"] = domain
        if pack.get("composite_score") is not None:
            checks[f"{domain}_score"] = pack.get("composite_score")
        result.checks = checks
    except Exception as exc:
        checks = dict(result.checks or {})
        checks[f"{domain}_engine_execution_error"] = str(exc)[:180]
        result.checks = checks
    return result


def build_unified_engine_result(
    *,
    domain: str,
    kundli: dict,
    question: str,
    archetype: str | None = None,
    wants_explain: bool = False,
    llm_intent: dict | None = None,
) -> EngineResult:
    spec = get_domain_spec(domain)
    if not spec:
        raise ValueError(f"unknown unified domain: {domain}")
    label = (archetype or "").strip().lower() or spec.default_archetype
    dims_hint = ""
    try:
        from ask_unified.facts import compute_domain_facts

        facts = compute_domain_facts(kundli if isinstance(kundli, dict) else {}, spec)
        bits = []
        for k, row in (facts.get("dimensions") or {}).items():
            if isinstance(row, dict) and row.get("verdict"):
                bits.append(f"{k}={row.get('verdict')}")
        dims_hint = "; ".join(bits)
        if facts.get("strength_label"):
            dims_hint = (dims_hint + " | " if dims_hint else "") + str(facts["strength_label"])
    except Exception:
        pass

    result = EngineResult(
        archetype=label,
        verdict=dims_hint or "",
        confidence="medium",
        word_budget=95 if wants_explain else 75,
        answer_plan=(
            f"Read {spec.json_label} (D1 + D9). "
            f"routing_label={label} is answer focus only — answer the user's exact "
            f"{spec.topic_label} question using pack facts. Avoid: {spec.banned}."
        ),
        summary=[
            f"Unified {spec.key} pack: D1 + D9 focus houses {spec.focus_houses}.",
            f"Routing label (focus): {label}",
        ],
        evidence=[],
        ignore=list(spec.banned.split(", ")),
        checks={
            "slice_type": spec.slice,
            "archetype": label,
            "routing_label": label,
            "unified_execution": True,
            "unified_domain": domain,
        },
    )
    return attach_domain_engine_execution(
        result, kundli, domain=domain, question=question or "", llm_intent=llm_intent,
    )


def domain_engine_slice_meta(result: EngineResult, *, domain: str) -> dict[str, Any]:
    spec = get_domain_spec(domain)
    pos, neg, neu = result._finalize_evidence_split()
    checks = dict(result.checks or {})
    return {
        "slice": (spec.slice if spec else f"{domain}_engine_v1"),
        "topic": domain,
        "archetype": result.archetype,
        "verdict": result.verdict,
        "confidence": result.confidence,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "evidence_positive": pos,
        "evidence_negative": neg,
        "evidence_neutral": neu,
        "ignore": list(result.ignore or []),
        "checks": checks,
        "skip_llm": bool(result.skip_llm),
        "word_budget": int(result.word_budget or 75),
        "narrator_mode": "engine_facts_only",
    }


def to_domain_llm_payload(
    result: EngineResult,
    *,
    domain: str | None = None,
    question: str = "",
) -> str:
    checks = dict(result.checks or {})
    domain = (domain or checks.get("unified_domain") or "").strip().lower()
    if not domain:
        # infer from checks keys
        for k, v in checks.items():
            if k.endswith("_engine_execution") and isinstance(v, dict):
                domain = k.replace("_engine_execution", "")
                break
    spec = get_domain_spec(domain) if domain else None
    if not spec:
        return result.to_narrator_payload()

    execution = checks.get(f"{domain}_engine_execution") or {}
    label = (
        str(checks.get("routing_label") or result.archetype or "").strip().lower()
        or str(execution.get("routing_label") or "").strip().lower()
    )
    payload = {
        "question": (question or "").strip(),
        "routing_label": label,
        "domain": domain,
        "schema_version": execution.get("schema_version") or spec.schema_version,
        "d1": execution.get("d1") or checks.get(f"d1_{domain}_facts") or {},
        "d9": execution.get("d9") or checks.get(f"d9_{domain}_facts") or {},
        "divisional_chart_tag": execution.get("divisional_chart_tag"),
        "divisional_chart": (
            execution.get("divisional_chart")
            or checks.get(f"{domain}_divisional_facts")
            or {}
        ),
        "charts_used": execution.get("charts_used") or checks.get("charts_used") or ["D1", "D9"],
        "lagnesh": execution.get("lagnesh") or {},
        "vargottama_planets": execution.get("vargottama_planets") or [],
        "dimensions": execution.get("dimensions") or {},
        "afflictions": execution.get("afflictions") or [],
        "sub_flags": execution.get("sub_flags") or {},
        "composite_score": execution.get("composite_score"),
        "strength_label": execution.get("strength_label"),
    }
    parts = [
        spec.json_label + ":\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
    ]
    try:
        selected = build_domain_selected_blocks(
            question or "", "", meta={"checks": checks, "routing_label": label},
            domain=domain, execution=execution if isinstance(execution, dict) else None,
        )
        priority = str(selected.get("priority_facts_for_llm") or "").strip()
        if priority:
            parts.append(priority)
            checks[f"{domain}_selected_blocks_preview"] = {
                "applies": True,
                "focus": selected.get("focus"),
                "focus_label": selected.get("focus_label"),
                "expected_blocks": (selected.get("expected_blocks") or [])[:8],
                "available_blocks": (selected.get("expected_blocks") or [])[:8],
                "priority_facts_for_llm": priority,
                "source": f"{domain}_engine_execution",
                "domain": domain,
            }
            result.checks = checks
    except Exception:
        pass

    parts.append(
        f"NARRATOR_LOCK: Use ONLY {spec.json_label} for chart facts. "
        f"routing_label={label} = answer focus — not a separate engine. "
        "Cite #1 from QUESTION_PRIORITY_FACTS as natural chart proof. "
        f"Do not invent placements. Avoid: {spec.banned}."
    )
    if result.verdict:
        parts.append(f"VERDICT_HINT: {result.verdict}")
    if result.answer_plan:
        parts.append(f"ANSWER_PLAN: {result.answer_plan}")
    return "\n\n".join(parts)


def build_domain_selected_blocks(
    question: str,
    answer: str = "",
    *,
    domain: str,
    meta: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = get_domain_spec(domain)
    meta = meta if isinstance(meta, dict) else {}
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = execution if isinstance(execution, dict) else checks.get(f"{domain}_engine_execution")
    if not isinstance(pack, dict):
        pack = {}
    focus = str(
        meta.get("routing_label") or meta.get("archetype")
        or checks.get("routing_label") or pack.get("routing_label")
        or (spec.default_archetype if spec else domain)
    ).strip().lower()
    d1 = pack.get("d1") if isinstance(pack.get("d1"), dict) else {}
    div = (
        pack.get("divisional_chart")
        if isinstance(pack.get("divisional_chart"), dict)
        else {}
    )
    div_tag = str(pack.get("divisional_chart_tag") or "").strip().upper()
    lords = d1.get("house_lords") or {}
    karakas = d1.get("karakas") or {}
    dims = pack.get("dimensions") or d1.get("dimensions") or {}
    afflictions = pack.get("afflictions") or d1.get("afflictions") or []

    blocks: list[dict[str, Any]] = []

    def add(bid: str, blabel: str, detail: str, *, priority: int, role: str) -> None:
        blocks.append({
            "id": bid, "label": blabel, "why": f"Focus={focus}",
            "detail": detail, "priority": priority, "role": role,
        })

    for dim_key, row in (dims.items() if isinstance(dims, dict) else []):
        if not isinstance(row, dict):
            continue
        verdict = str(row.get("verdict") or "")
        role = "weak" if verdict == "RED" else ("support" if verdict == "GREEN" else "neutral")
        pr = 90 if verdict == "RED" else (70 if verdict == "YELLOW" else 55)
        add(f"dim.{dim_key}", f"Dimension · {dim_key}",
            f"{verdict} — {row.get('reason') or ''}".strip(" —"), priority=pr, role=role)

    if div_tag and div_tag != "D9" and not div.get("error"):
        div_lords = div.get("house_lords") or {}
        primary_house = (spec.focus_houses[0] if spec else 1)
        div_lord = div_lords.get(f"h{primary_house}") if isinstance(div_lords, dict) else None
        if isinstance(div_lord, dict) and div_lord.get("lord"):
            add(
                f"{div_tag.lower()}.lord.h{primary_house}",
                f"{div_tag} confirmation · H{primary_house} lord",
                (
                    f"{div_lord.get('lord')} → H{div_lord.get('lord_house')} · "
                    f"{div_lord.get('lord_sign')} · {div_lord.get('lord_dignity')}"
                ),
                priority=85,
                role=(
                    "weak"
                    if div_lord.get("lord_in_dusthana")
                    else "support"
                    if div_lord.get("lord_dignity") in ("exalted", "own")
                    else "neutral"
                ),
            )

    houses = (spec.focus_houses if spec else (1, 10))[:4]
    for h in houses:
        st = lords.get(f"h{h}") if isinstance(lords, dict) else None
        if not isinstance(st, dict) or not st.get("lord"):
            continue
        dig = str(st.get("lord_dignity") or "")
        role = "weak" if dig in ("debilitated", "enemy") or st.get("lord_in_dusthana") else "neutral"
        if dig in ("exalted", "own"):
            role = "support"
        add(f"lord.h{h}", f"House lord · h{h}",
            f"{st.get('lord')} → H{st.get('lord_house')} · {st.get('lord_sign')} · {dig}",
            priority=80 if role == "weak" else 50, role=role)

    planets = (spec.focus_planets if spec else ("Jupiter", "Saturn"))[:4]
    for pname in planets:
        if pname == "Ascendant":
            continue
        k = karakas.get(pname) if isinstance(karakas, dict) else None
        if not isinstance(k, dict):
            continue
        dig = str(k.get("dignity") or "")
        role = "weak" if dig in ("debilitated", "enemy") else (
            "support" if dig in ("exalted", "own") else "neutral"
        )
        add(f"planet.{pname}", f"Planet · {pname}",
            f"{pname} · {k.get('sign')} · H{k.get('house')} · {dig}",
            priority=75 if role == "weak" else 48, role=role)

    for i, line in enumerate(list(afflictions)[:3]):
        add(f"affliction.{i}", "Affliction", str(line), priority=72, role="weak")

    if pack.get("strength_label") or pack.get("composite_score") is not None:
        add("pack.composite", "Theme strength",
            f"score={pack.get('composite_score')}/100 — {pack.get('strength_label') or ''}".strip(" —"),
            priority=40, role="neutral")

    _boost_applied: list[str] = []
    try:
        from ask_selected_blocks_common import dna_boost_selected_blocks

        blocks, _boost_applied = dna_boost_selected_blocks(
            question or "", blocks, meta=meta, pack=pack,
        )
    except Exception:
        blocks.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
        for i, b in enumerate(blocks, start=1):
            b["rank"] = i

    lines = [
        "QUESTION_PRIORITY_FACTS (from Engine Execution only — use in this order):",
        "Rules: #1 = main reason + MUST include its natural chart proof in the answer",
        "(planet + house/dignity). Max 2–3 facts total.",
    ]
    for b in blocks[:5]:
        hint = " ← CITE THIS as proof" if b.get("rank") == 1 else ""
        lines.append(
            f"#{b.get('rank')} [{b.get('role')}] {b.get('label')}: {b.get('detail')}{hint}"
        )
    priority_text = "\n".join(lines) if blocks else ""
    used = [n for n in _PLANET_NAMES if re.search(rf"(?i)\b{re.escape(n)}\b", answer or "")]
    audit = {
        "applies": True,
        "source": f"{domain}_engine_execution",
        "focus": focus,
        "focus_label": f"{domain} — {focus}",
        "expected_blocks": blocks,
        "available_blocks": blocks,
        "priority_facts_for_llm": priority_text,
        "used_in_answer": {"planets": used},
        "note": f"Question focus={focus}: priority facts for LLM.",
        "domain": domain,
    }
    try:
        from ask_selected_blocks_common import (
            coverage_check_selected_blocks,
            coverage_note_lines,
            dna_boost_note_lines,
            question_wants_everything,
        )

        if question_wants_everything(question or "", meta) and spec:
            # Widen limit already encoded in blocks; tag coverage notes.
            pass
        coverage = coverage_check_selected_blocks(
            question or "",
            meta=meta,
            audit=audit,
            execution=pack,
            general_focus=str(spec.default_archetype if spec else f"general_{domain}"),
        )
        audit["coverage"] = coverage
        audit["overlap_notes"] = (
            coverage_note_lines(coverage) + dna_boost_note_lines(_boost_applied)
        )
    except Exception:
        pass
    return audit


_GAP_DNA_JUDGE_OFF_BY_DEFAULT = frozenset({
    "spiritual", "siblings", "parents", "enemies", "fame", "personality",
    "dreams", "anger", "remedy", "charity", "settlement", "vastu", "pets",
    "wellness", "luck", "network",
})


def build_domain_dna_judge_display(
    question: str,
    answer: str,
    meta: dict[str, Any],
    *,
    domain: str,
    stored_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Debugger display for unified/gap DNA judge (observability; never blocks answer)."""
    from ask_health.answer_validator import _enrich_dna_contract, _resolve_dna_contract

    audit = stored_audit if isinstance(stored_audit, dict) else {}
    contract = _resolve_dna_contract(meta)
    if not contract and question:
        contract = _enrich_dna_contract(dict(meta), question)
    judge_audit = audit.get("dna_judge") if isinstance(audit.get("dna_judge"), dict) else {}
    if not judge_audit and audit.get("judge"):
        judge_audit = audit

    fix_hint = str(audit.get("fix_hint") or "").strip()
    if not fix_hint:
        fix_hint = str((judge_audit.get("parsed") or {}).get("fix_hint") or "").strip()

    passed = judge_audit.get("passed")
    if passed is None:
        passed = audit.get("passed")
    enabled = judge_audit.get(
        "enabled", audit.get("enabled", domain_dna_judge_enabled(domain))
    )
    issues = list(audit.get("issues") or judge_audit.get("issues") or [])
    contract_summary = {
        k: contract.get(k)
        for k in (
            "normalized_question", "intent", "user_wants", "question_type",
            "domain", "bucket", "answer_style", "answer_approach",
        )
        if contract.get(k)
    } if isinstance(contract, dict) else {}

    return {
        "applies": True,
        "enabled": bool(enabled),
        "passed": passed if passed is not None else (None if not enabled else True),
        "issues": issues,
        "fix_hint": fix_hint,
        "contract": contract_summary or audit.get("contract") or {},
        "judge_version": judge_audit.get("judge") or f"{domain}_dna_v1",
        "contract_keys": list((audit.get("contract") or contract_summary or {}).keys()),
        "skipped": judge_audit.get("skipped"),
        "error": judge_audit.get("error"),
        "domain": domain,
        "mode": "observability_display",
        "note": (
            "Observability only — answer is never blocked by DNA Judge. "
            f"Source: {'stored' if stored_audit else 'recomputed'}"
        ),
    }


# domain_dna_judge_enabled defined below (used at call-time by display builder).


def domain_dna_judge_enabled(domain: str) -> bool:
    """Phase 1: DNA judge OFF by default (no post-narrator rewrite/retry).

    Opt-in only: ASK_UNIFIED_DNA_JUDGE=1 or ASK_<DOMAIN>_DNA_JUDGE=1.
    """
    d = (domain or "").strip().lower()
    env = f"ASK_{d.upper()}_DNA_JUDGE" if d else "ASK_UNIFIED_DNA_JUDGE"
    explicit = os.environ.get(env)
    if explicit is not None and str(explicit).strip() != "":
        return str(explicit).strip() != "0"
    unified = os.environ.get("ASK_UNIFIED_DNA_JUDGE")
    if unified is not None and str(unified).strip() != "":
        return str(unified).strip() != "0"
    return False


def dna_judge_retry_enabled() -> bool:
    """Second LLM rewrite after judge fail — default OFF (was a major latency source)."""
    return (os.environ.get("ASK_DNA_JUDGE_RETRY") or "0").strip().lower() in (
        "1",
        "on",
        "true",
        "yes",
    )


def _parse_judge_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        pass
    m = _JUDGE_JSON_RX.search(text)
    if not m:
        return {}
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def run_domain_llm_with_dna_judge(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    question: str,
    meta: dict[str, Any],
    domain: str | None = None,
) -> tuple[str, dict[str, Any]]:
    from ask_health.answer_validator import _enrich_dna_contract

    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    domain = (domain or checks.get("unified_domain") or slice_to_domain(str(meta.get("slice") or "")) or "").strip().lower()
    spec = get_domain_spec(domain) if domain else None
    topic = spec.topic_label if spec else (domain or "topic")

    audit: dict[str, Any] = {
        "mode": "dna_judge_only",
        "enabled": domain_dna_judge_enabled(domain or "unified"),
        "attempts": 1,
        "passed": True,
        "issues": [],
        "domain": domain,
    }

    resp = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens)
    text = (resp.choices[0].message.content or "").strip()

    contract = _enrich_dna_contract(meta, question)
    audit["contract"] = {
        k: contract[k]
        for k in (
            "normalized_question", "intent", "user_wants", "question_type",
            "domain", "bucket", "answer_style", "answer_approach",
        )
        if contract.get(k)
    }
    try:
        if domain:
            audit["selected_blocks"] = build_domain_selected_blocks(
                question, text, meta=meta, domain=domain,
            )
    except Exception as exc:
        audit["selected_blocks"] = {"applies": True, "error": str(exc)[:120]}

    if not domain or not domain_dna_judge_enabled(domain):
        audit["dna_judge"] = {"enabled": False, "skipped": "disabled"}
        return text, audit

    answer_mode = str(
        meta.get("answer_mode")
        or (meta.get("question_dna_item") or {}).get("answer_mode")
        or ""
    ).strip().lower()
    requires_chart_proof = answer_mode not in ("llm_knowledge", "knowledge")
    proof_rule = (
        "FAIL if a specific/personal answer has NO chart proof "
        "(planet/house/dignity; issue: missing_question_proof)."
        if requires_chart_proof
        else "This is a general knowledge answer; chart proof is NOT required."
    )

    def _judge_answer(candidate: str) -> dict[str, Any]:
        prompt = f"""You are a strict QA judge for Vedic {topic.upper()} answers.
Check whether CANDIDATE ANSWER matches Question DNA. Return ONLY JSON:
{{"passed": true/false, "issues": ["..."], "fix_hint": "..."}}

FAIL if answer misses user_wants/intent or answers a different question.
{proof_rule}

NORMALIZED: {contract.get('normalized_question') or question}
INTENT: {contract.get('intent') or '—'}
USER WANTS: {contract.get('user_wants') or '—'}
TYPE: {contract.get('question_type') or '—'}
ANSWER:
{(candidate or '')[:1800]}
"""
        jresp = client.chat.completions.create(
            model=(os.environ.get("ASK_UNIFIED_DNA_JUDGE_MODEL") or "gpt-4.1-mini").strip(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=220,
        )
        return _parse_judge_json((jresp.choices[0].message.content or "").strip())

    try:
        parsed = _judge_answer(text)
        ok = bool(parsed.get("passed", True))
        issues = [str(x) for x in (parsed.get("issues") or []) if str(x).strip()]
        hint = str(parsed.get("fix_hint") or "").strip() or None
        audit["dna_judge"] = {
            "judge": f"{domain}_dna_v1", "enabled": True,
            "passed": ok, "issues": issues, "parsed": parsed,
        }
        audit["passed"] = ok
        audit["issues"] = issues
        if hint:
            audit["fix_hint"] = hint

        if not ok:
            if not dna_judge_retry_enabled():
                audit["dna_retry"] = False
                audit["dna_retry_skipped"] = "ASK_DNA_JUDGE_RETRY=off"
            else:
                retry = list(messages) + [
                    {"role": "assistant", "content": text},
                    {"role": "user", "content": (
                        "Rewrite the answer so it matches the exact Question DNA and fixes every "
                        f"judge issue: {', '.join(issues) or 'question mismatch'}. "
                        f"Fix hint: {hint or 'answer only what the user asked'}. "
                        + (
                            "Include 1 natural chart proof (planet + house/dignity)."
                            if requires_chart_proof
                            else "Do not invent personal chart facts."
                        )
                    )},
                ]
                try:
                    r2 = client.chat.completions.create(
                        model=model, messages=retry, max_tokens=max_tokens,
                    )
                    t2 = (r2.choices[0].message.content or "").strip()
                    if t2:
                        text = t2
                        audit["attempts"] = 2
                        audit["dna_retry"] = True
                        if domain:
                            audit["selected_blocks"] = build_domain_selected_blocks(
                                question, text, meta=meta, domain=domain,
                            )
                        parsed2 = _judge_answer(text)
                        ok2 = bool(parsed2.get("passed", False))
                        issues2 = [
                            str(x) for x in (parsed2.get("issues") or []) if str(x).strip()
                        ]
                        audit["passed"] = ok2
                        audit["issues"] = issues2
                        audit["dna_judge_retry"] = {
                            "judge": f"{domain}_dna_v1",
                            "enabled": True,
                            "passed": ok2,
                            "issues": issues2,
                            "parsed": parsed2,
                        }
                except Exception as exc:
                    audit["dna_retry_error"] = str(exc)[:120]
    except Exception as exc:
        audit["dna_judge"] = {
            "enabled": True, "passed": True, "error": str(exc)[:160], "soft_pass_on_error": True,
        }

    return text, audit


def maybe_upgrade_chart_text(
    result: EngineResult,
    chart_text: str,
    *,
    question: str = "",
) -> str:
    """If result has unified EE, replace narrator payload with domain JSON payload."""
    checks = dict(result.checks or {})
    if not checks.get("unified_execution"):
        return chart_text
    domain = str(checks.get("unified_domain") or "").strip().lower()
    if not domain:
        for k in checks:
            if k.endswith("_engine_execution") and isinstance(checks.get(k), dict):
                domain = k[: -len("_engine_execution")]
                break
    if not domain or not get_domain_spec(domain):
        return chart_text
    try:
        return to_domain_llm_payload(result, domain=domain, question=question)
    except Exception:
        return chart_text
