"""kundli_full_context.py — Phase 7.7-pre

Build a single comprehensive Hinglish prompt block that hands the LLM
FULL access to a devotee's kundli + a universal topic-routing
cheat-sheet + structured-answer instructions.

Design intent (per project owner, 30 Apr 2026):
    • Skip the rule engine entirely for this path.
    • Read the question, identify the topic itself, look at whichever
      bhavas/grahas are relevant for that topic (health → 6H/8H/12H +
      Mars/Saturn/Mercury, career → 10H/Sun/Saturn etc.).
    • Anchor every claim in the chart facts dumped below — do not
      invent anything.

This module is an OPT-IN augmentation. It is wired into
`openai_helper._build_messages` behind the env flag
`LLM_FULL_CHART_MODE` (default OFF). When the flag is OFF the wire-site
no-ops and the existing prompt path is unchanged.

Pure stdlib. No engines/models.py/PKs touched. Read-only over the
inputs — never mutates `kundli` or `intel`.
"""

from __future__ import annotations

from typing import Any, Optional

# ────────────────────────────────────────────────────────────────────
# Constants — ASCII-only signs/lords so the dump renders well in the
# OpenAI prompt regardless of client encoding. We deliberately do not
# import from chart_intelligence.py to keep this module standalone
# (so a smoke test can run it without the heavier import chain).
# ────────────────────────────────────────────────────────────────────

_SIGNS = (
    "Mesh", "Vrish", "Mithun", "Karka", "Simh", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
)
_SIGN_LORDS = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)
_SIGN_ALIASES = {
    "mesh": 0, "mesha": 0, "aries": 0,
    "vrish": 1, "vrishabha": 1, "vrushabh": 1, "taurus": 1,
    "mithun": 2, "mithuna": 2, "gemini": 2,
    "kark": 3, "karka": 3, "cancer": 3,
    "simh": 4, "simha": 4, "leo": 4,
    "kanya": 5, "virgo": 5,
    "tula": 6, "libra": 6,
    "vrishchik": 7, "vrishchika": 7, "scorpio": 7,
    "dhanu": 8, "dhanus": 8, "sagittarius": 8,
    "makar": 9, "makara": 9, "capricorn": 9,
    "kumbh": 10, "kumbha": 10, "aquarius": 10,
    "meen": 11, "meena": 11, "pisces": 11,
}

_PLANET_ORDER = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _sign_idx(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, dict):
        value = value.get("sign") or value.get("name")
    if not isinstance(value, str):
        return None
    return _SIGN_ALIASES.get(value.strip().lower())


def _sign_name(value: Any) -> str:
    idx = _sign_idx(value)
    if idx is None:
        return str(value).strip() if isinstance(value, str) else "?"
    return _SIGNS[idx]


def _fmt_deg(deg: Any) -> str:
    if not isinstance(deg, (int, float)):
        return ""
    try:
        return f"{float(deg):.2f}"
    except Exception:
        return ""


def _suffix(n: int) -> str:
    if 11 <= n <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _planet_lookup(planets: Any) -> dict[str, dict]:
    """Build {name: planet_dict} for the standard 9 grahas."""
    out: dict[str, dict] = {}
    if not isinstance(planets, list):
        return out
    for p in planets:
        if not isinstance(p, dict):
            continue
        name = (p.get("name") or "").strip()
        if name in _PLANET_ORDER and name not in out:
            out[name] = p
    return out


def _dignity_lookup(intel: Any) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(intel, dict):
        return out
    for d in intel.get("dignities") or []:
        if not isinstance(d, dict):
            continue
        name = (d.get("planet") or "").strip()
        if name:
            out[name] = d
    return out


# ────────────────────────────────────────────────────────────────────
# Section builders
# ────────────────────────────────────────────────────────────────────

