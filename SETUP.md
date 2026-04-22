# Cosmic Lens — Local Setup (VS Code)

## Backend (Flask API)

```bash
cd artifacts/api-server
cp .env.example .env
# Fill in: DATABASE_URL, SESSION_SECRET, OPENAI_API_KEY, FIREBASE_SERVICE_ACCOUNT_JSON,
#          MSG91_*, CASHFREE_APP_ID, CASHFREE_SECRET_KEY

pip install -r requirements.txt

# Dev mode (Flask dev server, debug-friendly):
bash start.sh

# Production mode (gunicorn, 4 workers):
PROD=1 bash start.sh
```

API runs on `http://localhost:8080`.

## Mobile (Expo)

```bash
cd artifacts/cosmic-lens-mobile
cp .env.example .env
# Set EXPO_PUBLIC_API_URL=http://localhost:8080 for local backend
# Fill in EXPO_PUBLIC_FIREBASE_* for web preview (optional)

pnpm install

# Local dev (no tunnel — for VS Code):
pnpm dev:local

# Replit dev (with cloudflare/localtunnel):
pnpm dev
```

Then open the QR code in **Expo Go** on your phone, or press `w` for web preview.

## Production checklist

- [ ] Backend hosted (Replit Deploy / Render / Railway)
- [ ] `EXPO_PUBLIC_API_URL` in mobile `.env` points to deployed backend
- [ ] Firebase keys filled (`google-services.json` for Android in `cosmic-lens-mobile/`)
- [ ] `FIREBASE_SERVICE_ACCOUNT_JSON` set on backend
- [ ] `MSG91_*` set for OTP
- [ ] `CASHFREE_*` set with `CASHFREE_ENV=PROD`
- [ ] `SESSION_SECRET` is a strong random value
- [ ] Run `pnpm eas:build:prod` for Play Store APK/AAB

## Known limitations

- Festival dates (`festivals10y.ts`) are pre-computed for 2026-2035; verify against Drik Panchang for ritual-critical timing.
- Local panchang fallback is approximation (used only when API is unreachable; status badge shows ⚠️).
- Marriage / Kundli Milan inline form: birth data attached via `_rawBirth` — fixes "Birth Data Missing" alert when not using a saved profile.
