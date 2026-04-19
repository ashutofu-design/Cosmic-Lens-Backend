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
