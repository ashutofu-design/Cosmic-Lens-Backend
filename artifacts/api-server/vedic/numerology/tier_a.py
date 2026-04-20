"""
numerology/tier_a.py — Premium feature pack (Tier A + Part-2 helpers).

Five high-engagement, classical features added to make the ₹99 report
feel like ₹500-2000 product:

  1. Mobile / Vehicle / House number analysis (3-in-1 engine)
  2. Compatibility scoring (love + business)  — Driver/Conductor/Life-path matrix
  3. Karmic Lessons (missing letters in name → numbers)
  4. Hidden Passion (most-frequent letter-number in name)
  5. Maturity Number (Life-Path + Expression, fires after age ~35)
  6. Strict Chaldean alphabet engine (no 9s; the Cheiro standard)
  7. Name correction suggestions (variants ranked by Driver/Conductor harmony)

100% deterministic — zero AI. All algorithms from classical corpus
(Cheiro / Sepharial / Bansilal Jumaani / K.N. Rao).
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .meanings import SINGLE_DIGIT_SHORT
from .phase_s import NUMBER_ENEMIES, NUMBER_FRIENDS, PLANET_BY_NUMBER

# ─── Alphabet maps ───────────────────────────────────────────────────

_PYTH = {c: ((i % 9) + 1) for i, c in enumerate("abcdefghijklmnopqrstuvwxyz")}

# Strict Chaldean alphabet — no 9 (sacred), letters mapped by sound vibration.
# Source: Cheiro's Book of Numbers, Sepharial.
CHALDEAN_MAP: Dict[str, int] = {
    "a": 1, "i": 1, "j": 1, "q": 1, "y": 1,
    "b": 2, "k": 2, "r": 2,
    "c": 3, "g": 3, "l": 3, "s": 3,
    "d": 4, "m": 4, "t": 4,
    "e": 5, "h": 5, "n": 5, "x": 5,
    "u": 6, "v": 6, "w": 6,
    "o": 7, "z": 7,
    "f": 8, "p": 8,
    # 9 is intentionally absent in Chaldean
}

_VOWELS = set("aeiou")


# ─── Helpers ─────────────────────────────────────────────────────────

def _digits_of(text: str) -> List[int]:
    """Extract numeric digits from any string (phone, vehicle plate, house no)."""
    return [int(c) for c in str(text or "") if c.isdigit()]


def _reduce(n: int, *, keep_master: bool = False) -> int:
    """Reduce to single digit. If keep_master, preserves 11/22/33."""
    if n is None:
        return 0
    n = abs(int(n))
    while n > 9:
        if keep_master and n in (11, 22, 33):
            return n
        n = sum(int(d) for d in str(n))
    return n


def _letters_only(name: str) -> str:
    return "".join(c for c in (name or "").lower() if c.isalpha())


# ─── 1. Mobile / Vehicle / House number analysis ─────────────────────

def analyze_number_string(value: str, *, kind: str,
                          driver: int | None = None,
                          conductor: int | None = None) -> Dict[str, Any]:
    """Generic engine for mobile, vehicle, house number analysis.

    kind ∈ {"mobile", "vehicle", "house"} — only changes the title/notes.
    Returns total, reduced, planet, verdict vs Driver/Conductor.
    """
    digits = _digits_of(value)
    if not digits:
        return {
            "ok": False,
            "error": f"No digits found in {kind} number.",
            "input": value,
        }

    total = sum(digits)
    reduced = _reduce(total)
    planet = PLANET_BY_NUMBER.get(reduced)

    # Verdict vs Driver
    verdict = "NEUTRAL"
    verdict_reason = ""
    if driver:
        if reduced == driver:
            verdict = "EXCELLENT"
            verdict_reason = f"Same as your Driver ({driver}) — strong resonance."
        elif reduced in (NUMBER_FRIENDS.get(driver) or []):
            verdict = "FAVOURABLE"
            verdict_reason = f"Friend of your Driver ({driver})."
        elif reduced in (NUMBER_ENEMIES.get(driver) or []):
            verdict = "AVOID"
            verdict_reason = f"Enemy of your Driver ({driver})."
        else:
            verdict = "NEUTRAL"
            verdict_reason = f"Neutral with your Driver ({driver})."

    # Bonus vs Conductor
    conductor_note = ""
    if conductor and reduced != driver:
        if reduced == conductor:
            conductor_note = f"Also matches your Conductor ({conductor}) — extra harmony."
        elif reduced in (NUMBER_FRIENDS.get(conductor) or []):
            conductor_note = f"Friendly to your Conductor ({conductor})."
        elif reduced in (NUMBER_ENEMIES.get(conductor) or []):
            conductor_note = f"Conflicts with your Conductor ({conductor})."

    # Calculation breakdown for transparency (digits → total → reduced)
    chain = " + ".join(str(d) for d in digits) + f" = {total}"
    if total != reduced:
        # Show the reduction chain
        steps = [total]
        cur = total
        while cur > 9:
            cur = sum(int(d) for d in str(cur))
            steps.append(cur)
        chain += " → " + " → ".join(str(x) for x in steps[1:])

    titles = {
        "mobile": "Mobile Number Analysis",
        "vehicle": "Vehicle Number Analysis",
        "house": "House Number Analysis",
    }

    return {
        "ok": True,
        "kind": kind,
        "title": titles.get(kind, "Number Analysis"),
        "input": value,
        "digits": digits,
        "total": total,
        "reduced": reduced,
        "planet": planet,
        "calculation_chain": chain,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "conductor_note": conductor_note,
        "energy": SINGLE_DIGIT_SHORT.get(reduced, ""),
        "tip": _kind_tip(kind, reduced, verdict),
    }


def _kind_tip(kind: str, reduced: int, verdict: str) -> str:
    """Practical guidance per kind."""
    if kind == "mobile":
        if verdict == "AVOID":
            return ("Yeh mobile number aapke Driver se mismatch hai — naya number "
                    "lete waqt 1, 3, 5, 6 jaisa friendly digit-sum prefer kare.")
        if verdict in ("EXCELLENT", "FAVOURABLE"):
            return "Yeh number aapke liye favourable hai — important calls/business is se kare."
        return "Yeh number neutral hai — koi badi mehnat ya benefit nahi degi."
    if kind == "vehicle":
        if verdict == "AVOID":
            return ("Vehicle number aapke Driver ke against hai — bar-bar repair, "
                    "loss ya accident risk. Naya number lete waqt friendly digit-sum chuniye.")
        if verdict in ("EXCELLENT", "FAVOURABLE"):
            return "Vehicle aapke liye lucky hai — long journeys, profit aur safety strong."
        return "Vehicle number neutral hai — sambhal ke chalaayein, drive safe."
    if kind == "house":
        if verdict == "AVOID":
            return ("Ghar ka number aapke vibration se nahi milta — financial stress, "
                    "family conflict ka risk. Door pe friendly number ka sticker laga sakte hain.")
        if verdict in ("EXCELLENT", "FAVOURABLE"):
            return "Ghar lucky hai — wealth, peace aur progress is jagah aayegi."
        return "Ghar neutral hai — koi remedy zaruri nahi, par actively bless kare."
    return ""


# ─── 2. Compatibility scoring (love + business) ──────────────────────

def _life_path(dob_yyyy_mm_dd: str) -> int:
    """Compute life-path from yyyy-mm-dd."""
    digits = _digits_of(dob_yyyy_mm_dd)
    return _reduce(sum(digits))


def _driver_from_dob(dob: str) -> int:
    """Driver = day of birth, reduced to single digit."""
    parts = (dob or "").split("-")
    if len(parts) != 3:
        return 0
    try:
        day = int(parts[2])
        return _reduce(day)
    except (TypeError, ValueError):
        return 0


def _conductor_from_dob(dob: str) -> int:
    """Conductor = sum of all DOB digits, reduced."""
    return _reduce(sum(_digits_of(dob)))


def _pair_score(a: int, b: int) -> Tuple[int, str]:
    """Return (score 0-100, label) for a pair of single-digit numbers."""
    if not a or not b:
        return 0, "UNKNOWN"
    if a == b:
        return 90, "TWIN"
    friends_a = NUMBER_FRIENDS.get(a) or []
    enemies_a = NUMBER_ENEMIES.get(a) or []
    if b in friends_a:
        return 80, "FRIEND"
    if b in enemies_a:
        return 25, "ENEMY"
    return 55, "NEUTRAL"


def compatibility(person1_dob: str, person2_dob: str,
                  kind: str = "love") -> Dict[str, Any]:
    """Calculate compatibility between two people for love or business.

    Returns per-axis scores (Driver, Conductor, Life-path) + overall %
    + verdict + classical advice.
    """
    if not person1_dob or not person2_dob:
        return {"ok": False, "error": "Both dates of birth required."}

    d1 = _driver_from_dob(person1_dob)
    d2 = _driver_from_dob(person2_dob)
    c1 = _conductor_from_dob(person1_dob)
    c2 = _conductor_from_dob(person2_dob)
    l1 = _life_path(person1_dob)
    l2 = _life_path(person2_dob)

    drv_score, drv_label = _pair_score(d1, d2)
    cnd_score, cnd_label = _pair_score(c1, c2)
    lp_score, lp_label = _pair_score(l1, l2)

    # Weighting: Driver matters most for daily personality;
    #   Life-path for long-term path; Conductor for fortune flow.
    if kind == "business":
        # Business: Conductor (fortune) + Life-path (vision) matter more
        overall = round(drv_score * 0.25 + cnd_score * 0.40 + lp_score * 0.35)
    else:
        # Love: Driver (daily compatibility) matters most
        overall = round(drv_score * 0.45 + cnd_score * 0.25 + lp_score * 0.30)

    if overall >= 75:
        verdict = "EXCELLENT MATCH"
        advice = ("Aap dono ki vibration bahut compatible hai. "
                  "Long-term success ke saare signs hain.")
    elif overall >= 60:
        verdict = "GOOD MATCH"
        advice = ("Strong compatibility. Kuch areas me thoda effort lagega "
                  "par overall favorable.")
    elif overall >= 45:
        verdict = "MIXED"
        advice = ("Mixed energy. Communication aur respect par jyada dhyan de — "
                  "yeh relationship work kar sakti hai mehnat se.")
    else:
        verdict = "CHALLENGING"
        advice = ("Vibrations clash karti hain. Kundli match karwana strongly "
                  "recommended — sirf numerology par decision na le.")

    return {
        "ok": True,
        "kind": kind,
        "person1": {"dob": person1_dob, "driver": d1, "conductor": c1, "life_path": l1},
        "person2": {"dob": person2_dob, "driver": d2, "conductor": c2, "life_path": l2},
        "axes": {
            "driver":    {"score": drv_score, "label": drv_label,
                          "p1": d1, "p2": d2,
                          "explain": "Day-to-day temperament compatibility."},
            "conductor": {"score": cnd_score, "label": cnd_label,
                          "p1": c1, "p2": c2,
                          "explain": "Fortune-flow and material harmony."},
            "life_path": {"score": lp_score, "label": lp_label,
                          "p1": l1, "p2": l2,
                          "explain": "Long-term life-direction alignment."},
        },
        "overall_score": overall,
        "verdict": verdict,
        "advice": advice,
    }


# ─── 3. Karmic Lessons (missing letters → numbers) ───────────────────

def karmic_lessons(name: str) -> Dict[str, Any]:
    """Numbers (1-9) NOT represented by any letter in the name.
    These are the karmic lessons — areas the soul came to learn.
    """
    letters = _letters_only(name)
    if not letters:
        return {"ok": False, "error": "Name required."}

    present_nums = {_PYTH[c] for c in letters if c in _PYTH}
    missing = sorted(set(range(1, 10)) - present_nums)

    LESSONS = {
        1: ("Independence — learn to lead, take own decisions, "
            "stop depending on others' approval."),
        2: ("Cooperation — learn to listen, partner respectfully, "
            "balance own needs with others'."),
        3: ("Self-expression — learn to communicate openly, "
            "show creativity without fear."),
        4: ("Discipline — build steady routines, finish what you start, "
            "respect rules and structure."),
        5: ("Adaptability — embrace change, travel, variety; "
            "stop clinging to comfort."),
        6: ("Responsibility — care for family, accept duty, "
            "learn nurturing without controlling."),
        7: ("Inner faith — trust intuition, develop spiritual depth, "
            "stop over-analyzing everything."),
        8: ("Material mastery — handle money/power ethically, "
            "build wealth without obsession."),
        9: ("Compassion — let go of grudges, serve humanity, "
            "complete what needs ending."),
    }

    return {
        "ok": True,
        "name_letters": letters,
        "present_numbers": sorted(present_nums),
        "missing_numbers": missing,
        "lessons": [{"number": n, "lesson": LESSONS[n]} for n in missing],
        "summary": (
            "Ye missing numbers aapki current life ke karmic lessons hain. "
            "Inhe consciously develop karne se rapid spiritual growth hota hai."
            if missing else
            "Aapke naam me sabhi 1-9 numbers represent hain — ek balanced soul, "
            "no specific karmic lesson is life me uthane ki zaroorat."
        ),
    }


# ─── 4. Hidden Passion (most-frequent letter-number) ─────────────────

def hidden_passion(name: str) -> Dict[str, Any]:
    """The number(s) that appear MOST in the name letters.
    These represent inherent talents and natural drives.
    """
    letters = _letters_only(name)
    if not letters:
        return {"ok": False, "error": "Name required."}

    counts: Dict[int, int] = {}
    for c in letters:
        v = _PYTH.get(c)
        if v:
            counts[v] = counts.get(v, 0) + 1
    if not counts:
        return {"ok": False, "error": "No alphabetic letters in name."}

    max_n = max(counts.values())
    dominant = sorted([n for n, c in counts.items() if c == max_n])

    PASSION = {
        1: "Leadership, originality, pioneering — drive to be first.",
        2: "Diplomacy, partnership, sensitivity — drive to harmonize.",
        3: "Self-expression, creativity, joy — drive to communicate.",
        4: "Building, structure, hard work — drive to create order.",
        5: "Freedom, change, adventure — drive to experience life.",
        6: "Love, family, service — drive to nurture and beautify.",
        7: "Wisdom, mystery, research — drive to understand.",
        8: "Power, achievement, wealth — drive to master material world.",
        9: "Compassion, completion, humanitarianism — drive to serve all.",
    }

    return {
        "ok": True,
        "letter_counts_by_number": counts,
        "max_count": max_n,
        "dominant_numbers": dominant,
        "meanings": [{"number": n, "passion": PASSION[n]} for n in dominant],
        "summary": (
            f"Aapka Hidden Passion: {', '.join(str(n) for n in dominant)} — "
            "yeh aapke inherent talents hain, jo natural easy aate hain. "
            "Career/hobbies inhi ke around build kare for max success."
        ),
    }


# ─── 5. Maturity Number ──────────────────────────────────────────────

def maturity_number(life_path: int, expression: int) -> Dict[str, Any]:
    """Maturity = Life-Path + Expression, reduced.
    Activates around age 30-35 and dominates the second half of life.
    """
    try:
        lp = int(life_path)
        ex = int(expression)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Both life_path and expression required (int)."}

    raw = lp + ex
    mat = _reduce(raw, keep_master=True)
    planet = PLANET_BY_NUMBER.get(_reduce(mat))

    MATURITY = {
        1: "Late-life leadership, recognition, pioneering achievements.",
        2: "Late-life partnership, diplomacy, peaceful collaborations dominate.",
        3: "Late-life expression — writing, teaching, public speaking flourish.",
        4: "Late-life builder — solid foundation, real estate, organizations.",
        5: "Late-life freedom — travel, change, multiple ventures.",
        6: "Late-life service — family, healing, beauty, community leadership.",
        7: "Late-life wisdom — research, spirituality, retreat and depth.",
        8: "Late-life material mastery — wealth, authority, recognition.",
        9: "Late-life humanitarian — philanthropy, completion, global vision.",
        11: "Late-life inspiration — spiritual teaching, illumination of others.",
        22: "Late-life master-builder — large-scale impact on society.",
        33: "Late-life master-teacher — selfless service at the highest level.",
    }

    return {
        "ok": True,
        "life_path": lp,
        "expression": ex,
        "raw_sum": raw,
        "maturity": mat,
        "planet": planet,
        "meaning": MATURITY.get(mat, ""),
        "activates_at": "around age 30-35",
        "summary": (
            f"Aapka Maturity Number {mat} hai — yeh ~age 30-35 ke baad strongly "
            "active hota hai aur jeevan ke uttarardh ka theme set karta hai."
        ),
    }


# ─── 6. Strict Chaldean alphabet engine ──────────────────────────────

def chaldean_name_numbers(name: str) -> Dict[str, Any]:
    """Compute name-numerology using strict Chaldean alphabet (no 9)."""
    letters = _letters_only(name)
    if not letters:
        return {"ok": False, "error": "Name required."}

    total_all = sum(CHALDEAN_MAP.get(c, 0) for c in letters)
    vowels = sum(CHALDEAN_MAP.get(c, 0) for c in letters if c in _VOWELS)
    cons = sum(CHALDEAN_MAP.get(c, 0) for c in letters if c not in _VOWELS)

    return {
        "ok": True,
        "alphabet": "Chaldean (strict — no 9, sacred)",
        "name_letters": letters,
        "expression": {"raw": total_all, "reduced": _reduce(total_all, keep_master=True)},
        "soul_urge": {"raw": vowels, "reduced": _reduce(vowels, keep_master=True)},
        "personality": {"raw": cons, "reduced": _reduce(cons, keep_master=True)},
        "compound": total_all,
        "note": ("Chaldean is the older, stricter system used by Cheiro. "
                 "Use Pythagorean for spiritual analysis, Chaldean for "
                 "professional/branding decisions."),
    }


# ─── 7. Name correction suggestions ──────────────────────────────────

def _name_score(name: str, target_driver: int, target_conductor: int) -> int:
    """Score a name variant against target Driver/Conductor.
    Higher = better harmony."""
    letters = _letters_only(name)
    if not letters:
        return 0
    total = sum(_PYTH.get(c, 0) for c in letters)
    name_num = _reduce(total)

    score = 30  # baseline
    # Best: name = driver
    if name_num == target_driver:
        score += 50
    elif name_num in (NUMBER_FRIENDS.get(target_driver) or []):
        score += 35
    elif name_num in (NUMBER_ENEMIES.get(target_driver) or []):
        score -= 30

    # Bonus for conductor harmony
    if name_num == target_conductor:
        score += 15
    elif name_num in (NUMBER_FRIENDS.get(target_conductor) or []):
        score += 10
    elif name_num in (NUMBER_ENEMIES.get(target_conductor) or []):
        score -= 15

    return max(0, min(100, score))


# ─── Part-2 deep-dive helpers ────────────────────────────────────────

def digit_breakdown(value: str) -> List[Dict[str, Any]]:
    """Break a number string into per-digit list with planet + meaning."""
    DIGIT_MEANING = {
        0: ("—",       "Void / amplifier — multiplies adjacent digit's energy."),
        1: ("Sun",     "Leadership, ego, authority, fame."),
        2: ("Moon",    "Emotion, public, mother, fluctuation."),
        3: ("Jupiter", "Wisdom, finance, expansion, dharma."),
        4: ("Rahu",    "Sudden change, illusion, rebellion, tech."),
        5: ("Mercury", "Business, communication, intelligence, agility."),
        6: ("Venus",   "Love, luxury, beauty, vehicles, women."),
        7: ("Ketu",    "Spirituality, mystery, isolation, research."),
        8: ("Saturn",  "Karma, hardship turning to wealth, discipline."),
        9: ("Mars",    "Courage, war, energy, brothers, action."),
    }
    out = []
    for d in _digits_of(value):
        planet, meaning = DIGIT_MEANING.get(d, ("—", ""))
        out.append({"digit": d, "planet": planet, "meaning": meaning})
    return out


def repeating_digit_alerts(value: str) -> List[str]:
    """Detect concerning patterns: e.g. lots of 4s/8s = Rahu/Saturn heavy."""
    digits = _digits_of(value)
    if not digits:
        return []
    alerts: List[str] = []
    counts: Dict[int, int] = {}
    for d in digits:
        counts[d] = counts.get(d, 0) + 1
    total = len(digits)

    if counts.get(4, 0) >= 3:
        alerts.append("⚠ 4 (Rahu) bahut baar — sudden disruptions, "
                      "tech glitches, unexpected events frequent.")
    if counts.get(8, 0) >= 3:
        alerts.append("⚠ 8 (Saturn) bahut baar — initial struggle bahut, "
                      "par disciplined log ke liye long-term wealth.")
    if counts.get(0, 0) >= 3:
        alerts.append("⚠ Multiple 0s — energy void, neighbor digits ki "
                      "energy ko amplify ya nullify karte hain.")
    if total >= 4 and counts.get(7, 0) >= 3:
        alerts.append("ℹ 7 (Ketu) repeated — spiritual but isolating; "
                      "social/business ke liye mixed.")
    if total >= 6 and counts.get(1, 0) + counts.get(3, 0) + counts.get(6, 0) >= 5:
        alerts.append("✓ Bahut saare 1/3/6 — natural prosperity & "
                      "favourable vibration.")
    return alerts


def last_four_analysis(value: str) -> Dict[str, Any]:
    """Cheiro: last 4 digits of a phone number have most influence."""
    digits = _digits_of(value)
    if len(digits) < 4:
        return {"ok": False}
    last4 = digits[-4:]
    last4_sum = sum(last4)
    return {
        "ok": True,
        "last4": "".join(str(d) for d in last4),
        "sum": last4_sum,
        "reduced": _reduce(last4_sum),
        "note": "Cheiro ke according — last 4 digits sabse jyada vibration deti hain.",
    }


def lucky_number_alternatives(driver: int, conductor: int,
                              base_value: str | None = None,
                              count: int = 6,
                              length: int = 10) -> List[Dict[str, Any]]:
    """Generate sample 'good' number variations near base_value (or random)
    that score well against driver+conductor.

    Tries swapping the last 1-2 digits of the base to get a friendlier sum.
    """
    if not driver:
        return []
    targets = set([driver] + (NUMBER_FRIENDS.get(driver) or []))
    if conductor:
        targets.update([conductor] + (NUMBER_FRIENDS.get(conductor) or []))

    base_digits = _digits_of(base_value or "")
    suggestions: List[Dict[str, Any]] = []
    seen = set()

    if len(base_digits) >= 4:
        # Try swapping the last digit through 0-9
        prefix = base_digits[:-1]
        prefix_sum = sum(prefix)
        for last in range(10):
            cand_sum = prefix_sum + last
            cand_red = _reduce(cand_sum)
            if cand_red in targets:
                cand = "".join(str(d) for d in prefix) + str(last)
                if cand == "".join(str(d) for d in base_digits):
                    continue
                if cand in seen:
                    continue
                seen.add(cand)
                verdict = ("EXCELLENT" if cand_red == driver
                           else "FAVOURABLE")
                suggestions.append({
                    "number": cand,
                    "sum": cand_sum,
                    "reduced": cand_red,
                    "verdict": verdict,
                    "matches": ("Driver" if cand_red == driver
                                else "Conductor" if cand_red == conductor
                                else "Friend of Driver"),
                })

        # Also try last 2 digits
        if len(suggestions) < count and len(base_digits) >= 5:
            prefix2 = base_digits[:-2]
            prefix2_sum = sum(prefix2)
            for tens in range(10):
                for ones in range(10):
                    cand_sum = prefix2_sum + tens + ones
                    cand_red = _reduce(cand_sum)
                    if cand_red == driver:
                        cand = "".join(str(d) for d in prefix2) + str(tens) + str(ones)
                        if cand in seen or cand == "".join(str(d) for d in base_digits):
                            continue
                        seen.add(cand)
                        suggestions.append({
                            "number": cand,
                            "sum": cand_sum,
                            "reduced": cand_red,
                            "verdict": "EXCELLENT",
                            "matches": "Driver",
                        })
                        if len(suggestions) >= count * 2:
                            break
                if len(suggestions) >= count * 2:
                    break

    # Sort: driver-matches first, then friends
    suggestions.sort(key=lambda s: (
        0 if s["reduced"] == driver else
        1 if s["reduced"] == conductor else 2,
        s["number"],
    ))
    return suggestions[:count]


def compatibility_matrix(driver: int) -> List[Dict[str, Any]]:
    """How user's driver pairs with each of 1-9. Returns 9 rows."""
    if not driver:
        return []
    out = []
    friends = NUMBER_FRIENDS.get(driver) or []
    enemies = NUMBER_ENEMIES.get(driver) or []
    for n in range(1, 10):
        if n == driver:
            label, score, advice = ("TWIN", 90,
                "Same vibration — strong resonance, par echo-chamber risk.")
        elif n in friends:
            label, score, advice = ("FRIEND", 80,
                "Natural support, harmonious interactions.")
        elif n in enemies:
            label, score, advice = ("ENEMY", 25,
                "Friction, misunderstandings — extra patience zaruri.")
        else:
            label, score, advice = ("NEUTRAL", 55,
                "Balanced — neither natural ally nor obstacle.")
        out.append({
            "number": n,
            "planet": PLANET_BY_NUMBER.get(n, "—"),
            "label": label,
            "score": score,
            "advice": advice,
        })
    return out


