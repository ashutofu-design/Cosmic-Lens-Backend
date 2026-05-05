"""
topic_specific_packs.py — Phase H2.7.11 SCAFFOLD (DORMANT — content TBD by user)
=============================================================================

PURPOSE
-------
Topic-aware ULTRA-LEAN pack builder. Filters even WITHIN sections so that
e.g. a HEALTH question gets only 1H/6H/8H/12H lords + Sun/Moon/Mars/Saturn
(not all 12 house lords + all 9 planets like the current lean pack does).

STATUS — IMPORTANT
------------------
This file is a SCAFFOLD ONLY. Each topic-builder function returns "" right
now. User will dictate exactly what each topic includes by filling in the
clearly marked "FILL HERE" blocks.

NOT WIRED into openai_helper.py yet (per user directive: "automatic kuch
mat bhejna"). To activate later, an env-flag killswitch
TOPIC_SPECIFIC_PACK_MODE=1 will be added at the same passthrough sites
(sync L13627, stream L17169) where LEAN_PACK_MODE lives.

DESIGN CONTRACT
---------------
Each topic builder has the same signature as build_full_chart_context:
    build_<topic>_pack(kundli, intel, birth, question) -> str

Returns "" when:
  - kundli missing/empty
  - planet lookup fails
  - topic builder body is unfilled (current default for all 6)

Returns formatted string (~1,500-3,000 chars) when filled, designed to
slot into the same _PT_SYS_INTRO + chart_block + locked_facts pipeline
as the existing full / lean packs.

REUSED PRIMITIVES
-----------------
We import the same lookup helpers from kundli_full_context so we never
re-derive planet/lord/dignity tables. Single source of truth.

  _planet_lookup, _dignity_lookup, _lordship_lookup, _aspects_lookup,
  _sign_idx, _sign_name, _fmt_deg, _suffix, _naks_pada_lord,
  _functional_nature

A few small formatters live HERE (not in kundli_full_context) because
they're topic-pack-specific output styling. Marked clearly.

DISPATCHER
----------
build_topic_specific_pack(topic_id, kundli, intel, birth, question) is
the single entry point. It maps topic_id → builder. Unknown topic →
fall through to build_general_pack (which itself is unfilled — caller
should fall back to existing lean/full pack on empty return).

ADD-ONLY GUARANTEE
------------------
- New file, no edits to existing modules.
- Existing build_full_chart_context() and build_lean_chart_context()
  100% untouched.
- Caller wire-up will be added LATER (separate edit) under killswitch.
"""

from __future__ import annotations

from typing import Any, Optional

# ─── Reuse primitives from full chart context (single source of truth) ───
from kundli_full_context import (
    _planet_lookup,
    _dignity_lookup,
    _lordship_lookup,
    _aspects_lookup,
    _sign_idx,
    _sign_name,
    _fmt_deg,
    _suffix,
    _naks_pada_lord,
    _functional_nature,
    _PLANET_ORDER,
)

# ─────────────────────────────────────────────────────────────────────────
# CONFIG SLOTS — user will fill these tables to dictate "what jaata hai"
# ─────────────────────────────────────────────────────────────────────────
# Each topic gets a config dict declaring which houses + planets matter.
# The builder function reads its own config and emits ONLY those rows.
#
# Conventions:
#   houses:   list of 1-12 (1H = self, 6H = disease, etc.)
#   planets:  list of canonical names from _PLANET_ORDER
#   include_lagna_lord:  bool — always emit lagna lord row regardless
#   include_current_dasha: bool — emit running MD/AD/PD line
#   include_d9: bool — emit Navamsha cross-reference for selected items
#   extras:  freeform list of additional flags ("sade_sati", "mangal_dosh"
#            etc.) the builder will check for and append if present.
#
# DEFAULT = empty lists → builder returns "" → caller must fall back to
# existing lean/full pack. This is intentional so nothing ships silently.
# ─────────────────────────────────────────────────────────────────────────

