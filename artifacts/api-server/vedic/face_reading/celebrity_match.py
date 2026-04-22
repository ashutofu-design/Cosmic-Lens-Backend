"""
Celebrity Archetype Match — curated mapping of archetype + dominant trait
to well-known Indian/global personalities with similar vibe.

This is reference inspiration, NOT a claim that the user IS this celebrity.
Mapping uses Big-5 archetype labels from personality.py + dominant element.
"""
from __future__ import annotations
from typing import Dict, List


# ── Curated celebrity library by archetype × element ──────────────────────
# Each entry: (name, why_hi, signature_trait_hi)
_CELEBS = {
    "Resilient": {
        "agni":    [("M.S. Dhoni", "Pressure me sabse calm — 'Captain Cool' isi liye bola jaata hai.",
                     "Crisis-time clarity"),
                    ("Virat Kohli", "Aag bhi hai, discipline bhi — high E + high C + low N ka classic mix.",
                     "Aggressive focus")],
        "prithvi": [("Ratan Tata", "Reliable, principled, durable leadership — earth ka shaant power.",
                     "Long-game wisdom"),
                    ("Sundar Pichai", "Calm under pressure, deeply analytical, no drama leadership.",
                     "Steady stewardship")],
        "vayu":    [("Shah Rukh Khan", "High energy + warmth + adaptability — vayu ka classic charm.",
                     "Charismatic adaptability"),
                    ("Priyanka Chopra", "Global mover, multi-domain, never stuck in one box.",
                     "Reinvention engine")],
        "jal":     [("A.R. Rahman", "Deep emotional intelligence + steady creative output for decades.",
                     "Quiet creative depth"),
                    ("Deepika Padukone", "Outwardly composed, inwardly deeply feeling.",
                     "Emotional poise")],
        "akash":   [("APJ Abdul Kalam", "Visionary, calm, big-picture thinker — akash ka teacher energy.",
                     "Inspirational vision")],
    },
    "Steadfast": {
        "prithvi": [("Ratan Tata", "Decades of consistent value-driven leadership.", "Principled patience"),
                    ("Saina Nehwal", "Quiet grind, year after year, no shortcuts.", "Disciplined endurance")],
        "agni":    [("Saurav Ganguly", "Stubborn fire + loyal to team — high A + high C combo.", "Loyal aggression"),
                    ("P.V. Sindhu", "Disciplined fire — silent killer on court.", "Quiet warrior")],
        "vayu":    [("Anushka Sharma", "Steady values + adaptable career arc.", "Grounded versatility")],
        "jal":     [("Vidya Balan", "Soft strength — chooses depth over flash.", "Emotional reliability")],
        "akash":   [("Sadhguru", "Consistent teaching, deep frame, calm authority.", "Wisdom-keeper energy")],
    },
    "Explorer": {
        "vayu":    [("Elon Musk", "Multi-domain explorer, novelty-driven, high-risk appetite.", "Frontier obsession"),
                    ("Ranveer Singh", "Performative explorer — style, music, films, all genres.", "Bold reinvention")],
        "agni":    [("Kangana Ranaut", "Bold, opinionated, unafraid of controversy — fire + openness.", "Fearless voice"),
                    ("Nikhil Kamath", "Risk-taker, public thinker, unconventional path.", "Independent intellect")],
        "akash":   [("Steve Jobs", "Pure visionary openness — saw products others couldn't imagine.", "Aesthetic vision"),
                    ("Jiddu Krishnamurti", "Boundary-less thinker, rejected all frames.", "Pure inquiry")],
        "jal":     [("Imtiaz Ali", "Emotional explorer — every film a new emotional landscape.", "Romantic seeker")],
        "prithvi": [("Sachin Tendulkar", "Quiet explorer of cricket craft — earth grounding + openness.", "Master craftsman")],
    },
    "Warm_Connector": {
        "vayu":    [("Shah Rukh Khan", "Room ka mood badal deta hai — vayu ki warmth at scale.", "Mass connector"),
                    ("Alia Bhatt", "Universal warmth, easy likability across demographics.", "Effortless rapport")],
        "jal":     [("Aishwarya Rai", "Soft + warm + emotionally attuned classic.", "Grace under spotlight"),
                    ("Mahesh Babu", "Quiet warmth, family man, fan-loved.", "Genuine warmth")],
        "agni":    [("Hrithik Roshan", "Charismatic intensity + genuine warmth combo.", "Passionate charm")],
        "prithvi": [("Sonu Sood", "Warm + reliable + grounded — earth-connector.", "Trusted helper")],
        "akash":   [("Mother Teresa", "Boundless compassion, universal warmth.", "Unconditional care")],
    },
    "Disciplined_Performer": {
        "prithvi": [("Saina Nehwal", "Decades of disciplined practice without drama.", "Quiet excellence"),
                    ("N.R. Narayana Murthy", "Disciplined builder, no shortcuts, principle-driven.", "Process integrity")],
        "agni":    [("Virat Kohli", "Disciplined aggression — daily routine + match-day fire.", "Process intensity"),
                    ("Mary Kom", "Disciplined fighter — fire focused into routine.", "Forged warrior")],
        "vayu":    [("Mukesh Ambani", "Adaptable + disciplined builder — pivots executed precisely.", "Strategic execution")],
        "jal":     [("Lata Mangeshkar", "Decades of disciplined craft + emotional depth.", "Devotional discipline")],
        "akash":   [("Visvesvaraya", "Disciplined visionary — engineered modern India.", "Architect mind")],
    },
    "Sensitive_Creative": {
        "jal":     [("A.R. Rahman", "Sensitivity channeled into creative depth.", "Emotional artistry"),
                    ("Imtiaz Ali", "Feels everything, films it.", "Deep romantic")],
        "vayu":    [("Anurag Kashyap", "Creative restlessness, emotional intensity.", "Bold storyteller")],
        "akash":   [("Rabindranath Tagore", "Sensitive visionary — poet, philosopher, painter.", "Renaissance soul"),
                    ("Vincent van Gogh", "Pure sensitive-creative archetype.", "Emotive vision")],
        "agni":    [("Kishore Kumar", "Volatile genius — emotional fire channeled into art.", "Untamed creative")],
        "prithvi": [("Satyajit Ray", "Sensitive observer + grounded craftsman.", "Quiet auteur")],
    },
    "Overcontrolled": {
        "prithvi": [("Manmohan Singh", "Reserved, careful, principled — overcontrolled in the best way.", "Quiet competence")],
        "jal":     [("Rahul Dravid", "Held back outwardly, deeply intense inwardly. 'The Wall'.", "Reserved depth"),
                    ("Anand Bakshi", "Quiet craftsman behind the spotlight.", "Behind-scenes mastery")],
        "akash":   [("Ramana Maharshi", "Inward-turned, minimal outer expression, infinite inner.", "Silent depth")],
        "vayu":    [("Anupam Kher (early career)", "Reserved professional, controlled craft.", "Studied performer")],
        "agni":    [("Anil Kumble", "Internalized fire — calm exterior, lethal focus.", "Cold-storage fire")],
    },
    "Undercontrolled": {
        "agni":    [("Sushant Singh Rajput (early)", "Restless, exploratory, emotionally raw.", "Restless seeker"),
                    ("Sanjay Dutt", "Spontaneous, follows impulse, lives loud.", "Untamed impulse")],
        "vayu":    [("Ranbir Kapoor (early)", "Spontaneous, mood-led, charming chaos.", "Free-spirit charm")],
        "jal":     [("Guru Dutt", "Emotionally raw, unable to hide pain.", "Unfiltered feeling")],
        "akash":   [("Osho", "Provocative, boundary-breaking thinker.", "Disruptive visionary")],
        "prithvi": [("Yuvraj Singh", "Earth + fire mix — unpredictable game-changer.", "Wild card brilliance")],
    },
    "Balanced": {
        "prithvi": [("Mahendra Singh Dhoni (off-field)", "Balanced, no-drama, quietly competent.", "Everyman wisdom")],
        "vayu":    [("Anushka Sharma", "Balanced public persona, multi-faceted.", "Balanced versatility")],
        "agni":    [("Ravi Shastri", "Balanced fire + groundedness.", "Steady commentator")],
        "jal":     [("Tabu", "Balanced presence, depth without drama.", "Quiet substance")],
        "akash":   [("Amartya Sen", "Balanced thinker, multi-domain wisdom.", "Quiet polymath")],
    },
}
# Backward-compat alias (older callers still pass "Average")
_CELEBS["Average"] = _CELEBS["Balanced"]


