"""
Sprint 32 / Phase F — Per-Varga Full Depth (gap fill)
Adds 3 sub-systems missing from existing varga depth:
  F3 Varga-Dasha overlay   — current Vimshottari MD lord position in EACH varga
  F4 Per-varga yoga expand — add D2/D3/D7/D12/D16/D20/D27/D30 detection
  F5 Per-varga dosha       — Mangal/Kemadruma/Papakartari/Daridra/Grahan
                              detected in 16 vargas
F1 (varga aspects) + F2 (varga ashtakavarga) already in
`vedic.varga.varga_deep` + `vedic.varga.ashtaka_deep` (Sprints 12-15).
"""
from __future__ import annotations
from typing import Any, Optional

SIGN_NAMES = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
SIGN_LORDS = ["Mars","Venus","Mercury","Moon","Sun","Mercury",
              "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter"]
BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
NODES = {"Rahu", "Ketu"}

VARGAS_ALL = ["D1","D2","D3","D7","D9","D10","D12","D16",
              "D20","D24","D27","D30","D40","D45","D60"]
# F4 expansion vargas (beyond D1/D9/D10/D24/D60 already in varga_yogas.py)
VARGAS_F4_NEW = ["D2","D3","D7","D12","D16","D20","D27","D30"]


# ─── helpers ──────────────────────────────────────────────────────────
def _sign_idx(s: Any) -> Optional[int]:
    if isinstance(s, int) and 0 <= s < 12: return s
    if isinstance(s, str) and s in SIGN_NAMES: return SIGN_NAMES.index(s)
    return None


def _planet_sign_in_varga(varga_chart: dict, planet: str) -> Optional[int]:
    """Extract sign-idx of planet from a varga chart (handles multiple shapes)."""
    if not isinstance(varga_chart, dict): return None
    p = varga_chart.get(planet)
    if isinstance(p, dict):
        si = p.get("sign_idx")
        if isinstance(si, int): return si
        s = p.get("sign")
        return _sign_idx(s)
    # Some vargas store under "planets" list
    pls = varga_chart.get("planets")
    if isinstance(pls, list):
        for q in pls:
            if isinstance(q, dict) and q.get("name") == planet:
                return _sign_idx(q.get("sign"))
    return None


def _varga_lagna_idx(varga_chart: dict) -> Optional[int]:
    if not isinstance(varga_chart, dict): return None
    lg = varga_chart.get("_lagna") or varga_chart.get("lagna") or varga_chart.get("ascendant")
    if isinstance(lg, dict):
        si = lg.get("sign_idx")
        if isinstance(si, int): return si
        return _sign_idx(lg.get("sign"))
    return _sign_idx(lg)


def _house_from_lagna(planet_si: int, lagna_si: int) -> int:
    return ((planet_si - lagna_si) % 12) + 1


def _build_all_vargas(planets: list, lagna_lon: Optional[float]) -> dict[str, dict]:
    """Compute all 16 vargas using existing divisional_charts API."""
    try:
        from divisional_charts import (compute_d2, compute_d3, compute_d7,  # type: ignore
                                       compute_d9, compute_d10, compute_d12,
                                       compute_d16, compute_d20, compute_d24,
                                       compute_d27, compute_d30, compute_d40,
                                       compute_d45)
        try:
            from divisional_charts import compute_d60  # type: ignore
        except Exception:
            compute_d60 = None
    except Exception:
        return {}
    if not isinstance(lagna_lon, (int, float)):
        return {}
    out = {
        "D2":  compute_d2(planets, lagna_lon),
        "D3":  compute_d3(planets, lagna_lon),
        "D7":  compute_d7(planets, lagna_lon),
        "D9":  compute_d9(planets, lagna_lon),
        "D10": compute_d10(planets, lagna_lon),
        "D12": compute_d12(planets, lagna_lon),
        "D16": compute_d16(planets, lagna_lon),
        "D20": compute_d20(planets, lagna_lon),
        "D24": compute_d24(planets, lagna_lon),
        "D27": compute_d27(planets, lagna_lon),
        "D30": compute_d30(planets, lagna_lon),
        "D40": compute_d40(planets, lagna_lon),
        "D45": compute_d45(planets, lagna_lon),
    }
    if compute_d60:
        try: out["D60"] = compute_d60(planets, lagna_lon)
        except Exception: pass
    return out


