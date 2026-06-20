"""Batch-test MR engine routing + evidence for a question list."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ask_mr.classifier import classify_mr_archetype
from ask_mr import run_mr_static_engine

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
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
    "divisionalCharts": {
        "D9": {
            "ascendant": "Libra",
            "planets": [
                {"name": "Moon", "sign": "Capricorn", "house": 4},
                {"name": "Venus", "sign": "Aquarius", "house": 5},
                {"name": "Mars", "sign": "Aries", "house": 7},
                {"name": "Mercury", "sign": "Scorpio", "house": 2},
                {"name": "Jupiter", "sign": "Cancer", "house": 10},
            ],
        }
    },
}

IDEAL = {
    1: "partner_nature",
    2: "emotional_attachment",
    3: "loyalty_trust",
    4: "love_vs_arranged",
    5: "spouse_profession",
    6: "partner_nature",
    7: "partner_nature",
    8: "general_mr",
    9: "general_mr",
    10: "partner_nature",
    11: "general_mr",
    12: "partner_nature",
    13: "partner_nature",
    14: "loyalty_trust",
    15: "partner_nature",
    16: "general_mr",
    17: "partner_nature",
    18: "general_mr",
    19: "partner_nature",
    20: "general_mr",
}

QUESTIONS = [
    "Mera life partner ka nature aur personality kaisa hoga?",
    "Partner emotionally expressive hoga ya reserved?",
    "Marriage mein loyalty aur commitment level kaisa rahega?",
    "Love marriage ke yog zyada hain ya arranged marriage ke?",
    "Partner ka profession ya work field kis type ka ho sakta hai?",
    "Partner ki family background kaisi ho sakti hai?",
    "Physical appearance aur overall personality kaisi ho sakti hai?",
    "Marriage ke baad relationship ki strengths kya hongi?",
    "Relationship mein major challenges ya conflicts kis wajah se aa sakte hain?",
    "Partner spiritual, practical, ambitious ya artistic nature ka hoga?",
    "Marriage ke baad emotional compatibility kaisi rahegi?",
    "Partner dominant hoga ya cooperative?",
    "Partner ke love language (care dikhane ka tareeka) kya ho sakta hai?",
    "Relationship mein trust aur communication ka level kaisa rahega?",
    "Partner ke andar kaunsi qualities mujhe sabse zyada attract karengi?",
    "Marriage se meri life mein kya positive changes aa sakte hain?",
    "Kya partner different culture, city ya background se ho sakta hai?",
    "Relationship mein kis cheez par mujhe sabse zyada kaam karna chahiye?",
    "Ideal spouse ki qualities meri kundli ke hisab se kya hain?",
    "Marriage partner meri career aur life goals ko support karega ya nahi?",
]


def main() -> int:
    results = []
    ok = warn = fail = 0

    for i, q in enumerate(QUESTIONS, 1):
        arch = classify_mr_archetype(q)
        try:
            res = run_mr_static_engine(SAMPLE_KUNDLI, q, wants_explain=False)
        except Exception as exc:
            results.append(
                {
                    "id": i,
                    "question": q,
                    "archetype": arch,
                    "status": "FAIL",
                    "error": str(exc),
                }
            )
            fail += 1
            continue

        ev_n = len(res.evidence or [])
        ideal = IDEAL.get(i)
        if arch != res.archetype:
            status = "FAIL"
            fail += 1
        elif ideal and arch != ideal:
            status = "WARN"
            warn += 1
        elif ev_n == 0:
            status = "WARN"
            warn += 1
        else:
            status = "OK"
            ok += 1

        results.append(
            {
                "id": i,
                "question": q,
                "ideal_archetype": ideal,
                "archetype": res.archetype,
                "status": status,
                "verdict": res.verdict,
                "evidence_count": ev_n,
                "evidence": res.evidence or [],
                "checks": res.checks or {},
                "skip_llm": bool(res.skip_llm),
                "word_budget": res.word_budget,
            }
        )

    out_path = ROOT / "scripts" / "batch_mr_questions_results.json"
    out_path.write_text(json.dumps({"summary": {"ok": ok, "warn": warn, "fail": fail}, "results": results}, indent=2), encoding="utf-8")

    print(f"OK={ok} WARN={warn} FAIL={fail} -> {out_path}")
    for r in results:
        flag = r["status"]
        arch = r.get("archetype", "?")
        ev = r.get("evidence_count", 0)
        ideal = r.get("ideal_archetype", "")
        note = "" if arch == ideal or not ideal else f" (wanted {ideal})"
        print(f"{r['id']:2} {flag:4} {arch:18} ev={ev}{note}")

    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
