"""
health_rules.py — Phase 7.6
────────────────────────────
Deterministic Vedic-rule engine. Each rule is a pure function of the
chart data (`kundli` + `intel`) that returns a finding dict (or None
if the rule did not fire).

NO LLM, NO I/O. Engines (health_engine.py et al.) are NOT touched —
this module READS the chart data those engines also read, and produces
a parallel structured "phase76_findings" payload that the narrator
will fold into the prompt later.

Conventions
───────────
Every rule function signature:
    rule_<name>(chart) -> Optional[dict]

`chart` is a normalised dict (see `_normalise_chart`) with these keys:
    {
      "lagna_sign":   str | None,
      "lagna_lord":   str | None,
      "planets":      dict[planet_name, {sign, sign_idx, house, retro,
                                         combust, dignity, aspects_houses}],
      "house_lords":  list[{house, sign, lord, lord_in_house, lord_in_sign}],
      "yogas":        list[str],
      "mangal_dosh":  dict | None,
      "sade_sati":    dict | None,
      "current_dasha": dict | None,  # {maha, antar, pratyantar}
    }

Each finding looks like:
    {
      "rule_id":     "lagna_lord_in_dusthana",
      "fired":       True,
      "finding":     "Lagnesh Saturn 8H mein hai — vitality ki neenv ...",
      "evidence":    {"planet": "Saturn", "house": 8, ...},
      "confidence":  0.85,
      "severity":    "high" | "medium" | "low",
    }

`severity` is a hint for the narrator on how to weight the finding —
NOT a clinical claim.

Public API
──────────
    evaluate_rules(rule_ids: list[str], chart: dict) -> list[dict]
    normalise_chart(kundli: dict, intel: dict) -> dict
"""
from __future__ import annotations

from typing import Any, Callable, Optional


# ── Constants ────────────────────────────────────────────────────────────────

DUSTHANAS = (6, 8, 12)
NATURAL_MALEFICS = ("Saturn", "Mars", "Rahu", "Ketu", "Sun")
NATURAL_BENEFICS = ("Jupiter", "Venus", "Moon", "Mercury")


def _coerce_int(v: Any) -> Optional[int]:
    """Best-effort int coercion. Returns None for non-numeric / bool / None.

    Defensive against the schema variability noted in the architect review:
    upstream chart data sometimes ships `house` / `lord_in_house` /
    `aspects_houses` as numeric strings ("8") instead of ints. Without
    this coercion, key rule predicates would silently under-fire.
    """
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        try:
            iv = int(v)
            return iv if iv == v else None
        except Exception:
            return None
    if isinstance(v, str):
        s = v.strip()
        if s.lstrip("-").isdigit():
            try:
                return int(s)
            except Exception:
                return None
    return None


def _coerce_int_list(seq: Any) -> list[int]:
    if not isinstance(seq, list):
        return []
    out: list[int] = []
    for v in seq:
        iv = _coerce_int(v)
        if iv is not None:
            out.append(iv)
    return out

PLANET_HINDI = {
    "Sun":     "Surya",
    "Moon":    "Chandra",
    "Mars":    "Mangal",
    "Mercury": "Budh",
    "Jupiter": "Guru",
    "Venus":   "Shukra",
    "Saturn":  "Shani",
    "Rahu":    "Rahu",
    "Ketu":    "Ketu",
}


# ── Chart normalisation ──────────────────────────────────────────────────────

def normalise_chart(
    kundli: Optional[dict],
    intel: Optional[dict],
) -> dict:
    """Flatten raw kundli + intel into the shape every rule expects.

    Defensive: missing inputs return a minimal stub. Rules will not fire.
    """
    chart: dict = {
        "lagna_sign":    None,
        "lagna_lord":    None,
        "planets":       {},
        "house_lords":   [],
        "yogas":         [],
        "mangal_dosh":   None,
        "sade_sati":     None,
        "current_dasha": None,
    }

    intel = intel if isinstance(intel, dict) else {}
    kundli = kundli if isinstance(kundli, dict) else {}

    chart["lagna_sign"] = intel.get("lagna_sign") or kundli.get("ascendant")
    chart["yogas"]      = list(intel.get("yogas") or [])
    chart["mangal_dosh"] = intel.get("mangal_dosh")
    chart["sade_sati"]   = intel.get("sade_sati")
    chart["current_dasha"] = (kundli.get("currentDasha")
                              or kundli.get("current_dasha"))

    house_lords = intel.get("house_lords") or []
    if isinstance(house_lords, list):
        chart["house_lords"] = [hl for hl in house_lords if isinstance(hl, dict)]

    # Build a planet-keyed lookup. Prefer intel.dignities (richer) and
    # fall back to kundli.planets if needed.
    planets: dict[str, dict] = {}

    digs = intel.get("dignities") or []
    if isinstance(digs, list):
        for d in digs:
            if not isinstance(d, dict):
                continue
            name = d.get("planet")
            if not name:
                continue
            planets[name] = {
                "sign":    d.get("sign"),
                "house":   _coerce_int(d.get("house")),
                "retro":   bool(d.get("retro")),
                "combust": bool(d.get("combust")),
                "dignity": d.get("dignity") or "",
                "aspects_houses": _coerce_int_list(d.get("aspects_houses")),
            }

    # Backfill from kundli.planets (different schemas in the wild).
    raw_planets = kundli.get("planets")
    if isinstance(raw_planets, dict):
        for name, info in raw_planets.items():
            if not isinstance(info, dict):
                continue
            entry = planets.setdefault(name, {})
            entry.setdefault("sign", info.get("sign"))
            if entry.get("house") is None:
                entry["house"] = _coerce_int(info.get("house"))
            entry.setdefault("retro", bool(info.get("retrograde")))
            entry.setdefault("combust", bool(info.get("combust")))
    elif isinstance(raw_planets, list):
        for info in raw_planets:
            if not isinstance(info, dict):
                continue
            name = info.get("name") or info.get("planet")
            if not name:
                continue
            entry = planets.setdefault(name, {})
            entry.setdefault("sign", info.get("sign"))
            if entry.get("house") is None:
                entry["house"] = _coerce_int(info.get("house"))
            entry.setdefault("retro", bool(info.get("retrograde")))
            entry.setdefault("combust", bool(info.get("combust")))

    chart["planets"] = planets

    # Coerce house ints inside house_lords too (architect-flagged shape gap).
    coerced_hl: list[dict] = []
    for hl in chart["house_lords"]:
        coerced_hl.append({
            **hl,
            "house":         _coerce_int(hl.get("house")),
            "lord_in_house": _coerce_int(hl.get("lord_in_house")),
        })
    chart["house_lords"] = coerced_hl

    # Lagna lord = lord of house 1.
    for hl in chart["house_lords"]:
        if hl.get("house") == 1:
            chart["lagna_lord"] = hl.get("lord")
            break

    return chart


