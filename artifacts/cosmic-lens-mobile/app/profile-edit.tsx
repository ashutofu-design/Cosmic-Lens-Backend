import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useState } from "react";
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

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const CY     = new Date().getFullYear();
const DAYS_L  = Array.from({ length: 31 }, (_, i) => ({ label: String(i+1).padStart(2,"0"), value: String(i+1) }));
const MONTHS_L= MONTHS.map((m, i) => ({ label: m, value: String(i+1) }));
const YEARS_L = Array.from({ length: CY-1900+1 }, (_, i) => { const y=CY-i; return { label: String(y), value: String(y) }; });
const HOURS_L = Array.from({ length: 12 }, (_, i) => ({ label: String(i+1).padStart(2,"0"), value: String(i+1) }));
const MINS_L  = Array.from({ length: 60 }, (_, i) => ({ label: String(i).padStart(2,"0"), value: String(i) }));

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

// ── Reusable field label ───────────────────────────────────────────────────────
function FieldLabel({ text }: { text: string }) {
  const C = useC();
  return <Text style={[s.label, { color: C.text, opacity: C.isDark ? 0.65 : 1 }]}>{text}</Text>;
}

// ── Styled text input ──────────────────────────────────────────────────────────
function Field({
  label, value, onChangeText, placeholder, keyboardType, maxLength,
  icon, returnKeyType, onSubmitEditing, hint,
}: {
  label: string; value: string; onChangeText: (v: string) => void;
  placeholder: string; keyboardType?: any; maxLength?: number;
  icon?: React.ComponentProps<typeof Feather>["name"];
  returnKeyType?: any; onSubmitEditing?: () => void;
  hint?: string;
}) {
  const C = useC();
  const [focused, setFocused] = useState(false);
  return (
    <View style={s.fieldWrap}>
      <FieldLabel text={label} />
      <View style={[
        s.inputRow,
        {
          backgroundColor: C.inputBg,
          borderColor: focused ? C.inputFocusBorder : C.inputBorder,
        },
        focused && { shadowColor: C.inputFocusBorder, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 5 },
      ]}>
        {icon && <Feather name={icon} size={14} color={focused ? C.inputFocusBorder : C.textMuted} style={{ marginRight: 2 }} />}
        <TextInput
          style={[s.input, { color: C.text }]}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={C.textDim}
          keyboardType={keyboardType}
          maxLength={maxLength}
          returnKeyType={returnKeyType}
          onSubmitEditing={onSubmitEditing}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
      </View>
      {hint && <Text style={[s.hint, { color: C.textMuted }]}>{hint}</Text>}
    </View>
  );
}

// ── Month selector — compact 4-column grid ────────────────────────────────────
const MONTH_ROWS = [[0,1,2,3], [4,5,6,7], [8,9,10,11]];

function MonthPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const C = useC();
  return (
    <View style={{ gap: 5 }}>
      <FieldLabel text="MONTH" />
      <View style={{ gap: 5 }}>
        {MONTH_ROWS.map((row, ri) => (
          <View key={ri} style={{ flexDirection: "row", gap: 5 }}>
            {row.map(i => {
              const v = String(i + 1);
              const active = value === v;
              return (
                <Pressable
                  key={i}
                  onPress={() => { onChange(v); Haptics.selectionAsync(); }}
                  style={[
                    s.monthChip,
                    { flex: 1, borderColor: active ? C.accent : C.border },
                    active && { backgroundColor: `${C.accent}18` },
                  ]}
                >
                  <Text style={[s.monthTxt, { color: active ? C.accent : C.textMuted }]}>{MONTHS[i]}</Text>
                </Pressable>
              );
            })}
          </View>
        ))}
      </View>
    </View>
  );
}

