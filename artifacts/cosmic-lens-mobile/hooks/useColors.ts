import { useC } from "@/context/ThemeContext";

export function useColors() {
  const C = useC();
  return {
    background:      C.bg,
    card:            C.bgCard,
    foreground:      C.text,
    mutedForeground: C.textMid,
    muted:           C.bgCard2,
    border:          C.border,
    primary:         C.accent,
    primaryForeground: C.isDark ? "#020d1a" : "#ffffff",
    input:           C.inputBg,
    radius:          12,
    C,
  };
}
