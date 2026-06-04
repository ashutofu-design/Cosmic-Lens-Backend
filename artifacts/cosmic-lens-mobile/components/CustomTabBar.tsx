import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import React, { useRef, useState } from "react";
import {
  Platform, Pressable,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import MoreDrawer, { type MoreDrawerHandle } from "@/components/MoreDrawer";
import { ScalePressable } from "@/components/motion/ScalePressable";
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

/** Inactive tab icon/label — full opacity so light (white) bar stays readable. */
function tabBarInactiveColor(C: ReturnType<typeof useC>) {
  return C.isDark ? C.textDim : C.textMuted;
}

function tabBarActiveColor(C: ReturnType<typeof useC>) {
  return C.isDark ? "#FCD34D" : C.accent;
}

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
  const activeColor = tabBarActiveColor(C);
  const inactiveColor = tabBarInactiveColor(C);

  if (isActive) {
    return (
      <Pressable
        style={({ pressed }) => [styles.tabBtn, { flex: 1.9, minWidth: 0 }, pressed && { opacity: 0.82 }]}
        onPress={onPress}
        onLongPress={onLongPress}
      >
        <View
          style={[
            styles.pillGlow,
            {
              backgroundColor: C.isDark ? `${accent}12` : `${accent}14`,
              shadowColor: accent,
              shadowOpacity: C.isDark ? 0.45 : 0.28,
              shadowRadius: C.isDark ? 10 : 12,
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
            style={[
              styles.pillGradient,
              { borderColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(109,93,246,0.22)" },
            ]}
          >
            <Feather name={tab.icon as any} size={19} color={activeColor} />
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
        </View>
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
          style={[
            styles.inactiveLabel,
            {
              color: inactiveColor,
              fontFamily: C.isDark ? "Nunito_500Medium" : "Nunito_600SemiBold",
              fontSize: C.isDark ? 9.5 : 10,
            },
          ]}
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
  const moreDrawerRef = useRef<MoreDrawerHandle>(null);
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const t    = getT(language);
  const TABS = TAB_META.map(tab => ({ ...tab, label: t[tab.labelKey] }));
  const accent = C.isDark ? "#f59e0b" : C.accent;

  const gradientTopColors: [string, string, string] = C.isDark
    ? ["#f59e0b88", "#8B5CF655", "#f59e0b44"]
    : ["#7C3AED55", "#6D5DF644", "#7C3AED55"];

  const barBg = C.isDark ? "rgba(8,16,32,0.95)" : C.navBg;
  const blurTint = C.isDark ? "dark" : "light";
  const useBlur = Platform.OS === "ios";

  return (
    <>
      <MoreDrawer
        ref={moreDrawerRef}
        visible={showMore}
        onClose={() => setStateShowMore(false)}
      />
      <View
        style={[
          styles.barOuter,
          {
            paddingBottom: botPad,
            height: BAR_H + botPad,
            borderTopWidth: 1,
            borderTopColor: C.isDark ? "rgba(255,255,255,0.08)" : C.navBorder,
            shadowColor: C.isDark ? "#000" : "rgba(15,23,42,0.18)",
            shadowOffset: { width: 0, height: C.isDark ? -2 : -4 },
            shadowOpacity: C.isDark ? 0.3 : 0.28,
            shadowRadius: C.isDark ? 8 : 12,
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

        {useBlur ? (
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
                    if (Platform.OS !== "web") {
                      Haptics.selectionAsync().catch(() => {});
                    }
                    navigation.navigate(route.name);
                  }
                }}
                onLongPress={() =>
                  navigation.emit({ type: "tabLongPress", target: route.key })
                }
              />
            );
          })}

          <MoreTabButton
            isOpen={showMore}
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
              if (showMore) {
                moreDrawerRef.current?.close();
              } else {
                setStateShowMore(true);
              }
            }}
          />
        </View>
      </View>
    </>
  );
}

function MoreTabButton({ onPress, isOpen }: { onPress: () => void; isOpen: boolean }) {
  const C = useC();
  const inactiveColor = tabBarInactiveColor(C);
  const activeColor = tabBarActiveColor(C);
  const accent = C.isDark ? "#f59e0b" : C.accent;

  if (isOpen) {
    return (
      <ScalePressable
        haptic="none"
        onPress={onPress}
        style={[styles.tabBtn, { flex: 1.9, minWidth: 0 }]}
      >
        <View
          style={[
            styles.pillGlow,
            {
              backgroundColor: C.isDark ? `${accent}12` : `${accent}14`,
              shadowColor: accent,
              shadowOpacity: C.isDark ? 0.45 : 0.28,
              shadowRadius: C.isDark ? 10 : 12,
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
            style={[
              styles.pillGradient,
              { borderColor: C.isDark ? "rgba(255,255,255,0.08)" : "rgba(109,93,246,0.22)" },
            ]}
          >
            <Feather name="grid" size={19} color={activeColor} />
            <Text
              numberOfLines={1}
              style={[styles.chipLabel, { color: activeColor, fontFamily: "Nunito_700Bold" }]}
            >
              More
            </Text>
          </LinearGradient>
        </View>
      </ScalePressable>
    );
  }

  return (
    <ScalePressable
      haptic="none"
      onPress={onPress}
      style={[styles.tabBtn, { flex: 1, minWidth: 0 }]}
    >
      <View style={styles.inactiveWrap}>
        <Feather name="grid" size={20} color={inactiveColor} />
        <Text
          style={[
            styles.inactiveLabel,
            { color: inactiveColor, fontFamily: "Nunito_600SemiBold", fontSize: C.isDark ? 9.5 : 10 },
          ]}
        >
          More
        </Text>
      </View>
    </ScalePressable>
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
    borderColor: "transparent",
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
