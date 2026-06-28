#!/usr/bin/env python3
"""Full non-timing children/progeny audit — routing, scope, evidence alignment."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_children import run_children_static_engine
from ask_children.classifier import classify_children_archetype, is_children_static_question
from ask_children.children_registry import detect_children_archetype, is_mr_spouse_children_question
from ask_health.classifier import is_health_static_question

K = {
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


@dataclass
class Case:
    q: str
    domain: str  # children | health | mr | timing | off
    engine: str
    focus_rx: str
    min_evidence: int = 4


def C(q: str, eng: str, rx: str, min_e: int = 4) -> Case:
    return Case(q, "children", eng, rx, min_e)


def HEALTH(q: str) -> Case:
    return Case(q, "health", "", "")


def MR(q: str) -> Case:
    return Case(q, "mr", "", "")


def TIMING(q: str) -> Case:
    return Case(q, "timing", "", "")


def OFF(q: str) -> Case:
    return Case(q, "off", "", "")


CASES: list[Case] = [
    # ── child_promise ──
    C("Kya mujhe santan hogi?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Santan yog hai kya?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Putra prapti ke yog hain?", "child_promise", r"promise|5th|Jupiter|putra|progeny"),
    C("Will I have a child?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Bachche honge kya?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Santaan milegi kya?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Aulad hogi kya?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Baby possible hai chart me?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Child possible hai kya?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Santan prapti hogi?", "child_promise", r"promise|5th|Jupiter|putra|progeny"),
    C("Putra prapti possible hai?", "child_promise", r"promise|5th|Jupiter|putra|progeny"),
    C("Kya main maa ban paungi?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Pita ban paunga kya?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Progeny promised hai chart me?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Offspring possible hai?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Santaan ka yog strong hai?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Bachcha hoga ya nahi?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    C("Santan blessing milegi?", "child_promise", r"promise|5th|Jupiter|Moon|progeny"),
    # ── fertility_conception ──
    C("Conceive kar paungi kya?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("IVF successful ho sakta hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Infertility chart kaisa hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Fertility strong hai kya?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Natural conceive possible hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("IUI ke chances chart se?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Conception ke yog hain?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Conceiving possible hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Fertile hoon kya chart ke hisaab se?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("IVF ke liye chart support karta hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Bachcha conceive ho payega?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Child conceive kar paunga?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Ovulation cycle ke saath conceive?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Sterility chart me dikh rahi hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Barren hone ka dar hai kya?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Garbhdharan ki sambhavna hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Baby conceive hoga kya?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    C("Fertility chart ke saath conceive possible hai?", "fertility_conception", r"Fertility|conception|Jupiter|Moon|5th"),
    # ── pregnancy_wellbeing ──
    C("Pregnancy safe rahegi kya?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Good news milegi kya?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Garbh tik sakta hai?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Khushkhabri aayegi kya?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Pregnant hone ke chances?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Garbhwati hone ka yog?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Pregnancy successful hogi?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Garbh safe rahega?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Godbharai ke liye chart kaisa?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Baby shower ke liye chart tone?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Khush khabri pregnancy related?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Garbh theek rahega?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Pregnancy smooth rahegi?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Garbh healthy rahega chart se?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Maternity phase support karega chart?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    C("Pregnant reh paungi safely?", "pregnancy_wellbeing", r"Pregnancy|garbh|Jupiter|Moon|5th"),
    # ── child_delay ──
    C("Santan me delay hai kya?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Late motherhood chart me?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Late fatherhood dikh raha hai?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Delay in children chart me?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Bachche me delay hai?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Santan der se milegi?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Putra prapti der se hogi?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Der se santan hogi kya?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Late child possible hai?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Child delay real hai chart me?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Progeny delay tone strong hai?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Santaan der se prapt hogi?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Bachcha late aayega?", "child_delay", r"delay|Saturn|5th|progeny"),
    C("Delay in progeny chart se?", "child_delay", r"delay|Saturn|5th|progeny"),
    # ── child_gender_note ──
    C("Ladka ya ladki hoga?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Beta ya beti hogi?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Boy or girl from chart?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Gender of child kya hoga?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Pehla beta hoga ya beti?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Bachcha ladka hoga kya?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Ladki hogi ya ladka?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Girl or boy prediction?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Pehla ladka milega?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Pehli beti hogi?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Bachche ka gender kya hoga?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Putra hoga ya putri?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Baby boy ya girl chart se?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    C("Gender prediction possible hai?", "child_gender_note", r"Gender|uncertain|5th|Jupiter"),
    # ── number_of_children ──
    C("Kitne bachche honge?", "number_of_children", r"Count|5th|11th|progeny"),
    C("How many children will I have?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Twins possible hain kya?", "number_of_children", r"Count|5th|11th|progeny|twin"),
    C("Jodwa bachche honge?", "number_of_children", r"Count|5th|11th|progeny|twin"),
    C("First child ke baad second?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Second child possible hai?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Third child hoga kya?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Teesra bachcha hoga?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Ek bachcha ya do?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Do bachche honge kya?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Teen bachche possible?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Number of children chart se?", "number_of_children", r"Count|5th|11th|progeny"),
    C("Twin pregnancy possible?", "number_of_children", r"Count|5th|11th|progeny|twin"),
    C("Judwa bachche ke yog?", "number_of_children", r"Count|5th|11th|progeny|twin"),
    # ── child_nature ──
    C("Mera bachcha kaisa nature ka hoga?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Child personality chart se?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Bachche ka swabhav kaisa hoga?", "child_nature", r"Mercury|Venus|swabhav|5th"),
    C("Child character kaisa rahega?", "child_nature", r"Mercury|Venus|character|5th"),
    C("Kids nature strong hai?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Bachche ka character chart me?", "child_nature", r"Mercury|Venus|character|5th"),
    C("Child temperament kaisa?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Mera beta kaisa type ka hoga?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Meri beti ka nature?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Child's nature from 5th house?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Bachche ka personality type?", "child_nature", r"Mercury|Venus|personality|5th"),
    C("Kids character strong hai?", "child_nature", r"Mercury|Venus|character|5th"),
    C("Bachcha sharmila hoga ya bold?", "child_nature", r"Mercury|Venus|nature|5th"),
    C("Child nature soft ya strict?", "child_nature", r"Mercury|Venus|nature|5th"),
    # ── parent_child_bond ──
    C("Bachche se mera rishta kaisa rahega?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Parent child bond strong hoga?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Bachchon se pyaar milega?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Connection with my children?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Mera bachcha mujhse close rahega?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Bacchon se rishta achha rahega?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Bond with child strong hai?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Bachche se emotional connect?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Parent-child bond chart me?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Bachchon ke saath closeness?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Meri beti se rishta kaisa?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Mere bete se bond?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Kids se attachment strong?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    C("Bachche se connect achha hoga?", "parent_child_bond", r"bond|Moon|Venus|5th"),
    # ── child_success ──
    C("Bachche ki success ka yog?", "child_success", r"future|success|5th|Jupiter"),
    C("Child future bright hoga?", "child_success", r"future|success|5th|Jupiter"),
    C("Mera bachcha successful hoga?", "child_success", r"future|success|5th|Jupiter"),
    C("Child career future kaisa?", "child_success", r"future|success|5th|Jupiter"),
    C("Kids study life kaisi?", "child_success", r"future|success|5th|Jupiter"),
    C("Bachche ki padhai achhi hogi?", "child_success", r"future|success|5th|Jupiter"),
    C("Child life prosperous hogi?", "child_success", r"future|success|5th|Jupiter"),
    C("Bachche ka future strong hai?", "child_success", r"future|success|5th|Jupiter"),
    C("Child study success?", "child_success", r"future|success|5th|Jupiter"),
    C("Meri aulad successful hogi?", "child_success", r"future|success|5th|Jupiter"),
    C("Bachche aage badhenge?", "child_success", r"future|success|5th|Jupiter"),
    C("Kids future secure hai?", "child_success", r"future|success|5th|Jupiter"),
    C("Child future from chart?", "child_success", r"future|success|5th|Jupiter"),
    C("Bachche ki life achhi hogi?", "child_success", r"future|success|5th|Jupiter"),
    # ── adoption_path ──
    C("Adoption possible hai kya?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Surrogacy ke liye chart?", "adoption_path", r"Adoption|Rahu|5th|surrogacy"),
    C("Gode lena sahi rahega?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Adopt kar sakte hain kya?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Surrogate se bachcha?", "adoption_path", r"Adoption|Rahu|5th|surrogacy"),
    C("Foster child possible?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Donor egg se bachcha?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Donor sperm route possible?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Adoption path chart me?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Surrogacy successful ho sakti hai chart se?", "adoption_path", r"Adoption|Rahu|5th|surrogacy"),
    C("Adopted child ke yog?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Non biological child route?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Gode bachcha lena sahi?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    C("Surrogacy ya adoption better?", "adoption_path", r"Adoption|Rahu|5th|Jupiter"),
    # ── child_loss_concern ──
    C("Miscarriage ka dar hai?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Garbhpat ke baad hope hai?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Pregnancy loss fear chart me?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Garbh gir gaya phir chance?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Child loss ke baad santan?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Abort ke baad conceive?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Miscarriage repeat hogi kya?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Garbhpat ka yog hai?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Pregnancy loss ke baad hope?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Bachcha nahi bacha fear?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Garbh safe nahi raha pehle?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Miscarriage chart me dikh raha?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Loss ke baad phir santan?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    C("Garbh loss ke baad chart?", "child_loss_concern", r"loss|Saturn|Ketu|5th|recovery"),
    # ── progeny_obstacles ──
    C("Nisantan dosh hai kya?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Santan nahi ho rahi obstacle kya?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Putra dosh chart me?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Childless hone ka dar?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Santan nahi mil rahi kyun?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Progeny obstacle strong hai?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Barren dosh hai kya?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Nispantan yog hai?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Santaan nahi ho rahi chart se?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Bachcha nahi ho raha obstacle?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Santan obstacle kaise door?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Putra prapti me rukawat?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Childless chart dikhata hai?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    C("Santan me rukawat hai?", "progeny_obstacles", r"obstacle|Saturn|5th|progeny"),
    # ── general_children ──
    C("Meri santan overall kaisi?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Bachche ke baare me chart kya kehta hai?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Children topic chart reading?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("5th house children analysis?", "general_children", r"progeny|5th|Jupiter|Moon|5th house"),
    C("Putra karaka Jupiter kaisa hai?", "general_children", r"progeny|5th|Jupiter|Moon|Jupiter"),
    C("Family planning chart se?", "general_children", r"progeny|5th|Jupiter|Moon|planning"),
    C("Baby planning ke liye chart?", "general_children", r"progeny|5th|Jupiter|Moon|planning"),
    C("Matritva yog chart me?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Paternity support chart me?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Kids ke baare me overall reading?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Santaan theme chart me kaisi?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Progeny overall strong hai?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Bachche ka overall yog?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Children blessing chart se?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Aulad ka overall pattern?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    C("Santan reading overall?", "general_children", r"progeny|5th|Jupiter|Moon|Overall"),
    # ── negative: timing ──
    TIMING("Bachcha kab hoga?"),
    TIMING("Santan kab milegi?"),
    TIMING("Baby kab hoga?"),
    TIMING("Conceive kab kar paungi?"),
    TIMING("Pregnancy kab hogi?"),
    TIMING("Good news kab milegi?"),
    TIMING("Garbh kab tik payega?"),
    TIMING("Child kab hoga dasha se?"),
    TIMING("IVF kab successful hoga?"),
    TIMING("Putra prapti kab hogi?"),
    TIMING("When will I have a child?"),
    TIMING("Baby kab conceive hoga muhurat?"),
    # ── negative: health/medical ──
    HEALTH("PCOD treatment ke baad fertility doctor ne kya kaha?"),
    HEALTH("Doctor ne infertility diagnose kiya hai?"),
    HEALTH("Hospital me pregnancy complication treatment?"),
    HEALTH("Sperm count test result kharab hai?"),
    HEALTH("Uterus problem ka medical diagnosis?"),
    HEALTH("Hormone medicine se pregnancy?"),
    HEALTH("Tube block surgery ke baad conceive?"),
    HEALTH("Medical treatment for infertility?"),
    HEALTH("PCOS symptoms aur doctor consult?"),
    HEALTH("Pregnancy disease diagnosis chart se?"),
    # ── negative: MR spouse parenting ──
    MR("Spouse parenting style kaisa hoga?"),
    MR("Partner ke saath bachon ka rishta?"),
    MR("Wife bachon ko kaise sambhalegi?"),
    MR("Husband bacchon ke saath bond?"),
    MR("Shaadi ke baad parenting style?"),
    MR("Patni bachon ke sanskaar?"),
    MR("Spouse family values for children?"),
    MR("Partner children ke saath kaise rahega?"),
    # ── negative: off-topic ──
    OFF("Love marriage hogi ya arrange?"),
    OFF("Exam pass ho jayega?"),
    OFF("Business profit hoga?"),
    OFF("Salary kitni hogi?"),
    OFF("Health theek rahegi?"),
    OFF("Promotion milegi kya?"),
    OFF("Foreign job possible?"),
    OFF("Property kharid paunga?"),
    OFF("Partner loyal hai kya?"),
    OFF("Loan clear ho jayega?"),
]


def _hit(text: str, rx: str) -> bool:
    if not rx:
        return True
    blob = (text or "").lower()
    return bool(re.search(rx, blob, re.I))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    gaps: list[str] = []
    total = len(CASES)
    scope_ok = route_ok = engine_ok = ev_ok = 0

    print(f"CHILDREN FULL AUDIT — {total} cases\n" + "=" * 72)

    for c in CASES:
        q = c.q
        is_child = is_children_static_question(q)
        is_health = is_health_static_question(q)
        is_mr = is_mr_spouse_children_question(q)
        arch = classify_children_archetype(q)
        detected = detect_children_archetype(q)

        if c.domain == "children":
            scope_hit = is_child and not is_health and not is_mr
            route_hit = arch == c.engine and (detected == c.engine or arch == c.engine)
            if scope_hit:
                scope_ok += 1
            if route_hit:
                route_ok += 1

            try:
                res = run_children_static_engine(K, q, archetype=arch)
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
                    f"{c.engine} | {q[:55]} | scope={is_child} health={is_health} mr={is_mr} "
                    f"arch={arch} det={detected} exp={c.engine} ev={ev_hit}"
                )
            tag = "OK" if ok else "GAP"
            print(f"  [{tag}] {q[:52]:<52} -> {arch}")

        elif c.domain == "timing":
            ok = not is_child
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"TIMING | {q} | should NOT be children static")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} child={is_child}")

        elif c.domain == "health":
            ok = not is_child and is_health
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"HEALTH | {q} | child={is_child} health={is_health}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} child={is_child} health={is_health}")

        elif c.domain == "mr":
            ok = not is_child and is_mr
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"MR | {q} | child={is_child} mr={is_mr}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} child={is_child} mr={is_mr}")

        else:  # off
            ok = not is_child
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"OFF | {q} | child={is_child} health={is_health} mr={is_mr}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} child={is_child}")

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
