/**
 * OrderSuccessModal — premium centered "order confirmed" overlay.
 *
 * Animated check badge + soft glow + trust chips. Used after a founder-review
 * order (e.g. AstroVastu room photo) is submitted, so the user clearly feels
 * the booking is confirmed and knows where the report will arrive.
 */
import { Feather } from "@expo/vector-icons";
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

type Props = {
  visible: boolean;
  onClose: () => void;
  onViewReports?: () => void;
  title?: string;
  message?: string;
  etaLabel?: string;
};

export function OrderSuccessModal({
  visible,
  onClose,
  onViewReports,
  title = "Order Confirmed!",
  message = "Your room photo has been received. Our Vastu expert is personally reviewing it.",
  etaLabel = "Report in My Reports within 24–48 hrs",
}: Props) {
  const cardScale = useRef(new Animated.Value(0.8)).current;
  const cardOpacity = useRef(new Animated.Value(0)).current;
  const checkScale = useRef(new Animated.Value(0)).current;
  const ringPulse = useRef(new Animated.Value(0)).current;
  const sparkle = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!visible) return;
    cardScale.setValue(0.8);
    cardOpacity.setValue(0);
    checkScale.setValue(0);
    ringPulse.setValue(0);
    sparkle.setValue(0);

    Animated.sequence([
      Animated.parallel([
        Animated.spring(cardScale, {
          toValue: 1,
          friction: 7,
          tension: 60,
          useNativeDriver: true,
        }),
        Animated.timing(cardOpacity, {
          toValue: 1,
          duration: 220,
          useNativeDriver: true,
        }),
      ]),
      Animated.spring(checkScale, {
        toValue: 1,
        friction: 4,
        tension: 90,
        useNativeDriver: true,
      }),
    ]).start();

    const pulse = Animated.loop(
      Animated.timing(ringPulse, {
        toValue: 1,
        duration: 1600,
        easing: Easing.out(Easing.ease),
        useNativeDriver: true,
      }),
    );
    pulse.start();

    const sparkleLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(sparkle, {
          toValue: 1,
          duration: 1400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(sparkle, {
          toValue: 0,
          duration: 1400,
          easing: Easing.inOut(Easing.ease),
          useNativeDriver: true,
        }),
      ]),
    );
    sparkleLoop.start();

    return () => {
      pulse.stop();
      sparkleLoop.stop();
    };
  }, [visible, cardScale, cardOpacity, checkScale, ringPulse, sparkle]);

  const ringScale = ringPulse.interpolate({
    inputRange: [0, 1],
    outputRange: [1, 1.9],
  });
  const ringOpacity = ringPulse.interpolate({
    inputRange: [0, 0.2, 1],
    outputRange: [0, 0.5, 0],
  });
  const sparkleUp = sparkle.interpolate({
    inputRange: [0, 1],
    outputRange: [0, -6],
  });
  const sparkleOpacity = sparkle.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.35, 1, 0.35],
  });

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={s.overlay}>
        <Animated.View
          style={[s.cardWrap, { opacity: cardOpacity, transform: [{ scale: cardScale }] }]}
        >
          <LinearGradient
            colors={["#241448", "#141031", "#0b0a1e"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={s.card}
          >
            {/* Floating sparkles */}
            <Animated.Text
              style={[s.sparkle, { top: 18, left: 22, opacity: sparkleOpacity, transform: [{ translateY: sparkleUp }] }]}
            >
              ✨
            </Animated.Text>
            <Animated.Text
              style={[s.sparkle, { top: 30, right: 26, opacity: sparkleOpacity, transform: [{ translateY: sparkleUp }] }]}
            >
              🌟
            </Animated.Text>
            <Animated.Text
              style={[s.sparkle, { bottom: 92, left: 30, opacity: sparkleOpacity, transform: [{ translateY: sparkleUp }] }]}
            >
              ✨
            </Animated.Text>

            {/* Animated check badge */}
            <View style={s.badgeWrap}>
              <Animated.View
                style={[s.badgeRing, { opacity: ringOpacity, transform: [{ scale: ringScale }] }]}
              />
              <Animated.View style={{ transform: [{ scale: checkScale }] }}>
                <LinearGradient
                  colors={["#34d399", "#10b981", "#059669"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={s.badge}
                >
                  <Feather name="check" size={40} color="#ffffff" />
                </LinearGradient>
              </Animated.View>
            </View>

            <Text style={s.title}>{title}</Text>
            <Text style={s.message}>{message}</Text>

            {/* ETA chip */}
            <View style={s.etaChip}>
              <Feather name="clock" size={13} color="#fbbf24" />
              <Text style={s.etaText}>{etaLabel}</Text>
            </View>

            {/* Trust row */}
            <View style={s.trustRow}>
              {[
                { icon: "shield" as const, label: "Secure" },
                { icon: "award" as const, label: "Expert reviewed" },
                { icon: "file-text" as const, label: "PDF report" },
              ].map((tItem) => (
                <View key={tItem.label} style={s.trustChip}>
                  <Feather name={tItem.icon} size={11} color="#a78bfa" />
                  <Text style={s.trustText}>{tItem.label}</Text>
                </View>
              ))}
            </View>

            {onViewReports ? (
              <Pressable
                onPress={onViewReports}
                style={({ pressed }) => [{ opacity: pressed ? 0.88 : 1, width: "100%" }]}
              >
                <LinearGradient
                  colors={["#7c3aed", "#a855f7", "#c084fc"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={s.primaryBtn}
                >
                  <Feather name="folder" size={16} color="#fff" />
                  <Text style={s.primaryBtnText}>Track in My Reports</Text>
                </LinearGradient>
              </Pressable>
            ) : null}

            <Pressable
              onPress={onClose}
              style={({ pressed }) => [s.closeBtn, { opacity: pressed ? 0.7 : 1 }]}
            >
              <Text style={s.closeBtnText}>Done</Text>
            </Pressable>
          </LinearGradient>
        </Animated.View>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(2,2,10,0.72)",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  cardWrap: {
    width: "100%",
    maxWidth: 360,
    borderRadius: 26,
    shadowColor: "#a855f7",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.45,
    shadowRadius: 32,
    elevation: 16,
  },
  card: {
    borderRadius: 26,
    borderWidth: 1,
    borderColor: "rgba(168,85,247,0.35)",
    paddingHorizontal: 24,
    paddingTop: 34,
    paddingBottom: 22,
    alignItems: "center",
    overflow: "hidden",
  },
  sparkle: { position: "absolute", fontSize: 16 },
  badgeWrap: {
    width: 96,
    height: 96,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  badgeRing: {
    position: "absolute",
    width: 78,
    height: 78,
    borderRadius: 39,
    backgroundColor: "#10b981",
  },
  badge: {
    width: 78,
    height: 78,
    borderRadius: 39,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.35)",
  },
  title: {
    fontSize: 23,
    fontWeight: "800",
    color: "#ffffff",
    letterSpacing: -0.3,
    marginBottom: 8,
    textAlign: "center",
  },
  message: {
    fontSize: 13.5,
    lineHeight: 20,
    color: "rgba(255,255,255,0.82)",
    textAlign: "center",
    marginBottom: 16,
  },
  etaChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "rgba(251,191,36,0.12)",
    borderColor: "rgba(251,191,36,0.45)",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginBottom: 14,
  },
  etaText: { color: "#fbbf24", fontSize: 12, fontWeight: "700" },
  trustRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 20,
    flexWrap: "wrap",
    justifyContent: "center",
  },
  trustChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    backgroundColor: "rgba(167,139,250,0.10)",
    borderColor: "rgba(167,139,250,0.35)",
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  trustText: { color: "#c4b5fd", fontSize: 11, fontWeight: "600" },
  primaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderRadius: 14,
    paddingVertical: 13,
    width: "100%",
  },
  primaryBtnText: { color: "#ffffff", fontSize: 15, fontWeight: "800" },
  closeBtn: { paddingVertical: 12, marginTop: 4 },
  closeBtnText: { color: "rgba(255,255,255,0.55)", fontSize: 13.5, fontWeight: "600" },
});
