"""ask_cosmo — question understanding + emotion-aware tone surface.

Phase 2.8.43 (02 May 2026): consolidated all "smart query understanding"
(SQU) logic into a single package. Previously these symbols lived in
two places:
  - `question_understanding.py` (1426L) at api-server root
  - `_EMOTION_TONE_HINT_HN` + `_build_emotion_tone_hint` inside
    `openai_helper.py` L1005-1062

Now the `ask_cosmo/` package owns both. Old `question_understanding.py`
is kept as a thin facade re-exporting from `ask_cosmo.understanding`
for backward-compat (any missed importer continues to work). The
helper definitions in `openai_helper.py` are replaced by an import
line from this package.

Public surface (what callers should import):
  - `understand_question(question)` — classifier entry, returns 16-field dict
  - `supertype_for(intent)` — supertype routing helper
  - `has_recovery_subask(question)` — Sprint-26 Fix-Q recovery detector
  - `is_personal_chart_question(question)` — Personal-chart override
  - `_WHY_LEADING_RX` — Fix-N why-promoter regex (private but used)
  - `_build_emotion_tone_hint(emotion, urgency)` — system-prompt tone hint
  - `_EMOTION_TONE_HINT_HN` — Hinglish emotion → tone-hint dict
"""

from __future__ import annotations

# Re-export the entire understanding.py public + private surface so
# `from ask_cosmo import understand_question` works exactly the same
# as the legacy `from question_understanding import understand_question`.
from .understanding import (  # noqa: F401
    understand_question,
    supertype_for,
    has_recovery_subask,
    is_personal_chart_question,
    _WHY_LEADING_RX,
)

# Tone-hint helpers (extracted from openai_helper.py in Phase 2.8.43).
from .tone_hints import (  # noqa: F401
    _EMOTION_TONE_HINT_HN,
    _build_emotion_tone_hint,
)


__all__ = [
    # understanding.py
    "understand_question",
    "supertype_for",
    "has_recovery_subask",
    "is_personal_chart_question",
    "_WHY_LEADING_RX",
    # tone_hints.py
    "_EMOTION_TONE_HINT_HN",
    "_build_emotion_tone_hint",
]
