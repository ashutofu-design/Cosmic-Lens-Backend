"""
numerology/core/narratives.py — Premium narrative content engine (psychology-only).

Deep, story-style content per driver number (1-9):
  life_essence, career_pattern, love_pattern, money_pattern,
  health_pattern, life_direction (a.k.a. spiritual_path — pure psychology label),
  strengths, challenges, risk_alerts, golden_periods.

100% deterministic — behavioral psychology framing, no astrology source text.
"""

from __future__ import annotations

from typing import Any, Dict, List

_NARRATIVES_HG: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "Number 1 — Leadership Archetype",
        "tagline": "Aap lead karne ke liye wired ho — apne tareeke se.",
        "life_essence": [
            "Core pattern: initiative, direction, outcome ownership. Follower mode long-term drain karta hai.",
            "Strength = vision + decision speed. Risk = impatience + ego jab pace match na ho.",
            "Growth: clarity assert karo politely — respect chahiye, control nahi.",
        ],
        "career_pattern": [
            "Best: founder, CEO, project lead, sales leadership, public authority, operations commander.",
            "Mistake: boss ego clash in employee mode — 30+ par ownership role better.",
            "Rhythm: 22-24 foundation, 28-32 break, 36-40 peak. Big calls on high-focus mornings.",
        ],
        "love_pattern": [
            "Intense, loyal — half-heart ties sustain nahi hote.",
            "Breakup: dominance ya 'change karo' pressure.",
            "Rhythm: 2, 4, 7 grounding. Friction: dual-1 leadership fights.",
        ],
        "money_pattern": "Variable pay, business, equity suit karta hai. 6-month buffer + auto-invest; impulse par 24-hour rule.",
        "health_pattern": "Sleep, BP, eyes, back protect karo. Morning movement + post-meeting decompression.",
        "spiritual_path": "Direction: mentor-by-example. Weekly review — clarity di ya control?",
        "golden_periods": "Personal Year 1, 5, 9 = launch energy. Q2 often strongest for new starts.",
        "strengths": [
            "Vision",
            "Fast decisions",
            "Natural magnetism",
            "Original thinking",
            "Calm in crisis",
        ],
        "challenges": [
            "Ego vs authority",
            "Loneliness at top",
            "Impatience",
            "Overruling advice",
            "Thin skin to criticism",
        ],
        "risk_alerts": [
            "Authority conflict around 28-32 — pause before reacting",
            "Heart/BP watch after 40 — annual check-ups",
            "Partnership deals need written clarity",
            "Yes-people will drain you — audit inner circle yearly",
            "Big purchases: 24-hour cooling rule",
        ],
    },
    2: {
        "title": "Number 2 — Emotional Intelligence Pattern",
        "tagline": "Aap log padhkar unhe safe feel karate ho.",
        "life_essence": [
            "Aap emotional radar se operate karte ho — tone, pause, body language sab register hota hai.",
            "Gift = empathy + diplomacy. Price = apni needs last rakhna.",
            "28-day emotional rhythm normal hai — flow karo, fight mat karo.",
        ],
        "career_pattern": [
            "Best: HR, counselling, nursing, hospitality, writing, psychology, client success.",
            "Mistake: hyper-competitive sales — 4-5 saal me burnout.",
            "Peak often 32-38 — slow burn career graph.",
        ],
        "love_pattern": [
            "Give-give pattern — needs early express karo.",
            "Breakup: silent resentment phir sudden exit.",
            "Rhythm: 1, 4, 8 structure dete hain. Turbulent: 5 (too much motion).",
        ],
        "money_pattern": "Tidal cash flow — forced SIP + 6-month emergency fund emotional security deta hai.",
        "health_pattern": "Sleep, stomach, lungs — late nights avoid. Hydration + gentle movement.",
        "spiritual_path": "Direction: emotional translator — help others name feelings, apni bhi name karo.",
        "golden_periods": "Personal Year 2, 4, 6, 8 — partnership aur stability themes.",
        "strengths": [
            "Empathy",
            "Diplomacy",
            "Adaptability",
            "Aesthetic sense",
            "Patience in long games",
        ],
        "challenges": [
            "Mood swings",
            "Over-giving",
            "Avoiding confrontation",
            "Indecision under pressure",
            "Emotional spending",
        ],
        "risk_alerts": [
            "Caregiver burnout — schedule weekly recharge",
            "Late-night decisions skew negative — decide after sleep",
            "Toxic friendships can run 5+ years — annual relationship audit",
            "Express small needs early — do not stockpile resentment",
            "Sleep and digestion suffer when overloaded",
        ],
    },
    3: {
        "title": "Number 3 — Creative Expression Pattern",
        "tagline": "Aap ideas ko words, deals, aur impact me convert karte ho.",
        "life_essence": [
            "Old-soul communicator — explain, teach, reframe automatically.",
            "Strength = optimism + storytelling. Risk = advice bina verify kiye.",
            "Humility + knowledge = sustainable influence.",
        ],
        "career_pattern": [
            "Best: teaching, law, finance advisory, publishing, content, coaching, product marketing.",
            "Mistake: sirf advise, execute kam — ek project khud deliver karo.",
            "Peak teaching phase 33-36; content income stream build karo.",
        ],
        "love_pattern": [
            "Partner ko mentor ban jaate ho — space for their growth chahiye.",
            "Breakup: 'I outgrew you' feeling.",
            "Rhythm: 3, 6, 9 creative peers. Turbulent: 5 emotionally.",
        ],
        "money_pattern": "Knowledge monetization — coaching, courses, writing. Diversify; one salary trap.",
        "health_pattern": "Liver, metabolism, hips — sweets limit; walk after meals.",
        "spiritual_path": "Direction: wisdom-sharing with accountability — learn publicly, iterate openly.",
        "golden_periods": "Personal Year 3, 6, 9 — expression aur income link strong.",
        "strengths": [
            "Teaching clarity",
            "Optimism",
            "Creative framing",
            "Generosity",
            "Long-range planning",
        ],
        "challenges": [
            "Overconfidence in advice",
            "Weak follow-through",
            "Weight gain when sedentary",
            "Unsolicited lecturing",
            "Over-invested in students",
        ],
        "risk_alerts": [
            "Verify facts before advising — reputation risk",
            "One executed project beats ten plans",
            "Limit alcohol and fried food after 35",
            "Set office hours for advice — avoid free consulting",
            "Detach from others' failures — support, don't absorb",
        ],
    },
    4: {
        "title": "Number 4 — Structure & Discipline Pattern",
        "tagline": "Aap systems tod kar better systems banate ho.",
        "life_essence": [
            "Non-linear path — sudden jumps, resets, comebacks.",
            "Strength = innovation + tech comfort. Risk = boredom + shortcut traps.",
            "Long ethical work beats quick wins.",
        ],
        "career_pattern": [
            "Best: software, AI/data, foreign trade, aviation, film/photo, fintech, research startups.",
            "Mistake: 2-3 saal job hop — 7+ years ek industry me depth.",
            "Breakthrough windows often 26-28, 33-35, 41-44.",
        ],
        "love_pattern": [
            "Unpredictable intensity — partner ko novelty chahiye.",
            "Breakup: boredom in routine.",
            "Rhythm: 1, 5, 7 independence respect. Mismatch: 2 (pace clash).",
        ],
        "money_pattern": "Wave income — 70% safe assets, 30% speculative max. Document everything.",
        "health_pattern": "Skin, nerves, sleep — meditation + phone curfew 1hr before bed.",
        "spiritual_path": "Direction: constructive disruption — upgrade broken processes, not people.",
        "golden_periods": "Personal Year 1, 4, 7 — innovation sprint months.",
        "strengths": [
            "Original thinking",
            "Tech adoption",
            "Crisis innovation",
            "Diverse network",
            "Systems mindset",
        ],
        "challenges": [
            "Restlessness",
            "Screen/addiction risk",
            "Sudden anger spikes",
            "Relationship boredom",
            "Get-rich-quick temptation",
        ],
        "risk_alerts": [
            "Cap speculative investments at 30% of portfolio",
            "Document travel and contracts — chaos tax is real",
            "Job-hop pattern blocks mastery — commit 7 years once",
            "Digital detox before sleep — non-negotiable",
            "Stress-eating and night scrolling erode health",
        ],
    },
    5: {
        "title": "Number 5 — Adaptability & Movement Pattern",
        "tagline": "Aap deals, ideas, aur logon ko jodne me fastest ho.",
        "life_essence": [
            "Brain always on — multitask natural, depth discipline hard.",
            "Strength = network + negotiation. Risk = shallow mastery.",
            "10,000 hours ek skill par — yahi mastery unlock hai.",
        ],
        "career_pattern": [
            "Best: sales, marketing, media, IT, brokerage, travel, PR, consulting.",
            "Mistake: hop every 2 years — umbrella business with varied clients.",
            "Commercial sense early 22-25; stabilize 35-40.",
        ],
        "love_pattern": [
            "Fun, stimulating — emotional depth avoid karte ho kabhi.",
            "Breakup: half-present feel (phone/work parallel).",
            "Rhythm: 1, 3, 6, 9 intellectual peers.",
        ],
        "money_pattern": "Multiple streams mandatory — side hustle + diversified investments.",
        "health_pattern": "Anxiety, IBS, skin — no multitask while eating; daily breathwork.",
        "spiritual_path": "Direction: connector-curator — bridge people, protect your focus blocks.",
        "golden_periods": "Personal Year 5 — change aur opportunity peak.",
        "strengths": [
            "Multitasking",
            "Networking",
            "Adaptability",
            "Negotiation",
            "Fast learning",
        ],
        "challenges": [
            "Shallow mastery",
            "Anxiety/restlessness",
            "Commitment phobia",
            "Sarcasm under stress",
            "Over-promising",
        ],
        "risk_alerts": [
            "Trading/speculation needs hard stop-loss rules",
            "Phone-free hour daily for relationships",
            "Social media cap — productivity leak",
            "Say no to extra projects until delivery clears",
            "Breathwork 10 min daily — nervous system reset",
        ],
    },
    6: {
        "title": "Number 6 — Responsibility & Harmony Pattern",
        "tagline": "Aap relationships aur environment ko beautiful banate ho.",
        "life_essence": [
            "Harmony, aesthetics, care — family glue role natural.",
            "Strength = charm + reliability. Risk = over-attachment, self neglect.",
            "Self-care sustainable relationship ka part hai.",
        ],
        "career_pattern": [
            "Best: fashion, beauty, events, hospitality, interior, healthcare client roles.",
            "Mistake: family duty me personal dreams compromise — both/and plan banao.",
            "Income peak often 32-38; brand = trust + taste.",
        ],
        "love_pattern": [
            "Romantic, generous — reciprocity clearly communicate karo.",
            "Breakup: silent scorekeeping.",
            "Rhythm: 3, 6, 9 beauty/wisdom blend.",
        ],
        "money_pattern": "Money via relationships, design, service — luxury OK if income ratio disciplined.",
        "health_pattern": "Kidneys, throat, skin mirror stress — hydration, boundaries, sleep.",
        "spiritual_path": "Direction: beautify responsibility — care with boundaries, art with budget.",
        "golden_periods": "Personal Year 6 — home, love, creative projects peak.",
        "strengths": [
            "Aesthetic sense",
            "Relationship maintenance",
            "Diplomacy",
            "Generosity",
            "First-meeting charm",
        ],
        "challenges": [
            "Luxury overspend",
            "Weak boundaries with family",
            "Conflict avoidance",
            "Vanity pressure",
            "Comfort-zone trap",
        ],
        "risk_alerts": [
            "Keep lifestyle spend under 40% of income",
            "Schedule personal goals alongside family duty",
            "Speak needs before resentment builds",
            "Reproductive/kidney/skin stress shows when overloaded",
            "Toxic relationship >7 years — get professional help",
        ],
    },
    7: {
        "title": "Number 7 — Analysis & Depth Pattern",
        "tagline": "Aap depth me jaakar truth dhundhte ho — quietly.",
        "life_essence": [
            "Introverted analyst — crowd me bhi inner world active.",
            "Strength = research + intuition. Risk = detachment from practical life.",
            "Daily 1hr admin/social grounding mandatory.",
        ],
        "career_pattern": [
            "Best: research, data science, writing, psychology, forensic, R&D, solo consulting.",
            "Mistake: rejecting money as 'shallow' — financial system bhi skill hai.",
            "Recognition often 35-45 — late bloomer graph.",
        ],
        "love_pattern": [
            "Intimacy slow — partner ko patience chahiye.",
            "Breakup: 'I can't reach you'.",
            "Rhythm: 4, 7, 1 respect space. Marriage often late OK.",
        ],
        "money_pattern": "Knowledge income — writing, consulting, research. Auto-SIP kyunki planning weak ho sakti hai.",
        "health_pattern": "Nerves, immunity, digestion — routine sleep, nature walks, limit stimulants.",
        "spiritual_path": "Direction: inner clarity for outer decisions — journal, retreat, then act.",
        "golden_periods": "Personal Year 7 — study, solo projects, insight breakthroughs.",
        "strengths": [
            "Deep research",
            "Intuition",
            "Self-sufficiency",
            "Unbiased judgment",
            "Pattern recognition",
        ],
        "challenges": [
            "Isolation risk",
            "Practical-world friction",
            "Intimacy distance",
            "Late commitment",
            "Cynicism",
        ],
        "risk_alerts": [
            "One hour daily for bills, family, admin — stay grounded",
            "Solo time is asset, not escape — balance social anchor",
            "Journaling clarifies relationship needs",
            "Unexplained fatigue — medical check, not just analysis",
            "Avoid substance escape — sober clarity wins",
        ],
    },
    8: {
        "title": "Number 8 — Accountability & Scale Pattern",
        "tagline": "Aap long game khelte ho — slow build, big scale.",
        "life_essence": [
            "Serious, strategic — shortcuts expensive padte hain.",
            "Strength = discipline + loyalty. Risk = emotional coldness + pessimism.",
            "Real momentum often 35+ — patience is strategy.",
        ],
        "career_pattern": [
            "Best: real estate, infrastructure, banking, insurance, ops leadership, judiciary-adjacent.",
            "Mistake: quick win frustration — 10-year roadmap likho.",
            "Peak bands 36-42, 48-55 wealth crystallization.",
        ],
        "love_pattern": [
            "Loyal once committed — words of affection matter.",
            "Breakup: perceived coldness.",
            "Rhythm: 4, 6, 8 stability. Late marriage often healthier.",
        ],
        "money_pattern": "Slow compound wealth — real assets, index funds, avoid speculative debt.",
        "health_pattern": "Joints, knees, teeth, mood — walking, strength training, therapy OK.",
        "spiritual_path": "Direction: scale with integrity — power ko service se balance karo.",
        "golden_periods": "Personal Year 8 — contracts, promotions, asset moves.",
        "strengths": [
            "Discipline",
            "Endurance",
            "Strategic mind",
            "Loyalty",
            "Justice orientation",
        ],
        "challenges": [
            "Perceived coldness",
            "Pessimism spells",
            "Slow early progress",
            "Workaholism",
            "Authority friction",
        ],
        "risk_alerts": [
            "Express affection in words, not only actions",
            "Bone/joint care from 30 — walking + mobility",
            "Depression window 28-30 — therapy is strength",
            "Calendar family time like client meetings",
            "10-year plans beat shortcut temptations",
        ],
    },
    9: {
        "title": "Number 9 — Completion & Impact Pattern",
        "tagline": "Aap passion ke liye fight karte ho — energy high, impact driven.",
        "life_essence": [
            "Volcano energy — channelled = massive impact, unchannelled = burnout/conflict.",
            "Strength = courage + protectiveness. Risk = anger + impulsivity.",
            "Daily movement non-negotiable — emotional regulation tool.",
        ],
        "career_pattern": [
            "Best: sports, defence, surgery, engineering, manufacturing, emergency roles, fitness leadership.",
            "Mistake: authority fights in jobs — 30+ self-employment often better.",
            "Surge 24-28, stabilize 32-36, legacy 42-48.",
        ],
        "love_pattern": [
            "Intense, protective — jealousy management lifelong skill.",
            "Breakup: words said in anger.",
            "Rhythm: 1, 5, 9 high energy. Dual-9 explosive.",
        ],
        "money_pattern": "Earn via effort + risk roles — diversify; anger se financial decisions mat lo.",
        "health_pattern": "Blood, muscles, head — sport safety, annual labs, spice moderation.",
        "spiritual_path": "Direction: fight for causes, not egos — mission > argument.",
        "golden_periods": "Personal Year 9 — completion, release, next-cycle prep.",
        "strengths": [
            "Courage",
            "High energy",
            "Passion",
            "Protective instinct",
            "Initiative",
        ],
        "challenges": [
            "Anger management",
            "Impulsivity",
            "Jealousy",
            "Injury risk",
            "Authority clashes",
        ],
        "risk_alerts": [
            "24-hour rule before angry texts or calls",
            "Defensive driving — accident risk above average",
            "Daily 60-min movement — anger outlet",
            "Health insurance early — surgery/injury possible",
            "Channel fight energy into sport or mission, not people",
        ],
    },
}

