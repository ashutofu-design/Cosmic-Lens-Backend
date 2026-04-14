import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator, KeyboardAvoidingView, Platform,
  Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fetchKundliFromAPI } from "@/lib/kundliAPI";
import { useUser } from "@/context/UserContext";
import type { BirthData } from "@/types";

const BASE_URL = `https://${process.env.EXPO_PUBLIC_DOMAIN}`;

const MONTHS = [
  "Jan","Feb","Mar","Apr","May","Jun",
  "Jul","Aug","Sep","Oct","Nov","Dec",
];

interface GeoResult { label: string; lat: number; lon: number; tz: number; }

async function searchPlace(q: string): Promise<GeoResult[]> {
  const r = await fetch(
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=5&addressdetails=1`,
  );
  const rows = await r.json();
  return rows.map((x: { display_name: string; lat: string; lon: string }) => ({
    label: x.display_name.split(",").slice(0, 3).join(", "),
    lat: parseFloat(x.lat),
    lon: parseFloat(x.lon),
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

// ── Month picker ──────────────────────────────────────────────────────────────
function MonthPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <View style={{ flexDirection:"row", flexWrap:"wrap", gap:6 }}>
      {MONTHS.map((m, i) => {
        const v = String(i + 1);
        const active = value === v;
        return (
          <Pressable key={m} onPress={() => onChange(v)}
            style={{ paddingHorizontal:10, paddingVertical:6, borderRadius:8,
              backgroundColor: active ? "#00d4ff22" : "#0a1828",
              borderWidth:1, borderColor: active ? "#00d4ff66" : "#1e293b" }}>
            <Text style={{ color: active ? "#00d4ff" : "#475569", fontSize:12, fontWeight:"600" }}>{m}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

// ── AM/PM toggle ──────────────────────────────────────────────────────────────
function AmPmToggle({ value, onChange }: { value: "AM"|"PM"; onChange: (v:"AM"|"PM") => void }) {
  return (
    <View style={{ flexDirection:"row", gap:8 }}>
      {(["AM","PM"] as const).map(v => (
        <Pressable key={v} onPress={() => onChange(v)}
          style={{ flex:1, paddingVertical:10, borderRadius:10, alignItems:"center",
            backgroundColor: value===v ? "#00d4ff22" : "#0a1828",
            borderWidth:1, borderColor: value===v ? "#00d4ff66" : "#1e293b" }}>
          <Text style={{ color: value===v ? "#00d4ff" : "#475569", fontWeight:"700", fontSize:13 }}>{v}</Text>
        </Pressable>
      ))}
    </View>
  );
}

export default function ProfileEditScreen() {
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ mode?: string; profileId?: string }>();
  const { profiles, addProfile, updateProfile, setBirthData, setKundli, primaryProfileId } = useUser();

  const isEdit   = params.mode === "edit" && !!params.profileId;
  const profile  = isEdit ? profiles.find(p => p.id === params.profileId) : null;

  const [f, setF]           = useState<FormState>(() => {
    if (profile) {
      const bd = profile.birthData;
      return {
        name: profile.name, gender: profile.gender,
        day: String(bd.day), month: String(bd.month), year: String(bd.year),
        hour: String(bd.hour), minute: String(bd.minute), ampm: bd.ampm,
        place: bd.place, lat: bd.lat, lon: bd.lon, tz: bd.tz,
      };
    }
    return blank();
  });

  const [placeQuery,  setPlaceQuery]  = useState(f.place);
  const [geoResults,  setGeoResults]  = useState<GeoResult[]>([]);
  const [searching,   setSearching]   = useState(false);
  const [tzLoading,   setTzLoading]   = useState(false);
  const [saving,      setSaving]      = useState(false);
  const [error,       setError]       = useState("");

  const set = (key: keyof FormState) => (val: string) =>
    setF(prev => ({ ...prev, [key]: val }));

  async function handlePlaceSearch() {
    if (placeQuery.trim().length < 2) return;
    setSearching(true);
    setGeoResults([]);
    try { setGeoResults(await searchPlace(placeQuery)); }
    catch { setError("Could not find location. Please check your internet."); }
    finally { setSearching(false); }
  }

  async function selectGeo(g: GeoResult) {
    setF(prev => ({ ...prev, place: g.label, lat: g.lat, lon: g.lon, tz: g.tz }));
    setPlaceQuery(g.label);
    setGeoResults([]);
    setTzLoading(true);
    try {
      const r = await fetch(`${BASE_URL}/api/timezone?lat=${g.lat}&lon=${g.lon}`);
      const d = await r.json();
      if (typeof d.tz === "number") setF(prev => ({ ...prev, tz: d.tz }));
    } catch {}
    finally { setTzLoading(false); }
  }

  async function handleSave() {
    if (!f.name.trim())   { setError("Name is required."); return; }
    if (!f.day || !f.month || !f.year) { setError("Please enter date of birth."); return; }
    if (!f.hour || !f.minute) { setError("Please enter birth time."); return; }
    if (!f.lat) { setError("Please search and select a place from the list."); return; }
    if (tzLoading) { setError("Confirming timezone..."); return; }
    setError("");
    setSaving(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const birthData: BirthData = {
        name:   f.name.trim(),
        day:    Number(f.day),
        month:  Number(f.month),
        year:   Number(f.year),
        hour:   Number(f.hour),
        minute: Number(f.minute),
        ampm:   f.ampm,
        place:  f.place,
        lat:    f.lat,
        lon:    f.lon,
        tz:     f.tz,
      };
      const kundli = await fetchKundliFromAPI(birthData);

      if (isEdit && params.profileId) {
        updateProfile(params.profileId, {
          name: f.name.trim(), gender: f.gender, birthData, kundli,
        });
        // If editing primary profile, update compat state too
        if (params.profileId === primaryProfileId) {
          setBirthData(birthData);
          setKundli(kundli);
        }
      } else {
        addProfile({ name: f.name.trim(), gender: f.gender, birthData, kundli });
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Chart calculation failed. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: "#020d1a" }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      {/* Header */}
      <View style={[s.header, { paddingTop: insets.top + 12 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color="#64748b" />
        </Pressable>
        <Text style={s.headerTitle}>{isEdit ? "Edit Profile" : "Add New Profile"}</Text>
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 20, paddingBottom: insets.bottom + 100 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >

        {/* Name */}
        <View style={s.field}>
          <Text style={s.label}>FULL NAME</Text>
          <TextInput
            style={s.input} value={f.name} onChangeText={set("name")}
            placeholder="Enter name" placeholderTextColor="#334155"
          />
        </View>

        {/* Gender */}
        <View style={s.field}>
          <Text style={s.label}>GENDER (OPTIONAL)</Text>
          <View style={{ flexDirection:"row", gap:8, flexWrap:"wrap" }}>
            {["Male","Female","Other"].map(g => (
              <Pressable key={g} onPress={() => setF(prev => ({ ...prev, gender: g }))}
                style={{ paddingHorizontal:14, paddingVertical:8, borderRadius:10,
                  backgroundColor: f.gender===g ? "#00d4ff22" : "#0a1828",
                  borderWidth:1, borderColor: f.gender===g ? "#00d4ff66" : "#1e293b" }}>
                <Text style={{ color: f.gender===g ? "#00d4ff" : "#475569", fontSize:13, fontWeight:"600" }}>{g}</Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Date of birth */}
        <View style={s.field}>
          <Text style={s.label}>DATE OF BIRTH</Text>
          <View style={{ flexDirection:"row", gap:10, marginBottom:10 }}>
            <TextInput
              style={[s.input, { flex:1 }]} value={f.day} onChangeText={set("day")}
              placeholder="DD" placeholderTextColor="#334155" keyboardType="number-pad" maxLength={2}
            />
            <TextInput
              style={[s.input, { flex:2 }]} value={f.year} onChangeText={set("year")}
              placeholder="YYYY" placeholderTextColor="#334155" keyboardType="number-pad" maxLength={4}
            />
          </View>
          <MonthPicker value={f.month} onChange={set("month")} />
        </View>

        {/* Time of birth */}
        <View style={s.field}>
          <Text style={s.label}>TIME OF BIRTH</Text>
          <View style={s.warningBox}>
            <Text style={s.warningText}>⚠ Birth time directly affects Mahadasha. Choose AM/PM carefully.</Text>
          </View>
          <View style={{ flexDirection:"row", gap:10, marginBottom:10 }}>
            <TextInput
              style={[s.input, { flex:1 }]} value={f.hour} onChangeText={set("hour")}
              placeholder="HH (1–12)" placeholderTextColor="#334155" keyboardType="number-pad" maxLength={2}
            />
            <TextInput
              style={[s.input, { flex:1 }]} value={f.minute} onChangeText={set("minute")}
              placeholder="MM (0–59)" placeholderTextColor="#334155" keyboardType="number-pad" maxLength={2}
            />
          </View>
          <AmPmToggle value={f.ampm} onChange={v => setF(prev => ({ ...prev, ampm: v }))} />
        </View>

        {/* Place of birth */}
        <View style={s.field}>
          <Text style={s.label}>PLACE OF BIRTH</Text>
          <View style={{ flexDirection:"row", gap:8 }}>
            <TextInput
              style={[s.input, { flex:1 }]}
              value={placeQuery} onChangeText={setPlaceQuery}
              onSubmitEditing={handlePlaceSearch}
              placeholder="City, Country" placeholderTextColor="#334155"
              returnKeyType="search"
            />
            <Pressable onPress={handlePlaceSearch}
              style={{ paddingHorizontal:14, paddingVertical:12, backgroundColor:"#00d4ff18",
                borderRadius:10, borderWidth:1, borderColor:"#00d4ff44", justifyContent:"center" }}>
              {searching
                ? <ActivityIndicator size="small" color="#00d4ff" />
                : <Text style={{ color:"#00d4ff", fontSize:12, fontWeight:"700" }}>SEARCH</Text>
              }
            </Pressable>
          </View>

          {geoResults.length > 0 && (
            <View style={s.geoList}>
              {geoResults.map((g, i) => (
                <Pressable key={i} onPress={() => selectGeo(g)}
                  style={[s.geoItem, i < geoResults.length-1 && { borderBottomWidth:1, borderBottomColor:"#1e293b" }]}>
                  <Text style={s.geoText} numberOfLines={2}>{g.label}</Text>
                </Pressable>
              ))}
            </View>
          )}

          {f.lat !== 0 && (
            <View style={{ flexDirection:"row", alignItems:"center", gap:6, marginTop:6 }}>
              <Feather name="check-circle" size={12} color="#00a86b" />
              <Text style={{ color:"#00a86b", fontSize:11 }} numberOfLines={1}>{f.place}</Text>
              {tzLoading && <ActivityIndicator size="small" color="#00d4ff" style={{ marginLeft:4 }} />}
            </View>
          )}
        </View>

        {/* Error */}
        {!!error && (
          <View style={s.errorBox}>
            <Text style={s.errorText}>{error}</Text>
          </View>
        )}

        {/* Save button */}
        <Pressable
          onPress={handleSave}
          disabled={saving || tzLoading}
          style={({ pressed }) => [s.saveBtn, (saving || tzLoading) && { opacity:0.6 }, pressed && { opacity:0.8 }]}
        >
          {saving
            ? <ActivityIndicator color="#fff" />
            : <Text style={s.saveBtnText}>{isEdit ? "Save Profile" : "Create Profile"}</Text>
          }
        </Pressable>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection:"row", alignItems:"center", gap:14,
    paddingHorizontal:20, paddingBottom:14,
    borderBottomWidth:1, borderBottomColor:"#0a1828",
  },
  backBtn: { padding:4 },
  headerTitle: { fontSize:16, fontWeight:"700", color:"#dde8f4" },

  field: { marginBottom:24 },
  label: { fontSize:10, fontWeight:"800", letterSpacing:2, color:"#00d4ff", marginBottom:10 },
  input: {
    backgroundColor:"#040e20", color:"#dde8f4", fontSize:14,
    paddingHorizontal:14, paddingVertical:12, borderRadius:10,
    borderWidth:1, borderColor:"#1e293b",
  },

  warningBox: {
    backgroundColor:"#0d1a2a", borderRadius:10,
    borderWidth:1, borderColor:"#f59e0b44", marginBottom:10,
    paddingHorizontal:12, paddingVertical:10,
  },
  warningText: { color:"#f59e0b", fontSize:11, lineHeight:16 },

  geoList: {
    marginTop:8, backgroundColor:"#040e20", borderRadius:12,
    borderWidth:1, borderColor:"#1e293b", overflow:"hidden",
  },
  geoItem: { paddingHorizontal:14, paddingVertical:12 },
  geoText: { color:"#94a3b8", fontSize:12, lineHeight:18 },

  errorBox: {
    backgroundColor:"#1a0a0a", borderRadius:10,
    paddingHorizontal:14, paddingVertical:10, marginBottom:16,
  },
  errorText: { color:"#f87171", fontSize:13 },

  saveBtn: {
    backgroundColor:"#00a86b", borderRadius:14,
    paddingVertical:16, alignItems:"center", justifyContent:"center",
  },
  saveBtnText: { color:"#fff", fontSize:16, fontWeight:"700" },
});
