// ══════════════════════════════════════════════════════════════════════════════
// useRTL — Lightweight hook exposing current RTL state + icon helpers.
// Components call this whenever they need to flip directional icons or
// conditionally tweak layout for right-to-left languages.
// ══════════════════════════════════════════════════════════════════════════════

import { I18nManager } from "react-native";

type FeatherDir = "chevron-left" | "chevron-right" | "arrow-left" | "arrow-right";

const FLIP_MAP: Record<FeatherDir, FeatherDir> = {
  "chevron-left":  "chevron-right",
  "chevron-right": "chevron-left",
  "arrow-left":    "arrow-right",
  "arrow-right":   "arrow-left",
};

/**
 * Returns:
 *   isRTL    — current layout direction
 *   flipIcon — helper that swaps directional Feather icon names when in RTL
 *   chev     — convenience: directional chevron pointing in NAV-FORWARD
 *              direction (right in LTR, left in RTL) — useful for "next" buttons
 *   chevBack — convenience: directional chevron pointing in NAV-BACK
 *              direction (left in LTR, right in RTL) — useful for back buttons
 */
export function useRTL() {
  const isRTL = I18nManager.isRTL;

  const flipIcon = (name: FeatherDir): FeatherDir => {
    if (!isRTL) return name;
    return FLIP_MAP[name] ?? name;
  };

  return {
    isRTL,
    flipIcon,
    chev:     isRTL ? "chevron-left"  : "chevron-right",
    chevBack: isRTL ? "chevron-right" : "chevron-left",
  } as const;
}