def _section_birth_lagna(
    kundli: dict,
    intel: dict | None,
    birth: dict | None,
    p_lookup: dict[str, dict],
) -> str:
    lines: list[str] = ["## 1. JANM & LAGNA"]

    if isinstance(birth, dict):
        bits: list[str] = []
        for label, key in (
            ("Naam", "name"), ("DOB", "dob"), ("Time", "time"),
            ("Sthaan", "place"), ("Gender", "gender"),
        ):
            val = birth.get(key)
            if not val and key == "place":
                val = birth.get("placeName") or birth.get("city")
            if not val and key == "dob":
                val = birth.get("date")
            if val:
                bits.append(f"{label}: {val}")
        if bits:
            lines.append("Janm: " + " | ".join(bits))

    asc = kundli.get("ascendant") or kundli.get("lagna")
    asc_idx = _sign_idx(asc)
    asc_deg = kundli.get("ascendantDeg") or kundli.get("ascendant_lon")
    if asc_idx is not None:
        deg_str = f" {_fmt_deg(asc_deg)}°" if isinstance(asc_deg, (int, float)) else ""
        lord = _SIGN_LORDS[asc_idx]
        lord_p = p_lookup.get(lord) or {}
        lord_house = lord_p.get("house")
        lord_sign = _sign_name(lord_p.get("sign") or lord_p.get("rashi"))
        lord_part = f"Lagnesh: {lord} in H{lord_house} ({lord_sign})" if lord_house else f"Lagnesh: {lord}"
        lines.append(f"Lagna: {_SIGNS[asc_idx]}{deg_str} | {lord_part}")

    moon = kundli.get("moonSign") or kundli.get("moon_sign")
    sun = kundli.get("sunSign") or kundli.get("sun_sign")
    rashi_bits = []
    if moon:
        rashi_bits.append(f"Chandra Rashi: {_sign_name(moon)}")
    if sun:
        rashi_bits.append(f"Surya Rashi: {_sign_name(sun)}")
    if rashi_bits:
        lines.append(" | ".join(rashi_bits))

    nak = kundli.get("nakshatra")
    if nak:
        nak_str = str(nak)
        pada = kundli.get("nakshatraPada") or kundli.get("nakshatra_pada")
        ruler = kundli.get("nakshatraRuler") or kundli.get("nakshatra_lord")
        if pada:
            nak_str += f" pada-{pada}"
        if ruler:
            nak_str += f" (Lord: {ruler})"
        lines.append(f"Janm-Nakshatra: {nak_str}")

    db = kundli.get("dashaBalance") or kundli.get("dasha_balance")
    if isinstance(db, (int, float)) and db > 0:
        lines.append(f"Dasha-balance at birth: {float(db):.2f} years")

    return "\n".join(lines)


def _section_grahas(
    kundli: dict,
    p_lookup: dict[str, dict],
    dig_lookup: dict[str, dict],
) -> str:
    """Render the 9-graha table."""
    lines = [
        "## 2. SAARE 9 GRAHAS (full detail)",
        "Graha   | House | Sign       | Deg    | Nakshatra-Pada       | Naks-Lord | Status",
        "--------|-------|------------|--------|----------------------|-----------|----------------------",
    ]
    any_row = False
    for name in _PLANET_ORDER:
        p = p_lookup.get(name)
        if not isinstance(p, dict):
            continue
        any_row = True
        sign = _sign_name(p.get("sign") or p.get("rashi"))
        house = p.get("house") or "?"
        # Degrees — accept multiple field names
        deg = p.get("degreeInSign") or p.get("deg_in_sign")
        if deg is None:
            lon = p.get("longitude")
            if isinstance(lon, (int, float)):
                deg = float(lon) % 30
        deg_str = _fmt_deg(deg) if deg is not None else ""

        nak = p.get("nakshatra") or ""
        pada = p.get("nakshatraPada") or p.get("pada") or ""
        nak_pada = f"{nak} / {pada}" if nak and pada else (nak or "")

        nak_lord = p.get("nakshatraRuler") or p.get("nakshatra_lord") or ""

        # Status from intel.dignities
        d = dig_lookup.get(name) or {}
        status_bits: list[str] = []
        dig = d.get("dignity")
        if dig:
            status_bits.append(str(dig))
        if d.get("combust"):
            status_bits.append("combust")
        if p.get("retrograde") and name not in {"Rahu", "Ketu"}:
            status_bits.append("retro")
        asp = d.get("aspects_houses") or []
        if asp:
            status_bits.append("asp H" + ",".join(str(a) for a in asp))
        status = ", ".join(status_bits) if status_bits else "-"

        lines.append(
            f"{name:<7s} | H{str(house):<4s}| {sign:<10s} | "
            f"{deg_str:<6s} | {nak_pada:<20s} | {nak_lord:<9s} | {status}"
        )
    return "\n".join(lines) if any_row else ""