def letter_by_letter(name: str) -> List[Dict[str, Any]]:
    """Per-letter Pythagorean + Chaldean breakdown for visual table."""
    rows: List[Dict[str, Any]] = []
    for c in (name or ""):
        if c.isalpha():
            cl = c.lower()
            rows.append({
                "letter": c.upper(),
                "vowel": cl in _VOWELS,
                "pythagorean": _PYTH.get(cl, 0),
                "chaldean": CHALDEAN_MAP.get(cl, 0),  # 0 if not in chaldean (i.e., maps to 9)
            })
        elif c == " ":
            rows.append({"letter": " ", "vowel": False,
                         "pythagorean": "—", "chaldean": "—"})
    return rows


def signature_advice(name: str, driver: int) -> Dict[str, Any]:
    """Initial-letter & signature recommendations."""
    letters = _letters_only(name)
    if not letters:
        return {"ok": False}
    first = letters[0]
    first_val = _PYTH.get(first, 0)
    first_planet = PLANET_BY_NUMBER.get(first_val, "—")

    INITIAL_ADVICE = {
        1: "Strong start — leadership presence in every interaction.",
        2: "Soft, diplomatic start — people feel safe around you.",
        3: "Joyful expressive start — natural communicator.",
        4: "Stable, dependable start — slow burn but reliable.",
        5: "Dynamic, restless start — change-bringer.",
        6: "Warm, nurturing start — beauty/family attracted to you.",
        7: "Mysterious, deep start — others sense hidden wisdom.",
        8: "Powerful, formidable start — material success magnet.",
        9: "Universal, humanitarian start — wide appeal.",
    }

    # Signature direction recommendation: based on driver
    SIG_DIRECTION = {
        1: "Upward stroke — solar energy supports you.",
        2: "Smooth curves — lunar fluidity matches your nature.",
        3: "Bold outward strokes — Jupiter expansion.",
        4: "Sharp angles — Rahu's modern edge (avoid sloppy).",
        5: "Quick, light strokes — Mercury's speed.",
        6: "Rounded, beautiful loops — Venus aesthetic.",
        7: "Minimal, mysterious — Ketu's restraint.",
        8: "Strong descenders — Saturn's depth.",
        9: "Energetic strokes with completion — Mars finishing power.",
    }

    return {
        "ok": True,
        "first_letter": first.upper(),
        "first_letter_value": first_val,
        "first_letter_planet": first_planet,
        "initial_meaning": INITIAL_ADVICE.get(first_val, ""),
        "signature_tip": SIG_DIRECTION.get(driver, ""),
        "general_rules": [
            "Signature hamesha upward angle me end karein (rising fortune).",
            "Apna pura naam clearly likhein — incomplete signature = incomplete results.",
            "Underline ke saath sign karna confidence aur stability deta hai.",
            "Cross-cuts (line cutting through name) avoid kare — self-sabotage indicator.",
        ],
    }


