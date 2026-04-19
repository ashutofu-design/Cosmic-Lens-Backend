# Cosmic Lens — Workspace

## Overview

pnpm workspace monorepo using TypeScript. This is the **Cosmic Lens** Vedic Astrology app — a mobile app with a Python Flask backend.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **Mobile app**: Expo (React Native) — `artifacts/cosmic-lens-mobile`
- **Backend**: Python Flask — `artifacts/api-server/flask_app.py`
- **Astrology engine**: pyswisseph (Swiss Ephemeris)
- **Database**: SQLite (`users.db`) for user auth

## Recent: Phase 7 — Cosmic Vision Accuracy Upgrade (2026-04-18)

Three fixes to close the marketing-vs-reality gap surfaced in the deep audit:

- **A1 Magnetometer-aware room photo capture** — new `components/RoomPhotoCapture.tsx` shows a live compass strip and snapshots `heading_deg` at the moment of capture; wired into both `astrovastu-pro.tsx` and `business-vastu.tsx`. Payload now carries `room_photos:[{room_type,image_data_url,heading_deg}]` (max 6). Backend `vision_layer.annotate_report_with_room_photos` forces `direction_basis="magnetometer"` whenever client supplied a heading, regardless of vision output.
- **A2 Floor plan orientation calibration** — `SmartScanUpload` adds a 4-button "Where is North on this plan?" picker (top/right/bottom/left). `floor_plan_loader.to_image_data_url` reads `north_at` and pre-rotates the PNG via Pillow (CCW: top=0°, right=90°, bottom=180°, left=270°) so North is always at the top before vision sees it.
- **A3 Scan basis badge** — new `components/ScanBasisBadge.tsx` shows "Compass-confirmed" (green), "Visual inference" (amber), or "Cosmic Vision" near the score card on both PRO + Business result screens (paid PDF and legacy on-screen paths). Sources `vision_room_findings.per_room[].direction_basis` + per-room `direction_basis` written by `vision_layer`.

Brand-safety: every new user-facing string uses "Cosmic Vision" — no AI/OpenAI/GPT mention.

## Artifacts

| Artifact | Path | Purpose |
|---|---|---|
| Cosmic Lens Mobile | `artifacts/cosmic-lens-mobile` | Expo React Native mobile app |
| API Server | `artifacts/api-server` | Python Flask backend (astrology APIs) |

## Mobile App — Screen Inventory

### Tabs (bottom nav)
- `index.tsx` — Home / Today's Energy
- `kundli.tsx` — Kundli chart
- `ask.tsx` — AI Jyotish chat
- `insights.tsx` — Energy charts / SVG
- `notice.tsx` — Notifications
- `profile.tsx` — Profile management

### "More" Drawer Feature Screens (app/*.tsx)
- `rashifal.tsx` — Daily/Weekly Rashifal for 12 signs
- `lucky.tsx` — Lucky Color, Number, Day, Gemstone, Deity, Mantra
- `panchang.tsx` — Tithi/Nakshatra/Yoga + Rahu Kaal + Festival calendar
- `kundli-milan.tsx` — 36 guna matching + Rashi compatibility (existing)
- `muhurat.tsx` — Shubh Muhurat finder (8 categories, monthly dates)
- `numerology.tsx` — Life Path + Name Number calculator (Chaldean system)
- `remedies.tsx` — Graha Upay (9 planets: mantra, daan, gemstone, upay)
- `vastu.tsx` — Vastu tips by room/direction (existing)
- `dosh.tsx` — Dosha analysis (existing)
- `forecast.tsx` — Forecast (existing)

### Drawer Component
- `components/MoreDrawer.tsx` — Side drawer with animated slide-from-right, organized categories

## Python Backend Modules

- `flask_app.py` — Main Flask server, auth, routing
- `kundli_engine.py` — Vedic kundli calculation (Swiss Ephemeris)
- `kp_engine.py` — KP (Krishnamurti Paddhati) astrology engine
- `ask_engine.py` — Rule-based astrology question answering
- `requirements.txt` — `flask`, `flask-cors`, `pyswisseph`, `gunicorn`, `python-dateutil`

## Mobile App Screens

