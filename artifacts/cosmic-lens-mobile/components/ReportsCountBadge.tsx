import React from "react";
import { StyleSheet, Text, View, type StyleProp, type ViewStyle } from "react-native";

import { useUnreadReportsCount } from "@/lib/unreadReportsBadge";

type Props = {
  /** Force a count (tests); otherwise uses live unread store. */
  count?: number;
  style?: StyleProp<ViewStyle>;
  /** Hide when zero (default true). */
  hideWhenZero?: boolean;
};

/** Red count pill — shows 1, 2, 9+ next to My Reports. */
export function ReportsCountBadge({ count, style, hideWhenZero = true }: Props) {
  const live = useUnreadReportsCount();
  const n = typeof count === "number" ? count : live;
  if (hideWhenZero && n <= 0) return null;
  const label = n > 9 ? "9+" : String(n);
  return (
    <View style={[s.badge, style]} accessibilityLabel={`${n} new reports`}>
      <Text style={s.text}>{label}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  badge: {
    minWidth: 20,
    height: 20,
    borderRadius: 10,
    paddingHorizontal: 6,
    backgroundColor: "#ef4444",
    borderWidth: 1.5,
    borderColor: "#ffffff",
    alignItems: "center",
    justifyContent: "center",
  },
  text: {
    color: "#ffffff",
    fontSize: 11,
    fontWeight: "800",
    lineHeight: 13,
  },
});
