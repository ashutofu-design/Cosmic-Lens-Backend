import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import Animated, {
  cancelAnimation,
  Easing,
  Extrapolation,
  interpolate,
  runOnJS,
  useAnimatedProps,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
  type SharedValue,
} from "react-native-reanimated";
import { router } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle, Ellipse, G, Line } from "react-native-svg";

import { needsProfileSetup, useUser } from "@/context/UserContext";
import { GalaxyBackground } from "@/components/reveal/GalaxyBackground";

const AnimatedG = Animated.createAnimatedComponent(G);
const AnimatedLine = Animated.createAnimatedComponent(Line);

/** ~9.6s cinematic — calm, mobile-first pacing */
const DURATION_MS = 9600;
const SKIP_AFTER_MS = 4000;
/** Stop before exit-flash range so finale + buttons stay visible */
const PROGRESS_END = 0.92;

/** Rich cosmic palette — higher saturation for mobile OLED */
const C = {
  gold: "#fbbf24",
  goldBright: "#fde047",
  goldDeep: "#f59e0b",
  violet: "#a78bfa",
  violetDeep: "#7c3aed",
  cyan: "#22d3ee",
  blue: "#38bdf8",
  white: "#f8fafc",
} as const;

const HUD_LINES = [
  "Initializing Cosmic Engine…",
  "Mapping Planetary Positions…",
  "Calculating Graha Frequencies…",
  "Generating Vedic Intelligence…",
  "Synchronizing Cosmic Patterns…",
] as const;

const ZODIAC = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"] as const;

const PARTICLES = Array.from({ length: 64 }, (_, i) => ({
  x: ((i * 97) % 100) / 100,
  y: ((i * 53) % 100) / 100,
  s: 1.4 + (i % 5) * 0.55,
  tint: i % 5 === 0 ? C.cyan : i % 3 === 0 ? C.violet : C.goldBright,
  phase: (i * 0.17) % 1,
}));

type RevealLayout = {
  W: number;
  H: number;
  CX: number;
  CY: number;
  ZODIAC_R: number;
  mandalaSize: number;
  scale: number;
  isCompact: boolean;
};

const LayoutCtx = createContext<RevealLayout>({
  W: 390,
  H: 844,
  CX: 195,
  CY: 380,
  ZODIAC_R: 140,
  mandalaSize: 300,
  scale: 1,
  isCompact: false,
});

function useRevealLayout(): RevealLayout {
  return useContext(LayoutCtx);
}

function buildLayout(W: number, H: number, top: number, bottom: number): RevealLayout {
  const short = Math.min(W, H);
  const isCompact = H < 700 || W < 360;
  const contentH = H - top - bottom;
  const CX = W / 2;
  const CY = top + contentH * (isCompact ? 0.4 : 0.42);
  const scale = Math.min(Math.max(short / 390, 0.82), 1.12);
  return {
    W,
    H,
    CX,
    CY,
    ZODIAC_R: short * (isCompact ? 0.34 : 0.36) * scale,
    mandalaSize: short * (isCompact ? 0.76 : 0.8) * scale,
    scale,
    isCompact,
  };
}

type Props = {
  userName?: string;
};

