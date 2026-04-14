#!/usr/bin/env python3
"""
Trace exact MD → AD → PD dates for: 29 Oct 1999, 11:30 AM IST, Bhubaneshwar
Today: 21 Mar 2026
"""
import swisseph as swe
import calendar
from datetime import datetime

swe.set_sid_mode(swe.SIDM_LAHIRI)

NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha",
    "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"
]
NAKSHATRA_RULERS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu",
    "Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu",
    "Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu",
    "Jupiter","Saturn","Mercury"
]
DASHA_ORDER = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
DASHA_YEARS = {"Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
               "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17}

def add_years(dt, years):
    y = int(years); rem = years - y
    m_f = rem * 12; m = int(m_f); d = round((m_f - m) * 30)
    yr = dt.year + y; mo = dt.month + m; day = dt.day + d
    while mo > 12: mo -= 12; yr += 1
    while mo < 1:  mo += 12; yr -= 1
    while day < 1:
        mo -= 1
        if mo < 1: mo = 12; yr -= 1
        day += calendar.monthrange(yr, mo)[1]
    while True:
        mx = calendar.monthrange(yr, mo)[1]
        if day <= mx: break
        day -= mx; mo += 1
        if mo > 12: mo = 1; yr += 1
    return dt.replace(year=yr, month=mo, day=day)

def sub_years(dt, years):
    y = int(years); rem = years - y
    m_f = rem * 12; m = int(m_f); d = round((m_f - m) * 30)
    yr = dt.year - y; mo = dt.month - m; day = dt.day - d
    while mo > 12: mo -= 12; yr += 1
    while mo < 1:  mo += 12; yr -= 1
    while day < 1:
        mo -= 1
        if mo < 1: mo = 12; yr -= 1
        day += calendar.monthrange(yr, mo)[1]
    while True:
        mx = calendar.monthrange(yr, mo)[1]
        if day <= mx: break
        day -= mx; mo += 1
        if mo > 12: mo = 1; yr += 1
    return dt.replace(year=yr, month=mo, day=day)

# ── Step 1: Moon position ──────────────────────────────────────────────────
year, month, day = 1999, 10, 29
hour_utc = 11.5 - 5.5   # 06:00 UTC
jd = swe.julday(year, month, day, hour_utc)
moon_trop, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
moon_sid = moon_trop[0] % 360

NAK_SPAN  = 360 / 27
nak_idx   = int(moon_sid / NAK_SPAN)
pos_in_nak = moon_sid % NAK_SPAN
frac_elapsed   = pos_in_nak / NAK_SPAN
frac_remaining = 1 - frac_elapsed

nak_lord  = NAKSHATRA_RULERS[nak_idx]
md0_full  = float(DASHA_YEARS[nak_lord])
elapsed   = frac_elapsed   * md0_full
balance   = frac_remaining * md0_full

birth_dt  = datetime(1999, 10, 29)
md0_start = sub_years(birth_dt, elapsed)
md0_end   = add_years(md0_start, md0_full)

print(f"Moon sidereal   : {moon_sid:.4f}°")
print(f"Nakshatra lord  : {nak_lord}  (frac_elapsed={frac_elapsed:.4f})")
print(f"Balance at birth: {balance:.4f}y")
print()
print(f"MD0 ({nak_lord:8s}): {md0_start.date()}  →  {md0_end.date()}  (full={md0_full}y)")

# ── Step 2: Chain all MDs ──────────────────────────────────────────────────
start_idx = DASHA_ORDER.index(nak_lord)
today = datetime(2026, 3, 21)
print()
print("── ALL MAHADASHAS ──────────────────────────────────────────────────")

md_start = md0_start
active_md = None
active_md_start = None
for i in range(len(DASHA_ORDER) * 3):
    pl  = DASHA_ORDER[(start_idx + i) % len(DASHA_ORDER)]
    yrs = float(DASHA_YEARS[pl])
    md_end = add_years(md_start, yrs)
    flag = " ← TODAY" if md_start <= today < md_end else ""
    print(f"  {pl:10s}: {md_start.date()}  →  {md_end.date()}  ({yrs}y){flag}")
    if md_start <= today < md_end:
        active_md = pl
        active_md_full = yrs
        active_md_start = md_start
    md_start = md_end
    if md_start > datetime(2060, 1, 1): break

# ── Step 3: ADs for active MD ─────────────────────────────────────────────
if active_md:
    print()
    print(f"── ANTARDASHAS in {active_md} MD ({active_md_start.date()}) ─────────────────────────")
    ad_seq = DASHA_ORDER.index(active_md)
    ad_start = active_md_start
    active_ad = None
    active_ad_start = None
    active_ad_full = None
    for j in range(len(DASHA_ORDER)):
        ad_pl  = DASHA_ORDER[(ad_seq + j) % len(DASHA_ORDER)]
        ad_yrs = (active_md_full * DASHA_YEARS[ad_pl]) / 120.0
        ad_end = add_years(ad_start, ad_yrs)
        flag = " ← TODAY" if ad_start <= today < ad_end else ""
        print(f"  {ad_pl:10s}: {ad_start.date()}  →  {ad_end.date()}  ({ad_yrs:.4f}y){flag}")
        if ad_start <= today < ad_end:
            active_ad = ad_pl
            active_ad_start = ad_start
            active_ad_full = ad_yrs
        ad_start = ad_end

    # ── Step 4: PDs for active AD ─────────────────────────────────────────
    if active_ad:
        print()
        print(f"── PRATYANTARDASHAS in {active_md}/{active_ad} ────────────────────────────────")
        pd_seq = DASHA_ORDER.index(active_ad)
        pd_start = active_ad_start
        for k in range(len(DASHA_ORDER)):
            pd_pl  = DASHA_ORDER[(pd_seq + k) % len(DASHA_ORDER)]
            pd_yrs = (active_ad_full * DASHA_YEARS[pd_pl]) / 120.0
            pd_end = add_years(pd_start, pd_yrs)
            flag = " ← TODAY" if pd_start <= today < pd_end else ""
            print(f"  {pd_pl:10s}: {pd_start.date()}  →  {pd_end.date()}  ({pd_yrs:.6f}y){flag}")
            pd_start = pd_end

print()
print(f"Expected by user: Jupiter MD → Rahu AD → Mars PD")