# ── Helpers ──────────────────────────────────────────────────────────────────

def _planet(chart: dict, name: str) -> Optional[dict]:
    p = (chart.get("planets") or {}).get(name)
    return p if isinstance(p, dict) else None


def _planet_house(chart: dict, name: str) -> Optional[int]:
    p = _planet(chart, name)
    if not p:
        return None
    h = p.get("house")
    return h if isinstance(h, int) else None


def _planets_in_house(chart: dict, house: int) -> list[str]:
    out: list[str] = []
    for name, info in (chart.get("planets") or {}).items():
        if isinstance(info, dict) and info.get("house") == house:
            out.append(name)
    return out


def _house_lord(chart: dict, house: int) -> Optional[dict]:
    for hl in (chart.get("house_lords") or []):
        if hl.get("house") == house:
            return hl
    return None


def _hindi(planet: str) -> str:
    return PLANET_HINDI.get(planet, planet)


# ── Rule definitions ─────────────────────────────────────────────────────────

def rule_lagna_lord_in_dusthana(chart: dict) -> Optional[dict]:
    lagnesh = chart.get("lagna_lord")
    if not lagnesh:
        return None
    h = _planet_house(chart, lagnesh)
    if h not in DUSTHANAS:
        return None
    return {
        "rule_id":   "lagna_lord_in_dusthana",
        "fired":     True,
        "finding":   (f"Lagnesh {_hindi(lagnesh)} {h}H mein baithe hain — "
                      f"sehat ki neenv pe chronic vulnerability hai, "
                      f"thakaan jaldi mehsoos hoti hai."),
        "evidence":  {"planet": lagnesh, "house": h},
        "confidence": 0.85,
        "severity":  "high",
    }


def rule_six_lord_in_dusthana(chart: dict) -> Optional[dict]:
    six = _house_lord(chart, 6)
    if not six:
        return None
    lord = six.get("lord")
    h = six.get("lord_in_house")
    if not (lord and isinstance(h, int) and h in (8, 12)):
        return None
    return {
        "rule_id":   "six_lord_in_dusthana",
        "fired":     True,
        "finding":   (f"Shashtesh {_hindi(lord)} {h}H mein hai — "
                      f"bimari deep root le sakti hai, recovery slow rehti hai."),
        "evidence":  {"lord": lord, "house": h},
        "confidence": 0.8,
        "severity":  "medium",
    }


def rule_eight_lord_in_lagna_or_six(chart: dict) -> Optional[dict]:
    eight = _house_lord(chart, 8)
    if not eight:
        return None
    lord = eight.get("lord")
    h = eight.get("lord_in_house")
    if not (lord and isinstance(h, int) and h in (1, 6)):
        return None
    return {
        "rule_id":   "eight_lord_in_lagna_or_six",
        "fired":     True,
        "finding":   (f"Ashtamesh {_hindi(lord)} {h}H mein hai — "
                      f"chronic ya hidden illness ka rasta khulta hai, "
                      f"diagnosis clear hone mein samay lag sakta hai."),
        "evidence":  {"lord": lord, "house": h},
        "confidence": 0.78,
        "severity":  "high",
    }


def rule_twelve_lord_active(chart: dict) -> Optional[dict]:
    twelve = _house_lord(chart, 12)
    if not twelve:
        return None
    lord = twelve.get("lord")
    h = twelve.get("lord_in_house")
    if not (lord and isinstance(h, int)):
        return None
    if h not in (1, 6, 8, 12):
        return None
    return {
        "rule_id":   "twelve_lord_active",
        "fired":     True,
        "finding":   (f"Vyayesh {_hindi(lord)} {h}H mein hai — "
                      f"hospitalization ya extended bed-rest ka mild risk, "
                      f"ek baar deep check-up advisable."),
        "evidence":  {"lord": lord, "house": h},
        "confidence": 0.65,
        "severity":  "medium",
    }