/** Premium post-login cinematic — Vedic × tech, mobile portrait ratio. */
export function PostLoginReveal({ userName }: Props) {
  const insets = useSafeAreaInsets();
  const { profiles, primaryProfileId } = useUser();
  const { width, height } = useWindowDimensions();
  const layout = useMemo(
    () => buildLayout(width, height, insets.top, insets.bottom),
    [width, height, insets.top, insets.bottom],
  );

  const navigatedRef = useRef(false);
  const canSkipRef = useRef(false);
  const progress = useSharedValue(0);
  const holdFinale = useSharedValue(0);
  const drift = useSharedValue(0);
  const twinkle = useSharedValue(0);

  const finishAndGo = useCallback(() => {
    if (navigatedRef.current) return;
    navigatedRef.current = true;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    if (needsProfileSetup(profiles, primaryProfileId)) {
      router.replace("/onboarding");
    } else {
      router.replace("/(tabs)");
    }
  }, [profiles, primaryProfileId]);

  const skip = () => {
    if (!canSkipRef.current || navigatedRef.current) return;
    cancelAnimation(progress);
    runOnJS(finishAndGo)();
  };

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    const schedule = (fn: () => void, ms: number) => {
      timers.push(setTimeout(fn, ms));
    };

    canSkipRef.current = false;
    holdFinale.value = 0;
    cancelAnimation(progress);
    progress.value = 0;

    schedule(() => { canSkipRef.current = true; }, SKIP_AFTER_MS);

    progress.value = withTiming(PROGRESS_END, {
      duration: DURATION_MS,
      easing: Easing.bezier(0.16, 0.04, 0.12, 1),
    }, (ok) => { if (ok) runOnJS(finishAndGo)(); });

    /** One full drift cycle ~100s — planets glide very slowly */
    drift.value = withRepeat(
      withTiming(1, { duration: 100000, easing: Easing.linear }),
      -1,
      false,
    );
    twinkle.value = withRepeat(
      withTiming(1, { duration: 2600, easing: Easing.inOut(Easing.sin) }),
      -1,
      true,
    );

    schedule(() => {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    }, 900);
    schedule(() => {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    }, 4200);
    schedule(() => {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    }, 8200);

    return () => {
      timers.forEach(clearTimeout);
      cancelAnimation(progress);
    };
  }, [drift, finishAndGo, holdFinale, progress, twinkle]);

  const vignetteStyle = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0, 0.1], [1, 0.88], Extrapolation.CLAMP),
  }));

  const exitStyle = useAnimatedStyle(() => ({
    opacity: holdFinale.value > 0
      ? 0
      : interpolate(progress.value, [0.95, 1], [0, 1], Extrapolation.CLAMP),
  }));

  const trackWidth = layout.W - 96;

  const progressBarStyle = useAnimatedStyle(() => ({
    width: interpolate(progress.value, [0, PROGRESS_END], [0, trackWidth], Extrapolation.CLAMP),
  }));

  return (
    <LayoutCtx.Provider value={layout}>
      <View style={s.root}>
        <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
          <LinearGradient
            colors={["#010108", "#050214", "#0a0520", "#020208"]}
            locations={[0, 0.35, 0.65, 1]}
            style={StyleSheet.absoluteFill}
          />
          <GalaxyBackground
            progress={progress}
            drift={drift}
            twinkle={twinkle}
            width={layout.W}
            height={layout.H}
          />
          <CenterSoftGlow progress={progress} />
          <Animated.View style={[s.vignette, vignetteStyle]} pointerEvents="none">
            <LinearGradient
              colors={["transparent", "rgba(0,0,0,0.25)", "rgba(0,0,0,0.75)"]}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>
        </View>

        <HeadlineBlock progress={progress} holdFinale={holdFinale} />
        <LogoFinale progress={progress} userName={userName} holdFinale={holdFinale} />

        <Animated.View style={[StyleSheet.absoluteFill, s.exitFlash, exitStyle]} pointerEvents="none">
          <LinearGradient
            colors={["rgba(253,224,71,0.18)", "rgba(124,58,237,0.1)", "rgba(0,0,0,0.94)"]}
            style={StyleSheet.absoluteFill}
          />
        </Animated.View>

        <View style={[s.progressTrack, { bottom: insets.bottom + 42 }]}>
          <Animated.View style={[{ height: "100%", overflow: "hidden", borderRadius: 1 }, progressBarStyle]}>
            <LinearGradient
              colors={[C.goldDeep, C.goldBright, C.gold]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>
        </View>

        <View style={[s.controlsLayer, { paddingBottom: insets.bottom + 14 }]} pointerEvents="box-none">
          <Pressable onPress={skip} hitSlop={12} style={s.skipTap}>
            <Text style={s.skip}>Skip animation</Text>
          </Pressable>
        </View>
      </View>
    </LayoutCtx.Provider>
  );
}

function LightBeams({ progress, spin }: { progress: SharedValue<number>; spin: SharedValue<number> }) {
  const { W, H, CX, CY } = useRevealLayout();
  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.06, 0.22, 0.7, 0.82], [0, 0.55, 0.35, 0], Extrapolation.CLAMP),
    transform: [{ rotate: `${spin.value * 360}deg` }],
  }));

  return (
    <Animated.View
      style={[{ position: "absolute", left: CX - W, top: CY - H, width: W * 2, height: H * 2 }, style]}
      pointerEvents="none"
    >
      {Array.from({ length: 8 }, (_, i) => {
        const deg = (i / 8) * 360;
        return (
          <LinearGradient
            key={i}
            colors={["transparent", "rgba(251,191,36,0.18)", "transparent"]}
            start={{ x: 0, y: 0.5 }}
            end={{ x: 1, y: 0.5 }}
            style={{
              position: "absolute",
              left: W * 0.5,
              top: H * 0.5,
              width: W * 0.95,
              height: 3,
              transform: [{ rotate: `${deg}deg` }, { translateX: -W * 0.1 }],
            }}
          />
        );
      })}
    </Animated.View>
  );
}

