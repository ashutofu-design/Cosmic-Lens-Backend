#!/usr/bin/env python3
import swisseph as swe

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
DASHA_YEARS = {
    "Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
    "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17
}

# Birth: 29 Oct 1999, 11:30 AM IST (tz=+5.5) → UTC 06:00
year, month, day = 1999, 10, 29
hour_utc = 11.5 - 5.5  # = 6.0

jd = swe.julday(year, month, day, hour_utc)
moon_trop, _ = swe.calc_ut(jd, swe.MOON)
ayanamsa   = swe.get_ayanamsa_ut(jd)
moon_sid   = (moon_trop[0] - ayanamsa) % 360

NAK_SPAN   = 360 / 27          # 13.3333...°
nak_idx    = int(moon_sid / NAK_SPAN)
nak_start  = nak_idx * NAK_SPAN
nak_name   = NAKSHATRAS[nak_idx]
nak_lord   = NAKSHATRA_RULERS[nak_idx]

elapsed_deg    = moon_sid - nak_start
frac_elapsed   = elapsed_deg / NAK_SPAN
frac_remaining = 1.0 - frac_elapsed

balance_yrs    = frac_remaining * DASHA_YEARS[nak_lord]
bal_y          = int(balance_yrs)
bal_m_frac     = (balance_yrs - bal_y) * 12
bal_m          = int(bal_m_frac)
bal_d          = round((bal_m_frac - bal_m) * 30)

print(f"Moon sidereal longitude : {moon_sid:.4f}°")
print(f"Nakshatra               : {nak_name}  (index {nak_idx},  start {nak_start:.4f}°)")
print(f"Nakshatra lord (MD-1)   : {nak_lord}  ({DASHA_YEARS[nak_lord]}y full)")
print()
print(f"Position in nak         : {elapsed_deg:.4f}°  of {NAK_SPAN:.4f}°")
print(f"Fraction elapsed        : {frac_elapsed:.6f}  ({frac_elapsed*100:.2f}%)")
print(f"Fraction remaining      : {frac_remaining:.6f}  ({frac_remaining*100:.2f}%)")
print()
print(f"Balance at birth        : {balance_yrs:.6f} years")
print(f"                        = {bal_y}y {bal_m}m {bal_d}d")
