/**
 * SmartScanCamera — single-tap live camera Smart Scan.
 *
 * Flow:
 *   1. User taps the big "Smart Scan" button.
 *   2. Camera permission is requested if needed; live camera modal opens.
 *   3. A live compass strip overlays the bottom of the camera.
 *   4. User taps the shutter; we capture base64 jpeg + magnetometer heading
 *      at the same instant and hand the result back via `onCapture`.
 *
 * Branding: surfaces "Cosmic Vision" — never mentions AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import { CameraType, CameraView, useCameraPermissions } from "expo-camera";
import * as Haptics from "expo-haptics";
import * as Location from "expo-location";
import { Magnetometer } from "expo-sensors";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";

export type SmartScanResult = {
  data_url:     string;
  base64:       string;
  heading_deg?: number;
};

type Props = {
  onCapture: (result: SmartScanResult) => void;
  loading?:  boolean;
  disabled?: boolean;
  label?:    string;
  hint?:     string;
};

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

export function SmartScanCamera({
  onCapture, loading, disabled, label, hint,
}: Props) {
  const C = useC();
  const cameraRef = useRef<CameraView | null>(null);
  const [perm, requestPerm] = useCameraPermissions();
  const [open,    setOpen]    = useState(false);
  const [busy,    setBusy]    = useState(false);
  const [heading, setHeading] = useState<number | null>(null);
  const [facing,  setFacing]  = useState<CameraType>("back");

  useEffect(() => {
    if (Platform.OS === "web") return;
    let locSub: Location.LocationSubscription | null = null;
    let magSub: { remove: () => void } | null = null;
    let cancelled = false;

    // Smoothing across the 0°/360° wrap-around. iOS already delivers a
    // de-jittered heading via Core Location, so use a soft alpha there.
    let smoothed: number | null = null;
    const ALPHA = Platform.OS === "ios" ? 0.5 : 0.25;
    const apply = (raw: number) => {
      let r = ((raw % 360) + 360) % 360;
      if (smoothed == null) {
        smoothed = r;
      } else {
        let diff = r - smoothed;
        if (diff > 180)  diff -= 360;
        if (diff < -180) diff += 360;
        smoothed = (smoothed + ALPHA * diff + 360) % 360;
      }
      setHeading(smoothed);
    };

    (async () => {
      // Preferred: Core Location / Android FusedLocation heading. This is
      // what the iOS Compass app uses — properly calibrated, with magnetic
      // declination corrected via GPS, so the value matches the system
      // compass instead of raw magnetometer math.
      try {
        const perm = await Location.requestForegroundPermissionsAsync();
        if (!cancelled && perm.granted) {
          locSub = await Location.watchHeadingAsync((h) => {
            // trueHeading uses GPS-corrected declination (matches iOS
            // Compass). Falls back to magHeading if GPS lock not yet
            // acquired (trueHeading reports -1 in that case).
            const t = typeof h.trueHeading === "number" ? h.trueHeading : -1;
            const m = typeof h.magHeading  === "number" ? h.magHeading  : -1;
            const pick = t >= 0 ? t : m;
            if (pick >= 0) apply(pick);
          });
          return; // success — don't fall back to raw magnetometer
        }
      } catch {
        // Permission denied or sensor unavailable — fall through.
      }

      // Fallback: raw magnetometer (no declination correction; will drift
      // from the system compass by up to ~10° depending on location).
      try {
        Magnetometer.setUpdateInterval(180);
        magSub = Magnetometer.addListener(({ x, y }) => {
          let raw = Math.atan2(-x, y) * (180 / Math.PI);
          if (raw < 0) raw += 360;
          apply(raw);
        });
      } catch { /* sensor unavailable */ }
    })();

    return () => {
      cancelled = true;
      try { locSub?.remove(); } catch { /* noop */ }
      try { magSub?.remove(); } catch { /* noop */ }
    };
  }, []);

  const dir = useMemo(
    () => (heading != null ? HEADING_TO_DIR(heading) : null),
    [heading],
  );

  const openCamera = useCallback(async () => {
    if (disabled || busy || loading) return;
    Haptics.selectionAsync();
    if (Platform.OS === "web") {
      Alert.alert(
        "Camera not available on web",
        "Please open Cosmic Lens on your phone via Expo Go to use the live Smart Scan camera.",
      );
      return;
    }
    if (!perm?.granted) {
      const r = await requestPerm();
      if (!r.granted) {
        Alert.alert(
          "Camera permission needed",
          "Please allow camera access in settings to use Smart Scan.",
        );
        return;
      }
    }
    setOpen(true);
  }, [busy, disabled, loading, perm, requestPerm]);

  const onShutter = useCallback(async () => {
    if (busy || !cameraRef.current) return;
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
      const result: SmartScanResult = {
        base64:   photo.base64,
        data_url: `data:image/jpeg;base64,${photo.base64}`,
        ...(typeof headingAtCapture === "number"
          ? { heading_deg: Math.round(headingAtCapture * 10) / 10 }
          : {}),
      };
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setOpen(false);
      onCapture(result);
    } catch (e: any) {
      Alert.alert("Capture failed", String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }, [busy, heading, onCapture]);

  const flipCamera = useCallback(() => {
    Haptics.selectionAsync();
    setFacing((f) => (f === "back" ? "front" : "back"));
  }, []);

  return (
    <>
      <Pressable
        onPress={openCamera}
        disabled={disabled || loading || busy}
        style={({ pressed }) => [
          s.bigBtn,
          {
            backgroundColor: C.accent,
            opacity: (disabled || loading) ? 0.6 : pressed ? 0.85 : 1,
          },
        ]}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <>
            <Feather name="camera" size={26} color="#fff" />
            <Text style={s.bigBtnText}>{label || "Smart Scan — Open Camera"}</Text>
          </>
        )}
      </Pressable>
      {hint ? (
        <Text style={[s.hint, { color: C.textMid }]}>{hint}</Text>
      ) : null}

      <Modal
        visible={open}
        animationType="slide"
        onRequestClose={() => !busy && setOpen(false)}
        statusBarTranslucent
      >
        <View style={s.camWrap}>
          {/* Top: live camera preview */}
          <View style={s.camTop}>
            {open ? (
              <CameraView
                ref={cameraRef}
                style={s.camView}
                facing={facing}
              />
            ) : null}

            <View style={s.topBar} pointerEvents="box-none">
              <View style={s.topBadge}>
                <Feather name="zap" size={13} color="#fff" />
                <Text style={s.topBadgeText}>Smart Scan</Text>
              </View>
              <Pressable
                onPress={() => !busy && setOpen(false)}
                hitSlop={12}
                style={s.closeBtn}
              >
                <Feather name="x" size={22} color="#fff" />
              </Pressable>
            </View>

            {/* Center crosshair to help user aim */}
            <View pointerEvents="none" style={s.crosshair}>
              <View style={s.crosshairBox} />
            </View>
          </View>

          {/* Bottom: compass + shutter (separate section, no overlap) */}
          <View style={s.bottomPanel}>
            <View style={s.camCompass}>
              <Feather name="compass" size={18} color={dir ? "#fbbf24" : "#9ca3af"} />
              {dir ? (
                <Text style={s.camCompassText}>
                  {heading?.toFixed(0)}°  ·  Facing{" "}
                  <Text style={{ color: "#fbbf24", fontWeight: "900" }}>{dir.label}</Text> ({dir.code})
                </Text>
              ) : (
                <Text style={[s.camCompassText, { color: "#9ca3af" }]}>
                  Reading compass…
                </Text>
              )}
            </View>

            <Text style={s.camHint}>
              Aim at your floor plan or the room, then tap the shutter.
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
                {busy ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <View style={s.shutterInner} />
                )}
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
    </>
  );
}

