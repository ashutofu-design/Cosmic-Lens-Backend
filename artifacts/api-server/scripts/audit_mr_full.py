#!/usr/bin/env python3
"""Full non-timing MR audit — marriage / relationship / love (EN + Hinglish + Hindi).

Checks per question:
  1. in_scope (MR static vs timing / career / finance / health off)
  2. archetype route matches expected engine
  3. engine runs without error
  4. evidence count >= min
  5. verdict+evidence contain focus keywords (alignment heuristic)
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_career.classifier import is_career_static_question
from ask_finance.classifier import is_finance_static_question
from ask_health.classifier import is_health_static_question
from ask_marriage_relationship_slice import is_marriage_relationship_static_question
from ask_mr.classifier import classify_mr_archetype
from ask_mr.engine import run_mr_static_engine

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


@dataclass
class Case:
    q: str
    domain: str  # mr | off | career | finance | health
    engine: str
    focus_rx: str
    min_evidence: int = 2


def C(q: str, eng: str, rx: str, dom: str = "mr", min_e: int = 2) -> Case:
    return Case(q, dom, eng, rx, min_e)


def O(q: str, bucket: str = "timing") -> Case:
    return Case(q, "off", bucket, r"", 0)


# Legacy coverage (96 Qs) flattened from audit_mr_question_coverage.py
def _legacy_cases() -> list[Case]:
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from audit_mr_question_coverage import AUDIT

    out: list[Case] = []
    for _cat, items in AUDIT:
        for q, eng, needles in items:
            rx = "|".join(re.escape(n) for n in needles)
            out.append(C(q, eng, rx))
    return out


EXTRA: list[Case] = [
    # ── partner_nature EN/HN/HI ──
    C("What will my partner personality be like?", "partner_nature", r"7th|partner|Venus|Moon|nature"),
    C("Mera partner introvert hoga ya extrovert?", "partner_nature", r"7th|partner|nature|Venus"),
    C("Spouse emotionally expressive hoga?", "partner_nature", r"7th|partner|Moon|emotion"),
    C("पति का स्वभाव कैसा होगा?", "partner_nature", r"7th|partner|nature|Venus|Moon"),
    C("पत्नी का व्यक्तित्व कैसा होगा?", "partner_nature", r"7th|partner|nature|Venus"),
    C("Partner dominant hoga ya cooperative?", "partner_nature", r"7th|partner|dominant|cooperative"),
    # ── manglik ──
    C("Am I manglik in my chart?", "manglik", r"Mangal|manglik|Mars|7th|dosh"),
    C("Kya main manglik hoon chart me?", "manglik", r"Mangal|manglik|Mars|7th"),
    C("Mangal dosh marriage pe effect?", "manglik", r"Mangal|manglik|Mars|7th"),
    C("क्या मैं मांगलिक हूँ?", "manglik", r"Mangal|manglik|Mars|7th"),
    C("मांगलिक दोष कितना है?", "manglik", r"Mangal|manglik|Mars|7th"),
    # ── love_vs_arranged ──
    C("Love marriage or arranged marriage?", "love_vs_arranged", r"Love|Arrange|5th|7th|Venus"),
    C("Love cum arranged hoga kya?", "love_vs_arranged", r"Love|Arrange|5th|7th"),
    C("Ghar walon ki pasand ya meri pasand?", "love_vs_arranged", r"Love|Arrange|family|5th"),
    C("प्रेम विवाह होगा या arranged?", "love_vs_arranged", r"Love|Arrange|5th|7th"),
    C("क्या love marriage hogi?", "love_vs_arranged", r"Love|Arrange|5th|7th"),
    # ── loyalty_trust ──
    C("Will my partner cheat on me?", "loyalty_trust", r"Trust|loyal|7th|Venus|cheat"),
    C("Partner dhokha dega kya?", "loyalty_trust", r"Trust|loyal|7th|cheat|dhokha"),
    C("Partner wafadar hoga?", "loyalty_trust", r"Trust|loyal|7th|faithful"),
    C("क्या पति विश्वास के योग्य है?", "loyalty_trust", r"Trust|loyal|7th|Venus"),
    C("विश्वास और वफादारी chart me?", "loyalty_trust", r"Trust|loyal|7th"),
    # ── chemistry ──
    C("Physical chemistry strong hogi?", "chemistry", r"chemistry|Venus|Mars|7th|passion"),
    C("Hamari attraction kaisi hogi?", "chemistry", r"chemistry|attraction|Venus|Mars"),
    C("Romance aur spark chart me?", "chemistry", r"chemistry|romance|Venus|Mars"),
    C("प्रेम और आकर्षण कैसा है?", "chemistry", r"chemistry|attraction|Venus|Mars"),
    # ── patchup ──
    C("Ex wapas aa sakta hai kya?", "patchup", r"patch|reconcil|return|7th|Venus"),
    C("Patch up hoga kya rishta?", "patchup", r"patch|reconcil|7th"),
    C("Purana partner wapas lautega?", "patchup", r"patch|return|7th|reconcil"),
    C("पुराना रिश्ता वापस आएगा?", "patchup", r"patch|return|7th|reconcil"),
    # ── family_approval ──
    C("Parents shaadi ke liye manenge?", "family_approval", r"family|approval|parents|Rahu|Jupiter"),
    C("Inter caste marriage family accept?", "family_approval", r"family|inter|caste|approval"),
    C("Ghar walon ka role shaadi me?", "family_approval", r"family|approval|role"),
    C("माता-पिता शादी के लिए राजी?", "family_approval", r"family|approval|parents"),
    C("इंटरकास्ट शादी मंजूर?", "family_approval", r"family|inter|caste|approval"),
    # ── spouse_profession ──
    C("What profession will my spouse have?", "spouse_profession", r"profession|4th|10th|spouse|house"),
    C("Husband doctor banega kya?", "spouse_profession", r"profession|4th|spouse|doctor"),
    C("Wife government job karegi?", "spouse_profession", r"profession|4th|spouse|job"),
    C("पति का पेशा क्या होगा?", "spouse_profession", r"profession|4th|spouse|10th"),
    # ── spouse_wealth ──
    C("Will my spouse be rich?", "spouse_wealth", r"wealth|8th|spouse|Jupiter|rich"),
    C("Partner amir hoga kya?", "spouse_wealth", r"wealth|8th|spouse|rich|Jupiter"),
    C("Spouse middle class se hoga?", "spouse_wealth", r"wealth|8th|spouse|middle"),
    C("पत्नी अमीर परिवार से?", "spouse_wealth", r"wealth|8th|spouse|Jupiter"),
    # ── spouse_appearance ──
    C("How tall will my spouse be?", "spouse_appearance", r"Height|7th|D9|appearance|spouse"),
    C("Partner ki height kaisi hogi?", "spouse_appearance", r"Height|7th|appearance"),
    C("Spouse attractive hoga?", "spouse_appearance", r"Attract|7th|Venus|appearance"),
    C("पति की शक्ल कैसी होगी?", "spouse_appearance", r"7th|appearance|face|Venus"),
    C("पत्नी की आंखें कैसी होंगी?", "spouse_appearance", r"7th|eyes|Moon|appearance"),
    # ── children_parenting ──
    C("Spouse parenting style kaisa hoga?", "children_parenting", r"Parent|5th|11th|children"),
    C("Partner bachon ke saath bond?", "children_parenting", r"Parent|5th|children|bond"),
    C("Family values strong honge?", "children_parenting", r"Family values|9th|Jupiter|5th"),
    C("बच्चों के साथ रिश्ता कैसा?", "children_parenting", r"Parent|5th|children"),
    # ── karmic_marriage ──
    C("Is this my soulmate?", "karmic_marriage", r"Soulmate|Karmic|Rahu|Ketu|7th"),
    C("Karmic debt marriage me hai?", "karmic_marriage", r"Karmic|Saturn|Rahu|7th"),
    C("Past life connection partner se?", "karmic_marriage", r"Past|Ketu|Rahu|7th"),
    C("क्या यह soulmate है?", "karmic_marriage", r"Soulmate|Karmic|7th|Rahu"),
    # ── lifestyle_marriage ──
    C("Luxury lifestyle after marriage?", "lifestyle_marriage", r"Luxury|2nd|11th|Venus|travel"),
    C("Shaadi ke baad travel zyada?", "lifestyle_marriage", r"Travel|9th|12th|lifestyle"),
    C("Ghar ka mahaul shaadi ke baad?", "lifestyle_marriage", r"Home|4th|Moon|lifestyle"),
    C("विदेश में बसना शादी के बाद?", "lifestyle_marriage", r"Foreign|12th|9th|settle|lifestyle|travel"),
    # ── dating_courtship ──
    C("Will I find true love?", "dating_courtship", r"True|love|5th|Venus|dating"),
    C("Dost se lover ban sakta hai?", "dating_courtship", r"Friend|lover|5th|11th"),
    C("Dating success milegi kya?", "dating_courtship", r"Dating|5th|Venus|success"),
    C("First impression partner pe kaisa?", "dating_courtship", r"First|7th|Venus|impression"),
    C("सच्चा प्यार मिलेगा?", "dating_courtship", r"True|love|5th|Venus"),
    C("डेटिंग में सफलता?", "dating_courtship", r"Dating|5th|Venus"),
    # ── second_marriage ──
    C("Second marriage hogi kya?", "second_marriage", r"Second|7th|marriage|Saturn"),
    C("Dusri shaadi ka yog?", "second_marriage", r"Second|7th|marriage"),
    C("Do bar shaadi hogi?", "second_marriage", r"Second|7th|marriage"),
    C("दूसरी शादी होगी?", "second_marriage", r"Second|7th|marriage"),
    # ── long_distance ──
    C("Long distance relationship chalega?", "long_distance", r"distance|Rahu|7th|online"),
    C("Online relationship successful hoga?", "long_distance", r"online|Rahu|distance|7th"),
    C("Door reh kar rishta chalega?", "long_distance", r"distance|7th|Rahu"),
    C("लॉन्ग डिस्टेंस रिश्ता?", "long_distance", r"distance|7th|Rahu"),
    # ── one_sided_love ──
    C("One sided love ka result?", "one_sided_love", r"one|sided|5th|Venus|crush"),
    C("Ek tarfa pyaar accept hoga?", "one_sided_love", r"one|sided|5th|crush"),
    C("Crush propose karega kya?", "one_sided_love", r"crush|propose|5th|one"),
    C("एकतरफा प्यार?", "one_sided_love", r"one|sided|5th|Venus"),
    # ── secret_relationship ──
    C("Secret affair chart me?", "secret_relationship", r"secret|12th|hidden|affair"),
    C("Chhupa rishta chal raha hai?", "secret_relationship", r"secret|12th|hidden"),
    C("Multiple relationships honge?", "secret_relationship", r"Multiple|parallel|12th|secret"),
    C("गुप्त रिश्ता chart me?", "secret_relationship", r"secret|12th|hidden"),
    # ── obsession ──
    C("Partner jealous hoga kya?", "obsession", r"jealous|possess|Moon|obsess"),
    C("Obsession relationship me?", "obsession", r"obsess|possess|Moon|control"),
    C("Partner possessive nature?", "obsession", r"possess|jealous|obsess|Moon"),
    C("अति लगाव partner me?", "obsession", r"obsess|attach|Moon|possess"),
    # ── emotional_attachment ──
    C("Mera attachment style kaisa hai?", "emotional_attachment", r"Moon|Emotional|attach|needs"),
    C("Meri emotional needs poori hongi?", "emotional_attachment", r"Moon|Emotional|needs|attach"),
    C("Emotional bond strong hoga?", "emotional_attachment", r"Moon|Emotional|attach|bond"),
    C("भावनात्मक जुड़ाव कैसा?", "emotional_attachment", r"Moon|Emotional|attach"),
    # ── bed_intimacy ──
    C("Physical compatibility bedroom me?", "bed_intimacy", r"intim|bed|8th|Venus|Moon"),
    C("Private life kaisi rahegi?", "bed_intimacy", r"intim|private|8th|Venus"),
    C("Conjugal life strong hoga?", "bed_intimacy", r"conjugal|intim|8th|Venus"),
    C("शारीरिक अनुकूलता?", "bed_intimacy", r"intim|8th|Venus|physical"),
    # ── self_worth ──
    C("Relationship me self worth weak?", "self_worth", r"self|worth|boundar|insecure|Moon"),
    C("Insecurity relationship me?", "self_worth", r"insecure|self|worth|Moon|boundar"),
    C("Meri boundaries strong hongi?", "self_worth", r"boundar|self|worth|Moon"),
    C("आत्मविश्वास रिश्ते में?", "self_worth", r"self|worth|insecure|Moon"),
    # ── breakup_risk ──
    C("Breakup ka chance hai?", "breakup_risk", r"Breakup|separation|7th|divorce"),
    C("Divorce hoga kya?", "breakup_risk", r"Breakup|divorce|7th|separation"),
    C("Rishta toot sakta hai?", "breakup_risk", r"Breakup|separation|7th"),
    C("Toxic relationship hoga?", "breakup_risk", r"Toxic|Breakup|7th|separation"),
    C("तलाक का योग?", "breakup_risk", r"Breakup|divorce|7th|separation"),
    C("रिश्ता टूट सकता है?", "breakup_risk", r"Breakup|separation|7th"),
    # ── general_mr ──
    C("Marriage stable rahegi kya?", "general_mr", r"Stability|7th|Jupiter|marriage"),
    C("Shaadi ke baad khushi rahegi?", "general_mr", r"Moon|Jupiter|happy|7th|strength"),
    C("Communication strong hogi marriage me?", "general_mr", r"Mercury|communication|7th"),
    C("Partner career support karega?", "general_mr", r"support|7th|Jupiter|career"),
    C("36 gun milan kaisa hai?", "general_mr", r"compat|7th|Moon|Jupiter"),
    C("शादी के बाद खुशी?", "general_mr", r"Moon|Jupiter|happy|7th|marriage"),
    C("विवाह में संवाद?", "general_mr", r"Mercury|communication|7th"),
    # ── OFF scope: timing (must be OUT) ──
    O("Kab shaadi hogi meri?", "timing"),
    O("When will I get married?", "timing"),
    O("Marriage kab hogi chart se?", "timing"),
    O("Rishta kab fix hoga?", "timing"),
    O("शादी कब होगी?", "timing"),
    O("विवाह का समय कब?", "timing"),
    O("2027 me shaadi hogi?", "timing"),
    O("Next year marriage hogi?", "timing"),
    # ── OFF scope: wrong domain ──
    O("Meri naukri kaisi hai?", "career"),
    O("Career growth strong hogi?", "career"),
    O("Medical ke liye savings FD?", "finance"),
    O("FD me paisa lagau?", "finance"),
    O("Meri sehat kaisi hai?", "health"),
    O("Meri immunity weak hai?", "health"),
]

CASES: list[Case] = _legacy_cases() + EXTRA


def _align_ok(text: str, focus_rx: str) -> bool:
    if not focus_rx:
        return True
    return bool(re.search(focus_rx, text, re.I))


def main() -> int:
    fails: list[str] = []
    by_engine: dict[str, list[str]] = {}

    print("=" * 72)
    print(f"MR FULL AUDIT — {len(CASES)} non-timing Qs (EN + Hinglish + Hindi)")
    print("=" * 72)

    for i, c in enumerate(CASES, 1):
        issues: list[str] = []
        in_mr = is_marriage_relationship_static_question(c.q)
        car = is_career_static_question(c.q)
        fin = is_finance_static_question(c.q)
        hlth = is_health_static_question(c.q)

        if c.domain == "mr":
            if not in_mr:
                issues.append("scope: expected MR IN but OUT")
            route = classify_mr_archetype(c.q) if in_mr else "OFF"
            if in_mr and route != c.engine:
                issues.append(f"route: got {route} want {c.engine}")
            if in_mr:
                try:
                    res = run_mr_static_engine(K, c.q, archetype=route)
                    blob = (res.verdict or "") + " " + " ".join(res.evidence or [])
                    if res.template_text:
                        blob += " " + res.template_text
                    if len(res.evidence or []) < c.min_evidence:
                        issues.append(f"evidence: {len(res.evidence or [])} < {c.min_evidence}")
                    if not _align_ok(blob, c.focus_rx):
                        issues.append("align: focus keywords missing in verdict/evidence")
                except Exception as exc:
                    issues.append(f"engine_error: {exc}")
        else:
            if in_mr:
                issues.append("scope: should be OFF but MR matched")
            if c.engine == "career" and not car:
                issues.append("scope: expected career IN but OUT")
            elif c.engine == "finance" and not fin:
                issues.append("scope: expected finance IN but OUT")
            elif c.engine == "health" and not hlth:
                issues.append("scope: expected health IN but OUT")

        status = "OK" if not issues else "FAIL"
        eng_key = c.engine if c.domain == "mr" else c.domain
        by_engine.setdefault(eng_key, []).append(status)
        lang = "HI" if re.search(r"[\u0900-\u097F]", c.q) else (
            "EN" if not re.search(r"\b(kya|meri|hai|kaisi|chart|kab|shaadi|pyaar)\b", c.q, re.I) else "HN"
        )
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
