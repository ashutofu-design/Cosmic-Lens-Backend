/**
 * SmartScanCamera — in-app camera preview with live compass below the view.
 * Falls back to the system camera if the preview cannot start.
 */
import { Feather } from "@expo/vector-icons";
import { CameraView, useCameraPermissions } from "expo-camera";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import * as Location from "expo-location";
import { Magnetometer } from "expo-sensors";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Linking,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

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
  disabledTitle?: string;
  disabledMessage?: string;
  label?:    string;
  hint?:     string;
  compact?:  boolean;
};

function headingToDir(h: number): { code: string; label: string } {
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
}

function useLiveHeading(enabled: boolean) {
  const headingRef = useRef<number | null>(null);
  const [heading, setHeading] = useState<number | null>(null);
  const [hasFix, setHasFix] = useState(false);

  useEffect(() => {
    if (!enabled || Platform.OS === "web") {
      setHeading(null);
      setHasFix(false);
      headingRef.current = null;
      return;
    }

    let locSub: Location.LocationSubscription | null = null;
    let magSub: { remove: () => void } | null = null;
    let cancelled = false;
    let smoothed: number | null = null;
    const ALPHA = Platform.OS === "ios" ? 0.5 : 0.28;

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
      headingRef.current = smoothed;
      setHeading(smoothed);
      setHasFix(true);
    };

    (async () => {
      try {
        const perm = await Location.requestForegroundPermissionsAsync();
        if (!cancelled && perm.granted) {
          locSub = await Location.watchHeadingAsync((h) => {
            const t = typeof h.trueHeading === "number" ? h.trueHeading : -1;
            const m = typeof h.magHeading  === "number" ? h.magHeading  : -1;
            const pick = t >= 0 ? t : m;
            if (pick >= 0) apply(pick);
          });
          return;
        }
      } catch { /* fall through */ }

      try {
        Magnetometer.setUpdateInterval(120);
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
  }, [enabled]);

  return { heading, headingRef, hasFix };
}

function CompassPanel({
  heading,
  hasFix,
  dark,
}: {
  heading: number | null;
  hasFix: boolean;
  dark?: boolean;
}) {
  const C = useC();
  const dir = heading != null ? headingToDir(heading) : null;
  const fg = dark ? "#fff" : C.text;
  const muted = dark ? "#9ca3af" : C.textMuted;
  const accent = dark ? "#fbbf24" : C.accent;

  return (
    <View style={[
      s.compassPanel,
      dark
        ? { backgroundColor: "#111827", borderColor: "#374151" }
        : { backgroundColor: C.bgCard, borderColor: C.border },
    ]}>
      <Feather name="compass" size={22} color={dir ? accent : muted} />
      <View style={{ flex: 1 }}>
        {dir ? (
          <Text style={[s.compassDeg, { color: fg }]}>
            {heading?.toFixed(0)}°{"  ·  "}
            Facing{" "}
            <Text style={{ color: accent, fontWeight: "900" }}>
              {dir.label}
            </Text>{" "}
            ({dir.code})
          </Text>
        ) : (
          <Text style={[s.compassDeg, { color: muted }]}>
            {Platform.OS === "web"
              ? "Compass not available on web — use your phone."
              : hasFix
                ? "Reading compass…"
                : "Calibrating compass… move phone in a figure-8"}
          </Text>
        )}
        <Text style={[s.compassSub, { color: muted }]}>
          Stand inside the room and point the phone at the wall you want analysed.
        </Text>
      </View>
    </View>
  );
}

export function SmartScanCompass({ disabled }: { disabled?: boolean }) {
  const { heading, hasFix } = useLiveHeading(!disabled);
  if (disabled) return null;
  return <CompassPanel heading={heading} hasFix={hasFix} />;
}

export function SmartScanCamera({
  onCapture,
  loading,
  disabled,
  disabledTitle,
  disabledMessage,
  label,
  hint,
  compact,
}: Props) {
  const C = useC();
  const insets = useSafeAreaInsets();
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [open, setOpen] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [facing, setFacing] = useState<"back" | "front">("back");
  const [busy, setBusy] = useState(false);
  const { heading, headingRef, hasFix } = useLiveHeading(open && !disabled);

  const finishCapture = useCallback((base64: string) => {
    const headingAtCapture = headingRef.current ?? heading;
    const result: SmartScanResult = {
      base64,
      data_url: `data:image/jpeg;base64,${base64}`,
      ...(typeof headingAtCapture === "number"
        ? { heading_deg: Math.round(headingAtCapture * 10) / 10 }
        : {}),
    };
    try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch { /* noop */ }
    onCapture(result);
  }, [heading, headingRef, onCapture]);

  const captureWithSystemCamera = useCallback(async () => {
    setBusy(true);
    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          "Camera permission needed",
          "Please allow camera access in Settings to use Smart Scan.",
          [
            { text: "Cancel", style: "cancel" },
            { text: "Open Settings", onPress: () => { void Linking.openSettings(); } },
          ],
        );
        return;
      }
      const res = await ImagePicker.launchCameraAsync({
        quality: 0.7,
        base64: true,
        allowsEditing: false,
      });
      if (res.canceled || !res.assets?.[0]?.base64) return;
      finishCapture(res.assets[0].base64);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert("Camera error", msg || "Could not open camera. Please try again.");
    } finally {
      setBusy(false);
    }
  }, [finishCapture]);

  const closeModal = useCallback(() => {
    setOpen(false);
    setCameraReady(false);
  }, []);

  const openCamera = useCallback(async () => {
    if (loading || busy) return;

    if (disabled) {
      Alert.alert(
        disabledTitle || "Select a room first",
        disabledMessage || "Please pick which room you are scanning, then tap Smart Scan again.",
      );
      return;
    }

    try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); } catch { /* noop */ }

    if (Platform.OS === "web") {
      void captureWithSystemCamera();
      return;
    }

    if (!permission?.granted) {
      const res = await requestPermission();
      if (!res.granted) {
        Alert.alert(
          "Camera permission needed",
          "Please allow camera access in Settings to use Smart Scan.",
          [
            { text: "Cancel", style: "cancel" },
            { text: "Open Settings", onPress: () => { void Linking.openSettings(); } },
          ],
        );
        return;
      }
    }

    setCameraReady(false);
    setOpen(true);
  }, [
    busy, captureWithSystemCamera, disabled, disabledMessage, disabledTitle,
    loading, permission?.granted, requestPermission,
  ]);

  const onShutter = useCallback(async () => {
    if (busy || !cameraReady || !cameraRef.current) return;
    try { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy); } catch { /* noop */ }
    setBusy(true);
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
      closeModal();
      finishCapture(photo.base64);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert("Capture failed", msg || "Please try again.");
    } finally {
      setBusy(false);
    }
  }, [busy, cameraReady, closeModal, finishCapture]);

  const onPreviewError = useCallback((message?: string) => {
    closeModal();
    Alert.alert(
      "Camera preview unavailable",
      message || "We will open your phone's built-in camera instead. Compass direction is still recorded.",
      [{ text: "OK", onPress: () => { void captureWithSystemCamera(); } }],
    );
  }, [captureWithSystemCamera, closeModal]);

  const flipCamera = useCallback(() => {
    try { Haptics.selectionAsync(); } catch { /* noop */ }
    setFacing((f) => (f === "back" ? "front" : "back"));
    setCameraReady(false);
  }, []);

  const btnOpacity = useMemo(
    () => (loading || busy ? 0.7 : disabled ? 0.55 : 1),
    [busy, disabled, loading],
  );

  return (
    <>
      <Pressable
        onPress={() => { void openCamera(); }}
        disabled={loading || busy}
        style={({ pressed }) => [
          s.bigBtn,
          compact && s.bigBtnCompact,
          {
            backgroundColor: C.accent,
            opacity: btnOpacity * (pressed ? 0.85 : 1),
          },
        ]}
      >
        {loading || busy ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <>
            <Feather name="camera" size={compact ? 22 : 26} color="#fff" />
            <Text style={[s.bigBtnText, compact && s.bigBtnTextCompact]}>
              {label || "Smart Scan — Open Camera"}
            </Text>
          </>
        )}
      </Pressable>

      {hint && !compact ? (
        <Text style={[s.hint, { color: C.textMid }]}>{hint}</Text>
      ) : null}

      <Modal
        visible={open}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={closeModal}
        statusBarTranslucent
      >
        <View style={s.modalRoot}>
          <View style={[s.previewWrap, { paddingTop: insets.top }]}>
            <CameraView
              ref={cameraRef}
              style={s.preview}
              facing={facing}
              mode="picture"
              active={open}
              onCameraReady={() => setCameraReady(true)}
              onMountError={({ message }) => onPreviewError(message)}
            />
            {!cameraReady && (
              <View style={s.previewLoading}>
                <ActivityIndicator color="#fff" size="large" />
                <Text style={s.previewLoadingText}>Starting camera…</Text>
              </View>
            )}
            <Pressable onPress={closeModal} hitSlop={12} style={[s.closeBtn, { top: insets.top + 10 }]}>
              <Feather name="x" size={22} color="#fff" />
            </Pressable>
          </View>

          <View style={s.bottomPanel}>
            <CompassPanel heading={heading} hasFix={hasFix} dark />

            <Text style={s.camHint}>
              Compass locks direction at shutter — keep the phone steady when you capture.
            </Text>

            <View style={s.shutterRow}>
              <View style={{ width: 46 }} />
              <Pressable
                onPress={() => { void onShutter(); }}
                disabled={busy || !cameraReady}
                accessibilityLabel="Capture photo"
                style={({ pressed }) => [
                  s.shutterOuter,
                  { opacity: busy || !cameraReady ? 0.45 : pressed ? 0.75 : 1 },
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
                  { opacity: busy ? 0.45 : pressed ? 0.75 : 1 },
                ]}
              >
                <Feather name="refresh-cw" size={20} color="#fff" />
              </Pressable>
            </View>

            <Pressable
              onPress={() => { closeModal(); void captureWithSystemCamera(); }}
              disabled={busy}
              style={{ paddingVertical: 10, alignItems: "center" }}
            >
              <Text style={s.fallbackText}>Use system camera instead</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </>
  );
}

