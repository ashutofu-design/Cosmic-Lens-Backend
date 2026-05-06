"""
health_focus_routing.py — H3 (2026-05-06)
================================================================
COMPOSABLE ATOMIC FOCUS BLOCKS for health/swasthya Qs.

Direct mirror of `property_focus_routing.py` (P1.2). Replaces the
fat `health_static/` engine (152 KB engine + 122 KB replies + 87 KB
topics + 25 KB pack + 14 KB routing) with ~25 atomic CHECK blocks
+ a thin axes router.

WHY THIS EXISTS
---------------
Health has ~1500+ possible Qs across 4 axes:
  ACTION   = analyze | prevent | recover | manage_chronic | mental_support
             | repro_support | analyze (general)
  SYSTEM   = digestive | cardio | nervous | musculoskeletal | skin
             | endocrine | respiratory | immune | reproductive
  INTENT   = STATIC (vitality kaisi hai?) | QUALITY (tendency/aage risk)
             | TIMING (kab thik honga? — REFUSE) | RISK | REMEDY
  EDGE     = parent_health | addiction | accident_risk | sensitive_repro
             | sensitive_mental

Enumerating in a fat prompt does NOT scale (the old health_static
had 87 KB of topics JSON and STILL missed Qs). Instead this module
exposes ~26 atomic CHECK blocks (~150 chars each) + a framework
header that teaches the LLM to:
  1. detect axes server-side
  2. compose 2-4 relevant atomic blocks
  3. ignore the rest

Total prompt: ~2.5 KB. Covers 1500+ Q combinations.

⚠️  BRAND-SAFETY HARD GUARDS (non-negotiable, ported from
    health_static.health_routing._WARN_PATTERNS):
  • NEVER predict death / longevity end (REFUSE_DEATH)
  • NEVER name specific diseases (REFUSE_DIAGNOSIS)
  • NEVER guarantee cure (REFUSE_CURE_GUARANTEE)
  • NEVER predict illness/recovery date (REFUSE_TIMING_*)
  • Suicide/self-harm phrasing → CRISIS_REDIRECT (helpline)
  • Mental / reproductive / parent / addiction → sensitive bucket
    → softer tone + extra disclaimer

KILLSWITCHES (independent, all default ON):
  HEALTH_FOCUS_BLOCK    = entire framework
  HEALTH_FOCUS_AXES     = axes-routing only (off → fat block)
  HEALTH_CHART_SLICE    = chart slicing only
  HEALTH_DISCLAIMER     = mandatory medical-disclaimer post-injector

ADD-ONLY: new file, no edits to existing modules' logic.
"""
from __future__ import annotations
import os as _os
import re as _re
from typing import Optional, Tuple, List, Dict, Any


