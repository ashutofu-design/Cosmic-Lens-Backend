#!/usr/bin/env python3
"""Full non-timing foreign travel audit — routing, scope, D9 evidence alignment."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_travel import run_travel_static_engine
from ask_travel.classifier import classify_travel_archetype, is_travel_static_question
from ask_travel.travel_registry import (
    detect_travel_archetype,
    is_career_job_abroad_question,
    is_education_study_abroad_question,
    is_mr_settle_abroad_question,
)

K = {
    "ascendant": "Sagittarius",
    "ascendantDeg": 255.0,
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 75.0},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
        {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 105.0},
        {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 15.0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 345.0},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 315.0},
        {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
    ],
}

_D9_RX = r"D9|Navamsa|9th|9H|12th|12H|Rahu|foreign|travel"


@dataclass
class Case:
    q: str
    domain: str
    engine: str
    focus_rx: str
    min_evidence: int = 6


def C(q: str, eng: str, rx: str = _D9_RX, min_e: int = 6) -> Case:
    return Case(q, "travel", eng, rx, min_e)


def EDU(q: str) -> Case:
    return Case(q, "education", "", "")


def CAREER(q: str) -> Case:
    return Case(q, "career", "", "")


def MR(q: str) -> Case:
    return Case(q, "mr", "", "")


def TIMING(q: str) -> Case:
    return Case(q, "timing", "", "")


def OFF(q: str) -> Case:
    return Case(q, "off", "", "")


CASES: list[Case] = [
    # travel_yog
    C("Videsh jaa sakta hoon kya?", "travel_yog"),
    C("Foreign travel yog hai?", "travel_yog"),
    C("Abroad possible hai chart se?", "travel_yog"),
    C("Will I go abroad?", "travel_yog"),
    C("Videsh yatra hogi kya?", "travel_yog"),
    C("Overseas travel possible?", "travel_yog"),
    C("Foreign travel strong hai?", "travel_yog"),
    C("Videsh ja paunga kya?", "travel_yog"),
    C("Abroad yog chart me?", "travel_yog"),
    C("Foreign trip yog?", "travel_yog"),
    C("Videsh milega kya chart se?", "travel_yog"),
    C("Travel promise chart me?", "travel_yog"),
    C("Overseas possible hai?", "travel_yog"),
    C("Videsh yatra yog strong?", "travel_yog"),
    C("Foreign lands possible?", "travel_yog"),
    C("Abroad ja sakta hoon?", "travel_yog"),
    C("Videsh travel chance?", "travel_yog"),
    C("Foreign journey possible?", "travel_yog"),
    # foreign_settlement
    C("Settle abroad possible hai?", "foreign_settlement"),
    C("Videsh me bas sakta hoon?", "foreign_settlement"),
    C("Permanent abroad settlement?", "foreign_settlement"),
    C("Videsh me reh sakta hoon?", "foreign_settlement"),
    C("Foreign settlement yog?", "foreign_settlement"),
    C("Abroad basna chart se?", "foreign_settlement"),
    C("Settle in Canada possible?", "foreign_settlement"),
    C("Videsh me permanent life?", "foreign_settlement"),
    C("Abroad settlement strong?", "foreign_settlement"),
    C("Foreign land me basna?", "foreign_settlement"),
    C("Settle videsh chart?", "foreign_settlement"),
    C("Permanent shift abroad?", "foreign_settlement"),
    C("Videsh bas paunga?", "foreign_settlement"),
    C("Life abroad settlement?", "foreign_settlement"),
    C("Overseas settlement theme?", "foreign_settlement"),
    # visa_theme
    C("Visa approve hoga kya?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("US visa milega chart se?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("UK visa possible hai?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Canada visa chart?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Visa rejection chart se?", "visa_theme", r"visa|Saturn|9th|12th|D9"),
    C("Visa problem chart me?", "visa_theme", r"visa|Saturn|9th|12th|D9"),
    C("Visa delay chart se?", "visa_theme", r"visa|Saturn|9th|12th|D9"),
    C("Schengen visa possible?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Visa interview chart tone?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Visa approve hone ke chances?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Visa refusal chart?", "visa_theme", r"visa|Saturn|9th|12th|D9"),
    C("Embassy visa chart?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Visa stuck chart se?", "visa_theme", r"visa|Saturn|9th|12th|D9"),
    C("Tourist visa possible?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Visitor visa chart?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    # relocation_abroad
    C("Relocate abroad chart support?", "relocation_abroad"),
    C("Shift to Canada possible?", "relocation_abroad"),
    C("Move abroad chart se?", "relocation_abroad"),
    C("Videsh shift chart?", "relocation_abroad"),
    C("Relocation overseas theme?", "relocation_abroad"),
    C("Shift foreign country chart?", "relocation_abroad"),
    C("Move to USA chart?", "relocation_abroad"),
    C("Abroad shift possible?", "relocation_abroad"),
    C("Relocate videsh chart?", "relocation_abroad"),
    C("Foreign shift chart se?", "relocation_abroad"),
    C("Move overseas possible?", "relocation_abroad"),
    C("Shift abroad chart reading?", "relocation_abroad"),
    C("Relocation chart tone?", "relocation_abroad"),
    C("Leaving India abroad chart?", "relocation_abroad"),
    C("Pack up abroad chart?", "relocation_abroad"),
    # return_india
    C("India wapas aa sakta hoon?", "return_india"),
    C("Abroad se wapas aana?", "return_india"),
    C("Return to India chart?", "return_india"),
    C("Videsh se wapas?", "return_india"),
    C("Come back India chart?", "return_india"),
    C("Wapas Bharat aana?", "return_india"),
    C("No settlement abroad chart?", "return_india"),
    C("Foreign settlement nahi hoga?", "return_india"),
    C("India return theme chart?", "return_india"),
    C("Abroad se return possible?", "return_india"),
    C("Wapas aana chart se?", "return_india"),
    C("Return home India chart?", "return_india"),
    # travel_obstacles
    C("Videsh me delay hai kya?", "travel_obstacles"),
    C("Travel obstacle chart me?", "travel_obstacles"),
    C("Abroad delay chart se?", "travel_obstacles"),
    C("Foreign travel block?", "travel_obstacles"),
    C("Settlement delay chart?", "travel_obstacles"),
    C("Videsh rukawat chart?", "travel_obstacles"),
    C("Travel problem abroad?", "travel_obstacles"),
    C("Visa obstacle chart?", "travel_obstacles"),
    C("Foreign travel ruka?", "travel_obstacles"),
    C("Abroad me dikkat chart?", "travel_obstacles"),
    C("Passport delay chart?", "passport_travel"),
    C("Travel block chart se?", "travel_obstacles"),
    # short_travel
    C("Foreign trip possible hai?", "short_travel"),
    C("Abroad vacation chart?", "short_travel"),
    C("Videsh ghumne ja sakta hoon?", "short_travel"),
    C("Holiday abroad chart?", "short_travel"),
    C("Short trip abroad?", "short_travel"),
    C("Foreign tour possible?", "short_travel"),
    C("Abroad trip chart se?", "short_travel"),
    C("Tourist trip abroad?", "short_travel"),
    C("Leisure travel abroad?", "short_travel"),
    C("Foreign visit chart?", "short_travel"),
    C("Vacation overseas chart?", "short_travel"),
    C("Abroad ghumna chart?", "short_travel"),
    # pilgrimage_travel
    C("Teerth yatra hogi kya?", "pilgrimage_travel", r"9th|Jupiter|pilgrimage|teerth|D9"),
    C("Pilgrimage abroad chart?", "pilgrimage_travel", r"9th|Jupiter|pilgrimage|D9"),
    C("Dharma yatra chart se?", "pilgrimage_travel", r"9th|Jupiter|dharma|D9"),
    C("Hajj possible chart?", "pilgrimage_travel", r"9th|Jupiter|hajj|D9"),
    C("Umrah chart se?", "pilgrimage_travel", r"9th|Jupiter|umrah|D9"),
    C("Sacred journey chart?", "pilgrimage_travel", r"9th|Jupiter|sacred|D9"),
    C("Religious travel chart?", "pilgrimage_travel", r"9th|Jupiter|religious|D9"),
    C("Tirth yatra chart?", "pilgrimage_travel", r"9th|Jupiter|tirth|D9"),
    C("Mandir yatra abroad?", "pilgrimage_travel", r"9th|Jupiter|mandir|D9"),
    C("Char dham yatra chart?", "pilgrimage_travel", r"9th|Jupiter|dham|D9"),
    # passport_travel
    C("Passport milega chart se?", "passport_travel"),
    C("Travel capacity chart?", "passport_travel"),
    C("Passport problem chart?", "passport_travel"),
    C("Foreign travel capacity?", "passport_travel"),
    C("Passport delay chart se?", "passport_travel"),
    C("Travel desire chart?", "passport_travel"),
    C("Abroad travel capacity chart?", "passport_travel"),
    C("Passport renew chart?", "passport_travel"),
    C("Passport issue chart tone?", "passport_travel"),
    C("Travel readiness passport?", "passport_travel"),
    # immigration
    C("Green card possible hai?", "immigration", r"immigration|12th|Saturn|PR|D9"),
    C("PR file karna chart se?", "immigration", r"immigration|12th|Saturn|PR|D9"),
    C("Immigration case chart?", "immigration", r"immigration|12th|Saturn|D9"),
    C("Citizenship abroad chart?", "immigration", r"immigration|citizenship|12th|D9"),
    C("Migration file chart?", "immigration", r"immigration|migration|12th|D9"),
    C("Express entry chart?", "immigration", r"immigration|12th|Saturn|D9"),
    C("Permanent residency chart?", "immigration", r"immigration|residen|12th|D9"),
    C("Immigration process chart?", "immigration", r"immigration|12th|Saturn|D9"),
    C("Green card file chart?", "immigration", r"immigration|green|12th|D9"),
    C("PR status chart se?", "immigration", r"immigration|PR|12th|D9"),
    # business_travel
    C("Business trip abroad chart?", "business_travel"),
    C("Official travel abroad?", "business_travel"),
    C("Corporate travel abroad chart?", "business_travel"),
    C("Work trip abroad non job?", "business_travel"),
    C("Foreign business travel?", "business_travel"),
    C("Official trip videsh chart?", "business_travel"),
    C("Business travel overseas?", "business_travel"),
    C("Corporate trip abroad?", "business_travel"),
    # travel_risk
    C("Foreign travel risk chart?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Abroad accident risk?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Travel danger abroad chart?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Unsafe abroad travel?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Videsh me khatra chart?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Accident abroad chart?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Foreign travel unsafe?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    C("Travel risk overseas?", "travel_risk", r"risk|Mars|Rahu|9th|12th|D9"),
    # travel_country_fit (kaun sa desh / country direction)
    C("Kaun sa desh jaaunga?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Konsa country milega chart se?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Which country will I go?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("USA ya Canada kaun sa better?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("UK ya Australia better chart?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Kaun si country suit karegi?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Videsh me kaun sa desh?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Foreign country fit chart?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Kis desh me jaunga chart se?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Canada ya USA jaa sakta hoon?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Dubai ya Europe better chart?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Kaun se desh me shift hoga?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Best country to settle chart?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Overseas country choose chart?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Germany ya UK kaun sa desh?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Konsa mulk milega videsh me?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("America ya Canada chart fit?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Kaun sa country possible hai?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    C("Desh kaun sa hoga chart se?", "travel_country_fit", r"country|Country-fit|9th|12H|Rahu|D9"),
    # extra real-user phrasing (mixed)
    C("Videsh yatra ka yog hai?", "travel_yog"),
    C("Foreign settlement ke yog hain?", "foreign_settlement"),
    C("H1B visa approve hoga?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Shift to Dubai possible chart?", "relocation_abroad"),
    C("Settle in USA chart se?", "foreign_settlement"),
    C("Settle in UK possible hai?", "foreign_settlement"),
    C("Australia me bas sakta hoon?", "foreign_settlement"),
    C("PR Canada file chart?", "immigration", r"immigration|12th|Saturn|D9"),
    C("Citizenship USA chart tone?", "immigration", r"immigration|citizenship|12th|D9"),
    C("Videsh ghumne ka plan chart?", "short_travel"),
    C("Foreign travel safe hai?", "travel_risk", r"risk|safe|Rahu|9th|12th|D9"),
    C("NRI ban sakta hoon chart se?", "foreign_settlement"),
    C("Overseas shift theme chart?", "relocation_abroad"),
    C("Flight abroad possible chart?", "short_travel"),
    C("Airport se videsh jana chart?", "travel_yog"),
    C("Migration abroad chart reading?", "immigration", r"immigration|12th|Saturn|D9"),
    C("Work permit visa chart?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Tourist visa USA chart?", "visa_theme", r"visa|Jupiter|9th|12th|D9"),
    C("Videsh me rukawat kyu chart?", "travel_obstacles"),
    C("Foreign travel block kyu?", "travel_obstacles"),
    # general_travel
    C("Meri videsh yatra overall kaisi?", "general_travel"),
    C("Foreign travel chart reading?", "general_travel"),
    C("Abroad theme chart me?", "general_travel"),
    C("Videsh overall chart?", "general_travel"),
    C("Travel reading overall?", "general_travel"),
    C("Foreign lands chart summary?", "general_travel"),
    C("Overseas chart reading?", "general_travel"),
    C("Videsh topic chart analysis?", "general_travel"),
    C("9th house travel reading?", "general_travel", r"9th|9H|12th|12H|D9|Rahu"),
    C("12th house foreign reading?", "general_travel", r"9th|9H|12th|12H|D9|Rahu"),
    # negatives timing
    TIMING("Videsh kab jaunga?"),
    TIMING("Visa kab milega?"),
    TIMING("Abroad kab shift karunga?"),
    TIMING("Foreign travel kab hoga?"),
    TIMING("Settle abroad kab hoga?"),
    TIMING("Passport kab milega?"),
    TIMING("When will I go abroad?"),
    TIMING("Travel timing dasha se?"),
    TIMING("Flight kab book karu muhurat?"),
    TIMING("Immigration kab hogi?"),
    TIMING("PR kab milega dasha?"),
    TIMING("Abroad shift kab sahi?"),
    # negatives education
    EDU("Study abroad possible hai IELTS ke baad?"),
    EDU("Masters abroad chart se?"),
    EDU("Foreign university admission?"),
    EDU("Student visa for study abroad?"),
    EDU("GRE ke baad videsh padhai?"),
    EDU("PhD abroad possible chart?"),
    EDU("Higher studies videsh me?"),
    EDU("Abroad study chart reading?"),
    EDU("Foreign degree possible?"),
    EDU("Videsh me padhai chart?"),
    # negatives career
    CAREER("Foreign job milega chart se?"),
    CAREER("Abroad naukri possible hai?"),
    CAREER("Videsh me kaam chart se?"),
    CAREER("Foreign company job chart?"),
    CAREER("MNC abroad job possible?"),
    CAREER("Software job abroad chart?"),
    CAREER("IT job videsh me?"),
    CAREER("Work abroad career chart?"),
    CAREER("Foreign career possible?"),
    CAREER("Abroad salary job chart?"),
    # negatives MR
    MR("Shaadi ke baad abroad settle?"),
    MR("Spouse ke saath videsh basna?"),
    MR("Partner abroad settlement after marriage?"),
    MR("Patni ke saath foreign shift?"),
    MR("Husband abroad settle chart?"),
    MR("Wife ke saath videsh shift?"),
    MR("Marriage ke baad abroad life?"),
    MR("Spouse foreign settle chart?"),
    # negatives off
    OFF("Ghar kab milega?"),
    OFF("Santan hogi kya?"),
    OFF("Promotion milegi?"),
    OFF("Business profit hoga?"),
    OFF("Health theek rahegi?"),
    OFF("Love marriage hogi?"),
    OFF("Property yog hai?"),
    OFF("Salary kitni hogi?"),
    OFF("Exam pass ho jayega?"),
    OFF("Partner loyal hai?"),
]


def _hit(text: str, rx: str) -> bool:
    if not rx:
        return True
    return bool(re.search(rx, (text or "").lower(), re.I))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    gaps: list[str] = []
    total = len(CASES)
    scope_ok = route_ok = engine_ok = ev_ok = 0

    print(f"TRAVEL FULL AUDIT — {total} cases (D9 evidence required)\n" + "=" * 72)

    for c in CASES:
        q = c.q
        is_trv = is_travel_static_question(q)
        is_edu = is_education_study_abroad_question(q)
        is_car = is_career_job_abroad_question(q)
        is_mr = is_mr_settle_abroad_question(q)
        arch = classify_travel_archetype(q)
        detected = detect_travel_archetype(q)

        if c.domain == "travel":
            scope_hit = is_trv and not is_edu and not is_car and not is_mr
            route_hit = arch == c.engine and (detected == c.engine or arch == c.engine)
            if scope_hit:
                scope_ok += 1
            if route_hit:
                route_ok += 1
            try:
                res = run_travel_static_engine(K, q, archetype=arch)
                eng_hit = res.archetype == c.engine
                if eng_hit:
                    engine_ok += 1
                ev_blob = " ".join(res.evidence or []) + " " + (res.verdict or "")
                ev_hit = len(res.evidence or []) >= c.min_evidence and _hit(ev_blob, c.focus_rx)
                if ev_hit:
                    ev_ok += 1
            except Exception as exc:
                eng_hit = ev_hit = False
                gaps.append(f"ENGINE_ERR | {q} | {exc}")

            ok = scope_hit and route_hit and eng_hit and ev_hit
            if not ok:
                gaps.append(
                    f"{c.engine} | {q[:55]} | scope={is_trv} edu={is_edu} car={is_car} mr={is_mr} "
                    f"arch={arch} det={detected} exp={c.engine} ev={ev_hit}"
                )
            tag = "OK" if ok else "GAP"
            print(f"  [{tag}] {q[:52]:<52} -> {arch}")

        elif c.domain == "timing":
            ok = not is_trv
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"TIMING | {q} | should NOT be travel static")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} trv={is_trv}")

        elif c.domain == "education":
            ok = not is_trv and is_edu
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"EDU | {q} | trv={is_trv} edu={is_edu}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} trv={is_trv} edu={is_edu}")

        elif c.domain == "career":
            ok = not is_trv and is_car
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"CAREER | {q} | trv={is_trv} car={is_car}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} trv={is_trv} car={is_car}")

        elif c.domain == "mr":
            ok = not is_trv and is_mr
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"MR | {q} | trv={is_trv} mr={is_mr}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} trv={is_trv} mr={is_mr}")

        else:
            ok = not is_trv
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"OFF | {q} | trv={is_trv}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} trv={is_trv}")

    print("\n" + "=" * 72)
    print(
        f"TOTAL={total} SCOPE={scope_ok}/{total} ROUTE={route_ok}/{total} "
        f"ENGINE={engine_ok}/{total} EVIDENCE={ev_ok}/{total} GAPS={len(gaps)}"
    )
    for g in gaps[:80]:
        print(f"  GAP: {g}")
    if len(gaps) > 80:
        print(f"  ... and {len(gaps) - 80} more")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
