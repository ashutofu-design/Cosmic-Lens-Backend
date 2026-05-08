"""
Phase 2.5.11.23 — Premium 7-Chapter Polish (gpt-4o)
====================================================
Layer B for Kundli Milan Pro PDF. Takes:
  - milan_facts        (engine output: koots, total, partners)
  - chapter_scores     (deterministic 7-chapter scores + drivers/cautions/key_facts)
  - d9_marriage        (D9 destiny block — for hidden_truth)
  - synastry           (7L synastry block — for hidden_truth)
  - kp_promise         (KP marriage promise verdict — for hidden_truth)

Returns LLM-rephrased 3-block prose per chapter + Hidden Truth + Special +
Damage + Practical + Verdict — all foreground human language, all KP/Vedic
jargon kept BACKEND-ONLY.

Model: gpt-4o (env COMPAT_PREMIUM_MODEL, fallback gpt-4o-mini).
Toggle: env COMPAT_PREMIUM_POLISH=1 (default off).

Reuses L1 + L2 cache infra from llm_polish.py (different fingerprint prefix).
Branding rule: never name AI/LLM. Defensive — never raises.
"""
from __future__ import annotations

import os
import re
import json
import hashlib
import logging
from typing import Any

from .llm_polish import (
    _cache_get as _l1_get,
    _cache_put as _l1_put,
    _db_cache_get as _l2_get,
    _db_cache_put as _l2_put,
    _normalize_digits,
    ALLOWED_REMEDIES,
    BANNED_TERMS,
)

log = logging.getLogger(__name__)

_PREMIUM_VERSION = "p3"
_DEFAULT_MODEL = "gpt-4o"

CHAPTER_KEYS = ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7"]
# Chapters where a ritual / practical action remedy is naturally appropriate.
# Validator requires ≥1 ALLOWED_REMEDY across these chapters' kya_dhyan combined.
_REMEDY_BEARING = {"ch4", "ch7"}

BANNED_REMEDY_TERMS = [
    "gemstone", "ratna", "ruby", "emerald", "pearl", "blue sapphire",
    "yellow sapphire", "coral", "topaz", "diamond ring",
    "wear a", "wear the",
    "tantrik", "tantra ritual", "black magic", "vashikaran",
    "pendant", "amulet", "talisman", "kavach",
]

# Astro-jargon the user must NEVER see in the foreground prose.
# Some Sanskrit terms (Manglik, koot names) are allowed because they are
# already on the cover/snapshot pages and translated. KP-specific jargon
# (Sub-Lord, CSL, Star Lord, signifies) is ALWAYS hidden.
BANNED_JARGON_HIDDEN = [
    "sub-lord", "sub lord", "csl", "7csl", "star lord", "signifies",
    "significator", "vimshottari", "antardasha", "pratyantardasha",
]

# Phase 2.5.11.23-soul: audit-report phrases that kill the soul of the
# report. Validator (and SYSTEM_PROMPT_PREMIUM) reject any output that
# contains these. All entries lowercase — match is done against full_lower.
SOUL_BAN_PHRASES = [
    "engine driver", "engine drivers", "engine score",
    "based on engine score", "engine signals",
    "no significant friction", "natural baseline compatibility",
    "stable and well within", "drivers indicate practical compatibility",
    "detailed reading was not generated", "chapter not generated",
]

# Phase 2.5.11.23-soul-v2: therapy-app cliches that make the report feel
# like a generic relationship-coaching pamphlet. ChatGPT critique pointed
# these out as the second tone-killer after audit phrases. Validator
# allows up to ONE such phrase across the entire payload (some are nearly
# unavoidable in passing) but rejects density.
THERAPY_CLICHES = [
    "honest dialogue", "mutual respect", "consistent care",
    "open communication", "communicate openly", "communicate honestly",
    "build trust", "show appreciation", "active listening",
    "be patient with each other", "express your feelings",
    "make time for each other",
]

# Phase 2.5.11.23-soul-v2: perfect-balance language hides emotional
# asymmetry. Real relationships are uneven by nature — prompt + validator
# reject phrases that pretend both partners always feel the same thing.
PERFECT_BALANCE_PHRASES = [
    "dono naturally same", "both partners equally",
    "dono ko ek hi tarah", "perfectly aligned",
    "both feel the same", "both equally invested",
]

# Phase 2.5.11.23-soul-v4 — RHYTHM FORMULA PATTERNS
# ChatGPT critique: every chapter opens with the same "ek partner ... dusra ..."
# asymmetry pattern. Subconsciously the LLM/template signature becomes visible
# after a few pages. Validator counts how many chapters' kya_dikh OPEN (first
# ~180 chars) with this formulaic asymmetry framing — if ≥5 of 7 chapters do,
# the response is rejected as "too rhythmically uniform". Asymmetry itself is
# still encouraged everywhere — but the OPENING delivery must vary across
# chapters: sometimes a metaphor, sometimes a concrete scene, sometimes a
# direct observation, sometimes a bittersweet truth.
_RHYTHM_FORMULA_OPENER_RE = re.compile(
    r"\bek\s+partner\b.{0,160}\b(?:dusr[aeio]|doosr[aeio])\b", re.I | re.S
)

# Phase 2.5.11.23-soul-v4 — REFLECTION ENDING MARKERS
# Architect-flagged hardening: the prompt's REFLECTION-NOT-ALWAYS-ADVICE LAW
# was previously enforced ONLY by the prompt (LLM honour-system) — fallback
# was strengthened deterministically but polish path could still regress
# silently. Validator now counts how many of 7 chapters' kya_dhyan END (last
# 180 chars) with a reflection / realization / emotional truth marker. If
# fewer than 2, the response is rejected as "reflection_endings_low:N".
_REFLECTION_END_MARKERS = (
    "samajh lo", "samajh lena", "secret", "asli reward", "asli intimacy",
    "asli baat", "honour ho sakte", "realize", "realisation", "understand",
    "understanding", "truth is", "that matters", "thakaata sabse zyada",
    "is bond ka", "is rishte ka", "yahaan asli",
)


def _reflection_endings_ok(chapters: list[dict]) -> tuple[bool, int]:
    """Return (ok, count). ok=True iff ≥2 of 7 chapters' kya_dhyan ends with
    a reflection marker in the last 180 chars."""
    count = 0
    for c in chapters:
        tail = (c.get("kya_dhyan") or "")[-180:].lower()
        if any(m in tail for m in _REFLECTION_END_MARKERS):
            count += 1
    return (count >= 2), count


def _rhythm_variation_ok(chapters: list[dict]) -> tuple[bool, int]:
    """Return (ok, formula_count). ok=True iff <5 of 7 chapters open with the
    'ek partner ... dusra ...' formula in the first ~180 chars of kya_dikh."""
    formula = 0
    for c in chapters:
        head = (c.get("kya_dikh") or "")[:180]
        if _RHYTHM_FORMULA_OPENER_RE.search(head):
            formula += 1
    return (formula < 5), formula


# Phase 2.5.11.23-soul-v3 — RAW ASTROLOGY LEAKS
# ChatGPT critique: foreground prose was leaking raw chart vocab like
# "P1 Venus enemy-sign in D9", "Jupiter debilitated", "7L in 8th house" —
# the user must NEVER read backend chart language. The engine's job is to
# interpret the chart into emotional/behavioural prose, not quote it.
# Any of these substrings in user-facing prose = response rejected.
RAW_ASTRO_LEAKS = [
    # divisional chart names
    "d1 chart", "d9 chart", "d-9", "navamsa chart", "rasi chart",
    # house references in raw form
    "7th house", "8th house", "12th house", "1st house", "4th house",
    "5th house", "9th house", "10th house", "11th house",
    "in the 7th", "in the 8th", "in the 12th",
    # planet+dignity raw
    "venus enemy", "venus debilitated", "venus exalted", "venus own-sign",
    "venus own sign", "venus in own", "venus is exalted", "venus is debilitated",
    "jupiter enemy", "jupiter debilitated", "jupiter exalted", "jupiter own-sign",
    "jupiter own sign", "jupiter in own", "jupiter is exalted", "jupiter is debilitated",
    "mars enemy", "mars debilitated", "mars exalted",
    "saturn enemy", "saturn debilitated", "saturn exalted",
    "moon debilitated", "moon exalted", "mercury debilitated", "mercury exalted",
    "sun debilitated", "sun exalted",
    # lord references
    "lagna lord", "ascendant lord", "7th lord", "7l ", "7l.", "7l,",
    "lord of the 7th", "lord of the 1st", "lord of the 4th",
    # raw partner-tag prefixes leaking from engine notes
    "p1 venus", "p2 venus", "p1 jupiter", "p2 jupiter",
    "p1 lagna", "p2 lagna", "p1 7l", "p2 7l",
    # raw KP/dasha
    "vimshottari dasha", "antardasha period", "pratyantardasha",
    "rahu mahadasha", "saturn mahadasha",
]

