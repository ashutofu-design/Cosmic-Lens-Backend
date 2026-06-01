/**
 * Web — live camera unavailable; show upload path only (no expo-camera hooks).
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useCallback } from "react";
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";

export type SmartScanResult = {
  data_url: string;
  base64: string;
  heading_deg?: number;
};

type Props = {
  onCapture: (result: SmartScanResult) => void;
  loading?: boolean;
  disabled?: boolean;
  label?: string;
  hint?: string;
  aside?: React.ReactNode;
};

export function SmartScanCamera({
  loading,
  disabled,
  label,
  hint,
  aside,
}: Props) {
  const C = useC();

  const openCamera = useCallback(() => {
    if (disabled || loading) return;
    Haptics.selectionAsync().catch(() => {});
    Alert.alert(
      "Camera not available on web",
      "Use Upload Photo on the right, or open Cosmic Lens on your phone (Expo Go) for live Smart Scan.",
    );
  }, [disabled, loading]);

  return (
    <>
      <View style={s.actionWrap}>
        <View style={s.actionRow}>
          <View style={aside ? s.pairSlot : s.pairSlotFull}>
            <Pressable
              onPress={openCamera}
              disabled={disabled || loading}
              style={({ pressed }) => [
                aside ? s.scanPairBtn : s.bigBtn,
                {
                  backgroundColor: C.accent,
                  opacity: disabled || loading ? 0.6 : pressed ? 0.85 : 1,
                },
              ]}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : aside ? (
                <>
                  <Feather name="camera" size={26} color="#fff" />
                  <Text style={s.bigBtnTextHalf} numberOfLines={2}>
                    {label || "Open Camera"}
                  </Text>
                </>
              ) : (
                <>
                  <Feather name="camera" size={26} color="#fff" />
                  <Text style={s.bigBtnText}>{label || "Smart Scan — Open Camera"}</Text>
                </>
              )}
            </Pressable>
          </View>
          {aside ? (
            <>
              <Text style={[s.orMid, { color: C.textMid }]}>or</Text>
              <View style={s.pairSlot}>{aside}</View>
            </>
          ) : null}
        </View>
      </View>
      {hint ? <Text style={[s.hint, { color: C.textMid }]}>{hint}</Text> : null}
    </>
  );
}

const s = StyleSheet.create({
  actionWrap: { width: "100%", alignItems: "center", justifyContent: "center" },
  actionRow: {
    flexDirection: "row",
    alignItems: "stretch",
    justifyContent: "center",
    gap: 10,
    width: "100%",
    maxWidth: 360,
    alignSelf: "center",
  },
  orMid: {
    fontSize: 13,
    fontWeight: "800",
    textTransform: "lowercase",
    paddingHorizontal: 4,
    alignSelf: "center",
  },
  pairSlot: { flex: 1, minWidth: 0 },
  pairSlotFull: { flex: 1, width: "100%" },
  scanPairBtn: {
    width: "100%",
    minHeight: 108,
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 10,
    borderRadius: 16,
  },
  bigBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingVertical: 22,
    paddingHorizontal: 14,
    borderRadius: 16,
  },
  bigBtnText: {
    color: "#fff",
    fontSize: 17,
    fontWeight: "800",
    letterSpacing: 0.3,
    textAlign: "center",
  },
  bigBtnTextHalf: {
    color: "#fff",
    fontSize: 13,
    fontWeight: "800",
    textAlign: "center",
    lineHeight: 17,
    width: "100%",
  },
  hint: { fontSize: 12, lineHeight: 17, textAlign: "center", marginTop: 10 },
});