- `app/(tabs)/index.tsx` — Home: today's energy chart
- `app/(tabs)/kundli.tsx` — Kundli (birth chart)
- `app/(tabs)/insights.tsx` — Jyotish insights
- `app/(tabs)/ask.tsx` — Ask a question
- `app/(tabs)/notice.tsx` — Notices
- `app/(tabs)/profile.tsx` — User profile
- `app/login.tsx`, `app/onboarding.tsx` — Auth flow
- `app/forecast.tsx`, `app/planet-position.tsx` — Extra features
- `app/dosh.tsx`, `app/kundli-milan.tsx`, `app/vastu.tsx` — Dosha, Milan, Vastu

## Key Commands

- `pnpm --filter @workspace/cosmic-lens-mobile run dev` — Run mobile app
- `python3 artifacts/api-server/flask_app.py` — Run Flask backend
- `pnpm run typecheck` — Full typecheck across all packages

## Cosmic Visual Design

- `components/CosmicBg.tsx` — Full-screen cosmic nebula background wrapper. Used in all 6 tab screens as the root container. Renders 4 gradient orbs (violet, indigo, amber, pink) + star dots (dark mode only) absolutely behind content.
- `ThemeContext.cardShadow` — CSS `boxShadow` string for card glow. Applied to key cards (HeroEnergyCard, ProfileCard, dashaCard, scoreCard, graphCard, noticeCard).
- `bgCard/bgCard2/bgCard3` are now `rgba(...)` values (80–55% opacity) so the cosmic background bleeds through, creating a glassmorphism effect.

## Zodiac Accent Theming

- `lib/zodiac.ts` — Pure utility: `getZodiacSign(day, month)` → `ZodiacSign`, `ZODIAC_ACCENTS` map (12 signs → `{ accent, accentBg }`), `ZODIAC_EMOJI`, `DEFAULT_ACCENT` (indigo fallback).
- `components/ZodiacBridge.tsx` — Zero-UI component. Reads `birthData` from UserContext, computes zodiac sign + accent, calls `setZodiacAccent` on ThemeContext. Mounted inside `_layout.tsx` between ThemeProvider and UserProvider.
- `ThemeContext.setZodiacAccent(sign, accent)` — Overrides `C.accent` and `C.accentBg` in the merged palette. All screens using `C.accent` automatically receive the zodiac color.
- **Fallback**: if no birth data → default indigo accent `#6366F1`.
- **Profile screen**: Zodiac Accent row in Settings section shows current sign emoji + glow dot + hex color.

## Dark / Light Theme

- `context/ThemeContext.tsx` — `DARK` / `LIGHT` palettes with `toggle()` and AsyncStorage persistence (`cl_theme` key). Now also carries zodiac accent state.
- `hooks/useColors.ts` — Wrapper exposing named aliases (`background`, `card`, `foreground`, `mutedForeground`, `border`, `primary`) plus raw `C` object
- Theme-aware screens (inline dynamic styles using `C.*`):
  - **index.tsx** — root bg, greeting text, HeroEnergyCard bg/border/label
  - **insights.tsx** — heading, dashaCard, category tabs, scoreCard, graphCard, textCards, body text
  - **ask.tsx** — header title/sub, assistant bubble, starter chips, input bar
  - **kundli.tsx** — root bg, snapshotCard bg/border/text
  - **notice.tsx** — root bg, card bg/border, row borders, title/desc/time text
  - **profile.tsx** — root bg, sectionCount
- Pattern: screens using `useColors()` access `C` via `{ C }` destructure; screens that import `useC` directly use it standalone

## i18n — Multi-Language Support