function NebulaLayer({ progress }: { progress: SharedValue<number> }) {
  const { W, H, CX, CY } = useRevealLayout();
  const orbs = [
    { dx: -0.28, dy: -0.18, c: ["rgba(124,58,237,0.72)", "rgba(124,58,237,0)"] as const, r: W * 0.58 },
    { dx: 0.24, dy: 0.1, c: ["rgba(245,158,11,0.55)", "rgba(245,158,11,0)"] as const, r: W * 0.52 },
    { dx: 0, dy: 0.06, c: ["rgba(34,211,238,0.35)", "rgba(34,211,238,0)"] as const, r: W * 0.65 },
  ];

  return (
    <>
      {orbs.map((o, i) => (
        <NebulaOrb key={i} cx={CX + o.dx * W} cy={CY + o.dy * H} radius={o.r} colors={o.c} progress={progress} delay={i * 0.04} />
      ))}
    </>
  );
}

function NebulaOrb({
  cx, cy, radius, colors, progress, delay,
}: {
  cx: number; cy: number; radius: number;
  colors: readonly [string, string]; progress: SharedValue<number>; delay: number;
}) {
  const style = useAnimatedStyle(() => ({
    position: "absolute",
    left: cx - radius,
    top: cy - radius,
    width: radius * 2,
    height: radius * 2,
    borderRadius: radius,
    opacity: interpolate(progress.value, [0.02 + delay, 0.2 + delay, 0.75, 0.9], [0, 1, 0.65, 0.15], Extrapolation.CLAMP),
    transform: [
      { scale: interpolate(progress.value, [0.02 + delay, 0.25], [0.6, 1.05], Extrapolation.CLAMP) },
    ],
  }));

  return (
    <Animated.View style={style} pointerEvents="none">
      <LinearGradient colors={[...colors]} style={StyleSheet.absoluteFill} start={{ x: 0.3, y: 0.2 }} end={{ x: 0.8, y: 0.9 }} />
    </Animated.View>
  );
}

function FilmGrain({ progress }: { progress: SharedValue<number> }) {
  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.05, 0.2, 0.9, 1], [0, 0.04, 0.03, 0], Extrapolation.CLAMP),
  }));
  return (
    <Animated.View style={[StyleSheet.absoluteFill, s.grain, style]} pointerEvents="none" />
  );
}

function AmbientParticles({ progress, pulse }: { progress: SharedValue<number>; pulse: SharedValue<number> }) {
  return (
    <>
      {PARTICLES.map((p, i) => (
        <Particle key={i} {...p} progress={progress} pulse={pulse} />
      ))}
    </>
  );
}

function Particle({
  x, y, size, tint, phase, progress, pulse,
}: {
  x: number; y: number; size: number; tint: string; phase: number;
  progress: SharedValue<number>; pulse: SharedValue<number>;
}) {
  const { W, H } = useRevealLayout();
  const style = useAnimatedStyle(() => {
    const twinkle = 0.35 + ((pulse.value + phase) % 1) * 0.65;
    return {
      position: "absolute",
      left: x * W,
      top: y * H,
      width: size,
      height: size,
      borderRadius: size,
      backgroundColor: tint,
      opacity:
        interpolate(progress.value, [0.03 + phase * 0.08, 0.28 + phase * 0.06], [0, 0.95], Extrapolation.CLAMP) *
        twinkle,
    };
  });
  return <Animated.View style={style} />;
}

function OuterGlowRing({ progress, spin }: { progress: SharedValue<number>; spin: SharedValue<number> }) {
  const { CX, CY, mandalaSize, scale } = useRevealLayout();
  const size = mandalaSize * 1.18;
  const style = useAnimatedStyle(() => ({
    position: "absolute",
    left: CX - size / 2,
    top: CY - size / 2,
    width: size,
    height: size,
    borderRadius: size / 2,
    borderWidth: 1.5 * scale,
    borderColor: "rgba(251,191,36,0.45)",
    shadowColor: C.gold,
    shadowOpacity: 0.45,
    shadowRadius: 18,
    elevation: 8,
    opacity: interpolate(progress.value, [0.08, 0.22, 0.7, 0.82], [0, 0.95, 0.7, 0.2], Extrapolation.CLAMP),
    transform: [
      { rotate: `${-spin.value * 360}deg` },
      { scale: interpolate(progress.value, [0.1, 0.3], [0.85, 1], Extrapolation.CLAMP) },
    ],
  }));
  return <Animated.View style={style} pointerEvents="none" />;
}

