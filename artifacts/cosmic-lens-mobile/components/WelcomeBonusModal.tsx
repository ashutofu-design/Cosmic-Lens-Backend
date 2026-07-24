/**
 * Top-of-screen gift-burst banner — new user won 3 free V1 questions.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type Props = {
  visible: boolean;
  isHindi?: boolean;
  onClose: () => void;
  onAskNow: () => void;
};

const SPARKLES = ["🎁", "✨", "🎉", "💫", "🌟", "🎊"] as const;

export function WelcomeBonusModal({
  visible,
  isHindi = false,
  onClose,
  onAskNow,
}: Props) {
  const insets = useSafeAreaInsets();
  const slideY = useRef(new Animated.Value(-220)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const burst = useRef(new Animated.Value(0)).current;
  const giftScale = useRef(new Animated.Value(0.4)).current;
  const sparkle = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!visible) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});

    slideY.setValue(-220);
    opacity.setValue(0);
    burst.setValue(0);
    giftScale.setValue(0.4);
    sparkle.setValue(0);

    Animated.sequence([
      Animated.parallel([
        Animated.spring(slideY, {
          toValue: 0,
          friction: 7,
          tension: 68,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 1,
          duration: 280,
          useNativeDriver: true,
        }),
      ]),
      Animated.parallel([
        Animated.spring(giftScale, {
          toValue: 1,
          friction: 3.2,
          tension: 110,
          useNativeDriver: true,
        }),
        Animated.timing(burst, {
          toValue: 1,
          duration: 600,
          easing: Easing.out(Easing.cubic),
          useNativeDriver: true,
        }),
      ]),
    ]).start();

    const sparkleLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(sparkle, {
          toValue: 1,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(sparkle, {
          toValue: 0,
          duration: 900,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ]),
    );
    sparkleLoop.start();

    return () => {
      sparkleLoop.stop();
    };
  }, [visible, slideY, opacity, burst, giftScale, sparkle]);

  const burstScale = burst.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 1.6],
  });
  const burstOpacity = burst.interpolate({
    inputRange: [0, 0.25, 1],
    outputRange: [0, 0.85, 0],
  });
  const sparkleOpacity = sparkle.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.35, 1, 0.35],
  });
  const sparkleY = sparkle.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -8],
  });

  const message = isHindi
    ? "Badhai ho! Aapne Cosmic Intelligence V1 ke 3 free questions jeete hain — abhi Ask me try karo."
    : "Congrats! You won 3 free Cosmic Intelligence V1 questions — try them in Ask now.";
  const chip = isHindi ? "3 FREE V1 QUESTIONS" : "3 FREE V1 QUESTIONS";
  const cta = isHindi ? "Abhi Pucho" : "Ask Now";
  const later = isHindi ? "Baad mein" : "Maybe later";

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={s.root} pointerEvents="box-none">
        <Pressable style={s.dim} onPress={onClose} />

        <Animated.View
          style={[
            s.bannerWrap,
            {
              paddingTop: Math.max(insets.top, 12) + 6,
              opacity,
              transform: [{ translateY: slideY }],
            },
          ]}
        >
          <LinearGradient
            colors={["#7c2d12", "#9a3412", "#b45309", "#ca8a04"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={s.banner}
          >
            {/* Gift rings + particles */}
            <View style={s.burstArea} pointerEvents="none">
              <Animated.View
                style={[
                  s.burstRing,
                  { opacity: burstOpacity, transform: [{ scale: burstScale }] },
                ]}
              />
              <Animated.View
                style={[
                  s.burstRingInner,
                  {
                    opacity: burstOpacity,
                    transform: [
                      {
                        scale: burst.interpolate({
                          inputRange: [0, 1],
                          outputRange: [0.22, 1.15],
                        }),
                      },
                    ],
                  },
                ]}
              />
              {SPARKLES.map((emoji, i) => {
                const angle = (i / SPARKLES.length) * Math.PI * 2;
                const r = 42;
                return (
                  <Animated.Text
                    key={`${emoji}-${i}`}
                    style={[
                      s.sparkle,
                      {
                        left: 48 + Math.cos(angle) * r - 8,
                        top: 48 + Math.sin(angle) * r - 8,
                        opacity: sparkleOpacity,
                        transform: [{ translateY: sparkleY }, { scale: giftScale }],
                      },
                    ]}
                  >
                    {emoji}
                  </Animated.Text>
                );
              })}
              <Animated.View style={{ transform: [{ scale: giftScale }] }}>
                <LinearGradient
                  colors={["#fde047", "#f59e0b", "#ea580c"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={s.giftBadge}
                >
                  <Feather name="gift" size={22} color="#fff" />
                  <Text style={s.giftNum}>3</Text>
                </LinearGradient>
              </Animated.View>
            </View>

            <View style={s.copy}>
              <Text style={s.kicker}>{isHindi ? "WELCOME GIFT" : "WELCOME GIFT"}</Text>
              <Text style={s.message}>{message}</Text>

              <View style={s.chip}>
                <Feather name="zap" size={12} color="#fef08a" />
                <Text style={s.chipText}>{chip}</Text>
              </View>

              <View style={s.actions}>
                <Pressable
                  onPress={onAskNow}
                  style={({ pressed }) => [{ flex: 1, opacity: pressed ? 0.88 : 1 }]}
                >
                  <LinearGradient
                    colors={["#fef08a", "#fbbf24", "#f59e0b"]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={s.primaryBtn}
                  >
                    <Feather name="message-circle" size={15} color="#7c2d12" />
                    <Text style={s.primaryBtnText}>{cta}</Text>
                  </LinearGradient>
                </Pressable>
                <Pressable
                  onPress={onClose}
                  style={({ pressed }) => [s.laterBtn, { opacity: pressed ? 0.7 : 1 }]}
                >
                  <Text style={s.laterText}>{later}</Text>
                </Pressable>
              </View>
            </View>
          </LinearGradient>
        </Animated.View>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  root: {
    flex: 1,
    justifyContent: "flex-start",
  },
  dim: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(2, 6, 23, 0.55)",
  },
  bannerWrap: {
    paddingHorizontal: 12,
    zIndex: 2,
  },
  banner: {
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: "rgba(253, 224, 71, 0.55)",
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 14,
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
    overflow: "hidden",
    shadowColor: "#f59e0b",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.45,
    shadowRadius: 20,
    elevation: 16,
  },
  burstArea: {
    width: 96,
    height: 96,
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
  },
  burstRing: {
    position: "absolute",
    width: 72,
    height: 72,
    borderRadius: 36,
    borderWidth: 2.5,
    borderColor: "#fde047",
  },
  burstRingInner: {
    position: "absolute",
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: "rgba(254, 243, 199, 0.7)",
  },
  sparkle: {
    position: "absolute",
    fontSize: 14,
  },
  giftBadge: {
    width: 58,
    height: 58,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.5)",
    gap: 0,
  },
  giftNum: {
    fontSize: 16,
    fontWeight: "900",
    color: "#fff",
    marginTop: -2,
    letterSpacing: -0.5,
  },
  copy: { flex: 1, minWidth: 0, paddingTop: 2 },
  kicker: {
    fontSize: 10,
    fontWeight: "800",
    color: "#fef08a",
    letterSpacing: 1.8,
    marginBottom: 2,
  },
  title: {
    fontSize: 20,
    fontWeight: "900",
    color: "#fff",
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  message: {
    fontSize: 12.5,
    lineHeight: 17.5,
    color: "rgba(255,255,255,0.92)",
    marginBottom: 8,
  },
  chip: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "rgba(0,0,0,0.22)",
    borderColor: "rgba(254, 243, 199, 0.45)",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 10,
  },
  chipText: {
    color: "#fef9c3",
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  actions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  primaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    borderRadius: 12,
    paddingVertical: 11,
    paddingHorizontal: 12,
  },
  primaryBtnText: {
    color: "#7c2d12",
    fontSize: 14,
    fontWeight: "900",
  },
  laterBtn: {
    paddingVertical: 10,
    paddingHorizontal: 8,
  },
  laterText: {
    color: "rgba(255,255,255,0.75)",
    fontSize: 12.5,
    fontWeight: "600",
  },
});
