"""Numerology framing helpers — Option D wrapper system.

Every tier (even purely astrological ones) gets:
  1. A numerology OPENER paragraph at the top — bridges driver/conductor
     numerology to the life-area being discussed. User feels: "yeh meri
     numerology report hai jo Vedic se backed hai".
  2. A numerology CLOSING TOOLKIT card at the bottom — lucky numbers, days,
     colors, mantra, gem, do's-don'ts for that life-area filtered by driver.

Usage from a tier renderer:
    from vedic.numerology.framing import (
        numerology_opener_block, numerology_closing_toolkit_block,
    )
    flow.extend(numerology_opener_block(s, driver, conductor, "career", lang))
    # ...existing tier cards...
    flow.extend(numerology_closing_toolkit_block(s, driver, conductor, "career", lang))
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

# Devanagari Unicode range (incl. vedic extensions). Wrap any run of
# Devanagari characters in a <font name="NotoDeva"> tag so reportlab uses
# the registered Devanagari TTF instead of Helvetica (which renders
# Devanagari as ▉▉▉ tofu boxes). Safe to call on already-tagged HTML
# because we only match raw Devanagari character runs.
_DEVA_RE = re.compile(r"([\u0900-\u097F\u1CD0-\u1CFF\uA8E0-\uA8FF]+)")

def _deva_safe(text: str) -> str:
    """Wrap Devanagari runs in <font name='NotoDeva'> so they render in
    PDFs even when the surrounding paragraph style uses Helvetica."""
    if not text:
        return text
    return _DEVA_RE.sub(r"<font name='NotoDeva'>\1</font>", str(text))

# ── Planet table (Cheiro / classical) ──────────────────────────────────
PLANET_BY_DRIVER: Dict[int, str] = {
    1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
    6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars",
}
PLANET_HI: Dict[str, str] = {
    "Sun": "सूर्य", "Moon": "चंद्र", "Jupiter": "गुरु", "Rahu": "राहु",
    "Mercury": "बुध", "Venus": "शुक्र", "Ketu": "केतु", "Saturn": "शनि", "Mars": "मंगल",
}

# ── Lucky toolkit per driver ───────────────────────────────────────────
# Cheiro + KN Rao classical numerology
LUCKY: Dict[int, Dict[str, Any]] = {
    1: {
        "numbers": [1, 4, 10, 13, 19, 22, 28, 31],
        "compound": [10, 19, 28, 37, 46],
        "days": ["Sunday", "Monday"],
        "days_hi": ["रविवार", "सोमवार"],
        "colors": ["Gold", "Orange", "Yellow", "Royal Blue"],
        "colors_hi": ["सुनहरा", "नारंगी", "पीला", "गहरा नीला"],
        "gem": "Ruby (Manik)",
        "gem_hi": "माणिक्य",
        "metal": "Gold / Copper",
        "direction": "East",
        "mantra": "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
        "avoid_numbers": [8, 17, 26],
        "avoid_days": ["Saturday"],
    },
    2: {
        "numbers": [2, 7, 11, 16, 20, 25, 29],
        "compound": [11, 20, 29, 38, 47],
        "days": ["Monday", "Friday"],
        "days_hi": ["सोमवार", "शुक्रवार"],
        "colors": ["Cream", "White", "Silver", "Light Green"],
        "colors_hi": ["क्रीम", "श्वेत", "रजत", "हल्का हरा"],
        "gem": "Pearl (Moti)",
        "gem_hi": "मोती",
        "metal": "Silver",
        "direction": "North-West",
        "mantra": "ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः",
        "avoid_numbers": [9, 18, 27],
        "avoid_days": ["Tuesday"],
    },
    3: {
        "numbers": [3, 6, 9, 12, 15, 21, 24, 30],
        "compound": [12, 21, 30, 39, 48],
        "days": ["Tuesday", "Thursday", "Friday"],
        "days_hi": ["मंगलवार", "गुरुवार", "शुक्रवार"],
        "colors": ["Yellow", "Saffron", "Gold", "Pink"],
        "colors_hi": ["पीला", "केसरी", "सुनहरा", "गुलाबी"],
        "gem": "Yellow Sapphire (Pukhraj)",
        "gem_hi": "पुखराज",
        "metal": "Gold",
        "direction": "North-East",
        "mantra": "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
        "avoid_numbers": [5, 14, 23],
        "avoid_days": ["Wednesday"],
    },
    4: {
        "numbers": [4, 1, 13, 22, 31],
        "compound": [13, 22, 31, 40, 49],
        "days": ["Sunday", "Monday", "Saturday"],
        "days_hi": ["रविवार", "सोमवार", "शनिवार"],
        "colors": ["Grey", "Khaki", "Electric Blue", "Navy"],
        "colors_hi": ["स्लेटी", "खाकी", "बिजली नीला", "गहरा नीला"],
        "gem": "Hessonite (Gomed)",
        "gem_hi": "गोमेद",
        "metal": "Mixed Metal (Panchdhatu)",
        "direction": "South-West",
        "mantra": "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
        "avoid_numbers": [5, 14, 23],
        "avoid_days": ["Wednesday"],
    },
    5: {
        "numbers": [5, 14, 23, 32, 41, 50],
        "compound": [14, 23, 32, 41, 50],
        "days": ["Wednesday", "Friday"],
        "days_hi": ["बुधवार", "शुक्रवार"],
        "colors": ["Light Green", "Sky Blue", "White"],
        "colors_hi": ["हल्का हरा", "आसमानी नीला", "श्वेत"],
        "gem": "Emerald (Panna)",
        "gem_hi": "पन्ना",
        "metal": "Bronze",
        "direction": "North",
        "mantra": "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
        "avoid_numbers": [4, 13, 22],
        "avoid_days": ["Tuesday"],
    },
    6: {
        "numbers": [6, 15, 24, 33, 42, 51],
        "compound": [15, 24, 33, 42, 51],
        "days": ["Friday", "Tuesday", "Thursday"],
        "days_hi": ["शुक्रवार", "मंगलवार", "गुरुवार"],
        "colors": ["Pink", "Light Blue", "White", "Pastel Green"],
        "colors_hi": ["गुलाबी", "हल्का नीला", "श्वेत", "पेस्टल हरा"],
        "gem": "Diamond / White Sapphire",
        "gem_hi": "हीरा / श्वेत पुखराज",
        "metal": "Silver / Platinum",
        "direction": "South-East",
        "mantra": "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
        "avoid_numbers": [8, 17, 26],
        "avoid_days": ["Saturday"],
    },
    7: {
        "numbers": [7, 16, 25, 34, 43, 52],
        "compound": [16, 25, 34, 43, 52],
        "days": ["Sunday", "Monday"],
        "days_hi": ["रविवार", "सोमवार"],
        "colors": ["Sea Green", "Cream", "Light Yellow", "Smokey Grey"],
        "colors_hi": ["समुद्री हरा", "क्रीम", "हल्का पीला", "धुएँदार स्लेटी"],
        "gem": "Cat's Eye (Lehsuniya)",
        "gem_hi": "लहसुनिया",
        "metal": "Mixed Metal (Panchdhatu)",
        "direction": "South",
        "mantra": "ॐ स्रां स्रीं स्रौं सः केतवे नमः",
        "avoid_numbers": [9, 18, 27],
        "avoid_days": ["Tuesday"],
    },
    8: {
        "numbers": [8, 17, 26, 35, 44, 53],
        "compound": [17, 26, 35, 44, 53],
        "days": ["Saturday", "Sunday"],
        "days_hi": ["शनिवार", "रविवार"],
        "colors": ["Black", "Dark Blue", "Purple", "Charcoal"],
        "colors_hi": ["काला", "गहरा नीला", "बैंगनी", "स्याही"],
        "gem": "Blue Sapphire (Neelam)",
        "gem_hi": "नीलम",
        "metal": "Iron / Steel",
        "direction": "West",
        "mantra": "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः",
        "avoid_numbers": [1, 10, 19],
        "avoid_days": ["Sunday"],
    },
    9: {
        "numbers": [9, 18, 27, 36, 45, 54],
        "compound": [18, 27, 36, 45, 54],
        "days": ["Tuesday", "Thursday", "Friday"],
        "days_hi": ["मंगलवार", "गुरुवार", "शुक्रवार"],
        "colors": ["Red", "Crimson", "Pink", "Maroon"],
        "colors_hi": ["लाल", "गहरा लाल", "गुलाबी", "मरून"],
        "gem": "Red Coral (Moonga)",
        "gem_hi": "मूँगा",
        "metal": "Copper",
        "direction": "South",
        "mantra": "ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
        "avoid_numbers": [2, 11, 20],
        "avoid_days": ["Monday"],
    },
}

# ── Life-area framing meta ─────────────────────────────────────────────
# Each area: (en_label, hi_label, hg_label, opener_lens)
# opener_lens is a 1-line bridge that ties the driver/conductor to this area.
LIFE_AREA: Dict[str, Dict[str, str]] = {
    "vedic_classical": {
        "label_en": "Vedic Classical Foundation",
        "label_hi": "वैदिक शास्त्रीय आधार",
        "label_hg": "Vedic Classical Foundation",
        "lens_en": "Your Driver number's planet IS the bridge between numerology and Vedic astrology — the same planet rules your number AND appears in your chart. This tier shows how that planet plays out across your Rashi, Nakshatra, dasha, and grid.",
        "lens_hi": "आपके Driver नंबर का ग्रह संख्याशास्त्र और वैदिक ज्योतिष के बीच का सेतु है — वही ग्रह आपके नंबर पर शासन करता है और आपकी कुंडली में भी आता है। यह टियर दिखाता है कि वह ग्रह आपकी राशि, नक्षत्र, दशा, और लो-शू ग्रिड में कैसे प्रकट होता है।",
        "lens_hg": "Aapke Driver number ka planet numerology aur Vedic astrology ke beech ka pul hai — wahi planet aapke number ko rule karta hai aur aapki kundli mein bhi appear karta hai. Yeh tier dikhata hai ki woh planet aapki Rashi, Nakshatra, dasha, aur Lo-Shu grid mein kaise play out hota hai.",
    },
    "remedies": {
        "label_en": "Personalised Remedies",
        "label_hi": "व्यक्तिगत उपाय",
        "label_hg": "Personalised Remedies",
        "lens_en": "Every remedy in this tier is filtered through your Driver number's ruling planet — the gem, mantra, color, fast-day, and even the donation list are picked so they vibrate with YOUR number, not generic advice.",
        "lens_hi": "इस टियर में हर उपाय आपके Driver नंबर के स्वामी ग्रह के अनुसार फ़िल्टर किया गया है — रत्न, मंत्र, रंग, व्रत-दिन, यहाँ तक कि दान-सूची भी आपके नंबर के अनुरूप चुनी गई है, सामान्य सलाह नहीं।",
        "lens_hg": "Iss tier mein har remedy aapke Driver number ke ruling planet ke through filter hua hai — gem, mantra, color, fast-day, aur donation list bhi aapke number ke according chuni gayi hai, generic advice nahi.",
    },
    "audits": {
        "label_en": "Personal Audits & Doshas",
        "label_hi": "व्यक्तिगत ऑडिट और दोष",
        "label_hg": "Personal Audits & Doshas",
        "lens_en": "Doshas are Vedic, but their IMPACT on you depends on your Driver number. A Mangal dosha hits a Driver-9 (Mars) person differently than a Driver-2 (Moon) person. This tier filters every dosha's severity & remedy through your number-DNA.",
        "lens_hi": "दोष वैदिक हैं, लेकिन आप पर उनका प्रभाव आपके Driver नंबर पर निर्भर करता है। मंगल दोष Driver-9 (मंगल) को अलग तरह प्रभावित करता है, Driver-2 (चंद्र) को अलग। यह टियर हर दोष की गंभीरता और उपाय को आपके नंबर-DNA से फ़िल्टर करता है।",
        "lens_hg": "Doshas Vedic hain, lekin aap par unka impact aapke Driver number par depend karta hai. Mangal dosha Driver-9 (Mars) wale ko alag tarah hit karta hai, Driver-2 (Moon) ko alag. Yeh tier har dosha ki severity aur remedy ko aapke number-DNA se filter karta hai.",
    },
    "relationships": {
        "label_en": "Relationships & Compatibility",
        "label_hi": "रिश्ते और संगतता",
        "label_hg": "Relationships & Compatibility",
        "lens_en": "Compatibility = your Driver/Conductor numbers + their Driver/Conductor numbers + both Moon Nakshatras. Numerology decides WHO you click with at the personality level, Vedic Ashtakoot decides WHO you build a karma-line with. This tier merges both.",
        "lens_hi": "संगतता = आपके Driver/Conductor + साथी के Driver/Conductor + दोनों के चंद्र नक्षत्र। संख्याशास्त्र तय करता है कि आप किसके साथ व्यक्तित्व-स्तर पर जुड़ते हैं, वैदिक अष्टकूट तय करता है कि किसके साथ कर्म-रेखा बनती है। यह टियर दोनों को मिलाता है।",
        "lens_hg": "Compatibility = aapke Driver/Conductor + saathi ke Driver/Conductor + dono ke Moon Nakshatra. Numerology decide karti hai ki aap kiske saath personality-level par click karte ho, Vedic Ashtakoot decide karti hai ki kiske saath karma-line banti hai. Yeh tier dono ko merge karta hai.",
    },
    "career": {
        "label_en": "Career & Profession",
        "label_hi": "करियर और व्यवसाय",
        "label_hg": "Career & Profession",
        "lens_en": "Your career path is a triangle: (1) Driver number's planet = your natural vocation vibration, (2) 10th house & D10 chart = the Vedic structural blueprint, (3) Atmakaraka = your soul's purpose. When all three align → dharmic career; when they disagree → confusion + delay.",
        "lens_hi": "आपका करियर-पथ एक त्रिकोण है: (1) Driver नंबर का ग्रह = सहज व्यवसाय-स्पंदन, (2) 10वाँ भाव और D10 चार्ट = वैदिक संरचनात्मक खाका, (3) आत्मकारक = आत्मा का प्रयोजन। जब तीनों मिलते हैं → धार्मिक करियर; जब टकराते हैं → भ्रम और विलंब।",
        "lens_hg": "Aapka career-path ek triangle hai: (1) Driver number ka planet = natural vocation vibration, (2) 10th house aur D10 chart = Vedic structural blueprint, (3) Atmakaraka = soul ka purpose. Jab teeno align hote hain → dharmic career; jab takrate hain → confusion aur delay.",
    },
    "wealth": {
        "label_en": "Wealth & Money",
        "label_hi": "धन और संपत्ति",
        "label_hg": "Wealth & Money",
        "lens_en": "Money flows through 3 channels: (1) Driver-number's money planet = your earning temperament, (2) 2nd/5th/9th/11th houses = Vedic Dhana yogas, (3) current Mahadasha lord = the wealth window NOW. This tier reads all three so the prose isn't generic.",
        "lens_hi": "धन तीन चैनलों से बहता है: (1) Driver नंबर का धन-ग्रह = आपकी अर्जन-प्रवृत्ति, (2) 2/5/9/11 भाव = वैदिक धन योग, (3) वर्तमान महादशा स्वामी = अभी की धन-खिड़की। यह टियर तीनों पढ़ता है, इसलिए प्रोज़ सामान्य नहीं है।",
        "lens_hg": "Paisa 3 channels se behta hai: (1) Driver number ka money-planet = aapki earning temperament, (2) 2nd/5th/9th/11th houses = Vedic Dhana yogas, (3) current Mahadasha lord = abhi ki wealth-window. Yeh tier teeno read karta hai, isliye prose generic nahi hai.",
    },
    "health": {
        "label_en": "Health & Vitality",
        "label_hi": "स्वास्थ्य और जीवन-शक्ति",
        "label_hg": "Health & Vitality",
        "lens_en": "Health = (Driver-planet body-region weakness) + (6th/8th house Vedic disease patterns) + (missing-number gaps in your Lo-Shu grid). Each driver-number has a known body-region (e.g. 8/Saturn = bones-knees, 6/Venus = reproductive-throat).",
        "lens_hi": "स्वास्थ्य = (Driver-ग्रह की शरीर-क्षेत्र कमज़ोरी) + (6/8 भाव वैदिक रोग-पैटर्न) + (आपकी Lo-Shu ग्रिड में लुप्त-अंक रिक्तियाँ)। हर Driver नंबर का एक ज्ञात शरीर-क्षेत्र है (जैसे 8/शनि = हड्डी-घुटने, 6/शुक्र = प्रजनन-गला)।",
        "lens_hg": "Health = (Driver-planet body-region weakness) + (6th/8th house Vedic disease patterns) + (Lo-Shu grid mein missing-number gaps). Har driver-number ka ek known body-region hai (jaise 8/Saturn = bones-knees, 6/Venus = reproductive-throat).",
    },
    "education": {
        "label_en": "Education & Knowledge",
        "label_hi": "शिक्षा और ज्ञान",
        "label_hg": "Education & Knowledge",
        "lens_en": "Learning style is dictated by Driver-planet (Mercury=fast/multi, Jupiter=deep/spiritual, Saturn=slow/mastery). Vedic 4th/5th house + Saraswati yoga add the structural intellect. Together they answer: what subjects, what method, what timing.",
        "lens_hi": "सीखने की शैली Driver-ग्रह तय करता है (बुध=तेज़/बहुविषय, गुरु=गहरा/आध्यात्मिक, शनि=धीमा/महारत)। वैदिक 4/5 भाव + सरस्वती योग संरचनात्मक बुद्धि देते हैं। मिलकर ये बताते हैं: कौन से विषय, क्या तरीका, क्या समय।",
        "lens_hg": "Learning style Driver-planet decide karta hai (Mercury=fast/multi, Jupiter=deep/spiritual, Saturn=slow/mastery). Vedic 4th/5th house + Saraswati yoga structural intellect dete hain. Milkar yeh batate hain: kaun se subjects, kya method, kya timing.",
    },
    "family": {
        "label_en": "Family, Marriage & Children",
        "label_hi": "परिवार, विवाह और संतान",
        "label_hg": "Family, Marriage & Children",
        "lens_en": "Family-DNA = Driver-number family role (1=leader, 2=peace-keeper, 6=nurturer, 8=karmic-burden-bearer) + 7th/5th house Vedic structure. Spouse-number compatibility decides peace; Santan yogas decide children.",
        "lens_hi": "परिवार-DNA = Driver-नंबर पारिवारिक भूमिका (1=नेता, 2=शांति-रक्षक, 6=पालक, 8=कर्म-भार-धारक) + 7/5 भाव वैदिक संरचना। पति-पत्नी नंबर-अनुकूलता शांति तय करती है; संतान योग संतान।",
        "lens_hg": "Family-DNA = Driver-number family role (1=leader, 2=peace-keeper, 6=nurturer, 8=karmic-burden-bearer) + 7th/5th house Vedic structure. Spouse-number compatibility peace decide karti hai; Santan yogas children decide karte hain.",
    },
    "spiritual": {
        "label_en": "Spirituality & Moksha",
        "label_hi": "आध्यात्म और मोक्ष",
        "label_hg": "Spirituality & Moksha",
        "lens_en": "Soul-number (your Driver) reveals your INNER deity-pull — Driver-7 (Ketu) = natural sannyasi, Driver-3 (Jupiter) = guru-path, Driver-9 (Mars) = warrior-devotion. Vedic 12th house + Atmakaraka add the moksha route.",
        "lens_hi": "आत्मा-संख्या (आपका Driver) आंतरिक देवता-आकर्षण प्रकट करती है — Driver-7 (केतु) = सहज संन्यासी, Driver-3 (गुरु) = गुरु-पथ, Driver-9 (मंगल) = योद्धा-भक्ति। वैदिक 12वाँ भाव + आत्मकारक मोक्ष-मार्ग देते हैं।",
        "lens_hg": "Soul-number (aapka Driver) inner deity-pull reveal karta hai — Driver-7 (Ketu) = natural sannyasi, Driver-3 (Jupiter) = guru-path, Driver-9 (Mars) = warrior-devotion. Vedic 12th house + Atmakaraka moksha route dete hain.",
    },
    "karma": {
        "label_en": "Karma & Past Lives",
        "label_hi": "कर्म और पूर्व-जन्म",
        "label_hg": "Karma & Past Lives",
        "lens_en": "Karmic-debt numbers (13/14/16/19) + missing numbers in Lo-Shu grid + Rahu-Ketu axis = your past-life unfinished business. Numerology names the debt; Vedic shows where in this life it activates.",
        "lens_hi": "कर्म-ऋण अंक (13/14/16/19) + Lo-Shu ग्रिड में लुप्त अंक + राहु-केतु अक्ष = आपका पूर्व-जन्म अधूरा व्यापार। संख्याशास्त्र ऋण का नाम देती है; वैदिक बताती है इस जीवन में कहाँ सक्रिय होगा।",
        "lens_hg": "Karmic-debt numbers (13/14/16/19) + Lo-Shu grid ke missing numbers + Rahu-Ketu axis = aapka past-life adhura business. Numerology debt ka naam deti hai; Vedic batati hai iss life mein kahan activate hoga.",
    },
    "travel": {
        "label_en": "Travel, Foreign & Property",
        "label_hi": "यात्रा, विदेश और संपत्ति",
        "label_hg": "Travel, Foreign & Property",
        "lens_en": "Foreign-yoga decision = (Driver-number's lucky direction) + (3rd/9th/12th house Vedic placements) + (current dasha lord's foreign indication). All three must agree for a strong foreign-settle yoga.",
        "lens_hi": "विदेश-योग निर्णय = (Driver-नंबर की शुभ-दिशा) + (3/9/12 भाव वैदिक स्थिति) + (वर्तमान दशा-स्वामी का विदेश-संकेत)। मज़बूत विदेश-निवास योग के लिए तीनों का मिलना ज़रूरी है।",
        "lens_hg": "Foreign-yoga decision = (Driver-number ki lucky direction) + (3rd/9th/12th house Vedic placements) + (current dasha lord ka foreign indication). Strong foreign-settle yoga ke liye teeno ka agree karna zaroori hai.",
    },
    "yearly": {
        "label_en": "Yearly Forecast",
        "label_hi": "वार्षिक भविष्यवाणी",
        "label_hg": "Yearly Forecast",
        "lens_en": "Your year ahead = (Personal-Year number, derived from Driver+current year) + (current Vimshottari Mahadasha/Antardasha) + (Saturn/Jupiter transit over your Moon). Numerology gives the THEME; Vedic gives the EVENTS.",
        "lens_hi": "आगामी वर्ष = (Personal-Year अंक, Driver+वर्तमान वर्ष से) + (वर्तमान विंशोत्तरी महादशा/अंतर्दशा) + (शनि/गुरु का चंद्र पर गोचर)। संख्याशास्त्र विषय देती है; वैदिक घटनाएँ।",
        "lens_hg": "Aane wala saal = (Personal-Year number, Driver+current year se) + (current Vimshottari Mahadasha/Antardasha) + (Saturn/Jupiter ka Moon par transit). Numerology theme deti hai; Vedic events.",
    },
    "monthly": {
        "label_en": "Monthly Snapshot",
        "label_hi": "मासिक झलक",
        "label_hg": "Monthly Snapshot",
        "lens_en": "Each month gets a Personal-Month number (1-9) based on your Driver. Vedic transits add the planetary triggers. Match them to schedule launches, signings, travels, fasts.",
        "lens_hi": "हर महीने को Personal-Month अंक (1-9) मिलता है आपके Driver के आधार पर। वैदिक गोचर ग्रहीय ट्रिगर जोड़ते हैं। इनसे मिलाकर लॉन्च, हस्ताक्षर, यात्रा, उपवास तय करें।",
        "lens_hg": "Har month ko Personal-Month number (1-9) milta hai aapke Driver ke aadhar par. Vedic transits planetary triggers add karte hain. Inhe match karke launches, signings, travels, fasts schedule karein.",
    },
    "lucky": {
        "label_en": "Lucky Toolkit",
        "label_hi": "शुभ उपकरण-संग्रह",
        "label_hg": "Lucky Toolkit",
        "lens_en": "This is the most numerology-pure tier — every lucky day, date, color, gem, mantra, mobile-number, signature-style, vehicle-number, name-spelling is filtered through your Driver+Conductor pair. Use it as a daily lookup table.",
        "lens_hi": "यह सबसे संख्याशास्त्र-शुद्ध टियर है — हर शुभ दिन, तिथि, रंग, रत्न, मंत्र, मोबाइल-नंबर, हस्ताक्षर-शैली, वाहन-नंबर, नाम-वर्तनी आपके Driver+Conductor जोड़ी से फ़िल्टर है। दैनिक संदर्भ-तालिका की तरह उपयोग करें।",
        "lens_hg": "Yeh sabse numerology-pure tier hai — har lucky day, date, color, gem, mantra, mobile-number, signature-style, vehicle-number, name-spelling aapke Driver+Conductor pair se filter hai. Daily lookup table ki tarah use karein.",
    },
    "synthesis": {
        "label_en": "Master Synthesis",
        "label_hi": "मास्टर संश्लेषण",
        "label_hg": "Master Synthesis",
        "lens_en": "Final synthesis = your Driver-Conductor signature woven across all 16 prior tiers' findings. Numerology gives the headline (who you are in one number); Vedic gives the proof-points (yogas, doshas, dashas) that confirm it.",
        "lens_hi": "अंतिम संश्लेषण = सभी 16 पूर्व टियर्स के निष्कर्षों में बुना आपका Driver-Conductor हस्ताक्षर। संख्याशास्त्र शीर्षक देती है (आप एक अंक में कौन हैं); वैदिक प्रमाण-बिंदु (योग, दोष, दशाएँ) देती है।",
        "lens_hg": "Final synthesis = sabhi 16 prior tiers ke findings mein bunaa aapka Driver-Conductor signature. Numerology headline deti hai (aap ek number mein kaun ho); Vedic proof-points (yogas, doshas, dashas) deti hai jo isse confirm karte hain.",
    },
}


# ── Driver synergy verdict ────────────────────────────────────────────
# CANONICAL pair-classification — kept identical to wealth.py _money_synergy
# so the same Driver/Conductor pair never gets contradictory verdicts across
# different tiers. Enemies & same_family are mutually-exclusive (verified by
# the assertion at module-load time below).
_ENEMY_PAIRS = {
    (2, 9), (9, 2), (3, 5), (5, 3), (4, 5), (5, 4),
    (6, 7), (7, 6), (2, 5), (5, 2),
}
_FAMILY_PAIRS = {
    (1, 4), (4, 1), (1, 8), (8, 1), (2, 7), (7, 2),
    (3, 9), (9, 3), (5, 6), (6, 5),
}
# Sanity assertion — fail-fast at import if a future edit re-introduces an
# overlap (architect-flagged: (6,9) was previously in both, making SYNERGY
# unreachable for that pair).
assert not (_ENEMY_PAIRS & _FAMILY_PAIRS), (
    "framing.py: Driver-Conductor pair classification overlap → "
    f"{_ENEMY_PAIRS & _FAMILY_PAIRS}"
)


def _synergy_verdict(driver: int, conductor: int) -> str:
    if driver == conductor:
        return "FOCUSED"
    pair = (driver, conductor)
    if pair in _ENEMY_PAIRS:
        return "FRICTION"
    if pair in _FAMILY_PAIRS:
        return "SYNERGY"
    return "NEUTRAL"


def _T(lang: str, en: str, hi: str, hg: str) -> str:
    if lang == "english": return en
    if lang == "hindi":   return hi
    return hg


# ──────────────────────────────────────────────────────────────────────
# Public API: opener block (call at TOP of every tier renderer)
# ──────────────────────────────────────────────────────────────────────
def numerology_opener_block(s: Dict[str, Any], driver: int, conductor: int,
                            life_area: str, lang: str = "hinglish") -> List[Any]:
    """Return Flowables: a numerology lens paragraph that bridges driver/
    conductor numerology to the upcoming Vedic-heavy section.

    Inject this RIGHT AFTER the section title, BEFORE existing content.
    """
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    area = LIFE_AREA.get(life_area, LIFE_AREA["synthesis"])
    d_planet = PLANET_BY_DRIVER.get(driver, "—")
    c_planet = PLANET_BY_DRIVER.get(conductor, "—")
    d_planet_hi = PLANET_HI.get(d_planet, d_planet)
    c_planet_hi = PLANET_HI.get(c_planet, c_planet)
    synergy = _synergy_verdict(driver, conductor)

    synergy_label = {
        "FOCUSED":  _T(lang, "FOCUSED (Driver = Conductor, single-track power)",
                       "केंद्रित (Driver = Conductor, एकल-दिशा शक्ति)",
                       "FOCUSED (Driver = Conductor, single-track power)"),
        "SYNERGY":  _T(lang, "SYNERGY (planets in same elemental family)",
                       "तालमेल (ग्रह एक ही तत्व-परिवार में)",
                       "SYNERGY (planets same elemental family)"),
        "FRICTION": _T(lang, "FRICTION (planets are classical enemies — discipline needed)",
                       "घर्षण (ग्रह शास्त्रीय शत्रु — अनुशासन ज़रूरी)",
                       "FRICTION (planets classical enemies — discipline needed)"),
        "NEUTRAL":  _T(lang, "NEUTRAL (planets have a workable balance)",
                       "तटस्थ (ग्रहों में कार्य-योग्य संतुलन)",
                       "NEUTRAL (planets workable balance)"),
    }[synergy]

    title = _T(lang,
        f"🔢 Your Numerology Lens for this Tier → {area['label_en']}",
        f"🔢 इस टियर के लिए आपका संख्याशास्त्र लेंस → {area['label_hi']}",
        f"🔢 Iss Tier ke liye Aapka Numerology Lens → {area['label_hg']}")

    lens_text = _T(lang, area["lens_en"], area["lens_hi"], area["lens_hg"])

    body_html = (
        f"<b>{_T(lang, 'Driver', 'Driver', 'Driver')} {driver}</b> → "
        f"<b>{_T(lang, d_planet, d_planet_hi, d_planet)}</b>"
        f" &nbsp;|&nbsp; "
        f"<b>{_T(lang, 'Conductor', 'Conductor', 'Conductor')} {conductor}</b> → "
        f"<b>{_T(lang, c_planet, c_planet_hi, c_planet)}</b>"
        f" &nbsp;|&nbsp; "
        f"<b>{_T(lang, 'Pair Verdict', 'युग्म परिणाम', 'Pair Verdict')}:</b> {synergy_label}<br/><br/>"
        f"{lens_text}"
    )

    flow: List[Any] = []
    tbl = Table([[Paragraph(f"<b>{title}</b>", s["body"])],
                 [Paragraph(body_html, s["body"])]],
                colWidths=[170 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EFF6FF")),
        ("BOX",        (0, 0), (-1, -1), 0.7, colors.HexColor("#1E3A8A")),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    flow.append(tbl)
    flow.append(Spacer(1, 4 * mm))
    return flow


# ──────────────────────────────────────────────────────────────────────
# Public API: closing toolkit (call at BOTTOM of every tier renderer)
# ──────────────────────────────────────────────────────────────────────
def numerology_closing_toolkit_block(s: Dict[str, Any], driver: int, conductor: int,
                                     life_area: str, lang: str = "hinglish") -> List[Any]:
    """Return Flowables: a compact numerology toolkit card filtered for this
    life-area. Inject RIGHT BEFORE the closing PageBreak of the tier.

    DEDUPE RULE (T003): The full lucky-toolkit table (numbers, days, colors, gem,
    metal, mantra) is shown ONLY ONCE per render — on the first call. Subsequent
    tiers get a SHORT area-specific reminder only (no big table) to avoid the
    "same toolkit at every tier-end" overload the user flagged.
    """
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm

    # ── Per-render dedup state (lives on the styles dict, fresh per request) ──
    shown_areas = s.setdefault("_shown_toolkit_areas", set())
    full_shown = s.setdefault("_full_toolkit_shown", [False])  # list = mutable flag

    # Skip if THIS exact life-area was already closed in this report
    if life_area in shown_areas:
        return []
    shown_areas.add(life_area)

    area = LIFE_AREA.get(life_area, LIFE_AREA["synthesis"])
    lk = LUCKY.get(driver, LUCKY[1])
    lk_c = LUCKY.get(conductor, lk)
    d_planet = PLANET_BY_DRIVER.get(driver, "—")
    d_planet_hi = PLANET_HI.get(d_planet, d_planet)

    days_str    = ", ".join(lk["days"]    if lang != "hindi" else lk["days_hi"])
    colors_str  = ", ".join(lk["colors"]  if lang != "hindi" else lk["colors_hi"])
    nums_str    = ", ".join(str(n) for n in lk["numbers"][:6])
    avoid_str   = ", ".join(str(n) for n in lk["avoid_numbers"])
    gem_str     = lk["gem"] if lang != "hindi" else lk["gem_hi"]
    # Combine driver + conductor lucky numbers as "stronger together" set
    combo_nums  = sorted(set(lk["numbers"][:4] + lk_c["numbers"][:4]))
    combo_str   = ", ".join(str(n) for n in combo_nums)

    title = _T(lang,
        f"🎯 Your Driver-{driver} ({d_planet}) Toolkit for {area['label_en']}",
        f"🎯 आपका Driver-{driver} ({d_planet_hi}) टूलकिट — {area['label_hi']}",
        f"🎯 Aapka Driver-{driver} ({d_planet}) Toolkit for {area['label_hg']}")

    # T003: Lucky NUMBERS live ONLY in the dedicated Lucky Catalog page.
    # Closing toolkit keeps lucky days / colors / direction / gem / metal /
    # avoid / mantra (operational reminders, not duplicates of the Catalog).
    rows = [
        [_T(lang, "Lucky Days",   "शुभ दिन",   "Lucky Days"),   days_str],
        [_T(lang, "Lucky Colors", "शुभ रंग",   "Lucky Colors"), colors_str],
        [_T(lang, "Lucky Direction", "शुभ दिशा", "Lucky Direction"), lk["direction"]],
        [_T(lang, "Recommended Gem", "अनुशंसित रत्न", "Recommended Gem"), gem_str],
        [_T(lang, "Lucky Metal", "शुभ धातु", "Lucky Metal"), lk["metal"]],
        [_T(lang, "Numbers to AVOID", "जिन अंकों से बचें", "Numbers to AVOID"), avoid_str],
        [_T(lang, "Daily Mantra (108×)", "दैनिक मंत्र (108×)", "Daily Mantra (108×)"), lk["mantra"]],
    ]

    para_rows = [[Paragraph(_deva_safe(f"<b>{r[0]}</b>"), s["body"]),
                  Paragraph(_deva_safe(str(r[1])), s["body"])] for r in rows]
    tbl = Table([[Paragraph(f"<b>{title}</b>", s["body"]), ""]] + para_rows,
                colWidths=[60 * mm, 110 * mm])
    tbl.setStyle(TableStyle([
        ("SPAN",          (0, 0), (-1, 0)),
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#9333EA")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("BACKGROUND",    (0, 1), (0, -1), colors.HexColor("#FAF5FF")),
        ("BACKGROUND",    (1, 1), (1, -1), colors.white),
        ("BOX",           (0, 0), (-1, -1), 0.6, colors.HexColor("#9333EA")),
        ("INNERGRID",     (0, 1), (-1, -1), 0.3, colors.HexColor("#E9D5FF")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    closer_html = _T(lang,
        f"💎 <b>How to use this toolkit:</b> Schedule important "
        f"{area['label_en'].lower()} actions on your lucky days, wear lucky colors during "
        f"key meetings, recite the mantra 108× on those days, and avoid scheduling on "
        f"AVOID-numbers (especially when the Hindu tithi also resists). This is the "
        f"numerology compass that converts Vedic insight into <b>daily action</b>.",
        f"💎 <b>इस टूलकिट का उपयोग:</b> महत्वपूर्ण {area['label_hi']} कार्य अपने शुभ दिनों पर "
        f"नियोजित करें, मुख्य बैठकों में शुभ रंग पहनें, उन दिनों मंत्र 108× जप करें, और "
        f"AVOID-अंकों पर निर्धारण से बचें (विशेषकर जब हिंदू तिथि भी प्रतिकूल हो)। यही वह "
        f"संख्याशास्त्र-कम्पास है जो वैदिक अंतर्दृष्टि को <b>दैनिक क्रिया</b> में बदलता है।",
        f"💎 <b>Iss toolkit ka use:</b> Important {area['label_hg'].lower()} actions apne "
        f"lucky days par schedule karein, key meetings mein lucky colors pehnein, un dino "
        f"mantra 108× japein, aur AVOID-numbers par scheduling se bachein (specially jab "
        f"Hindu tithi bhi resist kare). Yahi woh numerology-compass hai jo Vedic insight "
        f"ko <b>daily action</b> mein convert karta hai.")

    flow: List[Any] = []
    flow.append(Spacer(1, 4 * mm))

    # First call in this render → show the FULL toolkit table.
    # Every subsequent call → only show the area-specific reminder
    # (avoids the same lucky-numbers / days / colors table reappearing
    # at the end of every tier).
    if not full_shown[0]:
        flow.append(tbl)
        flow.append(Spacer(1, 3 * mm))
        full_shown[0] = True
    else:
        # Compact area-specific header (replaces the full purple table)
        mini_title = _T(lang,
            f"🎯 <b>{area['label_en']} — apply the master toolkit</b>",
            f"🎯 <b>{area['label_hi']} — मास्टर टूलकिट लागू करें</b>",
            f"🎯 <b>{area['label_hg']} — master toolkit apply karein</b>")
        flow.append(Paragraph(mini_title, s["body"]))
        flow.append(Spacer(1, 2 * mm))

    flow.append(Paragraph(closer_html, s["body"]))
    flow.append(Spacer(1, 3 * mm))
    return flow
