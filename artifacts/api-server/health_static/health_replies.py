"""Health reply builder (3 modes — supportive tone).

Modes:
  WARNING   -> locked safe-template (0 LLM tokens)
  DIRECT    -> format engine 5-dim facts as Hinglish (0 LLM tokens)
  NARRATIVE -> engine facts + 60-80w LLM polish (cached)
  HYBRID    -> DIRECT picture + short LLM narrative tailored to question

Tone discipline (per user directive):
  - SUPPORTIVE + CALM + NON-ALARMING (NEVER blunt finance-tone)
  - No fear amplification — "dhyan dena chahiye" not "danger"
  - Sensitive buckets (mental/repro/parent/addiction) get extra soft
    closing + bucket-specific helpline/specialist mention
  - Doctor disclaimer ALWAYS appended (validator enforces)

Public:
  handle_health_question(question, kundli, birth) -> dict | None
"""
from __future__ import annotations
import os
import re
import time as _time
from typing import Any, Dict, Optional

from health_static.health_facts import compute_health_facts
from health_static.health_routing import (is_health_question,
                                           route_health_question,
                                           detect_sensitive_bucket)
from health_static.health_warnings import WARNINGS
from health_static.answer_cache import (make_cache_key, get_cached,
                                         put_cached, _chart_fingerprint)
from health_static.telemetry import log_event as _telemetry_log
from health_static.validator import (validate_health_llm_output,
                                      apply_safety_tail,
                                      DOCTOR_DISCLAIMER)


_PATH_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}

# Standard dims: GREEN=strong/good. INVERTED dims: GREEN=low risk (still good).
_DIM_LABEL = {
    "vitality":           "Vitality (body strength)",
    "disease_resistance": "Recovery power",
    "chronic_risk":       "Chronic risk zone",
    "mental_health":      "Mental peace",
    "accident_risk":      "Accident risk zone",
}

# Hinglish translation for verdict words. INVERTED dims get inverted
# language so user reads it correctly (GREEN chronic_risk = "low risk").
_VERDICT_HINGLISH_STD = {
    "GREEN":  "Strong",
    "YELLOW": "Mixed",
    "RED":    "Weak — dhyan dena chahiye",
}
_VERDICT_HINGLISH_INV = {
    "GREEN":  "Low — basic care kaafi",
    "YELLOW": "Mixed — periodic checkup useful",
    "RED":    "Elevated — preventive care important",
}
_TIER_HINGLISH = {
    "high":     "strong support",
    "moderate": "moderate support",
    "low":      "weak / borderline",
    "none":     "support absent",
}


def _verdict_word(dim: dict) -> str:
    table = (_VERDICT_HINGLISH_INV if dim.get("inverted")
             else _VERDICT_HINGLISH_STD)
    return table.get(dim.get("verdict", "?"), dim.get("verdict", "?"))


# ── Comparative-intent helpers (Phase H2.3) ────────────────────────
# Detects "X ya Y", "body vs mental", "thakan ya stress", "kaunsa zyada
# weak", etc. — and answers with an explicit winner / loser / tie
# verdict instead of leaving the user to read a 5-dim table themselves.
# Principle: "Jab user comparison puche, system ko winner/loser ya tie
# bolna hi padega."
_COMPARATIVE_RX = re.compile(
    r"(\bya\b|\bvs\b|\bversus\b|\bkaunsa\b|\bkaunsi\b|\bkaunsi\s+zyada\b|"
    r"\bzyada\s+(weak|strong|kam|jyada|dominant|prabhal)\b|"
    r"\b(better|worse|more|less|dominant)\s+(kya|kaunsa|hai)\b|"
    r"\bcompare\b|\bcomparison\b|\bdifference\b)",
    re.IGNORECASE,
)

# (regex, dim_keys, display_label) — order matters; first match wins per
# concept group. Multi-key entries (e.g. body) average across channels.
_DIM_CONCEPTS = [
    # Phase H2.3.1 (B): expanded Hinglish lexicon
    (re.compile(r"\b(body|shareer|sharir|physical|tan|jism|"
                r"tabiyat|sehat|swasthya|bimari|beemari|rog)\b", re.I),
     ["vitality", "disease_resistance"], "Body (vitality + recovery)"),
    (re.compile(r"\b(mental|mann|man|mind|psych|emotional|"
                r"stress|anxiety|peace|mood|neend|sleep|"
                r"dimaag|dimag|mindset|khayal)\b", re.I),
     ["mental_health"], "Mental peace"),
    (re.compile(r"\b(thakan|fatigue|energy|stamina|kamzori|kamjor|"
                r"weakness|vitality)\b", re.I),
     ["vitality"], "Vitality (energy)"),
    (re.compile(r"\b(immunity|immune|pratiraksha|recovery|bounce|heal|"
                r"disease[\s-]?resistance)\b", re.I),
     ["disease_resistance"], "Recovery / immunity"),
    (re.compile(r"\b(chronic|long[\s-]?term|hereditary|lambi|"
                r"purani|permanent)\b", re.I),
     ["chronic_risk"], "Chronic risk zone"),
    (re.compile(r"\b(accident|chot|injury|sudden|sharp|"
                r"durghatna)\b", re.I),
     ["accident_risk"], "Accident risk zone"),
]

_STRENGTH = {"GREEN": 3, "YELLOW": 2, "RED": 1}


# ── Phase H2.4 — Locked Universal Answer Structure ─────────────────
# Behaviour-keyword detector for Secondary-factor logic (Q1=β):
# if user mentions lifestyle/routine/stress/habit → Secondary becomes
# "Lifestyle / routine load" instead of 2nd-weakest dim.
_BEHAVIOUR_RX = re.compile(
    r"\b(lifestyle|routine|habit|aadat|aadatein|stress|tension|"
    r"neend|sleep|nind|food|khaana|khana|diet|paani|water|"
    r"hydration|exercise|kasrat|workout|gym|screen|mobile|"
    r"smoke|smoking|cigarette|sharab|alcohol|drink|sedentary|"
    r"baith[ae]?|rehan[\s-]?sehan|daily kaam|work pressure|"
    r"kaam ka load|chai|coffee|junk|fast[\s-]?food)\b",
    re.IGNORECASE,
)

# Soft user-facing labels for Primary slot (Q2=Y — mental gets soft).
_PRIMARY_LABEL_SOFT = {
    "vitality":           "Body energy / vitality weak",
    "disease_resistance": "Recovery / immunity weak",
    "chronic_risk":       "Chronic-risk awareness needed",
    "mental_health":      "Mental wellbeing support",  # soft (Y)
    "accident_risk":      "Accident-risk awareness needed",
}

# Compact secondary labels (1st letter capital, no extra punctuation).
_SECONDARY_LABEL = {
    "vitality":           "Body energy bhi low side par",
    "disease_resistance": "Recovery slow side par",
    "chronic_risk":       "Chronic-risk slightly elevated",
    "mental_health":      "Mental peace stressed",
    "accident_risk":      "Accident-risk slightly elevated",
}

# Phase H2.5 — TENDENCY / FUTURE-RISK intent detector.
# When question asks for "kaun-kaun issues / future tendency / risk
# profile", we append a 4th locked block ('👉 Tendency issues') with
# category-based (NOT disease-name) issues drawn from each weak/
# yellow dim. Per-spec: never name diseases, never diagnose.
_TENDENCY_INTENT_RX = re.compile(
    r"(kaun[\s-]?kaun|kya[\s-]?kya|kis[\s-]?kis|"
    r"\btendency\b|\btendencies\b|"
    r"future\s+(me|mein)?\s*(health|issues?|problems?|risk|bimari|"
    r"tendency|tendencies)|"
    r"aage\s+(chal\s+ke|jaake|aane\s+wale)|"
    r"aane\s+wale\s+(samay|time|saalon)|"
    r"(probable|possible|likely)\s+(health|issues?|risks?)|"
    r"health\s+(risk|issue)\s+(profile|areas?|zones?)|"
    r"chances?\s+of\s+(health|illness|issues?))",
    re.IGNORECASE,
)

