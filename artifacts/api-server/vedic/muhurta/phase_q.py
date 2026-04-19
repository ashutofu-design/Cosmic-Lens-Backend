"""
Sprint 42 / Phase Q — Muhurta Full
Q1. Choghadiya (8 daily periods × 2 day/night = 16 windows)
Q2. Hora (24 daily, planet-wise hour-lord)
Q3. Rahu Kaal, Yamaganda Kaal, Gulika Kaal
Q4. Abhijit Muhurta, Brahma Muhurta
Q5. 30+ event muhurtas (marriage, business, travel, surgery, naamkaran, …)
Heuristic: sunrise=06:00, sunset=18:00 (no lat/lon available).
"""
from __future__ import annotations
from datetime import datetime, date, timedelta
from typing import Any

WEEKDAY_LORDS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]  # Mon=0?  python: Monday=0
# Python date.weekday(): Mon=0..Sun=6 → map to lord.
PY_WD_TO_LORD = {0:"Moon",1:"Mars",2:"Mercury",3:"Jupiter",4:"Venus",5:"Saturn",6:"Sun"}

# Q1 — Choghadiya day starting names by weekday (Sun=Udveg start)
CHOG_DAY = {
    "Sun":     ["Udveg","Char","Labh","Amrit","Kaal","Shubh","Rog","Udveg"],
    "Moon":    ["Amrit","Kaal","Shubh","Rog","Udveg","Char","Labh","Amrit"],
    "Tue":     ["Rog","Udveg","Char","Labh","Amrit","Kaal","Shubh","Rog"],
    "Mars":    ["Rog","Udveg","Char","Labh","Amrit","Kaal","Shubh","Rog"],
    "Mercury": ["Labh","Amrit","Kaal","Shubh","Rog","Udveg","Char","Labh"],
    "Jupiter": ["Shubh","Rog","Udveg","Char","Labh","Amrit","Kaal","Shubh"],
    "Venus":   ["Char","Labh","Amrit","Kaal","Shubh","Rog","Udveg","Char"],
    "Saturn":  ["Kaal","Shubh","Rog","Udveg","Char","Labh","Amrit","Kaal"],
}
CHOG_NIGHT = {
    "Sun":     ["Shubh","Amrit","Char","Rog","Kaal","Labh","Udveg","Shubh"],
    "Moon":    ["Char","Rog","Kaal","Labh","Udveg","Shubh","Amrit","Char"],
    "Mars":    ["Kaal","Labh","Udveg","Shubh","Amrit","Char","Rog","Kaal"],
    "Mercury": ["Udveg","Shubh","Amrit","Char","Rog","Kaal","Labh","Udveg"],
    "Jupiter": ["Amrit","Char","Rog","Kaal","Labh","Udveg","Shubh","Amrit"],
    "Venus":   ["Rog","Kaal","Labh","Udveg","Shubh","Amrit","Char","Rog"],
    "Saturn":  ["Labh","Udveg","Shubh","Amrit","Char","Rog","Kaal","Labh"],
}
CHOG_QUALITY = {
    "Amrit":"BEST (nectar — all auspicious work)",
    "Shubh":"GOOD (auspicious — ceremonies, learning)",
    "Labh":"GOOD (gain — business, transactions)",
    "Char":"NEUTRAL (movable — travel ok)",
    "Kaal":"AVOID (negative — postpone if possible)",
    "Rog":"AVOID (illness — health risk)",
    "Udveg":"AVOID (anxiety — disputes risk)",
}

# Q2 — Hora: each hour ruled by planet in Sun-Venus-Mercury-Moon-Saturn-Jupiter-Mars cycle
HORA_CYCLE = ["Sun","Venus","Mercury","Moon","Saturn","Jupiter","Mars"]
HORA_QUALITY = {
    "Sun":"authority/govt work","Moon":"travel/water/emotion",
    "Mars":"surgery/property/courage","Mercury":"writing/study/business",
    "Jupiter":"learning/spiritual/wedding","Venus":"romance/luxury/art",
    "Saturn":"discipline/longevity/iron",
}

