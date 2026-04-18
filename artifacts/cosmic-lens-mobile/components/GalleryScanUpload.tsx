/**
 * GalleryScanUpload — for users who aren't at home and can't open the live
 * camera. Lets them pick a photo from the gallery, then manually tag the
 * room type + direction (since there's no live magnetometer reading).
 *
 * Submits via the parent's `onSubmit` callback as:
 *   { data_url, base64, room_type, direction }
 * The parent wires this into the existing /api/astrovastu-pro POST.
 *
 * Branding: "Cosmic Vision" — never mentions AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
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

export function GalleryScanUpload({ onSubmit, loading, disabled }: Props) {
  const C = useC();
  const [open, setOpen] = useState(false);
  const [picking, setPicking] = useState(false);
  const [photo, setPhoto] = useState<{ data_url: string; base64: string } | null>(null);
  const [roomType, setRoomType] = useState<string>("");
  const [direction, setDirection] = useState<string>("");

  // ── Open gallery & pick image ───────────────────────────────────────
  const pickImage = useCallback(async () => {
    if (disabled || loading || picking) return;
    Haptics.selectionAsync();
    setPicking(true);
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert(
          "Gallery permission needed",
          "Please allow photo access so you can pick a room photo from your gallery.",
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
      setPhoto({
        base64:   a.base64!,
        data_url: `data:${a.mimeType || "image/jpeg"};base64,${a.base64}`,
      });
      setRoomType("");
      setDirection("");
      setOpen(true);
    } catch (e: any) {
      Alert.alert("Couldn't open gallery", String(e?.message || e));
    } finally {
      setPicking(false);
    }
  }, [disabled, loading, picking]);

  const close = useCallback(() => {
    if (loading) return;
    Haptics.selectionAsync();
    setOpen(false);
    setPhoto(null);
    setRoomType("");
    setDirection("");
  }, [loading]);

  const submit = useCallback(() => {
    if (!photo || !roomType || !direction || loading) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onSubmit({
      data_url:  photo.data_url,
      base64:    photo.base64,
      room_type: roomType,
      direction,
    });
    setOpen(false);
    setPhoto(null);
    setRoomType("");
    setDirection("");
  }, [direction, loading, onSubmit, photo, roomType]);

  const canSubmit = !!photo && !!roomType && !!direction && !loading;

  return (
    <>
      <Pressable
        onPress={pickImage}
        disabled={disabled || loading || picking}
        style={({ pressed }) => [
          s.uploadBtn,
          {
            borderColor: C.border,
            backgroundColor: C.bgCard,
            opacity: (disabled || loading) ? 0.5 : pressed ? 0.85 : 1,
          },
        ]}
      >
        {picking ? (
          <ActivityIndicator color={C.accent} />
        ) : (
          <>
            <Feather name="image" size={20} color={C.accent} />
            <View style={{ flex: 1 }}>
              <Text style={[s.uploadTitle, { color: C.text }]}>
                Upload from Gallery
              </Text>
              <Text style={[s.uploadSub, { color: C.textMid }]}>
                Not at home? Pick a photo and tag the room + direction manually.
              </Text>
            </View>
            <Feather name="chevron-right" size={18} color={C.textMid} />
          </>
        )}
      </Pressable>

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
            <Text style={[s.modalTitle, { color: C.text }]}>Tag this photo</Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
            {photo ? (
              <Image
                source={{ uri: photo.data_url }}
                style={s.preview}
                resizeMode="cover"
              />
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
              You picked the direction yourself, so Cosmic Vision will use it as
              ground truth instead of inferring from the photo.
            </Text>
          </ScrollView>
        </View>
      </Modal>
    </>
  );
}

const s = StyleSheet.create({
  uploadBtn: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 16, paddingHorizontal: 16,
    borderRadius: 14, borderWidth: 1, marginTop: 12,
  },
  uploadTitle: { fontSize: 14, fontWeight: "700" },
  uploadSub:   { fontSize: 11, marginTop: 2, lineHeight: 15 },

  modalWrap:    { flex: 1 },
  modalHeader:  {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 12, paddingTop: 50, paddingBottom: 12, borderBottomWidth: 1,
  },
  modalTitle:   { fontSize: 16, fontWeight: "700" },

  preview:      { width: "100%", height: 220, borderRadius: 12 },
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
