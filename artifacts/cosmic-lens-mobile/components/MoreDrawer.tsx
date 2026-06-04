import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from "react";
import {
  Animated,
  Easing,
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
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { drawerStagger, SlideInFromRight } from "@/components/motion/SlideInFromRight";
import { ScalePressable } from "@/components/motion/ScalePressable";
import { useC } from "@/context/ThemeContext";

import { useT } from "@/hooks/useT";
import { buildMoreDrawerCategories } from "@/lib/moreMenuData";

const DRAWER_W = 320;
const OPEN_OVERLAY_MS = 340;
const CLOSE_MS = 280;
const CONTENT_BASE_MS = 120;
const CONTENT_STEP_MS = 100;
const CONTENT_DURATION = 520;
const CONTENT_SLIDE = 80;
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

  const CATEGORIES = buildMoreDrawerCategories(t) as { title: string; items: FeatureItem[] }[];
  const insets = useSafeAreaInsets();
  const slideX = useRef(new Animated.Value(DRAWER_W)).current;
  const overlayOp = useRef(new Animated.Value(0)).current;
  const closingRef = useRef(false);
  const [animKey, setAnimKey] = useState(0);

  useEffect(() => {
    if (visible) {
      closingRef.current = false;
      setAnimKey(k => k + 1);
      slideX.setValue(0);
      overlayOp.setValue(0);
      Animated.timing(overlayOp, {
        toValue: 1,
        duration: OPEN_OVERLAY_MS,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();
    } else if (!closingRef.current) {
      Animated.parallel([
        Animated.timing(slideX, {
          toValue: DRAWER_W,
          duration: CLOSE_MS,
          easing: Easing.in(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(overlayOp, {
          toValue: 0,
          duration: CLOSE_MS,
          easing: Easing.in(Easing.quad),
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, overlayOp, slideX]);

  function closeDrawer(onDone?: () => void) {
    if (closingRef.current) return;
    closingRef.current = true;
    Animated.parallel([
      Animated.timing(slideX, {
        toValue: DRAWER_W,
        duration: CLOSE_MS,
        easing: Easing.in(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(overlayOp, {
        toValue: 0,
        duration: CLOSE_MS,
        easing: Easing.in(Easing.quad),
        useNativeDriver: true,
      }),
    ]).start(({ finished }) => {
      onClose();
      if (finished) onDone?.();
    });
  }

  useImperativeHandle(ref, () => ({ close: closeDrawer }));

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
        <Animated.View style={[s.overlay, { opacity: overlayOp }]}>
          {Platform.OS === "ios" ? (
            <BlurView intensity={28} tint="dark" style={StyleSheet.absoluteFill} />
          ) : null}
          <Pressable style={StyleSheet.absoluteFill} onPress={() => closeDrawer()} />
        </Animated.View>

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
          <SlideInFromRight
            active={visible}
            resetKey={animKey}
            delay={drawerStagger(0, CONTENT_STEP_MS, CONTENT_BASE_MS)}
            duration={CONTENT_DURATION}
            slide={44}
            style={s.header}
          >
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
          </SlideInFromRight>

          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 20, gap: 22 }}
          >
            {/* ── Talk to Founder (WhatsApp) ───────────────────────────── */}
            <SlideInFromRight
              active={visible}
              resetKey={animKey}
              delay={drawerStagger(1, CONTENT_STEP_MS, CONTENT_BASE_MS)}
              duration={CONTENT_DURATION}
              slide={CONTENT_SLIDE}
            >
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
            </SlideInFromRight>

            {CATEGORIES.map((cat, catIdx) => {
              const accent = cat.items[0]?.accent ?? "#a78bfa";
              return (
                <SlideInFromRight
                  key={cat.title}
                  active={visible}
                  resetKey={animKey}
                  delay={drawerStagger(catIdx + 2, CONTENT_STEP_MS, CONTENT_BASE_MS)}
                  duration={CONTENT_DURATION}
                  slide={CONTENT_SLIDE}
                >
                <View>
                  <Text style={[s.catLabel, { color: accent }]}>{cat.title}</Text>
                  <View
                    style={[
                      s.catCard,
                      {
                        backgroundColor: "#2a3358",
                        borderColor: `${accent}44`,
                        shadowColor: accent,
                        shadowOpacity: 0.22,
                        shadowRadius: 12,
                        shadowOffset: { width: 0, height: 4 },
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
                </SlideInFromRight>
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
    backgroundColor: Platform.OS === "ios" ? "rgba(0,0,0,0.35)" : "rgba(0,0,0,0.55)",
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
