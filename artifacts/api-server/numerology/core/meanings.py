"""
numerology/core/meanings.py — Pure numerology personality data (numbers 1–9).

No planets, grahas, gems, mantras, directions, or ritual remedies.
Used by Soul Blueprint (Part 1) PDF and APIs.
"""
from __future__ import annotations

from typing import Any, Dict

NUMBER_PERSONALITY: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "Number 1 — Leadership Archetype",
        "headline": "Independent · Decisive · Pioneer",
        "narrative": (
            "Number 1 profiles lead from the front. You prefer to set direction rather than "
            "follow it, and you grow when you own outcomes. Confidence is your asset; "
            "impatience and ego clashes are the usual growth edges. You do best where "
            "initiative, visibility, and clear authority are rewarded."
        ),
        "strengths": [
            "Strong willpower and decision-making",
            "Natural leadership and accountability",
            "Original thinking — new ideas and first moves",
            "Honest and direct communication",
            "Ambitious goal-setting",
        ],
        "weaknesses": [
            "Ego and stubbornness under stress",
            "Difficulty accepting slower partners",
            "Conflict with rigid hierarchies",
            "Impatience when progress is incremental",
        ],
        "famous": [
            "Mukesh Ambani", "Narendra Modi", "A.R. Rahman",
            "Steve Jobs", "Walt Disney",
        ],
        "career": (
            "Founder, CEO, project lead, sales leadership, public-facing roles, "
            "operations commander — anywhere you can set pace and standards."
        ),
        "love": (
            "Loyal and protective; needs respect and space to lead. "
            "Best rhythm with 1, 2, 4, 7. Friction patterns with 8 when control clashes."
        ),
        "wellness": (
            "High-drive schedule — protect sleep and recovery. Morning movement + "
            "short planning block reduce stress spikes. Watch blood pressure and screen "
            "strain when overworking; build 10-minute decompression after intense meetings."
        ),
        "best_match": [1, 2, 4, 7],
        "avoid_match": [8],
    },
    2: {
        "title": "Number 2 — Emotional Intelligence Pattern",
        "headline": "Sensitive · Cooperative · Intuitive",
        "narrative": (
            "Number 2 profiles read people quickly and value harmony. You excel in "
            "partnerships, support roles, and nuanced communication. Mood sensitivity is "
            "real — structure and trusted allies help you stay steady. Avoid isolating "
            "when stressed; small, consistent social anchors work better than big swings."
        ),
        "strengths": [
            "High emotional intelligence",
            "Diplomatic and peace-oriented",
            "Strong intuition in people matters",
            "Loyal in close relationships",
            "Patient with detail and follow-through",
        ],
        "weaknesses": [
            "Mood swings when overloaded",
            "Slow decisions when seeking consensus",
            "People-pleasing under pressure",
            "Confidence dips after criticism",
        ],
        "famous": [
            "Mahatma Gandhi", "Rabindranath Tagore", "Madonna",
            "Barack Obama", "Shah Rukh Khan",
        ],
        "career": (
            "Counselling, HR, teaching, hospitality, client success, design partnerships, "
            "research assistant — roles needing empathy and coordination."
        ),
        "love": (
            "Romantic and devoted; needs emotional safety. "
            "Best rhythm with 1, 2, 4, 7. Friction with 5 or 9 when pace feels chaotic."
        ),
        "wellness": (
            "Nervous-system care: regular meals, hydration, gentle walks. "
            "Journaling feelings prevents rumination. Limit late-night scrolling; "
            "pairing with a steady sleep window improves mood stability."
        ),
        "best_match": [1, 2, 4, 7],
        "avoid_match": [5, 9],
    },
    3: {
        "title": "Number 3 — Creative Expression Pattern",
        "headline": "Expressive · Social · Optimistic",
        "narrative": (
            "Number 3 profiles think in stories, images, and connections. You lift rooms "
            "with humour and ideas, but scatter focus when too many projects run at once. "
            "Channel creativity into one flagship outlet plus a simple weekly publish rhythm."
        ),
        "strengths": [
            "Communication and presentation",
            "Creativity and ideation",
            "Networking and social ease",
            "Optimism that motivates teams",
            "Teaching and explaining complex ideas simply",
        ],
        "weaknesses": [
            "Scattered focus across too many ideas",
            "Overspending on lifestyle or tools",
            "Avoiding boring but necessary admin",
            "Sensitivity to public criticism",
        ],
        "famous": [
            "Amitabh Bachchan", "Salman Khan", "Tom Cruise",
            "Alfred Hitchcock", "Raj Kapoor",
        ],
        "career": (
            "Media, marketing, design, training, content, events, consulting — "
            "any field rewarding voice, craft, and audience."
        ),
        "love": (
            "Warm and expressive; needs appreciation. "
            "Best rhythm with 1, 3, 5, 6, 9. Friction with 4 when structure feels rigid."
        ),
        "wellness": (
            "Voice and throat care for heavy talkers; stretch breaks between screens. "
            "Creative burnout fades with one non-negotiable rest evening per week. "
            "Light cardio + social hobbies balance sedentary work."
        ),
        "best_match": [1, 3, 5, 6, 9],
        "avoid_match": [4],
    },
    4: {
        "title": "Number 4 — Structure & Discipline Pattern",
        "headline": "Practical · Reliable · Builder",
        "narrative": (
            "Number 4 profiles trust systems, checklists, and proof. You build slowly and "
            "lastingly; sudden chaos drains you. Success comes from documenting processes "
            "and saying no to shortcuts that compromise quality."
        ),
        "strengths": [
            "Discipline and follow-through",
            "Systems thinking",
            "Loyalty and reliability",
            "Financial caution and planning",
            "Technical and operational skill",
        ],
        "weaknesses": [
            "Rigidity when plans change",
            "Overwork without recovery",
            "Skepticism slowing innovation",
            "Stubbornness in relationships",
        ],
        "famous": [
            "Bill Gates", "Oprah Winfrey", "Margaret Thatcher",
            "A.P.J. Abdul Kalam", "Dhirubhai Ambani",
        ],
        "career": (
            "Engineering, operations, finance, compliance, project management, "
            "infrastructure — roles with clear metrics and steady improvement."
        ),
        "love": (
            "Steady and dependable; shows love through actions. "
            "Best rhythm with 2, 4, 6, 8. Friction with 5 when change feels reckless."
        ),
        "wellness": (
            "Desk-bound tension — hourly posture resets and walking meetings help. "
            "Structured meal times prevent stress eating. Schedule true off-days; "
            "number 4 types often skip recovery until exhausted."
        ),
        "best_match": [2, 4, 6, 8],
        "avoid_match": [5],
    },
    5: {
        "title": "Number 5 — Adaptability & Movement Pattern",
        "headline": "Curious · Agile · Communicator",
        "narrative": (
            "Number 5 profiles need variety, travel, and fresh input. You learn fast and "
            "pivot quickly — boredom is your main risk. Anchor freedom with one financial "
            "rule and one health routine so movement stays productive, not chaotic."
        ),
        "strengths": [
            "Quick learning and adaptability",
            "Sales and negotiation instinct",
            "Networking across domains",
            "Crisis improvisation",
            "Multilingual or multi-skill tendency",
        ],
        "weaknesses": [
            "Restlessness and unfinished projects",
            "Impulsive spending or commitments",
            "Inconsistent routines",
            "Difficulty with long bureaucratic processes",
        ],
        "famous": [
            "Mark Zuckerberg", "Virat Kohli", "Helen Keller",
            "Angelina Jolie", "Aamir Khan",
        ],
        "career": (
            "Sales, trading, travel, media, product, startups, consulting — "
            "high-change environments with clear targets."
        ),
        "love": (
            "Needs mental stimulation and space; honest communication is essential. "
            "Best rhythm with 1, 3, 5, 9. Friction with 2 when closeness feels clingy."
        ),
        "wellness": (
            "Nervous energy — channel into short workouts, not late-night stimulation. "
            "Cap caffeine after mid-afternoon. Travel weeks need sleep hygiene "
            "and hydration rules to avoid crash cycles."
        ),
        "best_match": [1, 3, 5, 9],
        "avoid_match": [2],
    },
    6: {
        "title": "Number 6 — Responsibility & Harmony Pattern",
        "headline": "Caring · Aesthetic · Family-oriented",
        "narrative": (
            "Number 6 profiles carry duty for home, team, and quality of experience. "
            "You create beauty and stability for others — remember to budget time and "
            "money for yourself so generosity does not become resentment."
        ),
        "strengths": [
            "Responsibility and follow-through on promises",
            "Aesthetic sense and client care",
            "Mediation in groups",
            "Loyalty to family and team",
            "Teaching and mentoring patience",
        ],
        "weaknesses": [
            "Over-giving and martyrdom",
            "Perfectionism delaying delivery",
            "Taking criticism of work personally",
            "Neglecting personal goals for others",
        ],
        "famous": [
            "Sachin Tendulkar", "Madhuri Dixit", "Elizabeth Taylor",
            "Ben Affleck", "Sanjay Dutt",
        ],
        "career": (
            "Healthcare, education, design, hospitality, HR, family business, "
            "luxury services — roles blending care and presentation."
        ),
        "love": (
            "Devoted and romantic; needs reciprocity. "
            "Best rhythm with 2, 3, 6, 9. Friction with 1 when leadership styles collide."
        ),
        "wellness": (
            "Stress from caretaking — schedule non-negotiable personal time. "
            "Balanced meals and boundaries around evening work messages. "
            "Creative hobbies (music, cooking, decor) restore emotional balance."
        ),
        "best_match": [2, 3, 6, 9],
        "avoid_match": [1],
    },
    7: {
        "title": "Number 7 — Analysis & Depth Pattern",
        "headline": "Reflective · Private · Specialist",
        "narrative": (
            "Number 7 profiles seek truth beneath surface noise. You need solitude to "
            "think deeply; forced small talk drains you. Pair expertise with one trusted "
            "collaborator who handles outreach so your best work reaches the world."
        ),
        "strengths": [
            "Research and analytical depth",
            "Independent problem-solving",
            "Calm under complexity",
            "Integrity and discretion",
            "Specialist mastery over time",
        ],
        "weaknesses": [
            "Isolation and trust barriers",
            "Overthinking delaying action",
            "Skepticism sounding cold",
            "Difficulty scaling without help",
        ],
        "famous": [
            "A.P.J. Abdul Kalam", "Princess Diana", "Christian Bale",
            "Emma Watson", "Katrina Kaif",
        ],
        "career": (
            "Research, data, writing, academia, audit, strategy, niche consulting — "
            "depth beats breadth."
        ),
        "love": (
            "Slow to open; values intellectual honesty. "
            "Best rhythm with 2, 4, 7. Friction with 3 or 5 when pace feels superficial."
        ),
        "wellness": (
            "Quiet recovery is non-optional — digital sunsets and walking without podcasts. "
            "Gentle strength training supports posture for long desk sessions. "
            "Schedule medical checkups; number 7 types often ignore minor symptoms."
        ),
        "best_match": [2, 4, 7],
        "avoid_match": [3, 5],
    },
    8: {
        "title": "Number 8 — Accountability & Scale Pattern",
        "headline": "Ambitious · Strategic · Results-driven",
        "narrative": (
            "Number 8 profiles play long games: assets, institutions, measurable outcomes. "
            "You respect hierarchy when fair and rebel when it is not. Build wealth with "
            "written rules, legal clarity, and patience — shortcuts trigger your hardest lessons."
        ),
        "strengths": [
            "Executive judgment",
            "Financial and operational scale",
            "Persistence through setbacks",
            "Negotiation and boundary-setting",
            "Mentoring disciplined teams",
        ],
        "weaknesses": [
            "Workaholism and emotional distance",
            "Control issues in partnerships",
            "Cynicism after betrayal",
            "Health neglected during crunch periods",
        ],
        "famous": [
            "Narendra Modi", "Shah Rukh Khan", "Pablo Picasso",
            "Paul McCartney", "Saddam Hussein",
        ],
        "career": (
            "Banking, real estate, operations, law, manufacturing, C-suite — "
            "measurable P&L and governance."
        ),
        "love": (
            "Shows love through security and plans; needs respect. "
            "Best rhythm with 2, 4, 6, 8. Friction with 1 or 9 when egos compete."
        ),
        "wellness": (
            "Chronic stress management: sleep, joint care, scheduled breaks. "
            "Delegate before exhaustion; number 8 profiles often equate rest with weakness. "
            "Weekly offline block improves decision quality."
        ),
        "best_match": [2, 4, 6, 8],
        "avoid_match": [1, 9],
    },
    9: {
        "title": "Number 9 — Completion & Impact Pattern",
        "headline": "Intense · Courageous · Humanitarian",
        "narrative": (
            "Number 9 profiles finish cycles others abandon. You fight for causes, people, "
            "or standards you believe in — intensity is your gift and your trigger. "
            "Channel anger into structured goals; release what is complete so new work can start."
        ),
        "strengths": [
            "Courage and conviction",
            "Big-picture humanitarian drive",
            "Resilience after failure",
            "Charisma in mission-led work",
            "Ability to close and hand off",
        ],
        "weaknesses": [
            "Anger spikes and burnout",
            "Difficulty forgiving slights",
            "All-or-nothing commitments",
            "Letting go of finished chapters",
        ],
        "famous": [
            "Nelson Mandela", "Akshay Kumar", "Jimmy Carter",
            "Mother Teresa", "Bruce Lee",
        ],
        "career": (
            "Medicine, sports, defence, NGOs, emergency services, law enforcement, "
            "turnaround leadership — high-stakes impact roles."
        ),
        "love": (
            "Passionate and protective; needs honesty. "
            "Best rhythm with 3, 6, 9. Friction with 8 when power struggles dominate."
        ),
        "wellness": (
            "Anger and inflammation — regular cardio and conflict cooldown habits (walk, "
            "write, then reply). Protect head and muscle recovery in contact sports or "
            "high-stress jobs. Mandatory rest after major pushes."
        ),
        "best_match": [3, 6, 9],
        "avoid_match": [8],
    },
}