# Q3 — Rahu/Yama/Gulika kaal — slot index by weekday (out of 8 day-slots)
RAHU_SLOT = {"Sun":7,"Moon":1,"Mars":6,"Mercury":4,"Jupiter":5,"Venus":3,"Saturn":2}
YAMA_SLOT = {"Sun":4,"Moon":3,"Mars":2,"Mercury":1,"Jupiter":7,"Venus":5,"Saturn":6}
GULI_SLOT = {"Sun":6,"Moon":5,"Mars":4,"Mercury":3,"Jupiter":2,"Venus":1,"Saturn":7}

# Q5 — 30+ classical event muhurtas: which Choghadiya/Hora/Tithi favours each event
EVENT_MUHURTAS = [
    ("Marriage / Vivah",         ["Amrit","Shubh","Labh"], ["Jupiter","Venus","Moon"]),
    ("Engagement / Sagai",       ["Amrit","Shubh"],         ["Jupiter","Venus"]),
    ("Naamkaran (naming)",       ["Amrit","Shubh"],         ["Moon","Mercury","Jupiter"]),
    ("Annaprashana (1st food)",  ["Amrit","Shubh"],         ["Jupiter","Moon"]),
    ("Mundan (1st haircut)",     ["Amrit","Shubh"],         ["Mercury","Jupiter"]),
    ("Upanayana / Janeu",        ["Amrit","Shubh"],         ["Jupiter","Mercury"]),
    ("Griha Pravesh (housewarming)",["Amrit","Shubh","Labh"],["Jupiter","Venus"]),
    ("Bhumi Pujan (foundation)", ["Amrit","Shubh"],         ["Jupiter","Saturn"]),
    ("Vahana Kreya (vehicle buy)",["Labh","Amrit"],         ["Venus","Mercury","Jupiter"]),
    ("Property purchase",        ["Labh","Amrit","Shubh"],  ["Jupiter","Saturn","Venus"]),
    ("Business start / Aarambh", ["Labh","Amrit","Shubh"],  ["Mercury","Jupiter","Venus"]),
    ("Loan repayment",           ["Labh"],                  ["Mercury","Saturn"]),
    ("Loan taking (avoid if can)",["Char"],                 ["Mercury"]),
    ("Investment / Stock",       ["Labh","Amrit"],          ["Mercury","Jupiter"]),
    ("Job interview",            ["Amrit","Shubh","Labh"],  ["Sun","Mercury","Jupiter"]),
    ("Resignation / Job leave",  ["Char"],                  ["Saturn"]),
    ("Travel — domestic",        ["Char","Labh","Amrit"],   ["Moon","Mercury"]),
    ("Travel — foreign",         ["Char","Labh"],           ["Moon","Mercury","Rahu"]),
    ("Surgery — elective",       ["Amrit","Shubh"],         ["Mars","Saturn"]),
    ("Surgery — emergency",      ["any"],                   ["Mars"]),
    ("Medicine / Treatment start",["Amrit","Shubh"],        ["Jupiter","Sun"]),
    ("Court case filing",        ["Labh","Shubh"],          ["Mercury","Jupiter","Mars"]),
    ("Contract signing",         ["Labh","Amrit","Shubh"],  ["Mercury","Jupiter"]),
    ("Settlement / Compromise",  ["Amrit","Shubh"],         ["Jupiter","Venus"]),
    ("Diksha / Initiation",      ["Amrit","Shubh"],         ["Jupiter"]),
    ("Mantra Sadhana start",     ["Amrit","Brahma"],        ["Jupiter"]),
    ("Yagna / Homa",             ["Amrit","Shubh"],         ["Jupiter","Sun"]),
    ("Charity / Daan",           ["Amrit","Shubh"],         ["Jupiter","Moon"]),
    ("New clothes (1st wear)",   ["Amrit","Shubh"],         ["Venus","Moon"]),
    ("Jewellery purchase",       ["Labh","Amrit"],          ["Venus","Jupiter"]),
    ("Vidyarambha (study start)",["Amrit","Shubh"],         ["Mercury","Jupiter"]),
    ("Music / Art performance",  ["Shubh","Amrit"],         ["Venus"]),
    ("Cremation / Antyeshti",    ["any"],                   ["Saturn"]),
    ("Funeral rites / Pind",     ["any"],                   ["Saturn","Sun"]),
    ("Tonsure / Vapana",         ["Shubh","Amrit"],         ["Mercury"]),
]