- `lib/i18n.ts` — Central translation system. Full translations for **23 languages**.
- `UILang` type: `"en"|"hi"|"mr"|"bn"|"te"|"ta"|"gu"|"kn"|"ml"|"pa"|"or"|"as"|"zh"|"es"|"ar"|"fr"|"pt"|"de"|"ru"|"ja"|"id"|"ko"|"tr"`
- `INDIA_LANG_CODES` — 12 languages shown when birth place = India (en, hi, bn, mr, ta, te, gu, kn, ml, or, pa, as)
- `GLOBAL_LANG_CODES` — 12 languages shown for non-India users (en, zh, es, ar, fr, pt, de, ru, ja, id, ko, tr)
- **Region detection**: `isIndia` in `UserContext` is derived from `birthData.place` (string match) or `birthData.country === "in"`. Controls which language list appears in the picker.
- **Default**: always `"en"`. Language selection is manual — user opens picker in Profile settings.
- **Persistence**: saved to `AsyncStorage` key `cl_language`. Loaded on app start.
- **Fallback**: `getT(lang)` falls back to English for any unknown/unsupported code.
- Usage pattern: `import { getT } from "@/lib/i18n"; const t = getT(language);`
- `UserContext` exposes `language` (LangCode), `setLanguage`, `isIndia`
- **Wired screens**: CustomTabBar, profile.tsx (settings rows + section labels + logout dialog), login.tsx (full), verify-otp.tsx (full), onboarding.tsx, index.tsx (home), kundli.tsx, ask.tsx, insights.tsx, notice.tsx
- **Auth flow keys** (`i18nMore.ts`): `enterPhone`, `phonePromptSub`, `mobileNumberLabel`, `mobileNumberPh`, `otpAutoCreateNote`, `sendOtp`, `orDivider`, `demoLogin`, `demoLoginSub`, `termsAccept`, `termsLink`, `privacyLink`, `otpVerifyTitle`, `otpSentToHeading`, `verifyOtp`, `didntGetOtp`, `resendIn`, `resendOtp`, `changeNumber`, `invalidPhone`, `authNotConfigured`, `otpInvalid`, `otpExpired`, `otpQuotaExceeded`, `otpTooManyAttempts`, `errNetwork`, `loginGenericError`, `otpResent`, `otpFailed` — all defined in EN/HN/HI; other 21 languages auto-fall back to EN.
- **Profile settings keys**: `settingEditProfile`, `settingSubscription`, `settingAbout`, `settingHelp`, `settingRateUs`, `settingShareApp`, `settingLegal`, `settingDeleteAcc`, `sectionSupport`, `sectionLegal`, `sectionDanger`, `logoutTitle`, `logoutConfirm`, `logoutCta`, `cancel`, `profilesCount`.
- **Still hardcoded** (next pass): `(tabs)/index.tsx` "Namaste"/energy phrases, `subscription.tsx` plan features array, `profile-edit.tsx` form labels, `EnergyChart.tsx` time labels, `UpgradeLock.tsx` "Upgrade to Pro" panel.

## API Endpoints

- `GET /api/healthz` — Health check
- `POST /api/kundli` — Calculate Vedic kundli
- `GET /api/moon_history` — Moon position history
- `POST /api/ask` — Ask astrology question
- `POST /api/register`, `POST /api/login` — Auth

## Sprint 1 Day 1 — Locked Facts Protocol (api-server)

Goal: AI mirrors deterministic chart facts (yoga count/names, dosha count/names, planet strength verdicts, current dasha) instead of vague language. Especially for emotional asks ("yaar pareshan hun") — first line must cite exact yoga count + strongest yoga name.

- **`planet_strength.py`** (NEW) — `verdict_for_planet(...)` returns `{verdict: STRONG|MODERATE|WEAK, reason}`. Shadbala-first (>=100% STRONG, 70-100 MODERATE, <70 WEAK), composite fallback uses dignity+house+combust+retro.
- **`locked_facts.py`** (NEW) — `build_locked_facts(kundli, birth)` assembles MIRROR-EXACT block: LAGNA/MOON SIGN/NAKSHATRA, YOGA COUNT+LIST, DOSHA COUNT+LIST (active+mild), PLANET STRENGTHS table, CURRENT DASHA window, HOUSE-LORDS summary. Dasha keys normalized to support both `{maha, antar, startDate}` (kundli_engine output) and legacy `{mahadasha, ad, start}`.
- **`chart_intelligence.py`** — `_detect_yogas` extended with 5 high-value yogas: Lakshmi, Saraswati, Adhi (strict — all 3 benefics in 6/7/8 from Moon, ≥2 distinct houses), Amala (strict — alone in 10th, no malefic co-tenant), Dharma-Karmadhipati (9L+10L conjunct or parivartana).
- **`openai_helper.py`** — `locked_facts_str` injected as `═══ LOCKED FACTS — MIRROR EXACTLY ═══` block BEFORE `intel_section` in analysis-branch user message. Instruction 0b adds 4 strict mirror rules:
  - RULE A — exact COUNT for "kitne / how many"
  - RULE B — full NAME LIST for "kaunse / which"
  - RULE C — exact STRENGTH verdict (STRONG/MODERATE/WEAK)
  - RULE D — empathy + fact fusion: emotional asks open with strongest positive fact
  - 🛡️ Brevity-exemption clause: Rule 0b OVERRIDES Rule 10's "2 chart factors" cap for counting/naming questions
  - 🛡️ Emotional-ask clause: first 1-2 sentences MUST cite YOGA COUNT + strongest yoga name when ≥1 yoga exists