# Category-only tendency lines per dim (NO disease names per safety
# spec). Triggered only for RED + YELLOW dims; GREEN dims skipped.
_TENDENCY_BY_DIM = {
    "vitality": {
        "RED": ["fatigue / low-energy aur thakan repeat hone wali "
                "issues", "stamina-drop, daily kaam me effort zyada "
                "lagna"],
        "YELLOW": ["mild low-energy spells, occasional thakan"],
    },
    "disease_resistance": {
        "RED": ["immunity-related frequent minor issues (seasonal "
                "infections, slow recovery)", "small wound / cold-flu "
                "category issues ka late healing pattern"],
        "YELLOW": ["recovery thodi slow, occasional minor "
                   "infection-prone phase"],
    },
    "chronic_risk": {
        "RED": ["chronic-zone me lifestyle-driven gradual buildup "
                "(BP / sugar / metabolism category — preventive "
                "zone)", "long-term wear-and-tear category "
                "(joints, digestion sensitivity)"],
        "YELLOW": ["chronic-zone me mild signal — periodic basic "
                   "checkup useful, lifestyle preventive zone"],
    },
    "mental_health": {
        "RED": ["stress-related discomfort (neend disturbance, sir "
                "bhaari, mood dips)", "overthinking aur mental "
                "fatigue ka tendency"],
        "YELLOW": ["mild stress / mood-fluctuation phase, mental "
                   "rest important"],
    },
    "accident_risk": {
        "RED": ["accident-zone par caution (jaldbaazi, sharp "
                "objects, driving me dhyan)", "physical mishap / "
                "sports-injury category awareness"],
        "YELLOW": ["accident-zone par mild caution — jaldbaazi "
                   "avoid, daily mindfulness"],
    },
}


# ── Phase H2.6 — SIMPLE-OUTPUT MODE (structure-internal, narrative-out) ──
# User feedback (2026-05-05): H2.4/H2.5 produced report-style output with
# emojis + 5-dim list + verdict labels — felt like "natak". Engine still
# computes the locked verdict + tendency dim-list internally; presentation
# layer now renders ONE flowing 2-3 paragraph Hinglish narrative.
# Default = "simple". Set HEALTH_OUTPUT_STYLE=structured (env var) to
# revert to H2.5 4-block output (debug/admin only).
_OUTPUT_STYLE = (os.environ.get("HEALTH_OUTPUT_STYLE") or "simple").lower()

# Soft user-facing names for dims (NO labels like "vitality" / "RED").
_DIM_SOFT_NAME = {
    "vitality":           "body energy",
    "disease_resistance": "immunity / recovery",
    "mental_health":      "mental side",
    "chronic_risk":       "chronic-zone",
    "accident_risk":      "accident-zone",
}

# Inline tendency phrases (not bulleted) per dim+verdict — for static
# fallback renderer. LLM gets the same data via fact pack.
_DIM_TENDENCY_INLINE = {
    ("vitality", "RED"):           "baar-baar thakan, low stamina, aur chhoti energy-drop wali issues",
    ("vitality", "YELLOW"):        "kabhi-kabhi mild thakan ya energy-dip",
    ("disease_resistance", "RED"): "frequent chhoti health problems aur slow recovery",
    ("disease_resistance", "YELLOW"): "occasional minor infection-prone phase aur thodi slow recovery",
    ("mental_health", "RED"):      "neend disturbance, mental fatigue ya sir bhaari lagna jaisa feel",
    ("mental_health", "YELLOW"):   "mild stress ya mood-fluctuation phase",
    ("chronic_risk", "RED"):       "lifestyle-driven gradual buildup zone (BP / sugar / metabolism category — preventive zone)",
    ("chronic_risk", "YELLOW"):    "chronic-zone ka mild signal — periodic basic checkup useful",
    ("accident_risk", "RED"):      "accident-zone par caution — jaldbaazi avoid, sharp objects aur driving me dhyan",
    ("accident_risk", "YELLOW"):   "accident-zone par mild caution — jaldbaazi avoid",
}


def _compute_simple_summary(facts: dict) -> dict:
    """Internal structured summary used by simple renderers (LLM + static).
    Engine truth stays here; presentation layer never sees raw verdicts."""
    dims = facts.get("dimensions") or {}
    weak_body, weak_mind, weak_risk = [], [], []
    for k in ("vitality", "disease_resistance"):
        v = (dims.get(k) or {}).get("verdict")
        if v in ("RED", "YELLOW"):
            weak_body.append((k, v))
    v = (dims.get("mental_health") or {}).get("verdict")
    if v in ("RED", "YELLOW"):
        weak_mind.append(("mental_health", v))
    for k in ("chronic_risk", "accident_risk"):
        v = (dims.get(k) or {}).get("verdict")
        if v in ("RED", "YELLOW"):
            weak_risk.append((k, v))
    yogas = facts.get("yogas") or []
    has_arishta = any(
        ("arishta" in (y.get("name", "").lower())
         or "balarishta" in (y.get("name", "").lower()))
        for y in yogas
    )
    return {
        "weak_body": weak_body, "weak_mind": weak_mind,
        "weak_risk": weak_risk, "has_arishta": has_arishta,
        "all_green": not (weak_body or weak_mind or weak_risk),
    }


def _render_simple_narrative_static(facts: dict, question: str) -> str:
    """Static (no-LLM) fallback narrative renderer. Composes 2-3
    natural Hinglish paragraphs from engine truth — no emojis, no
    bullet lists, no dim/RED/YELLOW labels, no Final/Primary/Focus."""
    s = _compute_simple_summary(facts)
    if s["all_green"]:
        return ("Tumhare chart ke hisaab se health side par koi major "
                "stress nahi dikh raha. Body energy, immunity aur "
                "mental peace teeno theek-thaak phase me hain. "
                "Routine, neend aur balanced diet maintain rakho — "
                "yahi consistency long-term me sabse zyada kaam aati hai.")

    paras = []
    # Para 1 — body side (vitality + immunity)
    if s["weak_body"]:
        body_names = " aur ".join(_DIM_SOFT_NAME[k] for k, _ in s["weak_body"])
        body_tend = "; ".join(
            _DIM_TENDENCY_INLINE.get((k, v), "")
            for k, v in s["weak_body"] if _DIM_TENDENCY_INLINE.get((k, v))
        )
        paras.append(
            f"Tumhare chart ke hisaab se {body_names} thodi weak side "
            f"par dikh rahi hai, isliye tumhe {body_tend} hone ka "
            f"tendency ho sakta hai."
        )

    # Para 2 — mind side
    if s["weak_mind"]:
        mind_tend = _DIM_TENDENCY_INLINE.get(s["weak_mind"][0], "")
        paras.append(
            f"Stress side bhi thoda zyada impact karta hai, to "
            f"{mind_tend} aa sakta hai."
        )

    # Para 3 — risk zones (only if RED) + closing
    risk_red = [(k, v) for k, v in s["weak_risk"] if v == "RED"]
    risk_yellow = [(k, v) for k, v in s["weak_risk"] if v == "YELLOW"]
    closing_bits = []
    if risk_red:
        rnames = " aur ".join(_DIM_SOFT_NAME[k] for k, _ in risk_red)
        closing_bits.append(
            f"{rnames} ke side par bhi alert phase hai, isliye "
            f"preventive habits aur basic checkup important hain"
        )
    if not s["has_arishta"]:
        closing_bits.append(
            "overall yeh major bimari ka indication nahi hai — "
            "routine aur lifestyle sahi rakho to easily control me "
            "aa sakta hai"
        )
    else:
        closing_bits.append(
            "chart me ek classical health-yog active hai jo extra "
            "dhyan deserve karta hai — routine, rest aur preventive "
            "care priority pe rakho"
        )
    if risk_yellow and not risk_red:
        closing_bits.append(
            "chronic aur accident zones par hlka mild signal hai — "
            "periodic checkup aur daily mindfulness useful rahega"
        )
    paras.append(", ".join(closing_bits).capitalize() + ".")
    return "\n\n".join(paras)


