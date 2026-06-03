/**
 * Premium cinematic starfield engine — single canvas, in-place updates, delta-time fly-through.
 * Used by web (direct canvas) and native (WebView HTML export).
 */

export const GALAXY_FLY_SPEED = 0.2;
export const GALAXY_PHYSICS_STEP = 1 / 120;

export type GalaxyStar = {
  bx: number;
  by: number;
  z: number;
  pz: number;
  phase: number;
  bright: number;
  tint: 0 | 1 | 2;
  cr: number;
  cg: number;
  cb: number;
  gr: number;
  gg: number;
  gb: number;
};

export function starCountForViewport(w: number, h: number): number {
  return Math.min(5200, Math.floor((w * h) / 115));
}

export function setStarTint(s: GalaxyStar): void {
  if (s.tint === 1) {
    s.cr = 255;
    s.cg = 228;
    s.cb = 175;
    s.gr = 255;
    s.gg = 200;
    s.gb = 120;
    return;
  }
  if (s.tint === 2) {
    s.cr = 220;
    s.cg = 195;
    s.cb = 255;
    s.gr = 160;
    s.gg = 120;
    s.gb = 255;
    return;
  }
  s.cr = 255;
  s.cg = 255;
  s.cb = 255;
  s.gr = 175;
  s.gg = 210;
  s.gb = 255;
}

export function respawnStar(s: GalaxyStar): void {
  const angle = Math.random() * Math.PI * 2;
  const dist = Math.pow(Math.random(), 0.7);
  s.bx = Math.cos(angle) * dist;
  s.by = Math.sin(angle) * dist;
  s.z = 1;
  s.pz = 1;
  s.phase = Math.random() * Math.PI * 2;
  s.bright = Math.random();
  const roll = Math.random();
  s.tint = roll < 0.9 ? 0 : roll < 0.95 ? 1 : 2;
  setStarTint(s);
}

export function initGalaxyStars(count: number): GalaxyStar[] {
  const stars: GalaxyStar[] = new Array(count);
  for (let i = 0; i < count; i++) {
    const s: GalaxyStar = {
      bx: 0,
      by: 0,
      z: 1,
      pz: 1,
      phase: 0,
      bright: 0,
      tint: 0,
      cr: 255,
      cg: 255,
      cb: 255,
      gr: 180,
      gg: 210,
      gb: 255,
    };
    respawnStar(s);
    s.z = 0.15 + Math.random() * 0.85;
    s.pz = s.z;
    stars[i] = s;
  }
  return stars;
}

export function stepStar(s: GalaxyStar, step: number): void {
  s.pz = s.z;
  s.z -= GALAXY_FLY_SPEED * step;
  if (s.z <= 0.035) respawnStar(s);
}

export type GalaxyEngineState = {
  stars: GalaxyStar[];
  w: number;
  h: number;
  cx: number;
  cy: number;
  accum: number;
  last: number;
};

export function projectStar(
  s: GalaxyStar,
  z: number,
  cx: number,
  cy: number,
  w: number,
  h: number
): { x: number; y: number; inv: number } {
  const inv = 1 / Math.max(z, 0.045);
  return {
    x: cx + s.bx * w * 0.5 * inv,
    y: cy + s.by * h * 0.5 * inv,
    inv,
  };
}

export function drawGalaxyBackground(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number
): void {
  ctx.fillStyle = "#000000";
  ctx.fillRect(0, 0, w, h);
}

