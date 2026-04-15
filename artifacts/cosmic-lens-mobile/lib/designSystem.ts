/**
 * Cosmic Lens — Global Design System
 * Single source of truth for typography, spacing, color usage, and shadows.
 * Import `G` in any screen to get consistent values.
 */

export const G = {

  // ── Typography ────────────────────────────────────────────────────────────
  // Use these with fontFamily from the F alias in each screen.
  type: {
    pageTitle:     { fontSize: 20, letterSpacing: -0.4 },
    sectionHeader: { fontSize: 16, letterSpacing: -0.2 },
    cardTitle:     { fontSize: 15, letterSpacing: -0.1 },
    body:          { fontSize: 14, lineHeight: 22 },
    bodySmall:     { fontSize: 13, lineHeight: 20 },
    subtext:       { fontSize: 12, lineHeight: 18 },
    label:         { fontSize: 10, letterSpacing: 1.3 },
  },

  // ── Font families ─────────────────────────────────────────────────────────
  font: {
    regular:  "Nunito_400Regular",
    medium:   "Nunito_500Medium",
    semibold: "Nunito_600SemiBold",
    bold:     "Nunito_700Bold",
  },

  // ── Color palette (static, non-theme) ────────────────────────────────────
  color: {
    primary:   "#FF7A00",
    secondary: "#6366F1",
    success:   "#16A34A",
    error:     "#DC2626",
    warning:   "#F59E0B",
    // Light mode backgrounds
    pageBg:    "#F8FAFC",
    cardBg:    "#FFFFFF",
    // Text hierarchy
    textHigh:  "#0F172A",
    textMid:   "#334155",
    textLow:   "#64748B",
    textDim:   "#94A3B8",
  },

  // ── Spacing ───────────────────────────────────────────────────────────────
  space: {
    pagePad:    16,
    sectionGap: 16,
    cardGap:    12,
    cardPad:    14,
  },

  // ── Component sizes ───────────────────────────────────────────────────────
  size: {
    inputH:   46,
    btnH:     52,
    iconBtn:  36,
    tabBarH:  60,
  },

  // ── Card shadow — light mode ──────────────────────────────────────────────
  shadow: {
    card: {
      shadowColor:   "#64748B",
      shadowOffset:  { width: 0, height: 4 },
      shadowOpacity: 0.10,
      shadowRadius:  12,
      elevation:     4,
    },
    strong: {
      shadowColor:   "#64748B",
      shadowOffset:  { width: 0, height: 6 },
      shadowOpacity: 0.14,
      shadowRadius:  16,
      elevation:     6,
    },
  },

  // ── Card base style ───────────────────────────────────────────────────────
  card: {
    borderRadius:    16,
    paddingVertical: 14,
    paddingHorizontal: 14,
  },

  // ── Input base style ─────────────────────────────────────────────────────
  input: {
    borderRadius:  10,
    borderWidth:   0.75,
    minHeight:     46,
    paddingHorizontal: 12,
    fontSize:      14,
  },
};
