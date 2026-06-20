#!/usr/bin/env python3
"""MR Ask — test ONE question at a time (engine facts sent to LLM).

Usage:
  python scripts/mr_question_one_by_one.py              # all questions, one block each
  python scripts/mr_question_one_by_one.py --id 3       # single question by id
  python scripts/mr_question_one_by_one.py --from 10 --to 15
  python scripts/mr_question_one_by_one.py --out report.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ask_mr import run_mr_static_engine
from ask_mr.classifier import classify_mr_archetype


def _production_narrator_payload(res) -> str:
    """Match live API payload shape where specialized narrators exist."""
    arch = res.archetype
    if arch == "partner_nature":
        from ask_mr.engines.partner_nature import partner_nature_narrator_payload

        return partner_nature_narrator_payload(res)
    return res.to_narrator_payload()

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

QUESTIONS: list[tuple[int, str, str]] = [
    (1, "partner_nature", "Mera life partner ka nature aur personality kaisa hoga?"),
    (2, "partner_nature", "Partner emotionally expressive hoga ya reserved?"),
    (3, "loyalty_trust", "Marriage mein loyalty aur commitment level kaisa rahega?"),
    (4, "love_vs_arranged", "Love marriage ke yog zyada hain ya arranged marriage ke?"),
    (5, "spouse_profession", "Partner ka profession ya work field kis type ka ho sakta hai?"),
    (6, "partner_nature", "Partner ki family background kaisi ho sakti hai?"),
    (7, "partner_nature", "Physical appearance aur overall personality kaisi ho sakti hai?"),
    (8, "general_mr", "Marriage ke baad relationship ki strengths kya hongi?"),
    (9, "general_mr", "Relationship mein major challenges ya conflicts kis wajah se aa sakte hain?"),
    (10, "partner_nature", "Partner spiritual, practical, ambitious ya artistic nature ka hoga?"),
    (11, "general_mr", "Marriage ke baad emotional compatibility kaisi rahegi?"),
    (12, "partner_nature", "Partner dominant hoga ya cooperative?"),
    (13, "partner_nature", "Partner ke love language (care dikhane ka tareeka) kya ho sakta hai?"),
    (14, "loyalty_trust", "Relationship mein trust aur communication ka level kaisa rahega?"),
    (15, "partner_nature", "Partner ke andar kaunsi qualities mujhe sabse zyada attract karengi?"),
    (16, "general_mr", "Marriage se meri life mein kya positive changes aa sakte hain?"),
    (17, "partner_nature", "Kya partner different culture, city ya background se ho sakta hai?"),
    (18, "general_mr", "Relationship mein kis cheez par mujhe sabse zyada kaam karna chahiye?"),
    (19, "partner_nature", "Ideal spouse ki qualities meri kundli ke hisab se kya hain?"),
    (20, "general_mr", "Marriage partner meri career aur life goals ko support karega ya nahi?"),
    (21, "spouse_profession", "Meri patni ka kaam kis field mein hoga?"),
    (22, "spouse_profession", "Husband ki naukri ya business line kya ho sakti hai?"),
    (23, "general_mr", "Kya meri shaadi achhi rahegi?"),
    (24, "general_mr", "Vivah ke baad khushi aur sukh ka level kaisa rahega?"),
    (25, "breakup_risk", "Kya mera breakup ho sakta hai?"),
    (26, "breakup_risk", "Relationship tootne ka risk hai kya?"),
    (27, "breakup_risk", "Divorce ya alag hone ka pattern chart mein dikhta hai?"),
    (28, "patchup", "Patchup ho sakta hai kya?"),
    (29, "patchup", "Kya woh wapas aa sakta hai?"),
    (30, "patchup", "Reconciliation possible hai relationship mein?"),
    (31, "chemistry", "Hamari chemistry kaisi rahegi?"),
    (32, "chemistry", "Physical attraction strong rahega kya?"),
    (33, "chemistry", "Romance aur spark marriage mein rahega?"),
    (34, "emotional_attachment", "Mera emotional attachment style kaisa hai relationship mein?"),
    (35, "partner_nature", "Partner ke saath feelings gehra rahenge ya halki rahengi?"),
    (36, "family_approval", "Ghar wale meri shaadi ke liye maanenge kya?"),
    (37, "family_approval", "Intercaste marriage mein family approval milega?"),
    (38, "family_approval", "Parents meri pasand ko accept karenge?"),
    (39, "manglik", "Kya main manglik hoon?"),
    (40, "manglik", "Mangal dosh hai kya meri kundli mein?"),
    (41, "secret_relationship", "Kya chhupa rishta ya secret affair ka yog hai?"),
    (42, "one_sided_love", "Kya yeh ek tarfa pyar hai?"),
    (43, "one_sided_love", "Crush accept karega kya?"),
    (44, "obsession", "Kya main possessive ya jealous nature ka hoon?"),
    (45, "bed_intimacy", "Private life aur conjugal compatibility kaisi rahegi?"),
    (46, "self_worth", "Relationship mein self worth weak kyun lagti hai?"),
    (47, "partner_nature", "Partner mujhe respect dega ya nahi?"),
    (48, "second_marriage", "Kya meri dusri shaadi hogi?"),
    (49, "second_marriage", "Second marriage ka yog hai kya?"),
    (50, "long_distance", "Long distance relationship chalega kya?"),
    (51, "long_distance", "Door rehkar rishta strong reh sakta hai?"),
    (52, "spouse_wealth", "Partner rich hoga ya financially comfortable?"),
    (53, "spouse_wealth", "Spouse wealth aur paisa level kaisa hoga?"),
    (54, "patchup", "Ex wapas aayega kya?"),
    (55, "general_mr", "Gun milan / 36 gun score kaisa rahega?"),
    (56, "partner_nature", "Partner age gap zyada hoga kya?"),
    (57, "general_mr", "Kya main marry kar paungi?"),
    (58, "love_vs_arranged", "Khud pasand se shaadi hogi ya ghar wale choose karenge?"),
    (59, "loyalty_trust", "Kya mera partner loyal rahega ya dhokha de sakta hai?"),
    (60, "secret_relationship", "Multiple love relationships ka pattern hai?"),
]


def format_block(qid: int, expected: str, question: str) -> str:
    routed = classify_mr_archetype(question)
    res = run_mr_static_engine(SAMPLE_KUNDLI, question, wants_explain=False)
    route_ok = "OK" if routed == expected == res.archetype else "MISMATCH"
    lines = [
        "",
        "=" * 78,
        f"QUESTION #{qid}  [{route_ok}]",
        "=" * 78,
        f"Q: {question}",
        f"Expected engine : {expected}",
        f"Routed engine   : {routed}",
        f"Engine ran      : {res.archetype}",
        f"Skip LLM        : {res.skip_llm}",
        f"Verdict         : {res.verdict}",
        f"Confidence      : {res.confidence}",
        f"Word budget     : {res.word_budget}",
        "",
        "--- Evidence (LLM ko yeh facts jate hain) ---",
    ]
    for i, ev in enumerate(res.evidence or [], 1):
        lines.append(f"  {i}. {ev}")
    if res.summary:
        lines.append("")
        lines.append("--- Summary for narrator ---")
        for s in res.summary:
            lines.append(f"  • {s}")
    lines.append("")
    lines.append("--- Narrator payload (production shape) ---")
    lines.append(_production_narrator_payload(res))
    if res.skip_llm and res.template_text:
        lines.append("")
        lines.append("--- Template answer (no LLM) ---")
        lines.append(res.template_text)
    lines.append("")
    lines.append("CHECK: App mein yeh question pucho → admin mein archetype + verdict match karo.")
    lines.append("       User answer verdict ke direction mein human-friendly hona chahiye.")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="MR Ask one-by-one engine test")
    ap.add_argument("--id", type=int, help="Single question id (1-60)")
    ap.add_argument("--from", dest="from_id", type=int, default=1)
    ap.add_argument("--to", dest="to_id", type=int, default=60)
    ap.add_argument("--out", type=str, help="Write report to file")
    args = ap.parse_args()

    if args.id:
        items = [x for x in QUESTIONS if x[0] == args.id]
        if not items:
            print(f"No question id {args.id}", file=sys.stderr)
            return 1
    else:
        items = [x for x in QUESTIONS if args.from_id <= x[0] <= args.to_id]

    chunks = [format_block(qid, exp, q) for qid, exp, q in items]
    report = "\n".join(chunks)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"Wrote {len(items)} question(s) -> {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
