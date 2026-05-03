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
- **LLM Full Chart Mode**: Provides a comprehensive Hinglish chart-context block (`kundli_full_context.build_full_chart_context`) to the LLM, including birth details, grahas, bhavas, dashas, D9, yogas/doshas/sade-sati/gochar, Arudha, Ashtakavarga, Shadbala, and Argala data, with anti-hallucination rules.
- **Deep-Chart Framework (Rule 18)**: Implements a 7-layer classical BPHS framework (Karaka, Bhava, Bhavesh, Karaka-se-Bhava, D9 Navamsha, Dosh check, Timing) for comprehensive analysis, blending layers into concise bullets.
- **Topic-Lock Focus**: Enhanced prompt-level rules (17 BPHS-aligned topics with bhava+karaka mapping) and a topic-detector that prepends a `TOPIC-LOCK` block to the user message for strict focus.
- **Anti-AI-Feel Measures**: Prompt rules (Guru-tone, Lagna-aware personalization, No-hedging, No-AI-tells) and a defensive post-processor (`_scrub_ai_tells`) to remove AI-specific phrasing and ensure a "highly trained Vedic guru" persona.
- **Persona + Source Attribution**: Establishes "Cosmo" as the persona, explicitly forbids "AI" terminology, and provides natural attribution for information sources ("Aapki kundli mere paas hai").
- **Length-Match Fix**: Adapts answer length to question complexity (1-line for single-fact queries, TL;DR + bullets for detailed questions).
- **2-Mode Output System**: A binary mode-switch driven by `_is_transparency_query(question)`. Mode 1 (Quick Answer) provides concise bulleted responses without jargon. Mode 2 (Explain Mode) provides step-by-step explanations with chart-tech, triggered by intent-based questions.
- **Marriage Engine (Love or Arrange)**: Implemented as a package with sub-engines for timing and classification. The `love_or_arrange.py` sub-engine uses 3 independent astrological engines (Parashari D1, D9 Navamsha, KP CSL) and 6 trust layers for nuanced marriage predictions and explanations.
- **Marriage Timing Engine (VIVAH-7 Protocol)**: Rewritten KP-first 7-step pipeline (replacing previous 5-layer Parashari-first). Includes Late/Early Tendency, KP Filter (first gate), D1+D9 Cross-Validation, Redemption, Dasha + Confluence with VIVAH-7 weights (Mars trigger, Jupiter/Saturn aspects, Sandhi, Retrograde, Eclipse), and Reality Filter (age table).
- **Career Engine**: Includes KP bucket-tuned conditionals and systematic bucket verification.
- **Smart Query Understanding (SQU)**: Extends `question_understanding.py` with `subtopic`, `needs_engine`, `emotion`, `urgency`, `cleaned_q`, `final_topic_lock`, and `clarification_text` fields for improved LLM interaction.
- **System Prompt**: Uses a "Guided Freedom" approach with an 80% mindset prompt and 20% surgical guards, greatly reducing prompt size while preserving core directives.
- **Package Consolidation**: `ask_cosmo/` for question understanding, `reply_cosmo/` for response shaping (includes `engine_locked_to_llm/` for chart-truth source).

## External Dependencies

- **Database**: SQLite (user authentication), PostgreSQL with `pgvector` (knowledge base).
- **Astrology Engine**: `pyswisseph` (Swiss Ephemeris).
- **AI/NLP**: OpenAI API (GPT models).
- **PDF Generation**: `reportlab`.
- **Mobile Development**: Expo (React Native).
- **Image Processing**: Pillow.
- **Ask Pipeline V2**: AI Ear, `ai_ask_v2` dispatcher, AI Mouth.

## Recent Changes

- **Phase 2.8.63 (May 3 2026) — VIVAH-7 STEP 1 KP filter unified**: Method A (chain-union with Promise={2,7,11}, Deny={6,8,12}) removed entirely from `event_timing/marriage/marriage_timing.py`. Method B (strict sub-lord with Promise={2,7,11}, Deny={1,6,8,10,12}) is now the SOLE KP marriage filter per user lock-in. Deleted helpers: `_KP_PROMISE_HOUSES`, `_KP_DENY_HOUSES`, `_get_kp_significators`, `_planet_kp_significations`, `_kp_planet_verdict`, `_kp_csl_verdict`. STEP 1 invocation rewritten to use `_kp_sublord_filter_planet` for both 7CSL (primary, FINAL ARBITER) and 7C Star Lord (cross-check). Verdict mapping: STRONG→PROMISED, WEAK→DENIED, MIXED→MIXED. Verified on profile 40 (rajalaxmi): 7CSL Sun SB=Sun basic=[9,11] promise=[11] deny=[] → PROMISED; 7C StarLord Mars SB=Saturn basic=[2,3] promise=[2] deny=[] → PROMISED; STEP 1 KP GATE = PROMISED. No external callers existed for the removed helpers.

