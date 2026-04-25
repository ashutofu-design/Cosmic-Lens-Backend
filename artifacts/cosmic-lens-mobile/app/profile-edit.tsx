import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import {
  ActivityIndicator, Animated, KeyboardAvoidingView, Modal, Platform,
  Pressable, ScrollView, StyleSheet, Text,
  TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { fetchKundliFromAPI } from "@/lib/kundliAPI";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import PickerModal from "@/components/PickerModal";
import type { BirthData } from "@/types";

import { API_BASE as BASE_URL, apiFetch } from "@/lib/apiConfig";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

const MONTHS   = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const CY       = new Date().getFullYear();
const DAYS_L   = Array.from({ length: 31 }, (_, i) => ({ label: String(i+1).padStart(2,"0"), value: String(i+1) }));
const MONTHS_L = MONTHS.map((m, i) => ({ label: m, value: String(i+1) }));
const YEARS_L  = Array.from({ length: CY-1900+1 }, (_, i) => { const y=CY-i; return { label: String(y), value: String(y) }; });
const HOURS_L  = Array.from({ length: 12 }, (_, i) => ({ label: String(i+1).padStart(2,"0"), value: String(i+1) }));
const MINS_L   = Array.from({ length: 60 }, (_, i) => ({ label: String(i).padStart(2,"0"), value: String(i) }));

const C_SUCCESS = "#16A34A";

const RELATIONS = [
  { key: "Self",      emoji: "🧘" },
  { key: "Husband",   emoji: "👨" },
  { key: "Wife",      emoji: "👩" },
  { key: "Son",       emoji: "👦" },
  { key: "Daughter",  emoji: "👧" },
  { key: "Father",    emoji: "👴" },
  { key: "Mother",    emoji: "👵" },
  { key: "Brother",   emoji: "🧑" },
  { key: "Sister",    emoji: "👱‍♀️" },
  { key: "Friend",    emoji: "🤝" },
  { key: "Other",     emoji: "👥" },
];

// Map a stored relation key (English, used as DB value) → localized display label
export function relationLabel(rel: string | null | undefined, t: ReturnType<typeof useT>): string {
  switch (rel) {
    case "Self":     return t.pe_relSelf;
    case "Husband":  return t.pe_relHusband;
    case "Wife":     return t.pe_relWife;
    case "Son":      return t.pe_relSon;
    case "Daughter": return t.pe_relDaughter;
    case "Father":   return t.pe_relFather;
    case "Mother":   return t.pe_relMother;
    case "Brother":  return t.pe_relBrother;
    case "Sister":   return t.pe_relSister;
    case "Friend":   return t.pe_relFriend;
    case "Other":    return t.pe_relOther;
    default:         return rel || "";
  }
}

function buildRelationItems(t: ReturnType<typeof useT>) {
  return RELATIONS.map(r => ({
    label: `${r.emoji}  ${relationLabel(r.key, t)}`,
    value: r.key,
  }));
}

interface GeoResult { label: string; lat: number; lon: number; tz: number; }

async function searchPlace(q: string): Promise<GeoResult[]> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const r = await apiFetch(
      `${BASE_URL}/api/geocode?q=${encodeURIComponent(q)}`,
      { signal: ctrl.signal },
    );
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const rows = await r.json();
    if (!Array.isArray(rows)) return [];
    return rows.map((x: { label: string; lat: number; lon: number; tz: number }) => ({
      label: x.label,
      lat: x.lat,
      lon: x.lon,
      tz: x.tz,
    }));
  } finally {
    clearTimeout(timer);
  }
}

type FormState = {
  name: string; gender: string;
  day: string; month: string; year: string;
  hour: string; minute: string; ampm: "AM" | "PM";
  place: string; lat: number; lon: number; tz: number;
};

function blank(): FormState {
  return { name:"", gender:"", day:"", month:"", year:"", hour:"", minute:"", ampm:"AM", place:"", lat:0, lon:0, tz:5.5 };
}

function Lbl({ text }: { text: string }) {
  const C = useC();
  return <Text style={[s.lbl, { color: C.isDark ? C.textMuted : "#64748B" }]}>{text}</Text>;
}

function PickerBtn({
  value, placeholder, onPress,
}: { value: string; placeholder: string; onPress: () => void }) {
  const C = useC();
  return (
    <Pressable
      onPress={() => { Haptics.selectionAsync(); onPress(); }}
      style={[s.pickerBtn, { backgroundColor: C.isDark ? C.inputBg : "#F1F5F9", borderColor: C.isDark ? C.inputBorder : "#CBD5E1" }]}
    >
      <Text style={[s.pickerTxt, { color: value ? C.text : C.textDim }]} numberOfLines={1}>
        {value || placeholder}
      </Text>
      <Feather name="chevron-down" size={10} color={C.textDim} />
    </Pressable>
  );
}