def _build_health_kundli_pack(kundli: dict, facts: dict,
                               question: str) -> str:
    """Phase H2.7 (Path B+) — FULL health-relevant kundli pack for LLM.
    No pre-curation: send everything health-relevant, let LLM cherry-pick
    per question. Engine dim verdicts included as ground-truth checksum
    LLM must align with (cannot contradict)."""
    lines = []
    lines.append("════ FULL HEALTH KUNDLI PACK (truth source) ════\n")

    # Ascendant + basic identity
    asc = kundli.get("ascendant") or facts.get("ascendant") or "?"
    moon_sign = kundli.get("moonSign") or "?"
    sun_sign = kundli.get("sunSign") or "?"
    naksh = kundli.get("nakshatra") or "?"
    naksh_ruler = kundli.get("nakshatraRuler") or "?"
    lines.append(f"Ascendant (Lagna): {asc}")
    lines.append(f"Moon sign: {moon_sign} | Sun sign: {sun_sign}")
    lines.append(f"Janma Nakshatra: {naksh} (ruler: {naksh_ruler})\n")

    # All 9 planets with full attribution
    lines.append("--- PLANETS (house, sign, dignity, nakshatra) ---")
    karakas = facts.get("karakas") or {}
    for p in (kundli.get("planets") or []):
        nm = p.get("name", "?")
        kk = karakas.get(nm) or {}
        dignity = kk.get("dignity") or "?"
        retro = " R" if p.get("retrograde") else ""
        lines.append(
            f"  {nm}: house {p.get('house','?')}, "
            f"{p.get('sign','?')} {p.get('degrees','')}{retro}, "
            f"dignity={dignity}, "
            f"nakshatra={p.get('nakshatra','?')} "
            f"(ruler {p.get('nakshatraRuler','?')})"
        )
    lines.append("")

    # Health-relevant house lords (1, 6, 8, 12)
    lines.append("--- HEALTH HOUSE LORDS (1=self, 6=disease, 8=mrityu/chronic, 12=loss/hospital) ---")
    for hk in ("h1", "h6", "h8", "h12"):
        hl = (facts.get("house_lords") or {}).get(hk) or {}
        if hl:
            dush = " [IN DUSTHANA 6/8/12]" if hl.get("lord_in_dusthana") else ""
            lines.append(
                f"  {hk.upper()}: lord={hl.get('lord','?')} in house "
                f"{hl.get('lord_house','?')}, dignity={hl.get('lord_dignity','?')}{dush}"
            )
    lines.append("")

    # Health karakas (Sun=vitality, Moon=mind, Mars=energy/wounds, Jupiter=immunity, Saturn=chronic)
    lines.append("--- KEY HEALTH KARAKAS ---")
    karaka_role = {
        "Sun": "vitality / atma",
        "Moon": "mind / body fluids",
        "Mars": "energy / wounds / inflammation",
        "Jupiter": "immunity / liver",
        "Saturn": "chronic / longevity",
    }
    for nm, role in karaka_role.items():
        kk = karakas.get(nm) or {}
        if kk:
            lines.append(
                f"  {nm} ({role}): house {kk.get('house','?')}, "
                f"{kk.get('sign','?')}, dignity={kk.get('dignity','?')}"
            )
    lines.append("")

    # KP CSL chains for h1, h6, h8 (deepest health signal)
    lines.append("--- KP CSL CHAINS (1st=body, 6th=disease, 8th=chronic) ---")
    kp_csl = facts.get("kp_csl") or {}
    for hk in ("h1", "h6", "h8"):
        cs = kp_csl.get(hk) or {}
        if cs:
            chain = cs.get("chain") or {}
            lines.append(
                f"  {hk.upper()} CSL: {cs.get('csl_planet','?')}, "
                f"score={cs.get('score','?')}, verdict={cs.get('verdict','?')}, "
                f"signified houses={chain.get('signified', [])}"
            )
            reason = cs.get("reason")
            if reason:
                lines.append(f"     reason: {reason}")
    lines.append("")

    # Active yogas
    yogas = facts.get("yogas") or []
    lines.append(f"--- YOGAS active: {len(yogas)} ---")
    if yogas:
        for y in yogas:
            lines.append(f"  - {y.get('name','?')}: {y.get('description','')}")
    else:
        lines.append("  (none — no major Arishta/Balarishta detected)")
    lines.append("")

    # Current dasha — for "kab" questions
    cd = kundli.get("currentDasha") or {}
    if cd:
        lines.append(
            f"--- CURRENT DASHA: Mahadasha={cd.get('maha','?')} | "
            f"Antar={cd.get('antar','?')} | "
            f"Pratyantar={cd.get('pratyantar','?')} "
            f"({cd.get('startDate','?')} → {cd.get('endDate','?')}) ---\n"
        )

    # ENGINE DIM VERDICTS (ground-truth checksum — LLM MUST align)
    lines.append("--- ENGINE DIM VERDICTS (ground-truth checksum — DO NOT contradict) ---")
    dim_label = {
        "vitality": "Body energy / vitality",
        "disease_resistance": "Immunity / recovery",
        "mental_health": "Mental peace",
        "chronic_risk": "Chronic-zone",
        "accident_risk": "Accident-zone",
    }
    for dk, dlabel in dim_label.items():
        d = (facts.get("dimensions") or {}).get(dk) or {}
        if d:
            lines.append(
                f"  {dlabel}: {d.get('verdict','?')} "
                f"(severity={d.get('severity','?')})"
            )
    lines.append("")

    # User question
    lines.append(f"--- USER QUESTION ---\n  {question!r}")
    return "\n".join(lines)


def _render_simple_narrative_llm(facts: dict, question: str,
                                  sensitive_bucket: Optional[str],
                                  kundli: Optional[dict] = None) -> str:
    """Phase H2.7 (Path B+) — LLM gets FULL health kundli pack and
    cherry-picks per question. Engine = data supplier + ground-truth
    checksum. LLM = question-aware reasoning + framing.
    Falls back to static if no client."""
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return _render_simple_narrative_static(facts, question)
    except Exception:
        return _render_simple_narrative_static(facts, question)

    fact_pack = _build_health_kundli_pack(kundli or {}, facts, question)

    sys_prompt = (
        "You are an EXPERT Vedic-astrology HEALTH analyst with deep "
        "knowledge of classical houses, planets, dignities, KP system, "
        "and dasha-phala. Tone: warm, calm, direct, Hinglish — like a "
        "knowledgeable friend giving a focused samajh, NOT a report.\n\n"
        "YOU RECEIVE: a FULL health-kundli pack (planets, houses, "
        "lords, karakas, KP CSL chains, current dasha, yogas, and "
        "engine dim verdicts as ground-truth checksum).\n\n"
        "YOUR JOB:\n"
        "1. Read the user's question carefully.\n"
        "2. Cherry-pick ONLY the relevant pieces from the pack — do "
        "NOT dump everything. Be selective per question type.\n"
        "3. Reason like a real Vedic analyst from the data given. "
        "Form your own attribution-based explanation.\n"
        "4. Stay strictly aligned with the ENGINE DIM VERDICTS — if "
        "engine says vitality=RED, you cannot say body is healthy. "
        "If engine says no Arishta, you cannot invent one.\n\n"
        "REASONING PLAYBOOK (which data for which Q-type):\n"
        "- 'Health kaisi hai / overall' → engine dim verdicts + 1-2 "
        "key contributing planets/lords.\n"
        "- 'Kaunsa planet / kya combination / kyun weak' → name "
        "actual planets/lords from pack: afflicted house lords (esp "
        "1L/6L/8L/12L), debilitated/dusthana karakas, KP CSL RED "
        "verdicts. Quote real positions (e.g. 'Mars 8th house me "
        "debilitated baitha hai').\n"
        "- 'Future / kab / tendency timing' → use CURRENT DASHA "
        "(maha/antar) + dim verdicts. Be cautious — never give exact "
        "month/year predictions beyond what dasha pack shows.\n"
        "- Comparative Q (X vs Y) → direct verdict in para 1 (no "
        "balanced essay).\n"
        "- 'Issues kya ho sakte hain / tendency' → category list "
        "from weak dims (no disease names).\n\n"
        "LENGTH & SHAPE:\n"
        "- Target 100-160 words. Hard cap 200 words — NEVER exceed.\n"
        "- 2-3 short paragraphs. Closing line = ONE practical "
        "takeaway (sleep / khana / hydration / routine).\n"
        "- ONE clear core message — do NOT scatter across all 5 "
        "dims unless user specifically asked for full picture.\n"
        "- Attribution-rich (planet+house+dignity) lines are GOOD; "
        "filler/repetition is NOT — earn every word.\n\n"
        "STRICT BANS:\n"
        "1. NO emojis. NO bullet lists. NO numbered headers. NO "
        "section labels ('Final:', 'Primary factor:', 'Focus:', "
        "'Tendency issues:', '5 dimensions').\n"
        "2. NO engine jargon visible to user ('RED'/'YELLOW'/"
        "'GREEN'/'verdict'/'dim'/'channel'/'dimension'/"
        "'disease_resistance'). Use natural Hinglish: 'body energy', "
        "'immunity', 'mental side', 'chronic-zone', 'accident-zone'. "
        "(Planet names, house numbers, dignities are FINE — those "
        "are user-friendly Vedic terms.)\n"
        "3. NO disease names (cancer / diabetes / migraine / "
        "depression etc.). Category-only language.\n"
        "4. NO doctor / professional / specialist / therapist / "
        "expert / counsellor / 'medical advice' mention.\n"
        "5. NO 'tumhe X hai' direct-diagnosis assertion. Use 'X ka "
        "tendency ho sakta hai' / 'X side par dikh raha hai'.\n"
        "6. NO fear words (danger / serious / khatarnak / fatal).\n"
        "7. NEVER end with a 'Final:' label.\n"
        "8. NEVER invent yogas, planets, houses, or dasha periods "
        "not present in the pack. Stay anchored to the data.\n"
        "9. NEVER predict exact future dates beyond the CURRENT "
        "DASHA window shown in the pack."
    )

    if sensitive_bucket == "mental_health":
        sys_prompt += (
            "\n10. Mental side ko softly handle karo — gentle phrasing, "
            "no harsh labels.")

    try:
        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": fact_pack},
            ],
            temperature=0.5,
            max_tokens=600,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return _render_simple_narrative_static(facts, question)
        return text
    except Exception:
        return _render_simple_narrative_static(facts, question)


