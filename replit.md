# Cosmic Lens — Workspace

## Overview

Cosmic Lens is a pnpm workspace monorepo using TypeScript for a mobile Vedic Astrology application. It aims to provide accurate astrological analysis, including kundli calculations, numerology, Vastu, and AI-driven interpretations. The project's vision is to achieve over 97% accuracy through a robust calculation engine, a sophisticated AI, and continuous learning, ultimately creating a comprehensive astrological and numerological life mastery system.

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

The project is a pnpm workspace monorepo using Node.js 24 and TypeScript 5.9.

**Mobile App (Expo React Native):**
- **UI/UX**: Full-screen nebula background, card glow effects, glassmorphism, zodiac-based accent theming, and dark/light mode with bottom tab navigation.
- **Features**: Daily Rashifal, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, personalized forecasts ("Risk Radar"), and a Life Mastery Report.
- **Localization**: Supports 25 languages with region detection and a two-layer architecture for UI and Vedic content.

**Backend (Python Flask):**
- **Architecture**: Modular engines for Vedic astrological calculations (e.g., `planet_strength.py`, `ashtakavarga.py`).
- **CLE (Cosmic Lens Engine) Format**: Every new domain engine must include D9 Navamsa cross-check, a domain-specific D-chart, KP cuspal sub-lord, Jaimini karaka mapping, a 3-bucket tense detector, and brand-safety guards.
- **LOCKED FACTS Protocol**: `locked_facts.py` centralizes deterministic data for AI responses.
- **AI Orchestration**: `openai_helper.py` injects facts, enforces verbatim citation, and includes deterministic post-injectors for safety.
- **RAG (Retrieval-Augmented Generation)**: Uses `pgvector` for classical Vedic knowledge, bypassed for timing questions.
- **Engine-Aware Anti-Hallucination Pipeline**: Ensures timing answers are correctly sourced from engines, with a smart timing-validator that softens when engine data is unavailable.
- **Supertype Narrator Contract**: Classifies answers into 5 supertypes (PLANET_QUERY, PROBLEM_QUERY, TIMING_QUERY, DECISION_QUERY, GENERAL_ANALYSIS) with strict per-type response rules.
- **Question-Intent Classifier**: A deterministic function (`_classify_ask_intent`) identifies 13 intent categories, providing a canonical source of truth for routing.
- **AI-ONLY Question Understanding**: Replaced multi-layer understanding with a single LLM classifier call for intent, topic, and confidence.
- **Emotional Treatment Playbook**: A cross-engine module defining a `(emotional_tone × domain) → directive` matrix for nuanced AI responses.
- **Structured-Output Mode**: For specific engines (e.g., wealth), forces strict JSON output with defined schemas, disclaimers, and an "EMPATHY SANDWICH" narrative pattern.
- **Health Engine**: Deterministic Vedic + KP health/illness engine with 25 layers, 12 question buckets, and critical brand-safety guards including medical disclaimers and helpline information.
- **Wealth / Finance Engine**: Deterministic Vedic + KP wealth/finance engine with 25 layers, 12 question buckets, and critical brand-safety guards including financial disclaimers and advisor recommendations.
- **Stock Market Engine**: Deterministic Vedic-rule-based stock/trading/investment guidance with 17 core natal layers and a 10-category question classifier, enforcing anti-speculation policies.
- **Love vs. Arrange Engine**: Pure-Python deterministic scorer using classical Vedic rules for love vs. arrange marriage verdicts, with confidence-ratio-based public verdicts.
- **Yoga Registry**: Wires existing yoga detectors (Dhana, Raj, Vipareeta, etc.) into the minimal-prompt path, providing structured yoga facts.
- **Dosh Engine**: Wires `dosh_engine.analyze_doshas()` into the minimal-prompt path, presenting structured `DOSH_FACTS`.
- **Health Pipeline Orchestration**: Uses `health_topic_matcher.py`, `health_recipe_composer.py`, and `health_rules.py` to derive structured `phase76_findings` for health questions based on 132 topics and 34 rules.
- **LLM Full Chart Mode** (`LLM_FULL_CHART_MODE`, default ON since 30 Apr 2026): Env-gated passthrough that hands the LLM a comprehensive Hinglish chart-context block built by `kundli_full_context.build_full_chart_context`. Sections: 1.Birth/Lagna, 2.Grahas (with dignities), 3.Bhavas, 4.Current Dasha, 5.Upcoming Vimshottari (remaining antardashas + next 5 mahadashas), 6.Navamsha D9 (with vargottama detection), 7.Yogas/Doshas/Sade-Sati/Gochar (sourced from `chart_intelligence.analyze_chart`), 8.Niyam (anti-hallucination + Hinglish rails). The passthrough call lives in `openai_helper.ai_ask` and uses Replit AI Integrations' OpenAI proxy (`AI_INTEGRATIONS_OPENAI_*` env vars) with model from `OPENAI_MODEL` (default `gpt-5.4`). For gpt-5 / o-series models the `temperature` parameter is conditionally dropped (those models reject it).
- **Phase 1 Prompt Polish** (30 Apr 2026): The passthrough `_sys_intro_pt` system prompt (in `openai_helper.py`, applied to BOTH streaming L1957+ and non-streaming L13007+ paths) was upgraded from a 4-line minimal intro to an 8-rule output style guide. Rules: (1) TL;DR-first 1-line answer, (2) 3-4 bullet length cap, (3) question-relevant house/planet focus filter with quick-reference table for Health/Career/Marriage/Wealth/General, (4) reuse last 6 conversation turns instead of repeating facts, (5) ban generic Sun-sign/rashi-falit phrasing ("Mithun rashi ke hisaab se" → forbidden) — always personalize as "aapki kundli ke context mein" / "aapke Lagna se", (6) rotate CTA wraps instead of repeating "Agar chaho to...", (7) cite D9 navamsha placement for marriage/long-term-health/career/spiritual questions and call out vargottama planets, (8) anti-hallucination — only classical Vedic relationships (dignity, drishti, listed yogas, dasha, nakshatra) are permitted. Applied to both streaming and non-streaming passthrough. Smoke-test confirmed: TL;DR present, ~187 words / 11 lines (vs previous wall-of-text), no generic-rashi phrasing, no "Agar chaho to..." CTA, ~8s latency (down from ~30s).

## External Dependencies

- **Database**: SQLite for user authentication; PostgreSQL with `pgvector` for the knowledge base.
- **Astrology Engine**: `pyswisseph` (Swiss Ephemeris).
- **AI/NLP**: OpenAI API (GPT models).
- **PDF Generation**: `reportlab`.
- **Mobile Development**: Expo (React Native).
- **Image Processing**: Pillow.
- **Ask Pipeline V2**: AI Ear for multi-intent extraction, `ai_ask_v2` dispatcher for fan-out, and AI Mouth for conversational narration.