_NARRATIVES_EN: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "Number 1 — Leadership Archetype",
        "tagline": "You are wired to lead — on your own terms.",
        "life_essence": [
            "Core pattern: initiative, direction, outcome ownership. Follower mode drains you long-term.",
            "Strength = vision plus decision speed. Risk = impatience and ego when pace mismatches.",
            "Growth: assert clarity politely — you need respect, not control.",
        ],
        "career_pattern": [
            "Best: founder, CEO, project lead, sales leadership, public authority, operations commander.",
            "Mistake: boss ego clashes in employee mode — ownership role after 30 works better.",
            "Rhythm: 22-24 foundation, 28-32 break, 36-40 peak. Big calls on high-focus mornings.",
        ],
        "love_pattern": [
            "Intense, loyal — half-hearted ties do not sustain.",
            "Breakup: dominance or 'change yourself' pressure.",
            "Rhythm: 2, 4, 7 for grounding. Friction: dual-1 leadership fights.",
        ],
        "money_pattern": "Variable pay, business, and equity suit you. Six-month buffer plus auto-invest; 24-hour rule on impulse.",
        "health_pattern": "Protect sleep, blood pressure, eyes, and back. Morning movement plus post-meeting decompression.",
        "spiritual_path": "Direction: mentor by example. Weekly review — did you offer clarity or control?",
        "golden_periods": "Personal Years 1, 5, 9 = launch energy. Q2 is often strongest for new starts.",
        "strengths": [
            "Vision",
            "Fast decisions",
            "Natural magnetism",
            "Original thinking",
            "Calm in crisis",
        ],
        "challenges": [
            "Ego vs authority",
            "Loneliness at top",
            "Impatience",
            "Overruling advice",
            "Thin skin to criticism",
        ],
        "risk_alerts": [
            "Authority conflict around 28-32 — pause before reacting",
            "Heart/BP watch after 40 — annual check-ups",
            "Partnership deals need written clarity",
            "Yes-people will drain you — audit inner circle yearly",
            "Big purchases: 24-hour cooling rule",
        ],
    },
    2: {
        "title": "Number 2 — Emotional Intelligence Pattern",
        "tagline": "You read people and make them feel safe.",
        "life_essence": [
            "You operate on emotional radar — tone, pause, and body language all register.",
            "Gift = empathy plus diplomacy. Price = putting your needs last.",
            "A 28-day emotional rhythm is normal — flow with it, do not fight it.",
        ],
        "career_pattern": [
            "Best: HR, counselling, nursing, hospitality, writing, psychology, client success.",
            "Mistake: hyper-competitive sales — burnout in 4-5 years.",
            "Peak often 32-38 — slow-burn career graph.",
        ],
        "love_pattern": [
            "Give-give pattern — express needs early.",
            "Breakup: silent resentment then sudden exit.",
            "Rhythm: 1, 4, 8 provide structure. Turbulent: 5 (too much motion).",
        ],
        "money_pattern": "Tidal cash flow — forced SIP plus six-month emergency fund gives emotional security.",
        "health_pattern": "Sleep, stomach, lungs — avoid late nights. Hydration plus gentle movement.",
        "spiritual_path": "Direction: emotional translator — help others name feelings; name yours too.",
        "golden_periods": "Personal Years 2, 4, 6, 8 — partnership and stability themes.",
        "strengths": [
            "Empathy",
            "Diplomacy",
            "Adaptability",
            "Aesthetic sense",
            "Patience in long games",
        ],
        "challenges": [
            "Mood swings",
            "Over-giving",
            "Avoiding confrontation",
            "Indecision under pressure",
            "Emotional spending",
        ],
        "risk_alerts": [
            "Caregiver burnout — schedule weekly recharge",
            "Late-night decisions skew negative — decide after sleep",
            "Toxic friendships can run 5+ years — annual relationship audit",
            "Express small needs early — do not stockpile resentment",
            "Sleep and digestion suffer when overloaded",
        ],
    },
    3: {
        "title": "Number 3 — Creative Expression Pattern",
        "tagline": "You turn ideas into words, deals, and impact.",
        "life_essence": [
            "Old-soul communicator — you explain, teach, and reframe automatically.",
            "Strength = optimism plus storytelling. Risk = advice without verification.",
            "Humility plus knowledge = sustainable influence.",
        ],
        "career_pattern": [
            "Best: teaching, law, finance advisory, publishing, content, coaching, product marketing.",
            "Mistake: advise only, execute little — deliver one project yourself.",
            "Peak teaching phase 33-36; build a content income stream.",
        ],
        "love_pattern": [
            "You become mentor to partner — they need space to grow.",
            "Breakup: 'I outgrew you' feeling.",
            "Rhythm: 3, 6, 9 creative peers. Turbulent: 5 emotionally.",
        ],
        "money_pattern": "Monetize knowledge — coaching, courses, writing. Diversify; one salary is a trap.",
        "health_pattern": "Liver, metabolism, hips — limit sweets; walk after meals.",
        "spiritual_path": "Direction: wisdom-sharing with accountability — learn publicly, iterate openly.",
        "golden_periods": "Personal Years 3, 6, 9 — expression and income link strongly.",
        "strengths": [
            "Teaching clarity",
            "Optimism",
            "Creative framing",
            "Generosity",
            "Long-range planning",
        ],
        "challenges": [
            "Overconfidence in advice",
            "Weak follow-through",
            "Weight gain when sedentary",
            "Unsolicited lecturing",
            "Over-invested in students",
        ],
        "risk_alerts": [
            "Verify facts before advising — reputation risk",
            "One executed project beats ten plans",
            "Limit alcohol and fried food after 35",
            "Set office hours for advice — avoid free consulting",
            "Detach from others' failures — support, don't absorb",
        ],
    },
    4: {
        "title": "Number 4 — Structure & Discipline Pattern",
        "tagline": "You break systems to build better ones.",
        "life_essence": [
            "Non-linear path — sudden jumps, resets, comebacks.",
            "Strength = innovation plus tech comfort. Risk = boredom and shortcut traps.",
            "Long ethical work beats quick wins.",
        ],
        "career_pattern": [
            "Best: software, AI/data, foreign trade, aviation, film/photo, fintech, research startups.",
            "Mistake: job-hop every 2-3 years — 7+ years in one industry for depth.",
            "Breakthrough windows often 26-28, 33-35, 41-44.",
        ],
        "love_pattern": [
            "Unpredictable intensity — partner needs novelty.",
            "Breakup: boredom in routine.",
            "Rhythm: 1, 5, 7 respect independence. Mismatch: 2 (pace clash).",
        ],
        "money_pattern": "Wave income — 70% safe assets, 30% speculative max. Document everything.",
        "health_pattern": "Skin, nerves, sleep — meditation plus phone curfew one hour before bed.",
        "spiritual_path": "Direction: constructive disruption — upgrade broken processes, not people.",
        "golden_periods": "Personal Years 1, 4, 7 — innovation sprint months.",
        "strengths": [
            "Original thinking",
            "Tech adoption",
            "Crisis innovation",
            "Diverse network",
            "Systems mindset",
        ],
        "challenges": [
            "Restlessness",
            "Screen/addiction risk",
            "Sudden anger spikes",
            "Relationship boredom",
            "Get-rich-quick temptation",
        ],
        "risk_alerts": [
            "Cap speculative investments at 30% of portfolio",
            "Document travel and contracts — chaos tax is real",
            "Job-hop pattern blocks mastery — commit 7 years once",
            "Digital detox before sleep — non-negotiable",
            "Stress-eating and night scrolling erode health",
        ],
    },
    5: {
        "title": "Number 5 — Adaptability & Movement Pattern",
        "tagline": "You are fastest at connecting deals, ideas, and people.",
        "life_essence": [
            "Brain always on — multitasking is natural, depth discipline is hard.",
            "Strength = network plus negotiation. Risk = shallow mastery.",
            "Ten thousand hours on one skill — that unlocks mastery.",
        ],
        "career_pattern": [
            "Best: sales, marketing, media, IT, brokerage, travel, PR, consulting.",
            "Mistake: hop every 2 years — umbrella business with varied clients.",
            "Commercial sense by 22-25; stabilize 35-40.",
        ],
        "love_pattern": [
            "Fun, stimulating — you sometimes avoid emotional depth.",
            "Breakup: feeling half-present (phone/work parallel).",
            "Rhythm: 1, 3, 6, 9 intellectual peers.",
        ],
        "money_pattern": "Multiple streams are mandatory — side hustle plus diversified investments.",
        "health_pattern": "Anxiety, IBS, skin — no multitasking while eating; daily breathwork.",
        "spiritual_path": "Direction: connector-curator — bridge people, protect your focus blocks.",
        "golden_periods": "Personal Year 5 — peak change and opportunity.",
        "strengths": [
            "Multitasking",
            "Networking",
            "Adaptability",
            "Negotiation",
            "Fast learning",
        ],
        "challenges": [
            "Shallow mastery",
            "Anxiety/restlessness",
            "Commitment phobia",
            "Sarcasm under stress",
            "Over-promising",
        ],
        "risk_alerts": [
            "Trading/speculation needs hard stop-loss rules",
            "Phone-free hour daily for relationships",
            "Social media cap — productivity leak",
            "Say no to extra projects until delivery clears",
            "Breathwork 10 min daily — nervous system reset",
        ],
    },
    6: {
        "title": "Number 6 — Responsibility & Harmony Pattern",
        "tagline": "You make relationships and environments beautiful.",
        "life_essence": [
            "Harmony, aesthetics, care — natural family glue role.",
            "Strength = charm plus reliability. Risk = over-attachment and self-neglect.",
            "Self-care is part of a sustainable relationship.",
        ],
        "career_pattern": [
            "Best: fashion, beauty, events, hospitality, interior, healthcare client roles.",
            "Mistake: compromising personal dreams for family duty — plan both/and.",
            "Income peak often 32-38; brand = trust plus taste.",
        ],
        "love_pattern": [
            "Romantic, generous — communicate reciprocity clearly.",
            "Breakup: silent scorekeeping.",
            "Rhythm: 3, 6, 9 beauty and wisdom blend.",
        ],
        "money_pattern": "Money via relationships, design, service — luxury OK if income ratio is disciplined.",
        "health_pattern": "Kidneys, throat, skin mirror stress — hydration, boundaries, sleep.",
        "spiritual_path": "Direction: beautify responsibility — care with boundaries, art with budget.",
        "golden_periods": "Personal Year 6 — home, love, creative projects peak.",
        "strengths": [
            "Aesthetic sense",
            "Relationship maintenance",
            "Diplomacy",
            "Generosity",
            "First-meeting charm",
        ],
        "challenges": [
            "Luxury overspend",
            "Weak boundaries with family",
            "Conflict avoidance",
            "Vanity pressure",
            "Comfort-zone trap",
        ],
        "risk_alerts": [
            "Keep lifestyle spend under 40% of income",
            "Schedule personal goals alongside family duty",
            "Speak needs before resentment builds",
            "Reproductive/kidney/skin stress shows when overloaded",
            "Toxic relationship >7 years — get professional help",
        ],
    },
    7: {
        "title": "Number 7 — Analysis & Depth Pattern",
        "tagline": "You seek truth in depth — quietly.",
        "life_essence": [
            "Introverted analyst — inner world active even in crowds.",
            "Strength = research plus intuition. Risk = detachment from practical life.",
            "Daily one hour of admin/social grounding is mandatory.",
        ],
        "career_pattern": [
            "Best: research, data science, writing, psychology, forensic, R&D, solo consulting.",
            "Mistake: rejecting money as shallow — financial systems are a skill too.",
            "Recognition often 35-45 — late-bloomer graph.",
        ],
        "love_pattern": [
            "Intimacy is slow — partner needs patience.",
            "Breakup: 'I can't reach you'.",
            "Rhythm: 4, 7, 1 respect space. Late marriage is OK.",
        ],
        "money_pattern": "Knowledge income — writing, consulting, research. Auto-SIP because planning can be weak.",
        "health_pattern": "Nerves, immunity, digestion — routine sleep, nature walks, limit stimulants.",
        "spiritual_path": "Direction: inner clarity for outer decisions — journal, retreat, then act.",
        "golden_periods": "Personal Year 7 — study, solo projects, insight breakthroughs.",
        "strengths": [
            "Deep research",
            "Intuition",
            "Self-sufficiency",
            "Unbiased judgment",
            "Pattern recognition",
        ],
        "challenges": [
            "Isolation risk",
            "Practical-world friction",
            "Intimacy distance",
            "Late commitment",
            "Cynicism",
        ],
        "risk_alerts": [
            "One hour daily for bills, family, admin — stay grounded",
            "Solo time is asset, not escape — balance social anchor",
            "Journaling clarifies relationship needs",
            "Unexplained fatigue — medical check, not just analysis",
            "Avoid substance escape — sober clarity wins",
        ],
    },
    8: {
        "title": "Number 8 — Accountability & Scale Pattern",
        "tagline": "You play the long game — slow build, big scale.",
        "life_essence": [
            "Serious, strategic — shortcuts are expensive.",
            "Strength = discipline plus loyalty. Risk = emotional coldness and pessimism.",
            "Real momentum often after 35 — patience is strategy.",
        ],
        "career_pattern": [
            "Best: real estate, infrastructure, banking, insurance, ops leadership, judiciary-adjacent.",
            "Mistake: quick-win frustration — write a ten-year roadmap.",
            "Peak bands 36-42, 48-55 wealth crystallization.",
        ],
        "love_pattern": [
            "Loyal once committed — words of affection matter.",
            "Breakup: perceived coldness.",
            "Rhythm: 4, 6, 8 stability. Late marriage is often healthier.",
        ],
        "money_pattern": "Slow compound wealth — real assets, index funds, avoid speculative debt.",
        "health_pattern": "Joints, knees, teeth, mood — walking, strength training, therapy is OK.",
        "spiritual_path": "Direction: scale with integrity — balance power with service.",
        "golden_periods": "Personal Year 8 — contracts, promotions, asset moves.",
        "strengths": [
            "Discipline",
            "Endurance",
            "Strategic mind",
            "Loyalty",
            "Justice orientation",
        ],
        "challenges": [
            "Perceived coldness",
            "Pessimism spells",
            "Slow early progress",
            "Workaholism",
            "Authority friction",
        ],
        "risk_alerts": [
            "Express affection in words, not only actions",
            "Bone/joint care from 30 — walking + mobility",
            "Depression window 28-30 — therapy is strength",
            "Calendar family time like client meetings",
            "10-year plans beat shortcut temptations",
        ],
    },
    9: {
        "title": "Number 9 — Completion & Impact Pattern",
        "tagline": "You fight for passion — high energy, impact driven.",
        "life_essence": [
            "Volcano energy — channelled = massive impact, unchannelled = burnout and conflict.",
            "Strength = courage plus protectiveness. Risk = anger and impulsivity.",
            "Daily movement is non-negotiable — an emotional regulation tool.",
        ],
        "career_pattern": [
            "Best: sports, defence, surgery, engineering, manufacturing, emergency roles, fitness leadership.",
            "Mistake: authority fights in jobs — self-employment after 30 often better.",
            "Surge 24-28, stabilize 32-36, legacy 42-48.",
        ],
        "love_pattern": [
            "Intense, protective — jealousy management is a lifelong skill.",
            "Breakup: words said in anger.",
            "Rhythm: 1, 5, 9 high energy. Dual-9 is explosive.",
        ],
        "money_pattern": "Earn via effort and risk roles — diversify; do not decide finances in anger.",
        "health_pattern": "Blood, muscles, head — sport safety, annual labs, spice moderation.",
        "spiritual_path": "Direction: fight for causes, not egos — mission over argument.",
        "golden_periods": "Personal Year 9 — completion, release, next-cycle prep.",
        "strengths": [
            "Courage",
            "High energy",
            "Passion",
            "Protective instinct",
            "Initiative",
        ],
        "challenges": [
            "Anger management",
            "Impulsivity",
            "Jealousy",
            "Injury risk",
            "Authority clashes",
        ],
        "risk_alerts": [
            "24-hour rule before angry texts or calls",
            "Defensive driving — accident risk above average",
            "Daily 60-min movement — anger outlet",
            "Health insurance early — surgery/injury possible",
            "Channel fight energy into sport or mission, not people",
        ],
    },
}

