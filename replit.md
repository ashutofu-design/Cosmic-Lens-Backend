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
- **Wired screens**: CustomTabBar, profile.tsx, login.tsx, onboarding.tsx, index.tsx (home), kundli.tsx, ask.tsx, insights.tsx, notice.tsx

## API Endpoints

- `GET /api/healthz` — Health check
- `POST /api/kundli` — Calculate Vedic kundli
- `GET /api/moon_history` — Moon position history
- `POST /api/ask` — Ask astrology question
- `POST /api/register`, `POST /api/login` — Auth