# ── ATOMIC CHECK BLOCKS ──────────────────────────────────────────────
# Each block is a single-line directive (~150 chars). LLM picks 2-4
# based on question axes. Order in dict has no semantic meaning — but
# REFUSE/CRISIS blocks are visually grouped last as "always-append".
ATOMIC_CHECKS: Dict[str, str] = {
    # ── ACTION blocks (pick ONE primary based on user intent) ─────────
    "ANALYZE":         "General vitality scan: 1H + Lagnesh dignity → Sun (vitality karaka) + Moon (mind/fluids) strength → 6H/6L (disease) + 8H/8L (chronic) + Mars/Saturn affliction → KP 1st CSL.",
    "PREVENT":         "Risk-flag scan: 6H/6L + 8H/8L + 12H lords on 1H or aspecting Lagnesh → Mars-Saturn affliction on Lagna/Moon → benefic protection (Jupiter/Venus on 1/5/9). Frame as 'tendency to watch', NOT diagnosis.",
    "RECOVER":         "Recovery capacity (NOT date): 6L dignity (own/exalted = good resistance) → Mars+Mercury (healing karakas) → Jupiter aspect on 1H/6H → Vipreet-Raja-yoga from 6/8/12 lord exchange. Doctor compliance > chart.",
    "MANAGE_CHRONIC":  "Long-term tendency: 8H + 8L + Saturn dignity → Rahu node on 1/6/8 → 6L+8L exchange → mention 'lifestyle factors > chart' as primary lever. Suggest 1 chart-aligned habit (no medical names).",
    "MENTAL_SUPPORT":  "Moon dignity (own/exalted/debilitated) + Moon's nakshatra-lord → 4H (mind/peace) + 4L → Mercury (cognition) + Jupiter (wisdom/calm) aspect on Moon → afflictions from Saturn/Rahu/Ketu on Moon.",
    "REPRO_SUPPORT":   "5H + 5L (children) → Jupiter karaka (santaan-karaka) → 7H/7L (partner-support) → Mars/Venus (vitality of reproductive system) → D7 Saptamsa if available. Frame as energetic-tendency, fertility-specialist consult primary.",

    # ── SYSTEM modifier blocks (ADD when system detected; informational only) ──
    "DIGESTIVE":       "ADD: Mercury (digestion karaka) + 5H/Leo region → Sun digestion-fire → Moon (fluid imbalance) → afflictions from Saturn (slow) / Mars (acidity-tendency).",
    "CARDIO":          "ADD: Sun (heart karaka) + Leo/5H region → 4H (chest cavity) + 4L → Jupiter expansion vs Saturn constriction on Sun/4H. Cardiology consult primary.",
    "NERVOUS":         "ADD: Mercury (nerves) + Saturn (nervous-system endurance) → Moon (mind-body link) → Rahu/Ketu on Mercury or 3H = sensitivity-tendency.",
    "MUSCULOSKELETAL": "ADD: Mars (muscles) + Saturn (bones/joints) + Sun (skeletal frame) → 6H/6L (acute pain) vs 8H/8L (chronic stiffness-tendency).",
    "SKIN":            "ADD: Mercury (skin karaka) + Moon (complexion/hydration) → Saturn-Mars affliction on Mercury/Moon → 6H = surface-issue tendency.",
    "ENDOCRINE":       "ADD: Sun (vitality core) + Jupiter (metabolism/expansion) + Moon (fluid balance) → Saturn (slow metabolism) + Rahu (imbalance) afflictions. Endocrinologist consult primary.",
    "RESPIRATORY":     "ADD: Mercury (breath/lungs region) + Moon (mucous) → 3H (breath-channel) + 3L → Mars/Saturn affliction on Mercury/3H.",
    "IMMUNE":          "ADD: Sun (core vitality) + Mars (defence) + Lagnesh dignity → 6L well-placed = strong resistance → Jupiter aspect on 1H = protective.",
    "REPRO_SYS":       "ADD: 5H + 7H + 8H (reproductive cluster) → Jupiter (santaan-karaka) + Venus (vitality) + Mars (procreation-energy) → afflictions from Saturn-Rahu on 5/7/8.",

    # ── INTENT blocks (pick based on what user is asking) ────────────
    "STATIC_VITALITY": "If pure existence Q ('vitality kaisi? immunity strong? sehat kaisa?') → strength-rating (weak/moderate/strong) + 1H sign + Lagnesh placement + Sun-Moon dignity. NO dasha. NO transit. NO 'when'. NO disease names.",
    "QUALITY_TENDENCY":"If 'aage chal ke / kya tendency / future me kya risk' Q (NATURE not date) → describe TENDENCY-character: which afflictions create vulnerability (Saturn-Rahu on 6/8), which combinations protect (Jupiter on 1/5/9). Frame as inherent-nature, NOT 'kab hoga'. NO dasha forecasting.",
    "RISK":            "APPEND when -ve tone or 'kya risk/dikkat/khatra' asked: 6/8/12 lord placements, Rahu-Ketu axis on 1/6/8, Mars-Saturn affliction on Lagna/Moon, malefic transit on 1H/6H. Frame as 'tendency-zone to monitor'.",
    "REMEDY":          "APPEND in CLOSER (last line): ONE Vedic remedy specific to the weakest factor — graha mantra/japa, gemstone (with caveats), donation, OR a chart-aligned lifestyle nudge (sleep schedule for Moon, sunlight for Sun, etc.). Free-first, paid optional.",

    # ── EDGE-CASE blocks (sensitive sub-domains) ─────────────────────
    "ACCIDENT_RISK":   "If accident/injury/chot Q → Mars (sudden-event karaka) + 8H/8L (sudden disruption) + Ketu (mokshakaraka, also sudden hit) → malefic transit over Mars/8H. Frame as 'caution-window tendency', NEVER predict event.",
    "PARENT_HEALTH":   "If parent's health asked → 4H/4L for mother, 9H/9L for father → 1H/8H of native (parent karakas). Soft tone. Suggest immediate doctor + practical caregiver action; chart is supportive insight only.",
    "ADDICTION":       "If addiction/nasha asked → Rahu (illusion/intoxication-tendency) + Moon afflicted by Rahu/Saturn → 12H (escapism). Frame as 'tendency to watch'; recovery groups + counselling primary, chart is one input.",

    # ── HARD-GUARD REFUSAL blocks (always-last; replace closer) ──────
    "REFUSE_DIAGNOSIS":     "REFUSE: 'Specific bimari name karna shastra ke khilaf hai (jyotish diagnosis nahi karta — woh sirf doctor karte hain). Main vitality zones, tendency-areas, aur protective combinations bata sakta hu — diagnosis ke liye doctor se milo.'",
    "REFUSE_DEATH":         "REFUSE: 'Death/longevity exact predict karna shastriya etiquette ke khilaf hai (mrityu-yog ka exact timing nahi bataya jata). Main vitality + protective yogas + caution-windows bata sakta hu — exact end-date nahi.'",
    "REFUSE_CURE_GUARANTEE":"REFUSE: 'Cure-guarantee dena ya 100% recovery promise karna shastriya etiquette + medical ethics dono ke khilaf hai. Chart vitality + recovery-capacity bata sakta hai — cure ka final assurance sirf doctor de sakte hain.'",
    "REFUSE_TIMING_DECLINE":"REFUSE: 'Bimari-aane ka exact date predict karna shastriya etiquette ke khilaf hai (jyotish exact illness-date nahi batata). Main vulnerability-windows aur protective tendencies bata sakta hu — exact date nahi.'",
    "REFUSE_TIMING_RECOVERY":"REFUSE: 'Recovery ka exact date predict karna chart se possible nahi (recovery doctor compliance + body response pe depend karta hai). Main recovery-capacity + supportive yogas bata sakta hu — exact date nahi.'",
    "REFUSE_SURGERY_MUHURAT":"REFUSE: 'Surgery muhurat dena medical decision hai — surgeon + family ke saath finalize karo. Main supportive period-character bata sakta hu (general benefic vs malefic phase) — exact date nahi.'",
    "CRISIS_REDIRECT":      "OVERRIDE all other blocks: 'Bhai aap ke alfaz se lag raha hai aap bahut tough phase me ho. Please abhi iCall +91-9152987821 ya Vandrevala +91-1860-2662-345 pe baat karo — ye trained log 24/7 free me sun-te hain. Aap akele nahi ho. Chart baad me dekhenge — pehle aap safe.' Skip ALL chart talk.",
}


