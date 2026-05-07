"""Remedy Engine v1.1 — hybrid 3-tier (Practical / Ayurvedic / Vedic)
+ Practical Booster Pack v1.2 (May 7 2026) for verified India resources.

Public API:
    from remedy import get_remedies, render_for_locked_facts
    from remedy import get_practical_resources, render_practical_resources
"""
from .remedy_engine_v1 import get_remedies, render_for_locked_facts
from .practical_resources import (
    get_practical_resources,
    render_practical_resources,
)

__all__ = [
    "get_remedies",
    "render_for_locked_facts",
    "get_practical_resources",
    "render_practical_resources",
]
