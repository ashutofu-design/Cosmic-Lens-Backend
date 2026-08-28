/**
 * Release hardening for the Android manifest.
 *
 * - allowBackup=false so `adb backup` cannot lift the app sandbox (which holds
 *   the AsyncStorage profile DB and the SecureStore-encrypted API key blob).
 * - dataExtractionRules/fullBackupContent disabled for the same reason on
 *   Android 12+ cloud/device transfer.
 *
 * tools:replace is set because libraries commonly merge allowBackup="true".
 */
const { AndroidConfig, withAndroidManifest } = require("@expo/config-plugins");

function ensureToolsNamespace(manifest) {
  if (!manifest.$) manifest.$ = {};
  if (!manifest.$["xmlns:tools"]) {
    manifest.$["xmlns:tools"] = "http://schemas.android.com/tools";
  }
}

function mergeToolsAttr(application, attr, value) {
  const existing = String(application.$[attr] || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  application.$[attr] = Array.from(new Set([...existing, value])).join(",");
}

const withAndroidSecurityHardening = (config) =>
  withAndroidManifest(config, (modConfig) => {
    ensureToolsNamespace(modConfig.modResults.manifest);

    const application = AndroidConfig.Manifest.getMainApplicationOrThrow(
      modConfig.modResults,
    );
    if (!application.$) application.$ = {};

    application.$["android:allowBackup"] = "false";
    application.$["android:fullBackupContent"] = "false";
    mergeToolsAttr(application, "tools:replace", "android:allowBackup");

    return modConfig;
  });

module.exports = withAndroidSecurityHardening;
