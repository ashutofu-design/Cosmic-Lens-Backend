import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

export type ProProductPickerOption = {
  id: string;
  emoji: string;
  title: string;
  hint: string;
  priceLabel: string;
  /** Optional compare-at price shown struck through */
  strikeLabel?: string;
  badge?: string;
};

export type ProProductPickerAccent = {
  selectedBorder: string;
  selectedBg: string;
  iconBg: string;
  radio: string;
  badgeBg: string;
  badgeText: string;
  priceColor?: string;
  gradient?: [string, string];
};

type Props = {
  title: string;
  subtitle?: string;
  options: ProProductPickerOption[];
  selectedId: string;
  onSelect: (id: string) => void;
  isDark: boolean;
  cardBg: string;
  border: string;
  titleColor: string;
  bodyColor: string;
  accent: ProProductPickerAccent;
};

export function ProProductPicker({
  title,
  subtitle,
  options,
  selectedId,
  onSelect,
  isDark,
  cardBg,
  border,
  titleColor,
  bodyColor,
  accent,
}: Props) {
  return (
    <View style={[styles.card, { backgroundColor: cardBg, borderColor: border }]}>
      <View style={styles.head}>
        <View style={[styles.eyebrowDot, { backgroundColor: accent.radio }]} />
        <Text style={[styles.eyebrow, { color: accent.radio }]}>PICK & PAY</Text>
      </View>
      <Text style={[styles.title, { color: titleColor }]}>{title}</Text>
      {subtitle ? (
        <Text style={[styles.subtitle, { color: bodyColor }]}>{subtitle}</Text>
      ) : null}

      <View style={styles.list}>
        {options.map(opt => {
          const selected = opt.id === selectedId;
          return (
            <Pressable
              key={opt.id}
              onPress={() => {
                onSelect(opt.id);
                Haptics.selectionAsync();
              }}
              style={[
                styles.option,
                {
                  borderColor: selected ? accent.selectedBorder : border,
                  backgroundColor: selected ? accent.selectedBg : (isDark ? "rgba(255,255,255,0.03)" : "rgba(15,23,42,0.02)"),
                  paddingTop: opt.badge ? 18 : 12,
                },
              ]}
            >
              {selected && accent.gradient ? (
                <LinearGradient
                  colors={accent.gradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={StyleSheet.absoluteFill}
                />
              ) : null}

              {opt.badge ? (
                <View style={[styles.badge, { backgroundColor: accent.badgeBg }]}>
                  <Text style={[styles.badgeTxt, { color: accent.badgeText }]}>{opt.badge}</Text>
                </View>
              ) : null}

              <View style={[styles.iconWrap, { backgroundColor: accent.iconBg }]}>
                <Text style={styles.emoji}>{opt.emoji}</Text>
              </View>

              <View style={styles.mid}>
                <Text style={[styles.optTitle, { color: titleColor }]} numberOfLines={2}>
                  {opt.title}
                </Text>
                <Text style={[styles.optHint, { color: bodyColor }]} numberOfLines={2}>
                  {opt.hint}
                </Text>
              </View>

              <View style={styles.right}>
                {opt.strikeLabel ? (
                  <Text style={[styles.strike, { color: bodyColor }]}>{opt.strikeLabel}</Text>
                ) : null}
                <Text
                  style={[
                    styles.price,
                    { color: selected ? (accent.priceColor ?? accent.selectedBorder) : titleColor },
                  ]}
                >
                  {opt.priceLabel}
                </Text>
                <View
                  style={[
                    styles.radio,
                    {
                      borderColor: selected ? accent.radio : border,
                      backgroundColor: selected ? accent.radio : "transparent",
                    },
                  ]}
                >
                  {selected ? <Feather name="check" size={11} color="#fff" /> : null}
                </View>
              </View>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

export const PRO_PICKER_ACCENTS = {
  violet: {
    selectedBorder: "#7c3aed",
    selectedBg: "rgba(124,58,237,0.10)",
    iconBg: "rgba(124,58,237,0.14)",
    radio: "#7c3aed",
    badgeBg: "#7c3aed",
    badgeText: "#fff",
    priceColor: "#6d28d9",
    gradient: ["rgba(124,58,237,0.16)", "rgba(99,102,241,0.06)"] as [string, string],
  },
  violetDark: {
    selectedBorder: "#a78bfa",
    selectedBg: "rgba(124,58,237,0.18)",
    iconBg: "rgba(167,139,250,0.18)",
    radio: "#a78bfa",
    badgeBg: "#7c3aed",
    badgeText: "#fff",
    priceColor: "#c4b5fd",
    gradient: ["rgba(124,58,237,0.28)", "rgba(99,102,241,0.10)"] as [string, string],
  },
  pink: {
    selectedBorder: "#db2777",
    selectedBg: "rgba(236,72,153,0.10)",
    iconBg: "rgba(236,72,153,0.14)",
    radio: "#db2777",
    badgeBg: "#db2777",
    badgeText: "#fff",
    priceColor: "#be185d",
    gradient: ["rgba(236,72,153,0.16)", "rgba(168,85,247,0.08)"] as [string, string],
  },
  pinkDark: {
    selectedBorder: "#f9a8d4",
    selectedBg: "rgba(236,72,153,0.18)",
    iconBg: "rgba(249,168,212,0.18)",
    radio: "#f472b6",
    badgeBg: "#db2777",
    badgeText: "#fff",
    priceColor: "#fbcfe8",
    gradient: ["rgba(236,72,153,0.28)", "rgba(168,85,247,0.12)"] as [string, string],
  },
  teal: {
    selectedBorder: "#0f766e",
    selectedBg: "rgba(15,118,110,0.10)",
    iconBg: "rgba(15,118,110,0.12)",
    radio: "#0f766e",
    badgeBg: "#0f766e",
    badgeText: "#fff",
    priceColor: "#0f766e",
    gradient: ["rgba(15,118,110,0.14)", "rgba(20,184,166,0.06)"] as [string, string],
  },
  tealDark: {
    selectedBorder: "#5eead4",
    selectedBg: "rgba(15,118,110,0.20)",
    iconBg: "rgba(94,234,212,0.16)",
    radio: "#14b8a6",
    badgeBg: "#0f766e",
    badgeText: "#fff",
    priceColor: "#99f6e4",
    gradient: ["rgba(15,118,110,0.28)", "rgba(20,184,166,0.10)"] as [string, string],
  },
  amber: {
    selectedBorder: "#d97706",
    selectedBg: "rgba(245,158,11,0.12)",
    iconBg: "rgba(245,158,11,0.14)",
    radio: "#d97706",
    badgeBg: "#d97706",
    badgeText: "#fff",
    priceColor: "#b45309",
    gradient: ["rgba(245,158,11,0.16)", "rgba(251,191,36,0.06)"] as [string, string],
  },
  amberDark: {
    selectedBorder: "#fbbf24",
    selectedBg: "rgba(245,158,11,0.18)",
    iconBg: "rgba(251,191,36,0.16)",
    radio: "#f59e0b",
    badgeBg: "#d97706",
    badgeText: "#fff",
    priceColor: "#fde68a",
    gradient: ["rgba(245,158,11,0.26)", "rgba(251,191,36,0.10)"] as [string, string],
  },
} as const;

const styles = StyleSheet.create({
  card: {
    borderRadius: 18,
    borderWidth: 1,
    padding: 14,
    overflow: "hidden",
  },
  head: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 4,
  },
  eyebrowDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  eyebrow: {
    fontSize: 10,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.2,
  },
  title: {
    fontSize: 17,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: -0.3,
    lineHeight: 22,
  },
  subtitle: {
    fontSize: 12,
    fontFamily: "Nunito_500Medium",
    lineHeight: 16,
    marginTop: 3,
  },
  list: {
    gap: 10,
    marginTop: 12,
  },
  option: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 2,
    overflow: "hidden",
    position: "relative",
  },
  badge: {
    position: "absolute",
    top: 0,
    right: 10,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
    zIndex: 2,
  },
  badgeTxt: {
    fontSize: 9,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 0.6,
  },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  emoji: {
    fontSize: 20,
  },
  mid: {
    flex: 1,
    gap: 2,
    paddingRight: 4,
  },
  optTitle: {
    fontSize: 13.5,
    fontFamily: "Nunito_800ExtraBold",
    lineHeight: 18,
  },
  optHint: {
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
    lineHeight: 15,
  },
  right: {
    alignItems: "flex-end",
    gap: 4,
    minWidth: 64,
  },
  strike: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    textDecorationLine: "line-through",
    opacity: 0.7,
  },
  price: {
    fontSize: 16,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: -0.3,
  },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },
});
