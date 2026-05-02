"""reply_cosmo/hinglishify_stubs.py

Phase 2.8.46 PERMANENTLY DELETED `reply_cosmo/hinglishify.py` plus
the EN→Hinglish zodiac-name scrubber. The two surface functions called
by `flask_app.py` (post-LLM scrub) and `openai_helper.py` (every
narrator path) became no-op passthroughs.

Phase 2.8.49 — those passthrough stubs were *moved* out of
`openai_helper.py` into this dedicated module so the entire
narrator-shaping surface lives under `reply_cosmo/`. The functions
remain dead passthroughs (return input unchanged); `openai_helper.py`
keeps re-import shims so external callers like
`from openai_helper import hinglishify_response` keep working.

If Hinglish zodiac scrubbing is ever resurrected, replace the stub
bodies here with the real implementation — call sites in
`openai_helper.py` and `flask_app.py` need no further change.
"""

# Empty replacement table — no zodiac substitutions performed.
_ZODIAC_EN_TO_HI: dict[str, str] = {}

# Compiled regex placeholder kept as None so any consumer guarding
# `if _ZODIAC_RX:` short-circuits cleanly.
_ZODIAC_RX = None  # type: ignore[assignment]


def _hinglishify_zodiac(text, lang):  # noqa: D401
    """Phase 2.8.46 stub — passthrough (returns text unchanged)."""
    return text


def hinglishify_response(result, lang):  # noqa: D401
    """Phase 2.8.46 stub — passthrough (returns result unchanged)."""
    return result


__all__ = [
    "_ZODIAC_EN_TO_HI",
    "_ZODIAC_RX",
    "_hinglishify_zodiac",
    "hinglishify_response",
]
