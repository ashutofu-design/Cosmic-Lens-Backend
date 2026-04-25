import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import {
  Alert, Animated, Linking, Modal, Platform, Pressable,
  ScrollView, StatusBar, StyleSheet, Switch, Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC, useTheme } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT, INDIA_LANG_CODES, GLOBAL_LANG_CODES } from "@/lib/i18n";
import {
  sendTestNotification,
  setPushEnabled,
  setupPushForUser,
} from "@/lib/notifications";

// ── Font aliases ───────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

// ── Vedic-bucket labels (en/hn/hi) for hardcoded UI strings ───────────────────
type VLang = "en" | "hn" | "hi";
function vLangFromCode(code: string): VLang {
  if (code === "en") return "en";
  if (code === "hn") return "hn";
  return "hi";
}
function getProfileLabels(v: VLang) {
  const en = v === "en", hn = v === "hn";
  return {
    tabIndia:    en ? "India"     : hn ? "India"     : "भारत",
    tabGlobal:   en ? "Global"    : hn ? "Global"    : "विश्व",
    active:      en ? "ACTIVE"    : hn ? "ACTIVE"    : "सक्रिय",
    free:        en ? "FREE"      : hn ? "FREE"      : "निःशुल्क",
    freePlan:    en ? "FREE PLAN" : hn ? "FREE PLAN" : "निःशुल्क प्लान",
    myData:      en ? "MY DATA"   : hn ? "MY DATA"   : "मेरा डेटा",
    myKundli:    en ? "My Kundli" : hn ? "My Kundli" : "मेरी कुंडली",
    saved:       en ? "saved"     : hn ? "saved"     : "सहेजे गए",
    perYear:     en ? "year"      : hn ? "year"      : "वर्ष",
    perMonth:    en ? "month"     : hn ? "month"     : "माह",
  };
}

// ── Languages ─────────────────────────────────────────────────────────────────
type LangItem = { code: string; native: string; name: string };

const ALL_LANG_META: LangItem[] = [
  { code:"en",  native:"English",     name:"English"    },
  { code:"hn",  native:"Hinglish",    name:"Hinglish"   },
  { code:"hi",  native:"हिंदी",       name:"Hindi"      },
  { code:"bn",  native:"বাংলা",       name:"Bengali"    },
  { code:"mr",  native:"मराठी",       name:"Marathi"    },
  { code:"ta",  native:"தமிழ்",       name:"Tamil"      },
  { code:"te",  native:"తెలుగు",      name:"Telugu"     },
  { code:"gu",  native:"ગુજરાતી",    name:"Gujarati"   },
  { code:"kn",  native:"ಕನ್ನಡ",      name:"Kannada"    },
  { code:"ml",  native:"മലയാളം",      name:"Malayalam"  },
  { code:"or",  native:"ଓଡ଼ିଆ",       name:"Odia"       },
  { code:"pa",  native:"ਪੰਜਾਬੀ",     name:"Punjabi"    },
  { code:"as",  native:"অসমীয়া",     name:"Assamese"   },
  { code:"zh",  native:"中文",         name:"Chinese"    },
  { code:"es",  native:"Español",     name:"Spanish"    },
  { code:"ar",  native:"العربية",     name:"Arabic"     },
  { code:"fr",  native:"Français",    name:"French"     },
  { code:"pt",  native:"Português",   name:"Portuguese" },
  { code:"de",  native:"Deutsch",     name:"German"     },
  { code:"ru",  native:"Русский",     name:"Russian"    },
  { code:"ja",  native:"日本語",       name:"Japanese"   },
  { code:"id",  native:"Indonesia",   name:"Indonesian" },
  { code:"ko",  native:"한국어",       name:"Korean"     },
  { code:"tr",  native:"Türkçe",      name:"Turkish"    },
];

function getLangList(isIndia: boolean): LangItem[] {
  const codes = isIndia ? INDIA_LANG_CODES : GLOBAL_LANG_CODES;
  return (codes as readonly string[]).map(c => ALL_LANG_META.find(m => m.code === c)!).filter(Boolean);
}

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

// ── Animated row wrapper ──────────────────────────────────────────────────────
function PressRow({ onPress, style, children }: {
  onPress: () => void;
  style?: object;
  children: React.ReactNode;
}) {
  const sc = useRef(new Animated.Value(1)).current;
  function pressIn()  { Animated.spring(sc, { toValue:0.97, useNativeDriver:true, speed:40 }).start(); }
  function pressOut() { Animated.spring(sc, { toValue:1,    useNativeDriver:true, speed:40 }).start(); }

  return (
    <Pressable onPress={onPress} onPressIn={pressIn} onPressOut={pressOut}>
      <Animated.View style={[style, { transform:[{ scale:sc }] }]}>
        {children}
      </Animated.View>
    </Pressable>
  );
}

