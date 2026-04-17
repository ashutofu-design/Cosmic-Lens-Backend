import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useEffect, useRef } from "react";
import {
  Animated, Linking, Modal, Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

const DRAWER_W = 320;
const FOUNDER_WHATSAPP = "919040524394";
const FOUNDER_MSG = "Namaste 🙏 Main Cosmic Lens app se aa raha hu. Mujhe apni kundli / rashifal ke baare mein aapse personally baat karni hai.";

type FeatureItem = {
  id: string;
  icon: string;
  emoji: string;
  title: string;
  subtitle: string;
  route: string;
  accent: string;
  badge?: string;
};

export default function MoreDrawer({
  visible, onClose,
}: { visible: boolean; onClose: () => void }) {
  const C = useC();
  const t = useT();

  const CATEGORIES: { title: string; items: FeatureItem[] }[] = [
    {
      title: t.catRashifal,
      items: [
        { id: "lucky",     icon: "star",       emoji: "🍀", title: t.mdLuckyTitle,     subtitle: t.mdLuckySub,     route: "/lucky",        accent: "#22c55e" },
      ],
    },
    {
      title: t.catPanchang,
      items: [
        { id: "panchang",  icon: "clock",       emoji: "🗓️", title: t.mdPanchangTitle, subtitle: t.mdPanchangSub,  route: "/panchang",     accent: "#a78bfa" },
      ],
    },
    {
      title: t.catMuhurat,
      items: [
        { id: "muhurat",   icon: "check-circle",emoji: "✅", title: t.mdMuhuratTitle,   subtitle: t.mdMuhuratSub,  route: "/muhurat",      accent: "#10b981" },
      ],
    },
    {
      title: t.catNumerology,
      items: [
        { id: "numerology",icon: "hash",        emoji: "🔢", title: t.mdNumerologyTitle,subtitle: t.mdNumerologySub,route: "/numerology",  accent: "#8b5cf6" },
      ],
    },
    {
      title: t.catRemedies,
      items: [
        { id: "remedies",  icon: "zap",         emoji: "⚡", title: t.mdRemediesTitle,  subtitle: t.mdRemediesSub, route: "/remedies",     accent: "#f59e0b" },
      ],
    },
    {
      title: t.catVastu,
      items: [
        { id: "vastu",     icon: "home",        emoji: "🏠", title: t.mdVastuTitle,     subtitle: t.mdVastuSub,    route: "/vastu",        accent: "#06b6d4" },
      ],
    },
  ];
  const insets = useSafeAreaInsets();
  const slideX = useRef(new Animated.Value(DRAWER_W)).current;
  const overlayOp = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(slideX, { toValue: 0, useNativeDriver: true, speed: 18, bounciness: 0 }),
        Animated.timing(overlayOp, { toValue: 1, duration: 220, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.spring(slideX, { toValue: DRAWER_W, useNativeDriver: true, speed: 22, bounciness: 0 }),
        Animated.timing(overlayOp, { toValue: 0, duration: 180, useNativeDriver: true }),
      ]).start();
    }
  }, [visible]);

  function navigate(route: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onClose();
    setTimeout(() => router.push(route as any), 200);
  }

  async function openFounderWhatsApp() {
    try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch {}
    const msg = encodeURIComponent(FOUNDER_MSG);
    const webUrl = `https://wa.me/${FOUNDER_WHATSAPP}?text=${msg}`;
    const appUrl = `whatsapp://send?phone=${FOUNDER_WHATSAPP}&text=${msg}`;

    if (Platform.OS === "web") {
      if (typeof window !== "undefined") {
        window.open(webUrl, "_blank");
      }
      return;
    }

    try {
      const canOpen = await Linking.canOpenURL(appUrl);
      if (canOpen) {
        await Linking.openURL(appUrl);
        return;
      }
    } catch {}
    try { await Linking.openURL(webUrl); } catch {}
  }

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <View style={s.root}>
        {/* Overlay */}
        <Animated.View style={[s.overlay, { opacity: overlayOp }]}>
          <Pressable style={StyleSheet.absoluteFill} onPress={onClose} />
        </Animated.View>

        {/* Drawer panel */}
        <Animated.View
          style={[
            s.drawer,
            {
              backgroundColor: C.bg,
              borderLeftColor: C.border,
              paddingTop: insets.top + 8,
              paddingBottom: insets.bottom + 16,
              transform: [{ translateX: slideX }],
            },
          ]}
        >
          {/* Header */}
          <View style={s.header}>
            <View>
              <Text style={[s.headerTitle, { color: C.text }]}>{t.moreExplore}</Text>
              <Text style={[s.headerSub, { color: C.textMuted }]}>{t.moreSubtitle}</Text>
            </View>
            <Pressable
              onPress={onClose}
              style={[s.closeBtn, { backgroundColor: C.bgCard2, borderColor: C.border }]}
            >
              <Feather name="x" size={16} color={C.textMuted} />
            </Pressable>
          </View>

          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 20, gap: 22 }}
          >
            {/* ── Talk to Founder (WhatsApp) ───────────────────────────── */}
            <Pressable
              onPress={openFounderWhatsApp}
              style={({ pressed }) => [
                s.founderCard,
                { borderColor: "#25D36640", backgroundColor: C.bgCard },
                pressed && { opacity: 0.85, transform: [{ scale: 0.98 }] },
              ]}
            >
              <View style={[s.founderGlow, { backgroundColor: "#25D36612" }]} />
              <View style={[s.founderIconWrap, { backgroundColor: "#25D36620", borderColor: "#25D36655" }]}>
                <Text style={{ fontSize: 24 }}>💬</Text>
              </View>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <Text style={[s.founderTitle, { color: C.text }]}>Talk to Founder</Text>
                  <View style={s.founderBadge}>
                    <Text style={s.founderBadgeText}>FREE</Text>
                  </View>
                </View>
                <Text style={[s.founderSub, { color: C.textMuted }]}>
                  Personally apni kundli dikhani hai? WhatsApp par chat karein
                </Text>
              </View>
              <View style={[s.founderArrow, { backgroundColor: "#25D366" }]}>
                <Feather name="message-circle" size={14} color="#fff" />
              </View>
            </Pressable>

            {CATEGORIES.map(cat => (
              <View key={cat.title}>
                <Text style={[s.catLabel, { color: C.textMuted }]}>{cat.title}</Text>
                <View style={[s.catCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  {cat.items.map((item, idx) => (
                    <Pressable
                      key={item.id}
                      onPress={() => navigate(item.route)}
                      style={({ pressed }) => [
                        s.item,
                        idx < cat.items.length - 1 && [s.itemBorder, { borderBottomColor: C.border3 }],
                        pressed && { opacity: 0.7 },
                      ]}
                    >
                      <View style={[s.iconCircle, { backgroundColor: `${item.accent}18` }]}>
                        <Text style={{ fontSize: 18 }}>{item.emoji}</Text>
                      </View>
                      <View style={s.itemText}>
                        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                          <Text style={[s.itemTitle, { color: C.text }]}>{item.title}</Text>
                          {item.badge && (
                            <View style={[s.badge, { backgroundColor: `${item.accent}20`, borderColor: `${item.accent}40` }]}>
                              <Text style={[s.badgeText, { color: item.accent }]}>{item.badge}</Text>
                            </View>
                          )}
                        </View>
                        <Text style={[s.itemSub, { color: C.textMuted }]}>{item.subtitle}</Text>
                      </View>
                      <Feather name="chevron-right" size={14} color={C.textDim} />
                    </Pressable>
                  ))}
                </View>
              </View>
            ))}
          </ScrollView>
        </Animated.View>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, flexDirection: "row", justifyContent: "flex-end" },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.55)",
  },
  drawer: {
    width: DRAWER_W,
    height: "100%",
    borderLeftWidth: 1,
    borderLeftColor: "rgba(255,255,255,0.06)",
  },
  header: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20, paddingVertical: 14,
  },
  headerTitle: { fontSize: 20, fontFamily: "Nunito_700Bold", letterSpacing: -0.3 },
  headerSub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  closeBtn: {
    width: 32, height: 32, borderRadius: 16,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  catLabel: {
    fontSize: 10, fontFamily: "Nunito_700Bold",
    letterSpacing: 1.5, marginBottom: 8, marginLeft: 2,
  },
  catCard: {
    borderRadius: 14, borderWidth: 1, overflow: "hidden",
  },
  item: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 14, paddingVertical: 13,
  },
  itemBorder: { borderBottomWidth: 1 },
  iconCircle: {
    width: 40, height: 40, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
  },
  itemText: { flex: 1 },
  itemTitle: { fontSize: 14, fontFamily: "Nunito_600SemiBold" },
  itemSub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  badge: {
    paddingHorizontal: 6, paddingVertical: 1.5,
    borderRadius: 8, borderWidth: 1,
  },
  badgeText: { fontSize: 8, fontFamily: "Nunito_700Bold", letterSpacing: 0.5 },

  founderCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 14,
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    position: "relative",
  },
  founderGlow: {
    position: "absolute",
    top: -20, right: -20,
    width: 120, height: 120,
    borderRadius: 60,
  },
  founderIconWrap: {
    width: 48, height: 48, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },
  founderTitle: { fontSize: 15, fontFamily: "Nunito_700Bold", letterSpacing: -0.2 },
  founderSub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 2, lineHeight: 15 },
  founderBadge: {
    backgroundColor: "#25D36625",
    borderWidth: 1, borderColor: "#25D36660",
    paddingHorizontal: 6, paddingVertical: 1.5,
    borderRadius: 6,
  },
  founderBadgeText: {
    fontSize: 8, fontFamily: "Nunito_700Bold",
    color: "#25D366", letterSpacing: 0.8,
  },
  founderArrow: {
    width: 30, height: 30, borderRadius: 15,
    alignItems: "center", justifyContent: "center",
  },
});
