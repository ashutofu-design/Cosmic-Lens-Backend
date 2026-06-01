import { LinearGradient } from "expo-linear-gradient";
import React, { useMemo } from "react";
import { StyleSheet, View } from "react-native";
import Animated, {
  Extrapolation,
  interpolate,
  useAnimatedStyle,
  type SharedValue,
} from "react-native-reanimated";
import Svg, { Ellipse, G } from "react-native-svg";

type PlanetKind = "sun" | "moon" | "mercury" | "venus" | "mars" | "jupiter" | "saturn";

type BgPlanet = {
  kind: PlanetKind;
  x: number;
  y: number;
  scale: number;
  driftX: number;
  driftY: number;
  speed: number;
  phase: number;
  opacity: number;
};

const BG_PLANETS: BgPlanet[] = [
  { kind: "sun", x: 0.88, y: 0.1, scale: 1.1, driftX: 5, driftY: 4, speed: 0.028, phase: 0, opacity: 0.55 },
  { kind: "moon", x: 0.12, y: 0.18, scale: 0.7, driftX: 7, driftY: 5, speed: 0.032, phase: 1.2, opacity: 0.5 },
  { kind: "mars", x: 0.78, y: 0.55, scale: 0.65, driftX: 6, driftY: -5, speed: 0.03, phase: 2.4, opacity: 0.48 },
  { kind: "venus", x: 0.08, y: 0.62, scale: 0.55, driftX: 5, driftY: 6, speed: 0.034, phase: 0.6, opacity: 0.45 },
  { kind: "jupiter", x: 0.92, y: 0.72, scale: 0.95, driftX: -5, driftY: 4, speed: 0.026, phase: 3.1, opacity: 0.42 },
  { kind: "saturn", x: 0.22, y: 0.82, scale: 0.85, driftX: 8, driftY: -4, speed: 0.027, phase: 4.5, opacity: 0.5 },
  { kind: "mercury", x: 0.55, y: 0.12, scale: 0.4, driftX: 4, driftY: 6, speed: 0.036, phase: 1.8, opacity: 0.4 },
];

type Props = {
  progress: SharedValue<number>;
  drift: SharedValue<number>;
  twinkle: SharedValue<number>;
  width: number;
  height: number;
};

export function GalaxyBackground({ progress, drift, twinkle, width, height }: Props) {
  const stars = useMemo(
    () =>
      Array.from({ length: 110 }, (_, i) => ({
        x: ((i * 73 + 11) % 100) / 100,
        y: ((i * 41 + 29) % 100) / 100,
        size: 1 + (i % 4) * 0.6,
        phase: (i * 0.17) % 1,
        bright: i % 7 === 0,
      })),
    [],
  );

  const wrapStyle = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.04, 0.18], [0, 1], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, wrapStyle]} pointerEvents="none">
      <GalaxyNebula width={width} height={height} progress={progress} />
      <GalaxyBand width={width} height={height} drift={drift} />

      {stars.map((star, i) => (
        <Star key={i} {...star} twinkle={twinkle} width={width} height={height} />
      ))}

      {BG_PLANETS.map((p, i) => (
        <BgPlanet key={i} planet={p} drift={drift} width={width} height={height} />
      ))}
    </Animated.View>
  );
}

function GalaxyNebula({ width, height, progress }: { width: number; height: number; progress: SharedValue<number> }) {
  const clouds = [
    { cx: 0.25, cy: 0.35, r: 0.55, colors: ["rgba(88,28,135,0.55)", "rgba(88,28,135,0)"] as const },
    { cx: 0.75, cy: 0.45, r: 0.5, colors: ["rgba(30,58,138,0.45)", "rgba(30,58,138,0)"] as const },
    { cx: 0.5, cy: 0.7, r: 0.48, colors: ["rgba(120,53,15,0.25)", "rgba(120,53,15,0)"] as const },
    { cx: 0.15, cy: 0.75, r: 0.4, colors: ["rgba(124,58,237,0.35)", "rgba(124,58,237,0)"] as const },
    { cx: 0.85, cy: 0.2, r: 0.38, colors: ["rgba(251,191,36,0.2)", "rgba(251,191,36,0)"] as const },
  ];

  const style = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.05, 0.2], [0, 1], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, style]}>
      {clouds.map((c, i) => {
        const size = width * c.r * 2;
        return (
          <LinearGradient
            key={i}
            colors={[...c.colors]}
            style={{
              position: "absolute",
              left: width * c.cx - size / 2,
              top: height * c.cy - size / 2,
              width: size,
              height: size,
              borderRadius: size / 2,
            }}
            start={{ x: 0.3, y: 0.2 }}
            end={{ x: 0.8, y: 0.9 }}
          />
        );
      })}
    </Animated.View>
  );
}

function GalaxyBand({ width, height, drift }: { width: number; height: number; drift: SharedValue<number> }) {
  const style = useAnimatedStyle(() => ({
    position: "absolute",
    left: -width * 0.2,
    top: height * 0.38,
    width: width * 1.4,
    height: height * 0.35,
    opacity: 0.35,
    transform: [
      { rotate: "-18deg" },
      { translateX: Math.sin(drift.value * Math.PI * 2 * 0.4) * 5 },
    ],
  }));

  return (
    <Animated.View style={style}>
      <LinearGradient
        colors={["transparent", "rgba(167,139,250,0.15)", "rgba(251,191,36,0.12)", "rgba(56,189,248,0.1)", "transparent"]}
        start={{ x: 0, y: 0.5 }}
        end={{ x: 1, y: 0.5 }}
        style={StyleSheet.absoluteFill}
      />
    </Animated.View>
  );
}

