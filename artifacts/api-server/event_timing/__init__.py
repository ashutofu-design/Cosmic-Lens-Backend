"""
event_timing package
====================
Event-timing logic for all life domains.

Sub-packages:
  - marriage/   : Marriage timing (v2 pipeline + BCP + dasha/transit)
  - career/     : Career timing (8 buckets, 35 layers)
  - travel/     : Foreign travel/settlement timing (9-step pipeline)
  - property/   : Property buy/registry/possession timing (v1)
  - education/  : Exam/admission timing (v1)
  - litigation/ : Court/bail/verdict timing (v1)
  - love/       : Love/patchup timing (v1)
  - finance/    : Wealth timing windows
  - health/     : Health/recovery timing
  - baby/       : Children/conception timing
  - _shared/    : double_transit, kp_significator_scan, timing_pipeline

Central routing:
  - timing_router.py  : domain detect + engine dispatch
  - domain_specs.py   : master checklist per domain (dasha/transit/houses)
  - formatters.py     : narrator LOCKED blocks
"""

from event_timing.timing_router import (  # noqa: F401
    build_timing_demand,
    detect_timing_intent,
    format_timing_block,
    resolve_timing_domain,
    run_timing_engine,
)
from event_timing.domain_specs import DOMAIN_TIMING_SPECS, get_domain_spec  # noqa: F401
