"""
property_focus_routing.py — P1.2 (2026-05-05)
================================================================
COMPOSABLE ATOMIC FOCUS BLOCKS for property/ghar Qs.

WHY THIS EXISTS
---------------
Property has ~1000 possible questions across 4 axes:
  ACTION   = buy / sell / inherit / rent / build / dispute / analyze
  SCOPE    = first / additional / multiple / foreign / commercial / land
  INTENT   = yog (will it?) / quality / risk / timing / remedy
  ASSET    = residential / land / commercial / agricultural

Enumerating all sub-types in a fat prompt does NOT scale — Q21 falls
through the cracks. Instead this module exposes ~14 atomic CHECK blocks
(~150 chars each) and a framework header that teaches the LLM to:
  1. detect axes from the user's Q
  2. compose 2-4 relevant atomic blocks
  3. ignore the rest

Total prompt: ~2.2 KB. Covers 720+ Q combinations. Adding a new atomic
block (e.g. CHECK_REIT or CHECK_FARMHOUSE) instantly extends coverage to
50+ new Qs without touching the framework or routing logic.

Replaces _PROPERTY_FOCUS_TEXT (P1.1, fat constant). The wiring sites in
openai_helper.py (narrative + sync + stream + legacy passthrough) call
build_property_focus(question) here instead of using the constant.

KILLSWITCH (parent module): PROPERTY_FOCUS_BLOCK=0/false/no/off
ADD-ONLY: new file, no edits to existing modules' logic.
"""
from __future__ import annotations


# ── ATOMIC CHECK BLOCKS ──────────────────────────────────────────────
# Each block is a single-line directive (~150 chars). LLM picks 2-4
# based on question axes. Order in dict has no semantic meaning — but
# keep TIMING / RISK / REMEDY / REFUSE_TIMING last so they're visually
# grouped as "always-append" candidates.
ATOMIC_CHECKS = {
    # ── ACTION blocks (pick ONE primary based on user intent) ─────────
    "BUY":      "KP 4th CSL signifying 4 (gate) → Vedic 4H sign+occupants → 4L dignity+house → D9 4L vargottama → Mars/Venus karaka strength.",
    "SELL":     "KP 4th CSL signifying 3 (=12-from-4 = disposal) → 12L on/aspecting 4H → Saturn/Rahu transit on 4H → current dasha lord 6/8/12 connection.",
    "INHERIT":  "Moon karaka (mother/ancestral home) dignity → 8H + 8L (legacy/inheritance) → 9L bhagya → KP 4th CSL signifying 4+8 (paitric pattern).",
    "RENT":     "Saturn karaka (specifically rental/leased) dignity → 4H/4L→11H/11L connection → KP 11th CSL signifying 4 → Mercury (tenants/contracts).",
    "BUILD":    "Mars karaka (construction) on/aspecting 4H or 4L → current Mars/Saturn Mahadasha or Antardasha → 4L in upachaya (3,6,10,11) → avoid Saturn-only afflicted periods.",
    "DISPUTE":  "6L/8L/12L on 4H or aspecting 4L → Mars-Saturn affliction → Rahu-Ketu axis on 1-7 or 4-10 → KP 4th CSL signifying 3+6 (loss + enemy).",
    "ANALYZE":  "General property yog: Vedic 4H+4L+karakas survey → D9 strength → KP 4th CSL signifies 4? → name 1 strength + 1 weakness from chart.",

    # ── SCOPE modifier blocks (ADD when scope detected) ───────────────
    "FOREIGN":  "ADD: Rahu karaka strong (foreign indicator) → 12H/12L (foreign settlement) → KP 12th CSL signifying 4+11 → dual sign on 4H.",
    "LAND":     "ADD: Mars karaka primary (over Saturn) → 4H earth/movable sign favoured → 4L in upachaya supportive → pure water signs on 4H = quality concern, NOT a hard veto.",
    "COMMERCIAL":"ADD: Mercury (business/contracts) → 10H connection to 4H → Saturn karaka (long-term hold) → 11H gain stack.",
    "MULTIPLE": "ADD: Saturn strong (own/exalted) for accumulation → Dhana yoga (2-11) → 11H + upachaya stack → multiple benefics on/aspecting 4H.",

    # ── INTENT blocks (P1.2.3 — pick based on what user is asking) ────
    "STATIC_YOG":   "If pure existence Q ('property yog hai? milega kya? kaisa hai?') → YES/NO + strength rating (weak/moderate/strong) + 4H sign + 4L placement + Mars/Venus karaka strength. NO dasha. NO transit. NO 'when'.",
    "YOG_QUALITY":  "If 'delay vs early / slow vs fast / smooth vs friction' yog-NATURE Q → describe MATURATION character (which factors slow it: Saturn link to 4H/4L, malefic on 4H; which speed it: benefic on 4H, 4L in own/exalted, vargottama). Frame as yog ki nature, NOT 'kab milega'. NO dasha forecasting. NO 'near term movement' phrases.",
    "TIMING":       "ONLY IF explicit timing trigger ('kab/when/abhi/turant/next month/year/this year/upcoming/near future/muhurat'): name CURRENT Maha+Antar dasha lord, mark if = 4H/4L/Mars/Venus/Saturn. Saturn/Jupiter transit on 4H = supportive/indicative window (NOT a guarantee). NO SPECIFIC DATES. DO NOT fire on 'delay/early/slow/fast' alone — that is YOG_QUALITY.",
    "RISK":         "APPEND when -ve tone or 'kya dikkat/nuksan/risk' asked: 6/8/12 lords on 4H, Rahu-Ketu axis, Mars-Saturn affliction, malefic transit on 4H.",
    "REMEDY":       "APPEND in CLOSER (last line): ONE Vedic remedy specific to the weakest factor — Mars/Saturn pacification mantra, 4H Vastu tip, gemstone for 4L.",
    "REFUSE_TIMING":"If user asks SPECIFIC date / muhurat / griha-pravesh date / 'kab milega exact' → REFUSE: 'Specific date predict karna shastriya etiquette ke khilaf hai. Aapko property yog ke strength + risk + readiness ka picture de sakta hu.'",

    # ── EDGE-CASE blocks (architect-suggested for completeness) ───────
    "JOINT_TITLE":  "If joint ownership / 'biwi ke naam' / 'partner ke saath' → 7H + 7L dignity (partner) + 4H combined reading. Indicative only — practical reasoning > pure chart.",
    "LOAN_EMI":     "If home-loan / EMI / mortgage Q → 6H (loan/debt) + 6L dignity → 11H gain capacity → current dasha lord 6/8/12 = burden risk. ONE practical line: serviceability > approval-likelihood.",
}