_NARRATIVES_HI: Dict[int, Dict[str, Any]] = {}


def narrative_for(driver: int, lang: str = "hinglish") -> Dict[str, Any]:
    """Return narrative pack for driver 1-9. Falls back to Hinglish."""
    lang = (lang or "hinglish").lower()
    if lang == "english":
        table = _NARRATIVES_EN
    elif lang == "hindi":
        table = _NARRATIVES_HI
    else:
        table = _NARRATIVES_HG
    n = table.get(driver) or _NARRATIVES_HG.get(driver, {})
    out = dict(n) if n else {}
    # Surface a clean `life_direction` key for renderers (psychology label),
    # while keeping `spiritual_path` as backward-compat alias for older callers.
    if out and "life_direction" not in out and "spiritual_path" in out:
        out["life_direction"] = out["spiritual_path"]
    return out


_NARRATIVES = _NARRATIVES_HG


def life_summary_block(driver: int, conductor: int, name: str,
                       lang: str = "hinglish") -> Dict[str, str]:
    n = narrative_for(driver, lang) or {}
    strengths = n.get("strengths") or [""]
    challenges = n.get("challenges") or [""]
    focus = _pick_extra(lang, _FOCUS_2026_EN, _FOCUS_2026_HI,
                        _FOCUS_2026_HG, driver) or "Self-discovery year."
    from numerology.core.pure_numerology import archetype_for
    return {
        "core_personality": n.get("title", "—"),
        "tagline": n.get("tagline", "—"),
        "biggest_strength": strengths[0] if strengths else "—",
        "biggest_challenge": challenges[0] if challenges else "—",
        "2026_focus": focus,
        "primary_archetype": archetype_for(driver),
        "secondary_archetype": archetype_for(conductor),
        "name_signature": name,
    }


