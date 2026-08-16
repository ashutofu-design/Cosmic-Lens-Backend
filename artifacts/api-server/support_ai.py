"""Help & Support — Flask entry. Live answers come from support_agent.agent.run."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

log = logging.getLogger("support_ai")

APP_KNOWLEDGE = """
Cosmic Lens app — support facts (use only these; keep answers 2–4 short sentences).

IDENTITY
- Public User ID is COSMO + digits, e.g. COSMO109. Shown on Profile. Not a separate "Cosmo ID".
- The digits alone (109) are the same ID as COSMO109. COSMO110 in examples is only a sample, not their ID.
- If you know this user's COSMO id, say that exact id. It cannot be changed.

WHERE THINGS ARE
- Home: today's energy, 7-day forecast, Dosh, Risk Radar.
- Life Map: Relationship, Career, Health, Finance + Explore (Numerology, AstroVastu, Face Reading).
- Ask: Cosmic Intelligence V1 (chart Q&A) and V3 live timed chat with astrologer.
- Future: live dasha / PD timeline.
- More: Panchang, Planet Position, My Reports, Profile. Help is Profile → Help & Support.
- My Reports: paid PDFs + Ask chat history.

NUMEROLOGY
- Life Map → Explore → Numerology. Basic tab = free numbers on screen.
- Pro = paid human-written PDF (Life Mastery). Offer ₹299; Priority +₹100 (12h). After pay, PDF comes in My Reports (usually 24h, priority 12h).

LOVE / MILAN
- Life Map → Relationship.
- Love Reality Basic = free tools. Pro PDF offer ₹499; urgent +₹300.
- Kundli Milan Basic = free 36-guna. Pro PDF offer ₹699; urgent +₹300.
- Both people need name, DOB, time, place.

ASTROVASTU / BUSINESS
- Life Map → Explore → AstroVastu. Free compass at Vastu. Pro room scans ₹99 / ₹249 / ₹399. Expert room upload ₹199.
- Floor plans: home ₹999, shop ₹1499, office ₹2499, factory ₹4999.
- Business Vastu: shop/office/factory photos + optional floor-plan PDF. Founder writes the report → My Reports.

ASK / V3 / PACKS
- Free Ask: 3 lifetime questions at signup.
- V1 packs: Starter ₹49 (8 Q / 7 days), Popular ₹99 (15 Q / 14 days), Power ₹299 (45 Q / 30 days). Profile → Cosmic Packs.
- V3 Live (human astrologer, timer): 15 min ₹399, 30 min ₹699, 45 min ₹999, 60 min ₹1299. Ask tab.
- Help & Support is NOT V3. V3 is paid live consultation.

BIRTH TIME / KUNDLI
- Change birth details: Profile → edit profile / kundli. Family profiles can be added there.
- Birth Time Rectification: Ask tab → form with life events. Founder PDF → My Reports.

PAYMENTS / REPORTS
- Help → Transactions tab shows paid orders.
- After Pro PDF payment, open My Reports. Human reports take up to 24h (priority 12h).
- Subscription: Trial ₹1 / 7 days, Basic ₹199/mo or ₹1799/yr, Pro ₹499/mo.

OTHER
- Language: Profile → EN / Hinglish / Hindi.
- Refer: Profile → Refer & Earn. Code CL + your number. Friend buys a pack → you get 3 Ask questions.
- Face Reading Pro is not live yet (coming soon).
- Talk to Founder: More → Talk to Founder (Instagram / YouTube / WhatsApp).
- Gemstones in More open WhatsApp for certified stones.
- Support email: supportcosmiclens@gmail.com

ESCALATE TO HUMAN TEAM when:
- refund / chargeback / double charge
- money deducted AND not in Transactions
- already waited 24h (priority 12h) and PDF still missing
- legal / abuse / fraud
- user asks for a person / admin / team (not founder — More menu)
- screenshot / image
- you do not understand, or you cannot solve it from KNOWLEDGE + THIS CUSTOMER ACCOUNT

