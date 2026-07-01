"""LLM-first intent classifier for the raw-passthrough Ask path.

A single cheap JSON call (gpt-4.1-mini) that reads the user's question and
returns the routing decisions the regex layer used to make:

  - domain        : marriage | love | career | finance | health | general
  - is_timing     : kab / when / muhurat style question
  - is_decision   : should-I / yes-no decision question
  - wants_explain : user explicitly wants a longer "why" explanation
  - mr_archetype  : one of the MR archetype ids (only when domain is
                    marriage/love), so the MR engine can be dispatched
                    precisely instead of falling through to general_mr
  - confidence    : float in [0, 1]
  - source        : "llm" | "llm_low_conf" | "llm_error" | "llm_unavailable"

This module NEVER raises — on any failure it returns a dict with
source="llm_error"/"llm_unavailable" so the caller can fall back to the
existing regex routing with zero behaviour change.

Gated upstream by ASK_LLM_INTENT=1 (see raw_passthrough_ask).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

# Keep in sync with ask_mr/classifier.py archetype ids.
MR_ARCHETYPES = {
    "spouse_profession",
    "spouse_wealth",
    "spouse_appearance",
    "children_parenting",
    "karmic_marriage",
    "lifestyle_marriage",
    "dating_courtship",
    "secret_relationship",
    "one_sided_love",
    "obsession",
    "bed_intimacy",
    "self_worth",
    "partner_nature",
    "long_distance",
    "general_mr",
    "loyalty_trust",
    "emotional_attachment",
    "patchup",
    "chemistry",
    "love_vs_arranged",
    "family_approval",
    "manglik",
    "second_marriage",
    "breakup_risk",
}

CAREER_ARCHETYPES = {
    "job_vs_business",
    "sector_fit",
    "career_traits",
    "strengths_skills",
    "entrepreneurship",
    "work_environment",
    "income_wealth",
    "foreign_career",
    "workplace_relations",
    "fame_recognition",
    "creativity_innovation",
    "career_obstacles",
    "education_career",
    "retirement_legacy",
    "career_milestones",
    "vocational_trade",
    "govt_job",
    "govt_job",
    "it_job",
    "medical_job",
    "banking_job",
    "teaching_job",
    "law_job",
    "defence_job",
    "engineering_job",
    "ca_job",
    "aviation_job",
    "sales_job",
    "research_job",
    "consulting_job",
    "pharma_job",
    "architecture_job",
    "sports_job",
    "media_job",
    "ngo_job",
    "management_job",
    "private_job",
    "general_career",
}

FINANCE_ARCHETYPES = {
    "income_source",
    "savings_capacity",
    "save_vs_spend",
    "expense_pattern",
    "spending_personality",
    "financial_discipline",
    "investment_risk",
    "debt_loan",
    "property_money",
    "sudden_gain_loss",
    "business_profit",
    "loss_reasons",
    "wealth_potential",
    "dhana_yoga",
    "general_finance",
}

HEALTH_ARCHETYPES = {
    "overall_vitality",
    "chronic_tendency",
    "mental_stress",
    "surgery_risk_tone",
    "preventive_risk",
    "recovery_capacity",
    "accident_risk",
    "parent_health",
    "addiction_support",
    "reproductive_support",
    "digestive_health",
    "cardio_health",
    "nervous_health",
    "musculoskeletal_health",
    "skin_health",
    "endocrine_health",
    "respiratory_health",
    "immune_health",
    "refuse_diagnosis",
    "refuse_death",
    "refuse_cure_guarantee",
    "refuse_timing_decline",
    "refuse_timing_recovery",
    "refuse_surgery_muhurat",
    "crisis_redirect",
    "general_health",
}

EDUCATION_ARCHETYPES = {
    "exam_success",
    "competitive_exam",
    "higher_studies",
    "study_field",
    "specialization_path",
    "admission",
    "scholarship",
    "degree_completion",
    "marks_performance",
    "study_focus",
    "learning_ability",
    "coaching_support",
    "education_obstacles",
    "vocational_diploma",
    "general_education",
}

CHILDREN_ARCHETYPES = {
    "child_promise",
    "fertility_conception",
    "pregnancy_wellbeing",
    "child_delay",
    "child_gender_note",
    "number_of_children",
    "child_nature",
    "parent_child_bond",
    "child_success",
    "adoption_path",
    "child_loss_concern",
    "progeny_obstacles",
    "general_children",
}

PROPERTY_ARCHETYPES = {
    "property_yog",
    "property_capacity",
    "property_risk",
    "property_type_fit",
    "property_inherit",
    "property_dispute",
    "property_rent",
    "property_build",
    "property_sell",
    "property_buy",
    "property_loan",
    "property_land",
    "general_property",
}

TRAVEL_ARCHETYPES = {
    "travel_yog",
    "foreign_settlement",
    "visa_theme",
    "relocation_abroad",
    "return_india",
    "travel_obstacles",
    "short_travel",
    "pilgrimage_travel",
    "passport_travel",
    "immigration",
    "business_travel",
    "travel_risk",
    "travel_country_fit",
    "general_travel",
}

LITIGATION_ARCHETYPES = {
    "litigation_remedy",
    "litigation_yog",
    "case_outcome",
    "court_delay",
    "bail_theme",
    "jail_concern",
    "police_fir",
    "criminal_case",
    "civil_litigation",
    "legal_obstacles",
    "enemy_case",
    "acquittal_relief",
    "lawyer_support",
    "family_court",
    "general_litigation",
}

DOMAINS = {"marriage", "love", "career", "finance", "health", "education", "children", "property", "travel", "litigation", "vehicle", "general"}

# Low-confidence cutoff — below this the caller treats the result as
# untrustworthy and falls back to regex.
_LOW_CONF = 0.6
_TIMEOUT_S = 8

_PROMPT_TEMPLATE = """You are an intent router for a Vedic-astrology Q&A app. \
Read the user's question (Hindi/Hinglish/English) and return STRICT JSON only.

