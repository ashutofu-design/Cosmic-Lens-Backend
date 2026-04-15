import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import PickerModal from "@/components/PickerModal";

import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { fetchKundliFromAPI, fetchTimezone, searchPlaces, type PlaceSuggestion } from "@/lib/kundliAPI";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

const currentYear = new Date().getFullYear();
const DAYS   = Array.from({ length: 31 }, (_, i) => ({ label: String(i + 1).padStart(2,"0"), value: String(i + 1) }));
const YEARS  = Array.from({ length: currentYear - 1900 + 1 }, (_, i) => {
  const y = currentYear - i; return { label: String(y), value: String(y) };
});
const HOURS  = Array.from({ length: 12 }, (_, i) => ({ label: String(i + 1).padStart(2,"0"), value: String(i + 1) }));
const MINS   = Array.from({ length: 60 }, (_, i) => ({ label: String(i).padStart(2,"0"), value: String(i) }));

export default function OnboardingScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { setBirthData, setKundli, syncKundliToCloud, language } = useUser();
  const t = getT(language);

  const [name,    setName]    = useState("");
  const [day,     setDay]     = useState("");
  const [month,   setMonth]   = useState("");
  const [year,    setYear]    = useState("");
  const [hour,    setHour]    = useState("");
  const [minute,  setMinute]  = useState("");
  const [ampm,    setAmpm]    = useState<"AM"|"PM">("AM");

  const [placeQuery,    setPlaceQuery]    = useState("");
  const [selectedLat,   setSelectedLat]   = useState<number|null>(null);
  const [selectedLon,   setSelectedLon]   = useState<number|null>(null);
  const [selectedTz,    setSelectedTz]    = useState<number|null>(null);
  const [selectedPlace, setSelectedPlace] = useState("");
  const [suggestions,   setSuggestions]   = useState<PlaceSuggestion[]>([]);
  const [searching,     setSearching]     = useState(false);

  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  const [dayPickerOpen,   setDayPickerOpen]   = useState(false);
  const [monthPickerOpen, setMonthPickerOpen] = useState(false);
  const [yearPickerOpen,  setYearPickerOpen]  = useState(false);
  const [hourPickerOpen,  setHourPickerOpen]  = useState(false);
  const [minPickerOpen,   setMinPickerOpen]   = useState(false);
  const [ampmPickerOpen,  setAmpmPickerOpen]  = useState(false);

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  async function doSearchPlace() {
    if (placeQuery.length < 2) return;
    setSearching(true); setSuggestions([]);
    try {
      const results = await searchPlaces(placeQuery);
      setSuggestions(results);
    } catch { /* ignore */ }
    finally { setSearching(false); }
  }

  async function selectPlace(item: PlaceSuggestion) {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    const tz = await fetchTimezone(item.lat, item.lon);
    setSelectedLat(item.lat);
    setSelectedLon(item.lon);
    setSelectedTz(tz);
    setSelectedPlace(item.label);
    setPlaceQuery(item.label);
    setSuggestions([]);
  }

  async function handleSubmit() {
    if (!name.trim())            { setError("Name is required."); return; }
    if (!day || !month || !year) { setError("Please enter your complete date of birth."); return; }
    if (!hour || !minute)        { setError("Please enter your birth time."); return; }
    if (!selectedLat)            { setError("Please search and select your birth place."); return; }

    setError(""); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const bd = {
        name:   name.trim(),
        day:    parseInt(day),
        month:  parseInt(month),
        year:   parseInt(year),
        hour:   parseInt(hour),
        minute: parseInt(minute),
        ampm,
        place:  selectedPlace,
        lat:    selectedLat,
        lon:    selectedLon!,
        tz:     selectedTz!,
      };
      const kundli = await fetchKundliFromAPI(bd);
      setBirthData(bd);
      setKundli(kundli);
      syncKundliToCloud(bd, kundli).catch(() => {});
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.replace("/(tabs)");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Chart calculation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const canSubmit = !loading;

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <View style={s.header}>
        <Pressable
          onPress={() => router.back()}
          style={({ pressed }) => [s.backBtn, pressed && { opacity: 0.5 }]}
        >
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <Pressable
          onPress={() => router.replace("/(tabs)")}
          style={({ pressed }) => [s.skipBtn, pressed && { opacity: 0.5 }]}
        >
          <Text style={[s.skipText, { color: C.textMuted }]}>{t.skip}</Text>
        </Pressable>
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView
          contentContainerStyle={[s.scroll, { paddingBottom: botPad + 40 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >

          {/* ── Hero section ─────────────────────────────────────────── */}
          <View style={s.hero}>
            <LinearGradient
              colors={[C.accentBg, "transparent"]}
              style={[s.heroIcon, { borderColor: C.border2 }]}
            >
              <Feather name="star" size={26} color="#f59e0b" />
            </LinearGradient>
            <Text style={[s.heroTitle, { color: C.text }]}>{t.birthDetails}</Text>
            <Text style={[s.heroSub, { color: C.textMuted }]}>{t.birthSubtitle}</Text>
          </View>

          {/* ── Section: Full Name ────────────────────────────────────── */}
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(167,139,250,0.12)" }]}>
                <Feather name="user" size={14} color="#f59e0b" />
              </View>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.yourName.toUpperCase()}</Text>
            </View>
            <TextInput
              style={[s.input, { backgroundColor: C.inputBg, borderColor: C.inputBorder, color: C.text }]}
              placeholder="Enter full name"
              placeholderTextColor={C.textDim}
              value={name}
              onChangeText={setName}
              returnKeyType="next"
              autoCapitalize="words"
            />
          </View>

          {/* ── Section: Date of Birth ────────────────────────────────── */}
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(139,92,246,0.10)" }]}>
                <Feather name="calendar" size={14} color="#f59e0b" />
              </View>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.dateOfBirth.toUpperCase()}</Text>
            </View>
            <View style={s.dateRow}>
              {/* Day */}
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={[s.dateLabel, { color: C.textDim }]}>{t.day}</Text>
                <Pressable
                  style={[s.datePickerBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setDayPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: day ? C.text : C.textDim }]}>
                    {day ? String(day).padStart(2,"0") : "DD"}
                  </Text>
                  <Feather name="chevron-down" size={13} color={C.textDim} />
                </Pressable>
              </View>

              {/* Month */}
              <View style={[s.dateCell, { flex: 2 }]}>
                <Text style={[s.dateLabel, { color: C.textDim }]}>{t.month}</Text>
                <Pressable
                  style={[s.datePickerBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setMonthPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: month ? C.text : C.textDim }]}>
                    {month ? MONTHS[parseInt(month) - 1] : "Select"}
                  </Text>
                  <Feather name="chevron-down" size={13} color={C.textDim} />
                </Pressable>
              </View>

              {/* Year */}
              <View style={[s.dateCell, { flex: 1.8 }]}>
                <Text style={[s.dateLabel, { color: C.textDim }]}>{t.year}</Text>
                <Pressable
                  style={[s.datePickerBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setYearPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: year ? C.text : C.textDim }]}>
                    {year || "YYYY"}
                  </Text>
                  <Feather name="chevron-down" size={13} color={C.textDim} />
                </Pressable>
              </View>
            </View>
          </View>

          {/* ── Section: Time of Birth ────────────────────────────────── */}
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(250,204,21,0.10)" }]}>
                <Feather name="clock" size={14} color="#facc15" />
              </View>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.timeOfBirth.toUpperCase()}</Text>
            </View>

            {/* Warning */}
            <View style={[s.warnBox, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}>
              <Feather name="alert-triangle" size={11} color="#f59e0b" style={{ marginTop: 1 }} />
              <Text style={[s.warnText, { color: C.warningText }]}>{t.timeTip}</Text>
            </View>

            <View style={s.dateRow}>
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={[s.dateLabel, { color: C.textDim }]}>Hour</Text>
                <Pressable
                  style={[s.datePickerBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setHourPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: hour ? C.text : C.textDim }]}>
                    {hour ? String(hour).padStart(2,"0") : "HH"}
                  </Text>
                  <Feather name="chevron-down" size={13} color={C.textDim} />
                </Pressable>
              </View>
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={[s.dateLabel, { color: C.textDim }]}>{t.minute}</Text>
                <Pressable
                  style={[s.datePickerBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setMinPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: minute ? C.text : C.textDim }]}>
                    {minute !== "" ? String(minute).padStart(2,"0") : "MM"}
                  </Text>
                  <Feather name="chevron-down" size={13} color={C.textDim} />
                </Pressable>
              </View>
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={[s.dateLabel, { color: C.textDim }]}>AM / PM</Text>
                <Pressable
                  style={[s.datePickerBtn, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setAmpmPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: C.text }]}>{ampm}</Text>
                  <Feather name="chevron-down" size={13} color={C.textDim} />
                </Pressable>
              </View>
            </View>
          </View>

          {/* ── Section: Place of Birth ───────────────────────────────── */}
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(16,185,129,0.10)" }]}>
                <Feather name="map-pin" size={14} color="#10b981" />
              </View>
              <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.birthPlace.toUpperCase()}</Text>
            </View>

            <View style={s.placeRow}>
              <TextInput
                style={[s.input, { flex: 1, marginBottom: 0, backgroundColor: C.inputBg, borderColor: C.inputBorder, color: C.text }]}
                placeholder={t.searchCity}
                placeholderTextColor={C.textDim}
                value={placeQuery}
                onChangeText={v => { setPlaceQuery(v); setSelectedLat(null); setSelectedPlace(""); }}
                onSubmitEditing={doSearchPlace}
                returnKeyType="search"
              />
              <Pressable
                onPress={doSearchPlace}
                style={({ pressed }) => [s.searchBtn, { backgroundColor: C.accent }, pressed && { opacity: 0.7 }]}
              >
                {searching
                  ? <ActivityIndicator size="small" color={C.isDark ? "#020d1a" : "#fff"} />
                  : <Feather name="search" size={15} color={C.isDark ? "#020d1a" : "#fff"} />
                }
              </Pressable>
            </View>

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <View style={[s.suggestBox, { backgroundColor: C.bgCard, borderColor: C.inputBorder }]}>
                {suggestions.map((item, i) => (
                  <Pressable
                    key={i}
                    onPress={() => selectPlace(item)}
                    style={({ pressed }) => [
                      s.suggestItem,
                      i < suggestions.length - 1 && { borderBottomWidth: 1, borderBottomColor: C.border },
                      pressed && { backgroundColor: C.accentBg },
                    ]}
                  >
                    <Feather name="map-pin" size={11} color="#f59e0b" style={{ marginTop: 2 }} />
                    <Text style={[s.suggestText, { color: C.textMuted }]} numberOfLines={2}>{item.label}</Text>
                  </Pressable>
                ))}
              </View>
            )}

            {/* Confirmed place */}
            {selectedLat !== null && (
              <View style={s.confirmedRow}>
                <Feather name="check-circle" size={13} color="#10b981" />
                <Text style={s.confirmedText}>
                  {selectedPlace}{"  "}
                  <Text style={{ color: C.textDim }}>
                    (UTC{(selectedTz ?? 0) >= 0 ? "+" : ""}{selectedTz})
                  </Text>
                </Text>
              </View>
            )}
          </View>

          {/* ── Error ────────────────────────────────────────────────── */}
          {!!error && (
            <View style={s.errorBox}>
              <Feather name="alert-circle" size={14} color="#f87171" />
              <Text style={s.errorText}>{error}</Text>
            </View>
          )}

          {/* ── Submit button ─────────────────────────────────────────── */}
          <Pressable
            onPress={handleSubmit}
            disabled={!canSubmit}
            style={({ pressed }) => [pressed && canSubmit && { opacity: 0.88 }]}
          >
            <LinearGradient
              colors={loading ? [C.bgCard2, C.bgCard2] : [C.btnGradStart, C.btnGradEnd]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={[s.submitBtn, loading && { borderWidth: 1, borderColor: C.border }]}
            >
              {loading ? (
                <View style={s.submitInner}>
                  <ActivityIndicator size="small" color={C.accent} />
                  <Text style={[s.submitText, { color: C.accent }]}>{t.generatingKundli}</Text>
                </View>
              ) : (
                <View style={s.submitInner}>
                  <Feather name="star" size={16} color="#fff" />
                  <Text style={[s.submitText, { color: "#fff" }]}>{t.generateKundli}</Text>
                </View>
              )}
            </LinearGradient>
          </Pressable>

          {/* ── Trust badge ───────────────────────────────────────────── */}
          <View style={s.trustRow}>
            <Feather name="lock" size={11} color={C.textDim} />
            <Text style={[s.trustText, { color: C.textDim }]}>
              Your data is encrypted and private. Never shared with anyone.
            </Text>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>

      {/* ── Day Picker ────────────────────────────────────────────────── */}
      <PickerModal
        visible={dayPickerOpen}
        title="Select Day"
        items={DAYS}
        selected={day}
        onSelect={v => { setDay(v); setDayPickerOpen(false); }}
        onClose={() => setDayPickerOpen(false)}
      />

      {/* ── Month Picker Modal ─────────────────────────────────────────── */}
      <PickerModal
        visible={monthPickerOpen}
        title="Select Month"
        items={MONTHS.map((m, i) => ({ label: m, value: String(i + 1) }))}
        selected={month}
        onSelect={v => { setMonth(v); setMonthPickerOpen(false); }}
        onClose={() => setMonthPickerOpen(false)}
      />

      {/* ── Year Picker ───────────────────────────────────────────────── */}
      <PickerModal
        visible={yearPickerOpen}
        title="Select Birth Year"
        items={YEARS}
        selected={year}
        onSelect={v => { setYear(v); setYearPickerOpen(false); }}
        onClose={() => setYearPickerOpen(false)}
      />

      {/* ── Hour Picker ───────────────────────────────────────────────── */}
      <PickerModal
        visible={hourPickerOpen}
        title="Select Hour (1–12)"
        items={HOURS}
        selected={hour}
        onSelect={v => { setHour(v); setHourPickerOpen(false); }}
        onClose={() => setHourPickerOpen(false)}
      />

      {/* ── Minute Picker ─────────────────────────────────────────────── */}
      <PickerModal
        visible={minPickerOpen}
        title="Select Minute (0–59)"
        items={MINS}
        selected={minute}
        onSelect={v => { setMinute(v); setMinPickerOpen(false); }}
        onClose={() => setMinPickerOpen(false)}
      />

      {/* ── AM/PM Picker Modal ────────────────────────────────────────── */}
      <PickerModal
        visible={ampmPickerOpen}
        title="AM or PM?"
        items={[
          { label: "AM — Morning  (Midnight to Noon)", value: "AM" },
          { label: "PM — Evening  (Noon to Midnight)", value: "PM" },
        ]}
        selected={ampm}
        onSelect={v => { setAmpm(v as "AM"|"PM"); setAmpmPickerOpen(false); }}
        onClose={() => setAmpmPickerOpen(false)}
      />
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root:   { flex: 1 },
  scroll: { paddingHorizontal: 18, paddingTop: 8, gap: 14 },

  // Header
  header: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingHorizontal: 18, paddingBottom: 6, paddingTop: 6,
  },
  backBtn: { padding: 8 },
  skipBtn: { paddingVertical: 6, paddingHorizontal: 12 },
  skipText: { fontSize: 13, fontWeight: "600" },

  // Hero
  hero: { alignItems: "center", paddingVertical: 20, gap: 10 },
  heroIcon: {
    width: 64, height: 64, borderRadius: 32,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
    shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 20, elevation: 8,
  },
  heroTitle: { fontSize: 22, fontWeight: "800", letterSpacing: 0.3 },
  heroSub: {
    fontSize: 13, lineHeight: 20,
    textAlign: "center", paddingHorizontal: 8,
  },

  // Cards
  card: {
    borderRadius: 18, padding: 16,
    borderWidth: 1,
    gap: 12,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 3,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  cardIcon: { width: 28, height: 28, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  cardTitle: { fontSize: 10, fontWeight: "800", letterSpacing: 2 },

  // Input
  input: {
    borderWidth: 1,
    borderRadius: 12,
    fontSize: 15, paddingVertical: 13, paddingHorizontal: 14,
  },

  // Date cells
  dateRow:  { flexDirection: "row", gap: 8 },
  dateCell: { gap: 5 },
  dateLabel: { fontSize: 9, fontWeight: "700", letterSpacing: 1, textTransform: "uppercase" },
  dateInput: {
    borderWidth: 1,
    borderRadius: 12,
    fontSize: 15, paddingVertical: 13, paddingHorizontal: 8,
  },
  datePickerBtn: {
    borderWidth: 1,
    borderRadius: 12, paddingVertical: 13, paddingHorizontal: 12,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  datePickerText: { fontSize: 14 },

  // Warning
  warnBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 7,
    borderWidth: 1,
    borderRadius: 10, paddingHorizontal: 11, paddingVertical: 9,
  },
  warnText: { fontSize: 11, lineHeight: 16, flex: 1 },

  // Place
  placeRow: { flexDirection: "row", gap: 10, alignItems: "center" },
  searchBtn: {
    width: 44, height: 44, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
    shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 10, elevation: 4,
  },

  suggestBox: {
    borderRadius: 12, borderWidth: 1,
    overflow: "hidden",
  },
  suggestItem: { flexDirection: "row", alignItems: "flex-start", gap: 8, paddingHorizontal: 14, paddingVertical: 13 },
  suggestBorder: { borderBottomWidth: 1 },
  suggestText: { fontSize: 13, flex: 1 },

  confirmedRow: { flexDirection: "row", alignItems: "center", gap: 7 },
  confirmedText: { color: "#10b981", fontSize: 12, flex: 1 },

  // Error
  errorBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 9,
    backgroundColor: "rgba(239,68,68,0.08)",
    borderWidth: 1, borderColor: "rgba(239,68,68,0.2)",
    borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12,
  },
  errorText: { color: "#f87171", fontSize: 13, flex: 1 },

  // Submit
  submitBtn: {
    borderRadius: 16, paddingVertical: 17, marginTop: 4,
    shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.22, shadowRadius: 18, elevation: 6,
  },
  submitInner: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10 },
  submitText:  { fontSize: 16, fontWeight: "800", letterSpacing: 0.3 },

  // Trust
  trustRow: {
    flexDirection: "row", alignItems: "flex-start", gap: 7,
    justifyContent: "center", paddingHorizontal: 20,
  },
  trustText: { fontSize: 11, textAlign: "center", lineHeight: 16, flex: 1 },
});
