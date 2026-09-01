/**
 * Instagram reel auto-replies (DM trigger → answer in app).
 * Shown under Cosmic Intelligence on Ask. Set
 * EXPO_PUBLIC_ENABLE_INSTAGRAM_ANSWERS=0 to hide.
 */
export const INSTAGRAM_ANSWERS_ENABLED =
  (process.env.EXPO_PUBLIC_ENABLE_INSTAGRAM_ANSWERS ?? "1").trim() !== "0";
