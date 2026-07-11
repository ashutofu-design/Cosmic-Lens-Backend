import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

/**
 * Expo/Metro on Windows passes `D:\...` to ESM import() and crashes with
 * ERR_UNSUPPORTED_ESM_URL_SCHEME. Force load via file:// URL override.
 */
export function applyWindowsMetroConfigEnv(cwd, env) {
  if (process.platform !== "win32") {
    return env;
  }

  const candidates = [
    path.join(cwd, "metro.cosmic.cjs"),
  ];
  const configPath = candidates.find((p) => fs.existsSync(p));
  if (!configPath) {
    return env;
  }

  return {
    ...env,
    EXPO_OVERRIDE_METRO_CONFIG: pathToFileURL(configPath).href,
  };
}
