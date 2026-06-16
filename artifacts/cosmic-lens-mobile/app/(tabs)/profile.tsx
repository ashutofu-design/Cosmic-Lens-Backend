import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Alert, Linking, Platform, Pressable,
  ScrollView, StatusBar, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC, useTheme } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { APP_LANG_CODES, coerceUILang, getT, type UILang } from "@/lib/i18n";
import { useT } from "@/hooks/useT";

// ── Font aliases ───────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

// ── Profile labels (full 25-lang via i18n) ────────────────────────────────────
type VLang = "en" | "hn" | "hi";
function vLangFromCode(code: string): VLang {
  return coerceUILang(code);
}
function getProfileLabels(t: ReturnType<typeof import('@/hooks/useT').useT>) {
  return {
    active:      t.pr_active,
    free:        t.pr_free,
    freePlan:    t.pr_freePlan,
    myData:      t.pr_myData,
    myKundli:    t.pr_myKundli,
    saved:       t.pr_saved,
    perYear:     t.pr_perYear,
    perMonth:    t.pr_perMonth,
  };
}

// ── Languages ─────────────────────────────────────────────────────────────────
type LangItem = { code: string; native: string; name: string };

const APP_LANGS: LangItem[] = [
  { code: "en", native: "English",  name: "English"  },
  { code: "hn", native: "Hinglish", name: "Hinglish" },
  { code: "hi", native: "हिंदी",    name: "Hindi"    },
];

// ── Plans ─────────────────────────────────────────────────────────────────────
type BillingCycle = "monthly" | "yearly";

