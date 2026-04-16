import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated, LayoutAnimation, Platform, Pressable,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import MoreDrawer from "@/components/MoreDrawer";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

type BottomTabBarProps = {
  state: { index: number; routes: { key: string; name: string }[] };
  descriptors: Record<string, unknown>;
  navigation: any;
};

const TAB_META: {
  name: string;
  labelKey: "tabHome"|"tabLifeMap"|"tabAsk"|"tabFuture"|"tabNotice"|"tabProfile";
  icon: string;
  dot?: boolean;
}[] = [
  { name: "index",    labelKey: "tabHome",     icon: "home"           },
  { name: "lifemap",  labelKey: "tabLifeMap",  icon: "map"            },
  { name: "ask",      labelKey: "tabAsk",      icon: "message-circle" },
  { name: "insights", labelKey: "tabFuture",   icon: "bar-chart-2"   },
  { name: "profile",  labelKey: "tabProfile",  icon: "user"           },
];

const BAR_H = 84;

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
  const scaleAnim = useRef(new Animated.Value(isActive ? 1.08 : 1)).current;
  const glowAnim = useRef(new Animated.Value(isActive ? 1 : 0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: isActive ? 1.08 : 1,
        useNativeDriver: true,
        speed: 24,
        bounciness: isActive ? 8 : 3,
      }),
      Animated.timing(glowAnim, {
        toValue: isActive ? 1 : 0,
        duration: 280,
        useNativeDriver: false,
      }),
    ]).start();
  }, [isActive]);

  const activeColor = C.isDark ? "#FCD34D" : "#7C3AED";
  const inactiveColor = C.isDark ? "rgba(148,163,184,0.55)" : "rgba(100,116,139,0.6)";

  if (isActive) {
    return (
      <Pressable
        style={({ pressed }) => [styles.tabBtn, { flex: 1.9, minWidth: 0 }, pressed && { opacity: 0.75 }]}
        onPress={onPress}
        onLongPress={onLongPress}
      >
        <Animated.View
          style={[
            styles.pillGlow,
            {
              backgroundColor: C.isDark ? `${accent}12` : `${accent}14`,
              shadowColor: accent,
              shadowOpacity: glowAnim.interpolate({ inputRange: [0, 1], outputRange: [0, C.isDark ? 0.6 : 0.4] }),
              shadowRadius: glowAnim.interpolate({ inputRange: [0, 1], outputRange: [0, C.isDark ? 14 : 18] }),
            },
          ]}
        >
          <LinearGradient
            colors={
              C.isDark
                ? [`${accent}30`, `${accent}12`]
                : [`${accent}22`, `${accent}10`]
            }
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.pillGradient}
          >
            <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
              <Feather name={tab.icon as any} size={19} color={activeColor} />
            </Animated.View>
            {tab.dot && (
              <View style={[styles.chipDot, { borderColor: C.isDark ? "#0B1220" : "#fff" }]} />
            )}
            <Text
              numberOfLines={1}
              style={[styles.chipLabel, { color: activeColor, fontFamily: "Nunito_700Bold" }]}
            >
              {tab.label}
            </Text>
          </LinearGradient>
        </Animated.View>
      </Pressable>
    );
  }

  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, { flex: 1, minWidth: 0 }, pressed && { opacity: 0.5 }]}
      onPress={onPress}
      onLongPress={onLongPress}
    >
      <View style={styles.inactiveWrap}>
        <View style={{ position: "relative" }}>
          <Feather name={tab.icon as any} size={20} color={inactiveColor} />
          {tab.dot && (
            <View style={[styles.dot, { borderColor: C.isDark ? "#0B1220" : "#fff" }]} />
          )}
        </View>
        <Text
          numberOfLines={1}
          style={[styles.inactiveLabel, { color: inactiveColor, fontFamily: "Nunito_500Medium" }]}
        >
          {tab.label}
        </Text>
      </View>
    </Pressable>
  );
}

