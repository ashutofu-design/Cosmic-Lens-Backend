/**
 * TagRoomModal — reusable modal that asks the user to confirm
 * the room type + direction (disha) for a captured/picked photo,
 * before the photo is added to the AstroVastu PRO scan queue.
 *
 * Branding: surfaces "Cosmic Vision" — never AI/LLM/GPT.
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import {
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";

export type TagRoomModalResult = { room_type: string; direction: string };

type Props = {
  visible:           boolean;
  imageDataUrl?:     string;
  suggestedDirection?: string;
  onCancel:          () => void;
  onConfirm:         (r: TagRoomModalResult) => void;
};

export const ROOM_OPTIONS: {
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

export const DIRECTION_OPTIONS: {
  key: string; short: string; en: string; hi: string;
}[] = [
  { key: "N",  short: "N",  en: "North",      hi: "Uttar"    },
  { key: "NE", short: "NE", en: "North-East", hi: "Ishan"    },
  { key: "E",  short: "E",  en: "East",       hi: "Poorv"    },
  { key: "SE", short: "SE", en: "South-East", hi: "Agneya"   },
  { key: "S",  short: "S",  en: "South",      hi: "Dakshin"  },
  { key: "SW", short: "SW", en: "South-West", hi: "Nairutya" },
  { key: "W",  short: "W",  en: "West",       hi: "Paschim"  },
  { key: "NW", short: "NW", en: "North-West", hi: "Vayavya"  },
];

export function TagRoomModal({
  visible, imageDataUrl, suggestedDirection, onCancel, onConfirm,
}: Props) {
  const C = useC();
  const [roomType,  setRoomType]  = useState<string>("");
  const [direction, setDirection] = useState<string>("");

  // Pre-fill direction from compass suggestion whenever modal opens.
  useEffect(() => {
    if (visible) {
      setRoomType("");
      setDirection(suggestedDirection || "");
    }
  }, [visible, suggestedDirection]);

  const canConfirm = !!roomType && !!direction;

  const submit = () => {
    if (!canConfirm) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    onConfirm({ room_type: roomType, direction });
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      onRequestClose={onCancel}
      statusBarTranslucent
    >
      <View style={[s.wrap, { backgroundColor: C.bg }]}>
        <View style={[s.header, { borderColor: C.border }]}>
          <Pressable onPress={onCancel} hitSlop={10} style={{ padding: 6 }}>
            <Feather name="x" size={22} color={C.text} />
          </Pressable>
          <Text style={[s.title, { color: C.text }]}>Tag this room</Text>
          <View style={{ width: 28 }} />
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
          {imageDataUrl ? (
            <Image source={{ uri: imageDataUrl }} style={s.preview} resizeMode="cover" />
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
                  <Text style={{ color: sel ? C.accent : C.text, fontSize: 12, fontWeight: "700" }}>
                    {opt.en}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={[s.sectionLabel, { color: C.textMid, marginTop: 18 }]}>
            DIRECTION (DISHA)
            {suggestedDirection ? (
              <Text style={{ fontWeight: "600", color: C.accent }}>
                {"  · compass suggested " + suggestedDirection}
              </Text>
            ) : null}
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
                  <Text style={{ color: sel ? C.accent : C.text, fontWeight: "800", fontSize: 16 }}>
                    {d.short}
                  </Text>
                  <Text style={{ color: sel ? C.accent : C.textMid, fontSize: 10, marginTop: 2 }}>
                    {d.hi}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Pressable
            onPress={submit}
            disabled={!canConfirm}
            style={({ pressed }) => [
              s.submitBtn,
              {
                backgroundColor: C.accent,
                opacity: !canConfirm ? 0.4 : pressed ? 0.85 : 1,
              },
            ]}
          >
            <Text style={s.submitText}>Add to Scan</Text>
          </Pressable>
        </ScrollView>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  wrap:    { flex: 1 },
  header:  {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 12, paddingTop: 50, paddingBottom: 12, borderBottomWidth: 1,
  },
  title:   { fontSize: 16, fontWeight: "700" },

  preview: { width: "100%", height: 220, borderRadius: 12 },
  sectionLabel: {
    fontSize: 11, fontWeight: "800", textTransform: "uppercase",
    letterSpacing: 0.5, marginBottom: 8,
  },

  chipGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  roomChip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 9,
    borderRadius: 20, borderWidth: 1,
  },

  dirGrid:  { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  dirChip:  {
    width: "23%", aspectRatio: 1, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center",
  },

  submitBtn: {
    height: 52, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
    marginTop: 22, shadowOpacity: 0.2, shadowRadius: 8, elevation: 3,
  },
  submitText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});
