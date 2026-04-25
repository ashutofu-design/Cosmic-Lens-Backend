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