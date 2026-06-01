"""Step 5 marriage dasha windows — user 29 Oct 1999, next 5 years."""
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from kundli_engine import calculate_kundli
from event_timing.marriage.marriage_spec_pipeline import run_user_spec_pipeline
from event_timing.marriage.marriage_engine_v2 import (
    _flatten_dasha_chain,
    _step5_dasha_activation,
    _step5_5_future_cascade,
    _DASHA_SCORE_MD,
    _DASHA_SCORE_AD,
    _DASHA_SCORE_PD,
)

BIRTH = {
    "day": 29, "month": 10, "year": 1999,
    "hour": 6, "minute": 30, "ampm": "AM",
    "lat": 20.2961, "lon": 85.8245, "tz": 5.5,
    "name": "User",
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
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

spec = run_user_spec_pipeline(kundli, kp, 8)
target = set(spec.get("target_lords") or [])
d9_7l = spec.get("d9_seventh_lord")

now = datetime(2026, 5, 24)  # user date from context
horizon = now + timedelta(days=365 * 5)

chain = _flatten_dasha_chain(kundli)
act = _step5_dasha_activation(chain, target, now, d9_7l=d9_7l)
cands = _step5_5_future_cascade(chain, target, now, act.get("current"))

lines = []
lines.append(f"Target lords (Step 1-5): {sorted(target)}")
lines.append(f"Ranked: {[(r['name'], r['score']) for r in (spec.get('ranked_significators') or [])[:6]]}")
lines.append(f"\nNOW ({now.date()}): MD={act['current']['md']} AD={act['current']['ad']} PD={act['current']['pd']} score={act['active_score']}")
lines.append("\n=== ALL PD chunks (next 5y) with marriage hit ===\n")

for c in chain:
    if c["end"] <= now or c["start"] > horizon:
        continue
    hits = []
    sc = 0
    if c["md"] in target:
        sc += _DASHA_SCORE_MD
        hits.append(f"MD-{c['md']}(+{_DASHA_SCORE_MD})")
    if c["ad"] in target:
        sc += _DASHA_SCORE_AD
        hits.append(f"AD-{c['ad']}(+{_DASHA_SCORE_AD})")
    if c["pd"] in target:
        sc += _DASHA_SCORE_PD
        hits.append(f"PD-{c['pd']}(+{_DASHA_SCORE_PD})")
    ad_pd = (sc if c["ad"] in target else 0) + (sc if c["pd"] in target else 0)
    ad_pd = (_DASHA_SCORE_AD if c["ad"] in target else 0) + (_DASHA_SCORE_PD if c["pd"] in target else 0)
    if ad_pd < 5:
        continue
    lines.append(
        f"{c['start'].date()} → {c['end'].date()} | "
        f"{c['md']}-{c['ad']}-{c['pd']} | score≈{ad_pd + (_DASHA_SCORE_MD if c['md'] in target else 0)} | {', '.join(hits)}"
    )

lines.append("\n=== ENGINE Step 5.5 candidates (sorted) ===\n")
for c in cands[:25]:
    if c["start"] > horizon:
        continue
    lines.append(
        f"{c['start'].date()} → {c['end'].date()} | "
        f"{c['md']}-{c['ad']}-{c['pd']} | score={c['score']:.1f} | "
        f"pd_only={c.get('pd_only_activation')}"
    )

# Verify user-provided AD boundaries
lines.append("\n=== Jupiter MD — Antar dashas (computed) ===\n")
for md in kundli.get("dashas") or []:
    if md.get("planet") != "Jupiter":
        continue
    for ad in md.get("subDashas") or []:
        lines.append(f"  AD {ad['planet']}: {ad['startDate'][:10]} → {ad['endDate'][:10]}")
        if ad["planet"] == "Rahu":
            lines.append("    PD list:")
            for pd in ad.get("subDashas") or []:
                lines.append(f"      {pd['planet']}: {pd['startDate'][:10]} → {pd['endDate'][:10]}")

text = "\n".join(lines)
open("_dasha_step5_out.txt", "w", encoding="utf-8").write(text)
print(text)
