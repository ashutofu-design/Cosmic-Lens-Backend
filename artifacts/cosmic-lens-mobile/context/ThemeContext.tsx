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

  // Toggle buttons selected state (gender / AM-PM)
  toggleSelBg:     string;
  toggleSelBorder: string;
  toggleSelText:   string;

  // Primary button gradient stops [start, end]
  btnGradStart: string;
  btnGradEnd:   string;
}

// ── Dark — Charcoal + Subtle Purple Tint ──────────────────────────────────────
export const DARK: ThemeColors = {
  bg:      "#161420",
  bgCard:  "rgba(30,27,46,0.80)",
  bgCard2: "rgba(37,34,56,0.65)",
  bgCard3: "rgba(44,41,68,0.55)",

  text:      "#f2eeff",
  textMid:   "#c4b8e8",
  textMuted: "#9585c0",
  textDim:   "#5a4e80",

  accent:   "#f59e0b",
  accentBg: "rgba(245,158,11,0.13)",

  border:  "rgba(180,150,255,0.18)",
  border2: "rgba(180,150,255,0.30)",
  border3: "rgba(180,150,255,0.10)",

  switchTrackOff: "#252238",
  navBg:     "#161420",
  navBorder: "rgba(180,150,255,0.18)",
  inputBg:   "#1e1b2e",
  inputBorder: "rgba(180,150,255,0.26)",
  inputFocusBorder: "rgba(245,158,11,0.45)",

  shimmer1: "rgba(30,27,46,0.9)",
  shimmer2: "rgba(37,34,56,0.9)",
  shimmer3: "rgba(30,27,46,0.9)",

  cardShadow: "0 4px 28px rgba(139,92,246,0.22), 0 1px 0 rgba(255,255,255,0.06) inset",

  statusBar: "light-content",
  isDark: true,

  warningBg:     "rgba(255,165,0,0.08)",
  warningBorder: "rgba(255,165,0,0.35)",
  warningText:   "#FFD580",

  toggleSelBg:     "rgba(245,158,11,0.15)",
  toggleSelBorder: "#f59e0b",
  toggleSelText:   "#f59e0b",

  btnGradStart: "#f59e0b",
  btnGradEnd:   "#d97706",
};

// ── Light — Bold Premium Slate ─────────────────────────────────────────────────
export const LIGHT: ThemeColors = {
  bg:      "#F1F5F9",
  bgCard:  "#FFFFFF",
  bgCard2: "#F8FAFC",
  bgCard3: "#F1F5F9",

  text:      "#0F172A",   // slate-900  — headings (boldest)
  textMid:   "#1E293B",   // slate-800  — body
  textMuted: "#334155",   // slate-700  — labels / secondary (was 64748B — too faded)
  textDim:   "#94A3B8",   // slate-400  — placeholder

  accent:   "#6366F1",    // indigo-500 (overridden by zodiac)
  accentBg: "rgba(99,102,241,0.08)",

  border:  "#CBD5E1",     // slate-300  — stronger card border (was E2E8F0)
  border2: "#94A3B8",     // slate-400  — input border
  border3: "#E2E8F0",     // slate-200  — subtle dividers

  switchTrackOff: "#CBD5E1",
  navBg:     "#FFFFFF",
  navBorder: "#CBD5E1",
  inputBg:   "#F1F5F9",       // slightly grey background for inputs
  inputBorder: "#94A3B8",     // stronger border
  inputFocusBorder: "#6366F1",

  shimmer1: "rgba(248,250,252,0.95)",
  shimmer2: "rgba(241,245,249,0.95)",
  shimmer3: "rgba(248,250,252,0.95)",

  cardShadow: "0 2px 8px rgba(15,23,42,0.10), 0 8px 24px rgba(15,23,42,0.06), 0 1px 0 rgba(255,255,255,1) inset",

  statusBar: "dark-content",
  isDark: false,

  // Warning — amber
  warningBg:     "#FEF3C7",
  warningBorder: "#F59E0B",
  warningText:   "#92400E",

  // Toggle selected — red/crimson (high-contrast, bold)
  toggleSelBg:     "#FEE2E2",
  toggleSelBorder: "#DC2626",
  toggleSelText:   "#DC2626",

  // Primary button gradient — amber → orange
  btnGradStart: "#F59E0B",
  btnGradEnd:   "#EA580C",
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
  const [mode, _setMode]           = useState<ThemeMode>("dark");
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

  // Merge base palette with zodiac accent override
  const C = useMemo<ThemeColors>(() => {
    const base = mode === "dark" ? DARK : LIGHT;
    return { ...base, accent: zodiacAccent.accent, accentBg: zodiacAccent.accentBg };
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
