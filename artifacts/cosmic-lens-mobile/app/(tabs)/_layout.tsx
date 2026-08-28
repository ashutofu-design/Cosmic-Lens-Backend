import { isLiquidGlassAvailable } from "expo-glass-effect";
import { Tabs } from "expo-router";
import React from "react";
import { Platform } from "react-native";

import CustomTabBar from "@/components/CustomTabBar";
import { TabBarProvider } from "@/context/TabBarContext";
import { useT } from "@/hooks/useT";
import NativeTabLayout from "./NativeTabLayout";

function ClassicTabLayout() {
  const t = useT();

  return (
    <Tabs
      tabBar={(props) => <CustomTabBar {...props} />}
      screenOptions={{
        headerShown: false,
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
  const useNative = Platform.OS === "ios" && isLiquidGlassAvailable();
  return (
    <TabBarProvider>
      {useNative ? <NativeTabLayout /> : <ClassicTabLayout />}
    </TabBarProvider>
  );
}
