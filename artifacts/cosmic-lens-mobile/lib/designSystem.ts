/**
 * Cosmic Lens — Global Design System
 * Single source of truth for typography, spacing, and static color constants.
 * For theme-aware colors always use C.* tokens from ThemeContext.
 */

export const G = {

  // ── Typography scale ──────────────────────────────────────────────────────
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

  // ── Static brand colors (non-theme-aware) ─────────────────────────────────
  // For theme-aware colors, always use C.* from ThemeContext instead.
  color: {
    // Light mode accent — cool indigo
    indigoLight:  "#6366F1",
    indigoDark:   "#4F46E5",
    // Dark mode accent — violet glow
    violetLight:  "#A78BFA",
    violetDark:   "#8B5CF6",
    // CTA / action — orange
    orange:       "#FF7A00",
    orangeDark:   "#FF4D00",
    // CTA / action — gold (dark mode luxury)
    gold:         "#F59E0B",
    goldDark:     "#D97706",
    // Semantic
    success:      "#16A34A",
    error:        "#DC2626",
    warning:      "#F59E0B",
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

  // ── Elevation shadow (light mode — no glow) ───────────────────────────────
  shadow: {
    card: {
      shadowColor:   "#0F172A",
      shadowOffset:  { width: 0, height: 2 },
      shadowOpacity: 0.08,
      shadowRadius:  8,
      elevation:     3,
    },
    strong: {
      shadowColor:   "#0F172A",
      shadowOffset:  { width: 0, height: 4 },
      shadowOpacity: 0.12,
      shadowRadius:  16,
      elevation:     5,
    },
  },

  // ── Card base style ───────────────────────────────────────────────────────
  card: {
    borderRadius:      16,
    paddingVertical:   14,
    paddingHorizontal: 14,
  },

  // ── Input base style ─────────────────────────────────────────────────────
  input: {
    borderRadius:      10,
    borderWidth:       0.75,
    minHeight:         46,
    paddingHorizontal: 12,
    fontSize:          14,
  },
};
