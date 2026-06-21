"""gpt-4.1-mini pricing table (admin cost display)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vedic.compat.openai_pdf_telemetry import (  # noqa: E402
    estimate_call_cost_usd,
    get_effective_usd_per_1m_table,
    resolve_usd_per_1m_for_model,
)


def test_gpt41_mini_pricing_not_gpt4_fallback():
    table, _ = get_effective_usd_per_1m_table()
    inp, out, key = resolve_usd_per_1m_for_model("gpt-4.1-mini-2025-04-14", table)
    assert key == "gpt-4.1-mini", key
    assert inp == 0.40
    assert out == 1.60
    cost = estimate_call_cost_usd("gpt-4.1-mini-2025-04-14", 1077, 33, table)
    assert cost < 0.001, cost
