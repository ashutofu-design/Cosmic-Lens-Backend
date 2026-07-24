import AsyncStorage from "@react-native-async-storage/async-storage";
import * as Haptics from "expo-haptics";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  LayoutAnimation,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  UIManager,
  View,
} from "react-native";
import Animated, {
  cancelAnimation,
  Easing,
  Extrapolation,
  interpolate,
  type SharedValue,
  useAnimatedProps,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withSequence,
  withSpring,
  withTiming,
} from "react-native-reanimated";
import Svg, { Circle, Defs, RadialGradient, Stop } from "react-native-svg";

import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { playJaapCompleteSound, playJaapMalaSound, preloadJaapSounds } from "@/lib/jaapSounds";
import { useScreenLayout } from "@/lib/screenLayout";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

if (Platform.OS === "android" && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

const STORAGE_KEY = "cosmic.naamJaap.v1";

/** Sandalwood / rudraksha counter palette — feels physical, not “app purple”. */
const WOOD = {
  deep: "#2a1810",
  mid: "#5c3318",
  warm: "#c47a3a",
  gold: "#e8b86d",
  glow: "#f0c27a",
  bead: "#8b4513",
  beadLit: "#f6c453",
  ink: "#1a0f0a",
};

const PRESETS = [
  { id: "ram", label: "Ram Ram", text: "Ram Ram" },
  { id: "shiv", label: "Om Namah Shivaya", text: "Om Namah Shivaya" },
  { id: "krishna", label: "Hare Krishna", text: "Hare Krishna Hare Ram" },
  { id: "radhe", label: "Radhe Radhe", text: "Radhe Radhe" },
  { id: "jaiRam", label: "Jai Shri Ram", text: "Jai Shri Ram" },
  { id: "custom", label: "Custom", text: "" },
] as const;

/** 0 = unlimited (no finish target). */
const TARGETS = [11, 21, 54, 108, 1008, 0] as const;
const BEAD_DOTS = 36;

type SavedState = {
  presetId: string;
  customText: string;
  target: number;
  count: number;
  dayKey: string;
  elapsedSec: number;
};

/** Dial + type scale that fits any phone ratio (SE → Pro Max → fold). */
function useJaapMetrics() {
  const L = useScreenLayout();
  const { width, height, ph, compact, narrow, rs } = L;

  return useMemo(() => {
    const aspect = height / Math.max(width, 1);
    const short = height < 720 || aspect < 1.75;
    const veryShort = height < 640 || aspect < 1.55;
    const contentW = Math.max(260, width - ph * 2);

    // Leave room for mantra + controls + setup toggle inside the tab body.
    const dialBudgetH = height * (veryShort ? 0.30 : short ? 0.34 : 0.38);
    const dialBudgetW = contentW * (narrow ? 0.82 : 0.78);
    const dialMax = compact ? 232 : narrow ? 268 : 300;
    const dialMin = veryShort ? 156 : compact ? 172 : 196;

    const dialSize = Math.round(
      Math.max(dialMin, Math.min(dialMax, dialBudgetW, dialBudgetH)),
    );

    const stroke = Math.max(8, Math.round(dialSize * 0.05));
    const bead = Math.max(5, Math.round(dialSize * 0.028));
    const rim = Math.max(3, Math.round(dialSize * 0.018));
    const countFs = Math.round(dialSize * (compact ? 0.22 : 0.215));
    const mantraFs = rs(veryShort ? 18 : compact ? 20 : short ? 22 : 26);
    const gap = rs(veryShort ? 8 : compact ? 10 : 12);
    const glowPad = Math.round(dialSize * 0.06); // keep glow inside screen

    return {
      ...L,
      short,
      veryShort,
      dialSize,
      stroke,
      bead,
      rim,
      countFs,
      mantraFs,
      gap,
      glowPad,
      contentW,
    };
  }, [L, width, height, ph, compact, narrow, rs]);
}

function todayKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatElapsed(sec: number) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function RippleRing({
  progress,
  size,
}: {
  progress: SharedValue<number>;
  size: number;
}) {
  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0, 0.2, 1], [0.55, 0.35, 0], Extrapolation.CLAMP),
    transform: [
      {
        scale: interpolate(progress.value, [0, 1], [0.72, 1.55], Extrapolation.CLAMP),
      },
    ],
  }));
  return (
    <Animated.View
      pointerEvents="none"
      style={[
        {
          position: "absolute",
          width: size,
          height: size,
          borderRadius: size / 2,
          borderWidth: 2,
          borderColor: WOOD.gold,
        },
        style,
      ]}
    />
  );
}

