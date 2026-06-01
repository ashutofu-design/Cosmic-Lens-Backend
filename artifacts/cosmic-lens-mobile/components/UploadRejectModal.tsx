/**
 * Centered modal when an upload is rejected (wrong room photo, invalid floor plan, etc.).
 */
import { Feather } from "@expo/vector-icons";
import React from "react";
import {
  Image,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";

export type UploadRejectModalProps = {
  visible: boolean;
  onClose: () => void;
  title: string;
  message: string;
  primaryLabel: string;
  onPrimary: () => void;
  previewUrl?: string;
  icon?: keyof typeof Feather.glyphMap;
};

export function UploadRejectModal({
  visible,
  onClose,
  title,
  message,
  primaryLabel,
  onPrimary,
  previewUrl,
  icon = "home",
}: UploadRejectModalProps) {
  const C = useC();

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={s.rejectBackdrop}>
        <Pressable style={StyleSheet.absoluteFillObject} onPress={onClose} />
        <View style={[s.rejectCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={[s.rejectIconWrap, { backgroundColor: "rgba(239,68,68,0.12)" }]}>
            <Feather name={icon} size={28} color="#ef4444" />
          </View>
          <Text style={[s.rejectTitle, { color: C.text }]}>{title}</Text>
          <Text style={[s.rejectBody, { color: C.textMid }]}>{message}</Text>
          {previewUrl ? (
            <Image source={{ uri: previewUrl }} style={s.rejectPreview} resizeMode="cover" />
          ) : null}
          <Pressable
            onPress={onPrimary}
            style={({ pressed }) => [
              s.rejectPrimaryBtn,
              { backgroundColor: C.accent, opacity: pressed ? 0.85 : 1 },
            ]}
          >
            <Feather name="upload" size={16} color="#fff" />
            <Text style={s.rejectPrimaryTxt}>{primaryLabel}</Text>
          </Pressable>
          <Pressable
            onPress={onClose}
            style={({ pressed }) => [s.rejectSecondaryBtn, { opacity: pressed ? 0.7 : 1 }]}
          >
            <Text style={[s.rejectSecondaryTxt, { color: C.textMid }]}>Close</Text>
          </Pressable>
        </View>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  rejectBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.55)",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  },
  rejectCard: {
    width: "100%",
    maxWidth: 340,
    borderRadius: 20,
    borderWidth: 1.5,
    padding: 22,
    alignItems: "center",
    gap: 10,
  },
  rejectIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  rejectTitle: {
    fontSize: 18,
    fontWeight: "900",
    textAlign: "center",
    letterSpacing: -0.3,
  },
  rejectBody: {
    fontSize: 13,
    lineHeight: 20,
    textAlign: "center",
    marginBottom: 4,
  },
  rejectPreview: {
    width: "100%",
    height: 140,
    borderRadius: 12,
    opacity: 0.65,
    marginTop: 4,
    marginBottom: 6,
  },
  rejectPrimaryBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    width: "100%",
    paddingVertical: 14,
    borderRadius: 14,
    marginTop: 6,
  },
  rejectPrimaryTxt: { color: "#fff", fontSize: 14, fontWeight: "800" },
  rejectSecondaryBtn: { paddingVertical: 10 },
  rejectSecondaryTxt: { fontSize: 13, fontWeight: "700" },
});