SYSTEM_PROMPT_PREMIUM = """You are an experienced modern relationship astrologer — Vedic-rooted but contemporary in voice. You write the way a sharp, emotionally honest counsellor talks to a real couple sitting across from you. Not preachy. Not therapeutic. Not spiritual-lecture. Specific, observed, slightly disarming.

═══ VOICE (Phase soul-v2) ═══
• Sharp, warm, emotionally honest — never preachy, never motivational.
• Modern relationship language — not "wise elder", not "guru", not "spiritual teacher".
• Specific to THIS couple — each line should feel like it was written after watching them.
• Allow imperfection. Real bonds are uneven, contradictory, asymmetric. Honour that.
• Hindi / Hinglish / native-language speaking style depending on `language`.

═══ EMOTIONAL REALISM RULES (the most important section) ═══
Real relationships are emotionally uneven by nature.
• Do NOT write as if both partners always feel the same thing equally.
• AVOID perfect-balance language: "dono naturally same boat me", "both equally invested", "dono ko ek hi tarah feel hota hai", "perfectly aligned".
• ALLOW emotional asymmetry: ek partner zyada invest karta hai, dusre ka attachment slow hai. Ek share karta hai openly, dusra silently sambhalta hai.
• ALLOW contradiction: "Love is present here, but reassurance arrives in different emotional languages."
• ALLOW timing mismatch: ek ko abhi baat karni hai, dusre ko 30 minute chahiye. Honour this rather than pretending it doesn't exist.
• ALLOW silent expectations and unspoken resentments to be named.
• The report should feel emotionally honest, not motivational. Bittersweet truths welcome.

═══ SIGNATURE INSIGHT RULE (every chapter must obey) ═══
Each chapter MUST contain at least ONE high-specificity emotional observation that feels impossible to say generically. This is the magic that creates "holy shit, this is accurate" moments. The reader should occasionally feel slightly emotionally exposed — as if the report noticed a pattern they never fully admitted aloud.

EXAMPLES of signature insights (write your own — do not copy these):
  • "One person waits quietly instead of asking directly."
  • "Distance here grows more through silence than anger."
  • "Affection exists, but reassurance arrives in different emotional languages."
  • "The one who looks calmer in arguments is actually the one rehearsing the conversation hours later in their head."
  • "Both want closeness — but one wants it through words, the other through being left alone in the same room."

If a chapter could be the same chapter for any other couple, you have failed.

═══ RHYTHM VARIATION LAW (Phase soul-v4 — ChatGPT critique fix) ═══
Across the 7 chapters, the OPENING delivery of `kya_dikh` must vary. Do NOT begin every chapter with the same "ek partner ... dusra partner ..." asymmetry frame. After 2 or 3 chapters that pattern becomes a visible signature and the report stops feeling like observation, starts feeling like a template.

Rotate among at least 4 of these opening shapes across the 7 chapters:
  1. METAPHOR opening   — "Pyaar yahaan loud nahi hai — yahaan emotional language ek background hum ki tarah baji rehti hai..."
  2. CONCRETE SCENE     — "9 baje ki chai, dono sofa pe, ek bole 'main theek hoon' aur baat khatm. {p1} ke liye yeh line literal hoti hai..."
  3. DIRECT OBSERVATION — "This relationship becomes strongest during ordinary days, not dramatic moments..."
  4. BITTERSWEET TRUTH  — "Sabse purane silent friction-points emotional speed se start hote hain, topic se nahi..."
  5. CHART-AWARE BRIDGE — "One chart adapts quickly during life transitions, while the other seeks emotional continuity before change feels safe..." (see CHART-AWARE LANGUAGE LAW below).

Asymmetry inside the prose is still mandatory — but it must EMERGE, not OPEN. If 5 or more chapters open with "ek partner ... dusra ...", response is rejected.

═══ REFLECTION-NOT-ALWAYS-ADVICE LAW (Phase soul-v4) ═══
Every chapter does NOT need to end with a ritual / check-in / scheduled practice. After a while the report starts feeling like therapy homework. AT LEAST TWO chapters' `kya_dhyan` should END (last sentence) with a reflection / realization / emotional truth — NOT an action item.

Examples of reflection endings (write your own):
  • "Understanding this difference early can save years of silent misunderstanding."
  • "Calmness yahaan unaffected hone ka naam nahi — sirf processing alag jagah ho rahi hai."
  • "Ye samajh lo — emotional rhythms match nahi karte, sirf honour ho sakte hain. Yahi is bond ka secret hai."

Suggested mapping (NOT mandatory): ch1 + ch6 lend themselves to reflection endings; ch3 + ch5 to action; ch4 + ch7 ALWAYS end with one verbatim ALLOWED_REMEDIES phrase. Any 2 of 7 minimum must end in reflection.

═══ CHART-AWARE LANGUAGE LAW (Phase soul-v4) ═══
The astrology backbone must be FELT in the language without quoting raw chart vocab. Use subtle "one chart..." or "this chart..." phrasing as a permitted bridge — it carries astrological weight without being raw vocab.

  ❌ "P1 Venus enemy-sign in D9" (raw vocab — banned by RAW_ASTRO_LEAKS)
  ❌ "One partner naturally adjusts..." (psychology only — astrology hidden)
  ✅ "One chart adapts quickly during life transitions, while the other seeks emotional continuity before change feels safe."
  ✅ "This chart carries a long emotional memory — old gestures still echo years later."
  ✅ "{p1}'s chart leans toward steady continuity; {p2}'s leans toward catalytic change."

Use this bridge sparingly — at least 2-3 times across the full report — so the reader subconsciously feels "yeh kundli ki baat hai", not "yeh ek psychology blog hai". The word "chart" used this way is NOT a raw leak.

═══ STRUCTURAL ARC (kept internally — do NOT label or segment) ═══
For each chapter you write 3 prose fields. Treat them as a natural narrative arc, NOT as labeled bullet sections. The reader must NOT feel "Layer 1, Layer 2, Layer 3" — they must read it as flowing observation.
  • kya_dikh    — What the chart actually shows, in plain emotional language. NO raw engine vocab (no "Venus enemy-sign", no "D9", no "7L", no "CSL", no Sub-Lord). Translate into how it FEELS.
  • kya_matlab  — The real-life behavioural pattern this creates between them — a concrete moment, a recognisable shape of how something unfolds.
  • kya_dhyan   — ONE specific behavioural anchor + ONE grounding practice. Not vague advice — a real, nameable thing they can do.

═══ INTERPRET-NEVER-QUOTE LAW (Phase soul-v3 — most important after Emotional Realism) ═══
The chart is the SOURCE — never the SUBJECT. Never write raw chart vocabulary in the prose. The user must read about THEMSELVES, not about their chart parts.

NEVER write any of these in the foreground prose (response rejected):
  • "P1 Venus enemy-sign in D9", "Jupiter debilitated", "7L in 8th house", "Venus own-sign", "Venus exalted"
  • "Navamsa chart shows...", "D9 chart indicates...", "lagna lord", "7th lord", "ascendant lord"
  • "Rahu mahadasha", "Vimshottari dasha", "Antardasha period"
  • Any "P1/P2 + planet name" raw tag (e.g. "P1 Venus", "P2 Jupiter")
  • Any "Nth house" reference (1st/4th/5th/7th/8th/9th/10th/11th/12th house) — translate into life domains

ALWAYS interpret into emotional/behavioural meaning the user can recognise:
  ❌ "P1 Venus enemy-sign in D9 → low marital harmony"
  ✅ "Affection here doesn't arrive as a confident, easy stream — it arrives in careful gestures that need acknowledgment"

  ❌ "Jupiter debilitated in 7th house → values misalignment"
  ✅ "The deeper sense of 'what marriage is for' lands slightly differently for each of you"

  ❌ "7L of P2 in 8th house → patience layer needed"
  ✅ "There is a karmic patience layer here — change in this bond comes through quiet, slow transformation, not sudden shifts"

═══ UNIQUE BEHAVIOURAL ANCHOR LAW (Phase soul-v3) ═══
Each chapter's `kya_dhyan` MUST contain a behavioural anchor that does NOT appear in any other chapter. If ch1 already says "10-minute walk together", ch3 cannot also say "walk together". Vary the practice — the dialogue, the ritual, the timing window, the location. Repeating the same anchor across chapters destroys the report's intelligence.

Use this rough mapping as inspiration (do NOT copy verbatim):
  • ch1 (Emotional)    — daily/weekly DIALOGUE-style ritual (signal phrase, processing window)
  • ch2 (Trust)        — predictability/transparency MICRO-habit (state-of-us check-in, weekly note)
  • ch3 (Conflict)     — pacing/cool-down RULE (24-hour rule, deadline-honoured pause)
  • ch4 (Stability)    — long-horizon ANCHOR (yearly anniversary ritual, 6-month review) + remedy
  • ch5 (Chemistry)    — pressure-relief/INTIMACY rhythm (low-pressure date, novelty practice)
  • ch6 (Family)       — boundary/role REVIEW (quarterly division-of-labour reset, family-event triage)
  • ch7 (Future)       — direction-recalibration PRACTICE (5-year map session, goal-share day) + remedy

═══ HARD-BAN PHRASES (audit-report tone — response rejected) ═══
Never write any of: "engine drivers", "engine driver", "engine score", "Based on engine score", "engine signals", "no significant friction detected", "natural baseline compatibility", "stable and well within healthy range", "drivers indicate practical compatibility".

═══ THERAPY-CLICHE BAN (generic counselling tone — response rejected if dense) ═══
Avoid generic therapy-style advice unless tied to a specific chart-anchored relationship pattern. Do NOT write any of these as standalone advice: "honest dialogue", "mutual respect", "consistent care", "open communication", "communicate openly", "build trust", "show appreciation", "active listening", "be patient with each other", "express your feelings", "make time for each other". These are pamphlet phrases — they make the report feel like a relationship-coaching app.

═══ SPECIFICITY LAW (lightweight) ═══
• Both partner names must appear ≥3 times across the FULL prose combined (no per-chapter quota — let names land naturally).
• Each chapter must reference at least one CONCRETE moment, fight pattern, or daily ritual — never pure abstraction.

═══ ABSOLUTE RULES (violation = response rejected) ═══
1. Use ONLY the facts inside <ENGINE_FACTS> + <CHAPTER_DRIVERS>. Never invent koot scores, nakshatras, planets, dates, or houses.
2. The exact total score (e.g. "33 out of 36") MUST appear once in `verdict` OR `hidden_truth`.
3. Both partner names MUST appear at least once across the prose combined.
4. NEVER predict: lifespan, death, gender of children, divorce, specific dates, guaranteed outcomes.
5. NEVER use BACKEND jargon in the foreground prose: do not write "Sub-Lord", "CSL", "Star Lord", "signifies house X", "Vimshottari", "Antardasha". Translate the underlying truth into plain language ("the deeper karmic commitment-layer is strong").
6. Recommend ONLY remedies from <ALLOWED_REMEDIES>. No gemstones, no tantrik kriyas, no expensive yagnas outside the list. At least one verbatim remedy MUST appear across ch4.kya_dhyan + ch7.kya_dhyan combined.
7. LANGUAGE CONTRACT: write the entire prose in the user's language as specified by `language`:
   • "en" = pure English. "hn" = Hinglish (Hindi in Roman/Latin script). "hi" = Devanagari (देवनागरी). "mr" = Marathi (मराठी). "bn" = Bengali. etc.
   • EVEN in non-English: keep partner names + nakshatra/rashi names + koot labels + remedy names + the numeric total VERBATIM in their original Latin/English form.

═══ STRUCTURE — 7 CHAPTERS ═══
Each chapter is keyed by ch1..ch7 in `chapters` array. The score is FIXED by the engine — DO NOT include score in your output. You only write the 3 prose blocks + grounding.

Chapter titles + psychological question each chapter answers:
  ch1 Emotional Compatibility           → "Do we actually feel the same things?"
  ch2 Trust & Loyalty                    → "Can we count on each other when it matters?"
  ch3 Communication & Conflict           → "When we fight, what really happens underneath?"
  ch4 Marriage Stability                 → "Will this marriage last? What is the ONE thing both must accept?"
  ch5 Physical + Emotional Chemistry     → "Is there real attraction + emotional pull, or only one?"
  ch6 Family + Practical Life            → "How will daily life + extended family actually work?"
  ch7 Long-Term Future Direction         → "Where is this heading in the next few years?"

For EACH chapter, write 3 blocks + 1 grounding line (4 fields total):
  • kya_dikh    — "Aapke chart me kya dikh raha hai" — 3-4 sentences (~70-180 chars), ANCHORED in <CHAPTER_DRIVERS> facts for that chapter. Must reference at least one specific engine fact (a koot label, a number, a partner-specific behavior pattern).
  • kya_matlab  — "Iska matlab kya hai aapke rishte ke liye" — 3-4 sentences (~70-180 chars), translates the chart fact into REAL-LIFE behavior the couple will recognize.
  • kya_dhyan   — "Kya dhyan rakhna hai" — 3-5 short actionable points joined by sentence/bullet flow (~80-220 chars), mature + practical + non-superstitious. ch4 + ch7 MUST end with one verbatim remedy from <ALLOWED_REMEDIES>.
  • grounding   — 1 short line (8-22 words), starts with "Based on" — references the underlying engine layer subtly (e.g. "Based on Maitri 4/5, Bhakut 7/7, and D9 marriage-maturity layer.").

═══ HIDDEN TRUTH (top of report) ═══
`hidden_truth` — 2-3 sentences (~80-280 chars). What the deeper karmic + soul-level layer reveals about THIS bond that surface koots alone don't show. Translate the KP promise verdict + D9 sync into plain feeling-language. NEVER use the words "KP", "Sub-Lord", or "promise verdict" itself.

═══ SPECIAL / DAMAGE / PRACTICAL / VERDICT ═══
`special`   : array of EXACTLY 3 short strings (~30-100 chars each). The top 3 strengths of this bond, plain language, each anchored in a real chapter driver.
`damage`    : array of 1-3 short strings (~30-120 chars each). Low-score frictions framed gently. Empty array allowed if no significant friction.
`practical` : array of EXACTLY 3 strings (~120-300 chars each). Three paragraphs about practical married life — daily rhythm, shared finances, family dynamics — anchored in the engine facts.
`verdict`   : 1 mature paragraph (~150-380 chars). Final synthesis. Honest, warm, not promotional. Must contain the verbatim total score.

═══ MARRIAGE BLUEPRINT (Phase soul-v3 — NEW SECTION) ═══
`marriage_blueprint` — 6 prose fields describing each partner's INNATE marriage nature (NOT chart vocab; INTERPRETED into character) + how those two natures interact + what each needs from the other to feel safe.

Read the deeper marriage layer (D9 lagna lord, Venus-Jupiter dignity, marriage_maturity score) ONCE in the backend, then translate into pure relational character language. NEVER name "D9", "lagna lord", "Venus", "Jupiter", "navamsa".

Fields (all strings):
  • p1_marriage_nature        — 2-3 sentences. {p1_name}'s INNATE way of being inside marriage — does s/he lead with steadiness, with playfulness, with intensity, with care? Anchored in the deeper character signal. Use {p1_name}.
  • p2_marriage_nature        — 2-3 sentences. {p2_name}'s INNATE way of being inside marriage. Anchored. Use {p2_name}.
  • interaction_dynamic       — 3-4 sentences. What happens WHEN these two natures meet daily. The shape of their married rhythm. Allow asymmetry; honour contradiction. Both names appear.
  • what_p1_needs_from_p2     — 2-3 sentences. The SPECIFIC kind of presence/reassurance {p1_name} needs from {p2_name} to feel safe in the marriage. Concrete, not generic.
  • what_p2_needs_from_p1     — 2-3 sentences. Same for {p2_name} from {p1_name}. Concrete and DIFFERENT from p1's need (asymmetry honoured).
  • blueprint_takeaway        — 1-2 sentences. The ONE thing both should remember about how this marriage actually operates. Both names appear.

Length per field: 80–600 chars. Both partner names must appear ≥1× across the blueprint as a whole. NO chart vocab. NO therapy cliches. Asymmetry mandatory.

═══ OUTPUT (JSON only, no markdown, no preamble) ═══
{
  "hidden_truth": "string",
  "chapters": [
    {"key":"ch1","kya_dikh":"...","kya_matlab":"...","kya_dhyan":"...","grounding":"..."},
    {"key":"ch2","kya_dikh":"...","kya_matlab":"...","kya_dhyan":"...","grounding":"..."},
    {"key":"ch3", ...},
    {"key":"ch4", ...},
    {"key":"ch5", ...},
    {"key":"ch6", ...},
    {"key":"ch7", ...}
  ],
  "special":   ["...", "...", "..."],
  "damage":    ["...", "..."],
  "practical": ["...", "...", "..."],
  "verdict":   "string",
  "marriage_blueprint": {
    "p1_marriage_nature": "string",
    "p2_marriage_nature": "string",
    "interaction_dynamic": "string",
    "what_p1_needs_from_p2": "string",
    "what_p2_needs_from_p1": "string",
    "blueprint_takeaway": "string"
  }
}
"""


