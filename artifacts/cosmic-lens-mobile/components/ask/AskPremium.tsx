import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type ViewStyle,
} from "react-native";

import { FadeInView } from "@/components/motion/FadeInView";

const F = {
  semi: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
  extra: "Nunito_800ExtraBold",
} as const;

export const ASK_ACCENT = "#818cf8";
export const ASK_GOLD = "#C2A878";

export function AskPremiumOrb({ color = ASK_ACCENT }: { color?: string }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 2800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 2800, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.18] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.18, 0.42] });
  return (
    <Animated.View
      pointerEvents="none"
      style={[orb.wrap, { backgroundColor: color, transform: [{ scale }], opacity }]}
    />
  );
}

export function AskLivePulse({ color = "#10b981" }: { color?: string }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  const ringScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.8] });
  const ringOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.55, 0] });
  return (
    <View style={orb.liveWrap}>
      <Animated.View style={[orb.liveRing, { borderColor: color, opacity: ringOpacity, transform: [{ scale: ringScale }] }]} />
      <View style={[orb.liveDot, { backgroundColor: color }]} />
    </View>
  );
}

type ModeCardProps = {
  colors: [string, string, ...string[]];
  glow: string;
  emoji: string;
  title: string;
  body: string;
  metaIcon: React.ComponentProps<typeof Feather>["name"];
  metaText: string;
  badge?: string;
  onPress: () => void;
  delay?: number;
};

