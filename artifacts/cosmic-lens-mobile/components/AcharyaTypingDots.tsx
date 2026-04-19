/**
 * AcharyaTypingDots — three dots that fade-pulse in sequence to convey
 * "Acharya ji is composing a reply". Replaces a plain ActivityIndicator
 * for a more chat-app-native feel (ChatGPT / Gemini / WhatsApp parity).
 */
import React, { useEffect } from "react";
import { StyleSheet, Text, View } from "react-native";
import Animated, {
  Easing,
  type SharedValue,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withTiming,
} from "react-native-reanimated";

import { useC } from "@/context/ThemeContext";

type Props = {
  caption?: string;          // e.g. "Acharya ji likh rahe hain..."
  size?: number;             // dot size, default 7
  color?: string;            // dot color, default theme.accent
};

export function AcharyaTypingDots({ caption, size = 7, color }: Props) {
  const C = useC();
  const dotColor = color || C.accent;

  const o1 = useSharedValue(0.25);
  const o2 = useSharedValue(0.25);
  const o3 = useSharedValue(0.25);

  useEffect(() => {
    const cfg = { duration: 420, easing: Easing.inOut(Easing.ease) };
    const loop = (sv: SharedValue<number>, delayMs: number) => {
      sv.value = withDelay(
        delayMs,
        withRepeat(
          withTiming(1, cfg, () => {
            sv.value = withTiming(0.25, cfg);
          }),
          -1,
          true,
        ),
      );
    };
    loop(o1, 0);
    loop(o2, 160);
    loop(o3, 320);
  }, [o1, o2, o3]);

  const a1 = useAnimatedStyle(() => ({ opacity: o1.value }));
  const a2 = useAnimatedStyle(() => ({ opacity: o2.value }));
  const a3 = useAnimatedStyle(() => ({ opacity: o3.value }));

  const dotStyle = {
    width: size,
    height: size,
    borderRadius: size / 2,
    backgroundColor: dotColor,
  };

  return (
    <View style={s.row}>
      <View style={s.dots}>
        <Animated.View style={[dotStyle, a1]} />
        <Animated.View style={[dotStyle, a2]} />
        <Animated.View style={[dotStyle, a3]} />
      </View>
      {caption ? (
        <Text style={[s.caption, { color: C.textMuted }]}>{caption}</Text>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  row:     { flexDirection: "row", alignItems: "center", gap: 8 },
  dots:    { flexDirection: "row", alignItems: "center", gap: 4, paddingVertical: 4 },
  caption: { fontSize: 12, fontStyle: "italic" },
});
