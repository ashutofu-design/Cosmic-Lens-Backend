import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {
  createContext, useCallback, useContext,
  useEffect, useMemo, useState,
} from "react";

import { DEFAULT_ACCENT, type ZodiacAccent, type ZodiacSign } from "@/lib/zodiac";

export type ThemeMode = "dark" | "light";

export interface ThemeColors {
  // Backgrounds
  bg:      string;
  bgCard:  string;
  bgCard2: string;
  bgCard3: string;
  // Text
  text:      string;
  textMid:   string;
  textMuted: string;
  textDim:   string;
  // Accent (overridden by zodiac when available)
  accent:   string;
  accentBg: string;
  // Borders
  border:  string;
  border2: string;
  border3: string;
  // Misc
  switchTrackOff: string;
  navBg:          string;
  navBorder:      string;
  inputBg:        string;
  inputBorder:    string;
  inputFocusBorder: string;
  shimmer1:       string;
  shimmer2:       string;
  shimmer3:       string;
  // Card glow shadow (CSS boxShadow string)
  cardShadow: string;
  // Status bar style
  statusBar: "light-content" | "dark-content";
  isDark: boolean;

  // Warning / info box
  warningBg:     string;
  warningBorder: string;
  warningText:   string;

  // Toggle buttons selected state (gender / AM-PM / chips)
  toggleSelBg:     string;
  toggleSelBorder: string;
  toggleSelText:   string;

  // Primary button gradient stops [start, end]
  btnGradStart: string;
  btnGradEnd:   string;
}

// ── Dark — Deep Black + Purple Glow (Premium / Luxury) ────────────────────────
export const DARK: ThemeColors = {
  // Deep black backgrounds
  bg:      "#0B0F19",
  bgCard:  "#111827",
  bgCard2: "#1A2135",
  bgCard3: "#1D2545",

  // Clean high-contrast text
  text:      "#F9FAFB",
  textMid:   "#D1D5DB",
  textMuted: "#9CA3AF",
  textDim:   "#6B7280",

  // Purple accent (overridden by zodiac sign when set)
  accent:   "#8B5CF6",
  accentBg: "rgba(139,92,246,0.14)",

  // Subtle purple-tinted borders
  border:  "rgba(139,92,246,0.20)",
  border2: "rgba(139,92,246,0.32)",
  border3: "rgba(139,92,246,0.10)",

  switchTrackOff:   "#1A2135",
  navBg:            "#111827",
  navBorder:        "#1F2937",
  inputBg:          "#1F2937",
  inputBorder:      "#374151",
  inputFocusBorder: "#8B5CF6",

  shimmer1: "rgba(11,15,25,0.95)",
  shimmer2: "rgba(17,24,39,0.95)",
  shimmer3: "rgba(11,15,25,0.95)",

  // Luxury purple glow on cards
  cardShadow:
    "0 4px 24px rgba(139,92,246,0.28), 0 0 0 1px rgba(139,92,246,0.10) inset",

  statusBar: "light-content",
  isDark: true,

  warningBg:     "#451A03",
  warningBorder: "rgba(245,158,11,0.50)",
  warningText:   "#FCD34D",

  // Purple selection for toggle chips (gender / AM-PM)
  toggleSelBg:     "rgba(139,92,246,0.15)",
  toggleSelBorder: "#8B5CF6",
  toggleSelText:   "#C4B5FD",

  // Gold CTA gradient — luxury feel in dark mode
  btnGradStart: "#F59E0B",
  btnGradEnd:   "#EA580C",
};

