"""Customer-facing facts for the Support AI. No matching code — the model reads this."""

ALLOWED_KNOWLEDGE = """
Cosmic Lens — Help facts. Use only this. Do not invent prices. 2–4 short sentences.

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
- Lucky colour / number: Home → Risk Radar. Dark/light: sun/moon toggle on Home.

LIFE MAP
- Relationship, Career, Health, Finance + Explore (Numerology, AstroVastu, Face Reading).

LOVE REALITY (Life Map → Relationship → Love Reality)
- Needs your kundli + partner/family profile (Profile → edit).
- Basic (free, on-screen): Love Compatibility, Breakup Chances, Loyalty Check, Future Outcome.
- Pro PDF is written by our expert after pay — not an instant AI PDF. Offer ₹499 (was ₹999). Priority +₹300 (12h) = ₹799.
- Delivery: My Reports. Standard 24h, priority 12h. If 12h is missed, the ₹300 priority fee is refunded.

KUNDLI MILAN (Life Map → Relationship → Kundli Milan)
- Basic (free, on-screen): marriage structure /100 + Gun Milan /36.
- Pro PDF expert-written, not instant AI. Offer ₹699 (was ₹999). Priority +₹300 (12h) = ₹999.
- My Reports, 24h / 12h, same ₹300 priority-fee refund if 12h is missed.

CAREER / HEALTH / FINANCE
- Basic summaries free on-screen. Deeper detail: Pro plan ₹499/month via upgrade → Plans. Not expert PDFs.

NUMEROLOGY (Life Map → Explore → Numerology)
- Basic = free numbers on screen. Pro PDF expert-written after pay — not instant AI.
- Offer ₹299. Priority +₹100 (12h) = ₹399. My Reports, 24h / 12h.

ASTROVASTU
- Free compass on Vastu. Home: 1 room ₹199, 3-room ₹499, expert photo ₹199/room, floor-plan PDF ₹999, lifetime home ₹2999.
- Business: Shop ₹999 / Office ₹1499 / Factory ₹2999. Room photos ₹399 / ₹499 / ₹999. Full PDF ₹2999 / ₹6999 / ₹14999.
- PDFs in My Reports.

FACE READING — coming soon, not live.

ASK TAB
- V1: 3 free questions at signup. Packs ₹49 / ₹99 / ₹299 (Profile → Cosmic Packs).
- V3 Live (Ask tab, not this Help chat): 15 min ₹399, 30 ₹699, 45 ₹999, 60 ₹1299.
- Birth Time Rectification: Ask or Profile edit. Today ₹999 (was ₹2999).
- Chart / kundli readings belong on Ask, not this Help chat.

FUTURE TAB — free on-screen dasha timeline. Not a PDF.

MORE
- Talk to Founder (free): Instagram / YouTube / WhatsApp.
- Panchang, Planet Position (free), Gemstones (WhatsApp), My Reports, Profile.
- Website: https://cosmiclens.app
- Plans: Trial ₹1 / 7 days, Basic ₹199/month, Pro ₹499/month. Love Reality and Milan Basic stay free.
- Refer & Earn: Profile. Friend buys V1/V3 pack → 3 extra Ask questions.
- Delete account: Profile → About → type DELETE.
- Future Partner Portrait was removed — use Life Map → Relationship.

PAYMENTS
- Help → Transactions = paid orders. No wallet. If money left the bank but no order is listed, escalate to a team member.
- If the payment sheet closed, tap Pay again.
"""


def pick(answers: dict[str, str], lang: str) -> str:
    return answers.get(lang) or answers["hn"]