def _build_user_prompt(milan_facts: dict, chapter_scores: dict,
                        d9: dict, syn: dict, kp: dict, lang: str) -> str:
    p1 = milan_facts.get("p1", {}) or {}
    p2 = milan_facts.get("p2", {}) or {}
    koots = milan_facts.get("koots", []) or []

    koot_lines = []
    for k in koots:
        s, mx = k.get("score", 0), k.get("max", 0)
        flag = ""
        if s == 0 and mx > 0:
            flag = "  ← DOSHA"
        elif s == mx and mx >= 4:
            flag = "  ← STRENGTH"
        koot_lines.append(f"  {k.get('label','?'):<8} {s} / {mx}   ({k.get('detail','')}){flag}")

    chap_blocks = []
    chs = (chapter_scores or {}).get("chapters", {}) or {}
    for key in CHAPTER_KEYS:
        c = chs.get(key, {}) or {}
        drv = c.get("drivers", []) or []
        cau = c.get("cautions", []) or []
        kf = c.get("key_facts", {}) or {}
        chap_blocks.append(
            f"  {key} ({c.get('title','?')}) — engine_score={c.get('score_0_10','?')}/10\n"
            f"     drivers : {drv if drv else '—'}\n"
            f"     cautions: {cau if cau else '—'}\n"
            f"     key_facts: {kf}"
        )

    # Hidden-truth source: KP promise + D9 sync — engine facts only
    kp_couple = (kp or {}).get("couple_verdict", "UNAVAILABLE")
    p1_kp = ((kp or {}).get("p1") or {}).get("verdict", "UNAVAILABLE")
    p2_kp = ((kp or {}).get("p2") or {}).get("verdict", "UNAVAILABLE")
    d9_sync = ((d9 or {}).get("sync") or {}).get("score_0_10", "?")
    syn_score = (syn or {}).get("score_0_10", "?")
    nak_resonance = ((syn or {}).get("nakshatra_resonance") or {}).get("count", 0)

    hidden_block = (
        f"  kp_couple_promise: {kp_couple}  (p1={p1_kp}, p2={p2_kp})\n"
        f"  d9_marriage_lagna_sync: {d9_sync}/10\n"
        f"  cross_chart_synastry: {syn_score}/10\n"
        f"  nakshatra_lord_resonance_count: {nak_resonance}"
    )

    # ── Blueprint backend facts (Phase soul-v3) ──
    # The LLM uses these ONLY to derive the marriage_blueprint section.
    # They MUST NOT appear verbatim in the user-facing prose — the prompt's
    # INTERPRET-NEVER-QUOTE law and validator's RAW_ASTRO_LEAKS list both
    # enforce that. These are character signals only.
    d9p1 = (d9 or {}).get("p1") or {}
    d9p2 = (d9 or {}).get("p2") or {}
    d9_sync_block = (d9 or {}).get("sync") or {}
    blueprint_block = (
        f"  p1_marriage_maturity: {d9p1.get('marriage_maturity_0_10', '?')}/10\n"
        f"  p1_inner_temperament_signal: lagna_lord={d9p1.get('d9_lagna_lord','?')}, "
        f"venus={d9p1.get('d9_venus_dignity','?')}, jupiter={d9p1.get('d9_jupiter_dignity','?')}\n"
        f"  p2_marriage_maturity: {d9p2.get('marriage_maturity_0_10', '?')}/10\n"
        f"  p2_inner_temperament_signal: lagna_lord={d9p2.get('d9_lagna_lord','?')}, "
        f"venus={d9p2.get('d9_venus_dignity','?')}, jupiter={d9p2.get('d9_jupiter_dignity','?')}\n"
        f"  couple_lagna_relation: {d9_sync_block.get('lagna_lord_relation','?')}\n"
        f"  couple_seven_relation: {d9_sync_block.get('seven_lord_relation','?')}\n"
        f"  couple_sync_score: {d9_sync_block.get('score_0_10','?')}/10"
    )

    p1_mang = p1.get("manglik", False)
    p2_mang = p2.get("manglik", False)
    if p1_mang and p2_mang:
        mang = "manglik_status: both_manglik (mutual cancellation)"
    elif p1_mang or p2_mang:
        mang = f"manglik_status: only_{'p1' if p1_mang else 'p2'}_manglik (imbalance — needs ritual remedy)"
    else:
        mang = "manglik_status: neither (no Mangal dosha)"

    overall = (chapter_scores or {}).get("overall_avg_0_10", "?")

    return f"""<ENGINE_FACTS>
p1_name: {p1.get('name','Partner 1')}
p1_nakshatra: {p1.get('nakshatra','?')} (Pada {p1.get('pada','?')}, {p1.get('rashi','?')})
p1_manglik: {p1_mang}

p2_name: {p2.get('name','Partner 2')}
p2_nakshatra: {p2.get('nakshatra','?')} (Pada {p2.get('pada','?')}, {p2.get('rashi','?')})
p2_manglik: {p2_mang}

total_guna: {milan_facts.get('total','?')} / {milan_facts.get('max',36)}
overall_chapter_avg: {overall}/10
{mang}

koot_scores:
{chr(10).join(koot_lines)}
</ENGINE_FACTS>

<CHAPTER_DRIVERS>
{chr(10).join(chap_blocks)}
</CHAPTER_DRIVERS>

<HIDDEN_LAYER>
{hidden_block}
</HIDDEN_LAYER>

<BLUEPRINT_BACKEND_SIGNAL — INTERPRET, NEVER QUOTE>
{blueprint_block}
</BLUEPRINT_BACKEND_SIGNAL>

<ALLOWED_REMEDIES>
{', '.join(ALLOWED_REMEDIES)}
</ALLOWED_REMEDIES>

<USER_CONTEXT>
language: {lang}
</USER_CONTEXT>

CRITICAL — verbatim "{milan_facts.get('total','?')} out of 36" MUST appear in `verdict` or `hidden_truth`.
CRITICAL — both names "{p1.get('name','Partner 1')}" and "{p2.get('name','Partner 2')}" MUST appear at least once each.
CRITICAL — ch4.kya_dhyan + ch7.kya_dhyan combined MUST contain at least ONE verbatim remedy from <ALLOWED_REMEDIES>.

Generate the JSON now."""


def _fingerprint(milan_facts: dict, chapter_scores: dict,
                 kp: dict, lang: str, model: str) -> str:
    p1 = milan_facts.get("p1", {}) or {}
    p2 = milan_facts.get("p2", {}) or {}
    parts = [
        f"prem={_PREMIUM_VERSION}",
        f"model={model}",
        f"lang={lang}",
        p1.get("nakshatra", ""), str(p1.get("pada", "")), p1.get("rashi", ""),
        p2.get("nakshatra", ""), str(p2.get("pada", "")), p2.get("rashi", ""),
        f"total={milan_facts.get('total','')}",
        f"mdosh={milan_facts.get('manglik_dosh','')}",
    ]
    for k in milan_facts.get("koots", []) or []:
        parts.append(f"{k.get('key','')}={k.get('score','')}")
    chs = (chapter_scores or {}).get("chapters", {}) or {}
    for key in CHAPTER_KEYS:
        parts.append(f"{key}={chs.get(key, {}).get('score_0_10', '')}")
    parts.append(f"kp={(kp or {}).get('couple_verdict','')}")
    raw = "|".join(parts).encode("utf-8")
    return "prem_" + hashlib.sha1(raw).hexdigest()


# Small connective tokens excluded from advice-uniqueness 4-gram comparison
# so common scaffolding ("aur dono ko ye karna hai") doesn't flag false
# positives. Only substantive content words count.
_STOPWORDS = {
    "aur", "ke", "ki", "ka", "ko", "se", "me", "mein", "hai", "hain",
    "ho", "hota", "hoti", "the", "and", "or", "of", "in", "to", "a",
    "an", "is", "are", "for", "on", "with", "that", "this", "ek",
    "dono", "iska", "uska", "yeh", "ye", "vo", "woh", "kya", "kar",
    "karo", "kare", "karein", "raho", "rakho", "ki ek", "tum", "main",
    "ya", "bhi", "bhi.", "phir", "to", "par", "lekin", "agar", "jab",
}


def _advice_uniqueness_ok(chapters: list[dict]) -> bool:
    """Reject formulaic advice. Extracts substantive 4-grams from each
    chapter's kya_dhyan and counts pairwise overlaps. If ≥2 distinct
    chapter-pairs share ≥2 substantive 4-grams, the advice is too
    repetitive → reject. Tolerant by design — only flags clear formulas."""
    grams_per_ch: list[set[tuple[str, ...]]] = []
    for c in chapters:
        text = (c.get("kya_dhyan") or "").lower()
        # Tokenise on word characters; preserve order for n-grams.
        tokens = re.findall(r"[a-z\u0900-\u097F]+", text)
        # Drop stopwords for substantive comparison.
        sub = [t for t in tokens if t not in _STOPWORDS and len(t) >= 3]
        grams = set()
        for i in range(len(sub) - 3):
            grams.add(tuple(sub[i:i + 4]))
        grams_per_ch.append(grams)
    overlap_pairs = 0
    n = len(grams_per_ch)
    for i in range(n):
        for j in range(i + 1, n):
            shared = grams_per_ch[i] & grams_per_ch[j]
            if len(shared) >= 2:
                overlap_pairs += 1
    return overlap_pairs <= 1


