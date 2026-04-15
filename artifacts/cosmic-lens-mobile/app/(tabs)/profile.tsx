import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import {
  Alert, Animated, Modal, Platform, Pressable,
  ScrollView, StyleSheet, Switch, Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC, useTheme } from "@/context/ThemeContext";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import { getT, INDIA_LANG_CODES, GLOBAL_LANG_CODES } from "@/lib/i18n";

// ── Relation options ───────────────────────────────────────────────────────────
const RELATIONS = [
  { key: "Self",      emoji: "🧑",  label: "Self" },
  { key: "Husband",   emoji: "👨",  label: "Husband" },
  { key: "Wife",      emoji: "👩",  label: "Wife" },
  { key: "Son",       emoji: "👦",  label: "Son" },
  { key: "Daughter",  emoji: "👧",  label: "Daughter" },
  { key: "Father",    emoji: "👴",  label: "Father" },
  { key: "Mother",    emoji: "👵",  label: "Mother" },
  { key: "Brother",   emoji: "🧑",  label: "Brother" },
  { key: "Sister",    emoji: "👱‍♀️", label: "Sister" },
  { key: "Friend",    emoji: "🤝",  label: "Friend" },
  { key: "Other",     emoji: "👥",  label: "Other" },
];

// ── Font aliases ───────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

// ── Languages ─────────────────────────────────────────────────────────────────
type LangItem = { code: string; native: string; name: string };

