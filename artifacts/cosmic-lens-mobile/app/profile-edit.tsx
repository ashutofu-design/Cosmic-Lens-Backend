import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useRef, useState } from "react";
import {
  ActivityIndicator, KeyboardAvoidingView, Platform,
  Pressable, ScrollView, StyleSheet, Text,
  TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { fetchKundliFromAPI } from "@/lib/kundliAPI";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import PickerModal from "@/components/PickerModal";
import type { BirthData } from "@/types";

import { API_BASE as BASE_URL, apiFetch } from "@/lib/apiConfig";

// ── Constants ──────────────────────────────────────────────────────────────────
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

const C_PRIMARY  = "#FF7A00";
const C_FOCUS    = "#6366F1";
const C_SUCCESS  = "#16A34A";
const C_SEL_BG   = "rgba(99,102,241,0.06)";
const C_SEL_BORD = "#6366F1";
const C_SEL_TXT  = "#4F46E5";

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

const RELATION_EMOJIS: Record<string, string> = {
  Self:"🧑", Husband:"👨", Wife:"👩", Son:"👦", Daughter:"👧",
  Father:"👴", Mother:"👵", Brother:"🧑", Sister:"👱‍♀️", Friend:"🤝", Other:"👥",
};

// ── Shared sub-components ──────────────────────────────────────────────────────

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

function CardRow({ label, icon, children }: { label: string; icon: React.ComponentProps<typeof Feather>["name"]; children?: React.ReactNode }) {
  const C = useC();
  return (
    <View style={s.cardRow}>
      <View style={[s.cardRowIcon, { backgroundColor: C.isDark ? "rgba(99,102,241,0.15)" : "#EEF2FF" }]}>
        <Feather name={icon} size={11} color={C_FOCUS} />
      </View>
      <Text style={[s.cardRowLabel, { color: C.isDark ? C.textMuted : "#64748B" }]}>{label}</Text>
      {children}
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

// ── Main screen ────────────────────────────────────────────────────────────────
export default function ProfileEditScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const params = useLocalSearchParams<{ mode?: string; profileId?: string; relation?: string }>();
  const { profiles, addProfile, updateProfile, setBirthData, setKundli, primaryProfileId, syncKundliToCloud } = useUser();

  const isEdit  = params.mode === "edit" && !!params.profileId;
  const profile = isEdit ? profiles.find(p => p.id === params.profileId) : null;

  const [relation] = useState<string>(profile?.relation ?? params.relation ?? "Self");

  const [f, setF] = useState<FormState>(() => {
    if (profile) {
      const bd = profile.birthData;
      return {
        name: profile.name, gender: profile.gender ?? "",
        day: String(bd.day), month: String(bd.month), year: String(bd.year),
        hour: String(bd.hour), minute: String(bd.minute), ampm: bd.ampm,
        place: bd.place, lat: bd.lat, lon: bd.lon, tz: bd.tz,
      };
    }
    return blank();
  });

  const [placeQuery, setPlaceQuery] = useState(f.place);
  const [geoResults, setGeoResults] = useState<GeoResult[]>([]);
  const [searching,  setSearching]  = useState(false);
  const [tzLoading,  setTzLoading]  = useState(false);
  const [saving,     setSaving]     = useState(false);
  const [savingStatus, setSavingStatus] = useState("");
  const [error,        setError]        = useState("");
  const [isNetworkError, setIsNetworkError] = useState(false);
  const [nameFocused,  setNameFocused]  = useState(false);
  const [placeFocused, setPlaceFocused] = useState(false);

  const [dayOpen,   setDayOpen]   = useState(false);
  const [monthOpen, setMonthOpen] = useState(false);
  const [yearOpen,  setYearOpen]  = useState(false);
  const [hourOpen,  setHourOpen]  = useState(false);
  const [minOpen,   setMinOpen]   = useState(false);

  const nameRef = useRef<TextInput>(null);
  const set = (key: keyof FormState) => (val: string) =>
    setF(prev => ({ ...prev, [key]: val }));

  async function handlePlaceSearch() {
    if (placeQuery.trim().length < 2) return;
    setSearching(true); setGeoResults([]);
    try { setGeoResults(await searchPlace(placeQuery)); }
    catch { setError("Location not found."); }
    finally { setSearching(false); }
  }

  async function selectGeo(g: GeoResult) {
    setF(prev => ({ ...prev, place: g.label, lat: g.lat, lon: g.lon, tz: g.tz }));
    setPlaceQuery(g.label); setGeoResults([]);
    setTzLoading(true);
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 5000);
    try {
      const r = await apiFetch(`${BASE_URL}/api/timezone?lat=${g.lat}&lon=${g.lon}`, { signal: ctrl.signal });
      const d = await r.json();
      if (typeof d.tz === "number") setF(prev => ({ ...prev, tz: d.tz }));
    } catch {}
    finally { clearTimeout(timer); setTzLoading(false); }
  }

  async function handleSave() {
    if (!f.name.trim())                { setError("Name is required."); return; }
    if (!f.day || !f.month || !f.year) { setError("Please complete the birth date."); return; }
    if (!f.hour || !f.minute)          { setError("Please enter the birth time."); return; }
    if (!f.lat)                        { setError("Please select a birth location."); return; }
    setError(""); setIsNetworkError(false);
    setSavingStatus("Calculating chart…"); setSaving(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const birthData: BirthData = {
        name: f.name.trim(),
        day: Number(f.day), month: Number(f.month), year: Number(f.year),
        hour: Number(f.hour), minute: Number(f.minute), ampm: f.ampm,
        place: f.place, lat: f.lat, lon: f.lon, tz: f.tz,
      };
      setSavingStatus("Connecting to server…");
      const kundli = await fetchKundliFromAPI(birthData);
      setSavingStatus("Saving…");
      if (isEdit && params.profileId) {
        updateProfile(params.profileId, { name: f.name.trim(), gender: f.gender, relation, birthData, kundli });
        if (params.profileId === primaryProfileId) {
          setBirthData(birthData); setKundli(kundli);
          syncKundliToCloud(birthData, kundli).catch(() => {});
        }
      } else {
        addProfile({ name: f.name.trim(), gender: f.gender, relation, birthData, kundli });
        syncKundliToCloud(birthData, kundli).catch(() => {});
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Chart calculation failed.";
      const isNet = /network|timed out|connection|failed to fetch/i.test(msg);
      setIsNetworkError(isNet);
      setError(isNet ? "Could not reach the server. Check your connection and try again." : msg);
    } finally {
      setSaving(false); setSavingStatus("");
    }
  }

  const bgColor = C.isDark ? C.bg : "#F8FAFC";

  return (
    <View style={{ flex: 1, backgroundColor: bgColor }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>

        {/* ── Header ── */}
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
              <View style={s.headerAccentDot} />
              <Text style={[s.headerTitle, { color: C.isDark ? C.text : "#0F172A" }]}>
                {isEdit ? "Edit Profile" : `${RELATION_EMOJIS[relation] ?? "👤"} ${relation}'s Kundli`}
              </Text>
            </View>
            <Text style={[s.headerSub, { color: C.isDark ? C.textDim : "#94A3B8" }]}>
              Fill in accurate birth details
            </Text>
          </View>
        </View>

        {/* ── Scrollable body ── */}
        <ScrollView
          contentContainerStyle={s.scroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >

          {/* ══ CARD 1 — Personal Info ══ */}
          <Card>
            {/* Section label */}
            <CardRow label="PERSONAL INFO" icon="user" />

            {/* Name */}
            <View style={s.fieldWrap}>
              <Lbl text="FULL NAME" />
              <View style={[
                s.inputRow,
                { backgroundColor: C.isDark ? C.inputBg : "#F1F5F9", borderColor: nameFocused ? C_FOCUS : (C.isDark ? C.inputBorder : "#CBD5E1") },
                nameFocused && { shadowColor: C_FOCUS, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.18, shadowRadius: 6 },
              ]}>
                <Feather name="user" size={13} color={nameFocused ? C_FOCUS : C.textDim} />
                <TextInput
                  ref={nameRef}
                  style={[s.inputTxt, { color: C.text }]}
                  value={f.name}
                  onChangeText={v => { set("name")(v); setError(""); }}
                  placeholder="Full name"
                  placeholderTextColor={C.textDim}
                  autoCapitalize="words"
                  returnKeyType="done"
                  onFocus={() => setNameFocused(true)}
                  onBlur={() => setNameFocused(false)}
                />
              </View>
            </View>

            {/* Divider */}
            <View style={[s.divider, { backgroundColor: C.isDark ? C.border : "rgba(0,0,0,0.06)" }]} />

            {/* Gender */}
            <View style={s.fieldWrap}>
              <Lbl text="GENDER (OPTIONAL)" />
              <View style={{ flexDirection: "row", gap: 6 }}>
                {["Male", "Female", "Other"].map(g => {
                  const active = f.gender === g;
                  return (
                    <Pressable
                      key={g}
                      onPress={() => { setF(prev => ({ ...prev, gender: g })); Haptics.selectionAsync(); }}
                      style={[
                        s.chip,
                        active
                          ? { borderColor: C_SEL_BORD, backgroundColor: C_SEL_BG }
                          : { borderColor: C.isDark ? C.border : "#E2E8F0", backgroundColor: "transparent" },
                      ]}
                    >
                      <Text style={[s.chipTxt, { color: active ? C_SEL_TXT : C.textMuted }]}>{g}</Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>
          </Card>

          {/* ══ CARD 2 — Birth Details (Date + Time merged) ══ */}
          <Card>
            <CardRow label="BIRTH DATE & TIME" icon="calendar" />

            {/* Row 1 — Day | Month | Year */}
            <View style={s.fieldWrap}>
              <Lbl text="DATE" />
              <View style={{ flexDirection: "row", gap: 6 }}>
                <View style={{ flex: 22 }}>
                  <PickerBtn value={f.day ? String(f.day).padStart(2,"0") : ""} placeholder="DD" onPress={() => setDayOpen(true)} />
                </View>
                <View style={{ flex: 36 }}>
                  <PickerBtn value={f.month ? MONTHS[Number(f.month)-1] : ""} placeholder="Month" onPress={() => setMonthOpen(true)} />
                </View>
                <View style={{ flex: 42 }}>
                  <PickerBtn value={f.year} placeholder="Year" onPress={() => setYearOpen(true)} />
                </View>
              </View>
            </View>

            <View style={[s.divider, { backgroundColor: C.isDark ? C.border : "rgba(0,0,0,0.06)" }]} />

            {/* Row 2 — Hour | Min | AM/PM */}
            <View style={s.fieldWrap}>
              <Lbl text="TIME" />
              <View style={{ flexDirection: "row", gap: 6 }}>
                <View style={{ flex: 28 }}>
                  <PickerBtn value={f.hour ? String(f.hour).padStart(2,"0") : ""} placeholder="HH" onPress={() => setHourOpen(true)} />
                </View>
                <View style={{ flex: 28 }}>
                  <PickerBtn value={f.minute !== "" ? String(f.minute).padStart(2,"0") : ""} placeholder="MM" onPress={() => setMinOpen(true)} />
                </View>
                <View style={{ flex: 44 }}>
                  <View style={{ flexDirection: "row", gap: 4 }}>
                    {(["AM", "PM"] as const).map(v => {
                      const active = f.ampm === v;
                      return (
                        <Pressable
                          key={v}
                          onPress={() => { setF(prev => ({ ...prev, ampm: v })); Haptics.selectionAsync(); }}
                          style={[
                            s.ampmBtn,
                            active
                              ? { borderColor: C_SEL_BORD, backgroundColor: C_SEL_BG }
                              : { borderColor: C.isDark ? C.border : "#E2E8F0", backgroundColor: C.isDark ? C.inputBg : "#F8FAFC" },
                          ]}
                        >
                          <Text style={[s.ampmTxt, { color: active ? C_SEL_TXT : C.textMuted }]}>{v}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                </View>
              </View>
              <Text style={[s.timeHint, { color: C.isDark ? C.textDim : "#94A3B8" }]}>
                Affects Mahadasha calculation — verify AM/PM
              </Text>
            </View>
          </Card>

          {/* ══ CARD 3 — Birth Place ══ */}
          <Card>
            <CardRow label="BIRTH PLACE" icon="map-pin" />

            {/* Search input */}
            <View style={s.fieldWrap}>
              <View style={[
                s.inputRow,
                { backgroundColor: C.isDark ? C.inputBg : "#F1F5F9", borderColor: placeFocused ? C_FOCUS : (C.isDark ? C.inputBorder : "#CBD5E1"), gap: 6 },
                placeFocused && { shadowColor: C_FOCUS, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.18, shadowRadius: 6 },
              ]}>
                <Feather name="search" size={13} color={placeFocused ? C_FOCUS : C.textDim} />
                <TextInput
                  style={[s.inputTxt, { flex: 1, color: C.text }]}
                  value={placeQuery}
                  onChangeText={setPlaceQuery}
                  onSubmitEditing={handlePlaceSearch}
                  placeholder="City, Country"
                  placeholderTextColor={C.textDim}
                  returnKeyType="search"
                  onFocus={() => setPlaceFocused(true)}
                  onBlur={() => setPlaceFocused(false)}
                />
                <Pressable onPress={handlePlaceSearch} style={s.searchBtn}>
                  {searching
                    ? <ActivityIndicator size="small" color={C_FOCUS} />
                    : <Text style={s.searchBtnTxt}>Search</Text>
                  }
                </Pressable>
              </View>
            </View>

            {/* Search results */}
            {geoResults.length > 0 && (
              <View style={[s.geoList, { backgroundColor: C.isDark ? C.bgCard2 : "#FFFFFF", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.08)" }]}>
                {geoResults.map((g, i) => (
                  <Pressable
                    key={i}
                    onPress={() => { selectGeo(g); Haptics.selectionAsync(); }}
                    style={[s.geoItem, i < geoResults.length - 1 && { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.isDark ? C.border : "rgba(0,0,0,0.07)" }]}
                  >
                    <Feather name="map-pin" size={10} color={C_FOCUS} style={{ marginTop: 1 }} />
                    <Text style={[s.geoTxt, { color: C.isDark ? C.textMid : "#334155" }]} numberOfLines={1}>{g.label}</Text>
                  </Pressable>
                ))}
              </View>
            )}

            {/* Confirmed location */}
            {f.lat !== 0 && (
              <View style={[s.confirmedPlace, { backgroundColor: C.isDark ? "rgba(22,163,74,0.12)" : "#F0FDF4", borderColor: C.isDark ? "rgba(22,163,74,0.3)" : "#BBF7D0" }]}>
                <Feather name="check-circle" size={12} color={C_SUCCESS} />
                <Text style={[s.confirmedTxt, { color: C_SUCCESS }]} numberOfLines={1}>{f.place}</Text>
                {tzLoading && <ActivityIndicator size="small" color={C_SUCCESS} style={{ marginLeft: 4 }} />}
              </View>
            )}
          </Card>

          {/* Error */}
          {!!error && (
            <View style={[s.errorBox, isNetworkError && { borderColor: "rgba(220,38,38,0.35)", backgroundColor: "rgba(220,38,38,0.07)" }]}>
              <Feather name={isNetworkError ? "wifi-off" : "alert-circle"} size={12} color="#DC2626" />
              <View style={{ flex: 1 }}>
                <Text style={s.errorTxt}>{error}</Text>
                {isNetworkError && (
                  <Text style={s.errorHint}>Make sure you have a stable internet connection.</Text>
                )}
              </View>
            </View>
          )}

          {/* Saving status */}
          {saving && !!savingStatus && (
            <View style={s.savingRow}>
              <ActivityIndicator size="small" color={C_PRIMARY} />
              <Text style={[s.savingTxt, { color: C.textMuted }]}>{savingStatus}</Text>
            </View>
          )}

          {/* Scroll padding so content clears sticky button */}
          <View style={{ height: 8 }} />
        </ScrollView>

        {/* ── Sticky Save Button ── */}
        <View style={[s.stickyBottom, {
          backgroundColor: bgColor,
          paddingBottom: insets.bottom + 10,
          borderTopColor: C.isDark ? C.border : "rgba(0,0,0,0.06)",
        }]}>
          <Pressable
            onPress={handleSave}
            disabled={saving}
            style={({ pressed }) => [{ opacity: saving ? 0.65 : pressed ? 0.88 : 1 }]}
          >
            <LinearGradient
              colors={isNetworkError ? ["#DC2626", "#B91C1C"] : ["#FF7A00", "#FF3D00"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={[s.saveBtn, { shadowColor: isNetworkError ? "#DC2626" : "#FF7A00" }]}
            >
              {saving
                ? <ActivityIndicator color="#fff" />
                : isNetworkError
                ? <><Feather name="refresh-cw" size={15} color="#fff" /><Text style={s.saveTxt}>Try Again</Text></>
                : <><Feather name={isEdit ? "check" : "user-plus"} size={15} color="#fff" /><Text style={s.saveTxt}>{isEdit ? "Save Changes" : "Create Profile"}</Text></>
              }
            </LinearGradient>
          </Pressable>
        </View>

      </KeyboardAvoidingView>

      {/* ── Pickers ── */}
      <PickerModal visible={dayOpen}   title="Select Day"           items={DAYS_L}   selected={f.day}    onSelect={v => { set("day")(v);    setDayOpen(false);   }} onClose={() => setDayOpen(false)}   />
      <PickerModal visible={monthOpen} title="Select Month"          items={MONTHS_L} selected={f.month}  onSelect={v => { set("month")(v);  setMonthOpen(false); }} onClose={() => setMonthOpen(false)} />
      <PickerModal visible={yearOpen}  title="Select Birth Year"     items={YEARS_L}  selected={f.year}   onSelect={v => { set("year")(v);   setYearOpen(false);  }} onClose={() => setYearOpen(false)}  />
      <PickerModal visible={hourOpen}  title="Select Hour (1–12)"    items={HOURS_L}  selected={f.hour}   onSelect={v => { set("hour")(v);   setHourOpen(false);  }} onClose={() => setHourOpen(false)}  />
      <PickerModal visible={minOpen}   title="Select Minute (0–59)"  items={MINS_L}   selected={f.minute} onSelect={v => { set("minute")(v); setMinOpen(false);   }} onClose={() => setMinOpen(false)}   />
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  // Header
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
    backgroundColor: C_FOCUS, opacity: 0.7,
  },
  headerTitle: { fontSize: 16, fontFamily: F.bold, letterSpacing: -0.4 },
  headerSub:   { fontSize: 10.5, fontFamily: F.regular, marginLeft: 11 },

  // Scroll
  scroll: { paddingHorizontal: 14, paddingTop: 12, paddingBottom: 16, gap: 10 },

  // Card
  card: {
    borderRadius: 16, overflow: "hidden",
    paddingHorizontal: 14, paddingVertical: 13,
    gap: 11,
    shadowColor: "#64748B", shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10, shadowRadius: 12, elevation: 4,
  },

  // Card section label row
  cardRow: { flexDirection: "row", alignItems: "center", gap: 7 },
  cardRowIcon: { width: 22, height: 22, borderRadius: 7, alignItems: "center", justifyContent: "center" },
  cardRowLabel: { fontSize: 9.5, fontFamily: F.bold, letterSpacing: 1.4 },

  // Divider
  divider: { height: StyleSheet.hairlineWidth, marginVertical: 2 },

  // Field wrapper
  fieldWrap: { gap: 5 },
  lbl: { fontSize: 9.5, fontFamily: F.bold, letterSpacing: 1.3 },

  // Text input row
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

  // Picker button (day/month/year/hour/min)
  pickerBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    borderRadius: 10, borderWidth: 0.75,
    paddingHorizontal: 9, paddingVertical: 0,
    minHeight: 44, gap: 4,
  },
  pickerTxt: { flex: 1, fontSize: 13, fontFamily: F.semibold },

  // Gender chip
  chip: {
    flex: 1, paddingVertical: 8, borderRadius: 10, alignItems: "center",
    borderWidth: 0.75,
  },
  chipTxt: { fontSize: 12.5, fontFamily: F.bold },

  // AM/PM
  ampmBtn: {
    flex: 1, height: 44, borderRadius: 10, alignItems: "center",
    justifyContent: "center", borderWidth: 0.75,
  },
  ampmTxt: { fontSize: 13, fontFamily: F.bold },

  // Time helper hint
  timeHint: { fontSize: 11, fontFamily: F.regular, marginTop: 4, opacity: 0.75 },

  // Place search button
  searchBtn: {
    paddingHorizontal: 11, paddingVertical: 6,
    borderRadius: 8, backgroundColor: "transparent",
    borderWidth: 0.75, borderColor: C_FOCUS,
  },
  searchBtnTxt: { fontSize: 11.5, fontFamily: F.bold, color: C_FOCUS },

  // Geo dropdown
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

  // Confirmed place
  confirmedPlace: {
    flexDirection: "row", alignItems: "center", gap: 7,
    borderRadius: 9, borderWidth: 0.75,
    paddingHorizontal: 10, paddingVertical: 7,
  },
  confirmedTxt: { fontSize: 12, fontFamily: F.semibold, flex: 1 },

  // Error
  errorBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    backgroundColor: "rgba(220,38,38,0.05)",
    borderWidth: 0.75, borderColor: "rgba(220,38,38,0.2)",
    borderRadius: 11, paddingHorizontal: 12, paddingVertical: 10,
  },
  errorTxt:  { color: "#DC2626", fontSize: 12.5, fontFamily: F.semibold },
  errorHint: { color: "#EF4444", fontSize: 10.5, fontFamily: F.regular, marginTop: 3, lineHeight: 15 },

  // Saving
  savingRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 4,
  },
  savingTxt: { fontSize: 12, fontFamily: F.medium },

  // Sticky bottom
  stickyBottom: {
    paddingHorizontal: 14, paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  saveBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, borderRadius: 14, height: 52,
    shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.3, shadowRadius: 14, elevation: 7,
  },
  saveTxt: { color: "#fff", fontSize: 15, fontFamily: F.bold, letterSpacing: 0.2 },
});
