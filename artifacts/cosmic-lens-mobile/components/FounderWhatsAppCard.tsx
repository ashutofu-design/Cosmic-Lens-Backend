import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";

type Props = {
  /** e.g. close drawer before navigating */
  onBeforeOpen?: () => void;
  /** Override default navigate (e.g. close drawer then push) */
  onPress?: () => void;
};

/** Talk to Founder — opens contact page (Instagram, YouTube, WhatsApp). */
export function FounderWhatsAppCard({ onBeforeOpen, onPress }: Props) {
  const C = useC();

  function handlePress() {
    try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    if (onPress) {
      onPress();
      return;
    }
    onBeforeOpen?.();
    router.push("/talk-to-founder" as any);
  }

  return (
    <Pressable
      onPress={handlePress}
      style={({ pressed }) => [
        s.card,
        { borderColor: "#25D36640", backgroundColor: C.bgCard },
        pressed && { opacity: 0.85, transform: [{ scale: 0.98 }] },
      ]}
    >
      <View style={[s.glow, { backgroundColor: "#25D36612" }]} />
      <View style={[s.iconWrap, { backgroundColor: "#25D36620", borderColor: "#25D36655" }]}>
        <Text style={{ fontSize: 24 }}>💬</Text>
      </View>
      <View style={{ flex: 1 }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Text style={[s.title, { color: C.text }]}>Talk to Founder</Text>
          <View style={s.badge}>
            <Text style={s.badgeText}>FREE</Text>
          </View>
        </View>
        <Text style={[s.sub, { color: C.textMuted }]}>
          Instagram, YouTube ya WhatsApp par connect karein
        </Text>
      </View>
      <View style={[s.arrow, { backgroundColor: "#25D366" }]}>
        <Feather name="chevron-right" size={14} color="#fff" />
      </View>
    </Pressable>
  );
}

const s = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1.5,
    overflow: "hidden",
    position: "relative",
  },
  glow: {
    position: "absolute",
    top: -20,
    right: -20,
    width: 80,
    height: 80,
    borderRadius: 40,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  title: { fontSize: 15, fontFamily: "Nunito_700Bold", letterSpacing: -0.2 },
  sub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 2, lineHeight: 15 },
  badge: {
    backgroundColor: "#25D366",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  badgeText: {
    color: "#fff",
    fontSize: 8,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 0.8,
  },
  arrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
});