# Element key → user-visible English name (single source of truth)
_ELEMENT_DISPLAY = {
    "agni":    "Fire",
    "prithvi": "Earth",
    "vayu":    "Air",
    "jal":     "Water",
    "akash":   "Ether",
    "fire":    "Fire",
    "earth":   "Earth",
    "air":     "Air",
    "water":   "Water",
    "ether":   "Ether",
    "wood":    "Wood",
    "metal":   "Metal",
}


def _display_element(elem: str) -> str:
    return _ELEMENT_DISPLAY.get((elem or "").strip().lower(), (elem or "").title() or "Balanced")


_ELEMENT_KEYS = ["agni", "prithvi", "vayu", "jal", "akash"]


def get_celebrity_matches(archetype: str, dominant_element: str,
                          n: int = 3) -> List[Dict]:
    """Return up to n curated celebrity matches for the given archetype × element."""
    elem = (dominant_element or "").lower().strip()
    arche = archetype if archetype in _CELEBS else "Balanced"
    bucket = _CELEBS.get(arche, {})

    matches: List = []
    if elem in bucket:
        matches.extend(bucket[elem])
    # Top-up from other elements of same archetype
    for ek in _ELEMENT_KEYS:
        if ek == elem: continue
        for entry in bucket.get(ek, []):
            if entry not in matches:
                matches.append(entry)
            if len(matches) >= n + 2: break
        if len(matches) >= n + 2: break
    # Fallback to Balanced bucket if still empty
    if not matches:
        for ek in _ELEMENT_KEYS:
            for entry in _CELEBS["Balanced"].get(ek, []):
                matches.append(entry)
                if len(matches) >= n: break
            if len(matches) >= n: break

    return [
        {"name": e[0], "why_hi": e[1], "signature_trait_hi": e[2]}
        for e in matches[:n]
    ]