TOPIC_PACK_CONFIG: dict[str, dict] = {
    # ─── HEALTH ──────────────────────────────────────────────────────
    # User: jo houses + planets health ke liye chahiye, list me daalo.
    # Suggested (NOT auto-applied): houses=[1,6,8,12],
    #   planets=["Sun","Moon","Mars","Saturn"], include_lagna_lord=True
    # Leave empty for now — fill when ready.
    "health": {
        "houses": [],
        "planets": [],
        "include_lagna_lord": False,
        "include_current_dasha": False,
        "include_d9": False,
        "extras": [],  # e.g. ["sade_sati", "mangal_dosh"]
    },

    # ─── MARRIAGE ────────────────────────────────────────────────────
    # User: marriage ke liye kya kya houses+planets MUST aana chahiye.
    # Suggested (NOT auto-applied): houses=[1,5,7,8,11],
    #   planets=["Venus","Jupiter","Mars","Moon"], include_d9=True
    "marriage": {
        "houses": [],
        "planets": [],
        "include_lagna_lord": False,
        "include_current_dasha": False,
        "include_d9": False,
        "extras": [],  # e.g. ["upapada_lagna", "mangal_dosh", "vivah_saham"]
    },

    # ─── CAREER ──────────────────────────────────────────────────────
    # Suggested (NOT auto-applied): houses=[1,2,6,10,11],
    #   planets=["Sun","Mercury","Saturn","Jupiter","Mars"]
    "career": {
        "houses": [],
        "planets": [],
        "include_lagna_lord": False,
        "include_current_dasha": False,
        "include_d9": False,
        "extras": [],  # e.g. ["d10_dasamsa", "amatyakaraka"]
    },

    # ─── FINANCE / WEALTH ────────────────────────────────────────────
    # Suggested (NOT auto-applied): houses=[2,5,9,11],
    #   planets=["Jupiter","Venus","Mercury","Moon"]
    "finance": {
        "houses": [],
        "planets": [],
        "include_lagna_lord": False,
        "include_current_dasha": False,
        "include_d9": False,
        "extras": [],  # e.g. ["d2_hora", "dhan_yog", "kuber_yog"]
    },

    # ─── CHILDREN ────────────────────────────────────────────────────
    # Suggested (NOT auto-applied): houses=[5,9],
    #   planets=["Jupiter","Moon"], extras=["d7_saptamsa"]
    "children": {
        "houses": [],
        "planets": [],
        "include_lagna_lord": False,
        "include_current_dasha": False,
        "include_d9": False,
        "extras": [],
    },

    # ─── GENERAL / FALLBACK ──────────────────────────────────────────
    # When topic doesn't match any specific bucket. User decides if this
    # should be "everything" (call lean pack) or a small "vital signs"
    # bucket (lagna + moon + sun + current dasha only).
    "general": {
        "houses": [],
        "planets": [],
        "include_lagna_lord": False,
        "include_current_dasha": False,
        "include_d9": False,
        "extras": [],
    },
}


# ─────────────────────────────────────────────────────────────────────────
# HEADER / FOOTER — same wrapping style as full pack, distinct phase tag
# ─────────────────────────────────────────────────────────────────────────
_TS_HEADER = (
    "═══════ TOPIC-SPECIFIC PACK (H2.7.11 ULTRA-LEAN) ═══════"
)
_TS_FOOTER = (
    "═══════════════════════════════════════════════════════════"
)


# ─────────────────────────────────────────────────────────────────────────
# SHARED FORMATTERS (small, topic-pack-specific styling)
# ─────────────────────────────────────────────────────────────────────────
def _fmt_planet_row(
    name: str,
    p: dict,
    dig: dict,
    lord: dict,
    asp: dict,
    lagna_idx: Optional[int],
) -> str:
    """One-line planet summary — sign, house, degree, naks, dignity, lord-of."""
    sign = _sign_name(p.get("sign") or p.get("rashi"))
    house = p.get("house") or "?"
    deg = _fmt_deg(p.get("degree") or p.get("lon") or 0)
    lon = p.get("lon") or p.get("longitude") or 0.0
    try:
        naks, pada, naks_lord = _naks_pada_lord(lon)
    except Exception:
        naks, pada, naks_lord = ("?", "?", "?")
    dign_label = (dig.get(name) or {}).get("label", "")
    lords_of = (lord.get(name) or {}).get("houses") if isinstance(lord.get(name), dict) else lord.get(name)
    lords_str = (
        f"L{','.join(str(h) for h in lords_of)}H" if lords_of else ""
    )
    func = _functional_nature(name, lagna_idx)
    parts = [
        f"{name}",
        f"{sign} {deg}",
        f"H{house}",
        f"{naks}/p{pada}",
    ]
    if dign_label:
        parts.append(dign_label)
    if lords_str:
        parts.append(lords_str)
    if func:
        parts.append(func)
    return "  • " + " | ".join(parts)


