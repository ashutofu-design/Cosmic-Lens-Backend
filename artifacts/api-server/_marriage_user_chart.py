"""Marriage engine Steps 1-5 on user-provided D1 (+ computed BPHS D9)."""
import json
import sys

sys.path.insert(0, ".")

from event_timing.marriage.marriage_spec_pipeline import run_user_spec_pipeline

SIGNS_SHORT = [
    "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
    "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
]
EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
idx = {s: i for i, s in enumerate(SIGNS_SHORT)}

# User D1 (Dhanu lagna)
rows = [
    ("Sun", "Tula", 11.5, 11, False),
    ("Moon", "Mithun", 12.1, 7, False),
    ("Mars", "Dhanu", 15.0, 1, False),
    ("Mercury", "Vrishchik", 5.1, 12, False),
    ("Jupiter", "Mesh", 5.3, 5, True),
    ("Venus", "Simha", 25.0, 9, False),
    ("Saturn", "Mesh", 20.5, 5, True),
    ("Rahu", "Kark", 14.6, 8, True),
    ("Ketu", "Makar", 14.6, 2, True),
]

planets = []
for name, sign, deg, house, retro in rows:
    si = idx[sign]
    lon = si * 30 + deg
    planets.append({
        "name": name,
        "sign": EN[si],
        "signIndex": si,
        "house": house,
        "longitude": lon,
        "retrograde": retro,
    })

asc_lon = idx["Dhanu"] * 30 + 15.0
lagna_si = 8

kundli = {
    "ascendant": "Sagittarius",
    "ascendantDeg": asc_lon,
    "planets": planets,
}

result = run_user_spec_pipeline(kundli, kp={}, lagna_si=lagna_si)

out = {
    "d1_7L": result["d1_seventh_lord"],
    "d9_7L": result["d9_seventh_lord"],
    "natal_promise": result["natal_promise"],
    "reasoning": result["reasoning_summary"],
    "step1_d1_pool": {
        k: {"points": v["points"], "links": v["links"], "house": v.get("house")}
        for k, v in sorted(result["d1_pool"].items(), key=lambda x: -x[1]["points"])
    },
    "step2_d9_pool": {
        k: {"points": v["points"], "links": v["links"], "house": v.get("house")}
        for k, v in sorted(result["d9_pool"].items(), key=lambda x: -x[1]["points"])
    },
    "step3_merged_top": [
        {
            "planet": r["name"],
            "total": r["score"],
            "d1": r["d1_points"],
            "d9": r["d9_points"],
            "both_bonus": r["both_bonus"],
            "links": r["links"][:6],
        }
        for r in result["ranked_significators"][:9]
    ],
    "target_lords": sorted(result["target_lords"]),
}

with open("_marriage_user_out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print(json.dumps(out, indent=2, ensure_ascii=False))