def _section_bhavas(
    kundli: dict,
    intel: dict | None,
    p_lookup: dict[str, dict],
) -> str:
    """Render the 12-bhava table using intel.house_lords if present,
    else derive whole-sign from lagna."""
    lines = [
        "## 3. SAARE 12 BHAVAS (full detail)",
        "House | Sign       | Lord     | Lord placement     | Occupants",
        "------|------------|----------|--------------------|-----------------",
    ]

    rows: list[tuple[int, str, str, str]] = []  # (h, sign, lord, lord_placement)

    if isinstance(intel, dict) and intel.get("house_lords"):
        for hl in intel["house_lords"]:
            if not isinstance(hl, dict):
                continue
            h = hl.get("house")
            if not isinstance(h, int):
                continue
            sign = _sign_name(hl.get("sign"))
            lord = hl.get("lord") or ""
            lord_h = hl.get("lord_in_house")
            lord_s = hl.get("lord_in_sign") or ""
            placement = (
                f"H{lord_h} ({_sign_name(lord_s)})"
                if lord_h else f"({_sign_name(lord_s)})"
                if lord_s else "?"
            )
            rows.append((h, sign, lord, placement))
    else:
        asc_idx = _sign_idx(kundli.get("ascendant") or kundli.get("lagna"))
        if asc_idx is None:
            return ""
        for h in range(1, 13):
            s_idx = (asc_idx + h - 1) % 12
            lord = _SIGN_LORDS[s_idx]
            lord_p = p_lookup.get(lord) or {}
            lord_h = lord_p.get("house")
            lord_s = _sign_name(lord_p.get("sign") or lord_p.get("rashi"))
            placement = f"H{lord_h} ({lord_s})" if lord_h else (lord_s or "?")
            rows.append((h, _SIGNS[s_idx], lord, placement))

    # Occupants — derive from p_lookup
    occ_by_house: dict[int, list[str]] = {}
    for name, p in p_lookup.items():
        h = p.get("house")
        if isinstance(h, int):
            occ_by_house.setdefault(h, []).append(name)

    for h, sign, lord, placement in rows:
        occ = ", ".join(occ_by_house.get(h, [])) or "-"
        lines.append(
            f"H{h:<4d}| {sign:<10s} | {lord:<8s} | {placement:<18s} | {occ}"
        )
    return "\n".join(lines)


def _section_dasha(kundli: dict, p_lookup: dict[str, dict]) -> str:
    cd = kundli.get("currentDasha")
    if not isinstance(cd, dict):
        return ""
    lines = ["## 4. CURRENT DASHA TREE"]

    def _placement_for(lord: str | None) -> str:
        if not lord:
            return ""
        lp = p_lookup.get(lord) or {}
        h = lp.get("house")
        s = _sign_name(lp.get("sign") or lp.get("rashi"))
        if h:
            return f" → Lord: {lord} in H{h} ({s})"
        return f" → Lord: {lord}" if lord else ""

    maha = cd.get("maha")
    antar = cd.get("antar")
    pratyantar = cd.get("pratyantar") or cd.get("sookshma")
    starts = cd.get("startDate") or cd.get("start")
    ends = cd.get("endDate") or cd.get("end")

    if maha:
        line = f"Mahadasha:  {maha}"
        if starts and ends:
            line += f" ({starts} → {ends})"
        line += _placement_for(maha)
        lines.append(line)
    if antar:
        a_starts = cd.get("antarStart") or cd.get("antar_start")
        a_ends = cd.get("antarEnd") or cd.get("antar_end")
        line = f"Antardasha: {antar}"
        if a_starts and a_ends:
            line += f" ({a_starts} → {a_ends})"
        line += _placement_for(antar)
        lines.append(line)
    if pratyantar:
        lines.append(f"Pratyantar: {pratyantar}{_placement_for(pratyantar)}")

    # Optional: upcoming antars if kundli provides them
    upcoming = kundli.get("upcomingAntars") or kundli.get("upcoming_antars")
    if isinstance(upcoming, list) and upcoming:
        bits = []
        for u in upcoming[:3]:
            if isinstance(u, dict):
                lord = u.get("antar") or u.get("lord")
                start = u.get("startDate") or u.get("start") or ""
                end = u.get("endDate") or u.get("end") or ""
                if lord:
                    bits.append(f"{lord} ({start}→{end})".strip())
        if bits:
            lines.append("Upcoming antars: " + " ; ".join(bits))

    return "\n".join(lines) if len(lines) > 1 else ""