const ALL_LANG_META: LangItem[] = [
  { code:"en",  native:"English",     name:"English"    },
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
    features: ["1 Profile","Basic Kundli Chart","3 AI Questions / day","Demo Insights","Basic Planet View"],
    featureOff: ["Full Dasha Timeline","7-Day Forecast","PDF Report","Kundli Milan"],
  },
  {
    key: "pro", name: "Pro",
    accent: "#f59e0b", accentBg: "rgba(245,158,11,0.05)",
    border: "rgba(245,158,11,0.30)", badge: "POPULAR",
    monthlyPrice: 149, yearlyPrice: 999, yearlySave: 44,
    cta: "Get Pro", ctaActive: true,
    icon: "zap" as const,
    features: ["5 Profiles","Full Kundli + Dasha Timeline","Unlimited AI Chat","7-Day Forecast","Planet Positions + Nakshatra","Monthly Category Insights"],
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
            <Text style={[lm.tabLabel, { color: tab === "india" ? "#f59e0b" : C.textMuted }]}>India</Text>
          </Pressable>
          <Pressable
            style={[lm.tabBtn, {
              backgroundColor: tab === "global" ? C.bgCard : "transparent",
              borderColor:      tab === "global" ? "#6366f155" : "transparent",
            }]}
            onPress={() => switchTab("global")}
          >
            <Text style={lm.tabFlag}>🌍</Text>
            <Text style={[lm.tabLabel, { color: tab === "global" ? "#6366f1" : C.textMuted }]}>Global</Text>
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

// ── Relation Picker Modal ──────────────────────────────────────────────────────
function RelationPickerModal({ visible, onSelect, onClose }: {
  visible: boolean;
  onSelect: (relation: string) => void;
  onClose: () => void;
}) {
  const C = useC();
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={rp.overlay} onPress={onClose}>
        <Pressable style={[rp.sheet, { backgroundColor: C.bgCard, borderColor: C.border }]} onPress={e => e.stopPropagation()}>
          <View style={[rp.handle, { backgroundColor: C.border2 }]} />
          <Text style={[rp.title, { color: C.text }]}>Whose Kundli to Add?</Text>
          <Text style={[rp.sub, { color: C.textMuted }]}>Select the relation</Text>

          <View style={rp.grid}>
            {RELATIONS.map(r => (
              <Pressable
                key={r.key}
                onPress={() => { Haptics.selectionAsync(); onSelect(r.key); }}
                style={({ pressed }) => [rp.chip, { backgroundColor: C.bgCard2, borderColor: C.border }, pressed && { opacity: 0.7 }]}
              >
                <Text style={rp.chipEmoji}>{r.emoji}</Text>
                <Text style={[rp.chipLabel, { color: C.textMid }]}>{r.key}</Text>
                <Text style={[rp.chipSub, { color: C.textMuted }]}>{r.label.split("(")[1]?.replace(")", "") ?? ""}</Text>
              </Pressable>
            ))}
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

// ── Delete Confirm Modal ──────────────────────────────────────────────────────
function DeleteModal({ name, onConfirm, onCancel }: {
  name: string; onConfirm: () => void; onCancel: () => void;
}) {
  const C = useC();
  return (
    <Modal visible transparent animationType="fade" onRequestClose={onCancel}>
      <View style={dm.overlay}>
        <View style={[dm.box, { backgroundColor: C.bgCard, borderColor: "rgba(248,113,113,0.25)" }]}>
          <View style={dm.iconWrap}>
            <Feather name="trash-2" size={20} color="#f87171" />
          </View>
          <Text style={[dm.title, { color: C.text }]}>Profile Delete Karein?</Text>
          <Text style={[dm.body, { color: C.textMuted }]}>
            <Text style={{ color: C.textMid, fontFamily:F.semibold }}>{name}</Text>
            {" "}ka chart data permanently delete ho jayega.
          </Text>
          <View style={dm.btnRow}>
            <Pressable onPress={onCancel} style={[dm.cancelBtn, { borderColor: C.border }]}>
              <Text style={{ color: C.textMuted, fontSize:14, fontFamily:F.medium }}>Cancel</Text>
            </Pressable>
            <Pressable onPress={onConfirm} style={dm.deleteBtn}>
              <Text style={{ color:"#fff", fontSize:14, fontFamily:F.bold }}>Delete</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

// ── Profile Card ──────────────────────────────────────────────────────────────
function ProfileCard({ profile, isPrimary, canDelete, onEdit, onSetPrimary, onDelete }: {
  profile: ProfileEntry; isPrimary: boolean; canDelete: boolean;
  onEdit:()=>void; onSetPrimary:()=>void; onDelete:()=>void;
}) {
  const C = useC();
  const initials = profile.name.split(" ").map(w=>w[0]??"").join("").slice(0,2).toUpperCase()||"?";
  const relationInfo = RELATIONS.find(r => r.key === profile.relation);

  return (
    <View style={[pc.card, { backgroundColor: C.bgCard, borderColor: C.border, boxShadow: C.cardShadow } as any, isPrimary && pc.cardPrimary]}>
      <View style={{ flexDirection:"row", alignItems:"center", gap:12 }}>
        {/* Avatar */}
        <View>
          <LinearGradient
            colors={isPrimary ? ["#0ea5e9","#f59e0b"] : [C.bgCard2, C.bgCard3]}
            style={pc.avatar}
          >
            <Text style={pc.initials}>{initials}</Text>
          </LinearGradient>
          {relationInfo && (
            <View style={[pc.emojiTag, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Text style={{ fontSize: 11 }}>{relationInfo.emoji}</Text>
            </View>
          )}
        </View>

        <View style={{ flex:1, minWidth:0, gap:3 }}>
          {/* Name + badges */}
          <View style={{ flexDirection:"row", alignItems:"center", gap:6, flexWrap:"wrap" }}>
            <Text style={[pc.name,{ color: C.text }]} numberOfLines={1}>{profile.name}</Text>
            {isPrimary && (
              <View style={[pc.primaryBadge,{ backgroundColor: C.isDark ? "rgba(245,158,11,0.15)" : C.warningBg, borderColor: C.isDark ? "rgba(245,158,11,0.3)" : C.warningBorder }]}>
                <Feather name="star" size={8} color="#f59e0b" />
                <Text style={pc.primaryBadgeText}>PRIMARY</Text>
              </View>
            )}
            {relationInfo && (
              <View style={[pc.relationBadge,{ backgroundColor: C.bgCard2, borderColor: C.border }]}>
                <Text style={[pc.relationBadgeText,{ color: C.textMuted }]}>{profile.relation}</Text>
              </View>
            )}
          </View>

          <Text style={[pc.sub,{ color: C.textMuted }]} numberOfLines={1}>
            {profile.gender ? `${profile.gender} · ` : ""}
            {profile.birthData.place}
          </Text>
          <Text style={[pc.date,{ color: C.textDim }]}>
            {profile.birthData.day}/{profile.birthData.month}/{profile.birthData.year}
            {"  ·  "}
            {String(profile.birthData.hour).padStart(2,"0")}:{String(profile.birthData.minute).padStart(2,"0")} {profile.birthData.ampm}
          </Text>
        </View>

        <View style={{ flexDirection:"row", gap:6 }}>
          {canDelete && (
            <Pressable onPress={onDelete} style={[pc.iconBtn,{ backgroundColor: C.bgCard2 }]} hitSlop={8}>
              <Feather name="trash-2" size={14} color="#f87171" />
            </Pressable>
          )}
          <Pressable onPress={onEdit} style={[pc.iconBtn,{ backgroundColor: C.bgCard2 }]} hitSlop={8}>
            <Feather name="edit-3" size={14} color={C.textMuted} />
          </Pressable>
        </View>
      </View>

      {isPrimary ? (
        <View style={[pc.activeRow,{ borderTopColor: C.border }]}>
          <Feather name="check-circle" size={11} color="#00a86b" />
          <Text style={[pc.activeText,{ color: C.textMuted }]}>Active — sab calculations is chart se</Text>
        </View>
      ) : (
        <Pressable onPress={onSetPrimary} style={[pc.setPrimaryBtn,{ borderTopColor: C.border }]}>
          <Feather name="star" size={11} color="#f59e0b" />
          <Text style={[pc.setPrimaryText,{ color: C.textMuted }]}>Set as Primary — This chart will show on home screen</Text>
        </Pressable>
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
              <Text style={[pl.badgeText, { color: plan.accent }]}>ACTIVE</Text>
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
          <Text style={[pl.price, { color: plan.accent }]}>FREE</Text>
        ) : (
          <>
            <Text style={[pl.priceCurrency, { color: plan.accent }]}>₹</Text>
            <Text style={[pl.price, { color: plan.accent }]}>{price.toLocaleString("en-IN")}</Text>
            <Text style={[pl.pricePer, { color: C.textMuted }]}>/{cycle === "yearly" ? "year" : "month"}</Text>
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
    profiles, primaryProfileId,
    deleteProfile, setPrimaryProfile,
    language, setLanguage,
    logout,
  } = useUser();

  const [showLang,         setShowLang]         = useState(false);
  const [confirmDelete,    setConfirmDelete]    = useState<string | null>(null);
  const [switching,        setSwitching]        = useState(false);
  const [showRelationPick, setShowRelationPick] = useState(false);

  const t = getT(language);
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0];
  const initials = (primaryProfile?.name ?? "U")
    .split(" ").map(w=>w[0]??"").join("").slice(0,2).toUpperCase();

  function handleSetPrimary(id:string) {
    setSwitching(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setTimeout(() => { setPrimaryProfile(id); setSwitching(false); }, 400);
  }

  function handleLogout() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    logout();
    router.replace("/login");
  }

  const deleteTarget = confirmDelete ? profiles.find(p=>p.id===confirmDelete) : null;

  return (
    <CosmicBg>

      {/* Switching overlay */}
      {switching && (
        <View style={s.overlay}>
          <View style={s.overlayBox}>
            <Feather name="refresh-cw" size={22} color={C.isDark ? "#f59e0b" : "#92400E"} style={{ marginBottom:10 }} />
            <Text style={{ color: C.isDark ? "#f59e0b" : "#92400E", fontSize:13, fontFamily:F.semibold }}>Profile switch ho raha hai...</Text>
          </View>
        </View>
      )}

      {/* Delete modal */}
      {confirmDelete && deleteTarget && (
        <DeleteModal
          name={deleteTarget.name}
          onConfirm={() => { deleteProfile(confirmDelete); setConfirmDelete(null); }}
          onCancel={() => setConfirmDelete(null)}
        />
      )}

      {/* Relation picker */}
      <RelationPickerModal
        visible={showRelationPick}
        onSelect={relation => {
          setShowRelationPick(false);
          router.push({ pathname: "/profile-edit", params: { mode: "add", relation } });
        }}
        onClose={() => setShowRelationPick(false)}
      />

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
          colors={C.isDark ? ["#040e20","#071525"] : [C.bgCard, C.bgCard2]}
          style={[s.header,{ borderColor: C.border }]}
        >
          {/* Background star pattern */}
          <Text style={s.headerBgStar}>✦</Text>
          <Text style={[s.headerBgStar, { right:30, top:12, fontSize:14, opacity:0.04 }]}>✦</Text>

          <LinearGradient colors={["#0ea5e9","#f59e0b"]} style={s.headerAvatar}>
            <Text style={s.headerInitials}>{initials}</Text>
          </LinearGradient>

          <View style={{ alignItems:"center", gap:4 }}>
            <Text style={[s.headerName,{ color: C.text }]}>{primaryProfile?.name ?? "User"}</Text>
            <Text style={[s.headerSub,{ color: C.textMuted }]}>
              {profiles.length} profile{profiles.length!==1?"s":""} · {primaryProfile?.birthData.place ?? ""}
            </Text>
          </View>

          {/* Free plan badge */}
          <View style={[s.planBadge,{ backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Feather name="circle" size={9} color={C.textMuted} />
            <Text style={[s.planBadgeText,{ color: C.textMuted }]}>FREE PLAN</Text>
            <View style={[s.planDivider,{ backgroundColor: C.border }]} />
            <Text style={s.planUpgrade}>Upgrade Now →</Text>
          </View>
        </LinearGradient>

        {/* ── MY PROFILES ─────────────────────────────────────────────── */}
        <View>
          <View style={s.sectionRow}>
            <Text style={[s.sectionLabel,{ color: C.textMuted }]}>{t.myProfiles.toUpperCase()}</Text>
            <Text style={[s.sectionCount, { color: C.textMuted }]}>{profiles.length}/1</Text>
          </View>

          <View style={{ gap:10 }}>
            {profiles.map(p => (
              <ProfileCard
                key={p.id}
                profile={p}
                isPrimary={p.id === primaryProfileId}
                canDelete={p.id !== primaryProfileId && profiles.length > 1}
                onEdit={() => router.push({ pathname:"/profile-edit", params:{ mode:"edit", profileId:p.id } })}
                onSetPrimary={() => handleSetPrimary(p.id)}
                onDelete={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setConfirmDelete(p.id); }}
              />
            ))}

            {/* Add Family Member */}
            <Pressable
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                setShowRelationPick(true);
              }}
              style={({ pressed }) => [s.addBtn,{ backgroundColor: C.bgCard, borderColor: C.border }, pressed && { opacity: 0.7 }]}
            >
              <View style={[s.addCircle,{ backgroundColor: C.isDark ? "rgba(245,158,11,0.1)" : C.warningBg }]}>
                <Feather name="users" size={15} color={C.isDark ? "#f59e0b" : "#92400E"} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ color: C.isDark ? "#f59e0b" : "#92400E", fontSize: 13, fontFamily: F.semibold }}>
                  {t.addFamilyMember}
                </Text>
                <Text style={{ color: C.textDim, fontSize: 10, fontFamily: F.regular, marginTop: 2 }}>
                  Son, Daughter, Spouse, Parents, Friend & more
                </Text>
              </View>
              <Feather name="chevron-right" size={14} color={C.textDim} />
            </Pressable>
          </View>
        </View>

        {/* ── SETTINGS ─────────────────────────────────────────────────── */}
        <View>
          <Text style={[s.sectionLabel,{ color: C.textMuted }]}>{t.settings.toUpperCase()}</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>

            <SettingRow
              icon="star"
              label={t.subscription}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/subscription"); }}
              right={
                <View style={{ flexDirection:"row", alignItems:"center", gap:6 }}>
                  <View style={{ width:7, height:7, borderRadius:3.5, backgroundColor:C.textDim }} />
                  <Text style={{ color:C.textMuted, fontSize:12, fontFamily:F.medium }}>Free Plan</Text>
                  <Feather name="chevron-right" size={14} color={C.textDim} />
                </View>
              }
            />

            <SettingRow
              icon="globe"
              label={t.language}
              onPress={() => setShowLang(true)}
              right={
                <View style={{ flexDirection:"row", alignItems:"center", gap:6 }}>
                  <View style={{ alignItems: "flex-end" }}>
                    <Text style={{ color: C.isDark ? "#f59e0b" : "#92400E", fontSize:13, fontFamily:F.semibold }}>
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
          <Text style={[s.sectionLabel,{ color: C.textMuted }]}>SUPPORT & ABOUT</Text>
          <View style={[st.card,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
            <SettingRow
              icon="message-circle"
              label="Help & Support"
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            />
            <SettingRow
              icon="star"
              label="Rate Us ⭐"
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            />
            <SettingRow
              icon="book-open"
              label="My Kundli 📜"
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/(tabs)/kundli"); }}
            />
            <SettingRow
              icon="share-2"
              label="Share App"
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            />
            <SettingRow
              icon="shield"
              label="Privacy Policy"
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
            />
            <SettingRow
              icon="file-text"
              label="Terms of Service"
              onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}
              last
            />
          </View>
        </View>

        {/* ── APP VERSION + LOGOUT ─────────────────────────────────────── */}
        <View style={s.bottomSection}>
          <Text style={[s.versionText,{ color: C.textDim }]}>Cosmic Lens v1.0.0 · Made with ♥ in India</Text>

          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              Alert.alert("Logout", "Are you sure you want to log out?", [
                { text:"Cancel", style:"cancel" },
                { text:"Logout", style:"destructive", onPress: handleLogout },
              ]);
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
  overlay: {
    ...StyleSheet.absoluteFillObject, backgroundColor:"rgba(0,0,0,0.75)",
    alignItems:"center", justifyContent:"center", zIndex:999,
  },
  overlayBox: { alignItems:"center" },

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

  sectionRow: { flexDirection:"row", alignItems:"center", justifyContent:"space-between", marginBottom:12 },
  sectionLabel: { color:"#f59e0b", fontSize:10, fontFamily:F.bold, letterSpacing:2.2 },
  sectionCount: { color:"#1e3a5f", fontSize:10, fontFamily:F.medium },
  sectionAction:{ color:"#f59e0b", fontSize:10, fontFamily:F.semibold },

  addBtn: {
    flexDirection:"row", alignItems:"center", gap:12,
    padding:14, borderRadius:14,
    backgroundColor:"rgba(245,158,11,0.03)",
    borderWidth:1, borderColor:"rgba(245,158,11,0.14)",
  },
  addCircle: {
    width:34, height:34, borderRadius:17,
    borderWidth:1, borderColor:"rgba(245,158,11,0.25)",
    backgroundColor:"rgba(245,158,11,0.06)",
    alignItems:"center", justifyContent:"center",
  },

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

// ── Profile card ──────────────────────────────────────────────────────────────
const pc = StyleSheet.create({
  card: {
    backgroundColor:"#040e20", borderRadius:16,
    borderWidth:1, borderColor:"rgba(255,255,255,0.05)",
    padding:14, gap:10,
  },
  cardPrimary: {
    borderColor:"rgba(245,158,11,0.2)",
    backgroundColor:"rgba(0,20,40,0.9)",
  },
  avatar: {
    width:44, height:44, borderRadius:22,
    alignItems:"center", justifyContent:"center",
  },
  initials: { color:"#fff", fontSize:16, fontFamily:F.bold },
  name:     { color:"#dde8f4", fontSize:14, fontFamily:F.bold },
  sub:      { color:"#334155", fontSize:11, fontFamily:F.medium },
  date:     { color:"#1e3a5f", fontSize:10, fontFamily:F.regular },
  primaryBadge: {
    flexDirection:"row", alignItems:"center", gap:4,
    backgroundColor:"rgba(245,158,11,0.1)", borderWidth:1,
    borderColor:"rgba(245,158,11,0.25)", borderRadius:20,
    paddingVertical:2, paddingHorizontal:7,
  },
  primaryBadgeText: { color:"#f59e0b", fontSize:8, fontFamily:F.bold, letterSpacing:0.8 },
  iconBtn: {
    width:30, height:30, borderRadius:8,
    backgroundColor:"rgba(255,255,255,0.04)",
    borderWidth:1, borderColor:"rgba(255,255,255,0.06)",
    alignItems:"center", justifyContent:"center",
  },
  activeRow: {
    flexDirection:"row", alignItems:"center", gap:6,
    backgroundColor:"rgba(0,168,107,0.08)", borderRadius:8,
    paddingVertical:6, paddingHorizontal:10,
  },
  activeText:    { color:"#00a86b", fontSize:10, fontFamily:F.medium },
  setPrimaryBtn: {
    flexDirection:"row", alignItems:"center", gap:6,
    alignSelf:"stretch",
    backgroundColor:"rgba(245,158,11,0.06)", borderRadius:9,
    paddingVertical:8, paddingHorizontal:12,
    borderWidth:1, borderColor:"rgba(245,158,11,0.18)",
  },
  setPrimaryText: { color:"#f59e0b", fontSize:10.5, fontFamily:F.semibold, flex: 1 },
  emojiTag: {
    position: "absolute", bottom: -3, right: -4,
    width: 18, height: 18, borderRadius: 9,
    backgroundColor: "#040e20",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.08)",
    alignItems: "center", justifyContent: "center",
  },
  relationBadge: {
    backgroundColor: "rgba(167,139,250,0.1)",
    borderWidth: 1, borderColor: "rgba(167,139,250,0.25)",
    borderRadius: 20, paddingVertical: 2, paddingHorizontal: 7,
  },
  relationBadgeText: { color: "#a78bfa", fontSize: 8.5, fontFamily: F.bold, letterSpacing: 0.5 },
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

// ── Relation Picker ───────────────────────────────────────────────────────────
const rp = StyleSheet.create({
  overlay: {
    flex: 1, backgroundColor: "rgba(0,0,0,0.6)", justifyContent: "flex-end",
  },
  sheet: {
    backgroundColor: "#071525",
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.07)",
    paddingHorizontal: 20, paddingBottom: 36, paddingTop: 14,
  },
  handle: {
    width: 36, height: 4, borderRadius: 2,
    backgroundColor: "rgba(255,255,255,0.12)",
    alignSelf: "center", marginBottom: 20,
  },
  title: {
    color: "#dde8f4", fontSize: 17, fontFamily: F.bold,
    letterSpacing: -0.3, textAlign: "center",
  },
  sub: {
    color: "#334155", fontSize: 11.5, fontFamily: F.medium,
    textAlign: "center", marginTop: 4, marginBottom: 20,
  },
  grid: {
    flexDirection: "row", flexWrap: "wrap", gap: 10,
  },
  chip: {
    width: "30%", flexGrow: 1,
    alignItems: "center", gap: 4,
    backgroundColor: "#040e20",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.06)",
    borderRadius: 14, paddingVertical: 14, paddingHorizontal: 8,
  },
  chipEmoji: { fontSize: 22, lineHeight: 28 },
  chipLabel: {
    color: "#94a3b8", fontSize: 12, fontFamily: F.semibold, textAlign: "center",
  },
  chipSub: {
    color: "#334155", fontSize: 9.5, fontFamily: F.regular, textAlign: "center",
  },
});

// ── Delete modal ──────────────────────────────────────────────────────────────
const dm = StyleSheet.create({
  overlay: { flex:1, backgroundColor:"rgba(0,0,0,0.8)", alignItems:"center", justifyContent:"center" },
  box: {
    width:300, backgroundColor:"#071525",
    borderRadius:20, borderWidth:1, borderColor:"rgba(248,113,113,0.2)",
    padding:24, alignItems:"center", gap:10,
  },
  iconWrap: {
    width:48, height:48, borderRadius:24,
    backgroundColor:"rgba(248,113,113,0.1)", alignItems:"center", justifyContent:"center",
  },
  title: { color:"#dde8f4", fontSize:17, fontFamily:F.bold, textAlign:"center" },
  body:  { color:"#64748b", fontSize:13, fontFamily:F.regular, textAlign:"center", lineHeight:19 },
  btnRow: { flexDirection:"row", gap:12, marginTop:8 },
  cancelBtn: {
    flex:1, alignItems:"center", paddingVertical:11, borderRadius:12,
    borderWidth:1, borderColor:"rgba(255,255,255,0.08)",
    backgroundColor:"rgba(255,255,255,0.03)",
  },
  deleteBtn: {
    flex:1, alignItems:"center", paddingVertical:11, borderRadius:12,
    backgroundColor:"#b91c1c",
  },
});
