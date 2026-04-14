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

## API Endpoints

- `GET /api/healthz` — Health check
- `POST /api/kundli` — Calculate Vedic kundli
- `GET /api/moon_history` — Moon position history
- `POST /api/ask` — Ask astrology question
- `POST /api/register`, `POST /api/login` — Auth