def build_celebrity_section(personality_engine: Dict,
                             samudrika_engine: Dict) -> Dict:
    """Build celebrity-match section content."""
    arche = (personality_engine.get("archetype") or {}).get("label") or "Balanced"
    if arche == "Average":
        arche = "Balanced"
    elem = ((samudrika_engine.get("element_profile") or {}).get("dominant")
            or (samudrika_engine.get("element_profile") or {}).get("dominant_element")
            or "prithvi")
    elem_display = _display_element(elem)

    matches = get_celebrity_matches(arche, elem, n=3)
    intro = (
        f"Tumhara archetype <b>{arche}</b> aur dominant tatva <b>{elem_display}</b> "
        "ke combination se milte-julte 3 famous personalities. "
        "Yeh inspiration ke liye hai — tumhari personality bhi inhi jaisi structural pattern follow karti hai. "
        "Inn logon ka journey aur public persona study karke tumhe apni potential ki jhalak milegi."
    )
    return {
        "archetype":         arche,
        "dominant_element":  elem,
        "intro_para":        intro,
        "matches":           matches,
        "disclaimer_hi":     (
            "Note: Yeh sirf personality-pattern similarity hai, koi prediction ya guarantee nahi. "
            "Inka path tumhara path nahi hai — par inka mindset study karna helpful ho sakta hai."
        ),
    }