SINGLE_DIGIT_SHORT: Dict[int, str] = {
    1: "Number 1 — leadership, recognition, fresh start; favourable for action.",
    2: "Number 2 — cooperation, sensitivity, slow gains; favours diplomacy.",
    3: "Number 3 — creativity, expansion, teaching, money flow; very favourable.",
    4: "Number 4 — discipline, sudden change, hard work; mixed but steady.",
    5: "Number 5 — adaptability, business, communication, travel; favourable.",
    6: "Number 6 — responsibility, harmony, comforts; very favourable.",
    7: "Number 7 — analysis, research, depth; mixed but insightful.",
    8: "Number 8 — power, discipline, late but lasting success; cautious favourable.",
    9: "Number 9 — completion, courage, action; favourable for high-impact work.",
}


def get_personality(num: int) -> Dict[str, Any] | None:
    """Return personality block for 1–9 with practical habits attached."""
    from numerology.core.pure_numerology import affirmations_pack

    try:
        raw = NUMBER_PERSONALITY.get(int(num))
        if not raw:
            return None
        out = dict(raw)
        out["health"] = out.get("wellness", "")  # legacy PDF key
        out["practical"] = affirmations_pack(int(num))
        return out
    except (TypeError, ValueError):
        return None


def cheiro_compound_fallback(compound: int) -> str:
    try:
        n = int(compound)
    except (TypeError, ValueError):
        return ""
    while n > 9:
        n = sum(int(d) for d in str(n))
    short = SINGLE_DIGIT_SHORT.get(n, "")
    return f"reduces to {n} — {short}" if short else f"reduces to {n}."