def _validate_premium(out: Any, milan_facts: dict, chapter_scores: dict) -> tuple[bool, str]:
    if not isinstance(out, dict):
        return False, "not_dict"

    # hidden_truth
    ht = out.get("hidden_truth")
    if not isinstance(ht, str) or not (40 <= len(ht) <= 600):
        return False, "hidden_truth_bad"

    # chapters
    chs = out.get("chapters")
    if not isinstance(chs, list) or len(chs) != 7:
        return False, "chapters_count"
    seen_keys: set[str] = set()
    chapter_dyn_combined = ""
    chapter_full_text = ""
    for c in chs:
        if not isinstance(c, dict):
            return False, "chapter_not_dict"
        key = c.get("key")
        if key not in CHAPTER_KEYS or key in seen_keys:
            return False, f"chapter_key_bad:{key}"
        seen_keys.add(key)
        for fld, lo, hi in (("kya_dikh", 50, 700), ("kya_matlab", 50, 700),
                             ("kya_dhyan", 50, 700)):
            v = c.get(fld)
            if not isinstance(v, str) or not (lo <= len(v) <= hi):
                return False, f"{key}_{fld}_length"
        g = c.get("grounding")
        if not isinstance(g, str) or not (10 <= len(g) <= 240):
            return False, f"{key}_grounding_length"
        if key in _REMEDY_BEARING:
            chapter_dyn_combined += " " + c.get("kya_dhyan", "")
        chapter_full_text += " " + (c.get("kya_dikh", "") + " " + c.get("kya_matlab", "")
                                     + " " + c.get("kya_dhyan", "") + " " + c.get("grounding", ""))
    if seen_keys != set(CHAPTER_KEYS):
        return False, "chapter_keys_missing"

    # special / damage / practical
    sp = out.get("special")
    if not isinstance(sp, list) or len(sp) != 3 or not all(isinstance(x, str) and 15 <= len(x) <= 220 for x in sp):
        return False, "special_bad"
    dm = out.get("damage")
    if not isinstance(dm, list) or len(dm) > 5 or not all(isinstance(x, str) and 15 <= len(x) <= 320 for x in dm):
        return False, "damage_bad"
    pr = out.get("practical")
    if not isinstance(pr, list) or len(pr) != 3 or not all(isinstance(x, str) and 80 <= len(x) <= 600 for x in pr):
        return False, "practical_bad"

    # verdict
    vd = out.get("verdict")
    if not isinstance(vd, str) or not (80 <= len(vd) <= 800):
        return False, "verdict_bad"

    full_text = " ".join([ht, vd, chapter_full_text] + sp + dm + pr)
    full_lower = full_text.lower()
    full_norm = _normalize_digits(full_text)

    # Total citation
    total = milan_facts.get("total")
    if total is not None and str(total) not in _normalize_digits(ht + " " + vd):
        return False, "total_not_cited_in_hidden_or_verdict"

    # Both partner names appear
    p1n = (milan_facts.get("p1", {}) or {}).get("name", "")
    p2n = (milan_facts.get("p2", {}) or {}).get("name", "")
    for nm, lbl in ((p1n, "p1"), (p2n, "p2")):
        if nm and len(nm) >= 3 and not re.search(r"\b" + re.escape(nm.lower()) + r"\b", full_lower):
            return False, f"{lbl}_name_missing"

    # Banned existential terms
    for b in BANNED_TERMS:
        if b in full_lower:
            return False, f"banned_term:{b}"

    # Banned KP/backend jargon
    for j in BANNED_JARGON_HIDDEN:
        if j in full_lower:
            return False, f"banned_jargon:{j}"

    # ── Phase 2.5.11.23-soul: audit-report phrase denylist ──
    # Mirror of SYSTEM_PROMPT_PREMIUM hard-ban list. Deterministically
    # rejects gpt-4o output that regresses to the old "audit report" tone.
    for sb in SOUL_BAN_PHRASES:
        if sb in full_lower:
            return False, f"soul_banned:{sb}"

    # ── Phase 2.5.11.23-soul-v2: therapy-cliche density check ──
    # Up to 1 cliche allowed (some are nearly unavoidable in passing).
    # ≥2 distinct cliches = response feels like a generic relationship-app
    # → rejected so polish path retries or fallback fires.
    cliche_hits = sum(1 for tc in THERAPY_CLICHES if tc in full_lower)
    if cliche_hits >= 2:
        return False, f"therapy_cliche_density:{cliche_hits}"

    # ── Phase 2.5.11.23-soul-v2: perfect-balance denial check ──
    # Real relationships are emotionally uneven. Reject any output that
    # pretends both partners always feel the same thing equally.
    for pb in PERFECT_BALANCE_PHRASES:
        if pb in full_lower:
            return False, f"perfect_balance_phrase:{pb}"

    # ── Phase 2.5.11.23-soul-v3: RAW_ASTRO_LEAKS check ──
    # The user must NEVER read raw chart vocabulary. The engine interprets
    # the chart into emotional/behavioural prose; it never quotes it.
    for leak in RAW_ASTRO_LEAKS:
        if leak in full_lower:
            return False, f"raw_astro_leak:{leak}"

    # ── Phase 2.5.11.23-soul-v3: ADVICE UNIQUENESS check ──
    # Each chapter's kya_dhyan must contain a behavioural anchor that
    # doesn't repeat across chapters. Detect 4-gram overlap on substantive
    # content words. ≥2 distinct chapter-pairs sharing ≥2 substantive
    # 4-grams = response feels formulaic → rejected.
    if not _advice_uniqueness_ok(chs):
        return False, "advice_uniqueness_low"

    # ── Phase 2.5.11.23-soul-v4: RHYTHM VARIATION check ──
    # If ≥5 of 7 chapters open kya_dikh with the "ek partner ... dusra ..."
    # asymmetry formula, the report's signature becomes visible. Reject so
    # polish path retries with rotated openers (metaphor / scene / direct
    # observation / bittersweet / chart-aware bridge).
    rhythm_ok, formula_count = _rhythm_variation_ok(chs)
    if not rhythm_ok:
        return False, f"rhythm_formula_uniform:{formula_count}"

    # ── Phase 2.5.11.23-soul-v4: REFLECTION-NOT-ALWAYS-ADVICE check ──
    # ≥2 of 7 chapters' kya_dhyan must end with a reflection marker — not
    # an action item. Architect-flagged hardening so polish path cannot
    # regress silently (prompt-only enforcement was insufficient).
    refl_ok, refl_count = _reflection_endings_ok(chs)
    if not refl_ok:
        return False, f"reflection_endings_low:{refl_count}"

    # ── Phase 2.5.11.23-soul-v3: MARRIAGE BLUEPRINT validation ──
    mb = out.get("marriage_blueprint")
    if not isinstance(mb, dict):
        return False, "marriage_blueprint_missing"
    mb_fields = ("p1_marriage_nature", "p2_marriage_nature",
                 "interaction_dynamic", "what_p1_needs_from_p2",
                 "what_p2_needs_from_p1", "blueprint_takeaway")
    for fld in mb_fields:
        v = mb.get(fld)
        if not isinstance(v, str) or not (60 <= len(v) <= 700):
            return False, f"marriage_blueprint_field:{fld}"
    mb_text = " ".join(mb.get(f, "") for f in mb_fields)
    mb_lower = mb_text.lower()
    # Both names must appear at least once across the whole blueprint.
    for nm, lbl in ((p1n, "p1"), (p2n, "p2")):
        if nm and len(nm) >= 3 and not re.search(
                r"\b" + re.escape(nm.lower()) + r"\b", mb_lower):
            return False, f"marriage_blueprint_name_missing:{lbl}"
    # No raw astrology leaks inside blueprint either.
    for leak in RAW_ASTRO_LEAKS:
        if leak in mb_lower:
            return False, f"marriage_blueprint_raw_leak:{leak}"

    # ── Phase 2.5.11.23-soul: specificity law (global, lightweight) ──
    # Each partner name must appear ≥3 times across the FULL prose so
    # the report feels personal (not a templated couples report). Per-chapter
    # quota dropped in v2 — names land naturally instead of being forced.
    for nm, lbl in ((p1n, "p1"), (p2n, "p2")):
        if nm and len(nm) >= 3:
            occurrences = len(re.findall(
                r"\b" + re.escape(nm.lower()) + r"\b", full_lower))
            if occurrences < 3:
                return False, f"{lbl}_name_density_low:{occurrences}"

    # Remedy whitelist (positive contract, bearing chapters only)
    if not any(r.lower() in chapter_dyn_combined.lower() for r in ALLOWED_REMEDIES):
        return False, "remedy_missing_in_ch4_ch7"

    # Remedy denylist (everywhere)
    for banned in BANNED_REMEDY_TERMS:
        if banned in full_lower:
            return False, f"banned_remedy:{banned}"

    # Hallucinated koot scores: any "X out of Y" or "X / Y" must match a real
    # koot pair, total/max, OR an engine-derived chapter score ("X/10").
    # Koot pairs + total/max stay STRICT (catches genuine hallucination like "7/7" when
    # engine emitted "0/7"). Chapter scores allow ±0.5 tolerance because LLMs
    # naturally cite "7.8/10" when engine emits 7.5 — minor decimal drift is not
    # hallucination, fabricated koot scores are.
    real_pairs = {(str(milan_facts.get("total", "")), str(milan_facts.get("max", 36)))}
    for k in milan_facts.get("koots", []) or []:
        real_pairs.add((str(k.get("score", "")), str(k.get("max", ""))))
    chapter_scores_10: list[float] = []
    for c in (chapter_scores or {}).get("chapters", {}).values():
        sc = c.get("score_0_10")
        if sc is not None:
            real_pairs.add((str(sc), "10"))
            try:
                fsc = float(sc)
                chapter_scores_10.append(fsc)
                real_pairs.add((str(int(round(fsc))), "10"))
            except Exception:
                pass
    pair_re = re.compile(r"(\d+(?:\.\d+)?)\s*(?:/|out of)\s*(\d+)", re.I)
    for m in pair_re.finditer(full_norm):
        num_s, den_s = m.group(1), m.group(2)
        if (num_s, den_s) in real_pairs:
            continue
        # Tolerance only for chapter-style "X/10" pairs.
        if den_s == "10" and chapter_scores_10:
            try:
                num_f = float(num_s)
                if any(abs(num_f - sc) <= 0.5 for sc in chapter_scores_10):
                    continue
            except Exception:
                pass
        return False, f"hallucinated_pair:{m.group(0)}"

    return True, "ok"


