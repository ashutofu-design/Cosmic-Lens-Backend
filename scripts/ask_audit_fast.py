#!/usr/bin/env python3
"""FAST ASK AUDIT — local routing + MR engine evidence only (no LLM/API, ~seconds)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "artifacts" / "api-server"
sys.path.insert(0, str(API))

from ask_mr.classifier import classify_mr_archetype  # noqa: E402
from ask_mr import run_mr_static_engine  # noqa: E402

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

QUESTIONS = [
    "Kya mera partner sach me mujhse pyaar karta hai?",
    "Kya mera partner loyal aur faithful hai?",
    "Kya hum dono compatible hain?",
    "Relationship me problems kis wajah se aa rahi hain?",
]

MR_ARCHETYPES = {
    "partner_nature",
    "loyalty_trust",
    "general_mr",
    "one_sided_love",
    "chemistry",
    "emotional_attachment",
    "dating_courtship",
    "breakup_risk",
}


def _routing_flags(question: str) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    try:
        from ask_engine_verification import (  # noqa: E402
            apply_love_life_area_static_flags,
            apply_partner_relationship_static_flags,
        )
        from ask_marriage_relationship_slice import (  # noqa: E402
            is_marriage_relationship_static_question,
        )

        is_mr = is_marriage_relationship_static_question(question)
        is_health = False
        is_mr, is_health = apply_partner_relationship_static_flags(
            question, is_mr_static=is_mr, is_health_static=is_health
        )
        is_mr, is_health = apply_love_life_area_static_flags(
            question, is_mr_static=is_mr, is_health_static=is_health
        )
        flags["is_mr_static"] = bool(is_mr)
        flags["is_health_static"] = bool(is_health)
        flags["is_marriage_relationship"] = bool(
            is_marriage_relationship_static_question(question)
        )
    except Exception as exc:
        flags["routing_error"] = str(exc)
    return flags


def audit_one(question: str) -> dict:
    issues: list[str] = []
    ok: list[str] = []

    archetype = classify_mr_archetype(question)
    flags = _routing_flags(question)
    engine_res = run_mr_static_engine(SAMPLE_KUNDLI, question, wants_explain=False)
    evidence = [str(x) for x in (engine_res.evidence or []) if x]
    verdict = str(engine_res.verdict or "")

    expected_engine = "mr_engine_v1"
    if archetype in MR_ARCHETYPES:
        ok.append(f"archetype={archetype}")
    else:
        issues.append(f"UNEXPECTED_ARCHETYPE={archetype}")

    if flags.get("is_mr_static"):
        ok.append("routing=is_mr_static")
    else:
        issues.append("ROUTING_NOT_MR — health/other engine steal ho sakta hai")

    if flags.get("is_health_static"):
        issues.append("HEALTH_FLAG_ON — galat health_engine risk")

    if evidence:
        ok.append(f"evidence_lines={len(evidence)}")
    else:
        issues.append("NO_EVIDENCE — engine evidence empty")

    if engine_res.archetype == archetype:
        ok.append("engine_archetype_match")
    else:
        issues.append(
            f"ARCH_MISMATCH classifier={archetype} engine={engine_res.archetype}"
        )

    return {
        "question": question,
        "expected_engine": expected_engine,
        "archetype": archetype,
        "engine_archetype": engine_res.archetype,
        "routing_flags": flags,
        "verdict": verdict,
        "evidence_sample": evidence[:5],
        "evidence_count": len(evidence),
        "ok": ok,
        "issues": issues,
        "pass": not issues,
        "verdict_label": "SAHI" if not issues else "GALAT",
    }


def main() -> int:
    results = [audit_one(q) for q in QUESTIONS]
    out_json = ROOT / "scripts" / "ask_audit_fast_results.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    for i, r in enumerate(results, 1):
        print(f"\n{'='*60}\n[{i}/4] {r['question']}")
        print(f"VERDICT: {r['verdict_label']} | archetype={r['archetype']}")
        print(f"routing: {r['routing_flags']}")
        print(f"engine verdict: {r['verdict'][:120]}...")
        print("evidence:")
        for line in r["evidence_sample"]:
            print(f"  - {line[:140]}")
        if r["issues"]:
            print("issues:", r["issues"])
        else:
            print("ok:", r["ok"])

    print(f"\nWrote {out_json}")
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