# ── FRAMEWORK HEADER (composition instructions) ──────────────────────
_FRAMEWORK_HEADER = """FOCUS — PROPERTY ANALYSIS (composable framework).

You have D1 + D9 + KP cusps + Vimshottari Dasha + Transit in chart above.
Property Qs vary widely (buy/sell/inherit/rent/build/dispute × first/multiple/
foreign/commercial × yog/quality/risk/timing/remedy). Use this composable
framework — do NOT try to apply every block.

STEP 1 — Read user's Q and detect axes:
  ACTION:  buy | sell | inherit | rent | build | dispute | analyze (general)
  SCOPE:   first-home | additional | multiple | foreign | commercial | land
  INTENT:  STATIC (yog hai/nahi/kaisa) | QUALITY (delay/early/slow/fast)
           | TIMING (kab/exact/abhi/this year) | RISK | REMEDY
  ASSET:   residential | land | commercial | agricultural

STEP 2 — Pick atomic CHECK BLOCKS that match the detected axes:
  • Pick ONE primary ACTION block (BUY / SELL / INHERIT / RENT / BUILD /
    DISPUTE / ANALYZE).
  • If a SCOPE block applies (FOREIGN / LAND / COMMERCIAL / MULTIPLE), ADD it.
  • INTENT routing (P1.2.3 — CRITICAL, do NOT mix):
      - STATIC ('yog hai? milega kya? kaisa hai? strong hai?')
            → ADD [STATIC_YOG]. DO NOT ADD [TIMING].
      - QUALITY ('delay ya early? jaldi ya late? smooth ya friction?')
            → ADD [YOG_QUALITY]. DO NOT ADD [TIMING].
            (delay/early are NATURE words, not timing words.)
      - TIMING ('kab milega? abhi sahi hai? this year? next month? muhurat?')
            → ADD [TIMING]. (Or [REFUSE_TIMING] if 'exact date'.)
  • RISK block: add if user's tone is worried OR asks 'dikkat / nuksan / risk'.
  • REMEDY block: add ONE remedy in the closer (skip for pure STATIC yes/no Qs).

STEP 3 — Apply ONLY the picked blocks (typical: 2-4 total). IGNORE the rest.
        NEVER stack STATIC_YOG + YOG_QUALITY + TIMING together — pick ONE
        intent block based on what user actually asked.

WORKED EXAMPLES (do NOT copy verbatim — use to calibrate routing):
  ── STATIC (yog existence) ──
  Q: "property yog hai mere chart me?"            → ANALYZE + STATIC_YOG
  Q: "kya mujhe ghar milega life me?"             → BUY + STATIC_YOG + REMEDY
  Q: "mera property yog kaisa hai?"               → ANALYZE + STATIC_YOG
  Q: "paitric ghar milega kya?"                   → INHERIT + STATIC_YOG

  ── QUALITY (yog nature: delay/early/smooth) ──
  Q: "property me delay hoga ya early yog hai?"   → BUY + YOG_QUALITY
  Q: "ghar lene me jaldi yog hai ya late?"        → BUY + YOG_QUALITY
  Q: "smooth closure hogi ya friction?"           → BUY + YOG_QUALITY + RISK

  ── TIMING (when / explicit time-trigger) ──
  Q: "ghar kab milega next year tak?"             → BUY + TIMING
  Q: "abhi property lene ka time hai?"            → BUY + TIMING
  Q: "rent pe ghar dena chahiye abhi?"            → RENT + TIMING
  Q: "kab milega ghar exact date batao"           → REFUSE_TIMING

  ── ACTION + SCOPE composites ──
  Q: "commercial property me invest karu?"        → BUY + COMMERCIAL + RISK
  Q: "ghar bechu ya rakhu?"                       → SELL + RISK
  Q: "foreign me ghar lene ka yog hai?"           → BUY + FOREIGN + STATIC_YOG
  Q: "naya ghar banwa raha hu, suitable hai?"     → BUILD + REMEDY
  Q: "padosi se property dispute chal raha hai"   → DISPUTE + RISK + REMEDY
  Q: "agricultural land buy karu?"                → BUY + LAND + RISK
  Q: "ek aur property leni chahiye?"              → BUY + MULTIPLE + STATIC_YOG
  Q: "biwi ke naam property kharidu?"             → BUY + JOINT_TITLE + REMEDY
  Q: "home loan approve hoga? EMI bharne ka yog?" → BUY + LOAN_EMI + RISK
  Q: "joint property partner ke saath safe hai?"  → JOINT_TITLE + RISK + REMEDY

ATOMIC CHECK BLOCKS (pick from these only):
"""


