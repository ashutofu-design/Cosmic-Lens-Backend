"""treatment_playbook.py
═════════════════════════════════════════════════════════════════════════════
COSMIC LENS — Emotional Treatment Playbook (cross-engine).

Maps (emotional_tone × domain) → delivery directives so the SAME engine
facts get presented with the RIGHT human treatment — empathetic for grief,
practical for confusion, energising for hope, safety-first for fear.

Single source of truth for brand voice + per-tone phrasing rules. Consumed
by:
  • openai_helper._build_wealth_structured_system_prompt  (structured path)
  • openai_helper._validate_wealth_payload                (ban-list guard)
  • openai_helper._stitch_structured_narrative            (weaver)
  • Future: career / love / health / marriage structured paths
═════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

# Tones recognised by AI Ear (intent_extractor.EMOTIONAL_TONES).
TONES = (
    "anxious", "curious", "desperate", "hopeful", "neutral",
    "conflicted", "grieving", "angry", "skeptical",
)

# Domains recognised by AI Ear (subset that matters for empathy treatment).
DOMAINS = (
    "wealth", "career", "marriage", "love", "health",
    "education", "legal", "family", "general",
)

# AI Ear's `domain` enum is wider than the playbook taxonomy. Map every
# extra AI-Ear value to the closest playbook domain so empathy treatment
# never silently falls through to "general" (which has no hard rules).
# See intent_extractor.DOMAINS for the full source enum.
_DOMAIN_ALIAS: dict[str, str] = {
    # Direct synonyms / spelling variants
    "litigation": "legal",
    "court":      "legal",
    "law":        "legal",
    # Finance-adjacent → wealth (kept SEPARATE from career/marriage)
    "stock":      "wealth",
    "finance":    "wealth",
    "money":      "wealth",
    "property":   "wealth",
    "real_estate":"wealth",
    # Family-adjacent
    "child":      "family",
    "children":   "family",
    "kids":       "family",
    "parent":     "family",
    "parents":    "family",
    # Soft / non-prescriptive domains → general (curious / curious cell ok)
    "remedy":     "general",
    "spiritual":  "general",
    "vehicle":    "general",
    "vastu":      "general",
    "travel":     "general",
}


def canonical_domain(domain: str | None) -> str:
    """Map any AI-Ear domain value to a playbook-supported domain.

    Unknown / missing inputs collapse to "general".  Already-canonical
    inputs are returned unchanged.  Always returns a member of DOMAINS."""
    if not isinstance(domain, str) or not domain.strip():
        return "general"
    d = domain.strip().lower()
    if d in DOMAINS:
        return d
    return _DOMAIN_ALIAS.get(d, "general")


def canonical_tone(tone: str | None) -> str:
    """Same idea for tones — anything off-vocab → 'neutral'."""
    if not isinstance(tone, str) or not tone.strip():
        return "neutral"
    t = tone.strip().lower()
    return t if t in TONES else "neutral"

# ─────────────────────────────────────────────────────────────────────────────
# BRAND-VOICE BAN LIST (cliché empathy + AI-leak words)
# ─────────────────────────────────────────────────────────────────────────────
# These phrases sound either condescending, AI-canned, or fake-soothing. They
# break the "asli astrologer" feel. Validator rejects any payload that uses
# them in empathy_open / human_close.
BANNED_EMPATHY_PHRASES: tuple[str, ...] = (
    # Generic AI-canned empathy
    "main samajh sakta hoon",
    "i understand your pain",
    "i feel your pain",
    "i can imagine how",
    "i'm so sorry to hear",
    "as an ai",
    "as a language model",
    # Hollow Hinglish reassurance
    "tension mat lo",
    "tension mat lijiye",
    "chinta mat karo",
    "chinta mat kariye",
    "sab theek ho jaayega",
    "sab kuch theek ho jaayega",
    "sab acha hoga",
    "sab achha hoga",
    "khush rahein",
    "hamesha khush rahein",
    "positive raho",
    "be positive",
    "positive vibes",
    # Dismissive "you're not alone"-style platitudes when overused
    "aap akele nahi ho",
    "aap akele nahi hain",
    "you are not alone",
    # Guru-speak that sounds preachy
    "beta,",
    "bachcha,",
    "putra,",
    "puttar,",
    "my dear",
    "my child",
    # Fake astrology hype
    "destiny ke saath",
    "kismat aapke saath",
    "stars are aligning",
    "universe aapke saath",
)

# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN HARD-RULES (override any tone — non-negotiable safety)
# ─────────────────────────────────────────────────────────────────────────────
DOMAIN_HARD_RULES: dict[str, tuple[str, ...]] = {
    "wealth": (
        "NEVER predict specific rupee amounts (lakh / crore / package / salary).",
        "NEVER advise loan-default, EMI-skip, tax-evasion, or GST-fraud.",
        "NEVER endorse lottery / satta / matka / KBC / jackpot.",
        "ALWAYS recommend CA or SEBI-registered advisor consult.",
    ),
    "health": (
        "NEVER predict death, terminal illness, or surgery outcome.",
        "NEVER replace medical advice — ALWAYS recommend qualified doctor.",
        "For mental-health distress, surface helpline (iCall / Vandrevala / KIRAN 1800-599-0019).",
    ),
    "marriage": (
        "NEVER pressure 'compromise karo' or shame the user.",
        "NEVER predict divorce or affair as a fact — speak in possibility, never finality.",
        "Patience-first framing for delays.",
    ),
    "love": (
        "NEVER promise a specific person will return / commit / marry.",
        "Validate feelings first, then realistic framing.",
    ),
    "career": (
        "NEVER promise specific job offers, package figures, or company names.",
        "Action-oriented; encourage skill-building over fatalism.",
    ),
    "legal": (
        "NEVER promise 'you will win' or predict court verdict.",
        "ALWAYS recommend lawyer consult.",
    ),
    "education": (
        "NEVER predict exam result with certainty.",
        "Growth-mindset framing; effort over fate.",
    ),
    "family": (
        "Empathy-first; never blame any specific family member.",
    ),
    "general": (),
}

# ─────────────────────────────────────────────────────────────────────────────
# TREATMENT MATRIX  (tone × domain → directive bundle)
# ─────────────────────────────────────────────────────────────────────────────
# Each cell defines:
#   opening_style — instruction for the empathy_open line (≤25 words)
#   closing_style — instruction for the human_close line (≤25 words)
#   cadence       — "flowing"|"clinical"|"gentle"|"direct" — affects bullet
#                   density in the narrative
#
# Tone-default treatments are defined first; domain × tone overrides only
# where the default doesn't fit (e.g. anxious-health needs more caution
# than anxious-wealth).

_TONE_DEFAULTS: dict[str, dict[str, str]] = {
    "anxious": {
        "opening_style": (
            "Acknowledge the worry by NAMING the specific concern from the question "
            "(e.g. 'paisa nahi ruk raha — yeh thakawat samajh aati hai'). 1 sentence. "
            "Validate without minimising. Do NOT use generic 'main samajh sakta hoon'."
        ),
        "closing_style": (
            "Reframe the situation as a *phase / discipline-building chapter*, not a sentence. "
            "End with quiet agency — 1 sentence. No fake hope, no 'sab theek hoga'."
        ),
        "cadence": "flowing",
    },
    "hopeful": {
        "opening_style": (
            "Match the user's energy in 1 sentence — acknowledge the positive intent "
            "(e.g. 'achha mood me sawal poochha hai') without flattery."
        ),
        "closing_style": (
            "Channel the hope into a SPECIFIC discipline / habit (1 sentence). "
            "Temper without dampening — 'isi flow ko routine bana lo' style."
        ),
        "cadence": "flowing",
    },
    "curious": {
        "opening_style": (
            "Light, friendly opener — 1 short sentence. Almost playful. "
            "No heavy empathy — the user is exploring, not hurting."
        ),
        "closing_style": (
            "End with a small actionable nudge or follow-up suggestion — 1 sentence."
        ),
        "cadence": "direct",
    },
    "neutral": {
        "opening_style": (
            "1 short sentence — direct framing of the answer. "
            "Skip explicit empathy; user wants information, not warmth."
        ),
        "closing_style": (
            "1 brief grounding line — practical, no over-soft."
        ),
        "cadence": "direct",
    },
    "desperate": {
        "opening_style": (
            "Slow down. Acknowledge the WEIGHT of the situation in 1 sentence "
            "(e.g. 'samajh aata hai abhi raasta dhundhna mushkil lag raha hai'). "
            "No bullet-point energy. Soften the cadence."
        ),
        "closing_style": (
            "End with a SINGLE small concrete step the user can take TODAY — "
            "tiny, doable, removes overwhelm. 1 sentence."
        ),
        "cadence": "gentle",
    },
    "conflicted": {
        "opening_style": (
            "Name the dilemma in 1 sentence (e.g. 'do raaste samne hain, dono valid lagte hain'). "
            "Validate that confusion is rational here, not weakness."
        ),
        "closing_style": (
            "End with a CLARIFYING question or a 'first decide X, then Y will become clear' framing. "
            "1 sentence."
        ),
        "cadence": "flowing",
    },
    "grieving": {
        "opening_style": (
            "DEEP empathy, no rush. 1 sentence acknowledging the loss / pain. "
            "Do NOT pivot to advice in this line. Words like 'is samay shayad sirf "
            "sunna hi enough hai' style. NO 'sab theek hoga'."
        ),
        "closing_style": (
            "Gentle, no agenda. 1 sentence offering presence, not solution. "
            "End-line examples: 'apne aap pe naram rahein, time apna kaam karega' — "
            "but adapted to the engine facts, never generic."
        ),
        "cadence": "gentle",
    },
    "angry": {
        "opening_style": (
            "Validate the anger in 1 sentence WITHOUT agreeing on blame "
            "(e.g. 'frustration jaayaz hai, 3 saal stuck rehna shanti nahi deta')."
        ),
        "closing_style": (
            "Reframe: anger is a signal, not a strategy. End with a 1-sentence "
            "constructive next step driven by EVIDENCE, not emotion."
        ),
        "cadence": "direct",
    },
    "skeptical": {
        "opening_style": (
            "Acknowledge the doubt as healthy in 1 sentence "
            "(e.g. 'jyotish pe doubt hona reasonable hai'). No defensive tone."
        ),
        "closing_style": (
            "End with a 'try this, then judge' invitation — 1 sentence. "
            "Empirical, no faith-demand."
        ),
        "cadence": "direct",
    },
}

# Selective per-domain overrides (applied AFTER tone defaults).
_DOMAIN_TONE_OVERRIDES: dict[tuple[str, str], dict[str, str]] = {
    ("anxious", "health"): {
        "opening_style": (
            "Acknowledge the fear in 1 short sentence and IMMEDIATELY anchor: "
            "'pehle ek baat — kuch bhi serious lage to qualified doctor zaroori hai'. "
            "Astrology supports, never replaces, medical advice."
        ),
        "closing_style": (
            "End with a soft anchor — doctor / faith / family support. 1 sentence. "
            "Never date-stamp recovery as a guarantee."
        ),
    },
    ("desperate", "health"): {
        "opening_style": (
            "Slowest cadence. Acknowledge the weight (e.g. 'aise sawal mann mein "
            "aana himmat ki baat hai'). Anchor: time ki vyakhya kisi ke paas nahi. "
            "Doctor / mental-health support reference if distress is severe."
        ),
        "closing_style": (
            "Quiet, non-prescriptive. End with one small grounding action "
            "(parivar ke saath baat / Hanuman Chalisa / doctor visit). No timelines."
        ),
    },
    ("anxious", "wealth"): {
        "opening_style": (
            "Name the financial fear specifically (e.g. 'paisa nahi ruk raha — "
            "yeh thakawat samajh aati hai'). 1 sentence. Validate without "
            "minimising the struggle. No clichés."
        ),
        "closing_style": (
            "Reframe as a 'discipline-building phase, not a saza'. End with quiet "
            "confidence — the window will shift, the habit will compound. 1 sentence."
        ),
    },
    ("anxious", "marriage"): {
        "opening_style": (
            "Acknowledge the wait/pressure (e.g. 'rishta dhundhne ka time emotionally "
            "thakane wala hota hai'). Validate, never shame. 1 sentence."
        ),
        "closing_style": (
            "Patience-first close — emphasise that timing is cosmic alignment, "
            "not personal worth. 1 sentence."
        ),
    },
    ("angry", "career"): {
        "opening_style": (
            "Validate the frustration with TIMING specifics from the question "
            "(e.g. '3 saal se stuck rehna kisi ka bhi sabra todh deta hai'). "
            "1 sentence. Don't agree with blame yet."
        ),
        "closing_style": (
            "Reframe: chart aapke against nahi, sirf timing-recognition mismatch. "
            "End with one evidence-driven move (review meeting / portfolio doc). 1 sentence."
        ),
    },
    ("hopeful", "wealth"): {
        "opening_style": (
            "Match the energy briefly ('achhi soch se sawal poochha hai'), "
            "then immediately ground: hope without discipline ka koi compounding nahi."
        ),
        "closing_style": (
            "Channel into one specific habit (auto-debit SIP, ledger, weekly review). "
            "1 sentence."
        ),
    },
    ("conflicted", "marriage"): {
        "opening_style": (
            "Name BOTH sides of the dilemma (e.g. 'family pressure ek taraf, "
            "khud ka time ek taraf'). Validate that this tension is real."
        ),
        "closing_style": (
            "End with a 'first decide X, then Y becomes clear' framing — DO NOT "
            "make the marriage decision FOR the user. 1 sentence."
        ),
    },
}


def get_treatment(tone: str, domain: str) -> dict[str, str]:
    """Return the {opening_style, closing_style, cadence} directive for the
    (tone × domain) pair. Falls back to tone-default → neutral-default."""
    tone   = (tone or "neutral").lower().strip()
    domain = (domain or "general").lower().strip()
    if tone not in TONES:
        tone = "neutral"
    base = dict(_TONE_DEFAULTS.get(tone, _TONE_DEFAULTS["neutral"]))
    override = _DOMAIN_TONE_OVERRIDES.get((tone, domain))
    if override:
        base.update(override)
    return base


def get_domain_hard_rules(domain: str) -> tuple[str, ...]:
    """Return the non-negotiable safety rules for the domain."""
    domain = (domain or "general").lower().strip()
    return DOMAIN_HARD_RULES.get(domain, ())


def build_treatment_directive(tone: str, domain: str,
                              ask_types: list | None = None,
                              lang: str = "hn") -> str:
    """Build a system-prompt-ready directive string that any engine's
    structured prompt can append. Encodes:
      • tone-specific opening_style + closing_style instructions
      • cadence rule
      • banned-phrase list (renders cleanly in the prompt)
      • domain hard rules

    Returns a multi-line plain-text block, ready to drop into a system
    message. Designed to be IDEMPOTENT and FACT-FREE — only style rules,
    never any cosmic claim.
    """
    tx = get_treatment(tone, domain)
    hard = get_domain_hard_rules(domain)

    lines: list[str] = []
    lines.append("════ EMOTIONAL TREATMENT DIRECTIVE ════")
    lines.append(f"Detected tone:   {tone or 'neutral'}")
    lines.append(f"Domain:          {domain or 'general'}")
    if ask_types:
        lines.append(f"Ask types:       {', '.join(ask_types)}")
    lines.append(f"Cadence:         {tx.get('cadence', 'direct')}")
    lines.append("")
    lines.append("OPENING LINE (`empathy_open`):")
    lines.append(f"   {tx['opening_style']}")
    lines.append("")
    lines.append("CLOSING LINE (`human_close`):")
    lines.append(f"   {tx['closing_style']}")
    lines.append("")
    lines.append("BANNED PHRASES — do NOT use any of these (case-insensitive):")
    # Group ban list 4-per-line so the prompt doesn't balloon.
    chunk: list[str] = []
    for phrase in BANNED_EMPATHY_PHRASES:
        chunk.append(f'"{phrase}"')
        if len(chunk) == 4:
            lines.append("   " + ", ".join(chunk))
            chunk = []
    if chunk:
        lines.append("   " + ", ".join(chunk))
    if hard:
        lines.append("")
        lines.append("DOMAIN HARD RULES (non-negotiable):")
        for r in hard:
            lines.append(f"   • {r}")
    lines.append("")
    lines.append("LANGUAGE RULE:")
    lines.append(
        f"   Respond in Hinglish (Roman script — Hindi words written in English letters). "
        f"NO Devanagari script. NO pure-English unless lang='en'. (lang={lang})"
    )
    lines.append("════════════════════════════════════════")
    return "\n".join(lines)


def is_banned_empathy(text: str) -> tuple[bool, str]:
    """Check if `text` contains any banned cliché phrase. Returns
    (True, matched_phrase) or (False, '')."""
    if not text:
        return False, ""
    low = text.lower()
    for phrase in BANNED_EMPATHY_PHRASES:
        if phrase in low:
            return True, phrase
    return False, ""
