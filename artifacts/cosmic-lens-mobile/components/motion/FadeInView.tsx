import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import { enterMotion, isNativeApp, skipEnterMotion } from "@/lib/nativeMotion";

type Props = {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  slide?: number;
  style?: StyleProp<ViewStyle>;
  /** Change to replay enter animation (e.g. tab/mode switch). */
  resetKey?: string | number;
};

/**
 * Enter fade/slide — uses RN Animated so it runs on iOS/Android without Reanimated worklets.
 */
export function FadeInView({
  children,
  delay = 0,
  duration = 480,
  slide = 14,
  style,
  resetKey,
}: Props) {
  const motion = enterMotion(duration, slide);
  const animDelay = skipEnterMotion(delay);
  const opacity = useRef(new Animated.Value(isNativeApp ? 1 : 0)).current;
  const translateY = useRef(new Animated.Value(isNativeApp ? 0 : slide)).current;

  useEffect(() => {
    if (isNativeApp && motion.duration <= 0) return;
    opacity.setValue(isNativeApp ? 0.92 : 0);
    translateY.setValue(isNativeApp ? motion.slide : slide);
    const anim = Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: motion.duration,
        delay: animDelay,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration: motion.duration,
        delay: animDelay,
        easing: Easing.out(Easing.quad),
        useNativeDriver: true,
      }),
    ]);
    anim.start();
    return () => anim.stop();
  }, [animDelay, motion.duration, motion.slide, resetKey, opacity, translateY, slide]);

  return (
    <Animated.View style={[{ opacity, transform: [{ translateY }] }, style]}>
      {children}
    </Animated.View>
  );
}

/** Stagger helper: `delay={staggerDelay(index, 70)}` */
export function staggerDelay(index: number, stepMs = 65, baseMs = 0): number {
  return skipEnterMotion(baseMs + index * stepMs);
}