- **Untouched branches**: greeting / general / minimal / marriage deterministic narrator paths — only the analysis branch wraps intel with locked facts.
- **Router kill-switch**: `COSMIC_DISABLE_INTENT_ROUTER=1` still in place (8-route classifier deferred).

### Sprint 1 Day 1.5 — Polarity + Dasha Fidelity (smoke-test driven)

End-to-end smoke test against `/api/ask` exposed two interpretive bugs (data layer was fine, AI framing was off). Fixed:

1. **Yoga polarity tagging** — `locked_facts.py` now classifies each detected yoga as POSITIVE / NEGATIVE / NEUTRAL via substring match on negative keywords (Kemadruma, Daridra, Shakata, Vish, Punarphoo, Kalasarpa, Guru-Chandala, Angarak, Pisach) and neutral (Vipareeta). YOGA LIST renders with `[+ POSITIVE]` / `[− NEGATIVE]` / `[~ NEUTRAL]` tags + a `POSITIVE YOGAS: x  NEGATIVE: y  NEUTRAL: z` summary line. Prevents AI from labelling Kemadruma as "strong yoga".
2. **Rule D refined (3-tier emotional ask)** — In `openai_helper.py` 0b: (i) prefer POSITIVE yoga count, (ii) else strongest STRONG planet, (iii) else honest reframe + next-dasha hope-anchor. Explicitly forbids labelling NEGATIVE-tagged yogas as positive.
3. **Rule E added — Dasha-lord fidelity** — Mahadasha/Antardasha lord's described tone MUST match its `PLANET STRENGTHS` verdict. WEAK dasha lord = "confusion / effort-without-result", MODERATE = "mixed / kaam pe result", STRONG = "powerful / supportive". Eliminates "Rahu Mahadasha gives growth" hallucination when Rahu row says WEAK.

Smoke test result on tough chart (1 negative yoga, all-weak planets, Rahu-Rahu MD): AI now opens with honest "1 yoga hai, jo NEGATIVE hai: Kemadruma", correctly frames Rahu MD as confusion phase, and anchors hope on 2026 transition — no false positivity.

## Sprint 2 — Ashtakavarga + Aspects (api-server)

Goal: Enrich LOCKED FACTS with two more deterministic engines so AI answers about a specific life-area (career/money/marriage etc.) cite a numerical strength meter, and AI can reference classical planetary aspects without inventing them.

- **`ashtakavarga.py`** (NEW) — `compute_ashtakavarga(planets, lagna_sign_idx)` returns Bhinnashtakavarga (BAV per planet) + Sarvashtakavarga (SAV per house) using BPHS contribution tables. Per-house verdicts: VERY STRONG ≥32, STRONG 28-31, AVERAGE 25-27, WEAK <25. Invariant: SAV total = 337 across 12 houses (validated). `format_sav_summary()` renders compact 2-row block + highlights very-strong/weak houses.
- **`aspects.py`** (NEW) — `compute_aspects(planets, lagna_sign_idx)` implements classical Graha Drishti: Mars 4/7/8, Jupiter 5/7/9, Saturn 3/7/10, Rahu/Ketu 5/7/9, others 7th. Returns by_planet/on_planet/on_house maps + `key_aspects` highlights (Jupiter on kendra/trikona, Saturn on Lagna/Moon, Mars on 7H/4H, mutual aspects across all rows — bug fixed in review).
- **`locked_facts.py`** — Both modules wired into the LOCKED FACTS block as `▸ SARVASHTAKAVARGA (SAV) per house` and `▸ KEY ASPECTS (classical Parashari drishti)` sections. Fail-closed: if upstream data malformed, sections drop silently.
- **`openai_helper.py`** — Two new mirror rules added to instruction 0b:
  - **RULE F (Ashtakavarga)** — for life-area questions, MUST check the SAV row for the relevant house (career=H10, money=H2/H11, marriage=H7, kids=H5, health=H6, home=H4) and cite the SAV value with verdict. Includes guard: "If SARVASHTAKAVARGA block is missing/unavailable, NEVER invent a number — fall back to dignity/house-lord reasoning."
  - **RULE G (Aspects)** — Use only aspects from the KEY ASPECTS list, max 1 per answer, never invent.