def _build_tendency_block(facts: dict) -> str:
    """4th locked block per Phase H2.5 spec. Lists category-based
    tendencies for every RED + YELLOW dim. GREEN dims skipped.
    Returns '' if no weak/yellow dim present (all-GREEN chart)."""
    dims = facts.get("dimensions") or {}
    lines = ["👉 Tendency issues:"]
    any_added = False
    # Order: vitality → disease_resistance → mental_health →
    # chronic_risk → accident_risk (body first, then mind, then risk)
    order = ["vitality", "disease_resistance", "mental_health",
             "chronic_risk", "accident_risk"]
    for k in order:
        d = dims.get(k) or {}
        v = d.get("verdict")
        if v not in ("RED", "YELLOW"):
            continue
        bucket = _TENDENCY_BY_DIM.get(k, {}).get(v) or []
        for item in bucket:
            lines.append(f"- {item}")
            any_added = True
    if not any_added:
        return ""
    return "\n".join(lines)


# One-line action by Primary dim (Focus block).
_FOCUS_BY_PRIMARY = {
    "vitality":           ("Sleep, hydration aur protein-rich diet pe "
                           "focus karo, body ko build karne ka time do"),
    "disease_resistance": ("Sleep, hydration, daily light walk + balanced "
                           "diet — recovery channel ko support do"),
    "chronic_risk":       ("Periodic basic checkup + preventive lifestyle, "
                           "small issues ko early address karo"),
    "mental_health":      ("Daily 10-min breathing, journaling, trusted "
                           "insaan se baat — mental peace ko priority do"),
    "accident_risk":      ("Driving / sports / sharp-object care, "
                           "jaldbaazi avoid, daily mindfulness rakho"),
}


def _rank_dims_by_strength(dims: dict):
    """Return list of (score, key) sorted ascending — weakest first."""
    ranked = []
    for k, d in dims.items():
        v = (d or {}).get("verdict")
        if v in _STRENGTH:
            ranked.append((_STRENGTH[v], k))
    ranked.sort(key=lambda t: t[0])
    return ranked


def _build_verdict_block(facts: dict, question: str) -> str:
    """Generic 3-line locked verdict block (non-comparative path).
    Format:
      🎯 Final Verdict:
      Primary factor: <soft label>
      Secondary factor: <2nd weakest OR Lifestyle/routine load>
      Focus: <one action line>
    """
    dims = facts.get("dimensions") or {}
    ranked = _rank_dims_by_strength(dims)
    if not ranked:
        return ""

    primary_score, primary_key = ranked[0]
    primary_label = _PRIMARY_LABEL_SOFT.get(primary_key, primary_key)

    # Tie at the lowest score level
    tied = [k for s, k in ranked if s == primary_score]
    has_behaviour = bool(_BEHAVIOUR_RX.search(question or ""))

    if len(tied) >= 2 and not has_behaviour:
        # Two equally weakest dims — explicit equal-impact line
        a, b = tied[0], tied[1]
        a_lbl = _PRIMARY_LABEL_SOFT.get(a, a).replace(" weak", "").replace(
            " support", "").replace(" awareness needed", "")
        b_lbl = _PRIMARY_LABEL_SOFT.get(b, b).replace(" weak", "").replace(
            " support", "").replace(" awareness needed", "")
        primary_line = (f"Primary factor: {a_lbl} & {b_lbl} both equally "
                        "impacting")
        secondary_line = ""
    else:
        primary_line = f"Primary factor: {primary_label}"
        if has_behaviour:
            secondary = "Lifestyle / routine load"
        elif len(ranked) >= 2:
            sec_key = ranked[1][1]
            secondary = _SECONDARY_LABEL.get(sec_key, sec_key)
        else:
            secondary = "—"
        secondary_line = f"Secondary factor: {secondary}"

    focus = _FOCUS_BY_PRIMARY.get(
        primary_key,
        "Routine, rest, hydration aur calm habits maintain karo")

    parts = ["🎯 Final Verdict:", primary_line]
    if secondary_line:
        parts.append(secondary_line)
    parts.append(f"Focus: {focus}")
    return "\n".join(parts)


def _build_comparative_verdict(facts: dict, pair, question: str) -> str:
    """3-line locked verdict for comparative-intent questions.
    Uses _group_strength scoring + soft mental phrasing."""
    a_keys, a_label, b_keys, b_label = pair
    dims = facts.get("dimensions") or {}
    a_score, a_v = _group_strength(dims, a_keys)
    b_score, b_v = _group_strength(dims, b_keys)
    has_behaviour = bool(_BEHAVIOUR_RX.search(question or ""))

    def soft_label(label, keys):
        # Apply Y rule: mental_health → soft phrasing
        if "mental_health" in keys:
            return "Mental wellbeing"
        return label

    a_disp = soft_label(a_label, a_keys)
    b_disp = soft_label(b_label, b_keys)

    if abs(a_score - b_score) <= 0.6:
        primary_line = (f"Primary factor: {a_disp} & {b_disp} both "
                        "equally impacting")
        secondary_line = ""
        focus_key = a_keys[0]
    else:
        if a_score < b_score:
            weak_disp, strong_disp = a_disp, b_disp
            focus_key = a_keys[0]
        else:
            weak_disp, strong_disp = b_disp, a_disp
            focus_key = b_keys[0]
        primary_line = f"Primary factor: {weak_disp} weak"
        if has_behaviour:
            secondary_line = "Secondary factor: Lifestyle / routine load"
        else:
            secondary_line = (f"Secondary factor: {strong_disp} relatively "
                              "better but support needed")

    focus = _FOCUS_BY_PRIMARY.get(
        focus_key,
        "Routine, rest, hydration aur calm habits maintain karo")

    parts = ["🎯 Final Verdict:", primary_line]
    if secondary_line:
        parts.append(secondary_line)
    parts.append(f"Focus: {focus}")
    return "\n".join(parts)


def _detect_compare_pair(question: str):
    """Return (a_keys, a_label, b_keys, b_label) if question is a true
    comparative with two distinct concept groups. Else None."""
    if not question or not _COMPARATIVE_RX.search(question):
        return None
    matched = []
    seen_sigs = set()
    for rx, keys, label in _DIM_CONCEPTS:
        if rx.search(question):
            sig = tuple(sorted(keys))
            if sig in seen_sigs:
                continue
            seen_sigs.add(sig)
            matched.append((keys, label))
    if len(matched) < 2:
        return None
    a_keys, a_label = matched[0]
    b_keys, b_label = matched[1]
    return a_keys, a_label, b_keys, b_label


def _group_strength(dims: dict, keys):
    """Average strength score across a group of dim keys.
    Returns (avg_score, consensus_verdict) — verdicts already
    inverted-aware in engine, so GREEN==strong regardless of dim type."""
    scores, verdicts = [], []
    for k in keys:
        d = dims.get(k) or {}
        v = d.get("verdict", "?")
        if v in _STRENGTH:
            scores.append(_STRENGTH[v])
            verdicts.append(v)
    if not scores:
        return (0.0, "?")
    avg = sum(scores) / len(scores)
    label = verdicts[0] if all(v == verdicts[0] for v in verdicts) else "MIXED"
    return (avg, label)