export function drawGalaxyFrame(
  ctx: CanvasRenderingContext2D,
  state: GalaxyEngineState,
  dt: number,
  timeSec: number,
  blend: number
): void {
  const { stars, w, h, cx, cy } = state;

  for (let i = 0; i < stars.length; i++) {
    const s = stars[i];
    const zDraw = s.pz + (s.z - s.pz) * blend;
    const p1 = projectStar(s, zDraw, cx, cy, w, h);
    const p0 = projectStar(s, Math.min(1, zDraw + 0.06), cx, cy, w, h);

    const radius = Math.min(3.8, (0.18 + s.bright * 0.95) * p1.inv * 0.34);
    const tw = 0.88 + 0.12 * Math.sin(timeSec * (1.1 + s.bright * 1.4) + s.phase);
    const alpha = Math.min(1, (0.12 + (1 - zDraw) * 0.82) * (0.55 + s.bright * 0.45) * tw);
    if (alpha < 0.04 || radius < 0.1) continue;

    const dx = p1.x - p0.x;
    const dy = p1.y - p0.y;
    const seg = Math.sqrt(dx * dx + dy * dy);
    const near = zDraw < 0.5;

    if (near && seg > 1.1) {
      const ang = Math.atan2(dy, dx);
      const len = Math.min(seg * 0.9, radius * 7);
      ctx.save();
      ctx.translate(p1.x, p1.y);
      ctx.rotate(ang);
      ctx.globalAlpha = alpha * 0.32 * (0.5 - zDraw) * 2;
      const streak = ctx.createLinearGradient(-len, 0, radius * 0.3, 0);
      streak.addColorStop(0, `rgba(${s.gr},${s.gg},${s.gb},0)`);
      streak.addColorStop(0.45, `rgba(${s.cr},${s.cg},${s.cb},${alpha * 0.35})`);
      streak.addColorStop(1, `rgba(${s.cr},${s.cg},${s.cb},${alpha * 0.75})`);
      ctx.fillStyle = streak;
      ctx.beginPath();
      ctx.ellipse(-len * 0.35, 0, len * 0.45, radius * 0.5, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    if (radius < 1.1) {
      ctx.fillStyle = `rgba(${s.cr},${s.cg},${s.cb},${alpha * 0.85})`;
      ctx.beginPath();
      ctx.arc(p1.x, p1.y, Math.max(0.35, radius * 0.45), 0, Math.PI * 2);
      ctx.fill();
      continue;
    }

    const glow = ctx.createRadialGradient(p1.x, p1.y, 0, p1.x, p1.y, radius * 5);
    glow.addColorStop(0, `rgba(${s.cr},${s.cg},${s.cb},${alpha})`);
    glow.addColorStop(0.12, `rgba(${s.gr},${s.gg},${s.gb},${alpha * 0.55})`);
    glow.addColorStop(0.4, `rgba(${s.gr},${s.gg},${s.gb},${alpha * 0.12})`);
    glow.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(p1.x, p1.y, radius * 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = `rgba(${s.cr},${s.cg},${s.cb},${Math.min(1, alpha * 1.08)})`;
    ctx.beginPath();
    ctx.arc(p1.x, p1.y, Math.max(0.38, radius * 0.4), 0, Math.PI * 2);
    ctx.fill();
  }
}

export function advanceGalaxyPhysics(state: GalaxyEngineState, dt: number): number {
  state.accum += dt;
  let guard = 0;
  while (state.accum >= GALAXY_PHYSICS_STEP && guard < 10) {
    for (let i = 0; i < state.stars.length; i++) {
      stepStar(state.stars[i], GALAXY_PHYSICS_STEP);
    }
    state.accum -= GALAXY_PHYSICS_STEP;
    guard++;
  }
  return state.accum / GALAXY_PHYSICS_STEP;
}

/** Web: attach engine to canvas; returns cleanup. */
export function attachGalaxyCinematicCanvas(canvas: HTMLCanvasElement): () => void {
  const ctx = canvas.getContext("2d", { alpha: true });
  if (!ctx) return () => {};

  let w = 0;
  let h = 0;
  let dpr = 1;
  let raf = 0;
  let stars: GalaxyStar[] = [];

  const state: GalaxyEngineState = {
    stars,
    w: 0,
    h: 0,
    cx: 0,
    cy: 0,
    accum: 0,
    last: 0,
  };

  const resize = () => {
    w = window.innerWidth || 360;
    h = window.innerHeight || 640;
    state.w = w;
    state.h = h;
    state.cx = w * 0.5;
    state.cy = h * 0.5;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const count = starCountForViewport(w, h);
    stars = initGalaxyStars(count);
    state.stars = stars;
    state.accum = 0;
  };

  const frame = (now: number) => {
    if (!state.last) state.last = now;
    const dt = Math.min(0.05, Math.max(0.001, (now - state.last) / 1000));
    state.last = now;

    const blend = advanceGalaxyPhysics(state, dt);
    drawGalaxyBackground(ctx, w, h);
    drawGalaxyFrame(ctx, state, dt, now / 1000, blend);

    raf = requestAnimationFrame(frame);
  };

  resize();
  window.addEventListener("resize", resize);
  raf = requestAnimationFrame(frame);

  return () => {
    cancelAnimationFrame(raf);
    window.removeEventListener("resize", resize);
  };
}