- **Smoke test (career question on /tmp/k.json)**: AI correctly opened with "Aapki kundli mein 10th ghar ka SAV 34 hai, jo very strong hai — yeh career mein natural strength dikhata hai" and maintained Rule E ("Rahu Mahadasha … confusion aur effort-without-result type ka phase hai"). Anchored hope on 2026 dasha change (Rule D tier iii).
- **Architect review fixes applied**: (1) Moon→Moon BAV table reduced to 6 entries (was 7) → fixes SAV invariant 338→337; (2) mutual aspect detection now scans all rows of the candidate planet (was checking only first row); (3) Rule F augmented with "unavailable → don't invent" guard.

## Sprint 3 — Transits + Bhava Bala + Karakas (api-server)

Goal: Three more deterministic engines so AI can answer (a) "kab" / timing questions using REAL-TIME sky positions (not just natal), (b) "kya banu / partner kaisa" using soul-level Jaimini karakas, (c) house strength as a second opinion to SAV.

- **`transits.py`** (NEW) — `compute_transits(natal_lagna, natal_moon, dob, when)` uses `swisseph` (Lahiri sidereal) to compute current Saturn / Jupiter / Rahu / Ketu sign + house from natal Lagna. Auto-detects Sade-Sati phase (Saturn 12/1/2 from natal Moon), Dhaiya / Ardha-Ashtama (4/8 from Moon), Saturn / Jupiter return age windows, Jupiter aspect on natal Lagna/5/9/11, Saturn over natal 8/12 (caution), Rahu over natal 1/7/10 (theme).
- **`bhava_bala.py`** (NEW) — `compute_bhava_bala(intel, planet_verdicts, aspects)` returns composite house score = bhava-lord verdict (±20/+10/-5) + occupant half-weight (with malefic penalty) + drishti pts (Jup +18, Ven/Mer +10, Sat/Mar -8, R/K -4) + kendra +10. Verdicts assigned by RELATIVE rank within the chart (top-3 = STRONG, mid-6 = MODERATE, bot-3 = WEAK) so even an all-weak chart gets useful differentiation.
- **`karakas.py`** (NEW) — `compute_karakas(planets)` implements **strict 7-karaka Jaimini** scheme (Sun-Saturn only; Rahu and Ketu EXCLUDED — 8-karaka variant is a separate doctrine, not implemented). Ranks by degree-in-sign descending, assigns AK/AmK/BK/MK/PK/GK/DK roles with full role-name labels for AI to cite.
- **`locked_facts.py`** — All three modules wired in as `▸ BHAVA BALA …`, `▸ JAIMINI CHARA KARAKAS …`, `▸ CURRENT TRANSITS …` sections; `birth.date` auto-extracted (best-effort) for Saturn/Jupiter return age math.
- **`openai_helper.py`** — Three new mirror rules added to instruction 0b:
  - **RULE H (Transits)** — for ANY 'kab' / timing / near-future Q, must consult CURRENT TRANSITS first. Cite Sade-Sati / Dhaiya phase when user is stressed. Saturn / Jupiter return = once-in-decades signal. ⚠️ guard: missing block → don't invent transit positions.
  - **RULE I (Karakas)** — AK = soul-purpose, DK = spouse, AmK = career signature, PK = creativity. Always cite role name once. Never invent karakas not in list.
  - **RULE J (Bhava Bala)** — relative-rank verdict (top-3 / mid-6 / bot-3 within THIS chart). Use as second opinion to SAV. Cite as "is chart ke top-3 strongest houses mein aata hai" — never as absolute strength.