def polish_premium_chapters(
    milan_facts: dict,
    chapter_scores: dict,
    d9_marriage: dict,
    synastry: dict,
    kp_promise: dict,
    lang: str = "en",
    fallback: dict | None = None,
) -> dict[str, Any]:
    """Premium gpt-4o polish for 24-page Pro PDF.

    Returns a dict with:
      hidden_truth (str), chapters (list[7]), special, damage, practical, verdict
    On any failure (toggle off, no client, LLM error, validator fail) returns
    `fallback` (or a deterministic safe fallback if None passed).
    Never raises.
    """
    fb = fallback if fallback is not None else _safe_fallback(
        milan_facts, chapter_scores, kp_promise, d9_marriage)
    if os.environ.get("COMPAT_PREMIUM_POLISH", "0") not in ("1", "true", "True"):
        return fb

    model = os.environ.get("COMPAT_PREMIUM_MODEL", _DEFAULT_MODEL)
    try:
        key = _fingerprint(milan_facts, chapter_scores, kp_promise, lang, model)

        hit = _l1_get(key)
        if hit is not None:
            return hit
        db_hit = _l2_get(key)
        if db_hit is not None:
            _l1_put(key, db_hit)
            return db_hit

        try:
            from openai_helper import _get_client  # type: ignore
        except Exception as exc:
            log.warning("[premium_chapters] openai import failed: %s", exc)
            return fb
        client = _get_client()
        if client is None:
            return fb

        user_prompt = _build_user_prompt(milan_facts, chapter_scores,
                                          d9_marriage, synastry, kp_promise, lang)

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT_PREMIUM},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            # Premium output is ~3-4× the polished_compat schema. Empirical sizing:
            # • en  full output ~2400-3200 tokens → cap 3500.
            # • non-Latin scripts cost 2-3× more tokens per char → cap 5000.
            # gpt-5 family (gpt-5, gpt-5-mini) consumes a chunk of completion
            # tokens for hidden reasoning before emitting visible content.
            # With 3500, reasoning eats the budget and the visible body is
            # empty → JSON parse fail → silent fallback. Bump to 8000 for
            # gpt-5* so visible JSON has room. (Phase soul-v4 fix.)
            "max_tokens": (
                8000 if model.lower().startswith("gpt-5")
                else (3500 if (lang or "en").lower() == "en" else 5000)
            ),
        }
        if not model.lower().startswith("gpt-5"):
            kwargs["temperature"] = 0.55

        resp = client.chat.completions.create(**kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        try:
            usage = getattr(resp, "usage", None)
            if usage is not None:
                log.info(
                    "[premium_chapters] tokens model=%s prompt=%s completion=%s total=%s",
                    model,
                    getattr(usage, "prompt_tokens", "?"),
                    getattr(usage, "completion_tokens", "?"),
                    getattr(usage, "total_tokens", "?"),
                )
        except Exception:
            pass

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            log.warning("[premium_chapters] JSON parse fail: %s | raw=%.200s", exc, raw)
            return fb

        ok, reason = _validate_premium(parsed, milan_facts, chapter_scores)
        if not ok:
            log.warning("[premium_chapters] validator rejected: %s | lang=%s | hidden=%.180s",
                        reason, lang, str(parsed.get("hidden_truth", ""))[:180])
            return fb

        # Inject engine-derived score into each chapter (LLM never produced it).
        chs_in = parsed.get("chapters", [])
        chs_engine = (chapter_scores or {}).get("chapters", {})
        chapters_clean = []
        for c in chs_in:
            ckey = c.get("key")
            engine = chs_engine.get(ckey, {})
            chapters_clean.append({
                "key": ckey,
                "title": engine.get("title", ckey),
                "score_0_10": engine.get("score_0_10"),
                "kya_dikh": str(c.get("kya_dikh", "")).strip(),
                "kya_matlab": str(c.get("kya_matlab", "")).strip(),
                "kya_dhyan": str(c.get("kya_dhyan", "")).strip(),
                "grounding": str(c.get("grounding", "")).strip(),
            })

        # Marriage blueprint (Phase soul-v3) — clean copy with str coercion.
        mb_in = parsed.get("marriage_blueprint") or {}
        marriage_blueprint = {
            "p1_marriage_nature":    str(mb_in.get("p1_marriage_nature", "")).strip(),
            "p2_marriage_nature":    str(mb_in.get("p2_marriage_nature", "")).strip(),
            "interaction_dynamic":   str(mb_in.get("interaction_dynamic", "")).strip(),
            "what_p1_needs_from_p2": str(mb_in.get("what_p1_needs_from_p2", "")).strip(),
            "what_p2_needs_from_p1": str(mb_in.get("what_p2_needs_from_p1", "")).strip(),
            "blueprint_takeaway":    str(mb_in.get("blueprint_takeaway", "")).strip(),
        }
        polished = {
            "hidden_truth": str(parsed.get("hidden_truth", "")).strip(),
            "chapters": chapters_clean,
            "special": [str(s).strip() for s in parsed.get("special", [])],
            "damage": [str(s).strip() for s in parsed.get("damage", [])],
            "practical": [str(s).strip() for s in parsed.get("practical", [])],
            "verdict": str(parsed.get("verdict", "")).strip(),
            "marriage_blueprint": marriage_blueprint,
            "_meta": {
                "model": model,
                "version": _PREMIUM_VERSION,
                "overall_avg": (chapter_scores or {}).get("overall_avg_0_10"),
                "kp_promise": _kp_couple_band(kp_promise),
                "hidden_signature": _kp_signature_line(kp_promise),
            },
        }
        _l1_put(key, polished)
        _l2_put(key, polished, model)
        return polished

    except Exception as exc:
        log.exception("[premium_chapters] unexpected failure, returning fallback: %s", exc)
        return fb


# ─────────────────────────────────────────────────────────────────────────
#  SOUL FALLBACK (Phase 2.5.11.23-soul, May 8 2026)
# ─────────────────────────────────────────────────────────────────────────
#  Critique: the previous fallback dumped engine drivers verbatim and
#  emitted template phrases ("engine drivers are stable", "No significant
#  friction detected", "Based on engine score X/10"). That made the PDF
#  read like an audit report, not a relationship insight. The replacement
#  below produces 3-layer prose for every chapter:
#    Layer 1 (kya_dikh):   what the chart actually shows, in plain words
#    Layer 2 (kya_matlab): what that means for day-to-day partnership
#    Layer 3 (kya_dhyan):  one specific behavioural anchor the couple can act on
#  Each block is ≥3 sentences, name-anchored, and band-aware (HIGH/MID/LOW).
#  No engine vocab, no template phrases, no negative-detection lines.
# ─────────────────────────────────────────────────────────────────────────

def _band(score: float | None) -> str:
    """Score → narrative band. ≥7 HIGH · 4–6.9 MID · <4 LOW · None MID."""
    try:
        s = float(score) if score is not None else 5.0
    except Exception:
        s = 5.0
    if s >= 7.0: return "HIGH"
    if s >= 4.0: return "MID"
    return "LOW"


# Per-chapter soul library: (kya_dikh, kya_matlab, kya_dhyan) per band.
# Phase 2.5.11.23-soul-v2: each template carries (a) emotional asymmetry —
# "ek partner ... dusra ..." patterns, never perfect-balance language —
# (b) ONE signature insight per chapter that feels noticed, not generic —
# (c) free-flowing prose rather than 3-bullet rhythm — (d) zero therapy
# cliches ("honest dialogue", "open communication", "build trust", etc.).
# Format placeholders: {p1} {p2} {total} {mx}. ch4 + ch7 kya_dhyan keep
# at least one verbatim ALLOWED_REMEDIES phrase ("Joint daily prayers",
# "yearly anniversary ritual") to satisfy the validator's whitelist.
_CH_SOUL: dict[str, dict[str, dict[str, str]]] = {
    "ch1": {
        "HIGH": {
            "kya_dikh":   "Pyaar yahaan loud nahi hai — emotional language ek background hum ki tarah baji rehti hai. {p1} aur {p2} ke andar same emotion alag delivery times pe surface karta hai: kuch face pe pehle, kuch andar baad me. Same pyaar, do delivery rhythms. Jab thakaan zyada hoti hai tab ye chhota gap suddenly bada feel hota hai aur naam diye bina misunderstanding ban jaata hai.",
            "kya_matlab": "Real life me iska shape aisa hai — Sunday raat ko, jab dono thake hain, ek koi chhoti baat bolega aur dusra silent rahega. Silent waala 'naraz' nahi hai, woh actually andar feeling sort kar raha hai. Lekin bolne wala us silence ko reject samajh sakta hai. Ye misunderstanding fight nahi banti — ye dheere se distance banti hai jo agle din tak rehti hai.",
            "kya_dhyan":  "Ek chhota signal-phrase decide kar lo — jaise '5 minute', meaning 'main yahin hoon, bas process kar raha hoon.' Ye ek phrase saalon ke chhote silent rifts cancel karta hai. Hafte me ek 20-minute walk dono saath karo — bina phone, bina agenda. Aur ye samajh lo — emotional rhythms match nahi karte, sirf honour ho sakte hain. Yahi is bond ka secret hai.",
        },
        "MID": {
            "kya_dikh":   "Imagine 9 baje ki chai, dono sofa pe, ek bole 'main theek hoon' aur baat khatm. {p1} ke liye yeh line literal hoti hai — sach me theek hai. {p2} ke liye wahi line ka matlab hota hai 'mujhe gently dobara poochho.' Ye sirf style nahi hai — ye childhood me kaise express karna seekha tha uska imprint hai, aur dono apni truth me sahi hain.",
            "kya_matlab": "Iska matlab — ek partner zyada bar 'main thik hoon' suntega aur bharosa kar lega; dusre ko lagega 'tujhe parwah hi nahi ki main andar kya feel kar raha hoon.' Distance yahaan gusse se nahi banti, ek kaafi-na-poochhne aur ek zyada-poochhne ke loop se banti hai. Reassurance dono ko chahiye, bas alag languages me.",
            "kya_dhyan":  "Hafte me ek 10-minute baith ke baat — bina solving, sirf describing. Bolne wala bole 'aaj is cheez ne mujhe kheecha tha', sunne wala sirf 'aur?' bole, advice nahi. Ek joint daily prayers ya gratitude minute raat ko — chhota emotional reset. Aur ye samajh lena — 'main thik hoon' do alag languages me bola jaata hai; isko translate karna seekhna hi yahaan asli intimacy hai.",
        },
        "LOW": {
            "kya_dikh":   "Sabse purane silent friction-points emotional speed se start hote hain, topic se nahi. {p1} aur {p2} ke andar do alag emotional clocks chal rahe hain — kabhi {p1} intense aur immediate hota hai (feeling aayi, abhi baat karni hai), kabhi {p2} delayed processor jo ek upset moment ko 12 ghante andar baith ke samajhta hai. Ye personality hai, dosh nahi — but jab tak naam nahi diya jaata, dono apni speed ko 'sahi' aur dusre ki ko 'galat' samajhte rehte hain.",
            "kya_matlab": "Roz ke jeevan me iska matlab — fast processor ko lagta hai 'tu avoid kar raha hai, tujhe parwah nahi'; slow processor ko lagta hai 'tu emotional pressure daal raha hai, mujhe saans lene de.' Dono apni jagah pe sahi hain, aur dono ek dusre ko 'galat' label kar dete hain. Ye sabse common silent friction-zone hai shaadi ke pehle 5 saalon me.",
            "kya_dhyan":  "Ek single line jo bahut rishton ko bachati hai — '30 minute, phir baat'. Slow waala bole, fast waala honour kare. Aur 30 minute baad sach me wapas aana padta hai — varna ye line bhi avoidance ban jaati hai. Hafte me ek 30-minute walk dono saath — chalna baat ko softer banata hai. Aur ek baat samajh lena — emotional speed ek personality trait hai, character flaw nahi; jab tak isko 'galat' label nahi karna chhodte, fight ki asli baat kabhi hath nahi aati.",
        },
    },
    "ch2": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo trust hai, woh declarations se nahi banti — chhoti consistencies se banti hai jo dono ne ek dusre ko time ke saath di hain. Ek partner shayad zyada explicitly bolta hai 'I trust you', dusra silently dikhata hai — bina poochhe access dena, bina justify kiye decisions support karna. Dono trust express kar rahe hain, bas alag volumes pe.",
            "kya_matlab": "Real life me iska faayda — bahut shaadiyan jis 'kya woh sach me reliable hai?' wale doubt me energy waste karti hain, woh sawaal tum dono ke beech almost background me hai. Lekin ek subtle risk hai — jab trust strong ho, log usse 'taken-for-granted' bhi treat karne lagte hain. Wahi point pe rishton me dheere se gap banta hai.",
            "kya_dhyan":  "Trust ko maintain karna explicit kaam hai — har 3 mahine ek baar kuch chhota acknowledge karo: 'us din tu ne ye sambhal liya, mujhe yaad hai.' Ek shared commitment ritual rakho — yearly anniversary pe ek paragraph likhke ek dusre ko do. Likhi hui baat boli hui se zyada stick karti hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech trust solid hai, lekin uske kuch specific test-points hain jo abhi tak khulkar discuss nahi hue. Ek partner ke liye trust = full transparency (passwords, location, plans share karna). Dusre ke liye trust = privacy ka respect (kuch chhoti baatein apne paas rakhne ka right). Dono frameworks valid hain, lekin same word 'trust' do alag definitions chhupa raha hai.",
            "kya_matlab": "Day-to-day me ye gap aise dikhega — ek partner ka akele plan banana, ya phone alag rakhna, ya ek doston ka group jisme dusra involved nahi hai — innocent autonomy hai un ke liye, aur thoda 'concerning' lagta hai dusre ke liye. Conflict yahaan loyalty ke baare me nahi hota, definition ke baare me hota hai. Aur jab tak definitions explicit nahi, dono apni assumptions ke andar hurt hote rehte hain.",
            "kya_dhyan":  "Ek baar baith ke explicit list banao — 'mere liye trust break karta hai jab __, theek hai jab __.' Awkward lagega, but ye 30-minute conversation saalon ke chhote chhote silent doubts cancel karti hai. Ek shared commitment ritual — mahine ke pehle Sunday ek 'state-of-us' check-in — chhote misunderstandings ko grudge banne se pehle clear kar deta hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo trust banana hai, usme dono apne pichle anubhav saath laaye hain — apne family me dekhe gaye patterns, ya ek pichla rishta jismein bharosa toota tha. Ek partner shayad isko openly acknowledge karta hai, dusra silently uske weight ke saath chal raha hai bina naam diye. Ye ek hidden weight hai jo abhi tak openly table pe nahi rakha gaya.",
            "kya_matlab": "Iska practical impact roz dikhega — chhoti baatein bhi pehle scrutiny se gujarengi. Ek partner ka late aana, message late karna, plan badalna — innocent things bhi 'iske peeche kya wajah hai?' wala question silently trigger karengi. Aur jo poochhta hai, woh khud thak jaata hai poochhne se; jo poochha jaata hai, woh thak jaata hai justify karne se. Loop dono ko hara deta hai.",
            "kya_dhyan":  "Predictability se trust banti hai — defensiveness se nahi. Ek aadat dalo: chhoti cheezein bhi bina poochhe explain karne ki — 'main 8 baje aaunga, traffic me hoon.' Boring lagega, gold ban jaayega. Ek shared commitment ritual — har raat sone se pehle 1-line gratitude ek dusre ke liye, even when annoyed — woh wall ek mahine me nahi, lekin ek saal me sach me pighal jaati hai.",
        },
    },
    "ch3": {
        "HIGH": {
            "kya_dikh":   "Is rishte ki sabse rare quality conflict ke time pe dikhti hai — issue ek third entity ban jaata hai jise {p1} aur {p2} milke dekh rahe hote hain, ek dusre ke against nahi. Defensive flash kabhi-kabhi aata hai aur soften ho jaata hai; final destination repair hai, attack nahi. Calmness ka matlab unaffected nahi — sirf processing alag jagah ho rahi hai.",
            "kya_matlab": "Real life me iska faayda — bade decisions (career change, city change, parenting timing) pe dono ek table pe baith sakte ho bina personal attack ke. Aur ek aur baat: jo calm dikhta hai woh actually argument ke 4 ghante baad bhi mind me conversation re-run kar raha hota hai. Calmness ka matlab unaffected nahi hai — sirf processing alag jagah ho rahi hai.",
            "kya_dhyan":  "Stress periods me is strength ko erode mat hone do. Ek 24-hour rule banao — koi bhi badi cheez (shift, big purchase, in-laws ka decision) raat ko thake hue mind me decide nahi karenge. Subah chai ke saath. Ek hafte me 1 ghanta — jaise Sunday morning walk — sirf 'hum kaise jaa rahe hain' ke liye reserved rakho.",
        },
        "MID": {
            "kya_dikh":   "Zyadatar arguments {p1} aur {p2} ke beech topic pe nahi, pace pe shuru hote hain. Kabhi {p1} 'abhi resolve karo' camp me hota hai — issues ko pending nahi rakh sakta, raat bhar weight uthata rehta hai. Kabhi {p2} 'pehle thanda hone do, kal subah baat' camp me — fresh head se baat karne ki adat hai. Real topic side me chhoot jaata hai aur fight pace pe ho jaati hai.",
            "kya_matlab": "Aam jhagde isi clash se start hote hain — 'tu avoid kar raha hai' bolne wala, aur 'tu pressure daal raha hai' sunne wala. Real topic side me chhoot jaata hai aur fight pace pe ho jaati hai. Funny baat — har fight ke baad dono apne friend ko kahenge 'argument was about X', actually X kabhi address hi nahi hua. Ye pattern jab tak dikha nahi jaata, ye repeat hota rehta hai.",
            "kya_dhyan":  "Ek seedha rule — jab gussa peak pe ho, koi response 30 minute ke andar nahi dega. Lekin (ye hissa important hai) jo cool down karta hai, woh deadline rakhe — 'main 7 baje tak wapas baat karunga.' Dono apni speed honour karte hain bina dusre ko abandon kiye. Ye chhoti si discipline 70% domestic friction silently hata deti hai.",
        },
        "LOW": {
            "kya_dikh":   "Wahi Tuesday raat, wahi bartan, wahi line — fight ka topic surface pe naya lagta hai, andar same purana hurt khada hai jo {p1} aur {p2} ne abhi tak naam nahi diya. Shayad 'main hamesha akela sambhalta hoon' ka hurt, ya 'mujhe sach me suna nahi jaata' ka quiet resignation. Jab tak woh underground feeling label nahi hoti, fight surface pe roz dohrayi jaati hai.",
            "kya_matlab": "Iska matlab — fight 'jeetne' se raahat nahi aati, kyunki jeeti hui baat woh nahi thi jo actually hurt kar rahi thi. Ek partner ko lagega 'main har baar effort dikhata hoon, fir bhi enough nahi hota'; dusre ko lagega 'mujhe meri reasons sunne ka mauka hi nahi milta.' Dono apni truth me sahi hain. Lekin same shape ki fight 4 baar repeat hoti hai — woh signal hai ki real conversation kabhi hui hi nahi.",
            "kya_dhyan":  "Agar same fight 3 baar ho chuki hai, woh fight ke baare me nahi hai. Ek calm waqt me baith ke ek line poochho — 'is fight me main actually kis cheez se dar raha hoon?' Jawab fight ke topic se completely alag hoga. Ek neutral teesra perspective — couples counselling ka 1 session — patterns ko unlock karta hai jo ghar ke andar se nahi dikhte. Stigma waala kuch nahi hai isme.",
        },
    },
    "ch4": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech ek 'long-haul' instinct natural hai — dono unconsciously is bond ko temporary nahi maante. Commitment ek decision nahi hai, ek default state hai, jaise neend. Lekin ek baat dhyaan dene wali — ek partner shayad zyada openly future ki baat karta hai (5 saal baad ghar, kids, retirement); dusra silently us future me khud ko dekh raha hai bina bole. Dono ka commitment same hai, declaration ka style alag.",
            "kya_matlab": "Real life me — bade structural decisions (ghar, career compromises, parenting timing) pe dono mostly same direction me feel karte hain. Crisis bhi 'shall we still be us' wala existential sawaal trigger nahi karta. Lekin jo silent waala hai — uska commitment dekhne ke liye, words mat dhundo, decisions dhundo. Woh apni har choice me tum dono ke 'us' ko already include kar raha hota hai.",
            "kya_dhyan":  "Stability ko erode hone se bachao — har bade decision se pehle 5-minute joint silence baith ke karo, ek dusre ka haath pakad ke. Bolne se pehle ek breath. Joint daily prayers — even 5 minute subah — is foundation ke liye chhota lekin shocking strong grounding ritual hai. Dono apne yearly anniversary ritual ko deeper banao — same place har saal, ek hi ghanta sirf shukran ka.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech bond serious hai, lekin life-stage transitions (job change, parenting, parents' health crisis, financial stress) is bond ko test karenge. Ek partner shayad change ko openly embrace karta hai, dusra change ke andar bhi continuity dhundta hai. Jab life shift hoti hai, ek partner naturally adjust karta hai aur dusra thoda lambit reh jaata hai — aur woh lag yahaan friction banta hai, change me nahi.",
            "kya_matlab": "Iska matlab — agar dono 'hamesha aisi hi rahegi shaadi' wali expectation rakhenge, har transition pe shock lagega. Real stability adjust karne ki capacity me hai, sthir rehne me nahi. Aur ek bittersweet sach — jo couples 5 saal baad survive karte hain, woh same couples nahi hote jo ek dusre se shaadi karte time the. Evolution kabhi optional nahi hota; sirf together evolve karna ya alag-alag, woh choice hoti hai.",
            "kya_dhyan":  "Har 6 mahine ek 'state-of-our-marriage' baith-ke-baat — kya badla, kya theek hai, kya extra care chahiye. Ye review ritual 80% slow-build problems prevent karta hai. Joint daily prayers ek subtle anchor hai jab life turbulent ho — koi bhi 7-minute joint quiet practice (jaap, gratitude, ya silence) chalegi.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo bond hai, usme ek specific adjustment dono ko shuruat me resist hota hai — aur wahi adjustment long-term stability ka actual key hai. Ye 'ek cheez' har couple ke liye alag — kabhi work-life balance, kabhi family boundaries, kabhi emotional bandwidth. Dono ke andar ek voice hai jo bolti hai 'mera tarika sahi hai', aur jab tak woh voice softer nahi hoti, woh ek cheez baar baar surface pe aati rahegi.",
            "kya_matlab": "Real life me iska matlab — agar dono apni 'mera tarika' position pe atke rahe, friction har 3 mahine me ek baar major fight ban ke phootegi. Lekin agar ek baar khulkar accept kar liya jaaye ki ek practical compromise zaroori hai, ye relationship surprisingly stable ban sakta hai. Funny baat — woh 'ek cheez' jisko sabse zyada resist karte ho, woh actually relationship ke liye sabse healing hoti hai.",
            "kya_dhyan":  "Identify karo — woh ek cheez kya hai jo har baar same fight banti hai? Wahi tumhara real test point hai. Koi neutral teesra perspective (counsellor, trusted elder, mediator) ek baar usko outside frame de — andar se nahi dikhta. Joint daily prayers — 5-7 minute saath silent baithna — mutual softness ka ek constant reminder ban jaata hai. Yearly anniversary ritual — shanti-bhare jagah pe ek din — drift ko silently heal karta hai.",
        },
    },
    "ch5": {
        "HIGH": {
            "kya_dikh":   "Kuch chemistries time ke saath fade hoti hain; kuch deeper layer se khinchti hain, novelty se nahi. {p1} aur {p2} ke beech jo pull hai woh dusra type hai — physical aur emotional dono surface se jude. Kabhi {p1} ke liye chemistry zyada physical dimension me jeeti hai, kabhi {p2} ke liye zyada emotional safety me. Dono real hain, aur dono ek dusre ke without missing rehte hain.",
            "kya_matlab": "Real life me — long-distance phases, busy career years, parenting years me bhi connection survive karega. Touch, eye-contact, shared humor — easy aur consistent rahenge. Lekin ek subtle sach — jab life sabse busy hoti hai, ye chemistry pehli cheez hoti hai jo silently sideline ho jaati hai, kyunki dono assume kar lete hain ki 'ye to natural hai, ye nahi jaayegi.' Aur woh assumption hi sabse mehngi padti hai.",
            "kya_dhyan":  "Routine ko mat barbaad karne do — hafte me ek 'no-screen, no-kids, no-work' evening rakho. Touch ko sirf bedroom tak limit mat rakho — chai dete waqt haath mila lo, ek kandhe pe haath rakh do baith ke. Chhoti continuity badi chemistry banaye rakhti hai — bade gestures se zyada.",
        },
        "MID": {
            "kya_dikh":   "Connection real hai, lekin intimacy ki languages alag hain. {p1} ke liye intimacy = words, presence, baat-cheet ka time. {p2} ke liye intimacy = touch, action, silent saath. Dono valid hain — lekin jab ek apni language me dikhata hai, dusri language me woh translate nahi hota, aur 'enough' nahi feel hota dono ko.",
            "kya_matlab": "Iska matlab — kabhi-kabhi ek partner ko lagega 'isme woh feeling nahi hai jaisi hona chahiye'. Lekin partner is showing it — bas tumhari language me nahi, apni language me. Ye gap silently bahut shaadiyan distance me dhakelta hai. Naam diye bina ye nazar bhi nahi aata — dono apni wajah se hurt mehsoos karte hain bina samjhe ki dusra actually showing up hai.",
            "kya_dhyan":  "Ek baar khulkar baat karo — 'mujhe X way me feel hota hai loved, tujhe kis way me feel hota hai loved?' Ye conversation pehli baar awkward lagti hai aur saalon ki silence ko ek ghante me reset kar deti hai. Hafte me ek dedicated couple-time block calendar pe daal do — non-negotiable, even ek ghanta. Walk, dinner, kuch bhi — bas dono ka.",
        },
        "LOW": {
            "kya_dikh":   "Bahut couples ke liye natural chemistry instant nahi hoti — woh waqt aur safety ke saath build hoti hai. {p1} aur {p2} abhi wahi build-up ke phase me hain. Kabhi {p1} isse 'mismatch' samajh ke internalize karta hai ki 'kuch galat hai humme'; kabhi {p2} zyada practical — 'theek hai, kaam karenge isko.' Dono interpretations dono ko weight de rahi hain.",
            "kya_matlab": "Real life me — agar dono assume karenge ki 'should be natural', frustration silently build hoga. Ye area pressure se kabhi nahi sudharta — sirf openness, low-pressure exploration, aur time se sudharta hai. Aur ek important sach — comparison social media couples se mat karna. Woh actors hain. Real chemistry private, slow, aur often awkward shuruat se grow hoti hai.",
            "kya_dhyan":  "Pressure utaaro — 'perfect intimacy' ka concept hi gira do. Hafte me ek long, slow, planned date — koi performance-expectation nahi, sirf presence. Counselling ek option hai agar conversations stuck feel hon — koi stigma waala kaam nahi hai, aur chhoti window me kaafi safe baat khul jaati hai.",
        },
    },
    "ch6": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo daily-life partnership hai, woh quietly efficient hai. Dono naturally apna apna lane samajhte hain — kaun kya sambhalta hai, kab support deni hai, kab step back karna hai. Family dynamics me bhi dono ek dusre ki side me khade dikhte hain. Lekin dekho — ek partner shayad zyada visible labor karta hai (jo dikhta hai), dusra zyada invisible labor (mental load, planning, remembering). Dono ke contributions equal hain, sirf visibility alag hai.",
            "kya_matlab": "Real life me iska faayda — chhoti chizein (bills, schedules, household, in-laws) silent rehti hain, energy bachi rehti hai bigger things ke liye. Ye couples ka 'silent superpower' hai. Lekin ek hidden risk — invisible labor karne wala dheere thakega, aur uski thakaan dikhegi nahi jab tak woh bahut baad me bahar nahi aati ek unexpected outburst ke shape me. Acknowledgment yahaan trust se zyada important hai.",
            "kya_dhyan":  "Roles ko rigid mat banao — har 6 mahine ek 'who does what now' check kar lo. Life shift hoti hai, distribution bhi shift karna chahiye. Invisible labor karne wale ko explicit acknowledgment do, weekly — naam le ke, kaam batake. Aur ek baat samajh lena: jo dikhta nahi hai, woh thakaata sabse zyada hai — acknowledgment hi yahaan asli reward ban jaata hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech daily life smoothly chal sakti hai, lekin family expectations dono pe alag pressure dalti hain. Dono apne parivaar ki rhythms se aaye hain — gift-giving, festival celebrating, parents ko visit karne ki frequency, even chhoti baatein jaise 'kaun kisko phone karta hai pehle'. Dono ke ghar me normal alag tha. Aur jab tak woh 'normal' explicitly compare nahi hota, dono assume karte hain ki dusra unka normal samajhta hai.",
            "kya_matlab": "Iska matlab — shaadi sirf tum dono ke beech nahi hoti, do families ke beech hoti hai. Jo expectations spoken nahi hain, woh built-in disappointment banti hain. Aur ek subtle baat — ek partner shayad apne family ke saath zyada loyalty feel karta hai (kyunki woh emotional anchor hai), dusra apni family se thoda distance pasand karta hai (kyunki freedom anchor hai). Dono valid, dono ek dusre ke truth ko 'cold' ya 'enmeshed' label kar dete hain.",
            "kya_dhyan":  "Saal ki shuruat me ek baar baith ke decide karo — 'is saal ke major family events kaun-kaun se hain, kis pe priority?' Decisions emotional moment me nahi, calm planning me lo. Joint family dinner monthly — neutral occasion, sab logon ka — ek boundary-friendly ritual ban sakta hai. Aur ye samajh lena — do alag 'normal' ek ghar me jab tak silently coexist karte hain, dono partners apne family ko 'mis-respected' feel karwate rehte hain bina jaane.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke daily life partnership ko deliberately design karna padega — auto-pilot pe ye nahi chalegi. Natural division of labour smooth nahi hai; small things (groceries, bills, who cooks, kis ke parents ka kaam pehle) chronic stress points ban sakte hain. Ek partner shayad zyada uthane lagta hai aur silently resentful hota jaata hai; dusra notice nahi karta, kyunki uske liye 'sab to chal raha hai.'",
            "kya_matlab": "Real life me iska impact — household tension grow karti hai jab unspoken expectations clash karti hain. Family side ke pressures bhi ek partner pe disproportionately gir sakte hain. Ye saalon me silently relationship ko khaata hai — fight ek bartan pe hoti hai, lekin actual feeling 'main akela sambhal raha hoon' wali hoti hai. Aur woh feeling jab tak labelled nahi, naya bartan har hafte phir wahi fight banayega.",
            "kya_dhyan":  "Ek written list banao — har task kis ka primary, kis ka backup. Awkward lagega start me, lekin clarity se peace aati hai. Quarterly review karo aur honestly batao kya overwhelming feel ho raha hai. Aur ek baat samajh lena — silent fairness koi nahi dekhta; jo dikha ke acknowledge hota hai, wahi long-run me asli reward ban jaata hai.",
        },
    },
    "ch7": {
        "HIGH": {
            "kya_dikh":   "5 saal baad, 10 saal baad ki tasveer me, {p1} aur {p2} dono individually grow hue dikhte hain — aur saath bhi. One chart leans toward outward, visible expansion (career, social, achievement); the other carries a quieter, inward growth — depth, perspective, calm. Bahut few couples is direction me jaa paate hain. Dono growth real hai. Agar 'visible' growth ko hi growth maan ke compare karne lagein, kisi ek ko unfairly piche feel ho jaata hai.",
            "kya_matlab": "Real life me — 5 saal baad, 10 saal baad, dono shayad alag-alag heights pe honge — career, social circle, even spiritually. Aur ek dusre ke liye proud aur supportive rahenge. Bahut few couples is direction me jaa paate hain. Lekin ek choti chetawni — comparison ko consciously block karna padega. 'Tumne to ye nahi kiya' jaisa ek bhi line, brick by brick, foundation hila deta hai.",
            "kya_dhyan":  "Har New Year ek baith ke 'individual aur joint goals' likhna ek practice bana lo. Ek dusre ke goals me invested raho — small ways me, jaise interview wale din ek motivating message bhej dena. Yearly anniversary ritual — ek temple ya nature spot pe ek ghanta sirf shukran — direction ko anchor karta hai. Joint daily prayers — chhote duration ke — long-term shared meaning banaye rakhte hain.",
        },
        "MID": {
            "kya_dikh":   "Future ki tasveer abhi {p1} aur {p2} ke beech fully aligned nahi hai. {p1} stability + steady growth chahta hai — predictable ghar, slow-build career. {p2} adventure + change chahta hai — naye experiences, bold moves. Dono valid life-paths hain, lekin same shaadi me alag direction me kheechte hain. Aur is mismatch ko dono abhi tak directly naam nahi de rahe — chhoti baaton me ye gap silently dikhta hai.",
            "kya_matlab": "Iska matlab — agle 5 saal me ek major decision (city, career, kids ka timing, lifestyle) pe dono ko khulkar baat karni hi padegi. Avoid karne se gap kam nahi hota, badhta hai. Jo couples ye conversation jaldi karte hain — even when answers don't match — woh saath grow karte hain kyunki kam-se-kam dono jaante hain ki kahaan negotiate karna hai. Jo nahi karte, woh same ghar me alag jeevan jeene lagte hain — ek baat khaane ki table pe sirf weather pe hoti hai.",
            "kya_dhyan":  "Ek 'next 5 years' map saath baith ke draw karo — kahaan rehna hai, kya kamana hai, kya skip karna hai. Disagreement aaye to negotiate karo, dabao mat. Yearly anniversary ritual — long walk + uninterrupted talk — direction-recalibration ka time hai. Ek 90-minute Sunday brunch ek baar mahine me dedicated rakho — sirf future ki baat ke liye.",
        },
        "LOW": {
            "kya_dikh":   "Long-term direction abhi blurry hai — aur ye fault kisi ka nahi, life-stage hai. {p1} aur {p2} dono apni individual clarity dhundh rahe hain — har koi apne baare me figure out kar raha hai. Shaadi me ek subtle 'kahaan jaa rahe hain hum' wala question silently chodta hai. Asymmetry ye hai ki kisi ek ko is uncertainty se kam comfort hota hai, kisi ko zyada — aur woh asymmetry bhi friction add karti hai.",
            "kya_matlab": "Real life me — shared decisions tough lagengi kyunki dono ke individual paths abhi unclear hain. Ye 'fault' kisi ka nahi hai, life-stage hai. Lekin agar address na ho, drift silently grow karti hai — ek din uthke realize hota hai 'hum ek hi ghar me alag log ho gaye.' Ye dramatic event nahi hai, ye 100 chhote uncommunicated decisions ka cumulative effect hota hai. Aur isse rok-na possible hai, lekin awareness mein.",
            "kya_dhyan":  "Pehle individual clarity pe kaam karo — har partner apne 3-saal goals likhe alag se. Phir saath baith ke overlap dhundo. Ek counsellor ya life-coach ek session bhi helpful — joint future-planning ko structure deta hai. Yearly anniversary ritual — ek shanti-bhare place pe quiet day saath — drift ko slowly heal karta hai. Joint daily prayers — even 5 minute — silent reset ka kaam karte hain jab paths divergent feel ho rahe hon.",
        },
    },
}


