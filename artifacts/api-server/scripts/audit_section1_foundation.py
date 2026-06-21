"""Manual audit: Section 1 Career Foundation questions."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_career import run_career_static_engine
from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_career.routing import resolve_career_archetype

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
}

QUESTIONS = [
    "Mere liye job ya business me se kya zyada suitable hai?",
    "Mere career ki sabse badi strength kya hai?",
    "Mere career ki sabse badi weakness kya hai?",
    "Main naturally kis type ke work ke liye bana hoon?",
    "Mere andar leadership quality kitni hai?",
    "Main follower zyada hoon ya leader?",
    "Main independent work me better hoon ya team work me?",
    "Main practical hoon ya creative?",
    "Main analytical hoon ya intuitive?",
    "Main risk-taking hoon ya risk-averse?",
    "Main long-term planning me kitna strong hoon?",
    "Main pressure me kaisa perform karta hoon?",
    "Main responsibility lene me kaisa hoon?",
    "Main authority handle kar sakta hoon?",
    "Main authority ko accept kar pata hoon?",
    "Main disciplined hoon?",
    "Main consistent hoon?",
    "Main ambitious hoon?",
    "Main competitive hoon?",
    "Main innovation me strong hoon?",
    "Mere natural talents kya hain?",
    "Mere hidden talents kya hain?",
    "Mere career ke liye sabse valuable skill kya hai?",
    "Mujhe kis skill par focus karna chahiye?",
    "Mujhe kis skill ko avoid karna chahiye?",
    "Main communication me kitna strong hoon?",
    "Main public speaking me kitna strong hoon?",
    "Main negotiation me kitna strong hoon?",
    "Main networking me kitna strong hoon?",
    "Main persuasion me kitna strong hoon?",
    "Main problem solving me kitna strong hoon?",
    "Main decision making me kitna strong hoon?",
    "Main strategic thinking me kitna strong hoon?",
    "Main execution me kitna strong hoon?",
    "Main planning me kitna strong hoon?",
    "Main detail-oriented hoon?",
    "Main big-picture thinker hoon?",
    "Main multitasking me strong hoon?",
    "Main specialization me better hoon?",
    "Main management me better hoon?",
    "Main technical role me better hoon?",
    "Main client-facing role me better hoon?",
    "Main backend work me better hoon?",
    "Main research work me better hoon?",
    "Main field work me better hoon?",
    "Main office work me better hoon?",
    "Main remote work me better hoon?",
    "Main travel-based career me better hoon?",
    "Mere career ki core identity kya hai?",
    "Main kis tarah ka professional banne ke liye bana hoon?",
]

# Ideal archetype per question (Section 1 foundation mapping)
EXPECTED = {
    1: "job_vs_business",
    2: "strengths_skills",
    3: "strengths_skills",
    4: "general_career",
    5: "career_traits",
    6: "career_traits",
    7: "career_traits",
    8: "general_career",
    9: "general_career",
    10: "career_traits",
    11: "career_traits",
    12: "career_traits",
    13: "career_traits",
    14: "career_traits",
    15: "career_traits",
    16: "career_traits",
    17: "career_traits",
    18: "general_career",
    19: "general_career",
    20: "creativity_innovation",
    21: "strengths_skills",
    22: "strengths_skills",
    23: "strengths_skills",
    24: "strengths_skills",
    25: "strengths_skills",
    26: "strengths_skills",
    27: "strengths_skills",
    28: "career_traits",
    29: "career_traits",
    30: "career_traits",
    31: "general_career",
    32: "general_career",
    33: "career_traits",
    34: "general_career",
    35: "career_traits",
    36: "general_career",
    37: "general_career",
    38: "general_career",
    39: "general_career",
    40: "strengths_skills",
    41: "strengths_skills",
    42: "career_traits",
    43: "general_career",
    44: "general_career",
    45: "general_career",
    46: "general_career",
    47: "work_environment",
    48: "work_environment",
    49: "general_career",
    50: "general_career",
}


def main() -> None:
    ok = 0
    scope_fail = []
    route_fail = []
    no_evidence = []

    print(f"{'#':>3}  {'scope':5}  {'route':18}  {'ev':>2}  {'verdict':50}  question")
    print("-" * 140)

    for i, q in enumerate(QUESTIONS, 1):
        in_scope = is_career_static_question(q)
        rule = classify_career_archetype(q)
        resolved, _ = resolve_career_archetype(q, llm_archetype=None)
        res = run_career_static_engine(SAMPLE_KUNDLI, q, archetype=resolved)
        ev_n = len(res.evidence or [])
        verdict = (res.verdict or "")[:50]
        exp = EXPECTED.get(i, "?")
        match = resolved == exp or rule == exp
        if in_scope:
            ok += 1
        else:
            scope_fail.append(i)
        if not match:
            route_fail.append((i, exp, rule, resolved))
        if ev_n < 2:
            no_evidence.append((i, ev_n))

        flag = "OK" if in_scope and match and ev_n >= 2 else "!!"
        print(
            f"{i:>3}  {str(in_scope):5}  {resolved:18}  {ev_n:>2}  {verdict:50}  {q[:55]}"
        )
        if not match:
            print(f"      EXPECT {exp} | rule={rule} | resolved={resolved}")
        if ev_n >= 1:
            for e in (res.evidence or [])[:3]:
                print(f"        - {e[:90]}")

    print("\n=== SUMMARY ===")
    print(f"In scope: {ok}/{len(QUESTIONS)}")
    print(f"Scope fails: {scope_fail}")
    print(f"Route mismatches: {len(route_fail)}")
    for item in route_fail:
        print(f"  Q{item[0]}: expected={item[1]} rule={item[2]} resolved={item[3]}")
    print(f"Low evidence (<2): {no_evidence}")


if __name__ == "__main__":
    main()