# ─── F3: Varga-Dasha overlay ─────────────────────────────────────────
def compute_varga_dasha_overlay(vargas: dict[str, dict],
                                 current_md: str,
                                 current_ad: str = "") -> dict[str, Any]:
    """For each varga, locate the current Vimshottari MD lord (and AD lord)
       and report which sign + house from varga-lagna they occupy.
       This identifies WHERE the current dasha events will manifest in each
       life domain (D9=marriage, D10=career, D7=children, etc.)."""
    if not vargas or not current_md:
        return {"available": False, "reason": "missing vargas or current MD"}
    DOMAIN = {"D1":"Self","D2":"Wealth","D3":"Siblings","D7":"Children",
              "D9":"Marriage","D10":"Career","D12":"Parents","D16":"Vehicles",
              "D20":"Spirituality","D24":"Education","D27":"Strengths",
              "D30":"Misfortunes","D40":"Maternal","D45":"Paternal","D60":"Past-life"}
    rows = []
    for label, ch in vargas.items():
        if not ch: continue
        lg = _varga_lagna_idx(ch)
        if lg is None: continue
        md_si = _planet_sign_in_varga(ch, current_md)
        if md_si is None: continue
        md_h = _house_from_lagna(md_si, lg)
        row = {"varga": label, "domain": DOMAIN.get(label, "—"),
               "md_lord": current_md,
               "md_sign": SIGN_NAMES[md_si], "md_house": md_h}
        if current_ad and current_ad != current_md:
            ad_si = _planet_sign_in_varga(ch, current_ad)
            if ad_si is not None:
                row["ad_lord"] = current_ad
                row["ad_sign"] = SIGN_NAMES[ad_si]
                row["ad_house"] = _house_from_lagna(ad_si, lg)
        rows.append(row)
    return {"available": True, "current_md": current_md,
            "current_ad": current_ad, "rows": rows}


# ─── F4: Per-varga yoga expansion ────────────────────────────────────
def detect_varga_yoga_expand(vargas: dict[str, dict]) -> dict[str, Any]:
    """Detect classical yogas in D2/D3/D7/D12/D16/D20/D27/D30 (beyond
       D1/D9/D10/D24/D60 already in varga_yogas.py).
       Yogas detected per-varga: Pancha-Mahapurusha, Adhi-Yoga, Sunaphaa,
       Anaphaa, Durdhura, Kemadruma, Lagnadhi."""
    if not vargas: return {}
    KENDRA = {1, 4, 7, 10}
    OWN_EX = {"Mars":{0,7}, "Venus":{1,6}, "Mercury":{2,5},
              "Moon":{3}, "Sun":{4}, "Jupiter":{8,11}, "Saturn":{9,10}}
    PMP_NAME = {"Mars":"Ruchaka","Mercury":"Bhadra","Jupiter":"Hamsa",
                "Venus":"Malavya","Saturn":"Sasa"}
    out_by_varga: dict[str, list[dict]] = {}
    for label in VARGAS_F4_NEW:
        ch = vargas.get(label)
        if not ch: continue
        lg = _varga_lagna_idx(ch)
        if lg is None: continue
        yogas = []
        moon_si = _planet_sign_in_varga(ch, "Moon")
        # Pancha-Mahapurusha
        for pl, name in PMP_NAME.items():
            psi = _planet_sign_in_varga(ch, pl)
            if psi is None: continue
            h = _house_from_lagna(psi, lg)
            if h in KENDRA and psi in OWN_EX.get(pl, set()):
                yogas.append({"name": f"{name} Mahapurusha", "planet": pl,
                              "house": h, "sign": SIGN_NAMES[psi]})
        # Sunaphaa/Anaphaa/Durdhura/Kemadruma (Moon-based, exclude Sun + nodes)
        if moon_si is not None:
            second = (moon_si + 1) % 12
            twelfth = (moon_si - 1) % 12
            in_2nd, in_12th = [], []
            for p in ("Mars","Mercury","Jupiter","Venus","Saturn"):
                psi = _planet_sign_in_varga(ch, p)
                if psi == second: in_2nd.append(p)
                if psi == twelfth: in_12th.append(p)
            if in_2nd and not in_12th:
                yogas.append({"name": "Sunaphaa", "details": f"planets in 2nd from Moon: {in_2nd}"})
            elif in_12th and not in_2nd:
                yogas.append({"name": "Anaphaa", "details": f"planets in 12th from Moon: {in_12th}"})
            elif in_2nd and in_12th:
                yogas.append({"name": "Durdhura", "details": f"planets both sides of Moon"})
            elif not in_2nd and not in_12th:
                yogas.append({"name": "Kemadruma", "details": "Moon isolated — emotional struggle in this varga"})
        # Lagnadhi: benefics in 7/8/9 from Lagna
        adhi_houses = {7, 8, 9}
        adhi_planets = []
        for p in BENEFICS - {"Moon"}:  # Moon excluded
            psi = _planet_sign_in_varga(ch, p)
            if psi is None: continue
            if _house_from_lagna(psi, lg) in adhi_houses:
                adhi_planets.append(p)
        if len(adhi_planets) >= 2:
            yogas.append({"name": "Lagnadhi (Adhi)", "details": f"benefics in 7/8/9: {adhi_planets}"})
        if yogas:
            out_by_varga[label] = yogas
    return {"by_varga": out_by_varga,
            "total": sum(len(v) for v in out_by_varga.values())}


