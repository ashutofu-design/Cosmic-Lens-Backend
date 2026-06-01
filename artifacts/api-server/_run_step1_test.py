"""One-off: Step 1 dump for primary/golden kundli (P40 Rajalaxmi)."""
import json
import sys

sys.path.insert(0, ".")

from kundli_engine import calculate_kundli
from event_timing.marriage.kp_from_chart import resolve_kp
from event_timing.marriage.marriage_spec_pipeline import (
    _SIGN_IDX,
    _extract_division,
    _house_lord,
    run_user_spec_pipeline,
)

birth = {
    "name": "Rajalaxmi",
    "day": 26,
    "month": 11,
    "year": 1992,
    "hour": 7,
    "minute": 58,
    "ampm": "AM",
    "lat": 20.27,
    "lon": 85.84,
    "tz": 5.5,
    "gender": "F",
    "place": "Bhubaneswar",
}

kundli = calculate_kundli(birth)
asc = kundli.get("ascendant")
lagna_si = _SIGN_IDX.get(asc) if isinstance(asc, str) else None

out = {
    "birth": birth,
    "lagna": asc,
    "lagna_si": lagna_si,
    "d1_7th_lord": _house_lord(lagna_si, 7) if lagna_si is not None else None,
    "d1_2nd_lord": _house_lord(lagna_si, 2) if lagna_si is not None else None,
    "d1_11th_lord": _house_lord(lagna_si, 11) if lagna_si is not None else None,
    "planets_d1": [
        {
            "name": p.get("name"),
            "house": p.get("house"),
            "sign": p.get("sign"),
            "sign_idx": p.get("sign_idx"),
        }
        for p in (kundli.get("planets") or [])
        if isinstance(p, dict)
    ],
}

if lagna_si is not None:
    out["d1_pool"] = _extract_division(kundli.get("planets") or [], lagna_si, "D1")
    kp = resolve_kp(kundli, {}, birth)
    spec = run_user_spec_pipeline(kundli, kp, lagna_si)
    out["d9_7th_lord"] = spec.get("d9_seventh_lord")
    out["natal_promise"] = spec.get("natal_promise")
    out["reasoning_summary"] = spec.get("reasoning_summary")
    out["ranked_top6"] = (spec.get("ranked_significators") or [])[:6]

print(json.dumps(out, indent=2, ensure_ascii=False))