def why_impact_action_for_number(reduced: int, kind: str,
                                 lang: str = "hinglish") -> Dict[str, str]:
    from numerology.core.number_analysis import why_impact_action_for_number as _core_wia
    from numerology.core.digits import number_meaning_for
    out = _core_wia(reduced, kind, lang)
    out["archetype"] = number_meaning_for(reduced)
    out["planet"] = out["archetype"]  # legacy key
    return out


_REL: Dict[int, Dict[int, str]] = {
    1: {1: "T", 2: "F", 3: "F", 4: "E", 5: "N", 6: "E", 7: "E", 8: "E", 9: "F"},
    2: {1: "F", 2: "T", 3: "N", 4: "E", 5: "F", 6: "N", 7: "E", 8: "N", 9: "N"},
    3: {1: "F", 2: "N", 3: "T", 4: "N", 5: "E", 6: "E", 7: "N", 8: "N", 9: "F"},
    4: {1: "E", 2: "E", 3: "N", 4: "T", 5: "F", 6: "F", 7: "N", 8: "F", 9: "E"},
    5: {1: "N", 2: "F", 3: "E", 4: "F", 5: "T", 6: "F", 7: "F", 8: "N", 9: "N"},
    6: {1: "E", 2: "N", 3: "E", 4: "F", 5: "F", 6: "T", 7: "F", 8: "F", 9: "N"},
    7: {1: "E", 2: "E", 3: "N", 4: "N", 5: "F", 6: "F", 7: "T", 8: "F", 9: "E"},
    8: {1: "E", 2: "N", 3: "N", 4: "F", 5: "N", 6: "F", 7: "F", 8: "T", 9: "E"},
    9: {1: "F", 2: "N", 3: "F", 4: "E", 5: "N", 6: "N", 7: "E", 8: "E", 9: "T"},
}
_REL_SCORE = {"T": 95, "F": 80, "N": 60, "E": 30}