# ─── F5: Per-varga dosha ─────────────────────────────────────────────
def detect_varga_dosha(vargas: dict[str, dict]) -> dict[str, Any]:
    """Detect doshas in each varga: Mangal, Kemadruma, Papakartari (Lagna),
       Daridra (2H affliction), Grahan (Sun/Moon with Rahu/Ketu)."""
    if not vargas: return {}
    DOMAIN = {"D1":"Self","D2":"Wealth","D3":"Siblings","D7":"Children",
              "D9":"Marriage","D10":"Career","D12":"Parents","D16":"Vehicles",
              "D20":"Spirituality","D24":"Education","D27":"Strengths",
              "D30":"Misfortunes","D40":"Maternal","D45":"Paternal","D60":"Past-life"}
    out_by_varga: dict[str, list[dict]] = {}
    MANGAL_HOUSES = {1, 2, 4, 7, 8, 12}
    for label, ch in vargas.items():
        if not ch: continue
        lg = _varga_lagna_idx(ch)
        if lg is None: continue
        doshas = []
        # 1. Mangal Dosh per varga
        mars_si = _planet_sign_in_varga(ch, "Mars")
        if mars_si is not None:
            mh = _house_from_lagna(mars_si, lg)
            if mh in MANGAL_HOUSES:
                doshas.append({"name": "Mangal Dosh", "house": mh,
                               "detail": f"Mars in H{mh} of {label} ({DOMAIN.get(label,'')})"})
        # 2. Kemadruma per varga
        moon_si = _planet_sign_in_varga(ch, "Moon")
        if moon_si is not None:
            second = (moon_si + 1) % 12
            twelfth = (moon_si - 1) % 12
            empty_2 = empty_12 = True
            for p in ("Sun","Mars","Mercury","Jupiter","Venus","Saturn"):
                psi = _planet_sign_in_varga(ch, p)
                if psi == second: empty_2 = False
                if psi == twelfth: empty_12 = False
            if empty_2 and empty_12:
                doshas.append({"name": "Kemadruma Dosh",
                               "detail": f"Moon isolated in {label}"})
        # 3. Papakartari on Lagna: malefics in 2nd & 12th from Lagna
        snd_sign = (lg + 1) % 12
        twe_sign = (lg - 1) % 12
        mal_in_2 = mal_in_12 = False
        for p in MALEFICS:
            psi = _planet_sign_in_varga(ch, p)
            if psi == snd_sign: mal_in_2 = True
            if psi == twe_sign: mal_in_12 = True
        if mal_in_2 and mal_in_12:
            doshas.append({"name": "Papakartari (Lagna squeeze)",
                           "detail": f"Malefics in 2nd and 12th of {label} Lagna"})
        # 4. Daridra: 2H heavily afflicted (≥2 malefics in 2H)
        snd_h_count = 0
        for p in MALEFICS:
            psi = _planet_sign_in_varga(ch, p)
            if psi is not None and _house_from_lagna(psi, lg) == 2:
                snd_h_count += 1
        if snd_h_count >= 2:
            doshas.append({"name": "Daridra (2H wealth-house)",
                           "detail": f"{snd_h_count} malefics in 2H of {label}"})
        # 5. Grahan: Sun or Moon with Rahu or Ketu in same sign
        sun_si = _planet_sign_in_varga(ch, "Sun")
        rahu_si = _planet_sign_in_varga(ch, "Rahu")
        ketu_si = _planet_sign_in_varga(ch, "Ketu")
        if sun_si is not None and (sun_si == rahu_si or sun_si == ketu_si):
            node = "Rahu" if sun_si == rahu_si else "Ketu"
            doshas.append({"name": "Surya Grahan", "detail": f"Sun+{node} same sign in {label}"})
        if moon_si is not None and (moon_si == rahu_si or moon_si == ketu_si):
            node = "Rahu" if moon_si == rahu_si else "Ketu"
            doshas.append({"name": "Chandra Grahan", "detail": f"Moon+{node} same sign in {label}"})
        if doshas:
            out_by_varga[label] = doshas
    return {"by_varga": out_by_varga,
            "total": sum(len(v) for v in out_by_varga.values())}


