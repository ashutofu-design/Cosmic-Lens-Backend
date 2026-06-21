"""Audit career engine routing + evidence for 500+ style career question bank."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_career import run_career_static_engine

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

# (question, expected_archetype, evidence_needles)
AUDIT: list[tuple[str, list[tuple[str, str, list[str]]]]] = [
    (
        "1. Job vs Business & Path",
        [
            ("Mere liye job better hai ya business?", "job_vs_business", ["job", "business", "split"]),
            ("Main employee type hoon ya entrepreneur type?", "job_vs_business", ["job", "business", "independence"]),
            ("Kya mujhe salary-based career rakhna chahiye?", "income_wealth", ["salary", "job", "Income"]),
            ("Kya mujhe entrepreneurship se zyada paisa milega?", "income_wealth", ["business", "income", "2nd"]),
        ],
    ),
    (
        "2. Sector & Industry Fit",
        [
            ("Kaunsi industry mere liye best rahegi?", "sector_fit", ["10th", "industr", "Sector"]),
            ("Government job suit karegi?", "sector_fit", ["Government", "10th", "job"]),
            ("Private sector suit karega?", "sector_fit", ["Private", "10th", "corporate"]),
            ("Self-employment suit karega?", "entrepreneurship", ["business", "independence", "Entrepreneurship"]),
            ("Consulting field kaisi rahegi?", "sector_fit", ["Consulting", "10th", "Sector"]),
            ("Teaching profession suit karega?", "sector_fit", ["Teaching", "10th", "Sector"]),
            ("Main creative field me successful ho sakta hoon?", "sector_fit", ["Creative", "10th", "commercial"]),
            ("Technical field suit karti hai?", "sector_fit", ["Technical", "10th", "Sector"]),
            ("Management role suit karta hai?", "sector_fit", ["Management", "10th", "Sector"]),
            ("Sales aur marketing mere liye kaise rahenge?", "sector_fit", ["Sales", "10th", "commercial"]),
            ("Research field suit karti hai?", "sector_fit", ["Research", "10th", "Sector"]),
            ("Law profession suit karega?", "sector_fit", ["Law", "10th", "Sector"]),
            ("Medical field suit karegi?", "sector_fit", ["Medical", "10th", "Sector"]),
            ("Finance sector suit karega?", "sector_fit", ["Finance", "10th", "Sector"]),
            ("IT industry suit karegi?", "sector_fit", ["IT", "10th", "digital"]),
            ("Real estate business suit karega?", "sector_fit", ["Real estate", "10th", "Sector"]),
        ],
    ),
    (
        "3. Career Personality & Traits",
        [
            ("Main leadership role ke liye suitable hoon?", "career_traits", ["leadership", "score"]),
            ("Mere andar leadership quality kitni hai?", "career_traits", ["leadership", "score"]),
            ("Kya main team handle kar sakta hoon?", "career_traits", ["communication", "score"]),
            ("Kya main independent work me better hoon?", "career_traits", ["independence", "score"]),
            ("Kya main pressure handle kar sakta hoon?", "career_traits", ["persistence", "score"]),
            ("Kya main risk-taking person hoon?", "career_traits", ["risk", "score"]),
            ("Kya main disciplined hoon?", "career_traits", ["discipline", "score"]),
            ("Kya main strategic thinker hoon?", "career_traits", ["adaptability", "score"]),
            ("Kya main public dealing me achha hoon?", "career_traits", ["communication", "score"]),
            ("Kya main networking me strong hoon?", "career_traits", ["communication", "score"]),
            ("Kya main negotiation me strong hoon?", "career_traits", ["communication", "score"]),
        ],
    ),
    (
        "4. Strengths & Skills",
        [
            ("Mere natural talents kya hain?", "strengths_skills", ["strength", "natural"]),
            ("Mere career ki biggest strength kya hai?", "strengths_skills", ["strength", "Biggest"]),
            ("Meri biggest weakness kya hai?", "strengths_skills", ["weakness", "Growth edge"]),
            ("Kaunsi skill mujhe develop karni chahiye?", "strengths_skills", ["develop", "skill"]),
            ("Kaunsi skill naturally strong hai?", "strengths_skills", ["natural", "strong"]),
            ("Kya mujhe communication improve karna chahiye?", "strengths_skills", ["communication", "skill"]),
            ("Kya mujhe technical expertise par focus karna chahiye?", "strengths_skills", ["technical", "skill"]),
            ("Kya mujhe management skills par kaam karna chahiye?", "strengths_skills", ["management", "skill"]),
            ("Kya mujhe public speaking seekhni chahiye?", "strengths_skills", ["communication", "skill"]),
            ("Kya mujhe sales skills seekhni chahiye?", "strengths_skills", ["communication", "skill"]),
            ("Kya mujhe foreign language seekhni chahiye?", "strengths_skills", ["communication", "skill"]),
        ],
    ),
    (
        "5. Business & Entrepreneurship",
        [
            ("Kya mujhe apna business start karna chahiye?", "entrepreneurship", ["business", "Entrepreneurship"]),
            ("Kya partnership business suit karega?", "entrepreneurship", ["Partnership", "business"]),
            ("Kya solo business better rahega?", "entrepreneurship", ["Solo", "business"]),
            ("Kya family business join karna chahiye?", "entrepreneurship", ["Family", "business"]),
            ("Kya online business suit karega?", "entrepreneurship", ["Online", "business"]),
            ("Kya trading mere liye suitable hai?", "entrepreneurship", ["Trading", "business"]),
            ("Kya consulting business suit karega?", "entrepreneurship", ["Consulting", "business"]),
            ("Kya manufacturing business suit karega?", "entrepreneurship", ["Manufacturing", "business"]),
            ("Kya import-export business suit karega?", "entrepreneurship", ["Import-export", "business"]),
            ("Kya startup founder banna suit karega?", "entrepreneurship", ["Startup", "business"]),
        ],
    ),
    (
        "6. Work Environment & Foreign",
        [
            ("Kya mujhe foreign country me kaam karna chahiye?", "foreign_career", ["Foreign", "9th", "12th"]),
            ("Kya multinational company suit karegi?", "work_environment", ["MNC", "corporate"]),
            ("Kya remote work suit karega?", "work_environment", ["Remote", "independence"]),
            ("Kya frequent travel wala career suit karega?", "work_environment", ["Travel", "career"]),
            ("Kya public sector better rahega?", "work_environment", ["Public", "sector"]),
            ("Kya corporate world suit karega?", "work_environment", ["Corporate", "job"]),
            ("Kya NGO sector suit karega?", "sector_fit", ["NGO", "10th", "Sector"]),
            ("Kya politics me success mil sakti hai?", "sector_fit", ["Politics", "10th", "Sector"]),
            ("Kya media field suit karegi?", "sector_fit", ["Media", "10th", "Sector"]),
            ("Kya content creation suit karega?", "creativity_innovation", ["Creative", "Venus", "Mercury"]),
        ],
    ),
    (
        "7. Wealth & Income",
        [
            ("Main paisa kamane me kitna strong hoon?", "income_wealth", ["wealth", "Income", "2nd"]),
            ("Wealth creation ke liye meri approach kya honi chahiye?", "income_wealth", ["Wealth", "2nd", "11th"]),
            ("Kya main high-income profession ke liye suitable hoon?", "income_wealth", ["High-income", "commercial"]),
            ("Kya mujhe multiple income sources rakhne chahiye?", "income_wealth", ["Multiple", "income"]),
            ("Kya mujhe passive income build karni chahiye?", "income_wealth", ["Passive", "income"]),
            ("Kya mujhe investments par focus karna chahiye?", "income_wealth", ["Investment", "2nd"]),
            ("Kya mujhe commission-based work suit karega?", "income_wealth", ["Commission", "commercial"]),
            ("Kya mujhe freelancing suit karegi?", "income_wealth", ["Freelanc", "income"]),
        ],
    ),
    (
        "8. Workplace Relations & Satisfaction",
        [
            ("Kya boss se relation achha rahega?", "workplace_relations", ["Boss", "Sun", "6th"]),
            ("Office politics se problem hogi kya?", "workplace_relations", ["6th", "10th", "work"]),
            ("Colleagues ke saath bonding achhi hogi?", "workplace_relations", ["Colleague", "6th", "Mercury"]),
            ("Job satisfaction milegi kya?", "workplace_relations", ["satisfaction", "career mode"]),
        ],
    ),
    (
        "9. Fame, Creativity, Obstacles, Education, Legacy",
        [
            ("Career me fame milegi kya?", "fame_recognition", ["Fame", "10th", "Sun"]),
            ("Recognition milega profession me?", "fame_recognition", ["recognition", "10th", "Sun"]),
            ("Innovation field me success hoga?", "creativity_innovation", ["Creative", "Rahu", "Venus"]),
            ("Career me delay aur obstacles zyada hain?", "career_obstacles", ["Affliction", "obstacle"]),
            ("Kaunsa course ya degree career ke liye best?", "education_career", ["Education", "4th", "Mercury"]),
            ("Higher studies career boost karengi?", "education_career", ["Higher", "9th", "Jupiter"]),
            ("Retirement ke baad kya karun?", "retirement_legacy", ["Retirement", "Saturn", "legacy"]),
            ("Career legacy kaisi rahegi?", "retirement_legacy", ["legacy", "10th", "Saturn"]),
        ],
    ),
    (
        "10. Negative controls (must NOT route as career static)",
        [
            ("Kab job milegi?", None, []),
            ("Meri patni ka profession kya hoga?", None, []),
            ("Love marriage hogi ya arranged?", None, []),
        ],
    ),
]


def _expanded_audit_items() -> list[tuple[str, str, list[str]]]:
    """Programmatic ~500+ career question variants from subdomain templates."""
    items: list[tuple[str, str, list[str]]] = []
    sectors = [
        ("government job", "sector_fit", ["Government", "10th"]),
        ("private sector", "sector_fit", ["Private", "10th"]),
        ("IT industry", "sector_fit", ["IT", "10th"]),
        ("medical field", "sector_fit", ["Medical", "10th"]),
        ("law profession", "sector_fit", ["Law", "10th"]),
        ("teaching career", "sector_fit", ["Teaching", "10th"]),
        ("finance sector", "sector_fit", ["Finance", "10th"]),
        ("sales marketing", "sector_fit", ["Sales", "10th"]),
        ("research field", "sector_fit", ["Research", "10th"]),
        ("real estate", "sector_fit", ["Real estate", "10th"]),
        ("consulting field", "sector_fit", ["Consulting", "10th"]),
        ("media field", "sector_fit", ["Media", "10th"]),
        ("NGO sector", "sector_fit", ["NGO", "10th"]),
        ("politics", "sector_fit", ["Politics", "10th"]),
    ]
    suffixes = [
        "suit karega?",
        "suit karegi?",
        "mere liye sahi hai?",
        "ke liye best rahega?",
        "me success milega?",
    ]
    for sector, arch, needles in sectors:
        for suf in suffixes:
            items.append((f"Kya {sector} {suf}", arch, needles))

    traits = [
        ("leadership role", "career_traits", ["leadership", "score"]),
        ("team handle", "career_traits", ["communication", "score"]),
        ("pressure handle", "career_traits", ["persistence", "score"]),
        ("risk taking", "career_traits", ["risk", "score"]),
        ("discipline", "career_traits", ["discipline", "score"]),
        ("strategic thinking", "career_traits", ["adaptability", "score"]),
        ("public dealing", "career_traits", ["communication", "score"]),
        ("networking", "career_traits", ["communication", "score"]),
        ("negotiation", "career_traits", ["communication", "score"]),
    ]
    for trait, arch, needles in traits:
        items.append((f"Kya main {trait} me strong hoon?", arch, needles))
        items.append((f"Meri {trait} quality kaisi hai?", arch, needles))

    biz = [
        ("startup founder", "entrepreneurship", ["Startup", "business"]),
        ("partnership business", "entrepreneurship", ["Partnership", "business"]),
        ("solo business", "entrepreneurship", ["Solo", "business"]),
        ("family business", "entrepreneurship", ["Family", "business"]),
        ("online business", "entrepreneurship", ["Online", "business"]),
        ("trading business", "entrepreneurship", ["Trading", "business"]),
        ("consulting business", "entrepreneurship", ["Consulting", "business"]),
        ("manufacturing business", "entrepreneurship", ["Manufacturing", "business"]),
        ("import-export business", "entrepreneurship", ["Import-export", "business"]),
    ]
    for label, arch, needles in biz:
        items.append((f"Kya {label} mere liye sahi hai?", arch, needles))

    income = [
        ("passive income", "income_wealth", ["Passive", "income"]),
        ("multiple income sources", "income_wealth", ["Multiple", "income"]),
        ("commission based work", "income_wealth", ["Commission", "commercial"]),
        ("freelancing", "income_wealth", ["Freelanc", "income"]),
        ("salary based career", "income_wealth", ["Salary", "job"]),
        ("wealth creation", "income_wealth", ["Wealth", "2nd"]),
        ("high income profession", "income_wealth", ["High-income", "commercial"]),
    ]
    for label, arch, needles in income:
        items.append((f"Kya mujhe {label} par focus karna chahiye?", arch, needles))

    workplace = [
        ("boss se relation", "workplace_relations", ["Boss", "6th"]),
        ("colleagues ke saath bonding", "workplace_relations", ["Colleague", "6th"]),
        ("job satisfaction", "workplace_relations", ["satisfaction", "career mode"]),
    ]
    for label, arch, needles in workplace:
        items.append((f"Career me {label} kaisa rahega?", arch, needles))

    skills = [
        ("communication skill", "strengths_skills", ["communication", "skill"]),
        ("technical expertise", "strengths_skills", ["technical", "skill"]),
        ("management skill", "strengths_skills", ["management", "skill"]),
        ("public speaking", "strengths_skills", ["communication", "skill"]),
        ("sales skill", "strengths_skills", ["communication", "skill"]),
        ("foreign language", "strengths_skills", ["communication", "skill"]),
    ]
    for label, arch, needles in skills:
        items.append((f"Kya mujhe {label} develop karni chahiye?", arch, needles))
        items.append((f"Meri {label} strong hai kya?", arch, needles))

    envs = [
        ("remote work", "work_environment", ["Remote", "independence"]),
        ("corporate world", "work_environment", ["Corporate", "job"]),
        ("public sector", "work_environment", ["Public", "sector"]),
        ("private sector", "work_environment", ["Private", "sector"]),
        ("multinational company", "work_environment", ["MNC", "corporate"]),
        ("frequent travel career", "work_environment", ["Travel", "career"]),
    ]
    for label, arch, needles in envs:
        items.append((f"Kya {label} mere liye sahi hai?", arch, needles))

    foreign = [
        ("foreign country me kaam", "foreign_career", ["Foreign", "9th"]),
        ("abroad job", "foreign_career", ["Foreign", "12th"]),
        ("videsh me career", "foreign_career", ["Rahu", "foreign"]),
    ]
    for label, arch, needles in foreign:
        items.append((f"Kya mujhe {label} karna chahiye?", arch, needles))

    misc = [
        ("job vs business", "job_vs_business", ["job", "business"]),
        ("employee type ya entrepreneur type", "job_vs_business", ["job", "business"]),
        ("career fame", "fame_recognition", ["Fame", "10th"]),
        ("career recognition", "fame_recognition", ["recognition", "Sun"]),
        ("creative career", "creativity_innovation", ["Creative", "Venus"]),
        ("content creation career", "creativity_innovation", ["Creative", "Mercury"]),
        ("career obstacles", "career_obstacles", ["Affliction", "obstacle"]),
        ("career delay", "career_obstacles", ["Affliction", "delay"]),
        ("higher studies", "education_career", ["Higher", "9th"]),
        ("career course", "education_career", ["Education", "Mercury"]),
        ("retirement plan", "retirement_legacy", ["Retirement", "Saturn"]),
        ("career legacy", "retirement_legacy", ["legacy", "10th"]),
    ]
    for label, arch, needles in misc:
        items.append((f"Mera {label} kaisa rahega?", arch, needles))
        items.append((f"Kya {label} strong dikhta hai?", arch, needles))

    actions = [
        "suit karega?",
        "suit karegi?",
        "ke liye sahi hai?",
        "me success milega?",
        "try karna chahiye?",
        "better rahega?",
        "mujhe chahiye?",
        "possible hai?",
    ]
    topics = [
        ("government naukri", "sector_fit", ["Government", "10th"]),
        ("private company job", "sector_fit", ["Private", "10th"]),
        ("IT software job", "sector_fit", ["IT", "10th"]),
        ("medical line", "sector_fit", ["Medical", "10th"]),
        ("law line", "sector_fit", ["Law", "10th"]),
        ("teaching line", "sector_fit", ["Teaching", "10th"]),
        ("finance career", "sector_fit", ["Finance", "10th"]),
        ("sales job", "sector_fit", ["Sales", "10th"]),
        ("research career", "sector_fit", ["Research", "10th"]),
        ("real estate line", "sector_fit", ["Real estate", "10th"]),
        ("consulting career", "sector_fit", ["Consulting", "10th"]),
        ("media career", "sector_fit", ["Media", "10th"]),
        ("NGO kaam", "sector_fit", ["NGO", "10th"]),
        ("politics career", "sector_fit", ["Politics", "10th"]),
        ("creative field", "sector_fit", ["Creative", "10th"]),
        ("technical engineering", "sector_fit", ["Technical", "10th"]),
        ("management role", "sector_fit", ["Management", "10th"]),
        ("startup founder path", "entrepreneurship", ["Startup", "business"]),
        ("partnership dhandha", "entrepreneurship", ["Partnership", "business"]),
        ("solo business", "entrepreneurship", ["Solo", "business"]),
        ("family business join", "entrepreneurship", ["Family", "business"]),
        ("online business", "entrepreneurship", ["Online", "business"]),
        ("trading business", "entrepreneurship", ["Trading", "business"]),
        ("freelancing income", "income_wealth", ["Freelanc", "income"]),
        ("passive income path", "income_wealth", ["Passive", "income"]),
        ("commission sales job", "income_wealth", ["Commission", "commercial"]),
        ("salary career", "income_wealth", ["Salary", "job"]),
        ("remote work", "work_environment", ["Remote", "independence"]),
        ("corporate job", "work_environment", ["Corporate", "job"]),
        ("MNC job", "work_environment", ["MNC", "corporate"]),
        ("foreign job", "foreign_career", ["Foreign", "9th"]),
        ("abroad career", "foreign_career", ["Foreign", "12th"]),
        ("boss relation", "workplace_relations", ["Boss", "6th"]),
        ("colleague bonding", "workplace_relations", ["Colleague", "6th"]),
        ("job satisfaction", "workplace_relations", ["satisfaction", "career mode"]),
        ("career fame", "fame_recognition", ["Fame", "10th"]),
        ("content creation", "creativity_innovation", ["Creative", "Mercury"]),
        ("career obstacles", "career_obstacles", ["Affliction", "obstacle"]),
        ("higher studies", "education_career", ["Higher", "9th"]),
        ("retirement legacy", "retirement_legacy", ["Retirement", "Saturn"]),
        ("job vs business path", "job_vs_business", ["job", "business"]),
    ]
    for topic, arch, needles in topics:
        for act in actions:
            items.append((f"Kya {topic} {act}", arch, needles))

    return items


def _evidence_hit(evidence: list[str], needles: list[str]) -> bool:
    if not needles:
        return True
    blob = " ".join(evidence).lower()
    return any(n.lower() in blob for n in needles)


def _run_smoke_expand() -> int:
    """Smoke-test ~500 template variants: static detect + engine evidence only."""
    items = _expanded_audit_items()
    fails: list[str] = []
    ok = 0
    print("\nEXPANDED SMOKE TEST (~500 variants)\n" + "=" * 72)
    for q, _arch_hint, _needles in items:
        if not is_career_static_question(q):
            fails.append(f"not static: {q}")
            continue
        res = run_career_static_engine(SAMPLE_KUNDLI, q)
        if len(res.evidence or []) < 3:
            fails.append(f"thin evidence ({len(res.evidence or [])}): {q}")
            continue
        ok += 1
    print(f"SMOKE OK: {ok}/{len(items)} | FAILS: {len(fails)}")
    for f in fails[:20]:
        print(f"  FAIL: {f}")
    if len(fails) > 20:
        print(f"  ... and {len(fails) - 20} more")
    return 0 if not fails else 1


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Audit career question routing + evidence")
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Also smoke-test ~500 programmatic template variants",
    )
    args = parser.parse_args()

    audit_sets = list(AUDIT)

    total = 0
    static_ok = 0
    route_ok = 0
    evidence_ok = 0
    gaps: list[str] = []

    print("CAREER QUESTION COVERAGE AUDIT\n" + "=" * 72)
    for cat, items in audit_sets:
        print(f"\n{cat}")
        print("-" * 72)
        for q, expected_arch, must_have in items:
            total += 1
            is_static = is_career_static_question(q)
            arch = classify_career_archetype(q)

            if expected_arch is None:
                if not is_static:
                    static_ok += 1
                    route_ok += 1
                    evidence_ok += 1
                    status = "OK"
                else:
                    status = "GAP"
                    gaps.append(f"{cat} | {q} | should NOT be career static")
                print(f"  [{status}] {q[:52]:<52} static={is_static}")
                continue

            if is_static:
                static_ok += 1
            res = run_career_static_engine(SAMPLE_KUNDLI, q)
            ev = res.evidence or []
            ev_hit = _evidence_hit(ev, must_have)
            route_hit = arch == expected_arch and res.archetype == expected_arch

            if route_hit:
                route_ok += 1
            if ev_hit:
                evidence_ok += 1

            status = "OK" if is_static and route_hit and ev_hit else "GAP"
            if status == "GAP":
                gaps.append(
                    f"{cat} | {q} | static={is_static} arch={arch} exp={expected_arch} "
                    f"engine={res.archetype} ev={ev_hit}"
                )

            print(
                f"  [{status}] {q[:48]:<48} -> {arch:<22} ev={len(ev):2d} static={is_static}"
            )

    print("\n" + "=" * 72)
    print(
        f"TOTAL: {total} | STATIC: {static_ok}/{total - 3} career Qs | "
        f"ROUTING: {route_ok}/{total} | EVIDENCE: {evidence_ok}/{total} | GAPS: {len(gaps)}"
    )
    for g in gaps:
        print(f"  GAP: {g}")
    code = 0 if not gaps else 1
    if args.expand:
        code = max(code, _run_smoke_expand())
    return code


if __name__ == "__main__":
    raise SystemExit(main())
