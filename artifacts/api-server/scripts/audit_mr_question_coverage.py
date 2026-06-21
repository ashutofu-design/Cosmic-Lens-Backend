"""Audit MR engine routing + evidence for ~300-style relationship questions."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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
            ],
        }
    },
}

AUDIT: list[tuple[str, list[tuple[str, str | None, list[str]]]]] = [
    (
        "1. Love Life",
        [
            ("kya mujhe sachcha pyaar milega?", "dating_courtship", ["True-love", "5th", "Venus", "Jupiter"]),
            ("kya multiple relationships honge?", "secret_relationship", ["Multiple", "parallel", "12th", "hidden"]),
            ("kya secret affair chal raha hai?", "secret_relationship", ["secret", "hidden", "12th"]),
            ("online relationship chalega kya?", "long_distance", ["Rahu", "online", "distance", "relationship"]),
            ("friend se lover ban sakta hai kya?", "dating_courtship", ["Friend-to-lover", "11th", "5th"]),
            ("partner loyal rahega kya?", "loyalty_trust", ["Trust", "loyal", "7th"]),
            ("commitment issues honge kya?", "loyalty_trust", ["Trust", "commit", "loyal"]),
            ("meri emotional needs poori hongi?", "emotional_attachment", ["Moon", "Emotional", "attach"]),
            ("mera attachment style kaisa hai?", "emotional_attachment", ["Moon", "Emotional", "attach"]),
        ],
    ),
    (
        "2. Dating & Courtship",
        [
            ("first impression kaisa rahega?", "dating_courtship", ["First-impression", "7th", "Venus"]),
            ("mera flirting style kaisa hai?", "dating_courtship", ["Flirting", "Venus", "Mercury"]),
            ("dating success milegi kya?", "dating_courtship", ["Dating success", "5th", "Venus"]),
            ("mera attraction pattern kya hai?", "dating_courtship", ["Attraction pattern", "Venus", "Mars"]),
            ("relationship me red flags kya hain?", "dating_courtship", ["Red flag", "Venus", "Mars", "7th"]),
            ("relationship me green flags kya hain?", "dating_courtship", ["Green flag", "Jupiter", "Venus", "5th"]),
        ],
    ),
    (
        "3. Love vs Arrange",
        [
            ("love marriage hogi ya arranged?", "love_vs_arranged", ["Love indicator", "Arrange indicator"]),
            ("love cum arrange hoga kya?", "love_vs_arranged", ["Love", "Arrange"]),
            ("inter-caste marriage hogi?", "family_approval", ["Inter-caste", "family", "Rahu"]),
            ("inter-religion shaadi?", "family_approval", ["Inter-religion", "family", "approval"]),
            ("court marriage hogi kya?", "family_approval", ["Court marriage", "family"]),
            ("family kitna involve hoga?", "family_approval", ["family", "Rahu", "Jupiter"]),
        ],
    ),
    (
        "4. Spouse Physical Appearance",
        [
            ("partner ki height kaisi hogi?", "spouse_appearance", ["Height pattern", "7th", "D9"]),
            ("spouse ka complexion kaisa hoga?", "spouse_appearance", ["Complexion", "Venus", "7th"]),
            ("wife ka face shape kaisa hoga?", "spouse_appearance", ["face", "7th", "Moon"]),
            ("partner ki aankhen kaisi hongi?", "spouse_appearance", ["Moon", "Venus", "eyes", "7th"]),
            ("husband ke baal kaisi honge?", "spouse_appearance", ["Hair", "Saturn", "7th"]),
            ("spouse ka body type kaisa hoga?", "spouse_appearance", ["body", "7th", "Mars"]),
            ("partner dressing style kaisi hogi?", "spouse_appearance", ["Dressing", "Venus", "7th"]),
            ("spouse ki awaaz kaisi hogi?", "spouse_appearance", ["Voice", "8th", "Mercury"]),
            ("partner ka aura kaisa hoga?", "spouse_appearance", ["aura", "Sun", "Venus", "7th"]),
            ("spouse kitna attractive hoga?", "spouse_appearance", ["Attractiveness", "Venus", "D9"]),
        ],
    ),
    (
        "5. Spouse Personality",
        [
            ("partner introvert hoga ya extrovert?", "partner_nature", ["Social energy", "7th"]),
            ("partner romantic hoga kya?", "partner_nature", ["Romantic nature", "Venus", "7th"]),
            ("partner caring hoga kya?", "partner_nature", ["Caring nature", "Moon", "7th"]),
            ("partner emotionally expressive hoga?", "partner_nature", ["Emotional style", "7th", "Moon"]),
            ("partner practical hoga ya emotional?", "partner_nature", ["Practical vs emotional", "Mercury", "Moon"]),
            ("partner ambitious hoga kya?", "partner_nature", ["Nature blend", "7th", "Venus"]),
            ("partner loyal hoga?", "loyalty_trust", ["Trust", "loyal", "7th"]),
            ("partner spiritual hoga kya?", "partner_nature", ["Nature blend", "Jupiter", "7th"]),
            ("partner dominant hoga ya cooperative?", "partner_nature", ["Partnership style", "7th"]),
            ("partner humorous hoga kya?", "partner_nature", ["Humour style", "Mercury", "Jupiter"]),
            ("partner honest hoga kya?", "partner_nature", ["Honesty pattern", "Jupiter", "7th"]),
            ("partner jealous hoga kya?", "obsession", ["jealous", "possess", "Moon"]),
        ],
    ),
    (
        "6. Spouse Profession",
        [
            ("wife ka profession kya hoga?", "spouse_profession", ["profession axis", "house 4"]),
            ("husband business karega ya job?", "spouse_profession", ["profession axis", "house 4"]),
            ("spouse government job karega?", "spouse_profession", ["profession axis", "house 4"]),
            ("partner IT field me hoga?", "spouse_profession", ["profession axis", "house 4"]),
            ("spouse doctor ban sakta hai?", "spouse_profession", ["profession axis", "house 4"]),
        ],
    ),
    (
        "7. Spouse Wealth",
        [
            ("partner rich hoga?", "spouse_wealth", ["spouse wealth", "house 8", "Jupiter"]),
            ("wife middle class family se hogi?", "spouse_wealth", ["Middle-class", "spouse wealth", "house 8"]),
            ("spouse wealthy family se hoga?", "spouse_wealth", ["Wealthy-family", "8th lord", "spouse"]),
            ("partner self made hoga?", "spouse_wealth", ["Self-made", "Mars", "spouse"]),
            ("spouse saving habits kaisi hongi?", "spouse_wealth", ["Saving habit", "Saturn", "spouse"]),
        ],
    ),
    (
        "8. In-Laws",
        [
            ("wife ke family wale kaise honge?", "partner_nature", ["8th house", "in-law", "Spouse-family"]),
            ("saas kaisi hogi?", "partner_nature", ["8th house", "Mother-in-law", "in-law"]),
            ("sasural joint family hoga ya nuclear?", "partner_nature", ["Joint-family", "8th house", "4th"]),
            ("mother in law nature kaisi hogi?", "partner_nature", ["Mother-in-law", "8th house"]),
            ("sasural interference hoga kya?", "partner_nature", ["In-law interference", "8th"]),
        ],
    ),
    (
        "9. Emotional Compatibility",
        [
            ("marriage ke baad emotional compatibility kaisi rahegi?", "general_mr", ["Moon", "emotional", "7th"]),
            ("partner samajh payega mujhe?", "general_mr", ["Mercury", "Moon", "communication", "understanding"]),
            ("communication strong hogi kya?", "general_mr", ["Mercury", "communication", "7th"]),
            ("shaadi ke baad trust strong hoga?", "loyalty_trust", ["Trust", "loyal", "7th"]),
            ("partner respect dega?", "partner_nature", ["Respect pattern", "7th"]),
        ],
    ),
    (
        "10. Physical / Romantic",
        [
            ("hamari chemistry kaisi hogi?", "chemistry", ["Venus", "Mars", "chemistry"]),
            ("passion strong hogi kya?", "chemistry", ["Venus", "Mars", "chemistry"]),
            ("romance kaisa rahega?", "chemistry", ["Venus", "chemistry"]),
            ("private life kaisi rahegi?", "bed_intimacy", ["Moon", "Venus", "intim"]),
            ("partner ka affection style kya hoga?", "partner_nature", ["Care style", "7th", "Moon"]),
        ],
    ),
    (
        "11. Marriage Quality",
        [
            ("shaadi ke baad khushi rahegi?", "general_mr", ["Moon", "Jupiter", "strength"]),
            ("marriage stable rahegi kya?", "general_mr", ["Stability", "Jupiter", "Saturn"]),
            ("partner career support karega?", "general_mr", ["support", "7th", "Jupiter"]),
            ("marriage me growth hogi?", "general_mr", ["growth", "7th", "Jupiter"]),
            ("teamwork strong hoga kya?", "general_mr", ["Teamwork", "support", "7th"]),
        ],
    ),
    (
        "12. Challenges & Risks",
        [
            ("divorce ka chance hai kya?", "breakup_risk", ["Breakup", "separation", "7th"]),
            ("rishta toot sakta hai kya?", "breakup_risk", ["Breakup", "separation"]),
            ("ego clash hoga kya?", "breakup_risk", ["Breakup", "Mars", "Saturn", "7th"]),
            ("third person interference hogi?", "loyalty_trust", ["Trust", "third", "hidden"]),
            ("relationship toxic hoga kya?", "breakup_risk", ["Toxic", "Breakup", "7th"]),
            ("partner manipulative hoga kya?", "partner_nature", ["Manipulation risk", "Rahu", "7th"]),
        ],
    ),
    (
        "13. Children",
        [
            ("spouse ka parenting style kaisa hoga?", "children_parenting", ["Parenting style", "5th", "11th"]),
            ("partner bachon ke saath bond kaisa hoga?", "children_parenting", ["Children bond", "5th", "Venus"]),
            ("family values strong honge kya?", "children_parenting", ["Family values", "9th", "Jupiter", "2nd"]),
        ],
    ),
    (
        "14. Foreign",
        [
            ("foreign spouse milega kya?", "partner_nature", ["Different background", "Rahu", "7th"]),
            ("partner alag culture se hoga?", "partner_nature", ["Different background", "Rahu"]),
            ("shaadi ke baad abroad settle honge?", "lifestyle_marriage", ["Foreign settlement", "12th", "9th"]),
        ],
    ),
    (
        "15. Spiritual / Karmic",
        [
            ("kya yeh soulmate hai?", "karmic_marriage", ["Soulmate", "Rahu", "Ketu", "7th"]),
            ("karmic debt marriage me hai?", "karmic_marriage", ["Karmic", "Saturn", "Rahu", "7th"]),
            ("past life connection hai kya?", "karmic_marriage", ["Past-life", "Ketu", "Rahu"]),
            ("marriage se spiritual growth hogi?", "karmic_marriage", ["Spiritual growth", "Jupiter", "9th"]),
        ],
    ),
    (
        "16. Psychological",
        [
            ("mera love language kya hai?", "partner_nature", ["Care style", "Moon", "Venus", "Mercury"]),
            ("conflict style kaisa hoga?", "general_mr", ["friction", "Mars", "Saturn", "7th"]),
            ("emotional maturity kaisi hogi?", "general_mr", ["emotional", "Moon", "compatibility"]),
        ],
    ),
    (
        "17. Lifestyle",
        [
            ("shaadi ke baad luxury lifestyle hogi?", "lifestyle_marriage", ["Luxury", "2nd", "11th", "Venus"]),
            ("travel zyada hoga kya?", "lifestyle_marriage", ["Travel", "9th", "12th"]),
            ("social life active hogi?", "lifestyle_marriage", ["Social", "11th", "Venus"]),
            ("ghar ka mahaul kaisa hoga?", "lifestyle_marriage", ["Home", "4th", "Moon"]),
        ],
    ),
]


def _evidence_hit(evidence: list[str], needles: list[str]) -> bool:
    blob = " ".join(evidence).lower()
    return any(n.lower() in blob for n in needles)


def main() -> int:
    total = 0
    route_ok = 0
    evidence_ok = 0
    gaps: list[str] = []

    print("MR QUESTION COVERAGE AUDIT\n" + "=" * 72)
    for cat, items in AUDIT:
        print(f"\n{cat}")
        print("-" * 72)
        for q, expected_arch, must_have in items:
            total += 1
            arch = classify_mr_archetype(q)
            res = run_mr_static_engine(SAMPLE_KUNDLI, q)
            ev = res.evidence or []
            ev_hit = _evidence_hit(ev, must_have)
            route_hit = expected_arch is None or arch == expected_arch

            if route_hit:
                route_ok += 1
            if ev_hit:
                evidence_ok += 1

            status = "OK" if route_hit and ev_hit else "GAP"
            if status == "GAP":
                gaps.append(f"{cat} | {q} | arch={arch} exp={expected_arch} ev={ev_hit}")

            print(f"  [{status}] {q[:52]:<52} -> {arch:<20} ev={len(ev):2d}")

    print("\n" + "=" * 72)
    print(f"TOTAL: {total} | ROUTING: {route_ok}/{total} | EVIDENCE: {evidence_ok}/{total} | GAPS: {len(gaps)}")
    for g in gaps:
        print(f"  GAP: {g}")
    return 0 if not gaps else 1


if __name__ == "__main__":
    raise SystemExit(main())
