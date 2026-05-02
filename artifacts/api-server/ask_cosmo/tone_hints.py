"""ask_cosmo/tone_hints.py - back-compat re-export shim.

Phase 2.8.49 (02 May 2026) - the real implementation was relocated to
`narrator_cosmo/tone_hints.py` because tone-hints are a RESPONSE-SHAPING
helper (narrator side), not a question-classification helper (ask side).

This file is kept as a thin re-export shim so any code still doing
`from ask_cosmo import _build_emotion_tone_hint` or
`from ask_cosmo.tone_hints import _EMOTION_TONE_HINT_HN` continues to
work. New code should import from `narrator_cosmo` instead.

History (preserved for grep traceability):
  - Phase 2.8.42: `_EMOTION_TONE_HINT_HN` + `_build_emotion_tone_hint`
    originally lived in openai_helper.py L1005-1062.
  - Phase 2.8.43: extracted into `ask_cosmo/tone_hints.py` alongside the
    SQU classifier in `understanding.py`.
  - Phase 2.8.44a: server-side anchor rotation added (random.choice).
  - Phase 2.8.49: relocated to `narrator_cosmo/tone_hints.py`; this file
    is now a back-compat shim.
"""

from __future__ import annotations

from narrator_cosmo.tone_hints import (  # noqa: F401
    _EMOTION_TONE_HINT_HN,
    _build_emotion_tone_hint,
)

__all__ = ["_EMOTION_TONE_HINT_HN", "_build_emotion_tone_hint"]