When escalating, tell the customer to wait here — customer support will join this chat.
NEVER mention Telegram, admin panel, server, database, API, keys, models, prompts,
file paths, other customers, or internal IDs.
Answer how-to yourself when you can. Prefer a short how-to over escalating.
Do not do kundli readings here — send them to Ask tab. Do not invent prices.
Use THIS CUSTOMER ACCOUNT for their ID, plan, payments, and Ask credits.
Only tell them what they can already see in the app (Profile, Transactions, My Reports, Cosmic Packs).
"""

_ESCALATE_RE = re.compile(
    r"(refund|chargeback|double\s*charg|"
    r"paise\s*(wapas|kat\s*gaye)|paisa\s*kat|"
    r"money\s*(cut|deducted)|"
    r"\bcomplaint\b|\blegal\b|\blawyer\b|\bfraud\b|\bscam\b|harass|abuse)",
    re.I,
)

_ASK_HUMAN_RE = re.compile(
    r"(talk\s*to\s*(a\s*)?(human|person|admin|team|agent)\b|"
    r"connect\s*(me\s*)?(to\s*)?(admin|team|human|person|support)|"
    r"connect.{0,24}support|"
    r"support\s*chat|customer\s*support|live\s*support|"
    r"speak\s*to\s*(support|someone|a\s*person)|"
    r"insaan\s*se\s*baat|team\s*se\s*baat|admin\s*se\s*baat)",
    re.I,
)

_STUCK_RE = re.compile(
    r"(samajh\s*n[aei]|samajh\s*ni|solve\s*nahi|nahi\s*(hua|ho\s*raha)|"
    r"still\s*(not|same|broken)|doesn't\s*help|does\s*not\s*help|"
    r"not\s*working|kuch\s*nahi\s*hua|clear\s*nahi|"
    r"that'?s\s+not|not\s+showing|isn'?t\s+showing|still\s+not\s+show)",
    re.I,
)

_TX_ISSUE_RE = re.compile(
    r"(wallet|transaction|payment|order).{0,50}(not showing|isn'?t showing|missing|not\s+in)|"
    r"(not showing|isn'?t showing|missing|nahi\s*dikh).{0,50}(wallet|transaction|payment|order)|"
    r"done\s+(a\s+|one\s+)?transaction|"
    r"transaction.{0,30}(wallet|not show)",
    re.I,
)

_INTERNAL_LEAK_RE = re.compile(
    r"(api[_-]?key|openai|gpt-4|gpt-3|SUPPORT_AI|OPENAI_|TELEGRAM_|FOUNDER_|"
    r"\bpm2\b|\bvps\b|flask_app|\.env\b|postgres|sqlalchemy|webhook|"
    r"admin\s*(panel|token|key)|thread_id|support_threads|razorpay.?secret|"
    r"cashfree.?secret|localhost:\d+|127\.0\.0\.1|internal\s+id|"
    r"telegram|database\s+id|prompt\s+injection)",
    re.I,
)

_WAIT = {
    "en": "I couldn’t fully resolve this here. Customer support will join this chat shortly — please wait, they’ll reply here.",
    "hn": "Yeh yahan clear nahi ho paaya. Customer support abhi is chat mein aayenge — thoda wait kariye, yahin reply aayega.",
    "hi": "यह यहाँ पूरा हल नहीं हो पाया। कस्टमर सपोर्ट अभी इस चैट में आएंगे — थोड़ा इंतज़ार करें, यहीं जवाब आएगा।",
}

_COSMO_RE = re.compile(r"cosmo|user\s*id|userid", re.I)
_COSMO_FOLLOW_RE = re.compile(
    r"(dikha|dikh raha|showing|mera to|meri to|sirf|only|lekin|\bbut\b|\b\d{2,4}\b)",
    re.I,
)

_FAQ: list[tuple[re.Pattern[str], dict[str, str]]] = [
    (
        re.compile(
            r"balance|wallet|kitna\s*(paisa|balance)|account\s*me\s*kitna|"
            r"mere\s*account|paise\s*(kitne|hai)",
            re.I,
        ),
        {
            "en": "There is no wallet balance in Cosmic Lens. Paid orders show on Help → Transactions. Ask question credits are under Profile → Cosmic Packs.",
            "hn": "App mein wallet balance nahi hota. Paid orders Help → Transactions pe dikhte hain. Ask questions Profile → Cosmic Packs se milte hain.",
            "hi": "ऐप में वॉलेट बैलेंस नहीं होता। पेड ऑर्डर हेल्प → ट्रांजैक्शन्स में दिखते हैं। Ask क्रेडिट प्रोफ़ाइल → कॉस्मिक पैक्स में।",
        },
    ),
    (
        re.compile(r"\bprices?\b|kitna\s*(paisa|charge)|pro\s*ke\s*price", re.I),
        {
            "en": "Numerology Pro ₹299 (priority +₹100). Love Reality Pro ₹499 (+₹300 urgent). Kundli Milan Pro ₹699 (+₹300 urgent). V3 live from ₹399. Ask packs ₹49/₹99/₹299. Details in Cosmic Packs / each screen.",
            "hn": "Numerology Pro ₹299 (priority +₹100). Love Reality Pro ₹499 (+₹300 urgent). Milan Pro ₹699 (+₹300 urgent). V3 live ₹399 se. Ask packs ₹49/₹99/₹299.",
            "hi": "न्यूमरोलॉजी प्रो ₹299। लव रियलिटी प्रो ₹499। मिलान प्रो ₹699। V3 लाइव ₹399 से। Ask पैक ₹49/₹99/₹299।",
        },
    ),
    (
        re.compile(
            r"(numerolog|numerlog|numarolog|life\s*mastery|pro\s*report).{0,80}"
            r"(ai|admin|human|expert|generat|who\s*(write|make)|kaun)|"
            r"(ai\s*generated|made by admin|human\s*written|expert\s*(likh|write))",
            re.I,
        ),
        {
            "en": "Numerology Pro PDF is written by our expert after you pay — it is not an instant AI PDF. It arrives in My Reports (usually 24h, priority 12h). The Basic tab only shows free numbers on screen.",
            "hn": "Numerology Pro PDF expert khud likhte hain pay ke baad — instant AI PDF nahi hai. My Reports mein aati hai (24h, priority 12h). Basic tab pe sirf free numbers screen pe dikhte hain.",
            "hi": "न्यूमरोलॉजी प्रो PDF पेमेंट के बाद विशेषज्ञ लिखते हैं — यह तुरंत AI PDF नहीं है। माई रिपोर्ट्स में आती है (24 घंटे)। बेसिक टैब पर केवल फ्री नंबर स्क्रीन पर हैं।",
        },
    ),
    (
        re.compile(r"numerolog|numerlog|numarolog|life\s*mastery|life\s*path", re.I),
        {
            "en": "Life Map → Explore → Numerology. Basic = free numbers on screen. Pro PDF is ₹299 (Priority +₹100, 12h), written by our expert — not auto AI. After pay it arrives in My Reports.",
            "hn": "Life Map → Explore → Numerology. Basic free numbers screen pe. Pro PDF ₹299, Priority +₹100 (12h), expert likhte hain — auto AI PDF nahi. Pay ke baad My Reports mein aati hai.",
            "hi": "लाइफ मैप → एक्सप्लोर → न्यूमरोलॉजी। बेसिक स्क्रीन पर फ्री है। प्रो PDF ₹299 विशेषज्ञ लिखते हैं, ऑटो AI नहीं। पेमेंट के बाद माई रिपोर्ट्स में आएगी।",
        },
    ),
    (
        re.compile(r"love\s*realit|breakup|loyalty", re.I),
        {
            "en": "Life Map → Relationship → Love Reality. Basic tools are free. Pro couple PDF is ₹499 (urgent +₹300). Need both people’s birth details. PDF goes to My Reports.",
            "hn": "Life Map → Relationship → Love Reality. Basic free hai. Pro PDF ₹499, urgent +₹300. Dono ki birth details chahiye. PDF My Reports mein aati hai.",
            "hi": "लाइफ मैप → रिलेशनशिप → लव रियलिटी। बेसिक फ्री है। प्रो PDF ₹499, अर्जेंट +₹300। दोनों की जन्म डिटेल चाहिए। PDF माई रिपोर्ट्स में आएगी।",
        },
    ),
    (
        re.compile(r"milan|guna|kundli\s*milan|ashtakoot", re.I),
        {
            "en": "Life Map → Relationship → Kundli Milan. Basic 36-guna is free. Pro PDF is ₹699 (urgent +₹300). PDF lands in My Reports.",
            "hn": "Life Map → Relationship → Kundli Milan. Basic 36-guna free. Pro PDF ₹699, urgent +₹300. PDF My Reports mein.",
            "hi": "लाइफ मैप → रिलेशनशिप → कुंडली मिलान। बेसिक 36 गुण फ्री। प्रो PDF ₹699, अर्जेंट +₹300। PDF माई रिपोर्ट्स में।",
        },
    ),
    (
        re.compile(r"vastu|astrovastu|floor\s*plan|business\s*vastu", re.I),
        {
            "en": "Life Map → Explore → AstroVastu. Free compass is available. Pro room scans ₹99/₹249/₹399; expert room ₹199. Floor plans: home ₹999, shop ₹1499, office ₹2499, factory ₹4999. Photos you upload go to the expert; report comes in My Reports.",
            "hn": "Life Map → Explore → AstroVastu. Free compass hai. Pro room scan ₹99/₹249/₹399, expert room ₹199. Floor plan: home ₹999, shop ₹1499, office ₹2499, factory ₹4999. Photos expert ko jaati hain; report My Reports mein.",
            "hi": "लाइफ मैप → एक्सप्लोर → एस्ट्रोवास्तु। फ्री कंपास है। प्रो रूम स्कैन ₹99/₹249/₹399। फ्लोर प्लान होम ₹999, शॉप ₹1499। रिपोर्ट माई रिपोर्ट्स में आएगी।",
        },
    ),
    (
        re.compile(r"\bv3\b|live\s*(chat|astro)|talk\s*to\s*astro", re.I),
        {
            "en": "V3 Live is a timed chat with an astrologer on the Ask tab. Packs: 15 min ₹399, 30 min ₹699, 45 min ₹999, 60 min ₹1299. This Help chat is not V3.",
            "hn": "V3 Live Ask tab pe timed astrologer chat hai. 15 min ₹399, 30 min ₹699, 45 min ₹999, 60 min ₹1299. Yeh Help chat V3 nahi hai.",
            "hi": "V3 लाइव Ask टैब पर टाइमर वाली ज्योतिष चैट है। 15 मिनट ₹399, 30 मिनट ₹699। यह हेल्प चैट V3 नहीं है।",
        },
    ),
    (
        re.compile(r"ask\s*(pack|question|quota)|cosmic\s*pack|free\s*question", re.I),
        {
            "en": "Signup gives 3 free Ask questions. Extra packs: ₹49 (8Q/7d), ₹99 (15Q/14d), ₹299 (45Q/30d) under Profile → Cosmic Packs. Chart questions go on the Ask tab, not here.",
            "hn": "Signup pe 3 free Ask questions. Packs: ₹49 (8Q/7 din), ₹99 (15Q/14 din), ₹299 (45Q/30 din) — Profile → Cosmic Packs. Kundli sawaal Ask tab pe poochho.",
            "hi": "साइनअप पर 3 फ्री Ask प्रश्न। पैक: ₹49, ₹99, ₹299 — प्रोफ़ाइल → कॉस्मिक पैक्स। कुंडली सवाल Ask टैब पर पूछें।",
        },
    ),
    (
        re.compile(r"my\s*reports?|pdf\s*(kahan|where)|report\s*(kahan|where)", re.I),
        {
            "en": "Open My Reports from More or Profile. Paid Pro PDFs appear there after the expert finishes (usually 24h, priority 12h). Check the Transactions tab here for the payment.",
            "hn": "My Reports More/Profile se kholo. Paid Pro PDF expert ke baad wahan aati hai (24h, priority 12h). Payment ke liye yahan Transactions tab dekho.",
            "hi": "माई रिपोर्ट्स मोअर या प्रोफ़ाइल से खोलें। पेड प्रो PDF विशेषज्ञ के बाद वहाँ आती है (आमतौर पर 24 घंटे)।",
        },
    ),
    (
        re.compile(r"birth\s*(detail|time|data)|kundli\s*(edit|change)|dob\s*change", re.I),
        {
            "en": "Profile → edit profile to change name, DOB, time, and place. You can add family kundlis there. For minute-accurate time, use Birth Time Rectification on the Ask tab.",
            "hn": "Profile → edit pe name, DOB, time, place change karo. Family kundli bhi add ho sakti hai. Exact time ke liye Ask tab pe Birth Time Rectification.",
            "hi": "प्रोफ़ाइल → एडिट में नाम, जन्म तारीख, समय, स्थान बदलें। सटीक समय के लिए Ask टैब पर बर्थ टाइम रेक्टिफिकेशन।",
        },
    ),
    (
        re.compile(r"language|hindi|hinglish|bhasha", re.I),
        {
            "en": "Profile → language: English, Hinglish, or Hindi. It changes the app UI.",
            "hn": "Profile → language: English, Hinglish, ya Hindi. App UI badal jaati hai.",
            "hi": "प्रोफ़ाइल → भाषा: अंग्रेज़ी, हिंग्लिश या हिंदी। ऐप की भाषा बदल जाती है।",
        },
    ),
    (
        re.compile(r"refer|referral|earn", re.I),
        {
            "en": "Profile → Refer & Earn. Your code is CL plus your number. When a friend buys a V1/V3 pack, you get 3 extra Ask questions.",
            "hn": "Profile → Refer & Earn. Code CL + aapka number. Friend pack kharide to aapko 3 extra Ask questions milte hain.",
            "hi": "प्रोफ़ाइल → रेफर एंड अर्न। कोड CL + आपका नंबर। मित्र पैक खरीदे तो 3 अतिरिक्त Ask प्रश्न मिलते हैं।",
        },
    ),
    (
        re.compile(r"subscription|pro\s*plan|basic\s*plan|trial", re.I),
        {
            "en": "Plans: Trial ₹1 for 7 days, Basic ₹199/month or ₹1799/year, Pro ₹499/month. Some deep tools need Pro. Love Reality and Kundli Milan Basic stay free.",
            "hn": "Plans: Trial ₹1 / 7 din, Basic ₹199/month ya ₹1799/year, Pro ₹499/month. Love Reality aur Milan Basic free rehte hain.",
            "hi": "प्लान: ट्रायल ₹1 / 7 दिन, बेसिक ₹199/माह, प्रो ₹499/माह। लव रियलिटी और मिलान बेसिक फ्री रहते हैं।",
        },
    ),
    (
        re.compile(r"face\s*read", re.I),
        {
            "en": "Face Reading is on Life Map → Explore. Pro photo reading is not live yet (coming soon).",
            "hn": "Face Reading Life Map → Explore pe hai. Pro photo reading abhi live nahi hai — soon aayega.",
            "hi": "फेस रीडिंग लाइफ मैप → एक्सप्लोर पर है। प्रो फोटो रीडिंग अभी लाइव नहीं है।",
        },
    ),
    (
        re.compile(
            r"pdf\s*(nahi|not)|report\s*(nahi|not)|pdf\s*(aayi|aaya|received)|"
            r"abhi\s*tak|24\s*h|12\s*h|kitne\s*(din|hour|ghante)",
            re.I,
        ),
        {
            "en": "Paid Pro PDFs land in My Reports after the expert writes them — usually 24h, priority 12h. Check More → My Reports, and Help → Transactions for the payment. If you already waited that long, type “team se baat” with your order ID.",
            "hn": "Paid Pro PDF My Reports mein aati hai — usually 24h, priority 12h. More → My Reports dekho, payment Help → Transactions pe. Agar wait ho chuka hai to “team se baat” likho + order ID.",
            "hi": "पेड प्रो PDF माई रिपोर्ट्स में आती है — आमतौर पर 24 घंटे, प्रायोरिटी 12 घंटे। इंतज़ार हो चुका हो तो “team se baat” लिखें।",
        },
    ),
    (
        re.compile(
            r"payment\s*(fail|issue|problem|nahi)|pay\s*(kaise|how)|"
            r"transaction|razorpay|paise\s*(kahan|dikh)|order\s*id",
            re.I,
        ),
        {
            "en": "Open Help → Transactions to see paid orders. If the payment sheet closed without success, tap pay again — usually nothing was charged. If money left your bank but the order is missing here, type “team se baat” and share the order ID.",
            "hn": "Help → Transactions pe paid orders dikhte hain. Sheet band ho gayi ho to dobara Pay dabao — aksar charge nahi hota. Bank se paise kat gaye aur yahan order nahi hai to “team se baat” + order ID.",
            "hi": "हेल्प → ट्रांजैक्शन्स में पेड ऑर्डर दिखते हैं। पेमेंट फेल हो तो फिर से पे करें। पैसे कट गए और ऑर्डर नहीं दिखे तो “team se baat” लिखें।",
        },
    ),
    (
        re.compile(r"login|otp|google\s*sign|sign\s*in|logout|log\s*out", re.I),
        {
            "en": "Login with phone OTP or Google. Profile → Logout, then sign in again if the app is stuck. OTP comes on SMS; wait 30s before resend.",
            "hn": "Login phone OTP ya Google se. App atki ho to Profile → Logout karke dubara sign in. OTP SMS pe aata hai.",
            "hi": "लॉगिन फोन OTP या गूगल से। ऐप अटके तो प्रोफ़ाइल → लॉगआउट करके फिर साइन इन करें।",
        },
    ),
    (
        re.compile(
            r"app\s*(nahi|not|hang|crash|slow|open)|force\s*close|update\s*app|internet",
            re.I,
        ),
        {
            "en": "Update Cosmic Lens, check internet, force-close the app and reopen, then re-login. If it still fails, type “team se baat” with your phone model.",
            "hn": "App update karo, internet check karo, app band karke kholo, phir login. Phir bhi na chale to “team se baat” + phone model.",
            "hi": "ऐप अपडेट करें, इंटरनेट चेक करें, ऐप बंद करके खोलें, फिर लॉगिन। फिर भी न चले तो “team se baat” लिखें।",
        },
    ),
    (
        re.compile(r"notif|push|alert\s*nahi", re.I),
        {
            "en": "Phone Settings → Cosmic Lens → allow notifications. Report-ready push opens My Reports. Also check the app isn’t on mute/Do Not Disturb.",
            "hn": "Phone Settings → Cosmic Lens → notifications on karo. Report ready push My Reports kholta hai. DND/mute off rakho.",
            "hi": "फ़ोन सेटिंग → Cosmic Lens → नोटिफिकेशन ऑन करें। रिपोर्ट रेडी पुश माई रिपोर्ट्स खोलता है।",
        },
    ),
    (
        re.compile(r"founder|instagram|youtube|whatsapp", re.I),
        {
            "en": "Talk to Founder is under More → Talk to Founder (Instagram / YouTube / WhatsApp). This Help chat is for app how-to; V3 Live on Ask is paid timed astrology chat.",
            "hn": "Founder se baat: More → Talk to Founder (Instagram / YouTube / WhatsApp). Yeh Help app how-to ke liye hai. Paid live chat Ask → V3 Live.",
            "hi": "फाउंडर: मोअर → Talk to Founder। यह हेल्प ऐप हाउ-टू के लिए है। पेड लाइव चैट Ask → V3।",
        },
    ),
    (
        re.compile(r"panchang|muhurat|vrat|vivah", re.I),
        {
            "en": "More → Panchang & Muhurat: aaj, muhurat, vrat, vivah, naam jaap.",
            "hn": "More → Panchang & Muhurat: aaj, muhurat, vrat, vivah, naam jaap.",
            "hi": "मोअर → पंचांग और मुहूर्त: आज, मुहूर्त, व्रत, विवाह।",
        },
    ),
    (
        re.compile(r"planet\s*position|varga|divisional|gochar", re.I),
        {
            "en": "More → Planet Position: live planets, D1/varga, dasha, ashtak, transit, KP.",
            "hn": "More → Planet Position: live planets, D1/varga, dasha, transit, KP.",
            "hi": "मोअर → प्लैनेट पोज़िशन: लाइव ग्रह, वर्ग, दशा, ट्रांज़िट, KP।",
        },
    ),
    (
        re.compile(r"forecast|dasha|lucky|dosh|risk\s*radar", re.I),
        {
            "en": "Home has today’s energy, 7-day forecast, Dosh, and Risk Radar (lucky colour/number). Future tab shows live dasha.",
            "hn": "Home pe aaj ki energy, 7-day forecast, Dosh, Risk Radar (lucky colour/number). Future tab pe live dasha.",
            "hi": "होम पर आज की ऊर्जा, 7-दिन फोरकास्ट, दोष, रिस्क रडार। फ्यूचर टैब पर लाइव दशा।",
        },
    ),
    (
        re.compile(r"career|health|finance|divya\s*prashna", re.I),
        {
            "en": "Career, Health, Finance are on Life Map. Divya Prashna (horary) is on the Ask tab. Chart questions also go on Ask — not this Help chat.",
            "hn": "Career, Health, Finance Life Map pe hain. Divya Prashna Ask tab pe. Kundli sawaal Ask pe poochho, yahan nahi.",
            "hi": "करियर, हेल्थ, फाइनेंस लाइफ मैप पर हैं। दिव्य प्रश्न Ask टैब पर। कुंडली सवाल Ask पर पूछें।",
        },
    ),
    (
        re.compile(r"download|share\s*pdf|pdf\s*save", re.I),
        {
            "en": "More → My Reports → open the PDF → download or share. If the list is empty, the expert report may still be in the 24h (priority 12h) window.",
            "hn": "More → My Reports → PDF kholo → download/share. List khali ho to 24h (priority 12h) wait ho sakta hai.",
            "hi": "मोअर → माई रिपोर्ट्स → PDF खोलें → डाउनलोड/शेयर। सूची खाली हो तो 24 घंटे तक इंतज़ार हो सकता है।",
        },
    ),
    (
        re.compile(r"delete\s*account|account\s*delete|account\s*hatao", re.I),
        {
            "en": "Open About/legal → Delete account and confirm there. That removes the account. For a refund first, type “team se baat”.",
            "hn": "About/legal → Delete account se confirm karke account hat ta hai. Pehle refund chahiye to “team se baat” likho.",
            "hi": "अबाउट/लीगल → Delete account से खाता हटता है। पहले रिफंड चाहिए तो “team se baat” लिखें।",
        },
    ),
    (
        re.compile(r"gemstone|pukhraj|ratna", re.I),
        {
            "en": "More → Gemstones opens WhatsApp for certified Vedic stones. In-app Face Reading Pro is not live yet.",
            "hn": "More → Gemstones WhatsApp kholta hai certified stones ke liye.",
            "hi": "मोअर → जेमस्टोन व्हाट्सऐप खोलता है प्रमाणित रत्नों के लिए।",
        },
    ),
]


def _lang(raw: str | None) -> str:
    v = (raw or "").strip().lower()
    if v in ("hi", "hn", "en"):
        return v
    return "hn"


_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_HINGLISH = re.compile(
    r"\b(kya|hai|hain|nahi|nahin|kaise|kahan|kaha|meri|mera|mere|mujhe|"
    r"aap|ji|pooch|dikhegi|dikhega|kitna|kitne|paise|paisa|karun|karo|"
    r"chahiye|abhi|tak|wala|wali|ke\s+liye|batao|bataye|samjha|please\s+ji)\b",
    re.I,
)


def detect_reply_lang(text: str, preferred: str | None = None) -> str:
    """Reply in the language the user just typed (Hinglish or English)."""
    try:
        from support_agent.intent import detect_lang

        return detect_lang(text, preferred)
    except Exception:
        blob = text or ""
        if _DEVANAGARI.search(blob):
            return "hi"
        if _HINGLISH.search(blob):
            return "hn"
        letters = "".join(re.findall(r"[A-Za-z]+", blob))
        if len(letters) >= 8:
            return "en"
        return _lang(preferred)


def _polite(reply: str, lang: str) -> str:
    r = (reply or "").strip()
    if not r:
        return r
    if lang == "en":
        r = re.sub(r"^Ji,\s*", "", r, flags=re.I).strip()
    if re.match(
        r"^(ji[, ]|sure\b|happy to help|of course|please\b|namaste|"
        r"sorry|bilkul|zaroor|thank)",
        r,
        re.I,
    ):
        if lang == "en" and re.match(r"^ji[, ]", r, re.I):
            r = re.sub(r"^Ji,\s*", "", r, flags=re.I).strip()
        else:
            return r
    if lang == "en":
        return f"Happy to help. {r}"
    if lang == "hi":
        return f"जी, {r}"
    return f"Ji, {r}"


def _pick(answers: dict[str, str], lang: str) -> str:
    return answers.get(lang) or answers["hn"]


def wait_for_support_reply(lang: str) -> str:
    return _polite(_pick(_WAIT, lang), lang)


def scrub_customer_reply(reply: str, lang: str) -> str:
    """Strip internal leaks. If a leak is found, replace with the wait message."""
    text = (reply or "").strip()
    if not text:
        return wait_for_support_reply(lang)
    if _INTERNAL_LEAK_RE.search(text):
        return wait_for_support_reply(lang)
    return text


def _normalize_cosmo(raw: str) -> str:
    s = (raw or "").strip().upper()
    if not s:
        return ""
    if s.startswith("COSMO"):
        return s
    if s.isdigit():
        return f"COSMO{s}"
    return s


def _cosmo_reply(lang: str, cosmo_user_id: str, *, followup: bool) -> str:
    cid = _normalize_cosmo(cosmo_user_id)
    if followup:
        if cid:
            return _pick(
                {
                    "en": f"Yes — {cid} is your User ID. The number on Profile (like 109) is the same as COSMO109. COSMO110 in the earlier reply was only an example. It cannot be changed.",
                    "hn": f"Haan, {cid} hi aapka User ID hai. Jo number Profile pe dikh raha hai (jaise 109) wahi COSMO ke saath hota hai — COSMO109. Pehle wala COSMO110 sirf example tha. Change nahi hota.",
                    "hi": f"हाँ, {cid} आपकी यूज़र आईडी है। प्रोफ़ाइल पर जो नंबर दिखे (जैसे 109) वही COSMO109 है। COSMO110 केवल उदाहरण था। बदल नहीं सकती।",
                },
                lang,
            )
        return _pick(
            {
                "en": "The number on Profile is your User ID. COSMO + digits are the same thing — 109 means COSMO109. COSMO110 was only an example. It is assigned at signup and cannot be changed.",
                "hn": "Jo number Profile pe dikh raha hai wahi aapka User ID hai. COSMO aur number ek hi cheez hai — 109 matlab COSMO109. COSMO110 sirf example tha. Signup pe milta hai, change nahi hota.",
                "hi": "प्रोफ़ाइल पर जो नंबर दिखे वही आपकी आईडी है। 109 मतलब COSMO109। COSMO110 केवल उदाहरण था। साइनअप पर मिलती है, बदल नहीं सकती।",
            },
            lang,
        )
    if cid:
        return _pick(
            {
                "en": f"Your User ID on Profile is {cid}. It is assigned at signup and cannot be changed.",
                "hn": f"Aapka User ID Profile pe {cid} hai. Signup pe milta hai, change nahi hota.",
                "hi": f"प्रोफ़ाइल पर आपकी यूज़र आईडी {cid} है। यह साइनअप पर मिलती है, बदल नहीं सकती।",
            },
            lang,
        )
    return _pick(
        {
            "en": "Your User ID is the COSMO number on Profile (COSMO109, COSMO110…). It is assigned at signup and cannot be changed.",
            "hn": "Aapka User ID Profile pe COSMO number hai — jaise COSMO109. Signup pe milta hai, change nahi hota.",
            "hi": "आपकी यूज़र आईडी प्रोफ़ाइल पर COSMO नंबर है (जैसे COSMO109)। यह साइनअप पर मिलती है, बदल नहीं सकती।",
        },
        lang,
    )


def _purchases_from_card(account_card: str) -> list[str]:
    out: list[str] = []
    for line in (account_card or "").splitlines():
        s = line.strip()
        if s.startswith("- "):
            out.append(s[2:].strip()[:80])
    return out


def _tx_account_reply(lang: str, account_card: str) -> tuple[str, bool]:
    """Check this account's payments. Returns (reply, escalate)."""
    rows = _purchases_from_card(account_card)
    none = "Recent payments: none" in (account_card or "")
    if rows:
        listed = "; ".join(rows[:5])
        return (
            _pick(
                {
                    "en": (
                        "There is no wallet in Cosmic Lens. I checked this account — "
                        f"Help → Transactions currently shows: {listed}. "
                        "If the payment you made is not in that list, customer support "
                        "will join this chat shortly — please wait here."
                    ),
                    "hn": (
                        "App mein wallet nahi hota. Is account pe Help → Transactions mein "
                        f"abhi yeh dikh raha hai: {listed}. "
                        "Agar aapka payment is list mein nahi hai to customer support "
                        "yahin join karenge — wait kariye."
                    ),
                    "hi": (
                        "ऐप में वॉलेट नहीं होता। इस खाते पर ट्रांजैक्शन्स में "
                        f"अभी यह दिख रहा है: {listed}। "
                        "अगर आपका पेमेंट सूची में नहीं है तो कस्टमर सपोर्ट यहीं आएंगे।"
                    ),
                },
                lang,
            ),
            True,
        )
    if none or account_card:
        return (
            _pick(
                {
                    "en": (
                        "There is no wallet in Cosmic Lens. I checked this account and "
                        "do not see a paid order on Help → Transactions yet. "
                        "If money was deducted, customer support will join this chat "
                        "shortly — please wait here."
                    ),
                    "hn": (
                        "App mein wallet nahi hota. Is account pe Help → Transactions mein "
                        "abhi koi paid order nahi dikha. Agar paise kat gaye hon to "
                        "customer support yahin join karenge — wait kariye."
                    ),
                    "hi": (
                        "ऐप में वॉलेट नहीं होता। इस खाते पर अभी कोई पेड ऑर्डर नहीं दिखा। "
                        "अगर पैसे कट गए हैं तो कस्टमर सपोर्ट यहीं आएंगे।"
                    ),
                },
                lang,
            ),
            True,
        )
    return (
        _pick(
            {
                "en": "There is no wallet in Cosmic Lens. Paid orders show on Help → Transactions. Ask credits are under Profile → Cosmic Packs.",
                "hn": "App mein wallet balance nahi hota. Paid orders Help → Transactions pe dikhte hain. Ask questions Profile → Cosmic Packs se milte hain.",
                "hi": "ऐप में वॉलेट बैलेंस नहीं होता। पेड ऑर्डर हेल्प → ट्रांजैक्शन्स में दिखते हैं।",
            },
            lang,
        ),
        False,
    )


