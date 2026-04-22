"""
Consistency Layer — single source of truth + post-build normalizer for the
Face Intelligence Report.

Runs ONCE after all sections are assembled. Responsibilities:

  1. final_scores  — single source of truth for element / archetype / OCEAN /
                     dominant trait. Every downstream consumer (PDF, mobile,
                     synthesis) should read from here, never re-derive.
  2. clean_internal_labels — strips internal codes that leak into prose,
                     e.g.  "A-driven", "C-driven", "Cosmic Vision",
                     "AI-powered", and replaces them with friendly labels.
  3. normalize_section_keys — adds backward-compat aliases so narrative
                     writers and PDF templates don't break when producer
                     keys evolve (e.g.  best_match  ←  best_match_hi).
  4. validate_consistency — diff-checks element / archetype across all
                     sections and logs any mismatch (does not raise).
  5. apply_strict_bands — clamp helper to enforce no-overlap classification
                     bands (used by writers that classify scores into
                     low/mid/high).

Pure-Python, zero deps, idempotent. Safe to call multiple times.
"""
from __future__ import annotations
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ──────────────────────────────────────────────────────────────────────────
#  Brand & internal-code cleanup
# ──────────────────────────────────────────────────────────────────────────
OCEAN_LETTER_TO_LABEL = {
    "O": "Curiosity",
    "C": "Discipline",
    "E": "Energy",
    "A": "Warmth",
    "N": "Sensitivity",
}

OCEAN_NAME_TO_LABEL = {
    "openness":          "Curiosity",
    "conscientiousness": "Discipline",
    "extraversion":      "Energy",
    "agreeableness":     "Warmth",
    "neuroticism":       "Sensitivity",
    "balanced":          "Balance",
}

# Brand strings that must NEVER appear in user-facing prose.
# Order matters — longer strings first so we don't half-replace.
BANNED_PHRASES: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bArtificial Intelligence\b", re.I), "Cosmic Intelligence"),
    (re.compile(r"\bAI[- ]powered\b",            re.I), "Cosmic Intelligence-powered"),
    (re.compile(r"\bAI[- ]driven\b",             re.I), "Cosmic Intelligence-driven"),
    (re.compile(r"\bAI\s+analysis\b",            re.I), "Cosmic Intelligence analysis"),
    (re.compile(r"\bCosmic Vision\b",            re.I), "Cosmic Lens"),
    # Bare "AI" as a standalone word (kept last, narrowly scoped).
    (re.compile(r"(?<![A-Za-z])AI(?![A-Za-z])"),       "Cosmic Intelligence"),
]

# Internal OCEAN-letter leaks like  "A-driven", "C-driven core"
_OCEAN_DRIVEN = re.compile(
    r"\b([OCEAN])\s*-\s*driven\b"
)


def clean_internal_labels(text: str) -> str:
    """Strip internal codes / banned brand phrases from a single string."""
    if not isinstance(text, str) or not text:
        return text

    # 1. OCEAN single-letter "X-driven" → "Curiosity-driven" etc.
    def _repl(m: re.Match) -> str:
        return f"{OCEAN_LETTER_TO_LABEL.get(m.group(1).upper(), 'Balance')}-driven"
    text = _OCEAN_DRIVEN.sub(_repl, text)

    # 2. Bare lowercase trait names used as "{trait}-driven" template glue.
    for name, label in OCEAN_NAME_TO_LABEL.items():
        text = re.sub(
            rf"\b{name}\s*-\s*driven\b",
            f"{label}-driven",
            text,
            flags=re.I,
        )

    # 3. Banned brand phrases.
    for pat, repl in BANNED_PHRASES:
        text = pat.sub(repl, text)

    return text


def _walk(node: Any, fn) -> Any:
    """Recursively apply `fn` to every string leaf in a JSON-shaped tree.

    Handles dict / list / tuple / set / str. Other types (int, float, None,
    bool) are passed through unchanged.
    """
    if isinstance(node, str):
        return fn(node)
    if isinstance(node, list):
        return [_walk(x, fn) for x in node]
    if isinstance(node, tuple):
        return tuple(_walk(x, fn) for x in node)
    if isinstance(node, set):
        return {_walk(x, fn) for x in node}
    if isinstance(node, dict):
        return {k: _walk(v, fn) for k, v in node.items()}
    return node