// ── Language Picker — Full Screen Modal ───────────────────────────────────────
function LangSheet({ visible, current, onSelect, onClose }: {
  visible: boolean; current: string;
  onSelect: (code: string) => void; onClose: () => void;
}) {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { language, isIndia } = useUser();
  const v: VLang = vLangFromCode(language);
  const L = getProfileLabels(v);
  const t = getT(language);
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<"india" | "global">(isIndia ? "india" : "global");

  const LANGUAGES = getLangList(tab === "india");

  const filtered = query.trim().length > 0
    ? LANGUAGES.filter(l =>
        l.name.toLowerCase().includes(query.toLowerCase()) ||
        l.native.toLowerCase().includes(query.toLowerCase())
      )
    : LANGUAGES;

  function handleSelect(code: string) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    onSelect(code);
    onClose();
  }

  function switchTab(t: "india" | "global") {
    setTab(t);
    setQuery("");
    Haptics.selectionAsync();
  }

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={[lm.screen, { paddingTop: insets.top, backgroundColor: C.bg }]}>

        {/* ── Header ── */}
        <View style={[lm.header, { borderColor: C.border }]}>
          <Pressable onPress={onClose} style={[lm.backBtn, { backgroundColor: C.bgCard2 }]}>
            <Feather name="x" size={18} color={C.textMuted} />
          </Pressable>
          <View style={{ flex: 1, alignItems: "center" }}>
            <Text style={[lm.title, { color: C.text }]}>{t.selectLanguage}</Text>
            <Text style={[lm.subtitle, { color: C.textMuted }]}>{t.langSubtitle}</Text>
          </View>
          <View style={{ width: 36 }} />
        </View>

        {/* ── India / Global tab switcher ── */}
        <View style={[lm.tabRow, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Pressable
            style={[lm.tabBtn, {
              backgroundColor: tab === "india" ? C.bgCard : "transparent",
              borderColor:      tab === "india" ? "#f59e0b55" : "transparent",
            }]}
            onPress={() => switchTab("india")}
          >
            <Text style={lm.tabFlag}>🇮🇳</Text>
            <Text style={[lm.tabLabel, { color: tab === "india" ? "#f59e0b" : C.textMuted }]}>{L.tabIndia}</Text>
          </Pressable>
          <Pressable
            style={[lm.tabBtn, {
              backgroundColor: tab === "global" ? C.bgCard : "transparent",
              borderColor:      tab === "global" ? "#6366f155" : "transparent",
            }]}
            onPress={() => switchTab("global")}
          >
            <Text style={lm.tabFlag}>🌍</Text>
            <Text style={[lm.tabLabel, { color: tab === "global" ? "#6366f1" : C.textMuted }]}>{L.tabGlobal}</Text>
          </Pressable>
        </View>

        {/* ── Search bar ── */}
        <View style={[lm.searchWrap, { backgroundColor: C.inputBg, borderColor: C.border }]}>
          <Feather name="search" size={14} color={C.textMuted} />
          <TextInput
            style={[lm.searchInput, { color: C.text }]}
            value={query}
            onChangeText={setQuery}
            placeholder={t.langSearch}
            placeholderTextColor={C.textDim}
            autoCorrect={false}
          />
          {query.length > 0 && (
            <Pressable onPress={() => setQuery("")}>
              <Feather name="x-circle" size={14} color={C.textMuted} />
            </Pressable>
          )}
        </View>

        <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 40 }}>

          {/* ── Language grid ── */}
          {filtered.length > 0 ? (
            <View style={lm.grid}>
              {filtered.map(l => (
                <Pressable key={l.code}
                  onPress={() => handleSelect(l.code)}
                  style={[
                    lm.tile,
                    { backgroundColor: C.bgCard, borderColor: C.border },
                    l.code === current && lm.tileActive,
                  ]}
                >
                  <Text style={[lm.tileNative, { color: C.text }, l.code === current && { color: "#f59e0b" }]}>
                    {l.native}
                  </Text>
                  <Text style={[lm.tileEn, { color: C.textMuted }]}>{l.name}</Text>
                  {l.code === current && (
                    <View style={lm.checkBadge}>
                      <Feather name="check" size={10} color="#020d1a" />
                    </View>
                  )}
                </Pressable>
              ))}
            </View>
          ) : (
            <View style={{ alignItems: "center", paddingVertical: 40 }}>
              <Text style={{ color: C.textMuted, fontFamily: F.medium, fontSize: 14 }}>
                No language found for "{query}"
              </Text>
            </View>
          )}
        </ScrollView>
      </View>
    </Modal>
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
  const L = getProfileLabels(v);
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
  const L = getProfileLabels(v);

  const [showLang, setShowLang] = useState(false);
  const [pushOn, setPushOn]     = useState(true);
  const [pushBusy, setPushBusy] = useState(false);

  // Auto-register device for push on first profile mount (silent — only asks
  // permission once; on denial pushOn flips off).
  React.useEffect(() => {
    if (!user?.id) return;
    let cancelled = false;
    (async () => {
      const tok = await setupPushForUser(user.id);
      if (!cancelled && !tok) setPushOn(false);
    })();
    return () => { cancelled = true; };
  }, [user?.id]);

  async function handlePushToggle(next: boolean) {
    if (!user?.id || pushBusy) return;
    setPushBusy(true);
    setPushOn(next);
    try {
      if (next) {
        // Re-trigger permission + token register
        const tok = await setupPushForUser(user.id);
        if (!tok) {
          setPushOn(false);
          Alert.alert("Notifications off",
            "Permission denied. Phone Settings → Cosmic Lens → Notifications me enable karein.");
        }
      } else {
        await setPushEnabled(user.id, false);
      }
    } finally {
      setPushBusy(false);
    }
  }

  async function handlePushTest() {
    if (!user?.id) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const r = await sendTestNotification(user.id);
    const ok = r?.sent > 0;
    Alert.alert(ok ? "Test bhej diya ✨" : "Bhejne me dikkat",
      ok ? "Notification 1-2 second me dikhegi."
         : (r?.skipped || r?.error || "Token register nahi hai. Toggle off→on karein."));
  }

  const t = getT(language);
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0];
  const initials = (primaryProfile?.name ?? "U")
    .split(" ").map(w=>w[0]??"").join("").slice(0,2).toUpperCase();

  function handleLogout() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    logout();
    router.replace("/login");
  }

  return (
    <CosmicBg>

      {/* Language sheet */}
      <LangSheet
        visible={showLang}
        current={language}
        onSelect={code => { setLanguage(code as "hi"); Haptics.selectionAsync(); }}
        onClose={() => setShowLang(false)}
      />


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
            <Text style={[s.headerName,{ color: C.text }]}>{primaryProfile?.name ?? "User"}</Text>
            <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.medium }}>
              {profiles.length} profile{profiles.length!==1?"s":""} · {primaryProfile?.birthData.place ?? ""}
            </Text>
          </View>

          <View style={[s.planBadge,{ backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Feather name="circle" size={9} color={C.textMuted} />
            <Text style={{ color: C.textMuted, fontSize: 9.5, fontFamily: F.bold, letterSpacing: 1 }}>{L.freePlan}</Text>
          </View>
        </LinearGradient>

        {/* ── SETTINGS ─────────────────────────────────────────────────── */}
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

            <SettingRow
              icon="globe"
              label={t.language}
              onPress={() => setShowLang(true)}
              right={
                <View style={{ flexDirection:"row", alignItems:"center", gap:6 }}>
                  <View style={{ alignItems: "flex-end" }}>
                    <Text style={{ color: C.isDark ? "#f59e0b" : "#7C3AED", fontSize:13, fontFamily:F.semibold }}>
                      {ALL_LANG_META.find(l=>l.code===language)?.native ?? "English"}
                    </Text>
                    <Text style={{ color:C.textMuted, fontSize:10, fontFamily:F.medium }}>
                      {ALL_LANG_META.find(l=>l.code===language)?.name ?? "English"}
                    </Text>
                  </View>
                  <Feather name="chevron-right" size={14} color={C.textDim} />
                </View>
              }
            />


          </View>
        </View>

        {/* ── SUPPORT ──────────────────────────────────────────────────── */}
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
              icon="star"
              label={t.settingRateUs}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            />
            <SettingRow
              icon="share-2"
              label={t.settingShareApp}
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
              last
            />
          </View>
        </View>

        {/* ── LEGAL ────────────────────────────────────────────────────── */}
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{t.sectionLegal}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <SettingRow
              icon="shield"
              label={t.settingLegal}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/legal"); }}
              last
            />
          </View>
        </View>

        {/* ── NOTIFICATIONS ────────────────────────────────────────────── */}
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>
            NOTIFICATIONS
          </Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={st.notifRow}>
              <View style={{ flexDirection: "row", alignItems: "center", flex: 1 }}>
                <Feather name="bell" size={18} color={C.text} style={{ marginRight: 12 }} />
                <View style={{ flex: 1 }}>
                  <Text style={[st.notifLabel, { color: C.text }]}>Daily forecast & alerts</Text>
                  <Text style={[st.notifSub,   { color: C.textDim }]}>
                    Aaj ka rashifal, transit shifts, dasha changes
                  </Text>
                </View>
              </View>
              <Switch
                value={pushOn}
                onValueChange={handlePushToggle}
                disabled={pushBusy}
                trackColor={{ false: "#475569", true: "#7C3AED" }}
                thumbColor={pushOn ? "#fbbf24" : "#cbd5e1"}
              />
            </View>
            <SettingRow
              icon="send"
              label="Send test notification"
              onPress={handlePushTest}
              last
            />
          </View>
        </View>

        {/* ── DANGER ZONE ──────────────────────────────────────────────── */}
        <View>
          <Text style={[s.sectionLabel,{ color: "#ef4444" }]}>{t.sectionDanger}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: "rgba(239,68,68,0.25)" }]}>
            <SettingRow
              icon="trash-2"
              label={t.settingDeleteAcc}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/delete-account"); }}
              last
            />
          </View>
        </View>

        {/* ── MY DATA ──────────────────────────────────────────────────── */}
        <View>
          <Text style={[s.sectionLabel,{ color: C.isDark ? "#f59e0b" : "#7C3AED" }]}>{L.myData}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <SettingRow
              icon="book-open"
              label={L.myKundli}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/my-kundli"); }}
              right={
                <View style={{ flexDirection:"row", alignItems:"center", gap:6 }}>
                  <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.medium }}>{profiles.filter(p => p.kundli).length} {L.saved}</Text>
                  <Feather name="chevron-right" size={14} color={C.textDim} />
                </View>
              }
              last
            />
          </View>
        </View>

        {/* ── APP VERSION + LOGOUT ─────────────────────────────────────── */}
        <View style={s.bottomSection}>
          <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium }}>Cosmic Lens v1.0.0 · Made with ♥ in India</Text>

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
  headerName: { color:"#dde8f4", fontSize:18, fontFamily:F.bold, letterSpacing:-0.4 },
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
  notifRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 14, paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: "rgba(148,163,184,0.18)",
  },
  notifLabel: { fontSize: 14, fontFamily: F.semibold },
  notifSub:   { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
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

// ── Language modal ────────────────────────────────────────────────────────────
const lm = StyleSheet.create({
  screen: {
    flex: 1, backgroundColor: "#020d1a",
  },
  header: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1, borderColor: "rgba(255,255,255,0.05)",
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: "rgba(255,255,255,0.05)",
    alignItems: "center", justifyContent: "center",
  },
  title:    { color: "#dde8f4", fontSize: 16, fontFamily: F.bold },
  subtitle: { color: "#334155", fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  tabRow: {
    flexDirection: "row", marginHorizontal: 16, marginTop: 12,
    borderRadius: 14, borderWidth: 1, padding: 4, gap: 4,
  },
  tabBtn: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6, paddingVertical: 10, borderRadius: 10, borderWidth: 1,
  },
  tabFlag: { fontSize: 16 },
  tabLabel: { fontSize: 13, fontFamily: F.bold },
  searchWrap: {
    flexDirection: "row", alignItems: "center", gap: 10,
    backgroundColor: "#040e1e", borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)", borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 11,
    marginHorizontal: 16, marginVertical: 12,
  },
  searchInput: {
    flex: 1, color: "#dde8f4", fontSize: 13,
    fontFamily: F.regular, padding: 0,
  },
  groupHeader: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 16, paddingTop: 18, paddingBottom: 10,
  },
  groupDot:  { width: 6, height: 6, borderRadius: 3, backgroundColor: "#f59e0b" },
  groupLabel: {
    color: "#f59e0b", fontSize: 9, fontFamily: F.bold, letterSpacing: 2.2,
  },
  grid: {
    flexDirection: "row", flexWrap: "wrap",
    paddingHorizontal: 12, gap: 10,
  },
  tile: {
    width: "47%", backgroundColor: "#040e1e",
    borderRadius: 14, borderWidth: 1, borderColor: "rgba(255,255,255,0.06)",
    padding: 14, position: "relative",
  },
  tileActive: {
    borderColor: "#f59e0b",
    backgroundColor: "rgba(245,158,11,0.06)",
  },
  tileComingSoon: { opacity: 0.55 },
  tileNative: { color: "#dde8f4", fontSize: 18, fontFamily: F.semibold, marginBottom: 4 },
  tileEn:     { color: "#334155", fontSize: 11, fontFamily: F.medium },
  checkBadge: {
    position: "absolute", top: 8, right: 8,
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: "#f59e0b",
    alignItems: "center", justifyContent: "center",
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


