import { Feather } from "@expo/vector-icons";
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
  labelKey: "tabHome"|"tabAsk"|"tabFuture"|"tabNotice"|"tabProfile";
  icon: string;
  dot?: boolean;
}[] = [
  { name: "index",    labelKey: "tabHome",     icon: "home"           },
  { name: "ask",      labelKey: "tabAsk",      icon: "message-circle" },
  { name: "insights", labelKey: "tabFuture",   icon: "bar-chart-2"   },
  { name: "notice",   labelKey: "tabNotice",   icon: "bell", dot: true },
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

  useEffect(() => {
    Animated.spring(scaleAnim, {
      toValue: isActive ? 1.08 : 1,
      useNativeDriver: true,
      speed: 24,
      bounciness: isActive ? 8 : 3,
    }).start();
  }, [isActive]);

  const activeColor = C.isDark ? "#FCD34D" : "#FF7A00";

  if (isActive) {
    return (
      <Pressable
        style={({ pressed }) => [styles.tabBtn, { flex: 2.6 }, pressed && { opacity: 0.75 }]}
        onPress={onPress}
        onLongPress={onLongPress}
      >
        <View
          style={[
            styles.chip,
            {
              backgroundColor: C.isDark ? `${accent}28` : `${accent}18`,
              borderColor: C.isDark ? `${accent}72` : `${accent}55`,
              shadowColor: accent,
            },
          ]}
        >
          <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
            <Feather name={tab.icon as any} size={19} color={activeColor} />
          </Animated.View>
          {tab.dot && (
            <View style={[styles.chipDot, { borderColor: C.isDark ? "#0B1220" : "#fff" }]} />
          )}
          <Text style={[styles.chipLabel, { color: activeColor, fontFamily: "Nunito_700Bold" }]}>
            {tab.label}
          </Text>
        </View>
      </Pressable>
    );
  }

  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, { flex: 1 }, pressed && { opacity: 0.65 }]}
      onPress={onPress}
      onLongPress={onLongPress}
    >
      <View style={styles.inactiveWrap}>
        <View style={{ position: "relative" }}>
          <Feather name={tab.icon as any} size={20} color={C.textMuted} />
          {tab.dot && (
            <View style={[styles.dot, { borderColor: C.isDark ? "#0B1220" : "#fff" }]} />
          )}
        </View>
        <Text
          numberOfLines={1}
          style={[styles.inactiveLabel, { color: C.textMuted, fontFamily: "Nunito_500Medium" }]}
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
  const accent = C.btnGradStart;

  function triggerLayoutAnim() {
    if (Platform.OS !== "web") {
      LayoutAnimation.configureNext({
        duration: 220,
        update: { type: LayoutAnimation.Types.spring, springDamping: 0.75 },
        create: { type: LayoutAnimation.Types.easeInEaseOut, property: LayoutAnimation.Properties.scaleX },
      });
    }
  }

  return (
    <>
      <MoreDrawer visible={showMore} onClose={() => setStateShowMore(false)} />
      <View
        style={[
          styles.bar,
          {
            paddingBottom: botPad,
            height: BAR_H + botPad,
            backgroundColor: C.isDark ? "#0C1322" : C.navBg,
            borderTopColor: C.isDark ? `${accent}30` : C.navBorder,
            shadowColor: C.isDark ? accent : "#000",
            shadowOffset: { width: 0, height: -3 },
            shadowOpacity: C.isDark ? 0.22 : 0.06,
            shadowRadius: C.isDark ? 12 : 4,
            elevation: 12,
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
  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, { flex: 1 }, pressed && { opacity: 0.65 }]}
      onPress={onPress}
    >
      <View style={styles.inactiveWrap}>
        <Feather name="grid" size={20} color={C.textMuted} />
        <Text style={[styles.inactiveLabel, { color: C.textMuted, fontFamily: "Nunito_500Medium" }]}>
          More
        </Text>
      </View>
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
    paddingHorizontal: 6,
  },
  tabBtn: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
  },

  // ── Active: glowing horizontal chip ──
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 22,
    borderWidth: 1,
    // iOS glow
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.55,
    shadowRadius: 10,
    // Android glow
    elevation: 6,
  },
  chipLabel: {
    fontSize: 12,
    letterSpacing: 0.1,
  },
  chipDot: {
    position: "absolute", top: -2, right: -2,
    width: 7, height: 7, borderRadius: 3.5,
    backgroundColor: "#ef4444", borderWidth: 1.5,
  },

  // ── Inactive: stacked icon + tiny label ──
  inactiveWrap: {
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
  },
  inactiveLabel: {
    fontSize: 9.5,
    letterSpacing: 0.1,
    lineHeight: 12,
  },

  dot: {
    position: "absolute", top: -1, right: -3,
    width: 7, height: 7, borderRadius: 3.5,
    backgroundColor: "#ef4444", borderWidth: 1.5,
  },
});
