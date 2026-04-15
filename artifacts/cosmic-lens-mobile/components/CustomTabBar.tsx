import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import React, { useEffect, useRef, useState } from "react";
import { Animated, Platform, Pressable, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import MoreDrawer from "@/components/MoreDrawer";
import { useC, useTheme } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

type BottomTabBarProps = {
  state: { index: number; routes: { key: string; name: string }[] };
  descriptors: Record<string, unknown>;
  navigation: any;
};

const TAB_META: {
  name: string;
  labelKey: "tabHome"|"tabKundli"|"tabAsk"|"tabInsights"|"tabNotice"|"tabProfile";
  icon: string;
  dot?: boolean;
}[] = [
  { name: "index",    labelKey: "tabHome",     icon: "home"           },
  { name: "kundli",   labelKey: "tabKundli",   icon: "star"           },
  { name: "ask",      labelKey: "tabAsk",      icon: "message-circle" },
  { name: "insights", labelKey: "tabInsights", icon: "trending-up"    },
  { name: "notice",   labelKey: "tabNotice",   icon: "bell", dot: true },
  { name: "profile",  labelKey: "tabProfile",  icon: "user"           },
];

const BAR_H = 60;

// Inactive icon color — clearly visible but clearly inactive
const INACTIVE_CLR   = "#64748B";
const INACTIVE_LABEL = "#64748B";

function TabItem({
  tab, isActive, accent, onPress, onLongPress,
}: {
  tab: typeof TAB_META[0] & { label: string };
  isActive: boolean;
  accent: string;
  onPress: () => void;
  onLongPress: () => void;
}) {
  const C = useC();
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const glowAnim  = useRef(new Animated.Value(0)).current;
  const bgAnim    = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (isActive) {
      Animated.parallel([
        Animated.spring(scaleAnim, { toValue: 1.14, useNativeDriver: true, speed: 22, bounciness: 9 }),
        Animated.timing(glowAnim,  { toValue: 1, duration: 180, useNativeDriver: true }),
        Animated.timing(bgAnim,    { toValue: 1, duration: 200, useNativeDriver: false }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 22, bounciness: 4 }),
        Animated.timing(glowAnim,  { toValue: 0, duration: 160, useNativeDriver: true }),
        Animated.timing(bgAnim,    { toValue: 0, duration: 180, useNativeDriver: false }),
      ]).start();
    }
  }, [isActive]);

  // Animated bg pill color — use same hue as accent at 0→10% alpha
  const bgColor = bgAnim.interpolate({
    inputRange:  [0, 1],
    outputRange: [`${accent}00`, `${accent}1A`],
  });

  const iconColor  = isActive ? accent : INACTIVE_CLR;
  const labelColor = isActive ? accent : INACTIVE_LABEL;

  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, pressed && { opacity: 0.72 }]}
      onPress={onPress}
      onLongPress={onLongPress}
    >
      {/* Top accent line */}
      {isActive && (
        <Animated.View
          style={[
            styles.indicator,
            {
              backgroundColor: accent,
              shadowColor: accent,
              opacity: glowAnim,
            },
          ]}
        />
      )}

      {/* Icon + optional bg pill */}
      <Animated.View style={[styles.iconPill, { backgroundColor: bgColor }]}>
        <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
          <Feather name={tab.icon as any} size={20} color={iconColor} />
        </Animated.View>
        {tab.dot && (
          <View style={[styles.dot, { borderColor: C.isDark ? "#0B1220" : "#fff" }]} />
        )}
      </Animated.View>

      <Text
        style={[
          styles.label,
          {
            color: labelColor,
            fontFamily: isActive ? "Nunito_700Bold" : "Nunito_500Medium",
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
  const { zodiacAccent } = useTheme();
  const { language } = useUser();
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const [showMore, setShowMore] = useState(false);

  const t    = getT(language);
  const TABS = TAB_META.map(tab => ({ ...tab, label: t[tab.labelKey] }));

  // Use zodiac accent if available, otherwise brand orange
  const accent = zodiacAccent?.accent ?? "#FF7A00";

  return (
    <>
      <MoreDrawer visible={showMore} onClose={() => setShowMore(false)} />
      <View
        style={[
          styles.bar,
          {
            paddingBottom: botPad,
            height: BAR_H + botPad,
            backgroundColor: C.isDark ? "#0B1220" : C.navBg,
            borderTopColor: C.isDark ? "#1E293B" : C.navBorder,
          },
        ]}
      >
        <View style={styles.inner}>
          {TABS.map(tab => {
            const route    = state.routes.find(r => r.name === tab.name);
            if (!route) return null;
            const isActive = state.index === state.routes.indexOf(route);

            return (
              <TabItem
                key={tab.name}
                tab={tab}
                isActive={isActive}
                accent={accent}
                onPress={() => {
                  const event = navigation.emit({
                    type: "tabPress", target: route.key, canPreventDefault: true,
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

          {/* ── More (•••) button ── */}
          <MoreTabButton onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            setShowMore(true);
          }} />
        </View>
      </View>
    </>
  );
}

function MoreTabButton({ onPress }: { onPress: () => void }) {
  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, pressed && { opacity: 0.72 }]}
      onPress={onPress}
    >
      <View style={styles.iconPill}>
        <Feather name="grid" size={20} color={INACTIVE_CLR} />
      </View>
      <Text style={[styles.label, { color: INACTIVE_LABEL, fontFamily: "Nunito_500Medium" }]}>
        More
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  bar: {
    position: "absolute", bottom: 0, left: 0, right: 0,
    zIndex: 100,
    borderTopWidth: 1,
  },
  inner: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 4,
  },
  tabBtn: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 5,
    position: "relative",
  },

  // Top accent line for active tab
  indicator: {
    position: "absolute",
    top: 0, left: "20%", right: "20%",
    height: 2.5,
    borderRadius: 2,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.85,
    shadowRadius: 8,
    elevation: 5,
  },

  // Icon pill (subtle bg when active)
  iconPill: {
    position: "relative",
    width: 40, height: 30,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 1,
  },

  dot: {
    position: "absolute", top: 0, right: 2,
    width: 7, height: 7, borderRadius: 3.5,
    backgroundColor: "#ef4444", borderWidth: 1.5,
  },

  label: {
    fontSize: 10.5,
    letterSpacing: 0.1,
    lineHeight: 13,
  },
});