# ── FRAMEWORK HEADER (composition instructions) ──────────────────────
_FRAMEWORK_HEADER = """FOCUS — HEALTH ANALYSIS (composable framework).

You have D1 + (D9 if available) + KP cusps + Vimshottari Dasha + Transit
in chart above. Health Qs vary widely (analyze/prevent/recover/chronic
× digestive/cardio/nervous/mental/repro × static/quality/risk/remedy).
Use this composable framework — do NOT try to apply every block.

⚠️  HARD GUARDS (non-negotiable):
  • NEVER name specific diseases (no "diabetes", "cancer", "tumor" etc.)
  • NEVER predict death / lifespan / exact illness-date / recovery-date
  • NEVER guarantee cure or 100% recovery
  • Mental/reproductive/parent/addiction Qs → softer tone + extra
    disclaimer (helpline / specialist consult primary).
  • If user asks for diagnosis or date → use the matching REFUSE block
    as the closer (it replaces remedy/closer line).

STEP 1 — Read user's Q and detect axes:
  ACTION:  analyze | prevent | recover | manage_chronic | mental_support
           | repro_support
  SYSTEM:  digestive | cardio | nervous | musculoskeletal | skin
           | endocrine | respiratory | immune | reproductive
  INTENT:  STATIC (vitality hai/kaisa) | QUALITY (tendency/aage risk)
           | RISK | REMEDY  [TIMING is REFUSED, not answered]
  EDGE:    parent_health | addiction | accident_risk | crisis

STEP 2 — Pick atomic CHECK BLOCKS that match the detected axes:
  • Pick ONE primary ACTION block.
  • If a SYSTEM block applies, ADD it (info-only, no diagnosis).
  • INTENT routing:
      - STATIC ('vitality kaisi? immunity strong?') → ADD [STATIC_VITALITY]
      - QUALITY ('aage chal ke kya risk? tendency batao?') → ADD [QUALITY_TENDENCY]
      - TIMING ('kab beemar honga? kab thik?') → ADD matching REFUSE block
  • RISK block: add if user's tone is worried OR asks 'dikkat / risk / khatra'.
  • REMEDY block: add ONE remedy in the closer (skip for REFUSE/CRISIS Qs).

STEP 3 — Apply ONLY the picked blocks (typical: 2-4 total). IGNORE the rest.
        NEVER stack STATIC_VITALITY + TIMING blocks together — pick ONE
        intent block based on what user actually asked.

WORKED EXAMPLES (do NOT copy verbatim — use to calibrate routing):
  ── STATIC (vitality existence) ──
  Q: "meri sehat kaisi hai chart me?"           → ANALYZE + STATIC_VITALITY
  Q: "vitality strong hai meri?"                → ANALYZE + STATIC_VITALITY
  Q: "immunity weak hai kya?"                   → ANALYZE + IMMUNE + STATIC_VITALITY + REMEDY

  ── QUALITY (tendency / aage risk) ──
  Q: "aage chal ke kya health risk hai?"        → PREVENT + QUALITY_TENDENCY + REMEDY
  Q: "kya kya bimariyon ki tendency hai?"       → PREVENT + QUALITY_TENDENCY + RISK
  Q: "future me chronic risk hai?"              → MANAGE_CHRONIC + QUALITY_TENDENCY

  ── SYSTEM-specific ──
  Q: "digestive issue ki tendency hai?"         → PREVENT + DIGESTIVE + QUALITY_TENDENCY + REMEDY
  Q: "stress aur anxiety ka chart me kya?"      → MENTAL_SUPPORT + STATIC_VITALITY + REMEDY
  Q: "santaan yog hai chart me?"                → REPRO_SUPPORT + REPRO_SYS + STATIC_VITALITY

  ── EDGE / SENSITIVE ──
  Q: "papa ki tabiyat kharab, chart se bata"    → PARENT_HEALTH + REMEDY
  Q: "sharab ki addiction se kaise nikalu?"     → ADDICTION + MENTAL_SUPPORT + REMEDY
  Q: "accident ka risk hai chart me?"           → ACCIDENT_RISK + RISK + REMEDY

  ── HARD REFUSALS ──
  Q: "mujhe kaun si bimari hai chart se bata"   → ANALYZE + REFUSE_DIAGNOSIS
  Q: "kab marunga main?"                        → REFUSE_DEATH (only)
  Q: "mera cancer thik hoga 100%?"              → REFUSE_CURE_GUARANTEE
  Q: "kab beemar honga?"                        → REFUSE_TIMING_DECLINE
  Q: "kab thik honga main?"                     → REFUSE_TIMING_RECOVERY
  Q: "operation kab karwau, muhurat?"           → REFUSE_SURGERY_MUHURAT
  Q: "khatam kar lu life"                       → CRISIS_REDIRECT (only)

ATOMIC CHECK BLOCKS (pick from these only):
"""


_ANSWER_STYLE = """
ANSWER STYLE (mandatory):
  • 100-150 words, 2-3 short Hinglish paragraphs. NO bullets. NO headers.
  • Cite ACTUAL planet names + house numbers from THIS chart — never invent.
    If a value is missing, say so honestly ('Lagnesh ka exact dignity nahi
    mil raha').
  • Translate Sanskrit inline: 'Lagnesh (1st lord)', 'Mangal (Mars)'.
  • End with ONE practical line — Vedic remedy OR a 1-line summary insight
    OR (for REFUSE blocks) the refuse-message itself as the closer.
  • For STATIC_VITALITY / QUALITY_TENDENCY: do NOT name dasha periods or
    use phrases like 'near term me movement', 'this phase me', 'abhi chal
    raha hai' — those are TIMING-only (and TIMING is refused for health).
    Stay on chart structure (Lagnesh, Sun-Moon, 6H/8H, karakas).
  • DOCTRINAL HEDGES (do NOT overstate):
      - Vargottama = STRONGLY supportive, not a guarantee.
      - Affliction by Saturn/Rahu = TENDENCY, not certainty.
      - 6H/8H involvement = vulnerability-zone, not diagnosis.
  • FORBIDDEN VOCABULARY in body (will be stripped post-hoc):
      - Specific disease names (diabetes, cancer, tumor, hiv, etc.)
      - "100%", "guaranteed cure", "definitely thik hoga"
      - Exact dates / months / years for illness or recovery
"""


# ── KILLSWITCH HELPERS ────────────────────────────────────────────────
def _focus_block_enabled() -> bool:
    """True UNLESS HEALTH_FOCUS_BLOCK explicitly disables. Default ON."""
    val = _os.environ.get("HEALTH_FOCUS_BLOCK", "").strip().lower()
    return val not in ("0", "false", "no", "off")


def _focus_axes_enabled() -> bool:
    """True UNLESS HEALTH_FOCUS_AXES explicitly disables. Default ON."""
    val = _os.environ.get("HEALTH_FOCUS_AXES", "").strip().lower()
    return val not in ("0", "false", "no", "off")


def _chart_slice_enabled() -> bool:
    """True UNLESS HEALTH_CHART_SLICE explicitly disables. Default ON."""
    val = _os.environ.get("HEALTH_CHART_SLICE", "").strip().lower()
    return val not in ("0", "false", "no", "off")


def _disclaimer_enabled() -> bool:
    """True UNLESS HEALTH_DISCLAIMER explicitly disables. Default ON."""
    val = _os.environ.get("HEALTH_DISCLAIMER", "").strip().lower()
    return val not in ("0", "false", "no", "off")


# ── HARD-GUARD PATTERNS (ported from health_static.health_routing) ───
# Order matters: CRISIS first (highest priority, overrides everything),
# then DEATH, then DIAGNOSIS_DEMAND, then TIMING variants, then CURE.
_CRISIS_RX = _re.compile(
    r"(suicide|khud[\s-]?kushi|atm[\s-]?hatya|atmhatya|"
    r"khatam\s+kar\s+(lu|du|dunga|loon)|"
    r"jeena\s+nahi\s+chahta|marna\s+chahta|"
    r"end\s+(my\s+)?life|kill\s+(myself|me))",
    _re.IGNORECASE,
)

_DEATH_RX = _re.compile(
    r"(kab\s+marunga|kab\s+marungi|kab\s+(meri|mera)\s+(maut|death|mrityu)|"
    r"meri\s+death\s+(kab|kaise)|life\s+span|kitne\s+saal\s+jiyu(?:nga|ngi)?|"
    r"umar\s+kitni|longevity|when\s+will\s+i\s+die|"
    r"kab\s+tak\s+(zinda|alive|jiunga|jiyungi)|"
    r"mrityu\s+(kab|samay|tarikh))",
    _re.IGNORECASE,
)