function MandalaLayer({ progress, spin }: { progress: SharedValue<number>; spin: SharedValue<number> }) {
  const { CX, CY, mandalaSize } = useRevealLayout();
  const wrapStyle = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.1, 0.28, 0.62, 0.72], [0, 0.92, 0.7, 0], Extrapolation.CLAMP),
    transform: [
      { scale: interpolate(progress.value, [0.1, 0.35], [0.15, 1], Extrapolation.CLAMP) },
      { rotate: `${spin.value * 360}deg` },
    ],
  }));

  const ringProps = useAnimatedProps(() => ({
    opacity: interpolate(progress.value, [0.12, 0.32], [0, 0.9], Extrapolation.CLAMP),
  }));

  const size = mandalaSize;

  return (
    <Animated.View style={[{ position: "absolute", width: size, height: size, left: CX - size / 2, top: CY - size / 2 }, wrapStyle]} pointerEvents="none">
      <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <AnimatedG animatedProps={ringProps}>
          {[0.18, 0.28, 0.38, 0.48].map((r, i) => (
            <Circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={size * r}
              stroke={i % 2 === 0 ? "rgba(251,191,36,0.62)" : "rgba(167,139,250,0.52)"}
              strokeWidth={i < 2 ? 1.1 : 1.6}
              strokeDasharray={i === 3 ? "3 7" : "2 5"}
              fill="none"
            />
          ))}
          {Array.from({ length: 24 }, (_, i) => {
            const a = (i / 24) * Math.PI * 2;
            const r1 = size * 0.1;
            const r2 = size * (i % 2 === 0 ? 0.44 : 0.36);
            const cx = size / 2;
            const cy = size / 2;
            return (
              <Line
                key={`petal-${i}`}
                x1={cx + Math.cos(a) * r1}
                y1={cy + Math.sin(a) * r1}
                x2={cx + Math.cos(a) * r2}
                y2={cy + Math.sin(a) * r2}
                stroke={i % 3 === 0 ? "rgba(253,224,71,0.5)" : "rgba(167,139,250,0.38)"}
                strokeWidth={1}
              />
            );
          })}
          <Circle cx={size / 2} cy={size / 2} r={size * 0.08} stroke="rgba(253,224,71,0.85)" strokeWidth={1.4} fill="rgba(251,191,36,0.18)" />
        </AnimatedG>
      </Svg>
    </Animated.View>
  );
}

function CircuitLayer({ progress }: { progress: SharedValue<number> }) {
  const { W, H, CX, CY } = useRevealLayout();
  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.14, 0.32, 0.65, 0.74], [0, 0.9, 0.65, 0.2], Extrapolation.CLAMP),
  }));

  const lineProps = useAnimatedProps(() => ({
    strokeOpacity: interpolate(progress.value, [0.16, 0.38], [0, 0.75], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, style]} pointerEvents="none">
      <Svg width={W} height={H}>
        <AnimatedG animatedProps={lineProps}>
          {Array.from({ length: 12 }, (_, i) => {
            const a = (i / 12) * Math.PI * 2 + 0.15;
            return (
              <AnimatedLine
                key={i}
                x1={CX}
                y1={CY}
                x2={CX + Math.cos(a) * W * 0.4}
                y2={CY + Math.sin(a) * H * 0.22}
                stroke={i % 2 === 0 ? C.blue : C.violet}
                strokeWidth={1}
              />
            );
          })}
          <Circle cx={CX} cy={CY} r={Math.min(W, H) * 0.36} stroke="rgba(56,189,248,0.45)" strokeWidth={0.9} fill="none" strokeDasharray="4 10" />
          <Circle cx={CX} cy={CY} r={Math.min(W, H) * 0.28} stroke="rgba(251,191,36,0.38)" strokeWidth={0.8} fill="none" strokeDasharray="2 8" />
        </AnimatedG>
      </Svg>
    </Animated.View>
  );
}

