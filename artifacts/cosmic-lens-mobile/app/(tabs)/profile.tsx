import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  Alert, Modal, Platform, Pressable, ScrollView,
  StyleSheet, Switch, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useUser, type ProfileEntry } from "@/context/UserContext";

type LangItem = { code: string; native: string; name: string };
const LANGUAGES: LangItem[] = [
  { code:"hi", native:"हिंदी",      name:"Hindi"       },
  { code:"en", native:"English",    name:"English"     },
  { code:"mr", native:"मराठी",      name:"Marathi"     },
  { code:"bn", native:"বাংলা",      name:"Bengali"     },
  { code:"te", native:"తెలుగు",     name:"Telugu"      },
  { code:"ta", native:"தமிழ்",      name:"Tamil"       },
  { code:"gu", native:"ગુજરાતી",   name:"Gujarati"    },
  { code:"kn", native:"ಕನ್ನಡ",     name:"Kannada"     },
];

type BillingCycle = "monthly" | "yearly";

const PLANS = [
  {
    key: "free",
    name: "Muft",
    nameEn: "Free",
    badge: null,
    accent: "#475569",
    accentBg: "rgba(71,85,105,0.08)",
    border: "rgba(71,85,105,0.25)",
    monthlyPrice: 0,
    yearlyPrice: 0,
    cta: "Current Plan",
    ctaActive: false,
    features: [
      "1 Profile",
      "Basic Kundli Chart",
      "3 AI Sawaal / din",
      "Demo Insights",
      "Basic Planet View",
    ],
    featureOff: [
      "Full Dasha Timeline",
      "7-Day Forecast",
      "PDF Report",
    ],
  },
  {
    key: "pro",
    name: "Pro",
    nameEn: "Pro",
    badge: "POPULAR",
    badgeColor: "#00d4ff",
    accent: "#00d4ff",
    accentBg: "rgba(0,212,255,0.06)",
    border: "rgba(0,212,255,0.35)",
    monthlyPrice: 149,
    yearlyPrice: 999,
    yearlySave: 44,
    cta: "Pro Lein",
    ctaActive: true,
    features: [
      "5 Profiles",
      "Full Kundli + Dasha Timeline",
      "Unlimited AI Chat",
      "7-Din ka Forecast",
      "Planet Positions + Nakshatra",
      "Monthly Category Insights",
    ],
    featureOff: [
      "PDF Report",
      "Kundli Milan",
    ],
  },
  {
    key: "elite",
    name: "Elite",
    nameEn: "Elite",
    badge: "PREMIUM",
    badgeColor: "#a78bfa",
    accent: "#a78bfa",
    accentBg: "rgba(167,139,250,0.06)",
    border: "rgba(167,139,250,0.35)",
    monthlyPrice: 399,
    yearlyPrice: 2999,
    yearlySave: 37,
    cta: "Elite Lein",
    ctaActive: true,
    features: [
      "Unlimited Profiles",
      "Sab Pro Features",
      "Monthly PDF Horoscope Report",
      "Kundli Milan (Vivah Yog)",
      "Career & Finance Deep Analysis",
      "Priority Astrologer Chat",
      "Yearly Forecast",
    ],
    featureOff: [],
  },
];

