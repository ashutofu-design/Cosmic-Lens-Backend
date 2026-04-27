# Cosmic Lens — Workspace

## Overview

Cosmic Lens is a pnpm workspace monorepo utilizing TypeScript for a mobile Vedic Astrology application. The project aims to deliver accurate and comprehensive astrological analysis, providing modern-context reframing and actionable insights. Key features include in-depth kundli calculations, numerology, Vastu analysis, and AI-driven astrological interpretations. The long-term goal is to achieve over 97% accuracy through a robust calculation engine, a sophisticated AI brain, and continuous learning, ultimately providing a comprehensive astrological and numerological life mastery system.

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
- **UI/UX**: Features a full-screen nebula background, card glow effects, glassmorphism, zodiac-based accent theming, and dark/light mode. Navigation is via bottom tabs.
- **Features**: Includes daily Rashifal, Panchang, Kundli Milan, Muhurat finder, Numerology, Remedies, Vastu tips, Dosha analysis, and personalized forecasts with a "Risk Radar."
- **Localization**: Supports 25 languages (12 Indian, 13 global) with region detection and a two-layer architecture for UI and Vedic content, ensuring no language leakage.

**Backend (Python Flask):**
- **Architecture**: Modular engines for Vedic astrological calculations (`planet_strength.py`, `ashtakavarga.py`, etc.).
- **LOCKED FACTS Protocol**: `locked_facts.py` centralizes deterministic data for AI responses.
- **AI Orchestration**: `openai_helper.py` injects facts and enforces verbatim citation.
- **Deterministic Post-Injectors**: A safety layer in `ai_ask()` to ensure mandatory fact citation.
- **RAG (Retrieval-Augmented Generation)**: Uses `pgvector` for classical Vedic knowledge, explicitly bypassed for timing questions.
- **Life Mastery Report**: A 17-tier PDF generation system combining numerology and Vedic astrology.
- **Daily Energy Score**: Calculates a daily energy score based on transit-to-natal aspects, planetary overlays, Choghadiya/Hora, Tithi, and Dasha lord transits, with specific scoring methodologies and advisories.
- **Dosha Analysis**: Expands to 15 classical doshas, including strict-classical rewrites and cancellation rules.
- **Daily Lucky Engine**: Provides personalized "Aaj Ka Shubh Ank" and "Aaj Ka Shubh Rang" based on birth data and daily planetary positions.
- **Cosmic Intelligence Text Layer**: AI-generated friendly Hinglish text for Risk Radar guidance, adhering to strict brand voice guidelines, with severity-banded and per-day variants, and an anchor remedy for the week.
- **Risk Text Engine**: Replaces hardcoded templates with dynamic engine output for 7-day forecasts, including dominant trigger detection, Choghadiya schedules, and best/avoid times.
- **Stock Market Engine** (`stock_engine.py`): Deterministic Vedic-rule-based stock/trading/investment guidance engine that mirrors `marriage_engine.py`'s lock-output pattern. Composed of 17 core natal-promise layers (e.g. 2nd/5th/9th/11th house lords, Jupiter/Mercury/Venus dignity, Yogakaraka, Lakshmi/Dhana/Raj yogas) + 7 modifiers (debilitation, combustion, retrograde, malefic aspects, dasha-lord harmony, transit Saturn/Jupiter, KP sub-lord) + 2 conditionals (Rahu/Ketu speculation lift, 6th-house competition lift) + a 10-category question classifier (suitability, intraday, strategy, sector, instrument_risk, timing, loss_recovery, sl_target, broker_choice, learning) + the 2-step Promise/Trigger framework + weighted scoring. The framework score and the question-type bucket together resolve to a canonical verdict (`go_now` / `wait` / `limited` / `avoid`) with score-clamps that prevent contradictions between the bucket and the score band. AI is reduced to a NARRATOR — `openai_helper.py` injects the locked verdict, score, dasha context, timing window, and remedy as the LAST system message before the user turn (recency-bias lock). Brand voice is preserved: "Powered by Advanced Cosmic Intelligence" — AI/LLM is never revealed; no fake or random fallbacks. Trigger gate is a tightened regex over share/stock/equity/fund/derivative/crypto/SIP vocabulary — bare `bazar` / `vyapaar` are excluded to avoid false-firing on generic business questions. The pre-existing route-level brand-guard (anti-speculation policy that blocks `nifty/stock/sensex` + `buy/sell/target/tomorrow` patterns) intentionally takes precedence and intercepts pure tip-style queries before they reach the engine.

## External Dependencies

- **Database**: SQLite for user authentication; PostgreSQL with `pgvector` for the knowledge base.
- **Astrology Engine**: `pyswisseph` (Swiss Ephemeris).
- **AI/NLP**: OpenAI API (GPT models).
- **PDF Generation**: `reportlab`.
- **Mobile Development**: Expo (React Native).
- **Image Processing**: Pillow.