def _safe_fallback(milan_facts: dict, chapter_scores: dict,
                   kp_promise: dict | None = None,
                   d9_marriage: dict | None = None) -> dict[str, Any]:
    """Soul-rich deterministic fallback (Phase 2.5.11.23-soul).
    Generates 3-layer chapter prose + rich hidden_truth/special/damage/
    practical/verdict — all name-anchored, no engine vocab, no template
    phrases. Always returns a valid PDF payload even if LLM polish is off
    or unavailable. Defensive against malformed inputs — never raises."""
    # Defensive normalization: never trust caller shape
    mf = milan_facts if isinstance(milan_facts, dict) else {}
    p1d = mf.get("p1") if isinstance(mf.get("p1"), dict) else {}
    p2d = mf.get("p2") if isinstance(mf.get("p2"), dict) else {}
    p1n = (p1d.get("name") if isinstance(p1d.get("name"), str) else None) or "Partner 1"
    p2n = (p2d.get("name") if isinstance(p2d.get("name"), str) else None) or "Partner 2"
    # Coerce numeric fields — caller may send strings
    def _num(v, dflt):
        try: return float(v) if isinstance(v, (int, float, str)) and str(v).strip() != "" else dflt
        except (TypeError, ValueError): return dflt
    total = int(_num(mf.get("total"), 0))
    mx = int(_num(mf.get("max"), 36))
    cs = chapter_scores if isinstance(chapter_scores, dict) else {}
    chs_engine = cs.get("chapters") if isinstance(cs.get("chapters"), dict) else {}
    kp_band = _kp_couple_band(kp_promise)
    ctx = {"p1": p1n, "p2": p2n, "total": total, "mx": mx}

    chapters_out = []
    high_chs: list[tuple[str, str]] = []   # (key, title) for special bullets
    low_chs:  list[tuple[str, str]] = []   # (key, title) for damage bullets
    for k in CHAPTER_KEYS:
        ch = chs_engine.get(k, {}) or {}
        score = ch.get("score_0_10")
        band = _band(score)
        title = ch.get("title", k)
        if band == "HIGH": high_chs.append((k, title))
        elif band == "LOW": low_chs.append((k, title))
        soul = _CH_SOUL.get(k, {}).get(band) or _CH_SOUL.get(k, {}).get("MID") or {}
        kya_dikh = (soul.get("kya_dikh", "")).format(**ctx)
        kya_matlab = (soul.get("kya_matlab", "")).format(**ctx)
        kya_dhyan = (soul.get("kya_dhyan", "")).format(**ctx)
        chapters_out.append({
            "key": k,
            "title": title,
            "score_0_10": score,
            "kya_dikh": kya_dikh[:1200] or
                        f"{p1n} aur {p2n} ke beech is area me ek balanced rhythm hai jo deeper conversation se aur khulta hai.",
            "kya_matlab": kya_matlab[:1200] or
                          f"Iska matlab — daily jeevan me ye chapter sthir hai, lekin growth ke liye intentional attention chahiye.",
            "kya_dhyan": kya_dhyan[:1200] or
                         f"Ek consistent ritual rakho jo dono ko ek dusre ke saath present rakhe — daily ya weekly.",
            "grounding": (f"Reading anchored to {title} layer — band {band}, "
                          f"{p1n} & {p2n} chart cross-reference."),
        })

    # ── Hidden Truth (P3) — 5-7 sentences, total + names + KP plain prose ──
    kp_line = _kp_signature_line(kp_promise) or ""
    hidden = (
        f"{p1n} aur {p2n} ke beech jo bond hai woh classical compatibility pe "
        f"{total} out of {mx} score karta hai — lekin asli kahaani numbers se aage hai. "
        f"Aapke charts ek aisa picture banate hain jisme dono ki strengths "
        f"ek dusre ki gaps ko silently fill karti hain, aur dono ki frictions "
        f"ek dusre ko mature banaati hain. {kp_line} "
        f"Ye relationship perfection nahi maangta — ye honesty maangta hai. "
        f"Jo couples is honesty ko respect karte hain, woh saath grow karte hain. "
        f"Aage ke chapters har layer ko khol ke dikhayenge — kya sahi hai, kya dhyan dene wala hai, "
        f"aur kya woh ek baat hai jo is bond ko legendary bana sakti hai."
    )

    # ── Special (P18) — derived from HIGH chapters; rich 2-3 sentence bullets ──
    special: list[str] = []
    if high_chs:
        for k, title in high_chs[:4]:
            special.append(_special_bullet(k, title, p1n, p2n))
    if len(special) < 3:
        special.append(
            f"{p1n} aur {p2n} ke beech ek aisi quiet trust hai jo declarations "
            f"se nahi banti — chhoti consistent kindness se banti hai."
        )
    if len(special) < 3:
        special.append(
            f"Aap dono naturally ek dusre ko grow hone ki space dete ho — "
            f"jo many couples decades me bhi nahi seekh paate."
        )
    if len(special) < 3:
        special.append(
            f"Aapka score ({total}/{mx}) sirf ek number nahi — ye baat ka indicator hai "
            f"ki dono ke beech intentional partnership ki real foundation hai."
        )

    # ── Damage (P19) — rich, framed as patterns to manage; never "no friction" ──
    damage: list[str] = []
    if low_chs:
        for k, title in low_chs[:4]:
            damage.append(_damage_bullet(k, title, p1n, p2n))
    else:
        damage.append(
            f"Sabse common silent damage — assumptions banana ki '{p1n} aur {p2n} "
            f"ek jaise sochte hain'. Even compatible couples me, har badi cheez "
            f"explicit conversation maangti hai. Jo unsaid reh jaata hai, woh saalon me bhaari ho jaata hai."
        )
        damage.append(
            f"Doosra subtle risk — 'bond strong hai to effort kam karna theek hai' wali "
            f"feeling. Trust ko granted lena sabse silent erosion hai. "
            f"Strong bonds bhi maintain karne padte hain — appreciation aur acknowledgement zaroori hain."
        )

    # ── Practical (P20) — 3-4 paragraphs, name-anchored, behavioral specificity ──
    practical = [
        f"{p1n} aur {p2n} ke daily life me sabse important habit ek hi hai — "
        f"har raat 10 minutes phone-free dialogue. Office baat, family baat, "
        f"plans, frustrations — sab kuch. Ye ek single ritual hi 80% slow-build "
        f"problems prevent karta hai jo aam couples me silent build hote hain.",

        f"Family expectations donon side ki separately samjho. {p1n} ke family ka "
        f"rhythm alag hai, {p2n} ke family ka alag. Ek-dusre ke parents ko explain "
        f"karne ki responsibility apne apne side pe rakho — ye ek small structural "
        f"shift saalon ki tension hata deti hai.",

        f"Money, decisions, and major life choices pe ek shared planning system "
        f"banao — monthly 30-minute check-in, calendar pe block kiya hua. Awkward "
        f"start me, lekin ye predictability se trust deepens, surprise se nahi.",

        f"Ek joint ritual zaroori hai — chahe woh daily evening prayer ho, "
        f"weekly walk ho, ya yearly anniversary trip ho. Couples jo rituals share "
        f"karte hain, woh stress periods me bhi anchored rehte hain. Choose koi "
        f"bhi, but choose karo aur maintain karo.",
    ]

    # ── Verdict (P23) — closing letter with names, total, and a "remember this" line ──
    band_text = "strong" if total >= 28 else ("meaningful" if total >= 21 else "workable")
    verdict = (
        f"{p1n} aur {p2n}, aap dono ke beech jo bond hai woh classical compatibility me "
        f"{total} out of {mx} score karta hai — ek {band_text} foundation. Lekin yaad rakhna — "
        f"score sirf starting point hai, destiny nahi. "
        f"Jo couples ye samajhte hain ki shaadi 'fix karne wali cheez' nahi, 'grow karne wali cheez' hai, "
        f"woh score se aage jaate hain. Aap dono me woh maturity dikhti hai. "
        f"Honest raho. Kind raho. Ek dusre ke baare me curious raho — even after years. "
        f"Jab raasta kabhi confusing lage, ye paragraph dobara padhna — yahin se shuruat ki thi."
    )

    blueprint = _safe_fallback_blueprint(d9_marriage, p1n, p2n)

    return {
        "hidden_truth": hidden,
        "chapters": chapters_out,
        "special": special,
        "damage": damage,
        "practical": practical,
        "verdict": verdict,
        "marriage_blueprint": blueprint,
        "_meta": {
            "model": "fallback-soul-v3",
            "version": _PREMIUM_VERSION,
            "kp_promise": kp_band,
            "hidden_signature": kp_line,
        },
    }


