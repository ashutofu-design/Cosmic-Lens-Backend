import { useEffect, useRef } from "react";

const INSIGHTS = [
  { text: "Dasha timeline active", tone: "violet" },
  { text: "Kundli analyzed", tone: "cyan" },
  { text: "Milan score ready", tone: "gold" },
] as const;

/** Smooth, decorative astrology motion for the public homepage hero. */
export function HeroMotion() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = canvas?.parentElement;
    if (!canvas || !host) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const context = canvas.getContext("2d");
    if (!context) return;

    const onPointerMove = (event: PointerEvent) => {
      const rect = host.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / Math.max(rect.width, 1) - 0.5) * 14;
      const y = ((event.clientY - rect.top) / Math.max(rect.height, 1) - 0.5) * 10;
      host.style.setProperty("--hero-parallax-x", `${x}px`);
      host.style.setProperty("--hero-parallax-y", `${y}px`);
    };
    const resetPointer = () => {
      host.style.setProperty("--hero-parallax-x", "0px");
      host.style.setProperty("--hero-parallax-y", "0px");
    };
    host.addEventListener("pointermove", onPointerMove);
    host.addEventListener("pointerleave", resetPointer);

    type Star = {
      x: number;
      y: number;
      radius: number;
      alpha: number;
      phase: number;
      speed: number;
    };

    let width = 0;
    let height = 0;
    let stars: Star[] = [];
    let frame = 0;
    let active = false;
    let inViewport = true;
    let documentVisible = document.visibilityState === "visible";
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      const rect = host.getBoundingClientRect();
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
      const count = Math.min(90, Math.max(36, Math.floor((width * height) / 15000)));
      stars = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 1.15 + 0.35,
        alpha: Math.random() * 0.46 + 0.16,
        phase: Math.random() * Math.PI * 2,
        speed: Math.random() * 0.018 + 0.006,
      }));
    };

    const draw = () => {
      if (!active) return;
      context.clearRect(0, 0, width, height);

      for (let i = 0; i < stars.length; i += 1) {
        const star = stars[i];
        star.phase += star.speed;
        star.y -= 0.025;
        if (star.y < -3) star.y = height + 3;
        const opacity = star.alpha * (0.62 + Math.sin(star.phase) * 0.38);
        context.beginPath();
        context.fillStyle = `rgba(225, 235, 255, ${opacity})`;
        context.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        context.fill();

        const next = stars[i + 1];
        if (!next) continue;
        const dx = star.x - next.x;
        const dy = star.y - next.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < 92) {
          context.beginPath();
          context.strokeStyle = `rgba(167, 139, 250, ${(1 - distance / 92) * 0.1})`;
          context.lineWidth = 0.6;
          context.moveTo(star.x, star.y);
          context.lineTo(next.x, next.y);
          context.stroke();
        }
      }
      frame = window.requestAnimationFrame(draw);
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(host);
    resize();

    const syncAnimation = () => {
      active = documentVisible && inViewport;
      window.cancelAnimationFrame(frame);
      if (active) draw();
    };

    const viewportObserver = new IntersectionObserver(
      ([entry]) => {
        inViewport = entry.isIntersecting;
        syncAnimation();
      },
      { rootMargin: "160px" },
    );
    viewportObserver.observe(host);

    const onVisibility = () => {
      documentVisible = document.visibilityState === "visible";
      syncAnimation();
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      active = false;
      window.cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      viewportObserver.disconnect();
      document.removeEventListener("visibilitychange", onVisibility);
      host.removeEventListener("pointermove", onPointerMove);
      host.removeEventListener("pointerleave", resetPointer);
    };
  }, []);

  return (
    <div className="hero-motion" aria-hidden>
      <canvas ref={canvasRef} className="hero-star-canvas" />
      <div className="hero-glow" />
      <div className="hero-glow hero-glow-gold" />
      <div className="hero-zodiac">
        <span className="hero-zodiac-core">✦</span>
        <span className="hero-orbit hero-orbit-one">
          <i className="hero-planet hero-planet-one">☉</i>
        </span>
        <span className="hero-orbit hero-orbit-two">
          <i className="hero-planet hero-planet-two">☽</i>
        </span>
        <span className="hero-orbit hero-orbit-three">
          <i className="hero-planet hero-planet-three">♃</i>
        </span>
      </div>
      <div className="hero-insights">
        {INSIGHTS.map((insight, index) => (
          <span
            key={insight.text}
            className={`hero-insight hero-insight-${insight.tone}`}
            style={{ animationDelay: `${index * 2.8}s` }}
          >
            <i />
            {insight.text}
          </span>
        ))}
      </div>
    </div>
  );
}
