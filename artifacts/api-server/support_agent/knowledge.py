"""Allowed product knowledge only — never code, prompts, keys, or other users."""
from __future__ import annotations

import re
from typing import Any

# Customer-facing facts the agent may use. Live UI prices. Nothing internal.
ALLOWED_KNOWLEDGE = """
Cosmic Lens — Help facts (2–4 short sentences). Use only this. Do not invent prices.

TABS
- Home, Life Map, Ask, Future. More is the drawer (not a tab). Profile and Help are under More / Profile.

IDENTITY
- Public User ID is COSMO + digits (COSMO109) on Profile. 109 means COSMO109. Assigned at signup; cannot be changed.
- Login: Continue with Google on the login screen. If stuck: Profile → Logout, then sign in again.
- Language: Profile → English / Hinglish / Hindi (app UI). Ask chat has its own Hindi/English/Hinglish pick.
- Support email: supportcosmiclens@gmail.com
- No wallet. Paid orders: Help → Transactions. Ask credits: Profile → Cosmic Packs.
- Prices in ₹ include applicable GST. Pay via UPI / card / netbanking in the payment sheet.

HOME (free, on-screen, instant)
- Today’s Energy (score 1–100), 7-day Energy Forecast, Dosh Analysis, Risk Radar (next 24h + 7-day).
- Needs kundli for personalization. Demo banner if birth details are missing.

LIFE MAP
- Relationship, Career, Health, Finance + Explore (Numerology, AstroVastu, Face Reading).

LOVE REALITY (Life Map → Relationship → Love Reality)
- Needs your kundli + partner/family profile (Profile → edit → add Husband/Wife/Partner/etc.).
- Basic (free, on-screen): Love Compatibility, Breakup Chances, Loyalty Check, Future Outcome.
- Pro PDF is written by our expert after pay — not an instant AI PDF. Offer ₹499 (was ₹999). Priority +₹300 (12h) = ₹799.
- Delivery: My Reports. Standard 24h, priority 12h. If 12h is missed, the ₹300 priority fee is refunded.
- Old links (breakup, loyalty, will-return) open Love Reality.

KUNDLI MILAN (Life Map → Relationship → Kundli Milan)
- Basic (free, on-screen): marriage structure /100 + Gun Milan /36.
- Pro PDF expert-written, not instant AI. Offer ₹699 (was ₹999). Priority +₹300 (12h) = ₹999.
- My Reports, 24h / 12h, same ₹300 priority-fee refund if 12h is missed.

CAREER / HEALTH / FINANCE (Life Map)
- Basic summaries are free on-screen. Deeper Career/Health/Finance detail is on the Pro subscription (₹499/month) via the upgrade button → Plans.
- These are on-screen tools, not expert PDFs.

NUMEROLOGY (Life Map → Explore → Numerology)
- Basic = free numbers on screen (name + DOB). Pro PDF expert-written after pay — not instant AI.
- Offer ₹299 (was ₹399). Priority +₹100 (12h) = ₹399. My Reports, 24h / 12h.

ASTROVASTU (Life Map → Explore → AstroVastu)
- Free compass / direction guide (Vastu). Basic room+direction check on screen.
- Home: 1 room ₹199, 3-room bundle ₹499, expert photo review ₹199/room, full home floor-plan PDF ₹999, full home lifetime unlock ₹2999.
- Business: Shop unlock ₹999 / Office ₹1499 / Factory ₹2999. Room photos Shop ₹399, Office ₹499, Factory ₹999. Full plan PDF Shop ₹2999, Office ₹6999, Factory ₹14999.
- Scan on-screen; PDFs in My Reports. Pro subscribers: 20% off Vastu (shown on Plans).

FACE READING (Life Map → Explore)
- Coming soon. Not live. Do not take payment for it.

ASK TAB
- V1 Cosmic Intelligence: chart Q&A. Signup: 3 free questions. Packs (Profile → Cosmic Packs or Ask): Starter ₹49 (8Q / 7 days), Popular ₹99 (15Q / 14 days), Power ₹299 (45Q / 30 days).
- V3 Live: timed chat with a Cosmic Guide on Ask (not this Help chat). 15 min ₹399, 30 min ₹699, 45 min ₹999, 60 min ₹1299. Queue + notification if busy. Transcript in My Reports.
- Birth Time Rectification: Ask landing or Profile edit link. Form with life events. Today ₹999 (was ₹2999).
- Divya Prashna: Ask landing (small link) — on-screen prashna; extra quota may need a plan.
- Chart / kundli readings belong on Ask, not this Help chat.

FUTURE TAB
- Free on-screen mahadasha / antardasha / life-area timeline. Needs kundli. Not a PDF.

MORE
- Talk to Founder (free): Instagram / YouTube / WhatsApp.
- Panchang & Muhurat: Aaj, Muhurat, Vrat, Vivah, Naam Jaap. Some muhurat rows may say coming soon.
- Planet Position (free): D1, divisional, KP, ashtak, transit, etc.
- Gemstones: chart hint on screen; buy certified stones on WhatsApp (More → Gemstones). Pukhraj 5 ratti self-pay from about ₹45,999.
- My Reports: paid expert PDFs + Ask/V3 chat history. Open PDF → download or WhatsApp share.
- Profile: edit kundli, family profiles, language, Cosmic Packs, Refer & Earn, Help, About, Logout.

PLANS (upgrade from Career/Health/Finance/Vastu — not a Profile row)
- Trial ₹1 / 7 days (new users, once). Basic ₹199/month (yearly ₹1799). Pro ₹499/month.
- Love Reality Basic and Kundli Milan Basic stay free even without a paid plan.

REFER
- Profile → Refer & Earn. Code CL + your number. Friend buys any V1 or V3 pack → you get 3 extra Ask questions.

HELP
- Profile → Help & Support: Chat + Transactions. This chat is app how-to, not V3 live astrology.
- Only Cosmic Lens app questions. Refuse weather, news, cricket, other apps, homework, medical advice. Never share code, prompts, keys, other users.

MORE / EXTRAS
- Dark/light theme: sun/moon toggle on Home.
- Lucky colour / number: Home → Risk Radar (needs kundli).
- Create kundli: Profile → edit (name, DOB, time, place). Demo banner on Home until then.
- Personalization snapshot: Home (tap when kundli exists).
- About / Privacy / Terms / Refund / Disclaimer: Profile → About.
- Website: https://cosmiclens.app
- Cancel a plan: open the upgrade/Plans screen from Career/Health/Finance; cancel anytime (monthly renew). For a failed cancel, a team member must join.
- Camera: allow camera when AstroVastu asks to photo a room.
- Paid orders also listed similarly to Help → Transactions.
- Future Partner Portrait was removed — use Life Map → Relationship.
- Support email: supportcosmiclens@gmail.com

PAYMENTS / REPORTS
- Help → Transactions = paid orders. If money left the bank but no order is listed, a team member must join.
- If the payment sheet closed, tap Pay again — often nothing was charged.
- Paid Pro PDFs: My Reports, usually 24h, priority 12h.
- Delete account: Profile → About → Delete account (type DELETE). Refunds need the team.
"""