const PLANS = [
  {
    key: "free", name: "Free",
    accent: "#64748b", accentBg: "rgba(71,85,105,0.08)",
    border: "rgba(71,85,105,0.22)", badge: null,
    monthlyPrice: 0, yearlyPrice: 0,
    cta: "Current Plan", ctaActive: false,
    icon: "circle" as const,
    features: ["1 Profile","Basic Kundli Chart","3 Jyotish Questions / day","Demo Insights","Basic Planet View"],
    featureOff: ["Full Dasha Timeline","7-Day Forecast","PDF Report","Kundli Milan"],
  },
  {
    key: "pro", name: "Pro",
    accent: "#f59e0b", accentBg: "rgba(245,158,11,0.05)",
    border: "rgba(245,158,11,0.30)", badge: "POPULAR",
    monthlyPrice: 149, yearlyPrice: 999, yearlySave: 44,
    cta: "Get Pro", ctaActive: true,
    icon: "zap" as const,
    features: ["5 Profiles","Full Kundli + Dasha Timeline","Unlimited Jyotish Chat","7-Day Forecast","Planet Positions + Nakshatra","Monthly Category Insights"],
    featureOff: ["PDF Report","Kundli Milan"],
  },
  {
    key: "elite", name: "Elite",
    accent: "#a78bfa", accentBg: "rgba(167,139,250,0.05)",
    border: "rgba(167,139,250,0.30)", badge: "PREMIUM",
    monthlyPrice: 399, yearlyPrice: 2999, yearlySave: 37,
    cta: "Get Elite", ctaActive: true,
    icon: "star" as const,
    features: ["Unlimited Profiles","All Pro Features","Monthly PDF Report","Kundli Milan (Vivah Yog)","Career & Finance Deep Analysis","Priority Astrologer Chat","Yearly Forecast"],
    featureOff: [],
  },
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

// ── Plan Card ─────────────────────────────────────────────────────────────────
function PlanCard({ plan, cycle, isCurrent, onPress }: {
  plan: typeof PLANS[0]; cycle: BillingCycle;
  isCurrent: boolean; onPress: ()=>void;
}) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vLangFromCode(language);
  const t = useT();
  const L = getProfileLabels(t);
  const price = cycle === "yearly" ? plan.yearlyPrice : plan.monthlyPrice;
  const isFree = plan.key === "free";

  return (
    <View style={[
      pl.card,
      { borderColor: plan.border, backgroundColor: plan.accentBg },
      isCurrent && pl.cardCurrent,
    ]}>
      {/* Top row */}
      <View style={{ flexDirection:"row", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
        <View style={{ flexDirection:"row", alignItems:"center", gap:8 }}>
          <View style={[pl.iconWrap, { backgroundColor:`${plan.accent}18`, borderColor:`${plan.accent}30` }]}>
            <Feather name={plan.icon} size={14} color={plan.accent} />
          </View>
          <Text style={[pl.planName, { color: plan.accent }]}>{plan.name}</Text>
          {isCurrent && (
            <View style={[pl.badge, { backgroundColor:`${plan.accent}20`, borderColor:`${plan.accent}40` }]}>
              <Text style={[pl.badgeText, { color: plan.accent }]}>{L.active}</Text>
            </View>
          )}
        </View>
        {plan.badge && !isCurrent && (
          <View style={[pl.badge, { backgroundColor:`${plan.accent}15`, borderColor:`${plan.accent}35` }]}>
            <Text style={[pl.badgeText, { color: plan.accent }]}>{plan.badge}</Text>
          </View>
        )}
      </View>

      {/* Price */}
      <View style={{ flexDirection:"row", alignItems:"flex-end", gap:3, marginBottom:6 }}>
        {isFree ? (
          <Text style={[pl.price, { color: plan.accent }]}>{L.free}</Text>
        ) : (
          <>
            <Text style={[pl.priceCurrency, { color: plan.accent }]}>₹</Text>
            <Text style={[pl.price, { color: plan.accent }]}>{price.toLocaleString("en-IN")}</Text>
            <Text style={[pl.pricePer, { color: C.textMuted }]}>/{cycle === "yearly" ? L.perYear : L.perMonth}</Text>
          </>
        )}
      </View>

      {/* Save pill */}
      {cycle === "yearly" && !isFree && (plan as any).yearlySave && (
        <View style={pl.savePill}>
          <Feather name="tag" size={9} color="#4ade80" />
          <Text style={pl.saveText}>Save {(plan as any).yearlySave}% vs monthly</Text>
        </View>
      )}

      <View style={[pl.sep, { backgroundColor:`${plan.accent}18` }]} />

      {/* Features */}
      <View style={{ gap:7, marginBottom:14 }}>
        {plan.features.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor:`${plan.accent}22` }]}>
              <Feather name="check" size={9} color={plan.accent} />
            </View>
            <Text style={[pl.featureText, { color: C.textMid }]}>{f}</Text>
          </View>
        ))}
        {plan.featureOff.map(f => (
          <View key={f} style={pl.featureRow}>
            <View style={[pl.featureDot, { backgroundColor: C.bgCard2 }]}>
              <Feather name="minus" size={9} color={C.textDim} />
            </View>
            <Text style={[pl.featureText, { color: C.textDim }]}>{f}</Text>
          </View>
        ))}
      </View>

      {/* CTA */}
      {plan.ctaActive ? (
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onPress(); }}
          style={({ pressed }) => [{ opacity: pressed ? 0.8 : 1 }]}
        >
          <LinearGradient
            colors={plan.key==="pro" ? ["#d97706","#f59e0b"] : ["#7c3aed","#a78bfa"]}
            start={{x:0,y:0}} end={{x:1,y:0}}
            style={pl.ctaBtn}
          >
            <Feather name={plan.icon} size={14} color="#fff" />
            <Text style={pl.ctaBtnText}>{plan.cta}</Text>
          </LinearGradient>
        </Pressable>
      ) : (
        <View style={[pl.ctaBtnOutline, { borderColor:`${plan.accent}30` }]}>
          <Feather name="check-circle" size={14} color={plan.accent} />
          <Text style={[pl.ctaBtnText, { color: plan.accent }]}>{plan.cta}</Text>
        </View>
      )}
    </View>
  );
}