def _fmt_house_lord_row(
    house_num: int,
    intel: Optional[dict],
    p_lookup: dict,
    lagna_idx: Optional[int],
) -> str:
    """One-line house-lord summary — which planet rules H<n>, where it sits."""
    if not isinstance(intel, dict):
        return ""
    lords_table = (intel.get("houseLords") or intel.get("house_lords") or {})
    lord_name = ""
    if isinstance(lords_table, dict):
        lord_name = (lords_table.get(str(house_num)) or
                     lords_table.get(house_num) or "")
    if not lord_name or lord_name not in p_lookup:
        return f"  H{house_num}: lord=? (data missing)"
    p = p_lookup[lord_name]
    sign = _sign_name(p.get("sign") or p.get("rashi"))
    sits_in = p.get("house") or "?"
    deg = _fmt_deg(p.get("degree") or p.get("lon") or 0)
    return f"  H{house_num} lord = {lord_name} → {sign} {deg} (sits in H{sits_in})"


def _fmt_current_dasha(kundli: dict) -> str:
    """One-line current MD/AD/PD summary."""
    cd = kundli.get("currentDasha") or {}
    if not cd:
        return ""
    md = cd.get("mahadasha") or cd.get("md") or "?"
    ad = cd.get("antardasha") or cd.get("ad") or "?"
    pd = cd.get("pratyantar") or cd.get("pd") or ""
    md_end = cd.get("mahadashaEnd") or cd.get("md_end") or ""
    ad_end = cd.get("antardashaEnd") or cd.get("ad_end") or ""
    line = f"  Current: MD={md}"
    if md_end:
        line += f" (→ {md_end})"
    line += f" | AD={ad}"
    if ad_end:
        line += f" (→ {ad_end})"
    if pd:
        line += f" | PD={pd}"
    return line


def _fmt_lagna_block(kundli: dict, p_lookup: dict, intel: Optional[dict]) -> str:
    """Lagna sign + lagna lord placement (always emitted when requested)."""
    lagna_idx = _sign_idx(kundli.get("ascendant"))
    if lagna_idx is None:
        lagna_idx = _sign_idx(kundli.get("lagna"))
    if lagna_idx is None:
        return ""
    sign = _sign_name(lagna_idx)
    line = f"  Lagna: {sign}"
    # Lagna lord
    if isinstance(intel, dict):
        lords_table = (intel.get("houseLords") or intel.get("house_lords") or {})
        lord_name = (lords_table.get("1") or lords_table.get(1) or "")
        if lord_name and lord_name in p_lookup:
            lp = p_lookup[lord_name]
            lp_sign = _sign_name(lp.get("sign") or lp.get("rashi"))
            lp_house = lp.get("house") or "?"
            line += f" | Lagna lord = {lord_name} → {lp_sign} (H{lp_house})"
    return line


# ─────────────────────────────────────────────────────────────────────────
# CORE BUILDER — generic, driven entirely by config dict
# ─────────────────────────────────────────────────────────────────────────
def _build_from_config(
    topic: str,
    kundli: dict,
    intel: Optional[dict],
    birth: Optional[dict],
    question: str,
) -> str:
    """Generic builder — reads TOPIC_PACK_CONFIG[topic] and emits sections.

    Returns "" when config is empty (default state for all topics until
    user fills them). Defensive on every step.
    """
    cfg = TOPIC_PACK_CONFIG.get(topic) or {}
    has_houses = bool(cfg.get("houses"))
    has_planets = bool(cfg.get("planets"))
    if not (
        has_houses or has_planets
        or cfg.get("include_lagna_lord")
        or cfg.get("include_current_dasha")
        or cfg.get("extras")
    ):
        # Nothing configured → return empty so caller falls back.
        return ""

    p_lookup = _planet_lookup(kundli.get("planets"))
    if not p_lookup:
        return ""

    dig_lookup = _dignity_lookup(intel)
    lord_lookup = _lordship_lookup(intel)
    asp_lookup = _aspects_lookup(kundli)
    lagna_idx = _sign_idx(kundli.get("ascendant"))
    if lagna_idx is None:
        lagna_idx = _sign_idx(kundli.get("lagna"))

    blocks: list[str] = []
    blocks.append(f"## TOPIC: {topic.upper()} (filtered pack)")

    # ─── Lagna line ────────────────────────────────────────────────
    if cfg.get("include_lagna_lord"):
        try:
            lb = _fmt_lagna_block(kundli, p_lookup, intel)
            if lb:
                blocks.append("### LAGNA\n" + lb)
        except Exception:
            pass

    # ─── Selected house lords ──────────────────────────────────────
    if has_houses:
        try:
            rows = []
            for h in cfg["houses"]:
                row = _fmt_house_lord_row(h, intel, p_lookup, lagna_idx)
                if row:
                    rows.append(row)
            if rows:
                blocks.append("### RELEVANT HOUSE LORDS\n" + "\n".join(rows))
        except Exception:
            pass

    # ─── Selected planets ──────────────────────────────────────────
    if has_planets:
        try:
            rows = []
            for name in cfg["planets"]:
                if name not in p_lookup:
                    continue
                row = _fmt_planet_row(
                    name, p_lookup[name], dig_lookup, lord_lookup,
                    asp_lookup, lagna_idx,
                )
                if row:
                    rows.append(row)
            if rows:
                blocks.append("### RELEVANT PLANETS\n" + "\n".join(rows))
        except Exception:
            pass

    # ─── Current dasha ─────────────────────────────────────────────
    if cfg.get("include_current_dasha"):
        try:
            d = _fmt_current_dasha(kundli)
            if d:
                blocks.append("### CURRENT DASHA\n" + d)
        except Exception:
            pass

    # ─── D9 cross-reference (selected planets only) ────────────────
    if cfg.get("include_d9"):
        try:
            from kundli_full_context import _section_d9_navamsha
            # Full D9 section appended as-is for now; future refinement
            # could filter D9 to only the topic-relevant planets.
            d9 = _section_d9_navamsha(kundli, p_lookup)
            if d9:
                blocks.append(d9)
        except Exception:
            pass

    # ─── Extras (yogas, doshas, etc.) ──────────────────────────────
    extras = cfg.get("extras") or []
    if extras:
        try:
            extra_rows = _emit_extras(extras, kundli, intel, birth, p_lookup)
            if extra_rows:
                blocks.append("### EXTRAS\n" + extra_rows)
        except Exception:
            pass

    body = "\n\n".join(b for b in blocks if b)
    if not body:
        return ""
    return "\n".join([_TS_HEADER, "", body, "", _TS_FOOTER])


