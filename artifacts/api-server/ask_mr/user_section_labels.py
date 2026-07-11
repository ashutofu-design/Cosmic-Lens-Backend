"""Shared natural Hinglish section connectors for MR template answers.

Keeps validator keywords (mukhya sanket / dhyan dene layak) but reads less robotic.
"""
from __future__ import annotations

# Soft connectors — still contain tokens validators look for.
NATURAL_USER_SECTION: dict[str, str] = {
    "why_verdict": "Asli wajah seedhi hai —",
    "positive": "Jo mukhya sanket isko support karte hain —",
    "challenges": "Dhyan dene layak challenges yeh hain —",
    "meaning": "Practical matlab simple hai —",
    "focus": "Aapke liye zaroori focus yeh hai —",
    "outlook": "Aage ka outlook —",
    "transparency": "Transparency side pe —",
    "conditions": "Agar wapas aaye to yeh condition important hai —",
    "rem_outlook": "Remedy outlook —",
    "rver_outlook": "Verification outlook —",
    "rdec_outlook": "Decision outlook —",
    "rfut_outlook": "Future outlook —",
}
