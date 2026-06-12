import React from "react";
import { StyleSheet, Text, View } from "react-native";

import { LOVE_REALITY_SOCIAL_PROOF } from "@/lib/loveRealityProCopy";

/** Future social proof — hidden until real data is available. */
export function LoveRealitySocialProof({ visible = false }: { visible?: boolean }) {
  if (!visible) return null;

  return (
    <View style={s.wrap}>
      {LOVE_REALITY_SOCIAL_PROOF.map(line => (
        <Text key={line} style={s.line}>
          {line}
        </Text>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  wrap: { gap: 6, paddingVertical: 4 },
  line: { fontSize: 13, fontFamily: "Nunito_600SemiBold", color: "rgba(226,232,240,0.85)", textAlign: "center" },
});
