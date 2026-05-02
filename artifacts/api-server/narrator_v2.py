"""
narrator_v2.py — backward-compat facade
========================================

Phase 2.8.45 — the actual narrator_v2 module moved to
narrator_cosmo/narrator_v2.py. This file re-exports its public surface
so existing imports (`from narrator_v2 import _validate_card`,
`from narrator_v2 import compose_card_narrative`, etc.) continue to work
without modification.

Existing import sites preserved by this facade:
  - smoke_validator_v4.py:11    `from narrator_v2 import _validate_card,
                                 _REQUIRE_ADVISOR_BUCKETS`
  - smoke_narrator_v2.py:15     `from narrator_v2 import (...)`
  - openai_helper.py:18767      `from narrator_v2 import (...)` (lazy)

The canonical import path going forward is:
  `from narrator_cosmo.narrator_v2 import …`  (or `from narrator_cosmo import …`)

Once all call sites are updated to the canonical path, this facade can be
deleted. Until then, it stays as a zero-cost compatibility shim.
"""
from narrator_cosmo.narrator_v2 import *  # noqa: F401,F403

# Explicit re-exports for symbols starting with `_` (which `import *`
# does not propagate per Python convention).
from narrator_cosmo.narrator_v2 import (  # noqa: F401
    _REQUIRE_ADVISOR_BUCKETS,
    _REQUIRE_ADVISOR_DOMAINS,
    _BANNED_JARGON_RX,
    _OPENER_RX,
    _HEDGE_RX,
    _FORWARD_RX,
    _SUGGESTION_RX,
    _AI_BRAND_LEAK_RX,
    _BANNED_BRAND_RX,
    _NARRATOR_SCHEMA,
    _VOICE_RULES,
    _build_user_prompt,
    _word_count,
    _last_sentence,
    _validate_card,
)