def _emit_extras(
    extras: list,
    kundli: dict,
    intel: Optional[dict],
    birth: Optional[dict],
    p_lookup: dict,
) -> str:
    """Look up specific extras user requested.

    Each extra is a string flag. Builder checks intel/kundli for the
    relevant computed value and emits a one-line summary if present.
    Defensive — unknown flags silently ignored.

    Supported flags (extensible, FILL HERE as user adds):
      "sade_sati"      — Saturn over Moon transit (intel['sadeSati'])
      "mangal_dosh"    — Mars in 1/4/7/8/12 (intel['mangalDosha'])
      "kaal_sarp"      — Rahu-Ketu axis hemming (intel['kaalSarpa'])
      "upapada_lagna"  — Jaimini UL (intel['upapadaLagna'])
      "d2_hora"        — Hora chart wealth check
      "d7_saptamsa"    — Saptamsa for children
      "d10_dasamsa"    — Dasamsa for career
      "amatyakaraka"   — Jaimini AK for career
      "dhan_yog"       — Wealth yogas (intel['dhanYogas'])
      "vivah_saham"    — Marriage Saham (intel['vivahaSaham'])
      "kuber_yog"      — Kuber yoga
    """
    rows: list[str] = []
    intel_d = intel if isinstance(intel, dict) else {}

    if "sade_sati" in extras:
        ss = intel_d.get("sadeSati") or intel_d.get("sade_sati")
        if ss:
            rows.append(f"  • Sade-Sati: {ss}")

    if "mangal_dosh" in extras:
        md = intel_d.get("mangalDosha") or intel_d.get("mangal_dosha")
        if md:
            rows.append(f"  • Mangal Dosh: {md}")

    if "kaal_sarp" in extras:
        ks = intel_d.get("kaalSarpa") or intel_d.get("kaal_sarpa")
        if ks:
            rows.append(f"  • Kaal Sarp: {ks}")

    if "upapada_lagna" in extras:
        ul = intel_d.get("upapadaLagna") or intel_d.get("upapada_lagna")
        if ul:
            rows.append(f"  • Upapada Lagna (UL): {ul}")

    if "dhan_yog" in extras:
        dy = intel_d.get("dhanYogas") or intel_d.get("dhan_yogas")
        if dy:
            rows.append(f"  • Dhan Yogas: {dy}")

    if "vivah_saham" in extras:
        vs = intel_d.get("vivahaSaham") or intel_d.get("vivaha_saham")
        if vs:
            rows.append(f"  • Vivaha Saham: {vs}")

    # NOTE: D2/D7/D10/AK extras require divisional-chart computations.
    # Left as TODO stubs — wire to dedicated builders when user defines
    # exactly what fields are needed in the prompt.
    if "d2_hora" in extras:
        rows.append("  • D2 Hora: [TODO — wire to varga engine]")
    if "d7_saptamsa" in extras:
        rows.append("  • D7 Saptamsa: [TODO — wire to varga engine]")
    if "d10_dasamsa" in extras:
        rows.append("  • D10 Dasamsa: [TODO — wire to varga engine]")
    if "amatyakaraka" in extras:
        rows.append("  • Amatyakaraka: [TODO — wire to jaimini engine]")
    if "kuber_yog" in extras:
        rows.append("  • Kuber Yog: [TODO — wire to yoga engine]")

    return "\n".join(rows)


