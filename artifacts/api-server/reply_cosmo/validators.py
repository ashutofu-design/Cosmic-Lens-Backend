"""
reply_cosmo.validators — post-LLM output guards
===================================================

Phase 2.8.45 — extracted from openai_helper.py L159.

Currently houses ONE function:

  _validate_marriage_answer(answer_text, engine_block) -> str
      Phase 2.8.37 stub. Originally a deterministic post-injector
      validator (Phase 2.8.29) that did regex-only checks on LLM
      marriage-answer output (no extra LLM calls). Stubbed in
      Phase 2.8.37 when the marriage engine moved to a different
      contract. Currently a pass-through. Three call sites in
      openai_helper.py (L13270, L16560, L16623) keep calling it as
      a no-op so the contract is preserved when/if the validator
      is revived.

Future:
  - _validate_wealth_payload         (still in openai_helper L1901,
                                      heavy regex coupling, deferred)
  - _validate_supertype_contract     (still in openai_helper L9933,
                                      heavy regex coupling, deferred)

When those move, they belong in this file too.

Architecture invariant:
  Engine = Truth (locked) | LLM = Translator | Validator = Guard
"""
from __future__ import annotations


def _validate_marriage_answer(answer_text, engine_block):  # Phase 2.8.37 stub
    """Post-injector validator for marriage-answer LLM output.

    Phase 2.8.29 — original implementation did regex-only deterministic
    checks (no extra LLM calls).
    Phase 2.8.37 — stubbed to pass-through when marriage engine moved
    to a different contract.
    Phase 2.8.45 — moved into reply_cosmo/validators.py verbatim.
    Behavior unchanged — returns answer_text untouched.
    """
    return answer_text