def _hms(td: timedelta) -> str:
    s = int(td.total_seconds())
    h, m = divmod(s // 60, 60)
    return f"{h:02d}:{m:02d}"


def compute_phase_q(target_date: date | None = None) -> dict[str, Any]:
    if target_date is None: target_date = date.today()
    sunrise = datetime.combine(target_date, datetime.min.time()).replace(hour=6)
    sunset  = sunrise + timedelta(hours=12)
    night_end = sunrise + timedelta(hours=24)
    day_lord = PY_WD_TO_LORD[target_date.weekday()]

    day_slot_len  = timedelta(hours=12) / 8     # 1.5 hr each
    night_slot_len= timedelta(hours=12) / 8

    # Q1 — Choghadiya
    chog_day_names = CHOG_DAY.get(day_lord, ["?"]*8)
    chog_night_names = CHOG_NIGHT.get(day_lord, ["?"]*8)
    chog_rows = []
    for i in range(8):
        s = sunrise + i*day_slot_len
        e = s + day_slot_len
        chog_rows.append({"phase":"DAY","slot":i+1,"name":chog_day_names[i],
                            "start":_hms(s-sunrise.replace(hour=0,minute=0)),
                            "end":_hms(e-sunrise.replace(hour=0,minute=0)),
                            "quality":CHOG_QUALITY.get(chog_day_names[i],"?")})
    for i in range(8):
        s = sunset + i*night_slot_len
        e = s + night_slot_len
        chog_rows.append({"phase":"NIGHT","slot":i+1,"name":chog_night_names[i],
                            "start":_hms(s-sunrise.replace(hour=0,minute=0)),
                            "end":_hms(e-sunrise.replace(hour=0,minute=0)),
                            "quality":CHOG_QUALITY.get(chog_night_names[i],"?")})

    # Q2 — Hora (24 hrs starting from sunrise, each = 60 min, lord cycles)
    start_idx = HORA_CYCLE.index(day_lord)
    hora_rows = []
    for i in range(24):
        lord = HORA_CYCLE[(start_idx + i) % 7]
        s = sunrise + timedelta(hours=i)
        e = s + timedelta(hours=1)
        hora_rows.append({"hour":i+1,"lord":lord,
                           "start":_hms(s-sunrise.replace(hour=0,minute=0)),
                           "end":_hms(e-sunrise.replace(hour=0,minute=0)),
                           "best_for":HORA_QUALITY.get(lord,"?")})

    # Q3 — Rahu / Yama / Gulika kaal slots
    rahu_i = RAHU_SLOT[day_lord]; yama_i = YAMA_SLOT[day_lord]; guli_i = GULI_SLOT[day_lord]
    def slot_window(i: int) -> tuple[str,str]:
        s = sunrise + (i-1)*day_slot_len
        e = s + day_slot_len
        return _hms(s-sunrise.replace(hour=0,minute=0)), _hms(e-sunrise.replace(hour=0,minute=0))
    r_s, r_e = slot_window(rahu_i)
    y_s, y_e = slot_window(yama_i)
    g_s, g_e = slot_window(guli_i)

    # Q4 — Abhijit (8th muhurta of day = exactly midday ±24min) + Brahma (96-48 min before sunrise)
    midday = sunrise + timedelta(hours=6)
    abhijit_s = midday - timedelta(minutes=24)
    abhijit_e = midday + timedelta(minutes=24)
    brahma_s  = sunrise - timedelta(minutes=96)
    brahma_e  = sunrise - timedelta(minutes=48)
    abhijit_valid = (target_date.weekday() != 1)   # Tue (Mars day) — Abhijit invalid

    # Q5 — Event muhurta recommendations (today)
    today_qualities = set()
    for c in chog_rows:
        if c["phase"] == "DAY": today_qualities.add(c["name"])
    today_lords = {h["lord"] for h in hora_rows[:12]}
    event_recs = []
    for ev_name, good_chog, good_hora in EVENT_MUHURTAS:
        chog_ok = "any" in good_chog or any(c in today_qualities for c in good_chog)
        hora_ok = any(h in today_lords for h in good_hora)
        verdict = "✅ GOOD windows today" if (chog_ok and hora_ok) else \
                  "△ partial — pick best window" if (chog_ok or hora_ok) else \
                  "✗ unfavourable — postpone"
        event_recs.append({"event":ev_name,"good_choghadiya":good_chog,
                            "good_hora_lords":good_hora,"verdict":verdict})

    return {
        "available": True,
        "date": target_date.isoformat(),
        "weekday": target_date.strftime("%A"),
        "day_lord": day_lord,
        "sunrise_hhmm":"06:00", "sunset_hhmm":"18:00",
        "q1_choghadiya": chog_rows,
        "q2_hora": hora_rows,
        "q3_kaal":{
            "rahu_kaal":{"start":r_s,"end":r_e,"meaning":"AVOID — most inauspicious daily window"},
            "yamaganda":{"start":y_s,"end":y_e,"meaning":"AVOID — death-related delays"},
            "gulika_kaal":{"start":g_s,"end":g_e,"meaning":"AVOID — son-of-Saturn negative window"},
        },
        "q4_special":{
            "abhijit_muhurta":{"start":_hms(abhijit_s-sunrise.replace(hour=0,minute=0)),
                                 "end":_hms(abhijit_e-sunrise.replace(hour=0,minute=0)),
                                 "valid":abhijit_valid,
                                 "note":"Universal good muhurta — except Tuesdays"},
            "brahma_muhurta":{"start":_hms(brahma_s-sunrise.replace(hour=0,minute=0)),
                                "end":_hms(brahma_e-sunrise.replace(hour=0,minute=0)),
                                "note":"96-48 min before sunrise — best for sadhana, study"},
        },
        "q5_event_muhurtas": event_recs,
    }


def format_phase_q(r: dict) -> str:
    if not r or not r.get("available"):
        return "▸ PHASE Q MUHURTA: ❌ unavailable"
    L = [f"▸ PHASE Q MUHURTA FULL (Sprint-42) — {r['date']} ({r['weekday']}, day-lord={r['day_lord']})",
         f"  (Heuristic sunrise=06:00, sunset=18:00 — no lat/lon)"]
    L.append("  Q1 CHOGHADIYA (16 windows = 8 day + 8 night, each ~1.5hr):")
    for c in r["q1_choghadiya"]:
        L.append(f"      {c['phase']:<5} #{c['slot']}  {c['start']}-{c['end']}  "
                 f"{c['name']:<7} → {c['quality']}")
    L.append("  Q2 HORA (24 hours, planet-lord per hour):")
    for h in r["q2_hora"]:
        L.append(f"      Hr{h['hour']:>2}  {h['start']}-{h['end']}  "
                 f"{h['lord']:<8} → {h['best_for']}")
    k = r["q3_kaal"]
    L.append("  Q3 INAUSPICIOUS KAAL WINDOWS (avoid for shubh karma):")
    L.append(f"      ⚠ Rahu Kaal      {k['rahu_kaal']['start']}-{k['rahu_kaal']['end']} — {k['rahu_kaal']['meaning']}")
    L.append(f"      ⚠ Yamaganda Kaal {k['yamaganda']['start']}-{k['yamaganda']['end']} — {k['yamaganda']['meaning']}")
    L.append(f"      ⚠ Gulika Kaal    {k['gulika_kaal']['start']}-{k['gulika_kaal']['end']} — {k['gulika_kaal']['meaning']}")
    sp = r["q4_special"]
    a = sp["abhijit_muhurta"]; b = sp["brahma_muhurta"]
    L.append(f"  Q4 SPECIAL MUHURTAS:")
    L.append(f"      ✦ Abhijit Muhurta  {a['start']}-{a['end']}  "
             f"({'VALID' if a['valid'] else 'INVALID — Tuesday'})  — {a['note']}")
    L.append(f"      ✦ Brahma Muhurta   {b['start']}-{b['end']}  — {b['note']}")
    L.append(f"  Q5 EVENT MUHURTAS ({len(r['q5_event_muhurtas'])} events):")
    for e in r["q5_event_muhurtas"]:
        L.append(f"      • {e['event']:<32} {e['verdict']}  "
                 f"(needs Chog: {'/'.join(e['good_choghadiya'])} + Hora: {'/'.join(e['good_hora_lords'])})")
    return "\n".join(L)