def _rel(a: int, b: int) -> str:
    return _REL.get(a, {}).get(b, "N")


def _reduce(n: int) -> int:
    n = abs(int(n))
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


_MONTH_THEMES = {
    1: "New Beginnings — start projects, independent decisions, strengthen networking.",
    2: "Patience + Partnership — listen, collaborate, avoid forcing outcomes.",
    3: "Creativity + Expression — social events, teaching, writing, joy.",
    4: "Hard Work + Foundation — systems, paperwork, steady progress.",
    5: "Change + Movement — travel, new contacts, stay flexible.",
    6: "Love + Family — relationship investment, home projects.",
    7: "Reflection + Research — solo study, postpone big bets.",
    8: "Power + Money — close deals, promotions, discipline.",
    9: "Completion + Release — close chapters, forgive, reset.",
}

_MONTH_THEMES_EN = dict(_MONTH_THEMES)
_MONTH_THEMES_HI = {
    1: "नई शुरुआत — प्रोजेक्ट शुरू करें, स्वतंत्र निर्णय, नेटवर्किंग।",
    2: "धैर्य + साझेदारी — सुनें, सहयोग करें।",
    3: "रचनात्मकता + अभिव्यक्ति — सामाजिक, शिक्षण, लेखन।",
    4: "कड़ी मेहनत + नींव — सिस्टम, कागजी कार्य।",
    5: "परिवर्तन + गति — यात्रा, नए संपर्क, लचीलापन।",
    6: "प्रेम + परिवार — रिश्तों में निवेश, घर परियोजनाएँ।",
    7: "चिंतन + शोध — अकेला अध्ययन, बड़े दांव स्थगित।",
    8: "शक्ति + धन — सौदे, प्रमोशन, अनुशासन।",
    9: "पूर्णता + विमोचन — अध्याय बंद, क्षमा, रीसेट।",
}