_ANSWER_STYLE = """
ANSWER STYLE (mandatory):
  • 100-150 words, 2-3 short Hinglish paragraphs. NO bullets. NO headers.
  • Cite ACTUAL planet names + house numbers from THIS chart — never invent.
    If a value is missing, say so honestly ('D9 me 4L ka exact dignity nahi
    mil raha').
  • Translate Sanskrit inline: 'Chaturthesh (4H lord)', 'Mangal (Mars)',
    '4th cusp ka sub-lord'.
  • End with ONE practical line — Vedic remedy OR a 1-line summary insight.
  • For TIMING: name current Maha+Antar lord plainly, NEVER specific dates.
  • For STATIC_YOG / YOG_QUALITY: do NOT name dasha periods or use phrases
    like 'near term me movement', 'this phase me', 'abhi chal raha hai' —
    those are TIMING-only. Stay on chart structure (4H, 4L, karakas, D9).
  • DOCTRINAL HEDGES (do NOT overstate):
      - Vargottama = STRONGLY supportive, not a guarantee.
      - Neecha-bhanga only IF cancellation conditions verified.
      - KP "must signify 4+11+12" is too strict — core is 4 + (11 OR 2).
"""


def _atomic_blocks_dump() -> str:
    """Render all atomic blocks as a [TAG] line list."""
    return "\n".join(f"  [{k}] {v}" for k, v in ATOMIC_CHECKS.items())


import re as _re

# ── P1.2.4 POST-INJECTOR: dasha-leak strip for STATIC/QUALITY answers ────
# Even with framework guards, LLM occasionally slips dasha mentions
# ("Moon-Mars phase chal raha hai") into pure STATIC_YOG / YOG_QUALITY
# answers. This deterministic post-processor strips such sentences
# AFTER the LLM call (belt-and-braces). NO-OP for TIMING Qs.

