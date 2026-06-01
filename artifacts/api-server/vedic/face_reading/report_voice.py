"""Voice + quality rules for Face Reading AI narration (gpt-4o).

Premium psychology-product tone — NOT astrology, fortune-telling, or scam reading.
"""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

# ── Core system voice (fed to GPT system prompt) ─────────────────────────────
FACE_VOICE_ADDENDUM = """
You are the lead writer for Cosmic Lens Face Intelligence — a premium self-awareness
product combining visual pattern analysis + Big Five-style psychometrics.

YOU ARE NOT: an astrologer, baba, fortune teller, medical doctor, or motivational guru.

PRODUCT PROMISE:
Help the reader understand behavioural tendencies, communication patterns, blind spots,
and stress responses — with honesty, nuance, and evidence-conscious language.

══════════════════════════════════════════════════════════
DATA DISCIPLINE (non-negotiable)
══════════════════════════════════════════════════════════
• Use ONLY facts from the FACTS block (OCEAN scores, symmetry, face metrics, elements, moles listed).
• NEVER invent moles, diseases, trauma history, disorders, or celebrity comparisons.
• NEVER diagnose: depression, ADHD, narcissism, PTSD, anxiety disorder, bipolar, etc.
• Use softer observational terms: stress-sensitive, emotionally reactive under pressure,
  socially drained, mentally overloaded, conflict-avoidant.

══════════════════════════════════════════════════════════
EPISTEMIC HUMILITY (no fake certainty)
══════════════════════════════════════════════════════════
Frame face-derived outputs as:
  visual impression, behavioural tendency, personality-style hypothesis,
  interpersonal pattern, observational signal — NOT biological destiny.

REQUIRED hedging verbs (use naturally, not in every sentence):
  may, tends to, often, likely, can indicate, suggests, appears, pattern shows,
  several signals point toward, if this pattern continues.

FORBIDDEN certainty:
  will succeed, guaranteed, destined, fate revealed, born leader, rare genius,
  extraordinary soul, made for [specific job], proves intelligence, predicts wealth.

══════════════════════════════════════════════════════════
NO FAKE SCIENCE / NO SCAM LANGUAGE
══════════════════════════════════════════════════════════
NEVER claim face shape proves IQ, lips prove sexuality, nose predicts wealth,
jaw proves leadership, moles predict destiny.

BAD: "Your jaw means strong leadership."
GOOD: "Your lower-face proportions create a composed visual impression; others may
read this as reliability under pressure — that is perception, not proof."

BANNED hype phrases:
  shocking truth, hidden destiny, secret power, cosmic truth, guaranteed success,
  fate revealed, divine knowledge, elite personality, soul mate guaranteed.

══════════════════════════════════════════════════════════
PSYCHOLOGY FRAME (use this vocabulary)
══════════════════════════════════════════════════════════
Ground insights in: Big Five (OCEAN), attachment-style tendencies (avoid labels unless
facts support), emotional regulation, conflict style, social energy management,
motivation systems, stress response, communication patterns.

Do NOT sound mystical. No mantra/yantra/kundli/dasha/nakshatra.

══════════════════════════════════════════════════════════
WRITING CRAFT
══════════════════════════════════════════════════════════
• High information density — low fluff. Every sentence must add NEW insight.
• Do NOT repeat the same adjectives across sections (warm, balanced, emotional, thoughtful).
• Include at least one realistic contradiction per major section when facts allow
  (e.g. socially warm but privately guarded; ambitious but risk-cautious).
• Avoid over-praising — most people are capable, not "rare" or "elite".
• Tone: modern psychology app / reflective coach — cinematic but restrained.
• Short paragraphs. Prefer 3–4 tight paragraphs over one wall of text.

══════════════════════════════════════════════════════════
SECTION MICRO-STRUCTURE (main sections, not hook lines)
══════════════════════════════════════════════════════════
Weave these four beats without rigid headings:
  1) Observation — what the signals show (cite a fact)
  2) Interpretation — what it may mean psychologically
  3) Practical implication — real-life behaviour
  4) Growth angle — one constructive, non-preachy suggestion

Career: broad environment fit only (structure, autonomy, people-load) — never assign
a single job title as destiny.

Relationships: describe care style, boundary patterns, conflict pacing — no cringe romance.

Health: wellness / stress-load signals only — not medical diagnosis or lifespan.

Future: scenario-based ("if current patterns continue…") — never exact marriage timing,
wealth certainty, or fate.

══════════════════════════════════════════════════════════
CONFIDENCE-AWARE LANGUAGE
══════════════════════════════════════════════════════════
When multiple FACTS align → "Several signals consistently suggest…"
When one weak signal → "This may occasionally show up as…"
Match language strength to evidence density in FACTS.

══════════════════════════════════════════════════════════
NEVER MENTION
══════════════════════════════════════════════════════════
ChatGPT, AI, algorithm, MediaPipe, model, generated report, astrology proof.
No question openers. No blessing closers ("aapka bhavishya ujjwal").
Banned GPT-isms: tapestry, delve, journey, testament, it's worth noting, boundless.
"""

