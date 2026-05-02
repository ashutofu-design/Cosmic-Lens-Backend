"""question_understanding.py — BACKWARD-COMPAT FACADE (Phase 2.8.43).

The actual implementation now lives in `ask_cosmo/understanding.py`.
This file is preserved as a thin facade so any external importer
(or missed internal site) continues to work without code change.

New code should import from `ask_cosmo` directly:

    from ask_cosmo import understand_question, supertype_for, ...

Phase 2.8.43 (02 May 2026): Moved 1426L of classifier logic into the
new `ask_cosmo/` package as part of consolidating all smart-query-
understanding (SQU) surface area in one folder. Pure relocation —
zero logic change. The original 5 import sites in openai_helper.py
were updated to point at `ask_cosmo` directly; this facade exists
solely as a safety net.
"""

from __future__ import annotations

# Re-export the full PUBLIC surface from the new home. Note:
# `ask_cosmo.understanding` does NOT define `__all__`, so `import *`
# only picks up names that don't start with an underscore (Python's
# default behaviour). Underscore-prefixed symbols that legacy callers
# may import (e.g. `_WHY_LEADING_RX`) are re-exported EXPLICITLY in
# the second import block below — that's what actually preserves
# backward-compat for those symbols.
from ask_cosmo.understanding import *  # noqa: F401,F403

# Explicit re-exports of the symbols actually used by openai_helper.py
# (and any other in-tree consumer) for clarity + tooling support.
# This block is the SOLE guarantee for underscore-prefixed symbols
# like `_WHY_LEADING_RX`; do not remove without auditing legacy callers.
from ask_cosmo.understanding import (  # noqa: F401
    understand_question,
    supertype_for,
    has_recovery_subask,
    is_personal_chart_question,
    _WHY_LEADING_RX,
)