def _pick_extra(lang: str, en_dict, hi_dict, hg_dict, key, kind: str = ""):
    lang = (lang or "hinglish").lower()
    if lang == "english":
        flat = f"{key[0]}_{key[1]}" if isinstance(key, tuple) else key
        v = en_dict.get(flat)
        if v is not None:
            return v
    elif lang == "hindi":
        flat = f"{key[0]}_{key[1]}" if isinstance(key, tuple) else key
        v = hi_dict.get(flat)
        if v is not None:
            return v
    return hg_dict.get(key)


def monthly_forecast_pack(driver: int, conductor: int, year: int = 2026,
                          lang: str = "hinglish",
                          dob: str | None = None) -> Dict[str, Any]:
    if dob:
        try:
            _y, _m, _d = (int(x) for x in dob.split("-"))
            personal_year = _reduce(_reduce(_m) + _reduce(_d) + _reduce(year))
        except Exception:
            personal_year = _reduce(driver + conductor + _reduce(year))
    else:
        personal_year = _reduce(driver + conductor + _reduce(year))

    def _theme(pm: int, default: str) -> str:
        return _pick_extra(lang, _MONTH_THEMES_EN, _MONTH_THEMES_HI,
                           _MONTH_THEMES, pm) or default

    months = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i, mname in enumerate(month_names, start=1):
        pm = _reduce(personal_year + i)
        best_dates = [d for d in range(1, 32) if _rel(driver, _reduce(d)) in ("T", "F")]
        months.append({
            "month": mname,
            "personal_month": pm,
            "theme": _theme(pm, "Steady month."),
            "best_dates": best_dates[:5],
            "verdict": "EXCELLENT" if pm in (1, 5, 8) else
                       "GOOD" if pm in (3, 6, 9) else
                       "GENTLE" if pm in (2, 7) else "WORK",
        })
    return {
        "year": year,
        "personal_year": personal_year,
        "year_theme": _theme(personal_year, "Self-growth year."),
        "months": months,
    }


def deep_compatibility_pack(driver: int) -> Dict[str, Any]:
    from numerology.core.digits import number_meaning_for
    from numerology.core.pure_numerology import compat_label
    rows = []
    for n in range(1, 10):
        code = _rel(driver, n)
        base = _REL_SCORE[code]
        love = base + (5 if n in (2, 6) else 0) - (5 if n == 8 else 0)
        marriage = base + (5 if n in (1, 6) else 0) - (10 if n == 7 else 0)
        business = base + (5 if n in (5, 8) else 0) - (5 if n == 7 else 0)
        meaning = number_meaning_for(n)
        rows.append({
            "number": n,
            "archetype": meaning,
            "planet": meaning,  # legacy alias — same as archetype (psychology label)
            "label": compat_label(code),
            "love": max(20, min(100, love)),
            "marriage": max(20, min(100, marriage)),
            "business": max(20, min(100, business)),
        })
    sorted_avg = sorted(rows, key=lambda r: -(r["love"] + r["marriage"] + r["business"]))
    return {
        "driver": driver,
        "rows": rows,
        "top3_best": sorted_avg[:3],
        "top3_worst": sorted_avg[-3:][::-1],
    }


_PRODUCTIVITY_DAY = {
    1: "Sunday", 2: "Monday", 3: "Thursday", 4: "Saturday",
    5: "Wednesday", 6: "Friday", 7: "Tuesday", 8: "Saturday", 9: "Tuesday",
}


