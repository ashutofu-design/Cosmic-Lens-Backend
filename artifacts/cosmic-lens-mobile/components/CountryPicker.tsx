import { Feather } from "@expo/vector-icons";
import React, { useMemo, useState } from "react";
import {
  FlatList,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useC } from "@/context/ThemeContext";
import { COUNTRIES, type Country } from "@/lib/countries";

type Props = {
  visible: boolean;
  onClose: () => void;
  onSelect: (c: Country) => void;
  selectedCode?: string;
};

export function CountryPicker({ visible, onClose, onSelect, selectedCode }: Props) {
  const C = useC();
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return COUNTRIES;
    return COUNTRIES.filter(
      c =>
        c.name.toLowerCase().includes(q) ||
        c.dial.includes(q) ||
        c.code.toLowerCase().includes(q),
    );
  }, [query]);

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <Pressable style={styles.backdrop} onPress={onClose} />
      <View style={[styles.sheet, { backgroundColor: C.bgCard, borderColor: C.border2 }]}>
        <View style={styles.handle}>
          <View style={[styles.handleBar, { backgroundColor: C.border }]} />
        </View>

        <View style={styles.header}>
          <Text style={[styles.title, { color: C.text }]}>Select Country</Text>
          <Pressable onPress={onClose} hitSlop={10}>
            <Feather name="x" size={20} color={C.textMid} />
          </Pressable>
        </View>

        <View style={[styles.searchBox, { backgroundColor: C.inputBg, borderColor: C.inputBorder }]}>
          <Feather name="search" size={15} color={C.textMuted} />
          <TextInput
            value={query}
            onChangeText={setQuery}
            placeholder="Search country or code"
            placeholderTextColor={C.textMuted}
            style={[styles.searchInput, { color: C.text }]}
            autoCapitalize="none"
            autoCorrect={false}
          />
        </View>

        <FlatList
          data={filtered}
          keyExtractor={c => c.code}
          keyboardShouldPersistTaps="handled"
          renderItem={({ item }) => {
            const active = item.code === selectedCode;
            return (
              <Pressable
                onPress={() => { onSelect(item); onClose(); setQuery(""); }}
                style={({ pressed }) => [
                  styles.row,
                  { borderBottomColor: C.border, opacity: pressed ? 0.7 : 1 },
                  active && { backgroundColor: "rgba(124,58,237,0.10)" },
                ]}
              >
                <Text style={styles.flag}>{item.flag}</Text>
                <Text style={[styles.name, { color: C.text }]} numberOfLines={1}>{item.name}</Text>
                <Text style={[styles.dial, { color: C.textMuted }]}>+{item.dial}</Text>
                {active && <Feather name="check" size={16} color="#7c3aed" style={{ marginLeft: 6 }} />}
              </Pressable>
            );
          }}
          style={{ flex: 1 }}
          contentContainerStyle={{ paddingBottom: 24 }}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: "rgba(0,0,0,0.55)" },
  sheet: {
    position: "absolute", left: 0, right: 0, bottom: 0,
    height: "75%",
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    borderWidth: 1, borderBottomWidth: 0,
    paddingHorizontal: 16, paddingTop: 6,
    ...(Platform.OS === "web" ? { maxWidth: 420, marginHorizontal: "auto" as any } : {}),
  },
  handle: { alignItems: "center", paddingVertical: 8 },
  handleBar: { width: 40, height: 4, borderRadius: 2 },
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingVertical: 6, marginBottom: 8,
  },
  title: { fontSize: 16, fontFamily: "Nunito_700Bold" },
  searchBox: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 12, paddingVertical: 10,
    borderRadius: 12, borderWidth: 1, marginBottom: 10,
  },
  searchInput: { flex: 1, fontSize: 14, fontFamily: "Nunito_500Medium", padding: 0 },
  row: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 13, paddingHorizontal: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
  },
  flag: { fontSize: 22 },
  name: { flex: 1, fontSize: 14, fontFamily: "Nunito_600SemiBold" },
  dial: { fontSize: 13, fontFamily: "Nunito_700Bold" },
});
