import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Modal,
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

import { useUser } from "@/context/UserContext";
import { fetchKundliFromAPI, fetchTimezone, searchPlaces, type PlaceSuggestion } from "@/lib/kundliAPI";

const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December",
];

export default function OnboardingScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { setBirthData, setKundli } = useUser();

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

  const [monthPickerOpen, setMonthPickerOpen] = useState(false);
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
          <Feather name="arrow-left" size={20} color="#64748b" />
        </Pressable>
        <Pressable
          onPress={() => router.replace("/(tabs)")}
          style={({ pressed }) => [s.skipBtn, pressed && { opacity: 0.5 }]}
        >
          <Text style={s.skipText}>Skip</Text>
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
              colors={["rgba(0,198,255,0.18)", "rgba(120,80,255,0.10)"]}
              style={s.heroIcon}
            >
              <Feather name="star" size={26} color="#00c6ff" />
            </LinearGradient>
            <Text style={s.heroTitle}>Birth Details</Text>
            <Text style={s.heroSub}>
              Accurate birth details are needed for a correct Kundli.{"\n"}This data is kept private and secure.
            </Text>
          </View>

          {/* ── Section: Full Name ────────────────────────────────────── */}
          <View style={s.card}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(167,139,250,0.12)" }]}>
                <Feather name="user" size={14} color="#a78bfa" />
              </View>
              <Text style={s.cardTitle}>YOUR NAME</Text>
            </View>
            <TextInput
              style={s.input}
              placeholder="Enter full name"
              placeholderTextColor="#334155"
              value={name}
              onChangeText={setName}
              returnKeyType="next"
              autoCapitalize="words"
            />
          </View>

          {/* ── Section: Date of Birth ────────────────────────────────── */}
          <View style={s.card}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(0,198,255,0.10)" }]}>
                <Feather name="calendar" size={14} color="#00c6ff" />
              </View>
              <Text style={s.cardTitle}>DATE OF BIRTH</Text>
            </View>
            <View style={s.dateRow}>
              {/* Day */}
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={s.dateLabel}>Day</Text>
                <TextInput
                  style={s.dateInput}
                  placeholder="DD"
                  placeholderTextColor="#334155"
                  value={day}
                  onChangeText={setDay}
                  keyboardType="number-pad"
                  maxLength={2}
                  textAlign="center"
                />
              </View>

              {/* Month */}
              <View style={[s.dateCell, { flex: 2 }]}>
                <Text style={s.dateLabel}>Month</Text>
                <Pressable
                  style={s.datePickerBtn}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setMonthPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: month ? "#e2e8f0" : "#334155" }]}>
                    {month ? MONTHS[parseInt(month) - 1] : "Select"}
                  </Text>
                  <Feather name="chevron-down" size={13} color="#475569" />
                </Pressable>
              </View>

              {/* Year */}
              <View style={[s.dateCell, { flex: 1.5 }]}>
                <Text style={s.dateLabel}>Birth Year</Text>
                <TextInput
                  style={s.dateInput}
                  placeholder="YYYY"
                  placeholderTextColor="#334155"
                  value={year}
                  onChangeText={setYear}
                  keyboardType="number-pad"
                  maxLength={4}
                  textAlign="center"
                />
              </View>
            </View>
          </View>

          {/* ── Section: Time of Birth ────────────────────────────────── */}
          <View style={s.card}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(250,204,21,0.10)" }]}>
                <Feather name="clock" size={14} color="#facc15" />
              </View>
              <Text style={s.cardTitle}>TIME OF BIRTH</Text>
            </View>

            {/* Warning */}
            <View style={s.warnBox}>
              <Feather name="alert-triangle" size={11} color="#f59e0b" style={{ marginTop: 1 }} />
              <Text style={s.warnText}>
                Birth time directly affects Mahadasha. Please verify AM or PM carefully.
              </Text>
            </View>

            <View style={s.dateRow}>
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={s.dateLabel}>Hour</Text>
                <TextInput
                  style={s.dateInput}
                  placeholder="HH"
                  placeholderTextColor="#334155"
                  value={hour}
                  onChangeText={setHour}
                  keyboardType="number-pad"
                  maxLength={2}
                  textAlign="center"
                />
              </View>
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={s.dateLabel}>Minute</Text>
                <TextInput
                  style={s.dateInput}
                  placeholder="MM"
                  placeholderTextColor="#334155"
                  value={minute}
                  onChangeText={setMinute}
                  keyboardType="number-pad"
                  maxLength={2}
                  textAlign="center"
                />
              </View>
              <View style={[s.dateCell, { flex: 1 }]}>
                <Text style={s.dateLabel}>AM / PM</Text>
                <Pressable
                  style={s.datePickerBtn}
                  onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setAmpmPickerOpen(true); }}
                >
                  <Text style={[s.datePickerText, { color: "#e2e8f0" }]}>{ampm}</Text>
                  <Feather name="chevron-down" size={13} color="#475569" />
                </Pressable>
              </View>
            </View>
          </View>

          {/* ── Section: Place of Birth ───────────────────────────────── */}
          <View style={s.card}>
            <View style={s.cardHeader}>
              <View style={[s.cardIcon, { backgroundColor: "rgba(16,185,129,0.10)" }]}>
                <Feather name="map-pin" size={14} color="#10b981" />
              </View>
              <Text style={s.cardTitle}>PLACE OF BIRTH</Text>
            </View>

            <View style={s.placeRow}>
              <TextInput
                style={[s.input, { flex: 1, marginBottom: 0 }]}
                placeholder="Enter city name..."
                placeholderTextColor="#334155"
                value={placeQuery}
                onChangeText={t => { setPlaceQuery(t); setSelectedLat(null); setSelectedPlace(""); }}
                onSubmitEditing={doSearchPlace}
                returnKeyType="search"
              />
              <Pressable
                onPress={doSearchPlace}
                style={({ pressed }) => [s.searchBtn, pressed && { opacity: 0.7 }]}
              >
                {searching
                  ? <ActivityIndicator size="small" color="#020d1a" />
                  : <Feather name="search" size={15} color="#020d1a" />
                }
              </Pressable>
            </View>

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <View style={s.suggestBox}>
                {suggestions.map((item, i) => (
                  <Pressable
                    key={i}
                    onPress={() => selectPlace(item)}
                    style={({ pressed }) => [
                      s.suggestItem,
                      i < suggestions.length - 1 && s.suggestBorder,
                      pressed && { backgroundColor: "rgba(0,198,255,0.06)" },
                    ]}
                  >
                    <Feather name="map-pin" size={11} color="#00c6ff" style={{ marginTop: 2 }} />
                    <Text style={s.suggestText} numberOfLines={2}>{item.label}</Text>
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
                  <Text style={{ color: "#334155" }}>
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
              colors={loading ? ["#0a1828","#0a1828"] : ["#006aff","#00c6ff"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={[s.submitBtn, loading && { borderWidth: 1, borderColor: "#1e3a5f" }]}
            >
              {loading ? (
                <View style={s.submitInner}>
                  <ActivityIndicator size="small" color="#00c6ff" />
                  <Text style={[s.submitText, { color: "#00c6ff" }]}>Generating Kundli...</Text>
                </View>
              ) : (
                <View style={s.submitInner}>
                  <Feather name="star" size={16} color="#fff" />
                  <Text style={[s.submitText, { color: "#fff" }]}>Create My Kundli</Text>
                </View>
              )}
            </LinearGradient>
          </Pressable>

          {/* ── Trust badge ───────────────────────────────────────────── */}
          <View style={s.trustRow}>
            <Feather name="lock" size={11} color="#1e3a5f" />
            <Text style={s.trustText}>
              Your data is encrypted and private. Never shared with anyone.
            </Text>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>

      {/* ── Month Picker Modal ─────────────────────────────────────────── */}
      <PickerModal
        visible={monthPickerOpen}
        title="Select Month"
        items={MONTHS.map((m, i) => ({ label: m, value: String(i + 1) }))}
        selected={month}
        onSelect={v => { setMonth(v); setMonthPickerOpen(false); }}
        onClose={() => setMonthPickerOpen(false)}
      />

      {/* ── AM/PM Picker Modal ────────────────────────────────────────── */}
      <PickerModal
        visible={ampmPickerOpen}
        title="AM or PM?"
        items={[{ label: "AM — Morning (Midnight to Noon)", value: "AM" }, { label: "PM — Evening (After Noon)", value: "PM" }]}
        selected={ampm}
        onSelect={v => { setAmpm(v as "AM"|"PM"); setAmpmPickerOpen(false); }}
        onClose={() => setAmpmPickerOpen(false)}
      />
    </View>
  );
}

// ── Picker Modal ──────────────────────────────────────────────────────────────
function PickerModal({
  visible, title, items, selected, onSelect, onClose,
}: {
  visible: boolean;
  title: string;
  items: { label: string; value: string }[];
  selected: string;
  onSelect: (v: string) => void;
  onClose: () => void;
}) {
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={pm.overlay} onPress={onClose} />
      <View style={pm.sheet}>
        <View style={pm.handle} />
        <Text style={pm.title}>{title}</Text>
        <FlatList
          data={items}
          keyExtractor={i => i.value}
          renderItem={({ item }) => (
            <Pressable
              style={({ pressed }) => [
                pm.item,
                item.value === selected && pm.itemSel,
                pressed && { opacity: 0.7 },
              ]}
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); onSelect(item.value); }}
            >
              <Text style={[pm.itemText, item.value === selected && pm.itemTextSel]}>
                {item.label}
              </Text>
              {item.value === selected && <Feather name="check" size={14} color="#00c6ff" />}
            </Pressable>
          )}
          style={{ maxHeight: 360 }}
        />
      </View>
    </Modal>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root:   { flex: 1, backgroundColor: "#020d1a" },
  scroll: { paddingHorizontal: 18, paddingTop: 8, gap: 14 },

  // Header
  header: {
    flexDirection: "row", justifyContent: "space-between", alignItems: "center",
    paddingHorizontal: 18, paddingBottom: 6, paddingTop: 6,
  },
  backBtn: { padding: 8 },
  skipBtn: { paddingVertical: 6, paddingHorizontal: 12 },
  skipText: { color: "#334155", fontSize: 13, fontWeight: "600" },

  // Hero
  hero: { alignItems: "center", paddingVertical: 20, gap: 10 },
  heroIcon: {
    width: 64, height: 64, borderRadius: 32,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(0,198,255,0.25)",
    shadowColor: "#00c6ff", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 20, elevation: 8,
  },
  heroTitle: { color: "#dde8f4", fontSize: 22, fontWeight: "800", letterSpacing: 0.3 },
  heroSub: {
    color: "#334155", fontSize: 13, lineHeight: 20,
    textAlign: "center", paddingHorizontal: 8,
  },

  // Cards
  card: {
    backgroundColor: "#040e1f",
    borderRadius: 18, padding: 16,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
    gap: 12,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, shadowRadius: 8, elevation: 3,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  cardIcon: { width: 28, height: 28, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  cardTitle: { color: "#1e4a6e", fontSize: 10, fontWeight: "800", letterSpacing: 2 },

  // Input
  input: {
    backgroundColor: "#071525",
    borderWidth: 1, borderColor: "#0f2540",
    borderRadius: 12, color: "#e2e8f0",
    fontSize: 15, paddingVertical: 13, paddingHorizontal: 14,
  },

  // Date cells
  dateRow:  { flexDirection: "row", gap: 8 },
  dateCell: { gap: 5 },
  dateLabel: { color: "#1e3a5f", fontSize: 9, fontWeight: "700", letterSpacing: 1, textTransform: "uppercase" },
  dateInput: {
    backgroundColor: "#071525",
    borderWidth: 1, borderColor: "#0f2540",
    borderRadius: 12, color: "#e2e8f0",
    fontSize: 15, paddingVertical: 13, paddingHorizontal: 8,
  },
  datePickerBtn: {
    backgroundColor: "#071525",
    borderWidth: 1, borderColor: "#0f2540",
    borderRadius: 12, paddingVertical: 13, paddingHorizontal: 12,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  datePickerText: { fontSize: 14 },

  // Warning
  warnBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 7,
    backgroundColor: "rgba(245,158,11,0.07)",
    borderWidth: 1, borderColor: "rgba(245,158,11,0.20)",
    borderRadius: 10, paddingHorizontal: 11, paddingVertical: 9,
  },
  warnText: { color: "#d97706", fontSize: 11, lineHeight: 16, flex: 1 },

  // Place
  placeRow: { flexDirection: "row", gap: 10, alignItems: "center" },
  searchBtn: {
    backgroundColor: "#00c6ff",
    width: 44, height: 44, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
    shadowColor: "#00c6ff", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 10, elevation: 4,
  },

  suggestBox: {
    backgroundColor: "#071525",
    borderRadius: 12, borderWidth: 1, borderColor: "#0f2540",
    overflow: "hidden",
  },
  suggestItem: { flexDirection: "row", alignItems: "flex-start", gap: 8, paddingHorizontal: 14, paddingVertical: 13 },
  suggestBorder: { borderBottomWidth: 1, borderBottomColor: "#0a1828" },
  suggestText: { color: "#64748b", fontSize: 13, flex: 1 },

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
    shadowColor: "#00c6ff", shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.22, shadowRadius: 18, elevation: 6,
  },
  submitInner: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10 },
  submitText:  { fontSize: 16, fontWeight: "800", letterSpacing: 0.3 },

  // Trust
  trustRow: {
    flexDirection: "row", alignItems: "flex-start", gap: 7,
    justifyContent: "center", paddingHorizontal: 20,
  },
  trustText: { color: "#1e3a5f", fontSize: 11, textAlign: "center", lineHeight: 16, flex: 1 },
});

const pm = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.6)" },
  sheet: {
    backgroundColor: "#071525",
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    paddingHorizontal: 20, paddingBottom: 44, paddingTop: 16,
    borderTopWidth: 1, borderColor: "rgba(0,200,255,0.12)",
  },
  handle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: "#0f2540", alignSelf: "center", marginBottom: 16,
  },
  title:        { color: "#64748b", fontSize: 14, fontWeight: "700", marginBottom: 12, letterSpacing: 0.3 },
  item:         { paddingVertical: 15, paddingHorizontal: 6, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: "#0a1828" },
  itemSel:      { backgroundColor: "rgba(0,198,255,0.06)" },
  itemText:     { color: "#475569", fontSize: 15 },
  itemTextSel:  { color: "#00c6ff", fontWeight: "700" },
});