def _compare_one_liner(dims: dict, a_keys, a_label, b_keys, b_label) -> str:
    a_score, a_v = _group_strength(dims, a_keys)
    b_score, b_v = _group_strength(dims, b_keys)
    state_word = {"GREEN": "strong", "YELLOW": "mixed",
                  "RED": "weak", "MIXED": "mixed"}

    # Phase H2.3.1 (C): tie band widened to <= 0.6 to catch
    # boundary cases on a 1-3 scale (e.g. body avg 1.5 vs mental 1.0)
    if abs(a_score - b_score) <= 0.6:
        if a_v == "RED" and b_v == "RED":
            return (f"Is case me {a_label} aur {b_label} dono weak "
                    f"phase me hain — sirf ek nahi, dono ko saath "
                    f"improve karna padega (rest, hydration, breathing, "
                    f"routine sab parallel chalein).")
        if a_v == "GREEN" and b_v == "GREEN":
            return (f"{a_label} aur {b_label} dono supportive hain — "
                    f"balanced state, regular discipline maintain karo.")
        a_st = state_word.get(a_v, "uncertain")
        b_st = state_word.get(b_v, "uncertain")
        return (f"{a_label} aur {b_label} dono {a_st}/{b_st} similar "
                f"level pe — koi ek dominant nahi, balanced approach "
                f"better hai.")

    # Clear difference — name the weaker/stronger channel
    if a_score < b_score:
        weak_l, weak_v = a_label, a_v
        strong_l, strong_v = b_label, b_v
    else:
        weak_l, weak_v = b_label, b_v
        strong_l, strong_v = a_label, a_v
    return (f"Comparison me {weak_l} {state_word.get(weak_v,'?')} side "
            f"pe hai aur {strong_l} relatively "
            f"{state_word.get(strong_v,'?')} — primary focus "
            f"{weak_l} restoration pe rakho, doosre channel ko "
            f"maintenance mode me chalao.")


# ── DIRECT formatters ──────────────────────────────────────────────
def _direct_vitality_check(facts: dict, question: str = "") -> str:
    dims = facts.get("dimensions") or {}
    yogas = facts.get("yogas") or []
    sub = facts.get("sub_flags") or {}

    lines = ["💚 Aapki health picture (5 dimensions):"]
    for key in ("vitality", "disease_resistance", "chronic_risk",
                 "mental_health", "accident_risk"):
        d = dims.get(key) or {}
        v = d.get("verdict", "?")
        emoji = _PATH_EMOJI.get(v, "")
        lines.append(f"  • {_DIM_LABEL[key]}: {emoji} {_verdict_word(d)}")
        if d.get("reason"):
            lines.append(f"      └ {d['reason']}")

    if yogas:
        lines.append(f"\nHealth yogas noted: {', '.join(yogas)}")
    else:
        lines.append("\nKoi major Arishta / Balarishta yog active nahi mila.")

    # Phase H2.3: comparative intent overrides single-dim Final line
    pair = _detect_compare_pair(question) if question else None
    if pair:
        final = _compare_one_liner(dims, *pair)
    else:
        final = _vitality_one_liner(dims, sub, yogas)
    if final:
        lines.append(f"\nFinal: {final}")
    return "\n".join(lines)


def _vitality_one_liner(dims: dict, sub: dict, yogas: list) -> str:
    vt = dims.get("vitality", {}).get("verdict", "")
    cr = dims.get("chronic_risk", {}).get("verdict", "")
    mh = dims.get("mental_health", {}).get("verdict", "")
    ar = dims.get("accident_risk", {}).get("verdict", "")
    dr = dims.get("disease_resistance", {}).get("verdict", "")

    if vt == "GREEN" and cr == "GREEN" and mh == "GREEN":
        return ("Overall health channels supportive — basic discipline "
                "(neend, paani, exercise) maintain karte raho.")
    if cr == "RED":
        return ("Chronic-risk zone elevated hai — periodic checkup aur "
                "preventive lifestyle (saad khana, regular sleep) "
                "mukhya priority hai.")
    if mh == "RED":
        return ("Mental peace zone stressed dikh raha — daily routine me "
                "breathing, journaling aur proper rest add karo, "
                "trusted insaan se baat karna bhi helpful rahega.")
    if vt == "RED":
        return ("Vitality channel weak — proper neend, paani aur "
                "balanced diet pe focus karo, body ko build karne ka "
                "time dena hai.")
    if ar == "RED":
        return ("Accident risk zone elevated — driving, sports, sharp "
                "objects me extra mindfulness rakho, jaldbaazi avoid.")
    if dr == "RED":
        return ("Recovery power kam dikh raha — chhoti problem ko bhi "
                "ignore mat karo, rest aur hydration maintain karo.")
    if "Vipreet-Recovery" in yogas:
        return ("Mixed picture par Vipreet-Recovery yog active hai — "
                "setbacks ke baad bounce-back ki capacity strong hai.")
    return ("Mixed picture — preventive care + regular checkup aapki "
            "health ke liye sabse achchha plan hai.")


def _direct_yoga_check(facts: dict, question: str = "") -> str:
    # Phase H2.3.1 (D): accepts question kwarg for signature uniformity
    # so caller can drop the try/except TypeError wrapper. yoga_check
    # itself doesn't use comparative intent (yoga audit ≠ dim compare).
    _ = question  # explicitly unused
    yogas = facts.get("yogas") or []
    sub = facts.get("sub_flags") or {}
    lines = ["✨ Health-yoga audit (chart se):"]
    if yogas:
        for y in yogas:
            tag = ""
            if y == "Vipreet-Recovery":
                tag = " (recovery / bounce-back power)"
            elif y == "Arishta":
                tag = " (vitality caution marker)"
            elif y == "Balarishta":
                tag = " (early-life vulnerability marker)"
            lines.append(f"  ✓ {y}{tag}")
    else:
        lines.append("  Koi major Arishta / Balarishta / Vipreet "
                      "yog active nahi.")

    missing = [y for y in ("Arishta", "Balarishta", "Vipreet-Recovery")
               if y not in yogas]
    if missing:
        lines.append(f"\nNot active: {', '.join(missing)}")

    if sub.get("vipreet_recovery_active"):
        final = ("Vipreet-Recovery active hai — setbacks ke baad "
                 "recovery ki capacity classical strong yog hai.")
    elif sub.get("arishta_present") or sub.get("balarishta_present"):
        final = ("Caution-marker yog active hai — preventive lifestyle + "
                 "regular self-check (sleep, energy, routine) track karte "
                 "raho, yeh aapki neend chain me rakhega.")
    elif yogas:
        final = ("Kuch supportive yog hain — par alone enough nahi, "
                 "lifestyle discipline + checkup zaroori.")
    else:
        final = ("Major health-yog absent — yeh neutral hai (na bahut "
                 "achcha na bahut bura), regular care pe focus karo.")
    lines.append(f"\nFinal: {final}")
    return "\n".join(lines)


_DIRECT_FORMATTERS = {
    "vitality_check": _direct_vitality_check,
    "yoga_check":     _direct_yoga_check,
}


# ── Phase H2.4: Locked Universal Verdict Override ──────────────────
# Replaces H2.3.1 _force_comparative_final. Now handles BOTH paths:
#   - comparative Q → _build_comparative_verdict
#   - general Q    → _build_verdict_block
# Always strips any LLM-written 'Final:' line and appends the locked
# 3-line verdict block. Idempotent — safe to call multiple times.
def _force_locked_verdict(text: str, facts: dict, question: str) -> str:
    if not text:
        return text
    pair = _detect_compare_pair(question or "")
    if pair:
        block = _build_comparative_verdict(facts, pair, question or "")
    else:
        block = _build_verdict_block(facts, question or "")
    if not block:
        return text

    # Phase H2.5: append Tendency-issues block when intent matches.
    tendency_block = ""
    if question and _TENDENCY_INTENT_RX.search(question):
        tendency_block = _build_tendency_block(facts)

    # Strip ALL existing 'Final:' lines (case-insensitive) AND any
    # existing locked verdict block AND any existing Tendency block
    # (idempotency on re-runs / cache rehydration).
    lines = text.splitlines()
    cleaned, in_v_block, in_t_block = [], False, False
    for ln in lines:
        stripped = ln.lstrip()
        low = stripped.lower()
        if stripped.startswith("🎯 Final Verdict"):
            in_v_block = True
            continue
        if stripped.startswith("👉 Tendency issues"):
            in_t_block = True
            continue
        if in_v_block:
            if (low.startswith("primary factor")
                    or low.startswith("secondary factor")
                    or low.startswith("focus:")):
                continue
            if stripped == "":
                continue
            in_v_block = False
        if in_t_block:
            if stripped.startswith("- ") or stripped.startswith("•"):
                continue
            if stripped == "":
                continue
            in_t_block = False
        if low.startswith("final:"):
            continue
        cleaned.append(ln)

    out = "\n".join(cleaned).rstrip() + "\n\n" + block
    if tendency_block:
        out += "\n\n" + tendency_block
    return out


