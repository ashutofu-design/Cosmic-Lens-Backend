# Cosmic Lens — Workspace

## Overview

Cosmic Lens is a pnpm workspace monorepo using TypeScript, focused on delivering a mobile Vedic Astrology application. The project aims to provide a comprehensive and accurate astrological analysis tool, moving beyond traditional interpretations to offer modern-context reframing and actionable insights. Key capabilities include in-depth kundli calculations, numerology, Vastu analysis, and AI-driven astrological interpretations. The long-term vision is to achieve industry-leading accuracy (97%+) through a robust calculation engine, a sophisticated AI brain, and continuous learning from user feedback.

## User Preferences

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

## System Architecture

The project is a pnpm workspace monorepo utilizing Node.js 24 and TypeScript 5.9.

**Mobile App (Expo React Native):**
- **Artifact**: `artifacts/cosmic-lens-mobile`
- **Navigation**: Bottom tabs for Home, Kundli, AI Chat, Insights, Notifications, Profile.
- **Features**: Daily Rashifal, Lucky elements, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, Forecast.
- **UI/UX**: `CosmicBg.tsx` for full-screen nebula background; `ThemeContext.cardShadow` for card glow; glassmorphism effect using semi-transparent `rgba` backgrounds; zodiac-based accent theming driven by user birth data; dark/light theme support with persistence.
- **Localization**: i18n support for 25 languages (12 Indian, 13 global) with region detection and persistence.
    - **Two-layer localization architecture**:
      - **UILang (25 langs)**: Shared UI chrome keys via `lib/i18n.ts` (`getT(language)`) — tab labels, common button text, error messages.
      - **VLang (3 buckets — `en` / `hn` / `hi`)**: Inline labels for Vedic-specific content via `lib/i18nVedic.ts` (`vedicLang(language)`). Languages without dedicated translation fall back to `hi` (Devanagari) bucket.
    - **Strict no-leakage rule**: When user picks Hindi, ZERO English/Tamil words should appear; when English picked, ZERO Devanagari characters appear. Demo data, tab labels, card titles, error messages, time/date pickers, and all chrome obey this rule.
    - **Phase 1 BLOCKER files migrated**: `app/_layout.tsx`, `app/(tabs)/_layout.tsx`, `app/(tabs)/index.tsx` (home), `app/onboarding.tsx`, `app/dosh.tsx`. Each uses inline `getXxxLabels(v)` triplet helpers + `getDemoXxxList(v)` for vlang-bucketed content.
    - **Phase 2 hardcoded-string sweep complete (2026-04-25)**: Added ~50 new keys (`vu_al*`, `prof_al*`, `sub_av*`, `dl_*`, `car_*`, `fn_*`, `hl_*`, `rl_*`, `pe2_*`) auto-translated across 21 langs (gpt-5-mini batched). Replaced hardcoded English/Hinglish in `vastu.tsx` (~22 Alert.alerts), `(tabs)/profile.tsx` (push-notif alerts + footer), `profile-edit.tsx` (Cancel/Delete + delete-warning), `subscription.tsx` (AstroVastu pricing card), `daily-alerts.tsx` (Lucky labels + EmptyState), and life-area screens (`career`, `finance`, `health`, `relationship`). Translation pipeline at `scripts/i18n-translate/` (resumable per-lang, EN-829 keys × 25 langs). MoreT type now ~830 keys; access via `useT()` hook in `hooks/useT.ts` which merges base `getT(language)` + `getMoreT(language)`.
    - **Phase 3 full Vedic-vocabulary 25-lang complete (2026-04-25)**: Translated 109 Vedic terms (12 rashi, 9 planet, 7 day, 8 dir, 16 color, 5 metal, 5 element, 9 gem, 11 deity, 27 nakshatra) across 22 langs via category-aware pipeline (`scripts/i18n-translate/translate-vedic.mjs`): astronomy/calendar terms translated to native; Sanskrit deity + nakshatra names transliterated phonetically. Regenerated `lib/i18nVedic.ts` with `LangMap = Record<UILang, string>` for vocabulary alongside legacy `Triplet = {en,hn,hi}` for paragraph content. `pick()` smart-fallback: full lang → 3-bucket → en. Verified samples: zh 白羊座/火星/拉胡/哈奴曼/阿什维尼; ar الحمل/المريخ; ta மேஷம்.
    - **Phase 3 full UI-label 25-lang complete (2026-04-25)**: Migrated `getKundliLabels` (26 keys: MAHADASHA/ANTARDASHA/PRATYANTARDASHA/Navatara/Jaimini/KP/Transit), `getProfileLabels` (10 keys: India/Global/ACTIVE/FREE/MY DATA/etc), Vastu Compass L block + tabLabels (11 keys), kundli BAV labels + Transit disclaimer (9 keys), Subscription PREMIUM/BEST VALUE badges, kundli ternary text (Ashtakavarga/Approximate Transit/House) → all use `useT()` t.* references. EN-891 keys × 25 langs.
    - **Phase 3 kundli deep-cleanup (2026-04-25)**: Added 28 more keys to `getKundliLabels` covering all `CHART_BTNS` labels + section titles + snapshot rows + Jaimini/KP/SAV literals. Replaced hardcoded `CHART_BTNS` label/sec via `chartBtnLabel(tab,L)` / `sectionTitleFor(tab,L)` helpers. Replaced inline `"Nakshatra: …"`, `"Degree within sign: … — highest in chart"`, KP English description, KP Hinglish footer ("Kisi bhi ghatna…"), `KPLordChip` Star/Sub/Sub-Sub labels, `"Asc"` chip, `"Ascendant"` full label (uses `L.snapAscendant`), header fallback `"Kundli"` (uses `t.tabKundli`), and `"Sarvashtakavarga"` heading with `L.*` / `t.ku_*` references. EN-919 keys × 25 langs.
    - **Deferred Vedic content data tables** (out of original 17-file Phase 2 plan, similar to `vastu.tsx` `ROOMS_LOC`): `kundli.tsx` `TARA_DATA` (9 Navatara entries with `name`/`desc`, English-only with `nameHindi` partial), `KARAKA_DEFS` (8 Jaimini Karaka entries with `name`/`nameHindi`/`desc`), and the bare `MONTHS = ["Jan",…,"Dec"]` array used in birth-date `formatDate()`. These render English content inside otherwise localized chrome; full 25-lang coverage would add ~450 entries and is queued as a future pass.
    - **Phase 4 TRUE 100% UI localization (2026-04-25)**: Audited & extracted all remaining hardcoded strings across 13 files (about, astrovastu-pro-result, astrovastu-pro, business-vastu, delete-account, divya-prashna, face-reading, face-reading-upload, future-partner-portrait, legal, +not-found, prashna-kundli, six-month-future). Added 314 new keys to `MoreT` (~167 `lg_*` legal/about/policy/privacy long paragraphs, 76 `bv_*` business-vastu, 55 `avp_*` astrovastu-pro, 16 `avr_*` astrovastu-pro-result) bringing EN total to **1535 keys × 25 langs = 38,375 strings**. Translation pipeline (`scripts/i18n-translate/translate.mjs`, gpt-5-mini, BATCH_SIZE=80, CONCURRENCY=10, resumable per-lang JSON) auto-translated 21 non-base langs to full coverage; 20 langs at 1535/1535, `or` at 1299/1535 (236 keys fall back to en). Patched all hardcoded English JSX in target files to `t.*` references via `useT()` hook. Long-form legal/about/policy paragraphs are now machine-translated (user-accepted AI translation quality risk). Brand voice locked: business-vastu/astrovastu say "Powered by Advanced Cosmic Intelligence" — never reveals AI/LLM/GPT. TS clean, Web Bundled OK (1831 modules).