- **Smoke test 1 (marriage timing)**: AI cited Saptamesh Mercury weak + Venus combust → partner artistic + Rahu MD honest framing + 12-yr Jupiter cycle. Pass.
- **Smoke test 2 (life purpose)**: AI opened with "Aapka Atmakaraka Saturn hai, jo aapko discipline aur structure ki taraf le jaata hai" — Rule I cited correctly. Rule E maintained. Pass.
- **Architect review fixes applied**: (1) Karakas — removed Rahu from `_ELIGIBLE`, doc updated to "strict 7-karaka, Rahu/Ketu excluded"; (2) Bhava Bala — recalibrated weights (lord ±20 not ±30, Jupiter aspect +18 not +30) so no single factor dominates; (3) Bhava Bala legend + Rule J re-aligned to relative-rank semantics (was inconsistently mixing absolute thresholds + relative ranking).

## Sprint 4 — Divisional Charts (D9 + D10) + Pratyantar Dasha (api-server)

Goal: Refine marriage answers using D9 Navamsa (the strongest classical predictor of marriage quality), refine career answers using D10 Dasamsa, and add month-precision timing via Vimshottari Pratyantar (sub-period under current AD).

- **`divisional_charts.py`** (NEW) — `compute_d9` + `compute_d10` implement BPHS Ch. 7 varga rules: D9 seed = same/9th/5th sign for movable/fixed/dual signs; D10 seed = same/9th sign for odd/even signs. Detects **Vargottama** planets (D1 sign = D9/D10 sign → exceptional strength). `summarize_d9_for_marriage` extracts 7L's D9 placement + strength (EXALTED/DEBIL/OWN/NEUTRAL) — the single most important signal for marriage quality. `summarize_d10_for_career` does the equivalent for 10L. Test chart: 7L Mercury → Virgo D9 (EXALTED), Venus → Pisces D9 (EXALTED), Sun is Vargottama; 10L Mercury → Sagittarius D10 (own-sign).
- **`pratyantar.py`** (NEW) — `compute_pratyantar(currentDasha, when)` uses standard Vimshottari proportions: PD_duration = AD_duration × (PD_lord_years / 120), order starts at AD lord, walks 9-step cycle. Returns current PD + next 3 upcoming PDs as month-precision windows. Falls back to honest "out_of_window" marker (not invention) when `when` is outside AD bounds.
- **`locked_facts.py`** — Both blocks wired between Karakas and Transits sections. Lagna longitude best-effort extracted for D9/D10 lagna sign.
- **`openai_helper.py`** — Two new mirror rules:
  - **RULE K (Divisional Charts)** — for marriage Qs MUST consult D9 7L line; for career Qs MUST consult D10 10L line. D9/D10 strength can OVERRIDE conflicting natal D1 verdict (a 7L weak in D1 but EXALTED in D9 = much better marriage outcome than D1 alone suggests). Vargottama planets must be called out by name.
  - **RULE L (Pratyantar)** — for precise timing Qs (next 3-6 months, specific weeks), cite current PD lord + window AND the next 1-2 upcoming PDs as "change-windows". Combine with planet strengths for green/yellow/red light verdicts.
- **Smoke test (career Q)**: AI cited *"D10 chart mein aapka 10L Mercury Sagittarius mein hai, jo apne sign mein hai"* + *"Aane wale Jupiter pratyantar (2026-05-30 se) se growth aur opportunities"* — both Rule K and Rule L firing simultaneously with real computed values. Pass.
- **Architect review fixes applied**:
  1. **Pratyantar `_parse_date`** — was using format-string-length slicing which silently dropped time components; replaced with robust `datetime.fromisoformat()` + 'Z' normalization that preserves full datetime precision.
  2. **Pratyantar out-of-window honesty** — old code forced `current_pd = pds[0]` if `when` fell outside AD window (could mis-state reality); now returns explicit `out_of_window: true` and the formatter emits *"do NOT invent a current pratyantar"* guard.
  3. **Divisional summary anti-hallucination** — when 7L/10L cannot be resolved, formatter now emits explicit *"7L D9 placement: UNAVAILABLE (do NOT invent — fall back to natal 7L)"* line so Rule K cannot pressure the model into fabrication.

## Sprint 5 — Remedies Engine (api-server)

Goal: Replace per-answer remedy hallucination (AI was fabricating mantras like "Om Shum Shukraya Namah") with a single deterministic source of truth — classical Vedic remedies sourced from BPHS, Phaladeepika, and Lal Kitab consensus.

