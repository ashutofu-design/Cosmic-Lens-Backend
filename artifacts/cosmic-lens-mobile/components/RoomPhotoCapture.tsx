/**
 * RoomPhotoCapture — Phase 7 magnetometer-aware room photo capture.
 *
 * Flow per photo:
 *   1. User taps a room (from rooms they already listed).
 *   2. A live in-app camera modal opens with a compass overlay below the preview.
 *   3. User aims the phone at the wall to scan and taps the big shutter button.
 *      The current magnetometer heading is snapshotted at the same instant.
 *   4. Photo is converted to a data URL and stored in the parent's state as
 *      { room_type, image_data_url, heading_deg }.
 *
 * Branding: surfaces "Cosmic Vision" — never mentions AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import { CameraType, CameraView, useCameraPermissions } from "expo-camera";
import * as Haptics from "expo-haptics";
import { Magnetometer } from "expo-sensors";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Dimensions,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";

// ── Public types ────────────────────────────────────────────────────────────
export type RoomPhoto = {
  room_type:      string;
  image_data_url: string;
  heading_deg?:   number;        // omitted on web / when sensor unavailable
};

export type RoomChoice = { key: string; label: string };

type Props = {
  rooms:    RoomChoice[];                      // rooms the user already listed
  photos:   RoomPhoto[];
  onChange: (next: RoomPhoto[]) => void;
  disabled?: boolean;
  maxPhotos?: number;                          // default 6, hard cap server-side
};

// ── Helpers ─────────────────────────────────────────────────────────────────
const HEADING_TO_DIR = (h: number): { code: string; label: string } => {
  const a = ((h % 360) + 360) % 360;
  const buckets = [
    { code: "N",  label: "North",      lo: 337.5, hi: 22.5  },
    { code: "NE", label: "North-East", lo: 22.5,  hi: 67.5  },
    { code: "E",  label: "East",       lo: 67.5,  hi: 112.5 },
    { code: "SE", label: "South-East", lo: 112.5, hi: 157.5 },
    { code: "S",  label: "South",      lo: 157.5, hi: 202.5 },
    { code: "SW", label: "South-West", lo: 202.5, hi: 247.5 },
    { code: "W",  label: "West",       lo: 247.5, hi: 292.5 },
    { code: "NW", label: "North-West", lo: 292.5, hi: 337.5 },
  ];
  for (const b of buckets) {
    if (b.code === "N") {
      if (a >= b.lo || a < b.hi) return { code: b.code, label: b.label };
    } else if (a >= b.lo && a < b.hi) {
      return { code: b.code, label: b.label };
    }
  }
  return { code: "N", label: "North" };
};

// ── Component ───────────────────────────────────────────────────────────────
export function RoomPhotoCapture({
  rooms, photos, onChange, disabled, maxPhotos = 6,
}: Props) {
  const C = useC();
  const cameraRef = useRef<CameraView | null>(null);
  const [perm, requestPerm] = useCameraPermissions();
  const [heading, setHeading] = useState<number | null>(null);
  const [busy,    setBusy]    = useState(false);
  const [picked,  setPicked]  = useState<string | null>(null);   // room being captured
  const [facing,  setFacing]  = useState<CameraType>("back");

  // ── Magnetometer subscription (native only) ────────────────────────────
  useEffect(() => {
    if (Platform.OS === "web") return;
    let sub: { remove: () => void } | null = null;
    try {
      Magnetometer.setUpdateInterval(120);
      sub = Magnetometer.addListener(({ x, y }) => {
        let angle = Math.atan2(-x, y) * (180 / Math.PI);
        if (angle < 0) angle += 360;
        setHeading(angle);
      });
    } catch {
      // Sensor not available (e.g. some emulators) — silently skip.
    }
    return () => { try { sub?.remove(); } catch { /* noop */ } };
  }, []);

  const dir = useMemo(
    () => (heading != null ? HEADING_TO_DIR(heading) : null),
    [heading],
  );

  const canAdd = photos.length < maxPhotos;

  // ── Open camera modal for a given room ─────────────────────────────────
  const openCameraFor = useCallback(async (roomKey: string) => {
    if (disabled || busy || !canAdd) return;
    Haptics.selectionAsync();
    if (Platform.OS === "web") {
      Alert.alert("Camera not available", "Please open this on your phone to capture room photos.");
      return;
    }
    if (!perm?.granted) {
      const r = await requestPerm();
      if (!r.granted) {
        Alert.alert(
          "Camera permission needed",
          "Please allow camera access in settings to capture room photos with the compass.",
        );
        return;
      }
    }
    setPicked(roomKey);
  }, [busy, canAdd, disabled, perm, requestPerm]);

  // ── Capture photo (called from inside the modal) ───────────────────────
  const onShutter = useCallback(async () => {
    if (busy || !cameraRef.current || !picked) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setBusy(true);
    const headingAtCapture = heading;
    try {
      const photo = await cameraRef.current.takePictureAsync({
        base64: true,
        quality: 0.7,
        skipProcessing: true,
        exif: false,
      });
      if (!photo?.base64) {
        Alert.alert("Capture failed", "Photo could not be saved. Please try again.");
        return;
      }
      const next: RoomPhoto = {
        room_type:      picked,
        image_data_url: `data:image/jpeg;base64,${photo.base64}`,
        ...(typeof headingAtCapture === "number"
          ? { heading_deg: Math.round(headingAtCapture * 10) / 10 }
          : {}),
      };
      onChange([...photos, next]);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setPicked(null);
    } catch (e: any) {
      Alert.alert("Capture failed", String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }, [busy, heading, onChange, photos, picked]);

  const closeCamera = useCallback(() => {
    Haptics.selectionAsync();
    setPicked(null);
  }, []);

  const removePhoto = useCallback((idx: number) => {
    Haptics.selectionAsync();
    onChange(photos.filter((_, i) => i !== idx));
  }, [onChange, photos]);

  const flipCamera = useCallback(() => {
    Haptics.selectionAsync();
    setFacing((f) => (f === "back" ? "front" : "back"));
  }, []);

  // ── UI ─────────────────────────────────────────────────────────────────
  const pickedLabel = useMemo(
    () => rooms.find((r) => r.key === picked)?.label || picked || "",
    [picked, rooms],
  );
  const screen = Dimensions.get("window");
  const camHeight = Math.round(screen.height * 0.6);

  return (
    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <View style={s.headerRow}>
        <Feather name="camera" size={18} color={C.accent} />
        <Text style={[s.title, { color: C.text }]}>Room Photos with Compass</Text>
      </View>
      <Text style={[s.sub, { color: C.textMuted }]}>
        Optional. Tap a room below — a live camera with compass will open. Aim
        at the wall you want Cosmic Vision to analyse, then tap the shutter.
      </Text>

      {/* Live compass strip (also visible outside camera) */}
      <View style={[s.compass, { borderColor: C.border, backgroundColor: C.bg }]}>
        <Feather name="compass" size={18} color={dir ? C.accent : C.textMuted} />
        {dir ? (
          <Text style={[s.compassText, { color: C.text }]}>
            {heading?.toFixed(0)}°  ·  Facing <Text style={{ color: C.accent, fontWeight: "800" }}>{dir.label}</Text> ({dir.code})
          </Text>
        ) : (
          <Text style={[s.compassText, { color: C.textMuted }]}>
            {Platform.OS === "web"
              ? "Compass not available on web preview — open on your phone."
              : "Reading compass…"}
          </Text>
        )}
      </View>

      {/* Per-room capture buttons */}
      {rooms.length === 0 ? (
        <Text style={[s.empty, { color: C.textMuted }]}>
          Add at least one room below to capture a photo for it.
        </Text>
      ) : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 8, paddingVertical: 6 }}
        >
          {rooms.map((r) => (
            <Pressable
              key={r.key}
              disabled={disabled || busy || !canAdd}
              onPress={() => openCameraFor(r.key)}
              accessibilityLabel={`Capture photo for ${r.label}`}
              style={({ pressed }) => [
                s.roomBtn,
                {
                  borderColor: C.border,
                  backgroundColor: C.bg,
                  opacity: (disabled || busy || !canAdd) ? 0.5 : pressed ? 0.7 : 1,
                },
              ]}
            >
              <Feather name="camera" size={13} color={C.accent} />
              <Text style={[s.roomBtnText, { color: C.text }]} numberOfLines={1}>
                {r.label}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
      )}

      {!canAdd ? (
        <Text style={[s.empty, { color: C.textMuted, marginTop: 6 }]}>
          Maximum {maxPhotos} photos reached.
        </Text>
      ) : null}

      {/* Captured list */}
      {photos.length > 0 ? (
        <View style={{ marginTop: 10, gap: 6 }}>
          {photos.map((p, i) => {
            const dirLbl = typeof p.heading_deg === "number"
              ? HEADING_TO_DIR(p.heading_deg)
              : null;
            return (
              <View
                key={`${p.room_type}-${i}`}
                style={[s.photoRow, { borderColor: C.border, backgroundColor: C.bg }]}
              >
                <Feather name="image" size={14} color={C.accent} />
                <View style={{ flex: 1 }}>
                  <Text style={[s.photoTitle, { color: C.text }]} numberOfLines={1}>
                    {rooms.find((rr) => rr.key === p.room_type)?.label || p.room_type}
                  </Text>
                  <Text style={[s.photoMeta, { color: C.textMuted }]}>
                    {dirLbl
                      ? `Compass: ${p.heading_deg?.toFixed(0)}° · ${dirLbl.label} (${dirLbl.code})`
                      : "Compass: not recorded — Cosmic Vision will infer"}
                  </Text>
                </View>
                <Pressable onPress={() => removePhoto(i)} hitSlop={8}>
                  <Feather name="x" size={16} color={C.textMuted} />
                </Pressable>
              </View>
            );
          })}
        </View>
      ) : null}

      {/* ── Live camera modal ────────────────────────────────────────── */}
      <Modal
        visible={picked !== null}
        animationType="slide"
        onRequestClose={closeCamera}
        statusBarTranslucent
      >
        <View style={s.camWrap}>
          {picked !== null ? (
            <CameraView
              ref={cameraRef}
              style={[s.camView, { height: camHeight }]}
              facing={facing}
            />
          ) : null}

          {/* Top bar: room name + close */}
          <View style={s.topBar} pointerEvents="box-none">
            <View style={s.topBadge}>
              <Feather name="home" size={13} color="#fff" />
              <Text style={s.topBadgeText} numberOfLines={1}>{pickedLabel}</Text>
            </View>
            <Pressable onPress={closeCamera} hitSlop={12} style={s.closeBtn}>
              <Feather name="x" size={22} color="#fff" />
            </Pressable>
          </View>

          {/* Bottom controls: compass + shutter + flip */}
          <View style={s.bottomPanel}>
            <View style={s.camCompass}>
              <Feather name="compass" size={18} color={dir ? "#fbbf24" : "#9ca3af"} />
              {dir ? (
                <Text style={s.camCompassText}>
                  {heading?.toFixed(0)}°  ·  Facing <Text style={{ color: "#fbbf24", fontWeight: "900" }}>{dir.label}</Text> ({dir.code})
                </Text>
              ) : (
                <Text style={[s.camCompassText, { color: "#9ca3af" }]}>
                  Reading compass…
                </Text>
              )}
            </View>

            <Text style={s.camHint}>
              Aim at the wall you want to analyse, then tap the shutter.
            </Text>

            <View style={s.shutterRow}>
              <View style={{ width: 56 }} />
              <Pressable
                onPress={onShutter}
                disabled={busy}
                accessibilityLabel="Capture photo"
                style={({ pressed }) => [
                  s.shutterOuter,
                  { opacity: busy ? 0.5 : pressed ? 0.7 : 1 },
                ]}
              >
                <View style={s.shutterInner} />
              </Pressable>
              <Pressable
                onPress={flipCamera}
                disabled={busy}
                hitSlop={10}
                style={({ pressed }) => [
                  s.flipBtn,
                  { opacity: busy ? 0.5 : pressed ? 0.7 : 1 },
                ]}
              >
                <Feather name="refresh-cw" size={20} color="#fff" />
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  card:        { borderRadius: 12, borderWidth: 1, padding: 14, marginBottom: 14 },
  headerRow:   { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 },
  title:       { fontSize: 15, fontWeight: "700" },
  sub:         { fontSize: 12, lineHeight: 17, marginBottom: 10 },
  compass:     { flexDirection: "row", alignItems: "center", gap: 10,
                 paddingHorizontal: 12, paddingVertical: 9,
                 borderWidth: 1, borderRadius: 9, marginBottom: 8 },
  compassText: { fontSize: 12, fontWeight: "600" },
  empty:       { fontSize: 11, fontStyle: "italic", paddingVertical: 6 },
  roomBtn:     { flexDirection: "row", alignItems: "center", gap: 6,
                 paddingHorizontal: 12, paddingVertical: 9,
                 borderRadius: 9, borderWidth: 1, maxWidth: 200 },
  roomBtnText: { fontSize: 12, fontWeight: "600" },
  photoRow:    { flexDirection: "row", alignItems: "center", gap: 10,
                 paddingHorizontal: 11, paddingVertical: 9,
                 borderWidth: 1, borderRadius: 9 },
  photoTitle:  { fontSize: 12, fontWeight: "700" },
  photoMeta:   { fontSize: 11, marginTop: 2 },

  // ── Camera modal ──
  camWrap:        { flex: 1, backgroundColor: "#000" },
  camView:        { width: "100%", backgroundColor: "#000" },
  topBar:         { position: "absolute", top: 0, left: 0, right: 0,
                    paddingTop: 50, paddingHorizontal: 16, paddingBottom: 10,
                    flexDirection: "row", justifyContent: "space-between",
                    alignItems: "center", zIndex: 10 },
  topBadge:       { flexDirection: "row", alignItems: "center", gap: 6,
                    paddingHorizontal: 12, paddingVertical: 7,
                    backgroundColor: "rgba(0,0,0,0.55)", borderRadius: 18,
                    maxWidth: "70%" },
  topBadgeText:   { color: "#fff", fontSize: 13, fontWeight: "700" },
  closeBtn:       { width: 38, height: 38, borderRadius: 19,
                    backgroundColor: "rgba(0,0,0,0.55)",
                    alignItems: "center", justifyContent: "center" },
  bottomPanel:    { flex: 1, backgroundColor: "#0b1220",
                    paddingHorizontal: 20, paddingTop: 18, paddingBottom: 28,
                    justifyContent: "space-between" },
  camCompass:     { flexDirection: "row", alignItems: "center", gap: 12,
                    paddingHorizontal: 16, paddingVertical: 14,
                    backgroundColor: "#111827", borderRadius: 12,
                    borderWidth: 1, borderColor: "#374151" },
  camCompassText: { color: "#fff", fontSize: 14, fontWeight: "700" },
  camHint:        { color: "#9ca3af", fontSize: 12, textAlign: "center",
                    marginTop: 12, marginBottom: 4 },
  shutterRow:     { flexDirection: "row", alignItems: "center",
                    justifyContent: "space-between", paddingTop: 6 },
  shutterOuter:   { width: 78, height: 78, borderRadius: 39,
                    borderWidth: 4, borderColor: "#fff",
                    alignItems: "center", justifyContent: "center",
                    backgroundColor: "rgba(255,255,255,0.12)" },
  shutterInner:   { width: 60, height: 60, borderRadius: 30,
                    backgroundColor: "#fff" },
  flipBtn:        { width: 46, height: 46, borderRadius: 23,
                    backgroundColor: "rgba(255,255,255,0.18)",
                    alignItems: "center", justifyContent: "center" },
});
