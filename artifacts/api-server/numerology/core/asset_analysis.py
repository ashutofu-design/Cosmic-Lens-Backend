"""Data-driven mobile / vehicle / house analysis (pure numerology).

Includes a smart input normalizer for cross-country phone numbers, vehicle
plates, and house identifiers. All inputs (Indian, US, UK, etc.) get cleaned
into a numerology-ready digit string before the engine sums them up.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from numerology.core.compatibility import rel_code
from numerology.core.digits import archetype_for, digit_trait, reduce_number
from numerology.core.meanings import SINGLE_DIGIT_SHORT
from numerology.core.number_analysis import (
    analyze_identifier,
    detect_digit_pairs,
    digit_position_rows,
    dominance_score,
    missing_numbers_profile,
    repeating_digit_report,
    rhythm_pattern,
    stability_score,
)
from numerology.core.phase_s import NUMBER_ENEMIES, NUMBER_FRIENDS


# ─────────────────────────────────────────────────────────────────────
#  SMART INPUT NORMALIZER — strips country codes, validates length,
#  returns the digit-string the numerology engine should actually use.
# ─────────────────────────────────────────────────────────────────────
# Common country dialling codes (ordered longest-first so 3-digit codes
# like 971/972 match before 2-digit like 97 would).
_COUNTRY_CODES: List[str] = [
    "971", "972", "966", "964", "962", "961",            # ME (UAE, IL, SA, IQ, JO, LB)
    "91", "92", "93", "94", "95",                        # IN, PK, AF, LK, MM
    "60", "62", "63", "65", "66",                        # MY, ID, PH, SG, TH
    "81", "82", "84", "86", "880", "977",                # JP, KR, VN, CN, BD, NP
    "20", "27", "30", "31", "32", "33", "34",            # EG, ZA, GR, NL, BE, FR, ES
    "39", "40", "41", "43", "44", "45", "46", "47", "48", "49",  # IT, RO, CH, AT, UK, DK, SE, NO, PL, DE
    "51", "52", "54", "55", "56", "57", "58",            # PE, MX, AR, BR, CL, CO, VE
    "61", "64",                                          # AU, NZ
    "7", "1",                                            # RU/KZ, US/CA
]

# Maximum local digits we ever care about for numerology (longest local
# mobile globally is ~11, e.g. China 11-digit).
_MAX_LOCAL_DIGITS = 12
_MIN_PHONE_DIGITS = 7
_MAX_PHONE_DIGITS = 15  # E.164 international max (incl. country code)


def _digits_of(s: str) -> str:
    """Extract only ASCII digits from a string. Returns empty if none."""
    return re.sub(r"\D", "", str(s or ""))


def normalize_phone_input(raw: str) -> Dict[str, Any]:
    """Clean a phone number string for numerology calculation.

    Strategy:
      1. Strip everything except digits.
      2. If a known country dialling code prefix is present (e.g. 91, 1,
         44, 971) AND removing it leaves a plausible local length (7–11),
         remove it.
      3. Validate final length: 7 ≤ digits ≤ 15.

    Returns a dict with:
      original, cleaned (digits used by engine), digits_only (all digits
      including code), country_code (detected or None), length, valid, error.
    """
    original = str(raw or "")
    all_digits = _digits_of(original)
    if not all_digits:
        return {
            "original": original, "cleaned": "", "digits_only": "",
            "country_code": None, "length": 0,
            "valid": False, "error": "No digits found in input.",
        }

    # Pre-validate length range (using everything entered)
    if len(all_digits) < _MIN_PHONE_DIGITS:
        return {
            "original": original, "cleaned": all_digits, "digits_only": all_digits,
            "country_code": None, "length": len(all_digits),
            "valid": False,
            "error": f"Too short — phone numbers need at least {_MIN_PHONE_DIGITS} digits.",
        }
    if len(all_digits) > _MAX_PHONE_DIGITS:
        return {
            "original": original, "cleaned": all_digits[-_MAX_LOCAL_DIGITS:],
            "digits_only": all_digits,
            "country_code": None, "length": len(all_digits),
            "valid": False,
            "error": f"Too long — phone numbers can be at most {_MAX_PHONE_DIGITS} digits.",
        }

    cleaned = all_digits
    detected_cc: Optional[str] = None

    # IDD prefix '00' (e.g. 00919876543210) is equivalent to '+91...' — strip it.
    work = all_digits
    if work.startswith("00") and len(work) > 12:
        work = work[2:]

    # Try to strip a country code from the front IF length > 10
    # (an Indian/US local number is exactly 10; longer suggests a code).
    if len(work) > 10:
        for cc in _COUNTRY_CODES:
            if work.startswith(cc):
                remainder = work[len(cc):]
                # Local number must be 7–11 digits to plausibly be a phone
                if _MIN_PHONE_DIGITS <= len(remainder) <= 11:
                    cleaned = remainder
                    detected_cc = cc
                    break

    # Edge case: leading 0 in some local formats (UK: 07xxx, France: 06xxx)
    # — keep as-is (it's still the dialled local number).

    return {
        "original": original,
        "cleaned": cleaned,
        "digits_only": all_digits,
        "country_code": detected_cc,
        "length": len(cleaned),
        "valid": True,
        "error": "",
    }


_VEHICLE_ALPHA_RE = re.compile(r"[A-Za-z0-9]+")


def normalize_vehicle_input(raw: str) -> Dict[str, Any]:
    """Clean a vehicle registration plate.

    Plates vary wildly: `MH 12 AB 1234`, `7ABC123`, `AB12 CDE`,
    `京A 12345`. We keep alphanumerics, drop spaces/dashes, and
    extract digits for numerology. Letters are preserved for display.
    """
    original = str(raw or "")
    alpha_chunks = _VEHICLE_ALPHA_RE.findall(original.upper())
    cleaned = "".join(alpha_chunks)
    digits = _digits_of(original)

    if not cleaned:
        return {
            "original": original, "cleaned": "", "digits_only": "",
            "length": 0, "valid": False,
            "error": "No alphanumeric characters found.",
        }
    if len(cleaned) < 3:
        return {
            "original": original, "cleaned": cleaned, "digits_only": digits,
            "length": len(cleaned), "valid": False,
            "error": "Too short — plates need at least 3 characters.",
        }
    if len(cleaned) > 15:
        return {
            "original": original, "cleaned": cleaned, "digits_only": digits,
            "length": len(cleaned), "valid": False,
            "error": "Too long — plates can be at most 15 characters.",
        }
    if not digits:
        return {
            "original": original, "cleaned": cleaned, "digits_only": "",
            "length": len(cleaned), "valid": False,
            "error": "Plate has no digits — numerology needs at least one digit.",
        }

    return {
        "original": original,
        "cleaned": cleaned,
        "digits_only": digits,
        "length": len(cleaned),
        "valid": True,
        "error": "",
    }


_HOUSE_ALLOWED_RE = re.compile(r"[A-Za-z0-9\-]+")


def normalize_house_input(raw: str) -> Dict[str, Any]:
    """Clean a house / flat identifier (e.g. '204', 'B-204', '12A')."""
    original = str(raw or "").strip()
    chunks = _HOUSE_ALLOWED_RE.findall(original.upper())
    cleaned = "-".join(chunks) if len(chunks) > 1 else (chunks[0] if chunks else "")
    digits = _digits_of(original)

    if not cleaned:
        return {
            "original": original, "cleaned": "", "digits_only": "",
            "length": 0, "valid": False,
            "error": "No valid characters found.",
        }
    if len(cleaned) > 10:
        return {
            "original": original, "cleaned": cleaned, "digits_only": digits,
            "length": len(cleaned), "valid": False,
            "error": "Too long — house numbers can be at most 10 characters.",
        }
    if not digits:
        return {
            "original": original, "cleaned": cleaned, "digits_only": "",
            "length": len(cleaned), "valid": False,
            "error": "No digits in input — numerology needs at least one digit.",
        }
    return {
        "original": original,
        "cleaned": cleaned,
        "digits_only": digits,
        "length": len(cleaned),
        "valid": True,
        "error": "",
    }


def normalize_input(raw: str, kind: str) -> Dict[str, Any]:
    """Dispatch helper — picks the right normalizer for the input kind."""
    if kind == "mobile":
        return normalize_phone_input(raw)
    if kind == "vehicle":
        return normalize_vehicle_input(raw)
    if kind == "house":
        return normalize_house_input(raw)
    # Fallback — just digit-strip
    digits = _digits_of(raw)
    return {
        "original": str(raw or ""),
        "cleaned": digits, "digits_only": digits,
        "length": len(digits),
        "valid": bool(digits),
        "error": "" if digits else "No digits found.",
    }


def _verdict(reduced: int, driver: int | None) -> tuple[str, str]:
    if not driver:
        return "NEUTRAL", "No driver supplied for comparison."
    if reduced == driver:
        return "EXCELLENT", f"Matches your Driver ({driver}) — high alignment."
    if reduced in (NUMBER_FRIENDS.get(driver) or []):
        return "FAVOURABLE", f"Syncs with Driver {driver} (friendly number pattern)."
    if reduced in (NUMBER_ENEMIES.get(driver) or []):
        return "AVOID", f"Friction with Driver {driver} (high-mismatch pattern)."
    return "NEUTRAL", f"Neutral relative to Driver {driver}."


def _conductor_note(reduced: int, driver: int | None, conductor: int | None) -> str:
    if not conductor or reduced == driver:
        return ""
    if reduced == conductor:
        return f"Also matches Conductor ({conductor}) — reinforced balance."
    if reduced in (NUMBER_FRIENDS.get(conductor) or []):
        return f"Friendly to Conductor ({conductor})."
    if reduced in (NUMBER_ENEMIES.get(conductor) or []):
        return f"Tension with Conductor ({conductor})."
    return ""


def _communication_rhythm(kind: str, digits: List[int], rhythm: str) -> str:
    if kind == "mobile":
        return (
            f"{rhythm} — predicts notification load, reply speed, and whether "
            "you batch messages or react in bursts."
        )
    if kind == "vehicle":
        return f"{rhythm} — maps to trip pacing, stop frequency, and maintenance cadence."
    return f"{rhythm} — reflects household routine stability and how often the home 'resets'."


def _emotional_intensity(digits: List[int]) -> str:
    if not digits:
        return "Low data"
    highs = sum(1 for d in digits if d in (7, 8, 9))
    lows = sum(1 for d in digits if d in (2, 6))
    ratio = highs / len(digits)
    if ratio >= 0.45:
        return "High — reactive tone, urgency spikes, heated exchanges more likely."
    if lows >= len(digits) * 0.45:
        return "Moderate-low — calmer baseline, slower escalation under stress."
    return "Balanced — mix of calm and spike digits; context decides tone."


def _memory_impact(value: str, kind: str) -> str:
    ds = [int(c) for c in value if c.isdigit()]
    if len(ds) < 4:
        return "Short identifier — low memorability; people rely on contacts/saved labels."
    last4 = "".join(str(d) for d in ds[-4:])
    repeats = len(set(ds[-4:])) < 4
    if kind == "mobile":
        base = f"Last-4 block <b>{last4}</b> is what callers recall from SMS previews."
    elif kind == "vehicle":
        base = f"Last-4 <b>{last4}</b> is what parking/security staff remember."
    else:
        base = f"Last digits <b>{last4}</b> shape how guests remember your address."
    if repeats:
        base += " Repeating digits increase stickiness but can feel 'heavy'."
    return base


def _behavioral_influence(reduced: int, dom: int, dom_pct: float) -> str:
    theme, behavior = digit_trait(reduced)
    dom_theme, _ = digit_trait(dom)
    return (
        f"Reduced total <b>{reduced}</b> ({theme}) nudges {behavior}. "
        f"Dominant digit <b>{dom}</b> ({dom_theme}) appears {int(dom_pct * 100)}% of the time — "
        "that is the habit people experience most."
    )


def _kind_tip(kind: str, verdict: str) -> str:
    tips = {
        ("mobile", "AVOID"): "Prefer a new number whose digit-sum syncs with your Driver.",
        ("mobile", "EXCELLENT"): "Use for priority calls; keep notifications organized.",
        ("mobile", "FAVOURABLE"): "Good daily driver number; pair with calendar batching.",
        ("vehicle", "AVOID"): "Extra maintenance discipline; consider plate change at renewal.",
        ("vehicle", "EXCELLENT"): "Strong travel rhythm; schedule long trips on power days.",
        ("vehicle", "FAVOURABLE"): "Reliable enough for daily commute with routine servicing.",
        ("house", "AVOID"): "Use clear signage + calm entry routine to offset friction.",
        ("house", "EXCELLENT"): "Lean into home as a focus hub; keep entrance organized.",
        ("house", "FAVOURABLE"): "Stable base; small layout tweaks amplify comfort.",
    }
    return tips.get((kind, verdict), "Neutral pattern — consistency matters more than rituals.")


def analyze_number_string(
    value: str,
    *,
    kind: str,
    driver: int | None = None,
    conductor: int | None = None,
) -> Dict[str, Any]:
    """Full psychometric asset report for PDF/mobile/vehicle/house sections.

    Input is normalized FIRST (country code stripped for phones,
    alphanumerics preserved for plates/houses) so the numerology engine
    always sees a consistent digit string regardless of how the user
    typed the number.
    """
    norm = normalize_input(value, kind)
    if not norm.get("valid"):
        return {
            "ok": False,
            "error": norm.get("error") or f"Invalid {kind} input.",
            "input": value,
            "normalized": norm,
        }

    # For phones: use the stripped local number (post country code).
    # For vehicle/house: use the full digit string from the cleaned value.
    calc_digit_source = norm["cleaned"] if kind == "mobile" else norm["digits_only"]
    digits = [int(c) for c in calc_digit_source if c.isdigit()]
    if not digits:
        return {
            "ok": False,
            "error": f"No digits in {kind} value after normalization.",
            "input": value,
            "normalized": norm,
        }

    # Engine uses the cleaned display string (no spaces / no country code
    # leakage in PDF chains).
    display_value = norm["cleaned"]
    total = sum(digits)
    reduced = reduce_number(total)
    verdict, verdict_reason = _verdict(reduced, driver)
    dom, dom_pct = dominance_score(digits)
    psych = analyze_identifier(display_value, kind, driver or 0, conductor or 0)
    bad, good = detect_digit_pairs(display_value)

    chain = " + ".join(str(d) for d in digits) + f" = {total}"
    if total != reduced:
        cur = total
        steps = []
        while cur > 9:
            cur = sum(int(d) for d in str(cur))
            steps.append(cur)
        chain += " → " + " → ".join(str(s) for s in steps)

    balance = stability_score(digits, driver or reduced)
    rhythm = rhythm_pattern(digits)

    return {
        "ok": True,
        "kind": kind,
        "title": {"mobile": "Mobile Number", "vehicle": "Vehicle Number", "house": "House Number"}.get(
            kind, "Number"
        ),
        "input": value,
        "input_display": display_value,
        "normalized": norm,
        "digits": digits,
        "total": total,
        "reduced": reduced,
        "archetype": archetype_for(reduced),
        "calculation_chain": chain,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "conductor_note": _conductor_note(reduced, driver, conductor),
        "energy": SINGLE_DIGIT_SHORT.get(reduced, ""),
        "tip": _kind_tip(kind, verdict),
        "repeating_digits": repeating_digit_report(digits),
        "missing_digits": missing_numbers_profile(digits),
        "dominant_digit": dom,
        "dominance_pct": dom_pct,
        "balance_score": balance,
        "stability_score": balance,
        "communication_rhythm": _communication_rhythm(kind, digits, rhythm),
        "emotional_intensity": _emotional_intensity(digits),
        "memory_impact": _memory_impact(display_value, kind),
        "behavioral_influence": _behavioral_influence(reduced, dom, dom_pct),
        "digit_positions": digit_position_rows(display_value),
        "pairs_conflict": bad,
        "pairs_harmony": good,
        "sync_code": rel_code(driver or reduced, reduced) if driver else "N",
        "psych": psych,
    }