def implementation_timeline() -> List[Dict[str, str]]:
    """30-day rollout plan for name correction / number changes."""
    return [
        {"phase": "Day 1-7",
         "action": "Naya name spelling sirf signature aur social media par use karna start kare. Old documents abhi mat badle."},
        {"phase": "Day 8-21",
         "action": "Email signature, business cards, WhatsApp display name — sab jagah update kare. Mantra japna start kare driver number ke planet ka (e.g., 108 baar)."},
        {"phase": "Day 22-40",
         "action": "Vibrational shift mahsoos hone lagega — naye opportunities, naye contacts. Mobile/vehicle change ki planning is window me kare."},
        {"phase": "Day 41-90",
         "action": "Major life domains me effect dikhega — career conversations, relationship dynamics. Patience zaruri — full integration 90 din lagti hai."},
    ]


def name_correction_suggestions(name: str, driver: int, conductor: int,
                                limit: int = 8) -> Dict[str, Any]:
    """Generate spelling variants and rank by Driver/Conductor harmony.

    Strategies (classical numerology corrections):
      - Double a vowel (Anita → Aniita)
      - Double a consonant (Anita → Annita)
      - Add a trailing 'e', 'a', 'h'
      - Drop a vowel
      - Swap 'i'↔'y', 'k'↔'c'
    """
    if not name or not driver:
        return {"ok": False, "error": "Name and driver required."}

    base = name.strip()
    base_score = _name_score(base, driver, conductor)
    base_letters = _letters_only(base)
    base_num = _reduce(sum(_PYTH.get(c, 0) for c in base_letters))

    variants: List[Tuple[str, int, int]] = []  # (name, score, name_number)

    def _add(n: str):
        if not n or n.lower() == base.lower():
            return
        sc = _name_score(n, driver, conductor)
        nl = _letters_only(n)
        nn = _reduce(sum(_PYTH.get(c, 0) for c in nl))
        variants.append((n, sc, nn))

    # 1. Double each vowel once
    for i, ch in enumerate(base):
        if ch.lower() in _VOWELS:
            _add(base[:i + 1] + ch + base[i + 1:])

    # 2. Double each consonant once (in middle of word)
    for i, ch in enumerate(base):
        if ch.isalpha() and ch.lower() not in _VOWELS and 0 < i < len(base) - 1:
            _add(base[:i + 1] + ch + base[i + 1:])

    # 3. Add trailing letter
    for suffix in ["a", "e", "h"]:
        if not base.lower().endswith(suffix):
            _add(base + suffix)

    # 4. Drop one trailing vowel
    if base[-1:].lower() in _VOWELS and len(base) > 3:
        _add(base[:-1])

    # 5. Swap i↔y at word boundary
    if "y" in base.lower():
        _add(base.replace("y", "i").replace("Y", "I"))
    if "i" in base.lower():
        _add(base.replace("i", "y").replace("I", "Y"))

    # 6. Swap k↔c, s↔z
    if "k" in base.lower() or "K" in base:
        _add(base.replace("k", "c").replace("K", "C"))
    if "c" in base.lower() or "C" in base:
        _add(base.replace("c", "k").replace("C", "K"))

    # Dedupe + sort by score desc, take top N
    seen = set()
    unique = []
    for n, sc, nn in variants:
        key = n.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append((n, sc, nn))
    unique.sort(key=lambda x: -x[1])
    top = unique[:limit]

    # Filter only those that are an *improvement* over base
    improvements = [(n, sc, nn) for n, sc, nn in top if sc > base_score]

    def _verdict(score: int) -> str:
        if score >= 80:
            return "EXCELLENT"
        if score >= 60:
            return "GOOD"
        if score >= 40:
            return "OK"
        return "POOR"

    return {
        "ok": True,
        "original": {
            "name": base,
            "name_number": base_num,
            "harmony_score": base_score,
            "verdict": _verdict(base_score),
        },
        "target_driver": driver,
        "target_conductor": conductor,
        "suggestions": [
            {"name": n, "name_number": nn, "harmony_score": sc,
             "verdict": _verdict(sc),
             "delta": sc - base_score}
            for n, sc, nn in top
        ],
        "best_improvements": [
            {"name": n, "name_number": nn, "harmony_score": sc,
             "delta_vs_original": sc - base_score}
            for n, sc, nn in improvements[:3]
        ],
        "note": (
            "Name correction ek classical remedy hai — naya name signature, "
            "social media, business card pe use kare. Legal documents change "
            "karna optional hai. 21-40 din me vibration shift mahsoos hoga."
        ) if improvements else (
            "Aapka current name spelling already aapke Driver ke saath strong "
            "harmony me hai — koi badlav ki zarurat nahi."
        ),
    }
