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

export const DARK: ThemeColors = {
  bg:      "#020d1a",
  bgCard:  "#040e1e",
  bgCard2: "#071525",
  bgCard3: "#0a1f35",
  text:      "#dde8f4",
  textMid:   "#94a3b8",
  textMuted: "#475569",
  textDim:   "#1e3a5f",
  accent:    "#00d4ff",
  accentBg:  "rgba(0,212,255,0.08)",
  border:  "rgba(255,255,255,0.06)",
  border2: "rgba(255,255,255,0.10)",
  border3: "rgba(255,255,255,0.04)",
  switchTrackOff: "#0f1c2e",
  navBg:     "#040e1e",
  navBorder: "rgba(255,255,255,0.06)",
  inputBg:   "#040e1e",
  inputBorder: "rgba(255,255,255,0.08)",
  shimmer1: "#040e1e",
  shimmer2: "#071525",
  shimmer3: "#040e1e",
  statusBar: "light-content",
  isDark: true,
};

export const LIGHT: ThemeColors = {
  bg:      "#f0f4ff",
  bgCard:  "#ffffff",
  bgCard2: "#f8faff",
  bgCard3: "#edf2fb",
  text:      "#0f172a",
  textMid:   "#475569",
  textMuted: "#94a3b8",
  textDim:   "#cbd5e1",
  accent:    "#0284c7",
  accentBg:  "rgba(2,132,199,0.08)",
  border:  "rgba(0,0,0,0.07)",
  border2: "rgba(0,0,0,0.12)",
  border3: "rgba(0,0,0,0.04)",
  switchTrackOff: "#e2e8f0",
  navBg:     "#ffffff",
  navBorder: "rgba(0,0,0,0.06)",
  inputBg:   "#ffffff",
  inputBorder: "rgba(0,0,0,0.10)",
  shimmer1: "#f0f4ff",
  shimmer2: "#e2eaf8",
  shimmer3: "#f0f4ff",
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
