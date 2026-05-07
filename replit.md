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
- **DB Schema**: `artifacts/api-server/database.py`
- **API Contracts**: Implicitly defined by Flask routes in `flask_app.py`
- **Theme Files**: `apps/mobile/src/theme/`
- **User Memory Layer (UCML)**: `artifacts/api-server/user_memory.py`

## Architecture decisions
- **Monorepo Structure**: Uses pnpm workspaces for dependency management and code sharing.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors.
- **User Context Memory Layer (UCML) v1**: Silent, deterministic memory module (`user_memory.py`) building per-user profiles from question history with three tiers: `user_facts` (L1 atomic), `user_behavior` (L2 aggregates), `user_personality` (L3 vector). Engine accesses DB; LLM never touches it.
- **Health Timing Engine v1.0**: 9-step health-risk timing engine at `event_timing/health/health_engine_v1.py` with medical disclaimers and age guards. Emits a `▸ TIMING ENGINE` health row to `locked_facts.py`.
- **Finance Timing Engine v1.0 (Phase 2.3, May 7 2026)**: 9-step wealth/finance timing engine at `event_timing/finance/finance_engine_v1.py`, mirroring health v1 / marriage v2.4 architecture (FILTER → VERIFY → ACTIVATE → TRIGGER). Pipeline: STEP1 D1 wealth-significator filter (2L/5L/9L/11L wealth + 6L/8L/12L leak + occupants of 2/11/12 + planets aspecting 2H + karakas Jupiter/Venus/Mercury/Sun/Moon) → STEP2 D9 dignity → STEP3 **D2 Hora** (Parashara's wealth chart, replaces D30) → STEP3.5 KP CSL of 2nd & 11th cusps → STEP4 weighted ranking (D1·30 + D9·20 + D2·25 + KP·15 + karaka·10) → STEP5 dasha activation (AD=5, PD=6, MD=1; signed wealth-promoter vs leak-bearer) → STEP6 transits (Jupiter on 2/5/11 = gain, Saturn on 2H = squeeze / 12H = drain, Rahu on 11H = sudden gain / 6H = debt risk, Sade Sati on Moon) → STEP7 SAV bindus on 2H + 11H → STEP9 yogas (Dhana / Lakshmi / Kubera / Gaja-Kesari / Vipreet-Rajyoga positive; Daridra / Kemadruma / Papakartari-on-2H negative). Verdict = `WEALTH_PROMISED | STABLE | STRESSED | HIGH_LEAK_WINDOW | UNKNOWN`; tier = `watchful | supportive | celebratory | consult` (matches **money topic** in remedy engine). Mandatory llm_directives: `FINANCIAL_DISCLAIMER`, `NOT_INVESTMENT_ADVICE`, `NO_GUARANTEED_WEALTH`, `NO_GUARANTEED_LOSS`, `SEVERITY_TIER:<tier>`, `NO_STOCK_TICKER_NAMING`. 3-confirmation rule for `consult` tier. Engine delegates remedies via `remedy.get_remedies(topic="money")`. Wired in `locked_facts.py` (▸ Finance row + finance_remedies_block) alongside legacy `wealth_timing()`. Thread-local cache `get_last_finance_result()` for downstream consumers. Tests at `test_finance_engine.py` (24 cases).
- **Remedy Engine v1.1 (Phase 2.2, May 6 2026)**: Standalone hybrid 3-tier engine at `remedy/` (catalog + remedy_engine_v1 + conflict_check + substitutions + stack_builder). Public API `get_remedies(topic, planets, areas, severity, user_facts)` + `render_for_locked_facts(result)`. Covers **health / marriage / career / money / business** × 9 grahas × 3 tiers (PRACTICAL first → AYURVEDIC → VEDIC last). Money topic = dhan-yog/savings/debt/investing (separate from career = role/income-source). Business topic = startup/founders/cashflow/scaling (separate from career = employee track). New SYSTEM_PRACTICES added for `savings, debt, investing, income_growth, expense_control, emergency_fund, credit_score, taxes, gold_assets, founders_fit, product_market_fit, cashflow, hiring, sales_pipeline, partnerships, scaling, brand, legal_compliance`. Money/business severity tiers: `watchful / supportive / celebratory / consult`. Anti-superstition: vedic never alone, every entry carries KPI + cost + caveats. Health engine delegates via `_compute_health_remedies`. Marriage uses `top_marriage_planets`, career uses `house_lords`. All topics emit parallel `▸ <TOPIC> REMEDIES` blocks via `locked_facts.py`.
- **Marriage Engine v2.4**: Integrates multi-format DOB parsing and practical-age floor for marriage window predictions, influencing LLM directives for young users.
- **User-Facing Translation Layer (GOLDEN RULE)**: Bans all astrology jargon from user-facing output.

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
- **DB-Load Enforcement**: For authenticated users, `kundli` is always loaded from the database; client-supplied `kundli` is for anonymous demo mode only.
- **LLM Temperature**: The `temperature` parameter is often rejected by `gpt-5` models.
- **Telemetry Best-Effort**: Telemetry inserts are wrapped in `try/except` and silently drop rows on contention.

## Pointers
- **Relevant Skills**: `code_review`, `telemetry`, `test_generation`
- **External Docs**:
    - [pnpm workspaces](https://pnpm.pnpm.io/workspaces)
    - [Expo React Native](https://docs.expo.dev/)
    - [Flask Documentation](https://flask.palletsprojects.com/en/latest/)
    - [Pyswisseph Library](https://pyswisseph.readthedocs.io/en/latest/)
    - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)