_PLANET_TOKENS = (
    r"(?:Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu"
    r"|Surya|Soorya|Chandra|Mangal|Budh|Budha|Guru|Brihaspati|Shukra"
    r"|Shani|Sani)"
)
# Sentence-killer patterns — if a sentence matches ANY, drop it.
_DASHA_LEAK_RX = _re.compile(
    r"("
    # "Moon-Mars phase chal raha hai" / "Sun/Moon ka phase" / "Jupiter-Rahu dasha"
    rf"{_PLANET_TOKENS}\s*[-–/]\s*{_PLANET_TOKENS}\s+(?:ka\s+|ki\s+)?"
    rf"(?:phase|dasha|dasa|antardasha|antar[\s-]*dasha|maha[\s-]*dasha|mahadasha|mahadasa)"
    # "X mahadasha" / "Y antardasha" / "Saturn sub-period"
    rf"|{_PLANET_TOKENS}\s+(?:maha[\s-]*dasha|antar[\s-]*dasha|mahadasha|antardasha|sub[\s-]?period)"
    # P1.2.4.1 (architect-fix) — single-planet dasha forms LLMs commonly use:
    # "Rahu dasha chal rahi hai", "Moon ki dasha", "Jupiter ka dasha",
    # "currently in Saturn dasha", "Venus dasa me"
    rf"|{_PLANET_TOKENS}\s+(?:ka|ki)\s+(?:dasha|dasa)"
    rf"|{_PLANET_TOKENS}\s+(?:dasha|dasa)\s+(?:chal|me|mein|active|running|chalu)"
    rf"|(?:currently\s+in|abhi)\s+{_PLANET_TOKENS}\s+(?:dasha|dasa|phase|period)"
    # "abhi jo X-Y phase" / "abhi jo Moon ka phase chal raha"
    rf"|abhi\s+jo\s+{_PLANET_TOKENS}"
    # explicit timing-flavor phrases
    r"|near\s+term\s+me\s+movement"
    r"|this\s+phase\s+me"
    r")",
    _re.IGNORECASE,
)
# Question-intent triggers
_TIMING_Q_TRIGGER_RX = _re.compile(
    r"\b(kab|kab\s+tak|when|by\s+when|abhi|turant|"
    r"next\s+(?:month|year|week)|this\s+year|is\s+(?:saal|mahine|hafte)|"
    r"agle\s+(?:saal|mahine|hafte|year|month|week)|kitne\s+time|kitna\s+time|"
    r"upcoming|near\s+future|muhurat|exact\s+date|tareekh|tarikh|"
    r"by\s+(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december|\d{4}))\b",
    _re.IGNORECASE,
)
_QUALITY_Q_TRIGGER_RX = _re.compile(
    r"\b(delay|early|jaldi|late|slow|fast|smooth|friction|delayed|"
    r"matured?|nature)\b",
    _re.IGNORECASE,
)


def _detect_property_intent(question: str) -> str:
    """Classify the property Q intent → STATIC | QUALITY | TIMING."""
    if not isinstance(question, str):
        return "STATIC"
    if _TIMING_Q_TRIGGER_RX.search(question):
        return "TIMING"
    if _QUALITY_Q_TRIGGER_RX.search(question):
        return "QUALITY"
    return "STATIC"


def strip_dasha_leak(text: str, question: str) -> tuple[str, int]:
    """Drop dasha-mention sentences from STATIC/QUALITY property answers.

    Returns (cleaned_text, sentences_stripped). NO-OP for TIMING Qs
    (where dasha mentions are expected and correct). NO-OP if input is
    not a non-empty string.

    Sentence boundary uses period / exclaim / question / Devanagari
    danda (। U+0964). Multiple whitespaces are collapsed after stripping.
    """
    if not isinstance(text, str) or not text.strip():
        return text, 0
    intent = _detect_property_intent(question)
    if intent == "TIMING":
        return text, 0
    # Roughly split into sentences (keep the punctuation with each piece)
    sentences = _re.split(r'(?<=[.!?।])\s+', text)
    if len(sentences) <= 1:
        return text, 0
    kept = []
    stripped = 0
    for s in sentences:
        if _DASHA_LEAK_RX.search(s):
            stripped += 1
            continue
        kept.append(s)
    if stripped == 0:
        return text, 0
    cleaned = ' '.join(kept).strip()
    cleaned = _re.sub(r'\s+', ' ', cleaned)
    cleaned = _re.sub(r'\s+([.,;!?।])', r'\1', cleaned)
    return cleaned, stripped


