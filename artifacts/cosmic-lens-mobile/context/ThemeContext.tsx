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
  navBg:            "#0B0F19",
  navBorder:        "rgba(139,92,246,0.18)",
  inputBg:          "#111827",
  inputBorder:      "rgba(139,92,246,0.22)",
  inputFocusBorder: "rgba(139,92,246,0.75)",

  shimmer1: "rgba(11,15,25,0.95)",
  shimmer2: "rgba(17,24,39,0.95)",
  shimmer3: "rgba(11,15,25,0.95)",

  // Luxury purple glow on cards
  cardShadow:
    "0 4px 24px rgba(139,92,246,0.28), 0 0 0 1px rgba(139,92,246,0.10) inset",

  statusBar: "light-content",
  isDark: true,

  warningBg:     "rgba(245,158,11,0.10)",
  warningBorder: "rgba(245,158,11,0.40)",
  warningText:   "#FCD34D",

  // Purple selection for toggle chips (gender / AM-PM)
  toggleSelBg:     "rgba(139,92,246,0.18)",
  toggleSelBorder: "#8B5CF6",
  toggleSelText:   "#C4B5FD",

  // Gold CTA gradient — luxury feel in dark mode
  btnGradStart: "#F59E0B",
  btnGradEnd:   "#D97706",
};

// ── Light — Clean White + Indigo Accents (Modern / Minimal) ───────────────────
export const LIGHT: ThemeColors = {
  // Soft white backgrounds
  bg:      "#F8FAFC",
  bgCard:  "#FFFFFF",
  bgCard2: "#F1F5F9",
  bgCard3: "#E2E8F0",

  // Strong readable text hierarchy
  text:      "#0F172A",   // primary — headings
  textMid:   "#334155",   // secondary — body
  textMuted: "#64748B",   // subtext — labels
  textDim:   "#94A3B8",   // placeholder / dim

  // Indigo accent (overridden by zodiac sign when set)
  accent:   "#6366F1",
  accentBg: "rgba(99,102,241,0.08)",

  // Crisp slate borders
  border:  "#CBD5E1",
  border2: "#94A3B8",
  border3: "#E2E8F0",

  switchTrackOff:   "#CBD5E1",
  navBg:            "#FFFFFF",
  navBorder:        "#CBD5E1",
  inputBg:          "#FFFFFF",
  inputBorder:      "#CBD5E1",
  inputFocusBorder: "#6366F1",

  shimmer1: "rgba(248,250,252,0.95)",
  shimmer2: "rgba(241,245,249,0.95)",
  shimmer3: "rgba(248,250,252,0.95)",

  // Subtle elevation shadow — no glow in light mode
  cardShadow:
    "0 1px 4px rgba(15,23,42,0.06), 0 4px 16px rgba(15,23,42,0.08), 0 1px 0 #FFFFFF inset",

  statusBar: "dark-content",
  isDark: false,

  warningBg:     "#FEF3C7",
  warningBorder: "#F59E0B",
  warningText:   "#92400E",

  // Indigo selection — clean and modern
  toggleSelBg:     "rgba(99,102,241,0.10)",
  toggleSelBorder: "#6366F1",
  toggleSelText:   "#4F46E5",

  // Orange CTA gradient — punchy and visible
  btnGradStart: "#FF7A00",
  btnGradEnd:   "#FF4D00",
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
