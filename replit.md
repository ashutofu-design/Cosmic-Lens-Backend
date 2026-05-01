# Cosmic Lens — Workspace

## Overview

Cosmic Lens is a pnpm workspace monorepo for a mobile Vedic Astrology application, aiming for over 97% accuracy in astrological analysis. It includes features like kundli calculations, numerology, Vastu, and AI-driven interpretations. The project's vision is to create a comprehensive astrological and numerological life mastery system.

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
- **Architecture**: Modular engines for Vedic astrological calculations, adhering to a "CLE (Cosmic Lens Engine) Format" that includes D9 Navamsa cross-check, domain-specific D-chart, KP cuspal sub-lord, Jaimini karaka mapping, a 3-bucket tense detector, and brand-safety guards.
- **LOCKED FACTS Protocol**: `locked_facts.py` centralizes deterministic data for AI responses.
- **AI Orchestration**: `openai_helper.py` manages fact injection, verbatim citation, and deterministic post-injectors for safety.
- **RAG (Retrieval-Augmented Generation)**: Uses `pgvector` for classical Vedic knowledge, bypassed for timing questions.
- **Anti-Hallucination Pipeline**: Engine-aware, ensuring timing answers are sourced from engines with a smart timing-validator.
- **Supertype Narrator Contract**: Classifies answers into 5 supertypes (PLANET_QUERY, PROBLEM_QUERY, TIMING_QUERY, DECISION_QUERY, GENERAL_ANALYSIS) with strict response rules.
- **Question-Intent Classifier**: Deterministic function (`_classify_ask_intent`) identifies 13 intent categories for routing.
- **AI-ONLY Question Understanding**: Single LLM classifier call for intent, topic, and confidence.
- **Emotional Treatment Playbook**: Cross-engine module defining a `(emotional_tone × domain) → directive` matrix.
- **Structured-Output Mode**: For specific engines (e.g., wealth), forces strict JSON output with schemas, disclaimers, and "EMPATHY SANDWICH" narrative.
- **Specialized Engines**: Includes deterministic Vedic + KP engines for Health, Wealth/Finance, Stock Market, and Love vs. Arrange Marriage, each with specific layers, question buckets, and brand-safety guards.
- **Yoga and Dosh Registry**: Wires existing detectors for structured facts.
- **Health Pipeline Orchestration**: Uses `health_topic_matcher.py`, `health_recipe_composer.py`, and `health_rules.py` for structured health findings.
- **LLM Full Chart Mode**: Provides a comprehensive Hinglish chart-context block (`kundli_full_context.build_full_chart_context`) to the LLM, including birth details, grahas, bhavas, dashas, D9, yogas/doshas/sade-sati/gochar, and anti-hallucination rules. This full context now includes Arudha, Ashtakavarga, Shadbala, and Argala data.
- **Deep-Chart Framework (Rule 18)**: Implements a 7-layer classical BPHS framework (Karaka, Bhava, Bhavesh, Karaka-se-Bhava, D9 Navamsha, Dosh check, Timing) for comprehensive analysis, blending layers into concise bullets.
- **Topic-Lock Focus**: Enhanced prompt-level rules (17 BPHS-aligned topics with bhava+karaka mapping) and a topic-detector that prepends a `TOPIC-LOCK` block to the user message for strict focus.
- **Anti-AI-Feel Measures**: Prompt rules (Guru-tone, Lagna-aware personalization, No-hedging, No-AI-tells) and a defensive post-processor (`_scrub_ai_tells`) to remove AI-specific phrasing and ensure a "highly trained Vedic guru" persona.
- **Persona + Source Attribution**: Establishes "Cosmo" as the persona, explicitly forbids "AI" terminology, and provides natural attribution for information sources ("Aapki kundli mere paas hai").
- **Length-Match Fix**: Adapts answer length to question complexity (1-line for single-fact queries, TL;DR + bullets for detailed questions).
- **2-Mode Output System**: A binary mode-switch driven by `_is_transparency_query(question)`. Mode 1 (Quick Answer) provides concise bulleted responses without jargon. Mode 2 (Explain Mode) provides step-by-step explanations with chart-tech, triggered by intent-based questions.
- **Marriage Engine (Love or Arrange)**: Implemented as a package with sub-engines for timing and classification. The `love_or_arrange.py` sub-engine uses 3 independent astrological engines (Parashari D1, D9 Navamsha, KP CSL) and 6 trust layers (Self-disclosure NLP, Multi-engine consensus, 5-band confidence calibration, Sannyasi Yoga Detector, Multi-Marriage Detector, Era Adjustment) for nuanced marriage predictions and explanations.
- **Phase 2.8.27 — Passthrough Marriage Wiring (01 May 2026)**: Production logs revealed that all 3 LLM_FULL_CHART_MODE passthrough sites in `openai_helper.py` (legacy at L3619, sync ai_ask at L14642, stream ai_ask_stream at L17861) were bypassing `marriage_engine` entirely — they sent raw `chart_block + topic_lock + question` to the LLM, which then GUESSED love/arrange instead of running the deterministic 25-rule + 6-trust-layer classifier. Fix: added `_passthrough_marriage_block(question, kundli, intel, birth)` helper that mirrors the legacy ai_ask block (assess_marriage → format_verdict_for_prompt → Jaimini UL inject) and is now appended to the system message at all 3 passthrough sites. Helper uses a dedicated marriage-keyword regex (NOT `_detect_topic`) because the latter's ambiguity gate returns None when both `love` and `marriage` topic rules fire (e.g. "love marriage ya arrange") — but love-vs-arrange classification is exactly what marriage_engine's job is. Verified: marriage Q on real kundli now injects 1582-char LOCKED FACTS block with verdict (MIXED/LOVE/ARRANGED + confidence + supporting factors) into the LLM system prompt; non-marriage Q and empty-kundli cases correctly return empty (safe fallback).

## External Dependencies

- **Database**: SQLite (user authentication), PostgreSQL with `pgvector` (knowledge base).
- **Astrology Engine**: `pyswisseph` (Swiss Ephemeris).
- **AI/NLP**: OpenAI API (GPT models).
- **PDF Generation**: `reportlab`.
- **Mobile Development**: Expo (React Native).
- **Image Processing**: Pillow.
- **Ask Pipeline V2**: AI Ear, `ai_ask_v2` dispatcher, AI Mouth.