# ── P1.2.5 CHART TRIMMER: drop dasha/transit sections for STATIC/QUALITY ──
# User feedback: dasha tree (Sec 4), upcoming dasha (Sec 5), gochar (Sec 8),
# and dasha+transit overlay (Sec 9) are TIMING-only data. STATIC_YOG and
# YOG_QUALITY answers don't need them, and feeding them to the LLM only
# tempts dasha-leak (the very leak P1.2.4 strips post-hoc). Trim BEFORE
# the LLM call → cleaner prompt + lower tokens + less leak surface.
#
# Sections kept for STATIC/QUALITY: 1 (Janm/Lagna), 2 (Grahas),
# 3 (Bhavas), 6 (D9 Navamsha), 15 (Niyam), KP block (separate).
# Sections dropped: 4, 5, 8, 9.
# NO-OP for TIMING intent (full chart preserved).

# Section header pattern from kundli_full_context.py: "## N. TITLE"
# We split on `\n## ` boundaries, keep section headers we want, drop
# sections matching the drop-list. Defensive: if pattern doesn't match
# (format changed), return input unchanged (NO-OP, never blocks request).
_DASHA_SECTION_NUMS = frozenset({"4", "5", "8", "9"})
_SECTION_BOUNDARY_RX = _re.compile(r'(?=^## \d+\.)', _re.MULTILINE)
_SECTION_NUM_RX = _re.compile(r'^## (\d+)\.')


def trim_dasha_sections(chart_block: str, question: str) -> tuple[str, int]:
    """Drop dasha/transit sections from chart-context for STATIC/QUALITY
    property answers. Returns (trimmed_block, sections_dropped).

    NO-OP for TIMING intent, empty input, or when the section pattern
    doesn't match (defensive — never breaks the request).
    """
    if not isinstance(chart_block, str) or not chart_block.strip():
        return chart_block, 0
    intent = _detect_property_intent(question)
    if intent == "TIMING":
        return chart_block, 0
    parts = _SECTION_BOUNDARY_RX.split(chart_block)
    if len(parts) <= 1:
        return chart_block, 0
    kept = []
    dropped = 0
    for p in parts:
        m = _SECTION_NUM_RX.match(p)
        if m and m.group(1) in _DASHA_SECTION_NUMS:
            dropped += 1
            continue
        kept.append(p)
    if dropped == 0:
        return chart_block, 0
    return ''.join(kept).rstrip() + '\n', dropped


# ── P1.2.6 AXES PRE-ROUTING: server-side detect → minimal atomics ────
# Original build_property_focus dumps ALL 25 atomic blocks (~8 KB) into
# every property prompt. The LLM picks the relevant 2-4 itself. Wasteful:
# ~6 KB of unused atomics per Q × millions of Qs.
#
# P1.2.6 detects axes server-side (regex) and emits ONLY the matched
# atomic blocks (typical 3-5) → ~2 KB block, ~75% token savings, same
# answer quality (LLM gets the SAME doctrinal text for the matched axes,
# just without the noise of 20+ unrelated blocks).
#
# KILLSWITCH: PROPERTY_FOCUS_AXES=0/false/no/off → fallback to fat dump.
# Defensive: any detection error → fallback to fat dump (NEVER blocks).
import os as _os

