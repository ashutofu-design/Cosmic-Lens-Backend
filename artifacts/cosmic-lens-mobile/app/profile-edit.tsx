import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator, KeyboardAvoidingView, Modal, Platform,
  Pressable, ScrollView, StyleSheet, Text,
  TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { fetchKundliFromAPI } from "@/lib/kundliAPI";
import { useC } from "@/context/ThemeContext";
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
const RELATION_ITEMS = RELATIONS.map(r => ({ label: `${r.emoji}  ${r.key}`, value: r.key }));

interface GeoResult { label: string; lat: number; lon: number; tz: number; }

async function searchPlace(q: string): Promise<GeoResult[]> {
  const r = await fetch(
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5&addressdetails=1`,
  );
  const rows = await r.json();
  return rows.map((x: { display_name: string; lat: string; lon: string }) => ({
    label: x.display_name.split(",").slice(0, 3).join(", "),
    lat: parseFloat(x.lat), lon: parseFloat(x.lon),
    tz: Math.round((parseFloat(x.lon) / 15) * 2) / 2,
  }));
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

function Card({ children, style }: { children: React.ReactNode; style?: object }) {
  const C = useC();
  return (
    <View style={[
      s.card,
      C.isDark
        ? { backgroundColor: C.bgCard, shadowOpacity: 0.28 }
        : { backgroundColor: "#FFFFFF" },
      style,
    ]}>
      {children}
    </View>
  );
}

function CardRow({ label, icon }: { label: string; icon: React.ComponentProps<typeof Feather>["name"] }) {
  const C = useC();
  return (
    <View style={s.cardRow}>
      <View style={[s.cardRowIcon, { backgroundColor: C.accentBg }]}>
        <Feather name={icon} size={11} color={C.accent} />
      </View>
      <Text style={[s.cardRowLabel, { color: C.isDark ? C.textMuted : "#64748B" }]}>{label}</Text>
    </View>
  );
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

function ProfileRow({ profile, isPrimary, onView, onEdit, onDelete, onMakePrimary, canDelete }: {
  profile: ProfileEntry; isPrimary: boolean; canDelete: boolean;
  onView: () => void; onEdit: () => void; onDelete: () => void; onMakePrimary?: () => void;
}) {
  const C = useC();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const relInfo = RELATIONS.find(r => r.key === profile.relation);
  const bd = profile.birthData;
  const k = profile.kundli;
  const rashi = k?.moonSign ?? "—";
  const naksh = k?.nakshatra ?? "—";
  const lagna = k?.ascendant ?? "—";
  const initials = profile.name.split(" ").map(w => w[0] ?? "").join("").slice(0, 2).toUpperCase() || "?";

  return (
    <View style={fm.row}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
        <LinearGradient
          colors={isPrimary
            ? (C.isDark ? ["#f59e0b", "#ef4444"] : ["#7C3AED", "#6D28D9"])
            : (C.isDark ? ["#0ea5e9", "#f59e0b"] : ["#7C3AED", "#a78bfa"])}
          style={fm.avatar}
        >
          <Text style={fm.initials}>{relInfo?.emoji ?? initials}</Text>
        </LinearGradient>

        <View style={{ flex: 1, minWidth: 0 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 5, flexWrap: "wrap" }}>
            <Text style={[fm.name, { color: C.text }]} numberOfLines={1}>{profile.name}</Text>
            {isPrimary && (
              <View style={[fm.primaryBadge, {
                backgroundColor: C.isDark ? "#16a34a" : "#16a34a",
                borderColor: C.isDark ? "#22c55e" : "#16a34a",
              }]}>
                <Feather name="check-circle" size={7} color="#fff" />
                <Text style={{ color: "#fff", fontSize: 7.5, fontFamily: F.bold, letterSpacing: 0.6 }}>PRIMARY</Text>
              </View>
            )}
            {!isPrimary && profile.relation && (
              <View style={[fm.relBadge, { backgroundColor: C.isDark ? "rgba(245,158,11,0.1)" : "rgba(124,58,237,0.08)", borderColor: C.isDark ? "rgba(245,158,11,0.2)" : "rgba(124,58,237,0.15)" }]}>
                <Text style={[fm.relTxt, { color: ac }]}>{profile.relation}</Text>
              </View>
            )}
          </View>
          {!isPrimary && onMakePrimary && (
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onMakePrimary(); }}
              style={({ pressed }) => [fm.makePrimaryBtn, {
                borderColor: C.isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.12)",
                backgroundColor: C.isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.03)",
                opacity: pressed ? 0.6 : 1,
              }]}
            >
              <Feather name="arrow-up-circle" size={9} color={C.textMuted} />
              <Text style={{ color: C.textMuted, fontSize: 8.5, fontFamily: F.semibold, letterSpacing: 0.2 }}>Set as Primary</Text>
            </Pressable>
          )}
        </View>

        <View style={{ flexDirection: "row", gap: 5 }}>
          <Pressable onPress={onView} hitSlop={6} style={[fm.iconBtn, { backgroundColor: C.isDark ? "rgba(14,165,233,0.08)" : "rgba(124,58,237,0.06)", borderColor: C.isDark ? "rgba(14,165,233,0.18)" : "rgba(124,58,237,0.12)" }]}>
            <Feather name="eye" size={12} color={C.isDark ? "#38bdf8" : "#7C3AED"} />
          </Pressable>
          <Pressable onPress={onEdit} hitSlop={6} style={[fm.iconBtn, { backgroundColor: C.isDark ? C.bgCard2 : "#F1F5F9", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]}>
            <Feather name="edit-3" size={12} color={C.textMuted} />
          </Pressable>
          {canDelete && (
            <Pressable onPress={onDelete} hitSlop={6} style={[fm.iconBtn, { backgroundColor: C.isDark ? "rgba(248,113,113,0.08)" : "rgba(248,113,113,0.06)", borderColor: C.isDark ? "rgba(248,113,113,0.15)" : "rgba(248,113,113,0.12)" }]}>
              <Feather name="trash-2" size={12} color="#f87171" />
            </Pressable>
          )}
        </View>
      </View>

      <View style={[fm.astroRow, { backgroundColor: C.isDark ? C.bgCard2 : "#F8FAFC", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.05)" }]}>
        <View style={fm.astroItem}>
          <Text style={[fm.astroLabel, { color: C.textDim }]}>Rashi</Text>
          <Text style={[fm.astroValue, { color: C.isDark ? "#facc15" : "#7C3AED" }]}>{rashi}</Text>
        </View>
        <View style={[fm.astroDivider, { backgroundColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]} />
        <View style={fm.astroItem}>
          <Text style={[fm.astroLabel, { color: C.textDim }]}>Nakshatra</Text>
          <Text style={[fm.astroValue, { color: C.isDark ? "#facc15" : "#7C3AED" }]}>{naksh}</Text>
        </View>
        <View style={[fm.astroDivider, { backgroundColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]} />
        <View style={fm.astroItem}>
          <Text style={[fm.astroLabel, { color: C.textDim }]}>Lagna</Text>
          <Text style={[fm.astroValue, { color: C.isDark ? "#facc15" : "#7C3AED" }]}>{lagna}</Text>
        </View>
      </View>
    </View>
  );
}

export default function ProfileEditScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const {
    profiles, primaryProfileId, addProfile, updateProfile, deleteProfile,
    setBirthData, setKundli, syncKundliToCloud, setPrimaryProfile,
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
    setFmEditId(null);
    setFmIsPrimary(false);
    setFmForm(blank());
    setFmRelation("Father");
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
    setFmSearching(true); setFmGeoResults([]);
    try { setFmGeoResults(await searchPlace(fmPlaceQuery)); }
    catch { setFmError("Location not found."); }
    finally { setFmSearching(false); }
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
      const kundli = await fetchKundliFromAPI(birthData);
      if (fmEditId && fmIsPrimary) {
        updateProfile(fmEditId, { name: fmForm.name.trim(), gender: fmForm.gender, birthData, kundli });
        setBirthData(birthData);
        setKundli(kundli);
        syncKundliToCloud(birthData, kundli).catch(() => {});
      } else if (fmEditId) {
        updateProfile(fmEditId, { name: fmForm.name.trim(), gender: fmForm.gender, relation: fmRelation, birthData, kundli });
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
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>

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
                Edit Profile
              </Text>
            </View>
            <Text style={[s.headerSub, { color: C.isDark ? C.textDim : "#94A3B8" }]}>
              Manage your profile & family members
            </Text>
          </View>
        </View>

        <ScrollView
          contentContainerStyle={s.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >

          {/* ── MY KUNDLIS — unified compact list ── */}
          <Card style={{ paddingVertical: 10, gap: 6 }}>
            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
              <CardRow label="MY KUNDLIS" icon="users" />
              <Pressable
                onPress={openFmAdd}
                hitSlop={8}
                style={({ pressed }) => [fm.addBtn, {
                  backgroundColor: C.isDark ? "rgba(245,158,11,0.1)" : "rgba(124,58,237,0.08)",
                  borderColor: C.isDark ? "rgba(245,158,11,0.22)" : "rgba(124,58,237,0.2)",
                }, pressed && { opacity: 0.7 }]}
              >
                <Feather name="plus" size={11} color={ac} />
                <Text style={{ color: ac, fontSize: 10.5, fontFamily: F.bold }}>Add</Text>
              </Pressable>
            </View>

            {/* Primary profile row */}
            {primaryProfile && (
              <ProfileRow
                profile={primaryProfile}
                isPrimary
                canDelete={false}
                onView={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/(tabs)/kundli"); }}
                onEdit={() => openPrimaryEdit()}
                onDelete={() => {}}
              />
            )}

            {/* Family member rows */}
            {familyMembers.map((p) => (
              <React.Fragment key={p.id}>
                <View style={[fm.divider, { backgroundColor: C.isDark ? C.border : "rgba(0,0,0,0.06)" }]} />
                <ProfileRow
                  profile={p}
                  isPrimary={false}
                  canDelete
                  onView={() => { setPrimaryProfile(p.id); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/(tabs)/kundli"); }}
                  onEdit={() => openFmEdit(p)}
                  onDelete={() => handleFmDelete(p.id)}
                  onMakePrimary={() => { setPrimaryProfile(p.id); Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); }}
                />
              </React.Fragment>
            ))}

            {/* Empty state for no family members */}
            {familyMembers.length === 0 && (
              <>
                <View style={[fm.divider, { backgroundColor: C.isDark ? C.border : "rgba(0,0,0,0.06)" }]} />
                <Pressable
                  onPress={openFmAdd}
                  style={({ pressed }) => [fm.emptyRow, { backgroundColor: C.isDark ? C.bgCard2 : "#F8FAFC", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.06)" }, pressed && { opacity: 0.7 }]}
                >
                  <Feather name="user-plus" size={14} color={C.textDim} />
                  <Text style={{ color: C.textMuted, fontSize: 11.5, fontFamily: F.medium }}>Tap to add family members</Text>
                </Pressable>
              </>
            )}
          </Card>

          <View style={{ height: 8 }} />
        </ScrollView>

      </KeyboardAvoidingView>

      {/* ── Edit / Add Bottom Sheet ── */}
      <Modal visible={fmVisible} transparent animationType="slide" onRequestClose={() => setFmVisible(false)}>
        <Pressable style={bs.overlay} onPress={() => !fmSaving && setFmVisible(false)}>
          <Pressable style={[bs.sheet, { backgroundColor: C.isDark ? C.bgCard : "#FFFFFF" }]} onPress={e => e.stopPropagation()}>
            <View style={[bs.handle, { backgroundColor: C.isDark ? C.border2 : "#D4D4D8" }]} />

            <Text style={[bs.title, { color: C.text }]}>
              {fmIsPrimary ? "Edit Profile" : fmEditId ? "Edit Family Member" : "Add Family Member"}
            </Text>

            <ScrollView
              style={{ maxHeight: 420 }}
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
            >
              <View style={{ gap: 12 }}>
                <View style={s.fieldWrap}>
                  <Lbl text="NAME" />
                  <View style={[
                    s.inputRow,
                    { backgroundColor: C.inputBg, borderColor: fmNameFocused ? C.inputFocusBorder : C.inputBorder },
                  ]}>
                    <Feather name="user" size={13} color={fmNameFocused ? C.accent : C.textDim} />
                    <TextInput
                      style={[s.inputTxt, { color: C.text }]}
                      value={fmForm.name}
                      onChangeText={v => { fmSet("name")(v); setFmError(""); }}
                      placeholder="Full name"
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
                    {["Male", "Female", "Other"].map(g => {
                      const active = fmForm.gender === g;
                      return (
                        <Pressable
                          key={g}
                          onPress={() => { setFmForm(prev => ({ ...prev, gender: g })); Haptics.selectionAsync(); }}
                          style={[
                            s.chip,
                            active
                              ? { borderColor: C.toggleSelBorder, backgroundColor: C.toggleSelBg }
                              : { borderColor: C.border, backgroundColor: "transparent" },
                          ]}
                        >
                          <Text style={[s.chipTxt, { color: active ? C.toggleSelText : C.textMuted }]}>{g}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                </View>

                {!fmIsPrimary && (
                  <View style={s.fieldWrap}>
                    <Lbl text="RELATION" />
                    <PickerBtn value={fmRelation} placeholder="Select" onPress={() => setFmRelOpen(true)} />
                  </View>
                )}

                <View style={s.fieldWrap}>
                  <Lbl text="DATE OF BIRTH" />
                  <View style={{ flexDirection: "row", gap: 6 }}>
                    <View style={{ flex: 22 }}>
                      <PickerBtn value={fmForm.day ? String(fmForm.day).padStart(2,"0") : ""} placeholder="DD" onPress={() => setFmDayOpen(true)} />
                    </View>
                    <View style={{ flex: 36 }}>
                      <PickerBtn value={fmForm.month ? MONTHS[Number(fmForm.month)-1] : ""} placeholder="Month" onPress={() => setFmMonthOpen(true)} />
                    </View>
                    <View style={{ flex: 42 }}>
                      <PickerBtn value={fmForm.year} placeholder="Year" onPress={() => setFmYearOpen(true)} />
                    </View>
                  </View>
                </View>

                <View style={s.fieldWrap}>
                  <Lbl text="TIME OF BIRTH" />
                  <View style={{ flexDirection: "row", gap: 6 }}>
                    <View style={{ flex: 28 }}>
                      <PickerBtn value={fmForm.hour ? String(fmForm.hour).padStart(2,"0") : ""} placeholder="HH" onPress={() => setFmHourOpen(true)} />
                    </View>
                    <View style={{ flex: 28 }}>
                      <PickerBtn value={fmForm.minute !== "" ? String(fmForm.minute).padStart(2,"0") : ""} placeholder="MM" onPress={() => setFmMinOpen(true)} />
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
                  <Lbl text="BIRTH PLACE" />
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
                      placeholder="City, Country"
                      placeholderTextColor={C.textDim}
                      returnKeyType="search"
                      onFocus={() => setFmPlaceFocused(true)}
                      onBlur={() => setFmPlaceFocused(false)}
                    />
                    <Pressable onPress={handleFmPlaceSearch} style={[s.searchBtn, { borderColor: ac }]}>
                      {fmSearching
                        ? <ActivityIndicator size="small" color={ac} />
                        : <Text style={[s.searchBtnTxt, { color: ac }]}>Search</Text>
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
                <Text style={[bs.cancelTxt, { color: C.textMuted }]}>Cancel</Text>
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
          </Pressable>
        </Pressable>
      </Modal>

      {/* FM picker modals */}
      <PickerModal visible={fmDayOpen}   title="Select Day"        items={DAYS_L}        selected={fmForm.day}    onSelect={v => { fmSet("day")(v);    setFmDayOpen(false);   }} onClose={() => setFmDayOpen(false)}   />
      <PickerModal visible={fmMonthOpen} title="Select Month"      items={MONTHS_L}      selected={fmForm.month}  onSelect={v => { fmSet("month")(v);  setFmMonthOpen(false); }} onClose={() => setFmMonthOpen(false)} />
      <PickerModal visible={fmYearOpen}  title="Select Birth Year" items={YEARS_L}       selected={fmForm.year}   onSelect={v => { fmSet("year")(v);   setFmYearOpen(false);  }} onClose={() => setFmYearOpen(false)}  />
      <PickerModal visible={fmHourOpen}  title="Select Hour"       items={HOURS_L}       selected={fmForm.hour}   onSelect={v => { fmSet("hour")(v);   setFmHourOpen(false);  }} onClose={() => setFmHourOpen(false)}  />
      <PickerModal visible={fmMinOpen}   title="Select Minute"     items={MINS_L}        selected={fmForm.minute} onSelect={v => { fmSet("minute")(v); setFmMinOpen(false);   }} onClose={() => setFmMinOpen(false)}   />
      <PickerModal visible={fmRelOpen}   title="Select Relation"   items={RELATION_ITEMS} selected={fmRelation} onSelect={v => { setFmRelation(v); setFmRelOpen(false); }} onClose={() => setFmRelOpen(false)} />

      {/* Delete Confirm */}
      {confirmDeleteId && deleteTarget && (
        <Modal visible transparent animationType="fade" onRequestClose={() => setConfirmDeleteId(null)}>
          <View style={del.overlay}>
            <View style={[del.box, { backgroundColor: C.isDark ? C.bgCard : "#FFFFFF", borderColor: "rgba(248,113,113,0.25)" }]}>
              <View style={del.iconWrap}>
                <Feather name="trash-2" size={20} color="#f87171" />
              </View>
              <Text style={[del.title, { color: C.text }]}>Delete Member?</Text>
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

  scroll: { paddingHorizontal: 14, paddingTop: 12, paddingBottom: 16, gap: 10 },

  card: {
    borderRadius: 16, overflow: "hidden",
    paddingHorizontal: 14, paddingVertical: 13,
    gap: 11,
    shadowColor: "#64748B", shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10, shadowRadius: 12, elevation: 4,
  },

  cardRow: { flexDirection: "row", alignItems: "center", gap: 7 },
  cardRowIcon: { width: 22, height: 22, borderRadius: 7, alignItems: "center", justifyContent: "center" },
  cardRowLabel: { fontSize: 9.5, fontFamily: F.bold, letterSpacing: 1.4 },

  divider: { height: StyleSheet.hairlineWidth, marginVertical: 2 },

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

const fm = StyleSheet.create({
  row: { paddingVertical: 6, gap: 6 },
  avatar: {
    width: 34, height: 34, borderRadius: 17,
    alignItems: "center", justifyContent: "center",
  },
  initials: { color: "#fff", fontSize: 13, fontFamily: F.bold },
  name: { fontSize: 13, fontFamily: F.bold, flexShrink: 1 },
  primaryBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    borderRadius: 6, borderWidth: 0.75,
    paddingHorizontal: 5, paddingVertical: 1,
  },
  relBadge: {
    borderRadius: 6, borderWidth: 0.75,
    paddingHorizontal: 5, paddingVertical: 1,
  },
  relTxt: { fontSize: 8, fontFamily: F.bold, letterSpacing: 0.5 },
  makePrimaryBtn: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingVertical: 4, paddingHorizontal: 7,
    borderRadius: 7, borderWidth: 1, marginTop: 3,
    alignSelf: "flex-start",
  },
  iconBtn: {
    width: 26, height: 26, borderRadius: 7,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: "center", justifyContent: "center",
  },
  astroRow: {
    flexDirection: "row", alignItems: "center",
    borderRadius: 8, borderWidth: StyleSheet.hairlineWidth,
    paddingVertical: 5, paddingHorizontal: 8,
  },
  astroItem: { flex: 1, alignItems: "center", gap: 1 },
  astroLabel: { fontSize: 8, fontFamily: F.bold, letterSpacing: 0.5, textTransform: "uppercase" as const },
  astroValue: { fontSize: 10.5, fontFamily: F.bold },
  astroDivider: { width: StyleSheet.hairlineWidth, height: 18 },
  divider: { height: StyleSheet.hairlineWidth, marginVertical: 2 },
  addBtn: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 8, borderWidth: 0.75,
  },
  emptyRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 14, borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth, borderStyle: "dashed" as const,
  },
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
