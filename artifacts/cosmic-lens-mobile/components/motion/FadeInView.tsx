import React, { useEffect } from "react";
import { type StyleProp, type ViewStyle } from "react-native";
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withTiming,
} from "react-native-reanimated";

type Props = {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  slide?: number;
  style?: StyleProp<ViewStyle>;
  /** Change to replay enter animation (e.g. tab/mode switch). */
  resetKey?: string | number;
};

export function FadeInView({
  children,
  delay = 0,
  duration = 480,
  slide = 14,
  style,
  resetKey,
}: Props) {
  const opacity = useSharedValue(0);
  const translateY = useSharedValue(slide);

  useEffect(() => {
    opacity.value = 0;
    translateY.value = slide;
    opacity.value = withDelay(
      delay,
      withTiming(1, { duration, easing: Easing.out(Easing.cubic) }),
    );
    translateY.value = withDelay(
      delay,
      withTiming(0, { duration: duration + 40, easing: Easing.out(Easing.cubic) }),
    );
  }, [delay, duration, slide, resetKey, opacity, translateY]);

  const animStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: translateY.value }],
  }));

  return <Animated.View style={[animStyle, style]}>{children}</Animated.View>;
}

/** Stagger helper: `delay={staggerDelay(index, 70)}` */
export function staggerDelay(index: number, stepMs = 65, baseMs = 0): number {
  return baseMs + index * stepMs;
}
