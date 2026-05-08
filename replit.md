# Cosmic Lens
A mobile Vedic Astrology application delivering accurate astrological analyses and AI-driven interpretations to users.

## Run & Operate
- **Run**: `pnpm dev`
- **Build**: `pnpm build`
- **Typecheck**: `pnpm typecheck`
- **Codegen**: `pnpm codegen`
- **DB Push**: `pnpm db:push`
- **Required Env Vars**: `OPENAI_API_KEY`, `DATABASE_URL`, `HEALTH_LLM_MODEL`, `HEALTH_ROUTER_MODEL`, `FINANCE_STATIC_BYPASS`, `HEALTH_STATIC_BYPASS`, `LEAN_PACK_MODE`, `LAYER2_FUZZY`, `LAYER3_LLM`, `COMPAT_PREMIUM_POLISH`, `COMPAT_PREMIUM_MODEL`

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
- **Question History**: `artifacts/api-server/question_history.py`
- **Engines**: `artifacts/api-server/event_timing/{health,marriage,finance,travel,baby}/`, `artifacts/api-server/remedy/`, `artifacts/api-server/vedic/compat/`
- **Shared Engine Helpers**: `artifacts/api-server/event_timing/_shared/` (KP scan, double-transit)
- **LLM Orchestration**: `artifacts/api-server/openai_helper.py`, `artifacts/api-server/reply_cosmo/engine_locked_to_llm/locked_facts.py`
- **Engine Lineage & Phase History**: `docs/engines.md`

## Architecture decisions
- **Monorepo Structure**: pnpm workspaces for dependency management and code sharing.
- **2-Path Routing**: Live ask endpoint splits into `raw_passthrough_timing` (engine-locked, deterministic) and `raw_passthrough_static` (LLM-driven, jargon-free). `RAW_PASSTHROUGH_MODE=1` is the only live path; legacy paths kept for fallback.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors.
- **User Context Memory Layer (UCML) v1**: Silent, deterministic memory module (`user_memory.py`) building per-user profiles from question history with three tiers: `user_facts` (L1), `user_behavior` (L2), `user_personality` (L3). Engine accesses DB; LLM never touches it.
- **User-Facing Translation Layer (GOLDEN RULE)**: Bans all astrology jargon from user-facing output.
- **Engine Pipeline (5 timing engines)**: FILTER → VERIFY → KP-GATE → ACTIVATE → TRIGGER. Health v1, Marriage v2.4, Finance v1, Travel v1, Baby v1. Companion: Remedy Engine v1.1, Dasha Timeline Block, Ask-flow Sensitivity layer. Full per-engine specifics, weights, KP cusps, and shared helpers in `docs/engines.md`.