function BinduCore({ progress, pulse }: { progress: SharedValue<number>; pulse: SharedValue<number> }) {
  const { CX, CY, scale } = useRevealLayout();
  const r = 11 * scale;
  const style = useAnimatedStyle(() => {
    const grow = interpolate(progress.value, [0, 0.14, 0.32, 0.68], [0, 1, 1.12, 0.35], Extrapolation.CLAMP);
    const glow = 0.5 + pulse.value * 0.5;
    return {
      position: "absolute",
      left: CX - r,
      top: CY - r,
      width: r * 2,
      height: r * 2,
      opacity: interpolate(progress.value, [0, 0.06, 0.65, 0.76], [0, 1, 1, 0], Extrapolation.CLAMP),
      transform: [{ scale: grow }],
      shadowOpacity: glow,
    };
  });

  const haloStyle = useAnimatedStyle(() => ({
    position: "absolute",
    left: CX - r * 3.2,
    top: CY - r * 3.2,
    width: r * 6.4,
    height: r * 6.4,
    borderRadius: r * 3.2,
    backgroundColor: "rgba(251,191,36,0.22)",
    opacity: (0.4 + pulse.value * 0.5) * interpolate(progress.value, [0, 0.1, 0.6, 0.72], [0, 1, 1, 0], Extrapolation.CLAMP),
    transform: [{ scale: 1 + pulse.value * 0.15 }],
  }));

  const halo2Style = useAnimatedStyle(() => ({
    position: "absolute",
    left: CX - r * 5,
    top: CY - r * 5,
    width: r * 10,
    height: r * 10,
    borderRadius: r * 5,
    borderWidth: 1,
    borderColor: "rgba(167,139,250,0.45)",
    opacity: interpolate(progress.value, [0.08, 0.2, 0.55, 0.68], [0, 0.6, 0.35, 0], Extrapolation.CLAMP),
  }));

  return (
    <>
      <Animated.View style={halo2Style} pointerEvents="none" />
      <Animated.View style={haloStyle} pointerEvents="none" />
      <Animated.View style={[style, { shadowColor: "#fbbf24", shadowRadius: 28 * scale, shadowOffset: { width: 0, height: 0 }, elevation: 14 }]} pointerEvents="none">
        <LinearGradient colors={["#ffffff", "#fde047", "#f59e0b", "#b45309"]} style={{ width: r * 2, height: r * 2, borderRadius: r }} />
      </Animated.View>
    </>
  );
}

