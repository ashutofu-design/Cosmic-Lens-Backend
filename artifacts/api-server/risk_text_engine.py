"""
Cosmic Lens — Risk Text Engine
==============================
Enriches the existing energy-engine Risk Radar output with personalised
"KYA RISK / DHYAN / AVOID / KARNA / UPAY" text and Choghadiya-based
"BEST TIME / AVOID TIME" windows.

Brand voice  : Hinglish, supportive, never reveals planet/dasha names.
                Tagline reference: "Powered by Advanced Cosmic Intelligence".
Real engine  : All triggers come from energy_engine signals (Chandrashtama,
                Tara Bal, Sade Sati phase, Mars affliction, PD weakness,
                Tithi type, Rahukal, Volatile day). NO random fallbacks.

Inputs
------
- energy_result    : dict from energy_engine.calculate_energy(...)
- radar            : dict from energy_engine.compute_risk_radar(...)
- weekday          : int 0..6 (Mon..Sun) — local
- sunrise, sunset  : decimal local hours (e.g. 6.42, 18.83)
- current_hour     : decimal local hour for the "next upcoming" window
                      selection (e.g. 14.5 for 2:30 PM); pass 0 to start
                      from sunrise of the same day.

Output (merged into the API response)
-------------------------------------
    {
      "top_risk": {
        "trigger":   "<signal-id>",
        "category":  "Money / Conflict / Relations / Health / ...",
        "kya_risk_hai":          "...",
        "kya_dhyan_rakhna_hai":  "...",
        "kya_avoid_karna_hai":   "...",
        "kya_karna_hai":         "...",
        "upay":                  "..."
      },
      "best_time":  {"window": "10:42 AM — 12:18 PM", "label": "Amrit"},
      "avoid_time": {"window": "1:54 PM — 3:30 PM",   "label": "Rahukaal"},
      "choghadiya_today": [
        {"start": "06:25", "end": "07:48", "name": "Amrit", "period": "day", "quality": "best"},
        ...
      ]
    }
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Reuse the canonical Choghadiya tables + Rahukal segment map already
# defined in energy_engine.py — single source of truth.
from energy_engine import (
    _DAY_CHOGHADIYA,
    _NIGHT_CHOGHADIYA,
    _RAHUKAL_SEGMENT,
)

# ──────────────────────────────────────────────────────────────────────────────
# 1. TRIGGER → PERSONALISED TEXT MAP
#    Each trigger key matches the signal logic inside compute_risk_radar.
#    Voice = supportive Hinglish, no jargon, no destiny language.
# ──────────────────────────────────────────────────────────────────────────────

_TEXT_MAP: Dict[str, Dict[str, str]] = {
    # ── 1. Volatile day (multiple negative signals stacked) ─────────────────
    "volatile_day": {
        "category":            "Mixed Energy",
        "kya_risk_hai":        "Aaj kaafi mixed energy hai — ek ghante mein "
                                "achha lagega, agle ghante mein heavy. Ups aur "
                                "downs ke beech khud ko anchored rakhna zaroori hai.",
        "kya_dhyan_rakhna_hai":"Reactions slow karein. Ek pause-breath-respond "
                                "rule follow karein. Doosron ki mood swings ko "
                                "personally mat lein.",
        "kya_avoid_karna_hai": "Bade financial commitments, public arguments, "
                                "important emails jaldi mein send karna, aur "
                                "social media par strong opinions.",
        "kya_karna_hai":       "Routine kaam, journaling, light exercise, aur "
                                "ek trusted person se baat. Observation > reaction.",
        "upay":                "Subah aur shaam dono time 5 minute deep breathing. "
                                "Ek glass paani mein chutki haldi — body ko ground karega.",
    },

    # ── 2. Chandrashtama (Moon in 8th from natal Moon) — severity 9 ─────────
    "chandrashtama": {
        "category":            "Emotional Sensitivity",
        "kya_risk_hai":        "Aaj mann ki energy thodi disturbed hai. Chhoti "
                                "baat bhi badi feel ho sakti hai, aur emotional "
                                "matters mein clarity kam rahegi.",
        "kya_dhyan_rakhna_hai":"Apne mann ko quiet rakhein. Doosron ke comments "
                                "ko literal mat lein — aaj filter zaroori hai.",
        "kya_avoid_karna_hai": "Emotional decisions, family confrontations, "
                                "relationship 'serious talks', aur late-night "
                                "social media scrolling.",
        "kya_karna_hai":       "Solo kaam, journaling, gentle walk, ya koi "
                                "creative outlet. Apne thoughts ko process karein.",
        "upay":                "Subah ek glass paani mein 2 chamach gulab jal "
                                "milake piye — mann ko sheetal karega. Shaam ko "
                                "chandra mantra 'Om Som Somaya Namah' 11 baar.",
    },

    # ── 3. Tara Bal — Naidhana/Vadha (worst) — severity 8 ───────────────────
    "tara_naidhana": {
        "category":            "Reflective / Slow Day",
        "kya_risk_hai":        "Aaj nakshatra balance reflective mode mein hai. "
                                "Energy reserve mein rakhne ka din — naye "
                                "ventures stuck feel ho sakte hain.",
        "kya_dhyan_rakhna_hai":"Ek baat 2 baar sochein. Slow pace ko weakness "
                                "mat samjhein — yeh aaj ki strength hai.",
        "kya_avoid_karna_hai": "Naye contracts sign karna, public appearances, "
                                "interviews, ya important launches.",
        "kya_karna_hai":       "Existing kaam complete karein, planning "
                                "documents likhein, research aur reading.",
        "upay":                "Shaam ko ghee ka diya jalaayein, aur Hanuman "
                                "Chalisa ek baar. Naidhana energy ko soft karta hai.",
    },

    # ── 4. Saturn heavy (Sade Sati Madhya / Ashtam Shani) — severity 8 ─────
    "saturn_heavy": {
        "category":            "Pressure / Patience",
        "kya_risk_hai":        "Background mein heavy responsibility ki feeling "
                                "chal rahi hai. Aaj zyada thakaan, slow progress, "
                                "aur authority figures se friction ho sakta hai.",
        "kya_dhyan_rakhna_hai":"Patience top priority. Slow aur steady approach "
                                "se aaj ka kaam aage badhega. Discipline help karegi.",
        "kya_avoid_karna_hai": "Shortcuts, jaldbaazi, bosses ya elders se "
                                "argument, aur 'main hi sahi hu' attitude.",
        "kya_karna_hai":       "Structured kaam, routines maintain karein, "
                                "ek senior se guidance lein, aur kisi zaroori "
                                "person ki seva karein.",
        "upay":                "Shani mantra 'Om Sham Shanaishcharaya Namah' 11 "
                                "baar. Saturday ko kaale til ka daan ya kisi "
                                "needy ko khaana khilaayein.",
    },

    # ── 5. Mars affliction (Mars in 1/4/7/8/12 OR jup_mars delta < -3) — 7 ──
    "mars_active": {
        "category":            "Conflict / Anger",
        "kya_risk_hai":        "Aaj jaldbaazi aur frustration ki energy active "
                                "hai. Words sharp ho sakte hain, aur conflicts "
                                "(road, office, ghar mein) ka risk zyada.",
        "kya_dhyan_rakhna_hai":"Apni reactions slow karein. Bolne se pehle 3 "
                                "second pause. Anger physical channel mein nikalo "
                                "(walk, exercise) — words mein nahi.",
        "kya_avoid_karna_hai": "Arguments, sharp emails, impulsive driving, "
                                "alcohol, aur 'main right hu' wala ego mode.",
        "kya_karna_hai":       "Physical exercise, controlled venting (gym, "
                                "running), detail wala focused kaam, aur "
                                "competitive sports (constructive outlet).",
        "upay":                "Tuesday ko laal masoor ki dal kisi needy ko "
                                "daan. Hanuman Chalisa subah ek baar — Mangal "
                                "ki energy ko balance karta hai.",
    },

    # ── 6. Tara mild (Vipat / Pratyak) — severity 6 ─────────────────────────
    "tara_mild": {
        "category":            "Mental Drain",
        "kya_risk_hai":        "Aaj overthinking aur thakaan zyada feel hogi. "
                                "Productivity normal se kam rahegi, irritation "
                                "easily trigger ho sakti hai.",
        "kya_dhyan_rakhna_hai":"Apne body ke signals ko sune. Mind ko force "
                                "mat karein — break lena weakness nahi hai.",
        "kya_avoid_karna_hai": "Marathon meetings, multi-tasking, caffeine "
                                "overdose, aur emotionally draining conversations.",
        "kya_karna_hai":       "Power-naps, light meals, ek walk fresh air mein, "
                                "aur jo kaam asaan hain wo pehle nipta dein.",
        "upay":                "Shaam ko 10 minute meditation ya pranayam "
                                "(anulom-vilom). Mind reset karega.",
    },

    # ── 7. PD weak (Pratyantar dasha lord delta ≤ -4) — severity 6 ──────────
    "pd_weak": {
        "category":            "Delays / Effort vs Results",
        "kya_risk_hai":        "Aaj effort to chal raha hai par results dheere "
                                "milenge. Important kaam mein delays, follow-ups "
                                "mein silence, aur small obstacles ho sakte hain.",
        "kya_dhyan_rakhna_hai":"Process pe focus karein, outcome pe nahi. "
                                "Results timeline mein flexibility rakhein.",
        "kya_avoid_karna_hai": "Tight deadlines commit karna, panic karna, "
                                "ek hi din mein 10 kaam list karna.",
        "kya_karna_hai":       "Buffer time rakhein, ek kaam ek time, follow-ups "
                                "consistent rakhein, aur planning detailed karein.",
        "upay":                "Apne ishtadev ka 5 minute dhyan subah. Patience "
                                "aur consistency ki energy strong hogi.",
    },

    # ── 8. Tithi Amavasya — severity 6 ─────────────────────────────────────
    "amavasya": {
        "category":            "Introspective / Low Energy",
        "kya_risk_hai":        "Aaj din heavy aur introspective rahega. Energy "
                                "naturally slow hogi, mood thoda heavy. Body "
                                "rest maang rahi hai.",
        "kya_dhyan_rakhna_hai":"Body ke signals sune, naye kaam start mat "
                                "karein. Aaj 'restoration day' samjhein.",
        "kya_avoid_karna_hai": "Naye purchases, contracts, travel start, aur "
                                "important launches.",
        "kya_karna_hai":       "Existing kaam smoothly nipta dein, light "
                                "saatvik food, family ke saath quiet time.",
        "upay":                "Shaam ko ghee ka diya pitr-sthan (north-east) "
                                "mein. Amavasya par pitru-tarpan se peace milti hai.",
    },

    # ── 9. Saturn mild (Sade Sati Phase 1/3 or Kantaka) — severity 5 ───────
    "saturn_mild": {
        "category":            "Background Pressure",
        "kya_risk_hai":        "Background mein thoda burden chal raha hai. "
                                "Heavy nahi par steady — thakaan slowly build "
                                "ho sakti hai.",
        "kya_dhyan_rakhna_hai":"Steady aur consistent rahein. Shortcuts ki "
                                "tempt ho sakti hai — avoid karein.",
        "kya_avoid_karna_hai": "Cutting corners, deadlines miss karna, elders "
                                "ki advice ignore karna.",
        "kya_karna_hai":       "Long-term planning, organising, decluttering, "
                                "aur structured routine maintain karein.",
        "upay":                "Saturday ko kaale til + sarso ka tel kisi shani "
                                "mandir mein. Discipline ke saath kaam karna sabse "
                                "bada upay hai.",
    },

    # ── 10. Tithi Rikta (drain) — severity 5 ───────────────────────────────
    "tithi_rikta": {
        "category":            "Energy Drain",
        "kya_risk_hai":        "Aaj body aur mind dono mein energy thodi kam "
                                "hogi. Heavy commitments ka burden feel hoga.",
        "kya_dhyan_rakhna_hai":"Aaj 'less is more'. Jo critical hai wahi karein, "
                                "baki kal ke liye rakhein.",
        "kya_avoid_karna_hai": "Heavy workload, late nights, junk food, aur "
                                "draining social commitments.",
        "kya_karna_hai":       "Light meals, hydration, kaam mein breaks, aur "
                                "early sleep.",
        "upay":                "Shaam ko warm haldi-doodh. Energy restore karega "
                                "aur immunity boost karega.",
    },

    # ── 11. Rahukal active — severity 4 ────────────────────────────────────
    "rahukal_active": {
        "category":            "Sensitive Time Window",
        "kya_risk_hai":        "Aaj din mein ek window thodi sensitive hai "
                                "(Rahukaal). Iss samay liye decisions later mein "
                                "complications la sakte hain.",
        "kya_dhyan_rakhna_hai":"Important calls, signatures, aur naye kaam "
                                "Rahukaal ke baad ke liye rakhein.",
        "kya_avoid_karna_hai": "Naye ventures Rahukaal ke beech mein, important "
                                "meetings, aur major financial transactions.",
        "kya_karna_hai":       "Existing routine kaam continue karein, planning "
                                "aur reading kaam Rahukaal mein safe hai.",
        "upay":                "Rahukaal ke samay Hanuman Chalisa ya Maha "
                                "Mrityunjaya 11 baar — protective shield banti hai.",
    },

    # ── 12. Stable / Smooth Day — fallback when no risks active ─────────────
    "stable_day": {
        "category":            "Smooth Flow",
        "kya_risk_hai":        "Aaj koi major risk signal nahi mil raha — "
                                "energies aapke favor mein hain. Smooth flow ka din.",
        "kya_dhyan_rakhna_hai":"Opportunities ko khule mann se accept karein, "
                                "momentum banaye rakhein. Khud pe trust rakhein.",
        "kya_avoid_karna_hai": "Negative self-talk, doosron ki pessimism, aur "
                                "'kuch galat ho jayega' wali sochein.",
        "kya_karna_hai":       "Naye projects start, networking, important "
                                "calls, presentations, aur growth-oriented kaam.",
        "upay":                "Subah Surya ko jal arghya — energy boost ke liye. "
                                "Din ki shuruwat gratitude ke saath karein.",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# 2. CHOGHADIYA → QUALITY MAP (best/neutral/avoid)
# ──────────────────────────────────────────────────────────────────────────────

_CHOGHADIYA_QUALITY: Dict[str, str] = {
    "Amrit": "best",  "Shubh": "best",  "Labh": "best",
    "Char":  "neutral",
    "Udveg": "avoid", "Rog":   "avoid", "Kaal": "avoid",
}
# Higher = better when picking "best_time"
_BEST_RANK: Dict[str, int] = {"Amrit": 3, "Shubh": 2, "Labh": 2, "Char": 0,
                              "Udveg": -2, "Rog": -3, "Kaal": -3}


# ──────────────────────────────────────────────────────────────────────────────
# 3. UTIL — format decimal hour as "h:mm AM/PM"
# ──────────────────────────────────────────────────────────────────────────────

def _fmt_time(decimal_hour: float) -> str:
    """Format decimal hour as 'h:mm AM/PM'. Wraps over 24h cleanly."""
    h = decimal_hour % 24.0
    hh = int(h)
    mm = int(round((h - hh) * 60))
    if mm == 60:
        mm = 0
        hh = (hh + 1) % 24
    period = "AM" if hh < 12 else "PM"
    disp = hh % 12
    if disp == 0:
        disp = 12
    return f"{disp}:{mm:02d} {period}"


# ──────────────────────────────────────────────────────────────────────────────
# 4. BUILD FULL DAY+NIGHT CHOGHADIYA SCHEDULE (16 segments)
# ──────────────────────────────────────────────────────────────────────────────

def build_choghadiya_schedule(weekday: int,
                              sunrise: float,
                              sunset: float
                              ) -> List[Dict[str, Any]]:
    """
    Build full 16-segment Choghadiya schedule for the given weekday.
    Each segment includes start/end times (decimal + display) and quality.

    weekday : 0=Mon..6=Sun  (Python datetime.weekday())
    """
    segments: List[Dict[str, Any]] = []
    day_length   = max(0.5, sunset - sunrise)
    night_length = 24.0 - day_length

    # ── 8 day-time segments ────────────────────────────────────────────────
    day_seg_len = day_length / 8.0
    day_names   = _DAY_CHOGHADIYA.get(weekday, [])
    for i, name in enumerate(day_names):
        start = sunrise + i * day_seg_len
        end   = start + day_seg_len
        segments.append({
            "start_h": round(start, 4),
            "end_h":   round(end, 4),
            "start":   _fmt_time(start),
            "end":     _fmt_time(end),
            "name":    name,
            "period":  "day",
            "quality": _CHOGHADIYA_QUALITY.get(name, "neutral"),
            "rank":    _BEST_RANK.get(name, 0),
        })

    # ── 8 night-time segments ──────────────────────────────────────────────
    night_seg_len = night_length / 8.0
    night_names   = _NIGHT_CHOGHADIYA.get(weekday, [])
    for i, name in enumerate(night_names):
        start = sunset + i * night_seg_len
        end   = start + night_seg_len
        segments.append({
            "start_h": round(start, 4),
            "end_h":   round(end, 4),
            "start":   _fmt_time(start),
            "end":     _fmt_time(end),
            "name":    name,
            "period":  "night",
            "quality": _CHOGHADIYA_QUALITY.get(name, "neutral"),
            "rank":    _BEST_RANK.get(name, 0),
        })

    return segments


def compute_rahukaal_window(weekday: int,
                            sunrise: float,
                            sunset: float
                            ) -> Optional[Dict[str, Any]]:
    """
    Return the day's Rahukaal window as {start, end, label}.
    Returns None for Sunday only if not in segment map.
    """
    seg = _RAHUKAL_SEGMENT.get(weekday)
    if seg is None:
        return None
    day_length = max(0.1, sunset - sunrise)
    seg_len    = day_length / 8.0
    start      = sunrise + (seg - 1) * seg_len
    end        = start + seg_len
    return {
        "start_h": round(start, 4),
        "end_h":   round(end, 4),
        "start":   _fmt_time(start),
        "end":     _fmt_time(end),
        "label":   "Rahukaal",
    }


# ──────────────────────────────────────────────────────────────────────────────
# 5. PICK BEST + AVOID TIME WINDOWS
# ──────────────────────────────────────────────────────────────────────────────

def pick_best_avoid_times(schedule: List[Dict[str, Any]],
                          rahukaal: Optional[Dict[str, Any]],
                          current_h: float
                          ) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    From today's Choghadiya schedule, pick:
      - best_time  : earliest UPCOMING "best" (Amrit > Shubh = Labh) window.
                      If all best windows have passed today, return the
                      best-ranked one of the day with a "tomorrow's first"
                      hint stripped away — caller can prefix "Aaj nahi to kal".
      - avoid_time : Rahukaal if available; else earliest upcoming
                      Rog/Kaal/Udveg window.

    Both windows are returned as user-facing strings:
      {"window": "10:42 AM — 12:18 PM", "label": "Amrit"}
    """
    # ── Best time: prefer upcoming, highest rank ───────────────────────────
    upcoming_best = [s for s in schedule
                     if s["quality"] == "best" and s["end_h"] > current_h]
    if upcoming_best:
        # Sort by (rank desc, start asc) so Amrit beats Shubh/Labh ties
        upcoming_best.sort(key=lambda s: (-s["rank"], s["start_h"]))
        best = upcoming_best[0]
    else:
        all_best = [s for s in schedule if s["quality"] == "best"]
        if all_best:
            all_best.sort(key=lambda s: (-s["rank"], s["start_h"]))
            best = all_best[0]
        else:
            # Pure fallback: earliest neutral window (Char) — never lies
            neutral = [s for s in schedule if s["quality"] == "neutral"]
            best = neutral[0] if neutral else schedule[0]

    best_out = {
        "window": f"{best['start']} — {best['end']}",
        "label":  best["name"],
        "period": best["period"],
    }

    # ── Avoid time: Rahukaal first, then earliest upcoming "avoid" ─────────
    if rahukaal and rahukaal["end_h"] > current_h:
        avoid_out = {
            "window": f"{rahukaal['start']} — {rahukaal['end']}",
            "label":  "Rahukaal",
            "period": "day",
        }
    else:
        upcoming_avoid = [s for s in schedule
                          if s["quality"] == "avoid" and s["end_h"] > current_h]
        if upcoming_avoid:
            # Earliest, then by rank (most negative first)
            upcoming_avoid.sort(key=lambda s: (s["start_h"], s["rank"]))
            av = upcoming_avoid[0]
            avoid_out = {
                "window": f"{av['start']} — {av['end']}",
                "label":  av["name"],
                "period": av["period"],
            }
        elif rahukaal:
            avoid_out = {
                "window": f"{rahukaal['start']} — {rahukaal['end']}",
                "label":  "Rahukaal",
                "period": "day",
            }
        else:
            # Last resort: any avoid segment in schedule
            any_avoid = [s for s in schedule if s["quality"] == "avoid"]
            if any_avoid:
                any_avoid.sort(key=lambda s: s["rank"])  # most negative first
                av = any_avoid[0]
                avoid_out = {
                    "window": f"{av['start']} — {av['end']}",
                    "label":  av["name"],
                    "period": av["period"],
                }
            else:
                avoid_out = {"window": "", "label": "", "period": ""}

    return best_out, avoid_out