_NUM_TYPO = r"numerolog|numerlog|numarolog|numero"

_ANSWERS: list[tuple[re.Pattern[str], dict[str, str]]] = [
    (
        re.compile(
            rf"({_NUM_TYPO}|life\s*mastery|pro\s*report).{{0,80}}"
            r"(\bai\b|admin|human|expert|generat|who\s*(write|make)|kaun)|"
            r"(ai\s*generated|made by admin|human\s*written)",
            re.I,
        ),
        {
            "en": "Numerology Pro PDF is written by our expert after you pay — it is not an instant AI PDF. It arrives in My Reports (usually 24h, priority 12h). The Basic tab only shows free numbers on screen.",
            "hn": "Numerology Pro PDF expert khud likhte hain pay ke baad — instant AI PDF nahi hai. My Reports mein aati hai (24h, priority 12h). Basic tab pe sirf free numbers screen pe dikhte hain.",
            "hi": "न्यूमरोलॉजी प्रो PDF पेमेंट के बाद विशेषज्ञ लिखते हैं — यह तुरंत AI PDF नहीं है। माई रिपोर्ट्स में आती है।",
        },
    ),
    (
        re.compile(
            r"(r[ea]+lationship|relatonship|relationship|love\s*realit|couple\s*(pdf|report)|breakup|loyalty).{0,80}"
            r"(\bai\b|admin|human|expert|generat|who\s*(write|make)|kaun)|"
            r"(r[ea]+lationship|relationship|love\s*realit|couple).{0,40}(ai\s*report|ai\s*pdf)",
            re.I,
        ),
        {
            "en": "Love Reality Pro PDF is written by our expert after you pay — it is not an instant AI PDF. Open Life Map → Relationship. Basic tools are free on screen. Pro is ₹499 (priority +₹300) and arrives in My Reports (24h / 12h).",
            "hn": "Love Reality Pro PDF expert khud likhte hain pay ke baad — instant AI PDF nahi. Life Map → Relationship. Basic free. Pro ₹499, My Reports mein (24h / 12h).",
            "hi": "लव रियलिटी प्रो PDF विशेषज्ञ लिखते हैं — यह तुरंत AI PDF नहीं है। लाइफ मैप → रिलेशनशिप।",
        },
    ),
    (
        re.compile(
            r"(milan|guna|ashtakoot|marriage\s*compat).{0,80}"
            r"(\bai\b|admin|human|expert|generat|who\s*(write|make)|kaun)",
            re.I,
        ),
        {
            "en": "Kundli Milan Pro PDF is written by our expert after you pay — not an instant AI PDF. Basic 36-guna is free on screen. Pro is ₹699 (priority +₹300), in My Reports (24h / 12h).",
            "hn": "Kundli Milan Pro PDF expert likhte hain — instant AI PDF nahi. Basic 36-guna free. Pro ₹699, My Reports mein (24h / 12h).",
            "hi": "कुंडली मिलान प्रो PDF विशेषज्ञ लिखते हैं — तुरंत AI PDF नहीं।",
        },
    ),
    (
        re.compile(
            r"(report|pdf).{0,80}\bai\b|\bai\b.{0,80}(report|pdf)|ai\s*generated",
            re.I,
        ),
        {
            "en": "Paid Pro PDFs (Love Reality, Kundli Milan, Numerology) are written by our expert after you pay — they are not instant AI PDFs. Basic tools stay free on screen. PDFs arrive in My Reports (usually 24h, priority 12h).",
            "hn": "Paid Pro PDF (Love Reality, Milan, Numerology) expert likhte hain pay ke baad — instant AI PDF nahi. Basic screen pe free. PDF My Reports mein (24h / 12h).",
            "hi": "पेड प्रो PDF विशेषज्ञ लिखते हैं — तुरंत AI PDF नहीं। माई रिपोर्ट्स में आती है।",
        },
    ),
    (
        re.compile(rf"{_NUM_TYPO}|life\s*mastery|life\s*path", re.I),
        {
            "en": "Life Map → Explore → Numerology. Basic = free numbers on screen. Pro PDF is ₹299 (Priority +₹100, 12h), written by our expert — not auto AI. After pay it arrives in My Reports.",
            "hn": "Life Map → Explore → Numerology. Basic free numbers screen pe. Pro PDF ₹299, expert likhte hain — auto AI PDF nahi. Pay ke baad My Reports mein aati hai.",
            "hi": "लाइफ मैप → एक्सप्लोर → न्यूमरोलॉजी। प्रो PDF ₹299 विशेषज्ञ लिखते हैं, ऑटो AI नहीं।",
        },
    ),
    (
        re.compile(
            r"balance|wallet|kitna\s*(paisa|balance)|account\s*me\s*kitna|"
            r"mere\s*account|paise\s*(kitne|hai)",
            re.I,
        ),
        {
            "en": "There is no wallet in Cosmic Lens. Paid orders show on Help → Transactions. Ask credits are under Profile → Cosmic Packs.",
            "hn": "App mein wallet nahi hota. Paid orders Help → Transactions pe dikhte hain. Ask questions Profile → Cosmic Packs se milte hain.",
            "hi": "ऐप में वॉलेट नहीं होता। पेड ऑर्डर हेल्प → ट्रांजैक्शन्स में दिखते हैं।",
        },
    ),
    (
        re.compile(
            r"\bprices?\b|kitna\s*(paisa|charge)|pro\s*ke\s*price|price\s*list|kitne\s*ke",
            re.I,
        ),
        {
            "en": "Numerology Pro ₹299 (+₹100 priority). Love Reality Pro ₹499 (+₹300). Kundli Milan Pro ₹699 (+₹300). V3 live from ₹399. Ask packs ₹49/₹99/₹299. Vastu 1 room ₹199. Birth Time Rectification ₹999. Plans: Trial ₹1, Basic ₹199/mo, Pro ₹499/mo.",
            "hn": "Numerology Pro ₹299. Love Reality Pro ₹499. Milan Pro ₹699. V3 ₹399 se. Ask packs ₹49/₹99/₹299. Vastu 1 room ₹199. Birth Time ₹999. Plans: Trial ₹1, Basic ₹199/mo, Pro ₹499/mo.",
            "hi": "न्यूमरोलॉजी प्रो ₹299। लव रियलिटी प्रो ₹499। मिलान प्रो ₹699। V3 ₹399 से।",
        },
    ),
    (
        re.compile(r"milan|guna|kundli\s*milan|ashtakoot|gun\s*milan|36\s*gun", re.I),
        {
            "en": "Life Map → Relationship → Kundli Milan. Basic 36-guna is free on screen. Pro PDF is ₹699 (urgent +₹300), expert-written, in My Reports (24h / 12h).",
            "hn": "Life Map → Relationship → Kundli Milan. Basic 36-guna free. Pro PDF ₹699, expert likhte hain, My Reports mein.",
            "hi": "कुंडली मिलान बेसिक फ्री। प्रो PDF ₹699 विशेषज्ञ लिखते हैं।",
        },
    ),
    (
        re.compile(
            r"love\s*realit|r[ea]+lationship|relatonship|relationship|couple\s*(pdf|report)|breakup|loyalty|"
            r"will\s*return|future\s*outcome|love\s*compat",
            re.I,
        ),
        {
            "en": "Life Map → Relationship → Love Reality. Add a partner profile in Profile → edit first. Basic tools are free on screen. Pro couple PDF is ₹499 (urgent +₹300), expert-written, in My Reports.",
            "hn": "Life Map → Relationship → Love Reality. Pehle Profile → edit pe partner kundli add karo. Basic free. Pro PDF ₹499, expert likhte hain. PDF My Reports mein.",
            "hi": "लाइफ मैप → रिलेशनशिप → लव रियलिटी। प्रो PDF ₹499 विशेषज्ञ लिखते हैं।",
        },
    ),
    (
        re.compile(
            r"business\s*vastu|shop\s*vastu|office\s*vastu|factory\s*vastu|"
            r"dukaan|karkhana",
            re.I,
        ),
        {
            "en": "Business Vastu: Shop unlock ₹999, Office ₹1499, Factory ₹2999. Room photos ₹399 / ₹499 / ₹999. Full plan PDFs ₹2999 / ₹6999 / ₹14999. Reports go to My Reports.",
            "hn": "Business Vastu: Shop ₹999, Office ₹1499, Factory ₹2999. Room photo ₹399/₹499/₹999. Full PDF ₹2999/₹6999/₹14999. Report My Reports mein.",
            "hi": "बिज़नेस वास्तु: शॉप ₹999, ऑफिस ₹1499, फ़ैक्टरी ₹2999। रिपोर्ट माई रिपोर्ट्स में।",
        },
    ),
    (
        re.compile(r"vastu|astrovastu|floor\s*plan|compass|direction\s*guide", re.I),
        {
            "en": "Life Map → Explore → AstroVastu. Free compass is on Vastu. Home: 1 room ₹199, 3 rooms ₹499, expert photo ₹199/room, full floor-plan PDF ₹999, lifetime home ₹2999. PDFs land in My Reports.",
            "hn": "Life Map → Explore → AstroVastu. Free compass Vastu pe. Home: 1 room ₹199, 3 rooms ₹499, expert photo ₹199, floor PDF ₹999, lifetime ₹2999. PDF My Reports mein.",
            "hi": "एस्ट्रोवास्तु फ्री कंपास। 1 रूम ₹199, फ़्लोर प्लान ₹999। रिपोर्ट माई रिपोर्ट्स में।",
        },
    ),
    (
        re.compile(r"\bcareer\b|naukri|job\s*vs\s*business|career\s*(report|screen|tab)", re.I),
        {
            "en": "Life Map → Career. Free on-screen score, job vs business, strengths and risks. Deeper Career detail unlocks with Pro plan ₹499/month (upgrade on that screen). Not an expert PDF.",
            "hn": "Life Map → Career. Free score, job vs business screen pe. Deep Career Pro plan ₹499/month se. Yeh expert PDF nahi hai.",
            "hi": "लाइफ मैप → करियर। बेसिक फ्री स्क्रीन पर। डीप डिटेल प्रो प्लान से।",
        },
    ),
    (
        re.compile(r"\bhealth\b|tridosha|vata|pitta|kapha|sehat", re.I),
        {
            "en": "Life Map → Health. Free on-screen score and tridosha summary. Full risk periods unlock with Pro plan ₹499/month. Not an expert PDF.",
            "hn": "Life Map → Health. Free score aur tridosha screen pe. Full health Pro plan ₹499/month se.",
            "hi": "लाइफ मैप → हेल्थ। बेसिक फ्री। डीप डिटेल प्रो प्लान से।",
        },
    ),
    (
        re.compile(r"\bfinance\b|wealth\s*score|money\s*habit|dhan|paisa\s*leak", re.I),
        {
            "en": "Life Map → Finance. Free on-screen wealth score and leakage alerts. Deeper money detail is Pro plan ₹499/month. Not an expert PDF.",
            "hn": "Life Map → Finance. Free wealth score screen pe. Deep finance Pro plan ₹499/month se.",
            "hi": "लाइफ मैप → फाइनेंस। बेसिक फ्री। डीप डिटेल प्रो प्लान से।",
        },
    ),
    (
        re.compile(
            r"today.?s?\s*energy|7[\s-]*day|forecast|dosh|risk\s*radar|"
            r"manglik|kaal\s*sarp|pitru|home\s*tab",
            re.I,
        ),
        {
            "en": "Home tab is free and instant: Today’s Energy, 7-day Forecast, Dosh Analysis, and Risk Radar. Add birth details in Profile if you see a demo banner.",
            "hn": "Home tab free hai: Today’s Energy, 7-day Forecast, Dosh, Risk Radar. Demo dikhe to Profile pe birth details daalo.",
            "hi": "होम टैब फ्री है: ऊर्जा, फोरकास्ट, दोष, रिस्क रडार।",
        },
    ),
    (
        re.compile(r"future\s*tab|insights|mahadasha|antardasha|timeline|pratyantar|\bpd\b", re.I),
        {
            "en": "Future tab shows your dasha timeline on screen (needs kundli). It is not a PDF. Chart questions still go on the Ask tab.",
            "hn": "Future tab pe dasha timeline screen pe dikhta hai (kundli chahiye). Yeh PDF nahi hai. Sawaal Ask tab pe.",
            "hi": "फ्यूचर टैब पर दशा टाइमलाइन स्क्रीन पर है। सवाल Ask टैब पर पूछें।",
        },
    ),
    (
        re.compile(r"\bv3\b|live\s*(chat|astro|guide)|talk\s*to\s*astro|cosmic\s*guide", re.I),
        {
            "en": "V3 Live is a timed chat with a Cosmic Guide on the Ask tab — 15 min ₹399, 30 min ₹699, 45 min ₹999, 60 min ₹1299. This Help chat is not V3. Transcripts go to My Reports.",
            "hn": "V3 Live Ask tab pe timed Cosmic Guide chat hai — 15 min ₹399, 30 ₹699, 45 ₹999, 60 ₹1299. Yeh Help chat V3 nahi hai.",
            "hi": "V3 लाइव Ask टैब पर है। 15 मिनट ₹399 से। यह हेल्प चैट V3 नहीं है।",
        },
    ),
    (
        re.compile(
            r"ask\s*(pack|question|quota|tab)|cosmic\s*pack|free\s*question|"
            r"v1\b|cosmic\s*intelligence",
            re.I,
        ),
        {
            "en": "Ask tab = Cosmic Intelligence V1 chart Q&A. Signup gives 3 free questions. Extra packs: ₹49 (8Q/7d), ₹99 (15Q/14d), ₹299 (45Q/30d) under Profile → Cosmic Packs. Chart questions go on Ask, not this Help chat.",
            "hn": "Ask tab pe V1 chart Q&A. Signup pe 3 free questions. Packs: ₹49/₹99/₹299 — Profile → Cosmic Packs. Kundli sawaal Ask pe poochho.",
            "hi": "Ask टैब पर V1 प्रश्न। साइनअप पर 3 फ्री। पैक प्रोफ़ाइल → कॉस्मिक पैक्स में।",
        },
    ),
    (
        re.compile(
            r"rectif|birth\s*time|janm\s*samay|precision\s*birth|time\s*correct",
            re.I,
        ),
        {
            "en": "Birth Time Rectification is on the Ask tab (also a link from Profile → edit). Fill life events, then pay ₹999 today (was ₹2999) to unlock a more precise birth time.",
            "hn": "Birth Time Rectification Ask tab pe hai (Profile → edit se bhi). Life events bharo, aaj ₹999 (pehle ₹2999).",
            "hi": "बर्थ टाइम रेक्टिफिकेशन Ask टैब पर है। आज ₹999।",
        },
    ),
    (
        re.compile(r"divya\s*prashna|prashna|horary", re.I),
        {
            "en": "Divya Prashna is a small link on the Ask tab — on-screen answers for a question asked at that moment. Extra use may need a plan. Full chart Q&A is Ask V1.",
            "hn": "Divya Prashna Ask tab pe chhota link hai — us waqt ke sawaal ka on-screen jawab. Zyada use ke liye plan lag sakta hai.",
            "hi": "दिव्य प्रश्न Ask टैब पर है। कुंडली सवाल Ask V1 पर पूछें।",
        },
    ),
    (
        re.compile(r"cosmo|user\s*id|userid", re.I),
        {
            "en": "Your User ID is the COSMO number on Profile (COSMO109…). It is assigned at signup and cannot be changed.",
            "hn": "Aapka User ID Profile pe COSMO number hai — jaise COSMO109. Signup pe milta hai, change nahi hota.",
            "hi": "आपकी यूज़र आईडी प्रोफ़ाइल पर COSMO नंबर है। यह बदल नहीं सकती।",
        },
    ),
    (
        re.compile(
            r"my\s*reports?|my\s+(pdf|report)|"
            r"(where|kahan).{0,24}(pdf|report)|"
            r"pdf\s*(kahan|where)|report\s*(kahan|where)",
            re.I,
        ),
        {
            "en": "Open My Reports from More. Paid expert PDFs appear there (usually 24h, priority 12h). Ask/V3 chats are under Talked. Check Help → Transactions for the payment.",
            "hn": "My Reports More se kholo. Paid expert PDF wahan aati hai (24h, priority 12h). Ask/V3 chats Talked mein. Payment Help → Transactions pe.",
            "hi": "माई रिपोर्ट्स मोअर से खोलें। पेड PDF वहाँ आती है।",
        },
    ),
    (
        re.compile(
            r"pdf\s*(nahi|not)|report\s*(nahi|not)|abhi\s*tak|24\s*h|12\s*h",
            re.I,
        ),
        {
            "en": "Paid Pro PDFs land in My Reports after the expert finishes — usually 24h, priority 12h. Check Help → Transactions for the payment. Love/Milan priority: if 12h is missed, the ₹300 fee is refunded.",
            "hn": "Paid Pro PDF My Reports mein aati hai — usually 24h, priority 12h. Payment Help → Transactions pe. Love/Milan 12h miss ho to ₹300 priority fee refund.",
            "hi": "पेड प्रो PDF माई रिपोर्ट्स में आती है — आमतौर पर 24 घंटे।",
        },
    ),
    (
        re.compile(
            r"payment\s*(fail|issue|problem|nahi)|pay\s*(kaise|how)|"
            r"transaction|razorpay|cashfree|upi|gst|"
            r"paise\s*(kahan|dikh)|order\s*id",
            re.I,
        ),
        {
            "en": "Open Help → Transactions to see paid orders. There is no wallet. Pay with UPI / card / netbanking. Prices include GST. If the sheet closed, tap Pay again. If money left your bank but no order is listed, a team member will need to join.",
            "hn": "Help → Transactions pe paid orders dikhte hain. Wallet nahi hota. UPI/card se pay. Sheet band ho to dobara Pay. Bank se paise kat gaye aur order nahi hai to team join karegi.",
            "hi": "हेल्प → ट्रांजैक्शन्स में पेड ऑर्डर दिखते हैं। वॉलेट नहीं होता।",
        },
    ),
    (
        re.compile(
            r"family|partner\s*profile|add\s*(husband|wife|boyfriend|girlfriend)|"
            r"extra\s*kundli|doosri\s*kundli",
            re.I,
        ),
        {
            "en": "Profile → edit → add a family or partner profile (Husband, Wife, Partner, Son, Daughter, and more). Love Reality and Kundli Milan need both people’s birth details.",
            "hn": "Profile → edit pe family/partner kundli add karo (Husband, Wife, Partner…). Love Reality aur Milan ke liye dono ki birth details chahiye.",
            "hi": "प्रोफ़ाइल → एडिट में परिवार/पार्टनर कुंडली जोड़ें।",
        },
    ),
    (
        re.compile(r"birth\s*(detail|data)|kundli\s*(edit|change)|dob\s*change|janm\s*(tithi|detail)", re.I),
        {
            "en": "Profile → edit to change name, DOB, time, and place. Add family kundlis there. For an unsure birth time, use Birth Time Rectification on the Ask tab (₹999).",
            "hn": "Profile → edit pe name, DOB, time, place change karo. Family kundli bhi add ho sakti hai. Time sure na ho to Ask pe Birth Time Rectification (₹999).",
            "hi": "प्रोफ़ाइल → एडिट में जन्म विवरण बदलें।",
        },
    ),
    (
        re.compile(r"login|otp|google\s*sign|sign\s*in|logout|log\s*out", re.I),
        {
            "en": "Open the login screen and continue with Google. If the app is stuck, Profile → Logout, then sign in again.",
            "hn": "Login screen pe Continue with Google. App atki ho to Profile → Logout karke dubara sign in.",
            "hi": "लॉगिन पर गूगल से जारी रखें। अटके तो लॉगआउट करके फिर साइन इन करें।",
        },
    ),
    (
        re.compile(
            r"app\s*(nahi|not|hang|crash|slow|open)|force\s*close|update\s*app|internet",
            re.I,
        ),
        {
            "en": "Update Cosmic Lens, check internet, force-close the app and reopen, then sign in again.",
            "hn": "App update karo, internet check karo, force-close karke kholo, phir login.",
            "hi": "ऐप अपडेट करें, इंटरनेट जाँचें, बंद करके खोलें, फिर लॉगिन करें।",
        },
    ),
    (
        re.compile(r"language|hindi|hinglish|bhasha", re.I),
        {
            "en": "Profile → language: English, Hinglish, or Hindi for the app UI. Ask chat language is picked separately before a question.",
            "hn": "Profile → language: English, Hinglish, ya Hindi. Ask chat ki language alag pick hoti hai.",
            "hi": "प्रोफ़ाइल → भाषा: अंग्रेज़ी, हिंग्लिश या हिंदी।",
        },
    ),
    (
        re.compile(r"refer|referral|\bearn\b|invite", re.I),
        {
            "en": "Profile → Refer & Earn. Your code is CL plus your number. When a friend buys any V1 or V3 pack, you get 3 extra Ask questions.",
            "hn": "Profile → Refer & Earn. Code CL + aapka number. Friend V1/V3 pack kharide to 3 extra Ask questions milte hain.",
            "hi": "प्रोफ़ाइल → रेफर एंड अर्न। मित्र पैक खरीदे तो 3 अतिरिक्त Ask प्रश्न मिलते हैं।",
        },
    ),
    (
        re.compile(r"subscription|pro\s*plan|basic\s*plan|trial|\bplans?\b|upgrade", re.I),
        {
            "en": "Plans open from Career/Health/Finance upgrade: Trial ₹1 for 7 days, Basic ₹199/month (₹1799/year), Pro ₹499/month. Love Reality and Kundli Milan Basic stay free.",
            "hn": "Plans Career/Health/Finance upgrade se: Trial ₹1 / 7 din, Basic ₹199/month, Pro ₹499/month. Love Reality aur Milan Basic free rehte hain.",
            "hi": "प्लान: ट्रायल ₹1 / 7 दिन, बेसिक ₹199/माह, प्रो ₹499/माह। मिलान और लव बेसिक फ्री।",
        },
    ),
    (
        re.compile(r"face\s*read|chehra|mukh", re.I),
        {
            "en": "Face Reading is on Life Map → Explore. Pro photo reading is not live yet (coming soon).",
            "hn": "Face Reading Life Map → Explore pe hai. Pro photo reading abhi live nahi hai — soon aayega.",
            "hi": "फेस रीडिंग लाइफ मैप → एक्सप्लोर पर है। प्रो अभी लाइव नहीं है।",
        },
    ),
    (
        re.compile(r"notif|push|alert\s*nahi", re.I),
        {
            "en": "Phone Settings → Cosmic Lens → allow notifications. Report-ready push opens My Reports. V3 ready alerts also use notifications.",
            "hn": "Phone Settings → Cosmic Lens → notifications on karo. Report ready push My Reports kholta hai.",
            "hi": "फ़ोन सेटिंग → Cosmic Lens → नोटिफिकेशन ऑन करें।",
        },
    ),
    (
        re.compile(r"panchang|muhurat|vrat|vivah|naam\s*jaap|jaap", re.I),
        {
            "en": "More → Panchang & Muhurat: Aaj, Muhurat, Vrat, Vivah, Naam Jaap. Some muhurat rows may still say coming soon.",
            "hn": "More → Panchang & Muhurat: Aaj, Muhurat, Vrat, Vivah, Naam Jaap. Kuch muhurat rows soon likha ho sakta hai.",
            "hi": "मोअर → पंचांग और मुहूर्त।",
        },
    ),
    (
        re.compile(r"planet\s*position|varga|divisional|gochar|ashtak|navatara|jaimini|\bkp\b", re.I),
        {
            "en": "More → Planet Position (free): D1, divisional charts, KP, ashtak, transit, and more. Needs kundli for your chart; otherwise a demo chart shows.",
            "hn": "More → Planet Position free hai: D1, varga, KP, ashtak, transit. Kundli na ho to demo chart dikhta hai.",
            "hi": "मोअर → प्लैनेट पोज़िशन फ्री है।",
        },
    ),
    (
        re.compile(r"gemstone|pukhraj|ratna|emerald|sapphire|yellow\s*sapphire", re.I),
        {
            "en": "More → Gemstones shows a chart hint, then WhatsApp for certified stones with photos before you pay. Pukhraj 5 ratti self-pay starts around ₹45,999.",
            "hn": "More → Gemstones pe chart hint milta hai, kharidari WhatsApp pe certified stones ke saath. Pukhraj 5 ratti roughly ₹45,999 se.",
            "hi": "मोअर → जेमस्टोन व्हाट्सऐप पर प्रमाणित रत्न।",
        },
    ),
    (
        re.compile(r"download|share\s*pdf|pdf\s*save|whatsapp\s*share", re.I),
        {
            "en": "More → My Reports → open the PDF → download or share on WhatsApp. If the list is empty, the expert report may still be in the 24h (priority 12h) window.",
            "hn": "More → My Reports → PDF kholo → download/WhatsApp share. List khali ho to 24h wait ho sakta hai.",
            "hi": "मोअर → माई रिपोर्ट्स → PDF खोलें → डाउनलोड या शेयर।",
        },
    ),
    (
        re.compile(r"delete\s*account|account\s*delete|account\s*hatao", re.I),
        {
            "en": "Profile → About → Delete account and type DELETE to confirm. For a refund first, a team member will need to join.",
            "hn": "Profile → About → Delete account, DELETE type karke confirm. Pehle refund ho to team join karegi.",
            "hi": "प्रोफ़ाइल → अबाउट → Delete account। रिफंड के लिए टीम जुड़नी होगी।",
        },
    ),
    (
        re.compile(r"talk\s*to\s*founder|founder|instagram|youtube", re.I),
        {
            "en": "Talk to Founder is under More — Instagram, YouTube, or WhatsApp (free). This Help chat is for app how-to. Paid live astrology is Ask → V3 Live.",
            "hn": "Talk to Founder More menu pe hai — Instagram / YouTube / WhatsApp (free). Yeh Help app how-to ke liye hai. Paid live Ask → V3.",
            "hi": "टॉक टू फाउंडर मोअर मेनू पर है। पेड लाइव Ask → V3।",
        },
    ),
    (
        re.compile(r"whatsapp", re.I),
        {
            "en": "WhatsApp is used from More → Talk to Founder, Gemstones, and to share a PDF from My Reports. This Help chat stays in the app.",
            "hn": "WhatsApp More → Talk to Founder, Gemstones, aur My Reports PDF share ke liye hai. Yeh Help chat app ke andar hi rehta hai.",
            "hi": "व्हाट्सऐप मोअर → फाउंडर, जेमस्टोन, और रिपोर्ट शेयर के लिए है।",
        },
    ),
    (
        re.compile(
            r"^(hi|hii|hello|hey|yo|namaste|namaskar|thanks|thank\s*you|"
            r"ok|okay|haan|hanji|bye)[\s!.]*$",
            re.I,
        ),
        {
            "en": "I can help with the Cosmic Lens app: payments, My Reports, Profile, Home, Life Map, Ask, and Future. Tell me the screen or issue.",
            "hn": "Cosmic Lens app pe help kar sakta hoon: payments, My Reports, Profile, Home, Life Map, Ask, Future. Screen ya issue batao.",
            "hi": "Cosmic Lens ऐप पर मदद कर सकता हूँ। स्क्रीन या समस्या बताएं।",
        },
    ),
    (
        re.compile(r"lucky|shubh\s*(ank|rang)|lucky\s*(colour|color|number)", re.I),
        {
            "en": "Lucky colour and number show on Home → Risk Radar after your kundli is saved. Add birth details in Profile → edit if you see Demo.",
            "hn": "Lucky colour/number Home → Risk Radar pe dikhte hain (kundli chahiye). Demo ho to Profile → edit pe birth details daalo.",
            "hi": "लकी रंग/नंबर होम → रिस्क रडार पर हैं। कुंडली प्रोफ़ाइल में जोड़ें।",
        },
    ),
    (
        re.compile(r"remed|upay|totka|mantra", re.I),
        {
            "en": "Dosh remedies are on Home → Dosh Analysis (on-screen). Gemstones are under More (WhatsApp). Chart questions go on the Ask tab.",
            "hn": "Dosh remedies Home → Dosh Analysis pe screen pe hain. Gemstones More pe WhatsApp. Kundli sawaal Ask tab pe.",
            "hi": "दोष उपाय होम → दोष एनालिसिस पर हैं। रत्न मोअर में।",
        },
    ),
    (
        re.compile(r"personalization|snapshot|demo\s*banner|create\s*kundli|kundli\s*nahi|no\s*kundli", re.I),
        {
            "en": "If Home shows Demo, open Profile → edit and save name, DOB, time, and place. Then Home personalization and charts unlock.",
            "hn": "Home pe Demo dikhe to Profile → edit pe name, DOB, time, place save karo. Phir Home personalization khul jaati hai.",
            "hi": "डेमो दिखे तो प्रोफ़ाइल → एडिट में जन्म विवरण सेव करें।",
        },
    ),
    (
        re.compile(r"dark\s*mode|light\s*mode|theme|sun\s*/\s*moon", re.I),
        {
            "en": "Switch dark or light theme with the sun/moon toggle on the Home tab.",
            "hn": "Dark/light theme Home tab pe sun/moon toggle se badlo.",
            "hi": "डार्क/लाइट थीम होम टैब के सन/मून टॉगल से बदलें।",
        },
    ),
    (
        re.compile(r"privacy|terms|disclaimer|about\s*(page|section)|website|cosmiclens\.app", re.I),
        {
            "en": "Profile → About has mission, Privacy, Terms, Refund policy, Disclaimer, and Delete account. Website: https://cosmiclens.app Support email: supportcosmiclens@gmail.com",
            "hn": "Profile → About pe Privacy, Terms, Refund, Disclaimer, Delete account. Website: https://cosmiclens.app Email: supportcosmiclens@gmail.com",
            "hi": "प्रोफ़ाइल → अबाउट में नीतियाँ हैं। वेबसाइट cosmiclens.app",
        },
    ),
    (
        re.compile(r"cancel\s*(plan|sub|membership)|unsubscribe|plan\s*band", re.I),
        {
            "en": "Plans renew monthly; cancel anytime from the Plans screen (open it from Career/Health/Finance upgrade). If cancel fails, a team member will need to join.",
            "hn": "Plan monthly renew hota hai; Career/Health/Finance upgrade → Plans se cancel anytime. Cancel na ho to team join karegi.",
            "hi": "प्लान मासिक है। करियर/हेल्थ अपग्रेड → प्लान से रद्द करें।",
        },
    ),
    (
        re.compile(r"camera|permission|photo\s*access|location\s*permission", re.I),
        {
            "en": "Allow camera when AstroVastu asks to photograph a room. Birth place uses the place search in Profile → edit, not live GPS.",
            "hn": "AstroVastu room photo ke liye camera allow karo. Birth place Profile → edit pe search se lagta hai, live GPS nahi.",
            "hi": "एस्ट्रोवास्तु फोटो के लिए कैमरा अनुमति दें। जन्म स्थान प्रोफ़ाइल एडिट में खोजें।",
        },
    ),
    (
        re.compile(r"payment\s*history|invoice|gst\s*bill", re.I),
        {
            "en": "Paid orders show on Help → Transactions (same list as payment history). Prices include GST. For a GST invoice copy, a team member will need to join.",
            "hn": "Paid orders Help → Transactions pe. Price mein GST included. GST invoice copy ke liye team join karegi.",
            "hi": "पेड ऑर्डर हेल्प → ट्रांजैक्शन्स में। GST इनवॉइस के लिए टीम।",
        },
    ),
    (
        re.compile(r"partner\s*portrait|future\s*partner", re.I),
        {
            "en": "Future Partner Portrait was removed. Use Life Map → Relationship → Love Reality or Kundli Milan instead.",
            "hn": "Future Partner Portrait hata diya gaya. Life Map → Relationship → Love Reality ya Kundli Milan use karo.",
            "hi": "फ्यूचर पार्टनर पोर्ट्रेट हटा दिया गया। लाइफ मैप → रिलेशनशिप इस्तेमाल करें।",
        },
    ),
    (
        re.compile(
            r"life\s*map|explore\s*tab|where\s+is|kahan\s+(hai|he)|"
            r"feature|screens?|tabs?|app\s*(me|mein)|cosmic\s*lens|"
            r"kya\s*kya|what\s+can|how\s+to\s+use|kaise\s+use",
            re.I,
        ),
        {
            "en": "Tabs: Home, Life Map, Ask, Future, plus More. Life Map has Relationship, Career, Health, Finance, and Explore (Numerology, AstroVastu, Face Reading). Paid PDFs: My Reports. Orders: Help → Transactions. Chart questions: Ask tab. Tell me which screen you need.",
            "hn": "Tabs: Home, Life Map, Ask, Future, aur More. Life Map pe Relationship, Career, Health, Finance, Explore (Numerology, AstroVastu, Face Reading). PDF: My Reports. Orders: Help → Transactions. Kundli sawaal: Ask. Kaunsa screen chahiye?",
            "hi": "टैब: होम, लाइफ मैप, Ask, फ्यूचर, मोअर। PDF माई रिपोर्ट्स में। ऑर्डर हेल्प → ट्रांजैक्शन्स।",
        },
    ),
]


def pick(answers: dict[str, str], lang: str) -> str:
    return answers.get(lang) or answers["hn"]


def lookup_knowledge(text: str, lang: str) -> dict[str, Any] | None:
    blob = (text or "").strip()
    if not blob:
        return None
    for pat, answers in _ANSWERS:
        if pat.search(blob):
            return {"reply": pick(answers, lang), "source": "knowledge"}
    return None
