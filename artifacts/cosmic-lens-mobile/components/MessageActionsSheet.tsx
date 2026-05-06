/**
 * MessageActionsSheet — bottom sheet shown on long-press of an assistant
 * message bubble. Three actions: Copy text, Share, Regenerate (re-asks the
 * prior user question that produced this answer).
 */
import { Feather } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import * as Haptics from "expo-haptics";
import * as Sharing from "expo-sharing";
// expo-file-system v55 splits the legacy classic API into /legacy. We only
// need writeAsStringAsync + a cache dir, so legacy is the smallest surface.
import * as FileSystem from "expo-file-system/legacy";
import React from "react";
import {
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { useC } from "@/context/ThemeContext";

type Props = {
  visible: boolean;
  text: string;
  canRegenerate: boolean;
  onClose: () => void;
  onRegenerate: () => void;
};

export function MessageActionsSheet({
  visible,
  text,
  canRegenerate,
  onClose,
  onRegenerate,
}: Props) {
  const C = useC();

  const doCopy = async () => {
    try {
      await Clipboard.setStringAsync(text);
      try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
    } catch {}
    onClose();
  };

  const doShare = async () => {
    try {
      // Web doesn't support Sharing.shareAsync — gracefully fall back to copy.
      const available = Platform.OS === "web" ? false : await Sharing.isAvailableAsync();
      if (!available) {
        await Clipboard.setStringAsync(text);
        try { Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success); } catch {}
        onClose();
        return;
      }
      // Sharing.shareAsync needs a file URI on most platforms.
      const path = (FileSystem.cacheDirectory || FileSystem.documentDirectory || "") + "acharya_reply.txt";
      await FileSystem.writeAsStringAsync(path, text, {
        encoding: FileSystem.EncodingType.UTF8,
      });
      await Sharing.shareAsync(path, { mimeType: "text/plain", dialogTitle: "Share Cosmic Intelligence reply" });
    } catch {
      try { await Clipboard.setStringAsync(text); } catch {}
    }
    onClose();
  };

  const doRegen = () => {
    onClose();
    setTimeout(onRegenerate, 50);
  };

  const Item = ({ icon, label, onPress, disabled }: {
    icon: keyof typeof Feather.glyphMap; label: string; onPress: () => void; disabled?: boolean;
  }) => (
    <Pressable
      onPress={() => { if (!disabled) { try { Haptics.selectionAsync(); } catch {}; onPress(); } }}
      disabled={disabled}
      style={({ pressed }) => [
        s.row,
        { borderBottomColor: C.border + "55" },
        pressed && !disabled && { backgroundColor: C.bgCard2 },
        disabled && { opacity: 0.4 },
      ]}
    >
      <Feather name={icon} size={18} color={C.text} />
      <Text style={[s.rowText, { color: C.text }]}>{label}</Text>
    </Pressable>
  );

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={s.backdrop} onPress={onClose}>
        <Pressable
          onPress={(e) => e.stopPropagation?.()}
          style={[s.sheet, { backgroundColor: C.bgCard, borderColor: C.border }]}
        >
          <View style={[s.handle, { backgroundColor: C.textMuted + "55" }]} />
          <Item icon="copy"     label="Copy"       onPress={doCopy} />
          <Item icon="share-2"  label="Share"      onPress={doShare} />
          <Item icon="refresh-cw" label="Regenerate" onPress={doRegen} disabled={!canRegenerate} />
          <Pressable onPress={onClose} style={[s.cancel, { backgroundColor: C.bgCard2 }]}>
            <Text style={[s.cancelText, { color: C.textMid }]}>Cancel</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const s = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end" },
  sheet: {
    borderTopLeftRadius: 18, borderTopRightRadius: 18,
    borderTopWidth: 1, borderLeftWidth: 1, borderRightWidth: 1,
    paddingTop: 8, paddingBottom: 28,
  },
  handle: {
    alignSelf: "center", width: 40, height: 4, borderRadius: 2,
    marginBottom: 10, marginTop: 4,
  },
  row: {
    flexDirection: "row", alignItems: "center", gap: 14,
    paddingHorizontal: 22, paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  rowText: { fontSize: 15, fontWeight: "600" },
  cancel: {
    marginHorizontal: 16, marginTop: 12, borderRadius: 12,
    paddingVertical: 13, alignItems: "center",
  },
  cancelText: { fontSize: 14, fontWeight: "700" },
});
