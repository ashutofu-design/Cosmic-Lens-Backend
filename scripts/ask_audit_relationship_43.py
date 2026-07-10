#!/usr/bin/env python3
"""FAST ASK AUDIT — 43 relationship questions (local routing + MR engine)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "artifacts" / "api-server"
sys.path.insert(0, str(API))

from ask_mr.classifier import classify_mr_archetype  # noqa: E402
from ask_mr import run_mr_static_engine  # noqa: E402
from ask_engine_resolver import resolve_static_engine_route  # noqa: E402
from ask_marriage_relationship_slice import is_marriage_relationship_static_question  # noqa: E402
from ask_health.health_registry import is_health_static_question  # noqa: E402

QUESTIONS = [
    "Kya meri current relationship tik paayegi?",
    "Kya ye relationship mere liye sahi hai?",
    "Kya mera partner mujhse sachcha pyaar karta hai?",
    "Kya mera partner loyal hai?",
    "Kya partner cheating karega ya kar raha hai?",
    "Kya partner ka kisi aur ke saath affair hai?",
    "Kya partner commitment karega?",
    "Kya partner emotionally mature hai?",
    "Kya partner possessive ya controlling hai?",
    "Kya partner toxic hai?",
    "Kya partner honest aur trustworthy hai?",
    "Kya hum dono compatible hain?",
    "Hamare relationship ki strengths aur weaknesses kya hain?",
    "Relationship me baar-baar fights kyun hoti hain?",
    "Sabse bada challenge kya rahega?",
    "Communication kaisa rahega?",
    "Trust issues rahenge?",
    "Intimacy aur emotional bonding kaisi rahegi?",
    "Long-distance relationship successful rahegi?",
    "Family interference hogi?",
    "Kya partner ki family accept karegi?",
    "Kya hum ek dusre ko samajh paayenge?",
    "Kya relationship marriage tak ja sakti hai?",
    "Kya breakup ke yog hain?",
    "Agar breakup ho gaya hai, reconciliation ki possibility hai?",
    "Kya ex ke saath dobara relationship ban sakta hai?",
    "Kya relationship karmic hai?",
    "Kya soulmate connection hai?",
    "Kya twin flame connection hai?",
    "Relationship me kis partner ko zyada compromise karna padega?",
    "Relationship me kis taraf se zyada effort rahega?",
    "Financial issues relationship ko affect karenge?",
    "Career relationship ko affect karega?",
    "Distance ya foreign settlement relationship ko affect karegi?",
    "Physical attraction strong rahega?",
    "Emotional compatibility kaisi rahegi?",
    "Sexual compatibility kaisi rahegi?",
    "Kya partner supportive hoga?",
    "Kya partner dominant rahega ya caring?",
    "Kya partner secretive nature ka hoga?",
    "Kya partner jealous nature ka hoga?",
    "Kya relationship healthy rahegi ya stressful?",
    "Relationship ko successful banane ke liye kin cheezon par kaam karna hoga?",
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
    "obsession", "self_worth", "bed_intimacy", "spouse_wealth", "lifestyle_marriage",
}


def audit_one(question: str) -> dict:
    issues: list[str] = []
    ok: list[str] = []
    archetype = classify_mr_archetype(question)
    is_mr_q = is_marriage_relationship_static_question(question)
    health_flag = is_health_static_question(question)

    flags = {"health": bool(health_flag), "mr": bool(is_mr_q)}
    for domain in ("general", "health"):
        final, route, _ = _resolve(question, flags=flags, domain=domain)
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
        "engine": "mr_engine_v1" if is_mr_q and not issues else route.engine_key if not is_mr_q else "mr_engine_v1",
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
    out = ROOT / "scripts" / "ask_audit_relationship_43.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = sum(1 for r in results if r["pass"])
    failed = [r for r in results if not r["pass"]]
    print(f"FAST ASK AUDIT: {passed}/{len(results)} PASS\n")
    for i, r in enumerate(results, 1):
        mark = "PASS" if r["pass"] else "FAIL"
        print(f"[{i:02d}] {mark} | {r['archetype']:20} | ev={r['evidence_count']:2} | {r['question'][:55]}")
        if r["issues"]:
            print(f"      -> {r['issues']}")
    if failed:
        print(f"\nFAILED ({len(failed)}):")
        for r in failed:
            print(f"  - {r['question']}")
            print(f"    {r['issues']}")
    print(f"\nWrote {out}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