function Star({
  x, y, size, phase, bright, twinkle, width, height,
}: {
  x: number;
  y: number;
  size: number;
  phase: number;
  bright: boolean;
  twinkle: SharedValue<number>;
  width: number;
  height: number;
}) {
  const style = useAnimatedStyle(() => {
    const t = (twinkle.value + phase) % 1;
    const blink = 0.35 + t * 0.65;
    return {
      position: "absolute",
      left: width * x,
      top: height * y,
      width: size * (bright ? 2.2 : 1),
      height: size * (bright ? 2.2 : 1),
      borderRadius: size,
      backgroundColor: bright ? "#fff7c2" : "#e2e8f0",
      opacity: blink * (bright ? 0.95 : 0.65),
      shadowColor: bright ? "#fde047" : "#fff",
      shadowOpacity: bright ? 0.9 : 0.4,
      shadowRadius: bright ? 4 : 2,
    };
  });

  return <Animated.View style={style} />;
}

function BgPlanet({
  planet,
  drift,
  width,
  height,
}: {
  planet: BgPlanet;
  drift: SharedValue<number>;
  width: number;
  height: number;
}) {
  const baseD = 28 * planet.scale;

  const style = useAnimatedStyle(() => {
    const t = drift.value * Math.PI * 2 * planet.speed + planet.phase;
    const dx = Math.sin(t) * planet.driftX;
    const dy = Math.cos(t * 0.9) * planet.driftY;
    const d = baseD;
    const visualW = planet.kind === "saturn" ? d * 2 : d;
    const visualH = planet.kind === "saturn" ? d * 1.3 : d;
    return {
      position: "absolute",
      left: width * planet.x + dx - visualW / 2,
      top: height * planet.y + dy - visualH / 2,
      opacity: planet.opacity,
      transform: [{ scale: 0.96 + Math.sin(t * 0.35) * 0.03 }],
    };
  });

  return (
    <Animated.View style={style}>
      <PlanetDot kind={planet.kind} diameter={baseD} />
    </Animated.View>
  );
}

function PlanetDot({ kind, diameter }: { kind: PlanetKind; diameter: number }) {
  const d = diameter;
  const r = d / 2;

  switch (kind) {
    case "sun":
      return (
        <LinearGradient
          colors={["#fff7c2", "#fde047", "#f59e0b", "#c2410c"]}
          start={{ x: 0.2, y: 0.15 }}
          end={{ x: 0.9, y: 0.95 }}
          style={{ width: d, height: d, borderRadius: r }}
        />
      );
    case "moon":
      return (
        <LinearGradient
          colors={["#f1f5f9", "#94a3b8", "#475569"]}
          start={{ x: 0.25, y: 0.2 }}
          end={{ x: 0.85, y: 0.9 }}
          style={{ width: d, height: d, borderRadius: r }}
        />
      );
    case "mercury":
      return (
        <LinearGradient
          colors={["#d6d3d1", "#78716c", "#44403c"]}
          start={{ x: 0.22, y: 0.18 }}
          end={{ x: 0.88, y: 0.92 }}
          style={{ width: d, height: d, borderRadius: r }}
        />
      );
    case "venus":
      return (
        <LinearGradient
          colors={["#fffbeb", "#fde68a", "#fbbf24"]}
          start={{ x: 0.2, y: 0.15 }}
          end={{ x: 0.9, y: 0.9 }}
          style={{ width: d, height: d, borderRadius: r }}
        />
      );
    case "mars":
      return (
        <LinearGradient
          colors={["#fecaca", "#ef4444", "#991b1b"]}
          start={{ x: 0.25, y: 0.2 }}
          end={{ x: 0.9, y: 0.95 }}
          style={{ width: d, height: d, borderRadius: r }}
        />
      );
    case "jupiter":
      return (
        <LinearGradient
          colors={["#fde68a", "#d4a574", "#b45309", "#fde68a"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
          style={{ width: d, height: d, borderRadius: r }}
        />
      );
    case "saturn": {
      const w = d * 2;
      const h = d * 1.3;
      return (
        <View style={{ width: w, height: h, alignItems: "center", justifyContent: "center" }}>
          <Svg width={w} height={h} style={StyleSheet.absoluteFill}>
            <G rotation={-16} origin={`${w / 2}, ${h / 2}`}>
              <Ellipse
                cx={w / 2}
                cy={h / 2}
                rx={d * 0.85}
                ry={d * 0.24}
                stroke="rgba(226,201,144,0.7)"
                strokeWidth={Math.max(1, d * 0.06)}
                fill="rgba(210,180,120,0.1)"
              />
            </G>
          </Svg>
          <LinearGradient
            colors={["#fef3c7", "#c4a574", "#8b6914"]}
            start={{ x: 0.22, y: 0.18 }}
            end={{ x: 0.88, y: 0.92 }}
            style={{ width: d, height: d, borderRadius: r }}
          />
        </View>
      );
    }
    default:
      return null;
  }
}