function HeroCard({ profile, onView, onEdit }: {
  profile: ProfileEntry; onView: () => void; onEdit: () => void;
}) {
  const C = useC();
  const t = useT();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const k = profile.kundli;
  const initials = profile.name.split(" ").map(w => w[0] ?? "").join("").slice(0, 2).toUpperCase() || "?";
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const [menuOpen, setMenuOpen] = useState(false);
  const astroLine = [k?.moonSign, k?.nakshatra, k?.ascendant].filter(Boolean).join(" \u2022 ") || "—";

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={() => Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true, speed: 50, bounciness: 0 }).start()}
        onPressOut={() => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 30, bounciness: 4 }).start()}
        onPress={onView}
      >
        <View style={[card.wrap, {
          backgroundColor: C.isDark ? "rgba(26,33,53,0.9)" : "#FFFFFF",
          borderColor: C.isDark ? `${ac}25` : `${ac}18`,
        }]}>
          <View style={card.row}>
            <LinearGradient colors={C.isDark ? ["#f59e0b", "#ef4444"] : ["#7C3AED", "#6D28D9"]} style={card.avatar}>
              <Text style={card.avatarTxt}>{initials}</Text>
            </LinearGradient>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Text style={[card.name, { color: C.text }]} numberOfLines={1}>{profile.name}</Text>
                <View style={[card.badge, { backgroundColor: `${ac}15` }]}>
                  <Feather name="star" size={7} color={ac} />
                  <Text style={[card.badgeTxt, { color: ac }]}>{t.pe_primary}</Text>
                </View>
              </View>
              <Text style={[card.astro, { color: C.isDark ? "rgba(250,204,21,0.8)" : "#7C3AED" }]} numberOfLines={1}>{astroLine}</Text>
            </View>
            <Pressable
              onPress={() => { Haptics.selectionAsync(); setMenuOpen(!menuOpen); }}
              hitSlop={10}
              style={[card.menuBtn, { backgroundColor: C.isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)" }]}
            >
              <Feather name="more-vertical" size={15} color={C.textMuted} />
            </Pressable>
          </View>

          {menuOpen && (
            <View style={[card.menuDrop, {
              backgroundColor: C.isDark ? "#1E2340" : "#FFFFFF",
              borderColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)",
              shadowColor: "#000",
            }]}>
              <Pressable onPress={() => { setMenuOpen(false); onView(); }} style={({ pressed }) => [card.menuItem, pressed && { opacity: 0.6 }]}>
                <Feather name="eye" size={13} color={C.isDark ? "#38bdf8" : "#7C3AED"} />
                <Text style={[card.menuTxt, { color: C.text }]}>{t.pe_viewKundli}</Text>
              </Pressable>
              <View style={{ height: StyleSheet.hairlineWidth, backgroundColor: C.isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }} />
              <Pressable onPress={() => { setMenuOpen(false); onEdit(); }} style={({ pressed }) => [card.menuItem, pressed && { opacity: 0.6 }]}>
                <Feather name="edit-3" size={13} color={ac} />
                <Text style={[card.menuTxt, { color: C.text }]}>{t.pe_editProfile}</Text>
              </Pressable>
            </View>
          )}
        </View>
      </Pressable>
    </Animated.View>
  );
}