// ── Profile Card ─────────────────────────────────────────────────────────────
function ProfileCard({
  profile, isPrimary, canDelete,
  onEdit, onSetPrimary, onDelete,
}: {
  profile: ProfileEntry;
  isPrimary: boolean;
  canDelete: boolean;
  onEdit: () => void;
  onSetPrimary: () => void;
  onDelete: () => void;
}) {
  const initials = profile.name
    .split(" ").map(w => w[0] ?? "").join("").slice(0, 2).toUpperCase() || "?";

  return (
    <View style={[pc.card, isPrimary && pc.cardPrimary]}>
      <View style={{ flexDirection:"row", alignItems:"center", gap:12 }}>
        <View style={[pc.avatar, isPrimary && pc.avatarPrimary]}>
          <Text style={pc.initials}>{initials}</Text>
        </View>
        <View style={{ flex:1, minWidth:0 }}>
          <View style={{ flexDirection:"row", alignItems:"center", gap:6 }}>
            <Text style={pc.name} numberOfLines={1}>{profile.name}</Text>
            {isPrimary && (
              <View style={pc.primaryBadge}>
                <Text style={pc.primaryBadgeText}>PRIMARY</Text>
              </View>
            )}
          </View>
          <Text style={pc.sub} numberOfLines={1}>
            {profile.gender ? `${profile.gender} · ` : ""}{profile.birthData.place}
          </Text>
          <Text style={pc.date}>
            {profile.birthData.day}/{profile.birthData.month}/{profile.birthData.year}
            {"  ·  "}
            {String(profile.birthData.hour).padStart(2,"0")}:{String(profile.birthData.minute).padStart(2,"0")} {profile.birthData.ampm}
          </Text>
        </View>
        <View style={{ flexDirection:"row", gap:4 }}>
          {canDelete && (
            <Pressable onPress={onDelete} style={pc.iconBtn} hitSlop={8}>
              <Feather name="trash-2" size={15} color="#f87171" />
            </Pressable>
          )}
          <Pressable onPress={onEdit} style={pc.iconBtn} hitSlop={8}>
            <Feather name="chevron-right" size={18} color="#334155" />
          </Pressable>
        </View>
      </View>
      {!isPrimary && (
        <Pressable onPress={onSetPrimary} style={pc.setPrimaryBtn}>
          <Feather name="star" size={12} color="#00d4ff" />
          <Text style={pc.setPrimaryText}>Set as Primary</Text>
        </Pressable>
      )}
      {isPrimary && (
        <View style={pc.activeRow}>
          <Feather name="check" size={12} color="#00a86b" />
          <Text style={pc.activeText}>Active profile — all calculations use this chart</Text>
        </View>
      )}
    </View>
  );
}

