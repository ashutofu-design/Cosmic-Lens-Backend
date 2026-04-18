/**
 * RoomPhotoCapture — Phase 7 magnetometer-aware room photo upload.
 *
 * Flow per photo:
 *   1. User picks a room (from rooms they already listed).
 *   2. Live compass heading is shown (real magnetometer).
 *   3. User points phone at the wall they want to photograph and taps
 *      "Capture with Compass". We snapshot the current heading_deg and
 *      immediately launch the camera. The heading recorded is the
 *      pre-capture aim (most accurate ground truth available without a
 *      custom camera UI overlay).
 *   4. Photo is converted to data URL + heading is attached. Stored in
 *      parent's state as { room_type, image_data_url, heading_deg }.
 *
 * Branding: surfaces "Cosmic Vision Engine" — never mentions AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import { Magnetometer } from "expo-sensors";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
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
  const [heading, setHeading] = useState<number | null>(null);
  const [busy,    setBusy]    = useState(false);
  const [picked,  setPicked]  = useState<string | null>(null);

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

  // ── Pick room then capture ─────────────────────────────────────────────
  const onCapture = useCallback(async (roomKey: string) => {
    if (disabled || busy || !canAdd) return;
    Haptics.selectionAsync();
    setBusy(true);
    // Snapshot heading at this exact instant — last live magnetometer reading.
    const headingAtCapture = heading;

    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (perm.status !== "granted") {
        Alert.alert(
          "Camera permission needed",
          "Please allow camera access to capture a room photo for Cosmic Vision.",
        );
        return;
      }
      const r = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality:    0.7,
        base64:     true,
        exif:       false,
      });
      if (r.canceled || !r.assets?.[0]?.base64) return;
      const a    = r.assets[0];
      const mime = a.mimeType || "image/jpeg";
      const next: RoomPhoto = {
        room_type:      roomKey,
        image_data_url: `data:${mime};base64,${a.base64}`,
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
  }, [busy, canAdd, disabled, heading, onChange, photos]);

  const removePhoto = useCallback((idx: number) => {
    Haptics.selectionAsync();
    onChange(photos.filter((_, i) => i !== idx));
  }, [onChange, photos]);

  // ── UI ─────────────────────────────────────────────────────────────────
  return (
    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <View style={s.headerRow}>
        <Feather name="camera" size={18} color={C.accent} />
        <Text style={[s.title, { color: C.text }]}>Room Photos with Compass</Text>
      </View>
      <Text style={[s.sub, { color: C.textMuted }]}>
        Optional. Point your phone at the wall you want to scan, then tap a room
        below. Cosmic Vision will use the live compass heading for accurate
        direction analysis.
      </Text>

      {/* Live compass strip */}
      <View style={[s.compass, { borderColor: C.border, backgroundColor: C.bg }]}>
        <Feather name="compass" size={18} color={dir ? C.accent : C.textMuted} />
        {dir ? (
          <Text style={[s.compassText, { color: C.text }]}>
            {heading?.toFixed(0)}°  ·  Facing <Text style={{ color: C.accent, fontWeight: "800" }}>{dir.label}</Text> ({dir.code})
          </Text>
        ) : (
          <Text style={[s.compassText, { color: C.textMuted }]}>
            {Platform.OS === "web"
              ? "Compass not available on web preview — heading will be inferred from photo."
              : "Reading compass…"}
          </Text>
        )}
      </View>

      {/* Per-room capture buttons */}
      {rooms.length === 0 ? (
        <Text style={[s.empty, { color: C.textMuted }]}>
          Add at least one room above to capture a photo for it.
        </Text>
      ) : (
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 8, paddingVertical: 6 }}
        >
          {rooms.map((r) => {
            const isPicked = picked === r.key;
            return (
              <Pressable
                key={r.key}
                disabled={disabled || busy || !canAdd}
                onPress={() => { setPicked(r.key); onCapture(r.key); }}
                style={({ pressed }) => [
                  s.roomBtn,
                  {
                    borderColor: isPicked ? C.accent : C.border,
                    backgroundColor: isPicked ? C.accent + "15" : C.bg,
                    opacity: (disabled || busy || !canAdd) ? 0.5 : pressed ? 0.7 : 1,
                  },
                ]}
              >
                <Feather name="camera" size={13} color={C.accent} />
                <Text style={[s.roomBtnText, { color: C.text }]} numberOfLines={1}>
                  {r.label}
                </Text>
              </Pressable>
            );
          })}
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
                 borderRadius: 9, borderWidth: 1, maxWidth: 160 },
  roomBtnText: { fontSize: 12, fontWeight: "600" },
  photoRow:    { flexDirection: "row", alignItems: "center", gap: 10,
                 paddingHorizontal: 11, paddingVertical: 9,
                 borderWidth: 1, borderRadius: 9 },
  photoTitle:  { fontSize: 12, fontWeight: "700" },
  photoMeta:   { fontSize: 11, marginTop: 2 },
});
