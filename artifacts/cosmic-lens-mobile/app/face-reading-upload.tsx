import { Feather } from "@expo/vector-icons";
import * as FileSystem from "expo-file-system/legacy";
import * as ImagePicker from "expo-image-picker";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import * as Sharing from "expo-sharing";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { API_BASE } from "@/lib/apiConfig";

type Slot = "front" | "left" | "right";
type Phase = "idle" | "uploading" | "analyzing" | "rendering" | "done" | "error";

const ACCENT  = "#ec4899";
const GOLD    = "#C2A878";
const ACCENT2 = "#7B1F1F";

const SLOTS: { key: Slot; label: string; hint: string; emoji: string }[] = [
  { key: "front", label: "Front Selfie",   hint: "Camera ki taraf seedha dekhein",       emoji: "🙂" },
  { key: "left",  label: "Left Profile",   hint: "Apna left side camera ke saamne",      emoji: "👈" },
  { key: "right", label: "Right Profile",  hint: "Apna right side camera ke saamne",     emoji: "👉" },
];

export default function FaceReadingUploadScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;

  const [photos, setPhotos] = useState<Record<Slot, string | null>>({
    front: null, left: null, right: null,
  });
  const [age, setAge]       = useState("");
  const [gender, setGender] = useState<"male" | "female" | "">("");
  const [phase, setPhase]   = useState<Phase>("idle");
  const [progress, setProgress] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [pdfUri, setPdfUri]     = useState<string | null>(null);

  async function pick(slot: Slot, source: "camera" | "library") {
    try {
      let res;
      if (source === "camera") {
        const perm = await ImagePicker.requestCameraPermissionsAsync();
        if (!perm.granted) { Alert.alert("Camera permission needed"); return; }
        res = await ImagePicker.launchCameraAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          quality: 0.85, allowsEditing: false, cameraType: ImagePicker.CameraType.front,
        });
      } else {
        const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!perm.granted) { Alert.alert("Gallery permission needed"); return; }
        res = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: ImagePicker.MediaTypeOptions.Images,
          quality: 0.85, allowsEditing: false,
        });
      }
      if (!res.canceled && res.assets?.[0]) {
        setPhotos(p => ({ ...p, [slot]: res.assets[0].uri }));
      }
    } catch (e: any) {
      Alert.alert("Could not pick photo", String(e?.message || e));
    }
  }

  function pickPrompt(slot: Slot) {
    // Web preview ka Alert multi-button reliably nahi chalta — direct gallery open karo
    if (Platform.OS === "web") {
      pick(slot, "library");
      return;
    }
    Alert.alert("Add photo", "Camera ya gallery se choose karein", [
      { text: "Camera",  onPress: () => pick(slot, "camera") },
      { text: "Gallery", onPress: () => pick(slot, "library") },
      { text: "Cancel",  style: "cancel" },
    ]);
  }

  const allReady = !!(photos.front && photos.left && photos.right);

  async function generate() {
    if (!allReady) { Alert.alert("Add 3 photos first"); return; }
    setErrorMsg("");
    setPdfUri(null);
    try {
      // ── 1. Upload ─────────────────────────────────────────
      setPhase("uploading");
      setProgress("Photos upload kar rahe hain…");
      const fd = new FormData();
      (["front", "left", "right"] as const).forEach(k => {
        const uri = photos[k]!;
        const name = `${k}.jpg`;
        // RN FormData accepts {uri,name,type}
        fd.append(k, { uri, name, type: "image/jpeg" } as any);
      });
      const extractRes = await fetch(`${API_BASE}/api/face_reading/extract`, {
        method: "POST", body: fd,
      });
      if (!extractRes.ok) throw new Error(`Extract failed (${extractRes.status})`);
      const extractJson = await extractRes.json();
      const sid = extractJson.session_id;
      if (!sid) throw new Error("Session ID missing from server");

      // ── 2. Analyze ────────────────────────────────────────
      setPhase("analyzing");
      setProgress("19 engines analysis chal raha hai…");
      const params = new URLSearchParams();
      params.append("session_id", sid);
      if (age)    params.append("age", age);
      if (gender) params.append("gender", gender);
      const analyzeRes = await fetch(`${API_BASE}/api/face_reading/analyze`, {
        method:  "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body:    params.toString(),
      });
      if (!analyzeRes.ok) throw new Error(`Analyze failed (${analyzeRes.status})`);

      // ── 3. Render PDF ─────────────────────────────────────
      setPhase("rendering");
      setProgress("40-page PDF report ban rahi hai…");
      const pdfUrl = `${API_BASE}/api/face_reading/report.pdf?session_id=${sid}`;
      const target = (FileSystem.documentDirectory || FileSystem.cacheDirectory) + `face_reading_${sid}.pdf`;
      const dl = await FileSystem.downloadAsync(pdfUrl, target);
      if (dl.status !== 200) throw new Error(`PDF download failed (${dl.status})`);

      setPdfUri(dl.uri);
      setPhase("done");
      setProgress("Report ready!");
    } catch (e: any) {
      setPhase("error");
      setErrorMsg(String(e?.message || e));
    }
  }

  async function sharePdf() {
    if (!pdfUri) return;
    const ok = await Sharing.isAvailableAsync();
    if (!ok) { Alert.alert("Sharing not available on this device"); return; }
    await Sharing.shareAsync(pdfUri, { mimeType: "application/pdf", UTI: "com.adobe.pdf" });
  }

  function reset() {
    setPhotos({ front: null, left: null, right: null });
    setAge(""); setGender("");
    setPhase("idle"); setProgress(""); setErrorMsg(""); setPdfUri(null);
  }

  const busy = phase === "uploading" || phase === "analyzing" || phase === "rendering";

  return (
    <CosmicBg>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 4 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={12}>
          <Feather name="chevron-left" size={26} color={C.text} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>Face Reading Pro</Text>
        <View style={{ width: 26 }} />
      </View>

      <ScrollView
        contentContainerStyle={[s.scroll, { paddingBottom: insets.bottom + 32 }]}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Intro */}
        <View style={[s.introCard, { borderColor: C.border }]}>
          <LinearGradient
            colors={[`${ACCENT2}55`, `${ACCENT}22`, "transparent"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={StyleSheet.absoluteFill as any}
          />
          <Text style={[s.introEyebrow, { color: GOLD }]}>STEP 1 OF 2</Text>
          <Text style={[s.introTitle, { color: C.text }]}>3 selfies upload karein</Text>
          <Text style={[s.introSub, { color: C.textMuted }]}>
            Front + left + right profile. Achi roshni mein lein, chashma utar dein, baal forehead se hata lein.
          </Text>
        </View>

        {/* 3 photo slots */}
        {SLOTS.map(slot => {
          const uri = photos[slot.key];
          const filled = !!uri;
          return (
            <Pressable
              key={slot.key}
              onPress={() => !busy && pickPrompt(slot.key)}
              style={[
                s.slot,
                { borderColor: filled ? ACCENT : C.border, backgroundColor: C.bgCard },
                filled && { borderWidth: 1.5 },
              ]}
            >
              <View style={[s.slotThumb, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
                {filled ? (
                  <Image source={{ uri: uri! }} style={s.slotImg} />
                ) : (
                  <Text style={s.slotEmoji}>{slot.emoji}</Text>
                )}
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[s.slotLabel, { color: C.text }]}>{slot.label}</Text>
                <Text style={[s.slotHint,  { color: C.textMuted }]}>{slot.hint}</Text>
                {filled && (
                  <View style={s.slotMeta}>
                    <Feather name="check-circle" size={12} color="#10b981" />
                    <Text style={[s.slotMetaText, { color: "#10b981" }]}>Added · tap to change</Text>
                  </View>
                )}
              </View>
              <Feather name={filled ? "edit-2" : "plus-circle"} size={20} color={filled ? ACCENT : C.textMuted} />
            </Pressable>
          );
        })}

        {/* Optional details */}
        <Text style={[s.sectionCap, { color: C.textDim }]}>OPTIONAL — BETTER ACCURACY</Text>
        <View style={[s.optCard, { borderColor: C.border, backgroundColor: C.bgCard }]}>
          <View style={s.optRow}>
            <Text style={[s.optLabel, { color: C.textMuted }]}>Age</Text>
            <TextInput
              style={[s.optInput, { color: C.text, borderColor: C.border, backgroundColor: C.bgCard2 }]}
              placeholder="e.g. 28"
              placeholderTextColor={C.textDim}
              keyboardType="number-pad"
              value={age}
              onChangeText={setAge}
              maxLength={3}
              editable={!busy}
            />
          </View>
          <View style={[s.optRow, { marginTop: 10 }]}>
            <Text style={[s.optLabel, { color: C.textMuted }]}>Gender</Text>
            <View style={{ flexDirection: "row", gap: 8 }}>
              {(["male", "female"] as const).map(g => {
                const active = gender === g;
                return (
                  <Pressable
                    key={g}
                    onPress={() => !busy && setGender(active ? "" : g)}
                    style={[
                      s.genderChip,
                      { borderColor: C.border, backgroundColor: C.bgCard2 },
                      active && { borderColor: ACCENT, backgroundColor: `${ACCENT}18` },
                    ]}
                  >
                    <Text style={[s.genderText, { color: active ? ACCENT : C.textMuted }]}>
                      {g === "male" ? "Male" : "Female"}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        </View>

        {/* Progress / Error / Done */}
        {busy && (
          <View style={[s.progressCard, { borderColor: C.border, backgroundColor: C.bgCard }]}>
            <ActivityIndicator color={ACCENT} />
            <View style={{ flex: 1 }}>
              <Text style={[s.progressTitle, { color: C.text }]}>{progress}</Text>
              <Text style={[s.progressSub,   { color: C.textDim }]}>Yeh ~30-60 seconds le sakta hai. App ko close mat karein.</Text>
            </View>
          </View>
        )}

        {phase === "error" && (
          <View style={[s.errorCard, { borderColor: "rgba(239,68,68,0.4)", backgroundColor: "rgba(239,68,68,0.08)" }]}>
            <Feather name="alert-octagon" size={16} color="#ef4444" />
            <View style={{ flex: 1 }}>
              <Text style={[s.errorTitle, { color: "#ef4444" }]}>Something went wrong</Text>
              <Text style={[s.errorBody,  { color: C.textMuted }]}>{errorMsg}</Text>
            </View>
          </View>
        )}

        {phase === "done" && pdfUri && (
          <View style={[s.doneCard, { borderColor: "rgba(16,185,129,0.4)", backgroundColor: "rgba(16,185,129,0.08)" }]}>
            <Feather name="check-circle" size={20} color="#10b981" />
            <Text style={[s.doneTitle, { color: "#10b981" }]}>Report ready!</Text>
            <Text style={[s.doneSub, { color: C.textMuted }]}>40-page Hinglish PDF generate ho gayi.</Text>
            <Pressable onPress={sharePdf} style={[s.doneBtn, { backgroundColor: "#10b981" }]}>
              <Feather name="share-2" size={15} color="#fff" />
              <Text style={s.doneBtnText}>Open / Share PDF</Text>
            </Pressable>
            <Pressable onPress={reset}>
              <Text style={[s.doneAgain, { color: C.textMuted }]}>Generate another report</Text>
            </Pressable>
          </View>
        )}

        {/* Generate button */}
        {phase !== "done" && (
          <Pressable
            disabled={!allReady || busy}
            onPress={generate}
            style={[s.ctaWrap, (!allReady || busy) && { opacity: 0.45 }]}
          >
            <LinearGradient
              colors={[ACCENT, "#a21caf"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={s.ctaBtn}
            >
              {busy
                ? <ActivityIndicator color="#fff" />
                : <Feather name="zap" size={16} color="#fff" />}
              <Text style={s.ctaText}>
                {busy ? "Processing…" : phase === "error" ? "Try Again" : "Generate My Report"}
              </Text>
            </LinearGradient>
          </Pressable>
        )}

        <Text style={[s.legalLine, { color: C.textDim }]}>
          Aapki photos sirf analysis ke liye use hoti hain · 24 ghante ke baad auto-delete · server pe encrypted
        </Text>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 10,
  },
  backBtn: { padding: 4 },
  headerTitle: { fontSize: 17, fontWeight: "700" },
  scroll: { paddingHorizontal: 16, gap: 12 },

  introCard: {
    borderRadius: 18, borderWidth: 1, padding: 18,
    overflow: "hidden", marginBottom: 4,
  },
  introEyebrow: { fontSize: 10, fontWeight: "800", letterSpacing: 2 },
  introTitle:   { fontSize: 18, fontWeight: "800", marginTop: 6 },
  introSub:     { fontSize: 13, lineHeight: 19, marginTop: 6 },

  slot: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 16, borderWidth: 1, padding: 12,
  },
  slotThumb: {
    width: 60, height: 60, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center", overflow: "hidden",
  },
  slotImg:   { width: "100%", height: "100%" },
  slotEmoji: { fontSize: 28 },
  slotLabel: { fontSize: 14, fontWeight: "700" },
  slotHint:  { fontSize: 11.5, marginTop: 2 },
  slotMeta:  { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 4 },
  slotMetaText: { fontSize: 10.5, fontWeight: "600" },

  sectionCap: {
    fontSize: 10, fontWeight: "700", letterSpacing: 2,
    marginTop: 14, marginBottom: 2, paddingLeft: 2,
  },
  optCard: { borderRadius: 14, borderWidth: 1, padding: 14 },
  optRow:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  optLabel:{ fontSize: 13, fontWeight: "600" },
  optInput:{
    borderWidth: 1, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 8,
    minWidth: 90, fontSize: 14, textAlign: "center", fontWeight: "600",
  },
  genderChip: {
    paddingHorizontal: 14, paddingVertical: 8,
    borderRadius: 999, borderWidth: 1,
  },
  genderText: { fontSize: 13, fontWeight: "700" },

  progressCard: {
    flexDirection: "row", alignItems: "center", gap: 12,
    borderRadius: 14, borderWidth: 1, padding: 14, marginTop: 6,
  },
  progressTitle: { fontSize: 13, fontWeight: "700" },
  progressSub:   { fontSize: 11, marginTop: 2 },

  errorCard: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    borderRadius: 14, borderWidth: 1, padding: 14, marginTop: 6,
  },
  errorTitle: { fontSize: 13, fontWeight: "700" },
  errorBody:  { fontSize: 11.5, marginTop: 2, lineHeight: 16 },

  doneCard: {
    borderRadius: 16, borderWidth: 1, padding: 16,
    alignItems: "center", gap: 6, marginTop: 6,
  },
  doneTitle: { fontSize: 15, fontWeight: "800", marginTop: 2 },
  doneSub:   { fontSize: 12, textAlign: "center" },
  doneBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 18, paddingVertical: 11,
    borderRadius: 12, marginTop: 8,
  },
  doneBtnText: { color: "#fff", fontWeight: "800", fontSize: 14 },
  doneAgain:   { fontSize: 12, marginTop: 10, textDecorationLine: "underline" },

  ctaWrap: { marginTop: 18, borderRadius: 16, overflow: "hidden" },
  ctaBtn: {
    flexDirection: "row", gap: 10, alignItems: "center", justifyContent: "center",
    paddingVertical: 15, borderRadius: 16,
  },
  ctaText: { color: "#fff", fontWeight: "800", fontSize: 15, letterSpacing: 0.3 },
  legalLine: { fontSize: 10.5, textAlign: "center", marginTop: 10, lineHeight: 15 },
});
