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

## Dark / Light Theme

- `context/ThemeContext.tsx` — `DARK` / `LIGHT` palettes with `toggle()` and AsyncStorage persistence (`cl_theme` key)
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

- `lib/i18n.ts` — Central translation system with `getT(language)` function
- Supports 8 languages: English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada
- Usage pattern: `import { getT } from "@/lib/i18n"; const t = getT(language);`
- Language persists in AsyncStorage; changing it updates all wired screens instantly
- **Wired screens**: CustomTabBar, profile.tsx, login.tsx, onboarding.tsx, index.tsx (home), kundli.tsx, ask.tsx, insights.tsx, notice.tsx
- `UserContext` exposes `language` (LangCode) and `setLanguage` — accessible from any screen

## API Endpoints

- `GET /api/healthz` — Health check
- `POST /api/kundli` — Calculate Vedic kundli
- `GET /api/moon_history` — Moon position history
- `POST /api/ask` — Ask astrology question
- `POST /api/register`, `POST /api/login` — Auth
