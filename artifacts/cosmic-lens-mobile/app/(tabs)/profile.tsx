import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  Alert, Platform, Pressable,
  ScrollView, StatusBar, StyleSheet, Text, View,
} from "react-native";
import Animated, {
  Easing,
  interpolate,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withTiming,
} from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC, useTheme } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { coerceUILang } from "@/lib/i18n";
import { useT } from "@/hooks/useT";

// ── Font aliases ───────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

// ── Languages ─────────────────────────────────────────────────────────────────
type LangItem = { code: string; native: string; name: string };

const APP_LANGS: LangItem[] = [
  { code: "en", native: "English",  name: "English"  },
  { code: "hn", native: "Hinglish", name: "Hinglish" },
  { code: "hi", native: "हिंदी",    name: "Hindi"    },
];

// ── Language Picker — inline floating (same screen) ───────────────────────────
function LangFloatingPicker({
  open,
  current,
  onToggle,
  onSelect,
}: {
  open: boolean;
  current: string;
  onToggle: () => void;
  onSelect: (code: string) => void;
}) {
  const C = useC();
  const t = useT();
  const accent = C.isDark ? "#f59e0b" : "#7C3AED";
  const currentLang = coerceUILang(current);

  function pick(code: string) {
    onSelect(code);
    if (open) onToggle();
  }

  return (
    <View>
      <Pressable
        onPress={onToggle}
        style={({ pressed }) => [st.row, pressed && { backgroundColor: C.bgCard2 }]}
      >
        <View style={[st.iconCircle, { backgroundColor: C.bgCard2 }]}>
          <Feather name="globe" size={14} color={C.textMuted} />
        </View>
        <Text style={[st.label, { flex: 1, color: C.text }]}>{t.language}</Text>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <View style={{ alignItems: "flex-end" }}>
            <Text style={{ color: accent, fontSize: 13, fontFamily: F.semibold }}>
              {APP_LANGS.find(l => l.code === currentLang)?.native ?? "English"}
            </Text>
            <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium }}>
              {APP_LANGS.find(l => l.code === currentLang)?.name ?? "English"}
            </Text>
          </View>
          <Feather name={open ? "chevron-up" : "chevron-down"} size={14} color={C.textDim} />
        </View>
      </Pressable>

      {open && (
        <View
          style={[
            lm.floatPanel,
            {
              backgroundColor: C.bgCard2,
              borderColor: C.border,
              shadowColor: C.isDark ? "#000" : "#7C3AED",
            },
          ]}
        >
          <Text style={[lm.floatLabel, { color: C.textMuted }]}>{t.selectLanguage}</Text>
          <View style={lm.tabRow}>
            {APP_LANGS.map(l => {
              const active = l.code === currentLang;
              return (
                <Pressable
                  key={l.code}
                  onPress={() => pick(l.code)}
                  style={({ pressed }) => [
                    lm.tab,
                    {
                      backgroundColor: active ? `${accent}18` : C.bgCard,
                      borderColor: active ? accent : C.border,
                    },
                    pressed && { opacity: 0.85 },
                  ]}
                >
                  <Text style={[lm.tabNative, { color: active ? accent : C.text }]}>{l.native}</Text>
                  <Text style={[lm.tabEn, { color: C.textMuted }]}>{l.name}</Text>
                  {active && (
                    <View style={[lm.tabCheck, { backgroundColor: accent }]}>
                      <Feather name="check" size={9} color="#020d1a" />
                    </View>
                  )}
                </Pressable>
              );
            })}
          </View>
        </View>
      )}
    </View>
  );
}

// ── Motion helpers (profile hero) ─────────────────────────────────────────────
/** Slow twinkling star for the header background. */
function TwinkleStar({ style, size = 16, delay = 0, color = "#fde68a" }: {
  style?: any; size?: number; delay?: number; color?: string;
}) {
  const p = useSharedValue(0);
  useEffect(() => {
    p.value = withDelay(
      delay,
      withRepeat(
        withTiming(1, { duration: 1800, easing: Easing.inOut(Easing.ease) }),
        -1,
        true,
      ),
    );
  }, [p, delay]);
  const anim = useAnimatedStyle(() => ({
    opacity: interpolate(p.value, [0, 1], [0.12, 0.5]),
    transform: [{ scale: interpolate(p.value, [0, 1], [0.85, 1.12]) }],
  }));
  return (
    <Animated.Text style={[{ position: "absolute", fontSize: size, color }, style, anim]}>
      ✦
    </Animated.Text>
  );
}

