import React, { useEffect, useRef } from "react";
import { attachGalaxyCinematicCanvas } from "@/lib/galaxyCinematicEngine";

export function GalaxyCinematicCanvas() {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    return attachGalaxyCinematicCanvas(canvas);
  }, []);

  return (
    <canvas
      ref={ref}
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
    />
  );
}
