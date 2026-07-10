#!/usr/bin/env python3
"""FAST ASK AUDIT — 15 relationship promise/yog questions (no timing)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "artifacts" / "api-server"
sys.path.insert(0, str(API))

from ask_mr.classifier import classify_mr_archetype  # noqa: E402
from ask_mr import run_mr_static_engine  # noqa: E402
from ask_mr.timing_registry import has_explicit_timing_anchor  # noqa: E402
from ask_engine_resolver import resolve_static_engine_route  # noqa: E402
from ask_marriage_relationship_slice import is_marriage_relationship_static_question  # noqa: E402
from ask_health.health_registry import is_health_static_question  # noqa: E402

QUESTIONS = [
    "Kya meri life me serious relationship ka yog hai?",
    "Kya mujhe life me true love milega?",
    "Kya meri kundli me relationship ka strong promise hai?",
    "Kya meri life me romantic relationship banega?",
    "Kya meri life me long-term relationship ka yog hai?",
    "Kya main committed relationship ke liye bana/bani hoon?",
    "Kya meri life me multiple relationships honge ya ek hi serious relationship?",
    "Kya meri kundli stable relationship support karti hai?",
    "Kya meri love life successful rahegi?",
    "Kya mujhe genuine life partner milne ka yog hai?",
    "Kya meri kundli me healthy relationship ka indication hai?",
    "Kya meri kundli me relationship se zyada single rehne ka yog hai?",
    "Kya meri life me meaningful emotional connection banega?",
    "Kya meri kundli lifelong companionship support karti hai?",
    "Kya meri kundli me relationship ka promise weak hai ya strong?",
]

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "moonSign": "Gemini",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
}

MR_ARCHETYPES = {
    "partner_nature", "loyalty_trust", "general_mr", "one_sided_love", "chemistry",
    "emotional_attachment", "dating_courtship", "breakup_risk", "patchup",
    "long_distance", "secret_relationship", "karmic_marriage", "family_approval",
    "obsession", "self_worth", "bed_intimacy", "lifestyle_marriage", "open_chart_qa",
}


def audit_one(question: str) -> dict:
    issues: list[str] = []
    ok: list[str] = []
    archetype = classify_mr_archetype(question)
    is_mr_q = is_marriage_relationship_static_question(question)
    health_flag = is_health_static_question(question)
    timing = has_explicit_timing_anchor(question)

    if timing:
        issues.append("TIMING_ANCHOR — kab/when route risk (should be static promise)")
    else:
        ok.append("no_timing_anchor")

    flags = {"health": bool(health_flag), "mr": bool(is_mr_q)}
    for domain in ("general", "health"):
        _, route, _ = _resolve(question, flags=flags, domain=domain)
        if domain == "health" and route.engine_key == "health" and is_mr_q:
            issues.append("ROUTING_FAIL health_engine_steal")
        elif route.engine_key == "mr":
            ok.append(f"resolver_{domain}=mr")
        elif is_mr_q and route.engine_key != "mr":
            issues.append(f"ROUTING_FAIL domain={domain} winner={route.engine_key}")

    engine_res = run_mr_static_engine(SAMPLE_KUNDLI, question, wants_explain=False)
    evidence = [str(x) for x in (engine_res.evidence or []) if x]

    if archetype in MR_ARCHETYPES:
        ok.append(f"archetype={archetype}")
    else:
        issues.append(f"UNEXPECTED_ARCHETYPE={archetype}")

    if health_flag and is_mr_q:
        issues.append("HEALTH_FLAG_ON")
    elif not health_flag:
        ok.append("health_blocked")

    if evidence:
        ok.append(f"evidence_lines={len(evidence)}")
    else:
        issues.append("NO_EVIDENCE")

    if engine_res.archetype != archetype and not (
        archetype == "general_mr" and engine_res.archetype == "open_chart_qa"
    ):
        issues.append(f"ARCH_MISMATCH classifier={archetype} engine={engine_res.archetype}")

    return {
        "question": question,
        "archetype": archetype,
        "engine_archetype": engine_res.archetype,
        "evidence_count": len(evidence),
        "verdict": str(engine_res.verdict or "")[:160],
        "issues": issues,
        "pass": not issues,
        "verdict_label": "SAHI" if not issues else "GALAT",
    }


def _resolve(question: str, *, flags: dict, domain: str):
    intent = {"domain": domain, "routed_domain": domain}
    final, route = resolve_static_engine_route(
        question, flags=flags, llm_intent=intent, llm_intent_admin=intent, is_timing=False
    )
    active = [k for k, v in final.items() if v]
    return final, route, active


def main() -> int:
    results = [audit_one(q) for q in QUESTIONS]
    out = ROOT / "scripts" / "ask_audit_relationship_promise_15.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = sum(1 for r in results if r["pass"])
    print(f"FAST ASK AUDIT (promise/yog): {passed}/{len(results)} PASS\n")
    for i, r in enumerate(results, 1):
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"[{i:02d}] {mark} | {r['archetype']:20} | ev={r['evidence_count']:2} | {r['question'][:58]}")
        if r["issues"]:
            print(f"      -> {r['issues']}")
    print(f"\nWrote {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