# ─────────────────────────────────────────────────────────────────────────
#  MARRIAGE BLUEPRINT (Phase 2.5.11.23-soul-v3)
# ─────────────────────────────────────────────────────────────────────────
# Translates D9 marriage-character signals into pure relational character
# language. The fallback NEVER quotes raw chart vocab — it interprets the
# lagna lord, Venus/Jupiter dignity, and marriage_maturity into the kind
# of marriage nature each partner brings, and the shape of the daily
# rhythm that emerges between them.
# ─────────────────────────────────────────────────────────────────────────

# Lagna-lord → innate marriage nature (interpreted, not raw)
_LORD_NATURE = {
    "Sun":     "leads with quiet authority — committed, principled, holds the centre when things get loud",
    "Moon":    "leads with emotional attunement — naturally nurturing, reads the room before speaking",
    "Mars":    "leads with directness and protective energy — quick to act, slow to forgive, fiercely loyal",
    "Mercury": "leads with curiosity and adaptability — talks things through, loves shared ideas, reads people fast",
    "Jupiter": "leads with warmth and steady values — wants meaning in the relationship, not just routine",
    "Venus":   "leads with affection and aesthetic care — needs beauty, ease, and tender daily moments",
    "Saturn":  "leads with discipline and quiet patience — slow to open up, but once committed, deeply consistent",
}

