"""Weekday productivity framing — no weekday-planet mapping."""
from __future__ import annotations

from typing import Dict, List

_WEEKDAYS: List[Dict[str, str]] = [
    {
        "day": "Monday",
        "focus": "Planning & relationships",
        "colour": "Pearl White / Silver / Cream",
        "tip": "Batch admin, 1:1 check-ins, light meetings.",
    },
    {
        "day": "Tuesday",
        "focus": "Execution & deadlines",
        "colour": "Red / Maroon / Crimson",
        "tip": "Hard tasks, fitness, competitive work early.",
    },
    {
        "day": "Wednesday",
        "focus": "Communication & learning",
        "colour": "Green / Turquoise",
        "tip": "Calls, content, short travel, sales follow-ups.",
    },
    {
        "day": "Thursday",
        "focus": "Growth & teaching",
        "colour": "Yellow / Saffron / Gold",
        "tip": "Pitches, training, financial review.",
    },
    {
        "day": "Friday",
        "focus": "Collaboration & design",
        "colour": "White / Light Pink / Sky Blue",
        "tip": "Client delight, creative polish, team harmony.",
    },
    {
        "day": "Saturday",
        "focus": "Structure & long tasks",
        "colour": "Navy / Charcoal / Deep Purple",
        "tip": "Deep work blocks, contracts, systems cleanup.",
    },
    {
        "day": "Sunday",
        "focus": "Vision & reset",
        "colour": "Gold / Orange / Bright Yellow",
        "tip": "Weekly review, strategy, personal brand planning.",
    },
]


def weekday_productivity_pack(driver: int) -> List[Dict[str, str]]:
    return list(_WEEKDAYS)