const s = StyleSheet.create({
  bigBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingVertical: 22,
    borderRadius: 16,
    shadowOpacity: 0.25,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 5,
  },
  bigBtnText: { color: "#fff", fontSize: 17, fontWeight: "800", letterSpacing: 0.3 },
  bigBtnCompact: {
    flex: 1,
    flexDirection: "column",
    paddingVertical: 18,
    paddingHorizontal: 10,
    minHeight: 96,
  },
  bigBtnTextCompact: { fontSize: 13, textAlign: "center", letterSpacing: 0.1 },
  hint:       { fontSize: 12, lineHeight: 17, textAlign: "center", marginTop: 10 },

  compassPanel: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 4,
  },
  compassDeg: { fontSize: 15, fontWeight: "700", lineHeight: 21 },
  compassSub: { fontSize: 11, lineHeight: 16, marginTop: 4 },

  modalRoot:    { flex: 1, backgroundColor: "#000" },
  previewWrap:  { flex: 1, backgroundColor: "#000", position: "relative" },
  preview:      { flex: 1, width: "100%" },
  previewLoading: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(0,0,0,0.45)",
    gap: 10,
  },
  previewLoadingText: { color: "#fff", fontSize: 14, fontWeight: "600" },
  closeBtn: {
    position: "absolute",
    right: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "rgba(0,0,0,0.55)",
    alignItems: "center",
    justifyContent: "center",
  },

  bottomPanel: {
    backgroundColor: "#0b1220",
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 24,
    gap: 10,
  },
  camHint: {
    color: "#9ca3af",
    fontSize: 11,
    textAlign: "center",
    lineHeight: 16,
  },
  shutterRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 4,
  },
  shutterOuter: {
    width: 78,
    height: 78,
    borderRadius: 39,
    borderWidth: 4,
    borderColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.12)",
  },
  shutterInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#fff",
  },
  flipBtn: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: "rgba(255,255,255,0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  fallbackText: { color: "#94a3b8", fontSize: 12, fontWeight: "600" },
});
