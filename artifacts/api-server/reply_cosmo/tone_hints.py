"""reply_cosmo/tone_hints.py - emotion-aware tone hint helper.

Phase 2.8.49 (02 May 2026) - relocated from `ask_cosmo/tone_hints.py`
into `reply_cosmo/` so the entire response-shaping surface lives in
one place. Behavior preserved verbatim.

Why this lives in reply_cosmo (not ask_cosmo):
- It is a pure RESPONSE-SHAPING helper: takes SQU output (`emotion`,
  `urgency`) and emits a system-prompt directive that nudges the
  narrator's opening tone. No question-classification logic.
- ask_cosmo = "KYA poocha" (question understanding); reply_cosmo =
  "KAISE jawab dena" (response shaping). Tone-hints belong on the
  shaping side, even though they consume question-side data.

`ask_cosmo/tone_hints.py` remains as a back-compat re-export shim so any
caller still doing `from ask_cosmo import _build_emotion_tone_hint` keeps
working. The canonical import is now
`from reply_cosmo import _build_emotion_tone_hint`.

Phase 2.8.43 history (preserved): originally extracted from
openai_helper.py L1005-1062 and placed in `ask_cosmo/`.

Phase 2.8.44a history (preserved): SERVER-SIDE ROTATION. The first
attempt presented the LLM with a list of 4 anchors and asked it to
choose; live testing showed the LLM reliably copied anchor #1 verbatim
across consecutive runs (LLMs anchor on first example in a list). Fix:
rotate server-side via `random.choice()` and present ONE anchor per
request as a stylistic hint, with instruction "use as inspiration, do
NOT copy verbatim - rephrase in your own words". Probabilistic
variation across requests; uniform distribution; same anchor can
repeat by chance. If strict no-repeat variation is ever required, swap
`random.choice` for a shuffle-bag / round-robin tracker keyed by
emotion. Verified live: 5 consecutive anxiety calls produced 5 distinct
openings (3 unique anchors picked, LLM paraphrased each).

Phase 2.8.42 base: composes a tone-hint block for the system prompt
augmenting `understand_question()`'s `emotion` (anxiety / frustration /
sadness / anger / confusion / neutral / excitement) and `urgency` (low /
medium / high). When emotion != neutral, APPENDS a 1-2 line tone
directive so the narrator opens with empathy BEFORE diving into facts.
Pure additive - no engine-fact change, no routing change.

Returns "" for neutral / excitement / unknown emotion -> prompt is
byte-identical to pre-2.8.42 behaviour, preserving prompt-cache hits.
"""

from __future__ import annotations

import random


# Phase 2.8.44 - each emotion now maps to (instruction, [anchor list]).
# The anchor list is a SET of natural openings the narrator can use as
# stylistic anchors; the prompt explicitly tells the LLM to pick ONE
# naturally and AVOID verbatim copy. This kills the template-feel that
# emerged when the single-string version baked one example into the
# prompt and the LLM copied it on every request.
_EMOTION_TONE_HINT_HN = {
    "anxiety": (
        "User pareshan / anxious feel kar raha hai. Pehli 1 line "
        "REASSURANCE do - tone shaant aur supportive rakho, fir facts.",
        [
            "Aaram se, dekhiye - ghabraane ki baat nahi.",
            "Tension lene ki zarurat nahi, situation samajhne dete hain.",
            "Saans lijiye, main aapki concern samajh raha hu.",
            "Pehle ek baat clear kar du - dar ki koi wajah nahi hai.",
        ],
    ),
    "frustration": (
        "User tang aa chuka hai / frustrated hai. Pehli 1 line uski "
        "feeling VALIDATE karo, fir solution-oriented answer.",
        [
            "Samajh raha hu - ye situation real mein thakaa deti hai.",
            "Aap sahi keh rahe hain, ye wait genuinely frustrating hai.",
            "Bilkul valid hai aapka frustration - chaliye dekhte hain.",
            "Ye lambi process kisi ko bhi tang kar deti hai, samajh raha hu.",
        ],
    ),
    "sadness": (
        "User udaas hai. Gentle empathy se shuru karo (1 line), fir "
        "answer dete waqt ek hope-anchor zaroor rakhna (positive engine-"
        "fact se justified).",
        [
            "Aapka feel samajh raha hu, mushkil dor hota hai ye.",
            "Pata hai bhaari lag raha hoga, sath chaliye dekhte hain.",
            "Aapki baat suni - ye phase real me heavy hai.",
            "Hum dheere se chalte hain, ek-ek baat dekh ke.",
        ],
    ),
    "anger": (
        "User gussa / irritated hai. Pehle uski baat ACKNOWLEDGE karo, "
        "defensive mat hona, balanced view do. Lecture mat do.",
        [
            "Samjha - ye annoying hai, gussa aana natural hai.",
            "Aapki baat valid hai, ye situation chidata hai.",
            "Theek hai, point clear hai - chaliye seedhi baat karte hain.",
            "Frustration genuine hai, ignore nahi kar raha.",
        ],
    ),
    "confusion": (
        "User confused hai. Har point CLEAN single-thought sentences "
        "mein likho. Jargon avoid karo. Ek-ek concept simple example "
        "ke saath. Speed slow rakho.",
        [
            "Chaliye step-by-step samjhate hain.",
            "Ek-ek karke clear karte hain, jaldi nahi.",
            "Simple language mein bata raha hu - ek line ek baat.",
            "Confusion natural hai, tukde-tukde mein dekhte hain.",
        ],
    ),
}