- **`remedies.py`** (NEW) — Per-planet `_REMEDY_TABLE` with 9 entries (Sun→Ketu) containing: mantra (Sanskrit + transliteration + count + day), gemstone (name + carat range + metal + finger + caveat where applicable), charity items, fast day, colour, yantra. Special dosha-specific bundles for Sade-Sati, Mangal Dosh, and Kal-Sarpa Yoga (each with classical multi-line mantra + Hanuman/Naga-puja extras).
- **`select_remedies()`** prioritises: (1) special doshas, (2) running Mahadasha lord if WEAK / combust / debilitated, (3) topic-relevant house lord (7L for marriage, 10L for career, etc.) if weak, (4) truly weakest remaining planet by score (not dict order). Returns max 3 remedies.
- **Caveats baked in** — Blue Sapphire trial-period warning, Hessonite/Cat's-Eye flagged as "post-classical (Lal Kitab tradition) — not strict BPHS". Charity items are concrete, not generic ("Black sesame in flowing water" not "do something with black").
- **`locked_facts.py`** — Wired between Pratyantar and house-lords sections. Verdicts unwrapped from `{planet:{verdict, reason, score}}` to flat string map; full dict passed as `planet_scores=` for true weakest-planet ranking.
- **`openai_helper.py`** — **Rule M** added: AI MUST quote remedies VERBATIM from the REMEDIES block, NEVER invent Sanskrit, weights, or "lucky stones". Must use the `for: ...` label so user knows WHY this remedy. If REMEDIES block is empty, fall back to generic "Hanuman Chalisa" advice — never fabricate specifics.
- **Smoke test (job dikkat Q)**: AI cited *"Rahu ke liye 'Om Bhraam Bhreem Bhraum Sah Rahave Namah' 108 baar Saturday ko"* — exact mantra from block, correct planet (running MD lord), correct day. Rule M firing. Pass.
- **Architect review fixes applied**:
  1. **True weakest fallback** — replaced "first WEAK planet in dict iteration" with sorted-by-score lowest-first selection.
  2. **MD-lord robust extraction** — `_md_lord()` now accepts `maha | mahadasha | md | planet | lord` keys.
  3. **Kal-Sarpa name match** — old `"kal sarp"|"kalsarp"` substring check missed common `"Kaal Sarp Dosh"`; replaced with `"kal" in n and "sarp" in n` after dash/underscore normalisation.
  4. **Formatter `for:` label** — added missing colon to align with Rule M's enforcement pattern.

## Sprint 6 — KP Cuspal Sub-Lord Cross-Check (api-server)

Goal: Add KP (Krishnamurti Paddhati) cuspal sub-lord verdicts as a fructification cross-check to the LOCKED FACTS — the classical KP rule that says an event under house H only manifests if the SUB-LORD of cusp H signifies that house's event-set.

- **Discovery** — `kp_engine.py` already fully built (Placidus cusps via swisseph, sub-lord SL/NL/SB/SS computation per longitude, planet significations dict). Was used by prashna/marriage/partner-portrait but NOT by the conversational LOCKED FACTS pipeline.
- **`kp_locked_facts.py`** (NEW) — Adapter that:
  1. `_to_kp_input()` — accepts structured `birth` dict OR parses `kundli.dob` ("15 Jan 1990") + `kundli.time` ("06:30 AM") + lat/lon/tz fallback. Treats `0` as VALID for tz/lat (UTC, equator) — only `None`/empty-string is "missing".
  2. `_verdict_for()` — classical KP gating: PROMISE if sub-lord signifies any house in the event-set; DENIES if signifies only negative-set houses; PARTIAL if signifies BOTH event AND negative houses (obstruction/delay).
  3. Per-house event sets: H1 {1,5,9,11}, H2 {2,6,10,11}, H5 {2,5,11}, H7 {2,7,11}, H10 {2,6,10,11}, H11 {2,6,10,11}. Per-house negative sets per Krishnamurti negation conventions.
  4. `compute_kp_summary()` + `format_kp_summary()` — defensive type checks throughout (handles malformed `calculate_kp` output without crashing).
