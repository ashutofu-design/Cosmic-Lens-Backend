"""Property Static Engine — Y2 architecture (sister of health_static).

╔═══════════════════════════════════════════════════════════════╗
║  SCOPE: NON-TIMING engine                                     ║
║  ───────────────────────────────────────────────────────────  ║
║  General property / real-estate / land / home questions —     ║
║  STATIC chart analysis only. No timing, no muhurat, no        ║
║  "kab kharidu" answers.                                       ║
║                                                               ║
║  HANDLES (4 dimensions):                                      ║
║    • yog       — 4H lord/occupants + Mars/Saturn dignity       ║
║    • capacity  — 2H/11H lords + Jupiter + Dhana yogas         ║
║    • risk      — 6H/8H/12H influence on 4H + Rahu/Ketu/Mars   ║
║    • type_fit  — best property type from karaka dominance     ║
║                                                               ║
║  DOES NOT HANDLE:                                             ║
║    • Timing  ("property kab milegi", "ghar kab kharidu")      ║
║    • Muhurat ("registry ka muhurat", "shift kab karu")        ║
║    • Specific address / location prediction                   ║
║                                                               ║
║  Architecture:                                                ║
║    Engine    = deterministic 4-dim facts (ZERO LLM inference) ║
║    SignalPack= compact JSON sent to LLM (NO raw kundli)       ║
║    LLM       = expression layer ONLY                          ║
║    Sanitizer = strip planet/house/timing/jargon leaks         ║
║    ForceFinal= mandatory '👉 Final:' verdict (engine-built)   ║
║                                                               ║
║  Killswitches (default ON):                                   ║
║    PROPERTY_STATIC_BYPASS=0                                   ║
║    PROPERTY_SIGNAL_PACK=1                                     ║
║    PROPERTY_FINAL_VERDICT=1                                   ║
║    PROPERTY_REPLY_SANITIZER=1                                 ║
╚═══════════════════════════════════════════════════════════════╝
"""
SCOPE = "non_timing"

from property_static.property_engine import compute_property_facts  # noqa: F401, E402
from property_static.property_routing import (  # noqa: F401, E402
    is_property_question,
    route_property_question,
)
from property_static.property_replies import handle_property_question  # noqa: F401, E402
