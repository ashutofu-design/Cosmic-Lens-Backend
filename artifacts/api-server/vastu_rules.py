"""
Classical Vastu Shastra rule database for Cosmic Vastu Drishti.

Each rule cites the classical source it comes from so the LLM can reference
authoritative texts in its analysis. Sources used:
  - Brihat Samhita (Varahmihir, ~6th c. CE, Ch. 53 "Vastu Vidya")
  - Mayamatam (Maya, ~9th c. CE, esp. Ch. 9-15)
  - Manasara (~7th c. CE, Ch. 30-36)
  - Vastu Shastra (classical compilation)
  - Samarangana Sutradhara (Bhoja, 11th c.)

The rule set is intentionally curated — high-signal, room-specific rules a
real Vastu consultant would apply. Not exhaustive (Vastu has thousands of
sub-rules); this is the high-impact ~80% that drives most home consultations.
"""

# ── Direction reference ──────────────────────────────────────────────────────
# Vastu uses 8 + 1 directions — 4 cardinal + 4 inter-cardinal + center (Brahmasthan)
DIRECTIONS = {
    "N":   {"name": "North",     "deity": "Kubera",  "element": "Vayu",    "domain": "Wealth, opportunities"},
    "NE":  {"name": "North-East", "deity": "Ishaan",  "element": "Jal",     "domain": "Spirituality, clarity, divine energy"},
    "E":   {"name": "East",      "deity": "Surya",   "element": "Vayu",    "domain": "Vitality, social standing, growth"},
    "SE":  {"name": "South-East", "deity": "Agni",    "element": "Agni",    "domain": "Fire, energy, finance"},
    "S":   {"name": "South",     "deity": "Yama",    "element": "Prithvi", "domain": "Strength, fame, longevity"},
    "SW":  {"name": "South-West", "deity": "Niriti",  "element": "Prithvi", "domain": "Stability, relationships, ancestors"},
    "W":   {"name": "West",      "deity": "Varuna",  "element": "Jal",     "domain": "Gains, profits, completion"},
    "NW":  {"name": "North-West", "deity": "Vayu",    "element": "Vayu",    "domain": "Travel, networking, change"},
    "C":   {"name": "Center (Brahmasthan)", "deity": "Brahma", "element": "Akash", "domain": "Cosmic core — must remain open & clean"},
}


# ── General rules (apply to every space) ──────────────────────────────────────
GENERAL_RULES = [
    {
        "rule": "The Brahmasthan (center of the room/home) must remain unobstructed and clutter-free. Heavy furniture, beams, or storage at the center disrupts the cosmic energy core.",
        "source": "Mayamatam Ch. 7; Brihat Samhita 53.5",
        "severity": "major",
    },
    {
        "rule": "Sharp corners or beams pointing at sleeping/sitting positions create 'Vastu vedha' (energy piercing) and disturb mental peace.",
        "source": "Vastu Shastra; Samarangana Sutradhara",
        "severity": "moderate",
    },
    {
        "rule": "NE (Ishaan) corner is the most sacred zone — should be light, open, clean, and ideally hold a water source or pooja space. Heavy storage, toilet, or kitchen here is a major dosh.",
        "source": "Brihat Samhita 53.18; Mayamatam Ch. 9",
        "severity": "major",
    },
    {
        "rule": "SW (Nairutya) corner must be the heaviest zone — anchors stability. Master bedroom, heavy almirah, or storage belongs here.",
        "source": "Brihat Samhita 53.20; Manasara Ch. 30",
        "severity": "moderate",
    },
    {
        "rule": "Floor should slope gently from SW to NE — water (energy) flows toward the divine corner. Reverse slope drains prosperity.",
        "source": "Vastu Shastra; Mayamatam",
        "severity": "moderate",
    },
    {
        "rule": "Cracks in walls, peeling paint, broken glass, or damaged furniture trap negative energy ('apvaad shakti'). Repair immediately.",
        "source": "Brihat Samhita; classical compilations",
        "severity": "moderate",
    },
    {
        "rule": "Mirrors should never face beds, the front door, or each other. Mirror reflections multiply energy — including negative energy.",
        "source": "Vastu Shastra",
        "severity": "moderate",
    },
    {
        "rule": "Clutter, dust, and unused items block prana (life force) flow. Clean, organized spaces are non-negotiable for positive Vastu.",
        "source": "Mayamatam; Vastu Shastra",
        "severity": "minor",
    },
    {
        "rule": "Adequate natural light from E or NE windows is auspicious — Surya's rays purify the space each morning.",
        "source": "Brihat Samhita 53.12",
        "severity": "minor",
    },
    {
        "rule": "Indoor plants in N, E, or NE bring positive energy. Avoid thorny plants (cactus, bonsai) indoors as they generate Vastu dosh.",
        "source": "Vastu Shastra",
        "severity": "minor",
    },
]