def apply_label_cleanup(sections: Dict[str, Any]) -> Dict[str, Any]:
    """In-place cleanup of every string leaf inside the sections dict."""
    for k, v in list(sections.items()):
        sections[k] = _walk(v, clean_internal_labels)
    return sections


# ──────────────────────────────────────────────────────────────────────────
#  Single source of truth — element / archetype / OCEAN
# ──────────────────────────────────────────────────────────────────────────
def _g(d: Optional[Dict], *path, default=None):
    cur = d
    for p in path:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur


def get_dominant_element(engines: Dict) -> str:
    """Canonical element string. Tries every known key, returns Title-case."""
    sam_ep = _g(engines, "samudrika", "element_profile") or {}
    raw = (
        sam_ep.get("dominant_element")
        or sam_ep.get("dominant")
        or sam_ep.get("primary")
        or _g(engines, "samudrika", "dominant_element")
        or "Balanced"
    )
    if not isinstance(raw, str) or not raw.strip():
        return "Balanced"
    # Normalise common Sanskrit/Wu-Xing aliases to canonical Title-case form
    s = raw.strip().lower()
    aliases = {
        "agni": "Fire", "jal": "Water", "vayu": "Air", "akash": "Space",
        "prithvi": "Earth", "wood": "Wood", "fire": "Fire", "earth": "Earth",
        "metal": "Metal", "water": "Water", "balanced": "Balanced",
    }
    return aliases.get(s, raw.strip().title())


def get_archetype(engines: Dict) -> str:
    """Canonical archetype name."""
    a = _g(engines, "personality", "archetype") or {}
    name = (
        a.get("name")
        or a.get("archetype")
        or _g(engines, "personality", "archetype_name")
        or "Balanced"
    )
    if isinstance(name, str) and name.strip():
        return name.strip()
    return "Balanced"


def get_dominant_trait(engines: Dict) -> str:
    """Returns user-facing label (never single-letter code)."""
    raw = _g(engines, "personality", "dominant_trait") or "balanced"
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in OCEAN_NAME_TO_LABEL:
            return OCEAN_NAME_TO_LABEL[s]
        if len(s) == 1 and s.upper() in OCEAN_LETTER_TO_LABEL:
            return OCEAN_LETTER_TO_LABEL[s.upper()]
        return raw.strip()
    return "Balance"


def build_final_scores(engines: Dict) -> Dict[str, Any]:
    """Single source of truth — every downstream consumer reads from here."""
    ocean = _g(engines, "personality", "ocean_summary_scores") or {}

    def _num(v, d=50.0):
        try: return float(v)
        except (TypeError, ValueError): return d

    return {
        "element":          get_dominant_element(engines),
        "archetype":        get_archetype(engines),
        "dominant_trait":   get_dominant_trait(engines),
        "ocean": {
            "openness":          round(_num(ocean.get("openness")), 1),
            "conscientiousness": round(_num(ocean.get("conscientiousness")), 1),
            "extraversion":      round(_num(ocean.get("extraversion")), 1),
            "agreeableness":     round(_num(ocean.get("agreeableness")), 1),
            "neuroticism":       round(_num(ocean.get("neuroticism")), 1),
        },
        "vitality":         round(_num(_g(engines, "health", "vitality_score")), 1),
        "symmetry":         round(_num(_g(engines, "anthropometry", "symmetry_score")), 1),
        "phi_score":        round(_num(_g(engines, "phi", "overall_phi_score")), 1),
        "version":          "consistency_v1",
    }


# ──────────────────────────────────────────────────────────────────────────
#  Section key normalization (backward-compat aliases)
# ──────────────────────────────────────────────────────────────────────────
# Map: section_key  →  list of (alias_key, source_key) to mirror.
# After mirroring, a writer that reads `best_match` will find the value
# even though the producer wrote `best_match_hi`.
_KEY_ALIASES: Dict[str, List[Tuple[str, str]]] = {
    "section_20_compatibility": [
        ("best_match",       "best_match_hi"),
        ("avoid_match",      "avoid_match_hi"),
        ("ideal_partner",    "best_match_hi"),
        ("avoid_partner",    "avoid_match_hi"),
    ],
    "section_10_red_flags": [
        ("red_flags",        "red_flags_hi"),
    ],
    "section_18_action_plan": [
        ("daily_practices",  "daily_actions_hi"),
    ],
    "section_19_improvement_hacks": [
        ("quick_wins",       "hacks_hi"),
    ],
    "section_21_final_truth": [
        ("brutal_truth",     "biggest_mistake_hi"),
        ("must_do",          "must_do_hi"),
        ("closing_truth",    "closing_truth_hi"),
        ("one_line_truth",   "biggest_mistake_hi"),
    ],
}