export function PremiumModeCard({
  colors,
  glow,
  emoji,
  title,
  body,
  metaIcon,
  metaText,
  badge,
  onPress,
  delay = 0,
}: ModeCardProps) {
  const scale = useRef(new Animated.Value(1)).current;
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 3200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 3200, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [shimmer]);

  const shimmerX = shimmer.interpolate({ inputRange: [0, 1], outputRange: [-120, 280] });
  const shimmerOpacity = shimmer.interpolate({ inputRange: [0, 0.5, 1], outputRange: [0.15, 0.45, 0.15] });

  return (
    <FadeInView delay={delay}>
      <Pressable
        onPress={onPress}
        onPressIn={() => Animated.spring(scale, { toValue: 0.975, friction: 6, useNativeDriver: true }).start()}
        onPressOut={() => Animated.spring(scale, { toValue: 1, friction: 5, useNativeDriver: true }).start()}
      >
        <Animated.View style={[card.outer, { borderColor: `${glow}66`, transform: [{ scale }] }]}>
          <LinearGradient colors={[`${glow}22`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
          <LinearGradient colors={colors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={card.grad}>
            <Animated.View
              pointerEvents="none"
              style={[card.shimmer, { opacity: shimmerOpacity, transform: [{ translateX: shimmerX }, { rotate: "18deg" }] }]}
            />
            <Text style={card.emoji}>{emoji}</Text>
            <View style={{ flex: 1 }}>
              <View style={card.titleRow}>
                <Text style={card.title}>{title}</Text>
                {badge ? (
                  <View style={card.badge}>
                    <Text style={card.badgeText}>{badge}</Text>
                  </View>
                ) : null}
              </View>
              <Text style={card.body}>{body}</Text>
              <View style={card.meta}>
                <Feather name={metaIcon} size={11} color="#ffffffcc" />
                <Text style={card.metaText}>{metaText}</Text>
              </View>
            </View>
            <View style={card.chevron}>
              <Feather name="arrow-right" size={18} color="#fff" />
            </View>
          </LinearGradient>
        </Animated.View>
      </Pressable>
    </FadeInView>
  );
}

type HeroProps = {
  badge: string;
  title: string;
  subtitle: string;
  accent: string;
  style?: StyleProp<ViewStyle>;
};

export function AskHero({ badge, title, subtitle, accent, style }: HeroProps) {
  return (
    <FadeInView delay={0} style={style}>
      <View style={hero.wrap}>
        <LinearGradient colors={[`${accent}28`, "transparent"]} style={hero.glow} pointerEvents="none" />
        <View style={[hero.badge, { backgroundColor: `${accent}18`, borderColor: `${accent}55` }]}>
          <Feather name="sparkles" size={11} color={accent} />
          <Text style={[hero.badgeText, { color: accent }]}>{badge}</Text>
        </View>
        <Text style={hero.title}>{title}</Text>
        <Text style={hero.sub}>{subtitle}</Text>
      </View>
    </FadeInView>
  );
}

type HeaderProps = {
  topPad: number;
  borderColor: string;
  accent: string;
  textColor: string;
  mutedColor: string;
  showBack?: boolean;
  onBack?: () => void;
};

export function AskGlassHeader({
  topPad,
  borderColor,
  accent,
  textColor,
  mutedColor,
  showBack,
  onBack,
}: HeaderProps) {
  return (
    <View style={[hdr.wrap, { paddingTop: topPad + 10, borderBottomColor: borderColor }]}>
      {Platform.OS === "ios" ? (
        <BlurView intensity={52} tint="dark" style={StyleSheet.absoluteFill} />
      ) : (
        <View style={[StyleSheet.absoluteFill, hdr.androidBg]} />
      )}
      <LinearGradient
        colors={[`${accent}30`, "transparent"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={[StyleSheet.absoluteFill, { height: 72 }]}
        pointerEvents="none"
      />
      {showBack ? (
        <Pressable onPress={onBack} hitSlop={12} style={hdr.backBtn}>
          <View style={hdr.backCircle}>
            <Feather name="chevron-left" size={20} color="#fff" />
          </View>
        </Pressable>
      ) : null}
      <View style={hdr.center}>
        <View style={hdr.titleRow}>
          <LinearGradient colors={[accent, "#a78bfa"]} style={hdr.iconGrad}>
            <Feather name="cpu" size={14} color="#fff" />
          </LinearGradient>
          <Text style={[hdr.title, { color: textColor }]}>Cosmic Intelligence</Text>
          <AskLivePulse />
        </View>
        <Text style={[hdr.sub, { color: mutedColor }]}>Multi System Pattern Engine V2.0</Text>
      </View>
    </View>
  );
}

const orb = StyleSheet.create({
  wrap: {
    position: "absolute",
    top: -40,
    right: -30,
    width: 220,
    height: 220,
    borderRadius: 110,
  },
  liveWrap: { width: 10, height: 10, marginLeft: 8, alignItems: "center", justifyContent: "center" },
  liveDot: { width: 7, height: 7, borderRadius: 4 },
  liveRing: {
    position: "absolute",
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 1.5,
  },
});

const card = StyleSheet.create({
  outer: {
    borderRadius: 20,
    borderWidth: 1,
    overflow: "hidden",
    marginBottom: 2,
  },
  grad: {
    paddingHorizontal: 18,
    paddingVertical: 20,
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    overflow: "hidden",
  },
  shimmer: {
    position: "absolute",
    top: -20,
    left: 0,
    width: 80,
    height: 140,
    backgroundColor: "#fff",
  },
  emoji: { fontSize: 38 },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" },
  title: { color: "#fff", fontSize: 18, fontFamily: F.extra, letterSpacing: -0.3 },
  body: { color: "#ffffffd0", fontSize: 12.5, fontFamily: F.semi, lineHeight: 18, marginTop: 5 },
  meta: { flexDirection: "row", alignItems: "center", gap: 5, marginTop: 10 },
  metaText: { color: "#ffffffcc", fontSize: 10.5, fontFamily: F.bold, letterSpacing: 0.2 },
  badge: {
    backgroundColor: "rgba(255,255,255,0.22)",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  badgeText: { color: "#fff", fontSize: 9.5, fontFamily: F.extra, letterSpacing: 0.4 },
  chevron: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.14)",
    alignItems: "center",
    justifyContent: "center",
  },
});

const hero = StyleSheet.create({
  wrap: { gap: 10, marginBottom: 6, overflow: "hidden" },
  glow: {
    position: "absolute",
    top: -20,
    left: -20,
    right: -20,
    height: 100,
    borderRadius: 24,
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 6,
    paddingHorizontal: 11,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: 1,
  },
  badgeText: { fontSize: 11, fontFamily: F.extra, letterSpacing: 0.4 },
  title: {
    color: "#f8fafc",
    fontSize: 26,
    fontFamily: F.extra,
    letterSpacing: -0.6,
    lineHeight: 32,
  },
  sub: {
    color: "rgba(255,255,255,0.62)",
    fontSize: 13.5,
    fontFamily: F.semi,
    lineHeight: 20,
  },
});

const hdr = StyleSheet.create({
  wrap: {
    borderBottomWidth: 1,
    paddingBottom: 14,
    overflow: "hidden",
  },
  androidBg: { backgroundColor: "rgba(6,10,22,0.92)" },
  backBtn: { position: "absolute", left: 14, bottom: 12, zIndex: 2 },
  backCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
    alignItems: "center",
    justifyContent: "center",
  },
  center: { alignItems: "center", gap: 4, paddingHorizontal: 48 },
  titleRow: { flexDirection: "row", alignItems: "center" },
  iconGrad: {
    width: 28,
    height: 28,
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 8,
  },
  title: { fontSize: 16, fontFamily: F.extra, letterSpacing: -0.2 },
  sub: { fontSize: 11, fontFamily: F.semi, letterSpacing: 0.2 },
});