# ─── Master orchestrator ──────────────────────────────────────────────
def compute_varga_phase_f(planets: list, lagna_lon: Optional[float],
                           current_md: str = "", current_ad: str = "") -> dict[str, Any]:
    vargas = _build_all_vargas(planets, lagna_lon)
    if not vargas:
        return {"available": False,
                "reason": "missing lagna_lon — varga depth requires longitude"}
    return {
        "available": True,
        "vargas_count": len(vargas),
        "varga_dasha_overlay": compute_varga_dasha_overlay(vargas, current_md, current_ad),
        "varga_yoga_expand":  detect_varga_yoga_expand(vargas),
        "varga_dosha":        detect_varga_dosha(vargas),
    }


def format_varga_phase_f_summary(result: dict) -> str:
    if not result or not result.get("available"):
        return f"▸ PHASE F (Per-Varga Depth): ❌ {result.get('reason','n/a') if result else 'n/a'}"
    lines = [f"▸ PHASE F PER-VARGA DEPTH (Sprint-32): {result.get('vargas_count',0)} vargas analysed"]
    # F3 Dasha overlay
    vd = result.get("varga_dasha_overlay") or {}
    if vd.get("available") and vd.get("rows"):
        lines.append(f"  ── F3 VARGA-DASHA OVERLAY (current MD={vd.get('current_md','?')}, "
                     f"AD={vd.get('current_ad','?')}) ──")
        for r in vd["rows"]:
            ad_part = (f" · AD {r['ad_lord']} in {r['ad_sign']} (H{r['ad_house']})"
                       if r.get("ad_lord") else "")
            lines.append(f"    · {r['varga']:4s} ({r['domain']:14s}): "
                         f"MD {r['md_lord']} → {r['md_sign']} (H{r['md_house']}){ad_part}")
    # F4 Yoga expansion
    vy = result.get("varga_yoga_expand") or {}
    if vy.get("by_varga"):
        lines.append(f"  ── F4 VARGA-YOGA EXPAND ({vy.get('total',0)} new yogas across "
                     f"D2/D3/D7/D12/D16/D20/D27/D30) ──")
        for label, ys in vy["by_varga"].items():
            names = ", ".join(y["name"] for y in ys)
            lines.append(f"    · {label}: {names}")
    # F5 Dosha
    vx = result.get("varga_dosha") or {}
    if vx.get("by_varga"):
        lines.append(f"  ── F5 VARGA-DOSHA ({vx.get('total',0)} doshas across vargas) ──")
        for label, ds in vx["by_varga"].items():
            names = "; ".join(f"{d['name']}" for d in ds)
            lines.append(f"    · {label}: {names}")
    return "\n".join(lines)