def lucky_numbers_pack(driver: int) -> Dict[str, Any]:
    friends = [n for n in range(1, 10) if _rel(driver, n) in ("T", "F")]
    enemies = [n for n in range(1, 10) if _rel(driver, n) == "E"]
    lucky_dates = sorted({d for d in range(1, 32) if _reduce(d) in friends})
    unlucky_dates = sorted({d for d in range(1, 32) if _reduce(d) in enemies})
    lucky_pairs = []
    for tens in range(1, 10):
        for ones in range(0, 10):
            num = tens * 10 + ones
            if _reduce(num) in friends:
                lucky_pairs.append(num)
    lucky_pairs = lucky_pairs[:8]
    fav = friends[0] if friends else driver
    fav2 = friends[1] if len(friends) > 1 else driver
    prod_day = _PRODUCTIVITY_DAY.get(driver, "Monday")
    return {
        "single_digit_lucky": friends,
        "single_digit_avoid": enemies,
        "lucky_dates": lucky_dates,
        "unlucky_dates": unlucky_dates,
        "lucky_double_digit": lucky_pairs,
        "lucky_day": prod_day,
        "atm_pin_tip": f"Choose PIN digits that reduce to {fav} or {fav2}.",
        "account_tip": f"Prefer account suffix digits reducing to {fav}.",
        "lottery_tip": f"Optional: enter contests on {prod_day}; dates {lucky_dates[:3]} align with your number sync.",
    }


def mantras_pack(driver: int) -> Dict[str, Any]:
    from numerology.core.pure_numerology import affirmations_pack
    return affirmations_pack(driver)


_WORKSPACE_FOCUS = {
    1: "Private office with clear sightlines — minimise open-plan noise",
    2: "Calm collaborative corner — whiteboard + 1:1 space nearby",
    3: "Bright creative studio — natural light, walk breaks",
    4: "Structured desk, low-interruption zone",
    5: "Flexible hot-desk near communication tools",
    6: "Client-facing reception aesthetic — comfortable guest seating",
    7: "Minimal low-traffic room — headphones-friendly",
    8: "Executive desk with financial dashboards visible",
    9: "Action layout — standing option, quick ops access",
}

_BEST_BUSINESS_HG = {
    1: ["Founder / CEO ventures", "Luxury goods", "Government contracts", "Personal brand consulting",
        "Media ownership", "Executive coaching"],
    2: ["Hospitality & catering", "Dairy & beverages", "HR / counselling services", "Interior styling",
        "Client care brands", "Wellness hospitality"],
    3: ["Education / coaching", "Publishing & content", "Legal / advisory", "Finance & wealth coaching",
        "HR & mentoring", "Professional training"],
    4: ["IT / SaaS", "Import-export", "Digital platforms", "Fintech / research startups",
        "Electronics", "Innovation consulting"],
    5: ["Marketing agency", "Media & PR", "Sales & brokerage", "Travel & tourism",
        "Communication apps", "Affiliate / commission business"],
    6: ["Fashion & beauty", "Events & weddings", "Hotels & restaurants", "Interior design",
        "Healthcare client experience", "Luxury retail"],
    7: ["Research & analytics", "Writing & film", "Psychology / therapy", "Data science consulting",
        "Museum / knowledge brands", "Solo expert practice"],
    8: ["Real estate & construction", "Banking & insurance", "Heavy logistics", "Manufacturing ops",
        "Asset management", "Infrastructure services"],
    9: ["Sports & fitness", "Defence & security services", "Engineering & manufacturing",
        "Emergency medicine adjacent", "Motivational training", "High-intensity ops"],
}
_BEST_BUSINESS_EN = _BEST_BUSINESS_HG
_BEST_BUSINESS_HI = {
    1: ["संस्थापक / सीईओ उद्यम", "लक्जरी वस्तुएँ", "सरकारी ठेके", "व्यक्तिगत ब्रांड परामर्श",
        "मीडिया स्वामित्व", "कार्यकारी कोचिंग"],
    2: ["आतिथ्य और खानपान", "डेयरी और पेय", "एचआर / परामर्श", "इंटीरियर स्टाइलिंग",
        "क्लाइंट केयर ब्रांड", "वेलनेस आतिथ्य"],
    3: ["शिक्षा / कोचिंग", "प्रकाशन और कंटेंट", "विधिक / सलाह", "वित्त कोचिंग",
        "एचआर और मेंटरिंग", "प्रोफेशनल प्रशिक्षण"],
    4: ["आईटी / SaaS", "आयात-निर्यात", "डिजिटल प्लेटफ़ॉर्म", "फिनटेक / रिसर्च स्टार्टअप",
        "इलेक्ट्रॉनिक्स", "इनोवेशन परामर्श"],
    5: ["मार्केटिंग एजेंसी", "मीडिया और पीआर", "बिक्री और ब्रोकरेज", "यात्रा और पर्यटन",
        "संचार ऐप्स", "कमीशन व्यवसाय"],
    6: ["फैशन और सौंदर्य", "इवेंट और विवाह", "होटल और रेस्तरां", "इंटीरियर डिजाइन",
        "हेल्थकेयर क्लाइंट अनुभव", "लक्जरी रिटेल"],
    7: ["शोध और विश्लेषण", "लेखन और फिल्म", "मनोविज्ञान / थेरेपी", "डेटा साइंस परामर्श",
        "ज्ञान ब्रांड", "एकल विशेषज्ञ अभ्यास"],
    8: ["रियल एस्टेट और निर्माण", "बैंकिंग और बीमा", "भारी लॉजिस्टिक्स", "विनिर्माण संचालन",
        "संपत्ति प्रबंधन", "इंफ्रास्ट्रक्चर सेवाएँ"],
    9: ["खेल और फिटनेस", "रक्षा और सुरक्षा", "इंजीनियरिंग और विनिर्माण",
        "आपात चिकित्सा-संबद्ध", "प्रेरक प्रशिक्षण", "उच्च-तीव्रता संचालन"],
}