## Latest Phase
- **Phase 2.5.11.23-soul-v2 — Kundli Milan Pro PDF SOUL v2 (ChatGPT-critique-driven, May 8 2026)**: Killed the formulaic-template feel that v1 still had under the hood. Six big shifts driven by the user's ChatGPT critique: **(1) Archetype change** — `SYSTEM_PROMPT_PREMIUM` swapped from "wise family elder" to "experienced modern relationship astrologer — Vedic-rooted but contemporary in voice. Sharp, warm, emotionally honest — never preachy, never motivational." Removes risk of preachy/old-fashioned/spiritual-lecture tone. **(2) `EMOTIONAL REALISM RULES` section added** — explicitly bans perfect-balance language ("dono naturally same boat me", "both equally invested"), allows asymmetry ("ek partner zyada invest karta hai, dusra silently sambhalta hai"), allows contradiction ("Love is present here, but reassurance arrives in different emotional languages"), allows timing mismatch + silent expectations + bittersweet truths. **(3) `SIGNATURE INSIGHT RULE` added** — every chapter MUST contain ≥1 high-specificity emotional observation that feels impossible to say generically. Examples baked in: "One person waits quietly instead of asking directly", "Distance here grows more through silence than anger". **(4) `THERAPY-CLICHE BAN` added** — banned: "honest dialogue", "mutual respect", "consistent care", "open communication", "communicate openly", "build trust", "show appreciation", "active listening", "be patient with each other", "express your feelings", "make time for each other". Validator allows ≤1 cliche in passing, rejects ≥2 (density check). **(5) Per-chapter name density dropped** — v1's ≥3 names PER CHAPTER over-constrained creativity. v2 keeps global ≥3 in validator (already enforced) but drops the per-chapter quota — names land naturally. **(6) 3-layer structure preserved internally but de-segmented in prose** — JSON keys (kya_dikh/kya_matlab/kya_dhyan) unchanged for renderer compatibility, but prompt explicitly says "treat them as a natural narrative arc, NOT as labeled bullet sections — the reader must NOT feel Layer 1, Layer 2, Layer 3". New constants: `THERAPY_CLICHES` (12 phrases) + `PERFECT_BALANCE_PHRASES` (6 phrases). Validator extended with both checks; rejects "perfect_balance_phrase:*" instantly + "therapy_cliche_density:N" when N≥2. **`_CH_SOUL` library fully rewritten — 63 templates (7 ch × 3 bands × 3 blocks)** with v2 principles baked in: every template carries asymmetric "ek partner...dusra..." language, ≥1 signature insight per chapter (e.g. ch3.LOW: "fight 'jeetne' se raahat nahi aati, kyunki jeeti hui baat woh nahi thi jo actually hurt kar rahi thi"; ch6.HIGH: "invisible labor karne wala dheere thakega, aur uski thakaan dikhegi nahi jab tak woh bahut baad me bahar nahi aati"; ch7.MID: "ek baat khaane ki table pe sirf weather pe hoti hai"), zero therapy cliches, zero perfect-balance language, free-flowing prose with concrete moments ("Sunday raat ko jab dono thake hain", "5-minute joint silence", "20-minute walk bina phone"). ch4 + ch7 kya_dhyan still satisfy `ALLOWED_REMEDIES` whitelist ("Joint daily prayers", "yearly anniversary ritual"). Defensive fix: `_safe_fallback` `grounding` field now populated ("Reading anchored to {title} layer — band {band}, {p1n} & {p2n} chart cross-reference") so fallback is self-consistent against validator. **8 new v2 regression tests** appended to `test_premium_chapters_soul.py`: therapy-cliche density absence in fallback, perfect-balance language absence in fallback, validator rejects therapy-cliche density ≥2, validator rejects each PERFECT_BALANCE phrase, validator accepts 1 isolated cliche (no over-rejection), fallback carries asymmetry markers in ≥6/7 chapters, SYSTEM_PROMPT carries all v2 sections + new archetype + dropped v1 archetype, signature-insight specificity heuristic per chapter. **21/21 tests green; architect review clean (zero critical/high, one medium addressed — fallback grounding self-consistency).** POLISH=0 still in env (gpt-4o not firing), so v2 deterministic fallback is what users currently read. Brand voice preserved; AI never named; backend = facts; post-injectors = mandatory citation safety net. Phase 2.5.11.23-soul (v1) entry archived in `docs/engines.md`.

- **Phase 2.5.11.23-soul — Kundli Milan Pro PDF SOUL pass (May 8 2026)**: Killed the "audit-report" feel. `_safe_fallback()` rewritten with 3-layer prose architecture: kya_dikh (signal in plain emotional language) → kya_matlab (real-life behavioural pattern with concrete moment) → kya_dhyan (one specific anchor + grounding ritual). New `_CH_SOUL` library: 7 chapters × 3 score-bands (HIGH ≥7 / MID 4-6.9 / LOW <4) × 3 blocks = 63 name-anchored Hinglish prose templates. New `_special_bullet`/`_damage_bullet` generators replace generic "no friction detected" lines. **Polish-path validator hardened (deterministic enforcement of prompt laws)**: new `SOUL_BAN_PHRASES` denylist baked into `_validate_premium()` so gpt-4o output that regresses to audit-tone ("engine driver", "no significant friction", "natural baseline compatibility", etc) is rejected; name-density rule lifted from ≥1 to ≥3 mentions per partner; SYSTEM_PROMPT_PREMIUM mirrors the same hard-ban + 3-layer + specificity laws. `_safe_fallback()` defensively normalizes malformed `milan_facts` / `chapter_scores` (string-typed `total`, list-typed `chapters`, missing dicts, None) — never raises. `milan_pdf.py` placeholder also rewritten to soul tone. New `test_premium_chapters_soul.py` (13 regression tests): banned-phrase absence in fallback prose, 3-layer presence, name density ≥5, score citation, HIGH→special / LOW→damage routing, ≥1400 words, concrete-practice keyword in kya_dhyan, validator accepts soul payload, validator rejects every entry in SOUL_BAN_PHRASES, validator rejects low name density, fallback survives 8 malformed `chapter_scores` shapes + 8 malformed `milan_facts` shapes. **26/26 tests green; 3-lang live smoke clean: en/hn ≈2,618 words & 24pp, hi 1,358w & 24pp (Devanagari); zero banned phrases across all 3 PDFs.** Word density ~2.2× the audit-feel version. Phase 2.5.11.23 backend (5 `vedic/compat/` modules, dual-shape endpoint, mobile single-call wiring) unchanged. Full prior phase history in `docs/engines.md`.