def _section_yogas_doshas(intel: dict | None, kundli: dict) -> str:
    if not isinstance(intel, dict) and not isinstance(kundli, dict):
        return ""
    lines = ["## 5. YOGAS / DOSHAS / SADE-SATI / GOCHAR"]
    any_row = False

    yogas = (intel or {}).get("yogas") or kundli.get("yogas") or []
    if isinstance(yogas, list) and yogas:
        any_row = True
        names = [str(y) for y in yogas if y]
        lines.append("Yogas detected: " + " | ".join(names))

    md = (intel or {}).get("mangal_dosh") or kundli.get("mangalDosh") or kundli.get("mangal_dosh")
    if md:
        any_row = True
        lines.append(f"Mangal Dosh: {md}")

    ss = (intel or {}).get("sade_sati") or kundli.get("sadeSati") or kundli.get("sade_sati")
    if ss:
        any_row = True
        if isinstance(ss, dict):
            phase = ss.get("phase") or ss.get("status") or ""
            active = ss.get("active")
            ss_str = f"phase={phase}" if phase else ""
            if active is not None:
                ss_str += (", " if ss_str else "") + f"active={bool(active)}"
            ss = ss_str or str(ss)
        lines.append(f"Sade-Sati: {ss}")

    transits = kundli.get("transits") or kundli.get("gochar")
    if isinstance(transits, dict) and transits:
        bits = []
        for k in ("Saturn", "Jupiter", "Rahu", "Ketu"):
            t = transits.get(k)
            if isinstance(t, dict):
                h = t.get("house")
                s = _sign_name(t.get("sign"))
                if h:
                    bits.append(f"{k}: H{h} ({s})")
            elif isinstance(t, str) and t:
                bits.append(f"{k}: {t}")
        if bits:
            any_row = True
            lines.append("Gochar (transits): " + " ; ".join(bits))

    return "\n".join(lines) if any_row else ""


# ────────────────────────────────────────────────────────────────────
# Static prompt blocks (cheat-sheet + answer instructions)
# ────────────────────────────────────────────────────────────────────

