const HARDCODED_FALLBACK = "18370deb-aa55-4d9f-8391-57df5a15cf7a-00-phjaov5qh4np.expo.kirk.replit.dev";

const domain = process.env.EXPO_PUBLIC_DOMAIN || HARDCODED_FALLBACK;

export const API_BASE = `https://${domain}`;

if (__DEV__) {
  console.log("[CosmicLens] EXPO_PUBLIC_DOMAIN:", process.env.EXPO_PUBLIC_DOMAIN);
  console.log("[CosmicLens] API_BASE resolved to:", API_BASE);
}