export function NaamJaapTimer() {
  const C = useC();
  const t = useT();
  const M = useJaapMetrics();
  const {
    rs, compact, dialSize, stroke, bead, rim, countFs, mantraFs, gap, glowPad, short, veryShort,
  } = M;

  const [presetId, setPresetId] = useState<string>("ram");
  const [customText, setCustomText] = useState("");
  const [target, setTarget] = useState(108);
  const [count, setCount] = useState(0);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [running, setRunning] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [setupOpen, setSetupOpen] = useState(false);
  const [flashMantra, setFlashMantra] = useState(false);

  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const dialScale = useSharedValue(1);
  const countPop = useSharedValue(1);
  const progressSV = useSharedValue(0);
  const glowPulse = useSharedValue(0);
  const rippleA = useSharedValue(1);
  const rippleB = useSharedValue(1);
  const breathe = useSharedValue(0);
  const celebrate = useSharedValue(0);
  const beadRotate = useSharedValue(0);
  const rippleFlip = useRef(false);

  const mantra = useMemo(() => {
    if (presetId === "custom") return customText.trim() || t.pn_jaapCustomPh;
    return PRESETS.find((p) => p.id === presetId)?.text ?? "Ram Ram";
  }, [presetId, customText, t.pn_jaapCustomPh]);

  const unlimited = target === 0;
  /** For unlimited, beads/ring track progress within the current mala (108). */
  const progress = unlimited
    ? (count % 108) / 108
    : Math.min(1, target > 0 ? count / target : 0);
  const done = !unlimited && count >= target && target > 0;
  const malas = Math.floor(count / 108);
  const remaining = unlimited ? 0 : Math.max(0, target - count);

  const radius = (dialSize - stroke) / 2 - Math.round(dialSize * 0.065);
  const circumference = 2 * Math.PI * radius;
  const dialStage = dialSize + glowPad * 2;

  // Hydrate
  // Warm up audio so first complete chime isn't delayed
  useEffect(() => {
    void preloadJaapSounds();
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (!alive || !raw) return;
        const saved = JSON.parse(raw) as SavedState;
        const day = todayKey();
        setPresetId(saved.presetId || "ram");
        setCustomText(saved.customText || "");
        setTarget(
          TARGETS.includes(saved.target as (typeof TARGETS)[number]) ? saved.target : 108,
        );
        if (saved.dayKey === day) {
          setCount(Math.max(0, saved.count || 0));
          setElapsedSec(Math.max(0, saved.elapsedSec || 0));
        }
      } catch {
        /* ignore */
      } finally {
        if (alive) setHydrated(true);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      const payload: SavedState = {
        presetId,
        customText,
        target,
        count,
        dayKey: todayKey(),
        elapsedSec,
      };
      AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(payload)).catch(() => {});
    }, 400);
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, [hydrated, presetId, customText, target, count, elapsedSec]);

  useEffect(() => {
    progressSV.value = withTiming(progress, {
      duration: 420,
      easing: Easing.out(Easing.cubic),
    });
  }, [progress, progressSV]);

  // Soft breathe + bead orbit while session active
  useEffect(() => {
    if (running && !done) {
      glowPulse.value = withRepeat(
        withTiming(1, { duration: 1400, easing: Easing.inOut(Easing.sin) }),
        -1,
        true,
      );
      breathe.value = withRepeat(
        withTiming(1, { duration: 2200, easing: Easing.inOut(Easing.sin) }),
        -1,
        true,
      );
      beadRotate.value = withRepeat(
        withTiming(360, { duration: 48000, easing: Easing.linear }),
        -1,
        false,
      );
    } else {
      cancelAnimation(glowPulse);
      cancelAnimation(breathe);
      cancelAnimation(beadRotate);
      glowPulse.value = withTiming(0, { duration: 400 });
      breathe.value = withTiming(0, { duration: 400 });
    }
  }, [running, done, glowPulse, breathe, beadRotate]);

  useEffect(() => {
    if (!running) {
      if (tickRef.current) clearInterval(tickRef.current);
      tickRef.current = null;
      return;
    }
    tickRef.current = setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [running]);

  const showMantraFlash = useCallback(() => {
    setFlashMantra(true);
    setTimeout(() => setFlashMantra(false), 380);
  }, []);

  const playTapMotion = useCallback(
    (completed: boolean) => {
      dialScale.value = withSequence(
        withTiming(0.92, { duration: 55 }),
        withSpring(1, { damping: 11, stiffness: 320, mass: 0.55 }),
      );
      countPop.value = withSequence(
        withTiming(1.22, { duration: 70 }),
        withSpring(1, { damping: 10, stiffness: 280 }),
      );
      const rip = rippleFlip.current ? rippleB : rippleA;
      rippleFlip.current = !rippleFlip.current;
      rip.value = 0;
      rip.value = withTiming(1, { duration: 620, easing: Easing.out(Easing.quad) });
      showMantraFlash();

      if (completed) {
        celebrate.value = 0;
        celebrate.value = withSequence(
          withTiming(1, { duration: 500, easing: Easing.out(Easing.cubic) }),
          withDelay(900, withTiming(0, { duration: 600 })),
        );
      }
    },
    [dialScale, countPop, rippleA, rippleB, celebrate, showMantraFlash],
  );

  const bump = useCallback(() => {
    if (done) return;
    setCount((c) => {
      const next = c + 1;
      const completed = !unlimited && next >= target;
      const malaHit = next > 0 && next % 108 === 0;

      if (completed) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        void playJaapCompleteSound();
        setRunning(false);
      } else if (malaHit) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        void playJaapMalaSound();
      } else {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
      }
      playTapMotion(completed);
      return next;
    });
    if (!running) setRunning(true);
  }, [done, unlimited, target, running, playTapMotion]);

  const undo = useCallback(() => {
    Haptics.selectionAsync().catch(() => {});
    setCount((c) => Math.max(0, c - 1));
    dialScale.value = withSequence(
      withTiming(0.97, { duration: 60 }),
      withSpring(1, { damping: 14, stiffness: 260 }),
    );
  }, [dialScale]);

  const reset = useCallback(() => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    setCount(0);
    setElapsedSec(0);
    setRunning(false);
    celebrate.value = 0;
    progressSV.value = withTiming(0, { duration: 350 });
  }, [celebrate, progressSV]);

  const dialWrapStyle = useAnimatedStyle(() => ({
    transform: [{ scale: dialScale.value }],
  }));

  const countStyle = useAnimatedStyle(() => ({
    transform: [{ scale: countPop.value }],
  }));

  const glowStyle = useAnimatedStyle(() => ({
    opacity: interpolate(glowPulse.value, [0, 1], [0.18, 0.48]),
    transform: [
      {
        scale: interpolate(glowPulse.value, [0, 1], [1, 1.08]),
      },
    ],
  }));

  const mantraBreathStyle = useAnimatedStyle(() => ({
    opacity: interpolate(breathe.value, [0, 1], [0.72, 1]),
    transform: [
      {
        scale: interpolate(breathe.value, [0, 1], [1, 1.03]),
      },
    ],
  }));

  const celebrateStyle = useAnimatedStyle(() => ({
    opacity: celebrate.value * 0.85,
    transform: [{ scale: interpolate(celebrate.value, [0, 1], [0.6, 1.35]) }],
  }));

  const beadOrbitStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${beadRotate.value}deg` }],
  }));

  const progressProps = useAnimatedProps(() => ({
    strokeDashoffset: circumference * (1 - progressSV.value),
  }));

  const litBeads = Math.round(progress * BEAD_DOTS);

  return (
    <View style={{ width: "100%", maxWidth: 480, alignSelf: "center", gap }}>
      {/* Floating mantra */}
      <Animated.View
        style={[
          { alignItems: "center", paddingHorizontal: rs(4), maxWidth: "100%" },
          mantraBreathStyle,
        ]}
      >
        <Text
          style={[s.kicker, { color: WOOD.gold, fontSize: rs(veryShort ? 9 : 10) }]}
          numberOfLines={1}
          adjustsFontSizeToFit
        >
          {t.pn_jaapTitle}
        </Text>
        <Text
          style={[
            s.mantraHero,
            {
              color: flashMantra ? WOOD.glow : C.text,
              fontSize: mantraFs,
              lineHeight: Math.round(mantraFs * 1.28),
              marginTop: rs(4),
              paddingHorizontal: rs(4),
            },
          ]}
          numberOfLines={2}
          adjustsFontSizeToFit
          minimumFontScale={0.75}
        >
          {mantra}
        </Text>
        <Text
          style={[
            s.metaLine,
            {
              color: C.textMuted,
              fontSize: rs(veryShort ? 10 : 11),
              marginTop: rs(4),
              paddingHorizontal: rs(2),
            },
          ]}
          numberOfLines={2}
        >
          {formatElapsed(elapsedSec)}
          {malas > 0 ? `  ·  ${t.pn_jaapMalasDone.replace("{n}", String(malas))}` : ""}
          {!done && !unlimited
            ? `  ·  ${t.pn_jaapLeft.replace("{n}", String(remaining))}`
            : ""}
          {unlimited ? `  ·  ${t.pn_jaapUnlimited}` : ""}
        </Text>
      </Animated.View>

      {/* Physical dial — clipped stage so glow never overflows phone edges */}
      <View
        style={{
          alignItems: "center",
          justifyContent: "center",
          alignSelf: "center",
          width: dialStage,
          height: dialStage,
          maxWidth: "100%",
          overflow: "hidden",
        }}
      >
        <Animated.View
          pointerEvents="none"
          style={[
            {
              position: "absolute",
              width: dialSize + glowPad,
              height: dialSize + glowPad,
              borderRadius: dialSize,
              backgroundColor: WOOD.warm,
            },
            glowStyle,
          ]}
        />
        <Animated.View
          pointerEvents="none"
          style={[
            {
              position: "absolute",
              width: dialSize * 0.92,
              height: dialSize * 0.92,
              borderRadius: dialSize,
              borderWidth: 2,
              borderColor: WOOD.gold,
            },
            celebrateStyle,
          ]}
        />

        <RippleRing progress={rippleA} size={dialSize} />
        <RippleRing progress={rippleB} size={dialSize} />

        <Animated.View style={dialWrapStyle}>
          <Pressable
            onPress={bump}
            disabled={done}
            accessibilityRole="button"
            accessibilityLabel={t.pn_jaapTap}
            style={({ pressed }) => [
              {
                width: dialSize,
                height: dialSize,
                borderRadius: dialSize / 2,
                alignItems: "center",
                justifyContent: "center",
                opacity: pressed && !done ? 0.96 : 1,
              },
            ]}
          >
            {/* Outer wood rim */}
            <View
              style={{
                ...StyleSheet.absoluteFillObject,
                borderRadius: dialSize / 2,
                backgroundColor: WOOD.mid,
                borderWidth: rim,
                borderColor: WOOD.gold,
                shadowColor: "#000",
                shadowOpacity: 0.45,
                shadowRadius: Math.round(dialSize * 0.06),
                shadowOffset: { width: 0, height: Math.round(dialSize * 0.035) },
                elevation: 14,
              }}
            />
            {/* Inner face */}
            <View
              style={{
                position: "absolute",
                width: dialSize - Math.round(dialSize * 0.1),
                height: dialSize - Math.round(dialSize * 0.1),
                borderRadius: dialSize / 2,
                backgroundColor: WOOD.deep,
                borderWidth: 1,
                borderColor: `${WOOD.gold}55`,
              }}
            />

            {/* Progress ring */}
            <Svg
              width={dialSize}
              height={dialSize}
              style={StyleSheet.absoluteFill}
              pointerEvents="none"
            >
              <Defs>
                <RadialGradient id="faceGlow" cx="50%" cy="40%" r="60%">
                  <Stop offset="0%" stopColor={WOOD.warm} stopOpacity="0.35" />
                  <Stop offset="100%" stopColor={WOOD.deep} stopOpacity="0" />
                </RadialGradient>
              </Defs>
              <Circle
                cx={dialSize / 2}
                cy={dialSize / 2}
                r={dialSize / 2 - Math.round(dialSize * 0.05)}
                fill="url(#faceGlow)"
              />
              <Circle
                cx={dialSize / 2}
                cy={dialSize / 2}
                r={radius}
                stroke={`${WOOD.gold}28`}
                strokeWidth={stroke}
                fill="none"
              />
              <AnimatedCircle
                cx={dialSize / 2}
                cy={dialSize / 2}
                r={radius}
                stroke={done ? "#6ee7a0" : WOOD.glow}
                strokeWidth={stroke}
                fill="none"
                strokeDasharray={`${circumference} ${circumference}`}
                animatedProps={progressProps}
                strokeLinecap="round"
                transform={`rotate(-90 ${dialSize / 2} ${dialSize / 2})`}
              />
            </Svg>

            {/* Bead orbit — lit beads track progress */}
            <Animated.View
              pointerEvents="none"
              style={[
                {
                  position: "absolute",
                  width: dialSize,
                  height: dialSize,
                },
                beadOrbitStyle,
              ]}
            >
              {Array.from({ length: BEAD_DOTS }).map((_, i) => {
                const ang = (i / BEAD_DOTS) * Math.PI * 2 - Math.PI / 2;
                const rOrbit = dialSize / 2 - bead * 1.15;
                const x = dialSize / 2 + Math.cos(ang) * rOrbit - bead / 2;
                const y = dialSize / 2 + Math.sin(ang) * rOrbit - bead / 2;
                const lit = i < litBeads;
                return (
                  <View
                    key={i}
                    style={{
                      position: "absolute",
                      left: x,
                      top: y,
                      width: bead,
                      height: bead,
                      borderRadius: bead / 2,
                      backgroundColor: lit ? WOOD.beadLit : WOOD.bead,
                      opacity: lit ? 1 : 0.45,
                      borderWidth: lit ? 1 : 0,
                      borderColor: WOOD.glow,
                    }}
                  />
                );
              })}
            </Animated.View>

            {/* Count readout */}
            <Animated.View style={[{ alignItems: "center", zIndex: 2, maxWidth: dialSize * 0.7 }, countStyle]}>
              <Text
                style={{
                  fontSize: countFs,
                  fontFamily: "Nunito_700Bold",
                  color: done ? "#6ee7a0" : WOOD.glow,
                  fontVariant: ["tabular-nums"],
                  letterSpacing: -1,
                  textShadowColor: `${WOOD.gold}88`,
                  textShadowRadius: 12,
                  textShadowOffset: { width: 0, height: 0 },
                }}
                numberOfLines={1}
                adjustsFontSizeToFit
                minimumFontScale={0.55}
              >
                {count}
              </Text>
              <Text
                style={{
                  fontSize: rs(veryShort ? 11 : 13),
                  fontFamily: "Nunito_600SemiBold",
                  color: `${WOOD.gold}cc`,
                  marginTop: -2,
                }}
              >
                {unlimited ? "∞" : `/ ${target}`}
              </Text>
              <Text
                style={{
                  marginTop: rs(veryShort ? 6 : 10),
                  fontSize: rs(veryShort ? 9 : 11),
                  fontFamily: "Nunito_700Bold",
                  color: done ? "#6ee7a0" : WOOD.warm,
                  letterSpacing: 1.2,
                }}
                numberOfLines={1}
                adjustsFontSizeToFit
              >
                {done ? t.pn_jaapComplete.toUpperCase() : "TAP · JAAP"}
              </Text>
            </Animated.View>
          </Pressable>
        </Animated.View>
      </View>

      {done ? (
        <Text style={[s.doneLine, { color: "#6ee7a0", fontSize: rs(13), paddingHorizontal: rs(8) }]} numberOfLines={2}>
          {t.pn_jaapDone}
        </Text>
      ) : null}

      {/* Device controls */}
      <View style={[s.controls, { gap: rs(6) }]}>
        <Pressable
          onPress={() => setRunning((r) => !r)}
          style={[
            s.ctrlBtn,
            {
              borderColor: `${WOOD.gold}44`,
              backgroundColor: `${WOOD.mid}99`,
              paddingVertical: rs(short ? 10 : 12),
              minWidth: 0,
            },
          ]}
        >
          <Text
            style={[s.ctrlTxt, { color: WOOD.gold, fontSize: rs(compact ? 11 : 12) }]}
            numberOfLines={1}
            adjustsFontSizeToFit
            minimumFontScale={0.8}
          >
            {running ? `⏸ ${t.pn_jaapPause}` : `▶ ${t.pn_jaapResume}`}
          </Text>
        </Pressable>
        <Pressable
          onPress={undo}
          disabled={count === 0}
          style={[
            s.ctrlBtn,
            {
              borderColor: `${WOOD.gold}44`,
              backgroundColor: `${WOOD.mid}99`,
              opacity: count === 0 ? 0.4 : 1,
              paddingVertical: rs(short ? 10 : 12),
              minWidth: 0,
            },
          ]}
        >
          <Text
            style={[s.ctrlTxt, { color: WOOD.gold, fontSize: rs(compact ? 11 : 12) }]}
            numberOfLines={1}
          >
            {t.pn_jaapUndo}
          </Text>
        </Pressable>
        <Pressable
          onPress={reset}
          style={[
            s.ctrlBtn,
            {
              borderColor: `${WOOD.gold}44`,
              backgroundColor: `${WOOD.mid}99`,
              paddingVertical: rs(short ? 10 : 12),
              minWidth: 0,
            },
          ]}
        >
          <Text
            style={[s.ctrlTxt, { color: WOOD.gold, fontSize: rs(compact ? 11 : 12) }]}
            numberOfLines={1}
          >
            {t.pn_jaapReset}
          </Text>
        </Pressable>
      </View>

      {/* Collapsible setup — keeps focus on the counter */}
      <Pressable
        onPress={() => {
          LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
          Haptics.selectionAsync().catch(() => {});
          setSetupOpen((o) => !o);
        }}
        style={[
          s.setupToggle,
          {
            borderColor: `${WOOD.gold}33`,
            backgroundColor: C.bgCard,
            paddingHorizontal: rs(12),
            paddingVertical: rs(short ? 10 : 12),
            gap: rs(8),
          },
        ]}
      >
        <Text
          style={{
            flex: 1,
            flexShrink: 1,
            fontSize: rs(compact ? 12 : 13),
            fontFamily: "Nunito_600SemiBold",
            color: C.text,
          }}
          numberOfLines={1}
          adjustsFontSizeToFit
          minimumFontScale={0.75}
        >
          {setupOpen ? "▾" : "▸"}  {t.pn_jaapPickNaam} · {t.pn_jaapTarget}
        </Text>
        <Text
          style={{
            fontSize: rs(11),
            fontFamily: "Nunito_400Regular",
            color: C.textMuted,
            flexShrink: 0,
          }}
          numberOfLines={1}
        >
          {unlimited
            ? t.pn_jaapUnlimited
            : target === 108
              ? `108 ${t.pn_jaapMala}`
              : String(target)}
        </Text>
      </Pressable>

      {setupOpen ? (
        <View
          style={[
            s.setupPanel,
            {
              backgroundColor: C.bgCard,
              borderColor: C.border,
              gap: rs(12),
              padding: rs(12),
            },
          ]}
        >
          <Text style={[s.fieldLbl, { color: C.textMuted, fontSize: rs(10) }]}>{t.pn_jaapPickNaam}</Text>
          <View style={[s.chipRow, { gap: rs(7) }]}>
            {PRESETS.map((p) => {
              const active = presetId === p.id;
              return (
                <Pressable
                  key={p.id}
                  onPress={() => {
                    Haptics.selectionAsync().catch(() => {});
                    setPresetId(p.id);
                  }}
                  style={[
                    s.chip,
                    {
                      borderColor: C.border,
                      paddingHorizontal: rs(compact ? 8 : 10),
                      paddingVertical: rs(7),
                      maxWidth: "100%",
                    },
                    active && { backgroundColor: WOOD.warm, borderColor: WOOD.gold },
                  ]}
                >
                  <Text
                    style={[
                      s.chipText,
                      { color: active ? WOOD.ink : C.textMuted, fontSize: rs(compact ? 11 : 12) },
                    ]}
                    numberOfLines={1}
                  >
                    {p.id === "custom" ? t.pn_jaapCustom : p.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {presetId === "custom" ? (
            <TextInput
              value={customText}
              onChangeText={setCustomText}
              placeholder={t.pn_jaapCustomPh}
              placeholderTextColor={C.textMuted}
              style={[
                s.input,
                {
                  color: C.text,
                  borderColor: C.border,
                  backgroundColor: C.bgCard2,
                  fontSize: rs(15),
                  paddingHorizontal: rs(12),
                  paddingVertical: rs(10),
                  width: "100%",
                },
              ]}
            />
          ) : null}

          <Text style={[s.fieldLbl, { color: C.textMuted, fontSize: rs(10) }]}>{t.pn_jaapTarget}</Text>
          <View style={[s.chipRow, { gap: rs(7) }]}>
            {TARGETS.map((n) => {
              const active = target === n;
              return (
                <Pressable
                  key={n}
                  onPress={() => {
                    Haptics.selectionAsync().catch(() => {});
                    setTarget(n);
                  }}
                  style={[
                    s.chip,
                    {
                      borderColor: C.border,
                      paddingHorizontal: rs(compact ? 10 : 12),
                      paddingVertical: rs(7),
                    },
                    active && { backgroundColor: WOOD.mid, borderColor: WOOD.gold },
                  ]}
                >
                  <Text
                    style={[
                      s.chipText,
                      { color: active ? WOOD.glow : C.textMuted, fontSize: rs(compact ? 11 : 12) },
                    ]}
                    numberOfLines={1}
                  >
                    {n === 0
                      ? `∞ ${t.pn_jaapUnlimited}`
                      : n === 108
                        ? `108 · ${t.pn_jaapMala}`
                        : String(n)}
                  </Text>
                </Pressable>
              );
            })}
          </View>
        </View>
      ) : null}

      {!veryShort ? (
        <Text
          style={[
            s.tip,
            {
              color: C.textMuted,
              fontSize: rs(11),
              lineHeight: rs(16),
              paddingHorizontal: rs(4),
            },
          ]}
        >
          {t.pn_jaapTip}
        </Text>
      ) : null}
    </View>
  );
}

const s = StyleSheet.create({
  kicker: {
    fontFamily: "Nunito_700Bold",
    letterSpacing: 2,
    textAlign: "center",
  },
  mantraHero: {
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
    width: "100%",
  },
  metaLine: {
    fontFamily: "Nunito_500Medium",
    textAlign: "center",
    width: "100%",
  },
  doneLine: {
    fontFamily: "Nunito_700Bold",
    textAlign: "center",
  },
  controls: { flexDirection: "row", width: "100%" },
  ctrlBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
  },
  ctrlTxt: { fontFamily: "Nunito_600SemiBold", textAlign: "center" },
  setupToggle: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderWidth: 1,
    borderRadius: 14,
    width: "100%",
  },
  setupPanel: {
    borderRadius: 14,
    borderWidth: 1,
    width: "100%",
  },
  fieldLbl: { fontFamily: "Nunito_700Bold", letterSpacing: 1 },
  chipRow: { flexDirection: "row", flexWrap: "wrap" },
  chip: { borderRadius: 14, borderWidth: 1 },
  chipText: { fontFamily: "Nunito_600SemiBold" },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    fontFamily: "Nunito_600SemiBold",
  },
  tip: {
    fontFamily: "Nunito_400Regular",
    textAlign: "center",
    paddingBottom: 4,
  },
});