# ── ACTION axis (pick ONE) ────────────────────────────────────────────
# Order matters for tie-break: more specific verbs first. INHERIT before
# BUY (paitric ghar mil-jaata is inherit, not buy). DISPUTE before all
# (because "padosi se ghar" mentions ghar but is dispute).
_ACTION_PATTERNS = (
    ("DISPUTE", _re.compile(
        r"\b(dispute|vivad|jhagda|jhagra|jhagad|case|court|kachehri|"
        r"padosi|tenant\s+(?:nahi\s+)?vacat|kabza|illegal|"
        r"legal\s+(?:problem|issue|fight))\b", _re.IGNORECASE)),
    ("INHERIT", _re.compile(
        r"\b(paitrik|paitric|paitruk|inherit(?:ance|ed)?|ancestral|"
        r"papa\s+ka|papaji\s+ka|dada\s+ka|nana\s+ka|"
        r"family\s+(?:property|ghar)|virasat)\b", _re.IGNORECASE)),
    ("BUILD", _re.compile(
        r"\b(banwa|banwana|banwaun|banaun|banaungi|banayenge|construct|"
        r"construction|build|building|under\s+construction|"
        r"new\s+construction|naya\s+ghar\s+ban)\b", _re.IGNORECASE)),
    ("RENT", _re.compile(
        r"\b(rent|rental|kiraye|kiraya|lease|leased|leasing|tenant|"
        r"paying\s+guest|pg\b|let\s+out)\b", _re.IGNORECASE)),
    ("SELL", _re.compile(
        r"\b(bech|bechu|bechna|bechni|bechunga|sell|selling|sold|"
        r"disposal|liquidate|dispose|exit\s+(?:property|investment))\b",
        _re.IGNORECASE)),
    ("BUY", _re.compile(
        # P1.2.6.1 fixes:
        #   - khar[ie]+d* → catches kharid/khareed/khareedu spellings
        #   - lene/leni/lena/lenge → "ghar lene", "property leni chahiye"
        #   - invest\s+kar → Hinglish "invest karu/karna/karunga"
        r"\b(khar[ie]+d\w*|"
        r"buy|buying|purchase|"
        r"invest(?:ment)?\s+(?:in\s+(?:property|real)|kar\w*)|"
        r"le\s+lu|le\s+lun|lelu|lelun|lega|legi|le\s+rahe|"
        r"lene|leni|lena|lenge|lengi|"
        r"acquire|acquir)\b", _re.IGNORECASE)),
)

# ── SCOPE axis (0+ matches, ADD modifiers) ────────────────────────────
_SCOPE_PATTERNS = (
    ("FOREIGN", _re.compile(
        r"\b(foreign|abroad|overseas|videsh|videshi|nri|"
        r"dubai|usa|uk|canada|london|america|singapore|australia|"
        r"germany|europe|gulf)\b", _re.IGNORECASE)),
    ("LAND", _re.compile(
        # P1.2.6.1: drop trailing \b — "agricultural" extends "agricultur"
        # so trailing \b fails. Use prefix match for "agricultur*".
        r"\b(agricultur\w*|farmland|farm\s+land|khet|kheti|"
        r"plot|empty\s+land|raw\s+land|jameen|zameen)\b",
        _re.IGNORECASE)),
    ("COMMERCIAL", _re.compile(
        r"\b(commercial|shop|dukaan|dukan|office|office\s+space|"
        r"showroom|warehouse|godown|business\s+property|"
        r"retail|industrial)\b", _re.IGNORECASE)),
    ("MULTIPLE", _re.compile(
        r"\b(ek\s+aur|another|second|teesra|teesri|dusra|dusri|"
        r"multiple\s+propert|second\s+home|additional\s+propert|"
        r"kai\s+propert|investment\s+property)\b", _re.IGNORECASE)),
)

# ── EDGE axis (0+ matches, ADD edge concerns) ─────────────────────────
_EDGE_PATTERNS = (
    ("JOINT_TITLE", _re.compile(
        r"\b(joint|co[-\s]?own|biwi\s+ke\s+naam|wife[''s]+\s+name|"
        r"partner\s+ke\s+saath|partner[''s]+\s+name|together|"
        r"husband[''s]+\s+name|pati\s+ke\s+naam|saath\s+me\s+lena)\b",
        _re.IGNORECASE)),
    ("LOAN_EMI", _re.compile(
        r"\b(loan|emi|mortgage|karz|karza|finance|financ(?:ed|ing)|"
        r"installment|qist|kist|home\s+loan|housing\s+loan|"
        r"property\s+loan|down\s+payment)\b", _re.IGNORECASE)),
)

# ── APPENDIX axis (0+ matches) ────────────────────────────────────────
# RISK: fires on negative-tone keywords. REMEDY: always-on unless
# explicit refusal-only Q. REFUSE_TIMING: fires when intent=TIMING +
# explicit "exact"/"specific" hint.
_RISK_RX = _re.compile(
    # P1.2.6.2 (architect-fix): dropped "safe hai" / "theek hai" — those
    # are POSITIVE phrasings ("ghar safe hai?") and were causing RISK
    # false positives. Bare "safe" / "theek" also dropped to avoid
    # ambiguous matches; explicit risk vocabulary remains.
    r"\b(dikkat|nuksan|nuqsan|risk|risky|jokhim|loss|"
    r"problem|issue|trouble|danger|fraud|cheat|dhokha|"
    r"galat|wrong|unsafe|insecure)\b", _re.IGNORECASE)
