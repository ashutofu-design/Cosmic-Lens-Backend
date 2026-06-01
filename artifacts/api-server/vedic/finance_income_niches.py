"""
Career income paths — 127 micro-niches scored from birth chart (D1).
Used by Career module (top 4 shown in UI).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

# label, primary planets, favorable houses, career-alignment bucket
_N = Tuple[str, Tuple[str, ...], Tuple[int, ...], str]

_RAW: List[_N] = [
    # ── Digital / creator / online ─────────────────────────────────────
    ("YouTuber / Video creator", ("Mercury", "Venus"), (3, 10, 11), "digital"),
    ("Vlogger / Short-form video", ("Mercury", "Venus", "Moon"), (3, 5, 11), "digital"),
    ("Instagram / Social influencer", ("Venus", "Mercury", "Moon"), (3, 7, 11), "digital"),
    ("TikTok / Reels creator", ("Mercury", "Venus", "Rahu"), (3, 5, 11), "digital"),
    ("Podcast host", ("Mercury", "Jupiter", "Moon"), (3, 9, 10), "digital"),
    ("Blogger / Content writer", ("Mercury", "Moon"), (3, 9, 10), "digital"),
    ("Newsletter / Substack writer", ("Mercury", "Jupiter"), (3, 9, 11), "digital"),
    ("Affiliate marketing", ("Mercury", "Rahu"), (3, 7, 11), "digital"),
    ("Social media manager", ("Mercury", "Venus"), (3, 6, 10), "digital"),
    ("SEO / Digital marketing", ("Mercury", "Rahu"), (3, 6, 10), "digital"),
    ("UGC creator", ("Venus", "Mercury", "Moon"), (3, 5, 11), "digital"),
    ("Live streamer / Gaming", ("Mars", "Mercury", "Rahu"), (3, 5, 11), "digital"),
    ("Esports / Game coaching", ("Mars", "Mercury"), (3, 5, 10), "digital"),
    ("Subscription / Creator platform", ("Venus", "Rahu", "Moon"), (5, 7, 11), "digital"),
    ("Online course creator", ("Jupiter", "Mercury"), (5, 9, 10), "digital"),
    ("EdTech / E-learning", ("Jupiter", "Mercury"), (5, 9, 10), "digital"),
    ("App developer", ("Mercury", "Mars"), (3, 10, 11), "digital"),
    ("SaaS / Tech startup", ("Mercury", "Rahu", "Saturn"), (10, 11, 12), "digital"),
    ("Freelance developer", ("Mercury", "Saturn"), (6, 10, 11), "digital"),
    ("UI/UX designer", ("Mercury", "Venus"), (3, 5, 10), "digital"),
    ("Graphic designer", ("Venus", "Mercury"), (3, 5, 10), "digital"),
    ("Video editor", ("Mercury", "Venus"), (3, 6, 10), "digital"),
    ("NFT / Digital art", ("Venus", "Rahu"), (5, 11, 12), "digital"),
    ("Crypto / Web3 trading", ("Rahu", "Mercury"), (2, 5, 11), "business"),
    ("Forex / Day trading", ("Mercury", "Rahu", "Mars"), (2, 5, 8), "business"),
    ("Dropshipping", ("Mercury", "Rahu"), (2, 7, 11), "business"),
    ("E-commerce store", ("Mercury", "Venus"), (2, 7, 11), "business"),
    ("Amazon / Marketplace seller", ("Mercury", "Saturn"), (2, 7, 11), "business"),
    ("Print on demand", ("Mercury", "Venus"), (2, 3, 11), "digital"),
    ("Stock photography / Assets", ("Venus", "Mercury"), (2, 5, 11), "digital"),
    # ── Employment / salary ────────────────────────────────────────────
    ("Government / Civil services", ("Sun", "Saturn"), (1, 10, 11), "employment"),
    ("PSU / Public sector job", ("Sun", "Saturn"), (10, 11, 6), "employment"),
    ("Banking officer", ("Jupiter", "Mercury", "Venus"), (2, 10, 11), "employment"),
    ("Railway / SSC type jobs", ("Saturn", "Sun"), (6, 10, 11), "employment"),
    ("School teacher", ("Jupiter", "Mercury"), (4, 5, 9), "employment"),
    ("College professor", ("Jupiter", "Mercury"), (9, 10, 5), "employment"),
    ("Doctor / Physician", ("Sun", "Mars", "Jupiter"), (6, 10, 8), "employment"),
    ("Nurse / Hospital staff", ("Moon", "Saturn"), (6, 12, 10), "employment"),
    ("Corporate engineer", ("Mars", "Mercury", "Saturn"), (10, 6, 11), "employment"),
    ("IT company job", ("Mercury", "Saturn"), (6, 10, 11), "employment"),
    ("Software engineer", ("Mercury", "Mars"), (3, 10, 11), "employment"),
    ("Data analyst", ("Mercury", "Saturn"), (5, 6, 11), "employment"),
    ("HR / Recruitment", ("Mercury", "Venus"), (6, 7, 11), "employment"),
    ("Sales executive", ("Mercury", "Venus", "Mars"), (3, 7, 11), "employment"),
    ("Marketing executive", ("Mercury", "Venus"), (3, 7, 10), "employment"),
    ("Chartered accountant", ("Mercury", "Saturn", "Jupiter"), (2, 6, 10), "employment"),
    ("Lawyer / Legal practice", ("Jupiter", "Mercury", "Sun"), (6, 9, 10), "employment"),
    ("Pilot / Aviation", ("Sun", "Mars", "Mercury"), (9, 10, 11), "employment"),
    ("Defense / Armed forces", ("Sun", "Mars", "Saturn"), (1, 6, 10), "employment"),
    ("Police / Law enforcement", ("Mars", "Saturn", "Sun"), (6, 10, 1), "employment"),
    ("Scientist / Research", ("Mercury", "Saturn", "Jupiter"), (5, 9, 12), "employment"),
    ("Pharma / Healthcare corp", ("Mercury", "Saturn", "Sun"), (6, 10, 11), "employment"),
    # ── Business / trading ─────────────────────────────────────────────
    ("Trading business", ("Mercury", "Mars"), (2, 7, 11), "business"),
    ("Import / Export", ("Mercury", "Rahu", "Jupiter"), (7, 9, 12), "business"),
    ("Wholesale distribution", ("Mercury", "Saturn"), (2, 7, 11), "business"),
    ("Retail shop", ("Mercury", "Venus"), (2, 7, 11), "business"),
    ("Restaurant / Cafe", ("Venus", "Moon", "Mercury"), (2, 7, 11), "business"),
    ("Cloud kitchen", ("Mars", "Mercury", "Venus"), (2, 6, 11), "business"),
    ("Food truck", ("Mars", "Mercury"), (2, 6, 11), "business"),
    ("Franchise business", ("Saturn", "Mercury", "Jupiter"), (7, 10, 11), "business"),
    ("Manufacturing unit", ("Mars", "Saturn"), (10, 11, 6), "business"),
    ("Textile / Garment business", ("Venus", "Mercury"), (2, 7, 11), "business"),
    ("Jewelry business", ("Venus", "Sun"), (2, 5, 11), "business"),
    ("Hotel / Hospitality", ("Venus", "Moon", "Jupiter"), (2, 7, 12), "business"),
    ("Travel agency", ("Jupiter", "Mercury", "Rahu"), (3, 9, 12), "business"),
    ("Event management", ("Venus", "Mercury", "Mars"), (5, 7, 11), "business"),
    ("Wedding planner", ("Venus", "Moon", "Mercury"), (7, 2, 11), "business"),
    ("Salon / Beauty parlour", ("Venus", "Mercury"), (2, 7, 11), "creative"),
    ("Gym / Fitness centre", ("Mars", "Sun"), (1, 6, 11), "business"),
    ("Coaching institute", ("Jupiter", "Mercury"), (5, 9, 10), "business"),
    ("Tuition / Home tutoring", ("Jupiter", "Mercury", "Moon"), (4, 5, 9), "business"),
    ("Car / Bike dealership", ("Mars", "Mercury", "Venus"), (4, 7, 11), "business"),
    ("Fuel pump / Petrol pump", ("Saturn", "Mars"), (2, 10, 11), "business"),
    ("Courier / Logistics", ("Saturn", "Mercury", "Mars"), (6, 10, 12), "business"),
    ("Insurance agency", ("Jupiter", "Mercury", "Venus"), (2, 7, 11), "business"),
    ("Financial advisory practice", ("Jupiter", "Mercury", "Venus"), (2, 9, 11), "professional"),
    # ── Real estate / property / enterprise ──────────────────────────────
    ("Real estate agent", ("Mars", "Mercury", "Venus"), (4, 7, 11), "enterprise"),
    ("Property developer", ("Mars", "Saturn", "Sun"), (4, 10, 11), "enterprise"),
    ("Construction contractor", ("Mars", "Saturn"), (4, 10, 11), "enterprise"),
    ("Civil engineer / Site", ("Mars", "Saturn", "Mercury"), (4, 10, 6), "enterprise"),
    ("Architecture practice", ("Mercury", "Venus", "Saturn"), (4, 10, 9), "enterprise"),
    ("Interior design business", ("Venus", "Mercury"), (4, 7, 10), "enterprise"),
    ("Rental / Airbnb income", ("Venus", "Saturn", "Moon"), (4, 2, 11), "enterprise"),
    ("Land / Plot dealing", ("Mars", "Saturn", "Jupiter"), (4, 2, 11), "enterprise"),
    # ── Creative / arts / media ──────────────────────────────────────────
    ("Actor / Film industry", ("Sun", "Venus", "Moon"), (5, 10, 12), "creative"),
    ("Model / Fashion", ("Venus", "Moon", "Sun"), (1, 5, 7), "creative"),
    ("Singer / Musician", ("Venus", "Moon", "Mercury"), (2, 5, 11), "creative"),
    ("DJ / Music production", ("Venus", "Rahu", "Mercury"), (5, 11, 3), "creative"),
    ("Dancer / Choreographer", ("Venus", "Mars", "Moon"), (3, 5, 7), "creative"),
    ("Makeup artist", ("Venus", "Moon"), (2, 7, 11), "creative"),
    ("Fashion designer", ("Venus", "Mercury"), (2, 5, 7), "creative"),
    ("Photographer", ("Venus", "Mercury", "Moon"), (3, 5, 11), "creative"),
    ("Videographer", ("Mercury", "Venus", "Mars"), (3, 10, 11), "creative"),
    ("Stand-up comedian", ("Mercury", "Moon", "Venus"), (3, 5, 11), "creative"),
    ("Author / Book writing", ("Mercury", "Jupiter", "Moon"), (3, 9, 5), "creative"),
    ("Voice artist / Dubbing", ("Mercury", "Venus", "Moon"), (3, 2, 10), "creative"),
    ("Arts / Gallery", ("Venus", "Moon"), (2, 5, 9), "creative"),
    # ── Professional / advisory ────────────────────────────────────────────
    ("Teaching / Advisory", ("Jupiter", "Mercury"), (2, 5, 9, 11), "professional"),
    ("Life coach / Motivation", ("Jupiter", "Sun", "Mercury"), (1, 9, 10), "professional"),
    ("Astrologer / Consultation", ("Jupiter", "Ketu", "Mercury"), (5, 8, 9), "professional"),
    ("Spiritual teacher", ("Jupiter", "Ketu", "Moon"), (9, 12, 5), "professional"),
    ("Yoga instructor", ("Jupiter", "Moon", "Sun"), (1, 5, 9), "professional"),
    ("Nutritionist / Wellness", ("Moon", "Mercury", "Jupiter"), (6, 2, 11), "professional"),
    ("Translator / Interpreter", ("Mercury", "Jupiter"), (3, 9, 7), "professional"),
    ("Tour guide", ("Jupiter", "Mercury", "Venus"), (3, 9, 12), "professional"),
    ("Inheritance / Family wealth", ("Jupiter", "Moon"), (2, 4, 9), "professional"),
    # ── Agriculture / traditional ─────────────────────────────────────────
    ("Farming / Agriculture", ("Moon", "Saturn", "Mars"), (4, 2, 11), "enterprise"),
    ("Dairy farm", ("Moon", "Venus"), (2, 4, 11), "enterprise"),
    ("Poultry farm", ("Mars", "Moon"), (6, 2, 11), "enterprise"),
    ("Organic / Ayurveda products", ("Moon", "Jupiter", "Mercury"), (2, 6, 11), "business"),
    # ── Gig / skilled services ─────────────────────────────────────────────
    ("Cab / Ride share driver", ("Mars", "Saturn", "Moon"), (4, 10, 12), "gig"),
    ("Delivery partner", ("Mars", "Mercury", "Moon"), (6, 3, 11), "gig"),
    ("Freelance consultant", ("Mercury", "Jupiter"), (6, 7, 10), "gig"),
    ("Electrician", ("Mars", "Saturn"), (6, 10, 4), "gig"),
    ("Plumber", ("Mars", "Saturn"), (6, 4, 11), "gig"),
    ("Carpenter / Furniture", ("Mars", "Venus"), (4, 2, 11), "gig"),
    ("Mechanic / Garage", ("Mars", "Saturn"), (6, 10, 11), "gig"),
    ("AC / Appliance repair", ("Mars", "Mercury"), (6, 10, 4), "gig"),
    ("Home cleaning services", ("Moon", "Saturn"), (6, 12, 2), "gig"),
    ("Security agency", ("Mars", "Saturn", "Sun"), (6, 10, 8), "gig"),
    ("Catering services", ("Moon", "Venus", "Mars"), (2, 6, 11), "gig"),
    ("Pest control", ("Mars", "Saturn"), (6, 8, 12), "gig"),
    ("Landscaping / Gardening", ("Venus", "Moon", "Saturn"), (4, 2, 12), "gig"),
    ("Childcare / Daycare", ("Moon", "Jupiter"), (4, 5, 2), "gig"),
    ("Pet care / Grooming", ("Moon", "Venus"), (6, 2, 11), "gig"),
    ("Foreign income / Overseas", ("Rahu", "Jupiter", "Mercury"), (7, 9, 12), "business"),
    ("Speculation / High-risk bets", ("Rahu", "Mars"), (5, 8, 11), "business"),
]

# Normalize houses tuples (Teaching had 5 houses in tuple - fix)
INCOME_NICHE_CATALOG: List[Dict[str, Any]] = []
for label, planets, houses, bucket in _RAW:
    INCOME_NICHE_CATALOG.append({
        "label": label,
        "planets": planets,
        "houses": tuple(int(h) for h in houses if 1 <= int(h) <= 12),
        "bucket": bucket,
    })


def niche_catalog_size() -> int:
    return len(INCOME_NICHE_CATALOG)


def score_income_niches_from_chart(
    planets: List[dict],
    asc_idx: int,
    *,
    lord_2: str = "",
    lord_11: str = "",
    exalt: Dict[str, str],
    debil: Dict[str, str],
    own: Dict[str, List[str]],
) -> List[Dict[str, Any]]:
    """Score all micro-niches; return sorted list (caller takes top 4–6)."""
    from vedic.career_inclination_engine import ensure_planet_houses

    normed = ensure_planet_houses(list(planets or []), asc_idx)
    by_name = {p.get("name"): p for p in normed if p.get("name")}

    scored: List[Dict[str, Any]] = []
    for niche in INCOME_NICHE_CATALOG:
        label = niche["label"]
        primary = niche["planets"]
        fav_houses = niche["houses"]
        bucket = niche["bucket"]

        score = 26
        matched: List[str] = []
        for pname in primary:
            p = by_name.get(pname)
            if not p:
                continue
            matched.append(pname)
            score += 7
            h = int(p.get("house") or 0)
            if h in fav_houses:
                score += 12
            if h in (2, 11):
                score += 4
            sg = str(p.get("sign") or "")
            if pname in exalt and sg == exalt[pname]:
                score += 8
            elif pname in own and sg in own.get(pname, []):
                score += 4
            elif pname in debil and sg == debil[pname]:
                score -= 6

        if lord_2 and lord_2 in primary and by_name.get(lord_2):
            score += 3
        if lord_11 and lord_11 in primary and by_name.get(lord_11):
            score += 3

        if not matched:
            continue

        scored.append({
            "source": label,
            "strength": max(18, min(95, score)),
            "bucket": bucket,
            "why": "",
        })

    scored.sort(key=lambda x: -int(x.get("strength") or 0))
    return scored