// ── Language Picker Modal ─────────────────────────────────────────────────────
function LangModal({ visible, current, onSelect, onClose }: {
  visible: boolean; current: string;
  onSelect: (code: string) => void; onClose: () => void;
}) {
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={lm.overlay} onPress={onClose}>
        <Pressable style={lm.sheet} onPress={e => e.stopPropagation()}>
          <View style={lm.handle} />
          <Text style={lm.title}>SELECT LANGUAGE</Text>
          {LANGUAGES.map(lang => (
            <Pressable key={lang.code} onPress={() => { onSelect(lang.code); onClose(); }}
              style={[lm.row, lang.code === current && lm.rowActive]}>
              <Text style={lm.native}>{lang.native}</Text>
              <View style={{ flexDirection:"row", alignItems:"center", gap:8 }}>
                <Text style={lm.langName}>{lang.name}</Text>
                {lang.code === current && <Feather name="check" size={16} color="#00d4ff" />}
              </View>
            </Pressable>
          ))}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

// ── Delete Confirm Modal ──────────────────────────────────────────────────────
function DeleteModal({ name, onConfirm, onCancel }: {
  name: string; onConfirm: () => void; onCancel: () => void;
}) {
  return (
    <Modal visible transparent animationType="fade" onRequestClose={onCancel}>
      <View style={dm.overlay}>
        <View style={dm.box}>
          <View style={dm.iconWrap}>
            <Feather name="trash-2" size={18} color="#f87171" />
          </View>
          <Text style={dm.title}>Delete Profile?</Text>
          <Text style={dm.body}>
            <Text style={{ color:"#dde8f4", fontWeight:"600" }}>{name}</Text>
            {" "}'s profile and chart data will be permanently deleted.
          </Text>
          <View style={dm.btnRow}>
            <Pressable onPress={onCancel} style={dm.cancelBtn}>
              <Text style={{ color:"#94a3b8", fontSize:14 }}>Cancel</Text>
            </Pressable>
            <Pressable onPress={onConfirm} style={dm.deleteBtn}>
              <Text style={{ color:"white", fontWeight:"700", fontSize:14 }}>Delete</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

// ── Subscription Plan Card ─────────────────────────────────────────────────────
function PlanCard({
  plan, cycle, isCurrent,
  onPress,
}: {
  plan: typeof PLANS[0];
  cycle: BillingCycle;
  isCurrent: boolean;
  onPress: () => void;
}) {
  const price = cycle === "yearly" ? plan.yearlyPrice : plan.monthlyPrice;
  const isFree = plan.key === "free";

  return (
    <View style={[
      sb.planCard,
      { borderColor: plan.border, backgroundColor: plan.accentBg },
      isCurrent && sb.planCardCurrent,
    ]}>
      {/* Badge row */}
      <View style={{ flexDirection:"row", alignItems:"center", justifyContent:"space-between", marginBottom:10 }}>
        <View style={{ flexDirection:"row", alignItems:"center", gap:8 }}>
          <Text style={[sb.planName, { color: plan.accent }]}>{plan.name}</Text>
          {isCurrent && (
            <View style={[sb.badge, { backgroundColor:`${plan.accent}20`, borderColor:`${plan.accent}40` }]}>
              <Text style={[sb.badgeText, { color:plan.accent }]}>ACTIVE</Text>
            </View>
          )}
        </View>
        {plan.badge && !isCurrent && (
          <View style={[sb.badge, { backgroundColor:`${plan.accent}15`, borderColor:`${plan.accent}35` }]}>
            <Text style={[sb.badgeText, { color:plan.accent }]}>{plan.badge}</Text>
          </View>
        )}
      </View>

      {/* Price */}
      <View style={{ flexDirection:"row", alignItems:"flex-end", gap:4, marginBottom:4 }}>
        {isFree ? (
          <Text style={[sb.price, { color: plan.accent }]}>FREE</Text>
        ) : (
          <>
            <Text style={[sb.priceCurrency, { color: plan.accent }]}>₹</Text>
            <Text style={[sb.price, { color: plan.accent }]}>{price.toLocaleString("en-IN")}</Text>
            <Text style={sb.pricePer}>/{cycle === "yearly" ? "year" : "month"}</Text>
          </>
        )}
      </View>

      {/* Yearly saving note */}
      {cycle === "yearly" && !isFree && (plan as any).yearlySave && (
        <View style={sb.savePill}>
          <Feather name="tag" size={9} color="#4ade80" />
          <Text style={sb.saveText}>Save {(plan as any).yearlySave}% vs monthly</Text>
        </View>
      )}

      {/* Divider */}
      <View style={[sb.separator, { backgroundColor:`${plan.accent}18`, marginTop: cycle === "yearly" && !isFree ? 12 : 14 }]} />

      {/* Features ON */}
      <View style={{ gap:7, marginTop:12 }}>
        {plan.features.map(f => (
          <View key={f} style={sb.featureRow}>
            <View style={[sb.featureDot, { backgroundColor:`${plan.accent}25` }]}>
              <Feather name="check" size={9} color={plan.accent} />
            </View>
            <Text style={sb.featureText}>{f}</Text>
          </View>
        ))}
        {plan.featureOff.map(f => (
          <View key={f} style={sb.featureRow}>
            <View style={[sb.featureDot, { backgroundColor:"rgba(255,255,255,0.04)" }]}>
              <Feather name="minus" size={9} color="#1e3a5f" />
            </View>
            <Text style={[sb.featureText, { color:"#1e3a5f" }]}>{f}</Text>
          </View>
        ))}
      </View>

      {/* CTA */}
      {plan.ctaActive ? (
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onPress(); }}
          style={({ pressed }) => [{ opacity: pressed ? 0.8 : 1, marginTop:16 }]}
        >
          <LinearGradient
            colors={plan.key === "pro"
              ? ["#0284c7", "#00d4ff"]
              : ["#7c3aed", "#a78bfa"]}
            start={{ x:0, y:0 }} end={{ x:1, y:0 }}
            style={sb.ctaBtn}
          >
            <Feather name={plan.key === "pro" ? "zap" : "star"} size={14} color="#fff" />
            <Text style={sb.ctaText}>{plan.cta}</Text>
          </LinearGradient>
        </Pressable>
      ) : (
        <View style={[sb.ctaBtnOutline, { borderColor:`${plan.accent}30`, marginTop:16 }]}>
          <Feather name="check-circle" size={14} color={plan.accent} />
          <Text style={[sb.ctaText, { color:plan.accent }]}>{plan.cta}</Text>
        </View>
      )}
    </View>
  );
}

// ── Main Profile Screen ───────────────────────────────────────────────────────
export default function ProfileScreen() {
  const insets = useSafeAreaInsets();
  const {
    profiles, primaryProfileId,
    deleteProfile, setPrimaryProfile,
    language, setLanguage,
    logout,
  } = useUser();

  const [notifications,  setNotifications]  = useState(true);
  const [showLang,       setShowLang]       = useState(false);
  const [confirmDelete,  setConfirmDelete]  = useState<string | null>(null);
  const [switching,      setSwitching]      = useState(false);
  const [billingCycle,   setBillingCycle]   = useState<BillingCycle>("monthly");
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  function handleSetPrimary(id: string) {
    setSwitching(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setTimeout(() => { setPrimaryProfile(id); setSwitching(false); }, 400);
  }

  function handleLogout() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
    logout();
    router.replace("/login");
  }

  const deleteTarget = confirmDelete ? profiles.find(p => p.id === confirmDelete) : null;

  return (
    <View style={{ flex:1, backgroundColor:"#020d1a" }}>

      {/* Switching overlay */}
      {switching && (
        <View style={s.switchOverlay}>
          <View style={s.switchBox}>
            <Feather name="refresh-cw" size={24} color="#00d4ff" style={{ marginBottom:10 }} />
            <Text style={{ color:"#00d4ff", fontSize:13, fontWeight:"600" }}>Switching profile...</Text>
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

      {/* Language picker */}
      <LangModal
        visible={showLang}
        current={language}
        onSelect={code => { setLanguage(code as "hi"); Haptics.selectionAsync(); }}
        onClose={() => setShowLang(false)}
      />

      <ScrollView
        contentContainerStyle={{ paddingTop: topPad + 16, paddingBottom: botPad + 80, paddingHorizontal:20, gap:28 }}
        showsVerticalScrollIndicator={false}
      >

        {/* ── PROFILES ──────────────────────────────────────────────────── */}
        <View>
          <Text style={s.sectionLabel}>MY PROFILES</Text>
          <View style={{ gap:12 }}>
            {profiles.length === 0 && (
              <Text style={{ color:"#334155", fontSize:13, textAlign:"center", paddingVertical:20 }}>
                No profiles found. Add one below.
              </Text>
            )}
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

            {/* Add Profile button */}
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push({ pathname:"/profile-edit", params:{ mode:"add" } }); }}
              style={({ pressed }) => [s.addBtn, pressed && { opacity:0.7 }]}
            >
              <View style={s.addCircle}>
                <Feather name="plus" size={16} color="#00d4ff" />
              </View>
              <View>
                <Text style={{ color:"#00d4ff", fontSize:13, fontWeight:"600" }}>Add New Profile</Text>
                <Text style={{ color:"#334155", fontSize:10, marginTop:2 }}>For family members or others</Text>
              </View>
            </Pressable>
          </View>
        </View>

        {/* ── SUBSCRIPTION ──────────────────────────────────────────────── */}
        <View>
          <Text style={s.sectionLabel}>SUBSCRIPTION</Text>

          {/* Billing cycle toggle */}
          <View style={sb.cycleRow}>
            <Pressable
              onPress={() => { setBillingCycle("monthly"); Haptics.selectionAsync(); }}
              style={[sb.cycleBtn, billingCycle === "monthly" && sb.cycleBtnActive]}
            >
              <Text style={[sb.cycleBtnText, billingCycle === "monthly" && sb.cycleBtnTextActive]}>
                Monthly
              </Text>
            </Pressable>
            <Pressable
              onPress={() => { setBillingCycle("yearly"); Haptics.selectionAsync(); }}
              style={[sb.cycleBtn, billingCycle === "yearly" && sb.cycleBtnActive]}
            >
              <Text style={[sb.cycleBtnText, billingCycle === "yearly" && sb.cycleBtnTextActive]}>
                Yearly
              </Text>
              <View style={sb.savePillInline}>
                <Text style={sb.savePillText}>44% OFF</Text>
              </View>
            </Pressable>
          </View>

          {/* Plan cards */}
          <View style={{ gap:12, marginTop:14 }}>
            {PLANS.map(plan => (
              <PlanCard
                key={plan.key}
                plan={plan}
                cycle={billingCycle}
                isCurrent={plan.key === "free"}
                onPress={() => {}}
              />
            ))}
          </View>
        </View>

        {/* ── SETTINGS ──────────────────────────────────────────────────── */}
        <View>
          <Text style={s.sectionLabel}>SETTINGS</Text>
          <View style={s.card}>

            {/* Notifications */}
            <View style={s.settingRow}>
              <Feather name="bell" size={15} color="#64748b" />
              <Text style={s.settingLabel}>Notifications</Text>
              <Switch
                value={notifications}
                onValueChange={v => { setNotifications(v); Haptics.selectionAsync(); }}
                trackColor={{ false:"#1e293b", true:"#00d4ff" }}
                thumbColor="#fff"
                ios_backgroundColor="#1e293b"
              />
            </View>

            <View style={s.divider} />

            {/* Language */}
            <Pressable style={s.settingRow} onPress={() => setShowLang(true)}>
              <Feather name="globe" size={15} color="#64748b" />
              <Text style={[s.settingLabel, { flex:1 }]}>Bhasha</Text>
              <Text style={{ color:"#00d4ff", fontSize:13, fontWeight:"600", marginRight:4 }}>
                {LANGUAGES.find(l => l.code === language)?.native ?? "हिंदी"}
              </Text>
              <Feather name="chevron-right" size={15} color="#334155" />
            </Pressable>

            <View style={s.divider} />

            {/* Support */}
            <View style={s.settingRow}>
              <Feather name="message-circle" size={15} color="#64748b" />
              <Text style={[s.settingLabel, { flex:1 }]}>Support</Text>
              <Pressable style={{ marginRight:8 }}
                onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}>
                <Feather name="message-square" size={16} color="#475569" />
              </Pressable>
              <Pressable onPress={() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light)}>
                <Feather name="phone" size={16} color="#475569" />
              </Pressable>
            </View>

          </View>
        </View>

        {/* ── LOGOUT ────────────────────────────────────────────────────── */}
        <Pressable onPress={handleLogout}
          style={({ pressed }) => [s.logoutRow, pressed && { opacity:0.7 }]}>
          <Feather name="log-out" size={15} color="#f87171" />
          <Text style={{ color:"#f87171", fontSize:14, fontWeight:"500" }}>Logout</Text>
        </Pressable>

      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  sectionLabel: { fontSize:10, fontWeight:"800", letterSpacing:2.5, color:"#00d4ff", marginBottom:12 },
  card: {
    backgroundColor:"#040e20", borderRadius:16,
    borderWidth:1, borderColor:"rgba(0,200,255,0.1)", overflow:"hidden",
  },
  divider: { height:1, backgroundColor:"#0a1828", marginHorizontal:16 },

  settingRow: {
    flexDirection:"row", alignItems:"center", gap:12,
    paddingHorizontal:16, paddingVertical:14,
  },
  settingLabel: { color:"#dde8f4", fontSize:14 },

  addBtn: {
    flexDirection:"row", alignItems:"center", gap:12, padding:14,
    backgroundColor:"rgba(0,212,255,0.04)",
    borderWidth:1, borderColor:"rgba(0,212,255,0.18)",
    borderRadius:14,
  },
  addCircle: {
    width:36, height:36, borderRadius:18,
    borderWidth:1, borderColor:"rgba(0,212,255,0.3)",
    alignItems:"center", justifyContent:"center",
    backgroundColor:"rgba(0,212,255,0.06)",
  },

  logoutRow: {
    flexDirection:"row", alignItems:"center", gap:8,
    paddingVertical:8, paddingHorizontal:4,
  },

  switchOverlay: {
    ...StyleSheet.absoluteFillObject, backgroundColor:"rgba(0,0,0,0.7)",
    alignItems:"center", justifyContent:"center", zIndex:999,
  },
  switchBox: { alignItems:"center" },
});

