"""
Pure numerology lexicon — no astrology, planets, mantras, gems, or Vedic concepts.

Used by PDF renderers and narrative helpers when building the Life Mastery report
(default: NUMEROLOGY_INCLUDE_VEDIC_TIERS is off).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# ── Number archetypes (replace ruling-planet language) ───────────────────
ARCHETYPE_BY_DRIVER: Dict[int, str] = {
    1: "Leader / Pioneer",
    2: "Diplomat / Empath",
    3: "Creator / Communicator",
    4: "Builder / Strategist",
    5: "Explorer / Networker",
    6: "Harmonizer / Nurturer",
    7: "Analyst / Seeker",
    8: "Executive / Authority",
    9: "Humanitarian / Catalyst",
}

ARCHETYPE_SHORT: Dict[int, str] = {
    1: "Leader", 2: "Diplomat", 3: "Creator", 4: "Builder", 5: "Explorer",
    6: "Harmonizer", 7: "Analyst", 8: "Executive", 9: "Humanitarian",
}

# Weekday → root number (numerology day vibration, not graha)
WEEKDAY_ROOT_NUMBER: Dict[str, int] = {
    "Monday": 2, "Tuesday": 9, "Wednesday": 5, "Thursday": 3,
    "Friday": 6, "Saturday": 8, "Sunday": 1,
}

DAY_DRESS_BY_NUMBER: List[Dict[str, str]] = [
    {
        "day": "Monday",
        "root_number": "2",
        "archetype": "Diplomat",
        "colour": "Pearl White / Silver / Cream",
        "purpose": "Reflection, listening, partnership talks, emotional check-ins.",
    },
    {
        "day": "Tuesday",
        "root_number": "9",
        "archetype": "Humanitarian",
        "colour": "Red / Maroon / Crimson",
        "purpose": "Bold action, deadlines, fitness, competitive focus.",
    },
    {
        "day": "Wednesday",
        "root_number": "5",
        "archetype": "Explorer",
        "colour": "Green / Light Green / Turquoise",
        "purpose": "Communication, sales, learning, short travel.",
    },
    {
        "day": "Thursday",
        "root_number": "3",
        "archetype": "Creator",
        "colour": "Yellow / Saffron / Golden",
        "purpose": "Teaching, pitching ideas, creative work, financial planning.",
    },
    {
        "day": "Friday",
        "root_number": "6",
        "archetype": "Harmonizer",
        "colour": "White / Light Pink / Sky Blue",
        "purpose": "Relationships, design, client delight, team harmony.",
    },
    {
        "day": "Saturday",
        "root_number": "8",
        "archetype": "Executive",
        "colour": "Deep Blue / Charcoal / Dark Purple",
        "purpose": "Structure, admin, long-term contracts, discipline blocks.",
    },
    {
        "day": "Sunday",
        "root_number": "1",
        "archetype": "Leader",
        "colour": "Golden / Orange / Bright Yellow",
        "purpose": "Vision setting, leadership meetings, personal brand work.",
    },
]

AFFIRMATIONS_BY_DRIVER: Dict[int, Dict[str, str]] = {
    1: {
        "affirmation": "I lead with clarity; my decisions create momentum for everyone around me.",
        "practice": "5-minute morning intention + one bold priority before noon.",
        "lifestyle": "Structured morning routine; gold or warm accent in workspace.",
        "color_focus": "Wear gold or orange on power days (root number 1).",
        "habit": "Weekly review: one initiative you own end-to-end.",
    },
    2: {
        "affirmation": "I listen deeply and respond with calm; my empathy is a professional strength.",
        "practice": "2-minute breathing before important conversations.",
        "lifestyle": "Soft lighting, uncluttered desk, hydration reminders.",
        "color_focus": "Wear cream or silver on collaboration days (root number 2).",
        "habit": "Boundary script: 'I need 20 minutes to recharge' — use it weekly.",
    },
    3: {
        "affirmation": "I express ideas clearly; my voice opens doors.",
        "practice": "Daily 10-line journal or voice note on one insight.",
        "lifestyle": "Yellow accent, visible goals board, creative break every 90 min.",
        "color_focus": "Wear yellow or saffron on creative days (root number 3).",
        "habit": "Ship one small creative output per week (post, deck, lesson).",
    },
    4: {
        "affirmation": "I build systems that last; steady work compounds.",
        "practice": "25-minute focus blocks; checklist for recurring tasks.",
        "lifestyle": "Minimal desk, backup tools, digital hygiene Friday.",
        "color_focus": "Wear grey or electric blue on deep-work days (root number 4).",
        "habit": "One process documented per month (SOP, template, automation).",
    },
    5: {
        "affirmation": "I adapt fast and connect people; variety fuels my best work.",
        "practice": "Walk-and-talk for brainstorming; batch admin separately.",
        "lifestyle": "Green plants, mobile-friendly workflow, travel buffer time.",
        "color_focus": "Wear green on networking days (root number 5).",
        "habit": "Two new meaningful contacts per week — quality over quantity.",
    },
    6: {
        "affirmation": "I create harmony; beauty and care show up in my results.",
        "practice": "Gratitude note to one person daily.",
        "lifestyle": "Pleasant scents, organized home corner, balanced screen time.",
        "color_focus": "Wear pink or soft blue on relationship days (root number 6).",
        "habit": "One act of service that is not performative — weekly.",
    },
    7: {
        "affirmation": "I think before I act; depth beats noise.",
        "practice": "20-minute silent focus or reading — no phone.",
        "lifestyle": "Quiet zone, noise-cancelling when needed, sleep protected.",
        "color_focus": "Wear sea green or grey on analysis days (root number 7).",
        "habit": "One research block before major decisions.",
    },
    8: {
        "affirmation": "I earn through discipline; authority grows with integrity.",
        "practice": "End-of-day 3-line log: done / blocked / tomorrow.",
        "lifestyle": "Ergonomic setup, financial snapshot every Sunday.",
        "color_focus": "Wear navy or charcoal on execution days (root number 8).",
        "habit": "Negotiate once per quarter — salary, scope, or terms.",
    },
    9: {
        "affirmation": "I channel intensity into impact; completion matters.",
        "practice": "24-hour pause rule before reactive messages.",
        "lifestyle": "Red accent for energy, cooldown walk after heated meetings.",
        "color_focus": "Wear red or maroon on action days (root number 9).",
        "habit": "Close one open loop weekly (project, apology, donation, file).",
    },
}

# Practical habit stack (no spiritual/occult remedies)
PRACTICAL_BY_DRIVER: Dict[int, Dict[str, str]] = {
    1: {
        "routines": "Fixed wake time; 10-minute morning plan before inbox.",
        "journaling": "3 lines nightly: win / lesson / tomorrow's #1 priority.",
        "communication": "Open meetings with agenda; confirm decisions in writing.",
        "sleep_discipline": "Screens off 45 min before bed; 7+ hours non-negotiable.",
        "budgeting": "Sunday money snapshot; auto-transfer to savings first.",
        "productivity": "One bold task before 11 AM; batch admin after lunch.",
        "emotional_awareness": "Pause 10 seconds before replying when you feel challenged.",
    },
    2: {
        "routines": "Gentle morning stretch + hydration; same wind-down cue nightly.",
        "journaling": "Mood + energy log (1–10) to spot overload patterns.",
        "communication": "Reflect back what you heard before giving advice.",
        "sleep_discipline": "No heavy debates after 9 PM; protect quiet evenings.",
        "budgeting": "Shared-expense tracker; review subscriptions monthly.",
        "productivity": "Time-box listening calls; cap back-to-back meetings.",
        "emotional_awareness": "Name the feeling before fixing the problem.",
    },
    3: {
        "routines": "Creative block in calendar; short walk between deep-work sprints.",
        "journaling": "Daily idea capture (10 lines or 2-min voice note).",
        "communication": "One clear ask per message; teach/summarize in bullets.",
        "sleep_discipline": "Stop stimulating content 60 min before sleep.",
        "budgeting": "Separate fun vs business accounts; weekly cash-flow glance.",
        "productivity": "Ship one small public output per week (post, deck, lesson).",
        "emotional_awareness": "Notice when you talk to avoid silence — breathe first.",
    },
    4: {
        "routines": "Same start ritual: checklist review + top task pinned.",
        "journaling": "End-of-day log: done / blocked / tomorrow's first step.",
        "communication": "Document agreements; avoid vague 'ASAP' without dates.",
        "sleep_discipline": "Consistent bedtime; dim lights during evening admin.",
        "budgeting": "Envelope or category caps; emergency fund line item.",
        "productivity": "25-minute focus blocks; one SOP improved per month.",
        "emotional_awareness": "Spot rigidity — ask 'what would good enough look like?'",
    },
    5: {
        "routines": "Morning movement; afternoon admin batch; evening unplug window.",
        "journaling": "Weekly network map: who helped / who needs a follow-up.",
        "communication": "Confirm next step + owner on every call; recap in email.",
        "sleep_discipline": "Travel days: still anchor one wind-down habit (tea, stretch).",
        "budgeting": "Track variable spend weekly; cap impulse purchases with 24h rule.",
        "productivity": "Two quality outreach touches per week; batch messaging.",
        "emotional_awareness": "When restless, ask if you need novelty or real progress.",
    },
    6: {
        "routines": "Tidy shared spaces Sunday; mid-week relationship check-in.",
        "journaling": "Gratitude note to one person daily (specific, brief).",
        "communication": "Use 'I feel' statements; schedule hard talks, don't ambush.",
        "sleep_discipline": "Bedroom screen-free; gentle alarm, not snooze loops.",
        "budgeting": "Family budget meeting monthly; beauty/comfort spend planned.",
        "productivity": "Protect maker time; say no to one low-value obligation weekly.",
        "emotional_awareness": "Notice over-giving — schedule solo recharge without guilt.",
    },
    7: {
        "routines": "Morning quiet block (reading/planning) before messages.",
        "journaling": "Decision journal: options, assumptions, chosen path.",
        "communication": "Ask one clarifying question before debating.",
        "sleep_discipline": "Hard stop on work thoughts — notebook dump, then lights out.",
        "budgeting": "Long-term goals fund; automate boring bills.",
        "productivity": "Research block before major choices; limit open tabs.",
        "emotional_awareness": "Name isolation vs intentional solitude — reach out if lonely.",
    },
    8: {
        "routines": "Weekly planning Sunday; daily shutdown ritual (inbox zero-lite).",
        "journaling": "3-line executive log: outcomes / risks / asks.",
        "communication": "Direct feedback with data; negotiate in writing.",
        "sleep_discipline": "No laptop in bed; Saturday lighter workload if possible.",
        "budgeting": "Net-worth snapshot monthly; debt paydown order documented.",
        "productivity": "Eat the frog first; delegate one recurring task per quarter.",
        "emotional_awareness": "Watch control urges — delegate one decision this week.",
    },
    9: {
        "routines": "Morning movement to burn stress; evening cooldown walk.",
        "journaling": "Anger trigger log: situation → story → better response.",
        "communication": "24-hour pause on heated replies; voice tone check on calls.",
        "sleep_discipline": "Cool-down after conflict; no big arguments when tired.",
        "budgeting": "Charity/giving as a planned line, not impulse guilt spend.",
        "productivity": "Finish one lingering task weekly; don't start three new fires.",
        "emotional_awareness": "Channel intensity into sport or creative output, not blame.",
    },
}

PRACTICAL_CARD_LABELS: List[tuple] = [
    ("routines", "Daily routine", "दैनिक दिनचर्या", "Daily routine"),
    ("journaling", "Journaling", "जर्नलिंग", "Journaling"),
    ("communication", "Communication habits", "संवाद की आदतें", "Communication habits"),
    ("sleep_discipline", "Sleep discipline", "नींद अनुशासन", "Sleep discipline"),
    ("budgeting", "Budgeting", "बजट अनुशासन", "Budgeting"),
    ("productivity", "Productivity habits", "उत्पादकता की आदतें", "Productivity habits"),
    ("emotional_awareness", "Emotional awareness", "भावनात्मक जागरूकता", "Emotional awareness"),
]

ACCENT_TONE_BY_DRIVER: Dict[int, str] = {
    1: "Warm gold and coral accents in accessories or UI.",
    2: "Soft pearl and silver tones — calm, reflective palette.",
    3: "Yellow and amber highlights — optimistic, creative.",
    4: "Steel grey and electric blue — modern, structured.",
    5: "Fresh green and white — agile, communicative.",
    6: "Blush pink and sky blue — elegant, relational.",
    7: "Sea green and smoke grey — analytical, minimal.",
    8: "Navy and charcoal — executive, authoritative.",
    9: "Crimson and maroon — bold, high-energy.",
}

from numerology.core.sanitize import sanitize_mapping, sanitize_text  # noqa: F401


def affirmations_pack(driver: int) -> Dict[str, str]:
    base = dict(AFFIRMATIONS_BY_DRIVER.get(driver, AFFIRMATIONS_BY_DRIVER[1]))
    base.update(PRACTICAL_BY_DRIVER.get(driver, PRACTICAL_BY_DRIVER[1]))
    arch = ARCHETYPE_BY_DRIVER.get(driver, "—")
    return {"archetype": arch, **base}


def mantras_pack(driver: int) -> Dict[str, str]:
    """Legacy name — returns practical habits only (no mantras/gems)."""
    return affirmations_pack(driver)


def archetype_for(driver: int) -> str:
    return ARCHETYPE_BY_DRIVER.get(driver, "—")


def compat_label(code: str) -> str:
    return {
        "T": "MIRROR MATCH",
        "F": "HIGH SYNC",
        "N": "BALANCED",
        "E": "HIGH FRICTION",
    }.get(code, "BALANCED")


def why_impact_action_pure(reduced: int, kind: str, lang: str = "hinglish") -> Dict[str, str]:
    arch = ARCHETYPE_SHORT.get(reduced, f"Number {reduced}")
    templates = {
        "mobile": (
            f"Mobile total reduces to {reduced} — {arch} communication style.",
            "Calls and messages reinforce this number's decision and social habits.",
            f"Schedule important calls on days matching root numbers friendly to {reduced}.",
        ),
        "vehicle": (
            f"Vehicle number {reduced} — {arch} travel rhythm.",
            "Trips reflect this number's pace: solo vs family, fast vs steady.",
            f"Service the vehicle on numerology-friendly dates for number {reduced}.",
        ),
        "house": (
            f"House/unit number {reduced} — {arch} home environment.",
            "Domestic energy follows this number's themes: structure, warmth, or change.",
            f"Use entrance accents from your Driver palette; keep clutter low on stress dates.",
        ),
        "name": (
            f"Name vibration {reduced} — {arch} public identity.",
            "How people perceive your reliability, creativity, or authority.",
            "Align signature and email display with your corrected name total when possible.",
        ),
    }
    why, impact, action = templates.get(kind, templates["mobile"])
    return {"why": why, "impact": impact, "action": action, "archetype": arch}
