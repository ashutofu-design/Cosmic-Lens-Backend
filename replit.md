# Cosmic Lens
A pnpm workspace monorepo for a mobile Vedic Astrology application, aiming for over 97% accuracy in astrological analysis, including kundli calculations, numerology, Vastu, and AI-driven interpretations.

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
    - `ask_cosmo/`: Question understanding and intent classification.
    - `reply_cosmo/`: Response shaping and LLM interaction.
    - `event_timing/marriage/`: Marriage timing engine.
    - `finance/`: Finance static engine.
    - `health_static/`: Health static engine.
    - `kundli_engine/`: Core astrological calculation engine (`pyswisseph` integration).
    - `tests/golden/`: Golden marriage tests.
- `packages/`: Shared utilities and components.
- **DB Schema**: `artifacts/api-server/database.py` (for SQLite/PostgreSQL)
- **API Contracts**: Defined implicitly by Flask routes in `flask_app.py`
- **Theme Files**: `apps/mobile/src/theme/`

## Architecture decisions
- **Monorepo Structure**: Uses pnpm workspaces for better dependency management and code sharing between mobile and backend.
- **CLE (Cosmic Lens Engine) Format**: Backend astrological calculations follow a strict modular engine format for consistency and accuracy.
- **LOCKED FACTS Protocol**: Deterministic data for AI responses is centralized in `locked_facts.py` to prevent hallucination.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors for safety and brand consistency.
- **Two-Layer Prompting**: "Guided Freedom" approach for LLM prompts (80% mindset, 20% surgical guards) to balance flexibility and control.
- **Engine-Controlled Verdicts**: For certain complex questions (e.g., comparative health, marriage timing), the final verdict line is generated deterministically by the engine, not the LLM, to ensure accuracy and prevent drift. H2.7.16-fix2 added immunity-vs-lifestyle deterministic verdict (`_build_immunity_lifestyle_verdict` in `health_replies.py`) injected as MANDATORY first sentence; post-injector force-prepends if LLM drops it. Killswitch `HEALTH_ENGINE_VERDICT=0`.
- **Health Reply Sanitizer (H2.7.16)**: Post-LLM regex sweep (`_sanitize_health_reply`) strips 4 leak categories — disease overgeneration, planet-pair jargon (with plain-Hinglish glossary), timing words/phrases, fear tone. Runs BEFORE word-cap (architect-mandated order). Killswitch `HEALTH_REPLY_SANITIZER=0`.
- **Signal-Pack Layer (H2.7.17)**: "Controlled freedom" architecture — engine builds compact JSON signal-pack (`_build_signal_pack` in `health_replies.py`) with normalized dim states (weak/moderate/stable etc), primary/secondary drivers, key_factors, remedy_focus, engine_verdict. LLM gets ONLY this JSON (no raw kundli, no planets, no houses) → pure expression layer. Falls back to raw-pack path for unregistered question_types. Killswitch `HEALTH_SIGNAL_PACK=0`.
- **Universal Signal Pack v2 (H2.7.19)**: Per-question-type registry was abandoned (does not scale to N question types). Replaced with ONE universal pack always built containing all 4 dims (vitality, immunity, mental, chronic) each with `state` + plain `reason`, plus `overall_snapshot` 1-liner. LLM is intelligent — given strict "USE ONLY signals, do not infer new symptoms/conditions" prompt + sanitizer + bans, it correctly picks relevant dims per question. Engine-side classifier kept ONLY for the rare comparative-math case (`compare_immunity_vs_lifestyle`) where engine adds deterministic `engine_verdict` for verbatim lead. All other Qs: LLM picks freely from pack. Live-tested 16/16 top static health Qs (Rajalaxmi P40 all-RED) with zero planet/house/timing/disease/fear/escalation leaks. Routing (`_HEALTH_TOPIC_RX`) extended with vague-discomfort + common-ailment vocab (sardi, zukam, pet, gas, sirdard, thakan, gala, etc.). Cache namespace v11 → v12.

## Product
- **Mobile App**: Daily Rashifal, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, personalized forecasts ("Risk Radar"), Life Mastery Report.
- **AI-driven Insights**: AI-powered interpretations with anti-hallucination pipelines, RAG for classical Vedic knowledge, and structured output modes for sensitive topics (health, finance).
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
- **Static Gate Parity**: Any new engine/gate added to `/api/ask` MUST simultaneously be added to `/api/ask/stream`. The two routes have independent pipelines.
- **Cache Invalidation**: Any policy change (e.g., length caps, content bans) affecting static engine output or LLM responses requires bumping the cache namespace (`_vX`) to prevent stale cached replies from bypassing new rules.
- **Vedic Vocab Stripping**: The validator strips Vedic terms (planet names, house numbers) unless explicitly opted in or the user's question contains a "tech-request" keyword.
- **Topic-Lock Conflicts**: When multiple injection points (system prompt, user-prepended block, locked-facts block) compete, the latest injected point in the user message order wins.
- **DB-Load Enforcement**: For authenticated users, `kundli` is always loaded from the database; client-supplied `kundli` is for anonymous demo mode only.
- **LLM Temperature**: The `temperature` parameter is often rejected by `gpt-5` models, meaning LLM strict mode is currently dormant for those models.
- **Telemetry Best-Effort**: Telemetry inserts are wrapped in `try/except` and silently drop rows on contention to avoid blocking user requests.

## Pointers
- **Relevant Skills**: `code_review`, `telemetry`, `test_generation`
- **External Docs**:
    - [pnpm workspaces](https://pnpm.io/workspaces)
    - [Expo React Native](https://docs.expo.dev/)
    - [Flask Documentation](https://flask.palletsprojects.com/en/latest/)
    - [Pyswisseph Library](https://pyswisseph.readthedocs.io/en/latest/)
    - [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)