const sb = StyleSheet.create({
  cycleRow: {
    flexDirection:"row",
    backgroundColor:"#040e1f",
    borderRadius:12, borderWidth:1, borderColor:"rgba(255,255,255,0.06)",
    padding:4, gap:4,
  },
  cycleBtn: {
    flex:1, flexDirection:"row", alignItems:"center", justifyContent:"center",
    paddingVertical:9, borderRadius:9, gap:6,
  },
  cycleBtnActive: {
    backgroundColor:"#0c1f35",
    borderWidth:1, borderColor:"rgba(0,212,255,0.25)",
  },
  cycleBtnText:       { color:"#334155", fontSize:13, fontWeight:"600" },
  cycleBtnTextActive: { color:"#dde8f4" },

  savePillInline: {
    backgroundColor:"rgba(74,222,128,0.15)", borderRadius:8,
    paddingHorizontal:5, paddingVertical:2,
  },
  savePillText: { color:"#4ade80", fontSize:9, fontWeight:"700" },

  planCard: {
    borderRadius:18, borderWidth:1,
    padding:16,
  },
  planCardCurrent: {
    borderWidth:1,
  },

  planName: { fontSize:17, fontWeight:"800", letterSpacing:0.3 },

  badge: {
    borderRadius:20, borderWidth:1,
    paddingHorizontal:7, paddingVertical:2,
  },
  badgeText: { fontSize:9, fontWeight:"800", letterSpacing:1.5 },

  price: { fontSize:28, fontWeight:"800", lineHeight:32 },
  priceCurrency: { fontSize:16, fontWeight:"700", lineHeight:30, marginBottom:2 },
  pricePer: { color:"#334155", fontSize:13, lineHeight:30, marginBottom:2 },

  savePill: {
    flexDirection:"row", alignItems:"center", gap:4,
    backgroundColor:"rgba(74,222,128,0.1)", borderRadius:8,
    paddingHorizontal:8, paddingVertical:3, alignSelf:"flex-start",
  },
  saveText: { color:"#4ade80", fontSize:10, fontWeight:"600" },

  separator: { height:1 },

  featureRow: { flexDirection:"row", alignItems:"center", gap:8 },
  featureDot: {
    width:18, height:18, borderRadius:9,
    alignItems:"center", justifyContent:"center", flexShrink:0,
  },
  featureText: { color:"#94a3b8", fontSize:12, flex:1 },

  ctaBtn: {
    flexDirection:"row", alignItems:"center", justifyContent:"center", gap:7,
    borderRadius:12, paddingVertical:13,
  },
  ctaBtnOutline: {
    flexDirection:"row", alignItems:"center", justifyContent:"center", gap:7,
    borderRadius:12, paddingVertical:12, borderWidth:1,
  },
  ctaText: { color:"white", fontWeight:"700", fontSize:14 },
});

