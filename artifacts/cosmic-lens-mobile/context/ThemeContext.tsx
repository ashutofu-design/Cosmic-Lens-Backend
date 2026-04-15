import AsyncStorage from "@react-native-async-storage/async-storage";
import React, {
  createContext, useCallback, useContext,
  useEffect, useState,
} from "react";
import { Appearance } from "react-native";

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
  // Accent
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
  shimmer1:       string;
  shimmer2:       string;
  shimmer3:       string;
  // Card glow shadow (CSS boxShadow string)
  cardShadow: string;
  // Status bar style
  statusBar: "light-content" | "dark-content";
  isDark: boolean;
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

  shimmer1: "rgba(30,27,46,0.9)",
  shimmer2: "rgba(37,34,56,0.9)",
  shimmer3: "rgba(30,27,46,0.9)",

  cardShadow: "0 4px 28px rgba(139,92,246,0.22), 0 1px 0 rgba(255,255,255,0.06) inset",

  statusBar: "light-content",
  isDark: true,
};

// ── Light — Warm Lavender + Amber Gold ────────────────────────────────────────
export const LIGHT: ThemeColors = {
  bg:      "#faf5ff",
  bgCard:  "rgba(255,255,255,0.82)",
  bgCard2: "rgba(243,235,255,0.72)",
  bgCard3: "rgba(237,224,255,0.62)",

  text:      "#1e0a3c",
  textMid:   "#6b46c1",
  textMuted: "#9f7aea",
  textDim:   "#d8b4fe",

  accent:   "#d97706",
  accentBg: "rgba(217,119,6,0.09)",

  border:  "rgba(109,40,217,0.09)",
  border2: "rgba(109,40,217,0.16)",
  border3: "rgba(109,40,217,0.05)",

  switchTrackOff: "#e9d8fd",
  navBg:     "#ffffff",
  navBorder: "rgba(109,40,217,0.09)",
  inputBg:   "#faf5ff",
  inputBorder: "rgba(109,40,217,0.13)",

  shimmer1: "rgba(243,235,255,0.9)",
  shimmer2: "rgba(233,216,253,0.9)",
  shimmer3: "rgba(243,235,255,0.9)",

  cardShadow: "0 4px 24px rgba(109,40,217,0.10), 0 1px 0 rgba(255,255,255,0.80) inset",

  statusBar: "dark-content",
  isDark: false,
};

interface ThemeCtx {
  mode: ThemeMode;
  C: ThemeColors;
  setMode: (m: ThemeMode) => void;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeCtx>({
  mode: "dark", C: DARK,
  setMode: () => {}, toggle: () => {},
});

const STORAGE_KEY = "cl_theme";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [mode, _setMode] = useState<ThemeMode>("dark");

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

  const C = mode === "dark" ? DARK : LIGHT;

  return (
    <ThemeContext.Provider value={{ mode, C, setMode, toggle }}>
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
