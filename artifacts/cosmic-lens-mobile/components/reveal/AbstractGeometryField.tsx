import React from "react";
import { StyleSheet } from "react-native";
import Animated, {
  Extrapolation,
  interpolate,
  useAnimatedStyle,
  type SharedValue,
} from "react-native-reanimated";

type Shape =
  | {
      kind: "rect";
      x: number;
      y: number;
      w: number;
      h: number;
      color: string;
      borderRadius?: number;
      rot: number;
      driftX: number;
      driftY: number;
      speed: number;
      phase: number;
    }
  | {
      kind: "square";
      x: number;
      y: number;
      size: number;
      color: string;
      rot: number;
      driftX: number;
      driftY: number;
      speed: number;
      phase: number;
    }
  | {
      kind: "line";
      x: number;
      y: number;
      length: number;
      thickness: number;
      color: string;
      rot: number;
      driftX: number;
      driftY: number;
      speed: number;
      phase: number;
    };

/** Simple floating rects, squares & lines — abstract, not literal planets. */
const SHAPES: Shape[] = [
  { kind: "rect", x: 0.08, y: 0.14, w: 56, h: 10, color: "rgba(251,191,36,0.35)", rot: 18, driftX: 22, driftY: 14, speed: 0.2, phase: 0 },
  { kind: "square", x: 0.82, y: 0.12, size: 20, color: "rgba(167,139,250,0.4)", rot: -24, driftX: 16, driftY: 18, speed: 0.26, phase: 0.8 },
  { kind: "line", x: 0.15, y: 0.32, length: 72, thickness: 2, color: "rgba(56,189,248,0.45)", rot: -8, driftX: 28, driftY: 10, speed: 0.18, phase: 1.4 },
  { kind: "rect", x: 0.72, y: 0.28, w: 44, h: 44, color: "rgba(251,191,36,0.12)", borderRadius: 6, rot: 12, driftX: 12, driftY: 20, speed: 0.15, phase: 2.1 },
  { kind: "square", x: 0.05, y: 0.52, size: 14, color: "rgba(253,224,71,0.5)", rot: 35, driftX: 18, driftY: -16, speed: 0.32, phase: 0.5 },
  { kind: "line", x: 0.88, y: 0.48, length: 90, thickness: 1.5, color: "rgba(167,139,250,0.5)", rot: 72, driftX: -20, driftY: 12, speed: 0.22, phase: 3.2 },
  { kind: "rect", x: 0.22, y: 0.68, w: 38, h: 8, color: "rgba(34,211,238,0.35)", rot: -15, driftX: 24, driftY: -10, speed: 0.19, phase: 1.9 },
  { kind: "square", x: 0.65, y: 0.72, size: 26, color: "rgba(124,58,237,0.25)", rot: 8, driftX: -14, driftY: -18, speed: 0.24, phase: 4.0 },
  { kind: "line", x: 0.42, y: 0.2, length: 110, thickness: 2, color: "rgba(251,191,36,0.3)", rot: 25, driftX: 10, driftY: 22, speed: 0.17, phase: 2.8 },
  { kind: "rect", x: 0.48, y: 0.82, w: 62, h: 12, color: "rgba(167,139,250,0.28)", rot: -6, driftX: -22, driftY: 8, speed: 0.21, phase: 5.2 },
  { kind: "square", x: 0.9, y: 0.78, size: 16, color: "rgba(251,191,36,0.38)", rot: -40, driftX: 12, driftY: -12, speed: 0.28, phase: 0.3 },
  { kind: "line", x: 0.28, y: 0.42, length: 64, thickness: 1, color: "rgba(148,163,184,0.4)", rot: -55, driftX: 16, driftY: 16, speed: 0.25, phase: 3.8 },
];

type Props = {
  progress: SharedValue<number>;
  drift: SharedValue<number>;
  width: number;
  height: number;
};

export function AbstractGeometryField({ progress, drift, width, height }: Props) {
  const wrapStyle = useAnimatedStyle(() => ({
    opacity: interpolate(progress.value, [0.08, 0.22, 0.88, 0.94], [0, 1, 1, 0.85], Extrapolation.CLAMP),
  }));

  return (
    <Animated.View style={[StyleSheet.absoluteFill, wrapStyle]} pointerEvents="none">
      {SHAPES.map((shape, i) => (
        <FloatingShape key={i} shape={shape} drift={drift} width={width} height={height} />
      ))}
    </Animated.View>
  );
}

function FloatingShape({
  shape,
  drift,
  width,
  height,
}: {
  shape: Shape;
  drift: SharedValue<number>;
  width: number;
  height: number;
}) {
  const style = useAnimatedStyle(() => {
    const t = drift.value * Math.PI * 2 * shape.speed + shape.phase;
    const dx = Math.sin(t) * shape.driftX;
    const dy = Math.cos(t * 0.85) * shape.driftY;
    const spin = shape.rot + drift.value * 28;

    if (shape.kind === "line") {
      const left = width * shape.x + dx;
      const top = height * shape.y + dy;
      return {
        position: "absolute",
        left,
        top,
        width: shape.length,
        height: shape.thickness,
        backgroundColor: shape.color,
        borderRadius: shape.thickness / 2,
        transform: [{ rotate: `${spin}deg` }],
      };
    }

    if (shape.kind === "square") {
      const left = width * shape.x + dx;
      const top = height * shape.y + dy;
      return {
        position: "absolute",
        left,
        top,
        width: shape.size,
        height: shape.size,
        backgroundColor: shape.color,
        borderRadius: 3,
        transform: [{ rotate: `${spin}deg` }],
      };
    }

    const left = width * shape.x + dx;
    const top = height * shape.y + dy;
    return {
      position: "absolute",
      left,
      top,
      width: shape.w,
      height: shape.h,
      backgroundColor: shape.color,
      borderRadius: shape.borderRadius ?? 2,
      transform: [{ rotate: `${spin}deg` }],
    };
  });

  return <Animated.View style={style} />;
}
