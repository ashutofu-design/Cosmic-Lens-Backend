"""One-off: Step 4 scores for user chart (29 Oct 1999, Bhubaneswar, Dhanu lagna)."""
import json
import sys

sys.path.insert(0, ".")

from event_timing.marriage.marriage_spec_pipeline import run_user_spec_pipeline

# Dhanu lagna — conversation chart (whole-sign houses as stored in engine)
KUNDLI = {
    "ascendant": "Sagittarius",
    "planets": [
        {"name": "Sun", "sign": "Libra", "house": 11},
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Mars", "sign": "Sagittarius", "house": 1},
        {"name": "Mercury", "sign": "Scorpio", "house": 12},
        {"name": "Jupiter", "sign": "Aries", "house": 5, "retrograde": True},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Saturn", "sign": "Aries", "house": 5, "retrograde": True},
        {"name": "Rahu", "sign": "Cancer", "house": 8, "retrograde": True},
        {"name": "Ketu", "sign": "Capricorn", "house": 2, "retrograde": True},
    ],
}

BIRTH = {
    "day": 29,
    "month": 10,
    "year": 1999,
    "hour": 6,
    "minute": 30,
    "ampm": "AM",
    "lat": 20.2961,
    "lon": 85.8245,
    "tz": 5.5,
}

try:
    from kp_engine import calculate_kp

    KP = calculate_kp(BIRTH)
except Exception as e:
    KP = {}
    print("KP compute failed:", e, file=sys.stderr)

LAGNA_SI = 8  # Sagittarius

out = run_user_spec_pipeline(KUNDLI, KP, LAGNA_SI)

print("=== STEP 3 (natal merge) ===")
for p, m in sorted(
    (out.get("merged") or {}).items(),
    key=lambda x: -(x[1].get("natal_points") or 0),
):
    print(
        f"  {p}: natal={m.get('natal_points')} "
        f"(d1={m.get('d1_points')}, d9={m.get('d9_points')}, both+{m.get('both_bonus', 0)})"
    )

print("\n=== STEP 4 (KP Sub-Lord) ===")
print("CSL:", out.get("kp_summary", {}).get("csl_planet"), out.get("kp_summary", {}).get("csl_verdict"))
print("KP valid (SB confirms/partial):", out.get("kp_summary", {}).get("valid_planets"))

for p in sorted((out.get("merged") or {}).keys()):
    kd = (out.get("kp_details") or {}).get(p) or {}
    print(
        f"  {p}: verdict={kd.get('verdict')} kp_valid={kd.get('kp_valid')} "
        f"kp_pts={kd.get('kp_points')} SB={kd.get('houses_sb')} "
        f"promise={kd.get('domain_hits')} neg={kd.get('negation_hits')}"
    )

print("\n=== STEP 5 FINAL SCORES ===")
for r in out.get("ranked_significators") or []:
    print(
        f"  {r['name']}: TOTAL={r['score']} "
        f"(natal={r.get('d1_points', 0)+r.get('d9_points', 0)+r.get('both_bonus', 0)} "
        f"→ d1={r.get('d1_points')} d9={r.get('d9_points')} both+{r.get('both_bonus', 0)}, "
        f"KP+{r.get('kp_points')}) kp_note={r.get('kp_note', '')[:60]}"
    )

with open("_step4_result.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "merged": out.get("merged"),
            "kp_details": out.get("kp_details"),
            "kp_summary": out.get("kp_summary"),
            "ranked": out.get("ranked_significators"),
        },
        f,
        indent=2,
        default=str,
    )
print("\nWrote _step4_result.json")
