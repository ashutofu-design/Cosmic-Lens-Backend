"""
AstroVastu PRO — report language layers.

  summary_en / action_label_en  → English
  summary_hn / action_label_hn  → Roman Hinglish (chip: Hinglish)
  summary_hi / action_label_hi  → Devanagari Hindi (chip: हिन्दी)

Engine logic is unchanged; only user-facing copy is localized.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def strip_ai_branding(text: Optional[str]) -> str:
    """Remove accidental AI branding from user-facing report copy."""
    if not text:
        return ""
    out = re.sub(r"Photo Engine AI", "Photo Engine", text, flags=re.I)
    out = re.sub(r"\(AI\s*scan\)", "(report engine)", out, flags=re.I)
    out = re.sub(r"\(AI\s*स्कैन\)", "(रिपोर्ट इंजन)", out)
    out = re.sub(r"\bAI\s+server\b", "server", out, flags=re.I)
    out = re.sub(r"\bAI\s+service\b", "analysis service", out, flags=re.I)
    out = re.sub(r"\bAI\b", "", out)
    return re.sub(r"\s{2,}", " ", out).strip()


def _sanitize_report_branding(report: Dict[str, Any]) -> None:
    """In-place scrub of all narrative/remedy strings in an AstroVastu report."""
    text_keys = (
        "summary_en", "summary_hi", "summary_hn", "summary_hi_dev",
        "action_label_en", "action_label_hi", "action_label_hn", "action_label_hi_dev",
        "why", "why_hi", "why_hn", "why_hi_dev",
        "astro_note_hi", "astro_note_hi_dev", "chart_note_hi", "chart_note_hi_dev",
        "english", "hindi", "hinglish", "action",
    )
    for room in report.get("rooms") or []:
        for k in text_keys:
            if k in room and isinstance(room[k], str):
                room[k] = strip_ai_branding(room[k])
        for rem in room.get("remedies") or []:
            for k in ("english", "hindi", "hinglish", "action"):
                if k in rem and isinstance(rem[k], str):
                    rem[k] = strip_ai_branding(rem[k])
    for pa in report.get("priority_actions") or []:
        for k in text_keys:
            if k in pa and isinstance(pa[k], str):
                pa[k] = strip_ai_branding(pa[k])
    ov = report.get("overall") or {}
    summ = ov.get("summary") or {}
    for k in ("en", "hi", "hn", "hi_dev"):
        if k in summ and isinstance(summ[k], str):
            summ[k] = strip_ai_branding(summ[k])
    md = report.get("mahadasha_alert")
    if md:
        for k in ("summary_en", "summary_hi", "summary_hn", "summary_hi_dev"):
            if k in md and isinstance(md[k], str):
                md[k] = strip_ai_branding(md[k])

# ── Direction codes (short) → Devanagari ───────────────────────────────────
DIR_HI: Dict[str, str] = {
    "N": "उत्तर",
    "NE": "उत्तर-पूर्व",
    "E": "पूर्व",
    "SE": "दक्षिण-पूर्व",
    "S": "दक्षिण",
    "SW": "दक्षिण-पश्चिम",
    "W": "पश्चिम",
    "NW": "उत्तर-पश्चिम",
    "C": "केंद्र",
    "Center": "केंद्र",
}

DIR_LONG_HI: Dict[str, str] = {
    "North": "उत्तर",
    "North-East": "उत्तर-पूर्व",
    "East": "पूर्व",
    "South-East": "दक्षिण-पूर्व",
    "South": "दक्षिण",
    "South-West": "दक्षिण-पश्चिम",
    "West": "पश्चिम",
    "North-West": "उत्तर-पश्चिम",
    "Center": "केंद्र",
}

ROOM_HI: Dict[str, str] = {
    "kitchen": "रसोई",
    "bedroom": "शयनकक्ष",
    "master_bedroom": "मास्टर शयनकक्ष",
    "bathroom": "शौचालय",
    "toilet": "शौचालय",
    "main_door": "मुख्य द्वार",
    "entrance": "प्रवेश द्वार",
    "living": "बैठक",
    "living_room": "बैठक",
    "dining": "भोजन कक्ष",
    "pooja": "पूजा कक्ष",
    "pooja_room": "पूजा कक्ष",
    "study": "अध्ययन कक्ष",
    "staircase": "सीढ़ी",
}

SIGN_HI: Dict[str, str] = {
    "Aries": "मेष",
    "Taurus": "वृषभ",
    "Gemini": "मिथुन",
    "Cancer": "कर्क",
    "Leo": "सिंह",
    "Virgo": "कन्या",
    "Libra": "तुला",
    "Scorpio": "वृश्चिक",
    "Sagittarius": "धनु",
    "Capricorn": "मकर",
    "Aquarius": "कुंभ",
    "Pisces": "मीन",
}

PLANET_HI: Dict[str, str] = {
    "Sun": "सूर्य",
    "Moon": "चंद्र",
    "Mars": "मंगल",
    "Mercury": "बुध",
    "Jupiter": "बृहस्पति",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
}

ORDINAL_HI = {
    1: "प्रथम", 2: "द्वितीय", 3: "तृतीय", 4: "चतुर्थ", 5: "पंचम", 6: "षष्ठ",
    7: "सप्तम", 8: "अष्टम", 9: "नवम", 10: "दशम", 11: "एकादश", 12: "द्वादश",
}

ACTION_LABEL_HI = {
    "ok": "कोई बदलाव आवश्यक नहीं",
    "remedy": "उपाय सुझाए गए",
    "relocate": "स्थान बदलने की सिफारिश",
    "relocate_or_remedy": "स्थान बदलें या उपाय करें",
}

VERDICT_LABEL_HI = {
    "Ideal": "उत्तम",
    "Acceptable": "स्वीकार्य",
    "Adjustment Needed": "सुधार ज़रूरी",
    "Avoid": "टालें",
}


def _fmt_dirs_hi(short_list: str) -> str:
    """'S / SW / NW' → Devanagari slash list."""
    if not short_list or short_list == "—":
        return "—"
    parts = [p.strip() for p in short_list.replace(",", "/").split("/")]
    out: List[str] = []
    for p in parts:
        key = p.strip()
        out.append(DIR_HI.get(key, DIR_LONG_HI.get(key, key)))
    return " / ".join(out)


def room_hi(room_type: str) -> str:
    key = (room_type or "").strip().lower().replace(" ", "_")
    return ROOM_HI.get(key, (room_type or "कक्ष").replace("_", " "))


def placement_summary_hi_dev(
    *,
    room_type: str,
    cur: str,
    status: str,
    ideal_s: str,
    acc_s: str,
    verdict: str,
    astro_tail: str = "",
) -> str:
    rl = room_hi(room_type)
    cur_h = DIR_HI.get(cur, cur)
    ideal_h = _fmt_dirs_hi(ideal_s)
    acc_h = _fmt_dirs_hi(acc_s)
    tail = f" {astro_tail}" if astro_tail else ""

    if status == "acceptable" and cur == "C":
        return (
            f"{rl} ब्रह्मस्थान (केंद्र) में है — हल्का और खुला रखने पर स्वीकार्य; "
            f"भारी सामान न रखें; नवीनीकरण पर {ideal_h} बेहतर।{tail}"
        )
    if status == "correct":
        return (
            f"{rl} {cur_h} में है — आपकी जन्म कुंडली के अनुसार आदर्श ({ideal_h}) से मेल। "
            f"स्वच्छता बनाए रखें।{tail}"
        )
    if status == "acceptable":
        return (
            f"{rl} {cur_h} आपके चार्ट में स्वीकार्य है (आदर्श: {ideal_h})। "
            f"ज़रूरत हो तो नीचे उपाय देखें।{tail}"
        )
    if status == "wrong" and verdict == "Avoid":
        return (
            f"{rl} {cur_h} आपके चार्ट के लिए टालने योग्य क्षेत्र में है (आदर्श: {ideal_h})। "
            f"संभव हो तो स्थान बदलें, अन्यथा प्रबल उपाय करें।{tail}"
        )
    if status == "wrong":
        return (
            f"{rl} {cur_h} में सुधार चाहिए — आदर्श {ideal_h} (स्वीकार्य: {acc_h})। "
            f"स्थान बदलें या उपाय अपनाएं।{tail}"
        )
    return (
        f"{rl} {cur_h}: निर्णय {VERDICT_LABEL_HI.get(verdict, verdict)}। "
        f"आपके चार्ट के लिए सर्वोत्तम दिशा: {ideal_h}।{tail}"
    )


def bhava_placement_note_hi_dev(
    bhava: int,
    house_sign: str,
    lord: str,
    placed_sign: Optional[str],
    placed_house: Optional[int],
    overlay_dir: str,
) -> str:
    ob = ORDINAL_HI.get(bhava, f"{bhava}वां")
    hs = SIGN_HI.get(house_sign, house_sign)
    ld = PLANET_HI.get(lord, lord)
    od = DIR_LONG_HI.get(overlay_dir, overlay_dir)
    if placed_sign:
        ps = SIGN_HI.get(placed_sign, placed_sign)
        ph = f" (भाव {placed_house})" if placed_house else ""
        return (
            f"आपका {ob} भाव {hs} है (स्वामी {ld}); कुंडली में {ld} {ps} में स्थित{ph}। "
            f"इस कक्ष के लिए स्थिति-आधारित दिशा: {od}।"
        )
    return f"आपका {ob} भाव {hs} है (स्वामी {ld}); शास्त्रीय ओवरले दिशा: {od}।"


def mahadasha_note_hi_dev(lord: str, lord_dir: str, conflicts: int, favoured: int) -> str:
    ld = PLANET_HI.get(lord, lord)
    dh = DIR_LONG_HI.get(lord_dir, lord_dir)
    return (
        f"चल रही महादशा: {ld} ({dh} का स्वामी)। "
        f"{conflicts} कक्ष विरोधी, {favoured} कक्ष शुभ।"
    )


def overall_summary_hi_dev(score: int) -> str:
    if score >= 85:
        return "अत्यंत शुभ — घर आपकी कुंडली की ऊर्जाओं को पूरी तरह सहारा देता है।"
    if score >= 70:
        return "अच्छा — अधिकांश स्थान अनुकूल; थोड़ी सूक्ष्म सुधार पर्याप्त।"
    if score >= 50:
        return "मिश्रित — कई स्थानों पर ध्यान देने से संभावनाएँ खुलेंगी।"
    return "सुधार आवश्यक — कई महत्वपूर्ण स्थानों पर तत्काल उपाय ज़रूरी।"


def remedy_color_hi_dev(lagna: str, lord: str, primary: str, avoid_line: str, direction: str) -> str:
    lag = SIGN_HI.get(lagna, lagna) if lagna in SIGN_HI else lagna
    ld = PLANET_HI.get(lord, lord)
    dh = DIR_LONG_HI.get(direction, direction)
    return (
        f"{dh} क्षेत्र में मुख्य रंग: {primary}। बचें: {avoid_line} "
        f"({lag} लग्न के स्वामी {ld} के अनुसार)।"
    )


def remedy_cleanliness_hi_dev(direction: str) -> str:
    dh = DIR_LONG_HI.get(direction, direction)
    return f"{dh} कोना साफ रखें — रोज पोंछा, साप्ताहिक गहरी सफाई।"


def localize_remedy_for_hi(remedy: Dict[str, Any], direction: str) -> Dict[str, Any]:
    """
    Attach hinglish (Roman) + hindi (Devanagari).
    DB remedies keep Roman in `hinglish`; Devanagari best-effort via templates.
    """
    r = dict(remedy)
    action = (r.get("action") or "").lower()
    roman = (r.get("hindi") or r.get("english") or "").strip()
    r["hinglish"] = roman

    if action == "color":
        avoid_dv = (
            "धूसर/काले रंग (NE क्षेत्र में विशेष)"
            if direction == "North-East"
            else "भारी या टकराव वाले रंग"
        )
        r["hindi"] = remedy_color_hi_dev(
            "", "", "पीला/केसरिया", avoid_dv, direction,
        )
    elif action == "cleanliness":
        r["hindi"] = remedy_cleanliness_hi_dev(direction)
    elif action == "enhancement":
        dh = DIR_LONG_HI.get(direction, direction)
        r["hindi"] = f"यह स्थान उत्तम है। {dh} कोने में ताजे फूल या छोटा दीपक रखें।"
    elif action == "dasha_care":
        r["hindi"] = roman  # often already mixed; keep if no template
    else:
        # Roman DB remedy → keep hinglish; hindi = hinglish until full DV corpus
        r["hindi"] = _roman_remedy_to_devanagari(roman) if roman else roman
    return r


def _roman_remedy_to_devanagari(text: str) -> str:
    """Phrase-level map for remedies_db Roman Hindi (common tokens)."""
    if not text:
        return text
    repl = [
        ("Poorab", "पूर्व"), ("Dakshin", "दक्षिण"), ("Uttar", "उत्तर"), ("Pashchim", "पश्चिम"),
        ("North-East", "उत्तर-पूर्व"), ("North-West", "उत्तर-पश्चिम"),
        ("South-East", "दक्षिण-पूर्व"), ("South-West", "दक्षिण-पश्चिम"),
        ("NE", "उत्तर-पूर्व"), ("NW", "उत्तर-पश्चिम"), ("SE", "दक्षिण-पूर्व"), ("SW", "दक्षिण-पश्चिम"),
        ("rasoi", "रसोई"), ("Rasoi", "रसोई"), ("palang", "पलंग"), ("Palang", "पलंग"),
        ("shauchalaya", "शौचालय"), ("Shauchalaya", "शौचालय"), ("pooja", "पूजा"), ("Pooja", "पूजा"),
        ("deepak", "दीपक"), ("Deepak", "दीपक"), ("Safai", "सफाई"), ("safai", "सफाई"),
        ("Upaay", "उपाय"), ("upaay", "उपाय"), ("kone", "कोना"), ("Kone", "कोना"),
        ("deewar", "दीवार"), ("Deewar", "दीवार"), ("roz", "रोज"), ("Roz", "रोज"),
        ("hafte", "हफ्ते"), ("gehri", "गहरी"), ("bachein", "बचें"), ("Bachein", "बचें"),
        ("Mukhya rang", "मुख्य रंग"), ("mukhya rang", "मुख्य रंग"),
        ("Brihaspativar", "गुरुवार"), ("Mangalwar", "मंगलवार"), ("Shukravar", "शुक्रवार"),
        ("Shaniwar", "शनिवार"), ("sooryast", "सूर्यास्त"), ("ghee", "घी"),
        ("tambe", "तांबे"),         ("peetal", "पीतल"), ("lakdi", "लकड़ी"),
        ("master bedroom", "मास्टर शयनकक्ष"), ("Master bedroom", "मास्टर शयनकक्ष"),
        ("Dwar", "द्वार"), ("dwar", "द्वार"), ("Darwaze", "दरवाज़े"), ("darwaze", "दरवाज़े"),
        ("taaza", "ताजा"), ("Taaza", "ताजा"), ("patton", "पत्तों"), ("lagayein", "लगाएँ"),
        ("badlein", "बदलें"), ("ke upar", "के ऊपर"), ("beech mein", "बीच में"),
        ("Bijli", "बिजली"), ("bijli", "बिजली"), ("chalne wale", "चलने वाले"),
        ("sirf", "सिर्फ"), ("Wash basin", "वॉश बेसिन"),
        ("vidyarthi", "विद्यार्थी"), ("gruhasti", "गृहस्थ"), ("neend", "नींद"),
        ("chumbakiya", "चुंबकीय"), ("tarangein", "तरंगें"), ("bigaadta", "बिगाड़ता"),
        ("thos", "ठोस"), ("headboard", "हेडबोर्ड"), ("frame", "फ्रेम"),
        ("suryast", "सूर्यास्त"), ("se pehle", "से पहले"),
        ("chhota", "छोटा"), ("jalayein", "जलाएँ"), ("rakhein", "रखें"),
        ("aisi", "ऐसी"), ("ki ore", "की ओर"), ("kabhi nahi", "कभी नहीं"),
        ("peeche", "पीछे"), ("dhatu", "धातु"), ("beech mein", "बीच में"),
    ]
    out = text
    for a, b in repl:
        out = out.replace(a, b)
    return out


def apply_report_language(report: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """
    Normalize bilingual fields for mobile chips:
      en → English fields only
      hn → Roman in summary_hi / why / remedies (hinglish)
      hi → Devanagari in summary_hi / why / remedies (hindi)
    """
    code = (lang or "en").strip().lower()
    if code in ("hinglish", "roman", "hn"):
        code = "hn"
    if code not in ("hi", "hn"):
        _sanitize_report_branding(report)
        return report

    if code == "hn":
        # Roman Hinglish: promote summary_hn → summary_hi for mobile pickReportLine(hn)
        for room in report.get("rooms") or []:
            if room.get("summary_hn"):
                room["summary_hi"] = room["summary_hn"]
            for rem in room.get("remedies") or []:
                if not rem.get("hinglish"):
                    rem["hinglish"] = rem.get("hindi") or rem.get("english") or ""
                rem["hindi"] = rem["hinglish"]
        for pa in report.get("priority_actions") or []:
            if pa.get("why_hn"):
                pa["why_hi"] = pa["why_hn"]
        ov = report.get("overall") or {}
        if ov.get("summary", {}).get("hn"):
            ov["summary"]["hi"] = ov["summary"]["hn"]
        md = report.get("mahadasha_alert")
        if md and md.get("summary_hn"):
            md["summary_hi"] = md["summary_hn"]
        _sanitize_report_branding(report)
        return report

    # Devanagari Hindi
    ov = report.get("overall") or {}
    summ = ov.get("summary") or {}
    if summ.get("hi_dev"):
        summ["hi"] = summ["hi_dev"]
    md = report.get("mahadasha_alert")
    if md and md.get("summary_hi_dev"):
        md["summary_hi"] = md["summary_hi_dev"]

    for room in report.get("rooms") or []:
        if room.get("summary_hi_dev"):
            room["summary_hi"] = room["summary_hi_dev"]
        if room.get("action_label_hi_dev"):
            room["action_label_hi"] = room["action_label_hi_dev"]
        if room.get("astro_note_hi_dev"):
            room["astro_note_hi"] = room["astro_note_hi_dev"]
        if room.get("chart_note_hi_dev"):
            room["chart_note_hi"] = room["chart_note_hi_dev"]
        vl = room.get("verdict_label") or {}
        v = room.get("verdict", "")
        if v in VERDICT_LABEL_HI:
            vl = dict(vl)
            vl["hi"] = VERDICT_LABEL_HI[v]
            room["verdict_label"] = vl
        dlong = room.get("direction_long") or room.get("direction") or ""
        for i, rem in enumerate(room.get("remedies") or []):
            room["remedies"][i] = localize_remedy_for_hi(rem, dlong)

    for pa in report.get("priority_actions") or []:
        if pa.get("why_hi_dev"):
            pa["why_hi"] = pa["why_hi_dev"]
        if pa.get("action_label_hi_dev"):
            pa["action_label_hi"] = pa["action_label_hi_dev"]

    _sanitize_report_branding(report)
    return report
