/**
 * Play Console large-screen / orientation compliance for release builds.
 * - Unlock orientation on MainActivity + known library activities (e.g. ML Kit)
 * - Keep activities resizable (tablets / foldables)
 * - Ensure configChanges includes size/orientation so layouts adapt
 */
const {
  AndroidConfig,
  withAndroidManifest,
} = require("@expo/config-plugins");

const LIBRARY_ACTIVITIES_UNLOCK = [
  "com.google.mlkit.vision.codescanner.internal.GmsBarcodeScanningDelegateActivity",
];

function ensureToolsNamespace(manifest) {
  if (!manifest.$) manifest.$ = {};
  if (!manifest.$["xmlns:tools"]) {
    manifest.$["xmlns:tools"] = "http://schemas.android.com/tools";
  }
}

function patchActivity(activity) {
  if (!activity.$) activity.$ = {};

  delete activity.$["android:screenOrientation"];
  delete activity.$["android:maxAspectRatio"];
  activity.$["android:resizeableActivity"] = "true";
  // Force-remove orientation if a library merge re-adds it.
  activity.$["tools:remove"] = [
    activity.$["tools:remove"],
    "android:screenOrientation",
    "android:maxAspectRatio",
  ]
    .filter(Boolean)
    .join(",");

  const needed = [
    "keyboard",
    "keyboardHidden",
    "orientation",
    "screenSize",
    "screenLayout",
    "uiMode",
    "smallestScreenSize",
  ];
  const existing = String(activity.$["android:configChanges"] || "")
    .split("|")
    .map((s) => s.trim())
    .filter(Boolean);
  activity.$["android:configChanges"] = Array.from(new Set([...existing, ...needed])).join("|");
}

function ensureLibraryActivityOverrides(application) {
  if (!application.activity) application.activity = [];
  const existing = new Set(
    application.activity
      .map((a) => a?.$?.["android:name"])
      .filter(Boolean),
  );

  for (const name of LIBRARY_ACTIVITIES_UNLOCK) {
    if (existing.has(name)) continue;
    application.activity.push({
      $: {
        "android:name": name,
        "android:resizeableActivity": "true",
        "tools:node": "merge",
        "tools:remove": "android:screenOrientation,android:maxAspectRatio",
      },
    });
  }
}

const withPlayConsoleAndroidFixes = (config) =>
  withAndroidManifest(config, (modConfig) => {
    const manifest = modConfig.modResults.manifest;
    ensureToolsNamespace(manifest);

    const application = AndroidConfig.Manifest.getMainApplicationOrThrow(modConfig.modResults);
    const activities = application.activity || [];
    for (const activity of activities) {
      patchActivity(activity);
    }
    ensureLibraryActivityOverrides(application);

    return modConfig;
  });

module.exports = withPlayConsoleAndroidFixes;
