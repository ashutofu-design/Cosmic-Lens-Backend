/**
 * useFeatureGate — drop-in premium-content lock for any screen.
 *
 * Usage:
 *   const { allowed, LockOverlay } = useFeatureGate("marriage_compat_full");
 *   …
 *   return (
 *     <CosmicBg>
 *       …existing content…
 *       {LockOverlay}
 *     </CosmicBg>
 *   );
 *
 * The overlay is `position: absolute` and covers the whole parent. When the
 * user already has access, `LockOverlay` is `null` (zero render cost).
 */

import React from "react";
import { Platform, StyleSheet, View } from "react-native";
import { BlurView } from "expo-blur";
import { useC } from "@/context/ThemeContext";
import { usePlan, FeatureKey, FEATURE_REQUIREMENT, UPGRADE_COPY } from "@/lib/subscription";
import UpgradeLock from "./UpgradeLock";

interface GateOptions {
  /** Override the auto-derived tier (defaults to FEATURE_REQUIREMENT[feature]) */
  tier?: "basic" | "pro";
  /** Custom title shown in the lock card */
  title?: string;
  /** Custom message shown in the lock card */
  message?: string;
}

export function useFeatureGate(feature: FeatureKey, opts: GateOptions = {}) {
  const { has } = usePlan();
  const C = useC();

  const allowed = has(feature);
  const tier    = opts.tier ?? FEATURE_REQUIREMENT[feature];

  const message = opts.message
    ?? (tier === "pro" ? UPGRADE_COPY.proLocked : UPGRADE_COPY.basicLocked);

  const LockOverlay = allowed ? null : (
    <View style={s.overlay} pointerEvents="auto">
      {Platform.OS === "ios" ? (
        <BlurView
          intensity={45}
          tint={C.isDark ? "dark" : "light"}
          style={StyleSheet.absoluteFillObject}
        />
      ) : (
        <View
          style={[
            StyleSheet.absoluteFillObject,
            { backgroundColor: C.isDark ? "rgba(8,5,20,0.82)" : "rgba(255,255,255,0.82)" },
          ]}
        />
      )}

      <View style={s.center}>
        <UpgradeLock
          tier={tier}
          title={opts.title}
          message={message}
          style={s.card}
        />
      </View>
    </View>
  );

  return { allowed, LockOverlay };
}

const s = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 999,
    elevation: 999,
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 24,
  },
  card: {
    width: "100%",
    maxWidth: 360,
  },
});
