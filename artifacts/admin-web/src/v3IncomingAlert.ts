/** Browser ring + desktop notification for new V3 live chat requests. */

const STORAGE_KEY = "v3_admin_alerts_enabled";

let audioCtx: AudioContext | null = null;
let titleBlinkTimer: number | null = null;
let ringLoopTimer: number | null = null;
let baseTitle = "Cosmic Admin";

export function v3AlertsEnabled(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function setV3AlertsEnabled(on: boolean) {
  try {
    localStorage.setItem(STORAGE_KEY, on ? "1" : "0");
  } catch {
    /* ignore */
  }
}

/** True when the browser will actually play our ring right now. */
export function isSoundUnlocked(): boolean {
  return !!audioCtx && audioCtx.state === "running";
}

/**
 * Mobile Chrome suspends audio after every page load until the user touches
 * the page. Attach a global listener so the first tap anywhere re-unlocks
 * sound when alerts are armed. Calls onChange whenever lock state may change.
 */
export function ensureSoundAutoUnlock(onChange?: () => void) {
  if (typeof document === "undefined") return;
  const tryUnlock = () => {
    if (!v3AlertsEnabled()) return;
    try {
      const AC =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AC) return;
      audioCtx = audioCtx || new AC();
      if (audioCtx.state === "suspended") {
        void audioCtx.resume().then(() => onChange?.());
      } else {
        onChange?.();
      }
    } catch {
      /* ignore */
    }
  };
  document.addEventListener("pointerdown", tryUnlock, { passive: true });
  document.addEventListener("keydown", tryUnlock, { passive: true });
  // Also re-check when tab becomes visible again.
  document.addEventListener("visibilitychange", () => onChange?.());
}

/** Must run from a click — unlocks audio + requests Notification permission. */
export async function armV3Alerts(): Promise<{ sound: boolean; notify: boolean }> {
  setV3AlertsEnabled(true);
  let sound = false;
  let notify = false;
  try {
    const AC =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (AC) {
      audioCtx = audioCtx || new AC();
      if (audioCtx.state === "suspended") await audioCtx.resume();
      sound = true;
      // Soft unlock beep
      playV3RingTone(1);
    }
  } catch {
    sound = false;
  }
  try {
    if ("Notification" in window) {
      if (Notification.permission === "granted") notify = true;
      else if (Notification.permission !== "denied") {
        const p = await Notification.requestPermission();
        notify = p === "granted";
      }
    }
  } catch {
    notify = false;
  }
  return { sound, notify };
}

export function disarmV3Alerts() {
  setV3AlertsEnabled(false);
  stopTitleBlink();
  stopContinuousRing();
}

/** Keep ringing (and vibrating on phones) until stopContinuousRing(). */
export function startContinuousRing() {
  if (ringLoopTimer != null) return;
  const ringOnce = () => {
    playV3RingTone(1);
    try {
      navigator.vibrate?.([250, 120, 250, 120, 400]);
    } catch {
      /* unsupported */
    }
  };
  ringOnce();
  ringLoopTimer = window.setInterval(ringOnce, 2600);
}

export function stopContinuousRing() {
  if (ringLoopTimer != null) {
    window.clearInterval(ringLoopTimer);
    ringLoopTimer = null;
  }
  try {
    navigator.vibrate?.(0);
  } catch {
    /* unsupported */
  }
}

/** Multi-tone ring (chat-style), repeats `loops` times. */
export function playV3RingTone(loops = 3) {
  try {
    const AC =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return;
    audioCtx = audioCtx || new AC();
    const ctx = audioCtx;
    void ctx.resume();
    const now = ctx.currentTime;
    const pattern = [880, 1174, 880, 1174]; // A5–D6 ping
    for (let loop = 0; loop < loops; loop++) {
      pattern.forEach((freq, i) => {
        const t0 = now + loop * 1.05 + i * 0.18;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.0001, t0);
        gain.gain.exponentialRampToValueAtTime(0.4, t0 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.16);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(t0);
        osc.stop(t0 + 0.18);
      });
    }
  } catch {
    /* autoplay blocked or unsupported */
  }
}

export function showV3DesktopNotification(opts: {
  title?: string;
  body: string;
  tag?: string;
}) {
  try {
    if (!("Notification" in window) || Notification.permission !== "granted") return;
    const n = new Notification(opts.title || "Cosmic Intelligence V3", {
      body: opts.body,
      tag: opts.tag || "v3-live-incoming",
      renotify: true,
      requireInteraction: true,
    });
    n.onclick = () => {
      window.focus();
      n.close();
    };
  } catch {
    /* ignore */
  }
}

let blinkCount = 0;

export function startTitleBlink(pendingCount: number) {
  if (titleBlinkTimer != null && blinkCount === pendingCount) return;
  blinkCount = pendingCount;
  stopTitleBlink();
  if (typeof document === "undefined") return;
  baseTitle = document.title.replace(/^\(\d+\)\s*/, "").replace(/^🔔\s*/, "") || "Cosmic Admin";
  let on = true;
  const paint = () => {
    document.title = on
      ? `(${pendingCount}) 🔔 New V3 chat!`
      : baseTitle;
    on = !on;
  };
  paint();
  titleBlinkTimer = window.setInterval(paint, 900);
}

export function stopTitleBlink() {
  if (titleBlinkTimer != null) {
    window.clearInterval(titleBlinkTimer);
    titleBlinkTimer = null;
  }
  if (typeof document !== "undefined") {
    document.title = baseTitle.replace(/^\(\d+\)\s*/, "").replace(/^🔔\s*/, "") || document.title;
  }
}

export function alertNewV3Requests(newCount: number, sampleName?: string) {
  if (!v3AlertsEnabled() || newCount <= 0) return;
  const who = sampleName ? ` from ${sampleName}` : "";
  showV3DesktopNotification({
    body:
      newCount === 1
        ? `New live chat request${who}. Open V3 Live Chats to Accept.`
        : `${newCount} new live chat requests${who}. Open V3 Live Chats to Accept.`,
  });
  startTitleBlink(newCount);
  // Ring continuously — caller stops it via syncV3PendingAlarm when queue clears.
  startContinuousRing();
}

/**
 * Call on every pending poll: keeps the alarm ringing while any request is
 * waiting for Accept, and silences everything once the queue is empty.
 */
export function syncV3PendingAlarm(pendingCount: number) {
  if (!v3AlertsEnabled() || pendingCount <= 0) {
    stopContinuousRing();
    if (pendingCount <= 0) stopTitleBlink();
    return;
  }
  startContinuousRing();
  startTitleBlink(pendingCount);
}
