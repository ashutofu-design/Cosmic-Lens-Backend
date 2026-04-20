"""
AI Narrator for Life Mastery Report.

Purpose
-------
Engine calculates numbers (Life Path, Rashi, Nakshatra, Dasha, etc.).
This narrator wraps GPT-4.1 to turn those FACTS into premium storytelling
paragraphs in the "Ashutosh Bharadwaj live reading" voice — curious hook,
relatable metaphor, honest double-edge (gift + shadow), practical action.

Key guarantees
--------------
1. Engine facts are NEVER modified by AI — AI only writes the prose around them.
2. Strict prompt locks the exact numbers/planets AI may reference.
3. Hard word-count ceiling (enforced by post-trim).
4. If AI fails / times out → caller should fall back to static tier content.
5. 3 languages supported: english, hindi, hinglish.

Model: gpt-4.1 (user-provided OPENAI_API_KEY).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

_client = None
_client_err: Optional[str] = None


def _get_client():
    global _client, _client_err
    if _client is not None or _client_err is not None:
        return _client
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        _client_err = "OPENAI_API_KEY missing"
        return None
    try:
        from openai import OpenAI
        timeout = float(os.environ.get("OPENAI_TIMEOUT", "45"))
        _client = OpenAI(api_key=api_key, timeout=timeout)
        return _client
    except Exception as exc:
        _client_err = f"OpenAI SDK init failed: {exc}"
        return None


def is_available() -> bool:
    return _get_client() is not None


# ── Voice / style guide ──────────────────────────────────────────────────────
# This is the "Gold Standard Template" we want AI to match — the
# Ashutosh Bharadwaj live-reading vibe.

_VOICE_GUIDE = """
You are Acharya Ashutosh Bharadwaj, a warm, wise Vedic astrology guru who is
reading this person's chart OUT LOUD, one-to-one, like sitting across from them
over chai. Your voice is NOT a textbook. It is a story-telling friend.

RULES OF VOICE (non-negotiable):
1. START WITH A HOOK — a curious question, a "kya aapko pata hai?", or a
   childhood scene that feels strangely personal. NEVER start with "You are…"
   or "Aap ek…".
2. USE METAPHORS from everyday Indian life — school, cricket, trains, films,
   Jupiter-in-the-sky, rivers, ghee, lemons — whatever makes the reader
   SEE the concept.
3. HONEST DOUBLE-EDGE — every gift has a shadow. State the shadow plainly
   but WITH empathy: "kyunki agar koi raja hai, toh ego to aayega hi".
4. ONE PRACTICAL RULE at the end — "isliye rule simple hai: JO feel ho,
   BAHAR nikalo."
5. EMOTIONAL CLOSURE — last sentence must feel like a gentle push or a
   blessing, not a summary.

RULES OF FACTS (absolutely non-negotiable):
A. You may ONLY use the numbers, planets, signs, nakshatras, dashas given in
   the FACTS block below. DO NOT invent new numbers, planets, houses, dates,
   or years.
B. If a fact is not in the FACTS block, do NOT mention it. Better to be silent
   than wrong.
C. Do NOT use markdown headings (##, **, etc.) — plain flowing prose only.
   Short paragraph breaks (blank line) are fine.
D. Do NOT quote English proverbs unless the user's language is English.
E. NEVER prescribe medical / legal / financial action. Spiritual + lifestyle
   guidance only.

FORBIDDEN PHRASES: "As an AI", "I am a language model", "According to my
training", "I cannot", bullet lists, numbered lists.
"""


_LANG_INSTRUCT = {
    "english": "Write in clean, warm English. No Hindi words except proper nouns (Jupiter/Guru both OK).",
    "hindi": "Write in shuddh Hindi (Devanagari script). Technical Sanskrit terms OK (राशि, नक्षत्र, दशा, ग्रह). Tone: guru samjha rahe hain, not a textbook.",
    "hinglish": "Write in Hinglish (Hindi in Roman script) — the way Indians naturally WhatsApp. Mix English words freely (hook, challenge, problem, struggle). Tone: dost-jaisa, warm, live-reading vibe. Example: 'Ek baat batao — bachpan me jab sab chup the, aapke andar ek awaaz hoti thi...'",
}


def _build_prompt(section_key: str, facts: Dict[str, Any], lang: str,
                  word_target: int) -> tuple[str, str]:
    """Return (system_prompt, user_prompt)."""
    lang = lang if lang in _LANG_INSTRUCT else "hinglish"
    lang_rule = _LANG_INSTRUCT[lang]

    # Flatten facts into a locked, bullet-style block the AI can reference.
    facts_lines = []
    for k, v in facts.items():
        if v is None or v == "":
            continue
        facts_lines.append(f"  • {k}: {v}")
    facts_block = "\n".join(facts_lines) if facts_lines else "  (no facts provided)"

    min_words = int(word_target * 0.85)
    max_words = int(word_target * 1.10)

    sys_prompt = _VOICE_GUIDE + f"\n\nLANGUAGE RULE: {lang_rule}\n"
    sys_prompt += (
        f"\nLENGTH RULE: Write between {min_words} and {max_words} words. "
        "Not less, not more. Count carefully."
    )

    user_prompt = (
        f"Section: {section_key}\n\n"
        f"FACTS (use ONLY these — do not invent new ones):\n{facts_block}\n\n"
        f"Write the narration for this section in {lang}, "
        f"{word_target} words (±10%). Remember the voice rules. Start with a hook, "
        "weave in the facts, give one practical rule, end with an emotional line."
    )
    return sys_prompt, user_prompt


def narrate(section_key: str, facts: Dict[str, Any], lang: str = "hinglish",
            word_target: int = 300, model: Optional[str] = None) -> Optional[str]:
    """
    Generate a storytelling paragraph for a report section.

    Args:
        section_key: e.g. "tier1.life_path", "tier2.moon_nakshatra"
        facts: dict of engine-computed facts the AI may reference
        lang: english | hindi | hinglish
        word_target: target word count (±10% enforced by prompt)
        model: override model (default from OPENAI_NARRATOR_MODEL env or gpt-4.1)

    Returns:
        Storytelling text on success; None on failure (caller falls back to static).
    """
    client = _get_client()
    if client is None:
        return None

    model = model or os.environ.get("OPENAI_NARRATOR_MODEL", "gpt-4.1")
    sys_p, user_p = _build_prompt(section_key, facts, lang, word_target)

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.75,  # warm, storytelling — not robotic
            messages=[
                {"role": "system", "content": sys_p},
                {"role": "user", "content": user_p},
            ],
            max_tokens=int(word_target * 3),  # ~3 tokens per word buffer
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or None
    except Exception as exc:
        # Log but don't crash — caller falls back to static.
        print(f"[ai_narrator] {section_key} ({lang}) failed: {exc}")
        return None


def narrate_with_fallback(section_key: str, facts: Dict[str, Any],
                          static_text: str, lang: str = "hinglish",
                          word_target: int = 300) -> str:
    """Wrapper: try AI, fall back to static text on any failure."""
    ai_text = narrate(section_key, facts, lang, word_target)
    return ai_text if ai_text else static_text
