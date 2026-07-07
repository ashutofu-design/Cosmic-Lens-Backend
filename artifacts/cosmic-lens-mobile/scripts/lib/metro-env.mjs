/** Minimal Metro env helper (Linux/cloud — passthrough). */
export function applyWindowsMetroConfigEnv(_cwd, env) {
  return { ...env };
}