def _prior_user_texts(history: list[dict[str, Any]] | None) -> list[str]:
    users = [
        str(m.get("text") or "").strip()
        for m in (history or [])
        if isinstance(m, dict) and m.get("sender") == "user"
    ]
    return users[:-1]


def _rule_answer(
    text: str,
    lang: str,
    *,
    has_image: bool,
    history: list[dict[str, Any]] | None = None,
    cosmo_user_id: str = "",
    account_card: str = "",
) -> dict[str, Any] | None:
    if has_image:
        return {
            "escalate": True,
            "reply": _pick(
                {
                    "en": "Got your screenshot. Connecting you to the team — they’ll reply here.",
                    "hn": "Screenshot mil gayi. Team se connect kar rahe hain — yahin reply aayega.",
                    "hi": "स्क्रीनशॉट मिल गई। टीम से कनेक्ट कर रहे हैं — यहीं जवाब आएगा।",
                },
                lang,
            ),
            "source": "image",
        }
    blob = (text or "").strip()
    if not blob:
        return None
    prior = _prior_user_texts(history)
    if _ASK_HUMAN_RE.search(blob):
        if prior:
            return {
                "escalate": True,
                "reply": _pick(_WAIT, lang),
                "source": "unsolved",
            }
        return {
            "escalate": False,
            "reply": _pick(
                {
                    "en": "I can check this account first — payments, PDFs, login, COSMO ID. Tell me the issue. If I cannot solve it after checking, I will connect you to customer support.",
                    "hn": "Pehle is account ko check karta hoon — payment, PDF, login, COSMO ID. Issue batao. Agar check ke baad solve na ho, tab customer support se connect karunga.",
                    "hi": "पहले इस खाते को चेक करता हूँ — पेमेंट, PDF, लॉगिन, COSMO ID। समस्या बताएं। हल न हो तो कस्टमर सपोर्ट से जोड़ूंगा।",
                },
                lang,
            ),
            "source": "help_first",
        }
    if _ESCALATE_RE.search(blob):
        return {
            "escalate": True,
            "reply": _pick(_WAIT, lang),
            "source": "escalate_rule",
        }
    if _STUCK_RE.search(blob) and prior:
        return {
            "escalate": True,
            "reply": _pick(_WAIT, lang),
            "source": "unsolved",
        }
    if _TX_ISSUE_RE.search(blob):
        reply, esc = _tx_account_reply(lang, account_card)
        return {"escalate": esc, "reply": reply, "source": "account"}
    if _COSMO_RE.search(blob):
        prior = _prior_user_texts(history)
        followup = bool(prior) or bool(
            _COSMO_FOLLOW_RE.search(blob) and re.search(r"\d", blob)
        )
        return {
            "escalate": False,
            "reply": _cosmo_reply(lang, cosmo_user_id, followup=followup),
            "source": "faq",
        }
    prior = _prior_user_texts(history)
    for pat, answers in _FAQ:
        if not pat.search(blob):
            continue
        if any(pat.search(t) for t in prior):
            return None
        return {"escalate": False, "reply": _pick(answers, lang), "source": "faq"}
    return None


