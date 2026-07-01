// EAS / Linux Metro auto-discovery entry (require works on Unix CI).
// Windows local dev: use `pnpm run dev:phone` — sets EXPO_OVERRIDE_METRO_CONFIG
// to file:// URL for metro.cosmic.cjs (avoids ERR_UNSUPPORTED_ESM_URL_SCHEME).
module.exports = require("./metro.cosmic.cjs");
