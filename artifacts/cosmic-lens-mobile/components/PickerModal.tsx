import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useRef } from "react";
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";

export interface PickerItem {
  label: string;
  value: string;
}

interface Props {
  visible: boolean;
  title: string;
  items: PickerItem[];
  selected: string;
  onSelect: (value: string) => void;
  onClose: () => void;
}

const ITEM_HEIGHT = 52;
const LIST_HEIGHT = 320;

export default function PickerModal({
  visible, title, items, selected, onSelect, onClose,
}: Props) {
  const C = useC();
  const insets = useSafeAreaInsets();
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (!visible || items.length === 0) return;
    const idx = items.findIndex(i => i.value === selected);
    const target = idx >= 0 ? idx : 0;
    const y = Math.max(0, target * ITEM_HEIGHT - LIST_HEIGHT * 0.35);
    const timer = setTimeout(() => {
      scrollRef.current?.scrollTo({ y, animated: false });
    }, 80);
    return () => clearTimeout(timer);
  }, [visible, selected, items]);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={s.overlay} onPress={onClose} />
      <View style={[
        s.sheet,
        {
          backgroundColor: C.bgCard,
          borderColor: C.border,
          paddingBottom: insets.bottom + 8,
        },
      ]}>
        <View style={[s.handle, { backgroundColor: C.border }]} />
        <View style={[s.headerRow, { borderBottomColor: C.border }]}>
          <Text style={[s.title, { color: C.textMuted }]}>{title}</Text>
          <Pressable onPress={onClose} hitSlop={12}>
            <Feather name="x" size={18} color={C.textMuted} />
          </Pressable>
        </View>
        <ScrollView
          ref={scrollRef}
          style={s.list}
          contentContainerStyle={s.listContent}
          showsVerticalScrollIndicator
          keyboardShouldPersistTaps="handled"
          nestedScrollEnabled
        >
          {items.map(item => {
            const active = item.value === selected;
            return (
              <Pressable
                key={item.value}
                style={({ pressed }) => [
                  s.item,
                  { borderBottomColor: C.border3 },
                  active && { backgroundColor: `${C.accent}10` },
                  pressed && { opacity: 0.7 },
                ]}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  onSelect(item.value);
                }}
              >
                <Text style={[s.itemText, { color: active ? C.text : C.textMuted, fontFamily: active ? "Nunito_700Bold" : "Nunito_500Medium" }]}>
                  {item.label}
                </Text>
                {active && (
                  <Feather name="check" size={15} color={C.accent} />
                )}
              </Pressable>
            );
          })}
        </ScrollView>
      </View>
    </Modal>
  );
}

const s = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.55)",
  },
  sheet: {
    position: "absolute",
    bottom: 0, left: 0, right: 0,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderTopWidth: 1,
    paddingHorizontal: 4,
  },
  handle: {
    width: 40, height: 4, borderRadius: 2,
    alignSelf: "center", marginTop: 12, marginBottom: 4,
  },
  headerRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 12,
    fontFamily: "Nunito_700Bold", letterSpacing: 1.5, textTransform: "uppercase",
  },
  list: {
    height: LIST_HEIGHT,
  },
  listContent: {
    flexGrow: 1,
  },
  item: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 20, height: ITEM_HEIGHT,
    borderBottomWidth: 1,
  },
  itemText: {
    fontSize: 15,
  },
});
