import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, View } from "react-native";
import Animated, {
  Extrapolation,
  interpolate,
  useAnimatedStyle,
  type SharedValue,
} from "react-native-reanimated";
import Svg, { Ellipse, G } from "react-native-svg";

type PlanetKind = "sun" | "moon" | "mercury" | "venus" | "mars" | "jupiter" | "saturn";

type OrbitConfig = {
  id: string;
  kind: PlanetKind;
  /** Orbit radius multiplier */
  rMul: number;
  /** Planet size multiplier */
  sMul: number;
  speed: number;
  phase: number;
};

const ORBITS: OrbitConfig[] = [
  { id: "sun", kind: "sun", rMul: 1.05, sMul: 1.2, speed: 0.11, phase: 0 },
  { id: "moon", kind: "moon", rMul: 0.62, sMul: 0.55, speed: 0.28, phase: 1.2 },
  { id: "mercury", kind: "mercury", rMul: 0.78, sMul: 0.42, speed: 0.24, phase: 2.1 },
  { id: "venus", kind: "venus", rMul: 0.88, sMul: 0.52, speed: 0.19, phase: 0.8 },
  { id: "mars", kind: "mars", rMul: 0.95, sMul: 0.58, speed: 0.16, phase: 3.4 },
  { id: "jupiter", kind: "jupiter", rMul: 1.12, sMul: 0.95, speed: 0.13, phase: 4.2 },
  { id: "saturn", kind: "saturn", rMul: 1.22, sMul: 0.88, speed: 0.1, phase: 5.1 },
];

const UNIQUE_RADII = [...new Set(ORBITS.map((o) => o.rMul))].sort((a, b) => a - b);

type Props = {
  progress: SharedValue<number>;
  holdFinale: SharedValue<number>;
  orbitSpin: SharedValue<number>;
  centerX: number;
  centerY: number;
  baseR: number;
  scale: number;
};

/** 7 grahas — 3D-style spheres orbiting the hero headline (tilted ellipse). */
export function OrbitingPlanetsRing({
  progress,
  holdFinale,
  orbitSpin,
  centerX,
  centerY,
  baseR,
  scale,
}: Props) {
  const wrapStyle = useAnimatedStyle(() => {
    const enter = interpolate(progress.value, [0.32, 0.44], [0, 1], Extrapolation.CLAMP);
    const hold = holdFinale.value > 0
      ? 1
      : interpolate(progress.value, [0.8, 0.88], [1, 0.88], Extrapolation.CLAMP);
    return { opacity: enter * hold };
  });

  const tilt = 0.34;

  return (
    <Animated.View style={[StyleSheet.absoluteFill, wrapStyle]} pointerEvents="none">
      <Svg
        width="100%"
        height="100%"
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      >
        {UNIQUE_RADII.map((rm) => {
          const rx = baseR * rm;
          const ry = rx * tilt;
          return (
            <Ellipse
              key={rm}
              cx={centerX}
              cy={centerY}
              rx={rx}
              ry={ry}
              stroke="rgba(251,191,36,0.12)"
              strokeWidth={1}
              fill="none"
              strokeDasharray="4 10"
            />
          );
        })}
      </Svg>

      {ORBITS.map((cfg) => (
        <OrbitingPlanet
          key={cfg.id}
          config={cfg}
          orbitSpin={orbitSpin}
          centerX={centerX}
          centerY={centerY}
          baseR={baseR}
          scale={scale}
          tilt={tilt}
        />
      ))}
    </Animated.View>
  );
}

function OrbitingPlanet({
  config,
  orbitSpin,
  centerX,
  centerY,
  baseR,
  scale,
  tilt,
}: {
  config: OrbitConfig;
  orbitSpin: SharedValue<number>;
  centerX: number;
  centerY: number;
  baseR: number;
  scale: number;
  tilt: number;
}) {
  const d = config.sMul * 15 * scale;
  const rx = baseR * config.rMul;
  const ry = rx * tilt;

  const style = useAnimatedStyle(() => {
    const a = config.phase + orbitSpin.value * Math.PI * 2 * config.speed;
    const x = Math.cos(a) * rx;
    const y = Math.sin(a) * ry;
    const depth = (Math.sin(a) + 1) / 2;
    const visualW = config.kind === "saturn" ? d * 2.1 : d;
    const visualH = config.kind === "saturn" ? d * 1.35 : d;
    return {
      position: "absolute",
      left: centerX + x - visualW / 2,
      top: centerY + y - visualH / 2,
      zIndex: depth > 0.55 ? 14 : 6,
      transform: [{ scale: 0.68 + depth * 0.42 }],
      opacity: 0.48 + depth * 0.52,
    };
  });

  return (
    <Animated.View style={style}>
      <PlanetSphere kind={config.kind} diameter={d} />
    </Animated.View>
  );
}