# ── NARRATIVE: build engine fact pack for LLM (lean) ────────────────
def _build_llm_fact_block(facts: dict, route: str) -> str:
    dims = facts.get("dimensions") or {}
    sub = facts.get("sub_flags") or {}
    bs = facts.get("brand_safety") or {}
    lines = [
        "═══════════════════════════════════════════════",
        "🔒 HEALTH ENGINE — LOCKED FACTS (do not invent)",
        "═══════════════════════════════════════════════",
    ]
    for key in ("vitality", "disease_resistance", "chronic_risk",
                 "mental_health", "accident_risk"):
        d = dims.get(key) or {}
        inv = " [INVERTED]" if d.get("inverted") else ""
        lines.append(
            f"{_DIM_LABEL[key]}{inv}: {d.get('verdict','?')} "
            f"[severity={d.get('severity','?')}, "
            f"confidence={d.get('confidence','?')}] — "
            f"{d.get('reason','')}"
        )
    lines.append(f"Sub-flags: {sub}")

    yogas = facts.get("yogas") or []
    lines.append(f"Health yogas: {', '.join(yogas) if yogas else 'NONE'}")

    lines.append(
        "BRAND-SAFETY (must obey): doctor_disclaimer_required="
        f"{bs.get('doctor_disclaimer_required')}, "
        f"diagnosis_ban_active={bs.get('diagnosis_ban_active')}, "
        f"death_prediction_blocked={bs.get('death_prediction_blocked')}"
    )
    lines.append("═══════════════════════════════════════════════")
    return "\n".join(lines)


_NARRATIVE_INSTRUCTIONS = {
    "disease_risk": (
        "User asking 'baar-baar beemar / immunity weak / recovery slow'. "
        "Use disease_resistance dimension + Mars/Mercury health + 6L "
        "vipreet logic. SUPPORTIVE tone — never alarming.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Recovery / immunity picture:'\n"
        "Line 2: '• Current channel strength: <one-phrase>'\n"
        "Line 3: '• Mukhya theme: <one-phrase, no disease names>'\n"
        "Line 4: '• Practical step: <one-phrase, lifestyle/diet/checkup>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one calm sentence>'.\n"
        "NO disease names, NO planet names, NO house numbers, "
        "NO 'tumhe X hai' phrasing. Use 'risk indication' not "
        "'tumhe yeh hai'."
    ),
    "chronic_risk": (
        "User asking about chronic / long-term / lambi bimari / "
        "hereditary risk. Use chronic_risk dimension (INVERTED — "
        "GREEN means LOW risk). SUPPORTIVE tone, preventive framing.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Chronic-risk zone picture:'\n"
        "Line 2: '• Current zone level: <one-phrase>'\n"
        "Line 3: '• Mukhya theme: <one-phrase generic>'\n"
        "Line 4: '• Preventive plan: <one-phrase concrete action>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one calm sentence>'.\n"
        "NO disease names, NO 'tumhe X hai', NO fear words."
    ),
    "mental_health": (
        "User asking about stress / anxiety / depression / mood / sleep / "
        "mental peace. EXTREMELY GENTLE tone — this is sensitive bucket. "
        "Use mental_health dimension. Never diagnose, never name "
        "specific disorder.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Mental peace picture:'\n"
        "Line 2: '• Current state: <one-phrase, gentle>'\n"
        "Line 3: '• Mukhya theme: <one-phrase, generic — Moon/peace etc.>'\n"
        "Line 4: '• Supportive step: <one concrete action — meditation, "
        "walk, journaling, trusted insaan se baat>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one warm calm sentence>'.\n"
        "NO disease/disorder names (depression/anxiety as conditions), "
        "NO 'tumhe X hai', NO fear words. Reply layer will append "
        "helpline mention automatically."
    ),
    "accident_risk": (
        "User asking about accident / injury / sudden harm risk. "
        "INVERTED dim (GREEN = low risk). CALM tone, mindful framing.\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Accident-risk zone picture:'\n"
        "Line 2: '• Current zone level: <one-phrase>'\n"
        "Line 3: '• Mukhya theme: <one-phrase generic — Mars/Ketu energy etc>'\n"
        "Line 4: '• Mindful step: <one concrete — driving care, sports "
        "warmup, sharp object care>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one calm sentence>'.\n"
        "NO disease names, NO planet names, NO fear words like 'danger'."
    ),
    "general_health_overview": (
        "User ne general health/swasthya related question pucha hai jo "
        "specific pattern (vitality/disease/chronic/mental/accident) me "
        "fit nahi hota. Engine ne already 5-dimension picture DIRECT "
        "format me upar print kar di hai. Aapka kaam: us picture ke "
        "neeche 50-70 word ka short Hinglish narrative add karo jo:\n"
        "  1. User ki actual question ko address kare (paraphrase mat "
        "     karo, direct supportive answer do)\n"
        "  2. 5-dim verdict ke 1-2 strongest signals ko plain language "
        "     me concrete preventive guidance me convert kare\n"
        "  3. Ek practical takeaway de\n"
        "Format:\n"
        "  Line 1: blank\n"
        "  Line 2: '✏️ Aapke sawal pe focus:'\n"
        "  Line 3-5: 50-70 word narrative\n"
        "  Line 6: blank\n"
        "  Line 7: 'Final: <one calm direct sentence>'\n"
        "NO disease names, NO planet names, NO house numbers, "
        "NO RED/YELLOW/GREEN words, NO 'tumhe X hai' phrasing, "
        "NO fear words (danger/serious/khatarnak), NO timing/date "
        "predictions, NO cure-guarantees."
    ),
}