_REFUSE_TIMING_RX = _re.compile(
    r"\b(exact\s+(?:date|day|tareekh|tarikh|month)|"
    r"specific\s+(?:date|day|tareekh|tarikh|month)|"
    r"griha[\s-]*pravesh\s+(?:date|muhurat|tareekh)|"
    r"tareekh\s+batao|tarikh\s+batao|"
    r"kab\s+(?:exact|exactly)|exactly\s+kab)\b", _re.IGNORECASE)


def _property_focus_axes_enabled() -> bool:
    """True UNLESS PROPERTY_FOCUS_AXES explicitly disables. Default ON.

    Independent killswitch from PROPERTY_FOCUS_BLOCK so granular rollback
    possible (you can disable axes-routing while keeping the property
    focus block enabled — falls back to fat dump).
    """
    val = _os.environ.get("PROPERTY_FOCUS_AXES", "").strip().lower()
    return val not in ("0", "false", "no", "off")


def detect_property_axes(question: str) -> dict:
    """Detect property Q axes server-side. Returns a dict with keys:

      action:    str   — exactly one of ATOMIC_CHECKS ACTION keys.
      scopes:    list  — 0+ ATOMIC_CHECKS SCOPE keys (FOREIGN/LAND/...).
      intent:    str   — STATIC_YOG | YOG_QUALITY | TIMING | REFUSE_TIMING.
      edges:     list  — 0+ ATOMIC_CHECKS EDGE keys (JOINT_TITLE/LOAN_EMI).
      appendix:  list  — 0+ of {RISK, REMEDY} (REMEDY default-on).

    Defensive: invalid input → ANALYZE + STATIC_YOG + REMEDY (safest
    minimal block — covers a generic property Q without timing risk).
    """
    safe_default = {
        "action":   "ANALYZE",
        "scopes":   [],
        "intent":   "STATIC_YOG",
        "edges":    [],
        "appendix": ["REMEDY"],
    }
    if not isinstance(question, str) or not question.strip():
        return safe_default
    q = question

    # ── ACTION (first match wins; ANALYZE if none match) ──
    action = "ANALYZE"
    for tag, rx in _ACTION_PATTERNS:
        if rx.search(q):
            action = tag
            break

    # ── SCOPES (collect ALL matches; preserve declaration order) ──
    scopes = [tag for tag, rx in _SCOPE_PATTERNS if rx.search(q)]

    # ── EDGES (collect ALL matches) ──
    edges = [tag for tag, rx in _EDGE_PATTERNS if rx.search(q)]

    # P1.2.6.1: LOAN_EMI strongly implies BUY action ("home loan approve
    # hoga? EMI bharne ka yog?" — no explicit buy verb but intent is buy).
    # Only override default ANALYZE; never overwrite an explicit verb.
    if action == "ANALYZE" and "LOAN_EMI" in edges:
        action = "BUY"

    # ── INTENT (TIMING > QUALITY > STATIC; REFUSE_TIMING overrides) ──
    base_intent = _detect_property_intent(q)
    if base_intent == "TIMING" and _REFUSE_TIMING_RX.search(q):
        intent = "REFUSE_TIMING"
    elif base_intent == "TIMING":
        intent = "TIMING"
    elif base_intent == "QUALITY":
        intent = "YOG_QUALITY"
    else:
        intent = "STATIC_YOG"

    # ── APPENDIX ──
    # REMEDY: always-on (cheap safety; cosmic remedy line at closer).
    # Skip REMEDY for REFUSE_TIMING (refuse line is the closer).
    appendix = []
    if _RISK_RX.search(q):
        appendix.append("RISK")
    if intent != "REFUSE_TIMING":
        appendix.append("REMEDY")

    return {
        "action":   action,
        "scopes":   scopes,
        "intent":   intent,
        "edges":    edges,
        "appendix": appendix,
    }


