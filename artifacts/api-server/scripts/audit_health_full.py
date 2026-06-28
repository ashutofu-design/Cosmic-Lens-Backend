#!/usr/bin/env python3
"""Full non-timing health audit — EN / Hinglish / Hindi routing + engine + evidence.

Checks per question:
  1. in_scope (health static vs career/finance/off)
  2. archetype route matches expected engine
  3. engine runs without error
  4. evidence count >= min (hard guards may use 1)
  5. verdict+evidence contain focus keywords (alignment heuristic)
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import classify_career_archetype, is_career_static_question
from ask_finance.classifier import classify_finance_archetype, is_finance_static_question
from ask_health.classifier import classify_health_archetype, is_health_static_question
from ask_health.engine import run_health_static_engine

K = {
    "ascendant": "Leo",
    "planets": [
        {"name": "Sun", "house": 1, "sign": "Leo", "longitude": 120.0},
        {"name": "Moon", "house": 4, "sign": "Scorpio", "longitude": 220.0},
        {"name": "Mars", "house": 10, "sign": "Taurus", "longitude": 40.0},
        {"name": "Mercury", "house": 2, "sign": "Virgo", "longitude": 160.0},
        {"name": "Jupiter", "house": 5, "sign": "Scorpio", "longitude": 250.0},
        {"name": "Venus", "house": 3, "sign": "Libra", "longitude": 190.0},
        {"name": "Saturn", "house": 7, "sign": "Aquarius", "longitude": 300.0},
        {"name": "Rahu", "house": 11, "sign": "Gemini", "longitude": 80.0},
        {"name": "Ketu", "house": 5, "sign": "Sagittarius", "longitude": 260.0},
    ],
    "currentDasha": {"maha": "Jupiter", "antar": "Saturn"},
}

REFUSE_RX = r"allowed nahi|doctor|diagnose|death|mrityu|maut|date|muhurat|guarantee|helpline|consult"


@dataclass
class Case:
    q: str
    domain: str  # health | career | finance | off
    engine: str
    focus_rx: str
    min_evidence: int = 3


def C(q, eng, rx, dom="health", min_e=3):
    return Case(q, dom, eng, rx, min_e)


CASES: list[Case] = [
    # ── overall_vitality (EN/HN/HI) ──
    C("How is my overall health in the chart?", "overall_vitality", r"vitality|health|constitution|energy"),
    C("Is my vitality strong?", "overall_vitality", r"vitality|strong|energy|immunity"),
    C("Meri sehat kaisi hai chart me?", "overall_vitality", r"vitality|sehat|health|energy"),
    C("Meri tabiyat strong hai ya weak?", "overall_vitality", r"vitality|tabiyat|health|strong|weak"),
    C("Stamina aur energy level kaisa hai?", "overall_vitality", r"vitality|stamina|energy"),
    C("क्या मेरी सेहत अच्छी है?", "overall_vitality", r"vitality|sehat|health|energy"),
    C("मेरी ऊर्जा और शरीर की ताकत कैसी है?", "overall_vitality", r"vitality|energy|constitution"),
    C("Body strong hai ya kamzor?", "overall_vitality", r"vitality|strong|weak|body"),
    # ── chronic_tendency ──
    C("Chronic health issue ki tendency hai?", "chronic_tendency", r"chronic|long|8th|saturn"),
    C("Long term illness risk in my chart?", "chronic_tendency", r"chronic|long|tendency|8"),
    C("Purani bimari ki tendency chart me?", "chronic_tendency", r"chronic|purani|long|8"),
    C("Genetic disease history chart se?", "chronic_tendency", r"chronic|genetic|long|8"),
    C("Life long health problem rehta hai kya?", "chronic_tendency", r"chronic|long|life"),
    C("लंबी बीमारी की प्रवृत्ति है?", "chronic_tendency", r"chronic|long|8"),
    C("Hamesha health issue reh jata hai?", "chronic_tendency", r"chronic|long|reh"),
    # ── mental_stress ──
    C("Stress and anxiety in my chart?", "mental_stress", r"stress|mental|moon|mind"),
    C("Depression tendency chart me?", "mental_stress", r"stress|mental|moon|depress"),
    C("Neend nahi aati insomnia chart?", "mental_stress", r"sleep|neend|mental|moon|stress"),
    C("Man bechain rehta hai?", "mental_stress", r"mental|stress|moon|mind"),
    C("Mental peace weak hai?", "mental_stress", r"mental|stress|peace|moon"),
    C("क्या मेरा मानसिक तनाव ज्यादा है?", "mental_stress", r"mental|stress|moon|mind"),
    C("Tension aur ghabrahat chart me?", "mental_stress", r"tension|stress|mental|ghabrahat"),
    C("Sleep problem hai kya?", "mental_stress", r"sleep|neend|mental|stress"),
    # ── surgery_risk_tone ──
    C("Surgery risk high hai chart me?", "surgery_risk_tone", r"surgery|operation|risk|caution|mars"),
    C("Is operation safe for me astrologically?", "surgery_risk_tone", r"surgery|operation|safe|risk"),
    C("Operation zaroori hoga kya tone?", "surgery_risk_tone", r"operation|surgery|risk"),
    C("Hospital baar baar jana pad sakta hai?", "surgery_risk_tone", r"hospital|surgery|risk|caution"),
    C("Shastra kriya ka risk hai?", "surgery_risk_tone", r"surgery|operation|risk|mars"),
    C("ऑपरेशन का जोखिम कितना है?", "surgery_risk_tone", r"surgery|operation|risk"),
    # ── preventive_risk ──
    C("Future health risk kya hai?", "preventive_risk", r"prevent|risk|future|zone"),
    C("Aage chal ke kya health dikkat ho sakti hai?", "preventive_risk", r"prevent|risk|future|tendency"),
    C("Health risk zones chart me?", "preventive_risk", r"prevent|risk|zone|6|8"),
    C("Kya kya health issues ki tendency hai?", "preventive_risk", r"tendency|risk|prevent"),
    C("Vulnerable health areas?", "preventive_risk", r"prevent|risk|vulner|zone"),
    C("भविष्य में स्वास्थ्य जोखिम क्या है?", "preventive_risk", r"prevent|risk|future"),
    C("Health khatra zones?", "preventive_risk", r"risk|khatra|prevent|zone"),
    # ── recovery_capacity ──
    C("Recovery capacity strong hai?", "recovery_capacity", r"recover|heal|capacity|resist"),
    C("Healing power chart me kaisi?", "recovery_capacity", r"recover|heal|capacity|jupiter"),
    C("Body recover karti hai achhe se?", "recovery_capacity", r"recover|heal|capacity"),
    C("Swasth hone ki capacity hai?", "recovery_capacity", r"recover|swasth|capacity|heal"),
    C("Recovery resistance chart se?", "recovery_capacity", r"recover|resist|capacity|6"),
    C("ठीक होने की क्षमता कैसी है?", "recovery_capacity", r"recover|heal|capacity"),
    # ── accident_risk ──
    C("Accident risk chart me?", "accident_risk", r"accident|injury|chot|mars|8"),
    C("Chot lagne ka risk hai?", "accident_risk", r"accident|chot|injury|risk|mars"),
    C("Durghatna ka yog hai?", "accident_risk", r"accident|durghatna|risk|mars"),
    C("Physical injury risk tone?", "accident_risk", r"injury|accident|risk|mars"),
    C("दुर्घटना का खतरा है?", "accident_risk", r"accident|durghatna|risk|injury"),
    # ── parent_health ──
    C("Papa ki tabiyat chart se?", "parent_health", r"parent|4th|9th|doctor|4"),
    C("Mother health kaisi hogi?", "parent_health", r"mother|parent|4th|9th|doctor"),
    C("Mummy ki sehat chart me?", "parent_health", r"parent|mother|4th|9th"),
    C("Parents ki health support?", "parent_health", r"parent|4th|9th|doctor"),
    C("माता-पिता की सेहत कैसी है?", "parent_health", r"parent|4th|9th|mother|father"),
    # ── addiction_support ──
    C("Sharab addiction chart se?", "addiction_support", r"addiction|nasha|rahu|12|counsel"),
    C("Smoking chhod sakta hoon chart?", "addiction_support", r"addiction|smoking|nasha|rahu"),
    C("Alcohol habit chart me?", "addiction_support", r"addiction|alcohol|nasha|rahu"),
    C("Nasha se nikalne ka chart?", "addiction_support", r"addiction|nasha|rahu|12"),
    C("नशे की लत chart में?", "addiction_support", r"addiction|nasha|rahu|12"),
    # ── reproductive_support ──
    C("Fertility chart me kaisi?", "reproductive_support", r"repro|fertility|5th|jupiter|5"),
    C("Santaan yog health side?", "reproductive_support", r"santaan|repro|5th|jupiter|fertility"),
    C("Conceive karne ki capacity?", "reproductive_support", r"conceive|fertility|repro|5"),
    C("Pregnancy support chart se?", "reproductive_support", r"pregnan|repro|5th|fertility"),
    C("गर्भधारण की संभावना?", "reproductive_support", r"repro|fertility|5th|garbh|5"),
    # ── digestive_health ──
    C("Pet dard aur acidity?", "digestive_health", r"digest|stomach|pet|mercury|5"),
    C("Stomach problem tendency?", "digestive_health", r"digest|stomach|mercury|pet"),
    C("Gas aur hazma weak hai?", "digestive_health", r"digest|gas|hazma|stomach|mercury"),
    C("Liver kidney zone chart?", "digestive_health", r"digest|liver|kidney|mercury"),
    C("पेट दर्द की प्रवृत्ति?", "digestive_health", r"digest|stomach|pet|mercury"),
    C("Acidity chart me kya?", "digestive_health", r"digest|acidity|stomach|mercury"),
    # ── cardio_health ──
    C("Heart weak hai chart me?", "cardio_health", r"heart|cardio|sun|4th|chest"),
    C("BP blood pressure chart?", "cardio_health", r"heart|bp|blood|cardio|sun"),
    C("Seene me dard tendency?", "cardio_health", r"chest|heart|cardio|4th|sun"),
    C("Cardiac health tone?", "cardio_health", r"cardio|heart|sun|chest"),
    C("दिल की सेहत कैसी है?", "cardio_health", r"heart|cardio|dil|sun"),
    C("Hypertension risk chart?", "cardio_health", r"heart|bp|cardio|hypertension"),
    # ── respiratory_health ──
    C("Saans phool jati hai?", "respiratory_health", r"breath|respir|saans|lung|3"),
    C("Cough cold tendency?", "respiratory_health", r"cough|cold|respir|breath|3"),
    C("Breathing problem chart?", "respiratory_health", r"breath|respir|lung|3|mercury"),
    C("Khansi zukam bar bar?", "respiratory_health", r"cough|cold|respir|khansi|zukam|bar|3"),
    C("सांस की समस्या chart में?", "respiratory_health", r"breath|respir|saans|lung"),
    # ── immune_health ──
    C("Immunity weak baar baar bimar?", "immune_health", r"immun|resist|sun|mars|1"),
    C("Baar baar beemar kyun hota hoon?", "immune_health", r"immun|resist|baar|beemar"),
    C("Immune system strong hai?", "immune_health", r"immun|resist|strong|sun"),
    C("Rog pratirodh kamm hai?", "immune_health", r"immun|resist|rog|pratirodh"),
    C("प्रतिरक्षा कमजोर है?", "immune_health", r"immun|resist|immune"),
    # ── musculoskeletal_health ──
    C("Knee joint pain chronic?", "musculoskeletal_health", r"joint|muscle|mars|saturn|bone"),
    C("Kamar dard chart me?", "musculoskeletal_health", r"back|joint|muscle|mars|saturn"),
    C("Bone joint stiffness?", "musculoskeletal_health", r"bone|joint|stiff|mars|saturn"),
    C("Ghutna dard tendency?", "musculoskeletal_health", r"joint|knee|mars|muscle"),
    C("पीठ दर्द की प्रवृत्ति?", "musculoskeletal_health", r"back|joint|muscle|mars"),
    # ── skin_health ──
    C("Skin rash allergy chart?", "skin_health", r"skin|mercury|moon|rash"),
    C("Acne pimple tendency?", "skin_health", r"skin|acne|mercury|moon"),
    C("Twacha sensitive hai?", "skin_health", r"skin|twacha|mercury|moon"),
    C("Skin problem chart me?", "skin_health", r"skin|mercury|moon|surface"),
    C("त्वचा की समस्या?", "skin_health", r"skin|twacha|mercury|moon"),
    # ── endocrine_health ──
    C("Thyroid hormone chart?", "endocrine_health", r"thyroid|hormone|endocrin|metabol"),
    C("PCOS PCOD chart me?", "endocrine_health", r"pcos|hormone|endocrin|thyroid"),
    C("Weight gain metabolism?", "endocrine_health", r"metabol|weight|hormone|endocrin"),
    C("Sugar level tendency chart?", "endocrine_health", r"sugar|metabol|endocrin|hormone"),
    C("हार्मोन imbalance chart?", "endocrine_health", r"hormone|endocrin|metabol"),
    # ── nervous_health ──
    C("Nerve tingling numbness?", "nervous_health", r"nerve|nervous|mercury|moon|3"),
    C("Brain cognitive weakness?", "nervous_health", r"nerve|brain|nervous|mercury|moon"),
    C("Jhanjhanahat haath me?", "nervous_health", r"nerve|tingling|nervous|mercury"),
    C("Neurological sensitivity chart?", "nervous_health", r"nerve|nervous|mercury|brain"),
    C("नसों की कमजोरी?", "nervous_health", r"nerve|nervous|mercury|3"),
    # ── general_health ──
    C("Overall health picture chart?", "general_health", r"health|vitality|mental|chronic|prevent"),
    C("Meri health overall kaisi?", "general_health", r"health|vitality|overall|mental"),
    C("Health side strong ya weak?", "general_health", r"health|vitality|strong|weak"),
    C("स्वास्थ्य की स्थिति कैसी है?", "general_health", r"health|vitality|swasth|overall"),
    C("Body health summary?", "general_health", r"health|vitality|mental|chronic"),
    # ── HARD GUARDS — refuse (must skip_llm + refuse text) ──
    Case("Kya mujhe cancer hai chart me?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Do I have cancer in my kundli?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Mera cancer hoga kya?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Chart me diabetes hai kya?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Mujhe kaun si bimari hai chart se bata?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("क्या मुझे कैंसर है?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Diagnose my disease from chart", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Kab marunga main?", "health", "refuse_death", REFUSE_RX, 1),
    Case("Death kab hogi meri?", "health", "refuse_death", REFUSE_RX, 1),
    Case("When will I die?", "health", "refuse_death", REFUSE_RX, 1),
    Case("Kitni umar jiyunga?", "health", "refuse_death", REFUSE_RX, 1),
    Case("Life expectancy chart se?", "health", "refuse_death", REFUSE_RX, 1),
    Case("मृत्यु कब होगी?", "health", "refuse_death", REFUSE_RX, 1),
    Case("Mrityu kab hogi?", "health", "refuse_death", REFUSE_RX, 1),
    Case("100% thik ho jaunga guarantee?", "health", "refuse_cure_guarantee", REFUSE_RX, 1),
    Case("Cancer pakka thik ho jayega?", "health", "refuse_cure_guarantee", REFUSE_RX, 1),
    Case("Guaranteed cure chart se?", "health", "refuse_cure_guarantee", REFUSE_RX, 1),
    Case("Kab beemar honga?", "health", "refuse_timing_decline", REFUSE_RX, 1),
    Case("When will I fall ill?", "health", "refuse_timing_decline", REFUSE_RX, 1),
    Case("Bimari kab aayegi?", "health", "refuse_timing_decline", REFUSE_RX, 1),
    Case("Kab thik honga main?", "health", "refuse_timing_recovery", REFUSE_RX, 1),
    Case("Recovery date kab?", "health", "refuse_timing_recovery", REFUSE_RX, 1),
    Case("When will I recover?", "health", "refuse_timing_recovery", REFUSE_RX, 1),
    Case("Operation kab karwau muhurat?", "health", "refuse_surgery_muhurat", REFUSE_RX, 1),
    Case("Surgery date muhurat batao", "health", "refuse_surgery_muhurat", REFUSE_RX, 1),
    Case("Jeena nahi chahta ab", "health", "crisis_redirect", r"helpline|iCall|Vandrevala|safe|9152", 1),
    # ── OFF scope: pure timing (no hard guard phrase) ──
    Case("2027 me health kaisi hogi?", "off", "timing", r""),
    Case("Health kab improve hogi dasha se?", "off", "timing", r""),
    # ── OFF scope: career crossover ──
    Case("Job stress se health kharab?", "health", "mental_stress", r"stress|mental|moon|mind|job"),
    Case("Promotion ke liye health sacrifice?", "career", "career_milestones", r"promotion|career|job|milestone"),
    # ── OFF scope: finance crossover ──
    Case("Health insurance me paisa lagau?", "finance", "general_finance", r"finance|money|paisa|insurance|wealth"),
    Case("Medical expenses ke liye savings?", "finance", "savings_capacity", r"saving|bachat|paisa|money"),
    # ── OFF scope: pet animal ──
    Case("Meri kutti ki health kaisi hai?", "off", "pet", r""),
    Case("My dog health chart?", "off", "pet", r""),
    # ── EXTRA EN variants (200+ total) ──
    C("Constitution weak in birth chart?", "overall_vitality", r"vitality|constitution|weak|energy"),
    C("Am I physically strong?", "overall_vitality", r"vitality|strong|body|energy"),
    C("Energy levels low always?", "overall_vitality", r"vitality|energy|stamina"),
    C("Immune system chart reading?", "immune_health", r"immune|immunity|resistance|6"),
    C("I get sick frequently?", "immune_health", r"immune|sick|resistance|baar"),
    C("Weak immunity tendency?", "immune_health", r"immune|immunity|weak|resistance"),
    C("Digestion weak chart?", "digestive_health", r"digest|pet|stomach|mercury|5"),
    C("Acidity gas problem tendency?", "digestive_health", r"digest|acidity|gas|pet"),
    C("Liver kidney chart health?", "digestive_health", r"digest|liver|kidney|mercury"),
    C("Heart BP risk chart?", "cardio_health", r"heart|bp|cardio|sun|4"),
    C("Chest discomfort tendency?", "cardio_health", r"heart|chest|cardio|4"),
    C("Hypertension chart tendency?", "cardio_health", r"heart|bp|hypertension|cardio"),
    C("Breathing asthma tendency?", "respiratory_health", r"breath|respir|lung|3"),
    C("Lung weakness chart?", "respiratory_health", r"breath|lung|respir|3"),
    C("Skin allergy chart?", "skin_health", r"skin|mercury|moon|allergy"),
    C("Acne pimple tendency?", "skin_health", r"skin|acne|mercury|moon"),
    C("Eczema skin issue chart?", "skin_health", r"skin|eczema|mercury"),
    C("Joint pain stiffness chart?", "musculoskeletal_health", r"joint|bone|mars|saturn|6"),
    C("Back pain kamar dard chart?", "musculoskeletal_health", r"back|kamar|joint|mars|6"),
    C("Bone weakness chart?", "musculoskeletal_health", r"bone|joint|mars|saturn"),
    C("Thyroid hormone imbalance chart?", "endocrine_health", r"thyroid|hormone|endocrine|sun"),
    C("Weight gain metabolism chart?", "endocrine_health", r"weight|metabol|hormone|endocrine"),
    C("PCOS hormonal chart?", "endocrine_health", r"pcos|hormone|endocrine|thyroid"),
    C("Panic attack tendency chart?", "mental_stress", r"stress|mental|panic|moon"),
    C("Burnout exhaustion chart?", "mental_stress", r"stress|mental|moon|fatigue"),
    C("Emotional instability chart?", "mental_stress", r"mental|stress|moon|mood"),
    C("Future health risks to watch?", "preventive_risk", r"prevent|risk|6|8|tendency"),
    C("What health issues am I prone to?", "preventive_risk", r"prevent|risk|tendency|6"),
    C("Vulnerable health zones chart?", "preventive_risk", r"prevent|risk|vulner|6|8"),
    C("Healing capacity after illness?", "recovery_capacity", r"recover|heal|capacity|6"),
    C("Body bounce back ability chart?", "recovery_capacity", r"recover|heal|capacity|mars"),
    C("Slow recovery tendency?", "recovery_capacity", r"recover|heal|slow|6"),
    C("Is surgery risky for me chart?", "surgery_risk_tone", r"surgery|operation|risk|8"),
    C("Operation needed chart indication?", "surgery_risk_tone", r"surgery|operation|risk|8"),
    C("Hospital frequent visits chart?", "surgery_risk_tone", r"surgery|hospital|risk|8"),
    C("Accident injury risk chart?", "accident_risk", r"accident|injury|mars|8|chot"),
    C("Physical trauma tendency?", "accident_risk", r"accident|trauma|injury|mars|8"),
    C("Fall injury chart risk?", "accident_risk", r"accident|fall|injury|mars"),
    C("Father health chart concern?", "parent_health", r"father|papa|9|parent|health"),
    C("Mother illness chart support?", "parent_health", r"mother|mummy|4|parent|health"),
    C("Parents health both chart?", "parent_health", r"parent|mata|pita|4|9"),
    C("Alcohol addiction chart tendency?", "addiction_support", r"addiction|alcohol|rahu|12"),
    C("Smoking habit chart?", "addiction_support", r"addiction|smoking|nasha|rahu"),
    C("Substance abuse tendency chart?", "addiction_support", r"addiction|substance|rahu|12"),
    C("Conceive baby chart support?", "reproductive_support", r"repro|fertility|5|jupiter|santaan"),
    C("Pregnancy health chart?", "reproductive_support", r"pregnan|repro|5|garbh"),
    C("Infertility chart reading?", "reproductive_support", r"infertility|fertility|5|jupiter"),
    # ── EXTRA Hinglish ──
    C("Meri immunity kamzor hai?", "immune_health", r"immune|immunity|kamzor|resistance"),
    C("Pet me gas aur acidity?", "digestive_health", r"digest|pet|gas|acidity"),
    C("Dil aur BP chart me?", "cardio_health", r"heart|dil|bp|cardio"),
    C("Saans lene me dikkat?", "respiratory_health", r"breath|saans|respir|3"),
    C("Twacha allergy chart?", "skin_health", r"skin|twacha|allergy|mercury"),
    C("Ghutne aur jodon me dard?", "musculoskeletal_health", r"joint|ghutna|pain|mars"),
    C("Thyroid aur wajan chart?", "endocrine_health", r"thyroid|weight|hormone|endocrine"),
    C("Ghabrahat aur panic chart?", "mental_stress", r"stress|panic|mental|moon"),
    C("Aage health risk kya hai?", "preventive_risk", r"prevent|risk|aage|6"),
    C("Bimari ke baad recovery strong?", "recovery_capacity", r"recover|heal|capacity|6"),
    C("Operation safe hai chart se?", "surgery_risk_tone", r"surgery|operation|safe|risk"),
    C("Durghatna ka yog chart?", "accident_risk", r"accident|durghatna|mars|8"),
    C("Mummy ki tabiyat chart?", "parent_health", r"mother|mummy|4|parent|tabiyat"),
    C("Sharab se nikalne me chart help?", "addiction_support", r"addiction|sharab|rahu|12"),
    C("Bachcha conceive chart?", "reproductive_support", r"conceive|santaan|5|fertility"),
    # ── EXTRA Hindi Devanagari ──
    C("क्या मेरी प्रतिरक्षा कमजोर है?", "immune_health", r"immune|immunity|resistance|6"),
    C("पाचन तंत्र की समस्या?", "digestive_health", r"digest|pet|mercury|5"),
    C("हृदय और रक्तचाप?", "cardio_health", r"heart|cardio|sun|4"),
    C("सांस की समस्या?", "respiratory_health", r"breath|respir|lung|3"),
    C("त्वचा की समस्या?", "skin_health", r"skin|mercury|moon"),
    C("जोड़ों का दर्द?", "musculoskeletal_health", r"joint|bone|mars|6"),
    C("थायराइड समस्या?", "endocrine_health", r"thyroid|hormone|endocrine"),
    C("मानसिक स्वास्थ्य?", "mental_stress", r"mental|stress|moon|mind"),
    C("भविष्य में स्वास्थ्य जोखिम?", "preventive_risk", r"prevent|risk|6|8"),
    C("ठीक होने की क्षमता?", "recovery_capacity", r"recover|heal|capacity|6"),
    C("शल्य चिकित्सा का जोखिम?", "surgery_risk_tone", r"surgery|operation|risk|8"),
    C("दुर्घटना का खतरा?", "accident_risk", r"accident|injury|mars|8"),
    C("माता-पिता की सेहत?", "parent_health", r"parent|mata|pita|4|9"),
    C("नशे की लत?", "addiction_support", r"addiction|nasha|rahu|12"),
    C("गर्भधारण की संभावना?", "reproductive_support", r"repro|garbh|5|fertility"),
    # ── EXTRA hard guards ──
    Case("Tell me my illness name from kundli", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Am I having diabetes?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("Tumor hai kya mujhe?", "health", "refuse_diagnosis", REFUSE_RX, 1),
    Case("How long will I live?", "health", "refuse_death", REFUSE_RX, 1),
    Case("Aayu kitni hai chart se?", "health", "refuse_death", REFUSE_RX, 1),
    Case("Will I be cured 100 percent?", "health", "refuse_cure_guarantee", REFUSE_RX, 1),
    Case("Diabetes pakka thik ho jayega?", "health", "refuse_cure_guarantee", REFUSE_RX, 1),
    Case("Illness kab lagegi?", "health", "refuse_timing_decline", REFUSE_RX, 1),
    Case("Thik hone ka date batao", "health", "refuse_timing_recovery", REFUSE_RX, 1),
    Case("Best date for my surgery?", "health", "refuse_surgery_muhurat", REFUSE_RX, 1),
    Case("Mujhe marna hai ab", "health", "crisis_redirect", r"helpline|iCall|Vandrevala|safe|9152", 1),
    # ── EXTRA off-scope ──
    Case("Meri naukri stress?", "career", "general_career", r"career|naukri|job|stress|work"),
    Case("Salary badhne se health?", "finance", "income_source", r"salary|income|paisa|money|finance"),
    Case("Health ke liye FD lagau?", "finance", "savings_capacity", r"saving|fd|paisa|money"),
    Case("Hospital bill ka loan?", "finance", "debt_loan", r"loan|debt|paisa|money|finance"),
    Case("Billi ki tabiyat kaisi?", "off", "pet", r""),
]


def _align_ok(text: str, focus_rx: str) -> bool:
    if not focus_rx:
        return True
    return bool(re.search(focus_rx, text, re.I))


def main() -> int:
    fails: list[str] = []
    by_engine: dict[str, list[str]] = {}

    print("=" * 72)
    print(f"HEALTH FULL AUDIT — {len(CASES)} non-timing Qs (EN + Hinglish + Hindi)")
    print("=" * 72)

    for i, c in enumerate(CASES, 1):
        issues: list[str] = []
        hlth = is_health_static_question(c.q)
        car = is_career_static_question(c.q)
        fin = is_finance_static_question(c.q)

        if c.domain == "health":
            if not hlth:
                issues.append("scope: expected health IN but OUT")
            route = classify_health_archetype(c.q) if hlth else "OFF"
            if hlth and route != c.engine:
                issues.append(f"route: got {route} want {c.engine}")
            if hlth:
                try:
                    res = run_health_static_engine(K, c.q, archetype=route)
                    blob = (res.verdict or "") + " " + " ".join(res.evidence or [])
                    if res.template_text:
                        blob += " " + res.template_text
                    if len(res.evidence or []) < c.min_evidence:
                        issues.append(f"evidence: {len(res.evidence or [])} < {c.min_evidence}")
                    if not _align_ok(blob, c.focus_rx):
                        issues.append("align: focus keywords missing in verdict/evidence")
                    if c.engine.startswith("refuse_") or c.engine == "crisis_redirect":
                        if not res.skip_llm:
                            issues.append("guard: expected skip_llm=True for hard guard")
                except Exception as exc:
                    issues.append(f"engine_error: {exc}")
        elif c.domain == "career":
            if hlth and not car:
                issues.append("scope: health wrongly matched (should be career)")
            if not car:
                issues.append("scope: expected career IN but OUT")
            route = classify_career_archetype(c.q) if car else "OFF"
            if car and route != c.engine:
                issues.append(f"route: got {route} want {c.engine}")
        elif c.domain == "finance":
            if hlth and not fin:
                issues.append("scope: health wrongly matched (should be finance)")
            if not fin:
                issues.append("scope: expected finance IN but OUT")
            route = classify_finance_archetype(c.q) if fin else "OFF"
            if fin and route != c.engine:
                issues.append(f"route: got {route} want {c.engine}")
        else:
            if hlth:
                issues.append("scope: should be OFF but health matched")
            if car:
                issues.append("scope: should be OFF but career matched")
            if fin:
                issues.append("scope: should be OFF but finance matched")

        status = "OK" if not issues else "FAIL"
        eng_key = c.engine if c.domain == "health" else c.domain
        by_engine.setdefault(eng_key, []).append(status)
        lang = "HI" if re.search(r"[\u0900-\u097F]", c.q) else ("EN" if not re.search(r"\b(kya|meri|hai|kaisi|chart|kab|paisa)\b", c.q, re.I) else "HN")
        q_show = c.q[:48].encode("ascii", "backslashreplace").decode("ascii")
        print(f"[{i:3}] {status:4} | {lang:2} | {c.domain:7} | {c.engine:24} | {q_show}")
        if issues:
            for iss in issues:
                print(f"       -> {iss}")
                fails.append(f"Q{i}: {c.q[:50]} — {iss}")

    print("\n" + "=" * 72)
    print("SUMMARY BY BUCKET")
    print("=" * 72)
    for eng, statuses in sorted(by_engine.items()):
        ok = sum(1 for s in statuses if s == "OK")
        print(f"  {eng:28} {ok}/{len(statuses)} OK")

    fail_ids = set()
    for f in fails:
        m = re.match(r"Q(\d+):", f)
        if m:
            fail_ids.add(int(m.group(1)))
    passed = len(CASES) - len(fail_ids)
    print(f"\nTOTAL: {passed}/{len(CASES)} OK, {len(fail_ids)} FAIL")
    if fail_ids:
        print("\nFAILED CASE IDS:", sorted(fail_ids))
    return 1 if fail_ids else 0


if __name__ == "__main__":
    raise SystemExit(main())
