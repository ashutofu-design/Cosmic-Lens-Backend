"""Full marriage pipeline (Steps 0–8) — user chart 29 Oct 1999, Bhubaneswar."""
import json
import sys
from datetime import datetime

sys.path.insert(0, ".")

from kundli_engine import calculate_kundli
from event_timing.marriage import assess_marriage

BIRTH = {
    "day": 29, "month": 10, "year": 1999,
    "hour": 6, "minute": 30, "ampm": "AM",
    "lat": 20.2961, "lon": 85.8245, "tz": 5.5,
    "name": "User", "gender": "male",
}

planets = [
    {"name": "Sun", "sign": "Libra", "house": 11, "longitude": 185.5},
    {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 72.1},
    {"name": "Mars", "sign": "Sagittarius", "house": 1, "longitude": 255.0},
    {"name": "Mercury", "sign": "Scorpio", "house": 12, "longitude": 215.1},
    {"name": "Jupiter", "sign": "Aries", "house": 5, "longitude": 15.3},
    {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 145.0},
    {"name": "Saturn", "sign": "Aries", "house": 5, "longitude": 20.5},
    {"name": "Rahu", "sign": "Cancer", "house": 8, "longitude": 104.6},
    {"name": "Ketu", "sign": "Capricorn", "house": 2, "longitude": 284.6},
]

kundli = calculate_kundli({**BIRTH})
kundli["planets"] = planets
kundli["ascendant"] = "Sagittarius"

try:
    from kp_engine import calculate_kp
    kp = calculate_kp(BIRTH)
except Exception:
    kp = {}

intel = {"gender": "male"}
v = assess_marriage(kundli, intel, kp, BIRTH, question="shaadi kab hogi")

out = {
    "engine_version": v.get("engine_version"),
    "engine_arch": v.get("engine_arch"),
    "verdict": v.get("verdict"),
    "band": v.get("band"),
    "user_age": v.get("user_age"),
    "step0_tendency": v.get("step0_tendency"),
    "chart_late_marriage": v.get("chart_late_marriage"),
    "primary_window": v.get("primary_window"),
    "key_trigger": v.get("key_trigger"),
    "final_transit_support": v.get("final_transit_support"),
    "final_double_transit": v.get("final_double_transit"),
    "final_transit_detail": v.get("final_transit_detail"),
    "confluence_strength": v.get("confluence_strength"),
    "top_3_windows": v.get("top_3_windows"),
    "top_marriage_planets": (v.get("top_marriage_planets") or [])[:6],
    "step_factors": [f for f in (v.get("factors") or []) if f.startswith("STEP")],
}

print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
print("\n--- Full STEP factors ---")
for f in v.get("factors") or []:
    if "STEP" in f or "BCP" in f or "AGE" in f:
        print(f)
