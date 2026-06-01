import sys
sys.path.insert(0, ".")
from divisional_charts import compute_d9

SIGNS_SHORT = ["Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya", "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen"]
EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
idx = {s: i for i, s in enumerate(SIGNS_SHORT)}
data = [
    ("Sun", "Tula", 11.5),
    ("Moon", "Mithun", 12.1),
    ("Mars", "Dhanu", 15.0),
    ("Mercury", "Vrishchik", 5.1),
    ("Jupiter", "Mesh", 5.3),
    ("Venus", "Simha", 25.0),
    ("Saturn", "Mesh", 20.5),
    ("Rahu", "Kark", 14.6),
    ("Ketu", "Makar", 14.6),
]
lons = {n: idx[s] * 30 + d for n, s, d in data}
asc = idx["Dhanu"] * 30 + 15.0
d9 = compute_d9([{"name": n, "longitude": lon} for n, lon in lons.items()], asc)
lagna = d9["_lagna"]["sign_idx"]
print("D9 lagna", d9["_lagna"]["sign"])
for n, _, _ in data:
    info = d9[n]
    h = ((info["sign_idx"] - lagna) % 12) + 1
    print(f"{n}: {info['sign']} H{h}")

print("simple:")
for n, lon in lons.items():
    si = int(lon * 9 / 30) % 12
    h = ((si - lagna) % 12) + 1
    print(f"{n}: {EN[si]} H{h}")
