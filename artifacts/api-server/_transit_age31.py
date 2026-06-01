"""Step 6 transit check at user age ~31 (2030-2031)."""
import sys
from datetime import datetime

sys.path.insert(0, ".")

try:
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    HAS = True
except Exception:
    HAS = False
    print("no swisseph")

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
LAGSIGN = 8  # Sagittarius
H7_SIGN = (LAGSIGN + 6) % 12  # Gemini = 2
H7L_SIGN = 7  # Scorpio - Mercury natal

def _aspects_target(aspector, ap_si, target_si):
    diff = (target_si - ap_si) % 12 + 1
    if diff == 7:
        return True
    if aspector == "Jupiter" and diff in (4, 8):
        return True
    if aspector == "Saturn" and diff in (3, 10):
        return True
    return False

def hits(aspector, p_si, target_si):
    return p_si == target_si or _aspects_target(aspector, p_si, target_si)

def check_date(when):
    if not HAS:
        return
    jd = swe.julday(when.year, when.month, when.day, 12.0)
    jup, _ = swe.calc_ut(jd, swe.JUPITER, swe.FLG_SIDEREAL)
    sat, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
    j_si = int(float(jup[0]) / 30) % 12
    s_si = int(float(sat[0]) / 30) % 12
    targets = {"7H Gemini": H7_SIGN, "7L Scorpio": H7L_SIGN}
    print(f"\n=== {when.date()} (age ~{(when.year-1999)}) ===")
    print(f"  Jupiter in {SIGNS[j_si]} | Saturn in {SIGNS[s_si]}")
    all_t = list(targets.values())
    jh = any(hits("Jupiter", j_si, t) for t in all_t)
    sh = any(hits("Saturn", s_si, t) for t in all_t)
    for name, t in targets.items():
        print(f"  {name}: Jup={'HIT' if hits('Jupiter',j_si,t) else 'no'} Sat={'HIT' if hits('Saturn',s_si,t) else 'no'}")
    print(f"  DOUBLE TRANSIT (dt): {jh and sh}")
    print(f"  Step7 pass (Jup OR Sat): {jh or sh}")

# Age 31 windows from earlier analysis
for d in [
    datetime(2026, 5, 15),   # now Mars PD
    datetime(2027, 3, 1),    # Sa-Sa-Me mid
    datetime(2030, 6, 1),    # ~age 30.5
    datetime(2030, 11, 15),  # age 31 BCP
    datetime(2031, 6, 1),    # Sa-Me antar
]:
    check_date(d)
