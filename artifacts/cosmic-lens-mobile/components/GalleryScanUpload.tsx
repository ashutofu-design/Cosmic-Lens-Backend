/**
 * GalleryScanUpload — for users who aren't at home and can't open the live
 * camera. Lets them pick EITHER a photo from the gallery OR a PDF floor
 * plan from files, then manually tag the room type + direction (since
 * there's no live magnetometer reading).
 *
 * Submits via the parent's `onSubmit` callback as:
 *   { kind: "image"|"pdf", data_url, base64, room_type, direction }
 * The parent wires this into the existing /api/astrovastu-pro POST.
 *
 * Branding: "Photo Engine" — never mentions AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import * as FileSystem from "expo-file-system/legacy";
import * as Haptics from "expo-haptics";
import * as ImagePicker from "expo-image-picker";
import React, { useCallback, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";

export type GalleryScanResult = {
  kind:      "image" | "pdf";
  data_url:  string;
  base64:    string;
  room_type: string;
  direction: string;
};

type Props = {
  onSubmit:  (result: GalleryScanResult) => void;
  loading?:  boolean;
  disabled?: boolean;
};

const ROOM_OPTIONS: {
  key: string; en: string; hi: string; icon: keyof typeof Feather.glyphMap;
}[] = [
  { key: "bedroom",  en: "Bedroom",     hi: "Shayan",        icon: "moon"         },
  { key: "kitchen",  en: "Kitchen",     hi: "Rasoi",         icon: "coffee"       },
  { key: "pooja",    en: "Pooja Room",  hi: "Pooja sthal",   icon: "sun"          },
  { key: "study",    en: "Study",       hi: "Adhyayan",      icon: "book-open"    },
  { key: "bathroom", en: "Bathroom",    hi: "Snan-grih",     icon: "droplet"      },
  { key: "toilet",   en: "Toilet",      hi: "Shauchalaya",   icon: "alert-circle" },
  { key: "living",   en: "Living Room", hi: "Baithak",       icon: "home"         },
  { key: "entrance", en: "Entrance",    hi: "Pravesh dwaar", icon: "log-in"       },
  { key: "store",    en: "Store",       hi: "Bhandaar",      icon: "package"      },
];

const DIRECTION_OPTIONS: { key: string; short: string; en: string; hi: string }[] = [
  { key: "N",  short: "N",  en: "North",      hi: "Uttar"    },
  { key: "NE", short: "NE", en: "North-East", hi: "Ishan"    },
  { key: "E",  short: "E",  en: "East",       hi: "Poorv"    },
  { key: "SE", short: "SE", en: "South-East", hi: "Agneya"   },
  { key: "S",  short: "S",  en: "South",      hi: "Dakshin"  },
  { key: "SW", short: "SW", en: "South-West", hi: "Nairutya" },
  { key: "W",  short: "W",  en: "West",       hi: "Paschim"  },
  { key: "NW", short: "NW", en: "North-West", hi: "Vayavya"  },
];

type PickedFile =
  | { kind: "image"; data_url: string; base64: string; name?: string }
  | { kind: "pdf";   data_url: string; base64: string; name?: string };

export function GalleryScanUpload({ onSubmit, loading, disabled }: Props) {
  const C = useC();
  const [open, setOpen] = useState(false);
  const [picking, setPicking] = useState<"image" | "pdf" | null>(null);
  const [file, setFile] = useState<PickedFile | null>(null);
  const [roomType, setRoomType] = useState<string>("");
  const [direction, setDirection] = useState<string>("");

  // ── Pick image from gallery ─────────────────────────────────────────
  const pickImage = useCallback(async () => {
    if (disabled || loading || picking) return;
    Haptics.selectionAsync();
    setPicking("image");
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          "Gallery permission needed",
          "Please allow photo access so you can pick a floor plan from your gallery.",
        );
        return;
      }
      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.7,
        base64: true,
      });
      if (res.canceled || !res.assets?.[0]?.base64) return;
      const a = res.assets[0];
      setFile({
        kind:     "image",
        base64:   a.base64!,
        data_url: `data:${a.mimeType || "image/jpeg"};base64,${a.base64}`,
        name:     a.fileName || undefined,
      });
      setRoomType("");
      setDirection("");
      setOpen(true);
    } catch (e: any) {
      Alert.alert("Couldn't open gallery", String(e?.message || e));
    } finally {
      setPicking(null);
    }
  }, [disabled, loading, picking]);

  // ── Pick PDF from device ────────────────────────────────────────────
  const pickPdf = useCallback(async () => {
    if (disabled || loading || picking) return;
    Haptics.selectionAsync();
    setPicking("pdf");
    try {
      const res = await DocumentPicker.getDocumentAsync({
        type: "application/pdf",
        copyToCacheDirectory: true,
        multiple: false,
      });
      if (res.canceled || !res.assets?.[0]) return;
      const a = res.assets[0];

      // Read the file as base64
      const base64 = await FileSystem.readAsStringAsync(a.uri, {
        encoding: FileSystem.EncodingType.Base64,
      });

      // Soft size limit (~10 MB raw → ~13 MB base64)
      if (base64.length > 13 * 1024 * 1024) {
        Alert.alert(
          "PDF too large",
          "Please pick a PDF smaller than 10 MB.",
        );
        return;
      }

      setFile({
        kind:     "pdf",
        base64,
        data_url: `data:application/pdf;base64,${base64}`,
        name:     a.name || "floor-plan.pdf",
      });
      setRoomType("");
      setDirection("");
      setOpen(true);
    } catch (e: any) {
      Alert.alert("Couldn't open file picker", String(e?.message || e));
    } finally {
      setPicking(null);
    }
  }, [disabled, loading, picking]);

  const close = useCallback(() => {
    if (loading) return;
    Haptics.selectionAsync();
    setOpen(false);
    setFile(null);
    setRoomType("");
    setDirection("");
  }, [loading]);

  const submit = useCallback(() => {
    if (!file || !roomType || !direction || loading) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onSubmit({
      kind:      file.kind,
      data_url:  file.data_url,
      base64:    file.base64,
      room_type: roomType,
      direction,
    });
    setOpen(false);
    setFile(null);
    setRoomType("");
    setDirection("");
  }, [direction, file, loading, onSubmit, roomType]);

  const canSubmit = !!file && !!roomType && !!direction && !loading;
  const busy      = !!picking || !!loading;

  return (
    <>
      {/* Two side-by-side buttons: Image | PDF */}
      <View style={s.btnRow}>
        <Pressable
          onPress={pickImage}
          disabled={disabled || busy}
          style={({ pressed }) => [
            s.uploadBtn,
            {
              borderColor: C.border,
              backgroundColor: C.bgCard,
              opacity: (disabled || loading) ? 0.5 : pressed ? 0.85 : 1,
              flex: 1,
            },
          ]}
        >
          {picking === "image" ? (
            <ActivityIndicator color={C.accent} />
          ) : (
            <>
              <Feather name="image" size={22} color={C.accent} />
              <Text style={[s.uploadTitle, { color: C.text, marginTop: 8 }]}>
                Upload Photo
              </Text>
              <Text style={[s.uploadSub, { color: C.textMid }]}>
                JPG / PNG from gallery
              </Text>
            </>
          )}
        </Pressable>

        <Pressable
          onPress={pickPdf}
          disabled={disabled || busy}
          style={({ pressed }) => [
            s.uploadBtn,
            {
              borderColor: C.border,
              backgroundColor: C.bgCard,
              opacity: (disabled || loading) ? 0.5 : pressed ? 0.85 : 1,
              flex: 1,
            },
          ]}
        >
          {picking === "pdf" ? (
            <ActivityIndicator color={C.accent} />
          ) : (
            <>
              <Feather name="file-text" size={22} color={C.accent} />
              <Text style={[s.uploadTitle, { color: C.text, marginTop: 8 }]}>
                Upload PDF
              </Text>
              <Text style={[s.uploadSub, { color: C.textMid }]}>
                Floor plan PDF (page 1)
              </Text>
            </>
          )}
        </Pressable>
      </View>

      <Text style={[s.hintLine, { color: C.textMid }]}>
        Not at home? Pick a photo or PDF and tag the room + direction manually.
      </Text>

      <Modal
        visible={open}
        animationType="slide"
        onRequestClose={close}
        statusBarTranslucent
      >
        <View style={[s.modalWrap, { backgroundColor: C.bg }]}>
          <View style={[s.modalHeader, { borderColor: C.border }]}>
            <Pressable onPress={close} hitSlop={10} style={{ padding: 6 }}>
              <Feather name="x" size={22} color={C.text} />
            </Pressable>
            <Text style={[s.modalTitle, { color: C.text }]}>Tag this {file?.kind === "pdf" ? "PDF" : "photo"}</Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
            {file?.kind === "image" ? (
              <Image
                source={{ uri: file.data_url }}
                style={s.preview}
                resizeMode="cover"
              />
            ) : file?.kind === "pdf" ? (
              <View style={[s.pdfBadge, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Feather name="file-text" size={36} color={C.accent} />
                <Text style={{ color: C.text, fontWeight: "700", marginTop: 8, textAlign: "center" }}>
                  {file.name || "floor-plan.pdf"}
                </Text>
                <Text style={{ color: C.textMid, fontSize: 11, marginTop: 4, textAlign: "center" }}>
                  We will read page 1 of this PDF as your floor plan.
                </Text>
              </View>
            ) : null}

            <Text style={[s.sectionLabel, { color: C.textMid, marginTop: 18 }]}>
              ROOM TYPE
            </Text>
            <View style={s.chipGrid}>
              {ROOM_OPTIONS.map((opt) => {
                const sel = opt.key === roomType;
                return (
                  <Pressable
                    key={opt.key}
                    onPress={() => { Haptics.selectionAsync(); setRoomType(opt.key); }}
                    style={[s.roomChip, {
                      borderColor: sel ? C.accent : C.border,
                      backgroundColor: sel ? C.accentBg : C.bgCard,
                    }]}
                  >
                    <Feather name={opt.icon} size={14} color={sel ? C.accent : C.textMid} />
                    <Text style={{
                      color: sel ? C.accent : C.text,
                      fontSize: 12, fontWeight: "700",
                    }}>{opt.en}</Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={[s.sectionLabel, { color: C.textMid, marginTop: 18 }]}>
              DIRECTION (DISHA)
            </Text>
            <View style={s.dirGrid}>
              {DIRECTION_OPTIONS.map((d) => {
                const sel = d.key === direction;
                return (
                  <Pressable
                    key={d.key}
                    onPress={() => { Haptics.selectionAsync(); setDirection(d.key); }}
                    style={[s.dirChip, {
                      borderColor: sel ? C.accent : C.border,
                      backgroundColor: sel ? C.accentBg : C.bgCard,
                    }]}
                  >
                    <Text style={{
                      color: sel ? C.accent : C.text, fontWeight: "800", fontSize: 16,
                    }}>{d.short}</Text>
                    <Text style={{
                      color: sel ? C.accent : C.textMid, fontSize: 10, marginTop: 2,
                    }}>{d.hi}</Text>
                  </Pressable>
                );
              })}
            </View>

            <Pressable
              onPress={submit}
              disabled={!canSubmit}
              style={({ pressed }) => [
                s.submitBtn,
                {
                  backgroundColor: C.accent,
                  opacity: !canSubmit ? 0.4 : pressed ? 0.85 : 1,
                  marginTop: 22,
                },
              ]}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={s.submitText}>Run Smart Scan</Text>
              )}
            </Pressable>

            <Text style={[s.fineprint, { color: C.textMid }]}>
              You picked the direction yourself, so Photo Engine will use it as
              ground truth instead of inferring from the {file?.kind === "pdf" ? "PDF" : "photo"}.
            </Text>
          </ScrollView>
        </View>
      </Modal>
    </>
  );
}

const s = StyleSheet.create({
  btnRow: {
    flexDirection: "row", gap: 10, marginTop: 12,
  },
  uploadBtn: {
    alignItems: "center", justifyContent: "center",
    paddingVertical: 18, paddingHorizontal: 12,
    borderRadius: 14, borderWidth: 1,
    minHeight: 110,
  },
  uploadTitle: { fontSize: 13, fontWeight: "700" },
  uploadSub:   { fontSize: 10, marginTop: 3, textAlign: "center" },
  hintLine:    { fontSize: 11, marginTop: 8, textAlign: "center", lineHeight: 15 },

  modalWrap:    { flex: 1 },
  modalHeader:  {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 12, paddingTop: 50, paddingBottom: 12, borderBottomWidth: 1,
  },
  modalTitle:   { fontSize: 16, fontWeight: "700" },

  preview:      { width: "100%", height: 220, borderRadius: 12 },
  pdfBadge:     {
    width: "100%", paddingVertical: 28, paddingHorizontal: 18,
    borderRadius: 12, borderWidth: 1, alignItems: "center",
  },

  sectionLabel: { fontSize: 11, fontWeight: "800", textTransform: "uppercase",
                  letterSpacing: 0.5, marginBottom: 8 },

  chipGrid:     { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  roomChip:     {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 9,
    borderRadius: 20, borderWidth: 1,
  },

  dirGrid:      { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  dirChip:      {
    width: "23%", aspectRatio: 1, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },

  submitBtn:    {
    height: 52, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
    shadowOpacity: 0.2, shadowRadius: 8, elevation: 3,
  },
  submitText:   { color: "#fff", fontSize: 16, fontWeight: "700" },
  fineprint:    { fontSize: 11, lineHeight: 16, textAlign: "center", marginTop: 12 },
});
