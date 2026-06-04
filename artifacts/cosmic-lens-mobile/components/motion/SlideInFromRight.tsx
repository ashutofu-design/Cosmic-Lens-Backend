import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  type StyleProp,
  type ViewStyle,
} from "react-native";

type Props = {
  children: React.ReactNode;
  /** ms before motion starts */
  delay?: number;
  duration?: number;
  /** start offset to the right (px) */
  slide?: number;
  style?: StyleProp<ViewStyle>;
  /** Change to replay enter animation */
  resetKey?: string | number;
  active?: boolean;
};

/**
 * Drawer row enter — slides in from the right and settles in place.
 * Full motion on device (not throttled like FadeInView).
 */
export function SlideInFromRight({
  children,
  delay = 0,
  duration = 460,
  slide = 68,
  style,
  resetKey,
  active = true,
}: Props) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateX = useRef(new Animated.Value(slide)).current;

  useEffect(() => {
    if (!active) {
      opacity.setValue(0);
      translateX.setValue(slide);
      return;
    }

    opacity.setValue(0);
    translateX.setValue(slide);

    const anim = Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration,
        delay,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(translateX, {
        toValue: 0,
        duration,
        delay,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]);

    anim.start();
    return () => anim.stop();
  }, [active, delay, duration, resetKey, slide, opacity, translateX]);

  return (
    <Animated.View style={[{ opacity, transform: [{ translateX }] }, style]}>
      {children}
    </Animated.View>
  );
}

/** Stagger helper for drawer rows */
export function drawerStagger(index: number, stepMs = 90, baseMs = 0): number {
  return baseMs + index * stepMs;
}
