"""
leak_channels_v1 — Personalized wealth leak channels (D1 + KP).

Up to 4 chart-specific alerts: where money may drain and one practical tip each.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORD = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
DEBIL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer", "Mercury": "Pisces",
    "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
}
_DUSTHANA = frozenset({6, 8, 12})
_MALEFICS = frozenset({"Mars", "Saturn", "Rahu", "Ketu", "Sun"})
_MAX_ALERTS = 4

# severity desc — higher shown first
_SEVERITY: Dict[str, int] = {
    "sudden_loss_tax": 90,
    "speculation_trading": 85,
    "kp_income_leak": 80,
    "emi_debt": 75,
    "family_shared_money": 70,
    "medical_hospital": 65,
    "property_legal": 60,
    "partnership_client_loss": 55,
    "savings_dont_stick": 50,
    "income_not_retained": 48,
    "kp_savings_leak": 45,
    "foreign_online_spend": 40,
    "impulsive_fines": 35,
    "subscriptions_small_spend": 30,
}

_TEMPLATES: Dict[str, Tuple[str, str, str]] = {
    "subscriptions_small_spend": (
        "Small recurring spends — track subscriptions and micro-payments monthly.",
        "Chhote repeat kharcha — subscriptions aur micro-payment monthly track karo.",
        "छोटे बार-बार खर्च — सब्सक्रिप्शन और छोटे भुगतान मासिक देखें।",
    ),
    "emi_debt": (
        "EMI / debt pressure — cap loans and service bills before new commitments.",
        "EMI / karz pressure — naye kharcha se pehle loan aur bills limit karo.",
        "ईएमआई / कर्ज दबाव — नई जिम्मेदारी से पहले ऋण और बिल सीमित करें।",
    ),
    "medical_hospital": (
        "Medical / hospital spend — keep a health buffer; don't skip insurance review.",
        "Medical / hospital kharcha — health buffer rakho; insurance review mat chhodo.",
        "चिकित्सा / अस्पताल खर्च — स्वास्थ्य फंड रखें; बीमा समीक्षा करें।",
    ),
    "property_legal": (
        "Property / legal / rent — double-check papers before big asset moves.",
        "Property / legal / rent — bade asset move se pehle papers dhyaan se dekho.",
        "संपत्ति / कानूनी / किराया — बड़े फैसले से पहले कागज़ जाँचें।",
    ),
    "sudden_loss_tax": (
        "Sudden loss / tax / inheritance — avoid rushed joint-money decisions.",
        "Achanak loss / tax / virasat — jaldi joint-money faisla mat lo.",
        "अचानक नुकसान / कर / विरासत — जल्दबाज़ी संयुक्त धन निर्णय न लें।",
    ),
    "speculation_trading": (
        "Speculation / trading / crypto — no impulsive bets; use a strict loss limit.",
        "Trading / crypto / satta — jaldi bet mat; strict loss limit rakho.",
        "सट्टा / ट्रेडिंग / क्रिप्टो — आवेग में दांव न लें; सीमा तय करें।",
    ),
    "partnership_client_loss": (
        "Partnership / client leakage — put client and partner payouts in writing.",
        "Partnership / client leak — partner aur client payment likhit rakho.",
        "साझेदारी / ग्राहक रिसाव — भुगतान लिखित करार में रखें।",
    ),
    "family_shared_money": (
        "Family / shared money — separate personal savings from family pool.",
        "Family / shared paisa — apni bachat family pool se alag rakho.",
        "परिवार / साझा धन — निजी बचत परिवार के पैसे से अलग रखें।",
    ),
    "foreign_online_spend": (
        "Foreign / online / hidden spend — watch cross-border and app-store charges.",
        "Foreign / online / chhupa kharcha — cross-border aur app charges dekho.",
        "विदेश / ऑनलाइन / छिपा खर्च — विदेशी और ऐप शुल्क पर नज़र रखें।",
    ),
    "impulsive_fines": (
        "Impulsive / fines / accidents — pause before big purchases; avoid rash driving.",
        "Impulsive / fine / accident — badi shopping se pehle ruko; rash driving avoid.",
        "आवेग / जुर्माना / दुर्घटना — बड़ी खरीद से पहले रुकें; लापरवाही न करें।",
    ),
    "savings_dont_stick": (
        "Savings don't stick — auto-transfer to a separate account on payday.",
        "Bachat tikti nahi — salary aate hi alag account me auto-transfer.",
        "बचत नहीं टिकती — वेतन आते ही अलग खाते में स्वतः स्थानांतरण करें।",
    ),
    "income_not_retained": (
        "Income comes but doesn't stay — track inflow vs outflow every month.",
        "Income aata hai, bachta nahi — har mahine inflow vs outflow track karo.",
        "आय आती है, टिकती नहीं — हर महीने आमदनी बनाम खर्च देखें।",
    ),
    "kp_savings_leak": (
        "Savings may drain — guard accumulated wealth and review recurring commitments.",
        "Bachat slip ho sakti hai — jama paisa bachao aur repeat commitments review karo.",
        "बचत रिस सकती है — संचित धन सुरक्षित रखें और बार-बार की प्रतिबद्धता देखें।",
    ),
    "kp_income_leak": (
        "Income may slip — tighten payouts and review where gains go each month.",
        "Kamai slip ho sakti hai — payouts tight karo aur har mahine dekho paisa kahan ja raha hai.",
        "आय फिसल सकती है — खर्च कम करें और हर महीने देखें लाभ कहाँ जा रहा है।",
    ),
}


def _find_p(planets: List[dict], name: str) -> Optional[dict]:
    return next((p for p in planets if p.get("name") == name), None)


def _house_lord(asc_idx: int, house: int) -> str:
    return SIGN_LORD[SIGNS[(asc_idx + house - 1) % 12]]


def _planet_house(planets: List[dict], name: str) -> Optional[int]:
    p = _find_p(planets, name)
    if not p:
        return None
    h = p.get("house")
    return int(h) if isinstance(h, int) else None


def _planet_sign(planets: List[dict], name: str) -> Optional[str]:
    p = _find_p(planets, name)
    if not p:
        return None
    s = p.get("sign")
    return str(s) if s else None


def _is_debilitated(planets: List[dict], name: str) -> bool:
    sign = _planet_sign(planets, name)
    return bool(sign and DEBIL.get(name) == sign)


def _is_combust(planets: List[dict], lord: str) -> bool:
    if lord == "Sun":
        return False
    p = _find_p(planets, lord)
    sun = _find_p(planets, "Sun")
    if not p or not sun:
        return False
    lon_p = p.get("longitude")
    lon_s = sun.get("longitude")
    if not isinstance(lon_p, (int, float)) or not isinstance(lon_s, (int, float)):
        return False
    diff = abs(float(lon_p) - float(lon_s))
    diff = min(diff, 360 - diff)
    return diff < 8.0


def _lord_placement_fact(lord: str, house: int) -> str:
    return f"{lord} in {house}th house"


def _fmt(channel: str, fact: str) -> Dict[str, str]:
    en, hn, hi = _TEMPLATES[channel]
    return {
        "channel": channel,
        "severity": _SEVERITY[channel],
        "message_en": en,
        "message_hn": hn,
        "message_hi": hi,
    }


def _scan_d1_channels(
    planets: List[dict],
    asc_idx: int,
    hits: Dict[str, str],
) -> None:
    lord_2 = _house_lord(asc_idx, 2)
    lord_4 = _house_lord(asc_idx, 4)
    lord_7 = _house_lord(asc_idx, 7)
    lord_8 = _house_lord(asc_idx, 8)
    lord_11 = _house_lord(asc_idx, 11)
    h2l = _planet_house(planets, lord_2)
    h4l = _planet_house(planets, lord_4)
    h7l = _planet_house(planets, lord_7)
    h8l = _planet_house(planets, lord_8)
    h11l = _planet_house(planets, lord_11)

    # 2 — EMI / debt
    if h2l == 6 or h11l == 6:
        lord = lord_2 if h2l == 6 else lord_11
        hits.setdefault("emi_debt", _lord_placement_fact(lord, 6))
    if _planet_house(planets, "Saturn") == 6:
        hits.setdefault("emi_debt", "Saturn in 6th house")

    # 3 — Medical
    moon_h = _planet_house(planets, "Moon")
    if moon_h in (6, 12) or _is_debilitated(planets, "Moon"):
        fact = f"Moon in {moon_h}th house" if moon_h else "Moon debilitated"
        if _is_debilitated(planets, "Moon") and moon_h:
            fact = f"Moon in {moon_h}th house (debilitated)"
        elif _is_debilitated(planets, "Moon"):
            fact = "Moon debilitated"
        hits.setdefault("medical_hospital", fact)

    # 4 — Property / legal
    if _planet_house(planets, "Saturn") == 12:
        hits.setdefault("property_legal", "Saturn in 12th house")
    elif _planet_house(planets, "Mars") == 12:
        hits.setdefault("property_legal", "Mars in 12th house")
    elif h4l == 8 or h8l == 4:
        lord = lord_4 if h4l == 8 else lord_8
        house = h4l if h4l == 8 else h8l
        if house:
            hits.setdefault("property_legal", _lord_placement_fact(lord, house))

    # 5 — Sudden loss / tax
    if _planet_house(planets, "Rahu") == 8:
        hits.setdefault("sudden_loss_tax", "Rahu in 8th house")
    elif h8l in _DUSTHANA and h8l:
        hits.setdefault("sudden_loss_tax", _lord_placement_fact(lord_8, h8l))

    # 7 — Partnership
    if h7l in _DUSTHANA and h7l:
        hits.setdefault("partnership_client_loss", _lord_placement_fact(lord_7, h7l))
    if h11l in _DUSTHANA and h11l:
        hits.setdefault("partnership_client_loss", _lord_placement_fact(lord_11, h11l))

    # 8 — Family / shared money
    if h2l == 8:
        hits.setdefault("family_shared_money", _lord_placement_fact(lord_2, 8))

    # 9 — Foreign / online
    if _planet_house(planets, "Rahu") == 12:
        hits.setdefault("foreign_online_spend", "Rahu in 12th house")

    # 10 — Impulsive / fines
    if _planet_house(planets, "Mars") == 12 and "property_legal" not in hits:
        hits.setdefault("impulsive_fines", "Mars in 12th house")

    # 11 — Savings don't stick
    if _planet_house(planets, "Ketu") == 2:
        hits.setdefault("savings_dont_stick", "Ketu in 2nd house")
    if _is_combust(planets, lord_2):
        hits.setdefault("savings_dont_stick", f"2nd lord {lord_2} combust")

    # 12 — Income not retained
    if h11l in _DUSTHANA and h11l:
        hits.setdefault("income_not_retained", _lord_placement_fact(lord_11, h11l))

    # 1 — Subscriptions (after weak-2H signals)
    weak_2h = (
        h2l in _DUSTHANA
        or _planet_house(planets, "Ketu") == 2
        or _is_combust(planets, lord_2)
    )
    if _planet_house(planets, "Mercury") == 12 or (weak_2h and _planet_house(planets, "Mercury") in (2, 12)):
        hits.setdefault("subscriptions_small_spend", "Mercury in 12th house" if _planet_house(planets, "Mercury") == 12 else f"Mercury with weak 2nd-house ({lord_2})")

    # 6 — Speculation (D1 leg): malefic in 5H
    for name in ("Rahu", "Mars", "Saturn"):
        if _planet_house(planets, name) == 5:
            hits.setdefault("speculation_trading", f"{name} in 5th house")
            break


def _scan_kp_channels(
    h2: Optional[Dict[str, Any]],
    h11: Optional[Dict[str, Any]],
    h12: Optional[Dict[str, Any]],
    hits: Dict[str, str],
) -> None:
    if h2 and (h2.get("loss_hits") or h2.get("verdict") == "RED"):
        csl = str(h2.get("csl_planet") or "planet")
        loss = h2.get("loss_hits") or []
        hits.setdefault("kp_savings_leak", f"2nd cusp CSL {csl} → loss houses {loss}")

    if h11 and (h11.get("loss_hits") or h11.get("verdict") == "RED"):
        csl = str(h11.get("csl_planet") or "planet")
        loss = h11.get("loss_hits") or []
        hits.setdefault("kp_income_leak", f"11th cusp CSL {csl} → loss houses {loss}")

    if not h12:
        return

    csl = str(h12.get("csl_planet") or "")
    sig = set((h12.get("chain") or {}).get("signified") or [])

    if csl == "Rahu" and (sig & {5, 8}):
        hits.setdefault("speculation_trading", f"12th cusp CSL Rahu signifies {sorted(sig & {5, 8})}")

    if csl == "Mercury" and (h12.get("verdict") == "RED" or h12.get("loss_hits")):
        hits.setdefault("subscriptions_small_spend", f"12th cusp CSL Mercury → expense drain")


def scan_wealth_leak_channels(
    planets: List[dict],
    asc_idx: int,
    h2: Optional[Dict[str, Any]] = None,
    h11: Optional[Dict[str, Any]] = None,
    h12: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return up to 4 personalized leak channel alerts, highest severity first."""
    hits: Dict[str, str] = {}
    _scan_d1_channels(planets, asc_idx, hits)
    _scan_kp_channels(h2, h11, h12, hits)

    ranked = sorted(
        hits.items(),
        key=lambda item: _SEVERITY.get(item[0], 0),
        reverse=True,
    )[:_MAX_ALERTS]

    return [_fmt(channel, fact) for channel, fact in ranked]
