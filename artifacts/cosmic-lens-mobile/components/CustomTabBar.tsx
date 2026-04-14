import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React from "react";
import { Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

type BottomTabBarProps = {
  state: { index: number; routes: { key: string; name: string }[] };
  descriptors: Record<string, unknown>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  navigation: any;
};

const TABS: {
  name: string;
  label: string;
  icon: string;
  activeColor: string;
  dot?: boolean;
}[] = [
  { name: "index",    label: "Home",     icon: "home",        activeColor: "#00d4ff" },
  { name: "kundli",   label: "Kundli",   icon: "star",        activeColor: "#00d4ff" },
  { name: "ask",      label: "Ask",      icon: "message-circle", activeColor: "#00d4ff" },
  { name: "insights", label: "Insights", icon: "trending-up", activeColor: "#22c55e" },
  { name: "notice",   label: "Notice",   icon: "bell",        activeColor: "#f87171", dot: true },
  { name: "profile",  label: "Profile",  icon: "user",        activeColor: "#a78bfa" },
];

const INACTIVE = "#3d5a7a";
const BAR_H    = 56;

export default function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={[styles.bar, { paddingBottom: botPad, height: BAR_H + botPad }]}>
      {/* Top hairline */}
      <View style={styles.topLine} />

      <View style={styles.inner}>
        {TABS.map((tab, idx) => {
          const route   = state.routes.find(r => r.name === tab.name);
          if (!route) return null;
          const isActive = state.index === state.routes.indexOf(route);
          const color    = isActive ? tab.activeColor : INACTIVE;

          return (
            <Pressable
              key={tab.name}
              style={({ pressed }) => [styles.tabBtn, pressed && { opacity: 0.7 }]}
              onPress={() => {
                const event = navigation.emit({
                  type: "tabPress",
                  target: route.key,
                  canPreventDefault: true,
                });
                if (!isActive && !event.defaultPrevented) {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  navigation.navigate(route.name);
                }
              }}
              onLongPress={() =>
                navigation.emit({ type: "tabLongPress", target: route.key })
              }
            >
              {/* Active top indicator */}
              {isActive && (
                <View
                  style={[
                    styles.indicator,
                    {
                      backgroundColor: tab.activeColor,
                      shadowColor: tab.activeColor,
                    },
                  ]}
                />
              )}

              {/* Icon + dot */}
              <View style={styles.iconWrap}>
                <Feather name={tab.icon as any} size={19} color={color} />
                {tab.dot && (
                  <View style={[styles.dot, { borderColor: "#020d1a" }]} />
                )}
              </View>

              {/* Label */}
              <Text style={[styles.label, { color, fontWeight: isActive ? "700" : "400" }]}>
                {tab.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: "absolute",
    bottom: 0, left: 0, right: 0,
    backgroundColor: "#020d1a",
    zIndex: 100,
  },
  topLine: {
    height: 1,
    backgroundColor: "rgba(0,200,255,0.12)",
  },
  inner: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
  },
  tabBtn: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 6,
    position: "relative",
  },
  indicator: {
    position: "absolute",
    top: 0, left: "22%", right: "22%",
    height: 2,
    borderRadius: 2,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.55,
    shadowRadius: 4,
    elevation: 3,
  },
  iconWrap: {
    position: "relative",
  },
  dot: {
    position: "absolute",
    top: -2, right: -3,
    width: 6, height: 6,
    borderRadius: 3,
    backgroundColor: "#ef4444",
    borderWidth: 1.5,
  },
  label: {
    fontSize: 8,
    letterSpacing: 0.2,
    marginTop: 2,
    lineHeight: 10,
  },
});
