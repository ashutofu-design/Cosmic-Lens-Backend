"""
Sprint 47 — MODERN CONTEXT REFRAME ENGINE
Re-interprets every "classical bad" placement through TODAY'S environment
where remote work, internet, crypto, AI, freelancing, content creation,
psychology/healing professions, deep-research roles, OTT, gaming etc. exist.

Core philosophy (user-stated):
  "Old astrology gave correct results, but their environment was different.
   Same placement = problem in old days, SUPERPOWER today."

Engine outputs for each native:
  R1.  Planet-in-House modern reframe (chart-driven)
  R2.  Planet-in-Sign modern reframe (chart-driven)
  R3.  "Afflicted" planet → Modern superpower mapping
  R4.  Modern profession suggestions per placement
  R5.  Internet-age advantages from chart traits
  R6.  Old-fear vs New-reframe table (per planet)
  R7.  Top 3 hidden superpowers in this chart
"""
from __future__ import annotations
from typing import Any

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# ─── R1: Planet × House — modern reframe table (108 combos, focusing on
#       the placements that classical astrology labelled "bad") ─────────────
PLANET_HOUSE_REFRAME = {
    # ── MERCURY ──────────────────────────────────────────────────────────
    ("Mercury", 6):  ("Wins enemies through wit, debates, lawyering",
                       "Lawyer, debater, problem-solver, customer-service lead, fact-checker"),
    ("Mercury", 8):  ("Researcher of taboo/hidden topics, occultist, forensic mind",
                       "Forensic analyst, OSINT investigator, data-leak specialist, occult writer, reverse-engineer"),
    ("Mercury", 12): ("Deep silent thinker — perfect for research, foreign work, online writing",
                       "Online writer, research scientist, foreign-language translator, ghostwriter, AI-prompt engineer, freelance coder"),

    # ── MARS ─────────────────────────────────────────────────────────────
    ("Mars", 4):     ("Restless at home, but champion fighter for family/property",
                       "Real-estate flipper, security/defence consultant, home-renovation entrepreneur"),
    ("Mars", 6):     ("Born competitor, conquers enemies, athletic stamina",
                       "Athlete, MMA fighter, military, surgeon, debate champion, competitive gamer"),
    ("Mars", 7):     ("Argumentative partner BUT also fierce business partner",
                       "Co-founder of intense startup, sports partner, defence-contracts dealer"),
    ("Mars", 8):     ("Survivor of crises, hidden energy, loves extreme sports, longevity-research",
                       "Crisis manager, ER doctor, extreme-sport athlete, insurance investigator, occult researcher"),
    ("Mars", 12):    ("Stealth operator, hidden strategist, foreign-army mindset",
                       "Special-forces, intelligence agent, anonymous online activist, secret R&D, foreign-deployment engineer"),

    # ── JUPITER ──────────────────────────────────────────────────────────
    ("Jupiter", 6):  ("Heals enemies through wisdom — therapist for difficult people",
                       "Counselor, mediator, dispute resolver, immigration lawyer, pet-healer"),
    ("Jupiter", 8):  ("Researcher of hidden wealth, inheritance specialist, occult teacher",
                       "Estate planner, wealth-tax advisor, life-insurance consultant, tantra/yoga teacher"),
    ("Jupiter", 12): ("Spiritual sage, foreign-funded NGO, monastery, ashram, university researcher",
                       "Foreign-grant researcher, NGO founder, monk-teacher, online spiritual coach, philanthropy advisor"),

    # ── VENUS ────────────────────────────────────────────────────────────
    ("Venus", 6):    ("Beautiful work in service industries, creative under pressure",
                       "Spa/salon owner, hotel-service designer, cosmetic dermatologist, food-blogger"),
    ("Venus", 8):    ("Fascinated by deep love + occult beauty + tantric arts",
                       "Sex therapist, cosmetic surgeon, tantra teacher, jewellery dealer, true-crime romance writer"),
    ("Venus", 12):   ("Loves anonymous beauty, foreign luxury, secret romance",
                       "Foreign-luxury exporter, OnlyFans/influencer, perfume designer, cinematographer, hotel-bedroom designer"),

    # ── SATURN ───────────────────────────────────────────────────────────
    ("Saturn", 1):   ("Mature-faced from youth, taken seriously, long-haul builder",
                       "Long-term founder, marathon runner, anti-aging researcher, longevity coach, monk-CEO"),
    ("Saturn", 4):   ("Detached from family, but excellent at building structures/property over decades",
                       "Real-estate developer, infrastructure engineer, hostel/PG owner, home-care service founder"),
    ("Saturn", 5):   ("Late children, but excellent mentor of others' kids, disciplined creative",
                       "School founder, tutor, child-psychologist, structured creative (architect, novelist), discipline coach"),
    ("Saturn", 6):   ("Defeats enemies through patience and law, expert litigator",
                       "Litigation lawyer, compliance officer, auditor, debt collector, slow-but-sure executor"),
    ("Saturn", 7):   ("Late marriage but stable; serious business partnerships",
                       "Mature-age dating-app founder, B2B contracts specialist, government-tender expert"),
    ("Saturn", 8):   ("Long life, slow-burning research, transformation expert",
                       "Forensic accountant, longevity researcher, hospice worker, bankruptcy lawyer"),
    ("Saturn", 9):   ("Skeptic of religion → modern philosopher, reformer",
                       "Atheist philosopher, secular educator, ethics professor, foreign-policy analyst"),
    ("Saturn", 12):  ("Loves solitude, monk mindset, foreign retirement",
                       "Remote worker (Bali/digital-nomad), monk, dream-researcher, sleep-doctor, prison reformer"),

    # ── RAHU ─────────────────────────────────────────────────────────────
    ("Rahu", 1):     ("Unconventional appearance, foreign-style personality, viral charisma",
                       "Influencer, viral content creator, foreign-brand ambassador, model with unique look"),
    ("Rahu", 4):     ("Foreign property, unusual home, expat lifestyle",
                       "Real-estate-abroad investor, Airbnb host, home-decor influencer, expat-coach"),
    ("Rahu", 5):     ("Adopted children OR child via tech (IVF), unusual creativity",
                       "Game designer, IVF specialist, edutainment startup, viral kid-content"),
    ("Rahu", 6):     ("Crushes enemies through unconventional means — foreign jobs",
                       "Cybersecurity, ethical hacker, immigration-firm owner, gig-economy CEO"),
    ("Rahu", 7):     ("Foreign/inter-caste/online spouse, unconventional partnership",
                       "Online-dating founder, cross-border business, marriage-immigration lawyer"),
    ("Rahu", 8):     ("Sudden inheritance, hidden research, occult researcher",
                       "Crypto-trader, dark-web analyst, occult-content YouTuber, intelligence agent"),
    ("Rahu", 10):    ("Unconventional career — viral, foreign, non-traditional fame",
                       "Tech founder, content creator, foreign-CEO role, NRI businessperson"),
    ("Rahu", 11):    ("Massive gains through unusual networks — foreign collaborations",
                       "Crypto whale, NFT artist, multi-country networker, viral-affiliate marketer"),
    ("Rahu", 12):    ("Foreign settlement, online anonymity, dream-research",
                       "Digital nomad, dark-web researcher, foreign-currency trader, dream therapist"),

    # ── KETU ─────────────────────────────────────────────────────────────
    ("Ketu", 1):     ("Detached self-image, mysterious aura, monk-philosopher",
                       "Spiritual influencer, minimalist lifestyle coach, monk-content creator"),
    ("Ketu", 4):     ("Detached from home/mother — global wanderer mindset",
                       "Travel vlogger, retreat organizer, hospice volunteer, monk"),
    ("Ketu", 5):     ("Detached from kids/creativity in conventional way → spiritual mentoring",
                       "Spiritual teacher of children, meditation-app founder, Vedic-school founder"),
    ("Ketu", 7):     ("Detached partnerships, spiritual partner, late/unconventional marriage",
                       "Spiritual couples-coach, monk-therapist, ashram counselor"),
    ("Ketu", 8):     ("Past-life karma awareness, healer of trauma",
                       "Trauma therapist, past-life regressor, hypnotist, energy healer, crematorium reformer"),
    ("Ketu", 10):    ("Detached from worldly career — spiritual/healing profession",
                       "Healer, counselor, monk-CEO, NGO founder, alternative-medicine practitioner"),
    ("Ketu", 12):    ("Strong moksha placement — mystic/foreign spiritual path",
                       "Yoga-retreat owner, Vipassana teacher, foreign-monk, dream-interpreter"),

    # ── SUN ──────────────────────────────────────────────────────────────
    ("Sun", 6):      ("Wins legal/political battles, strong immunity, leadership in conflict",
                       "Politician, judge, doctor, military officer, sports captain"),
    ("Sun", 8):      ("Hidden authority, longevity researcher, transformation leader",
                       "Insurance-firm CEO, longevity scientist, occult researcher, crisis-leader"),
    ("Sun", 12):     ("Quiet leader, foreign-government role, behind-the-scenes power",
                       "Diplomat, foreign-embassy officer, ghost-CEO, monk-leader, anonymous philanthropist"),

    # ── MOON ─────────────────────────────────────────────────────────────
    ("Moon", 6):     ("Emotionally tough, healer of others' wounds",
                       "Nurse, therapist, social worker, food-relief NGO, animal rescuer"),
    ("Moon", 8):     ("Deep emotional intelligence, transformation through feeling",
                       "Trauma therapist, occult writer, hospice nurse, crisis counselor"),
    ("Moon", 12):    ("Sensitive to subconscious, dream-worker, foreign nurse",
                       "Dream therapist, foreign-nurse (NHS/Gulf), meditation-app founder, ASMR creator"),
}