Decide:
1. "domain": the life area the question is really about. One of:
   marriage, love, career, finance, health, education, children, property, travel, litigation, vehicle, general.
   CRITICAL RULE: if the question is ABOUT THE PARTNER / SPOUSE / lover \
(their support, nature, behaviour, loyalty, feelings, family) — even if it \
also mentions career or money — the domain is "marriage" or "love" (the \
PARTNER is the subject). e.g. "will my partner support my career" → domain \
love (partner is the subject), NOT career. Use "career" / "finance" ONLY when \
the question is about the NATIVE's own job / money, with no partner focus. \
Use "education" when the question is about study, school/college, exams \
(pass/clear/result — NOT when), admission, stream/course choice, higher \
studies/masters/PhD/abroad study, or study focus — WITHOUT a job/career angle. \
Govt/competitive career exams (UPSC/IAS/SSC/bank PO) → domain career, NOT education.
Career TIMING (kab/when/dasha) for job, naukri, promotion, transfer, job change, \
resignation, govt job selection, interview/joining, salary hike → domain career + \
is_timing true. Tricky: user age 60+ asking "job kab lagega" is still career timing \
(re-employment/consulting frame), NOT general. Police job/naukri → career static govt_job, \
NOT litigation.
Use "children" when the question is about the native's own progeny/santan/bachcha — \
conception/fertility tone, pregnancy support, child promise, delay, gender/count tone \
(without WHEN), child nature/bond/success, adoption/surrogacy, miscarriage/loss fear, \
progeny obstacles — WITHOUT spouse parenting style (that stays marriage MR) and WITHOUT \
pure medical diagnosis/treatment (that stays health). Timing (kab/when) → is_timing true, \
NOT children static.
Use "property" when the question is about home/ghar/makaan/flat/plot/zameen/land/real \
estate — yog/capacity/risk/type fit, buy/sell/inherit/rent/build/dispute, home loan from \
property lens — WITHOUT pure money-only Q (paisa/bachat/afford for ghar → finance) and \
WITHOUT timing (kab/when/muhurat/registry date) → is_timing true, NOT property static.
Use "travel" when the question is about videsh/foreign/abroad/overseas movement — travel yog, \
settlement/relocation abroad, visa/passport/immigration/PR/green card theme (NOT when), short trip, \
pilgrimage/teerth, travel obstacles/risk, return to India — WITHOUT study-abroad padhai (education), \
job/naukri abroad (career foreign_career), or spouse settle after marriage (MR lifestyle). \
Timing (kab/when/muhurat/dasha) → is_timing true, NOT travel static.
Use "vehicle" when the question is about car/bike/gaadi/scooter/vehicle purchase, \
delivery, or ownership timing (kab/when/lunga/paunga/kharid) — NOT health (do NOT map \
car pollution to health unless user asks about their illness/symptoms). Timing → is_timing true.
Use "litigation" when the question is about court case/mukadma/legal/litigation/police/FIR/bail/jail/criminal/civil \
case outcome tone, delay, enemy case, acquittal, lawyer support, family court case — WITHOUT property \
ghar/zameen dispute (property), divorce/spouse nature only (MR), police job/naukri career (career), or \
death penalty/phansi crisis. Timing (kab verdict/bail/hearing) → is_timing true, NOT litigation static.
NATIVE OVERVIEW (CRITICAL): "mere bare/baare me kuch batao", "mujhe batao", "tell me about myself", \
"main kaisa hun", "meri personality" — when NO specific domain (shaadi/career/health/paisa/planet) is \
named → domain=general, mr_archetype=null, is_timing=false, interpretation about the USER's own chart \
overview. Do NOT route these to marriage/love or partner_nature/in-laws.
2. "is_timing": true if the user asks WHEN something happens (kab, timing, \
date, muhurat, age). false otherwise.
3. "is_decision": true if it is a should-I / yes-or-no decision question.
4. "wants_explain": true if the user wants a detailed "why" explanation \
(samjhao, explain, reason, kyun) rather than a short verdict.
5. "mr_archetype": ONLY when domain is marriage or love, pick the single \
best-fitting archetype id; otherwise null. Allowed ids and meaning:
   - spouse_profession: partner's job/career field (doctor/IT/gov/business etc.)
   - spouse_wealth: partner's wealth / financial status / saving habits
   - spouse_appearance: partner's physical look (height, face, eyes, complexion, voice, aura)
   - children_parenting: spouse parenting style, bond with children, family values
   - karmic_marriage: soulmate, past life, karmic debt, spiritual growth via marriage
   - lifestyle_marriage: luxury/travel/social/home/abroad settlement after marriage
   - dating_courtship: true love, dating, flirting, red/green flags, friend-to-lover
   - secret_relationship: secret/hidden/parallel affair
   - one_sided_love: one-sided love, crush, proposal
   - obsession: obsession, jealousy, possessiveness
   - bed_intimacy: physical/sexual intimacy
   - self_worth: user's own confidence/boundaries
   - partner_nature: partner's nature/personality/behaviour/age/respect/temper; \
OR spouse's in-laws / family-wale (8th house axis — NOT user's parents approval). \
NEVER use for "mere bare/baare me", "tell me about myself", or other generic \
native-overview asks — those are domain=general with mr_archetype=null.
   - long_distance: long-distance relationship
   - general_mr: overall marriage quality/happiness/compatibility, OR whether \
the partner will SUPPORT the native's career / life goals / decisions
   - loyalty_trust: loyalty, trust, cheating, commitment
   - emotional_attachment: emotional bonding / feelings depth
   - patchup: reconciliation, ex returning
   - chemistry: attraction, romance, spark
   - love_vs_arranged: love vs arranged marriage
   - family_approval: family/parents approval, intercaste
   - manglik: manglik / mangal dosh
   - second_marriage: second/again marriage
   - breakup_risk: breakup, separation, divorce risk
6. "career_archetype": ONLY when domain is career, pick best id; otherwise null:
   - job_vs_business: ONLY employment vs self-employment (job OR business, naukri ya dhandha)
   - sector_fit: industry/field OR which business is best / konsa business / business type / line
   - career_traits: leadership, pressure, risk, discipline, team, independence
   - strengths_skills: strengths, weaknesses, skills to develop
   - entrepreneurship: startup, partnership business, online, family business, trading business
   - work_environment: remote, corporate, MNC, public/private sector
   - income_wealth: salary, passive income, high income, freelancing, commission
   - foreign_career: abroad job, foreign company, settle abroad for work
   - workplace_relations: boss, colleagues, job satisfaction
   - fame_recognition: fame, reputation, recognition in career
   - creativity_innovation: YouTuber, actor, singer, photographer, gamer, content creator, creative/innovation career
   - career_milestones: promotion, interview, job change, govt/competitive EXAM clear/pass, side hustle/part-time income
   - govt_job: government/sarkari job suitability, IAS/IPS/police/railway/bank PO/public sector naukri (NOT exam timing)
   - it_job / medical_job / banking_job / teaching_job / law_job / defence_job / engineering_job / ca_job / aviation_job / sales_job / research_job / consulting_job / pharma_job / architecture_job / sports_job / media_job / ngo_job / management_job / private_job: named profession/job-line suitability (doctor, software, pilot, CA, etc.)
   - vocational_trade: electrician, plumber, mechanic, carpenter, driver, ITI/skilled trade
   - career_obstacles: delays, setbacks, obstacles in career
   - education_career: study, degree, education for career
   - retirement_legacy: late career, legacy, retirement tone
   - general_career: other career questions
7. "finance_archetype": ONLY when domain is finance, pick best id; otherwise null:
   - income_source: salary, earning, income stability, source of money
   - savings_capacity: saving, bachat, paisa tikta/rukta, kitni bachat
   - save_vs_spend: saver vs spender, bachane wala ya kharch wala
   - expense_pattern: kharcha, spending, leak, paisa nahi tikta
   - spending_personality: emotional spending, luxury-oriented, impulsive spend
   - financial_discipline: financial discipline, money habits, budget discipline
   - investment_risk: risk investor vs conservative, aggressive vs safe investing
   - debt_loan: loan, karz, EMI, udhar, debt free
   - property_money: ghar/flat/property purchase money, home loan readiness
   - sudden_gain_loss: lottery/inheritance/windfall OR sudden loss
   - business_profit: business profit, partnership money safety
   - loss_reasons: paisa kyun nahi, money problems, garib kyun
   - wealth_potential: amir/rich/crorepati potential
   - dhana_yoga: dhana/dhan yog audit
   - general_finance: other money questions
8. "health_archetype": ONLY when domain is health, pick best id; otherwise null:
   - overall_vitality: sehat/vitality/immunity/stamina/energy kaisi
   - chronic_tendency: chronic/long-term/purani bimari tendency
   - mental_stress: stress/anxiety/depression/sleep/neend/tension
   - surgery_risk_tone: surgery/operation risk tone (NOT muhurat/date)
   - preventive_risk: future health risk/tendency/prevention
   - recovery_capacity: recovery/healing capacity (NOT recovery date)
   - accident_risk: accident/injury/chot risk tone
   - parent_health: mother/father/parent health
   - addiction_support: addiction/nasha/sharab/smoking
   - reproductive_support: fertility/pregnancy/santaan
   - digestive_health / cardio_health / nervous_health / musculoskeletal_health / \
skin_health / endocrine_health / respiratory_health / immune_health: body-system subdomains
   - refuse_diagnosis: cancer/diabetes/disease name from chart — NEVER diagnose
   - refuse_death: death/mrityu/kab marunga/lifespan — NEVER predict death timing
   - refuse_cure_guarantee / refuse_timing_decline / refuse_timing_recovery / \
refuse_surgery_muhurat / crisis_redirect: other hard-guard Qs
   - general_health: other health questions
8. "education_archetype": ONLY when domain is education, pick best id; otherwise null:
   - exam_success: generic exam pass/clear/selection/result tone (NOT date)
   - competitive_exam: NEET/JEE/CAT/GATE/CLAT/board/entrance/competitive academic test
   - higher_studies: masters, PhD, research, study abroad, GRE/IELTS/student visa
   - study_field: which stream/subject/course/branch to choose (PCM/PCB/commerce/arts)
   - specialization_path: medical/engineering/law/CA/teaching line as study direction
   - admission: college/university admission/seat/waitlist/merit list
   - scholarship: scholarship/stipend/fee waiver/financial aid for study
   - degree_completion: degree complete/graduate/pass-out/final year clear
   - marks_performance: marks/percentage/grade/GPA/topper/distinction
   - study_focus: concentration, mann nahi lagta, motivation, study habits
   - learning_ability: buddhi, memory, weak in maths/subject, grasping power
   - coaching_support: coaching/tuition/online course vs self-study
   - education_obstacles: backlog, gap year, fail year, ATKT, study delay/break
   - vocational_diploma: ITI, polytechnic, diploma, certificate/skill course
   - general_education: other study/education questions
9. "children_archetype": ONLY when domain is children, pick best id; otherwise null:
   - child_promise: santan yog / will I have children / putra prapti tone (NOT when)
   - fertility_conception: conceive/IVF/infertility/fertility chart tone (NOT medical diagnosis)
   - pregnancy_wellbeing: pregnancy/good news/garbh safe tone (NOT due date)
   - child_delay: delay in santan/late motherhood/fatherhood (NOT when)
   - child_gender_note: ladka/ladki/beta/beti gender tone — stay uncertain
   - number_of_children: kitne bachche/twins — qualitative only, no exact count
   - child_nature: child personality/swabhav/character
   - parent_child_bond: native's bond with own children (NOT spouse parenting)
   - child_success: child's future/success/study/life tone
   - adoption_path: adoption/surrogacy/gode lena/foster
   - child_loss_concern: miscarriage/loss/garbhpat fear — sensitive tone
   - progeny_obstacles: nisantan/barren/dosh/obstacle in santan
   - general_children: other progeny/children questions
10. "property_archetype": ONLY when domain is property, pick best id; otherwise null:
   - property_yog: property/home yog, milega kya, own home possible (NOT when)
   - property_capacity: capacity/readiness to buy/own property (NOT exact price)
   - property_risk: legal/documentation/dispute risk tone (NOT exact outcome)
   - property_type_fit: plot vs flat vs luxury vs rental vs ancestral fit
   - property_inherit: paitrik/ancestral/virasat/family property
   - property_dispute: property court/dispute/vivad case
   - property_rent: rental income, rent out property, kiraya
   - property_build: ghar banwana/construction/build home
   - property_sell: sell/dispose property
   - property_buy: buy/purchase/invest in property (NOT when)
   - property_loan: home loan/EMI/mortgage from property chart lens
   - property_land: plot/zameen/land/farm land specific
   - general_property: other property/real-estate questions
11. "travel_archetype": ONLY when domain is travel, pick best id; otherwise null:
   - travel_yog: foreign/videsh travel yog, possible hai, will I go abroad (NOT when)
   - foreign_settlement: settle abroad, basna videsh, permanent abroad life
   - visa_theme: visa approve/reject/delay/issue (NOT student visa for study → education)
   - relocation_abroad: shift/move/relocate abroad
   - return_india: wapas India, return from abroad, no settlement abroad
   - travel_obstacles: delay/block/ruka in travel/settlement/visa
   - short_travel: trip/vacation/holiday abroad
   - pilgrimage_travel: teerth/dharma yatra/hajj/umrah
   - passport_travel: passport issue/capacity/travel desire
   - immigration: PR/green card/citizenship/migration file
   - business_travel: official/business trip abroad (NOT permanent job)
   - travel_risk: accident/danger abroad travel
   - travel_country_fit: kaun sa desh/country, USA ya Canada, which country — qualitative direction only
   - general_travel: other foreign/travel questions
12. "litigation_archetype": ONLY when domain is litigation, pick best id; otherwise null:
   - litigation_remedy: upay/remedy/solution/mantra/puja/daan for court case/legal matter (NOT when-only)
   - litigation_yog: court case yog, mukadma hoga, legal trouble yog (NOT when)
   - case_outcome: jeet/har/win/loss/favour tone — indicative only, NOT guaranteed
   - court_delay: case delay, ruka, pending, lamba chalega (NOT when)
   - bail_theme: bail/zamanat/interim/anticipatory bail theme (NOT when)
   - jail_concern: jail/prison/custody fear — calm tone only, NOT jail yog prediction
   - police_fir: FIR/police case/thana/complaint (NOT police job career)
   - criminal_case: criminal court/charge/498a/IPC/session court
   - civil_litigation: civil suit/civil court/consumer/labour tribunal
   - legal_obstacles: legal problems, kanooni pareshani, rukawat
   - enemy_case: dushman/shatru/enemy litigation
   - acquittal_relief: acquittal/bera gari/chhutkara/case dismiss/quash
   - lawyer_support: advocate/vakil/lawyer support theme (NOT legal advice)
   - family_court: family court/custody/maintenance/498a case (NOT divorce spouse MR)
   - general_litigation: other court/legal questions
13. "question_summary": ONE line plain Hinglish — restate what the user wants to know \
in your own words (12-40 words). For LONG or multi-part questions, still ONE line but \
cover every sub-part the user asked. Do NOT invent topics not in the question. \
Do NOT use routing jargon (domain/archetype/engine).
14. "interpretation": short echo only if needed — prefer question_summary for meaning.
15. "understanding_line": EXACTLY one word — "Yes" if you understood the question topic, \
"No" if off-topic / too broken / unclear. Examples: finance Q → "Yes"; gibberish → "No".
16. "confidence": 0.0-1.0 how sure you are.

Return ONLY this JSON object:
{{"domain": "...", "is_timing": false, "is_decision": false, \
"wants_explain": false, "mr_archetype": null, "career_archetype": null, \
"finance_archetype": null, "health_archetype": null, "education_archetype": null, \
"children_archetype": null, "property_archetype": null, "travel_archetype": null, \
"litigation_archetype": null, "question_summary": "...", \
"interpretation": "User asked: \\"...\\"", "understanding_line": "Yes", "confidence": 0.0}}

Question: {question}"""


def _error(reason: str, source: str = "llm_error") -> dict:
    return {
        "domain": "general",
        "is_timing": False,
        "is_decision": False,
        "wants_explain": False,
        "mr_archetype": None,
        "career_archetype": None,
        "finance_archetype": None,
        "health_archetype": None,
        "education_archetype": None,
        "children_archetype": None,
        "property_archetype": None,
        "travel_archetype": None,
        "litigation_archetype": None,
        "question_summary": "",
        "interpretation": "",
        "understanding_line": "",
        "confidence": 0.0,
        "source": source,
        "error": reason[:200],
    }


def classify_ask_intent(
    question: str,
    *,
    client: Any = None,
    model: Optional[str] = None,
) -> dict:
    """Classify an Ask question with one LLM call. Never raises.

    Returns a dict with keys: domain, is_timing, is_decision, wants_explain,
    mr_archetype, confidence, source (+ latency_ms / error diagnostics).
    """
    q = (question or "").strip()
    if not q:
        return _error("empty question", source="llm_unavailable")

    if model is None:
        model = (
            os.environ.get("ASK_INTENT_MODEL")
            or os.environ.get("QU_MODEL")
            or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        )

    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore

            client = _get_client()
        except Exception as exc:  # pragma: no cover - defensive
            return _error(f"client import failed: {exc}", source="llm_unavailable")

    if client is None:
        return _error("no OpenAI client", source="llm_unavailable")

    t0 = time.time()
    _create_kwargs = dict(
        model=model,
        temperature=0.1,
        timeout=_TIMEOUT_S,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": _PROMPT_TEMPLATE.format(question=q)}],
    )
    try:
        # gpt-5 series / some proxies renamed max_tokens -> max_completion_tokens
        # and reject the legacy name with HTTP 400. Try new first, fall back.
        try:
            resp = client.chat.completions.create(
                max_completion_tokens=320, **_create_kwargs
            )
        except TypeError:
            resp = client.chat.completions.create(max_tokens=200, **_create_kwargs)
        except Exception as exc:
            _msg = str(exc).lower()
            if ("max_tokens" in _msg and "max_completion_tokens" in _msg) or (
                "use 'max_tokens'" in _msg
            ):
                resp = client.chat.completions.create(max_tokens=200, **_create_kwargs)
            else:
                raise

        latency_ms = int((time.time() - t0) * 1000)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
    except Exception as exc:
        fb = _error(str(exc))
        fb["latency_ms"] = int((time.time() - t0) * 1000)
        return fb

    domain = str(data.get("domain") or "").strip().lower()
    if domain not in DOMAINS:
        domain = "general"

    archetype = data.get("mr_archetype")
    if isinstance(archetype, str):
        archetype = archetype.strip().lower()
    if archetype not in MR_ARCHETYPES:
        archetype = None
    # Archetype only makes sense for relationship domains.
    if domain not in {"marriage", "love"}:
        archetype = None
    elif archetype is None:
        # Domain is relationship but model gave no/invalid archetype — use the
        # safe catch-all so the MR engine still runs deterministically.
        archetype = "general_mr"

    try:
        conf = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))

    if domain == "career":
        career_arch = data.get("career_archetype")
        if isinstance(career_arch, str):
            career_arch = career_arch.strip().lower()
        if career_arch not in CAREER_ARCHETYPES:
            career_arch = None
        if career_arch is None:
            career_arch = "general_career"
        finance_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
        litigation_arch = None
    elif domain == "finance":
        finance_arch = data.get("finance_archetype")
        if isinstance(finance_arch, str):
            finance_arch = finance_arch.strip().lower()
        if finance_arch not in FINANCE_ARCHETYPES:
            finance_arch = None
        if finance_arch is None:
            finance_arch = "general_finance"
        career_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
        litigation_arch = None
    elif domain == "health":
        health_arch = data.get("health_archetype")
        if isinstance(health_arch, str):
            health_arch = health_arch.strip().lower()
        if health_arch not in HEALTH_ARCHETYPES:
            health_arch = None
        if health_arch is None:
            health_arch = "general_health"
        career_arch = None
        finance_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
        litigation_arch = None
    elif domain == "education":
        education_arch = data.get("education_archetype")
        if isinstance(education_arch, str):
            education_arch = education_arch.strip().lower()
        if education_arch not in EDUCATION_ARCHETYPES:
            education_arch = None
        if education_arch is None:
            education_arch = "general_education"
        career_arch = None
        finance_arch = None
        health_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
        litigation_arch = None
    elif domain == "children":
        children_arch = data.get("children_archetype")
        if isinstance(children_arch, str):
            children_arch = children_arch.strip().lower()
        if children_arch not in CHILDREN_ARCHETYPES:
            children_arch = None
        if children_arch is None:
            children_arch = "general_children"
        career_arch = None
        finance_arch = None
        health_arch = None
        education_arch = None
        property_arch = None
        travel_arch = None
    elif domain == "property":
        property_arch = data.get("property_archetype")
        if isinstance(property_arch, str):
            property_arch = property_arch.strip().lower()
        if property_arch not in PROPERTY_ARCHETYPES:
            property_arch = None
        if property_arch is None:
            property_arch = "general_property"
        career_arch = None
        finance_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        travel_arch = None
        litigation_arch = None
    elif domain == "travel":
        travel_arch = data.get("travel_archetype")
        if isinstance(travel_arch, str):
            travel_arch = travel_arch.strip().lower()
        if travel_arch not in TRAVEL_ARCHETYPES:
            travel_arch = None
        if travel_arch is None:
            travel_arch = "general_travel"
        career_arch = None
        finance_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        litigation_arch = None
    elif domain == "vehicle":
        career_arch = None
        finance_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
        litigation_arch = None
    elif domain == "litigation":
        litigation_arch = data.get("litigation_archetype")
        if isinstance(litigation_arch, str):
            litigation_arch = litigation_arch.strip().lower()
        if litigation_arch not in LITIGATION_ARCHETYPES:
            litigation_arch = None
        if litigation_arch is None:
            litigation_arch = "general_litigation"
        career_arch = None
        finance_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
    else:
        career_arch = None
        finance_arch = None
        health_arch = None
        education_arch = None
        children_arch = None
        property_arch = None
        travel_arch = None
        litigation_arch = None

    question_summary = str(data.get("question_summary") or "").strip()[:500]
    interpretation = str(data.get("interpretation") or "").strip()[:2000]

    try:
        from ask_native_overview import (
            is_native_overview_question,
        )

        if is_native_overview_question(q):
            domain = "general"
            archetype = None
            career_arch = None
            finance_arch = None
            health_arch = None
            education_arch = None
            children_arch = None
            property_arch = None
            travel_arch = None
            litigation_arch = None
            data["is_timing"] = False
            data["is_decision"] = False
    except Exception:
        pass

    result = {
        "domain": domain,
        "is_timing": bool(data.get("is_timing")),
        "is_decision": bool(data.get("is_decision")),
        "wants_explain": bool(data.get("wants_explain")),
        "mr_archetype": archetype,
        "career_archetype": career_arch,
        "finance_archetype": finance_arch,
        "health_archetype": health_arch,
        "education_archetype": education_arch,
        "children_archetype": children_arch,
        "property_archetype": property_arch,
        "travel_archetype": travel_arch,
        "litigation_archetype": litigation_arch,
        "question_summary": question_summary,
        "interpretation": interpretation,
        "understanding_line": str(data.get("understanding_line") or "").strip()[:200],
        "confidence": conf,
        "source": "llm_low_conf" if conf < _LOW_CONF else "llm",
        "latency_ms": latency_ms,
    }

    try:
        from ask_intent_fidelity import repair_llm_intent

        result = repair_llm_intent(q, result)
    except Exception:
        try:
            from ask_intent_fidelity import faithful_interpretation

            result["interpretation"] = faithful_interpretation(q)
        except Exception:
            pass

    try:
        from ask_question_understand import ensure_question_understanding

        # Routing module owns mandatory LLM paraphrase (Rule #1).
        result = ensure_question_understanding(q, result, client=client, force_llm=False)
    except Exception:
        pass

    return result


def finalize_intent_understanding(
    question: str,
    result: dict[str, Any] | None,
    *,
    client: Any = None,
) -> dict[str, Any]:
    """After repair — mandatory one-line understanding for admin + narrator."""
    from ask_question_understand import ensure_question_understanding

    base = result if isinstance(result, dict) else {}
    return ensure_question_understanding(question, base, client=client)
