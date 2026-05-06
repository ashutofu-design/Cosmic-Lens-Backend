# Cosmic Lens
A mobile Vedic Astrology application delivering accurate astrological analyses and AI-driven interpretations to users.

## Run & Operate
- **Run**: `pnpm dev`
- **Build**: `pnpm build`
- **Typecheck**: `pnpm typecheck`
- **Codegen**: `pnpm codegen`
- **DB Push**: `pnpm db:push`
- **Required Env Vars**: `OPENAI_API_KEY`, `DATABASE_URL`, `HEALTH_LLM_MODEL`, `HEALTH_ROUTER_MODEL`, `FINANCE_STATIC_BYPASS`, `HEALTH_STATIC_BYPASS`, `LEAN_PACK_MODE`, `LAYER2_FUZZY`, `LAYER3_LLM`

## Stack
- **Frameworks**: React Native (Expo), Flask (Python)
- **Runtime Versions**: Node.js 24, TypeScript 5.9, Python 3.10+
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Build Tool**: pnpm

## Where things live
- `apps/mobile`: Expo React Native application.
- `artifacts/api-server`: Flask backend.
- `packages/`: Shared utilities and components.
- **DB Schema**: `artifacts/api-server/database.py` (+ models in `models.py`)
- **API Contracts**: Implicitly defined by Flask routes in `flask_app.py`
- **Theme Files**: `apps/mobile/src/theme/`
- **User Memory Layer (UCML)**: `artifacts/api-server/user_memory.py` — silent fact extraction + bundle assembly. Tables: `user_facts` (L1 atomic), `user_behavior` (L2 aggregates), `user_personality` (L3 vector).

