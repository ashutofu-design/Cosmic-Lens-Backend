"""
narrator_cosmo — "AI Mouth" / response-shaping package
=======================================================

Phase 2.8.45 (current) — Initial extraction of narrator surface from
openai_helper.py. Mirror of the Phase 2.8.43 ask_cosmo move (which
extracted question-understanding into ask_cosmo/).

Scope split between ask_cosmo and narrator_cosmo:

  ask_cosmo/         →  "KYA poocha" — input understanding
                          - understanding.py  (intent classifier)
                          - tone_hints.py     (emotion → style nudge)

  narrator_cosmo/    →  "KAISE jawab" — response shaping
                          - narrator_v2.py    (P3 conversational diagnostic
                                               card narrator — wealth-card
                                               structured render path)
                          - validators.py     (post-LLM output guards)
                          - hinglishify.py    (zodiac EN→Hinglish scrubber +
                                               recursive payload walker)

What is INTENTIONALLY still in openai_helper.py (Phase 2.8.45 deferred —
will be moved in a follow-up phase, kept where they live to avoid a
high-risk wholesale refactor in one shot):

  Prompt builders (4):
    - _build_topic_lock()                    (openai_helper L887)
    - _build_wealth_structured_system_prompt (openai_helper L1619)
    - _build_true_intent_hint()              (openai_helper L8895, gated by
                                              Phase 2.8.44 confidence floor)
    - _build_repair_prompt()                 (openai_helper L9315)

  Validators (2):
    - _validate_wealth_payload()             (openai_helper L1901)
    - _validate_supertype_contract()         (openai_helper L9933)

These remain in openai_helper.py because they reference many internal
regex constants, helper functions, and module-level state. Moving them
requires a careful per-function dependency walk (see Phase 2.8.45 doc
in replit.md). The functions in this folder are the "low-coupling"
subset that move cleanly without dragging dependencies along.

Backward compat:
  - Root `narrator_v2.py` remains as a thin facade re-exporting from
    narrator_cosmo.narrator_v2 so existing test imports
    (`from narrator_v2 import _validate_card`) keep working.
  - openai_helper.py re-imports the 3 moved validator/hinglishify
    functions at module top so existing call sites
    (`from openai_helper import hinglishify_response`) keep working.
"""

# Re-exports — the canonical import path is `from narrator_cosmo import X`,
# but submodule imports (`from narrator_cosmo.hinglishify import …`) also
# remain valid for explicit-source paths.
from narrator_cosmo.narrator_v2 import (
    NarratorCard,
    NarratorV2Error,
    VERDICT_TAGS,
    compose_card_narrative,
    _validate_card,
    _REQUIRE_ADVISOR_BUCKETS,
)
from narrator_cosmo.validators import (
    _validate_marriage_answer,
)
from narrator_cosmo.hinglishify import (
    _ZODIAC_EN_TO_HI,
    _ZODIAC_RX,
    _hinglishify_zodiac,
    hinglishify_response,
)

__all__ = [
    # narrator_v2
    "NarratorCard",
    "NarratorV2Error",
    "VERDICT_TAGS",
    "compose_card_narrative",
    "_validate_card",
    "_REQUIRE_ADVISOR_BUCKETS",
    # validators
    "_validate_marriage_answer",
    # hinglishify
    "_ZODIAC_EN_TO_HI",
    "_ZODIAC_RX",
    "_hinglishify_zodiac",
    "hinglishify_response",
]
