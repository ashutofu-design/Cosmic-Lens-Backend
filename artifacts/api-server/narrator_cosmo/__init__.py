"""narrator_cosmo package - response-shaping surface for the LLM pipeline.

Phase 2.8.45 (02 May 2026, original): created with three modules
extracted from openai_helper.py - validators.py, narrator_v2.py,
hinglishify.py.

Phase 2.8.46 (02 May 2026): user-approved PERMANENT DELETE of
narrator_v2.py + hinglishify.py + their root facade. Only validators.py
survived. Passthrough stubs were left at openai_helper.py L2496-2517
(hinglishify) so flask_app.py imports kept working without code change.

Phase 2.8.47 + 2.8.48 (02 May 2026): created `engine_locked_to_llm/`
package and nested it under narrator_cosmo per user direction. Holds
the deterministic chart-truth source (`build_locked_facts`,
`compute_strength_facts`, KP cuspal cross-check, etc).

Phase 2.8.49 (02 May 2026): consolidated the entire narrator-shaping
surface into this package. Moved out of openai_helper.py:
  - `_build_topic_lock`                       -> prompt_builders.py
  - `_build_wealth_structured_system_prompt`  -> prompt_builders.py
  - `_build_true_intent_hint`                 -> prompt_builders.py
  - `_build_repair_prompt`                    -> prompt_builders.py
  - `_topic_lagna_sign_idx` (helper)          -> prompt_builders.py
  - `_topic_house_lord` (helper)              -> prompt_builders.py
  - `_topic_current_dasha` (helper)           -> prompt_builders.py
  - `_TOPIC_SIGN_LORDS` (constant)            -> prompt_builders.py
  - `_TOPIC_SIGN_ALIASES` (constant)          -> prompt_builders.py
  - `_hinglishify_zodiac` (dead stub)         -> hinglishify_stubs.py
  - `hinglishify_response` (dead stub)        -> hinglishify_stubs.py

Plus relocated from `ask_cosmo/`:
  - `_EMOTION_TONE_HINT_HN`                   -> tone_hints.py
  - `_build_emotion_tone_hint`                -> tone_hints.py

openai_helper.py keeps thin re-import shims so external callers like
`from openai_helper import _build_topic_lock` keep working unchanged.

Public surface (canonical import paths):
  - validators:
      `from narrator_cosmo import _validate_marriage_answer`
  - prompt builders:
      `from narrator_cosmo import _build_topic_lock,
                                  _build_wealth_structured_system_prompt,
                                  _build_true_intent_hint,
                                  _build_repair_prompt`
  - tone hints:
      `from narrator_cosmo import _build_emotion_tone_hint,
                                  _EMOTION_TONE_HINT_HN`
  - hinglishify stubs (dead passthroughs - kept for back-compat):
      `from narrator_cosmo import _hinglishify_zodiac,
                                  hinglishify_response`
  - engine-locked-to-LLM truth source (nested subpackage):
      `from narrator_cosmo.engine_locked_to_llm import build_locked_facts,
                                                       compute_strength_facts,
                                                       compute_kp_summary,
                                                       ...`
"""

from __future__ import annotations

# Phase 2.8.45 - the marriage-answer validator (KP-anti-leak Sprint-25).
from narrator_cosmo.validators import _validate_marriage_answer  # noqa: F401

# Phase 2.8.49 - prompt builders moved from openai_helper.py.
from narrator_cosmo.prompt_builders import (  # noqa: F401
    _build_topic_lock,
    _build_wealth_structured_system_prompt,
    _build_true_intent_hint,
    _build_repair_prompt,
    _topic_lagna_sign_idx,
    _topic_house_lord,
    _topic_current_dasha,
    _TOPIC_SIGN_LORDS,
    _TOPIC_SIGN_ALIASES,
)

# Phase 2.8.49 - hinglishify dead-stub passthroughs moved from openai_helper.
from narrator_cosmo.hinglishify_stubs import (  # noqa: F401
    _ZODIAC_EN_TO_HI,
    _ZODIAC_RX,
    _hinglishify_zodiac,
    hinglishify_response,
)

# Phase 2.8.49 - emotion tone hints relocated from ask_cosmo.
from narrator_cosmo.tone_hints import (  # noqa: F401
    _EMOTION_TONE_HINT_HN,
    _build_emotion_tone_hint,
)


__all__ = [
    # validators
    "_validate_marriage_answer",
    # prompt builders
    "_build_topic_lock",
    "_build_wealth_structured_system_prompt",
    "_build_true_intent_hint",
    "_build_repair_prompt",
    # topic helpers + constants
    "_topic_lagna_sign_idx",
    "_topic_house_lord",
    "_topic_current_dasha",
    "_TOPIC_SIGN_LORDS",
    "_TOPIC_SIGN_ALIASES",
    # hinglishify dead stubs
    "_ZODIAC_EN_TO_HI",
    "_ZODIAC_RX",
    "_hinglishify_zodiac",
    "hinglishify_response",
    # tone hints
    "_EMOTION_TONE_HINT_HN",
    "_build_emotion_tone_hint",
]
