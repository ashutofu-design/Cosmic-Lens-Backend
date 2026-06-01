import * as Haptics from "expo-haptics";
import React from "react";
import {
  Pressable,
  type PressableProps,
  type StyleProp,
  type ViewStyle,
} from "react-native";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
} from "react-native-reanimated";

type Props = PressableProps & {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  haptic?: "light" | "medium" | "none";
};

export function ScalePressable({
  children,
  style,
  onPress,
  onPressIn,
  onPressOut,
  disabled,
  haptic = "light",
  ...rest
}: Props) {
  const scale = useSharedValue(1);

  const animStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <Pressable
      {...rest}
      disabled={disabled}
      onPressIn={(e) => {
        scale.value = withTiming(0.97, { duration: 70 });
        onPressIn?.(e);
      }}
      onPressOut={(e) => {
        scale.value = withSpring(1, { damping: 16, stiffness: 280 });
        onPressOut?.(e);
      }}
      onPress={(e) => {
        if (!disabled && haptic !== "none") {
          Haptics.impactAsync(
            haptic === "medium"
              ? Haptics.ImpactFeedbackStyle.Medium
              : Haptics.ImpactFeedbackStyle.Light,
          ).catch(() => {});
        }
        onPress?.(e);
      }}
    >
      <Animated.View style={[animStyle, style]}>{children}</Animated.View>
    </Pressable>
  );
}