def _agent_rules_excerpt() -> str:
    try:
        from support_agent.agent import load_rules

        return (load_rules() or "")[:1800]
    except Exception:
        return "Check this account first. Do not hand off to a human until Cosmic Help cannot solve it."


def _llm_answer(
    text: str,
    lang: str,
    history: list[dict[str, Any]],
    *,
    cosmo_user_id: str = "",
    account_card: str = "",
) -> dict[str, Any] | None:
    try:
        from openai_helper import _get_client
    except Exception:
        return None
    client = _get_client()
    if client is None:
        return None
    lang_name = {"en": "English", "hi": "Hindi (Devanagari)", "hn": "Hinglish"}[lang]
    hist_lines: list[str] = []
    for m in history[-6:]:
        if not isinstance(m, dict):
            continue
        who = str(m.get("sender") or "")
        if who not in ("user", "admin", "bot"):
            continue
        body = str(m.get("text") or "").strip()
        if body:
            hist_lines.append(f"{who}: {body[:300]}")
    prompt = (
        f"The user wrote in {lang_name}. Reply in that same language only "
        f"(Hinglish = Hindi in Roman letters, not Devanagari unless they used it).\n"
        "If the user wrote English, reply in English only — never Ji, never Hinglish.\n"
        "Return JSON only: {\"escalate\": true|false, \"reply\": \"...\"}\n"
        "Tone: always polite, warm, respectful — like a calm support agent. "
        "Never rude, never sarcastic, even if the user is angry.\n"
        "reply = 2 to 4 short sentences. No markdown.\n"
        "Answer how-to from KNOWLEDGE + THIS CUSTOMER ACCOUNT (their ID, plan, payments, Ask credits).\n"
        "Only tell this customer what they can see in the app. Never invent other accounts.\n"
        "FORBIDDEN in the reply: Telegram, admin, server, database, API keys, model names, "
        "file paths, prompts, internal IDs, other customers.\n"
        "escalate=true ONLY after checking THIS CUSTOMER ACCOUNT and still cannot solve, "
        "or for refund/double-charge, money cut with no order on Transactions, "
        "PDF missing after 24h, legal/abuse, or a screenshot. "
        "Do NOT escalate only because they asked to talk to support — help first; "
        "escalate on a later turn if still unsolved.\n"
        "If escalate=true, reply must tell them to wait here — customer support will join this chat.\n"
        "Talk to Founder is a More-menu link — do not escalate that.\n"
        "Do not do kundli readings — send those to the Ask tab.\n\n"
        f"KNOWLEDGE:\n{APP_KNOWLEDGE}\n\n"
        f"AGENT RULES:\n{_agent_rules_excerpt()}\n\n"
        f"THIS CUSTOMER ACCOUNT:\n{(account_card or '').strip() or '(unknown — do not invent)'}\n"
        f"THIS USER'S ID: {_normalize_cosmo(cosmo_user_id) or '(unknown — do not invent)'}\n"
        "If they mention a number like 109, that is the same as COSMO109. "
        "COSMO110 is only an example.\n\n"
        f"RECENT CHAT:\n" + ("\n".join(hist_lines) or "(none)") + "\n\n"
        f"USER: {text.strip()[:1200]}"
    )
    # Dedicated cheap model — do not inherit Ask's OPENAI_MODEL (gpt-4.1-mini).
    model = (os.environ.get("SUPPORT_AI_MODEL") or "gpt-4.1-nano").strip()
    timeout_s = float(os.environ.get("SUPPORT_AI_TIMEOUT") or "8")
    timeout_s = min(10.0, max(4.0, timeout_s))
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Cosmic Help for this one logged-in Cosmic Lens customer. "
                        "Use only their account facts plus app how-to. "
                        "Never leak internal/system data. Be brief and kind. No kundli readings."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=180,
            temperature=0.2,
            timeout=timeout_s,
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        log.warning("[support_ai] llm failed: %s", exc)
        return None
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    if not isinstance(data, dict):
        return None
    reply = str(data.get("reply") or "").strip()[:1200]
    if not reply:
        return None
    escalate = bool(data.get("escalate"))
    reply = scrub_customer_reply(reply, lang)
    if reply == wait_for_support_reply(lang) and _INTERNAL_LEAK_RE.search(
        str(data.get("reply") or "")
    ):
        escalate = True
    return {
        "escalate": escalate,
        "reply": reply,
        "source": "llm",
    }