_DIAGNOSIS_DEMAND_RX = _re.compile(
    r"(mujhe\s+kya\s+(bimari|disease|illness)\s+(hai|hogi)|"
    r"kaun\s*si\s+(bimari|disease|illness)\s+(hai|hogi|hai\s+mujhe)|"
    r"mujhe\s+kaun\s*si\s+(bimari|disease|illness)|"
    r"diagnose\s+me|"
    r"chart\s+se\s+(bimari|disease|illness)\s+(bata|tell|name)|"
    r"chart\s+se\s+bata.{0,30}(bimari|disease|illness)|"
    r"chart\s+(me|mein)\s+(bimari|disease|illness)\s+(bata|name|kya))",
    _re.IGNORECASE,
)

_TIMING_DECLINE_RX = _re.compile(
    r"(kab\s+(beemar|bimar|sick|ill)\s+(honga|hungi|ho\s+jaunga)|"
    r"bimari\s+(kab|kis\s+saal|kis\s+mahine)|"
    r"disease\s+(kab|when)|"
    r"health\s+(kab\s+kharab|when\s+will\s+(deteriorate|fail))|"
    r"mujhe\s+kab\s+(bimari|disease|illness))",
    _re.IGNORECASE,
)

_TIMING_RECOVERY_RX = _re.compile(
    r"(kab\s+(thik|theek|swasth|healthy)\s+(honga|hungi|ho\s+jaunga|hounga)|"
    r"recovery\s+(date|kab|when)|"
    r"cure\s+(kab|when|date)|"
    r"bimari\s+(kab\s+jayegi|kab\s+thik|exit\s+date))",
    _re.IGNORECASE,
)

_TIMING_SURGERY_RX = _re.compile(
    r"(operation\s+(kab|date|muhurat|kis\s+din)|"
    r"surgery\s+(kab|date|muhurat|when)|"
    r"shastra[\s-]?kriya\s+kab|"
    r"muhurat\s+(operation|surgery))",
    _re.IGNORECASE,
)

_CURE_GUARANTEE_RX = _re.compile(
    r"(guarantee\s+(thik|cure|swasth|recover)|"
    r"100\s*(?:%|percent|prcnt|pct)\s+(thik|cure|recover|theek)|"
    r"(cancer|diabetes|tumour|tumor|hiv|aids)\s+(thik\s+ho|cure|theek))",
    _re.IGNORECASE,
)


def detect_hard_guard(question: str) -> Optional[str]:
    """Returns the matching REFUSE/CRISIS block tag if Q hits a hard
    guard, else None. Order = severity priority (CRISIS first).

    Order rationale: RECOVERY checked BEFORE DECLINE because phrases like
    "bimari kab jayegi" (bimari going away = recovery) are ambiguous
    against DECLINE's "bimari kab" pattern. RECOVERY's positive-direction
    cues take precedence."""
    if not isinstance(question, str) or not question.strip():
        return None
    if _CRISIS_RX.search(question):
        return "CRISIS_REDIRECT"
    if _DEATH_RX.search(question):
        return "REFUSE_DEATH"
    if _DIAGNOSIS_DEMAND_RX.search(question):
        return "REFUSE_DIAGNOSIS"
    # RECOVERY first (positive-direction cues like "kab thik", "kab jayegi")
    if _TIMING_RECOVERY_RX.search(question):
        return "REFUSE_TIMING_RECOVERY"
    if _TIMING_DECLINE_RX.search(question):
        return "REFUSE_TIMING_DECLINE"
    if _TIMING_SURGERY_RX.search(question):
        return "REFUSE_SURGERY_MUHURAT"
    if _CURE_GUARANTEE_RX.search(question):
        return "REFUSE_CURE_GUARANTEE"
    return None


# ── ACTION axis (pick ONE; first match wins) ──────────────────────────
_ACTION_PATTERNS = (
    ("REPRO_SUPPORT", _re.compile(
        r"\b(infertility|santaan|santan|baby|pregnan(?:cy|t)|conceive|"
        r"miscarriage|garbh|bachcha\s+(nahi|hone)|fertility|"
        r"reproductive|repro\b|maa\s+banna|pita\s+banna)\b",
        _re.IGNORECASE)),
    ("MENTAL_SUPPORT", _re.compile(
        r"\b(stress|anxiety|depression|tension|"
        r"mental\s+(health|peace|stress|state|wellness)|"
        r"man\s+(ashaant|udas|thik\s+nahi|pareshan|bechain)|"
        r"mood\s+(off|swing|low|depressed)|"
        r"udaasi|chinta|ghabrahat|panic|"
        r"neend\s+nahi|insomnia|sleep\s+(problem|nahi|kharab))\b",
        _re.IGNORECASE)),
    ("MANAGE_CHRONIC", _re.compile(
        r"\b(chronic|long[\s-]?term\s+(illness|problem|bimari)|"
        r"lambi\s+bimari|purani\s+bimari|"
        r"genetic\s+(disease|risk|history)|"
        r"family\s+history\s+(disease|illness)|hereditary|"
        r"life[\s-]?long|hamesha\s+rehta|reh\s+jata)\b",
        _re.IGNORECASE)),
    ("RECOVER", _re.compile(
        r"\b(recover|recovery|cure|healing|heal|"
        r"thik\s+(honga|hounga|ho\s+jaunga)|"
        r"bimari\s+(se\s+nikal|se\s+door)|"
        r"swasth\s+(honga|hounga))\b",
        _re.IGNORECASE)),
    ("PREVENT", _re.compile(
        r"\b(prevent|prevention|avoid|bachna|bachne|bachao|"
        r"future\s+risk|aage\s+(chal\s+ke|jaake)|aane\s+wale|"
        r"tendency|tendencies|kya\s+kya\s+(bimari|issues?)|"
        r"kaun[\s-]?kaun\s+(se|si)?\s*(health|bimari|issues?)|"
        r"probable|possible|likely\s+(health|illness|disease))\b",
        _re.IGNORECASE)),
)
# ANALYZE = default (no explicit verb match)


