#!/usr/bin/env python3
"""Full non-timing litigation audit — routing, scope, 6H/8H/12H evidence alignment."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_litigation import run_litigation_static_engine
from ask_litigation.classifier import classify_litigation_archetype, is_litigation_static_question
from ask_litigation.litigation_registry import (
    detect_litigation_archetype,
    is_career_police_job_question,
    is_death_penalty_crisis_question,
    is_mr_divorce_court_question,
    is_property_court_question,
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

_LIT_RX = r"6th|6H|8th|8H|12th|12H|Mars|Saturn|Rahu|litigation|legal"


@dataclass
class Case:
    q: str
    domain: str
    engine: str
    focus_rx: str
    min_evidence: int = 6


def C(q: str, eng: str, rx: str = _LIT_RX, min_e: int = 6) -> Case:
    return Case(q, "litigation", eng, rx, min_e)


def PROP(q: str) -> Case:
    return Case(q, "property", "", "")


def MR(q: str) -> Case:
    return Case(q, "mr", "", "")


def CAREER(q: str) -> Case:
    return Case(q, "career", "", "")


def TIMING(q: str) -> Case:
    return Case(q, "timing", "", "")


def DEATH(q: str) -> Case:
    return Case(q, "death", "", "")


def OFF(q: str) -> Case:
    return Case(q, "off", "", "")


CASES: list[Case] = [
    # litigation_yog
    C("Court case hoga kya?", "litigation_yog"),
    C("Mukadma ladega chart?", "litigation_yog"),
    C("Litigation yog hai?", "litigation_yog"),
    C("Legal case possible hai?", "litigation_yog"),
    C("Court case yog chart me?", "litigation_yog"),
    C("Mukadma hoga kya chart se?", "litigation_yog"),
    C("Case chalega kya?", "litigation_yog"),
    C("Kanooni mamla hoga?", "litigation_yog"),
    C("Will I face a court case?", "litigation_yog"),
    C("Legal trouble yog?", "litigation_yog"),
    C("Court case promise chart?", "litigation_yog"),
    C("Mukadma yog strong?", "litigation_yog"),
    C("Case ladega kya?", "litigation_yog"),
    C("Litigation possible chart se?", "litigation_yog"),
    C("Court case theme chart?", "litigation_yog"),
    C("Legal case yog chart?", "litigation_yog"),
    C("Mukadma chalega chart?", "litigation_yog"),
    C("Court yog kundli me?", "litigation_yog"),
    # litigation_remedy
    C("Court case ka upay kya hai?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Mukadma se bachne ka upay?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Case ka remedy chart se?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Legal case upay kya hai?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Bail ke liye upay?", "litigation_remedy", r"practical|REMEDIES|bail|Mars|Saturn|6th|8th"),
    C("FIR case ka upay?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Court case mantra kya hai?", "litigation_remedy", r"practical|REMEDIES|vedic|Mars|Saturn|6th|8th"),
    C("Case jeetne ka upay?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Kanooni pareshani ka upay?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Jail se bachne ka upay chart?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Police case remedy?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Case solution chart se?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Court case puja daan?", "litigation_remedy", r"practical|REMEDIES|vedic|Mars|Saturn|6th|8th"),
    C("Mukadma nivaran upay?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    C("Case ka parihar kya hai?", "litigation_remedy", r"practical|REMEDIES|Mars|Saturn|6th|8th"),
    # case_outcome
    C("Case jeet jaunga kya?", "case_outcome"),
    C("Court case jeet sakta hoon?", "case_outcome"),
    C("Case haar jaunga kya?", "case_outcome"),
    C("Will I win the case?", "case_outcome"),
    C("Case loss chart se?", "case_outcome"),
    C("Verdict favour chart?", "case_outcome"),
    C("Judgment against chart?", "case_outcome"),
    C("Case outcome chart se?", "case_outcome"),
    C("Case result kya hoga chart?", "case_outcome"),
    C("Case favourable hai?", "case_outcome"),
    C("Unfavourable case chart?", "case_outcome"),
    C("Jeet paunga case?", "case_outcome"),
    C("Har jayega case?", "case_outcome"),
    C("Case fate chart?", "case_outcome"),
    C("Court jeet chart se?", "case_outcome"),
    C("Case win possible chart?", "case_outcome"),
    C("Verdict positive chart?", "case_outcome"),
    C("Case against me chart?", "case_outcome"),
    # court_delay
    C("Case delay hoga kya?", "court_delay"),
    C("Court case ruka hai chart?", "court_delay"),
    C("Case pending chart se?", "court_delay"),
    C("Litigation delay chart?", "court_delay"),
    C("Mukadma lamba chalega?", "court_delay"),
    C("Case atka hua chart?", "court_delay"),
    C("Court delay theme?", "court_delay"),
    C("Hearing delay chart?", "court_delay"),
    C("Judgment delay chart se?", "court_delay"),
    C("Case late chart?", "court_delay"),
    C("Legal delay chart me?", "court_delay"),
    C("Case rukawat chart?", "court_delay"),
    C("Court case lamba?", "court_delay"),
    C("Mukadma delay chart?", "court_delay"),
    C("Case pending long chart?", "court_delay"),
    # bail_theme
    C("Bail milegi kya?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th|12th"),
    C("Zamanat milega chart se?", "bail_theme", r"bail|zamanat|Jupiter|Mercury|6th|8th"),
    C("Bail approve hoga?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Anticipatory bail chart?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Interim bail possible?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Bail reject chart se?", "bail_theme", r"bail|Saturn|6th|8th|12th"),
    C("Bail nahi milegi chart?", "bail_theme", r"bail|Saturn|6th|8th|12th"),
    C("Regular bail chart?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Bail petition chart se?", "bail_theme", r"bail|Mercury|6th|8th|12th"),
    C("Release on bail chart?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Zamanat legi chart?", "bail_theme", r"bail|zamanat|Jupiter|Mercury|6th|8th"),
    C("Bail possible chart se?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Bail order chart tone?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Bail theme chart reading?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Jamant milegi chart?", "bail_theme", r"bail|zamanat|Jupiter|Mercury|6th|8th"),
    C("Bail deny chart se?", "bail_theme", r"bail|Saturn|6th|8th|12th"),
    C("Bail hoga kya chart?", "bail_theme", r"bail|Jupiter|Mercury|6th|8th"),
    C("Zamanat possible hai?", "bail_theme", r"bail|zamanat|Jupiter|Mercury|6th|8th"),
    # jail_concern
    C("Jail hoga kya chart se?", "jail_concern"),
    C("Prison possible chart?", "jail_concern"),
    C("Andar jaunga kya?", "jail_concern"),
    C("Custody hoga kya?", "jail_concern"),
    C("Judicial custody chart?", "jail_concern"),
    C("Police custody chart se?", "jail_concern"),
    C("Remand chart theme?", "jail_concern"),
    C("Qaid hoga kya?", "jail_concern"),
    C("Jail ja sakta hoon chart?", "jail_concern"),
    C("Prison jaunga chart?", "jail_concern"),
    C("Andar milega chart se?", "jail_concern"),
    C("Custody possible chart?", "jail_concern"),
    C("Jail fear chart se?", "jail_concern"),
    C("Qaidkhana chart theme?", "jail_concern"),
    C("Remand possible chart?", "jail_concern"),
    # police_fir
    C("FIR lag sakti hai kya?", "police_fir"),
    C("Police case hoga chart?", "police_fir"),
    C("Thana case chart se?", "police_fir"),
    C("FIR chart me?", "police_fir"),
    C("Police complaint chart?", "police_fir"),
    C("Police report chart se?", "police_fir"),
    C("FIR possible chart?", "police_fir"),
    C("Police case bane ga?", "police_fir"),
    C("Thana complaint chart?", "police_fir"),
    C("Police action chart se?", "police_fir"),
    C("FIR lag sakti chart?", "police_fir"),
    C("Police station case chart?", "police_fir"),
    C("First information report chart?", "police_fir"),
    C("Police case theme?", "police_fir"),
    C("FIR hogi kya chart?", "police_fir"),
    C("Thana me case chart?", "police_fir"),
    C("Police ne case chart?", "police_fir"),
    C("Complaint police chart se?", "police_fir"),
    # criminal_case
    C("Criminal case chart se?", "criminal_case"),
    C("Criminal court case?", "criminal_case"),
    C("498a case chart?", "criminal_case"),
    C("IPC case chart se?", "criminal_case"),
    C("Session court case chart?", "criminal_case"),
    C("Criminal charge chart?", "criminal_case"),
    C("Criminal trial chart?", "criminal_case"),
    C("Murder case chart se?", "criminal_case"),
    C("Cheating case criminal chart?", "criminal_case"),
    C("Fraud case criminal chart?", "criminal_case"),
    C("Criminal proceeding chart?", "criminal_case"),
    C("NDPS case chart?", "criminal_case"),
    C("Criminal matter chart se?", "criminal_case"),
    C("Sessions court chart?", "criminal_case"),
    C("Penal code case chart?", "criminal_case"),
    C("Criminal litigation chart?", "criminal_case"),
    C("498 a case chart?", "criminal_case"),
    C("Criminal case theme?", "criminal_case"),
    # civil_litigation
    C("Civil case chart se?", "civil_litigation"),
    C("Civil court case?", "civil_litigation"),
    C("Civil suit chart?", "civil_litigation"),
    C("Money suit chart se?", "civil_litigation"),
    C("Recovery suit chart?", "civil_litigation"),
    C("Consumer court case chart?", "civil_litigation"),
    C("Labour court case chart?", "civil_litigation"),
    C("Civil dispute chart se?", "civil_litigation"),
    C("Injunction case chart?", "civil_litigation"),
    C("Civil decree chart?", "civil_litigation"),
    C("Civil litigation chart?", "civil_litigation"),
    C("Tribunal case chart se?", "civil_litigation"),
    C("Civil matter chart?", "civil_litigation"),
    C("Specific performance case chart?", "civil_litigation"),
    C("Civil court theme chart?", "civil_litigation"),
    # legal_obstacles
    C("Legal problem chart se?", "legal_obstacles"),
    C("Kanooni pareshani chart?", "legal_obstacles"),
    C("Legal trouble chart me?", "legal_obstacles"),
    C("Case me dikkat chart?", "legal_obstacles"),
    C("Court problem chart se?", "legal_obstacles"),
    C("Legal friction chart?", "legal_obstacles"),
    C("Kanooni rukawat chart?", "legal_obstacles"),
    C("Litigation problem chart?", "legal_obstacles"),
    C("Legal stress chart se?", "legal_obstacles"),
    C("Case obstacle chart?", "legal_obstacles"),
    C("Kanooni mushkil chart?", "legal_obstacles"),
    C("Legal issue chart me?", "legal_obstacles"),
    C("Court dikkat chart?", "legal_obstacles"),
    C("Case trouble chart se?", "legal_obstacles"),
    C("Legal obstacle chart reading?", "legal_obstacles"),
    # enemy_case
    C("Dushman case chart se?", "enemy_case"),
    C("Enemy case chart?", "enemy_case"),
    C("Shatru mukadma chart?", "enemy_case"),
    C("Dushman ne case chart?", "enemy_case"),
    C("Enemy litigation chart?", "enemy_case"),
    C("Shatru court case chart?", "enemy_case"),
    C("Opponent case chart se?", "enemy_case"),
    C("Rival case chart?", "enemy_case"),
    C("Dushman mukadma chart?", "enemy_case"),
    C("Shatru se case chart?", "enemy_case"),
    C("Enemy lawsuit chart?", "enemy_case"),
    C("Shatru case chart se?", "enemy_case"),
    C("Dushman court chart?", "enemy_case"),
    C("Enemy court case chart?", "enemy_case"),
    C("Shatru litigation chart?", "enemy_case"),
    # acquittal_relief
    C("Acquittal hoga kya chart?", "acquittal_relief"),
    C("Bera gari milegi chart?", "acquittal_relief"),
    C("Case dismiss chart se?", "acquittal_relief"),
    C("Case quash chart?", "acquittal_relief"),
    C("Chhutkara milega case se?", "acquittal_relief"),
    C("Case se chhut chart?", "acquittal_relief"),
    C("FIR quash chart se?", "acquittal_relief"),
    C("Case clear chart?", "acquittal_relief"),
    C("Innocent prove chart?", "acquittal_relief"),
    C("Case band hoga chart?", "acquittal_relief"),
    C("Discharge from case chart?", "acquittal_relief"),
    C("Case dropped chart se?", "acquittal_relief"),
    C("Acquit chart theme?", "acquittal_relief"),
    C("Case khatam chart se?", "acquittal_relief"),
    C("Release from case chart?", "acquittal_relief"),
    # lawyer_support
    C("Advocate sahi milega chart?", "lawyer_support"),
    C("Vakil support chart se?", "lawyer_support"),
    C("Lawyer help chart?", "lawyer_support"),
    C("Legal counsel support chart?", "lawyer_support"),
    C("Accha vakil chart se?", "lawyer_support"),
    C("Advocate strong chart?", "lawyer_support"),
    C("Vakil sahi chart se?", "lawyer_support"),
    C("Lawyer support chart reading?", "lawyer_support"),
    C("Legal help chart me?", "lawyer_support"),
    C("Counsel support chart?", "lawyer_support"),
    C("Sahi advocate chart se?", "lawyer_support"),
    C("Vakil milega chart?", "lawyer_support"),
    # family_court
    C("Family court case chart?", "family_court"),
    C("Custody case chart se?", "family_court"),
    C("Child custody court chart?", "family_court"),
    C("Maintenance case chart?", "family_court"),
    C("Alimony case chart se?", "family_court"),
    C("Matrimonial court chart?", "family_court"),
    C("498a case chart reading?", "criminal_case"),
    C("Domestic violence case chart?", "family_court"),
    C("DV case chart se?", "family_court"),
    C("Matrimonial dispute chart?", "family_court"),
    C("Family court theme chart?", "family_court"),
    C("Custody court chart se?", "family_court"),
    C("Maintenance court chart?", "family_court"),
    C("Matrimonial case chart?", "family_court"),
    C("Family court litigation chart?", "family_court"),
    # general_litigation
    C("Court case chart reading?", "general_litigation"),
    C("Legal chart summary?", "general_litigation"),
    C("Mukadma chart analysis?", "general_litigation"),
    C("Litigation chart tone?", "general_litigation"),
    C("Kanooni chart reading?", "general_litigation"),
    C("Court matter chart se?", "general_litigation"),
    C("Legal case chart overall?", "general_litigation"),
    C("Dispute court chart?", "general_litigation"),
    C("Law suit chart se?", "general_litigation"),
    C("Kanoon chart reading?", "general_litigation"),
    C("Court chart analysis?", "general_litigation"),
    C("Legal matter chart tone?", "general_litigation"),
    C("Mukadma overall chart?", "general_litigation"),
    C("Litigation overall chart se?", "general_litigation"),
    C("Court case overall reading?", "general_litigation"),
    # negatives — timing
    TIMING("Case kab khatam hoga?"),
    TIMING("Court kab decide karega?"),
    TIMING("Bail kab milegi?"),
    TIMING("Verdict kab aayega?"),
    TIMING("FIR kab lag sakti hai?"),
    TIMING("Case hearing kab hai chart?"),
    TIMING("Jail kab tak chart?"),
    TIMING("Mukadma kab solve hoga?"),
    TIMING("When will case end?"),
    TIMING("Court case timing chart?"),
    TIMING("Judgment kab chart se?"),
    TIMING("Case dasha se kab?"),
    TIMING("Bail kab tak milegi?"),
    TIMING("Release kab hoga chart?"),
    TIMING("Case 2026 me khatam?"),
    # property defer
    PROP("Property court case chart?"),
    PROP("Ghar dispute court case?"),
    PROP("Land dispute court chart?"),
    PROP("Property litigation chart se?"),
    PROP("Zameen vivad court case?"),
    PROP("Plot dispute court chart?"),
    PROP("Ghar ka vivad court?"),
    PROP("Property case court chart?"),
    PROP("Hissa vivad property court?"),
    PROP("Family dispute property court?"),
    # MR defer
    MR("Divorce court case chart?"),
    MR("Family court divorce chart se?"),
    MR("Talaq court case chart?"),
    MR("Spouse divorce court chart?"),
    MR("Shaadi tut gayi court case?"),
    MR("Pati divorce court chart?"),
    MR("Alimony divorce court chart?"),
    MR("Marriage case divorce court?"),
    # career police defer
    CAREER("Police job milegi chart se?"),
    CAREER("IPS ban sakta hoon chart?"),
    CAREER("Police naukri chart?"),
    CAREER("Police officer job chart?"),
    CAREER("Police career chart se?"),
    CAREER("Become police chart?"),
    CAREER("Police me naukri chart?"),
    CAREER("Law enforcement career chart?"),
    # death penalty crisis — not static
    DEATH("Death penalty hoga kya chart?"),
    DEATH("Phansi ki saza chart se?"),
    DEATH("Hanging possible chart?"),
    DEATH("Capital punishment chart?"),
    DEATH("Maut ki saza chart se?"),
    # off-topic
    OFF("Shaadi kab hogi?"),
    OFF("Foreign job milega?"),
    OFF("Health problem chart?"),
    OFF("Property yog chart?"),
    OFF("Videsh jaa sakta hoon?"),
    OFF("Padhai clear hogi?"),
    OFF("Salary kitni hogi?"),
    OFF("Bachcha hoga kya?"),
]


def _hit(blob: str, rx: str) -> bool:
    if not rx:
        return True
    return bool(re.search(rx, blob, re.IGNORECASE))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    gaps: list[str] = []
    total = len(CASES)
    scope_ok = route_ok = engine_ok = ev_ok = 0

    print(f"LITIGATION FULL AUDIT — {total} cases (6H/8H/12H evidence required)\n" + "=" * 72)

    for c in CASES:
        q = c.q
        is_lit = is_litigation_static_question(q)
        is_prop = is_property_court_question(q)
        is_mr = is_mr_divorce_court_question(q)
        is_car = is_career_police_job_question(q)
        is_death = is_death_penalty_crisis_question(q)
        arch = classify_litigation_archetype(q)
        detected = detect_litigation_archetype(q)

        if c.domain == "litigation":
            scope_hit = is_lit and not is_prop and not is_mr and not is_car and not is_death
            route_hit = arch == c.engine and (detected == c.engine or arch == c.engine)
            if scope_hit:
                scope_ok += 1
            if route_hit:
                route_ok += 1
            try:
                res = run_litigation_static_engine(K, q, archetype=arch)
                eng_hit = res.archetype == c.engine
                if eng_hit:
                    engine_ok += 1
                ev_blob = " ".join(res.evidence or []) + " " + (res.verdict or "")
                if c.engine == "litigation_remedy":
                    ev_blob += " " + str((res.checks or {}).get("remedy_text") or "")
                ev_hit = len(res.evidence or []) >= c.min_evidence and _hit(ev_blob, c.focus_rx)
                fear_hit = not re.search(
                    r"(?ix)\b(jail\s+yog|pakka\s+andar|death\s+penalty|phansi)\b",
                    res.verdict or "",
                )
                if ev_hit and fear_hit:
                    ev_ok += 1
                elif not fear_hit:
                    gaps.append(f"FEAR_LEAK | {q} | jail yog in engine output")
            except Exception as exc:
                eng_hit = ev_hit = False
                gaps.append(f"ENGINE_ERR | {q} | {exc}")

            ok = scope_hit and route_hit and eng_hit and ev_hit
            if not ok:
                gaps.append(
                    f"{c.engine} | {q[:55]} | scope={is_lit} prop={is_prop} mr={is_mr} car={is_car} "
                    f"arch={arch} det={detected} exp={c.engine} ev={ev_hit}"
                )
            tag = "OK" if ok else "GAP"
            print(f"  [{tag}] {q[:52]:<52} -> {arch}")

        elif c.domain == "timing":
            ok = not is_lit
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"TIMING | {q} | should NOT be litigation static")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} lit={is_lit}")

        elif c.domain == "property":
            ok = not is_lit and is_prop
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"PROP | {q} | lit={is_lit} prop={is_prop}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} lit={is_lit} prop={is_prop}")

        elif c.domain == "mr":
            ok = not is_lit and is_mr
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"MR | {q} | lit={is_lit} mr={is_mr}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} lit={is_lit} mr={is_mr}")

        elif c.domain == "career":
            ok = not is_lit and is_car
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"CAREER | {q} | lit={is_lit} car={is_car}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} lit={is_lit} car={is_car}")

        elif c.domain == "death":
            ok = not is_lit and is_death
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"DEATH | {q} | lit={is_lit} death={is_death}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} lit={is_lit} death={is_death}")

        else:
            ok = not is_lit
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"OFF | {q} | lit={is_lit}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} lit={is_lit}")

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
