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
import { useC } from "@/context/ThemeContext";
import { useTabBar } from "@/context/TabBarContext";
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
];

const BAR_H = 84;

/** Inactive tab icon/label — full opacity so light (white) bar stays readable. */
function tabBarInactiveColor(C: ReturnType<typeof useC>) {
  return C.isDark ? C.textDim : C.textMuted;
}

function tabBarActiveColor(C: ReturnType<typeof useC>) {
  return C.isDark ? "#FCD34D" : C.accent;
}

function TabSlot({
  icon,
  label,
  isActive,
  showDot,
  onPress,
  onLongPress,
}: {
  icon: string;
  label: string;
  isActive: boolean;
  showDot?: boolean;
  onPress: () => void;
  onLongPress?: () => void;
}) {
  const C = useC();
  const activeColor = tabBarActiveColor(C);
  const inactiveColor = tabBarInactiveColor(C);
  const color = isActive ? activeColor : inactiveColor;

  return (
    <Pressable
      style={({ pressed }) => [styles.tabBtn, pressed && { opacity: isActive ? 0.82 : 0.55 }]}
      onPress={onPress}
      onLongPress={onLongPress}
    >
      <View style={styles.tabSlot}>
        <View style={styles.iconWrap}>
          <Feather name={icon as any} size={20} color={color} />
          {showDot && (
            <View style={[styles.dot, { borderColor: C.isDark ? "#0B1220" : "#fff" }]} />
          )}
        </View>
        <Text
          numberOfLines={1}
          adjustsFontSizeToFit
          minimumFontScale={0.72}
          style={[
            styles.tabLabel,
            {
              color,
              fontFamily: isActive ? "Nunito_700Bold" : "Nunito_600SemiBold",
            },
          ]}
        >
          {label}
        </Text>
      </View>
    </Pressable>
  );
}

function TabItem({
  tab, isActive, onPress, onLongPress,
}: {
  tab: typeof TAB_META[0] & { label: string };
  isActive: boolean;
  onPress: () => void;
  onLongPress: () => void;
}) {
  return (
    <TabSlot
      icon={tab.icon}
      label={tab.label}
      isActive={isActive}
      showDot={tab.dot}
      onPress={onPress}
      onLongPress={onLongPress}
    />
  );
}

export default function CustomTabBar({ state, descriptors, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { language } = useUser();
  const { hidden } = useTabBar();
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

  // Full-screen mode (e.g. Ask chat) — hide the bar entirely.
  if (hidden) return null;

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

function MoreTabButton({
  onPress,
  isOpen,
}: {
  onPress: () => void;
  isOpen: boolean;
}) {
  return (
    <TabSlot
      icon="grid"
      label="More"
      isActive={isOpen}
      onPress={onPress}
    />
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
    alignItems: "stretch",
    paddingHorizontal: 4,
    paddingTop: 6,
    paddingBottom: 4,
  },
  tabBtn: {
    flex: 1,
    flexBasis: 0,
    minWidth: 0,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 1,
  },
  tabSlot: {
    width: "100%",
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
    paddingVertical: 7,
    paddingHorizontal: 2,
  },
  iconWrap: {
    position: "relative",
    width: 22,
    height: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  tabLabel: {
    fontSize: 9,
    lineHeight: 11,
    letterSpacing: 0,
    textAlign: "center",
    width: "100%",
    paddingHorizontal: 1,
  },
  dot: {
    position: "absolute",
    top: -1,
    right: -4,
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: "#ef4444",
    borderWidth: 1.5,
  },
});