# ── SYSTEM axis (0+ matches, ADD modifiers) ───────────────────────────
_SYSTEM_PATTERNS = (
    ("DIGESTIVE", _re.compile(
        r"\b(digest(?:ion|ive)?|pet|stomach|acidity|gas|"
        r"intestine|aant|appetite|bhook|hazme|hajma|"
        r"liver|jigar|kidney|gurda)\b",
        _re.IGNORECASE)),
    ("CARDIO", _re.compile(
        r"\b(heart|dil|cardiac|cardio|"
        r"blood\s+pressure|bp\b|hypertension|"
        r"chest\s+(pain|discomfort)|seene\s+me)\b",
        _re.IGNORECASE)),
    ("NERVOUS", _re.compile(
        r"\b(nerve|nerves|nervous|neurolog|"
        r"jhanjhanahat|tingling|numbness|sunn\s+pad|"
        r"brain|dimag|cognitive)\b",
        _re.IGNORECASE)),
    ("MUSCULOSKELETAL", _re.compile(
        r"\b(joint|jod|jodo|knee|ghutna|back\s*pain|kamar|"
        r"bone|haddi|haddiyan|spine|reedh|"
        r"muscle|maans|cramp|akadan|stiffness|"
        r"arthritis\b|gathiya|orthop)\b",
        _re.IGNORECASE)),
    ("SKIN", _re.compile(
        r"\b(skin|chamdi|twacha|rash|allergy\s+(?:skin)?|"
        r"acne|pimple|kil|muhase|"
        r"eczema|psoriasis|daag|patch)\b",
        _re.IGNORECASE)),
    ("ENDOCRINE", _re.compile(
        r"\b(thyroid|hormone|hormonal|"
        r"sugar(?:\s+level)?|metabolism|metabolic|"
        r"weight\s+(gain|loss)|wajan|motapa|"
        r"pcod|pcos|endocrin)\b",
        _re.IGNORECASE)),
    ("RESPIRATORY", _re.compile(
        r"\b(breath|breathing|saans|saans\s+phool|"
        r"asthma|dama|"
        r"lung|phephra|"
        r"cough|khansi|cold|sardi|zukam|"
        r"chest\s+infect|nasal|nose\s+block)\b",
        _re.IGNORECASE)),
    ("IMMUNE", _re.compile(
        r"\b(immunity|immune|"
        r"baar[\s-]?baar\s+(beemar|bimar|sick|ill)|"
        r"jaldi[\s-]?jaldi\s+(beemar|bimar|sick)|"
        r"frequently\s+(sick|ill)|"
        r"rog[\s-]?pratirodh|"
        r"resistance|stamina)\b",
        _re.IGNORECASE)),
    ("REPRO_SYS", _re.compile(
        r"\b(reproductive|fertility|santaan|santan|"
        r"period|menstrual|periods\s+(?:irregular|miss)|"
        r"prostate|sperm|ovary|uterus|garbhashay)\b",
        _re.IGNORECASE)),
)


# ── EDGE axis (0+ matches) ────────────────────────────────────────────
_EDGE_PATTERNS = (
    ("ACCIDENT_RISK", _re.compile(
        r"\b(accident\s+(risk|chance|hoga|honga|ka\s+yog)?|"
        r"injury\s+(risk|chance|hoga)?|"
        r"chot\s+(lagne|ka\s+yog|risk)?|"
        r"physical\s+(harm|safety|injury)|"
        r"durghatna|fall\s+down|gir(?:na|enge|jaunga))\b",
        _re.IGNORECASE)),
    ("PARENT_HEALTH", _re.compile(
        r"\b(papa|mummy|mother|father|maa|maaji|pita|pitaji|parent[s]?|"
        r"mom\b|dad\b|mata\b|mataji)\s+"
        r"(ki\s+|ke\s+|ka\s+)?"
        r"(health|sehat|bimari|illness|tabiyat|swasthya|tabiyyat)",
        _re.IGNORECASE)),
    ("ADDICTION", _re.compile(
        r"\b(addiction|nasha|nashedi|alcohol|sharab|"
        r"smoking|cigarette|cigarrette|"
        r"drug[s]?|tambaku|tobacco|gutka|paan\s+masala|"
        r"substance\s+abuse|de[\s-]?addict)\b",
        _re.IGNORECASE)),
)


# ── INTENT detection (STATIC vs QUALITY) ──────────────────────────────
# TIMING is handled by hard-guards (REFUSE_TIMING_*). For non-refused
# Qs we only need STATIC vs QUALITY split.
_QUALITY_TRIGGER_RX = _re.compile(
    r"\b(tendency|tendencies|aage\s+(chal\s+ke|jaake)|"
    r"future\s+(me|risk)|aane\s+wale|"
    r"kya\s+kya\s+(bimari|issues?|risk)|"
    r"kaun[\s-]?kaun\s+(se|si)?\s*(health|bimari|issues?)|"
    r"probable|possible|likely|"
    r"prone\s+to|risk\s+(profile|areas?|zones?))\b",
    _re.IGNORECASE,
)

_RISK_RX = _re.compile(
    r"\b(dikkat|nuksan|nuqsan|risk|risky|jokhim|loss|"
    r"problem|issue|trouble|danger|khatra|khatre|"
    r"weak|kamzor|kamzori|kharab|"
    r"worry|worried|chinta|tension|"
    r"galat|wrong|unsafe)\b",
    _re.IGNORECASE,
)


# ── SENSITIVE bucket detection (extra-soft tone signal) ───────────────
_SENSITIVE_BUCKETS = (
    ("mental_health", _re.compile(
        r"\b(stress|anxiety|depression|tension|"
        r"mental|man\s+ashaant|udas|udaasi|chinta|"
        r"mood|ghabrahat|panic|insomnia|neend|sleep)\b",
        _re.IGNORECASE)),
    ("reproductive", _re.compile(
        r"\b(infertility|santaan|santan|baby|pregnancy|conceive|"
        r"miscarriage|garbh|bachcha\s+(nahi|hone)|fertility)\b",
        _re.IGNORECASE)),
    ("parent_health", _re.compile(
        r"\b(papa|mummy|mother|father|maa|pita|parent[s]?)\s+"
        r"(ki\s+|ke\s+|ka\s+)?(health|sehat|bimari|illness|tabiyat)",
        _re.IGNORECASE)),
    ("addiction", _re.compile(
        r"\b(addiction|nasha|alcohol|sharab|smoking|cigarette|"
        r"drug[s]?|tambaku|tobacco|gutka|substance\s+abuse)\b",
        _re.IGNORECASE)),
)


def detect_sensitive_bucket(question: str) -> Optional[str]:
    """Returns sensitive-bucket name if Q matches one, else None."""
    if not isinstance(question, str):
        return None
    for name, rx in _SENSITIVE_BUCKETS:
        if rx.search(question):
            return name
    return None


