"""
Inter-room adjacency Vastu rules — classical-text-driven.

Engine accepts an optional list:
  room_adjacencies: [
    {"a": "kitchen",  "b": "bathroom", "relation": "shared_wall"},
    {"a": "pooja",    "b": "bathroom", "relation": "above"},          # bathroom above pooja
    {"a": "bedroom",  "b": "bathroom", "relation": "door_facing"},    # dwar-vedh
    ...
  ]

Returns a list of finding dicts, each with verdict / severity / reason / classical_ref / remedy.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple

# Each rule: ((roomA, roomB, relation) -> finding template). Order in pair is irrelevant
# at lookup time — we normalise pairs alphabetically.
_RULES: Dict[Tuple[str, str, str], Dict[str, Any]] = {
    ("bathroom", "kitchen", "shared_wall"): {
        "title":         "Agni-Jal Dosh (kitchen-bathroom shared wall)",
        "verdict":       "Avoid",
        "severity":      "major",
        "reason_en":     "Kitchen (Agni / fire) and bathroom (Jal / water) sharing a wall create elemental conflict — Vastu Saar Ch.11 calls this 'Agni-Jal dosh' which weakens both digestion (kitchen) and household drainage (bathroom).",
        "reason_hi":     "Kitchen (Agni) aur bathroom (Jal) ka common wall = Agni-Jal dosh. Vastu Saar Ch.11 ke anusaar paachan aur pravah dono kamzor hote hain.",
        "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.11"},
        "remedy_en":     "Move the bathroom or kitchen so they don't share a wall. If structural change isn't possible, install a thick partition / cabinet wall and place a copper plate on the kitchen-side wall to balance fire-water elements.",
        "remedy_hi":     "Bathroom ya kitchen me se kisi ek ko shift karein taaki common wall na ho. Agar nahi ho sakta, kitchen wali deewar par tambe ki plate lagayein.",
    },
    ("bathroom", "pooja", "above"): {
        "title":         "Bathroom above Pooja room (mahadosh)",
        "verdict":       "Avoid",
        "severity":      "critical",
        "reason_en":     "A bathroom directly above the pooja room is classified as mahadosh in Brihat Samhita 53.95 — sacred space cannot have flowing waste matter overhead. It blocks devta-shakti and invites instability.",
        "reason_hi":     "Pooja room ke upar bathroom mahadosh hai. Brihat Samhita 53.95 ke anusaar devta-shakti rok jaati hai.",
        "classical_ref": {"type": "vastu", "source": "Brihat Samhita 53.95"},
        "remedy_en":     "Relocate the pooja room to a different floor or position so nothing impure sits above it. Until then, install a copper or brass yantra plate on the pooja room ceiling and keep the upper bathroom unused if possible.",
        "remedy_hi":     "Pooja room ko alag floor / sthaan par shift karein. Tab tak chhat par tambe ka yantra lagayein.",
    },
    ("bathroom", "pooja", "below"): {
        "title":         "Bathroom below Pooja room",
        "verdict":       "Adjustment Needed",
        "severity":      "moderate",
        "reason_en":     "Bathroom directly below a pooja room is less severe than bathroom-above, but still drains the pooja room's positive energy downward.",
        "reason_hi":     "Pooja room ke neeche bathroom — aboveground se kam, par positive energy neeche kheench leta hai.",
        "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.11"},
        "remedy_en":     "Place a thick rug and a Sri-yantra under the pooja altar. Avoid using the bathroom during pooja hours.",
        "remedy_hi":     "Pooja sthaan ke neeche moti chatai aur Sri-yantra rakhein.",
    },
    ("bathroom", "bedroom", "door_facing"): {
        "title":         "Dwar-vedh (bedroom door facing bathroom door)",
        "verdict":       "Adjustment Needed",
        "severity":      "moderate",
        "reason_en":     "Two doors directly facing each other across a corridor create 'dwar-vedh' — Mansara Ch.9 says this leaks the bedroom's restorative energy into the bathroom drainage.",
        "reason_hi":     "Bedroom aur bathroom ke darwaze aamne-saamne hain — Mansara Ch.9 ke anusaar dwar-vedh dosh.",
        "classical_ref": {"type": "vastu", "source": "Mansara Ch.9"},
        "remedy_en":     "Keep the bathroom door closed when not in use. Hang a small wind-chime or a beaded curtain between the two doors to break the energy line.",
        "remedy_hi":     "Bathroom ka darwaza band rakhein. Beech me wind-chime / ladi ka parda lagayein.",
    },
    ("kitchen", "pooja", "above"): {
        "title":         "Kitchen above Pooja room",
        "verdict":       "Adjustment Needed",
        "severity":      "moderate",
        "reason_en":     "Cooking heat directly above the pooja altar over-activates Agni element and dries the calm Sattva needed for worship.",
        "reason_hi":     "Pooja sthaan ke upar kitchen — Agni adhik chhalakti hai, Sattva soshit hota hai.",
        "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.10"},
        "remedy_en":     "Use the kitchen for cold prep / morning cooking only when pooja is in session. Place a cooling water pot in the NE of the pooja room.",
        "remedy_hi":     "Pooja ke samay garam khaana banane se bachein. Pooja room ke NE me jal-paatra rakhein.",
    },
    ("entrance", "bathroom", "door_facing"): {
        "title":         "Main entrance facing bathroom door",
        "verdict":       "Avoid",
        "severity":      "major",
        "reason_en":     "The main entrance is the mouth of Lakshmi's energy. A bathroom door facing it directly drains incoming wealth-energy — Vastu Saar Ch.6.",
        "reason_hi":     "Mukhya darwaze ke saamne bathroom ka darwaza Lakshmi-urja ko bahar nikaal deta hai.",
        "classical_ref": {"type": "vastu", "source": "Vastu Saar Ch.6"},
        "remedy_en":     "Always keep the bathroom door shut. Hang a beaded curtain or place a tall plant between the entrance and the bathroom door.",
        "remedy_hi":     "Bathroom ka darwaza hamesha band rakhein. Beech me lambi pattedaar plant / parda lagayein.",
    },
}


def _norm_pair(a: str, b: str, rel: str) -> Tuple[str, str, str]:
    a = (a or "").strip().lower().replace("-", "_")
    b = (b or "").strip().lower().replace("-", "_")
    rel = (rel or "").strip().lower()
    pair = tuple(sorted([a, b]))
    return (pair[0], pair[1], rel)


def evaluate_adjacencies(adjacencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a list of human-ready finding dicts for each adjacency clash."""
    if not isinstance(adjacencies, list):
        return []
    findings: List[Dict[str, Any]] = []
    for adj in adjacencies:
        if not isinstance(adj, dict): continue
        key = _norm_pair(adj.get("a", ""), adj.get("b", ""), adj.get("relation", ""))
        rule = _RULES.get(key)
        if not rule: continue
        findings.append({
            "rooms":         [key[0], key[1]],
            "relation":      key[2],
            "title":         rule["title"],
            "verdict":       rule["verdict"],
            "severity":      rule["severity"],
            "reason_en":     rule["reason_en"],
            "reason_hi":     rule["reason_hi"],
            "classical_ref": rule["classical_ref"],
            "remedy_en":     rule["remedy_en"],
            "remedy_hi":     rule["remedy_hi"],
        })
    return findings