# ─── R2: Planet × Sign — generic modern reframe (notable placements) ───────
PLANET_SIGN_REFRAME = {
    ("Mercury","Scorpio"):  ("Investigative mind — perfect for research & psychology",
                              "Detective, psychologist, true-crime writer, OSINT analyst"),
    ("Mercury","Pisces"):   ("Imaginative, intuitive — content/film-script genius",
                              "Screenwriter, lyricist, AI-art prompter, fiction novelist"),
    ("Mars","Cancer"):      ("Emotional warrior — protects family & vulnerable",
                              "Child-protection officer, paediatric surgeon, women-safety activist"),
    ("Saturn","Aries"):     ("Disciplined fighter, slow-but-relentless competitor",
                              "Marathon coach, long-form athlete, late-bloomer entrepreneur"),
    ("Jupiter","Capricorn"):("Practical wisdom — applies philosophy to business",
                              "Ethics consultant, business-school professor, ESG advisor"),
    ("Venus","Virgo"):      ("Perfectionist beauty — refined craft",
                              "Luxury craftsman, jewellery designer, Michelin chef, perfumer"),
    ("Sun","Libra"):        ("Diplomatic authority — leads through balance",
                              "UN diplomat, mediator, HR-head, ethics committee chair"),
    ("Moon","Scorpio"):     ("Intense emotional depth — magnetic, transformative",
                              "Hypnotherapist, occult counselor, intense-romance novelist"),
    ("Rahu","Sagittarius"): ("Unconventional teacher — viral wisdom content",
                              "Spiritual influencer, online-course creator, philosophy YouTuber"),
    ("Ketu","Gemini"):      ("Detached communicator — minimalist content",
                              "Silent-meditation teacher, monk-podcaster, koan writer"),
}