def rule_malefic_in_lagna(chart: dict) -> Optional[dict]:
    in_lagna = _planets_in_house(chart, 1)
    malefics_here = [p for p in in_lagna if p in NATURAL_MALEFICS]
    if not malefics_here:
        return None
    names = " + ".join(_hindi(p) for p in malefics_here)
    return {
        "rule_id":   "malefic_in_lagna",
        "fired":     True,
        "finding":   (f"Lagna mein {names} ki upasthiti — body / vitality "
                      f"par direct paap-prabhav, chot ya sudden discomfort "
                      f"jaldi ho sakti hai."),
        "evidence":  {"planets": malefics_here, "house": 1},
        "confidence": 0.75,
        "severity":  "medium",
    }


def rule_malefic_in_six(chart: dict) -> Optional[dict]:
    in_six = _planets_in_house(chart, 6)
    malefics_here = [p for p in in_six if p in NATURAL_MALEFICS]
    if not malefics_here:
        return None
    names = " + ".join(_hindi(p) for p in malefics_here)
    return {
        "rule_id":   "malefic_in_six",
        "fired":     True,
        "finding":   (f"6H (rog bhav) mein {names} — bimari se ladne ki "
                      f"shakti achchi hai par flare-ups bhi aate-jaate hain."),
        "evidence":  {"planets": malefics_here, "house": 6},
        "confidence": 0.7,
        "severity":  "low",
    }


def rule_moon_with_malefic(chart: dict) -> Optional[dict]:
    moon = _planet(chart, "Moon")
    if not moon:
        return None
    moon_h = moon.get("house")
    if not isinstance(moon_h, int):
        return None
    co_planets = [p for p in _planets_in_house(chart, moon_h)
                  if p != "Moon" and p in NATURAL_MALEFICS]
    if not co_planets:
        return None
    names = " + ".join(_hindi(p) for p in co_planets)
    return {
        "rule_id":   "moon_with_malefic",
        "fired":     True,
        "finding":   (f"Chandra {moon_h}H mein {names} ke saath baithe hain — "
                      f"mann anstable rehta hai, mood-swings, neend disturb."),
        "evidence":  {"moon_house": moon_h, "with": co_planets},
        "confidence": 0.78,
        "severity":  "medium",
    }


