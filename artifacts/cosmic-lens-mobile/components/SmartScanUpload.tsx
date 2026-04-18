/**
 * SmartScanUpload — Phase 6 Cosmic Vision UI
 *
 * Lets a user upload a top-down floor plan (image OR PDF). The selected file
 * is converted to base64 client-side and emitted via onChange so the parent
 * screen can include it in the scan POST body as `floor_plan_upload`.
 *
 * Branding: "Cosmic Vision Engine" — never mentions AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import React, { useCallback, useState } from "react";
import { Alert, Pressable, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";

export type SmartScanUploadValue = {
  type: "image" | "pdf";
  base64?: string;            // raw base64 (PDF or fallback)
  data_url?: string;          // data URL (preferred for images)
  filename?: string;
  size_bytes?: number;
};

type Props = {
  value:    SmartScanUploadValue | null;
  onChange: (v: SmartScanUploadValue | null) => void;
  disabled?: boolean;
};

const MAX_BYTES = 10 * 1024 * 1024;   // 10 MB client guard

export function SmartScanUpload({ value, onChange, disabled }: Props) {
  const C = useC();
  const [busy, setBusy] = useState(false);

  const guardSize = (n?: number) => {
    if (typeof n === "number" && n > MAX_BYTES) {
      Alert.alert(
        "File too large",
        `Floor plan must be under ${MAX_BYTES / (1024 * 1024)} MB.`,
      );
      return false;
    }
    return true;
  };

  const onPickImage = useCallback(async () => {
    if (disabled || busy) return;
    Haptics.selectionAsync();
    setBusy(true);
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (perm.status !== "granted") {
        Alert.alert("Permission needed", "Please allow photo library access to upload your floor plan.");
        return;
      }
      const r = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.85,
        base64: true,
        exif:  false,
      });
      if (r.canceled || !r.assets?.[0]?.base64) return;
      const a = r.assets[0];
      if (!guardSize(a.fileSize)) return;
      const mime = a.mimeType || "image/jpeg";
      onChange({
        type:        "image",
        data_url:    `data:${mime};base64,${a.base64}`,
        filename:    a.fileName || "floor_plan.jpg",
        size_bytes:  a.fileSize,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      Alert.alert("Upload failed", String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }, [busy, disabled, onChange]);

  const onPickPdf = useCallback(async () => {
    if (disabled || busy) return;
    Haptics.selectionAsync();
    setBusy(true);
    try {
      const r = await DocumentPicker.getDocumentAsync({
        type:               ["application/pdf", "image/*"],
        copyToCacheDirectory: true,
        multiple:           false,
      });
      if (r.canceled || !r.assets?.[0]) return;
      const f = r.assets[0];
      if (!guardSize(f.size)) return;

      // Read file as base64 (use legacy API for stable readAsStringAsync surface)
      const FileSystem = await import("expo-file-system/legacy");
      const b64 = await FileSystem.readAsStringAsync(f.uri, {
        encoding: FileSystem.EncodingType.Base64,
      });
      const isPdf = (f.mimeType || "").includes("pdf") ||
                    (f.name || "").toLowerCase().endsWith(".pdf");
      onChange({
        type:        isPdf ? "pdf" : "image",
        base64:      b64,
        data_url:    isPdf ? undefined : `data:${f.mimeType || "image/jpeg"};base64,${b64}`,
        filename:    f.name || (isPdf ? "floor_plan.pdf" : "floor_plan.jpg"),
        size_bytes:  f.size,
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      Alert.alert("Upload failed", String(e?.message || e));
    } finally {
      setBusy(false);
    }
  }, [busy, disabled, onChange]);

  const onClear = useCallback(() => {
    Haptics.selectionAsync();
    onChange(null);
  }, [onChange]);

  // ────────────────────────────────────────────────────────────────────
  return (
    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <View style={s.headerRow}>
        <Feather name="zap" size={18} color={C.accent} />
        <Text style={[s.title, { color: C.text }]}>Smart Scan — Cosmic Vision</Text>
      </View>
      <Text style={[s.sub, { color: C.textMuted }]}>
        Upload your floor plan (image or PDF). Cosmic Vision will auto-detect rooms and their directions.
      </Text>

      {value ? (
        <View style={[s.uploadedBox, { borderColor: C.accent + "55", backgroundColor: C.accent + "10" }]}>
          <Feather name="check-circle" size={18} color={C.accent} />
          <View style={{ flex: 1, marginLeft: 8 }}>
            <Text style={[s.uploadedName, { color: C.text }]} numberOfLines={1}>
              {value.filename || (value.type === "pdf" ? "floor_plan.pdf" : "floor_plan.jpg")}
            </Text>
            <Text style={[s.uploadedMeta, { color: C.textMuted }]}>
              {value.type.toUpperCase()}
              {value.size_bytes ? `  ·  ${(value.size_bytes / 1024).toFixed(0)} KB` : ""}
              {"  ·  Rooms will auto-detect on submit"}
            </Text>
          </View>
          <Pressable onPress={onClear} hitSlop={8} style={{ padding: 6 }}>
            <Feather name="x" size={18} color={C.textMuted} />
          </Pressable>
        </View>
      ) : (
        <View style={s.btnRow}>
          <Pressable
            onPress={onPickImage}
            disabled={disabled || busy}
            style={({ pressed }) => [
              s.btn,
              { backgroundColor: C.bg, borderColor: C.border, opacity: (disabled || busy) ? 0.5 : pressed ? 0.7 : 1 },
            ]}
          >
            <Feather name="image" size={16} color={C.text} />
            <Text style={[s.btnText, { color: C.text }]}>Upload Image</Text>
          </Pressable>
          <Pressable
            onPress={onPickPdf}
            disabled={disabled || busy}
            style={({ pressed }) => [
              s.btn,
              { backgroundColor: C.bg, borderColor: C.border, opacity: (disabled || busy) ? 0.5 : pressed ? 0.7 : 1 },
            ]}
          >
            <Feather name="file-text" size={16} color={C.text} />
            <Text style={[s.btnText, { color: C.text }]}>Upload PDF</Text>
          </Pressable>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  card:        { borderRadius: 12, borderWidth: 1, padding: 14, marginBottom: 14 },
  headerRow:   { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 },
  title:       { fontSize: 15, fontWeight: "700" },
  sub:         { fontSize: 12, lineHeight: 17, marginBottom: 10 },
  btnRow:      { flexDirection: "row", gap: 10 },
  btn:         { flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
                 gap: 8, paddingVertical: 11, borderRadius: 9, borderWidth: 1 },
  btnText:     { fontSize: 13, fontWeight: "600" },
  uploadedBox: { flexDirection: "row", alignItems: "center", padding: 11,
                 borderWidth: 1, borderRadius: 9 },
  uploadedName:{ fontSize: 13, fontWeight: "600" },
  uploadedMeta:{ fontSize: 11, marginTop: 2 },
});