def answer_support(
    text: str,
    *,
    lang: str | None = None,
    has_image: bool = False,
    history: list[dict[str, Any]] | None = None,
    cosmo_user_id: str = "",
    account_card: str = "",
    user: Any = None,
) -> dict[str, Any]:
    """Bounded Support Agent: scope → allowed knowledge/tools → guard → handoff."""
    from support_agent.agent import run

    out = run(
        text,
        lang=lang,
        has_image=has_image,
        history=history,
        user=user,
        account_card=account_card,
        cosmo_user_id=cosmo_user_id,
    )
    L = detect_reply_lang(text, lang)
    reply = scrub_customer_reply(str(out.get("reply") or ""), L)
    if not reply.strip():
        reply = wait_for_support_reply(L)
        return {"escalate": True, "reply": reply, "source": "empty"}
    return {
        "escalate": bool(out.get("escalate")),
        "reply": reply,
        "source": str(out.get("source") or ""),
        "intent": out.get("intent") or "",
    }


def maybe_auto_reply(
    rec: dict[str, Any],
    user_msg: dict[str, Any],
    *,
    lang: str | None = None,
    cosmo_user_id: str = "",
    account_card: str = "",
    min_think: float | None = None,
    user: Any = None,
) -> dict[str, Any]:
    """Check the account, wait while typing, then append a bot reply."""
    msgs = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    if any(isinstance(m, dict) and m.get("sender") == "admin" for m in msgs):
        return {"handled": False, "escalate": True, "source": "human_live"}

    import time

    try:
        from support_agent.agent import apply_check_delay
    except Exception:

        def apply_check_delay(*_a, **_k) -> None:
            return None

    from support_chat import append_message, mark_escalated

    started = time.monotonic()
    tid = str(rec.get("thread_id") or "")
    text = str(user_msg.get("text") or "")
    has_image = bool(user_msg.get("image_url"))
    history = rec.get("messages") if isinstance(rec.get("messages"), list) else []
    cid = (cosmo_user_id or str(rec.get("cosmo_user_id") or "")).strip()
    try:
        decision = answer_support(
            text,
            lang=lang,
            has_image=has_image,
            history=history,
            cosmo_user_id=cid,
            account_card=account_card,
            user=user,
        )
    except Exception:
        log.exception("[support_ai] answer_support failed")
        L = detect_reply_lang(text, lang)
        decision = {
            "escalate": False,
            "reply": wait_for_support_reply(L),
            "source": "error",
        }
    if not str(decision.get("reply") or "").strip():
        L = detect_reply_lang(text, lang)
        decision = {
            "escalate": False,
            "reply": wait_for_support_reply(L),
            "source": "empty",
        }
    apply_check_delay(started, min_think=min_think if min_think is not None else 0)
    bot = append_message(tid, sender="bot", text=decision["reply"])
    if not bot.get("ok"):
        return {"handled": False, "escalate": True, "source": "append_failed"}
    if decision.get("escalate"):
        mark_escalated(tid)
    return {
        "handled": True,
        "escalate": bool(decision.get("escalate")),
        "source": decision.get("source") or "",
        "reply": decision["reply"],
    }
