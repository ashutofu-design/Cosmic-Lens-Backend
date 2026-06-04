import React, { startTransition, useEffect, useRef, useState } from "react";
import { AppState, StyleSheet, View, useWindowDimensions } from "react-native";
import Svg, { Circle } from "react-native-svg";

import {
  advanceGalaxyPhysics,
  initGalaxyStars,
  projectStar,
  starCountForViewport,
  type GalaxyEngineState,
} from "@/lib/galaxyCinematicEngine";

type StarDraw = { key: string; x: number; y: number; r: number; fill: string };

/** Smooth motion; fly speed boosted slightly on native vs web canvas. */
const MOBILE_STAR_CAP = 120;
const PAINT_INTERVAL_MS = 24;
const NATIVE_FLY_SPEED = 1.5;

function buildDrawList(st: GalaxyEngineState, blend: number, timeSec: number): StarDraw[] {
  const out: StarDraw[] = [];
  for (let i = 0; i < st.stars.length; i++) {
    const s = st.stars[i];
    const zDraw = s.pz + (s.z - s.pz) * blend;
    const p = projectStar(s, zDraw, st.cx, st.cy, st.w, st.h);
    const radius = Math.min(3.6, (0.18 + s.bright * 0.95) * p.inv * 0.34);
    const tw = 0.88 + 0.12 * Math.sin(timeSec * (1.1 + s.bright * 1.4) + s.phase);
    const alpha = Math.min(1, (0.12 + (1 - zDraw) * 0.82) * (0.55 + s.bright * 0.45) * tw);
    if (alpha < 0.05 || radius < 0.12) continue;
    out.push({
      key: String(i),
      x: p.x,
      y: p.y,
      r: Math.max(0.45, radius),
      fill: `rgba(${s.cr},${s.cg},${s.cb},${alpha})`,
    });
  }
  return out;
}

const StarLayer = React.memo(function StarLayer({ stars }: { stars: StarDraw[] }) {
  return (
    <>
      {stars.map((s) => (
        <Circle key={s.key} cx={s.x} cy={s.y} r={s.r} fill={s.fill} />
      ))}
    </>
  );
});

/** Native starfield — physics every frame, paint throttled, low-priority React updates. */
export function GalaxyCinematicCanvas() {
  const { width, height } = useWindowDimensions();
  const [drawn, setDrawn] = useState<StarDraw[]>([]);
  const engineRef = useRef<GalaxyEngineState | null>(null);
  const rafRef = useRef(0);
  const activeRef = useRef(true);

  useEffect(() => {
    const sub = AppState.addEventListener("change", (state) => {
      activeRef.current = state === "active";
    });
    return () => sub.remove();
  }, []);

  useEffect(() => {
    if (width < 1 || height < 1) return;

    const count = Math.min(MOBILE_STAR_CAP, starCountForViewport(width, height));
    const engine: GalaxyEngineState = {
      stars: initGalaxyStars(count),
      w: width,
      h: height,
      cx: width * 0.5,
      cy: height * 0.5,
      accum: 0,
      last: 0,
    };
    engineRef.current = engine;

    let lastMs = 0;
    let lastPaint = 0;
    const tick = (now: number) => {
      rafRef.current = requestAnimationFrame(tick);
      if (!activeRef.current) return;
      const st = engineRef.current;
      if (!st) return;
      if (!lastMs) lastMs = now;
      const dt = Math.min(0.05, Math.max(0.001, (now - lastMs) / 1000));
      lastMs = now;
      const blend = advanceGalaxyPhysics(st, dt * NATIVE_FLY_SPEED);
      if (now - lastPaint >= PAINT_INTERVAL_MS) {
        lastPaint = now;
        const frame = buildDrawList(st, blend, now / 1000);
        startTransition(() => setDrawn(frame));
      }
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [width, height]);

  if (width < 1 || height < 1) return null;

  return (
    <View style={[styles.root, { width, height }]} pointerEvents="none" collapsable={false}>
      <Svg width={width} height={height} style={styles.svg}>
        <StarLayer stars={drawn} />
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: "#000000",
  },
  svg: {
    backgroundColor: "#000000",
  },
});
