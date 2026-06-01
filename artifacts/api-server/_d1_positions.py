"""Print D1 positions for confirmation before Step 1."""
import json
import sys

sys.path.insert(0, ".")
from kundli_engine import calculate_kundli

birth = {
    "name": "User",
    "day": 29,
    "month": 10,
    "year": 1999,
    "hour": 11,
    "minute": 30,
    "ampm": "AM",
    "lat": 20.27,
    "lon": 85.84,
    "tz": 5.5,
    "place": "Bhubaneswar",
}

k = calculate_kundli(birth)
rows = []
for p in k.get("planets") or []:
    if not isinstance(p, dict):
        continue
    rows.append({
        "graha": p.get("name"),
        "rashi": p.get("sign"),
        "ghar": p.get("house"),
        "degree": p.get("degree") or p.get("formatted"),
    })

out = {
    "birth": "29/10/1999 11:30 AM Bhubaneswar (lat 20.27, lon 85.84, IST +5.5)",
    "lagna": k.get("ascendant"),
    "lagna_degree": k.get("ascendantDeg") or k.get("ascendantLongitude"),
    "moon_sign_janma_rashi": next(
        (p.get("sign") for p in (k.get("planets") or [])
         if isinstance(p, dict) and p.get("name") == "Moon"),
        None,
    ),
    "planets_d1": rows,
}
with open("_d1_positions_out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print(json.dumps(out, indent=2, ensure_ascii=False))
