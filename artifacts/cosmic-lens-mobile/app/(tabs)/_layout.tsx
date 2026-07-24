import { BlurView } from "expo-blur";
import { isLiquidGlassAvailable } from "expo-glass-effect";
import { Tabs } from "expo-router";
import { Icon, Label, NativeTabs } from "expo-router/unstable-native-tabs";
import { Feather } from "@expo/vector-icons";
import React from "react";
import { Platform, StyleSheet, View } from "react-native";

import CustomTabBar from "@/components/CustomTabBar";
import { TabBarProvider, useTabBar } from "@/context/TabBarContext";
import { useT } from "@/hooks/useT";

// ── iOS 26 Native Tab Layout (Liquid Glass) ──────────────────────────────────
function NativeTabLayout() {
  const t = useT();
  const { hidden } = useTabBar();
  // `hidden` on <NativeTabs> is the Expo-recommended way to make a screen
  // full-screen (e.g. Ask chat). It is available in SDK 55+; on the current
  // SDK 54 it's a harmless no-op (cast keeps types happy and forward-ready —
  // it will start hiding the native liquid-glass bar after an SDK 55 upgrade,
  // with no further code changes). The Ask screen drives the flag via the
  // shared TabBarContext, same as the Android/JS custom tab bar.
  const nativeTabsProps = { hidden } as Record<string, unknown>;
  return (
    <NativeTabs {...nativeTabsProps}>
      <NativeTabs.Trigger name="index">
        <Icon sf={{ default: "house", selected: "house.fill" }} />
        <Label>{t.tabHome}</Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="lifemap">
        <Icon sf={{ default: "map", selected: "map.fill" }} />
        <Label>{t.tabLifeMap}</Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="ask">
        <Icon sf={{ default: "message", selected: "message.fill" }} />
        <Label>{t.tabAsk}</Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="insights">
        <Icon sf={{ default: "chart.line.uptrend.xyaxis", selected: "chart.line.uptrend.xyaxis" }} />
        <Label>{t.tabFuture}</Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}

// ── Classic Tab Layout (Android / older iOS / Web) ───────────────────────────
function ClassicTabLayout() {
  const t = useT();
  const isIOS = Platform.OS === "ios";

  return (
    <Tabs
      tabBar={(props) => <CustomTabBar {...props} />}
      screenOptions={{
        headerShown: false,
        // Pause inactive tab trees so Home/Ask/LifeMap loops don't stack.
        freezeOnBlur: true,
      }}
    >
      <Tabs.Screen name="index"    options={{ title: t.tabHome }} />
      <Tabs.Screen name="kundli"   options={{ title: t.tabKundli, href: null }} />
      <Tabs.Screen name="lifemap"  options={{ title: t.tabLifeMap }} />
      <Tabs.Screen name="ask"      options={{ title: t.tabAsk }} />
      <Tabs.Screen name="insights" options={{ title: t.tabFuture }} />
      <Tabs.Screen name="notice"   options={{ title: t.tabNotice, href: null }} />
      <Tabs.Screen name="profile"  options={{ title: t.tabProfile, href: null }} />
    </Tabs>
  );
}

export default function TabLayout() {
  return (
    <TabBarProvider>
      {isLiquidGlassAvailable() ? <NativeTabLayout /> : <ClassicTabLayout />}
    </TabBarProvider>
  );
}