/** Diagonal light sweep that glides across the hero every few seconds. */
function HeroSheen() {
  const x = useSharedValue(-1);
  useEffect(() => {
    x.value = withRepeat(
      withSequence(
        withTiming(1.4, { duration: 2600, easing: Easing.inOut(Easing.ease) }),
        withDelay(1800, withTiming(-1, { duration: 0 })),
      ),
      -1,
      false,
    );
  }, [x]);
  const anim = useAnimatedStyle(() => ({
    transform: [
      { translateX: interpolate(x.value, [-1, 1.4], [-260, 420]) },
      { rotate: "18deg" },
    ],
  }));
  return (
    <Animated.View pointerEvents="none" style={[sheen.bar, anim]}>
      <LinearGradient
        colors={["transparent", "rgba(255,255,255,0.10)", "transparent"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
        style={{ flex: 1 }}
      />
    </Animated.View>
  );
}

const sheen = StyleSheet.create({
  bar: {
    position: "absolute",
    top: -40, bottom: -40,
    width: 90,
  },
});

// ── Settings Row ──────────────────────────────────────────────────────────────
function SettingRow({ icon, label, right, onPress, last = false, accent }: {
  icon: React.ComponentProps<typeof Feather>["name"];
  label: string;
  right?: React.ReactNode;
  onPress?: () => void;
  last?: boolean;
  accent?: string;
}) {
  const C = useC();
  const Wrap = onPress ? Pressable : View;
  return (
    <>
      <Wrap
        onPress={onPress}
        style={({ pressed }: any) => [
          st.row, onPress && pressed && { backgroundColor: C.bgCard2 },
        ]}
      >
        <View style={[st.iconCircle,{ backgroundColor: accent ? `${accent}16` : C.bgCard2 }]}>
          <Feather name={icon} size={14} color={accent ?? C.textMuted} />
        </View>
        <Text style={[st.label, { flex:1, color: C.text }]}>{label}</Text>
        {right ?? <Feather name="chevron-right" size={15} color={C.textDim} />}
      </Wrap>
      {!last && <View style={[st.divider,{ backgroundColor: C.border }]} />}
    </>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const { C } = useTheme();
  const {
    user, profiles, primaryProfileId,
    language, setLanguage,
    logout,
  } = useUser();
  const t = useT();

  const [showLang, setShowLang] = useState(false);

  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0];
  const cosmoId = (user?.cosmo_user_id || "").trim();

  function handleLogout() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    logout();
    router.replace("/login");
  }

  return (
    <CosmicBg>

      <ScrollView
        contentContainerStyle={{
          paddingTop: topPad + 8,
          paddingBottom: botPad + 90,
          paddingHorizontal: 16,
          gap: 20,
        }}
        showsVerticalScrollIndicator={false}
      >

        {/* ── USER HEADER ──────────────────────────────────────────────── */}
        <FadeInView delay={0}>
        <LinearGradient
          colors={
            C.isDark
              ? ["#0b1026", "#1a1033", "#0a1628"]
              : ["#4c1d95", "#6d28d9", "#3b0764"]
          }
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={s.header}
        >
          <HeroSheen />
          <TwinkleStar style={{ left: 20, top: 16 }} size={20} delay={0} />
          <TwinkleStar style={{ right: 26, top: 24 }} size={13} delay={600} />
          <TwinkleStar style={{ left: 42, bottom: 20 }} size={11} delay={1100} color="#c4b5fd" />
          <TwinkleStar style={{ right: 52, bottom: 34 }} size={16} delay={300} color="#c4b5fd" />

          <View style={s.nameIdRow}>
            <Text style={s.headerName}>{primaryProfile?.name ?? "User"}</Text>
            {cosmoId ? (
              <View style={s.userIdBadge}>
                <Text style={s.userIdText}>{cosmoId}</Text>
              </View>
            ) : null}
          </View>
        </LinearGradient>
        </FadeInView>

        {/* ── SETTINGS ─────────────────────────────────────────────────── */}
        <FadeInView delay={staggerDelay(1)}>
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{t.settings.toUpperCase()}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>

            <SettingRow
              icon="edit-3"
              label={t.settingEditProfile}
              accent={C.isDark ? "#f59e0b" : "#7C3AED"}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/profile-edit"); }}
              right={
                <View style={{ flexDirection:"row", alignItems:"center", gap:6 }}>
                  <Text style={{ color:C.textMuted, fontSize:11, fontFamily:F.medium }}>
                    {profiles.length} {t.profilesCount}
                  </Text>
                  <Feather name="chevron-right" size={14} color={C.textDim} />
                </View>
              }
            />

            <LangFloatingPicker
              open={showLang}
              current={language}
              onToggle={() => setShowLang(v => !v)}
              onSelect={code => {
                setLanguage(coerceUILang(code));
                Haptics.selectionAsync().catch(() => {});
              }}
            />
            <View style={[st.divider, { backgroundColor: C.border }]} />

          </View>
        </View>
        </FadeInView>

        {/* ── SUPPORT ──────────────────────────────────────────────────── */}
        <FadeInView delay={staggerDelay(2)}>
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{t.sectionSupport}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <SettingRow
              icon="info"
              label={t.settingAbout}
              accent="#60a5fa"
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/about"); }}
            />
            <SettingRow
              icon="package"
              label={t.settingCosmicPacks}
              accent="#fbbf24"
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                router.push("/cosmic-packs");
              }}
              right={<Feather name="chevron-right" size={14} color={C.textDim} />}
              last
            />
          </View>
        </View>
        </FadeInView>

        {/* ── REFER AND EARN (between Cosmic Packs & Help) ─────────────── */}
        <FadeInView delay={staggerDelay(3)}>
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{t.sectionReferEarn}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <SettingRow
              icon="gift"
              label={t.settingReferEarn}
              accent="#f472b6"
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                router.push("/refer-earn" as any);
              }}
              right={<Feather name="chevron-right" size={14} color={C.textDim} />}
              last
            />
          </View>
        </View>
        </FadeInView>

        {/* ── HELP ─────────────────────────────────────────────────────── */}
        <FadeInView delay={staggerDelay(4)}>
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{t.sectionHelp}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <SettingRow
              icon="message-circle"
              label={t.settingHelp}
              accent="#34d399"
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                router.push("/help-support");
              }}
            />
            <SettingRow
              icon="share-2"
              label={t.settingShareApp}
              accent="#a78bfa"
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
              last
            />
          </View>
        </View>
        </FadeInView>

        {/* ── APP VERSION + LOGOUT ─────────────────────────────────────── */}
        <FadeInView delay={staggerDelay(5)}>
        <View style={[s.bottomSection, { marginTop: 8 }]}>
          <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium }}>{t.prof_madeWith}</Text>

          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
              if (Platform.OS === "web") {
                // RN Web's Alert with 3 buttons does not fire the destructive onPress reliably.
                // Use the browser's native confirm() instead.
                // eslint-disable-next-line no-alert
                const ok = typeof window !== "undefined" && window.confirm(t.logoutConfirm);
                if (ok) handleLogout();
              } else {
                Alert.alert(t.logoutTitle, t.logoutConfirm, [
                  { text: t.cancel, style:"cancel" },
                  { text: t.logoutCta, style:"destructive", onPress: handleLogout },
                ]);
              }
            }}
            style={({ pressed }) => [s.logoutBtn, pressed && { opacity:0.75 }]}
          >
            <Feather name="log-out" size={14} color="#f87171" />
            <Text style={s.logoutText}>{t.logOut}</Text>
          </Pressable>
        </View>
        </FadeInView>

      </ScrollView>
    </CosmicBg>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  header: {
    borderRadius: 24,
    paddingVertical: 22,
    paddingHorizontal: 16,
    alignItems: "center",
    gap: 0,
    overflow: "hidden",
  },
  nameIdRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    flexWrap: "wrap",
    paddingHorizontal: 8,
  },
  headerName: { color: "#fff", fontSize: 20, fontFamily: F.bold, letterSpacing: -0.3 },
  userIdBadge: {
    backgroundColor: "rgba(255,255,255,0.16)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.22)",
    borderRadius: 8,
    paddingVertical: 3,
    paddingHorizontal: 8,
  },
  userIdText: { color: "#fde68a", fontSize: 11, fontFamily: F.bold, letterSpacing: 0.6 },

  sectionLabel: { fontSize: 10, fontFamily: F.bold, letterSpacing: 2.2, marginBottom: 8 },

  currentPlanBanner: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 16, borderWidth: 1, borderColor: "rgba(100,116,139,0.15)",
    padding: 16,
  },
  freeDot: {
    width: 7, height: 7, borderRadius: 3.5, backgroundColor: "#475569",
  },
  currentPlanName: { color: "#94a3b8", fontSize: 13, fontFamily: F.semibold },
  currentPlanSub: { color: "#1e3a5f", fontSize: 10.5, fontFamily: F.regular },
  upgradeBtn: {},
  upgradeBtnGrad: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingVertical: 8, paddingHorizontal: 14, borderRadius: 10,
  },
  upgradeBtnText: { color: "#fff", fontSize: 12, fontFamily: F.bold },

  bottomSection: { alignItems: "center", gap: 14 },
  versionText: { color: "#0f1c2e", fontSize: 10, fontFamily: F.medium },
  logoutBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 12, paddingHorizontal: 24,
    backgroundColor: "rgba(248,113,113,0.07)",
    borderWidth: 1, borderColor: "rgba(248,113,113,0.15)",
    borderRadius: 14,
  },
  logoutText: { color: "#f87171", fontSize: 14, fontFamily: F.semibold },
});