# ──────────────────────────────────────────────────────────────────────────────
# 6. PICK DOMINANT TRIGGER FROM ENERGY-ENGINE SIGNALS
#    Mirrors compute_risk_radar's signal logic; ranks by severity.
# ──────────────────────────────────────────────────────────────────────────────

def detect_dominant_trigger(energy_result: Dict[str, Any]) -> str:
    """
    Inspect energy_result overlays/components and return the highest-severity
    trigger key from _TEXT_MAP. Returns 'stable_day' if no risk signals fire.
    """
    components = energy_result.get("components", {}) or {}
    overlays   = energy_result.get("overlays", {}) or {}
    flags      = energy_result.get("active_flags", []) or []

    moon_d     = components.get("moon_transit", {}) or {}
    tara_d     = components.get("tara_bal", {}) or {}
    saturn_d   = overlays.get("saturn", {}) or {}
    tithi_d    = overlays.get("tithi", {}) or {}
    pd_d       = overlays.get("pd_transit", {}) or {}
    jup_mars_d = overlays.get("jupiter_mars", {}) or {}
    time_q_d   = overlays.get("time_quality", {}) or {}

    volatile = bool(overlays.get("volatile_day", False))
    saturn_phase = saturn_d.get("phase", "") if saturn_d.get("active") else ""
    tara_idx     = tara_d.get("tara_idx", -1)
    tithi_type   = tithi_d.get("type", "") or ""
    tithi_idx    = tithi_d.get("tithi_idx", -1)
    pd_delta     = pd_d.get("delta", 0) or 0
    jup_mars_delta = jup_mars_d.get("delta", 0) or 0
    mars_house     = (jup_mars_d.get("mars_house")
                      or jup_mars_d.get("mars_house_lagna"))

    # Severity-ranked candidate list (same scores as compute_risk_radar)
    cands: List[Tuple[int, str]] = []
    if volatile:
        cands.append((10, "volatile_day"))
    if moon_d.get("chandrashtama"):
        cands.append((9,  "chandrashtama"))
    if tara_idx == 6:
        cands.append((8,  "tara_naidhana"))
    if "Madhya" in saturn_phase or "Ashtam" in saturn_phase:
        cands.append((8,  "saturn_heavy"))
    if jup_mars_delta < -3 or mars_house in (1, 4, 7, 8, 12):
        cands.append((7,  "mars_active"))
    if tara_idx in (2, 4):
        cands.append((6,  "tara_mild"))
    if pd_delta <= -4:
        cands.append((6,  "pd_weak"))
    # Tithi: Rikta takes precedence over Amavasya when both present
    # (mirrors compute_risk_radar's `if Rikta ... elif Amavasya` ordering)
    if tithi_type == "Rikta (drain)":
        cands.append((6,  "tithi_rikta"))
    elif tithi_idx == 30:
        cands.append((6,  "amavasya"))
    if ("Phase 1" in saturn_phase or "Phase 3" in saturn_phase
            or "Kantaka" in saturn_phase):
        cands.append((5,  "saturn_mild"))
    if bool(time_q_d.get("rahukal")) or "rahukal" in flags:
        cands.append((4,  "rahukal_active"))

    if not cands:
        return "stable_day"
    cands.sort(key=lambda c: -c[0])
    return cands[0][1]