# ── HEALTH-TOPIC GATE (port from health_static.health_routing) ────────
_HEALTH_TOPIC_RX = _re.compile(
    r"\b("
    r"health|sehat|swasthya|swasth|tabiyat|tabiyyat|"
    r"body|sharir|sharirik|"
    r"beemar|bimar|bimari|illness|disease|sick|"
    r"rog|rogi|"
    r"vitality|immunity|stamina|energy|"
    r"strength|weak|kamzor|kamzori|"
    r"recovery|recover|cure|thik|theek|"
    r"chronic|long[\s-]?term|lambi|purani|"
    r"stress|anxiety|depression|mental|"
    r"man|mood|tension|chinta|"
    r"ashaant|udas|udaasi|pareshan|bechain[ai]?|ghabrahat|"
    r"neend|sleep|insomnia|"
    r"ajeeb|ajib|uneasy|weird|strange|unsettled|"
    r"khali\s*sa|khaali\s*sa|theek\s*nahi\s*lagta|"
    r"sardi|zukam|jukam|khansi|kha?ansi|cold|cough|fever|"
    r"bukhar|jukham|gala|throat|"
    r"pet|stomach|acidity|gas|digest|"
    r"sirdard|headache|migraine|"
    r"thakan|fatigue|tiredness|kamzori|weakness|"
    r"accident|injury|chot|durghatna|"
    r"infertility|santaan|santan|fertility|pregnancy|conceive|"
    r"addiction|nasha|sharab|smoking|"
    r"arishta|balarishta|vipreet[\s-]?recovery|"
    r"swasthya|aarogya|arogya"
    r")\b",
    _re.IGNORECASE,
)

# Animal/pet absolute-non-health context.
_ABSOLUTE_NON_HEALTH_RX = _re.compile(
    r"\b(kutta|kuttiya|billi|dog|cat|janwar|"
    r"animal|puppy|kitten|paalt(u|oo))\b",
    _re.IGNORECASE,
)

_AMBIGUOUS_HEALTH_TOKENS_RX = _re.compile(
    r"\b(weakness|kamzori|kamzor|thakan|tiredness|fatigue|"
    r"pet|cold|cough|strange|weird|unsettled)\b",
    _re.IGNORECASE,
)

_STRONG_HEALTH_RX = _re.compile(
    r"\b(body|sharir|sharirik|sehat|tabiyat|swasthya|swasth|"
    r"health|bimari|bimar|beemar|illness|medical|disease|"
    r"stomach|acidity|digestion|digest|sirdard|headache|migraine|"
    r"sardi|zukam|jukam|fever|bukhar|"
    r"immunity|stamina|recovery|chronic|"
    r"stress|anxiety|depression|insomnia|"
    r"ghabrahat|bechain[ai]?|"
    r"man|mood|mental|"
    r"neend|sleep|"
    r"ajeeb\s+(sa|si)?\s*feel|"
    r"gala\s*kharab|"
    r"khansi|throat)\b",
    _re.IGNORECASE,
)

_NON_HEALTH_CTX_RX = _re.compile(
    r"\b(career|kaa?riyar|business|job|office|kaam(?!\s*nahi)|naukri|"
    r"spiritual|aatmik|aatma\b|atma\b|sadhana|dhyan(?!\s+dena)|"
    r"relationship|rishta|partner|love|pyaar|"
    r"financial|paisa|paise|money|wealth|dhan|"
    r"willpower|will\s*power|determination|motivation)\b",
    _re.IGNORECASE,
)


def is_health_question(question: str) -> bool:
    """True if Q is about general health AND not pure-finance/career/etc.
    Mirrors health_static.health_routing.is_health_question logic."""
    if not isinstance(question, str) or not question.strip():
        return False
    # 1. Absolute non-health context wins (pet animals)
    if _ABSOLUTE_NON_HEALTH_RX.search(question):
        return False
    # 2. Hard-guard patterns ALWAYS owned by health (so refuse fires)
    if detect_hard_guard(question) is not None:
        return True
    # 3. Health topic keyword present?
    if not _HEALTH_TOPIC_RX.search(question):
        return False
    # 4. Ambiguous-only context guard
    if (_AMBIGUOUS_HEALTH_TOKENS_RX.search(question)
            and not _STRONG_HEALTH_RX.search(question)
            and _NON_HEALTH_CTX_RX.search(question)):
        return False
    return True


# ── AXES DETECTOR ─────────────────────────────────────────────────────
def detect_health_axes(question: str) -> Dict[str, Any]:
    """Detect health Q axes server-side. Returns dict with keys:
      action:    str   — exactly one ATOMIC_CHECKS ACTION key.
      systems:   list  — 0+ SYSTEM keys.
      intent:    str   — STATIC_VITALITY | QUALITY_TENDENCY.
      edges:     list  — 0+ EDGE keys.
      appendix:  list  — 0+ of {RISK, REMEDY}.
      hard_guard:str|None — REFUSE_*/CRISIS_REDIRECT tag if any.
      sensitive: str|None — sensitive-bucket name if any.

    Defensive: invalid input → ANALYZE + STATIC_VITALITY + REMEDY."""
    safe_default = {
        "action":     "ANALYZE",
        "systems":    [],
        "intent":     "STATIC_VITALITY",
        "edges":      [],
        "appendix":   ["REMEDY"],
        "hard_guard": None,
        "sensitive":  None,
    }
    if not isinstance(question, str) or not question.strip():
        return safe_default
    q = question

    # ── HARD GUARD (highest priority — short-circuits intent) ──
    hard = detect_hard_guard(q)

    # ── ACTION (first match wins; ANALYZE if none) ──
    action = "ANALYZE"
    for tag, rx in _ACTION_PATTERNS:
        if rx.search(q):
            action = tag
            break

    # ── SYSTEMS (collect all matches; preserve declaration order) ──
    systems = [tag for tag, rx in _SYSTEM_PATTERNS if rx.search(q)]

    # ── EDGES ──
    edges = [tag for tag, rx in _EDGE_PATTERNS if rx.search(q)]

    # ── INTENT (STATIC vs QUALITY; TIMING is hard-guarded above) ──
    if _QUALITY_TRIGGER_RX.search(q):
        intent = "QUALITY_TENDENCY"
    else:
        intent = "STATIC_VITALITY"

    # ── APPENDIX ──
    appendix = []
    if _RISK_RX.search(q):
        appendix.append("RISK")
    # REMEDY: always-on EXCEPT for CRISIS (replaces everything) and
    # REFUSE_DEATH (refuse line is the closer).
    if hard not in ("CRISIS_REDIRECT", "REFUSE_DEATH"):
        appendix.append("REMEDY")

    return {
        "action":     action,
        "systems":    systems,
        "intent":     intent,
        "edges":      edges,
        "appendix":   appendix,
        "hard_guard": hard,
        "sensitive":  detect_sensitive_bucket(q),
    }