function PlanetSphere({ kind, diameter }: { kind: PlanetKind; diameter: number }) {
  const d = diameter;
  const r = d / 2;

  switch (kind) {
    case "sun":
      return (
        <View style={[s.planetWrap, { width: d, height: d }]}>
          <View style={[s.sunGlow, { width: d * 1.7, height: d * 1.7, borderRadius: d * 0.85 }]} />
          <LinearGradient
            colors={["#fff7c2", "#fde047", "#f59e0b", "#ea580c", "#9a3412"]}
            start={{ x: 0.2, y: 0.15 }}
            end={{ x: 0.9, y: 0.95 }}
            style={[s.sphere, { width: d, height: d, borderRadius: r }]}
          />
        </View>
      );

    case "moon":
      return (
        <View style={[s.planetWrap, { width: d, height: d }]}>
          <LinearGradient
            colors={["#f1f5f9", "#94a3b8", "#475569", "#1e293b"]}
            start={{ x: 0.25, y: 0.2 }}
            end={{ x: 0.85, y: 0.9 }}
            style={[s.sphere, { width: d, height: d, borderRadius: r }]}
          />
          <View style={[s.crater, { width: d * 0.22, height: d * 0.22, top: d * 0.22, left: d * 0.18, opacity: 0.35 }]} />
          <View style={[s.crater, { width: d * 0.14, height: d * 0.14, top: d * 0.55, left: d * 0.52, opacity: 0.28 }]} />
        </View>
      );

    case "mercury":
      return (
        <LinearGradient
          colors={["#d6d3d1", "#78716c", "#44403c", "#292524"]}
          start={{ x: 0.22, y: 0.18 }}
          end={{ x: 0.88, y: 0.92 }}
          style={[s.sphere, { width: d, height: d, borderRadius: r }]}
        />
      );

    case "venus":
      return (
        <LinearGradient
          colors={["#fffbeb", "#fde68a", "#fbbf24", "#d97706"]}
          start={{ x: 0.2, y: 0.15 }}
          end={{ x: 0.9, y: 0.9 }}
          style={[s.sphere, { width: d, height: d, borderRadius: r }]}
        />
      );

    case "mars":
      return (
        <LinearGradient
          colors={["#fecaca", "#ef4444", "#b91c1c", "#7f1d1d"]}
          start={{ x: 0.25, y: 0.2 }}
          end={{ x: 0.9, y: 0.95 }}
          style={[s.sphere, { width: d, height: d, borderRadius: r }]}
        />
      );

    case "jupiter":
      return (
        <View style={[s.planetWrap, { width: d, height: d, borderRadius: r, overflow: "hidden" }]}>
          <LinearGradient
            colors={["#fde68a", "#d4a574", "#b45309", "#92400e", "#fde68a", "#fcd34d"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 0, y: 1 }}
            style={[s.sphere, { width: d, height: d, borderRadius: r }]}
          />
          {[0.28, 0.42, 0.58, 0.72].map((p, i) => (
            <View
              key={i}
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: d * p,
                height: d * 0.07,
                backgroundColor: i % 2 === 0 ? "rgba(120,53,15,0.35)" : "rgba(253,230,138,0.25)",
              }}
            />
          ))}
          <View style={[s.shine, { width: d * 0.35, height: d * 0.2, top: d * 0.12, left: d * 0.15 }]} />
        </View>
      );

    case "saturn":
      return (
        <View style={[s.planetWrap, { width: d * 2.1, height: d * 1.35, alignItems: "center", justifyContent: "center" }]}>
          <Svg width={d * 2.1} height={d * 1.35} style={StyleSheet.absoluteFill}>
            <G rotation={-18} origin={`${(d * 2.1) / 2}, ${(d * 1.35) / 2}`}>
              <Ellipse
                cx={(d * 2.1) / 2}
                cy={(d * 1.35) / 2}
                rx={d * 0.92}
                ry={d * 0.26}
                stroke="rgba(226,201,144,0.75)"
                strokeWidth={Math.max(1.5, d * 0.07)}
                fill="rgba(210,180,120,0.12)"
              />
            </G>
          </Svg>
          <LinearGradient
            colors={["#fef3c7", "#e8d4a8", "#c4a574", "#8b6914"]}
            start={{ x: 0.22, y: 0.18 }}
            end={{ x: 0.88, y: 0.92 }}
            style={[s.sphere, { width: d, height: d, borderRadius: r }]}
          />
        </View>
      );

    default:
      return null;
  }
}

const s = StyleSheet.create({
  planetWrap: {
    alignItems: "center",
    justifyContent: "center",
  },
  sphere: {
    shadowColor: "#000",
    shadowOpacity: 0.45,
    shadowRadius: 6,
    shadowOffset: { width: 2, height: 3 },
    elevation: 6,
  },
  sunGlow: {
    position: "absolute",
    backgroundColor: "rgba(251,191,36,0.28)",
  },
  crater: {
    position: "absolute",
    borderRadius: 999,
    backgroundColor: "#334155",
  },
  shine: {
    position: "absolute",
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.35)",
  },
});
