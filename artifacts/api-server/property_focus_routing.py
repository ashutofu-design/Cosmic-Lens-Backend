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


def build_property_focus(question: str = "") -> str:
    """Return the composable property-focus block.

    Args:
        question: user's question text. Reserved for future use (e.g. light
                  keyword hint injection); current implementation returns a
                  question-agnostic framework + atomic-blocks dump.

    Returns:
        ~2.2 KB framework string ready to slot into the system prompt
        (caller wraps with 'SHASTRIYA FOCUS for this question:\\n...').
    """
    return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE


__all__ = [
    "ATOMIC_CHECKS",
    "build_property_focus",
    "strip_dasha_leak",
    "_detect_property_intent",
]
