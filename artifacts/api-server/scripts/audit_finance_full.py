#!/usr/bin/env python3
"""Full non-timing finance audit — routing, engine, evidence alignment.

Checks per question:
  1. in_scope (finance static vs career vs off)
  2. archetype route matches expected engine
  3. engine runs without error
  4. evidence count >= min
  5. verdict+evidence contain question-focus keywords (alignment heuristic)
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_finance.classifier import classify_finance_archetype, is_finance_static_question
from ask_finance.engine import run_finance_static_engine

K = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo", "longitude": 120.0},
        {"name": "Moon", "house": 4, "sign": "Scorpio", "longitude": 220.0},
        {"name": "Mars", "house": 10, "sign": "Taurus", "longitude": 40.0},
        {"name": "Mercury", "house": 2, "sign": "Virgo", "longitude": 160.0},
        {"name": "Jupiter", "house": 5, "sign": "Sagittarius", "longitude": 250.0},
        {"name": "Venus", "house": 3, "sign": "Libra", "longitude": 190.0},
        {"name": "Saturn", "house": 7, "sign": "Aquarius", "longitude": 300.0},
        {"name": "Rahu", "house": 11, "sign": "Gemini", "longitude": 80.0},
        {"name": "Ketu", "house": 5, "sign": "Sagittarius", "longitude": 260.0},
    ],
    "currentDasha": {"maha": "Jupiter", "antar": "Saturn"},
}


@dataclass
class Case:
    q: str
    domain: str  # finance | career | off
    engine: str
    focus_rx: str  # regex that should appear in verdict+evidence (case-insensitive)
    min_evidence: int = 3


# ── 15 finance engines × ~5 questions each + edge cases ──────────────
CASES: list[Case] = [
    # wealth_potential
    Case("Kya main ameer banne ki potential rakhta hoon?", "finance", "wealth_potential", r"amir|wealth|rich|crorepati|capacity"),
    Case("Main crorepati ban sakta hoon?", "finance", "wealth_potential", r"amir|wealth|rich|crorepati"),
    Case("Mera wealth potential kaisa hai?", "finance", "wealth_potential", r"wealth|potential|amir|rich"),
    Case("Wealth create karne me kitna capable hoon?", "finance", "wealth_potential", r"wealth|amir|rich|capacity"),
    Case("Main kitna amir ho sakta hoon?", "finance", "wealth_potential", r"amir|wealth|rich"),
    # income_source
    Case("Mera paisa kamaane ka natural tareeka kya hai?", "finance", "income_source", r"income|earning|affinity|salary|business"),
    Case("Meri income stable hai ya nahi?", "finance", "income_source", r"income|stabil"),
    Case("Passive income ka yog hai?", "finance", "income_source", r"income|passive|11th|gain"),
    Case("Multiple income source ban sakte hain?", "finance", "income_source", r"income|multiple|source"),
    Case("Freelancing se paisa aayega?", "finance", "income_source", r"income|freelanc|project"),
    # savings_capacity
    Case("Kitni bachat kar sakta hoon?", "finance", "savings_capacity", r"saving|bachat|retain"),
    Case("Paisa bach pata hai ya nahi?", "finance", "savings_capacity", r"saving|bachat|retain"),
    Case("Saving capacity kaisi hai?", "finance", "savings_capacity", r"saving|bachat"),
    Case("Paisa rukta hai ya ud jata hai?", "finance", "savings_capacity", r"saving|leak|retain|tik"),
    Case("Monthly bachat ho sakti hai?", "finance", "savings_capacity", r"saving|bachat"),
    # save_vs_spend
    Case("Main paisa bachane wala hoon ya kharch karne wala?", "finance", "save_vs_spend", r"saver|spender|bach|kharch|mixed"),
    Case("Saver hoon ya spender?", "finance", "save_vs_spend", r"saver|spender|bach|kharch"),
    Case("Bachat zyada karti hoon ya kharch?", "finance", "save_vs_spend", r"saver|spender|bach|kharch"),
    # expense_pattern
    Case("Mera kharcha zyada kyun hai?", "finance", "expense_pattern", r"kharch|expense|leak|spend"),
    Case("Paisa kyun nahi tikta?", "finance", "expense_pattern", r"leak|kharch|tik|spend"),
    Case("Paisa haath me nahi rukta", "finance", "expense_pattern", r"leak|tik|kharch|spend"),
    Case("Expense control me hai ya nahi?", "finance", "expense_pattern", r"expense|leak|kharch|control"),
    Case("Fizul kharch hota hai kya?", "finance", "expense_pattern", r"kharch|leak|spend"),
    # spending_personality
    Case("Main emotional spending karta hoon?", "finance", "spending_personality", r"emotional|impulsive|spend|mood"),
    Case("Main luxury-oriented hoon?", "finance", "spending_personality", r"luxury|comfort|brand|spend"),
    Case("Impulsive shopping karta hoon?", "finance", "spending_personality", r"impulsive|spend|leak"),
    Case("Brand pe zyada kharch hota hai?", "finance", "spending_personality", r"luxury|brand|spend|comfort"),
    # financial_discipline
    Case("Main financial discipline me kaisa hoon?", "finance", "financial_discipline", r"discipline|saving|budget|leak"),
    Case("Budget banane ki aadat hai?", "finance", "financial_discipline", r"discipline|budget|saving"),
    Case("Paisa discipline weak hai kya?", "finance", "financial_discipline", r"discipline|weak|leak|saving"),
    Case("Saving discipline strong hai?", "finance", "financial_discipline", r"discipline|saving|strong"),
    # investment_risk
    Case("Main risk lene wala investor hoon ya conservative?", "finance", "investment_risk", r"risk|conservative|invest|moderate"),
    Case("Aggressive invest suit karega?", "finance", "investment_risk", r"risk|aggressive|invest|conservative"),
    Case("Safe investor hoon ya risky?", "finance", "investment_risk", r"safe|risk|invest|conservative"),
    Case("Investment me risk le sakta hoon?", "finance", "investment_risk", r"risk|invest"),
    # debt_loan
    Case("Loan lena chahiye?", "finance", "debt_loan", r"loan|debt|karz|emi"),
    Case("Karz clear ho payega?", "finance", "debt_loan", r"karz|debt|loan|clear|emi"),
    Case("EMI afford kar sakta hoon?", "finance", "debt_loan", r"emi|loan|debt|service"),
    Case("Credit card debt problem hai?", "finance", "debt_loan", r"debt|loan|karz|emi"),
    Case("Home loan lena safe hai?", "finance", "debt_loan", r"loan|debt|emi|home"),
    # property_money
    Case("Ghar khareedne ke liye paisa banega?", "finance", "property_money", r"property|ghar|home|purchase|saving"),
    Case("Property purchase possible hai?", "finance", "property_money", r"property|purchase|wealth|ghar"),
    Case("Flat lene ka yog hai?", "finance", "property_money", r"flat|property|ghar|home"),
    Case("Apna ghar ban sakta hai?", "finance", "property_money", r"ghar|home|property|house"),
    Case("Real estate me paisa jama hoga?", "finance", "property_money", r"property|real|estate|ghar"),
    # business_profit
    Case("Business se profit aayega?", "finance", "business_profit", r"business|profit|partnership|gain"),
    Case("Partnership business safe hai?", "finance", "business_profit", r"partnership|business|profit|7th"),
    Case("Apna kaam chalega paisa ke liye?", "finance", "business_profit", r"business|profit|income|kaam"),
    Case("Dhandha profit dega?", "finance", "business_profit", r"business|profit|dhandha|gain"),
    Case("Startup se paisa aayega?", "finance", "business_profit", r"business|profit|startup|venture"),
    # sudden_gain_loss
    Case("Sudden wealth ka yog hai?", "finance", "sudden_gain_loss", r"sudden|windfall|lottery|inheritance|gain"),
    Case("Lottery jeet sakta hoon?", "finance", "sudden_gain_loss", r"sudden|lottery|windfall|inheritance"),
    Case("Inheritance milegi?", "finance", "sudden_gain_loss", r"inheritance|sudden|virasat|windfall"),
    Case("Achanak bada loss hoga?", "finance", "sudden_gain_loss", r"loss|sudden|risk|emergency"),
    Case("Virasat se paisa aayega?", "finance", "sudden_gain_loss", r"inheritance|virasat|sudden|windfall"),
    # loss_reasons
    Case("Paisa kyun nahi bachta?", "finance", "loss_reasons", r"leak|bachat|saving|kyun|problem"),
    Case("Money problem kyun hai?", "finance", "loss_reasons", r"problem|leak|money|kyun"),
    Case("Financial problem ka reason kya?", "finance", "loss_reasons", r"problem|leak|reason|finance"),
    Case("Wealth block kyun lagta hai?", "finance", "loss_reasons", r"block|leak|wealth|kyun"),
    # dhana_yoga
    Case("Dhana yoga hai kya?", "finance", "dhana_yoga", r"yog|dhana|dhan|wealth"),
    Case("Chart me rich yog hai?", "finance", "dhana_yoga", r"yog|rich|wealth|dhana"),
    Case("Lakshmi yog active hai?", "finance", "dhana_yoga", r"lakshmi|yog|wealth"),
    Case("Kaun kaun se dhan yog hain?", "finance", "dhana_yoga", r"yog|dhana|active|wealth"),
    # general_finance
    Case("Mera overall finance kaisa hai?", "finance", "general_finance", r"finance|wealth|income|saving|leak"),
    Case("Meri financial condition kaisi hai?", "finance", "general_finance", r"finance|wealth|income|condition"),
    Case("Financial decisions me practical hoon?", "finance", "general_finance", r"finance|wealth|income|practical|decision"),
    Case("Money side strong hai ya weak?", "finance", "general_finance", r"money|wealth|income|strong|weak"),
    # career crossover (NOT finance)
    Case("Main employee mindset wala hoon ya entrepreneur mindset wala?", "career", "job_vs_business", r"job|business|employment|naukri|entrepreneur"),
    Case("Salary karu ya business?", "career", "job_vs_business", r"job|business|salary|naukri"),
    Case("Naukri better hai ya apna dhandha?", "career", "job_vs_business", r"job|business|naukri|dhandha"),
    # off-scope: timing
    Case("Kab amir banunga?", "off", "timing", r""),
    Case("Kab paisa aayega?", "off", "timing", r""),
    Case("2027 me wealth aayegi?", "off", "timing", r""),
    # off-scope: stock
    Case("Nifty me invest karu?", "off", "stock", r""),
    Case("Share market me paisa lagau?", "off", "stock", r""),
    Case("SIP start karu mutual fund?", "off", "stock", r""),
]


def _align_ok(text: str, focus_rx: str) -> bool:
    if not focus_rx:
        return True
    return bool(re.search(focus_rx, text, re.I))


def main() -> int:
    fails: list[str] = []
    by_engine: dict[str, list[str]] = {}

    print("=" * 72)
    print("FINANCE FULL AUDIT — non-timing routing + engine + evidence alignment")
    print("=" * 72)

    for i, c in enumerate(CASES, 1):
        issues: list[str] = []
        fin = is_finance_static_question(c.q)
        car = is_career_static_question(c.q)

        if c.domain == "finance":
            if not fin:
                issues.append("scope: expected finance IN but OUT")
            route = classify_finance_archetype(c.q) if fin else "OFF"
            if fin and route != c.engine:
                issues.append(f"route: got {route} want {c.engine}")
            if fin:
                try:
                    res = run_finance_static_engine(K, c.q, archetype=route)
                    blob = (res.verdict or "") + " " + " ".join(res.evidence or [])
                    if len(res.evidence or []) < c.min_evidence:
                        issues.append(f"evidence: {len(res.evidence or [])} < {c.min_evidence}")
                    if not _align_ok(blob, c.focus_rx):
                        issues.append(f"align: focus keywords missing in verdict/evidence")
                except Exception as exc:
                    issues.append(f"engine_error: {exc}")
        elif c.domain == "career":
            if fin:
                issues.append("scope: finance wrongly matched (should be career)")
            if not car:
                issues.append("scope: expected career IN but OUT")
            route = classify_career_archetype(c.q) if car else "OFF"
            if car and route != c.engine:
                issues.append(f"route: got {route} want {c.engine}")
        else:  # off
            if fin:
                issues.append("scope: should be OFF but finance matched")
            if car:
                issues.append("scope: should be OFF but career matched")

        status = "OK" if not issues else "FAIL"
        eng_key = c.engine if c.domain == "finance" else c.domain
        by_engine.setdefault(eng_key, []).append(status)
        print(f"[{i:3}] {status:4} | {c.domain:7} | {c.engine:22} | {c.q[:55]}")
        if issues:
            for iss in issues:
                print(f"       -> {iss}")
                fails.append(f"Q{i}: {c.q[:50]} — {iss}")

    print("\n" + "=" * 72)
    print("SUMMARY BY BUCKET")
    print("=" * 72)
    for eng, statuses in sorted(by_engine.items()):
        ok = sum(1 for s in statuses if s == "OK")
        print(f"  {eng:26} {ok}/{len(statuses)} OK")

    total = len(CASES)
    ok_n = total - len({f.split(":")[0] for f in fails})
    # count unique failed cases
    failed_cases = len([c for c in CASES if any(f.startswith(f"Q{CASES.index(c)+1}:") for f in fails)])
    # simpler:
    fail_ids = set()
    for f in fails:
        m = re.match(r"Q(\d+):", f)
        if m:
            fail_ids.add(int(m.group(1)))
    passed = total - len(fail_ids)
    print(f"\nTOTAL: {passed}/{total} OK, {len(fail_ids)} FAIL")
    return 1 if fail_ids else 0


if __name__ == "__main__":
    raise SystemExit(main())