## Product
- **Mobile App**: Daily Rashifal, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, personalized forecasts ("Risk Radar"), Life Mastery Report.
- **AI-driven Insights**: AI-powered interpretations with anti-hallucination pipelines, RAG for classical Vedic knowledge, and structured output modes.
- **Localization**: Supports 25 languages with region detection.

## User preferences
- The user wants the AI to act as a Replit coding agent.
- **Strict development methodology** for every new engine: engine.py file (correct folder), unit test (`test_engine.py`), `locked_facts.py` wiring, rule entry in system prompt, deterministic post-injector, 3x smoke test on real chart (`/tmp/k.json`, `/tmp/req.json`, `/tmp/qm.json`), architect review (`code_review` skill), and `replit.md` entry are all mandatory.
- The user has provided a clear roadmap for project phases and expects strict adherence. Deviations require explicit user confirmation.
- The user expects the AI to avoid hallucinating, especially regarding timing-related questions.
- **UNIVERSAL TIMING RULE (MANDATORY for ALL timing engines)**: Jupiter+Saturn DOUBLE TRANSIT (K.N.Rao classical rule) is COMPULSORY on the concerned house AND concerned house lords for ANY event-prediction question. Dasha alone never sufficient. Helper + concern-house presets + caveat in `docs/engines.md`.
- The user wants the AI to integrate classical Vedic knowledge through RAG for opinion-based questions, but strictly NOT for timing questions.
- Brand voice: "Powered by Advanced Cosmic Intelligence". AI is never named; AI = language layer only; backend = facts; post-injectors = mandatory citation safety net.
- The user prefers deterministic post-injectors to ensure mandatory facts are cited even if the AI misclassifies a topic.
- The user prefers that the AI refine language for opinion questions but must cite engine facts.
- Mandatory disclaimers per domain: medical (banner + 3-confirmation rule), financial (banner + tiered risk profile), remedies ("SUPPLEMENT, never substitute action" + free + paid alternatives), Astrocartography ("energetic affinity, not guaranteed luck"), and ethical/safety disclaimers for sensitive topics (lifespan, death prediction, destiny vs. guidance).
- Numerology PDF Pro branding: hybrid numerology + Vedic Astrology content, framed with numerology language.

## Gotchas
- **Static Gate Parity**: Any new engine/gate added to `/api/ask` MUST simultaneously be added to `/api/ask/stream`.
- **Cache Invalidation**: Any policy change requires bumping the cache namespace (`_vX`).
- **Vedic Vocab Stripping**: The validator strips Vedic terms unless explicitly opted in or the user's question contains a "tech-request" keyword.
- **Topic-Lock Conflicts**: When multiple injection points compete, the latest injected point in the user message order wins.
- **DB-Load Enforcement**: For authenticated users, `kundli` is always loaded from the database; client-supplied `kundli` is for anonymous demo mode only.
- **LLM Temperature**: The `temperature` parameter is often rejected by `gpt-5` models.
- **Telemetry Best-Effort**: Telemetry inserts are wrapped in `try/except` and silently drop rows on contention.
- **Anon Q&A**: `UserQuestion.user_id` is NOT NULL — anonymous Asks are intentionally NOT persisted.
- **DB Migrations**: `db.create_all()` does NOT add columns to existing tables. Use `ALTER TABLE` directly.
- **Naive datetime drift**: `datetime.utcnow()` + `_parse_iso()` may drift on `±HH:MM` ISO offsets across all 5 engines (deferred — needs monorepo-wide tz normalization).

## Pointers
- **Engine reference**: `docs/engines.md` (lineage, per-engine specifics, shared helpers, UNIVERSAL TIMING RULE detail, full phase history)
- **Relevant Skills**: `code_review`, `telemetry`, `test_generation`
- **External Docs**: [pnpm workspaces](https://pnpm.pnpm.io/workspaces) · [Expo](https://docs.expo.dev/) · [Flask](https://flask.palletsprojects.com/en/latest/) · [Pyswisseph](https://pyswisseph.readthedocs.io/en/latest/) · [OpenAI API](https://platform.openai.com/docs/api-reference)