## Architecture decisions
- **Monorepo Structure**: Uses pnpm workspaces for dependency management and code sharing.
- **CLE (Cosmic Lens Engine) Format**: Backend astrological calculations follow a strict modular engine format.
- **LOCKED FACTS Protocol**: Deterministic data for AI responses is centralized in `locked_facts.py` to prevent hallucination.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors.
- **RAW PASSTHROUGH MODE (default ON)**: Bypasses legacy gates and routes API calls through `openai_helper.raw_passthrough_ask()` for simplified processing.
- **Universal Signal Pack v2**: Uses one universal pack containing all four health dimensions for LLM interpretation.
- **User-Facing Translation Layer (GOLDEN RULE)**: Bans all astrology jargon from user-facing output, using plain language.
- **Mandatory Final Verdict**: Enforces a sharp, engine-built final verdict line (`👉 Final:`) in responses.
- **Health Focus Block (CAFB-health)**: Replaces legacy health rule-engine with atomic checks, a 4-axis detector, chart-slicer, and hard-guards for sensitive health topics.
- **KP opt-in enrichment for raw_passthrough**: Appends cuspal-sub-lord verdict block to chart context for explicit KP terminology, hard yes/no event markers, OR plain timing markers (`kab hoga/hogi`, `when will`) in questions.
- **Marriage Engine v2.3**: D9 7th Lord (D9 7L) is a supreme propagation across the entire pipeline, influencing every step from D1 marriage planet filtering to dasha activation and double-transit confirmation, ensuring its weight in predictions.
- **User Context Memory Layer (UCML) v1 — "Digital Mirror"**: Silent, deterministic memory module (`user_memory.py`) that builds a per-user profile from question history with ZERO user-facing footprint. Three tiers — L1 `user_facts` (atomic regex-extracted facts like marital_status, has_children, profession_hint, location_city, health_concern, mood_baseline — ~50 keys, dedup-on-update), L2 `user_behavior` (aggregates: topic distribution, avg question length, time-of-day pattern), L3 `user_personality` (8-dim vector: analytical/anxious/self-focus/formal/brief/action-oriented/skeptical/future-focused). DESIGN LOCKS: (a) ENGINE accesses DB, LLM never touches it; (b) silent enrichment — bundle injected via `inject_into_prompt()` with explicit DO-NOT-RECITE directive, the LLM must NEVER expose memory ("aapne pichli baar..." is forbidden); (c) free — pure regex + DB, no per-call LLM cost; (d) self-correcting — every new Q refines existing facts via confidence-merge upsert; (e) ~5 KB lifetime per user. Phase 1 ships L1 extractor + storage + bundle assembly + prompt injection. Phases 2-7 (backfill, behavioral aggregator, personality scorer, real-time context, telemetry) pending.
- **Health Timing Engine v1.0**: 9-step health-risk timing engine at `event_timing/health/health_engine_v1.py`, mirrors Marriage v2.4 (FILTER→VERIFY→ACTIVATE→TRIGGER). Steps: (1) D1 filter — 1L/6L/8L/12L + 2L/7L marakas (age-gated ≥55) + occupants of 6/8/12 + planets ASPECTING the 6th + functional malefics for lagna; (2) D9 dignity verify; (3) D30 (Trimshamsa) disease verify; (3.5) KP cuspal sub lord of 6th & 8th; (4) Weighted ranking with TRUE D1 min-max normalization — D1·30% + D9·20% + D30·25% + KP·15% + karaka·10%; (5) Dasha activation with **AD=5, PD=6, MD=1** + **SIGNED contribution model** so benefic AD/PD reduce risk; (6) Transits — Saturn over 1/6/8, Rahu/Ketu over Lagna/Moon, Mars over 6/8, Jupiter over 6, Sade Sati phases; (7) Ashtakavarga SAV bindus on Lagna + 6H; (9) Yoga layer — Papakartari, Arishta, Subhakartari protective. Hard guards: MEDICAL_DISCLAIMER + AGE_GUARD_NO_DEATH_PREDICTION (age<25 OR unknown) + NO_DIAGNOSIS_NAMING + NO_CURE_GUARANTEE + 3-confirmation rule for `urgent_consult` tier. Output: verdict (STRONG_VITALITY/STABLE/VULNERABLE/HIGH_RISK_WINDOW/UNKNOWN) + band + current_window + next_3_windows + protection_windows + affected_systems + recommendation_tier (monitor/preventive/consult/urgent_consult) + top_health_planets + weighted_breakdown + kp_layer + transits + ashtakavarga + yogas + risk_flags + factors + llm_directives. Public API: `compute_health_window(kundli, intel, kp, birth)`. **Phase 2 SHIPPED (May 6 2026)**: (a) `locked_facts.py::build_locked_facts` emits a `▸ TIMING ENGINE` Health row (`verdict/band tier: <tier> | now: MD-AD-PD/severity | risk: ...`) plus up to 3 `trace N: window (score, sev)` lines, mirroring VIVAH-7 marriage pattern; HARD RULE in the same block forbids any date not in the block. (b) Engine stashes its result on a `threading.local` (`get_last_health_result()` / `clear_last_health_result()`) so the post-injector can cite verbatim without recomputing. **Cache lifecycle is single-exit-safe**: `compute_health_window` is now a thin wrapper over `_compute_health_window_impl` that (i) clears cache at entry — defensive against worker-thread reuse on Flask threaded dev / gunicorn threaded workers, (ii) wraps the inner pipeline in `try/except` so any engine exception falls back to a synthetic `UNKNOWN` result instead of leaking the prior request's verdict, (iii) re-stores on every exit path including UNKNOWN gates. (c) New deterministic post-injector `health_focus_routing.inject_health_engine_verdict(answer, question)` appends a single `👉 Final: <verdict-label> — <tier-label>. [engine: health-v1]` line with the engine verdict; idempotent (tag-based bail), killswitch-gated (HEALTH_DISCLAIMER), no-op when cache empty OR verdict==UNKNOWN, and **reconciles duplicate finals** by stripping any pre-existing `👉 Final:` line the LLM wrote so the engine line is the sole authoritative final. Wired into `apply_health_postinjectors` between `strip_forbidden_vocab` and `inject_medical_disclaimer`. (d) **Parity automatic**: both `/api/ask` (sync, openai_helper.py:15838) and `/api/ask/stream` (line 19629) already call `apply_health_postinjectors` gated by `_is_health_topic` — no edit needed; the new verdict line flows through both. Tests: `test_health_engine.py` (22/22) + `test_health_postinjector.py` (9/9) — covers idempotency, killswitch, no-op-on-empty-cache + UNKNOWN, full-pipeline-includes-verdict-and-disclaimer, thread-isolation, **stale-leak regression** (prior valid result must not survive a subsequent empty-kundli call), **engine-exception → UNKNOWN-cache** hardening, **duplicate-final reconciliation**. Smoke fixture `/tmp/k.json` only (req.json + qm.json missing — note for future runs).
- **Marriage Engine v2.4 — Age Sanity Guard**: Two real-life "akal" fixes. (1) Multi-format DOB parser (`_parse_dob_string` + `_extract_dob_dt`) handles Indian formats (`26 Nov 1992`, `26-11-1992`, `26/11/1992`, etc.) and falls back to `kundli` dict — fixes silent v2.3 bug where ISO-only parser made `user_age=None` for most profiles, killing the entire age system. (2) Practical-age floor (Female ≥19, Male ≥22, Neutral ≥20) demotes any candidate window starting before user reaches that age, so a 17-year-old whose dasha/PD aligns next month no longer gets "shaadi 3 mahine mein" — engine pushes primary window past the floor and emits an `AGE_GUARD` LLM directive instructing the model to lead with study/career framing. New output fields: `min_practical_age`, `too_young_for_marriage`, `earliest_practical_window_start_iso`, `windows_suppressed_too_young`.

