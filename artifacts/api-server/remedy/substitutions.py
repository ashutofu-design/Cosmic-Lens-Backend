"""Remedy substitutions — auto-swap items based on user constraints.

Pulls UCML user_facts (vegetarian, allergies, no_temple, no_fast,
location_city, etc) and replaces incompatible remedies with practical
alternatives, so the engine NEVER blocks the user with "you can't do
this remedy".
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# Substitution rules. Each rule:
#   (constraint_key, target_substring_in_text, replacement_text)
_RULES = [
    # vegetarian users
    ("vegetarian",       "non-veg",      "skip — keep vegetarian"),
    ("vegan",            "milk",         "almond/soy milk"),
    ("vegan",            "ghee",         "coconut oil / sesame oil"),
    ("vegan",            "Pearl",        "Moonstone (vegan-aligned alternative for Moon)"),
    ("vegan",            "Coral",        "Red Carnelian (vegan alternative for Mars)"),
    # users who explicitly say can't fast (medical/diabetes/pregnancy)
    ("no_fast",          "vrat",         "30-min mantra + light fruit-only meal (skip strict fast)"),
    ("no_fast",          "fast",         "light fruit-only meal (no strict fast)"),
    # users who can't visit temple (homebound, foreign location, time)
    ("no_temple",        "at temple",    "at home altar OR feed a needy person"),
    ("no_temple",        "to a brahmin", "to any needy person OR online charity"),
    # users with sesame/nut allergy
    ("allergy_sesame",   "sesame",       "(skip — allergy) sunflower seeds"),
    # users with skin sensitivity → no oil massage
    ("skin_sensitive",   "oil massage",  "dry-brush self-massage"),
    # diabetes → reduce sweet donations advice
    ("diabetes",         "jaggery",      "small token jaggery (only as donation, not consumption)"),
]


def apply_substitutions(remedies: List[Dict[str, Any]],
                          user_facts: Optional[Dict[str, Any]]) -> tuple[
                              List[Dict[str, Any]], List[Dict[str, str]]
                          ]:
    """Apply all matching substitutions to the remedy list.

    Returns (modified_remedies, applied_swaps).
    `applied_swaps` is a list of {constraint, original_snippet, replacement}
    so the locked-facts layer can show the user "we adjusted X because
    we know you're vegetarian".
    """
    if not remedies:
        return remedies, []
    facts = user_facts or {}
    applied: List[Dict[str, str]] = []

    out: List[Dict[str, Any]] = []
    for r in remedies:
        # Deep-but-shallow copy of nested tier dicts so we don't mutate
        # the source catalog.
        r2 = dict(r)
        for tier_key in ("practical", "ayurvedic", "vedic"):
            tier = r2.get(tier_key)
            if not isinstance(tier, dict):
                continue
            tier2 = dict(tier)
            for ck, needle, replacement in _RULES:
                if not facts.get(ck):
                    continue
                for fk, fv in list(tier2.items()):
                    if not isinstance(fv, str):
                        continue
                    # Case-insensitive find then preserve case-of-original
                    # by replacing all matching occurrences. Architect-fix
                    # (May 6 2026): annotation-only was a foot-gun — old
                    # text remained visible. Now we actually swap the
                    # substring with the replacement (parenthesised so
                    # the user sees what was changed and why).
                    lower = fv.lower()
                    nlow  = needle.lower()
                    if nlow not in lower:
                        continue
                    # Build the new text by case-insensitive replacement
                    new_text = ""
                    i = 0
                    while True:
                        j = fv.lower().find(nlow, i)
                        if j < 0:
                            new_text += fv[i:]
                            break
                        new_text += fv[i:j] + f"({replacement} — adapted for {ck})"
                        i = j + len(needle)
                    tier2[fk] = new_text
                    applied.append({
                        "constraint":  ck,
                        "original":    needle,
                        "replacement": replacement,
                        "field":       f"{tier_key}.{fk}",
                    })
            r2[tier_key] = tier2
        out.append(r2)
    return out, applied
