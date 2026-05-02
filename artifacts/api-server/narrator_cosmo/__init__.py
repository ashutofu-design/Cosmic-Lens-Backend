"""
narrator_cosmo — post-LLM output guard package
===============================================

Phase 2.8.45 — Initial extraction of narrator surface from
openai_helper.py (mirror of Phase 2.8.43's ask_cosmo move).

Phase 2.8.46 — User-approved PERMANENT REMOVAL of narrator_v2.py +
hinglishify.py. Direction (Hinglish): "validator chodke sab remove karo
permanent agar kuch baad me chahiye me add karunga". Only the validator
surface remains in this package.

Current contents:
  - validators.py    — post-LLM output guards (currently just the
                       Phase 2.8.37 marriage-answer passthrough stub;
                       intentionally kept as a stable extraction point
                       for future validator additions).

Deleted in Phase 2.8.46 (gone from filesystem, can be re-added later
if needed):
  - narrator_v2.py  — wealth-card structured payload reshaper. Lazy-
                      import in openai_helper.py L18703 was replaced
                      with a fall-through stub (now skips straight to
                      raw engine text fallback).
  - hinglishify.py  — zodiac EN→Hinglish scrubber. The 4 symbols it
                      exposed (`_ZODIAC_EN_TO_HI`, `_ZODIAC_RX`,
                      `_hinglishify_zodiac`, `hinglishify_response`)
                      were replaced with passthrough stubs in
                      openai_helper.py so flask_app.py's import
                      (`from openai_helper import hinglishify_response`)
                      keeps working as a no-op.

Functional consequence (user-accepted regression):
  - Wealth structured-payload diagnostic cards no longer get the v2
    conversational reshape. Raw engine text reaches the user.
  - English zodiac names in Hinglish-locale responses (Aries / Cancer /
    Sagittarius / etc.) will reach the user unscrubbed.

Companion package: ask_cosmo/  (question understanding — KYA poocha)
"""

from narrator_cosmo.validators import _validate_marriage_answer

__all__ = [
    "_validate_marriage_answer",
]