// ── Settings ──────────────────────────────────────────────────────────────────
const st = StyleSheet.create({
  card: {
    backgroundColor:"#040e20", borderRadius:16,
    borderWidth:1, borderColor:"rgba(255,255,255,0.05)", overflow:"hidden",
  },
  row: {
    flexDirection:"row", alignItems:"center", gap:12,
    paddingHorizontal:16, paddingVertical:13,
  },
  iconCircle: {
    width:30, height:30, borderRadius:8,
    backgroundColor:"rgba(255,255,255,0.04)",
    alignItems:"center", justifyContent:"center",
  },
  label:   { color:"#c5d5e8", fontSize:13.5, fontFamily:F.medium },
  divider: { height:1, backgroundColor:"rgba(255,255,255,0.04)", marginHorizontal:16 },
});

// ── Language floating picker ──────────────────────────────────────────────────
const lm = StyleSheet.create({
  floatPanel: {
    marginHorizontal: 12,
    marginBottom: 10,
    marginTop: 2,
    padding: 10,
    borderRadius: 14,
    borderWidth: 1,
    ...Platform.select({
      ios: {
        shadowOffset: { width: 0, height: 6 },
        shadowOpacity: 0.22,
        shadowRadius: 12,
      },
      android: { elevation: 8 },
      default: {},
    }),
  },
  floatLabel: {
    fontSize: 9,
    fontFamily: F.bold,
    letterSpacing: 1.4,
    marginBottom: 8,
    marginLeft: 2,
    textTransform: "uppercase",
  },
  tabRow: {
    flexDirection: "row",
    gap: 8,
  },
  tab: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    paddingVertical: 10,
    paddingHorizontal: 6,
    alignItems: "center",
    position: "relative",
  },
  tabNative: { fontSize: 13, fontFamily: F.semibold, marginBottom: 2 },
  tabEn: { fontSize: 9, fontFamily: F.medium },
  tabCheck: {
    position: "absolute",
    top: 5,
    right: 5,
    width: 14,
    height: 14,
    borderRadius: 7,
    alignItems: "center",
    justifyContent: "center",
  },
});


