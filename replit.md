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
- **DB Schema**: `artifacts/api-server/database.py`, `artifacts/api-server/models.py`
- **API Contracts**: Flask routes in `artifacts/api-server/flask_app.py`
- **Theme Files**: `apps/mobile/src/theme/`
- **User Memory Layer (UCML)**: `artifacts/api-server/user_memory.py`
- **Question History**: `artifacts/api-server/question_history.py` (Q + A persistence)
- **Engines**: `artifacts/api-server/event_timing/{health,marriage,finance,travel,baby}/`, `artifacts/api-server/remedy/`
- **Shared Engine Helpers**: `artifacts/api-server/event_timing/_shared/` (KP scan, double-transit)
- **LLM Orchestration**: `artifacts/api-server/openai_helper.py`, `artifacts/api-server/reply_cosmo/engine_locked_to_llm/locked_facts.py`

## Architecture decisions

### Foundational
- **Monorepo Structure**: pnpm workspaces for dependency management and code sharing.
- **2-Path Routing**: Live ask endpoint splits into `raw_passthrough_timing` (engine-locked, deterministic) and `raw_passthrough_static` (LLM-driven, jargon-free). `RAW_PASSTHROUGH_MODE=1` is the only live path; legacy paths kept for fallback.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors.
- **User Context Memory Layer (UCML) v1**: Silent, deterministic memory module (`user_memory.py`) building per-user profiles from question history with three tiers: `user_facts` (L1 atomic), `user_behavior` (L2 aggregates), `user_personality` (L3 vector). Engine accesses DB; LLM never touches it.
- **User-Facing Translation Layer (GOLDEN RULE)**: Bans all astrology jargon from user-facing output.

### Engine Lineage (Phases 2.2 → 2.5.11, May 2026 — consolidated)
Five timing engines (Health v1, Marriage v2.4, Finance v1, Travel v1, Baby v1) all follow the same pipeline (FILTER → VERIFY → KP-GATE → ACTIVATE → TRIGGER): D1 lean filter → D9 dignity → divisional chart (D7 babies / D2 finance / D4 travel) → KP CSL of topic cusps → weighted ranking → dasha activation (AD=5, PD=6, MD=1) → transits/yogas. Each engine emits a `▸ <TOPIC>` row to `locked_facts.py` + mandatory `llm_directives` + thread-local cache. Every engine has a paired `test_<topic>_engine.py`.

**Per-engine specifics**:
- **Health v1** (post-2.5.11.11): 6-step (D30 + transits + SAV all permanently removed). Weights D1·40 + D9·30 + KP·20 + karaka·10. KP CSL of 6/8/12 cusps + active-CSL gate + dusthana convergence in `at_risk_planets` ranking.
- **Finance v1** (post-2.5.11.12-b): 5-step (D2 Hora + transits + SAV + Yogas removed). KP CSL of 2/5/9/11 acts as **hard final-filter** with safe fallback. Weights D1·40 + D9·30 + KP·20 + karaka·10.
- **Travel v1**: full 8-step. KP-dasha gate (NL→SB→SS chain hits on 3/9/12) boosts MD/AD/PD windows independently of D1 ranking. Past-window lookback (15y, MD-diversity cap of 4 in top 12).
- **Marriage v2.4**: multi-format DOB parsing + practical-age floor for marriage windows + specific-partner synastry bridge.
- **Baby v1** (2.5.0→2.5.10): cross-chart filter (D1∩D9∩D7), KP 2-5-11 significator gate, K.N.Rao Double Transit, gestation-aware re-rank, mandatory `NO_GENDER_PREDICTION` directive (PCPNDT compliance).

