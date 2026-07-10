#!/usr/bin/env python3
"""FAST ASK AUDIT — 15 relationship questions (local routing + MR engine)."""
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
from ask_intent_fidelity import is_partner_relationship_question  # noqa: E402
from ask_health.health_registry import is_health_static_question  # noqa: E402

QUESTIONS = [
    "Kya ye relationship mere liye sahi hai?",
    "Kya hume breakup kar dena chahiye ya relationship bach sakti hai?",
    "Kya partner ka koi affair ya third person hai?",
    "Kya partner toxic ya manipulative hai?",
    "Kya partner commitment karega?",
    "Kya partner ka nature kaisa hai?",
    "Kya partner family-oriented hai?",
    "Kya long-distance relationship successful rahegi?",
    "Kya ex wapas aa sakta hai?",
    "Kya hum emotionally compatible hain?",
    "Kya trust issues khatam honge?",
    "Kya relationship me red flags hain?",
    "Kya partner honest hai?",
    "Kya hum marriage ke liye compatible hain?",
    "Kya ye karmic relationship hai ya soulmate connection?",
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
    "obsession", "self_worth",
}


def audit_one(question: str) -> dict:
    issues: list[str] = []
    ok: list[str] = []
    archetype = classify_mr_archetype(question)
    is_mr_q = is_marriage_relationship_static_question(question)
    partner_rel = is_partner_relationship_question(question)
    health_flag = is_health_static_question(question)

    flags = {"health": bool(health_flag), "mr": bool(is_mr_q)}
    for domain in ("general", "health", "love"):
        final, route, _ = _resolve(question, flags=flags, domain=domain)
        winner = route.engine_key
        if domain == "health" and winner == "health" and is_mr_q:
            issues.append(f"ROUTING_FAIL domain={domain} winner=health (should be mr)")
        elif winner == "mr":
            ok.append(f"resolver_{domain}=mr")
        elif winner is None and is_mr_q:
            issues.append(f"ROUTING_FAIL domain={domain} no_engine")
        elif domain == "love" and winner != "mr" and is_mr_q:
            issues.append(f"ROUTING_FAIL domain=love winner={winner}")

    engine_res = run_mr_static_engine(SAMPLE_KUNDLI, question, wants_explain=False)
    evidence = [str(x) for x in (engine_res.evidence or []) if x]

    if archetype in MR_ARCHETYPES:
        ok.append(f"archetype={archetype}")
    else:
        issues.append(f"UNEXPECTED_ARCHETYPE={archetype}")

    if health_flag and is_mr_q:
        issues.append("HEALTH_FLAG_ON — health steal risk")
    elif not health_flag:
        ok.append("health_blocked")

    if evidence:
        ok.append(f"evidence_lines={len(evidence)}")
    else:
        issues.append("NO_EVIDENCE")

    if engine_res.archetype == archetype:
        ok.append("engine_archetype_match")
    else:
        issues.append(f"ARCH_MISMATCH classifier={archetype} engine={engine_res.archetype}")

    return {
        "question": question,
        "archetype": archetype,
        "engine_archetype": engine_res.archetype,
        "is_mr_static": is_mr_q,
        "partner_rel": partner_rel,
        "health_static": health_flag,
        "verdict": str(engine_res.verdict or "")[:200],
        "evidence_sample": evidence[:3],
        "evidence_count": len(evidence),
        "ok": ok,
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
    out = ROOT / "scripts" / "ask_audit_relationship_15.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = sum(1 for r in results if r["pass"])
    print(f"FAST ASK AUDIT: {passed}/{len(results)} PASS\n")
    for i, r in enumerate(results, 1):
        status = "PASS" if r["pass"] else "FAIL"
        print(f"[{i:02d}] {status} | {r['verdict_label']} | arch={r['archetype']} | ev={r['evidence_count']}")
        print(f"     Q: {r['question']}")
        if r["issues"]:
            print(f"     ISSUES: {r['issues']}")
        print()
    print(f"Wrote {out}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