# ── Compact framework header for axes-routed mode ─────────────────────
# When axes are pre-routed, the LLM does NOT need the full STEP 1 / STEP 2
# composition logic + 16 worked-examples (~5 KB). Just tell it which
# blocks to apply. ~400 chars vs 5 KB.
_AXES_FRAMEWORK_HEADER = """FOCUS — PROPERTY ANALYSIS (server pre-routed for this Q).

You have D1 + D9 + KP cusps + Vimshottari Dasha + Transit in chart above.
Server has detected this Q's axes and selected the relevant CHECK blocks
below. Apply ONLY these blocks (not the full property doctrine). Cite
ACTUAL planet names + house numbers from THIS chart — never invent.

ROUTED CHECK BLOCKS for this Q:
"""


def _picked_atomic_blocks_dump(picked: list) -> str:
    """Render a subset of ATOMIC_CHECKS as [TAG] lines, preserving the
    CALLER-PROVIDED picked order (so REFUSE_TIMING / closer blocks land
    last as intended). Unknown tags silently skipped (defensive).

    P1.2.6.2 (architect-fix): previous version iterated ATOMIC_CHECKS
    declaration order, defeating the build_property_focus assembly
    ordering (REFUSE_TIMING was placed BEFORE later-declared blocks like
    JOINT_TITLE). Caller is now responsible for picked order; this
    renderer just respects it.
    """
    return "\n".join(
        f"  [{k}] {ATOMIC_CHECKS[k]}" for k in picked if k in ATOMIC_CHECKS
    )


def build_property_focus(question: str = "") -> str:
    """Return the property-focus block.

    P1.2.6: when PROPERTY_FOCUS_AXES is enabled (default ON) AND a non-
    empty question is provided, returns a COMPACT axes-routed block
    (~1.5-2.5 KB) containing only the matched atomic CHECK blocks.

    When disabled OR question is empty, returns the original FAT block
    (~8 KB) with all 25 atomic blocks for the LLM to self-route.

    Defensive: any detection error → fat-block fallback (NEVER blocks).
    """
    # Killswitch + empty-question fallback to original behavior
    if not _property_focus_axes_enabled() or not (
        isinstance(question, str) and question.strip()
    ):
        return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE

    try:
        axes = detect_property_axes(question)
        picked = [axes["action"]]
        picked.extend(axes["scopes"])
        # P1.2.6.2 (architect-fix): REFUSE_TIMING MUST be the closer-line
        # block (refuse-message replaces remedy/closer). For other intents
        # (STATIC_YOG/YOG_QUALITY/TIMING) intent block goes mid-stack so
        # appendix RISK/REMEDY can still close. Assembly:
        #   non-refuse → action, scopes, intent, edges, appendix
        #   refuse     → action, scopes, edges, appendix, REFUSE_TIMING (last)
        if axes["intent"] == "REFUSE_TIMING":
            picked.extend(axes["edges"])
            picked.extend(axes["appendix"])
            picked.append("REFUSE_TIMING")
        else:
            picked.append(axes["intent"])
            picked.extend(axes["edges"])
            picked.extend(axes["appendix"])
        # Dedup while preserving order (in case action == intent == ...)
        seen = set()
        picked_unique = []
        for tag in picked:
            if tag in ATOMIC_CHECKS and tag not in seen:
                seen.add(tag)
                picked_unique.append(tag)
        if not picked_unique:
            # Should never happen, but defensive: fallback to fat dump.
            return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE
        return (
            _AXES_FRAMEWORK_HEADER
            + _picked_atomic_blocks_dump(picked_unique)
            + "\n"
            + _ANSWER_STYLE
        )
    except Exception as _axes_exc:  # noqa: BLE001
        # P1.2.6.2 (architect-fix): log fallback so silent quality
        # regressions become visible. Counter for crude alerting.
        try:
            global _AXES_FALLBACK_COUNT
            _AXES_FALLBACK_COUNT += 1
        except NameError:
            _AXES_FALLBACK_COUNT = 1  # type: ignore[name-defined]
        print(
            f"[property_focus_axes][FALLBACK_COUNT={_AXES_FALLBACK_COUNT}] "
            f"axes detection failed → fat-dump fallback: "
            f"{type(_axes_exc).__name__}: {str(_axes_exc)[:160]}",
            flush=True,
        )
        # Any unexpected error → fall back to original fat dump (safe).
        return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE


__all__ = [
    "ATOMIC_CHECKS",
    "build_property_focus",
    "detect_property_axes",
    "strip_dasha_leak",
    "trim_dasha_sections",
    "_detect_property_intent",
]
