"""
engine_locked_to_llm — deterministic engine→LLM "LOCKED FACTS" package
=======================================================================

Phase 2.8.47 — User direction (Hinglish): "Locked facts py and kp locked
facts ko milao ek folder karo name rakho engine locked to LLM .py".
Consolidated the two engine→LLM bridge modules into a single namespace.

Purpose:
  These modules build the deterministic LOCKED FACTS block that is
  prepended to the LLM system prompt so the AI cannot "invent" chart
  data — every astrological claim it makes must trace back to a
  pre-computed verbatim string in this block. The LLM is the
  Translator; these modules are the Truth source.

Contents:
  - locked_facts.py       — main builder. Public API:
      * build_locked_facts(kundli, birth)       — full LOCKED FACTS string
      * compute_strength_facts(kundli, ...)     — planet strength facts
      * get_last_engine_status()                — last-run engine phases
      * _is_primary_phase(phase_name)           — phase-A through phase-G
        (also internally cross-imports kp_locked_facts at L1306)
  - kp_locked_facts.py    — KP cuspal sub-lord cross-check addon.
      Public API:
      * compute_kp_summary(birth, kundli)       — KP house signification
      * format_kp_summary(kp_summary)           — render to prompt string

Re-exports below let callers use
`from narrator_cosmo.engine_locked_to_llm import …` as the canonical
import path. The two sub-modules can also be imported directly via
`narrator_cosmo.engine_locked_to_llm.locked_facts` /
`.kp_locked_facts` for situations where lazy-loading the heavy
`locked_facts` body matters.

Phase 2.8.48 — package nested under narrator_cosmo/ on user direction
"Engine locked to LLM isko narrator cosmo ke andar rakho". The previous
top-level path `engine_locked_to_llm/` is gone — all 5 importers
(4 in openai_helper.py + 1 internal cross-import) now use the
`narrator_cosmo.engine_locked_to_llm.*` prefix.
"""

from narrator_cosmo.engine_locked_to_llm.locked_facts import (
    build_locked_facts,
    compute_strength_facts,
    get_last_engine_status,
    _is_primary_phase,
)
from narrator_cosmo.engine_locked_to_llm.kp_locked_facts import (
    compute_kp_summary,
    format_kp_summary,
)

__all__ = [
    "build_locked_facts",
    "compute_strength_facts",
    "get_last_engine_status",
    "_is_primary_phase",
    "compute_kp_summary",
    "format_kp_summary",
]
