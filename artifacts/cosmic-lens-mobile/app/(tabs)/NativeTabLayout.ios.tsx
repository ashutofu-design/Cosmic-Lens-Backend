/**
 * iOS 26+ liquid-glass tab bar — Metro loads this file only on iOS.
 * Web must not import expo-router/unstable-native-tabs (CSS → lightningcss crash).
 */
import { Icon, Label, NativeTabs } from "expo-router/unstable-native-tabs";
import React from "react";

import { useTabBar } from "@/context/TabBarContext";
import { useT } from "@/hooks/useT";

export default function NativeTabLayout() {
  const t = useT();
  const { hidden } = useTabBar();
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