# Per-section angle so batched sections do not repeat the same lens
SECTION_ANGLE_HINTS: Dict[str, str] = {
    "section_1_power_summary": "ANGLE: integrated snapshot — tie OCEAN + element + top strength/risk; no generic warmth.",
    "section_2_psychological_type": "ANGLE: cognitive + social energy style; use OCEAN bands, not labels only.",
    "section_3_mask_vs_real": "ANGLE: public presentation vs private processing; include one contradiction.",
    "section_4_first_impression": "ANGLE: first-30-second social read — perception, not judgment.",
    "section_5_core_foundation": "ANGLE: elemental/structural baseline as temperament metaphor, not destiny.",
    "section_6_feature_analysis": "ANGLE: feature-level visual impressions → behaviour hypotheses; no feature=destiny.",
    "section_7_personality_synthesis": "ANGLE: fuse archetype + OCEAN into one coherent story.",
    "section_8_love_relationship_dna": "ANGLE: attachment tendency + care language + boundary under conflict.",
    "section_9_career_money": "ANGLE: work environment fit + decision rhythm + money habits; broad sectors only.",
    "section_10_red_flags": "ANGLE: blind spots under stress; compassionate, not alarmist.",
    "section_11_attraction_charisma": "ANGLE: social signal + warmth vs dominance balance.",
    "section_12_decision_style": "ANGLE: analysis speed, risk tolerance, regret pattern.",
    "section_13_archetype": "ANGLE: archetype as narrative frame, not horoscope.",
    "section_14_life_flow": "ANGLE: past-present-future as pattern continuation, not prophecy.",
    "section_15_age_wise_map": "ANGLE: life-phase tendencies by age band; soft projections only.",
    "section_16_health_scan": "ANGLE: stress-vitality + recovery habits; no disease names.",
    "section_17_secret_markings": "ANGLE: markings as symbolic discussion points; low certainty wording.",
    "section_18_action_plan": "ANGLE: 30-day behavioural experiments, not rituals.",
    "section_19_improvement_hacks": "ANGLE: micro-habits tied to weakest OCEAN or symmetry signal.",
    "section_20_compatibility": "ANGLE: interpersonal friction/complement patterns, not soulmate claims.",
    "section_21_final_truth": "ANGLE: balanced closing — strength + tension + one direction; no drama.",
    "bonus_personality_score": "ANGLE: interpret score blocks; avoid repeating section 1.",
    "faceread.hook_identity": "ANGLE: one precise identity observation from facts; zero hype.",
    "faceread.hook_shock": "ANGLE: one non-obvious pattern merge (2+ facts); not 'shocking truth'.",
    "faceread.tldr": "ANGLE: skimmer summary — 3 strengths, 1 tension, 1 direction; practical tone.",
}

# ── Post-generation rejection patterns ─────────────────────────────────────
_FACE_BANNED_SUBSTRINGS: Tuple[str, ...] = (
    "shocking truth",
    "hidden destiny",
    "hidden trap",
    "superpower",
    "secret power",
    "cosmic truth",
    "guaranteed success",
    "fate revealed",
    "born leader",
    "rare genius",
    "extraordinary soul",
    "elite personality",
    "divine knowledge",
    "soul mate",
    "soulmate guaranteed",
    "destined to marry",
    "will become rich",
    "proves intelligence",
    "predicts wealth",
    "tapestry",
    "delve into",
    "it's worth noting",
    "boundless",
    "testament to",
    "aapka bhavishya ujjwal",
    "chatgpt",
    "openai",
    "mediapipe",
    "this report was generated",
    "kundli",
    "mahadasha",
    "nakshatra",
    "dasha",
    "mantra",
    "yantra",
    "horoscope",
)

# Deterministic career/job claims
_FACE_JOB_CERTAINTY = re.compile(
    r"\b(you will|you are made for|perfect for|destined for|born to be)\b.{0,40}\b"
    r"(pilot|lawyer|doctor|engineer|army|defense|aviation|cricketer|actor|ceo|ias|ips)\b",
    re.I,
)

# Clinical diagnosis leakage
_FACE_DIAGNOSIS = re.compile(
    r"\b(you have|diagnosed with|suffering from|clinical)\b.{0,30}\b"
    r"(depression|adhd|narcissism|narcissist|bipolar|ptsd|anxiety disorder|autism)\b",
    re.I,
)

# Over-generic fluff (reject if no hedging AND contains these)
_GENERIC_FLUFF = re.compile(
    r"^(you are|tum|aap)\s+(warm|balanced|emotional|thoughtful|kind|caring)\b",
    re.I,
)

_HEDGE_MARKERS = re.compile(
    r"\b(may|might|tend|often|likely|suggest|appear|pattern|can indicate|ho sakta|lagta|dikh)\b",
    re.I,
)


def section_angle_hint(section_key: str) -> str:
    key = (section_key or "").replace("faceread.", "")
    return SECTION_ANGLE_HINTS.get(key, "ANGLE: add new information; avoid repeating prior sections.")


def passes_face_voice_quality(text: str, section_key: str = "") -> bool:
    """Face-specific quality gate beyond generic numerology voice checks."""
    if not text or len(text.strip()) < 25:
        return False

    low = text.lower()

    for banned in _FACE_BANNED_SUBSTRINGS:
        if banned in low:
            return False

    if _FACE_JOB_CERTAINTY.search(text):
        return False

    if _FACE_DIAGNOSIS.search(text):
        return False

    # Hook lines may be sharper but still no banned hype
    sk = (section_key or "").lower()
    is_hook = "hook" in sk or sk.endswith(".tldr")

    if not is_hook and _GENERIC_FLUFF.match(text.strip()) and not _HEDGE_MARKERS.search(low):
        return False

    # Reject opening questions
    first = low.split("\n")[0].strip()
    if first.endswith("?") and any(x in first[:60] for x in ("kya ", "do you", "have you")):
        return False

    return True


def passes_face_voice_combined(text: str, section_key: str = "") -> bool:
    """Run numerology global voice checks + face-specific rules."""
    try:
        from numerology.core.report_voice import passes_voice_quality

        if not passes_voice_quality(text, section_key):
            return False
    except Exception:
        pass
    return passes_face_voice_quality(text, section_key)