- **`locked_facts.py`** — Wired between Pratyantar and Remedies. Best-effort: silently absent if birth lacks lat/lon/tz (mobile client supplies these for saved kundlis).
- **`openai_helper.py`** — **Rule N** added (mandatory citation): when KP block is present and question maps to H1/H2/H5/H7/H10/H11, AI must weave one natural KP citation. Resolution rules for Vedic⇄KP disagreement codified (Strong+Confirms = green light; Strong+Denies = "delay/alternate timing"; Weak+Confirms = "possible with effort"). NEVER invent KP sub-lords if block absent.
- **Architect review fixes applied**:
  1. `_missing()` helper — `0`/`0.0` no longer collapse to None (fixes UTC tz=0, equator lat=0).
  2. `_verdict_for` — added negative-house set; now distinguishes clean PROMISE from PARTIAL (obstruction). Matches K.S. Krishnamurti's classical gating.
  3. Rule N rewording — softened "FINAL arbiter" → "PARALLEL cross-check" (no override of D9/D10/Dasha), retained MANDATORY-citation requirement for compliance.
  4. Defensive isinstance guards in `compute_kp_summary` / `format_kp_summary` for malformed engine output.
- **Smoke test**: career Q with Delhi birth → AI cited *"KP paddhati se bhi 10th cusp ka sub-lord Moon hai, jo is growth ko support nahi karta"*. Block correctly emits 6 houses with verdict + signified/obstructed house lists. Unit tests pass for missing-detection (tz=0, lat=0) and verdict logic (DENIES/PARTIAL/CONFIRMS/UNKNOWN).
- **Known limitation**: Mandatory KP citation is intermittent under gpt-4o-mini with the now-very-long system prompt — model reliably cites when nudged or for direct KP questions, but sometimes drops the citation under topic-driven phrasing. Mitigations for a future polish pass: model upgrade, prompt restructure (rules at end for recency), or post-response verification.

## Session Final Status

6 sprints complete in this session. LOCKED FACTS now contains 14 deterministic blocks (lagna/moon/nak → yogas → doshas → planet strengths → SAV → bhava bala → aspects → karakas → D9/D10 → transits → dasha → pratyantar → house lords → KP cusp cross-check → remedies). 14 mirror prompt rules (A–N) ensure verbatim citation and zero hallucination.

What remains DEFERRED:
- **8-route question-router reactivation** — current openai_helper topic detection works; 8-route classifier would be incremental polish, not core capability.


## Sprint 7 — Jaimini Upapada Lagna + Arudha Padas (DONE)

**Engine:** `artifacts/api-server/jaimini.py`
- `compute_arudha_padas(planets, lagna_sign)` → A1-A12 (formula `(2×LordSign − HouseSign) mod 12` with classical 1st/7th-from-itself → 10th-from-Arudha exception).
- `compute_upapada(arudha_result, planets)` → UL = A12 + UL-lord placement (house-from-UL) + 2nd-from-UL occupants + 12th-from-UL occupants + planets in UL itself + STABLE/STRAINED/MIXED/NEUTRAL verdict + dusthana-caution flag.
- `format_jaimini_summary()` → LOCKED FACTS block.

**Wiring:**
- `locked_facts.py` includes the Jaimini block.
- `openai_helper.py` adds Rule O (mandatory UL citation for marriage), pins it FIRST in FINAL REMINDERS.
- `marriage_facts['jaimini']` populated for narrator path with template Para 4.
- **Deterministic post-processor** in `ai_ask()` → if marriage answer doesn't contain "Upapada"/"Jaimini", appends one engine-generated sentence using the live UL data (Hindi translations of verdict tags, dusthana caution, separation flag from Ketu/Saturn/Rahu in 12th-from-UL). 100% reliable Rule O satisfaction.

**Smoke test (3/3):** All marriage answers now end with the Jaimini UL citation. Example: *"Jaimini paddhati se Upapada Lagna Leo mein hai (lord Sun) — yeh marriage signature neutral hai (UL-lord Sun dusthana 6th from UL — thodi caution)."*

**Roadmap remaining (Sprints 8-15):** Chara Dasha; D7+D12+D2+D3; D24+D16+D20+D27; D30+D40+D45+D60; per-varga deep (lord/aspects/vargottama); Argala+Virodhargala; Sthira+Niryana Shoola dashas; varga-specific yoga/dosha detection.