const pc = StyleSheet.create({
  card: {
    backgroundColor:"#040e20", borderRadius:16,
    borderWidth:1, borderColor:"#1e293b", padding:14,
  },
  cardPrimary: {
    backgroundColor:"#050f1c",
    borderColor:"rgba(0,212,255,0.25)",
  },
  avatar: {
    width:44, height:44, borderRadius:22,
    backgroundColor:"#1e293b",
    alignItems:"center", justifyContent:"center", flexShrink:0,
  },
  avatarPrimary: { backgroundColor:"#004d3a" },
  initials: { color:"white", fontWeight:"700", fontSize:15 },

  name: { color:"#dde8f4", fontSize:14, fontWeight:"600" },
  sub:  { color:"#475569", fontSize:11, marginTop:2 },
  date: { color:"#1e3a5f", fontSize:10, marginTop:2 },

  primaryBadge: {
    backgroundColor:"rgba(0,212,255,0.1)", borderRadius:20,
    paddingHorizontal:6, paddingVertical:2,
  },
  primaryBadgeText: { color:"#00d4ff", fontSize:9, fontWeight:"700", letterSpacing:1 },

  iconBtn: { padding:4 },

  setPrimaryBtn: {
    flexDirection:"row", alignItems:"center", justifyContent:"center", gap:6,
    marginTop:10, paddingVertical:8, borderRadius:10,
    borderWidth:1, borderColor:"#1e293b",
  },
  setPrimaryText: { color:"#00d4ff", fontSize:12, fontWeight:"600" },

  activeRow: {
    flexDirection:"row", alignItems:"center", justifyContent:"center", gap:5,
    marginTop:10,
  },
  activeText: { color:"#00a86b", fontSize:11 },
});