function SecondaryCard({ profile, onView, onEdit, onDelete, onMakePrimary }: {
  profile: ProfileEntry; onView: () => void; onEdit: () => void;
  onDelete: () => void; onMakePrimary: () => void;
}) {
  const C = useC();
  const t = useT();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const k = profile.kundli;
  const initials = profile.name.split(" ").map(w => w[0] ?? "").join("").slice(0, 2).toUpperCase() || "?";
  const [menuOpen, setMenuOpen] = useState(false);
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const astroLine = [k?.moonSign, k?.nakshatra, k?.ascendant].filter(Boolean).join(" \u2022 ") || "—";

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        onPressIn={() => Animated.spring(scaleAnim, { toValue: 0.98, useNativeDriver: true, speed: 50, bounciness: 0 }).start()}
        onPressOut={() => Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 30, bounciness: 4 }).start()}
        onPress={onView}
      >
        <View style={[card.wrap, {
          backgroundColor: C.isDark ? "rgba(26,33,53,0.85)" : "#FFFFFF",
          borderColor: C.isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)",
        }]}>
          <View style={card.row}>
            <LinearGradient colors={C.isDark ? ["#0ea5e9", "#f59e0b"] : ["#7C3AED", "#a78bfa"]} style={card.avatar}>
              <Text style={card.avatarTxt}>{initials}</Text>
            </LinearGradient>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Text style={[card.name, { color: C.text }]} numberOfLines={1}>{profile.name}</Text>
                {profile.relation && profile.relation !== "Self" && (
                  <Text style={[card.relTag, { color: C.textDim, borderColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)" }]}>{relationLabel(profile.relation, t)}</Text>
                )}
              </View>
              <Text style={[card.astro, { color: C.textMuted }]} numberOfLines={1}>{astroLine}</Text>
            </View>
            <Pressable
              onPress={() => { Haptics.selectionAsync(); setMenuOpen(!menuOpen); }}
              hitSlop={10}
              style={[card.menuBtn, { backgroundColor: C.isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)" }]}
            >
              <Feather name="more-vertical" size={15} color={C.textMuted} />
            </Pressable>
          </View>

          {menuOpen && (
            <View style={[card.menuDrop, {
              backgroundColor: C.isDark ? "#1E2340" : "#FFFFFF",
              borderColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)",
              shadowColor: "#000",
            }]}>
              <Pressable onPress={() => { setMenuOpen(false); onMakePrimary(); }} style={({ pressed }) => [card.menuItem, pressed && { opacity: 0.6 }]}>
                <Feather name="star" size={13} color="#f59e0b" />
                <Text style={[card.menuTxt, { color: C.text }]}>{t.pe_setAsPrimary}</Text>
              </Pressable>
              <View style={{ height: StyleSheet.hairlineWidth, backgroundColor: C.isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }} />
              <Pressable onPress={() => { setMenuOpen(false); onEdit(); }} style={({ pressed }) => [card.menuItem, pressed && { opacity: 0.6 }]}>
                <Feather name="edit-3" size={13} color={ac} />
                <Text style={[card.menuTxt, { color: C.text }]}>{t.pe_editProfile}</Text>
              </Pressable>
              <View style={{ height: StyleSheet.hairlineWidth, backgroundColor: C.isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }} />
              <Pressable onPress={() => { setMenuOpen(false); onDelete(); }} style={({ pressed }) => [card.menuItem, pressed && { opacity: 0.6 }]}>
                <Feather name="trash-2" size={13} color="#f87171" />
                <Text style={[card.menuTxt, { color: "#f87171" }]}>{t.pe_delete}</Text>
              </Pressable>
            </View>
          )}
        </View>
      </Pressable>
    </Animated.View>
  );
}

export default function ProfileEditScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const {
    profiles, primaryProfileId, addProfile, updateProfile, deleteProfile,
    setBirthData, setKundli, syncKundliToCloud, setPrimaryProfile, user,
  } = useUser();

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const familyMembers = profiles.filter(p => p.id !== (primaryProfile?.id ?? ""));

  const [fmVisible, setFmVisible] = useState(false);
  const [fmEditId, setFmEditId]   = useState<string | null>(null);
  const [fmIsPrimary, setFmIsPrimary] = useState(false);
  const [fmForm, setFmForm]       = useState<FormState>(blank);
  const [fmRelation, setFmRelation] = useState("Father");
  const [fmPlaceQuery, setFmPlaceQuery] = useState("");
  const [fmGeoResults, setFmGeoResults] = useState<GeoResult[]>([]);
  const [fmSearching,  setFmSearching]  = useState(false);
  const [fmTzLoading,  setFmTzLoading]  = useState(false);
  const [fmSaving,     setFmSaving]     = useState(false);
  const [fmError,      setFmError]      = useState("");
  const [fmPlaceFocused, setFmPlaceFocused] = useState(false);
  const [fmNameFocused, setFmNameFocused]   = useState(false);

  const [fmDayOpen,   setFmDayOpen]   = useState(false);
  const [fmMonthOpen, setFmMonthOpen] = useState(false);
  const [fmYearOpen,  setFmYearOpen]  = useState(false);
  const [fmHourOpen,  setFmHourOpen]  = useState(false);
  const [fmMinOpen,   setFmMinOpen]   = useState(false);
  const [fmRelOpen,   setFmRelOpen]   = useState(false);

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const fmSet = (key: keyof FormState) => (val: string) =>
    setFmForm(prev => ({ ...prev, [key]: val }));

  function openFmAdd() {
    const isFirstEver = profiles.length === 0;
    setFmEditId(null);
    setFmIsPrimary(isFirstEver);
    setFmForm(blank());
    setFmRelation(isFirstEver ? "Self" : "Father");
    setFmPlaceQuery("");
    setFmGeoResults([]);
    setFmError("");
    setFmVisible(true);
  }

  function openPrimaryEdit() {
    if (!primaryProfile) return;
    setFmEditId(primaryProfile.id);
    setFmIsPrimary(true);
    const bd = primaryProfile.birthData;
    setFmForm({
      name: primaryProfile.name, gender: primaryProfile.gender ?? "",
      day: String(bd.day), month: String(bd.month), year: String(bd.year),
      hour: String(bd.hour), minute: String(bd.minute), ampm: bd.ampm,
      place: bd.place, lat: bd.lat, lon: bd.lon, tz: bd.tz,
    });
    setFmRelation(primaryProfile.relation ?? "Self");
    setFmPlaceQuery(bd.place);
    setFmGeoResults([]);
    setFmError("");
    setFmVisible(true);
  }

  function openFmEdit(p: ProfileEntry) {
    setFmEditId(p.id);
    setFmIsPrimary(false);
    const bd = p.birthData;
    setFmForm({
      name: p.name, gender: p.gender ?? "",
      day: String(bd.day), month: String(bd.month), year: String(bd.year),
      hour: String(bd.hour), minute: String(bd.minute), ampm: bd.ampm,
      place: bd.place, lat: bd.lat, lon: bd.lon, tz: bd.tz,
    });
    setFmRelation(p.relation ?? "Other");
    setFmPlaceQuery(bd.place);
    setFmGeoResults([]);
    setFmError("");
    setFmVisible(true);
  }

  async function handleFmPlaceSearch() {
    if (fmPlaceQuery.trim().length < 2) return;
    setFmSearching(true); setFmGeoResults([]); setFmError("");
    try {
      const results = await searchPlace(fmPlaceQuery);
      setFmGeoResults(results);
      if (results.length === 0) {
        setFmError("No matching place found. Try different spelling or a nearby city.");
      }
    } catch (e: any) {
      const msg = e?.name === "AbortError"
        ? "Search timed out. Check your internet and try again."
        : "Search failed. Please try again.";
      setFmError(msg);
    } finally {
      setFmSearching(false);
    }
  }

  async function fmSelectGeo(g: GeoResult) {
    setFmForm(prev => ({ ...prev, place: g.label, lat: g.lat, lon: g.lon, tz: g.tz }));
    setFmPlaceQuery(g.label); setFmGeoResults([]);
    setFmTzLoading(true);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    try {
      const r = await apiFetch(`${BASE_URL}/api/timezone?lat=${g.lat}&lon=${g.lon}`, { signal: ctrl.signal });
      const d = await r.json();
      if (typeof d.tz === "number") setFmForm(prev => ({ ...prev, tz: d.tz }));
    } catch {}
    finally { clearTimeout(timer); setFmTzLoading(false); }
  }

  async function handleFmSave() {
    if (!fmForm.name.trim())                        { setFmError("Name is required."); return; }
    if (!fmForm.day || !fmForm.month || !fmForm.year) { setFmError("Please complete the birth date."); return; }
    if (!fmForm.hour || !fmForm.minute)              { setFmError("Please enter the birth time."); return; }
    if (!fmForm.lat)                                  { setFmError("Please select a birth location."); return; }
    setFmError(""); setFmSaving(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const birthData: BirthData = {
        name: fmForm.name.trim(),
        day: Number(fmForm.day), month: Number(fmForm.month), year: Number(fmForm.year),
        hour: Number(fmForm.hour), minute: Number(fmForm.minute), ampm: fmForm.ampm,
        place: fmForm.place, lat: fmForm.lat, lon: fmForm.lon, tz: fmForm.tz,
      };
      const auth = user?.id && user?.api_key ? { user_id: user.id, api_key: user.api_key } : null;
      const kundli = await fetchKundliFromAPI(birthData, auth);
      if (fmEditId && fmIsPrimary) {
        updateProfile(fmEditId, { name: fmForm.name.trim(), gender: fmForm.gender, birthData, kundli });
        setBirthData(birthData);
        setKundli(kundli);
        syncKundliToCloud(birthData, kundli).catch(() => {});
      } else if (fmEditId) {
        updateProfile(fmEditId, { name: fmForm.name.trim(), gender: fmForm.gender, relation: fmRelation, birthData, kundli });
      } else if (fmIsPrimary) {
        // First-ever profile on a new account → save as primary (Self)
        const newEntry = addProfile({ name: fmForm.name.trim(), gender: fmForm.gender, relation: "Self", birthData, kundli });
        setPrimaryProfile(newEntry.id);
        setBirthData(birthData);
        setKundli(kundli);
        syncKundliToCloud(birthData, kundli).catch(() => {});
      } else {
        addProfile({ name: fmForm.name.trim(), gender: fmForm.gender, relation: fmRelation, birthData, kundli });
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setFmVisible(false);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Chart calculation failed.";
      setFmError(/network|timed out|connection|failed to fetch/i.test(msg)
        ? "Could not reach the server. Check your connection." : msg);
    } finally {
      setFmSaving(false);
    }
  }

  function handleFmDelete(id: string) {
    setConfirmDeleteId(id);
  }

  function confirmDelete() {
    if (confirmDeleteId) {
      deleteProfile(confirmDeleteId);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }
    setConfirmDeleteId(null);
  }

  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const bgColor = C.isDark ? C.bg : "#F8FAFC";
  const deleteTarget = confirmDeleteId ? profiles.find(p => p.id === confirmDeleteId) : null;

  return (
    <View style={{ flex: 1, backgroundColor: bgColor }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>

        <View style={[s.header, { paddingTop: insets.top + 8, backgroundColor: bgColor, borderBottomColor: C.isDark ? C.border : "rgba(0,0,0,0.05)" }]}>
          <Pressable
            onPress={() => router.back()}
            hitSlop={10}
            style={[s.backBtn, { backgroundColor: C.isDark ? C.bgCard2 : "#FFFFFF", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]}
          >
            <Feather name="arrow-left" size={16} color={C.isDark ? C.text : "#1E293B"} />
          </Pressable>
          <View style={{ flex: 1, gap: 2 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 7 }}>
              <View style={[s.headerAccentDot, { backgroundColor: C.accent }]} />
              <Text style={[s.headerTitle, { color: C.isDark ? C.text : "#0F172A" }]}>
                {t.editProfileTitle}
              </Text>
            </View>
            <Text style={[s.headerSub, { color: C.isDark ? C.textDim : "#94A3B8" }]}>
              {t.pe_manageProfile}
            </Text>
          </View>
        </View>

        <ScrollView
          contentContainerStyle={[s.scroll, { paddingBottom: insets.bottom + 90 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {primaryProfile && (
            <HeroCard
              profile={primaryProfile}
              onView={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/(tabs)/kundli"); }}
              onEdit={() => openPrimaryEdit()}
            />
          )}

          {familyMembers.length > 0 && (
            <View style={{ gap: 6, marginTop: 4 }}>
              <Text style={{ color: C.textMuted, fontSize: 9, fontFamily: F.bold, letterSpacing: 1.8, marginLeft: 4, marginBottom: 0 }}>{t.pe_otherProfiles}</Text>
              {familyMembers.map((p) => (
                <SecondaryCard
                  key={p.id}
                  profile={p}
                  onView={() => { setPrimaryProfile(p.id); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/(tabs)/kundli"); }}
                  onEdit={() => openFmEdit(p)}
                  onDelete={() => handleFmDelete(p.id)}
                  onMakePrimary={() => { setPrimaryProfile(p.id); Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); }}
                />
              ))}
            </View>
          )}

          {/* Recently Deleted entry */}
          <Pressable
            onPress={() => { Haptics.selectionAsync(); router.push("/recently-deleted"); }}
            style={({ pressed }) => [{
              marginTop: 14,
              padding: 14,
              borderRadius: 14,
              borderWidth: 1,
              borderColor: C.isDark ? C.border2 : "#E5E7EB",
              backgroundColor: C.isDark ? C.bgCard : "#FFFFFF",
              flexDirection: "row",
              alignItems: "center",
              gap: 12,
              opacity: pressed ? 0.85 : 1,
            }]}
          >
            <View style={{
              width: 36, height: 36, borderRadius: 18,
              backgroundColor: `${ac}15`,
              alignItems: "center", justifyContent: "center",
            }}>
              <Feather name="trash-2" size={16} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={{ color: C.text, fontSize: 14, fontFamily: F.bold }}>{t.pe_recentlyDeleted}</Text>
              <Text style={{ color: C.textMuted, fontSize: 11.5, fontFamily: F.medium, marginTop: 2 }}>
                Restore profiles within 24 hours
              </Text>
            </View>
            <Feather name="chevron-right" size={18} color={C.textMuted} />
          </Pressable>

          {!primaryProfile && familyMembers.length === 0 && (
            <View style={{ alignItems: "center", paddingVertical: 40, gap: 12 }}>
              <View style={{ width: 64, height: 64, borderRadius: 32, backgroundColor: `${ac}15`, alignItems: "center", justifyContent: "center" }}>
                <Feather name="star" size={28} color={ac} />
              </View>
              <Text style={{ color: C.text, fontSize: 17, fontFamily: F.bold }}>{t.pe_noKundliYet}</Text>
              <Text style={{ color: C.textMuted, fontSize: 12.5, fontFamily: F.medium, textAlign: "center", lineHeight: 19 }}>
                Add your birth details to generate{"\n"}your first kundli chart
              </Text>
            </View>
          )}
        </ScrollView>

        <View style={{ position: "absolute", bottom: insets.bottom + 20, left: 16, right: 16 }}>
          <Pressable
            onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); openFmAdd(); }}
            style={({ pressed }) => [{ opacity: pressed ? 0.85 : 1, transform: [{ scale: pressed ? 0.97 : 1 }] }]}
          >
            <LinearGradient
              colors={C.isDark ? ["#f59e0b", "#ef4444"] : ["#7C3AED", "#6D28D9"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={fab.btn}
            >
              <Feather name="plus" size={18} color="#fff" />
              <Text style={fab.txt}>{t.pe_addNewKundli}</Text>
            </LinearGradient>
          </Pressable>
        </View>

      </KeyboardAvoidingView>

      {/* ── Edit / Add Bottom Sheet ── */}
      <Modal visible={fmVisible} transparent animationType="slide" onRequestClose={() => setFmVisible(false)}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
        <View style={bs.overlay}>
          <Pressable
            style={StyleSheet.absoluteFillObject}
            onPress={() => { if (!fmSaving) setFmVisible(false); }}
          />
          <View style={[bs.sheet, { backgroundColor: C.isDark ? C.bgCard : "#FFFFFF" }]}>
            <View style={[bs.handle, { backgroundColor: C.isDark ? C.border2 : "#D4D4D8" }]} />

            <Text style={[bs.title, { color: C.text }]}>
              {fmIsPrimary ? t.pe_editProfile : fmEditId ? t.pe_editFamily : t.pe_addFamily}
            </Text>

            <ScrollView
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
              contentContainerStyle={{ paddingBottom: 20 }}
            >
              <View style={{ gap: 12 }}>
                <View style={s.fieldWrap}>
                  <Lbl text={t.pe_lblName} />
                  <View style={[
                    s.inputRow,
                    { backgroundColor: C.inputBg, borderColor: fmNameFocused ? C.inputFocusBorder : C.inputBorder },
                  ]}>
                    <Feather name="user" size={13} color={fmNameFocused ? C.accent : C.textDim} />
                    <TextInput
                      style={[s.inputTxt, { color: C.text }]}
                      value={fmForm.name}
                      onChangeText={v => { fmSet("name")(v); setFmError(""); }}
                      placeholder={t.pe_phName}
                      placeholderTextColor={C.textDim}
                      autoCapitalize="words"
                      returnKeyType="done"
                      onFocus={() => setFmNameFocused(true)}
                      onBlur={() => setFmNameFocused(false)}
                    />
                  </View>
                </View>

                <View style={s.fieldWrap}>
                  <Lbl text="GENDER (OPTIONAL)" />
                  <View style={{ flexDirection: "row", gap: 6 }}>
                    {[
                      { val: "Male", lbl: t.pe_male },
                      { val: "Female", lbl: t.pe_female },
                      { val: "Other", lbl: t.pe_other },
                    ].map(({ val, lbl }) => {
                      const active = fmForm.gender === val;
                      return (
                        <Pressable
                          key={val}
                          onPress={() => { setFmForm(prev => ({ ...prev, gender: val })); Haptics.selectionAsync(); }}
                          style={[
                            s.chip,
                            active
                              ? { borderColor: C.toggleSelBorder, backgroundColor: C.toggleSelBg }
                              : { borderColor: C.border, backgroundColor: "transparent" },
                          ]}
                        >
                          <Text style={[s.chipTxt, { color: active ? C.toggleSelText : C.textMuted }]}>{lbl}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                </View>

                {!fmIsPrimary && (
                  <View style={s.fieldWrap}>
                    <Lbl text={t.pe_lblRelation} />
                    <PickerBtn value={fmRelation} placeholder={t.pe_phSelect} onPress={() => setFmRelOpen(true)} />
                  </View>
                )}

                <View style={s.fieldWrap}>
                  <Lbl text={t.pe_lblDOB} />
                  <View style={{ flexDirection: "row", gap: 6 }}>
                    <View style={{ flex: 22 }}>
                      <PickerBtn value={fmForm.day ? String(fmForm.day).padStart(2,"0") : ""} placeholder={t.pe_phDD} onPress={() => setFmDayOpen(true)} />
                    </View>
                    <View style={{ flex: 36 }}>
                      <PickerBtn value={fmForm.month ? MONTHS[Number(fmForm.month)-1] : ""} placeholder={t.pe_phMonth} onPress={() => setFmMonthOpen(true)} />
                    </View>
                    <View style={{ flex: 42 }}>
                      <PickerBtn value={fmForm.year} placeholder={t.pe_phYear} onPress={() => setFmYearOpen(true)} />
                    </View>
                  </View>
                </View>

                <View style={s.fieldWrap}>
                  <Lbl text={t.pe_lblTOB} />
                  <View style={{ flexDirection: "row", gap: 6 }}>
                    <View style={{ flex: 28 }}>
                      <PickerBtn value={fmForm.hour ? String(fmForm.hour).padStart(2,"0") : ""} placeholder={t.pe_phHH} onPress={() => setFmHourOpen(true)} />
                    </View>
                    <View style={{ flex: 28 }}>
                      <PickerBtn value={fmForm.minute !== "" ? String(fmForm.minute).padStart(2,"0") : ""} placeholder={t.pe_phMM} onPress={() => setFmMinOpen(true)} />
                    </View>
                    <View style={{ flex: 44 }}>
                      <View style={{ flexDirection: "row", gap: 4 }}>
                        {(["AM", "PM"] as const).map(v => {
                          const active = fmForm.ampm === v;
                          return (
                            <Pressable
                              key={v}
                              onPress={() => { setFmForm(prev => ({ ...prev, ampm: v })); Haptics.selectionAsync(); }}
                              style={[
                                s.ampmBtn,
                                active
                                  ? { borderColor: C.toggleSelBorder, backgroundColor: C.toggleSelBg }
                                  : { borderColor: C.border, backgroundColor: C.inputBg },
                              ]}
                            >
                              <Text style={[s.ampmTxt, { color: active ? C.toggleSelText : C.textMuted }]}>{v}</Text>
                            </Pressable>
                          );
                        })}
                      </View>
                    </View>
                  </View>
                </View>

                <View style={s.fieldWrap}>
                  <Lbl text={t.pe_lblBirthPlace} />
                  <View style={[
                    s.inputRow,
                    { backgroundColor: C.inputBg, borderColor: fmPlaceFocused ? C.inputFocusBorder : C.inputBorder, gap: 6 },
                  ]}>
                    <Feather name="search" size={13} color={fmPlaceFocused ? C.accent : C.textDim} />
                    <TextInput
                      style={[s.inputTxt, { flex: 1, color: C.text }]}
                      value={fmPlaceQuery}
                      onChangeText={setFmPlaceQuery}
                      onSubmitEditing={handleFmPlaceSearch}
                      placeholder={t.pe_phCity}
                      placeholderTextColor={C.textDim}
                      returnKeyType="search"
                      onFocus={() => setFmPlaceFocused(true)}
                      onBlur={() => setFmPlaceFocused(false)}
                    />
                    <Pressable onPress={handleFmPlaceSearch} style={[s.searchBtn, { borderColor: ac }]}>
                      {fmSearching
                        ? <ActivityIndicator size="small" color={ac} />
                        : <Text style={[s.searchBtnTxt, { color: ac }]}>{t.pe_search}</Text>
                      }
                    </Pressable>
                  </View>
                </View>

                {fmGeoResults.length > 0 && (
                  <View style={[s.geoList, { backgroundColor: C.isDark ? C.bgCard2 : "#FFFFFF", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]}>
                    {fmGeoResults.map((g, i) => (
                      <Pressable
                        key={i}
                        onPress={() => { fmSelectGeo(g); Haptics.selectionAsync(); }}
                        style={[s.geoItem, i < fmGeoResults.length - 1 && { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.isDark ? C.border : "rgba(0,0,0,0.07)" }]}
                      >
                        <Feather name="map-pin" size={10} color={ac} style={{ marginTop: 1 }} />
                        <Text style={[s.geoTxt, { color: C.isDark ? C.textMid : "#334155" }]} numberOfLines={1}>{g.label}</Text>
                      </Pressable>
                    ))}
                  </View>
                )}

                {fmForm.lat !== 0 && (
                  <View style={[s.confirmedPlace, { backgroundColor: C.isDark ? "rgba(22,163,74,0.12)" : "#F0FDF4", borderColor: C.isDark ? "rgba(22,163,74,0.3)" : "#BBF7D0" }]}>
                    <Feather name="check-circle" size={12} color={C_SUCCESS} />
                    <Text style={[s.confirmedTxt, { color: C_SUCCESS }]} numberOfLines={1}>{fmForm.place}</Text>
                    {fmTzLoading && <ActivityIndicator size="small" color={C_SUCCESS} style={{ marginLeft: 4 }} />}
                  </View>
                )}
              </View>
            </ScrollView>

            {!!fmError && (
              <View style={[s.errorBox, { marginTop: 8 }]}>
                <Feather name="alert-circle" size={12} color="#DC2626" />
                <Text style={s.errorTxt}>{fmError}</Text>
              </View>
            )}

            <View style={[bs.btnRow, { borderTopColor: C.isDark ? C.border : "rgba(0,0,0,0.06)" }]}>
              <Pressable
                onPress={() => setFmVisible(false)}
                disabled={fmSaving}
                style={[bs.cancelBtn, { borderColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]}
              >
                <Text style={[bs.cancelTxt, { color: C.textMuted }]}>{t.cancel}</Text>
              </Pressable>
              <Pressable
                onPress={handleFmSave}
                disabled={fmSaving}
                style={{ flex: 1, opacity: fmSaving ? 0.65 : 1 }}
              >
                <LinearGradient
                  colors={[C.btnGradStart, C.btnGradEnd]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={bs.saveBtn}
                >
                  {fmSaving
                    ? <ActivityIndicator color="#fff" size="small" />
                    : <><Feather name={fmEditId ? "check" : "user-plus"} size={14} color="#fff" /><Text style={bs.saveTxt}>{fmEditId ? "Update" : "Add"}</Text></>
                  }
                </LinearGradient>
              </Pressable>
            </View>
          </View>
        </View>
        </KeyboardAvoidingView>

        {/* FM picker modals — MUST be inside the sheet Modal so they present on top on iOS */}
        <PickerModal visible={fmDayOpen}   title={t.pe_pickDay}      items={DAYS_L}        selected={fmForm.day}    onSelect={v => { fmSet("day")(v);    setFmDayOpen(false);   }} onClose={() => setFmDayOpen(false)}   />
        <PickerModal visible={fmMonthOpen} title={t.pe_pickMonth}    items={MONTHS_L}      selected={fmForm.month}  onSelect={v => { fmSet("month")(v);  setFmMonthOpen(false); }} onClose={() => setFmMonthOpen(false)} />
        <PickerModal visible={fmYearOpen}  title={t.pe_pickYear}     items={YEARS_L}       selected={fmForm.year}   onSelect={v => { fmSet("year")(v);   setFmYearOpen(false);  }} onClose={() => setFmYearOpen(false)}  />
        <PickerModal visible={fmHourOpen}  title={t.pe_pickHour}     items={HOURS_L}       selected={fmForm.hour}   onSelect={v => { fmSet("hour")(v);   setFmHourOpen(false);  }} onClose={() => setFmHourOpen(false)}  />
        <PickerModal visible={fmMinOpen}   title={t.pe_pickMinute}   items={MINS_L}        selected={fmForm.minute} onSelect={v => { fmSet("minute")(v); setFmMinOpen(false);   }} onClose={() => setFmMinOpen(false)}   />
        <PickerModal visible={fmRelOpen}   title={t.pe_pickRelation} items={buildRelationItems(t)} selected={fmRelation} onSelect={v => { setFmRelation(v); setFmRelOpen(false); }} onClose={() => setFmRelOpen(false)} />
      </Modal>

      {/* Delete Confirm */}
      {confirmDeleteId && deleteTarget && (
        <Modal visible transparent animationType="fade" onRequestClose={() => setConfirmDeleteId(null)}>
          <View style={del.overlay}>
            <View style={[del.box, { backgroundColor: C.isDark ? C.bgCard : "#FFFFFF", borderColor: "rgba(248,113,113,0.25)" }]}>
              <View style={del.iconWrap}>
                <Feather name="trash-2" size={20} color="#f87171" />
              </View>
              <Text style={[del.title, { color: C.text }]}>{t.pe_deleteMember}</Text>
              <Text style={[del.body, { color: C.textMuted }]}>
                <Text style={{ color: C.textMid, fontFamily: F.semibold }}>{deleteTarget.name}</Text>
                {" "}ka chart data permanently delete ho jayega.
              </Text>
              <View style={del.btnRow}>
                <Pressable onPress={() => setConfirmDeleteId(null)} style={[del.cancelBtn, { borderColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]}>
                  <Text style={{ color: C.textMuted, fontSize: 14, fontFamily: F.medium }}>Cancel</Text>
                </Pressable>
                <Pressable onPress={confirmDelete} style={del.deleteBtn}>
                  <Text style={{ color: "#fff", fontSize: 14, fontFamily: F.bold }}>Delete</Text>
                </Pressable>
              </View>
            </View>
          </View>
        </Modal>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 11,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: "center", justifyContent: "center",
    shadowColor: "#000", shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06, shadowRadius: 2, elevation: 1,
  },
  headerAccentDot: {
    width: 4, height: 16, borderRadius: 2,
    backgroundColor: "#6366F1", opacity: 0.7,
  },
  headerTitle: { fontSize: 16, fontFamily: F.bold, letterSpacing: -0.4 },
  headerSub:   { fontSize: 10.5, fontFamily: F.regular, marginLeft: 11 },

  scroll: { paddingHorizontal: 14, paddingTop: 10, paddingBottom: 16, gap: 6 },

  fieldWrap: { gap: 5 },
  lbl: { fontSize: 9.5, fontFamily: F.bold, letterSpacing: 1.3 },

  inputRow: {
    flexDirection: "row", alignItems: "center",
    borderRadius: 10, borderWidth: 0.75,
    paddingHorizontal: 10, minHeight: 44,
    gap: 7,
  },
  inputTxt: {
    flex: 1, fontSize: 13.5, fontFamily: F.semibold,
    padding: 0, margin: 0,
  },

  pickerBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    borderRadius: 10, borderWidth: 0.75,
    paddingHorizontal: 9, paddingVertical: 0,
    minHeight: 44, gap: 4,
  },
  pickerTxt: { flex: 1, fontSize: 13, fontFamily: F.semibold },

  chip: {
    flex: 1, paddingVertical: 8, borderRadius: 10, alignItems: "center",
    borderWidth: 0.75,
  },
  chipTxt: { fontSize: 12.5, fontFamily: F.bold },

  ampmBtn: {
    flex: 1, height: 44, borderRadius: 10, alignItems: "center",
    justifyContent: "center", borderWidth: 0.75,
  },
  ampmTxt: { fontSize: 13, fontFamily: F.bold },

  timeHint: { fontSize: 11, fontFamily: F.regular, marginTop: 4, opacity: 0.75 },

  searchBtn: {
    paddingHorizontal: 11, paddingVertical: 6,
    borderRadius: 8, backgroundColor: "transparent",
    borderWidth: 0.75,
  },
  searchBtnTxt: { fontSize: 11.5, fontFamily: F.bold },

  geoList: {
    borderRadius: 10, borderWidth: StyleSheet.hairlineWidth, overflow: "hidden",
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08, shadowRadius: 6, elevation: 2,
  },
  geoItem: {
    flexDirection: "row", alignItems: "center", gap: 7,
    paddingHorizontal: 12, paddingVertical: 10,
  },
  geoTxt: { fontSize: 12, fontFamily: F.medium, flex: 1 },

  confirmedPlace: {
    flexDirection: "row", alignItems: "center", gap: 7,
    borderRadius: 9, borderWidth: 0.75,
    paddingHorizontal: 10, paddingVertical: 7,
  },
  confirmedTxt: { fontSize: 12, fontFamily: F.semibold, flex: 1 },


  errorBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    backgroundColor: "rgba(220,38,38,0.05)",
    borderWidth: 0.75, borderColor: "rgba(220,38,38,0.2)",
    borderRadius: 11, paddingHorizontal: 12, paddingVertical: 10,
  },
  errorTxt:  { color: "#DC2626", fontSize: 12.5, fontFamily: F.semibold },
  errorHint: { color: "#EF4444", fontSize: 10.5, fontFamily: F.regular, marginTop: 3, lineHeight: 15 },

});

const card = StyleSheet.create({
  wrap: {
    borderRadius: 14, borderWidth: 1, paddingVertical: 10, paddingHorizontal: 12,
  },
  row: { flexDirection: "row", alignItems: "center", gap: 10 },
  avatar: {
    width: 36, height: 36, borderRadius: 18,
    alignItems: "center", justifyContent: "center",
  },
  avatarTxt: { color: "#fff", fontSize: 13, fontFamily: F.bold },
  name: { fontSize: 13.5, fontFamily: F.bold, flexShrink: 1 },
  badge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6,
  },
  badgeTxt: { fontSize: 7.5, fontFamily: F.bold, letterSpacing: 0.6 },
  relTag: {
    fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5,
    borderWidth: 0.75, borderRadius: 5,
    paddingHorizontal: 5, paddingVertical: 1,
  },
  astro: { fontSize: 11.5, fontFamily: F.medium, marginTop: 2 },
  menuBtn: {
    width: 30, height: 30, borderRadius: 9,
    alignItems: "center", justifyContent: "center",
  },
  menuDrop: {
    borderRadius: 12, borderWidth: 1, overflow: "hidden", marginTop: 6,
    shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 6,
  },
  menuItem: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 11, paddingHorizontal: 14,
  },
  menuTxt: { fontSize: 12.5, fontFamily: F.semibold },
});

const fab = StyleSheet.create({
  btn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 10, height: 54, borderRadius: 16,
    shadowColor: "#000", shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3, shadowRadius: 16, elevation: 10,
  },
  txt: { color: "#fff", fontSize: 15, fontFamily: F.bold, letterSpacing: 0.3 },
});

const bs = StyleSheet.create({
  overlay: {
    flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end",
  },
  sheet: {
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    paddingHorizontal: 18, paddingBottom: 28, paddingTop: 12,
    maxHeight: "85%",
  },
  handle: {
    width: 36, height: 4, borderRadius: 2,
    alignSelf: "center", marginBottom: 16,
  },
  title: {
    fontSize: 17, fontFamily: F.bold, letterSpacing: -0.3,
    marginBottom: 16,
  },
  btnRow: {
    flexDirection: "row", gap: 10, marginTop: 14,
    paddingTop: 14, borderTopWidth: StyleSheet.hairlineWidth,
  },
  cancelBtn: {
    flex: 0.5, alignItems: "center", paddingVertical: 13, borderRadius: 12,
    borderWidth: 1,
  },
  cancelTxt: { fontSize: 14, fontFamily: F.medium },
  saveBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 13, borderRadius: 12,
  },
  saveTxt: { color: "#fff", fontSize: 14, fontFamily: F.bold },
});

const del = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.8)", alignItems: "center", justifyContent: "center" },
  box: {
    width: 300, borderRadius: 20, borderWidth: 1,
    padding: 24, alignItems: "center", gap: 10,
  },
  iconWrap: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: "rgba(248,113,113,0.1)", alignItems: "center", justifyContent: "center",
  },
  title: { fontSize: 17, fontFamily: F.bold, textAlign: "center" },
  body:  { fontSize: 13, fontFamily: F.regular, textAlign: "center", lineHeight: 19 },
  btnRow: { flexDirection: "row", gap: 12, marginTop: 8 },
  cancelBtn: {
    flex: 1, alignItems: "center", paddingVertical: 11, borderRadius: 12,
    borderWidth: 1, backgroundColor: "rgba(255,255,255,0.03)",
  },
  deleteBtn: {
    flex: 1, alignItems: "center", paddingVertical: 11, borderRadius: 12,
    backgroundColor: "#b91c1c",
  },
});