# ── Room-specific rules ───────────────────────────────────────────────────────
ROOM_RULES = {
    "bedroom": [
        {"rule": "Master bedroom should ideally be in the SW (Nairutya) corner — provides stability, deep sleep, strong relationships.", "source": "Brihat Samhita 53.42; Mayamatam Ch. 14", "severity": "major"},
        {"rule": "Bed should be placed against the South or West wall. Head should point South (preferred), East, or West while sleeping — NEVER North (causes disturbed sleep, health issues).", "source": "Brihat Samhita 53.45", "severity": "major"},
        {"rule": "Mirror must NOT face the bed. Reflection of sleeping body causes 'pratibimb dosh' — leads to nightmares, marital discord, health issues.", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "TV, electronics, or computers in bedroom should be covered when not in use. Active screens disrupt sleep aura.", "source": "Modern Vastu adaptation", "severity": "minor"},
        {"rule": "No beam (overhead structural element) should run directly above the bed — causes pressure on the sleeper, headaches, anxiety.", "source": "Samarangana Sutradhara", "severity": "moderate"},
        {"rule": "Pooja space, idols, or religious images should NOT be inside the bedroom. Sacred energy and conjugal energy should be separated.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Bedroom door should NOT directly face the bed (foot pointing toward door = 'death position' in classical Vastu).", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Almirahs/heavy storage best placed along South or West walls. Avoid heavy furniture in NE.", "source": "Mayamatam", "severity": "moderate"},
        {"rule": "Color palette: soft pastels (light pink, peach, light green, cream, light blue). Avoid stark black, deep red, dark grey for bedroom walls.", "source": "Vastu Shastra colour guidance", "severity": "minor"},
        {"rule": "No water features (fountain, fish tank) in bedroom — water + sleep direction creates emotional turbulence.", "source": "Vastu Shastra", "severity": "minor"},
    ],
    "kitchen": [
        {"rule": "Kitchen should be in the SE (Agni) corner of the home — Agni Devta's domain, fire element naturally aligned.", "source": "Brihat Samhita 53.28; Mayamatam Ch. 11", "severity": "major"},
        {"rule": "If SE not possible, NW is the next acceptable location. NEVER place kitchen in NE (extinguishes spiritual fire) or SW (instability).", "source": "Brihat Samhita 53.30", "severity": "major"},
        {"rule": "Cooking stove must be placed in SE corner of the kitchen. Cook MUST face East while cooking — invokes Surya energy into food.", "source": "Mayamatam; Brihat Samhita", "severity": "major"},
        {"rule": "Sink (water) and stove (fire) must NEVER be adjacent or facing each other. Maintain at least 3 ft separation OR a barrier between them — water-fire conflict creates marital discord and financial loss.", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "Refrigerator best placed in SW or W. Avoid NE for refrigerator.", "source": "Modern Vastu adaptation", "severity": "minor"},
        {"rule": "Drinking water pot/filter should be in NE corner of the kitchen.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Storage of grains, pulses, oil — in S or W cabinets (SW area best for heavy storage).", "source": "Mayamatam", "severity": "minor"},
        {"rule": "Kitchen must have a window or exhaust on the East wall — for fresh air and to release Agni's smoke.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Avoid black colour dominantly in kitchen. Yellow, orange, red, light brown are auspicious — invoke Agni element.", "source": "Vastu Shastra colour guidance", "severity": "minor"},
        {"rule": "Toilet adjacent to kitchen wall is a major dosh — bacteria and Vastu energies clash.", "source": "Vastu Shastra", "severity": "major"},
    ],
    "pooja room": [
        {"rule": "Pooja room MUST be in NE (Ishaan) corner — meeting point of Surya and Brahma energies.", "source": "Brihat Samhita 53.18; Mayamatam Ch. 9", "severity": "major"},
        {"rule": "If NE not possible, E or N. NEVER place pooja in S, SE, SW, or under a staircase.", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "Idols/deities should face West so the devotee faces East while praying. Surya's rays then fall on the idol from behind the devotee.", "source": "Brihat Samhita; Mayamatam", "severity": "major"},
        {"rule": "Idols should NOT face each other. Place all in a row facing the same direction.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "No broken or chipped idols — discard respectfully (immerse in flowing water). Damaged idols invite negative energy.", "source": "Classical scriptural guidance", "severity": "major"},
        {"rule": "Pooja room should NOT be under a bedroom on the floor above — feet of sleepers point down at deities.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Toilet must NEVER share a wall with pooja room.", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "Idols above 9 inches tall NOT recommended in home pooja — temple-grade idols need temple-grade rituals.", "source": "Agama Shastra; Vastu Shastra", "severity": "minor"},
        {"rule": "Pooja space should be elevated — never directly on the floor. A wooden or marble platform is ideal.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Door of pooja room should ideally be in N or E wall.", "source": "Mayamatam", "severity": "moderate"},
    ],
    "living room": [
        {"rule": "Living/drawing room is best in N, E, or NE — these are zones of social energy, communication, and growth.", "source": "Brihat Samhita; Mayamatam", "severity": "moderate"},
        {"rule": "Head of household should sit facing East or North while in the living room — for authority and clarity in conversations.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Heavy furniture (sofa sets, large showcase) along S and W walls. NE corner should be open / hold a water feature, plant, or display of light items.", "source": "Mayamatam", "severity": "moderate"},
        {"rule": "TV/electronics in SE corner of living room (Agni domain — fits the electrical fire energy).", "source": "Modern Vastu adaptation", "severity": "minor"},
        {"rule": "Aquarium or small water fountain in N or NE corner is highly auspicious — invokes Kubera and divine prosperity.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Avoid hanging images of war, sadness, decay, or wild animals in living room — sets negative tone for the house.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Family photos best on S or W wall. Photos of deceased ancestors should be on S wall, never E or N.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Clocks should be on N or E walls for auspicious time-energy alignment.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Living room ceiling should be lighter in colour than the walls — keeps energy uplifted.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Curtains should be light, breathable colours in NE-facing windows; heavier in S/W to control afternoon Yama-energy.", "source": "Vastu Shastra", "severity": "minor"},
    ],
    "main door": [
        {"rule": "Main entrance facing N, E, NE, or W is auspicious. NE is most divine. SW-facing main door is a major dosh (invites instability).", "source": "Brihat Samhita 53.10; Mayamatam Ch. 8", "severity": "major"},
        {"rule": "Main door should be the LARGEST door in the house — establishes it as the primary energy intake.", "source": "Mayamatam", "severity": "moderate"},
        {"rule": "Door should open INWARD and clockwise — invites prana into the home.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "No shoe rack, dustbin, or broken items at the entrance. First impression of energy entering must be clean.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Threshold (chaukhat) should always be present — symbolises the boundary between outer and inner energy fields.", "source": "Brihat Samhita; Mayamatam", "severity": "moderate"},
        {"rule": "Toran (decorative archway) of mango leaves, flowers, or auspicious symbols above the door is recommended.", "source": "Classical tradition", "severity": "minor"},
        {"rule": "No cracks, peeling paint, or squeaking hinges on main door — these are direct energy leaks.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Avoid placing a mirror directly opposite the main door — reflects entering positive energy back out.", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "Two-shutter (double) doors generally more auspicious than single-shutter for main entrance.", "source": "Mayamatam", "severity": "minor"},
        {"rule": "Nameplate, Ganesh idol or Om symbol on or near main door is highly recommended.", "source": "Classical tradition", "severity": "minor"},
    ],
    "bathroom": [
        {"rule": "Bathroom/toilet best in NW or W. SE is acceptable. NEVER in NE (cancels divine energy) or SW (destabilises the home).", "source": "Brihat Samhita; Mayamatam", "severity": "major"},
        {"rule": "Toilet seat should face N-S axis (so user faces N or S). Never E-W (disturbs solar alignment).", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Bathroom door should remain CLOSED at all times to contain dispersing energy.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Drainage / outflow ideally to N or E direction.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Bathroom ABOVE pooja room or kitchen on the floor above is a major dosh.", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "Adequate ventilation via window or exhaust is mandatory — stale energy must escape daily.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "No mirror facing toilet directly. Mirror should be on N or E wall.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Use light colors — white, light blue, light green. Avoid deep red, black for bathrooms.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Keep bathroom dry — wet floors trap stagnant energy.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Salt bowl in a corner absorbs accumulated negative energy — replace weekly.", "source": "Practical Vastu remedy", "severity": "minor"},
    ],
    "study room": [
        {"rule": "Study room ideally in W, NW, or NE. Student should face E or N while studying — stimulates concentration and memory.", "source": "Brihat Samhita 53.35; Vastu Shastra", "severity": "major"},
        {"rule": "Study table should NOT be against a wall directly — leave breathing space behind for energy flow. If touching wall, then East or North wall.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Door should be visible from study seat (do not sit with back to door) — psychological + energetic alertness.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Bookshelves on E, N, NE walls. Avoid heavy bookshelves in NE corner itself (open zone preferred).", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Saraswati image, idol, or yantra on E or NE wall promotes academic success.", "source": "Vastu Shastra; tradition", "severity": "minor"},
        {"rule": "Light, focused desk lamp from SE is ideal — Agni's energy aids focused work.", "source": "Vastu Shastra adaptation", "severity": "minor"},
        {"rule": "Avoid clutter on study desk — directly correlates with mental clutter.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Wall colors: light yellow, cream, soft green stimulate focus. Avoid red (over-stimulating) or dark grey.", "source": "Vastu Shastra colour guidance", "severity": "minor"},
        {"rule": "Globe in NW corner aids in goals related to travel/foreign opportunities.", "source": "Modern Vastu adaptation", "severity": "minor"},
        {"rule": "No mirror in front of study desk — distracts and reflects effort outward.", "source": "Vastu Shastra", "severity": "minor"},
    ],
    "office": [
        {"rule": "Owner/manager seat in SW corner facing N or E — projects authority, control, decisive thinking.", "source": "Brihat Samhita; Mayamatam", "severity": "major"},
        {"rule": "Employees / juniors face N or E while working. Cash counter / safe in N (Kubera direction).", "source": "Vastu Shastra", "severity": "major"},
        {"rule": "Sales/marketing teams ideally seated in NW (Vayu — networking, movement).", "source": "Modern Vastu adaptation", "severity": "minor"},
        {"rule": "Reception in NE or N — first welcoming energy zone for clients.", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Office main door in N, E, or NE most auspicious for business growth.", "source": "Brihat Samhita 53.10", "severity": "major"},
        {"rule": "Solid wall behind owner's chair (no glass, no door) — for support and stability ('parvat back').", "source": "Vastu Shastra", "severity": "moderate"},
        {"rule": "Avoid beams overhead at any seat — causes pressure, headaches, employee turnover.", "source": "Samarangana Sutradhara", "severity": "moderate"},
        {"rule": "Conference room in NW — discussions and decisions flow well in this air-element zone.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Plants in N and E corners. Avoid thorny plants in office.", "source": "Vastu Shastra", "severity": "minor"},
        {"rule": "Wealth corner of office (N) should hold a Kubera yantra, fish tank, or growth-symbolising decor.", "source": "Vastu Shastra; tradition", "severity": "minor"},
    ],
    "room": [],  # generic catch-all
}


# ── Public helpers ────────────────────────────────────────────────────────────
def get_relevant_rules(room_type: str) -> dict:
    """
    Return all rules relevant to a given room.

    Returns:
      {
        "general":    list of general rules (always applied),
        "room":       list of room-specific rules,
        "directions": directions reference dict (deity, element, domain),
      }
    """
    key = (room_type or "").strip().lower()
    room_rules = ROOM_RULES.get(key, ROOM_RULES.get("room", []))
    return {
        "general":    GENERAL_RULES,
        "room":       room_rules,
        "directions": DIRECTIONS,
    }


def format_rules_for_prompt(room_type: str) -> str:
    """
    Render the rule set as a clean reference block to inject into the LLM
    prompt. Keeps source citations so the model can attribute each
    observation to a classical text.
    """
    bundle = get_relevant_rules(room_type)
    lines: list[str] = []

    lines.append("=== DIRECTIONAL REFERENCE (8 + 1 directions) ===")
    for code, d in bundle["directions"].items():
        lines.append(f"  {code:3s} ({d['name']:24s}) — Deity: {d['deity']:8s} | Element: {d['element']:8s} | Domain: {d['domain']}")

    lines.append("")
    lines.append("=== GENERAL VASTU RULES (apply to every space) ===")
    for i, r in enumerate(bundle["general"], 1):
        lines.append(f"  G{i}. [{r['severity'].upper()}] {r['rule']}")
        lines.append(f"      Source: {r['source']}")

    if bundle["room"]:
        lines.append("")
        lines.append(f"=== ROOM-SPECIFIC RULES ({room_type.upper()}) ===")
        for i, r in enumerate(bundle["room"], 1):
            lines.append(f"  R{i}. [{r['severity'].upper()}] {r['rule']}")
            lines.append(f"      Source: {r['source']}")

    return "\n".join(lines)


def heading_to_direction(heading_deg: float | None) -> str:
    """Convert a compass heading in degrees (0-360) to one of the 8 directions."""
    if heading_deg is None:
        return "unknown"
    h = float(heading_deg) % 360
    # 8 sectors of 45° each, centered on each direction
    sectors = [
        (337.5, 360.0, "N"), (0.0, 22.5, "N"),
        (22.5, 67.5, "NE"),
        (67.5, 112.5, "E"),
        (112.5, 157.5, "SE"),
        (157.5, 202.5, "S"),
        (202.5, 247.5, "SW"),
        (247.5, 292.5, "W"),
        (292.5, 337.5, "NW"),
    ]
    for lo, hi, name in sectors:
        if lo <= h < hi:
            return name
    return "N"
