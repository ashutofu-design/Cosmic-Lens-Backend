"""Locked warning templates for HEALTH engine (7 warnings).

These are LITERAL strings. LLM never sees them, never modifies them.
Returned verbatim when the question matches a warning trigger.

Tone discipline (per user directive):
  - SUPPORTIVE + CALM + NON-ALARMING (never blunt finance-tone)
  - Never "danger", "serious problem", "you have X disease"
  - Always end with doctor-consult line
  - Crisis template includes helpline (India: iCall 9152987821)

Doctor disclaimer is appended automatically by reply layer to ALL
non-warning replies via validator. Warnings include their own
context-specific closing line.
"""
from __future__ import annotations
from typing import Dict


_DOC = ("\n\nYeh astrological guidance hai — proper diagnosis aur "
        "treatment ke liye doctor consult zaroor karein.")


WARN_CRISIS_REDIRECT = (
    "Ruk jao — tum jo feel kar rahe ho woh bahut bhaari lag raha hoga, "
    "lekin tum akele nahi ho. Yeh moment guzar jayega, par abhi ek "
    "trained insaan se baat karna sabse zaroori kaam hai.\n\n"
    "🆘 India helpline (free, 24×7):\n"
    "  • iCall — 9152987821\n"
    "  • Vandrevala Foundation — 1860-2662-345\n"
    "  • Aasra — 022-2754-6669\n\n"
    "Kundli baad me dekhi ja sakti hai. Pehle ek call karo — kisi ko "
    "bata do jo sun sake (dost, family, ya helpline). Doctor / "
    "mental-health professional se bhi zaroor baat karein — yeh "
    "astrological guidance medical care ka substitute nahi hai."
    "\n\nFinal: Pehle baat karo, kundli baad me."
)

WARN_DEATH_PREDICTION_BLOCKED = (
    "Beta, koi bhi sachcha jyotish 'kab marunga' ya death-date predict "
    "nahi karta — yeh galat practice hai aur classical Vedic shastra "
    "(Parashara, Jaimini) bhi isko forbidden mante hain. Kundli sirf "
    "longevity ki TENDENCY (lambi/madhyam/short) ka indication de "
    "sakti hai, exact date nahi.\n\n"
    "Agar specific health worry hai to woh dimension-wise dekha ja "
    "sakta hai — vitality, recovery, chronic risk — par exact mrityu "
    "tarikh nahi."
    + _DOC +
    "\n\nFinal: Death-date kundli ka kaam nahi hai."
)

WARN_TIMING_HEALTH_DECLINE = (
    "Beta, 'kab beemar honga' / 'kis saal disease aayegi' yeh exact "
    "timing kundli se predict karna safe nahi hai — har bimari ke "
    "kayee karan hote hain (lifestyle, genetics, environment) jo "
    "chart se beyond hain. Aur exact bimari date batana matlab fear "
    "phailana, jo galat hai.\n\n"
    "Kundli se yeh bata sakte hain: vitality channel kaisa hai, "
    "recovery power kaisi hai, chronic risk zone elevated hai ya nahi. "
    "Iska use preventive care plan banane me karo, fear me nahi."
    + _DOC +
    "\n\nFinal: Risk zones dekho, exact dates nahi."
)

WARN_TIMING_RECOVERY = (
    "Recovery exact date kundli se predict karna possible nahi — har "
    "treatment ka response patient-to-patient alag hota hai. Kundli "
    "yeh dikha sakti hai ki recovery channel (Vipreet-Recovery yog, "
    "6th house support) strong hai ya weak — par exact 'kab thik "
    "honge' woh aapka doctor + body response milkar batayenge."
    + _DOC +
    "\n\nFinal: Recovery channel dekho, exact date nahi."
)

WARN_TIMING_SURGERY = (
    "Surgery muhurat ek serious matter hai — purely jyotish ke "
    "calculations pe medical procedure kab karwana yeh decide karna "
    "doctor ki advice ke against ja sakta hai. Treating doctor jo "
    "date suggest kare, woh pehli priority — kyunki body condition "
    "+ surgical readiness + team availability sab milkar safe-window "
    "decide karte hain.\n\n"
    "Agar phir bhi astrological angle dekhna ho to: ek experienced "
    "muhurat astrologer se in-person consult lo, generic AI tool se "
    "nahi."
    + _DOC +
    "\n\nFinal: Doctor ki date pehli priority hai."
)

WARN_DIAGNOSIS_DEMAND = (
    "Beta, 'mujhe kya bimari hai chart se bata do' — yeh kundli ka "
    "kaam nahi hai, balki doctor + medical tests ka kaam hai. Jyotish "
    "se sirf risk-zones ka idea milta hai (vitality kamzor hai, "
    "chronic risk elevated hai, mental peace stressed hai etc.) — "
    "exact disease-name diagnose karna jyotish ki capacity ke bahar "
    "hai. Jo bhi astrologer specific bimari name kar ke bataye, "
    "use trust mat karo.\n\n"
    "Aap kya kar sakte ho: regular health checkup, symptom-based "
    "doctor visit, aur kundli ke risk-zones ko preventive care me "
    "use karo."
    + _DOC +
    "\n\nFinal: Risk-zone yes, disease-name no."
)

WARN_CURE_GUARANTEE_BLOCKED = (
    "Koi sachcha jyotish 'guarantee thik ho jaoge' / '100% cure' "
    "promise nahi karta — health outcomes me treatment + body response "
    "+ lifestyle + time sab role play karte hain, sirf chart nahi. "
    "Jo astrologer cure-guarantee de raha ho, woh fake hai ya paisa "
    "lutne wala scheme.\n\n"
    "Kundli yeh dikha sakti hai: recovery channel strong hai ya weak, "
    "Vipreet-Recovery yog active hai ya nahi — yeh supportive "
    "indication hai, guarantee nahi."
    + _DOC +
    "\n\nFinal: Support yes, guarantee no."
)


WARNINGS: Dict[str, str] = {
    "CRISIS_REDIRECT":           WARN_CRISIS_REDIRECT,
    "DEATH_PREDICTION_BLOCKED":  WARN_DEATH_PREDICTION_BLOCKED,
    "TIMING_HEALTH_DECLINE":     WARN_TIMING_HEALTH_DECLINE,
    "TIMING_RECOVERY":           WARN_TIMING_RECOVERY,
    "TIMING_SURGERY":            WARN_TIMING_SURGERY,
    "DIAGNOSIS_DEMAND":          WARN_DIAGNOSIS_DEMAND,
    "CURE_GUARANTEE_BLOCKED":    WARN_CURE_GUARANTEE_BLOCKED,
}