def normalize_section_keys(sections: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror producer keys to legacy alias keys without overwriting existing values."""
    for sk, aliases in _KEY_ALIASES.items():
        sec = sections.get(sk)
        if not isinstance(sec, dict):
            continue
        for alias, source in aliases:
            if alias in sec and sec[alias]:
                continue  # don't clobber
            if source in sec and sec[source]:
                sec[alias] = sec[source]
    return sections


# ──────────────────────────────────────────────────────────────────────────
#  Strict band classifier (no-overlap)
# ──────────────────────────────────────────────────────────────────────────
def classify_band(score: float, low: float = 40.0, high: float = 60.0,
                  labels: Tuple[str, str, str] = ("low", "medium", "high")) -> str:
    """Strict <low / [low,high] / >high — no overlaps, no gaps."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return labels[1]
    if s < low:  return labels[0]
    if s > high: return labels[2]
    return labels[1]


# ──────────────────────────────────────────────────────────────────────────
#  Consistency validator (logs only, never raises)
# ──────────────────────────────────────────────────────────────────────────
def validate_consistency(sections: Dict[str, Any], final: Dict[str, Any]) -> List[str]:
    """Returns a list of human-readable warnings; empty list = all consistent."""
    warnings: List[str] = []
    elem = (final.get("element") or "").lower()
    arch = (final.get("archetype") or "").lower()

    # Element should match across s5 and s20 (and any other section that mentions it).
    s5 = sections.get("section_5_core_foundation") or {}
    s5_elem = (s5.get("five_element_profile") or "").lower()
    if elem and s5_elem and elem not in s5_elem and s5_elem not in elem:
        warnings.append(f"element mismatch: final={elem!r} s5={s5_elem!r}")

    # Archetype should match between s7, s13.
    s7 = sections.get("section_7_personality_synthesis") or {}
    s13 = sections.get("section_13_archetype") or {}
    s7_arch = (s7.get("archetype") or "").lower()
    s13_arch = (s13.get("archetype_name") or "").lower()
    if arch and s7_arch and arch not in s7_arch and s7_arch not in arch:
        warnings.append(f"archetype mismatch: final={arch!r} s7={s7_arch!r}")
    if arch and s13_arch and arch not in s13_arch and s13_arch not in arch:
        warnings.append(f"archetype mismatch: final={arch!r} s13={s13_arch!r}")

    return warnings


# ──────────────────────────────────────────────────────────────────────────
#  Top-level orchestrator
# ──────────────────────────────────────────────────────────────────────────
_WUXING_TRAITS_HI = {
    "Wood":  "Growth-oriented, leader, ambitious, idealistic.",
    "Fire":  "Energetic, expressive, passionate, social.",
    "Earth": "Reliable, nurturing, grounded, loyal.",
    "Metal": "Disciplined, organised, principled, refined.",
    "Water": "Wise, intuitive, adaptive, deep-thinker.",
}


def _mirror_canonical_into_sections(sections: Dict, final: Dict) -> None:
    """SSOT enforcement — overwrite per-section element/archetype with the
    canonical values from final_scores so downstream narrative writers
    cannot drift. Silent no-op when section keys are missing."""
    elem = (final.get("element") or "").strip().capitalize()
    arch = (final.get("archetype") or "").strip()

    if elem:
        s5 = sections.get("section_5_core_foundation")
        if isinstance(s5, dict):
            s5["five_element_profile"] = elem
            traits = _WUXING_TRAITS_HI.get(elem)
            if traits:
                s5["five_element_traits"] = traits

    if arch:
        s7 = sections.get("section_7_personality_synthesis")
        if isinstance(s7, dict):
            s7["archetype"] = arch
        s13 = sections.get("section_13_archetype")
        if isinstance(s13, dict):
            s13["archetype_name"] = arch


def apply_consistency_layer(engines: Dict, sections: Dict) -> Dict[str, Any]:
    """One-call wrapper — mutates `sections` in-place AND returns final_scores."""
    final = build_final_scores(engines)
    normalize_section_keys(sections)
    apply_label_cleanup(sections)
    _mirror_canonical_into_sections(sections, final)
    warnings = validate_consistency(sections, final)
    final["consistency_warnings"] = warnings
    return final
