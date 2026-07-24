import { createAudioPlayer, setAudioModeAsync, type AudioPlayer } from "expo-audio";

let ready = false;
let completePlayer: AudioPlayer | null = null;
let malaPlayer: AudioPlayer | null = null;

async function ensureReady() {
  if (ready) return;
  try {
    await setAudioModeAsync({
      playsInSilentMode: true,
      shouldPlayInBackground: false,
      interruptionMode: "mixWithOthers",
    });
  } catch {
    /* platform may ignore some flags */
  }
  try {
    completePlayer = createAudioPlayer(require("../assets/sounds/jaap-complete.wav"));
    malaPlayer = createAudioPlayer(require("../assets/sounds/jaap-mala.wav"));
    ready = true;
  } catch (e) {
    console.warn("[jaapSounds] load failed", e);
  }
}

async function replay(player: AudioPlayer | null) {
  if (!player) return;
  try {
    await player.seekTo(0);
  } catch {
    /* some platforms start from 0 on play */
  }
  try {
    player.play();
  } catch (e) {
    console.warn("[jaapSounds] play failed", e);
  }
}

/** Prefetch players (no audible playback). */
export async function preloadJaapSounds() {
  await ensureReady();
}

/** Target reached — longer temple-bell chime. */
export async function playJaapCompleteSound() {
  await ensureReady();
  await replay(completePlayer);
}

/** Every 108 (mala) — shorter soft chime. */
export async function playJaapMalaSound() {
  await ensureReady();
  await replay(malaPlayer);
}
