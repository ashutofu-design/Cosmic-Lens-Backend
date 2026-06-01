/**
 * iOS 26+ liquid-glass tab bar — loaded only when supported (not on web/Android).
 */
import { Icon, Label, NativeTabs } from "expo-router/unstable-native-tabs";
import React from "react";

import { useT } from "@/hooks/useT";

export default function NativeTabLayout() {
  const t = useT();
  return (
    <NativeTabs>
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
      <NativeTabs.Trigger name="profile">
        <Icon sf={{ default: "person", selected: "person.fill" }} />
        <Label>{t.tabProfile}</Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
