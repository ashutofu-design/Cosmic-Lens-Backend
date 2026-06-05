import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useMemo, useRef } from "react";
import {
  I18nManager,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Animated, {
  Easing,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ScalePressable } from "@/components/motion/ScalePressable";
import { useC } from "@/context/ThemeContext";

import { useT } from "@/hooks/useT";
import { buildMoreDrawerCategories } from "@/lib/moreMenuData";

const DRAWER_W = 320;
/** UI-thread slide — smooth 60fps, not sluggish. */
const OPEN_MS = 480;
const CLOSE_MS = 340;
const EASE_OPEN  = Easing.bezier(0.22, 1, 0.36, 1);
const EASE_CLOSE = Easing.bezier(0.4, 0, 1, 1);
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

export type MoreDrawerHandle = {
  close: (onDone?: () => void) => void;
};

export default forwardRef<MoreDrawerHandle, { visible: boolean; onClose: () => void }>(function MoreDrawer({
  visible, onClose,
}, ref) {
  const C = useC();
  const t = useT();

  const CATEGORIES = useMemo(
    () => buildMoreDrawerCategories(t) as { title: string; items: FeatureItem[] }[],
    [t],
  );
  const insets = useSafeAreaInsets();
  const progress = useSharedValue(0);
  const closingRef = useRef(false);

  const finishClose = useCallback((onDone?: () => void) => {
    onClose();
    onDone?.();
  }, [onClose]);

  const overlayStyle = useAnimatedStyle(() => ({
    opacity: progress.value,
  }));

  const drawerStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: DRAWER_W * (1 - progress.value) }],
  }));

  useEffect(() => {
    if (visible) {
      closingRef.current = false;
      progress.value = withTiming(1, { duration: OPEN_MS, easing: EASE_OPEN });
    } else if (!closingRef.current) {
      progress.value = withTiming(0, { duration: CLOSE_MS, easing: EASE_CLOSE });
    }
  }, [visible, progress]);

  const closeDrawer = useCallback((onDone?: () => void) => {
    if (closingRef.current) return;
    closingRef.current = true;
    progress.value = withTiming(
      0,
      { duration: CLOSE_MS, easing: EASE_CLOSE },
      (finished) => {
        if (finished) runOnJS(finishClose)(onDone);
      },
    );
  }, [progress, finishClose]);

  useImperativeHandle(ref, () => ({ close: closeDrawer }), [closeDrawer]);

  function navigate(route: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    closeDrawer(() => {
      const q = route.indexOf("?");
      if (q >= 0) {
        const pathname = route.slice(0, q);
        const params = Object.fromEntries(new URLSearchParams(route.slice(q + 1)));
        router.push({ pathname: pathname as any, params } as any);
      } else {
        router.push(route as any);
      }
    });
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
    <Modal visible={visible} transparent animationType="none" onRequestClose={() => closeDrawer()}>
      <View style={s.root}>
        <Animated.View style={[s.overlay, overlayStyle]}>
          <Pressable style={StyleSheet.absoluteFill} onPress={() => closeDrawer()} />
        </Animated.View>

        <Animated.View
          style={[
            s.drawer,
            drawerStyle,
            {
              backgroundColor: C.bg,
              borderLeftColor: C.border,
              paddingTop: insets.top + 8,
              paddingBottom: insets.bottom + 16,
            },
          ]}
        >
          <View style={s.header}>
            <View>
              <Text style={[s.headerTitle, { color: C.text }]}>More</Text>
              <Text style={[s.headerSub, { color: C.textMuted }]}>{t.moreSubtitle}</Text>
            </View>
            <ScalePressable
              haptic="light"
              onPress={() => closeDrawer()}
              style={[s.closeBtn, { backgroundColor: C.bgCard2, borderColor: C.border }]}
            >
              <Feather name="x" size={16} color={C.textMuted} />
            </ScalePressable>
          </View>

          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 20, gap: 22 }}
          >
            {/* ── Talk to Founder (WhatsApp) ───────────────────────────── */}
            <ScalePressable
              haptic="medium"
              onPress={openFounderWhatsApp}
              style={[s.founderCard, { borderColor: "#25D36640", backgroundColor: C.bgCard }]}
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
            </ScalePressable>

            {CATEGORIES.map((cat) => {
              const accent = cat.items[0]?.accent ?? "#a78bfa";
              return (
                <View key={cat.title}>
                  <Text style={[s.catLabel, { color: accent }]}>{cat.title}</Text>
                  <View
                    style={[
                      s.catCard,
                      {
                        backgroundColor: "#2a3358",
                        borderColor: `${accent}44`,
                        elevation: 2,
                      },
                    ]}
                  >
                    <View
                      pointerEvents="none"
                      style={[
                        StyleSheet.absoluteFillObject,
                        { backgroundColor: `${accent}10`, borderRadius: 14 },
                      ]}
                    />
                    {cat.items.map((item, idx) => (
                      <ScalePressable
                        key={item.id}
                        haptic="none"
                        onPress={() => navigate(item.route)}
                        style={[
                          s.item,
                          idx < cat.items.length - 1 && [
                            s.itemBorder,
                            { borderBottomColor: `${accent}22` },
                          ],
                        ]}
                      >
                        <View style={[s.iconCircle, { backgroundColor: `${item.accent}28`, borderWidth: 1, borderColor: `${item.accent}55` }]}>
                          <Text style={{ fontSize: 18 }}>{item.emoji}</Text>
                        </View>
                        <View style={s.itemText}>
                          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                            <Text style={[s.itemTitle, { color: "#f5f6ff" }]}>{item.title}</Text>
                            {item.badge && (
                              <View style={[s.badge, { backgroundColor: `${item.accent}25`, borderColor: `${item.accent}55` }]}>
                                <Text style={[s.badgeText, { color: item.accent }]}>{item.badge}</Text>
                              </View>
                            )}
                          </View>
                          <Text style={[s.itemSub, { color: "#9aa3c7" }]}>{item.subtitle}</Text>
                        </View>
                        <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={14} color={`${accent}99`} />
                      </ScalePressable>
                    ))}
                  </View>
                </View>
              );
            })}
          </ScrollView>
        </Animated.View>
      </View>
    </Modal>
  );
});

const s = StyleSheet.create({
  root: { flex: 1, flexDirection: "row", justifyContent: "flex-end" },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.52)",
  },
  drawer: {
    width: DRAWER_W,
    height: "100%",
    borderLeftWidth: 1,
    borderLeftColor: "rgba(255,255,255,0.06)",
    overflow: "hidden",
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