export default function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { language } = useUser();
  const [showMore, setStateShowMore] = useState(false);
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const t    = getT(language);
  const TABS = TAB_META.map(tab => ({ ...tab, label: t[tab.labelKey] }));
  const accent = C.isDark ? "#f59e0b" : "#7C3AED";

  const gradientTopColors: [string, string, string] = C.isDark
    ? ["#f59e0b88", "#8B5CF655", "#f59e0b44"]
    : ["#7C3AED55", "#6D5DF644", "#7C3AED55"];

  function triggerLayoutAnim() {
    if (Platform.OS !== "web") {
      LayoutAnimation.configureNext({
        duration: 220,
        update: { type: LayoutAnimation.Types.spring, springDamping: 0.75 },
        create: { type: LayoutAnimation.Types.easeInEaseOut, property: LayoutAnimation.Properties.scaleX },
      });
    }
  }

  const barBg = C.isDark ? "rgba(8,16,32,0.95)" : "rgba(255,255,255,0.94)";
  const blurTint = C.isDark ? "dark" : "light";

  return (
    <>
      <MoreDrawer visible={showMore} onClose={() => setStateShowMore(false)} />
      <View
        style={[
          styles.barOuter,
          {
            paddingBottom: botPad,
            height: BAR_H + botPad,
            shadowColor: C.isDark ? "#000" : "rgba(80,60,140,0.25)",
            shadowOffset: { width: 0, height: C.isDark ? -2 : -4 },
            shadowOpacity: C.isDark ? 0.3 : 0.2,
            shadowRadius: C.isDark ? 8 : 16,
            elevation: C.isDark ? 10 : 15,
          },
        ]}
      >
        <LinearGradient
          colors={gradientTopColors}
          start={{ x: 0, y: 0.5 }}
          end={{ x: 1, y: 0.5 }}
          style={styles.topGlowLine}
        />

        {Platform.OS !== "web" ? (
          <BlurView
            intensity={C.isDark ? 45 : 70}
            tint={blurTint}
            style={StyleSheet.absoluteFill}
          />
        ) : null}

        <View style={[StyleSheet.absoluteFill, { backgroundColor: barBg }]} />

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
                    triggerLayoutAnim();
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

          <MoreTabButton onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            setStateShowMore(true);
          }} />
        </View>
      </View>
    </>
  );
}

function MoreTabButton({ onPress }: { onPress: () => void }) {
  const C = useC();
  const inactiveColor = C.isDark ? "rgba(148,163,184,0.55)" : "rgba(100,116,139,0.6)";
  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, { flex: 1, minWidth: 0 }, pressed && { opacity: 0.5 }]}
      onPress={onPress}
    >
      <View style={styles.inactiveWrap}>
        <Feather name="grid" size={20} color={inactiveColor} />
        <Text style={[styles.inactiveLabel, { color: inactiveColor, fontFamily: "Nunito_500Medium" }]}>
          More
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  barOuter: {
    position: "absolute", bottom: 0, left: 0, right: 0,
    zIndex: 100,
    overflow: "hidden",
  },
  topGlowLine: {
    position: "absolute",
    top: 0, left: 0, right: 0,
    height: 1.5,
    zIndex: 10,
  },
  inner: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 3,
  },
  tabBtn: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
    paddingHorizontal: 2,
  },

  pillGlow: {
    borderRadius: 22,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
    maxWidth: "100%",
  },
  pillGradient: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 11,
    paddingVertical: 9,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.08)",
  },
  chipLabel: {
    fontSize: 11.5,
    letterSpacing: 0.1,
    flexShrink: 1,
  },
  chipDot: {
    position: "absolute", top: -2, right: -2,
    width: 7, height: 7, borderRadius: 3.5,
    backgroundColor: "#ef4444", borderWidth: 1.5,
  },

  inactiveWrap: {
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
  },
  inactiveLabel: {
    fontSize: 9.5,
    letterSpacing: 0,
    lineHeight: 12,
    textAlign: "center",
    paddingHorizontal: 1,
  },

  dot: {
    position: "absolute", top: -1, right: -3,
    width: 7, height: 7, borderRadius: 3.5,
    backgroundColor: "#ef4444", borderWidth: 1.5,
  },
});