// ── AM / PM toggle ─────────────────────────────────────────────────────────────
function AmPmToggle({ value, onChange }: { value: "AM" | "PM"; onChange: (v: "AM" | "PM") => void }) {
  const C = useC();
  return (
    <View style={s.ampmRow}>
      {(["AM", "PM"] as const).map(v => {
        const active = value === v;
        return (
          <Pressable key={v} onPress={() => { onChange(v); Haptics.selectionAsync(); }}
            style={[
              s.ampmBtn,
              active
                ? { borderColor: C.toggleSelBorder, backgroundColor: C.toggleSelBg }
                : { borderColor: C.border, backgroundColor: "transparent" },
            ]}
          >
            <Text style={[s.ampmTxt, { color: active ? C.toggleSelText : C.textMuted }]}>{v}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

// ── Section block wrapper ──────────────────────────────────────────────────────
function Section({ title, icon, children }: {
  title: string; icon: React.ComponentProps<typeof Feather>["name"]; children: React.ReactNode;
}) {
  const C = useC();
  return (
    <View style={[s.section, C.isDark && { backgroundColor: C.bgCard, shadowOpacity: 0.25 }]}>
      <View style={[s.sectionHeader, { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.isDark ? C.border : "rgba(0,0,0,0.07)" }]}>
        <View style={{ width: 26, height: 26, borderRadius: 8, backgroundColor: `${C.accent}18`, alignItems: "center", justifyContent: "center" }}>
          <Feather name={icon} size={12} color={C.accent} />
        </View>
        <Text style={[s.sectionTitle, { color: C.isDark ? C.textMuted : "#475569" }]}>{title}</Text>
      </View>
      <View style={s.sectionBody}>
        {children}
      </View>
    </View>
  );
}

// ── Main Screen ────────────────────────────────────────────────────────────────
const RELATION_EMOJIS: Record<string, string> = {
  Self:"🧑", Husband:"👨", Wife:"👩", Son:"👦", Daughter:"👧",
  Father:"👴", Mother:"👵", Brother:"🧑", Sister:"👱‍♀️", Friend:"🤝", Other:"👥",
};

export default function ProfileEditScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const params = useLocalSearchParams<{ mode?: string; profileId?: string; relation?: string }>();
  const { profiles, addProfile, updateProfile, setBirthData, setKundli, primaryProfileId, syncKundliToCloud } = useUser();

  const isEdit  = params.mode === "edit" && !!params.profileId;
  const profile = isEdit ? profiles.find(p => p.id === params.profileId) : null;

  const [relation, setRelation] = useState<string>(
    profile?.relation ?? params.relation ?? "Self"
  );

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
  const [error,      setError]      = useState("");

  const [dayOpen,   setDayOpen]   = useState(false);
  const [monthOpen, setMonthOpen] = useState(false);
  const [yearOpen,  setYearOpen]  = useState(false);
  const [hourOpen,  setHourOpen]  = useState(false);
  const [minOpen,   setMinOpen]   = useState(false);

  const set = (key: keyof FormState) => (val: string) =>
    setF(prev => ({ ...prev, [key]: val }));

  async function handlePlaceSearch() {
    if (placeQuery.trim().length < 2) return;
    setSearching(true);
    setGeoResults([]);
    try { setGeoResults(await searchPlace(placeQuery)); }
    catch { setError("Location not found. Check your internet connection."); }
    finally { setSearching(false); }
  }

  async function selectGeo(g: GeoResult) {
    setF(prev => ({ ...prev, place: g.label, lat: g.lat, lon: g.lon, tz: g.tz }));
    setPlaceQuery(g.label);
    setGeoResults([]);
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

  const [savingStatus, setSavingStatus] = useState("");
  const [isNetworkError, setIsNetworkError] = useState(false);

  async function handleSave() {
    if (!f.name.trim())                { setError("Name is required."); return; }
    if (!f.day || !f.month || !f.year) { setError("Please complete the birth date."); return; }
    if (!f.hour || !f.minute)          { setError("Please enter the birth time."); return; }
    if (!f.lat)                        { setError("Please search and select a valid location."); return; }
    setError("");
    setIsNetworkError(false);
    setSavingStatus("Calculating chart…");
    setSaving(true);
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
      setSavingStatus("Saving profile…");

      if (isEdit && params.profileId) {
        updateProfile(params.profileId, { name: f.name.trim(), gender: f.gender, relation, birthData, kundli });
        if (params.profileId === primaryProfileId) {
          setBirthData(birthData); setKundli(kundli);
          syncKundliToCloud(birthData, kundli).catch(() => {});
        }
      } else {
        addProfile({ name: f.name.trim(), gender: f.gender, relation, birthData, kundli });
        if (!isEdit) syncKundliToCloud(birthData, kundli).catch(() => {});
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Chart calculation failed. Please try again.";
      const isNet = msg.toLowerCase().includes("network") ||
                    msg.toLowerCase().includes("timed out") ||
                    msg.toLowerCase().includes("connection") ||
                    msg.toLowerCase().includes("failed to fetch");
      setIsNetworkError(isNet);
      setError(
        isNet
          ? "Could not reach the server. Please check your internet connection and tap Try Again."
          : msg
      );
    } finally {
      setSaving(false);
      setSavingStatus("");
    }
  }

  return (
    <View style={{ flex: 1, backgroundColor: C.isDark ? C.bg : "#F8FAFC" }}>
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      {/* ── Header ── */}
      <View style={[s.header, {
        paddingTop: insets.top + 10,
        backgroundColor: C.isDark ? C.bg : "#F8FAFC",
        borderBottomColor: C.isDark ? C.border : "rgba(0,0,0,0.07)",
      }]}>
        <Pressable onPress={() => router.back()}
          style={[s.backBtn, { backgroundColor: C.isDark ? C.bgCard2 : "#FFFFFF", borderColor: C.isDark ? C.border : "rgba(0,0,0,0.10)" }]}
          hitSlop={10}
        >
          <Feather name="arrow-left" size={18} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[s.headerTitle, { color: C.text }]}>
            {isEdit ? "Edit Profile" : `${RELATION_EMOJIS[relation] ?? "👤"} ${relation}'s Kundli`}
          </Text>
          <Text style={[s.headerSub, { color: C.textMuted }]}>Accurate birth details ensure a precise chart</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={s.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >

        {/* ── PERSONAL INFO ── */}
        <Section title="Personal Info" icon="user">
          <Field
            label="FULL NAME"
            value={f.name}
            onChangeText={set("name")}
            placeholder="Enter full name"
            icon="user"
          />

          {/* Gender */}
          <View style={s.fieldWrap}>
            <FieldLabel text="GENDER (OPTIONAL)" />
            <View style={{ flexDirection: "row", gap: 8 }}>
              {["Male", "Female", "Other"].map(g => {
                const active = f.gender === g;
                return (
                  <Pressable key={g}
                    onPress={() => { setF(prev => ({ ...prev, gender: g })); Haptics.selectionAsync(); }}
                    style={[
                      s.genderChip,
                      active
                        ? { borderColor: C.toggleSelBorder, backgroundColor: C.toggleSelBg }
                        : { borderColor: C.border, backgroundColor: "transparent" },
                    ]}
                  >
                    <Text style={[s.genderTxt, { color: active ? C.toggleSelText : C.textMuted }]}>{g}</Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        </Section>

        {/* ── DATE OF BIRTH ── */}
        <Section title="Birth Date" icon="calendar">
          <View style={{ flexDirection: "row", gap: 6 }}>
            {/* Day — 25% */}
            <View style={{ flex: 25 }}>
              <View style={s.fieldWrap}>
                <FieldLabel text="DAY" />
                <Pressable
                  style={[s.selectBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.selectionAsync(); setDayOpen(true); }}
                >
                  <Text style={[s.selectBtnText, { color: f.day ? C.text : C.textDim }]}>
                    {f.day ? String(f.day).padStart(2,"0") : "DD"}
                  </Text>
                  <Feather name="chevron-down" size={11} color={C.textMuted} />
                </Pressable>
              </View>
            </View>
            {/* Month — 35% */}
            <View style={{ flex: 35 }}>
              <View style={s.fieldWrap}>
                <FieldLabel text="MONTH" />
                <Pressable
                  style={[s.selectBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.selectionAsync(); setMonthOpen(true); }}
                >
                  <Text style={[s.selectBtnText, { color: f.month ? C.text : C.textDim }]}>
                    {f.month ? MONTHS[Number(f.month) - 1] : "Mon"}
                  </Text>
                  <Feather name="chevron-down" size={11} color={C.textMuted} />
                </Pressable>
              </View>
            </View>
            {/* Year — 40% */}
            <View style={{ flex: 40 }}>
              <View style={s.fieldWrap}>
                <FieldLabel text="YEAR" />
                <Pressable
                  style={[s.selectBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.selectionAsync(); setYearOpen(true); }}
                >
                  <Text style={[s.selectBtnText, { color: f.year ? C.text : C.textDim }]}>
                    {f.year || "YYYY"}
                  </Text>
                  <Feather name="chevron-down" size={11} color={C.textMuted} />
                </Pressable>
              </View>
            </View>
          </View>
        </Section>

        {/* ── TIME OF BIRTH ── */}
        <Section title="Birth Time" icon="clock">
          {/* Warning strip */}
          <View style={[s.infoBox, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}>
            <Feather name="alert-triangle" size={12} color={C.warningBorder} />
            <Text style={[s.infoTxt, { color: C.warningText }]} numberOfLines={1}>
              Birth time affects Mahadasha — select AM/PM correctly
            </Text>
          </View>

          {/* Hour + Minute + AM/PM — single row */}
          <View style={{ flexDirection: "row", gap: 6 }}>
            {/* Hour */}
            <View style={{ flex: 28 }}>
              <View style={s.fieldWrap}>
                <FieldLabel text="HOUR" />
                <Pressable
                  style={[s.selectBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.selectionAsync(); setHourOpen(true); }}
                >
                  <Text style={[s.selectBtnText, { color: f.hour ? C.text : C.textDim }]}>
                    {f.hour ? String(f.hour).padStart(2,"0") : "HH"}
                  </Text>
                  <Feather name="chevron-down" size={11} color={C.textMuted} />
                </Pressable>
              </View>
            </View>
            {/* Minute */}
            <View style={{ flex: 28 }}>
              <View style={s.fieldWrap}>
                <FieldLabel text="MIN" />
                <Pressable
                  style={[s.selectBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.selectionAsync(); setMinOpen(true); }}
                >
                  <Text style={[s.selectBtnText, { color: f.minute !== "" ? C.text : C.textDim }]}>
                    {f.minute !== "" ? String(f.minute).padStart(2,"0") : "MM"}
                  </Text>
                  <Feather name="chevron-down" size={11} color={C.textMuted} />
                </Pressable>
              </View>
            </View>
            {/* AM / PM */}
            <View style={{ flex: 44 }}>
              <View style={s.fieldWrap}>
                <FieldLabel text="AM / PM" />
                <AmPmToggle value={f.ampm} onChange={v => setF(prev => ({ ...prev, ampm: v }))} />
              </View>
            </View>
          </View>
        </Section>

        {/* ── PLACE OF BIRTH ── */}
        <Section title="Birth Place" icon="map-pin">
          <View style={s.fieldWrap}>
            <FieldLabel text="CITY / COUNTRY" />
            <View style={[s.inputRow, { backgroundColor: C.inputBg, borderColor: C.inputBorder, gap: 7 }]}>
              <Feather name="search" size={14} color={C.textMuted} />
              <TextInput
                style={[s.input, { flex: 1, color: C.text }]}
                value={placeQuery}
                onChangeText={setPlaceQuery}
                onSubmitEditing={handlePlaceSearch}
                placeholder="e.g. Mumbai, India"
                placeholderTextColor={C.textDim}
                returnKeyType="search"
              />
              <Pressable onPress={handlePlaceSearch} style={s.searchBtn}>
                {searching
                  ? <ActivityIndicator size="small" color="#f59e0b" />
                  : <Text style={s.searchBtnTxt}>Search</Text>
                }
              </Pressable>
            </View>
          </View>

          {/* Search results */}
          {geoResults.length > 0 && (
            <View style={[s.geoList, C.isDark && { backgroundColor: C.bgCard }]}>
              {geoResults.map((g, i) => (
                <Pressable key={i} onPress={() => { selectGeo(g); Haptics.selectionAsync(); }}
                  style={[s.geoItem, i < geoResults.length - 1 && [s.geoItemBorder, { borderBottomColor: C.border }]]}
                >
                  <Feather name="map-pin" size={11} color={C.isDark ? C.textMuted : "#6366F1"} style={{ marginTop: 2 }} />
                  <Text style={[s.geoTxt, { color: C.isDark ? C.textMuted : "#334155" }]} numberOfLines={2}>{g.label}</Text>
                </Pressable>
              ))}
            </View>
          )}

          {/* Selected place */}
          {f.lat !== 0 && (
            <View style={s.selectedPlace}>
              <Feather name="check-circle" size={13} color="#00a86b" />
              <Text style={s.selectedPlaceTxt} numberOfLines={1}>{f.place}</Text>
              {tzLoading && <ActivityIndicator size="small" color="#f59e0b" style={{ marginLeft: 4 }} />}
            </View>
          )}
        </Section>

        {/* Error */}
        {!!error && (
          <View style={[s.errorBox, isNetworkError && s.errorBoxNetwork]}>
            <Feather name={isNetworkError ? "wifi-off" : "alert-circle"} size={13} color="#f87171" />
            <View style={{ flex: 1 }}>
              <Text style={s.errorTxt}>{error}</Text>
              {isNetworkError && (
                <Text style={s.errorHint}>
                  Tip: Make sure your phone has a stable internet connection (Wi-Fi recommended).
                </Text>
              )}
            </View>
          </View>
        )}

        {/* Saving status */}
        {saving && !!savingStatus && (
          <View style={s.savingStatus}>
            <ActivityIndicator size="small" color="#f59e0b" />
            <Text style={[s.savingStatusTxt, { color: C.textMuted }]}>{savingStatus}</Text>
          </View>
        )}

        {/* ── Save / Retry button ── */}
        <Pressable
          onPress={handleSave}
          disabled={saving}
          style={({ pressed }) => [{ opacity: saving ? 0.6 : pressed ? 0.85 : 1 }]}
        >
          <LinearGradient
            colors={isNetworkError ? ["#dc2626", "#ef4444"] : ["#FF7A00", "#FF3D00"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
            style={[s.saveBtn, { shadowColor: isNetworkError ? "#dc2626" : "#FF7A00", shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.32, shadowRadius: 16, elevation: 8 }]}
          >
            {saving
              ? <ActivityIndicator color="#fff" />
              : isNetworkError
              ? (
                <>
                  <Feather name="refresh-cw" size={16} color="#fff" />
                  <Text style={s.saveBtnTxt}>Try Again</Text>
                </>
              )
              : (
                <>
                  <Feather name={isEdit ? "check" : "user-plus"} size={16} color="#fff" />
                  <Text style={s.saveBtnTxt}>{isEdit ? "Save Changes" : "Create Profile"}</Text>
                </>
              )
            }
          </LinearGradient>
        </Pressable>

      </ScrollView>

      {/* ── Pickers ── */}
      <PickerModal visible={dayOpen}   title="Select Day"           items={DAYS_L}   selected={f.day}    onSelect={v => { setF(p=>({...p,day:v}));    setDayOpen(false);   }} onClose={() => setDayOpen(false)}   />
      <PickerModal visible={monthOpen} title="Select Month"          items={MONTHS_L} selected={f.month}  onSelect={v => { setF(p=>({...p,month:v}));  setMonthOpen(false); }} onClose={() => setMonthOpen(false)} />
      <PickerModal visible={yearOpen}  title="Select Birth Year"     items={YEARS_L}  selected={f.year}   onSelect={v => { setF(p=>({...p,year:v}));   setYearOpen(false);  }} onClose={() => setYearOpen(false)}  />
      <PickerModal visible={hourOpen}  title="Select Hour (1–12)"    items={HOURS_L}  selected={f.hour}   onSelect={v => { setF(p=>({...p,hour:v}));   setHourOpen(false);  }} onClose={() => setHourOpen(false)}  />
      <PickerModal visible={minOpen}   title="Select Minute (0–59)"  items={MINS_L}   selected={f.minute} onSelect={v => { setF(p=>({...p,minute:v}));  setMinOpen(false);   }} onClose={() => setMinOpen(false)}   />

    </KeyboardAvoidingView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  // Header
  header: {
    flexDirection: "row", alignItems: "center", gap: 14,
    paddingHorizontal: 18, paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: {
    width: 38, height: 38, borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: "center", justifyContent: "center",
    shadowColor: "#000", shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06, shadowRadius: 3, elevation: 1,
  },
  headerTitle: { fontSize: 17, fontFamily: F.bold, letterSpacing: -0.4 },
  headerSub:   { fontSize: 11, fontFamily: F.regular, marginTop: 2 },

  scroll: { padding: 16, paddingBottom: 100, gap: 14 },

  // Section card — floating, shadow-only depth
  section: {
    borderRadius: 18, overflow: "hidden",
    backgroundColor: "#FFFFFF",
    shadowColor: "#000", shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.07, shadowRadius: 16, elevation: 4,
  },
  sectionHeader: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 16, paddingVertical: 12,
  },
  sectionTitle: {
    fontSize: 11, fontFamily: F.bold, letterSpacing: 1.4,
  },
  sectionBody: { paddingHorizontal: 16, paddingBottom: 18, paddingTop: 6, gap: 12 },

  // Field
  fieldWrap: { gap: 6 },
  label: {
    fontSize: 10, fontFamily: F.bold, letterSpacing: 1.4,
  },
  inputRow: {
    flexDirection: "row", alignItems: "center",
    borderRadius: 12, borderWidth: 1.5,
    paddingHorizontal: 12, paddingVertical: 0,
    gap: 8,
    minHeight: 48,
  },
  inputRowFocused: {
    shadowColor: "#6366F1", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.2, shadowRadius: 8,
  },
  input: {
    flex: 1, fontSize: 14, fontFamily: F.semibold,
    padding: 0, margin: 0,
  },
  hint: { fontSize: 10, fontFamily: F.regular },

  // Month picker — 4 columns, compact chips
  monthGrid: { flexDirection: "row", flexWrap: "wrap", gap: 5 },
  monthChip: {
    paddingVertical: 8, borderRadius: 10,
    borderWidth: 1.5, alignItems: "center",
  },
  monthTxt: { fontSize: 12, fontFamily: F.semibold },

  // Gender chips
  genderChip: {
    flex: 1, paddingVertical: 10, borderRadius: 12, alignItems: "center",
    borderWidth: 1.5,
  },
  genderTxt: { fontSize: 13, fontFamily: F.bold },

  // AM/PM
  ampmRow: { flexDirection: "row", gap: 8 },
  ampmBtn: {
    flex: 1, paddingVertical: 0, borderRadius: 12, alignItems: "center",
    justifyContent: "center", borderWidth: 1.5, minHeight: 48,
  },
  ampmTxt: { fontSize: 14, fontFamily: F.bold },

  // Info box (warning) — compact single-line strip
  infoBox: {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderWidth: 1.5,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8,
  },
  infoTxt: { fontSize: 11, fontFamily: F.semibold, flex: 1, lineHeight: 15 },

  // Place search
  searchBtn: {
    paddingHorizontal: 14, paddingVertical: 7,
    backgroundColor: "rgba(99,102,241,0.10)",
    borderRadius: 10, borderWidth: 1.5, borderColor: "#6366F1",
  },
  searchBtnTxt: { color: "#6366F1", fontSize: 12, fontFamily: F.bold },

  // Geo results
  geoList: {
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    shadowColor: "#000", shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08, shadowRadius: 12, elevation: 3,
    overflow: "hidden",
  },
  geoItem: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    paddingHorizontal: 14, paddingVertical: 12,
  },
  geoItemBorder: { borderBottomWidth: StyleSheet.hairlineWidth },
  geoTxt: { fontSize: 12, fontFamily: F.regular, flex: 1, lineHeight: 18 },

  // Selected place confirmation
  selectedPlace: {
    flexDirection: "row", alignItems: "center", gap: 8,
    backgroundColor: "rgba(0,168,107,0.07)",
    borderRadius: 10, borderWidth: 1.5, borderColor: "rgba(0,168,107,0.25)",
    paddingHorizontal: 12, paddingVertical: 8,
  },
  selectedPlaceTxt: {
    color: "#00a86b", fontSize: 12, fontFamily: F.semibold, flex: 1,
  },

  // Error
  errorBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    backgroundColor: "rgba(239,68,68,0.06)",
    borderWidth: 1.5, borderColor: "rgba(239,68,68,0.25)",
    borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
  },
  errorBoxNetwork: {
    backgroundColor: "rgba(239,68,68,0.09)",
    borderColor: "rgba(239,68,68,0.35)",
  },
  errorTxt:  { color: "#dc2626", fontSize: 13, fontFamily: F.semibold },
  errorHint: { color: "#ef4444", fontSize: 11, fontFamily: F.regular, marginTop: 4, lineHeight: 16 },

  savingStatus: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 8, paddingHorizontal: 4,
    justifyContent: "center",
  },
  savingStatusTxt: { fontSize: 12, fontFamily: F.medium },

  // Select button (tap-to-open picker)
  selectBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    borderRadius: 12, borderWidth: 1.5,
    paddingHorizontal: 12, paddingVertical: 0,
    minHeight: 48,
  },
  selectBtnText: {
    fontSize: 14, fontFamily: F.semibold,
  },

  // Save button — tall, vivid gradient, strong shadow
  saveBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 10, borderRadius: 16, height: 54,
  },
  saveBtnTxt: { color: "#fff", fontSize: 15, fontFamily: F.bold, letterSpacing: 0.3 },
});
