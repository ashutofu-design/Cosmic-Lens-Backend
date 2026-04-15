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
  // Status bar style
  statusBar: "light-content" | "dark-content";
  isDark: boolean;
}

// ── Dark — Matte Black ─────────────────────────────────────────────────────────
export const DARK: ThemeColors = {
  bg:      "#141414",
  bgCard:  "#1f1f1f",
  bgCard2: "#262626",
  bgCard3: "#2e2e2e",

  text:      "#f0f0f0",
  textMid:   "#c8c8c8",
  textMuted: "#999999",
  textDim:   "#555555",

  accent:   "#f59e0b",
  accentBg: "rgba(245,158,11,0.13)",

  border:  "rgba(255,255,255,0.10)",
  border2: "rgba(255,255,255,0.18)",
  border3: "rgba(255,255,255,0.06)",

  switchTrackOff: "#262626",
  navBg:     "#141414",
  navBorder: "rgba(255,255,255,0.10)",
  inputBg:   "#1f1f1f",
  inputBorder: "rgba(255,255,255,0.16)",

  shimmer1: "#1f1f1f",
  shimmer2: "#262626",
  shimmer3: "#1f1f1f",

  statusBar: "light-content",
  isDark: true,
};

// ── Light — Warm Lavender + Amber Gold ────────────────────────────────────────
export const LIGHT: ThemeColors = {
  bg:      "#faf5ff",
  bgCard:  "#ffffff",
  bgCard2: "#f3ebff",
  bgCard3: "#ede0ff",

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

  shimmer1: "#f3ebff",
  shimmer2: "#e9d8fd",
  shimmer3: "#f3ebff",

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