const lm = StyleSheet.create({
  overlay: { flex:1, backgroundColor:"rgba(0,0,0,0.7)", justifyContent:"flex-end" },
  sheet: { backgroundColor:"#0b1120", borderRadius:18, borderBottomLeftRadius:0, borderBottomRightRadius:0, paddingBottom:40 },
  handle: { width:36, height:4, backgroundColor:"#1e293b", borderRadius:2, alignSelf:"center", marginTop:12, marginBottom:20 },
  title: { fontSize:10, fontWeight:"800", letterSpacing:2.5, color:"#4b6a86", textAlign:"center", marginBottom:8 },
  row: { flexDirection:"row", alignItems:"center", justifyContent:"space-between", paddingVertical:16, paddingHorizontal:24 },
  rowActive: { backgroundColor:"rgba(0,212,255,0.06)" },
  native: { color:"#dde8f4", fontSize:16 },
  langName: { color:"#4b6a86", fontSize:13 },
});

const dm = StyleSheet.create({
  overlay: { flex:1, backgroundColor:"rgba(0,0,0,0.85)", alignItems:"center", justifyContent:"center", padding:24 },
  box: { backgroundColor:"#0f172a", borderRadius:20, padding:24, borderWidth:1, borderColor:"#1e293b", width:"100%" },
  iconWrap: { width:40, height:40, borderRadius:20, backgroundColor:"rgba(248,113,113,0.12)", alignItems:"center", justifyContent:"center", marginBottom:12 },
  title: { color:"white", fontSize:16, fontWeight:"700", marginBottom:8 },
  body: { color:"#64748b", fontSize:13, lineHeight:20, marginBottom:20 },
  btnRow: { flexDirection:"row", gap:10 },
  cancelBtn: { flex:1, paddingVertical:13, borderRadius:10, borderWidth:1, borderColor:"#1e293b", alignItems:"center" },
  deleteBtn: { flex:1, paddingVertical:13, borderRadius:10, backgroundColor:"#7f1d1d", alignItems:"center" },
});