# ─── R3: Afflicted-planet → Modern superpower mapping ─────────────────────
AFFLICTED_TO_SUPERPOWER = {
    "Mercury": ("Overthinking, anxiety in old context",
                "DEEP RESEARCH, AI-prompting, coding, writing — perfect for knowledge economy"),
    "Mars":    ("Anger, accidents in old context",
                "EXTREME SPORTS, MMA, military gaming, surgical precision, crisis leadership"),
    "Saturn":  ("Delays, depression in old context",
                "LONG-HAUL building (10-yr startups), monk discipline, anti-aging, marathon"),
    "Sun":     ("Ego clash, father issues in old context",
                "INDEPENDENT brand-building, solo-founder, personal branding, leadership coaching"),
    "Moon":    ("Mood swings in old context",
                "EMPATH professions: therapy, ASMR, content-creation, music, hospitality"),
    "Venus":   ("Romance scandals in old context",
                "INFLUENCER economy, OnlyFans, beauty industry, luxury branding, content monetization"),
    "Jupiter": ("Religious extremism in old context",
                "ONLINE TEACHING, course creation, philosophy YouTuber, ethics consulting"),
    "Rahu":    ("Foreign confusion in old context",
                "VIRAL fame, crypto, NFT, international business, digital-nomad lifestyle"),
    "Ketu":    ("Spiritual escapism in old context",
                "HEALING professions, meditation-app, hospice work, minimalist lifestyle"),
}

