import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import {
  FlatList,
  Modal,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

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

export default function PickerModal({
  visible, title, items, selected, onSelect, onClose,
}: Props) {
  const insets = useSafeAreaInsets();

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={s.overlay} onPress={onClose} />
      <View style={[s.sheet, { paddingBottom: insets.bottom + 8 }]}>
        <View style={s.handle} />
        <View style={s.headerRow}>
          <Text style={s.title}>{title}</Text>
          <Pressable onPress={onClose} hitSlop={12}>
            <Feather name="x" size={18} color="#475569" />
          </Pressable>
        </View>
        <FlatList
          data={items}
          keyExtractor={i => i.value}
          initialScrollIndex={Math.max(0, items.findIndex(i => i.value === selected))}
          getItemLayout={(_, index) => ({ length: 52, offset: 52 * index, index })}
          showsVerticalScrollIndicator={false}
          style={{ maxHeight: 320 }}
          renderItem={({ item }) => {
            const active = item.value === selected;
            return (
              <Pressable
                style={({ pressed }) => [
                  s.item,
                  active && s.itemActive,
                  pressed && { opacity: 0.7 },
                ]}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  onSelect(item.value);
                }}
              >
                <Text style={[s.itemText, active && s.itemTextActive]}>
                  {item.label}
                </Text>
                {active && (
                  <Feather name="check" size={15} color="#00d4ff" />
                )}
              </Pressable>
            );
          }}
        />
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
    backgroundColor: "#071525",
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderTopWidth: 1,
    borderColor: "rgba(255,255,255,0.07)",
    paddingHorizontal: 4,
  },
  handle: {
    width: 40, height: 4, borderRadius: 2,
    backgroundColor: "rgba(255,255,255,0.12)",
    alignSelf: "center", marginTop: 12, marginBottom: 4,
  },
  headerRow: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.05)",
  },
  title: {
    color: "#94a3b8", fontSize: 12,
    fontFamily: "Nunito_700Bold", letterSpacing: 1.5, textTransform: "uppercase",
  },
  item: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 20, height: 52,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
  },
  itemActive: {
    backgroundColor: "rgba(0,212,255,0.07)",
  },
  itemText: {
    color: "#64748b", fontSize: 15, fontFamily: "Nunito_500Medium",
  },
  itemTextActive: {
    color: "#e2e8f0", fontFamily: "Nunito_700Bold",
  },
});
