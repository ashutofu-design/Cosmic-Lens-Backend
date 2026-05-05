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

    # ── ALWAYS-APPEND blocks (apply per intent context) ───────────────
    "TIMING":   "ALWAYS APPEND: name CURRENT Maha+Antar dasha lord, mark if = 4H/4L/Mars/Venus/Saturn. Saturn/Jupiter transit on 4H = supportive/indicative window (NOT a guarantee). NO SPECIFIC DATES.",
    "RISK":     "APPEND when -ve tone or 'kya dikkat/nuksan/risk' asked: 6/8/12 lords on 4H, Rahu-Ketu axis, Mars-Saturn affliction, malefic transit on 4H.",
    "REMEDY":   "APPEND in CLOSER (last line): ONE Vedic remedy specific to the weakest factor — Mars/Saturn pacification mantra, 4H Vastu tip, gemstone for 4L.",
    "REFUSE_TIMING": "If user asks SPECIFIC date / muhurat / griha-pravesh date / 'kab milega exact' → REFUSE: 'Specific date predict karna shastriya etiquette ke khilaf hai. Aapko property yog ke strength + risk + readiness ka picture de sakta hu.'",

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
  INTENT:  yog? (will it happen) | quality? (how good) | risk? | timing? | remedy?
  ASSET:   residential | land | commercial | agricultural

STEP 2 — Pick atomic CHECK BLOCKS that match the detected axes:
  • Pick ONE primary ACTION block (BUY / SELL / INHERIT / RENT / BUILD /
    DISPUTE / ANALYZE).
  • If a SCOPE block applies (FOREIGN / LAND / COMMERCIAL / MULTIPLE), ADD it.
  • TIMING block is always relevant unless user explicitly asks "kab milega
    exact date" (then use REFUSE_TIMING instead).
  • RISK block: add if user's tone is worried OR asks "dikkat / nuksan / risk".
  • REMEDY block: always add ONE remedy in the closer.

STEP 3 — Apply ONLY the picked blocks (typical: 2-4 total). IGNORE the rest.

WORKED EXAMPLES (do NOT copy verbatim — use to calibrate routing):
  Q: "kya mujhe paitric ghar milega?"            → INHERIT + TIMING + REMEDY
  Q: "commercial property me invest karu?"        → BUY + COMMERCIAL + RISK + TIMING
  Q: "rent pe ghar dena chahiye abhi?"            → RENT + TIMING + REMEDY
  Q: "ghar bechu ya rakhu?"                       → SELL + RISK + TIMING
  Q: "foreign me ghar lene ka yog hai?"           → BUY + FOREIGN + TIMING
  Q: "naya ghar banwa raha hu, suitable hai?"     → BUILD + TIMING + REMEDY
  Q: "padosi se property dispute chal raha hai"   → DISPUTE + RISK + REMEDY
  Q: "kab milega ghar exact date batao"           → REFUSE_TIMING
  Q: "agricultural land buy karu?"                → BUY + LAND + RISK + TIMING
  Q: "ek aur property leni chahiye?"              → BUY + MULTIPLE + RISK + TIMING
  Q: "biwi ke naam property kharidu?"             → BUY + JOINT_TITLE + REMEDY
  Q: "shop business ke liye property?"            → BUY + COMMERCIAL + TIMING
  Q: "home loan approve hoga? EMI bharne ka yog?" → BUY + LOAN_EMI + RISK + TIMING
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
  • DOCTRINAL HEDGES (do NOT overstate):
      - Vargottama = STRONGLY supportive, not a guarantee.
      - Neecha-bhanga only IF cancellation conditions verified.
      - KP "must signify 4+11+12" is too strict — core is 4 + (11 OR 2).
"""


def _atomic_blocks_dump() -> str:
    """Render all atomic blocks as a [TAG] line list."""
    return "\n".join(f"  [{k}] {v}" for k, v in ATOMIC_CHECKS.items())


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
]
