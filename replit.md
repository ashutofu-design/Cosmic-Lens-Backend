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

## Architecture decisions
- **Monorepo Structure**: Uses pnpm workspaces for dependency management and code sharing.
- **CLE (Cosmic Lens Engine) Format**: Backend astrological calculations follow a strict modular engine format.
- **LOCKED FACTS Protocol**: Deterministic data for AI responses is centralized in `locked_facts.py` to prevent hallucination.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors.
- **Two-Layer Prompting**: "Guided Freedom" approach for LLM prompts (80% mindset, 20% surgical guards).
- **Engine-Controlled Verdicts**: Complex questions (e.g., marriage timing) use engine-generated verdicts, not LLM.
- **Signal-Pack Layer**: Engine builds a compact JSON signal-pack for LLM expression, preventing raw astrological data exposure.
- **Universal Signal Pack v2**: Replaced per-question-type registries with one universal pack containing all four health dimensions for LLM interpretation.
- **Mandatory Final Verdict**: Enforces a sharp, engine-built final verdict line (`👉 Final:`) in responses.
- **Property Focus Block**: Per-topic analysis framework for property questions, with layered processing and chart slicing for efficiency.
- **KP-ALWAYS-FULL**: When enabled, sends all 12 cusps and all 9 planet significators to the LLM for every question.
- **Multi-Intent Splitter**: Handles questions with multiple astrological domains by identifying a primary intent and acknowledging secondary ones.
- **Question Length Cap**: Implements a hard character limit on incoming questions to conserve tokens.
- **Unified Question-Type Gate**: Centralized deterministic logic for classifying questions as TIMING or STATIC.
- **Routing Context Guards**: Implements a three-layer disambiguation for question routing.
- **Health Focus Block (CAFB-health)**: Replaces legacy health rule-engine, implementing atomic checks, a 4-axis detector, chart-slicer, and hard-guards for sensitive health topics, including a pre-gate for crisis detection.
- **RAW PASSTHROUGH MODE (2026-05-06, default ON)**: User-requested nuclear simplification. `RAW_PASSTHROUGH_MODE=1` (default) bypasses ALL legacy gates — length-cap, brand-guard, layer3-clarifier, crisis-pregate, shortcut, every static engine (health/property/finance), classifier-routing, signal-packs, post-injectors, multi-intent ack, disclaimers — and routes `/api/ask` + `/api/ask/stream` through `openai_helper.raw_passthrough_ask()`. Pipeline: `auth + DB-load kundli (FAIL-CLOSED, tamper-proof) + quota (FAIL-CLOSED) → classify_question_type() → STATIC: D1+D9 only / TIMING: D1+D9+currentDasha → ONE unified mega-prompt → single LLM call → answer`. Tunables: `RAW_PASSTHROUGH_MODEL` (default `gpt-4.1-mini`), `RAW_PASSTHROUGH_MAX_TOKENS` (default `700`). Killswitch: `RAW_PASSTHROUGH_MODE=0` reverts to legacy pipeline (all gate code intact, just bypassed).
- **Unified Mega-Prompt (2026-05-06)**: One single system prompt covers all topics — LLM picks the relevant checklist based on the user's question. Embeds: (a) Core reading method = D1 placement read + **mandatory D9 cross-check**; (b) **SPECIAL ASPECTS table** — Mars 4/7/8, Jupiter 5/7/9, Saturn 3/7/10, Rahu/Ketu 5/7/9 (prevents LLM from defaulting to only 7th-aspect reading); (c) **YOGA LIBRARY** — positive (Raj, Dhana, Gajakesari, Pancha Mahapurusha, Neecha-Bhanga, Vipareeta Raja, Budh-Aditya, Chandra-Mangal, Adhi, Parivartana) + negative (Kemadruma, Kala Sarpa, Vish, Shakat, Guru Chandal, Angarak, Pitra Dosha, Mangal Dosha); (d) **CANCELLATION RULES** — Neecha Bhanga, Vipareeta Raja, Mangal Dosha bhanga (LLM must check cancellation before declaring a planet "weak"); (e) Topic checklist for wealth/marriage/love-vs-arranged/career/health/children/education/property/foreign/spirituality/litigation/parents/siblings/longevity; (f) STATIC vs TIMING output rule injected per request. Defined inline in `raw_passthrough_ask()`.

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