# ── COMPOSER (axes-routed compact block) ──────────────────────────────
_AXES_FRAMEWORK_HEADER = """FOCUS — HEALTH ANALYSIS (server pre-routed for this Q).

You have D1 + (D9 if available) + KP cusps + Vimshottari Dasha + Transit
in chart above. Server has detected this Q's axes and selected the
relevant CHECK blocks below. Apply ONLY these blocks (not the full
health doctrine). Cite ACTUAL planet names + house numbers from THIS
chart — never invent.

⚠️  HARD GUARDS still apply: NO disease names, NO death prediction,
NO cure guarantee, NO illness/recovery dates. If a REFUSE_* block is
present, USE its message as the closer (it replaces remedy/closer).

ROUTED CHECK BLOCKS for this Q:
"""


def _atomic_blocks_dump() -> str:
    """Render all atomic blocks as a [TAG] line list."""
    return "\n".join(f"  [{k}] {v}" for k, v in ATOMIC_CHECKS.items())


def _picked_atomic_blocks_dump(picked: List[str]) -> str:
    """Render a subset of ATOMIC_CHECKS as [TAG] lines, preserving
    caller-provided order. Unknown tags silently skipped."""
    return "\n".join(
        f"  [{k}] {ATOMIC_CHECKS[k]}" for k in picked if k in ATOMIC_CHECKS
    )


_AXES_FALLBACK_COUNT = 0


def build_health_focus(question: str = "") -> str:
    """Return the health-focus block.

    When HEALTH_FOCUS_AXES is enabled (default ON) AND a non-empty
    question is provided, returns a COMPACT axes-routed block (~1.5-2.5
    KB) containing only the matched atomic CHECK blocks.

    When disabled OR question is empty, returns the FAT block (~6 KB)
    with all atomic blocks for the LLM to self-route.

    Defensive: any detection error → fat-block fallback (NEVER blocks)."""
    if not _focus_axes_enabled() or not (
        isinstance(question, str) and question.strip()
    ):
        return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE

    try:
        axes = detect_health_axes(question)

        # CRISIS → only the crisis block (skip all chart talk)
        if axes["hard_guard"] == "CRISIS_REDIRECT":
            return (
                _AXES_FRAMEWORK_HEADER
                + _picked_atomic_blocks_dump(["CRISIS_REDIRECT"])
                + "\n"
                + _ANSWER_STYLE
            )

        picked: List[str] = [axes["action"]]
        picked.extend(axes["systems"])
        picked.extend(axes["edges"])

        # REFUSE_DEATH = closer-only (skip intent + remedy)
        if axes["hard_guard"] == "REFUSE_DEATH":
            picked.append("REFUSE_DEATH")
        elif axes["hard_guard"] is not None:
            # Other REFUSE blocks: keep intent + risk, replace remedy with refuse
            picked.append(axes["intent"])
            if "RISK" in axes["appendix"]:
                picked.append("RISK")
            picked.append(axes["hard_guard"])
        else:
            picked.append(axes["intent"])
            picked.extend(axes["appendix"])

        # Dedup preserving order
        seen = set()
        picked_unique = []
        for tag in picked:
            if tag in ATOMIC_CHECKS and tag not in seen:
                seen.add(tag)
                picked_unique.append(tag)

        if not picked_unique:
            return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE

        return (
            _AXES_FRAMEWORK_HEADER
            + _picked_atomic_blocks_dump(picked_unique)
            + "\n"
            + _ANSWER_STYLE
        )
    except Exception as _exc:  # noqa: BLE001
        global _AXES_FALLBACK_COUNT
        _AXES_FALLBACK_COUNT += 1
        print(
            f"[health_focus_routing][AXES_FALLBACK={_AXES_FALLBACK_COUNT}] "
            f"err={str(_exc)[:160]} → fat-block fallback"
        )
        return _FRAMEWORK_HEADER + _atomic_blocks_dump() + "\n" + _ANSWER_STYLE


# ── CHART SLICER (drop dasha sections for STATIC/QUALITY) ─────────────
# Health STATIC_VITALITY / QUALITY_TENDENCY answers don't need dasha
# tree (Sec 4), upcoming dasha (Sec 5), gochar (Sec 8), or
# dasha+transit overlay (Sec 9). Trim BEFORE LLM call → cleaner prompt
# + fewer dasha-leaks. NO-OP when hard-guard is TIMING (refuse blocks
# need full chart available) — actually NO-OP for TIMING never applies
# since timing is refused; we slice for ALL non-refuse health Qs.

_DASHA_SECTION_NUMS = frozenset({"4", "5", "8", "9"})
_SECTION_BOUNDARY_RX = _re.compile(r'(?=^## \d+\.)', _re.MULTILINE)
_SECTION_NUM_RX = _re.compile(r'^## (\d+)\.')


def trim_dasha_sections(chart_block: str, question: str) -> Tuple[str, int]:
    """Drop dasha/transit sections from chart-context for health Qs.
    Returns (trimmed_block, sections_dropped). Defensive NO-OP on
    pattern mismatch or empty input."""
    if not isinstance(chart_block, str) or not chart_block.strip():
        return chart_block, 0
    if not _chart_slice_enabled():
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


# ── POST-INJECTORS ────────────────────────────────────────────────────
# H3.P1 — mandatory medical disclaimer (always-on for health answers).
_DISCLAIMER_LINE = (
    "\n\n_⚕️ Yeh chart-based insight hai, medical advice nahi. "
    "Kisi bhi health concern ke liye qualified doctor se zaroor milein._"
)

# Specialised disclaimers for sensitive buckets
_SENSITIVE_DISCLAIMERS = {
    "mental_health": (
        "\n\n_💚 Agar aap distress me ho — iCall +91-9152987821 "
        "ya Vandrevala +91-1860-2662-345 (24/7 free helpline) pe baat karo. "
        "Yeh chart-based insight hai, professional therapy nahi._"
    ),
    "reproductive": (
        "\n\n_⚕️ Yeh chart-based energetic-tendency hai, fertility advice nahi. "
        "Kisi qualified gynaecologist / fertility-specialist se zaroor milein._"
    ),
    "parent_health": (
        "\n\n_⚕️ Yeh chart-based supportive insight hai. Parent ki tabiyat ke "
        "liye immediate doctor consult primary hai — chart sirf ek dimension hai._"
    ),
    "addiction": (
        "\n\n_💚 Addiction recovery ke liye AA/NA support groups + qualified "
        "counsellor primary path hain. Chart sirf ek perspective deta hai. "
        "Bhai akele mat ladho — help leni strength hai._"
    ),
}