const s = StyleSheet.create({
  bigBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 12, paddingVertical: 22, borderRadius: 16,
    shadowOpacity: 0.25, shadowRadius: 12, shadowOffset: { width: 0, height: 6 },
    elevation: 5,
  },
  bigBtnText: { color: "#fff", fontSize: 17, fontWeight: "800", letterSpacing: 0.3 },
  hint:       { fontSize: 12, lineHeight: 17, textAlign: "center", marginTop: 10 },

  camWrap:        { flex: 1, backgroundColor: "#000", flexDirection: "column" },
  camTop:         { flex: 1, position: "relative", backgroundColor: "#000",
                    overflow: "hidden" },
  camView:        { flex: 1, width: "100%", backgroundColor: "#000" },
  topBar:         { position: "absolute", top: 0, left: 0, right: 0,
                    paddingTop: 50, paddingHorizontal: 16, paddingBottom: 10,
                    flexDirection: "row", justifyContent: "space-between",
                    alignItems: "center", zIndex: 10 },
  topBadge:       { flexDirection: "row", alignItems: "center", gap: 6,
                    paddingHorizontal: 12, paddingVertical: 7,
                    backgroundColor: "rgba(0,0,0,0.55)", borderRadius: 18 },
  topBadgeText:   { color: "#fff", fontSize: 13, fontWeight: "700" },
  closeBtn:       { width: 38, height: 38, borderRadius: 19,
                    backgroundColor: "rgba(0,0,0,0.55)",
                    alignItems: "center", justifyContent: "center" },
  crosshair:      { position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
                    alignItems: "center", justifyContent: "center" },
  crosshairBox:   { width: 110, height: 110, borderWidth: 1.5,
                    borderColor: "rgba(255,255,255,0.7)", borderRadius: 8 },
  bottomPanel:    { backgroundColor: "#0b1220",
                    paddingHorizontal: 20, paddingTop: 18, paddingBottom: 32 },
  camCompass:     { flexDirection: "row", alignItems: "center", gap: 12,
                    paddingHorizontal: 16, paddingVertical: 14,
                    backgroundColor: "#111827", borderRadius: 12,
                    borderWidth: 1, borderColor: "#374151" },
  camCompassText: { color: "#fff", fontSize: 14, fontWeight: "700" },
  camHint:        { color: "#9ca3af", fontSize: 12, textAlign: "center",
                    marginTop: 12, marginBottom: 4 },
  shutterRow:     { flexDirection: "row", alignItems: "center",
                    justifyContent: "space-between", paddingTop: 6 },
  shutterOuter:   { width: 84, height: 84, borderRadius: 42,
                    borderWidth: 4, borderColor: "#fff",
                    alignItems: "center", justifyContent: "center",
                    backgroundColor: "rgba(255,255,255,0.12)" },
  shutterInner:   { width: 64, height: 64, borderRadius: 32,
                    backgroundColor: "#fff" },
  flipBtn:        { width: 46, height: 46, borderRadius: 23,
                    backgroundColor: "rgba(255,255,255,0.18)",
                    alignItems: "center", justifyContent: "center" },
});