// ── Settings Row ──────────────────────────────────────────────────────────────
function SettingRow({ icon, label, right, onPress, last = false }: {
  icon: React.ComponentProps<typeof Feather>["name"];
  label: string;
  right?: React.ReactNode;
  onPress?: () => void;
  last?: boolean;
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
        <View style={[st.iconCircle,{ backgroundColor: C.bgCard2 }]}>
          <Feather name={icon} size={14} color={C.textMuted} />
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
  const v: VLang = vLangFromCode(language);
  const t = useT();
  const L = getProfileLabels(t);

  const [showLang, setShowLang] = useState(false);

  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0];
  const initials = (primaryProfile?.name ?? "U")
    .split(" ").map(w=>w[0]??"").join("").slice(0,2).toUpperCase();
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
          colors={C.isDark ? ["#040e20","#071525"] : ["#F8F7FC","#F0EDF8"]}
          style={[s.header,{ borderColor: C.border }]}
        >
          <Text style={[s.headerBgStar, { color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>✦</Text>
          <Text style={[s.headerBgStar, { right:30, top:12, fontSize:14, opacity:0.04, color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>✦</Text>

          <LinearGradient colors={C.isDark ? ["#0ea5e9","#f59e0b"] : ["#7C3AED","#a78bfa"]} style={s.headerAvatar}>
            <Text style={s.headerInitials}>{initials}</Text>
          </LinearGradient>

          <View style={{ alignItems:"center", gap:4 }}>
            <View style={s.nameIdRow}>
              <Text style={[s.headerName,{ color: C.text }]}>{primaryProfile?.name ?? "User"}</Text>
              {cosmoId ? (
                <View style={[s.userIdBadge, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
                  <Text style={[s.userIdText, { color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{cosmoId}</Text>
                </View>
              ) : null}
            </View>
            <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.medium }}>
              {profiles.length} profile{profiles.length!==1?"s":""} · {primaryProfile?.birthData.place ?? ""}
            </Text>
          </View>

          <View style={[s.planBadge,{ backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Feather name="circle" size={9} color={C.textMuted} />
            <Text style={{ color: C.textMuted, fontSize: 9.5, fontFamily: F.bold, letterSpacing: 1 }}>{L.freePlan}</Text>
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

            <SettingRow
              icon="award"
              label={t.settingSubscription}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/subscription"); }}
              right={<Feather name="chevron-right" size={14} color={C.textDim} />}
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
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/about"); }}
            />
            <SettingRow
              icon="message-circle"
              label={t.settingHelp}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); Linking.openURL("mailto:support@cosmiclens.app"); }}
            />
            <SettingRow
              icon="share-2"
              label={t.settingShareApp}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
              last
            />
          </View>
        </View>
        </FadeInView>

        {/* ── APP VERSION + LOGOUT ─────────────────────────────────────── */}
        <FadeInView delay={staggerDelay(3)}>
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
    borderRadius:20, borderWidth:1, borderColor:"rgba(0,200,255,0.08)",
    paddingVertical:24, paddingHorizontal:16,
    alignItems:"center", gap:10, overflow:"hidden",
  },
  headerBgStar: {
    position:"absolute", left:20, top:18,
    fontSize:22, color:"#f59e0b", opacity:0.05,
  },
  headerAvatar: {
    width:68, height:68, borderRadius:34,
    alignItems:"center", justifyContent:"center",
    shadowColor:"#f59e0b", shadowOpacity:0.5, shadowRadius:12, shadowOffset:{width:0,height:0},
  },
  headerInitials: { color:"#fff", fontSize:22, fontFamily:F.bold },
  nameIdRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    flexWrap: "wrap",
    paddingHorizontal: 8,
  },
  headerName: { color:"#dde8f4", fontSize:18, fontFamily:F.bold, letterSpacing:-0.4 },
  userIdBadge: {
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 3,
    paddingHorizontal: 8,
  },
  userIdText: { fontSize: 11, fontFamily: F.bold, letterSpacing: 0.6 },
  headerSub: { color:"#1e3a5f", fontSize:11, fontFamily:F.medium },

  planBadge: {
    flexDirection:"row", alignItems:"center", gap:7,
    backgroundColor:"rgba(255,255,255,0.04)",
    borderWidth:1, borderColor:"rgba(255,255,255,0.07)",
    borderRadius:20, paddingVertical:6, paddingHorizontal:12,
  },
  planBadgeText: { color:"#475569", fontSize:9.5, fontFamily:F.bold, letterSpacing:1 },
  planDivider:   { width:1, height:10, backgroundColor:"rgba(255,255,255,0.08)" },
  planUpgrade:   { color:"#f59e0b", fontSize:10, fontFamily:F.semibold },

  sectionLabel: { fontSize:10, fontFamily:F.bold, letterSpacing:2.2 },

  currentPlanBanner: {
    flexDirection:"row", alignItems:"center", gap:12,
    borderRadius:16, borderWidth:1, borderColor:"rgba(100,116,139,0.15)",
    padding:16,
  },
  freeDot: {
    width:7, height:7, borderRadius:3.5, backgroundColor:"#475569",
  },
  currentPlanName: { color:"#94a3b8", fontSize:13, fontFamily:F.semibold },
  currentPlanSub:  { color:"#1e3a5f", fontSize:10.5, fontFamily:F.regular },
  upgradeBtn:      {},
  upgradeBtnGrad: {
    flexDirection:"row", alignItems:"center", gap:5,
    paddingVertical:8, paddingHorizontal:14, borderRadius:10,
  },
  upgradeBtnText: { color:"#fff", fontSize:12, fontFamily:F.bold },

  bottomSection: { alignItems:"center", gap:14 },
  versionText:   { color:"#0f1c2e", fontSize:10, fontFamily:F.medium },
  logoutBtn: {
    flexDirection:"row", alignItems:"center", gap:8,
    paddingVertical:12, paddingHorizontal:24,
    backgroundColor:"rgba(248,113,113,0.07)",
    borderWidth:1, borderColor:"rgba(248,113,113,0.15)",
    borderRadius:14,
  },
  logoutText: { color:"#f87171", fontSize:14, fontFamily:F.semibold },
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

// ── Subscription ──────────────────────────────────────────────────────────────
const sb = StyleSheet.create({
  cycleRow: {
    flexDirection:"row",
    backgroundColor:"#040e1f",
    borderRadius:12, borderWidth:1, borderColor:"rgba(255,255,255,0.06)",
    padding:4, gap:4,
  },
  cycleBtn: {
    flex:1, flexDirection:"row", alignItems:"center", justifyContent:"center",
    gap:7, paddingVertical:10, borderRadius:9,
  },
  cycleBtnActive: {
    backgroundColor:"rgba(245,158,11,0.1)",
    borderWidth:1, borderColor:"rgba(245,158,11,0.25)",
  },
  cycleTxt: { color:"#334155", fontSize:13, fontFamily:F.semibold },
  cycleTxtActive: { color:"#f59e0b" },
  savePill: {
    backgroundColor:"rgba(74,222,128,0.15)", borderRadius:6,
    paddingVertical:2, paddingHorizontal:6,
  },
  savePillTxt: { color:"#4ade80", fontSize:9, fontFamily:F.bold, letterSpacing:0.5 },
});

// ── Plan card ─────────────────────────────────────────────────────────────────
const pl = StyleSheet.create({
  card: {
    borderRadius:16, borderWidth:1.5,
    padding:16,
  },
  cardCurrent: { borderWidth:1 },
  iconWrap: {
    width:28, height:28, borderRadius:8,
    borderWidth:1, alignItems:"center", justifyContent:"center",
  },
  planName:    { fontSize:16, fontFamily:F.bold, letterSpacing:-0.2 },
  badge: {
    borderWidth:1, borderRadius:20,
    paddingVertical:2, paddingHorizontal:8,
  },
  badgeText: { fontSize:8.5, fontFamily:F.bold, letterSpacing:0.8 },
  price:         { fontSize:26, fontFamily:F.bold, lineHeight:30 },
  priceCurrency: { fontSize:15, fontFamily:F.bold, paddingBottom:3 },
  pricePer:      { color:"#334155", fontSize:12, fontFamily:F.medium, paddingBottom:4 },
  savePill: {
    flexDirection:"row", alignItems:"center", gap:5,
    backgroundColor:"rgba(74,222,128,0.1)", borderRadius:6,
    paddingVertical:3, paddingHorizontal:8, alignSelf:"flex-start",
  },
  saveText: { color:"#4ade80", fontSize:10, fontFamily:F.semibold },
  sep: { height:1, marginVertical:14 },
  featureRow: { flexDirection:"row", alignItems:"center", gap:8 },
  featureDot: {
    width:18, height:18, borderRadius:5,
    alignItems:"center", justifyContent:"center",
  },
  featureText: { color:"#94a3b8", fontSize:12, fontFamily:F.medium, flex:1 },
  ctaBtn: {
    flexDirection:"row", alignItems:"center", justifyContent:"center",
    gap:7, paddingVertical:12, borderRadius:12,
  },
  ctaBtnOutline: {
    flexDirection:"row", alignItems:"center", justifyContent:"center",
    gap:7, paddingVertical:12, borderRadius:12,
    borderWidth:1, backgroundColor:"rgba(255,255,255,0.03)",
  },
  ctaBtnText: { color:"#fff", fontSize:14, fontFamily:F.bold },
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

// ── Subscription card ─────────────────────────────────────────────────────────
const sub = StyleSheet.create({
  card: {
    marginTop: 12,
    backgroundColor: "#040e1e",
    borderRadius: 16, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)",
    overflow: "hidden",
  },
  planRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingHorizontal: 16, paddingVertical: 14,
  },
  planDotWrap: {
    width: 32, height: 32, borderRadius: 9,
    backgroundColor: "rgba(100,116,139,0.12)",
    borderWidth: 1, borderColor: "rgba(100,116,139,0.2)",
    alignItems: "center", justifyContent: "center",
  },
  freeDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: "#475569" },
  planName: { color: "#94a3b8", fontSize: 13, fontFamily: F.semibold },
  planSub:  { color: "#1e3a5f", fontSize: 10.5, fontFamily: F.regular, marginTop: 2 },
  upgradePill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingVertical: 6, paddingHorizontal: 12, borderRadius: 20,
  },
  upgradeText: { color: "#fff", fontSize: 11.5, fontFamily: F.bold },
  divider: { height: 1, backgroundColor: "rgba(255,255,255,0.05)", marginHorizontal: 0 },
  expandedWrap: { paddingHorizontal: 14, paddingBottom: 16, paddingTop: 14, gap: 0 },
});