def _build_emotion_tone_hint(emotion, urgency="medium", _rng=None) -> str:
    """Phase 2.8.42 - compose tone-hint block for the system prompt.

    Phase 2.8.44a - SERVER-SIDE ROTATION: we randomly pick ONE anchor
    from the per-emotion list each call (using `random.choice`) and
    present only that one to the LLM, with instruction "use as
    INSPIRATION, do NOT copy verbatim, rephrase in your own words".
    This gives PROBABILISTIC variation across requests (uniform
    distribution; same anchor can repeat by chance) PLUS nudges
    intra-request paraphrase. The earlier "give LLM a list of 4, ask
    it to choose" approach failed live (3 consecutive runs all picked
    anchor #1 verbatim - LLMs anchor on first example in a list).

    Returns '' for neutral / excitement / unknown emotion so the prompt
    stays cache-friendly in the common path. When emotion is one of
    the 5 negative-affect labels, returns a small block that nudges
    narrator opening tone WITHOUT changing engine facts or routing.

    `urgency='high'` adds a brief tail nudging concise + immediate
    action focus; otherwise no tail (medium/low = default pacing).

    `_rng` is an optional `random.Random` instance for deterministic
    test runs; production callers leave it None and get module-level
    `random.choice` (cryptographically-non-secure but fine for stylistic
    variation).
    """
    try:
        e = (emotion or "").strip().lower()
        entry = _EMOTION_TONE_HINT_HN.get(e)
        if not entry:
            return ""
        # Backward-compat: if a caller mutated the dict to put a string
        # back (or some test stub), still handle it gracefully.
        if isinstance(entry, str):
            instruction, anchors = entry, []
        else:
            instruction, anchors = entry
        u = (urgency or "medium").strip().lower()
        urgency_tail = ""
        if u == "high":
            urgency_tail = (
                " Urgency HIGH - answer ko concise rakho aur immediate "
                "next-step (1 actionable line) zaroor do."
            )
        # Phase 2.8.44a - rotate ONE anchor per request server-side.
        if anchors:
            picker = _rng.choice if _rng is not None else random.choice
            chosen = picker(anchors)
            anchor_block = (
                "\nSTYLE ANCHOR (use as INSPIRATION only - DO NOT copy "
                "verbatim, rephrase in your own words):\n"
                f"  > {chosen}"
            )
        else:
            anchor_block = ""
        return (
            "\n[EMOTION-AWARE TONE - Phase 2.8.42/44a]\n"
            f"{instruction}{urgency_tail}"
            f"{anchor_block}\n"
        )
    except Exception:
        return ""


__all__ = ["_EMOTION_TONE_HINT_HN", "_build_emotion_tone_hint"]