# ─────────────────────────────────────────────────────────────────────────
# PUBLIC TOPIC BUILDERS — thin wrappers around the config-driven core
# ─────────────────────────────────────────────────────────────────────────
def build_health_pack(kundli, intel=None, birth=None, question="") -> str:
    """Health-only pack. Returns "" until TOPIC_PACK_CONFIG['health'] is filled.

    User dictates content via TOPIC_PACK_CONFIG['health'].
    """
    if not isinstance(kundli, dict) or not kundli:
        return ""
    return _build_from_config("health", kundli, intel, birth, question)


def build_marriage_pack(kundli, intel=None, birth=None, question="") -> str:
    """Marriage-only pack. Returns "" until config filled."""
    if not isinstance(kundli, dict) or not kundli:
        return ""
    return _build_from_config("marriage", kundli, intel, birth, question)


def build_career_pack(kundli, intel=None, birth=None, question="") -> str:
    """Career-only pack. Returns "" until config filled."""
    if not isinstance(kundli, dict) or not kundli:
        return ""
    return _build_from_config("career", kundli, intel, birth, question)


def build_finance_pack(kundli, intel=None, birth=None, question="") -> str:
    """Finance/wealth-only pack. Returns "" until config filled."""
    if not isinstance(kundli, dict) or not kundli:
        return ""
    return _build_from_config("finance", kundli, intel, birth, question)


def build_children_pack(kundli, intel=None, birth=None, question="") -> str:
    """Children/santaan-only pack. Returns "" until config filled."""
    if not isinstance(kundli, dict) or not kundli:
        return ""
    return _build_from_config("children", kundli, intel, birth, question)


def build_general_pack(kundli, intel=None, birth=None, question="") -> str:
    """General / fallback pack. Returns "" until config filled."""
    if not isinstance(kundli, dict) or not kundli:
        return ""
    return _build_from_config("general", kundli, intel, birth, question)


# ─────────────────────────────────────────────────────────────────────────
# DISPATCHER — single entry point, used by future wire-up
# ─────────────────────────────────────────────────────────────────────────
_BUILDERS: dict[str, Any] = {
    "health":          build_health_pack,
    "marriage":        build_marriage_pack,
    "love":            build_marriage_pack,   # alias
    "career":          build_career_pack,
    "finance":         build_finance_pack,
    "wealth":          build_finance_pack,    # alias
    "money":           build_finance_pack,    # alias
    "children":        build_children_pack,
    "child":           build_children_pack,   # alias
    "general":         build_general_pack,
}


def build_topic_specific_pack(
    topic_id: str,
    kundli: Any,
    intel: Any = None,
    birth: Any = None,
    question: str = "",
) -> str:
    """Single dispatch entry point.

    Args:
        topic_id: classifier output ('health' / 'marriage' / 'career' /
                  'finance' / 'children' / 'general' or any alias).
        kundli, intel, birth, question: same contract as build_full_chart_context.

    Returns:
        Formatted topic pack string, OR "" when:
          - topic_id unknown
          - matching config is empty (default until user fills it)
          - kundli missing
        Caller MUST fall back to build_lean_chart_context or
        build_full_chart_context on empty return.
    """
    if not isinstance(kundli, dict) or not kundli:
        return ""
    builder = _BUILDERS.get((topic_id or "").lower().strip())
    if builder is None:
        return ""
    try:
        return builder(kundli, intel, birth, question)
    except Exception:
        # Defensive — never raise, always return empty for clean fallback.
        return ""


def get_topic_config(topic_id: str) -> dict:
    """Helper for tests / introspection — returns current config for topic."""
    return dict(TOPIC_PACK_CONFIG.get((topic_id or "").lower().strip()) or {})


def list_supported_topics() -> list[str]:
    """Helper — returns list of topic_ids the dispatcher recognizes."""
    return sorted(set(_BUILDERS.keys()))


__all__ = [
    "TOPIC_PACK_CONFIG",
    "build_health_pack",
    "build_marriage_pack",
    "build_career_pack",
    "build_finance_pack",
    "build_children_pack",
    "build_general_pack",
    "build_topic_specific_pack",
    "get_topic_config",
    "list_supported_topics",
]
