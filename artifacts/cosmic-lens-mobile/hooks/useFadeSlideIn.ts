import { useEffect } from "react";
import {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withTiming,
} from "react-native-reanimated";

/** Reanimated enter style for legacy screens still using animated views inline. */
export function useFadeSlideIn(delay = 0, slide = 16) {
  const opacity = useSharedValue(0);
  const translateY = useSharedValue(slide);

  useEffect(() => {
    opacity.value = withDelay(
      delay,
      withTiming(1, { duration: 500, easing: Easing.out(Easing.cubic) }),
    );
    translateY.value = withDelay(
      delay,
      withTiming(0, { duration: 480, easing: Easing.out(Easing.cubic) }),
    );
  }, [delay, slide, opacity, translateY]);

  return useAnimatedStyle(() => ({
    opacity: opacity.value,
    transform: [{ translateY: translateY.value }],
  }));
}