# ──────────────────────────────────────────────────────────────────────────────
# 7. PUBLIC API — enrich the existing Risk Radar response
# ──────────────────────────────────────────────────────────────────────────────

def enrich_risk_radar(radar:         Dict[str, Any],
                      energy_result: Dict[str, Any],
                      weekday:       int,
                      sunrise:       float,
                      sunset:        float,
                      current_h:     float = 0.0,
                      ) -> Dict[str, Any]:
    """
    Merge personalised top-level text + Choghadiya timing into the Risk
    Radar dict produced by energy_engine.compute_risk_radar.

    The original `risk_radar_24h` array is preserved untouched (mobile may
    still want to display the multi-risk list). New top-level keys added:
      - top_risk         (5-field personalised text + trigger metadata)
      - best_time        ({window, label, period})
      - avoid_time       ({window, label, period})
      - choghadiya_today (full 16-segment schedule)
      - rahukaal_today   ({start, end, label}) or None

    Mutates and returns `radar` for convenience.
    """
    # ── 1. Detect dominant trigger from real engine signals ─────────────────
    trigger = detect_dominant_trigger(energy_result)
    text    = _TEXT_MAP.get(trigger) or _TEXT_MAP["stable_day"]

    radar["top_risk"] = {
        "trigger":              trigger,
        "category":             text["category"],
        "kya_risk_hai":         text["kya_risk_hai"],
        "kya_dhyan_rakhna_hai": text["kya_dhyan_rakhna_hai"],
        "kya_avoid_karna_hai":  text["kya_avoid_karna_hai"],
        "kya_karna_hai":        text["kya_karna_hai"],
        "upay":                 text["upay"],
    }

    # ── 2. Build Choghadiya schedule + Rahukaal window ──────────────────────
    schedule = build_choghadiya_schedule(weekday, sunrise, sunset)
    rahukaal = compute_rahukaal_window(weekday, sunrise, sunset)

    best_time, avoid_time = pick_best_avoid_times(schedule, rahukaal, current_h)

    radar["best_time"]        = best_time
    radar["avoid_time"]       = avoid_time
    radar["choghadiya_today"] = [
        {
            "start":   s["start"],
            "end":     s["end"],
            "name":    s["name"],
            "period":  s["period"],
            "quality": s["quality"],
        } for s in schedule
    ]
    radar["rahukaal_today"]   = (
        {"start": rahukaal["start"], "end": rahukaal["end"], "label": "Rahukaal"}
        if rahukaal else None
    )

    # ── 3. Brand-voice attribution (NEVER reveal AI/LLM) ────────────────────
    radar.setdefault("powered_by", "Advanced Cosmic Intelligence")

    return radar


__all__ = [
    "enrich_risk_radar",
    "build_choghadiya_schedule",
    "compute_rahukaal_window",
    "pick_best_avoid_times",
    "detect_dominant_trigger",
]
