# Cosmic Lens
A mobile Vedic Astrology application delivering accurate astrological analyses and AI-driven interpretations.

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
- **Property Focus Block** (`property_focus_routing.py`): Per-topic analysis framework for property/ghar Qs. Layers: P1.2.4 dasha-leak post-injector (sink-side strip), P1.2.5 chart-section trim (drops dasha sections 4/5/8/9 for STATIC/QUALITY), P1.2.6 axes-routing (server-side action/scope/intent/edge detection → only matched atomic blocks emitted, ~75% framework token savings), P1.2.7.2 timing-keyword fix (`delay|early|jaldi|late|soon` moved from QUALITY → TIMING regex so dasha context preserved for "delay hoga?" style Qs), P1.2.7 chart-slice (drops irrelevant Sec-2 planet rows + Sec-3 bhava rows; keeps houses {1,2,4,11,12} + karaka-occupied + karakas {Mars,Venus,Jupiter,Saturn} + Lagnesh + relevant-house lords + aspecting planets). Combined ~57% chart + ~75% framework reduction. Killswitches: `PROPERTY_FOCUS_BLOCK`, `PROPERTY_FOCUS_AXES`, `PROPERTY_CHART_SLICE` (all default ON, independent). NO-OP for TIMING intent (full chart preserved).
- **KP-ALWAYS-FULL**: When enabled, sends all 12 cusps and all 9 planet significators to the LLM for every question.
- **Routing Context Guards**: Implements a three-layer disambiguation for question routing.

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
    - [pnpm workspaces](https://pnpm.io/workspaces)
    - [Expo React Native](https://docs.expo.dev/)
    - [Flask Documentation](https://flask.palletsprojects.com/en/latest/)
    - [Pyswisseph Library](https://pyswisseph.readthedocs.io/en/latest/)
    - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)