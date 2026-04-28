"""
Sprint 37 / Phase L — Special Lagnas gap fill.
Adds 6 time-based / formula-based lagnas not in special_lagnas.py:
  L1 Bhava Lagna, Hora Lagna, Ghati Lagna
  L2 Vighati Lagna, Pranapada Lagna
  L4 Varnada Lagna
(L3 Indu Lagna ✅ already in special_lagnas.py)

Time-based lagnas need IshtaKaal = time elapsed from local sunrise.
Without lat/lon we approximate sunrise = 06:00 local on birth date.
1 ghati = 24 min, 1 vighati = 24 sec, 1 day = 60 ghatis.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORD = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
             "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]


def _parse_dob(dob: str, btime: str = "12:00") -> Optional[datetime]:
    for fmt in ("%Y-%m-%d","%d-%m-%Y","%d %b %Y","%d %B %Y"):
        try: dt = datetime.strptime(dob, fmt); break
        except Exception: continue
    else: return None
    try:
        if isinstance(btime, str) and ":" in btime:
            hh, mm = btime.split(":")[:2]
            dt = dt.replace(hour=int(hh), minute=int(mm))
    except Exception: pass
    return dt


def _ishtakaal_ghatis(birth_dt: datetime) -> float:
    """Approximate IshtaKaal in ghatis (1 ghati = 24 min) from local sunrise.
       Heuristic: sunrise = 06:00 local on birth date. If birth before
       sunrise, count from previous sunrise (24 hr earlier)."""
    sunrise = birth_dt.replace(hour=6, minute=0, second=0, microsecond=0)
    if birth_dt < sunrise:
        sunrise -= timedelta(days=1)
    delta_min = (birth_dt - sunrise).total_seconds() / 60.0
    return delta_min / 24.0  # ghatis


def _sun_lon(planets: list[dict]) -> Optional[float]:
    for p in planets:
        if isinstance(p, dict) and p.get("name") == "Sun":
            l = p.get("longitude")
            if isinstance(l, (int, float)): return float(l) % 360
    return None


# ─── L1 Bhava / Hora / Ghati Lagnas ───────────────────────────────────
def bhava_lagna(sun_lon: float, ishta_g: float) -> dict[str, Any]:
    """Bhava Lagna advances 30° per 5 ghatis (= 2 hrs)."""
    bl = (sun_lon + (ishta_g / 5.0) * 30.0) % 360
    si = int(bl // 30)
    return {"longitude": round(bl, 2), "sign": SIGN_NAMES[si],
            "deg_in_sign": round(bl % 30, 2), "lord": SIGN_LORD[si],
            "indicates": "General well-being, body, life-direction"}


def hora_lagna(sun_lon: float, ishta_g: float) -> dict[str, Any]:
    """Hora Lagna advances 30° per 2.5 ghatis (= 1 hr)."""
    hl = (sun_lon + (ishta_g / 2.5) * 30.0) % 360
    si = int(hl // 30)
    return {"longitude": round(hl, 2), "sign": SIGN_NAMES[si],
            "deg_in_sign": round(hl % 30, 2), "lord": SIGN_LORD[si],
            "indicates": "Wealth flow, prosperity rhythm"}


def ghati_lagna(sun_lon: float, ishta_g: float) -> dict[str, Any]:
    """Ghati Lagna advances 30° per 1 ghati (24 min) — ~5 deg/min."""
    gl = (sun_lon + ishta_g * 30.0) % 360
    si = int(gl // 30)
    return {"longitude": round(gl, 2), "sign": SIGN_NAMES[si],
            "deg_in_sign": round(gl % 30, 2), "lord": SIGN_LORD[si],
            "indicates": "Power, position, status changes"}


# ─── L2 Vighati / Pranapada Lagnas ────────────────────────────────────
def vighati_lagna(sun_lon: float, ishta_g: float) -> dict[str, Any]:
    """Vighati Lagna — used in Jaimini for sub-trends; advances 30° per
       1 vighati of ghati (very fast). We use: 30° per 0.0167 ghati (1 vighati = 1/60 ghati).
       Practical formula: Vighati Lagna = Sun + (ghatis × 60°) mod 360 (one classical variant)."""
    vl = (sun_lon + (ishta_g * 60.0)) % 360
    si = int(vl // 30)
    return {"longitude": round(vl, 2), "sign": SIGN_NAMES[si],
            "deg_in_sign": round(vl % 30, 2), "lord": SIGN_LORD[si],
            "indicates": "Sub-cycle micro-events, fine-tuned timing"}


def pranapada_lagna(sun_lon: float, ishta_g: float) -> dict[str, Any]:
    """Pranapada — vital point. Classical formula:
       Pranapada (in vighatis) = ishtakaal in vighatis ÷ 15 ⇒ remainder used.
       Each Pranapada = 6 navamshas (= 1.5 sign each = 60° / 4 = 15°).
       Simplified BPHS-aligned formula: PP_lon = Sun_lon + (vighatis_total mod 12)*30° + (offset)."""
    vighatis = ishta_g * 60.0
    # PP starts depend on movable/fixed/dual sign of Sun
    sun_si = int(sun_lon // 30)
    if sun_si % 3 == 0:        # movable signs (Ari, Can, Lib, Cap)
        offset = 0.0
    elif sun_si % 3 == 1:      # fixed (Tau, Leo, Sco, Aqu)
        offset = 240.0         # +8 signs
    else:                       # dual (Gem, Vir, Sag, Pis)
        offset = 120.0         # +4 signs
    pp = (sun_lon + offset + (vighatis % 12) * 30.0) % 360
    si = int(pp // 30)
    return {"longitude": round(pp, 2), "sign": SIGN_NAMES[si],
            "deg_in_sign": round(pp % 30, 2), "lord": SIGN_LORD[si],
            "indicates": "Vital force / prana node — health & lifespan trigger point"}


# ─── L4 Varnada Lagna ─────────────────────────────────────────────────
def varnada_lagna(lagna_si: int, hora_lagna_si: int) -> dict[str, Any]:
    """Varnada Lagna (Jaimini) — caste/varna trend.
       Rule: count from Aries to Lagna if Lagna is odd sign,
             from Pisces to Lagna if Lagna is even sign — gives N1.
             Same procedure for Hora Lagna gives N2.
             If both same parity → Varnada Lagna = (N1 + N2)th sign from Aries.
             If different parity → (N1 - N2)th sign (mod 12), counted from Aries.
       Indicates: Varna (mode of life) & overall outer destiny."""
    def _count(si):
        if si % 2 == 0:    # odd sign (1,3,5...) – Aries=index 0 is odd house number 1
            return si + 1  # count from Aries
        else:
            return 12 - si  # count from Pisces
    n1 = _count(lagna_si)
    n2 = _count(hora_lagna_si)
    same_parity = (lagna_si % 2) == (hora_lagna_si % 2)
    if same_parity:
        v_pos = (n1 + n2) % 12 or 12
    else:
        v_pos = (n1 - n2) % 12 or 12
    v_si = (v_pos - 1) % 12
    return {"sign": SIGN_NAMES[v_si], "lord": SIGN_LORD[v_si],
            "varna_count": v_pos, "same_parity": same_parity,
            "indicates": "Varna / mode-of-life, outer destiny path"}


# ─── Master orchestrator ──────────────────────────────────────────────
def compute_lagnas_phase_l(kundli: dict, birth: dict) -> dict[str, Any]:
    # Sprint-26 Fix-K: defensive None-handling. Father/spouse charts pass
    # birth=None which previously crashed via 'NoneType.get' on the
    # birth.get("dob")/birth.get("time") lines. We treat missing birth as
    # an empty dict — those fields fall back to kundli.get("dob") /
    # kundli.get("time") / "12:00" which the rest of the function
    # already handles gracefully.
    birth = birth or {}
    planets = kundli.get("planets") or []
    sun_lon = _sun_lon(planets)
    if sun_lon is None:
        return {"available": False, "reason": "Sun longitude missing"}
    dob = birth.get("dob") or birth.get("date") or kundli.get("dob")
    btime = birth.get("time") or kundli.get("time") or "12:00"
    if not isinstance(dob, str):
        return {"available": False, "reason": "dob missing"}
    birth_dt = _parse_dob(dob, btime)
    if not birth_dt:
        return {"available": False, "reason": "dob parse failed"}
    ishta = _ishtakaal_ghatis(birth_dt)
    lagna_sign = kundli.get("ascendant") or kundli.get("lagna")
    lagna_si = (SIGN_NAMES.index(lagna_sign)
                if isinstance(lagna_sign, str) and lagna_sign in SIGN_NAMES
                else 0)
    bl = bhava_lagna(sun_lon, ishta)
    hl = hora_lagna(sun_lon, ishta)
    gl = ghati_lagna(sun_lon, ishta)
    vl = vighati_lagna(sun_lon, ishta)
    pp = pranapada_lagna(sun_lon, ishta)
    hl_si = SIGN_NAMES.index(hl["sign"])
    var = varnada_lagna(lagna_si, hl_si)
    return {
        "available": True,
        "ishtakaal_ghatis": round(ishta, 2),
        "ishtakaal_note": "approx — sunrise=06:00 local (no lat/lon)",
        "bhava_lagna":     bl,
        "hora_lagna":      hl,
        "ghati_lagna":     gl,
        "vighati_lagna":   vl,
        "pranapada_lagna": pp,
        "varnada_lagna":   var,
    }


def format_lagnas_phase_l_summary(r: dict) -> str:
    if not r or not r.get("available"):
        return f"▸ PHASE L SPECIAL LAGNAS: ❌ {r.get('reason','n/a') if r else 'n/a'}"
    L = ["▸ PHASE L SPECIAL LAGNAS (Sprint-37) — 6 time/formula-based lagnas",
         f"  IshtaKaal: {r['ishtakaal_ghatis']} ghatis  ({r['ishtakaal_note']})"]
    rows = [
        ("L1 Bhava Lagna",     r["bhava_lagna"]),
        ("L1 Hora Lagna",      r["hora_lagna"]),
        ("L1 Ghati Lagna",     r["ghati_lagna"]),
        ("L2 Vighati Lagna",   r["vighati_lagna"]),
        ("L2 Pranapada Lagna", r["pranapada_lagna"]),
    ]
    for label, d in rows:
        L.append(f"    {label:<22} {d['sign']:<11} {d['deg_in_sign']:5.2f}° "
                 f"(lord {d['lord']:<8}) — {d['indicates']}")
    v = r["varnada_lagna"]
    parity = "same" if v["same_parity"] else "diff"
    L.append(f"    {'L4 Varnada Lagna':<22} {v['sign']:<11} (lord {v['lord']:<8}) — count {v['varna_count']} ({parity} parity) — {v['indicates']}")
    return "\n".join(L)