_CHEAT_SHEET = """## 6. KARAKA / HOUSE CHEAT-SHEET (topic match hone par PRIORITISE karo)

• Health (sehat / bimari / rog / pain / treatment) →
    1H+lord (vital strength), 6H+lord (rog/disease), 8H (chronic/surgery),
    12H (hospital/sleep/loss), Lagna afflictions, Mars (blood/inflammation),
    Saturn (chronic/joints/longevity), Mercury (nerves), Sun (heart/eyes),
    Moon (mental/fluid), Rahu (mystery/poison), Ketu (sudden/surgery),
    current dasha lord ki affliction, sade-sati phase.
    Sign-to-bodypart map: Mesh=head, Vrish=throat, Mithun=lungs/arms,
    Karka=chest, Simh=heart/spine, Kanya=intestine, Tula=kidney,
    Vrishchik=reproductive, Dhanu=hips/thighs, Makar=knees, Kumbh=calves,
    Meen=feet.

• Career (naukri / job / business / promotion) →
    10H+lord (karma-bhava), 6H (service/competition), 11H (gains/promotion),
    2H (income), Sun (authority), Saturn (discipline/karma), Mercury
    (commerce/communication), Mars (technical/competition/sports),
    Amatya-karaka (Jaimini), raja-yogas, parivartana, current dasha lord,
    Saturn gochar over 10H.

• Marriage (vivah / shaadi / partner) →
    7H+lord (kalatra), 5H (love/pre-marital), 8H (longevity of bond),
    2H (kutumb), Venus (men's wife-karaka), Jupiter (women's husband-karaka),
    Mangal-dosh, Upapada (UL = A12), current dasha lord vs 2/7/11
    significators, Jupiter gochar over natal 1/5/7.

• Wealth (dhana / paisa / business / income) →
    2H (sanchita-dhana), 11H (labha/gains), 5H (purva-punya wealth),
    9H (bhagya), Jupiter (dhana-karaka), Venus (bhog), Mercury (commerce),
    dhana-yogas (2L+11L conn, 5L+9L Lakshmi-yoga, parivartana between
    2/5/9/11 lords), daridra patterns (2L or 11L in 6/8/12).

• Children (santaan / bachhe / fertility) →
    5H+lord (putra-bhava), 9H (santati continuation), Jupiter (putra-karaka),
    Saptamsha (D-7), putra-dosh patterns (5L in 6/8/12, Rahu/Saturn in 5H,
    malefic aspect on 5L).

• Education / exam (vidya / padhai / competitive) →
    4H (basic schooling), 5H (intellect/buddhi/competitive), 9H (higher
    learning/dharma), 2H (memory/speech), Mercury (buddhi-karaka),
    Jupiter (vidya/wisdom), Sun (focus/willpower), Saraswati-yoga
    (Mer+Ven+Jup in kendra/trikona), Jupiter/Mercury transit over 5/9.

• Property / Vehicle (ghar / vahan / land) →
    4H+lord (sukh-sthan), Mars (real-estate karaka), Venus (vehicle/luxury),
    Mercury (paperwork/registration), Jupiter transit over 4H = buying
    window.

• Travel / Foreign (yatra / videsh / settlement) →
    3H (short journeys/courage), 9H (long/dharmic/foreign), 12H (videsh-vaas
    /settlement abroad), Rahu (foreign), Moon (movement), Mercury
    (commerce travel).

• Litigation (mukadama / case / court) →
    6H (vijay over enemy), 7H (opponent), 8H (sudden reversal/chronic),
    11H (gain from case), Mars (fight), Saturn (delay), Mercury (paperwork),
    Jupiter (judge/dharma).

• Mental / Emotional (mann / depression / anxiety / stress) →
    Moon (mind/emotion — sign + nakshatra + lord), Mercury (nerves/buddhi),
    4H (peace/home), 5H (joy), Saturn (depression/heaviness), Rahu
    (anxiety/confusion/addiction), papakartari Moon (Moon hemmed by
    malefics in 12th & 2nd from itself), sade-sati phase.

• Spiritual (moksha / dharma / sadhana) →
    9H (dharma), 12H (moksha-sthan), Jupiter (guru/wisdom), Ketu
    (renunciation/jnana), 4L+12L conn, Saturn in 12H with Jupiter aspect.

• Family (parivar / mata-pita / siblings) →
    4H (mata/home), 9H (pita), 3H (younger siblings/courage), 11H
    (elder sibling), 5H (children). Karakas: Moon (mother), Sun (father),
    Mars (siblings).
"""


