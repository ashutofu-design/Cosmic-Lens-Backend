# MR Relationship Engines — Architecture Freeze v1

**Status:** FROZEN — no new engines, no module-matrix churn without explicit approval.

## Pipeline

```
Question DNA
  → Engine Router (classifier / DNA bucket)
  → Engine Orchestrator (primary + secondary engines)
  → ModuleLoader (per-engine matrix)
  → Rule Priority Layer
  → Rule Evaluator
  → Contradiction Detector
  → Conflict Resolver
  → Scorecard
  → Verdict + Explanation Layer
  → JSON Output (EngineOutputV2)
  → Narrator
```

## Frozen engine list (20)

loyalty_trust, commitment, compatibility, partner_nature, communication,
emotional_attachment, secret_relationship, breakup_risk, patchup, family_approval,
long_distance, toxicity, one_sided_love, chemistry, bed_intimacy, karmic_marriage,
relationship_future, relationship_decisions, relationship_verification, relationship_remedies

(`general_mr` remains legacy catch-all; not part of v2 target set.)

## Module symbols

| Symbol | Meaning |
|--------|---------|
| ✅ | Always load |
| ❌ | Never load |
| ⚡ | Load only when timing trigger in question |
| 🔀 | Static ❌ / Timing ✅ |
| opt | Optional module (load if chart data present) |

## Spec files (code)

| Component | Module |
|-----------|--------|
| Module matrix | `registry.py` |
| ModuleLoader | `module_loader.py` + `modules/*` |
| Rule engine | `rules/priority.py`, `rules/evaluator.py`, `rules/conflict_resolver.py` |
| Contradiction | `contradiction.py` |
| Engine memory | `memory.py` |
| Explanation | `explanation.py` |
| Scorecard | `scorecard.py` |
| JSON schema | `schema.py` |
| Orchestrator | `orchestrator.py` |
| Pipeline | `pipeline.py` |
| Reference engine | `engines/commitment.py` |

## Remedies invariant

**Never emit a remedy without `target_affliction` evidence** from D1/D9/AV/BCP.

## Reference implementation order

1. Commitment (done first in v2)
2. Loyalty, Compatibility, Breakup, Patch-up (Phase 1 full-stack)
3. Remaining 15 engines — clone template only