def rule_mercury_afflicted(chart: dict) -> Optional[dict]:
    mer = _planet(chart, "Mercury")
    if not mer:
        return None
    h = mer.get("house")
    flags = []
    if mer.get("combust"):
        flags.append("combust")
    if isinstance(h, int):
        co = [p for p in _planets_in_house(chart, h)
              if p != "Mercury" and p in NATURAL_MALEFICS]
        if co:
            flags.append("malefic conjunction (" + ", ".join(co) + ")")
    if not flags:
        return None
    return {
        "rule_id":   "mercury_afflicted",
        "fired":     True,
        "finding":   (f"Budh kamzor / pid-it ({', '.join(flags)}) — "
                      f"nervous system, skin, ya pachan tantra par dabaav."),
        "evidence":  {"flags": flags, "house": h},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_sun_in_six_or_eight(chart: dict) -> Optional[dict]:
    h = _planet_house(chart, "Sun")
    if h not in (6, 8):
        return None
    return {
        "rule_id":   "sun_in_six_or_eight",
        "fired":     True,
        "finding":   (f"Surya {h}H mein — heart, eyes, immunity ka core "
                      f"karaka kamzor placement mein, lifestyle care zaroori."),
        "evidence":  {"house": h},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_sun_afflicted(chart: dict) -> Optional[dict]:
    sun = _planet(chart, "Sun")
    if not sun:
        return None
    h = sun.get("house")
    flags = []
    dig = (sun.get("dignity") or "").lower()
    if dig in ("debilitated", "neech"):
        flags.append("debilitated")
    if isinstance(h, int):
        co = [p for p in _planets_in_house(chart, h)
              if p != "Sun" and p in ("Saturn", "Rahu", "Ketu")]
        if co:
            flags.append("affliction (" + ", ".join(co) + ")")
    if not flags:
        return None
    return {
        "rule_id":   "sun_afflicted",
        "fired":     True,
        "finding":   (f"Surya {', '.join(flags)} — heart, blood pressure, "
                      f"eyes, vitality ke karaka par dabaav, regular check-up rakhain."),
        "evidence":  {"flags": flags, "house": h},
        "confidence": 0.72,
        "severity":  "medium",
    }


def rule_mars_in_one_or_six(chart: dict) -> Optional[dict]:
    h = _planet_house(chart, "Mars")
    if h not in (1, 6):
        return None
    return {
        "rule_id":   "mars_in_one_or_six",
        "fired":     True,
        "finding":   (f"Mangal {h}H mein — blood-related issues, bukhar, "
                      f"chot ya inflammation jaldi flare ho sakte hain."),
        "evidence":  {"house": h},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_mars_afflicted(chart: dict) -> Optional[dict]:
    mars = _planet(chart, "Mars")
    if not mars:
        return None
    h = mars.get("house")
    dig = (mars.get("dignity") or "").lower()
    flags = []
    if dig in ("debilitated", "neech"):
        flags.append("debilitated")
    if isinstance(h, int) and h in DUSTHANAS:
        flags.append(f"in dusthana H{h}")
    if not flags:
        return None
    return {
        "rule_id":   "mars_afflicted",
        "fired":     True,
        "finding":   (f"Mangal {', '.join(flags)} — energy aur blood "
                      f"karaka kamzor, accident-risk window mein extra savdhani."),
        "evidence":  {"flags": flags, "house": h},
        "confidence": 0.68,
        "severity":  "medium",
    }


def rule_saturn_aspect_lagna(chart: dict) -> Optional[dict]:
    sat = _planet(chart, "Saturn")
    if not sat:
        return None
    aspects = sat.get("aspects_houses") or []
    if 1 not in aspects:
        return None
    return {
        "rule_id":   "saturn_aspect_lagna",
        "fired":     True,
        "finding":   ("Shani ki drishti Lagna par — dheere-dheere joints, "
                      "bones, stamina mein delay aur stiffness aati hai. "
                      "Discipline aur posture-care must."),
        "evidence":  {"saturn_house": sat.get("house"), "aspects_lagna": True},
        "confidence": 0.72,
        "severity":  "medium",
    }


def rule_saturn_in_lagna_or_six(chart: dict) -> Optional[dict]:
    h = _planet_house(chart, "Saturn")
    if h not in (1, 6):
        return None
    return {
        "rule_id":   "saturn_in_lagna_or_six",
        "fired":     True,
        "finding":   (f"Shani {h}H mein — chronic, slow-burn type tendency, "
                      f"bones, joints, vaat dosh ka dabaav. Long-term "
                      f"routine se hi balance milega."),
        "evidence":  {"house": h},
        "confidence": 0.78,
        "severity":  "high" if h == 1 else "medium",
    }


def rule_rahu_in_lagna(chart: dict) -> Optional[dict]:
    h = _planet_house(chart, "Rahu")
    if h != 1:
        return None
    return {
        "rule_id":   "rahu_in_lagna",
        "fired":     True,
        "finding":   ("Rahu Lagna mein — anxiety, mysterious / hard-to-"
                      "diagnose ailments, allergies, sleep disturbance. "
                      "Mind-body grounding routine zaroori."),
        "evidence":  {"house": 1},
        "confidence": 0.75,
        "severity":  "medium",
    }


def rule_ketu_in_lagna_or_six(chart: dict) -> Optional[dict]:
    h = _planet_house(chart, "Ketu")
    if h not in (1, 6):
        return None
    return {
        "rule_id":   "ketu_in_lagna_or_six",
        "fired":     True,
        "finding":   (f"Ketu {h}H mein — sudden, sharp ya mysterious "
                      f"affliction ki tendency, surgery-prone window mein "
                      f"sahi specialist consult."),
        "evidence":  {"house": h},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_sade_sati_active(chart: dict) -> Optional[dict]:
    """Fires for the canonical chart_intelligence string output (e.g.
    "Sade-sati ACTIVE — peak phase ...") AND legacy dict form. Empty
    string / None → not active.
    """
    ss = chart.get("sade_sati")
    finding_template = (
        "Sade-Sati ({phase}) chal rahi hai — Shani ki "
        "transit pressure mann pe + body pe, chronic "
        "low-energy phase, routine + meditation zaroori."
    )
    if isinstance(ss, str):
        s = ss.strip()
        if not s:
            return None
        s_low = s.lower()
        if "active" not in s_low and "dhaiya" not in s_low:
            return None
        if "first phase" in s_low:
            phase = "first phase"
        elif "peak phase" in s_low or "peak" in s_low:
            phase = "peak"
        elif "final phase" in s_low:
            phase = "final"
        elif "ashtama" in s_low and "ardha" not in s_low:
            phase = "ashtama (8th from Moon)"
        elif "ardhashtama" in s_low:
            phase = "ardhashtama (4th from Moon)"
        else:
            phase = "active"
        return {
            "rule_id":   "sade_sati_active",
            "fired":     True,
            "finding":   finding_template.format(phase=phase),
            "evidence":  {"raw": s, "phase": phase},
            "confidence": 0.8,
            "severity":  "high",
        }
    if isinstance(ss, dict):
        active = ss.get("active") or ss.get("phase") or ss.get("running")
        if not active:
            return None
        phase = ss.get("phase") or "active"
        return {
            "rule_id":   "sade_sati_active",
            "fired":     True,
            "finding":   finding_template.format(phase=phase),
            "evidence":  ss,
            "confidence": 0.8,
            "severity":  "high",
        }
    return None


def rule_mangal_dosh_active(chart: dict) -> Optional[dict]:
    """Fires for the canonical chart_intelligence string output (e.g.
    "Mangal-dosh present (from Lagna)") AND legacy dict form. The
    "no Mangal-dosh" string never fires.
    """
    md = chart.get("mangal_dosh")
    finding = (
        "Mangal Dosh active — blood, garmi (heat-related), "
        "BP, ya energy imbalance ki tendency. Mars-friendly "
        "remedies + cooling diet helpful."
    )
    if isinstance(md, str):
        s = md.strip()
        if not s:
            return None
        s_low = s.lower()
        if "no mangal" in s_low:
            return None
        if "present" not in s_low and "dosh" not in s_low:
            return None
        return {
            "rule_id":   "mangal_dosh_active",
            "fired":     True,
            "finding":   finding,
            "evidence":  {"raw": s},
            "confidence": 0.7,
            "severity":  "medium",
        }
    if isinstance(md, dict):
        if not (md.get("present") or md.get("active") or md.get("dosh")):
            return None
        return {
            "rule_id":   "mangal_dosh_active",
            "fired":     True,
            "finding":   finding,
            "evidence":  md,
            "confidence": 0.7,
            "severity":  "medium",
        }
    return None


def rule_current_dasha_dusthana_lord(chart: dict) -> Optional[dict]:
    cd = chart.get("current_dasha") or {}
    if not isinstance(cd, dict):
        return None
    maha = cd.get("maha") or cd.get("mahaDasha") or cd.get("md")
    antar = cd.get("antar") or cd.get("antarDasha") or cd.get("ad")
    if not maha:
        return None
    # Find which house this dasha lord rules.
    flagged = []
    for label, planet in (("Mahadasha", maha), ("Antardasha", antar)):
        if not planet:
            continue
        for hl in (chart.get("house_lords") or []):
            if hl.get("lord") == planet and hl.get("house") in DUSTHANAS:
                flagged.append((label, planet, hl.get("house")))
                break
    if not flagged:
        return None
    bits = ", ".join(
        f"{lbl} {_hindi(p)} ({h}H ka swami)" for lbl, p, h in flagged
    )
    return {
        "rule_id":   "current_dasha_dusthana_lord",
        "fired":     True,
        "finding":   (f"Abhi chal raha hai: {bits} — yeh dasha health pe "
                      f"sensitive window banati hai, abhi self-care zyaada."),
        "evidence":  {"flagged": [{"label": l, "planet": p, "house": h}
                                  for l, p, h in flagged]},
        "confidence": 0.78,
        "severity":  "high",
    }


def rule_jupiter_aspect_lagna(chart: dict) -> Optional[dict]:
    jup = _planet(chart, "Jupiter")
    if not jup:
        return None
    aspects = jup.get("aspects_houses") or []
    if 1 not in aspects:
        return None
    return {
        "rule_id":   "jupiter_aspect_lagna",
        "fired":     True,
        "finding":   ("Guru ki drishti Lagna par — recovery support strong, "
                      "bimari se ladne ki shakti achi, divine protection."),
        "evidence":  {"jupiter_house": jup.get("house"), "aspects_lagna": True},
        "confidence": 0.75,
        "severity":  "low",
    }


def rule_venus_in_six_or_eight(chart: dict) -> Optional[dict]:
    h = _planet_house(chart, "Venus")
    if h not in (6, 8):
        return None
    return {
        "rule_id":   "venus_in_six_or_eight",
        "fired":     True,
        "finding":   (f"Shukra {h}H mein — kidneys, reproductive, urinary, "
                      f"ya hormonal balance par hawa hai, sweet/sugar care."),
        "evidence":  {"house": h},
        "confidence": 0.65,
        "severity":  "medium",
    }


def rule_house_lord_placement_summary(chart: dict) -> Optional[dict]:
    """Always-fires informational rule for house_lord_placement_query topic.

    Returns a compact summary of where each key health-related house lord
    sits. Severity = "low" because it's descriptive, not diagnostic.
    """
    targets = (1, 5, 6, 8, 10, 12)
    bits: list[str] = []
    for h in targets:
        hl = _house_lord(chart, h)
        if not hl:
            continue
        lord = hl.get("lord")
        sits_in = hl.get("lord_in_house")
        if not lord:
            continue
        if isinstance(sits_in, int):
            bits.append(f"H{h} swami {_hindi(lord)} → H{sits_in} mein")
        else:
            bits.append(f"H{h} swami {_hindi(lord)}")
    if not bits:
        return None
    return {
        "rule_id":   "house_lord_placement_summary",
        "fired":     True,
        "finding":   "Aapke kundli mein house lords: " + "; ".join(bits) + ".",
        "evidence":  {"summary": bits},
        "confidence": 0.95,
        "severity":  "low",
    }


# ── Phase 7.6.1 — additional topic-specific rules ────────────────────────────

def _h_offset(base: int, offset: int) -> int:
    """Return the house at `offset` positions from `base` (1-indexed, mod 12).

    Example: 2nd from H1 = H2, 12th from H1 = H12, 2nd from H12 = H1.
    """
    return ((base - 1 + offset) % 12) + 1


def rule_venus_afflicted(chart: dict) -> Optional[dict]:
    """Venus combust, in dusthana, debilitated, or with malefic
    → skin / beauty / female reproductive vulnerability.
    """
    v = _planet(chart, "Venus")
    if not v:
        return None
    h = _coerce_int(v.get("house"))
    afflictions: list[str] = []
    if v.get("combust"):
        afflictions.append("combust")
    if h in DUSTHANAS:
        afflictions.append(f"{h}H mein")
    dignity = (v.get("dignity") or "").lower()
    if "debilitat" in dignity or "neech" in dignity:
        afflictions.append("neech")
    if isinstance(h, int):
        co_planets = [p for p in _planets_in_house(chart, h) if p != "Venus"]
        if any(p in NATURAL_MALEFICS for p in co_planets):
            afflictions.append("malefic ke saath")
    if not afflictions:
        return None
    return {
        "rule_id":   "venus_afflicted",
        "fired":     True,
        "finding":   (f"Shukra afflicted ({', '.join(afflictions)}) — "
                      f"twacha, baal, soundarya, ya stree-vishay area mein "
                      f"vulnerability rehti hai."),
        "evidence":  {"house": h, "afflictions": afflictions},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_jupiter_afflicted(chart: dict) -> Optional[dict]:
    """Jupiter combust, in dusthana, debilitated, or with malefic
    → liver / fat metabolism / growth / immunity protection compromised.
    """
    j = _planet(chart, "Jupiter")
    if not j:
        return None
    h = _coerce_int(j.get("house"))
    afflictions: list[str] = []
    if j.get("combust"):
        afflictions.append("combust")
    if h in DUSTHANAS:
        afflictions.append(f"{h}H mein")
    dignity = (j.get("dignity") or "").lower()
    if "debilitat" in dignity or "neech" in dignity:
        afflictions.append("neech")
    if isinstance(h, int):
        co_planets = [p for p in _planets_in_house(chart, h) if p != "Jupiter"]
        if any(p in NATURAL_MALEFICS for p in co_planets):
            afflictions.append("malefic ke saath")
    if not afflictions:
        return None
    return {
        "rule_id":   "jupiter_afflicted",
        "fired":     True,
        "finding":   (f"Guru afflicted ({', '.join(afflictions)}) — "
                      f"liver, fat metabolism, vridhi, aur sehat ki suraksha "
                      f"par chot lag sakti hai."),
        "evidence":  {"house": h, "afflictions": afflictions},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_papakartari_lagna(chart: dict) -> Optional[dict]:
    """Malefics in BOTH 2nd house and 12th house (squeezing the lagna)
    → vitality squeezed from both sides.
    """
    p2 = [p for p in _planets_in_house(chart, 2) if p in NATURAL_MALEFICS]
    p12 = [p for p in _planets_in_house(chart, 12) if p in NATURAL_MALEFICS]
    if not (p2 and p12):
        return None
    return {
        "rule_id":   "papakartari_lagna",
        "fired":     True,
        "finding":   (f"Papakartari yoga lagna pe — "
                      f"2H mein {', '.join(_hindi(p) for p in p2)} aur "
                      f"12H mein {', '.join(_hindi(p) for p in p12)} — "
                      f"vitality dono taraf se dabav mein hai."),
        "evidence":  {"second": p2, "twelfth": p12},
        "confidence": 0.78,
        "severity":  "high",
    }


def rule_papakartari_moon(chart: dict) -> Optional[dict]:
    """Malefics in 2nd and 12th from Moon → mental squeeze."""
    moon_h = _planet_house(chart, "Moon")
    if not isinstance(moon_h, int):
        return None
    h_next = _h_offset(moon_h, 1)   # 2nd from moon
    h_prev = _h_offset(moon_h, -1)  # 12th from moon
    p_next = [p for p in _planets_in_house(chart, h_next)
              if p in NATURAL_MALEFICS and p != "Moon"]
    p_prev = [p for p in _planets_in_house(chart, h_prev)
              if p in NATURAL_MALEFICS and p != "Moon"]
    if not (p_next and p_prev):
        return None
    return {
        "rule_id":   "papakartari_moon",
        "fired":     True,
        "finding":   (f"Chandra papakartari mein — Chandra {moon_h}H mein, "
                      f"dono taraf malefics ({', '.join(_hindi(p) for p in p_next)} "
                      f"aur {', '.join(_hindi(p) for p in p_prev)}) — "
                      f"mann pe lagataar dabav."),
        "evidence":  {"moon_house": moon_h,
                      "second_from_moon": p_next,
                      "twelfth_from_moon": p_prev},
        "confidence": 0.78,
        "severity":  "high",
    }


def rule_kemadruma_yoga(chart: dict) -> Optional[dict]:
    """Moon with no planet in 2nd or 12th from Moon (excluding Rahu/Ketu)
    → emotional isolation, mood instability.
    """
    moon_h = _planet_house(chart, "Moon")
    if not isinstance(moon_h, int):
        return None
    h_next = _h_offset(moon_h, 1)
    h_prev = _h_offset(moon_h, -1)
    real = lambda lst: [p for p in lst
                        if p not in ("Moon", "Rahu", "Ketu")]
    if real(_planets_in_house(chart, h_next)) or real(_planets_in_house(chart, h_prev)):
        return None
    return {
        "rule_id":   "kemadruma_yoga",
        "fired":     True,
        "finding":   (f"Kemadruma yoga — Chandra {moon_h}H mein akela hai "
                      f"(2nd/12th from Moon dono khali) — emotional isolation, "
                      f"mood ka utar-chadhav."),
        "evidence":  {"moon_house": moon_h},
        "confidence": 0.72,
        "severity":  "medium",
    }


def rule_eight_lord_with_six_lord(chart: dict) -> Optional[dict]:
    """6L and 8L in same house → strong disease formation."""
    six = _house_lord(chart, 6)
    eight = _house_lord(chart, 8)
    if not (six and eight):
        return None
    six_lord = six.get("lord")
    eight_lord = eight.get("lord")
    six_h = _coerce_int(six.get("lord_in_house"))
    eight_h = _coerce_int(eight.get("lord_in_house"))
    if not (six_lord and eight_lord and six_h and eight_h):
        return None
    if six_h != eight_h:
        return None
    if six_lord == eight_lord:
        return None  # same planet rules both — different finding, skip here
    return {
        "rule_id":   "eight_lord_with_six_lord",
        "fired":     True,
        "finding":   (f"Shashtesh {_hindi(six_lord)} aur Ashtmesh "
                      f"{_hindi(eight_lord)} dono {six_h}H mein milkar baithe "
                      f"hain — bimari ki gehri sambhavna, recovery time lega."),
        "evidence":  {"six_lord": six_lord, "eight_lord": eight_lord,
                      "house": six_h},
        "confidence": 0.82,
        "severity":  "high",
    }


def rule_eight_lord_with_lagna_lord(chart: dict) -> Optional[dict]:
    """1L and 8L in same house → life-vitality / health-life bridge stress."""
    one = _house_lord(chart, 1)
    eight = _house_lord(chart, 8)
    if not (one and eight):
        return None
    one_lord = one.get("lord")
    eight_lord = eight.get("lord")
    one_h = _coerce_int(one.get("lord_in_house"))
    eight_h = _coerce_int(eight.get("lord_in_house"))
    if not (one_lord and eight_lord and one_h and eight_h):
        return None
    if one_h != eight_h:
        return None
    if one_lord == eight_lord:
        return None
    return {
        "rule_id":   "eight_lord_with_lagna_lord",
        "fired":     True,
        "finding":   (f"Lagnesh {_hindi(one_lord)} aur Ashtmesh "
                      f"{_hindi(eight_lord)} dono {one_h}H mein — sehat aur "
                      f"jeevan-shakti ka bandhan kasta hai, deep health "
                      f"sensitivity."),
        "evidence":  {"lagna_lord": one_lord, "eight_lord": eight_lord,
                      "house": one_h},
        "confidence": 0.8,
        "severity":  "high",
    }


def rule_dasha_or_antar_lord_in_dusthana(chart: dict) -> Optional[dict]:
    """Either current Mahadasha OR Antardasha lord placed in 6/8/12
    → active health-weak window.
    """
    cd = chart.get("current_dasha")
    if not isinstance(cd, dict):
        return None
    flagged: list[tuple[str, str, int]] = []
    for level_key, label in (("maha", "Mahadasha"), ("antar", "Antardasha")):
        lord = cd.get(level_key)
        if isinstance(lord, dict):
            lord = lord.get("lord") or lord.get("planet")
        if not isinstance(lord, str):
            continue
        h = _planet_house(chart, lord)
        if h in DUSTHANAS:
            flagged.append((label, lord, h))
    if not flagged:
        return None
    bits = "; ".join(f"{lab} {_hindi(p)} {h}H" for lab, p, h in flagged)
    return {
        "rule_id":   "dasha_or_antar_lord_in_dusthana",
        "fired":     True,
        "finding":   (f"Active health-weak window: {bits} — is samay sehat "
                      f"par dhyaan dena zaroori hai."),
        "evidence":  {"flagged": [{"level": lab, "lord": p, "house": h}
                                  for lab, p, h in flagged]},
        "confidence": 0.85,
        "severity":  "high",
    }


def rule_kendra_lord_in_trika(chart: dict) -> Optional[dict]:
    """Lord of any kendra (1/4/7/10) sitting in trika (6/8/12)
    → kendra dignity falling into health/loss/transformation house.
    """
    kendras = (1, 4, 7, 10)
    flagged: list[tuple[int, str, int]] = []
    seen: set[str] = set()
    for kh in kendras:
        hl = _house_lord(chart, kh)
        if not hl:
            continue
        lord = hl.get("lord")
        in_h = _coerce_int(hl.get("lord_in_house"))
        if not (lord and in_h in DUSTHANAS):
            continue
        if lord in seen:
            continue
        seen.add(lord)
        flagged.append((kh, lord, in_h))
    if not flagged:
        return None
    bits = "; ".join(f"H{kh} swami {_hindi(p)} → {h}H"
                     for kh, p, h in flagged)
    return {
        "rule_id":   "kendra_lord_in_trika",
        "fired":     True,
        "finding":   (f"Kendra lord trika mein gaya — {bits} — "
                      f"shareer ke mukhya pillars (1/4/7/10) sehat-loss area "
                      f"se jude hain."),
        "evidence":  {"flagged": [{"kendra": kh, "lord": p, "in_house": h}
                                  for kh, p, h in flagged]},
        "confidence": 0.75,
        "severity":  "medium",
    }


def rule_trika_lord_in_kendra(chart: dict) -> Optional[dict]:
    """Lord of any trika (6/8/12) sitting in kendra (1/4/7/10)
    → disease/loss energy spilling into life pillars (mostly health drain;
    classical 'vipreet raja' applies only when trika lords aspect each other,
    which we do NOT claim here).
    """
    kendras = (1, 4, 7, 10)
    flagged: list[tuple[int, str, int]] = []
    seen: set[str] = set()
    for th in DUSTHANAS:
        hl = _house_lord(chart, th)
        if not hl:
            continue
        lord = hl.get("lord")
        in_h = _coerce_int(hl.get("lord_in_house"))
        if not (lord and in_h in kendras):
            continue
        if lord in seen:
            continue
        seen.add(lord)
        flagged.append((th, lord, in_h))
    if not flagged:
        return None
    bits = "; ".join(f"H{th} swami {_hindi(p)} → {h}H"
                     for th, p, h in flagged)
    return {
        "rule_id":   "trika_lord_in_kendra",
        "fired":     True,
        "finding":   (f"Trika lord kendra mein — {bits} — "
                      f"bimari/loss ki urja jeevan ke pillars tak pohonchti "
                      f"hai, lifestyle discipline zaroori."),
        "evidence":  {"flagged": [{"trika": th, "lord": p, "in_house": h}
                                  for th, p, h in flagged]},
        "confidence": 0.7,
        "severity":  "medium",
    }


def rule_moon_in_eight_or_twelve(chart: dict) -> Optional[dict]:
    """Moon in 8H or 12H → mental low / hidden emotional patterns."""
    h = _planet_house(chart, "Moon")
    if h not in (8, 12):
        return None
    flavor = ("transformative emotional cycle" if h == 8
             else "hidden emotional drain, sleep aur retreat zaroori")
    return {
        "rule_id":   "moon_in_eight_or_twelve",
        "fired":     True,
        "finding":   (f"Chandra {h}H mein — mann ki sthiti {flavor}; "
                      f"meditation, regular routine, aur emotional outlet help karenge."),
        "evidence":  {"house": h},
        "confidence": 0.72,
        "severity":  "medium",
    }


def rule_jupiter_in_six_or_eight(chart: dict) -> Optional[dict]:
    """Jupiter in 6H or 8H → health protector compromised; can also act
    as a recovery aid when in 6H (vipareeta-style benefic). Both flavors
    are relevant for narrator tone.
    """
    h = _planet_house(chart, "Jupiter")
    if h not in (6, 8):
        return None
    if h == 6:
        msg = ("Guru 6H mein — chronic illness se ladne ki shakti deta hai, "
               "lekin shareer pe stress fir bhi rehta hai.")
    else:
        msg = ("Guru 8H mein — gehri sehat sensitivity, "
               "deep healing aur dhyaan ki zarurat hai.")
    return {
        "rule_id":   "jupiter_in_six_or_eight",
        "fired":     True,
        "finding":   msg,
        "evidence":  {"house": h},
        "confidence": 0.7,
        "severity":  "medium",
    }


# ── Registry + dispatcher ────────────────────────────────────────────────────

RULE_REGISTRY: dict[str, Callable[[dict], Optional[dict]]] = {
    "lagna_lord_in_dusthana":      rule_lagna_lord_in_dusthana,
    "six_lord_in_dusthana":        rule_six_lord_in_dusthana,
    "eight_lord_in_lagna_or_six":  rule_eight_lord_in_lagna_or_six,
    "twelve_lord_active":          rule_twelve_lord_active,
    "malefic_in_lagna":            rule_malefic_in_lagna,
    "malefic_in_six":              rule_malefic_in_six,
    "moon_with_malefic":           rule_moon_with_malefic,
    "mercury_afflicted":           rule_mercury_afflicted,
    "sun_in_six_or_eight":         rule_sun_in_six_or_eight,
    "sun_afflicted":               rule_sun_afflicted,
    "mars_in_one_or_six":          rule_mars_in_one_or_six,
    "mars_afflicted":              rule_mars_afflicted,
    "saturn_aspect_lagna":         rule_saturn_aspect_lagna,
    "saturn_in_lagna_or_six":      rule_saturn_in_lagna_or_six,
    "rahu_in_lagna":               rule_rahu_in_lagna,
    "ketu_in_lagna_or_six":        rule_ketu_in_lagna_or_six,
    "sade_sati_active":            rule_sade_sati_active,
    "mangal_dosh_active":          rule_mangal_dosh_active,
    "current_dasha_dusthana_lord": rule_current_dasha_dusthana_lord,
    "jupiter_aspect_lagna":        rule_jupiter_aspect_lagna,
    "venus_in_six_or_eight":       rule_venus_in_six_or_eight,
    "house_lord_placement_summary": rule_house_lord_placement_summary,
    # Phase 7.6.1 additions
    "venus_afflicted":               rule_venus_afflicted,
    "jupiter_afflicted":             rule_jupiter_afflicted,
    "papakartari_lagna":             rule_papakartari_lagna,
    "papakartari_moon":              rule_papakartari_moon,
    "kemadruma_yoga":                rule_kemadruma_yoga,
    "eight_lord_with_six_lord":      rule_eight_lord_with_six_lord,
    "eight_lord_with_lagna_lord":    rule_eight_lord_with_lagna_lord,
    "dasha_or_antar_lord_in_dusthana": rule_dasha_or_antar_lord_in_dusthana,
    "kendra_lord_in_trika":          rule_kendra_lord_in_trika,
    "trika_lord_in_kendra":          rule_trika_lord_in_kendra,
    "moon_in_eight_or_twelve":       rule_moon_in_eight_or_twelve,
    "jupiter_in_six_or_eight":       rule_jupiter_in_six_or_eight,
}


def evaluate_rules(rule_ids: list[str], chart: dict) -> list[dict]:
    """Run each requested rule against the chart. Skip unknown IDs.

    Returns only the findings where `fired=True`. Order matches input.
    Each rule is wrapped in try/except — a single bad rule never blocks
    the others.
    """
    findings: list[dict] = []
    if not isinstance(chart, dict) or not rule_ids:
        return findings
    for rid in rule_ids:
        fn = RULE_REGISTRY.get(rid)
        if fn is None:
            continue
        try:
            res = fn(chart)
        except Exception:
            # Defensive — never let one rule blow up the engine pass.
            continue
        if isinstance(res, dict) and res.get("fired"):
            findings.append(res)
    return findings