**Backend (Python Flask):**
- **Artifact**: `artifacts/api-server`
- **Core Components**: `flask_app.py` (main server, auth, routing), `kundli_engine.py` (Vedic calculations), `kp_engine.py` (Krishnamurti Paddhati), `ask_engine.py` (rule-based AI), `requirements.txt` (dependencies).
- **Architecture**:
    - **Modular Engines**: Vedic astrological calculations are broken down into numerous specialized modules (e.g., `planet_strength.py`, `ashtakavarga.py`, `transits.py`, `divisional_charts.py`, `remedies.py`, `kp_cuspal_sub_lord.py`, `jaimini.py`, `chara_dasha.py`, `dosh_deep.py`, `dasha_extras.py`, `varga_deep.py`, `ashtaka_deep.py`, `transit_deep.py`, `kp_deep.py`, `special_lagnas.py`, `sahams_extended.py`, `nadi.py`, `lal_kitab_full.py`, `compat.py`, `muhurta.py`, `panchang.py`, `numerology.py`, `astro_vastu_engine.py`, `medical_engine.py`, `modern_context_engine.py`, `financial_engine.py`, `remedies_deep_engine.py`, `astrocartography_engine.py`, `timing_engine.py`).
    - **LOCKED FACTS Protocol**: A central `locked_facts.py` aggregates deterministic data from all engines into a structured block. This block serves as the single source of truth for AI responses.
    - **AI Orchestration**: `openai_helper.py` injects `locked_facts_str` into user messages and applies strict "mirror rules" (A-W) to ensure AI quotes verbatim from the factual block, preventing hallucination.
    - **Deterministic Post-Injectors**: A critical safety layer in `ai_ask()` that automatically appends engine-generated sentences if the AI fails to cite mandatory facts for specific topics, especially timing, marriage, career, finance, and children.
    - **AI Brain Phase**: Future `ai_brain/` directory will house advanced AI components like `system_prompts`, `few_shot_examples`, `decision_trees`, `question_router`, `answer_schemas`, `verification` (fact/brand-voice/hallucination checkers), `post_injectors`, `memory`, `training_data`, `prompts`, `config`, and `orchestrator.py`.
    - **RAG (Retrieval-Augmented Generation)**: Designed with `chunker.py`, `embedder.py`, `retriever.py`, and `ingest.py` to provide the AI with classical Vedic knowledge from a `knowledge_chunks` table (PostgreSQL `pgvector`). This RAG system is explicitly bypassed for timing-related questions to prevent hallucination.
    - **Life Mastery Report**: A comprehensive 17-tier PDF generation system that combines numerology and Vedic astrology, wrapped with numerology framing. Each tier is backed by dedicated modules (e.g., `numerology/core_ext.py`, `numerology/vedic_classical.py`, `numerology/remedies.py`, `numerology/audits.py`, `numerology/relationships.py`, `numerology/wealth.py`, `numerology/career.py`, `numerology/health.py`, `numerology/family.py`, `numerology/transits.py`, `numerology/spirituality.py`, `numerology/marriage.py`, `numerology/progeny.py`, `numerology/property.py`, `numerology/foreign.py`, `numerology/longevity.py`, `numerology/moksha.py`).

## External Dependencies

- **Database**: SQLite (`users.db`) for user authentication. PostgreSQL with `pgvector` extension for knowledge base (RAG).
- **Astrology Engine**: `pyswisseph` (Swiss Ephemeris) for precise planetary calculations.
- **AI/NLP**: OpenAI API (GPT models for narration and interpretation).
- **PDF Generation**: `reportlab` (Python library for PDF creation).
- **Mobile Development**: Expo (React Native framework).
- **Authentication/Notifications**: Firebase (planned for push notifications).
- **Payment Gateway**: Cashfree (planned for subscriptions).
- **SMS Gateway**: MSG91 (planned for OTP verification).
- **Image Processing**: Pillow (Python Imaging Library) for floor plan rotation.