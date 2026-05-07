"""Remedy Engine v1.0 — hybrid 3-tier (Practical / Ayurvedic / Vedic).

Public API:
    from remedy import get_remedies, render_for_locked_facts
"""
from .remedy_engine_v1 import get_remedies, render_for_locked_facts

__all__ = ["get_remedies", "render_for_locked_facts"]