# H3.P2 — strip forbidden vocabulary from answer body
_DISEASE_NAME_RX = _re.compile(
    r"\b(diabetes|cancer|tumour|tumor|hiv|aids|"
    r"alzheimer|parkinson|hepatitis|tuberculosis|tb\b|"
    r"leukemia|leukaemia|lymphoma|carcinoma|sarcoma)\b",
    _re.IGNORECASE,
)

_CURE_GUARANTEE_OUTPUT_RX = _re.compile(
    r"\b(100\s*%\s+(?:cure|thik|recover|theek)|"
    r"guaranteed?\s+(?:cure|recovery|thik|theek)|"
    r"definitely\s+(?:thik|theek|cure|recover))\b",
    _re.IGNORECASE,
)


def strip_forbidden_vocab(text: str) -> Tuple[str, int]:
    """Replace forbidden disease names + cure-guarantee phrasings with
    safe alternatives. Returns (cleaned_text, replacements_made)."""
    if not isinstance(text, str) or not text.strip():
        return text, 0
    count = 0
    new = text

    def _disease_repl(m: _re.Match) -> str:
        nonlocal count
        count += 1
        return "specific condition"

    new = _DISEASE_NAME_RX.sub(_disease_repl, new)

    def _cure_repl(m: _re.Match) -> str:
        nonlocal count
        count += 1
        return "supportive recovery-tendency"

    new = _CURE_GUARANTEE_OUTPUT_RX.sub(_cure_repl, new)
    return new, count


def inject_medical_disclaimer(answer_text: str, question: str) -> str:
    """H3.P1 post-injector — append the mandatory medical disclaimer
    (sensitive-bucket-specific if applicable) to the answer body.
    Idempotent: skips if disclaimer marker already present.

    Killswitch: HEALTH_DISCLAIMER=0/false/no/off → NO-OP.
    """
    if not _disclaimer_enabled():
        return answer_text
    if not isinstance(answer_text, str):
        return answer_text
    # Idempotency check (look for the unique marker emoji + key phrase)
    if ("⚕️ Yeh chart-based" in answer_text
            or "💚 Agar aap distress" in answer_text
            or "💚 Addiction recovery" in answer_text):
        return answer_text
    bucket = detect_sensitive_bucket(question)
    disc = _SENSITIVE_DISCLAIMERS.get(bucket, _DISCLAIMER_LINE)
    return (answer_text or "").rstrip() + disc


def inject_health_engine_verdict(answer_text: str,
                                   question: str = "") -> str:
    """Deterministic Health Engine v1 post-injector.

    If the most recent `compute_health_window()` produced a verdict on
    this thread (stashed by `health_engine_v1.get_last_health_result()`),
    enforce a `👉 Final:` line near the end of the answer carrying the
    engine verdict + recommendation tier verbatim. This is the safety
    net for cases where the LLM either skips the verdict or paraphrases
    it (mirrors the Marriage NARRATOR-MODE enforcement).

    Idempotent: if the engine line already appears, no change. If no
    engine result is cached (engine wasn't run for this Q), no-op.
    Killswitch: HEALTH_DISCLAIMER off → no-op (same env as the rest of
    the H3 post-injector pipeline).
    """
    if not answer_text:
        return answer_text or ""
    if not _disclaimer_enabled():
        return answer_text
    try:
        from event_timing.health.health_engine_v1 import (  # type: ignore
            get_last_health_result,
        )
    except Exception:
        return answer_text
    res = get_last_health_result()
    if not isinstance(res, dict) or not res.get("verdict"):
        return answer_text
    verdict = str(res.get("verdict") or "").strip()
    tier = str(res.get("recommendation_tier") or "").strip()
    if not verdict:
        return answer_text
    # Architect-fix: never inject for UNKNOWN gates (data missing /
    # engine exception) — those should fall through to the LLM's own
    # framing rather than nailing a generic "saaf reading nahi" line
    # onto every answer where the engine couldn't compute.
    if verdict == "UNKNOWN":
        return answer_text
    # Idempotency — bail if our exact tag already present
    tag = "[engine: health-v1]"
    if tag in answer_text:
        return answer_text
    # Architect-fix: if the LLM already produced a "👉 Final:" line, strip
    # it so the engine line becomes the authoritative final (avoid
    # duplicate finals stacking).
    body = answer_text
    try:
        import re as _re
        body = _re.sub(r"(?m)^\s*👉\s*Final:.*(?:\n|$)", "", body).rstrip()
    except Exception:
        body = answer_text
    # Gentle, non-clinical phrasing (CAFB-health translation rules).
    verdict_label = {
        "STRONG_VITALITY":   "swasthya bal majboot dikh raha hai",
        "STABLE":            "swasthya stable lag raha hai",
        "VULNERABLE":        "swasthya pe abhi extra dhyan ki zarurat hai",
        "HIGH_RISK_WINDOW":  "swasthya ko abhi sambhal ke chalna chahiye",
        "UNKNOWN":           "swasthya ki saaf reading nahi mil rahi",
    }.get(verdict, verdict.lower())
    tier_label = {
        "monitor":         "rozmarra ki monitoring kafi hai",
        "preventive":      "preventive habits + routine check-up rakhein",
        "consult":         "ek bar professional doctor se baat kar lijiye",
        "urgent_consult":  "jaldi kisi qualified doctor se mil lijiye",
    }.get(tier, tier)
    line = f"\n\n👉 Final: {verdict_label} — {tier_label}. {tag}"
    return body.rstrip() + line


def apply_health_postinjectors(answer_text: str, question: str) -> str:
    """Convenience: run all health post-injectors in correct order.
    1. strip_forbidden_vocab (clean body)
    2. inject_health_engine_verdict (engine-fact citation safety net)
    3. inject_medical_disclaimer (append safety footer)
    """
    cleaned, _ = strip_forbidden_vocab(answer_text)
    cleaned = inject_health_engine_verdict(cleaned, question)
    return inject_medical_disclaimer(cleaned, question)


# ── PUBLIC API SUMMARY ────────────────────────────────────────────────
__all__ = [
    "ATOMIC_CHECKS",
    "build_health_focus",
    "detect_health_axes",
    "detect_hard_guard",
    "detect_sensitive_bucket",
    "is_health_question",
    "trim_dasha_sections",
    "strip_forbidden_vocab",
    "inject_medical_disclaimer",
    "inject_health_engine_verdict",
    "apply_health_postinjectors",
]