- **Phase 2.8.64 (May 3 2026) — VIVAH-7 STEP 2 D1+D9 link filter (ADD-ONLY)**: Added `compute_step2_link_filter(kundli, kp)` in `event_timing/marriage/marriage_timing.py` (Section 2c, L516+). Takes STEP 1 per-planet verdicts (STRONG/MIXED/WEAK) and re-classifies each of the 9 planets by link strength to 7H + 7L in BOTH D1 and D9 (occupation, conjunction, aspect, parivartana — Rahu/Ketu skip parivartana). Link strength: BOTH > D1 > D9 > NONE. 12-cell verdict×strength matrix yields STRONGEST_PROMISE / CONFIRMED_PROMISE / PASSIVE_PROMISE / STRONG_CONDITIONAL / CONDITIONAL / NEUTRAL / STRONGEST_DENIAL / ACTIVE_DENIAL / PASSIVE_DENIAL. Final 4 buckets: approvers / conditional / deniers / ignore. New helpers: `_planet_owned_signs`, `_aspects_target` (universal 7th + Mars 4/7/8 + Jupiter 5/7/9 + Saturn 3/7/10), `_planet_link_in_chart`, `_d1_planet_state`, `_d9_planet_state`. D9 read from `kundli['divisionalCharts']['D9']` (planets+ascendantSignIndex) — NOT from `_get_d9_chart` which lacks lagna. Verified on profile 40: approvers=[Sun,Mars,Rahu,Ketu], conditional=[Moon,Saturn], deniers=[Jupiter,Venus], ignore=[Mercury].

- **Phase 2.8.67 (May 3 2026) — KP CONFIDENCE GATE WRAPPER (ADD-ONLY)**: Added `compute_kp_gate_decision(kp, birth_time_confidence)` in `event_timing/marriage/marriage_timing.py` (Section 2b, L516+). Wraps `compute_kp_sublord_marriage_filter` with birth-time-confidence awareness. Default behavior (`confident`) is IDENTICAL to before — DENIED still hard-gates. New behavior only when caller explicitly passes `birth_time_confidence="uncertain"`: DENIED → DENIED_LOW_CONFIDENCE with `gate_action=PROCEED_LOW_CONF`, `allow_timing_scan=True`, and a mandatory disclaimer for the LLM narration. PROMISED path is unchanged regardless of confidence flag. Decision matrix: PROMISED→PROCEED, DELAYED+confident→PROCEED, DELAYED+uncertain→PROCEED_LOW_CONF, DENIED+confident→HARD_STOP, DENIED+uncertain→PROCEED_LOW_CONF, UNKNOWN→PROCEED_LOW_CONF. New helpers: `_normalize_birth_time_confidence` (accepts confident/uncertain/exact/approx/low/known/yes/no/true/false/0/1/bool/None), `extract_birth_time_confidence(birth_data)` (reads `birth_time_confidence` | `btc` | `time_confidence` | `tob_confidence` | `birthTimeConfidence` keys, defaults to `confident`), and `apply_birth_time_confidence_to_verdict(verdict, btc)` — a lightweight wiring helper for callers that already hold a KP verdict from the live STEP-1 path (7CSL + StarLord truth-table) and only need the confidence overlay without re-running the full 9-planet sub-lord filter. Constants `_BTC_CONFIDENT`, `_BTC_UNCERTAIN`, `_BTC_VALID`. Architect review fixes applied: (a) non-dict KP now returns PROCEED_LOW_CONF (matches matrix instead of HARD_STOP), (b) string normalizer extended with no/false/0/yes/true/1, (c) `apply_birth_time_confidence_to_verdict` added so callers can preserve existing 7CSL gate semantics. No call sites updated yet — wrappers available for future wiring; existing `compute_kp_sublord_marriage_filter` callers remain unchanged. Verified on profile 40: PROMISED+any-confidence → PROCEED; non-dict KP → UNKNOWN → PROCEED_LOW_CONF; full verdict matrix tested for both helpers.
- **Phase 2.8.68 (May 3 2026) — STEP 0 LATE/EARLY refinement (3 fixes)**: External review of `_step0_late_early_tendency` validated by Cosmo: 3/6 reviewer claims confirmed, 1 partial, 2 invalid. Applied fixes in `event_timing/marriage/marriage_timing.py` (L1839-1932). **FIX A — Saturn de-duplication**: previously L1 (Saturn aspect/conj 7H) AND L11 (Saturn IN 7H) both fired when Saturn occupied 7H, giving silent +2 via two +1 lines. Now `sat_in_7h` (house==7 OR sign_index==h7_si) takes the strongest reading via L11=+2 and explicitly skips L1; aspect-only path still gives +1 via L1. **FIX B — Venus debilitation**: previously L3 used elif chain (combust XOR dusthana), debilitated Venus added 0 LATE points. Now combust + dusthana + debilitated each contribute +1 independently, total Venus weakness capped at +2 to prevent triple-affliction over-bias. New reason line `L3: Venus debilitated (+1 LATE) [NEW 2.8.68]`. **FIX C — 7L retrograde**: previously E6 retro path was neutral skip. Now retro 7L adds +1 LATE via new tag `L4` independently of house placement (classical Vedic delay signal); kendra/trikona EARLY still requires non-retro. New helper hoisted: `seventh_lord_retro` computed once at top of function. **REJECTED** reviewer claims: G2 oversimplification (code already checks dusthana+debilitated as suggested), generic strength weighting (deferred to Phase 2.8.65 STEP 2 strength layer), E5 cardinal/dual generic (low-impact, weight already +1). Verified via 5 synthetic unit tests on Profile 40 chart shape: T1 baseline LATE score=3 unchanged, T2 Saturn-in-7H scores +2 once (no double), T3 debilitated Venus adds +1, T4 retro 7L adds +1 via new L4 tag, T5 triple Venus affliction caps at +2 with cap reason logged. Bias correction: charts with Saturn in 7H now score 1 point lower (more accurate, less delay-bias); charts with debilitated Venus or retro 7L now score 1 point higher (closer to classical reading).
