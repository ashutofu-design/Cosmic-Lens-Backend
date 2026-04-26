# Cosmic Lens — Workspace

## Overview

Cosmic Lens is a pnpm workspace monorepo utilizing TypeScript for a mobile Vedic Astrology application. The project aims to deliver accurate and comprehensive astrological analysis, providing modern-context reframing and actionable insights. Key features include in-depth kundli calculations, numerology, Vastu analysis, and AI-driven astrological interpretations. The long-term goal is to achieve over 97% accuracy through a robust calculation engine, a sophisticated AI brain, and continuous learning.

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
- **Artifact**: `artifacts/cosmic-lens-mobile`
- **Navigation**: Bottom tabs for Home, Kundli, AI Chat, Insights, Notifications, Profile.
- **Features**: Daily Rashifal, Lucky elements, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, Forecast.
- **UI/UX**: `CosmicBg.tsx` for full-screen nebula background; `ThemeContext.cardShadow` for card glow; glassmorphism effect; zodiac-based accent theming; dark/light theme support.
- **Localization**: i18n support for 25 languages (12 Indian, 13 global) with region detection. Two-layer architecture for UI and Vedic content. Strict no-leakage rule between languages. Full UI and Vedic vocabulary localization complete, including RTL support for Arabic.
- **Risk Radar**: Integrated into the Forecast page as a comprehensive card, providing next-24-hours signals and 7-day outlook. Features a Vedic-themed UI with Sri Yantra Shatkona, 27 Nakshatra rim dots, Devanagari house markers, and an ॐ-centric center hub.

**Backend (Python Flask):**
- **Artifact**: `artifacts/api-server`
- **Core Components**: `flask_app.py`, `kundli_engine.py`, `kp_engine.py`, `ask_engine.py`, `requirements.txt`.
- **Architecture**:
    - **Modular Engines**: Vedic astrological calculations are organized into numerous specialized Python modules (e.g., `planet_strength.py`, `ashtakavarga.py`, `transits.py`, `divisional_charts.py`, `remedies.py`, `kp_cuspal_sub_lord.py`, `jaimini.py`, `chara_dasha.py`, `dosh_deep.py`, `dasha_extras.py`, `varga_deep.py`, `ashtaka_deep.py`, `transit_deep.py`, `kp_deep.py`, `special_lagnas.py`, `sahams_extended.py`, `nadi.py`, `lal_kitab_full.py`, `compat.py`, `muhurta.py`, `panchang.py`, `numerology.py`, `astro_vastu_engine.py`, `medical_engine.py`, `modern_context_engine.py`, `financial_engine.py`, `remedies_deep_engine.py`, `astrocartography_engine.py`, `timing_engine.py`).
    - **LOCKED FACTS Protocol**: `locked_facts.py` centralizes deterministic data from all engines for AI responses.
    - **AI Orchestration**: `openai_helper.py` injects `locked_facts_str` and applies "mirror rules" for verbatim citation.
    - **Deterministic Post-Injectors**: A safety layer in `ai_ask()` that ensures mandatory facts are cited.
    - **AI Brain Phase**: Future `ai_brain/` will house advanced AI components for system prompts, decision trees, RAG, and verification.
    - **RAG (Retrieval-Augmented Generation)**: Uses `chunker.py`, `embedder.py`, `retriever.py`, and `ingest.py` for classical Vedic knowledge from PostgreSQL `pgvector`, explicitly bypassed for timing questions.
    - **Life Mastery Report**: A comprehensive 17-tier PDF generation system combining numerology and Vedic astrology.
    - **Daily Energy Score**: A sophisticated system (`energy_engine.py`) that calculates a daily energy score based on transit-to-natal aspects, Jupiter & Mars house overlays, Choghadiya/Hora time-of-day, Tithi, and active Pratyantar-dasha lord transits. It includes a hard cap for Sade Sati Madhya, Mahadasha Sandhi detection, and active PD lord retrograde advisories. Scoring is based primarily on Moon-driven factors (75%) with Dasha providing a 25% backdrop. The system incorporates realistic scoring with lower bases and a compression curve for higher scores, seasonal sunrise/sunset calculations, degree-based aspects with orbs, and a Lagna + Chandra-lagna weighted blend for house calculations.
    - **Dosha Analysis**: `dosh_engine.py` expanded to 15 classical doshas including strict-classical rewrites for Putra Dosh, Pitru Dosh, Shrapit Yog, Daridra Yog, Guru Chandal, and Kaal Sarp Dosh (with 12 variants). Chandra-Mangal Dosh has been removed as a standalone entry. Kemadruma cancellation rules are strictly applied.

## External Dependencies

- **Database**: SQLite (`users.db`) for user authentication; PostgreSQL with `pgvector` for knowledge base.
- **Astrology Engine**: `pyswisseph` (Swiss Ephemeris).
- **AI/NLP**: OpenAI API (GPT models).
- **PDF Generation**: `reportlab`.
- **Mobile Development**: Expo (React Native).
- **Authentication/Notifications**: Firebase (planned).
- **Payment Gateway**: Cashfree (planned).
- **SMS Gateway**: MSG91 (planned).
- **Image Processing**: Pillow.