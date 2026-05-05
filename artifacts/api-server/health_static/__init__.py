"""Health Static Engine — Y2 architecture (sister module to finance_static).

╔═══════════════════════════════════════════════════════════════╗
║  SCOPE: NON-TIMING engine                                     ║
║  ───────────────────────────────────────────────────────────  ║
║  General health / vitality questions — chart-based.           ║
║  Based on user's natal chart + KP cuspal sub-lord layer.      ║
║                                                               ║
║  HANDLES (non-timing, 5 dimensions):                          ║
║    • vitality            — body strength / immunity (H1+Sun+Moon)
║    • disease_resistance  — recovery power (H6+Mars+Mercury)   ║
║    • chronic_risk        — long-term illness (H8+Saturn+Rahu) ║
║    • mental_health       — mind stability (Moon+H4+Mer+Jup)   ║
║    • accident_risk       — sudden events (Mars+H8+Ketu)       ║
║                                                               ║
║  KP CSL layer (1st + 6th + 8th cusps):                        ║
║    GREEN signify {1, 5, 11} (vitality, recovery, fulfilment)  ║
║    RED   signify {6, 8, 12} (disease, chronic, hospital)      ║
║                                                               ║
║  DOES NOT HANDLE (timing — separate future module):           ║
║    • "Kab beemar honga" / specific date / muhurat             ║
║    • Surgery date selection / treatment timing                ║
║                                                               ║
║  ⚠️  BRAND-SAFETY HARD GUARDS (non-negotiable):                ║
║    • NEVER predict death / longevity end                      ║
║    • NEVER replace medical advice — doctor disclaimer mandatory
║    • NEVER name specific diseases ("diabetes" / "cancer" etc.)║
║    • NEVER guarantee cure                                     ║
║    • Mental-health / reproductive / parent-health =           ║
║      sensitive bucket → softer language + extra disclaimer    ║
╚═══════════════════════════════════════════════════════════════╝

Architecture (mirrors finance_static):
  Engine   = deterministic facts (ZERO LLM inference)
  Cache    = chart_norm + MD-AD key, TTL until next AD change
  KP layer = 1st/6th/8th cusp sub-lord chain (read-only nudge)
  Conflict = KP-Vedic resolver demotes/upgrades with confidence=LOW

Public API (Phase H1 — engine core only):
  compute_health_facts(kundli) -> dict
    Returns 5 dimensions + yogas + KP CSL block + brand_safety meta.
  compute_kp_health_csl(kundli) -> dict | None
    KP 1st/6th/8th CSL verdict. None if KP cusps absent.

Phase H2 (next session): handle_health_question + routing + LLM
narration + flask_app wiring + validator (diagnosis-ban + doctor
disclaimer enforcement).

Engine scope tag (will appear in every response): "non_timing"
"""
SCOPE = "non_timing"

from health_static.health_facts import compute_health_facts  # noqa: F401, E402
from health_static.kp_health_csl import compute_kp_health_csl  # noqa: F401, E402