function HeroGlow({ progress, pulse }: { progress: SharedValue<number>; pulse: SharedValue<number> }) {
  const { CX, CY, scale } = useRevealLayout();
  const size = 200 * scale;
  const style = useAnimatedStyle(() => ({
    position: "absolute",
    left: CX - size / 2,
    top: CY - size / 2 - 40 * scale,
    width: size,
    height: size,
    borderRadius: size / 2,
    opacity:
      interpolate(progress.value, [0.26, 0.38, 0.88, 0.92], [0, 0.75, 0.65, 0.5], Extrapolation.CLAMP) *
      (0.7 + pulse.value * 0.3),
    transform: [{ scale: 1 + pulse.value * 0.08 }],
  }));

  return (
    <Animated.View style={style} pointerEvents="none">
      <LinearGradient
        colors={["rgba(251,191,36,0.35)", "rgba(124,58,237,0.2)", "transparent"]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      />
    </Animated.View>
  );
}

/** Hero title — both lines stay visible; only gentle dim when logo appears */
function HeadlineBlock({
  progress,
  holdFinale,
}: {
  progress: SharedValue<number>;
  holdFinale: SharedValue<number>;
}) {
  const { CY, scale, isCompact, W } = useRevealLayout();

  const blockStyle = useAnimatedStyle(() => {
    const enter = interpolate(progress.value, [0.26, 0.38], [0, 1], Extrapolation.CLAMP);
    const dimForLogo = holdFinale.value > 0
      ? 1
      : interpolate(progress.value, [0.8, 0.88], [1, 0.92], Extrapolation.CLAMP);
    return {
      opacity: enter * dimForLogo,
      transform: [{ translateY: interpolate(progress.value, [0.26, 0.4], [32, 0], Extrapolation.CLAMP) }],
    };
  });

  const meetsStyle = useAnimatedStyle(() => {
    const enter = interpolate(progress.value, [0.38, 0.5], [0, 1], Extrapolation.CLAMP);
    const dimForLogo = holdFinale.value > 0
      ? 1
      : interpolate(progress.value, [0.8, 0.88], [1, 0.92], Extrapolation.CLAMP);
    return {
      opacity: enter * dimForLogo,
      transform: [{ translateY: interpolate(progress.value, [0.38, 0.52], [20, 0], Extrapolation.CLAMP) }],
    };
  });

  const fontSize = (isCompact ? 24 : 28) * scale;
  const letter = (isCompact ? 5 : 7) * scale;
  const padH = Math.max(18, W * 0.06);

  return (
    <Animated.View
      style={[s.headlineWrap, { top: CY - 100 * scale, paddingHorizontal: padH }, blockStyle]}
      pointerEvents="none"
    >
      <Text style={[s.headline, { fontSize, letterSpacing: letter }]}>WHEN VEDIC</Text>
      <Animated.View style={meetsStyle}>
        <Text style={[s.headline, s.headlineAccent, { fontSize: fontSize + 4, letterSpacing: letter + 1, marginTop: 8 }]}>
          MEETS TECH
        </Text>
      </Animated.View>
    </Animated.View>
  );
}

function CenterSoftGlow({ progress }: { progress: SharedValue<number> }) {
  const { CX, CY, scale } = useRevealLayout();
  const size = 220 * scale;
  const style = useAnimatedStyle(() => ({
    position: "absolute",
    left: CX - size / 2,
    top: CY - size / 2,
    width: size,
    height: size,
    borderRadius: size / 2,
    opacity: interpolate(progress.value, [0.1, 0.28], [0, 0.5], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View style={style} pointerEvents="none">
      <LinearGradient
        colors={["rgba(124,58,237,0.2)", "rgba(251,191,36,0.12)", "transparent"]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0.5, y: 0.5 }}
        end={{ x: 1, y: 1 }}
      />
    </Animated.View>
  );
}

function HudPanel({ progress, shimmer }: { progress: SharedValue<number>; shimmer: SharedValue<number> }) {
  const { CY, scale, W, isCompact } = useRevealLayout();
  const padH = Math.max(20, W * 0.07);

  const frameStyle = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.48, 0.58, 0.82, 0.9], [0, 1, 1, 0], Extrapolation.CLAMP),
    transform: [{ scale: interpolate(progress.value, [0.48, 0.6], [0.94, 1], Extrapolation.CLAMP) }],
  }));

  const sweepStyle = useAnimatedStyle(() => ({
    position: "absolute",
    top: 0,
    bottom: 0,
    width: 80,
    left: interpolate(shimmer.value, [0, 1], [-80, W - padH * 2 + 80], Extrapolation.CLAMP),
    opacity: 0.35,
  }));

  return (
    <Animated.View style={[s.hudFrame, { left: padH, right: padH, top: CY + 28 * scale, paddingVertical: 18 * scale }, frameStyle]} pointerEvents="none">
      <Animated.View style={sweepStyle} pointerEvents="none">
        <LinearGradient colors={["transparent", "rgba(251,191,36,0.25)", "transparent"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={StyleSheet.absoluteFill} />
      </Animated.View>
      <View style={s.hudCornerTL} />
      <View style={s.hudCornerTR} />
      <View style={s.hudCornerBL} />
      <View style={s.hudCornerBR} />
      <Text style={[s.hudTitle, { fontSize: (isCompact ? 8 : 9) * scale }]}>COSMIC ENGINE</Text>
      {HUD_LINES.map((line, i) => (
        <HudLine key={line} text={line} index={i} progress={progress} />
      ))}
    </Animated.View>
  );
}

function HudLine({ text, index, progress }: { text: string; index: number; progress: SharedValue<number> }) {
  const start = 0.52 + index * 0.038;
  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [start, start + 0.032], [0, 1], Extrapolation.CLAMP),
    transform: [{ translateX: interpolate(progress.value, [start, start + 0.032], [-14, 0], Extrapolation.CLAMP) }],
  }));

  return (
    <Animated.View style={[s.hudRow, style]}>
      <View style={s.hudDot} />
      <Text style={s.hudText}>{text}</Text>
    </Animated.View>
  );
}

function ZodiacRing({ progress }: { progress: SharedValue<number> }) {
  const { W, H, CX, CY, ZODIAC_R } = useRevealLayout();
  const ringStyle = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.7, 0.78, 0.92, 0.97], [0, 1, 1, 0], Extrapolation.CLAMP),
  }));

  const lineProps = useAnimatedProps(() => ({
    strokeOpacity: interpolate(progress.value, [0.74, 0.88], [0, 0.38], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, ringStyle]} pointerEvents="none">
      <Svg width={W} height={H} style={StyleSheet.absoluteFill}>
        <AnimatedG animatedProps={lineProps}>
          {ZODIAC.map((_, i) => {
            const a1 = (i / 12) * Math.PI * 2 - Math.PI / 2;
            const a2 = (((i + 1) % 12) / 12) * Math.PI * 2 - Math.PI / 2;
            return (
              <Line
                key={`link-${i}`}
                x1={CX + Math.cos(a1) * ZODIAC_R}
                y1={CY + Math.sin(a1) * ZODIAC_R}
                x2={CX + Math.cos(a2) * ZODIAC_R}
                y2={CY + Math.sin(a2) * ZODIAC_R}
                stroke="rgba(251,191,36,0.38)"
                strokeWidth={0.9}
              />
            );
          })}
          <Circle cx={CX} cy={CY} r={ZODIAC_R} stroke="rgba(251,191,36,0.15)" strokeWidth={0.5} fill="none" strokeDasharray="2 6" />
        </AnimatedG>
      </Svg>
      {ZODIAC.map((sym, i) => (
        <ZodiacGlyph key={sym} symbol={sym} index={i} progress={progress} />
      ))}
    </Animated.View>
  );
}

