import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useRef } from "react";
import { Animated, Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";

type BottomTabBarProps = {
  state: { index: number; routes: { key: string; name: string }[] };
  descriptors: Record<string, unknown>;
  navigation: any;
};

const TABS: {
  name: string;
  label: string;
  icon: string;
  activeColor: string;
  dot?: boolean;
}[] = [
  { name: "index",    label: "Home",     icon: "home",           activeColor: "#00d4ff" },
  { name: "kundli",   label: "Kundli",   icon: "star",           activeColor: "#00d4ff" },
  { name: "ask",      label: "Ask",      icon: "message-circle", activeColor: "#00d4ff" },
  { name: "insights", label: "Insights", icon: "trending-up",    activeColor: "#22c55e" },
  { name: "notice",   label: "Notice",   icon: "bell",           activeColor: "#f87171", dot: true },
  { name: "profile",  label: "Profile",  icon: "user",           activeColor: "#a78bfa" },
];

const BAR_H = 64;

function TabItem({
  tab, isActive, onPress, onLongPress,
}: {
  tab: typeof TABS[0]; isActive: boolean; onPress: () => void; onLongPress: () => void;
}) {
  const C = useC();
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const glowAnim  = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isActive) {
      Animated.parallel([
        Animated.spring(scaleAnim, { toValue: 1.12, useNativeDriver: true, speed: 20, bounciness: 8 }),
        Animated.timing(glowAnim,  { toValue: 1, duration: 200, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 20, bounciness: 4 }),
        Animated.timing(glowAnim,  { toValue: 0, duration: 180, useNativeDriver: true }),
      ]).start();
    }
  }, [isActive]);

  const INACTIVE = C.isDark ? "#3d5a7a" : "#94a3b8";
  const color = isActive ? tab.activeColor : INACTIVE;

  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, pressed && { opacity: 0.7 }]}
      onPress={onPress}
      onLongPress={onLongPress}
    >
      {isActive && (
        <Animated.View
          style={[
            styles.indicator,
            {
              backgroundColor: tab.activeColor,
              shadowColor:      tab.activeColor,
              opacity: glowAnim,
            },
          ]}
        />
      )}

      <Animated.View style={[styles.iconWrap, { transform: [{ scale: scaleAnim }] }]}>
        <Feather name={tab.icon as any} size={22} color={color} />
        {tab.dot && (
          <View style={[styles.dot, { borderColor: C.navBg }]} />
        )}
      </Animated.View>

      <Text
        style={[
          styles.label,
          {
            color,
            fontFamily: isActive ? "Nunito_700Bold" : "Nunito_400Regular",
            opacity: isActive ? 1 : 0.7,
          },
        ]}
      >
        {tab.label}
      </Text>
    </Pressable>
  );
}

export default function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const C = useC();
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={[
      styles.bar,
      {
        paddingBottom: botPad,
        height: BAR_H + botPad,
        backgroundColor: C.navBg,
        borderTopColor: C.navBorder,
      },
    ]}>
      <View style={[styles.topLine, { backgroundColor: C.isDark ? "rgba(0,200,255,0.14)" : C.border }]} />
      <View style={styles.inner}>
        {TABS.map((tab) => {
          const route = state.routes.find(r => r.name === tab.name);
          if (!route) return null;
          const isActive = state.index === state.routes.indexOf(route);

          return (
            <TabItem
              key={tab.name}
              tab={tab}
              isActive={isActive}
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
            />
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
    zIndex: 100,
    borderTopWidth: 1,
  },
  topLine: {
    height: 1,
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
    paddingVertical: 7,
    position: "relative",
  },
  indicator: {
    position: "absolute",
    top: 0, left: "18%", right: "18%",
    height: 2.5,
    borderRadius: 2,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.7,
    shadowRadius: 6,
    elevation: 4,
  },
  iconWrap: {
    position: "relative",
    marginBottom: 2,
  },
  dot: {
    position: "absolute",
    top: -2, right: -3,
    width: 7, height: 7,
    borderRadius: 3.5,
    backgroundColor: "#ef4444",
    borderWidth: 1.5,
  },
  label: {
    fontSize: 10,
    letterSpacing: 0.15,
    lineHeight: 12,
  },
});
