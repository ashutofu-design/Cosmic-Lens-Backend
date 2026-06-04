import { useMemo } from "react";
import { useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

/** Reference width (iPhone 14 / common Android). */
const REF_W = 390;

export type ScreenLayout = {
  width: number;
  height: number;
  /** Clamped 0.8–1.2 from screen width */
  scale: number;
  compact: boolean;
  narrow: boolean;
  ph: number;
  gap: number;
  padBottom: number;
  tabRowH: number;
  rs: (n: number) => number;
};

export function useScreenLayout(): ScreenLayout {
  const { width, height, fontScale } = useWindowDimensions();
  const insets = useSafeAreaInsets();

  return useMemo(() => {
    const scale = Math.min(Math.max(width / REF_W, 0.8), 1.2);
    const compact = width < 360;
    const narrow = width < 400;
    const fs = Math.min(fontScale, 1.12);
    const rs = (n: number) => Math.round(n * scale * fs);
    const ph = rs(compact ? 12 : narrow ? 14 : 16);
    const gap = rs(compact ? 10 : 12);
    const tabRowH = rs(compact ? 38 : 44);
    const padBottom = Math.max(insets.bottom, 8) + rs(compact ? 16 : 24);

    return {
      width,
      height,
      scale,
      compact,
      narrow,
      ph,
      gap,
      padBottom,
      tabRowH,
      rs,
    };
  }, [width, height, fontScale, insets.bottom]);
}