# ─── R6: Old-fear vs New-reframe master table ─────────────────────────────
OLD_VS_NEW_TABLE = [
    ("Saturn in 1st",       "Old: looks weak/sad",
                            "Today: mature-faced founder, longevity-researcher, marathon runner"),
    ("Mercury in 12th",     "Old: depression, confusion",
                            "Today: deep-research scientist, online writer, AI-prompt engineer"),
    ("Rahu in 7th",         "Old: bad spouse, divorce",
                            "Today: foreign/online spouse, cross-border partnership business"),
    ("Mars in 8th",         "Old: accidents, surgery",
                            "Today: ER doctor, extreme-sport athlete, crisis manager"),
    ("Venus in 12th",       "Old: scandals, secret affairs",
                            "Today: cinematographer, perfume designer, OnlyFans creator, foreign-luxury exporter"),
    ("Saturn in 7th",       "Old: late/bad marriage",
                            "Today: mature-age dating success, B2B contracts king"),
    ("Ketu in 10th",        "Old: career failure",
                            "Today: healing/spiritual career, NGO founder, monk-CEO"),
    ("Mars in 4th",         "Old: home conflict, mother trouble",
                            "Today: real-estate flipper, security consultant, home-renovation entrepreneur"),
    ("Sun in 12th",         "Old: weak father, hidden enemies",
                            "Today: diplomat, foreign-embassy officer, anonymous philanthropist"),
    ("Moon in 8th",         "Old: emotional crisis, mother illness",
                            "Today: trauma therapist, hospice nurse, occult writer"),
    ("Jupiter in 6th",      "Old: weak teacher, debts",
                            "Today: counselor, immigration lawyer, mediator, dispute resolver"),
    ("Rahu in 12th",        "Old: foreign exile, isolation",
                            "Today: digital-nomad, dark-web researcher, foreign-currency trader"),
    ("6/8/12 stellium",     "Old: 'dushtana' triple curse",
                            "Today: research/healing/foreign-tech triple advantage"),
    ("Saturn-Moon conj",    "Old: chronic depression",
                            "Today: deep-emotional creator (musician, novelist), trauma-healer"),
    ("Mars-Rahu conj",      "Old: violence, accidents",
                            "Today: extreme-sports star, viral stunt creator, military-gaming pro"),
]