function ZodiacGlyph({
  symbol, index, progress,
}: {
  symbol: string; index: number; progress: SharedValue<number>;
}) {
  const { CX, CY, ZODIAC_R, scale } = useRevealLayout();
  const a = (index / 12) * Math.PI * 2 - Math.PI / 2;
  const box = 30 * scale;
  const x = CX + Math.cos(a) * ZODIAC_R - box / 2;
  const y = CY + Math.sin(a) * ZODIAC_R - box / 2;
  const start = 0.72 + index * 0.012;

  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [start, start + 0.028], [0, 1], Extrapolation.CLAMP),
    transform: [
      { scale: interpolate(progress.value, [start, start + 0.028], [0.5, 1], Extrapolation.CLAMP) },
    ],
  }));

  return (
    <Animated.View style={[s.zodiacGlyphBox, { left: x, top: y, width: box, height: box }, style]}>
      <View style={[s.zodiacGlyphRing, { width: box - 4, height: box - 4, borderRadius: (box - 4) / 2 }]}>
        <Text style={[s.zodiacGlyph, { fontSize: 17 * scale }]}>{symbol}</Text>
      </View>
    </Animated.View>
  );
}

function LogoFinale({
  progress, userName, holdFinale,
}: {
  progress: SharedValue<number>;
  userName?: string;
  holdFinale: SharedValue<number>;
}) {
  const { CY, scale, isCompact } = useRevealLayout();
  const logoStyle = useAnimatedStyle(() => ({
    opacity: holdFinale.value > 0
      ? 1
      : interpolate(progress.value, [0.55, 0.65, 0.9, 0.94], [0, 1, 1, 0], Extrapolation.CLAMP),
    transform: [
      {
        scale: holdFinale.value > 0
          ? 1
          : interpolate(progress.value, [0.55, 0.68], [0.8, 1], Extrapolation.CLAMP),
      },
    ],
  }));

  const textStyle = useAnimatedStyle(() => ({
    opacity: holdFinale.value > 0
      ? 1
      : interpolate(progress.value, [0.62, 0.72, 0.9, 0.94], [0, 1, 1, 0], Extrapolation.CLAMP),
    transform: [{
      translateY: holdFinale.value > 0
        ? 0
        : interpolate(progress.value, [0.62, 0.7], [12, 0], Extrapolation.CLAMP),
    }],
  }));

  const logoSz = 76 * scale;
  const welcome = userName?.trim() ? `Welcome, ${userName.trim()}` : undefined;

  const finaleTop = useAnimatedStyle(() => ({
    top: holdFinale.value > 0 ? CY + 8 * scale : CY - 28 * scale,
  }));

  return (
    <Animated.View style={[s.finaleWrap, finaleTop]} pointerEvents="none">
      <Animated.View style={[s.logoBlock, logoStyle]}>
        <Svg width={logoSz} height={logoSz} viewBox="0 0 38 38">
          <Circle cx={19} cy={19} r={17} stroke="#f59e0b" strokeWidth={1.2} strokeOpacity={0.55} strokeDasharray="4 3" fill="none" />
          <Circle cx={19} cy={19} r={7} fill="#f59e0b" />
          <Ellipse cx={19} cy={19} rx={13} ry={4} stroke="#a78bfa" strokeWidth={1.1} strokeOpacity={0.8} fill="none" />
        </Svg>
      </Animated.View>
      <Animated.View style={textStyle}>
        {welcome ? (
          <Text style={[s.welcome, { fontSize: (isCompact ? 13 : 14) * scale }]}>{welcome}</Text>
        ) : null}
        <Text style={[s.brand, { fontSize: (isCompact ? 22 : 26) * scale, letterSpacing: 4 * scale }]}>COSMIC LENS</Text>
        <Text style={[s.tagline, { fontSize: (isCompact ? 11 : 12) * scale }]}>Ancient Wisdom · Modern Intelligence</Text>
      </Animated.View>
    </Animated.View>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: "#000" },
  vignette: { ...StyleSheet.absoluteFillObject },
  grain: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(255,255,255,0.02)",
    opacity: 0.03,
  },
  headlineWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    alignItems: "center",
    zIndex: 22,
  },
  headlineCard: {
    width: "100%",
    paddingVertical: 18,
    paddingHorizontal: 20,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
  },
  headlineRule: {
    width: 48,
    height: 2,
    borderRadius: 1,
    backgroundColor: "rgba(251,191,36,0.75)",
    marginBottom: 12,
    shadowColor: "#fbbf24",
    shadowOpacity: 0.8,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 0 },
  },
  headline: {
    color: "#ffffff",
    fontFamily: "Nunito_700Bold",
    textShadowColor: "rgba(251,191,36,0.85)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 22,
  },
  headlineAccent: {
    marginTop: 10,
    color: "#fde047",
    textShadowColor: "rgba(253,224,71,0.9)",
    textShadowRadius: 20,
  },
  hudFrame: {
    position: "absolute",
    borderWidth: 1,
    borderColor: "rgba(56,189,248,0.45)",
    backgroundColor: "rgba(8,12,28,0.78)",
    borderRadius: 6,
    overflow: "hidden",
  },
  hudCornerTL: {
    position: "absolute", left: -1, top: -1, width: 16, height: 16,
    borderTopWidth: 2, borderLeftWidth: 2, borderColor: "rgba(251,191,36,0.75)",
  },
  hudCornerTR: {
    position: "absolute", right: -1, top: -1, width: 16, height: 16,
    borderTopWidth: 2, borderRightWidth: 2, borderColor: "rgba(251,191,36,0.75)",
  },
  hudCornerBL: {
    position: "absolute", left: -1, bottom: -1, width: 16, height: 16,
    borderBottomWidth: 2, borderLeftWidth: 2, borderColor: "rgba(251,191,36,0.75)",
  },
  hudCornerBR: {
    position: "absolute", right: -1, bottom: -1, width: 16, height: 16,
    borderBottomWidth: 2, borderRightWidth: 2, borderColor: "rgba(251,191,36,0.75)",
  },
  hudTitle: {
    color: "rgba(96,165,250,0.9)",
    fontFamily: "Nunito_700Bold",
    letterSpacing: 3,
    marginBottom: 12,
  },
  hudRow: { flexDirection: "row", alignItems: "center", gap: 10, marginTop: 6 },
  hudDot: { width: 5, height: 5, borderRadius: 2.5, backgroundColor: "#fbbf24" },
  hudText: {
    color: "rgba(226,232,240,0.94)",
    fontSize: 13,
    fontFamily: "Nunito_500Medium",
    letterSpacing: 0.4,
  },
  zodiacGlyphBox: {
    position: "absolute",
    alignItems: "center",
    justifyContent: "center",
  },
  zodiacGlyphRing: {
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.25)",
    backgroundColor: "rgba(3,7,18,0.55)",
  },
  zodiacGlyph: {
    textAlign: "center",
    color: "#fde68a",
    textShadowColor: "rgba(251,191,36,0.85)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10,
  },
  finaleWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    alignItems: "center",
  },
  logoPulse: {
    position: "absolute",
    backgroundColor: "rgba(245,158,11,0.12)",
  },
  logoBlock: { marginBottom: 18 },
  welcome: {
    color: "rgba(253,224,71,0.9)",
    fontFamily: "Nunito_600SemiBold",
    letterSpacing: 0.8,
    textAlign: "center",
    marginBottom: 10,
  },
  brand: {
    color: "#fff",
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
    textShadowColor: "rgba(245,158,11,0.55)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 18,
  },
  tagline: {
    marginTop: 10,
    color: "rgba(148,163,184,0.95)",
    fontFamily: "Nunito_500Medium",
    letterSpacing: 1.4,
    textAlign: "center",
  },
  exitFlash: { backgroundColor: "#000" },
  progressTrack: {
    position: "absolute",
    left: 48,
    right: 48,
    height: 2,
    borderRadius: 1,
    backgroundColor: "rgba(255,255,255,0.08)",
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    borderRadius: 1,
  },
  topBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 50,
    alignItems: "center",
  },
  replayBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: "rgba(251,191,36,0.45)",
    backgroundColor: "rgba(15,23,42,0.75)",
  },
  replayText: {
    color: "#fde68a",
    fontSize: 13,
    fontFamily: "Nunito_600SemiBold",
    letterSpacing: 0.3,
  },
  skipWrap: { position: "absolute", bottom: 0, left: 0, right: 0, alignItems: "center", zIndex: 20 },
  skip: {
    color: "rgba(100,116,139,0.8)",
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
    letterSpacing: 1.2,
  },
  continueBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 22,
    paddingVertical: 13,
    borderRadius: 28,
    backgroundColor: "#f59e0b",
  },
  continueText: {
    color: "#0f172a",
    fontSize: 14,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.4,
  },
});
