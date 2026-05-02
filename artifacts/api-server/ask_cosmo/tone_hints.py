"""ask_cosmo/tone_hints.py — emotion-aware tone hint helper (Phase 2.8.42).

Phase 2.8.43 (02 May 2026): extracted verbatim from openai_helper.py L1005-1062
into the new `ask_cosmo/` package alongside `understanding.py`. No logic
change; pure relocation. The two public symbols are re-exported via
`ask_cosmo/__init__.py` so callers can do
`from ask_cosmo import _build_emotion_tone_hint`.

Why this lives in ask_cosmo, not openai_helper:
- It is a pure consumer of `understand_question()`'s `emotion` + `urgency`
  fields (no kundli, no LLM call, no engine state).
- Keeping it next to the classifier makes the question-understanding
  surface area discoverable in one folder.

Phase 2.8.42 — composes a tone-hint block for the system prompt that
augments the question_understanding classifier output. Reads two new
SQU fields: `emotion` (anxiety / frustration / sadness / anger /
confusion / neutral / excitement) and `urgency` enum (low / medium /
high). When emotion != neutral, we APPEND a 1-2 line tone directive to
the system prompt so the narrator opens with empathy BEFORE diving into
facts. Pure additive — no engine-fact change, no routing change. The
directive is a soft hint (single block); the narrator's existing
contracts (Rule 1-N) still drive structure.

Returns "" for neutral / excitement / unknown emotion → prompt is
byte-identical to pre-2.8.42 behaviour, preserving prompt-cache hits.
"""

from __future__ import annotations


_EMOTION_TONE_HINT_HN = {
    "anxiety": (
        "User pareshan / anxious feel kar raha hai. Pehli 1 line "
        "REASSURANCE do (jaise: 'Aaram se, dekho — ghabraane ki baat "
        "nahi'), uske baad hi facts batao. Tone: shaant, supportive."
    ),
    "frustration": (
        "User tang aa chuka hai / frustrated hai. Pehli 1 line uski "
        "feeling VALIDATE karo (jaise: 'Samajh raha hu — ye situation "
        "real mein thakaa deti hai'), fir solution-oriented answer."
    ),
    "sadness": (
        "User udaas hai. Gentle empathy se shuru karo (1 line), fir "
        "answer dete waqt ek hope-anchor zaroor rakhna (kuch positive "
        "engine-fact se justified)."
    ),
    "anger": (
        "User gussa / irritated hai. Pehle uski baat ACKNOWLEDGE karo "
        "('Samjha — ye annoying hai'), defensive mat hona, balanced "
        "view do. Lecture mat do."
    ),
    "confusion": (
        "User confused hai. Har point CLEAN single-thought sentences "
        "mein likho. Jargon avoid karo. Ek-ek concept simple example "
        "ke saath. Speed slow rakho."
    ),
}


def _build_emotion_tone_hint(emotion, urgency="medium") -> str:
    """Phase 2.8.42 — compose tone-hint block for the system prompt.

    Returns '' for neutral / excitement / unknown emotion so the prompt
    stays cache-friendly in the common path. When emotion is one of
    the 5 negative-affect labels, returns a small block that nudges
    narrator opening tone WITHOUT changing engine facts or routing.

    `urgency='high'` adds a brief tail nudging concise + immediate
    action focus; otherwise no tail (medium/low = default pacing).
    """
    try:
        e = (emotion or "").strip().lower()
        hint = _EMOTION_TONE_HINT_HN.get(e)
        if not hint:
            return ""
        u = (urgency or "medium").strip().lower()
        urgency_tail = ""
        if u == "high":
            urgency_tail = (
                " Urgency HIGH — answer ko concise rakho aur immediate "
                "next-step (1 actionable line) zaroor do."
            )
        return (
            "\n[EMOTION-AWARE TONE — Phase 2.8.42]\n"
            f"{hint}{urgency_tail}\n"
        )
    except Exception:
        return ""


__all__ = ["_EMOTION_TONE_HINT_HN", "_build_emotion_tone_hint"]