// ── Light — Premium White + Strong Purple Accents ─────────────────────────────
export const LIGHT: ThemeColors = {
  // Clean neutral — lavender only in explicit accent cards
  bg:      "#F5F5F8",
  bgCard:  "#FFFFFF",
  bgCard2: "#F3F4F6",
  bgCard3: "#E5E7EB",

  // High-contrast readable text hierarchy
  text:      "#111827",   // primary headings — near-black
  textMid:   "#374151",   // body text
  textMuted: "#6B7280",   // secondary labels
  textDim:   "#9CA3AF",   // placeholder / dim

  // Strong purple accent
  accent:   "#6D5DF6",
  accentBg: "rgba(109,93,246,0.08)",

  // Clear visible borders
  border:  "#E5E7EB",
  border2: "#D1D5DB",
  border3: "#F3F4F6",

  switchTrackOff:   "#D1D5DB",
  navBg:            "#FFFFFF",
  navBorder:        "#E5E7EB",
  inputBg:          "#F9FAFB",
  inputBorder:      "#E5E7EB",
  inputFocusBorder: "#6D5DF6",

  shimmer1: "rgba(248,249,252,0.95)",
  shimmer2: "rgba(243,244,248,0.95)",
  shimmer3: "rgba(248,249,252,0.95)",

  // Visible card shadow for depth
  cardShadow:
    "0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.08), 0 0 0 1px #E5E7EB",

  statusBar: "dark-content",
  isDark: false,

  warningBg:     "#FEF3C7",
  warningBorder: "#F59E0B",
  warningText:   "#92400E",

  // Strong purple selection
  toggleSelBg:     "rgba(109,93,246,0.08)",
  toggleSelBorder: "#6D5DF6",
  toggleSelText:   "#4F46E5",

  // Strong purple CTA gradient — matches accent
  btnGradStart: "#6D5DF6",
  btnGradEnd:   "#8B5CF6",
};

// ── Context shape ─────────────────────────────────────────────────────────────
interface ThemeCtx {
  mode: ThemeMode;
  C: ThemeColors;
  setMode:          (m: ThemeMode) => void;
  toggle:           () => void;
  // Zodiac accent
  zodiacSign:       ZodiacSign | null;
  zodiacAccent:     ZodiacAccent;
  setZodiacAccent:  (sign: ZodiacSign | null, accent: ZodiacAccent) => void;
}

const ThemeContext = createContext<ThemeCtx>({
  mode: "dark", C: DARK,
  setMode: () => {}, toggle: () => {},
  zodiacSign: null, zodiacAccent: DEFAULT_ACCENT,
  setZodiacAccent: () => {},
});

const STORAGE_KEY = "cl_theme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, _setMode]                 = useState<ThemeMode>("dark");
  const [zodiacSign, _setZodiacSign]     = useState<ZodiacSign | null>(null);
  const [zodiacAccent, _setZodiacAccent] = useState<ZodiacAccent>(DEFAULT_ACCENT);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then(v => {
      if (v === "light" || v === "dark") _setMode(v);
    });
  }, []);

  const setMode = useCallback((m: ThemeMode) => {
    _setMode(m);
    AsyncStorage.setItem(STORAGE_KEY, m).catch(() => {});
  }, []);

  const toggle = useCallback(() => {
    setMode(mode === "dark" ? "light" : "dark");
  }, [mode, setMode]);

  const setZodiacAccent = useCallback(
    (sign: ZodiacSign | null, accent: ZodiacAccent) => {
      _setZodiacSign(sign);
      _setZodiacAccent(accent);
    },
    []
  );

  const C = useMemo<ThemeColors>(() => {
    const base = mode === "dark" ? DARK : LIGHT;

    // When no zodiac is selected (DEFAULT_ACCENT), use mode-appropriate purple:
    // Light → indigo #6366F1 (cool & modern)
    // Dark  → violet #8B5CF6 (glowing premium)
    const isDefault = zodiacAccent === DEFAULT_ACCENT;
    const finalAccent: ZodiacAccent = (isDefault && mode === "dark")
      ? { accent: "#8B5CF6", accentBg: "rgba(139,92,246,0.14)" }
      : zodiacAccent;

    return { ...base, accent: finalAccent.accent, accentBg: finalAccent.accentBg };
  }, [mode, zodiacAccent]);

  return (
    <ThemeContext.Provider value={{ mode, C, setMode, toggle, zodiacSign, zodiacAccent, setZodiacAccent }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

export function useC() {
  return useContext(ThemeContext).C;
}