def business_launch_pack(driver: int, year: int = 2026,
                         lang: str = "hinglish") -> Dict[str, Any]:
    forecast = monthly_forecast_pack(driver, driver, year)
    best_months = [m for m in forecast["months"] if m["verdict"] in ("EXCELLENT", "GOOD")][:6]
    friends = [n for n in range(1, 10) if _rel(driver, n) in ("T", "F")]
    name_numbers = friends[:3] or [driver]
    lmap = (lang or "hinglish").lower()
    biz = (_BEST_BUSINESS_EN if lmap == "english" else
           _BEST_BUSINESS_HI if lmap == "hindi" else _BEST_BUSINESS_HG).get(driver, [])
    from numerology.core.digits import number_meaning_for
    arch = number_meaning_for(driver)
    if lmap == "english":
        name_tip = (f"Align brand name to reduce to {name_numbers[0]} or "
                    f"{name_numbers[1] if len(name_numbers) > 1 else name_numbers[0]} (Chaldean).")
        logo_tip = f"Use {arch}-aligned colours in logo and UI."
        invoice_tip = f"Start first invoice from {name_numbers[0]} or master 11/22."
    elif lmap == "hindi":
        name_tip = (f"ब्रांड नाम {name_numbers[0]} या "
                    f"{name_numbers[1] if len(name_numbers) > 1 else name_numbers[0]} पर रिड्यूस हो (चाल्डियन)।")
        logo_tip = f"लोगो में {arch}-संगत रंग।"
        invoice_tip = f"पहला इनवॉइस {name_numbers[0]} या 11/22 से।"
    else:
        name_tip = (f"Brand name reduce {name_numbers[0]} ya "
                    f"{name_numbers[1] if len(name_numbers) > 1 else name_numbers[0]} (Chaldean).")
        logo_tip = f"Logo me {arch}-aligned colours."
        invoice_tip = f"Pehla invoice {name_numbers[0]} ya 11/22 se."
    return {
        "driver": driver,
        "workspace_focus": _WORKSPACE_FOCUS.get(driver, "Quiet dedicated desk"),
        "best_launch_months": [{"month": m["month"], "verdict": m["verdict"]} for m in best_months],
        "best_business_types": biz,
        "best_company_name_numbers": name_numbers,
        "best_partner_numbers": name_numbers,
        "avoid_partner_numbers": [n for n in range(1, 10) if _rel(driver, n) == "E"],
        "name_tip": name_tip,
        "logo_tip": logo_tip,
        "registration_day": _PRODUCTIVITY_DAY.get(driver, "Monday"),
        "first_invoice_tip": invoice_tip,
    }


_CELEBRITY_MATCH: Dict[int, List[Dict[str, str]]] = {
    1: [
        {"name": "Mukesh Ambani", "born": "19 April", "lesson": "Vision + calculated risk — empire from scratch."},
        {"name": "Lata Mangeshkar", "born": "28 September", "lesson": "Solo excellence — one craft, decades of mastery."},
        {"name": "Ratan Tata", "born": "28 December", "lesson": "Quiet authority + ethics in leadership."},
        {"name": "Bill Gates", "born": "28 October", "lesson": "Innovation paired with long-term purpose."},
    ],
    2: [
        {"name": "Shahrukh Khan", "born": "2 November", "lesson": "Charm + emotional intelligence in public life."},
        {"name": "Amitabh Bachchan", "born": "11 October", "lesson": "Reinvention across generations."},
        {"name": "Mahatma Gandhi", "born": "2 October", "lesson": "Soft power and listening as strength."},
    ],
    3: [
        {"name": "Rajinikanth", "born": "12 December", "lesson": "Authentic style — fame without losing self."},
        {"name": "Anushka Sharma", "born": "1 May", "lesson": "Multi-role expansion — actor, producer, founder."},
    ],
    4: [
        {"name": "Barack Obama", "born": "4 August", "lesson": "Disruption with structure — change from inside."},
    ],
    5: [
        {"name": "Virat Kohli", "born": "5 November", "lesson": "Aggression + adaptability across formats."},
        {"name": "Aamir Khan", "born": "14 March", "lesson": "Versatility + perfectionism."},
        {"name": "Mark Zuckerberg", "born": "14 May", "lesson": "Communication as business moat."},
        {"name": "Albert Einstein", "born": "14 March", "lesson": "Curiosity + intellectual courage."},
    ],
    6: [
        {"name": "Sachin Tendulkar", "born": "24 April", "lesson": "Consistency over flash — long-game craft."},
        {"name": "A.R. Rahman", "born": "6 January", "lesson": "Art + discipline — daily practice at scale."},
        {"name": "Steve Jobs", "born": "24 February", "lesson": "Design obsession as product strategy."},
        {"name": "A.P.J. Kalam", "born": "15 October", "lesson": "Service + humility with influence."},
    ],
    7: [
        {"name": "M.S. Dhoni", "born": "7 July", "lesson": "Calm under pressure — clarity in chaos."},
    ],
    8: [
        {"name": "Narendra Modi", "born": "17 September", "lesson": "Discipline + long-game political stamina."},
        {"name": "Saurav Ganguly", "born": "8 July", "lesson": "Authority + comeback mindset."},
        {"name": "Roger Federer", "born": "8 August", "lesson": "Longevity through structure and recovery."},
    ],
    9: [
        {"name": "Salman Khan", "born": "27 December", "lesson": "Raw energy + loyalty to inner circle."},
        {"name": "Akshay Kumar", "born": "9 September", "lesson": "Discipline + action — early starts, zero drama."},
    ],
}


def celebrity_match_pack(driver: int) -> List[Dict[str, str]]:
    return _CELEBRITY_MATCH.get(driver, [])


def lucky_colours_pack(driver: int, lang: str = "hinglish") -> Dict[str, Any]:
    from numerology.core.colours import lucky_colours_pack as _core_lc
    return _core_lc(driver, lang)


_FOCUS_2026_HG = {
    1: "Independent venture launch — apna initiative start karo. Authority figures se clear boundaries.",
    2: "Emotional boundaries strong karo. Sleep aur stress hygiene priority.",
    3: "Teaching/writing se income stream. Certification ya upskilling consider karo.",
    4: "Tech/foreign opportunities capture karo. Ek field me depth — job-hop band.",
    5: "Multiple income streams. Communication business expand.",
    6: "Family + creative projects balance. Pending relationship decision lo.",
    7: "Deep research + solo clarity time. Practical admin mat ignore karo.",
    8: "Foundation work slow-steady. Assets build. Father/authority bond heal.",
    9: "Anger ko sport/exercise me channel karo. Big relocation possible.",
}
_FOCUS_2026_EN = {
    1: "Launch an independent venture. Set clear boundaries with authority figures.",
    2: "Strengthen emotional boundaries. Prioritise sleep and stress hygiene.",
    3: "Build income from teaching or writing. Consider certification or upskilling.",
    4: "Capture tech or foreign opportunities. Go deep in one field — stop job-hopping.",
    5: "Crystallise multiple income streams. Expand communication-based business.",
    6: "Balance family and creative projects. Make a pending relationship decision.",
    7: "Deep research plus solo clarity time. Do not ignore practical admin.",
    8: "Slow-steady foundation work. Build assets. Heal father or authority bond.",
    9: "Channel anger into sport or exercise. A big move is possible.",
}
_FOCUS_2026_HI = {
    1: "स्वतंत्र उद्यम शुरू करें। प्राधिकरण के साथ स्पष्ट सीमाएँ।",
    2: "भावनात्मक सीमाएँ मजबूत करें। नींद और तनाव स्वच्छता प्राथमिकता।",
    3: "शिक्षण/लेखन से आय। प्रमाणन या अपस्किलिंग।",
    4: "तकनीकी/विदेशी अवसर। एक क्षेत्र में गहराई।",
    5: "कई आय स्रोत। संचार व्यवसाय विस्तार।",
    6: "परिवार + रचनात्मक संतुलन। लंबित संबंध निर्णय।",
    7: "गहन शोध + एकांत स्पष्टता। व्यावहारिक कार्य न neglect।",
    8: "धीमी-स्थिर नींव। संपत्ति निर्माण।",
    9: "क्रोध को व्यायाम में channel। बड़ा स्थानांतरण संभव।",
}