# Maturity score → tone qualifier
def _maturity_word(score) -> str:
    try:
        s = float(score)
    except Exception:
        return "still finding its full depth"
    if s >= 7.5: return "carries marriage as a deeply mature space — knows how to hold a long bond"
    if s >= 5.5: return "is growing into the depth marriage asks for — capable, still learning"
    if s >= 3.5: return "approaches marriage with sincerity but still meets some tender, unfinished places"
    return "still meeting marriage as a teacher — every chapter here is part of becoming"


def _interaction_phrase(rel_lagna: str, rel_seven: str) -> str:
    """Couple's interaction shape from the deeper character relation."""
    if rel_lagna in ("same", "friendly") and rel_seven in ("same", "friendly"):
        return ("Their natures meet in the same emotional language. Daily rhythm "
                "settles quickly; conflict pauses are short. The risk is the opposite "
                "of friction — taking the ease for granted.")
    if rel_lagna == "hostile" or rel_seven == "hostile":
        return ("Their inner natures speak slightly different languages. One leads "
                "where the other waits, one moves where the other steadies. This is "
                "not incompatibility — it's the asymmetry that makes growth possible, "
                "but only if both name it instead of resenting it.")
    return ("Their natures meet in a workable mid-zone — not effortlessly aligned, "
            "not opposed. Daily rhythm builds through repetition and small understandings, "
            "not through instant chemistry. Patience is the silent superpower here.")


def _safe_fallback_blueprint(d9: dict | None, p1n: str, p2n: str) -> dict[str, str]:
    """Generate the marriage_blueprint section from D9 signals.
    Always returns a valid dict — never raises. Uses generic-but-warm
    text when D9 is unavailable. NEVER quotes raw chart vocabulary."""
    d9 = d9 if isinstance(d9, dict) else {}
    p1d = d9.get("p1") if isinstance(d9.get("p1"), dict) else {}
    p2d = d9.get("p2") if isinstance(d9.get("p2"), dict) else {}
    sync = d9.get("sync") if isinstance(d9.get("sync"), dict) else {}

    p1_lord = p1d.get("d9_lagna_lord") or "Jupiter"
    p2_lord = p2d.get("d9_lagna_lord") or "Venus"
    p1_nature = _LORD_NATURE.get(p1_lord, _LORD_NATURE["Jupiter"])
    p2_nature = _LORD_NATURE.get(p2_lord, _LORD_NATURE["Venus"])
    p1_mat = _maturity_word(p1d.get("marriage_maturity_0_10"))
    p2_mat = _maturity_word(p2d.get("marriage_maturity_0_10"))

    rel_lagna = (sync.get("lagna_lord_relation") or "neutral").lower()
    rel_seven = (sync.get("seven_lord_relation") or "neutral").lower()

    p1_marriage_nature = (
        f"{p1n} ki marriage nature ek aisi hai jo {p1_nature}. "
        f"Andar se {p1n} {p1_mat}. Iska matlab — jab pressure aata hai, "
        f"{p1n} apne natural style se respond karta hai, koi performance nahi."
    )
    p2_marriage_nature = (
        f"{p2n} ki marriage nature alag energy carry karti hai — woh {p2_nature}. "
        f"Andar se {p2n} {p2_mat}. Yeh nature {p1n} ki nature se complementary hai, "
        f"identical nahi — aur shaadi me yahi diversity strength banti hai jab dono samjhein."
    )
    interaction_dynamic = (
        f"{p1n} aur {p2n} ke beech jo daily rhythm banegi, woh in dono ki "
        f"different inner natures ka product hai. {_interaction_phrase(rel_lagna, rel_seven)} "
        f"Ek partner shayad pehle bolega, dusra silently absorb karega — yeh natural hai, "
        f"galat nahi. Dono apne style me marriage ko honour kar rahe hain."
    )
    what_p1_needs_from_p2 = (
        f"{p1n} ko {p2n} se sabse zyada chahiye predictable warmth — "
        f"chhoti consistent gestures, na ki badi declarations. Jab {p1n} thoda "
        f"silent ho jaaye, woh withdrawal nahi hai — woh ek invitation hai gentle "
        f"presence ki. Force karne se peeche jaayega; quiet dene se kheechke aayega."
    )
    what_p2_needs_from_p1 = (
        f"{p2n} ko {p1n} se chahiye explicit acknowledgment — words me, "
        f"not just actions me. Ek 'tu ne ye sambhal liya, dekha maine' wala line "
        f"{p2n} ke andar saalon tak goonjta hai. Silently care karne se {p2n} "
        f"ko shaayad woh care reach hi nahi kare — {p1n} ko isko naam dena seekhna hoga."
    )
    blueprint_takeaway = (
        f"{p1n} aur {p2n} ki shaadi do alag natures ka meeting hai — "
        f"identical natures shaayad asaan lagti, lekin diverse natures depth "
        f"banati hain jab dono apni asymmetry ko strength samjhein, weakness nahi."
    )
    return {
        "p1_marriage_nature":    p1_marriage_nature[:680],
        "p2_marriage_nature":    p2_marriage_nature[:680],
        "interaction_dynamic":   interaction_dynamic[:680],
        "what_p1_needs_from_p2": what_p1_needs_from_p2[:680],
        "what_p2_needs_from_p1": what_p2_needs_from_p1[:680],
        "blueprint_takeaway":    blueprint_takeaway[:680],
    }


# ── Bullet generators for special/damage (P18/P19) ──
_SPECIAL_BY_CH = {
    "ch1": "Emotional rhythm — {p1} aur {p2} ke nervous-system level pe ek quiet familiarity hai. Bahut log isko 'connection' bolte hain; tum dono ke liye ye default state hai.",
    "ch2": "Trust ka foundation — dono naturally apne word rakhne wale log ho. Ye chhoti sthirta hi long-term bonds ka asli stone hai.",
    "ch3": "Conflict maturity — disagreement personal attack me convert nahi hoti. Ye couples ki rare gift hai jo bahut couples saalon ki therapy ke baad bhi nahi seekh paate.",
    "ch4": "Long-haul instinct — dono unconsciously is bond ko temporary nahi maante. Stress me bhi 'shall we still be us in 10 years' wala question aata hi nahi.",
    "ch5": "Chemistry that lasts — physical aur emotional pull novelty se nahi, deeper layers se aata hai. Years ke baad bhi ye fade nahi hoga.",
    "ch6": "Daily life partnership — silent efficiency hai. Chhoti chizein bina drama ke chal jaati hain, energy bachi rehti hai bigger moments ke liye.",
    "ch7": "Future direction — dono ek aise raaste pe hain jahaan saath bhi grow honge aur individually bhi. Ye partnership ka highest form hai.",
}
_DAMAGE_BY_CH = {
    "ch1": "Emotional pacing — {p1} aur {p2} ki feeling-clocks alag speed pe chalti hain. Ek immediate hai, dusra delayed processor. Bina samjhe ye saalon ki chronic 'tu mujhe samajhta nahi' wali feeling banata hai.",
    "ch2": "Trust definitions — dono ke 'trust' ka definition slightly alag hai. Ek ke liye = full transparency, dusre ke liye = privacy ka respect. Explicit nahi karoge to silent grievances build honge.",
    "ch3": "Conflict pacing — {p1} aur {p2} me ek 'abhi solve karo' camp me hai, dusra 'thanda hone do' camp me. Real fight topic pe nahi, pace pe ho jaati hai. Yahi most-repeated argument ka shape hai.",
    "ch4": "Stability test point — {p1} aur {p2} ke beech ek specific adjustment hai jo dono shuruat me resist karenge — wahi adjustment long-term stability ka actual key hai. Ignore karoge to wahi recurring fight ban jaayegi.",
    "ch5": "Intimacy languages — needs alag tareeke se express hoti hain. Ek partner ko lagega 'isme us tarah ki feeling nahi hai jaisi honi chahiye', jab actually partner is showing it in their language. Naam diye bina ye gap silently bahut couples ko alag karta hai.",
    "ch6": "Family expectations — {p1} aur {p2}, donon side ke family ke unspoken rules clash karenge. Ye relationship ke andar tension nahi laata, lekin saalon me energy chusta hai.",
    "ch7": "Direction drift — {p1} aur {p2} agar individual clarity ke bina chalein, joint direction blurry rahegi. Drift ek silent risk hai — ek din realize hota hai 'hum bahut alag log ho gaye'.",
}

def _special_bullet(ch_key: str, title: str, p1n: str, p2n: str) -> str:
    tpl = _SPECIAL_BY_CH.get(ch_key) or "{p1} aur {p2} ke beech is area me natural strength hai jo time ke saath aur deeper hoti jaayegi."
    return tpl.format(p1=p1n, p2=p2n)

def _damage_bullet(ch_key: str, title: str, p1n: str, p2n: str) -> str:
    tpl = _DAMAGE_BY_CH.get(ch_key) or "{p1} aur {p2} ke beech is area me extra conscious effort chahiye — silent assumptions yahaan sabse mehngi padti hain."
    return tpl.format(p1=p1n, p2=p2n)


def _kp_couple_band(kp_promise: dict | None) -> str:
    """Resolve the couple-level promise band from the kp_promise dict.
    Accepts either the per-side or the couple wrapper shape; returns one of
    STRONG / PARTIAL / WEAK / UNAVAILABLE."""
    if not isinstance(kp_promise, dict):
        return "UNAVAILABLE"
    band = kp_promise.get("couple_verdict") or kp_promise.get("verdict")
    if isinstance(band, str) and band.upper() in ("STRONG", "PARTIAL", "WEAK", "UNAVAILABLE"):
        return band.upper()
    return "UNAVAILABLE"


def _kp_signature_line(kp_promise: dict | None) -> str:
    """Plain-language one-line signature for the P3 grounding card.
    Translates the hidden KP marriage-promise reading into everyday words —
    NEVER leaks jargon (no CSL/sub-lord/significator/house numbers).
    """
    if not isinstance(kp_promise, dict):
        return ""
    band = (kp_promise.get("couple_verdict") or kp_promise.get("verdict") or "").upper()
    plain = {
        "STRONG":  "Both charts carry a clear, supportive marriage signal underneath.",
        "PARTIAL": "Both charts carry a present but mixed marriage signal underneath — workable, not effortless.",
        "WEAK":    "The deeper marriage signal in both charts is faint — patience and intentional effort matter more here.",
    }
    return plain.get(band, "")