_ANSWER_INSTRUCTIONS = """## 7. JAWAB KAISE DENA HAI

Tum ek anubhavi Vedic jyotishi ho. Upar di hui kundli pe POORA access hai.
Koi pre-defined rule engine nahi — tumhari shastriya samajh + upar di hui
ground-truth use karo.

STEP-BY-STEP:
  1. Question dhyaan se padho. Sub-questions list karo (1, 2, 3...).
  2. Topic identify karo. Cheat-sheet (Section 6) se decide karo konse
     ghar/grah dekhne hain. Multi-topic ho to sab cover karo.
  3. Saari relevant placements (graha + sign + house + dignity + aspect)
     Section 2 (Grahas) aur Section 3 (Bhavas) se nikalo.
  4. Section 4 (Dasha tree) se timing nikalo — current MD/AD lord ki
     placement aur condition relevant ghar/grah ko support karti hai
     ya block karti hai.
  5. Section 5 (Yogas/Doshas/Gochar) se context lo — kya koi
     yoga/dosha/sade-sati actively relevant hai.
  6. Hinglish mein structured jawab do.

STRUCTURE (har question ka):

**Verdict** — ek line: clear answer (haan / nahi / sambhavna + crux).

**Dekha kya** — 2-4 line: konse ghar/grah/dasha/yoga se yeh nikla.
   Specific cite karo (e.g. "Mars 6H mein, sign-mapping se yeh stomach ka
   ghar; saath Saturn ka aspect — chronic angle"). SIRF upar di hui
   kundli ke fields cite karo.

**Timing** — 1-2 line: kab tak / konsa dasha period / agla change-window.
   Section 4 ki dates use karo. "Kab" naa pucha ho to is block ko skip
   kar do.

**Upay** — 1-2 specific suggestions: mantra+count+day, ya daan+day,
   ya gemstone (gemstone sirf trial-period ke saath suggest karo —
   "neelam 5-7 ct, silver, 3 din trial"). Generic "puja karwao" NA bolo.

NIYAM:
• Sirf upar di hui kundli ke fields use karo. Naye planet placement, dasha,
  ya yoga IMAGINE NAHI karo. Missing data ho to honestly bolo "iska clear
  data abhi available nahi".
• Hinglish — Devanagari + English mix, simple bhasha. Sanskrit term ke
  saath English meaning ek baar ('Shukra (Venus)', 'Saade-Sati — Shani
  ka 7.5 saal ka phase').
• Emoji NAHI.
• Bullet/numbered lists chhote, max 3-4 items per block.
• Question multi-part ho to har part ko apna mini-block do.
• Tone: anubhavi jyotishi — confident par grounded. Guru-tone nahi.
• Length: 100-180 words total per single-topic question; multi-part
  question 200-280 words.
• Health questions mein: ek line "doctor se zaroor consult karein" likhna
  mandatory — yeh medical advice nahi, sirf jyotishiya disha hai.
"""


# ────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────

_HEADER = "═══════ POORI KUNDLI (FULL CHART ACCESS — Phase 7.7-pre) ═══════"
_FOOTER = "═══════════════════════════════════════════════════════════════"


def build_full_chart_context(
    kundli: Any,
    intel: Any = None,
    birth: Any = None,
    question: str = "",  # accepted for API stability; intentionally NOT echoed
) -> str:
    """Build the full-chart-access prompt block.

    Returns "" when kundli is missing/empty so the wire-site can no-op.
    Never raises — defensive on every field.

    Security note: ``question`` is accepted for backward-compatible callers
    but is intentionally NOT echoed inside this block. The block becomes a
    SYSTEM message; echoing user-controlled text into a system-priority
    context would elevate prompt-injection risk. The devotee's actual
    question is delivered to the model via the normal user-role message.
    """
    # Touch ``question`` so static analysers don't flag it; the value is
    # deliberately unused inside the system block (see security note).
    _ = question
    if not isinstance(kundli, dict) or not kundli:
        return ""

    intel_d = intel if isinstance(intel, dict) else None
    birth_d = birth if isinstance(birth, dict) else None

    p_lookup = _planet_lookup(kundli.get("planets"))
    if not p_lookup:
        # Without any planet data, the dump is useless.
        return ""

    dig_lookup = _dignity_lookup(intel_d)

    sections: list[str] = []

    try:
        sections.append(_section_birth_lagna(kundli, intel_d, birth_d, p_lookup))
    except Exception:
        pass
    try:
        s = _section_grahas(kundli, p_lookup, dig_lookup)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_bhavas(kundli, intel_d, p_lookup)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_dasha(kundli, p_lookup)
        if s:
            sections.append(s)
    except Exception:
        pass
    try:
        s = _section_yogas_doshas(intel_d, kundli)
        if s:
            sections.append(s)
    except Exception:
        pass

    sections.append(_CHEAT_SHEET.rstrip())
    sections.append(_ANSWER_INSTRUCTIONS.rstrip())

    body = "\n\n".join(s for s in sections if s)

    # Note: we DO NOT echo the devotee's question into this system block
    # (see security note in the docstring). The question reaches the model
    # via its normal user-role message; the cheat-sheet + answer template
    # alone provide the recency lock at the end of the system stack.
    parts = [_HEADER, "", body, "", _FOOTER]
    return "\n".join(parts)


__all__ = ["build_full_chart_context"]