def run_modern_reframe(kundli: dict) -> dict[str, Any]:
    out: dict[str, Any] = {"available": True}
    planets = kundli.get("planets") or []
    lag = kundli.get("ascendant") or kundli.get("lagna") or "Aries"
    try: lagna_si = SIGN_NAMES.index(lag)
    except Exception: lagna_si = 0

    h_map: dict[int, list[str]] = {h: [] for h in range(1,13)}
    p_si: dict[str, int] = {}
    for p in planets:
        lon = p.get("longitude")
        if not isinstance(lon,(int,float)): continue
        si = int(lon // 30) % 12
        h = ((si - lagna_si) % 12) + 1
        h_map[h].append(p["name"])
        p_si[p["name"]] = si

    # R1 — Planet-in-house reframes for THIS chart
    r1 = []
    for h, plist in h_map.items():
        for p in plist:
            entry = PLANET_HOUSE_REFRAME.get((p, h))
            if entry:
                r1.append({"planet": p, "house": h,
                           "modern_meaning": entry[0],
                           "modern_professions": entry[1]})

    # R2 — Planet-in-sign reframes
    r2 = []
    for p, si in p_si.items():
        entry = PLANET_SIGN_REFRAME.get((p, SIGN_NAMES[si]))
        if entry:
            r2.append({"planet": p, "sign": SIGN_NAMES[si],
                       "modern_meaning": entry[0],
                       "modern_professions": entry[1]})

    # R3 — Afflicted planets → superpower
    afflicted = set(h_map.get(6,[]) + h_map.get(8,[]) + h_map.get(12,[]))
    r3 = []
    for p in afflicted:
        entry = AFFLICTED_TO_SUPERPOWER.get(p)
        if entry:
            r3.append({"planet": p, "old_label": entry[0],
                       "modern_superpower": entry[1]})

    # R4 — Aggregate top professions from r1+r2
    profs = []
    for x in r1+r2:
        for prof in x["modern_professions"].split(","):
            profs.append(prof.strip())
    # dedupe preserving order
    seen, profession_list = set(), []
    for p in profs:
        if p and p not in seen:
            seen.add(p); profession_list.append(p)

    # R5 — Internet-age advantages
    r5 = []
    if "Mercury" in afflicted:
        r5.append("Knowledge economy — online research, writing, AI prompting are now full careers")
    if "Saturn" in (h_map.get(1,[])+h_map.get(12,[])):
        r5.append("Remote-work era — Saturn's solitude becomes a digital-nomad superpower")
    if "Rahu" in p_si:
        r5.append("Internet virality — Rahu's foreign/unusual energy now monetizes via content")
    if "Venus" in afflicted:
        r5.append("Creator economy — beauty/luxury monetization via OnlyFans, Insta, brand deals")
    if "Mars" in afflicted:
        r5.append("Gaming/extreme-sport economy — Mars's aggression now becomes pro-eSports & MMA")
    if "Ketu" in (h_map.get(10,[])+h_map.get(12,[])):
        r5.append("Wellness economy — Ketu's spirituality is now a $4-trillion industry")
    if not r5:
        r5.append("Chart shows balanced placements — multiple modern career paths available")

    # R6 — Old vs new master table
    r6 = OLD_VS_NEW_TABLE

    # R7 — Top 3 hidden superpowers
    r7 = r3[:3] if r3 else [
        {"planet": "—", "old_label": "Balanced chart",
         "modern_superpower": "Multi-skill versatility — pick any modern field"}
    ]

    out.update({
        "r1_planet_house_reframes": r1,
        "r2_planet_sign_reframes": r2,
        "r3_afflicted_superpowers": r3,
        "r4_modern_professions": profession_list[:25],
        "r5_internet_age_advantages": r5,
        "r6_old_vs_new_table": r6,
        "r7_top_hidden_superpowers": r7,
        "philosophy": (
            "Old astrology gave correct results for THEIR environment. "
            "Today the same placements unlock superpowers because the world has changed. "
            "Same chart + new world = new opportunities."
        ),
    })
    return out


def format_modern_reframe(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ MODERN CONTEXT REFRAME ENGINE: ❌ unavailable"
    L = ["▸ MODERN CONTEXT REFRAME ENGINE — Old astrology in TODAY'S world (Sprint-47)",
         f"  ⚐ {r['philosophy']}",
         "  " + "═"*78]

    L.append("  R1 PLANET-IN-HOUSE — modern reframe for YOUR chart:")
    for x in r["r1_planet_house_reframes"]:
        L.append(f"      ▪ {x['planet']:<8} in H{x['house']:<2} → {x['modern_meaning']}")
        L.append(f"           ▶ Modern careers: {x['modern_professions']}")
    if not r["r1_planet_house_reframes"]:
        L.append("      ▪ (No specific reframes for current placements)")

    L.append("  R2 PLANET-IN-SIGN — modern reframe:")
    for x in r["r2_planet_sign_reframes"]:
        L.append(f"      ▪ {x['planet']:<8} in {x['sign']:<11} → {x['modern_meaning']}")
        L.append(f"           ▶ Modern careers: {x['modern_professions']}")
    if not r["r2_planet_sign_reframes"]:
        L.append("      ▪ (No notable sign reframes triggered)")

    L.append("  R3 'AFFLICTED' PLANETS → MODERN SUPERPOWERS:")
    for x in r["r3_afflicted_superpowers"]:
        L.append(f"      🔄 {x['planet']:<8} — OLD: {x['old_label']}")
        L.append(f"                    NEW: {x['modern_superpower']}")
    if not r["r3_afflicted_superpowers"]:
        L.append("      ▪ No 'afflicted' planets — chart already favorable in classical sense")

    L.append("  R4 TOP MODERN PROFESSION SUGGESTIONS (chart-derived):")
    for i, p in enumerate(r["r4_modern_professions"], 1):
        L.append(f"      {i:>2}. {p}")

    L.append("  R5 INTERNET-AGE ADVANTAGES from this chart:")
    for x in r["r5_internet_age_advantages"]:
        L.append(f"      ✚ {x}")

    L.append("  R6 OLD-FEAR vs NEW-REFRAME (master table — universal):")
    for placement, old, new in r["r6_old_vs_new_table"]:
        L.append(f"      ▪ {placement:<22} | {old:<32} | {new}")

    L.append("  R7 TOP HIDDEN SUPERPOWERS in this chart:")
    for i, x in enumerate(r["r7_top_hidden_superpowers"], 1):
        L.append(f"      ★ #{i} {x['planet']} — {x['modern_superpower']}")

    return "\n".join(L)