## Product
- **Mobile App**: Daily Rashifal, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, personalized forecasts ("Risk Radar"), Life Mastery Report.
- **AI-driven Insights**: AI-powered interpretations with anti-hallucination pipelines, RAG for classical Vedic knowledge, and structured output modes.
- **Localization**: Supports 25 languages with region detection.

## User preferences
- The user wants the AI to act as a replit coding agent.
- The user prefers a strict development methodology: `engine.py file (sahi folder mein)`, `Unit test (test_engine.py)`, `locked_facts.py wiring`, `Rule entry in system prompt`, `Deterministic post-injector`, `3x smoke test on real chart (/tmp/k.json, /tmp/req.json, /tmp/qm.json)`, `Architect review (code_review skill)`, `replit.md entry` are mandatory for every new engine.
- The user has provided a clear roadmap for project phases and expects strict adherence to it. Deviations require explicit user confirmation.
- The user expects the AI to avoid hallucinating, especially regarding timing-related questions.
- The user wants the AI to integrate classical Vedic knowledge through RAG for opinion-based questions, but strictly NOT for timing questions.
- The user has defined a brand voice: "Powered by Advanced Cosmic Intelligence" and explicitly states "AI never named; AI = language layer only; backend = facts; post-injectors = mandatory citation safety net."
- The user prefers deterministic post-injectors to ensure mandatory facts are cited even if the AI misclassifies a topic.
- The user prefers that the AI refine language for opinion questions but must cite engine facts.
- The user wants medical outputs to include a mandatory medical disclaimer banner and a 3-confirmation rule for severity tiers.
- The user wants financial outputs to include a mandatory financial disclaimer banner and a tiered risk profile.
- The user wants remedies outputs to include a mandatory disclaimer ("Remedies SUPPLEMENT, never substitute action") and provide both free and paid alternatives.
- The user wants Astrocartography outputs to include a mandatory disclaimer ("energetic affinity, not guaranteed luck").
- The user expects ethical and safety disclaimers for sensitive topics like medical, lifespan, death prediction, and destiny vs. guidance.
- The user prefers a "Numerology PDF Pro" branding for the report, with a hybrid numerology + Vedic Astrology content, framed with numerology language.

## Gotchas
- **Static Gate Parity**: Any new engine/gate added to `/api/ask` MUST simultaneously be added to `/api/ask/stream`.
- **Cache Invalidation**: Any policy change requires bumping the cache namespace (`_vX`).
- **Vedic Vocab Stripping**: The validator strips Vedic terms unless explicitly opted in or the user's question contains a "tech-request" keyword.
- **Topic-Lock Conflicts**: When multiple injection points compete, the latest injected point in the user message order wins.
- **DB-Load Enforcement**: For authenticated users, `kundli` is always loaded from the database by `/api/ask{,/stream}`; client-supplied `kundli` is for anonymous demo mode only. The primary profile's `chart_data` is atomically mirrored into the `kundlis` table to ensure deterministic single-chart answers.
- **LLM Temperature**: The `temperature` parameter is often rejected by `gpt-5` models, meaning LLM strict mode is currently dormant for those models.
- **Telemetry Best-Effort**: Telemetry inserts are wrapped in `try/except` and silently drop rows on contention.

## Pointers
- **Relevant Skills**: `code_review`, `telemetry`, `test_generation`
- **External Docs**:
    - [pnpm workspaces](https://pnpm.pnpm.io/workspaces)
    - [Expo React Native](https://docs.expo.dev/)
    - [Flask Documentation](https://flask.palletsprojects.com/en/latest/)
    - [Pyswisseph Library](https://pyswisseph.readthedocs.io/en/latest/)
    - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)