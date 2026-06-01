import * as Haptics from "expo-haptics";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useC } from "@/context/ThemeContext";
import { REPORT_LANG_OPTIONS, type ReportLangCode } from "@/lib/reportDisplayLang";

type Props = {
  value: ReportLangCode;
  onChange: (code: ReportLangCode) => void;
  disabled?: boolean;
};

/** English / Hinglish / Hindi — controls on-screen report text (engine output). */
export function ReportLanguageChips({ value, onChange, disabled }: Props) {
  const C = useC();

  return (
    <View style={s.row}>
      {REPORT_LANG_OPTIONS.map((opt) => {
        const sel = value === opt.code;
        return (
          <Pressable
            key={opt.code}
            disabled={disabled}
            onPress={() => {
              Haptics.selectionAsync();
              onChange(opt.code);
            }}
            style={({ pressed }) => [
              s.chip,
              {
                borderColor: sel ? C.accent : C.border,
                backgroundColor: sel ? C.accent + "18" : "transparent",
                opacity: disabled ? 0.5 : pressed ? 0.75 : 1,
              },
            ]}
          >
            <Text style={{ color: sel ? C.accent : C.text, fontWeight: "800", fontSize: 12 }}>
              {opt.native}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const s = StyleSheet.create({
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1.5,
  },
});