**Shared helpers** (`event_timing/_shared/`):
- `kp_significator_scan.py`: `compute_kp_planet_scan(kp, domain, in_filter_set)` — scans all 9 vimshottari planets across 6 domains via `CONCERN_HOUSES` preset, returns layered houses + `delivers ∈ {STRONG,PARTIAL,ABSENT}` + audit-flag for engine-dropped-but-delivers planets. `kp_promote_survivors(d1_map, kp, domain, threshold=2)` — data-adaptive STEP1 promotion (mutates `d1_map` to set `in_filter=True` for any planet whose KP chain signifies ≥threshold domain houses; engine's hardcoded floor retained as safety net).
- `double_transit.py`: `check_double_transit(kundli, target_date, lagna_si, planets_d1, concern_houses)` — K.N.Rao Jupiter+Saturn classical rule. Returns `{verdict, score 0-100, anchors[]}`. Vedic full-strength aspects (J: 5/7/9; S: 3/7/10) checked vs concern-house signs AND concern house-lords' natal signs. **Caveat**: empirically validated as reliable for life events (marriage/baby/career) but FAILED on travel for one ground-truth chart (Phase 2.5.11.15-c) — needs framework re-design before broader rollout.

**Companion modules**:
- **Remedy Engine v1.1**: hybrid 3-tier (PRACTICAL → AYURVEDIC → VEDIC last) covering health/marriage/career/money/business × 9 grahas; anti-superstition rules, every entry carries KPI + cost + caveats.
- **Dasha Timeline Block**: `_format_dasha_block` emits current MD/AD/PD + every dasha transition over next 5 years; handles both `{planet,startDate,subDashas}` and `{lord,start,antardashas}` shapes; hard-cap 60 lines.
- **Ask-flow Sensitivity** (Phases 2.5.11.4-.6): `_SENSITIVE_STATIC_RE` covers parent-illness/anxiety/panic/suicidal/depression/addiction/job-loss; `_LONG_STORY_RE` for "N saal se" pattern; `_MARRIAGE_DOMAIN_RE` with 6 framing protocols; `_SPECIFIC_PARTNER_RE` routes "mere BF/wife/pati" Qs to real synastry (when partner kundli saved) or `requires_partner_profile` CTA.

### Active Development (last 3)
- **Kundli Milan LLM Polish — Phase 2.5.11.20-A: Persistent DB Cache + Token Trim (May 7 2026)**: Cost-reduction follow-on to 2.5.11.20. Original cache was in-process LRU only — wiped on every API restart, so each new worker re-paid ~₹0.038 for prose it had already generated. **Changes**: (a) New `KundliMilanCache` model (`models.py`): PK `fingerprint VARCHAR(64)`, JSON `polished_json`, plus `model`, `prompt_version` (indexed), `created_at`, `last_hit_at`, `hits`. Auto-created via `db.create_all()`. (b) Two-tier cache in `vedic/compat/llm_polish.py`: **L1** in-process `OrderedDict` (fast, per-worker) → **L2** persistent DB (shared across workers, survives restarts/deploys). Cache hierarchy: L1 hit → return; else L2 hit → warm L1 + return; else LLM call → write both. (c) `_db_cache_get` bumps `hits` + `last_hit_at` best-effort. `_db_cache_put` upserts (insert or update). Both swallow all DB errors and fall through (engine prose served regardless). (d) `max_tokens` trimmed 900 → 600 (real outputs ~480 tokens; 33% worst-case cost cut). (e) **3 new unit tests**: `_db_cache_get` no-app-context returns None (not raise), `_db_cache_put` no-app-context swallows, `polish_compat_analysis` skips LLM when L2 hits — 31/31 total green. **Live verified**: smoke 1 (Vikram+Sanya 16.5/36) → DB row created (`fp=a26e83687224... model=gpt-4o-mini ver=v7`); workflow restart → smoke 2 same chart → identical insight returned (L2 hit), `hits=1`; smoke 3 different chart (Arjun+Meera 19.5/36) → 2nd DB row added. `_PROMPT_VERSION` baked into fingerprint so any policy bump auto-invalidates stale L2 rows. **Projected savings**: at scale (90% cache hit), per-call cost drops from ₹0.038 → effectively ₹0 across restarts. New unique-pair calls only: ~₹0.025/call (33% less due to token cap).
- **Kundli Milan LLM Prose Polish — Phase 2.5.11.20 (May 7 2026)**: User feedback "compatibility text robotic feel deta hai, LLM se sundr likhwa do". Implemented HYBRID layer over deterministic Ashtakoot facts: engine still computes all numbers (Swiss Ephemeris) + rule-based templates (preserved as fallback); new `vedic/compat/llm_polish.py` rewrites the 4 narrative sections (`compatibility_insight`, `strengths`, `challenges`, `marriage_outlook`) in a "mature Vedic astrologer" voice. **Architecture**: prompt builder + `gpt-4o-mini` call + multi-rule validator + fact-fingerprint LRU cache (1024 entries). Wired into `flask_app.py /api/kundli-milan` exit (line 8815). Enabled in production via `COMPAT_LLM_POLISH=1`. Cost: ~$0.0004 per call, 90%+ cache hit rate at scale. **Validator hardening through v1→v7** (architect-driven): (a) verbatim total citation, (b) per-partner anchor — nakshatra OR rashi OR partner-name (≥3 chars) using **case-insensitive WORD-BOUNDARY regex** to avoid substring collisions ("Mula" ⊄ "formula", "Leo" ⊄ "chameleon", short "An" ⊄ "and"), (c) **whitelist-positive** remedy contract — at least one verbatim `ALLOWED_REMEDIES` (11 entries) phrase must appear across `challenges`+`marriage_outlook` (relaxed from per-bullet to whole-block since gpt-4o-mini concentrates remedies; paraphrase-only like "spiritual healer" rejected), (d) **denylist-negative** banned-remedy guard (gemstone/ratna/sapphire/wear-a/tantrik/vashikaran/kavach/pendant) covering BOTH challenges AND outlook, (e) banned existential terms (lifespan/death/gender/guaranteed), (f) per-pair koot-score fact-lock (any "X out of Y" must match a real koot or the total), (g) **case-insensitive whole-word** vocab lock for `_KNOWN_NAKSHATRAS` (28 entries) + `_KNOWN_RASHIS` (12 entries) catching lowercase Hinglish hallucinations like "yeh shravana wali...", (h) length sanity (insight 50-1200 chars, outlook 80-1500). `_PROMPT_VERSION` baked into cache fingerprint so any policy bump auto-invalidates. **Fallback path**: any validator reject / LLM error / JSON parse error silently returns rule-based templates → user never sees an error. **28 unit tests** (validator + cache + toggle-off + mocked-LLM happy/sad paths + 4 architect-blind-spot regressions: substring-collision, lowercase-hallucination, paraphrase-only-remedy, banned-remedy-in-outlook) — all pass. Live verified on 2 real charts (low-compat ashu+Animesh 11.5/36 with Revati/Krittika anchors + gratitude-practice remedy; mid-compat Priya+Rohan 22/36 with Ashwini/Magha anchors) — both return warm, factually-anchored, whitelist-only prose.
- **Ask Q&A Persistence — Phase 2.5.11.19 (May 7 2026)**: User mandate "store karo Ask section ki har baat-cheet". Discovery: `UserQuestion` + `save_user_question()` already wired in 4 legacy paths but ZERO save call at the live raw passthrough sync exit (flask_app.py:5937) or stream exit (line 6709) — Ask history was silently empty. Legacy save also explicitly excluded answer text. **Changes**: (a) `models.py UserQuestion` gained `answer_text` (Text, 8000-char cap) + `answer_source` (VARCHAR(40) indexed) nullable columns. (b) `save_user_question()` signature extended with both kwargs (None-safe, length-capped, exception-swallowing). (c) Both raw passthrough exits gained `if rp_user is not None: save_user_question(...)` — pulls topic from `out["topic"]`, source/verdict from `out["source"]`, full answer from `out["text"]`, primary_kundli_id from `rp_user.kundli.id`. Anon questions intentionally skipped (UserQuestion.user_id is NOT NULL). (d) DB migration applied via in-app `ALTER TABLE`. **Verification**: 3x authenticated smoke on user_id=33 — finance/marriage/lagna Qs all persisted with correct topic + source + answer text. Foundation for future Phase B (UCML correction loop) and Phase E (outcome dashboard).
- **KP-Driven STEP1 Auto-Promote — Phase 2.5.11.18 (May 7 2026)**: Follow-on to 2.5.11.17 audit-flag (Ketu KP-signified all 3 travel houses STRONG but was dropped by hardcoded `_KARAKA_FLOOR_SURVIVORS`). New `kp_promote_survivors(d1_map, kp, domain, threshold=2)` — data-adaptive promotion across all 5 engines. Schema-tolerant (reuses `compute_kp_planet_scan` + `CONCERN_HOUSES`). Engine's own hardcoded floor RETAINED as safety net for charts where KP data is missing. All 5 engines wired with try/except guarded call between `_step1_d1_filter(...)` and survivors-set construction; emits `factors.append("STEP1 KP-promoted=[...]")` when any planet promoted. 4 new tests, 173/174 total green. Live verification: Ketu now appears in travel survivors set (7→8) on Raj chart.

**Earlier consolidated** (Phases 2.5.11.4 → 2.5.11.17): Ask-flow sensitivity expansion + marriage psychology + specific-partner synastry bridge (.4-.6); Health/Finance engine trims and KP convergence waves (.9-.12-b — Health D30 removal, KP 3-layer at-risk filter, STEP 6/7 removal, Finance D2/transits/SAV/yogas removal, Finance KP-as-final-filter hard gate); Travel past-window lookback + architect follow-up (.14, .14-b); Universal Double-Transit (K.N.Rao) shared helper rolled out to travel — empirically failed on travel ground-truth, kept as universal mandate (.15, .15-c); Travel Moon-floor + KP-Dasha-Gate + past-window diversification (.16). All entries are in git history if needed.

## Product
- **Mobile App**: Daily Rashifal, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, personalized forecasts ("Risk Radar"), Life Mastery Report.
- **AI-driven Insights**: AI-powered interpretations with anti-hallucination pipelines, RAG for classical Vedic knowledge, and structured output modes.
- **Localization**: Supports 25 languages with region detection.

## User preferences
- The user wants the AI to act as a Replit coding agent.
- **Strict development methodology** for every new engine: `engine.py file (sahi folder mein)`, `Unit test (test_engine.py)`, `locked_facts.py wiring`, `Rule entry in system prompt`, `Deterministic post-injector`, `3x smoke test on real chart (/tmp/k.json, /tmp/req.json, /tmp/qm.json)`, `Architect review (code_review skill)`, `replit.md entry` are all mandatory.
- The user has provided a clear roadmap for project phases and expects strict adherence. Deviations require explicit user confirmation.
- The user expects the AI to avoid hallucinating, especially regarding timing-related questions.
- **UNIVERSAL TIMING RULE (Phase 2.5.11.15, MANDATORY for ALL engines)**: For ANY event-prediction question — past, present, OR future ("kab hoga / kab gaya tha / kab jaaunga / when") — Jupiter+Saturn DOUBLE TRANSIT (K.N.Rao classical rule) is COMPULSORY on the **concerned house AND concerned house lords**. Dasha alone is never sufficient. Use shared helper `event_timing/_shared/double_transit.py::check_double_transit(...)`. Concern-house presets (single source of truth): `travel=[3,9,12]`, `health=[1,6,8,12]`, `finance=[2,5,9,11]`, `marriage=[7,2,8,11]`, `baby=[5,11]`, `career=[10,6,2,11]`. Every timing engine MUST annotate past_windows / current_window / next_windows with `double_transit` field AND append the `DOUBLE_TRANSIT_TIMING_RULE_APPLIED` directive. **Caveat**: empirically failed on travel ground-truth (Phase 2.5.11.15-c) — rule is RETAINED but framework re-design pending before health/finance/marriage rollout.
- The user wants the AI to integrate classical Vedic knowledge through RAG for opinion-based questions, but strictly NOT for timing questions.
- Brand voice: "Powered by Advanced Cosmic Intelligence". AI is never named; AI = language layer only; backend = facts; post-injectors = mandatory citation safety net.
- The user prefers deterministic post-injectors to ensure mandatory facts are cited even if the AI misclassifies a topic.
- The user prefers that the AI refine language for opinion questions but must cite engine facts.
- Mandatory disclaimers per domain: medical (banner + 3-confirmation rule for severity tiers), financial (banner + tiered risk profile), remedies ("SUPPLEMENT, never substitute action" + free + paid alternatives), Astrocartography ("energetic affinity, not guaranteed luck"), and ethical/safety disclaimers for sensitive topics (lifespan, death prediction, destiny vs. guidance).
- Numerology PDF Pro branding: hybrid numerology + Vedic Astrology content, framed with numerology language.

## Gotchas
- **Static Gate Parity**: Any new engine/gate added to `/api/ask` MUST simultaneously be added to `/api/ask/stream`.
- **Cache Invalidation**: Any policy change requires bumping the cache namespace (`_vX`).
- **Vedic Vocab Stripping**: The validator strips Vedic terms unless explicitly opted in or the user's question contains a "tech-request" keyword.
- **Topic-Lock Conflicts**: When multiple injection points compete, the latest injected point in the user message order wins.
- **DB-Load Enforcement**: For authenticated users, `kundli` is always loaded from the database; client-supplied `kundli` is for anonymous demo mode only.
- **LLM Temperature**: The `temperature` parameter is often rejected by `gpt-5` models.
- **Telemetry Best-Effort**: Telemetry inserts are wrapped in `try/except` and silently drop rows on contention.
- **Anon Q&A**: `UserQuestion.user_id` is NOT NULL — anonymous Asks are intentionally NOT persisted. Add a separate telemetry table if anon analytics needed.
- **DB Migrations**: `db.create_all()` does NOT add columns to existing tables. Use `ALTER TABLE` directly when adding columns.
- **Naive datetime drift**: `datetime.utcnow()` + `_parse_iso()` may drift on `±HH:MM` ISO offsets across all 5 engines (deferred — needs monorepo-wide tz normalization).

## Pointers
- **Relevant Skills**: `code_review`, `telemetry`, `test_generation`
- **External Docs**:
    - [pnpm workspaces](https://pnpm.pnpm.io/workspaces)
    - [Expo React Native](https://docs.expo.dev/)
    - [Flask Documentation](https://flask.palletsprojects.com/en/latest/)
    - [Pyswisseph Library](https://pyswisseph.readthedocs.io/en/latest/)
    - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
