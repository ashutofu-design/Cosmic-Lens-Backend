"""
event_timing.finance package
============================
Finance Timing Engine v1.0 — mirror of Health Timing Engine v1 / Marriage v2.

Public API:
    from event_timing.finance import compute_finance_window
    from event_timing.finance.finance_engine_v1 import (
        compute_finance_window, get_last_finance_result,
        clear_last_finance_result,
    )
"""
from .finance_engine_v1 import (
    compute_finance_window,
    get_last_finance_result,
    clear_last_finance_result,
)

__all__ = [
    "compute_finance_window",
    "get_last_finance_result",
    "clear_last_finance_result",
]