def _llm_narrative(facts: dict, route: str, question: str,
                    sensitive_bucket: Optional[str]) -> str:
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return _direct_vitality_check(facts, question=question)
    except Exception:
        return _direct_vitality_check(facts, question=question)

    fact_block = _build_llm_fact_block(facts, route)
    instruction = _NARRATIVE_INSTRUCTIONS.get(
        route, "Summarise the 5-dim health picture in 60-80 words "
               "Hinglish supportive tone. End with 'Final: <one-line>'.")

    bucket_note = ""
    if sensitive_bucket:
        bucket_note = (
            f"\nSENSITIVE BUCKET ACTIVE: {sensitive_bucket} — extra "
            "gentle tone, no labels, no fear words, no diagnosis "
            "phrasing. Reply layer will append a bucket-specific "
            "support line + doctor disclaimer automatically.")

    sys_prompt = (
        "You are a Vedic-astrology HEALTH translator. Tone is "
        "SUPPORTIVE, CALM, NON-ALARMING — never blunt or fear-inducing.\n\n"
        "RULES:\n"
        "1. Use ONLY the LOCKED FACTS below. Never invent planets, "
        "houses, dignities, or yogas not listed.\n"
        "2. Reply in Hinglish, warm and direct.\n"
        "3. ⚠️ DO NOT write any 'Final:' line yourself. The system "
        "appends a deterministic 3-line verdict block "
        "('🎯 Final Verdict / Primary factor / Secondary factor / "
        "Focus') automatically — your job is ONLY the explanation "
        "(Samajh) section.\n"
        "4. No 'Beta', 'Pranam', 'I sense', 'I understand'.\n"
        "5. NEVER write engine codes like 'RED', 'YELLOW', 'GREEN', "
        "'verdict', 'tier', 'severity', 'confidence', 'sub_flags'.\n"
        "6. NEVER mention specific planets, houses, signs, dignities "
        "UNLESS the user explicitly asked WHY / technical / planet name.\n"
        "7. ⚠️ NEVER name a specific disease (diabetes / cancer / "
        "depression / asthma / heart disease etc.) — use generic "
        "phrasing like 'metabolic stress zone', 'cardiac stress zone', "
        "'low-mood zone', 'respiratory zone'.\n"
        "8. ⚠️ NEVER write 'tumhe X hai' / 'aapko X hai' / 'you have X' "
        "— use 'X risk indication present' / 'X zone elevated'.\n"
        "9. ⚠️ NEVER use fear words: 'danger', 'serious problem', "
        "'khatarnak', 'ghatak', 'fatal', 'deadly', 'life-threatening'. "
        "Use 'dhyan dena chahiye', 'preventive care useful', "
        "'important matter' instead.\n"
        "10. ⚠️ NEVER predict death, longevity end, or specific dates "
        "— this engine is NON-TIMING.\n"
        "11. ⚠️ NEVER guarantee cure — use 'supportive indication'.\n"
        "12. ⚠️ TONE-GUARD (CRITICAL): DO NOT suggest doctor, "
        "professional, therapist, expert, specialist, counsellor, "
        "or ANY medical/clinical consultation. NO 'doctor se milein', "
        "'professional se baat karo', 'expert guidance lo', "
        "'therapist consult karo', 'mental-health professional', "
        "'specialist dikhaiye'. Yeh static engine PREVENTIVE INSIGHT "
        "hai, doctor-replacement nahi — referral line reply layer "
        "WARNING routes pe automatic add hoti hai, narrative me MAT "
        "likho. Tone supportive, practical, self-action oriented "
        "rakho (sleep / hydration / breathing / journaling / walking "
        "/ talking to a trusted friend / lifestyle tweaks).\n"
        "13. Follow the per-route format EXACTLY.\n\n"
        f"{fact_block}{bucket_note}\n\n"
        f"INSTRUCTION: {instruction}"
    )
    try:
        resp = client.chat.completions.create(
            model=os.environ.get("HEALTH_LLM_MODEL", "gpt-5.4"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
            max_tokens=350,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return _direct_vitality_check(facts, question=question)
        return text
    except Exception as e:
        print(f"[health_static.llm] narrative call failed: {e}", flush=True)
        return _direct_vitality_check(facts, question=question)


# ── Public entry point ──────────────────────────────────────────────
_ENGINE_SCOPE = "non_timing"


def handle_health_question(question: str, kundli: dict,
                            birth: dict | None = None
                            ) -> Optional[Dict[str, Any]]:
    """Route + serve a NON-TIMING general health question."""
    t_start = _time.time()
    chart_fp = _chart_fingerprint(kundli) if isinstance(kundli, dict) else ""
    sensitive = detect_sensitive_bucket(question or "")

    tele_state = {
        "regex_mode": None, "regex_route": None,
        "llm_mode": None, "llm_route": None,
        "llm_confidence": None, "llm_reason": None,
        "validator_flags": [], "validator_action": "none",
        "facts": None,
        "brand_safety_action": None,
        "sensitive_bucket": sensitive,
    }

    def _emit(mode_f: str, route_f: str, cache_hit: bool) -> None:
        try:
            f = tele_state.get("facts") or {}
            dims = (f.get("dimensions") or {}) if isinstance(f, dict) else {}
            kp = (f.get("kp_csl") or {}) if isinstance(f, dict) else {}
            vt = dims.get("vitality") or {}
            dr = dims.get("disease_resistance") or {}
            cr = dims.get("chronic_risk") or {}
            mh = dims.get("mental_health") or {}
            ar = dims.get("accident_risk") or {}
            h1 = (kp.get("h1") or {}) if isinstance(kp, dict) else {}
            h6 = (kp.get("h6") or {}) if isinstance(kp, dict) else {}
            h8 = (kp.get("h8") or {}) if isinstance(kp, dict) else {}
            conflict_flag = any(
                d.get("conflict_flag") for d in (vt, dr, cr, mh, ar)
            ) if dims else None
            low_conf = sum(
                1 for d in (vt, dr, cr, mh, ar)
                if d.get("confidence") == "LOW"
            ) if dims else None

            _telemetry_log({
                "ts": int(t_start),
                "question": question or "",
                "chart_fp": chart_fp,
                "regex_mode": tele_state["regex_mode"],
                "regex_route": tele_state["regex_route"],
                "llm_mode": tele_state["llm_mode"],
                "llm_route": tele_state["llm_route"],
                "llm_confidence": tele_state["llm_confidence"],
                "llm_reason": tele_state["llm_reason"],
                "final_mode": mode_f,
                "final_route": route_f,
                "cache_hit": cache_hit,
                "latency_ms": int((_time.time() - t_start) * 1000),
                "validator_flags": tele_state["validator_flags"],
                "validator_action": tele_state["validator_action"],
                "vitality_v": vt.get("verdict") if dims else None,
                "disease_v": dr.get("verdict") if dims else None,
                "chronic_v": cr.get("verdict") if dims else None,
                "mental_v": mh.get("verdict") if dims else None,
                "accident_v": ar.get("verdict") if dims else None,
                "kp_h1_v": (
                    f"{h1.get('csl_planet','?')}/{h1.get('verdict','?')}"
                    if h1 else None),
                "kp_h6_v": (
                    f"{h6.get('csl_planet','?')}/{h6.get('verdict','?')}"
                    if h6 else None),
                "kp_h8_v": (
                    f"{h8.get('csl_planet','?')}/{h8.get('verdict','?')}"
                    if h8 else None),
                "kp_engine_ver": kp.get("engine_version") if kp else None,
                "conflict_flag": conflict_flag,
                "confidence_low_count": low_conf,
                "brand_safety_action": tele_state["brand_safety_action"],
                "sensitive_bucket": tele_state["sensitive_bucket"],
            })
        except Exception:
            pass

    if not is_health_question(question or ""):
        return None
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        out = {
            "text": ("Health analysis aapki janm-kundli ke bina possible "
                      "nahi. Pehle birth details save karein.\n\n"
                      "Final: Pehle kundli, fir health analysis."),
            "mode": "FAILSAFE", "route": "no_kundli",
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": None,
        }
        _emit("FAILSAFE", "no_kundli", False)
        return out

    mode, route = route_health_question(question)
    tele_state["regex_mode"] = mode
    tele_state["regex_route"] = route

    # ── WARNING — locked safe template (no engine, no LLM, no cache) ──
    if mode == "WARNING":
        raw_text = WARNINGS.get(route, "")
        # WARNING (timing/serious) is the ONLY path that gets the doctor
        # disclaimer + sensitive-bucket extra (Phase H2.1 user policy).
        # Other modes (DIRECT/NARRATIVE/HYBRID) skip doctor mention to
        # keep the static engine positioned as preventive insight, not
        # doctor replacement.
        text, w_flags = apply_safety_tail(raw_text,
                                           sensitive_bucket=sensitive,
                                           add_doctor=True)
        bs = [f"warning:{route}"]
        if "doctor_disclaimer_added" in w_flags:
            bs.append("doctor_disclaimer_added")
        tele_state["validator_flags"] = w_flags
        tele_state["validator_action"] = "warning_tail"
        tele_state["brand_safety_action"] = ",".join(bs)
        out = {
            "text": text, "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": None,
            "router": None,
            "sensitive_bucket": sensitive,
        }
        _emit(mode, route, False)
        return out

    # ── HYBRID re-route via LLM classifier (Option A — runs BEFORE cache) ──
    router_meta = None
    if mode == "HYBRID" and route == "general_health_overview":
        try:
            from health_static.llm_router import classify_health_question
            cls_mode, cls_route, conf, reason = classify_health_question(
                question)
        except Exception as _re:
            print(f"[health_static] llm_router error: {_re}", flush=True)
            cls_mode = cls_route = None
            conf = 0.0
            reason = "router exception"
        tele_state["llm_mode"] = cls_mode
        tele_state["llm_route"] = cls_route
        tele_state["llm_confidence"] = conf
        tele_state["llm_reason"] = reason
        router_meta = {"cls_mode": cls_mode, "cls_route": cls_route,
                        "confidence": conf, "reason": reason}
        if (cls_mode and cls_route and conf >= 0.75
                and not (cls_mode == "HYBRID"
                         and cls_route == "general_health_overview")):
            mode, route = cls_mode, cls_route
            if mode == "WARNING":
                raw_w = WARNINGS.get(route, "")
                text_w, w_flags = apply_safety_tail(
                    raw_w, sensitive_bucket=sensitive, add_doctor=True)
                bs = [f"warning:{route}", "via_llm_router"]
                if "doctor_disclaimer_added" in w_flags:
                    bs.append("doctor_disclaimer_added")
                tele_state["validator_flags"] = w_flags
                tele_state["validator_action"] = "warning_tail"
                tele_state["brand_safety_action"] = ",".join(bs)
                out = {
                    "text": text_w, "mode": mode, "route": route,
                    "scope": _ENGINE_SCOPE,
                    "dimensions": None, "cache_hit": False,
                    "engine_facts": None, "router": router_meta,
                    "sensitive_bucket": sensitive,
                }
                _emit(mode, route, False)
                return out

    # ── Cache check ──
    # Phase H2.4: include question in cache key for ALL non-DIRECT modes.
    # The locked verdict block is question-context-aware (comparative pair
    # detection + behaviour-keyword Secondary slot), so two NARRATIVE Qs on
    # the same route can produce different verdicts. Cache MUST not collapse
    # them. (Pre-H2.4 only HYBRID included the question.)
    # Phase H2.5: include question in cache key for ALL modes (DIRECT
    # added). Tendency-intent detection + comparative-pair detection +
    # behaviour-keyword Secondary slot ALL depend on question. Even
    # DIRECT mode now produces question-aware output via the locked
    # verdict + tendency blocks. Cache must not collapse different Qs.
    _q_for_key = question
    # Cache namespace bumped to v2 in Phase H2.2.2 — invalidates stale
    # entries written before the doctor-mention/tone-guard cleanup
    # (H2.1 + H2.2 + H2.2.1) so legacy "professional support" / "doctor
    # consult" text cannot resurface from cache. Bump again on any
    # future policy change to the static engine output.
    # Phase H2.6: namespace bumped v4→v5. Output style flipped from
    # 4-block structured to flowing narrative — old cached entries are
    # structurally incompatible with new presentation contract.
    # Phase H2.7: namespace bumped v5→v6. LLM now receives full
    # health-kundli pack (planets+lords+karakas+KP chains+dasha) and
    # cherry-picks per question — answers are richer and may include
    # planet/house attribution. Old v5 entries are summary-only.
    _ns = f"health_static_v6_{_OUTPUT_STYLE}"
    cache_key = make_cache_key(birth, kundli, _ns, route,
                                question=_q_for_key)
    cached = get_cached(cache_key)
    if cached:
        out = {
            "text": cached["text"], "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": cached.get("meta", {}).get("dimensions"),
            "cache_hit": True, "engine_facts": None,
            "router": router_meta,
            "sensitive_bucket": sensitive,
        }
        _emit(mode, route, True)
        return out

    # ── Compute facts ──
    facts = compute_health_facts(kundli)
    tele_state["facts"] = facts
    if facts.get("error"):
        # Phase H2.1: failsafe also drops doctor disclaimer (per policy).
        out = {
            "text": (f"Engine error: {facts['error']}\n\n"
                      "Final: Kundli check karein."),
            "mode": "FAILSAFE", "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": facts,
            "router": router_meta,
            "sensitive_bucket": sensitive,
        }
        _emit("FAILSAFE", route, False)
        return out

    # ── Phase H2.6: SIMPLE-OUTPUT branch ──
    # Default style. Engine truth + locked verdict + tendency are
    # computed internally (passed to LLM as fact pack); presentation
    # layer renders one flowing Hinglish narrative — no emojis, no
    # bullet headers, no dim labels. Set HEALTH_OUTPUT_STYLE=structured
    # to revert to H2.5 4-block output (debug/admin only).
    if _OUTPUT_STYLE == "simple":
        # Phase H2.7: pass full kundli to LLM (Path B+ — no pre-curation).
        narrative_raw = _render_simple_narrative_llm(
            facts, question, sensitive, kundli=kundli)
        # Validator scrub for safety (referral/disease/fear words).
        # H2.7.1: simple-mode opts into Vedic-vocab pass-through —
        # planet/house/sign/dignity words stay (those are the
        # attribution LLM forms from the full kundli pack).
        text, v_flags, v_action = validate_health_llm_output(
            narrative_raw,
            user_question=question,
            sensitive_bucket=sensitive,
            allowed_yogas=facts.get("yogas") or [],
            direct_fallback_text=_render_simple_narrative_static(
                facts, question),
            allow_vedic_terms=True,
        )
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = v_action

        # H2.6 strict contract: NEVER end with a "Final:" label.
        # Validator's _ensure_final_line auto-appends one — strip it
        # back out for the simple-narrative presentation contract.
        text = re.sub(
            r"\n+\s*Final\s*:[^\n]*\s*$", "", text,
            flags=re.IGNORECASE,
        ).rstrip()

        bs_actions = []
        if "doctor_disclaimer_added" in v_flags:
            bs_actions.append("doctor_disclaimer_added")
        if any(f.startswith("disease_name") for f in v_flags):
            bs_actions.append("diagnosis_ban_triggered")
        if "diagnosis_assert_softened" in v_flags:
            bs_actions.append("assert_softened")
        if "fear_softened" in v_flags:
            bs_actions.append("fear_softened")
        if "cure_guarantee_softened" in v_flags:
            bs_actions.append("cure_softened")
        if "death_prediction_stripped" in v_flags:
            bs_actions.append("death_stripped")
        if sensitive:
            bs_actions.append(f"sensitive:{sensitive}")
        bs_actions.append("style:simple")
        tele_state["brand_safety_action"] = ",".join(bs_actions) or "none"

        put_cached(cache_key, text, {
            "dimensions": facts.get("dimensions"),
            "composite": facts.get("composite_score"),
            "mode": mode, "route": route,
            "sensitive_bucket": sensitive, "style": "simple",
        })
        out = {
            "text": text, "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": facts.get("dimensions"),
            "cache_hit": False, "engine_facts": facts,
            "router": router_meta,
            "sensitive_bucket": sensitive,
        }
        _emit(mode, route, False)
        return out

    # ── Build text per mode (validator runs on every LLM-touched mode) ──
    # (legacy structured path — only when HEALTH_OUTPUT_STYLE=structured)
    if mode == "DIRECT":
        formatter = _DIRECT_FORMATTERS.get(route, _direct_vitality_check)
        # Phase H2.3 + H2.3.1 (D): all DIRECT formatters now accept
        # question kwarg uniformly (vitality uses it for comparative
        # intent; yoga_check ignores). Direct call — no try/except mask.
        raw_text = formatter(facts, question=question)
        # Phase H2.4: also append locked verdict block to DIRECT mode
        # so the entire system uses one consistent answer structure.
        raw_text = _force_locked_verdict(raw_text, facts, question)
        # DIRECT text is engine-controlled deterministic — MUST NOT pass
        # through LLM-scrubbing validator (it would strip legitimate
        # words like 'dimensions' and 'Arishta'). Only attach safety
        # tail (final-line + sensitive-bucket extra + doctor disclaimer).
        text, v_flags = apply_safety_tail(raw_text,
                                           sensitive_bucket=sensitive)
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = (
            "soft_tail" if v_flags else "none"
        )
    elif mode == "HYBRID":
        direct_text = _direct_vitality_check(facts, question=question)
        narrative_raw = _llm_narrative(facts, route, question, sensitive)
        narrative, v_flags, v_action = validate_health_llm_output(
            narrative_raw,
            user_question=question,
            sensitive_bucket=sensitive,
            allowed_yogas=facts.get("yogas") or [],
            direct_fallback_text="",
        )
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = v_action
        # Strip 'Final:' from direct so combined text has only one
        direct_clean = "\n".join(
            ln for ln in direct_text.splitlines()
            if not ln.strip().lower().startswith("final:")
        )
        # Phase H2.4: ALL questions get locked 3-line verdict block
        # (Truth from engine + Explanation from LLM + Verdict forced).
        # Comparative path uses _build_comparative_verdict; general
        # path uses _build_verdict_block. LLM's Final: line stripped.
        narrative = _force_locked_verdict(narrative, facts, question)
        text = direct_clean.rstrip() + "\n\n" + narrative.lstrip()
    else:  # NARRATIVE
        narrative_raw = _llm_narrative(facts, route, question, sensitive)
        fallback_for_validator = _direct_vitality_check(
            facts, question=question
        )
        text, v_flags, v_action = validate_health_llm_output(
            narrative_raw,
            user_question=question,
            sensitive_bucket=sensitive,
            allowed_yogas=facts.get("yogas") or [],
            direct_fallback_text=fallback_for_validator,
        )
        tele_state["validator_flags"] = v_flags
        tele_state["validator_action"] = v_action
        # Phase H2.4: locked 3-line verdict block on every NARRATIVE
        # answer — comparative or general, both paths covered.
        text = _force_locked_verdict(text, facts, question)

    # Set brand_safety_action telemetry tag (compact summary)
    bs_actions = []
    if "doctor_disclaimer_added" in tele_state["validator_flags"]:
        bs_actions.append("doctor_disclaimer_added")
    if any(f.startswith("disease_name") for f in tele_state["validator_flags"]):
        bs_actions.append("diagnosis_ban_triggered")
    if "diagnosis_assert_softened" in tele_state["validator_flags"]:
        bs_actions.append("assert_softened")
    if "fear_softened" in tele_state["validator_flags"]:
        bs_actions.append("fear_softened")
    if "cure_guarantee_softened" in tele_state["validator_flags"]:
        bs_actions.append("cure_softened")
    if "death_prediction_stripped" in tele_state["validator_flags"]:
        bs_actions.append("death_stripped")
    if sensitive:
        bs_actions.append(f"sensitive:{sensitive}")
    tele_state["brand_safety_action"] = ",".join(bs_actions) or "none"

    put_cached(cache_key, text, {
        "dimensions": facts.get("dimensions"),
        "composite": facts.get("composite_score"),
        "mode": mode, "route": route,
        "sensitive_bucket": sensitive,
    })

    out = {
        "text": text, "mode": mode, "route": route,
        "scope": _ENGINE_SCOPE,
        "dimensions": facts.get("dimensions"),
        "cache_hit": False, "engine_facts": facts,
        "router": router_meta,
        "sensitive_bucket": sensitive,
    }
    _emit(mode, route, False)
    return out
