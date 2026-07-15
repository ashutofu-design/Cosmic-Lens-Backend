# Relationship Routing — Developer Reference

Production architecture: [RELATIONSHIP_ARCHITECTURE.md](../../../docs/RELATIONSHIP_ARCHITECTURE.md)

## Resolver

`relationship_routing.py` — **Domain → DNA → Engine**. No love-before-marriage keyword priority.

## Key modules

| Module | Role |
|--------|------|
| `relationship_routing.py` | Unified relationship route resolver |
| `relationship_dna_taxonomy.py` | 23 DNA buckets → MR archetype map |
| `ask_question_dna.py` | DNA extract, `dna_routing_lock`, `apply_question_dna_to_routing` |
| `ask_master_router.py` | `resolve_ask_route` — timing/static/chart paths |
| `ask_mr/engine.py` | Static engine run + narrator |
| `event_timing/timing_router.py` | Timing domain dispatch |
| `event_timing/marriage/marriage_engine_v2.py` | Marriage timing M17 |
| `event_timing/love/love_timing_engine_v1.py` | Love timing |
| `ask_marriage_relationship_slice.py` | Legacy chart slice (when `ASK_MR_ENGINE=0`) |
| `dcr_love.py` | Legacy DCR love slice |

## Mobile

| Path | Role |
|------|------|
| `app/(tabs)/ask.tsx` | Ask chat, `/api/ask/stream` |
| `app/relationship.tsx` | Hub |
| `app/love-reality.tsx` | Couple tools |
| `app/kundli-milan.tsx` | Gun milan |
| `lib/loveRealityToolsConfig.ts` | Tool → API map |

## APIs

- `POST /api/ask`, `POST /api/ask/stream` — Ask
- `POST /api/love-compatibility`, `/api/breakup-chances`, `/api/loyalty-check`, `/api/future-outcome`
- `POST /api/kundli-milan`, `/api/kundli-milan/pro-pdf`

## Flags

- `ASK_MR_ENGINE=0` — legacy DCR/marriage slice instead of MR engines
- Question DNA routing — `apply_question_dna_to_routing` when confidence trusted

## Tests

- `tests/test_relationship_routing.py`
- `tests/test_relationship_dna_taxonomy.py`
- `tests/test_ask_question_dna.py`
- `tests/test_ask_marriage_relationship_slice.py`
- `tests/test_wave1_relationship_engines.py`
