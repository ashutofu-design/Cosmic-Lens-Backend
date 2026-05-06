# Cosmic Lens
A mobile Vedic Astrology application delivering highly accurate astrological analyses and AI-driven interpretations.

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
- **Property Focus Block (P1.2.4 + .1 + .5 chart-trim + .6 axes-routing)**: Per-topic analysis framework injected into LLM system prompt for property/ghar questions. **P1.2.4 dasha-leak post-injector**: deterministic `strip_dasha_leak(text, question) -> (cleaned, n)` in `property_focus_routing.py` drops sentences mentioning dasha/phase from STATIC_YOG / YOG_QUALITY answers (NO-OP for TIMING). Intent classifier `_detect_property_intent` (TIMING > QUALITY > STATIC) gates strip. Wired post-`_strip_verdict_label_prefixes` at sync passthrough (~L14568) + stream passthrough final (~L18229), gated on `_is_property_topic() and _property_focus_enabled()`, traces `PASSTHROUGH[(stream)].DASHA_LEAK_STRIPPED` / `*.DASHA_LEAK_SKIP`. Validation 6/6 STATIC/QUALITY clean + 3/3 TIMING preserved on P40 chart. **P1.2.4.1 (architect-fix)**: regex extended to single-planet dasha forms (`<planet> ka/ki dasha`, `<planet> dasha chal/me/active/running`, `currently in <planet> dasha/phase/period`, `<planet> sub-period`); TIMING triggers widened from 9→17 (`kab tak`, `by when`, `is/agle saal/mahine/hafte`, `kitne time`, `by <month|YYYY>`). Unit-test 15/15 (6 single-planet strips + 5 TIMING preserves + 4 regression incl. false-positive guard). **Deferred (need permission)**: (i) wire post-injector at narrative path (~L4532) + legacy passthrough (~L3883) — currently passthrough-only (>95% traffic since `LLM_FULL_CHART_MODE` ON), fallback paths unprotected; (ii) sentence-segmentation fallback for punctuation-light Hinglish (currently splits on `.!?।` only). Killswitch: `PROPERTY_FOCUS_BLOCK ∈ {0,false,no,off}` (same env gate as P1.2 framework). **P1.2.5 (user-feedback "STATIC me dasha kyu jaa raha hai → remove")**: dasha-leak post-injector strips OUTPUT, but the LLM was still being FED Sections 4 (CURRENT DASHA TREE), 5 (UPCOMING DASHA SEQUENCE), 8 (GOCHAR), 9 (DASHA + TRANSIT OVERLAY) on every property Q via `build_full_chart_context` — wasted tokens + temptation to leak. New helper `trim_dasha_sections(chart_block, question) -> (trimmed, n)` in `property_focus_routing.py` splits the chart-block on `## N.` section boundaries and drops the 4 dasha/transit sections when intent is STATIC or QUALITY. KEPT for STATIC/QUALITY: Sec 1 (Janm/Lagna), 2 (Grahas full), 3 (Bhavas full), 6 (D9 Navamsha), 15 (Niyam), plus separate KP block (KP-ALWAYS-FULL still wires all 12 cusps + 9 significators). NO-OP for TIMING (full chart preserved byte-identical). Wired AT chart-build sites (BEFORE message assembly): legacy passthrough (~L3860), sync passthrough (~L14376), stream passthrough (~L17949) — gated on `_is_property_topic() and _property_focus_enabled()`, try/except trace `PASSTHROUGH[(stream)].CHART_TRIMMED` (logs `dropped_sections + before_chars + after_chars`) / `*.CHART_TRIM_SKIP` on failure. Defensive: returns input unchanged when chart format doesn't match (NO-OP, never blocks request). **Validation**: unit-test 6 asserts pass — STATIC/QUALITY drop exactly 4 sections (6323→3266 chars, **~48% token savings**), TIMING preserves byte-identical (n_dropped=0), empty input + no-section-marker text no-op. **Integration 4/4 on P40**: STATIC + QUALITY clean (zero leaks, answers from 4H/10L/Mangal-8H structural positions only — no dasha citation possible since LLM never saw sections 4-9), TIMING preserves dasha context (REFUSE_TIMING correctly cites "Moon Mahadasha aur Mars Antardasha chal rahi hai"). Pairs with P1.2.4 post-injector as defense-in-depth: P1.2.5 prevents leaks at SOURCE, P1.2.4 catches any remaining leakage at SINK. **P1.2.6 (user-feedback "atomic block bhi alag-alag chahiye, jitna chahiye utna do")**: original `build_property_focus(question)` dumped ALL 25 atomic CHECK blocks (~8043 chars) into every property prompt, expecting the LLM to self-route via the framework header's STEP1/STEP2 instructions. Wasteful — typical Q only needs 3-5 blocks. New `detect_property_axes(question) -> {action, scopes, intent, edges, appendix}` (regex-based, ~30 patterns) detects axes server-side. ACTION (DISPUTE > INHERIT > BUILD > RENT > SELL > BUY > ANALYZE-default; first-match-wins precedence). SCOPES (FOREIGN/LAND/COMMERCIAL/MULTIPLE — 0+ matches). EDGES (JOINT_TITLE/LOAN_EMI — 0+). INTENT reuses `_detect_property_intent` (TIMING > QUALITY > STATIC) + REFUSE_TIMING when TIMING + explicit "exact date / specific date / exactly kab / griha-pravesh date / tareekh batao". APPENDIX: RISK on negative-tone keywords, REMEDY always-on except for REFUSE_TIMING (which IS the closer). LOAN_EMI implies BUY when no other action verb matches. `build_property_focus(question)` now returns COMPACT axes-routed block (~1.7-2.5 KB, 70-78% savings) using `_AXES_FRAMEWORK_HEADER` (~400 chars compact, replaces ~5 KB STEP1/STEP2 + worked-examples header) + only matched atomics + `_ANSWER_STYLE` (kept). Killswitch `PROPERTY_FOCUS_AXES ∈ {0,false,no,off}` (default ON, **independent** from `PROPERTY_FOCUS_BLOCK` for granular rollback). Empty/non-string question → fat-dump fallback. Caller `_passthrough_property_focus` already passes `question` — NO openai_helper.py edits needed (signature preserved). **P1.2.6.2 (architect-fix)**: (i) REFUSE_TIMING assembly order fix — when intent is REFUSE_TIMING, assemble as `[action, scopes, edges, appendix, REFUSE_TIMING-LAST]` so refuse-line lands as closer (was placed mid-stack before edges/appendix); (ii) `_picked_atomic_blocks_dump` rewritten to respect caller-provided picked-order (was iterating ATOMIC_CHECKS declaration-order, defeating the assembly ordering); (iii) `_RISK_RX` dropped "safe hai", "theek hai", bare "safe" — those are POSITIVE phrasings ("ghar safe hai?") causing RISK false-positives; (iv) silent fallback now logs `[property_focus_axes][FALLBACK_COUNT=N] axes detection failed → fat-dump fallback: <Type>: <msg>` with module-level counter for crude alerting (matches `_passthrough_property_focus` FALLBACK_COUNT pattern). **Validation**: 18/18 axes-detection unit tests + 9/9 architect-fix asserts (REFUSE_TIMING-last verified across 4 combos incl. JOINT_TITLE+LOAN_EMI+RISK; "safe hai"/"theek hai" no-RISK; "nuksan" still fires; synthetic-exception triggers logged fallback). Sizes: 1739-2497 chars (axes mode) vs 8043 (fat) → ~70-78% input-token savings. P40 smoke: STATIC+BUY Q cites 4H Meen + Guru 10H + Mangal 8H neecha + Shukra 1H + Hanuman remedy (full quality preserved); TIMING Q cites houses + Moon-Mars phase (correct dasha context). Defensive: invalid input (None/123/[]/{}/'   ') → fat-dump fallback no-crash. Pairs with P1.2.5 chart-trim: combined ~55% total token reduction per property STATIC Q (~3,965 → ~1,800 input tokens, same answer quality).
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