"""Practical Resources — Phase 3.0 Practical Booster Pack (May 7 2026).

Verified India-specific real-world resources — helplines, government
schemes, free tools, official portals — that the Remedy Engine surfaces
ALONGSIDE the planet-keyed practical/ayurvedic/vedic stack.

Why this exists
---------------
User mandate (May 7 2026): "Vedic remedy hamesha kaam nehi karta — kuch
aisa chahiye jisme logo ki actual help ho." A mantra cannot replace a
suicide-prevention helpline, an SIP, a CIBIL fix, or a NALSA free lawyer.
This module is the engine's promise that EVERY remedy block also surfaces
at least one verified, reachable, cost-transparent real-world lever the
user can act on TODAY.

Design locks
------------
- ONLY verified Indian government / public-trust / well-known resources.
  Phone numbers, URLs, scheme names are official. No app/influencer
  recommendations that could rot.
- Every entry carries `why` (one-line value), `free` flag, `cost_inr`
  (0 if free), and a topic/area/severity gate.
- Severity-aware: urgent_consult / consult tiers always surface a
  crisis-level resource FIRST (suicide hotline, cybercrime, women safety).
- Demographic-aware (`applies_to`): women-specific / senior / general so
  an 18-yr-old isn't shown SCSS pension scheme or vice versa.
- Cap output at 3 resources per call so the locked_facts block stays
  scannable. Crisis resources always win the tie-break.

Public API
----------
    get_practical_resources(topic, areas, severity, user_facts) -> list

Returns: list[dict] (≤3) ready for renderer or JSON consumption. Each
dict has: label, kind, value, why, free, cost_inr.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


# ────────────────────────────────────────────────────────────────────────
# Resource catalog — VERIFIED India-specific only
# ────────────────────────────────────────────────────────────────────────
# Schema:
#   "id": {
#       "label":       "human-readable name",
#       "kind":        "helpline" | "govt_scheme" | "free_tool" |
#                       "directory" | "legal_aid",
#       "value":       "phone OR url OR scheme handle",
#       "why":         "one-line reason this matters",
#       "free":        bool,
#       "cost_inr":    0 if free else ballpark int,
#       "for_topics":  ["health", "money", ...]  # empty = all topics
#       "for_areas":   ["anxiety", "debt", ...]  # empty = topic-default
#       "for_severity":["urgent_consult", ...]   # empty = any severity
#       "applies_to":  "all" | "women" | "senior" | "youth" | "founder"
#       "crisis":      bool   # if True, always-rank-first when triggered
#   }

_RESOURCES: Dict[str, Dict[str, Any]] = {

    # ════════════════════════════════════════════════════════════════
    # CRISIS HELPLINES (always rank first when triggered)
    # ════════════════════════════════════════════════════════════════
    "kiran_mental_health": {
        "label":        "KIRAN — Govt of India Mental Health Helpline",
        "kind":         "helpline",
        "value":        "1800-599-0019 (24×7, 13 languages, free)",
        "why":          "Free anonymous govt helpline; trained counsellors; calls don't appear on bill.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health", "marriage", "career", "money", "business"],
        "for_areas":    ["mind", "anxiety", "nervous", "chronic", "founders_fit"],
        "for_severity": ["consult", "urgent_consult", "watchful"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "telemanas_nimhans": {
        "label":        "Tele-MANAS (NIMHANS-backed mental health)",
        "kind":         "helpline",
        "value":        "14416 OR 1-800-891-4416 (24×7, free)",
        "why":          "Govt-of-India + NIMHANS clinical backbone; psychiatrist referral built-in.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health"],
        "for_areas":    ["mind", "anxiety", "nervous", "chronic"],
        "for_severity": ["consult", "urgent_consult"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "icall_tiss": {
        "label":        "iCall (TISS-run psychosocial helpline)",
        "kind":         "helpline",
        "value":        "9152987821 (Mon–Sat 8am–10pm) | icallhelpline.org",
        "why":          "TISS-trained counsellors, email + chat options for those who can't call.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health", "marriage", "career"],
        "for_areas":    ["mind", "anxiety", "communication", "trust", "founders_fit"],
        "for_severity": ["consult", "urgent_consult", "watchful"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "aasra_suicide": {
        "label":        "AASRA Suicide Prevention",
        "kind":         "helpline",
        "value":        "91-9820466726 (24×7, all languages, free, confidential)",
        "why":          "Highest-priority crisis resource — no judgement, no log, no bill.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health"],
        "for_areas":    ["mind", "anxiety", "chronic", "nervous"],
        "for_severity": ["urgent_consult"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "vandrevala_24x7": {
        "label":        "Vandrevala Foundation — 24×7 Mental Health",
        "kind":         "helpline",
        "value":        "1860-2662-345 (24×7, free, all India)",
        "why":          "Privately-funded but free; psychiatrist-backed; WhatsApp option.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health", "marriage"],
        "for_areas":    ["mind", "anxiety", "chronic", "trust"],
        "for_severity": ["consult", "urgent_consult"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "women_helpline_181": {
        "label":        "Women in Distress — National Helpline",
        "kind":         "helpline",
        "value":        "181 (24×7, free, all India)",
        "why":          "Domestic violence, harassment, dowry — direct route to OSC (One Stop Centre) + police escort.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["marriage", "health"],
        "for_areas":    ["harmony", "trust", "in-laws", "communication", "anxiety"],
        "for_severity": ["watchful", "consult", "urgent_consult", "supportive"],
        "applies_to":   "women",
        "crisis":       True,
    },
    "police_112": {
        "label":        "All-India Emergency (Police / Ambulance / Fire)",
        "kind":         "helpline",
        "value":        "112 (24×7, free)",
        "why":          "Single-number ERSS — works even with locked SIM / no balance.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health", "marriage"],
        "for_areas":    ["accident_risk", "harmony", "trust"],
        "for_severity": ["urgent_consult"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "cybercrime_1930": {
        "label":        "Cybercrime / Financial Fraud Helpline",
        "kind":         "helpline",
        "value":        "1930 (24×7) | cybercrime.gov.in",
        "why":          "Report financial fraud within 1 hour → 80%+ chance of freezing the transaction.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money", "business"],
        "for_areas":    ["debt", "savings", "investing", "expense_control",
                         "credit_score", "cashflow", "legal_compliance"],
        "for_severity": ["watchful", "consult", "supportive"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "senior_helpline_14567": {
        "label":        "Elderline — Senior Citizen Helpline",
        "kind":         "helpline",
        "value":        "14567 (Mon–Sat 8am–8pm, free, 17 states+UTs)",
        "why":          "Pension issues, elder abuse, loneliness, healthcare nav — single point of contact.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health", "money", "marriage"],
        "for_areas":    ["chronic", "joints", "savings", "harmony"],
        "for_severity": [],
        "applies_to":   "senior",
        "crisis":       False,
    },
    "childline_1098": {
        "label":        "Childline India",
        "kind":         "helpline",
        "value":        "1098 (24×7, free)",
        "why":          "Child abuse, missing child, child labour, education emergency — verified-NGO-backed.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["marriage", "health"],
        "for_areas":    ["harmony", "in-laws", "communication"],
        "for_severity": ["urgent_consult", "consult"],
        "applies_to":   "all",
        "crisis":       True,
    },
    "consumer_1800_11_4000": {
        "label":        "National Consumer Helpline",
        "kind":         "helpline",
        "value":        "1800-11-4000 / 1915 | consumerhelpline.gov.in",
        "why":          "Refunds, defective products, fake e-commerce — pre-court resolution route.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money", "business"],
        "for_areas":    ["expense_control", "debt", "investing", "partnerships"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },

    # ════════════════════════════════════════════════════════════════
    # GOVERNMENT SCHEMES (verified, official only)
    # ════════════════════════════════════════════════════════════════
    "ayushman_bharat": {
        "label":        "Ayushman Bharat PM-JAY",
        "kind":         "govt_scheme",
        "value":        "pmjay.gov.in | helpline 14555",
        "why":          "₹5 lakh/year cashless health cover per family — eligibility check 30 sec on portal.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health", "money"],
        "for_areas":    ["heart", "chronic", "joints", "kidneys", "liver",
                         "auto-immune", "savings", "debt"],
        "for_severity": ["consult", "urgent_consult", "watchful"],
        "applies_to":   "all",
        "crisis":       False,
    },
    "jan_aushadhi": {
        "label":        "Pradhan Mantri Jan Aushadhi (PMBJP)",
        "kind":         "govt_scheme",
        "value":        "janaushadhi.gov.in (find nearest store)",
        "why":          "Same-molecule generic medicines at 50–90% lower price; 11,000+ stores nationwide.",
        "free":         False,
        "cost_inr":     0,
        "for_topics":   ["health", "money"],
        "for_areas":    ["chronic", "heart", "blood", "joints", "kidneys",
                         "auto-immune", "expense_control", "savings"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "scss_senior_savings": {
        "label":        "SCSS — Senior Citizen Savings Scheme (Post Office)",
        "kind":         "govt_scheme",
        "value":        "Any post office / SBI / PNB; 8.2% (Q1 2026), max ₹30L deposit",
        "why":          "Sovereign-guaranteed quarterly payout for 60+; safer + higher than most FDs.",
        "free":         False,
        "cost_inr":     0,
        "for_topics":   ["money"],
        "for_areas":    ["savings", "investing", "income_growth", "emergency_fund"],
        "for_severity": [],
        "applies_to":   "senior",
        "crisis":       False,
    },
    "pmvvy_pension": {
        "label":        "PMVVY — Pradhan Mantri Vaya Vandana Yojana",
        "kind":         "govt_scheme",
        "value":        "LIC branches; check current intake window",
        "why":          "Govt-backed monthly pension for 60+; complements SCSS for income laddering.",
        "free":         False,
        "cost_inr":     0,
        "for_topics":   ["money"],
        "for_areas":    ["savings", "income_growth", "emergency_fund"],
        "for_severity": [],
        "applies_to":   "senior",
        "crisis":       False,
    },
    "nps_retirement": {
        "label":        "NPS — National Pension System",
        "kind":         "govt_scheme",
        "value":        "enps.nsdl.com (10-min eNPS account)",
        "why":          "Extra ₹50K tax deduction (80CCD-1B) on top of 80C; lowest-cost equity exposure for retirement.",
        "free":         False,
        "cost_inr":     500,
        "for_topics":   ["money"],
        "for_areas":    ["taxes", "savings", "investing", "income_growth"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "sukanya_samriddhi": {
        "label":        "Sukanya Samriddhi Yojana (girl child)",
        "kind":         "govt_scheme",
        "value":        "Any post office / authorised bank",
        "why":          "Highest small-savings rate for girl child; tax-free maturity; locks long-term savings discipline.",
        "free":         False,
        "cost_inr":     250,
        "for_topics":   ["money"],
        "for_areas":    ["savings", "investing", "taxes"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "pmmy_mudra": {
        "label":        "PM Mudra Yojana (business loan up to ₹10L)",
        "kind":         "govt_scheme",
        "value":        "mudra.org.in | any PSU bank",
        "why":          "Collateral-free business loan; Shishu (₹50K) → Tarun (₹10L) tiers; suits micro-founder.",
        "free":         False,
        "cost_inr":     0,
        "for_topics":   ["business", "money"],
        "for_areas":    ["cashflow", "scaling", "income_growth", "founders_fit"],
        "for_severity": [],
        "applies_to":   "founder",
        "crisis":       False,
    },
    "standup_india": {
        "label":        "Stand-Up India (SC/ST/Women — ₹10L–₹1Cr loan)",
        "kind":         "govt_scheme",
        "value":        "standupmitra.in",
        "why":          "Govt-backed business loan + handholding for first-time SC/ST/Women entrepreneurs.",
        "free":         False,
        "cost_inr":     0,
        "for_topics":   ["business", "money"],
        "for_areas":    ["cashflow", "scaling", "founders_fit"],
        "for_severity": [],
        "applies_to":   "founder",
        "crisis":       False,
    },
    "udyam_msme": {
        "label":        "Udyam Registration (free MSME certification)",
        "kind":         "govt_scheme",
        "value":        "udyamregistration.gov.in (free, Aadhaar-linked, 10 min)",
        "why":          "Unlocks Mudra, GeM tenders, lower interest, govt-procurement preference, late-payment protection.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["business"],
        "for_areas":    ["legal_compliance", "cashflow", "scaling", "sales_pipeline"],
        "for_severity": [],
        "applies_to":   "founder",
        "crisis":       False,
    },
    "startup_india_dpiit": {
        "label":        "Startup India DPIIT recognition",
        "kind":         "govt_scheme",
        "value":        "startupindia.gov.in",
        "why":          "3-yr tax holiday eligibility (80-IAC), faster patent route, easier compliance, SIDBI fund access.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["business"],
        "for_areas":    ["legal_compliance", "founders_fit", "scaling", "taxes"],
        "for_severity": [],
        "applies_to":   "founder",
        "crisis":       False,
    },
    "pmjdy_jan_dhan": {
        "label":        "PMJDY — zero-balance bank account",
        "kind":         "govt_scheme",
        "value":        "Any PSU/private bank; only Aadhaar needed",
        "why":          "₹2L accident insurance + ₹30K life cover + RuPay debit free — basic safety net for unbanked.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money"],
        "for_areas":    ["savings", "emergency_fund", "expense_control"],
        "for_severity": ["watchful"],
        "applies_to":   "all",
        "crisis":       False,
    },

    # ════════════════════════════════════════════════════════════════
    # FREE TOOLS / OFFICIAL PORTALS
    # ════════════════════════════════════════════════════════════════
    "myscheme_finder": {
        "label":        "myScheme.gov.in — eligibility-based scheme finder",
        "kind":         "free_tool",
        "value":        "myscheme.gov.in",
        "why":          "Single portal that auto-matches you to 1,800+ central+state schemes from your profile.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money", "health", "business", "career"],
        "for_areas":    ["savings", "income_growth", "expense_control",
                         "founders_fit", "stability"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "digilocker": {
        "label":        "DigiLocker — govt document vault",
        "kind":         "free_tool",
        "value":        "digilocker.gov.in",
        "why":          "Aadhaar/PAN/RC/marksheet legally valid digital copies; survives lost-wallet/fire/flood.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money", "career", "business", "marriage"],
        "for_areas":    ["legal_compliance", "stability", "expense_control"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "rbi_sachet_scam": {
        "label":        "RBI Sachet — report unregistered finance scams",
        "kind":         "free_tool",
        "value":        "sachet.rbi.org.in",
        "why":          "Verify if a lender/scheme is RBI-registered BEFORE paying; report suspected ponzi.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money", "business"],
        "for_areas":    ["debt", "investing", "savings", "credit_score",
                         "partnerships", "legal_compliance"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "cibil_free_check": {
        "label":        "Free CIBIL credit-score check (1×/year)",
        "kind":         "free_tool",
        "value":        "cibil.com (also Experian/Equifax/CRIF — all give 1 free/yr)",
        "why":          "Catch identity theft + dispute wrong entries; 30-pt score lift = ₹L saved on home loan.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money"],
        "for_areas":    ["credit_score", "debt", "savings"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "rbi_ombudsman": {
        "label":        "RBI Banking Ombudsman (free dispute redressal)",
        "kind":         "free_tool",
        "value":        "cms.rbi.org.in",
        "why":          "Bank/NBFC/wallet not responding within 30 days? File here free; binding on bank.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money"],
        "for_areas":    ["debt", "credit_score", "savings", "expense_control"],
        "for_severity": ["watchful", "consult"],
        "applies_to":   "all",
        "crisis":       False,
    },
    "mcessation_quit": {
        "label":        "mCessation — quit-tobacco SMS programme (Govt)",
        "kind":         "free_tool",
        "value":        "Missed call 011-22901701 | nhp.gov.in/quit-tobacco",
        "why":          "Free behavioural-science-backed SMS coaching; 3× higher quit-rate vs going alone.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["health"],
        "for_areas":    ["heart", "vitality", "blood", "chronic", "auto-immune"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
    "shebox_posh": {
        "label":        "SHe-Box (workplace harassment, Govt of India)",
        "kind":         "free_tool",
        "value":        "shebox.wcd.gov.in",
        "why":          "POSH Act complaints route directly to ICC + Ministry oversight; works even after employer denial.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["career", "marriage"],
        "for_areas":    ["leadership", "stability", "harmony", "trust"],
        "for_severity": [],
        "applies_to":   "women",
        "crisis":       False,
    },

    # ════════════════════════════════════════════════════════════════
    # LEGAL AID
    # ════════════════════════════════════════════════════════════════
    "nalsa_free_lawyer": {
        "label":        "NALSA — Free legal aid (lawyer + court fee waived)",
        "kind":         "legal_aid",
        "value":        "nalsa.gov.in | helpline 15100",
        "why":          "Income < threshold OR woman/SC/ST/senior/disabled → free Supreme-Court-grade lawyer.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["marriage", "money", "business", "health"],
        "for_areas":    ["harmony", "trust", "in-laws", "debt", "credit_score",
                         "legal_compliance", "partnerships"],
        "for_severity": ["watchful", "consult", "urgent_consult"],
        "applies_to":   "all",
        "crisis":       False,
    },
    "lok_adalat": {
        "label":        "Lok Adalat — fast-track free dispute settlement",
        "kind":         "legal_aid",
        "value":        "Contact District Legal Services Authority (DLSA)",
        "why":          "Pre-litigation / pending case settlement in 1 hearing; binding; zero court fee; no appeal.",
        "free":         True,
        "cost_inr":     0,
        "for_topics":   ["money", "business", "marriage"],
        "for_areas":    ["debt", "credit_score", "partnerships", "trust",
                         "legal_compliance"],
        "for_severity": [],
        "applies_to":   "all",
        "crisis":       False,
    },
}


# ────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────
def _user_demo_tags(user_facts: Optional[Dict[str, Any]]) -> set:
    """Pull demographic tags from UCML user_facts to filter resources.

    Recognised tags (best-effort, missing or malformed = no filter):
        - age (int, plausible 0-120)  → senior if ≥ 60, youth if ≤ 25
        - gender ('F'/'M')            → women resources only for F
        - role                        → 'founder' opens MSME/startup schemes

    Architect-fix May 7 2026 (Phase 3.0 review): clamp age to plausible
    range so a malformed UCML value (e.g., "150" or -5) does NOT leak
    senior-only schemes to the wrong demographic.
    """
    tags = {"all"}
    if not isinstance(user_facts, dict):
        return tags
    age = user_facts.get("age")
    try:
        age = int(age) if age is not None else None
    except (TypeError, ValueError):
        age = None
    # Plausibility clamp: out-of-range = unknown (no demo filter applied)
    if age is not None and not (0 <= age <= 120):
        age = None
    if age is not None:
        if age >= 60:
            tags.add("senior")
        if age <= 25:
            tags.add("youth")
    gender = (user_facts.get("gender") or "").upper()
    if gender in ("F", "FEMALE", "WOMAN"):
        tags.add("women")
    role = (user_facts.get("role") or user_facts.get("occupation") or "").lower()
    if any(k in role for k in ("founder", "entrepreneur", "owner", "ceo",
                                  "director", "proprietor")):
        tags.add("founder")
    return tags


def _matches(res: Dict[str, Any],
             topic: str,
             areas: List[str],
             severity: str,
             demo_tags: set) -> bool:
    """Return True if the resource fits the query context.

    Architect-fix May 7 2026 (Phase 3.0 CRITICAL #2): for `crisis=True`
    resources, the AREA gate is RELAXED. Rationale — if upstream area
    extraction fails (empty `areas`) on a high-severity health/marriage
    query, we MUST still surface the suicide / women-181 / cybercrime
    line. Topic + severity + demo gates remain enforced (women-181
    still requires gender=F, AASRA still requires urgent_consult).
    """
    # Topic gate (empty list = all topics)
    if res.get("for_topics") and topic not in res["for_topics"]:
        return False
    # Severity gate (empty list = any severity)
    sev_gate = res.get("for_severity") or []
    if sev_gate and severity not in sev_gate:
        return False
    # Demographic gate
    applies = res.get("applies_to", "all")
    if applies != "all" and applies not in demo_tags:
        return False
    # Area gate (empty list = topic-default; non-empty must intersect)
    # CRISIS bypass: crisis resources are reachable on topic+severity+demo
    # alone, even if `areas` is missing or doesn't intersect.
    area_gate = res.get("for_areas") or []
    if area_gate and not res.get("crisis"):
        if not any(a in area_gate for a in (areas or [])):
            return False
    return True


def get_practical_resources(topic: str,
                            areas: Optional[List[str]] = None,
                            severity: Optional[str] = None,
                            user_facts: Optional[Dict[str, Any]] = None,
                            limit: int = 3) -> List[Dict[str, Any]]:
    """Select up to `limit` verified India-specific resources for the
    current remedy context.

    Crisis resources (suicide, women-181, cybercrime-1930, police-112,
    childline-1098) are always rank-first when their gate triggers,
    regardless of any other resource's relevance.

    Returns: list[dict] with keys {label, kind, value, why, free,
    cost_inr}.  Empty list if nothing matched (engine then renders
    nothing — no padding).
    """
    areas    = list(areas or [])
    sev      = severity or ""
    demos    = _user_demo_tags(user_facts)
    matches: List[Dict[str, Any]] = []
    for _id, res in _RESOURCES.items():
        if not _matches(res, topic, areas, sev, demos):
            continue
        matches.append({
            "id":        _id,
            "label":     res["label"],
            "kind":      res["kind"],
            "value":     res["value"],
            "why":       res["why"],
            "free":      bool(res.get("free")),
            "cost_inr":  int(res.get("cost_inr") or 0),
            "crisis":    bool(res.get("crisis")),
        })

    # Crisis-first ordering, then free-first, then helpline-first
    def _sort_key(r: Dict[str, Any]):
        kind_rank = {"helpline": 0, "legal_aid": 1, "govt_scheme": 2,
                     "free_tool": 3, "directory": 4}.get(r["kind"], 9)
        return (
            0 if r["crisis"] else 1,
            0 if r["free"] else 1,
            kind_rank,
        )
    matches.sort(key=_sort_key)
    out = matches[:max(1, int(limit))] if matches else []
    # Strip internal flags before returning to caller
    for r in out:
        r.pop("crisis", None)
    return out


def render_practical_resources(resources: List[Dict[str, Any]]) -> List[str]:
    """Format a list of resources as locked_facts-ready lines.

    Returns a list of strings (not joined) so the parent renderer can
    splice them into its block. Empty input → empty list.
    """
    if not resources:
        return []
    icon = {
        "helpline":    "📞",
        "legal_aid":   "⚖️",
        "govt_scheme": "🇮🇳",
        "free_tool":   "🛠️",
        "directory":   "📒",
    }
    lines: List[str] = ["   ◦ Verified India resources (real-world help):"]
    for r in resources:
        ico = icon.get(r.get("kind"), "•")
        cost_tag = "FREE" if r.get("free") and not r.get("cost_inr") else (
            f"~₹{r['cost_inr']:,}" if r.get("cost_inr") else "low-cost"
        )
        lines.append(f"     {ico} {r['label']} — {r['value']}  [{cost_tag}]")
        if r.get("why"):
            lines.append(f"        why: {r['why']}")
    return lines


__all__ = ["get_practical_resources", "render_practical_resources"]
