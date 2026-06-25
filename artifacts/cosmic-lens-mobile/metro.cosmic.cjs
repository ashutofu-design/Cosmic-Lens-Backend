const path = require("path");
const fs = require("fs");
const { getDefaultConfig } = require("expo/metro-config");

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, "../..");

const config = getDefaultConfig(projectRoot);

// pnpm monorepo — resolve deps from app + workspace root
config.watchFolders = [monorepoRoot];
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, "node_modules"),
  path.resolve(monorepoRoot, "node_modules"),
];
// pnpm: allow resolving siblings inside .pnpm virtual-store folders (expo-router peers).
config.resolver.disableHierarchicalLookup = false;
config.resolver.unstable_enableSymlinks = true;

/** Resolve a package from app/root node_modules, or from a pnpm importer's siblings. */
function resolvePackageDir(pkgName, importerPkg) {
  for (const root of [projectRoot, monorepoRoot]) {
    try {
      return path.dirname(require.resolve(`${pkgName}/package.json`, { paths: [root] }));
    } catch {
      // try next root
    }
  }
  if (!importerPkg) return null;
  try {
    const importerDir = path.dirname(
      require.resolve(`${importerPkg}/package.json`, { paths: [projectRoot, monorepoRoot] }),
    );
    const parts = pkgName.split("/");
    const candidate = path.join(importerDir, "..", ...parts);
    if (fs.existsSync(path.join(candidate, "package.json"))) return candidate;
  } catch {
    // optional fallback
  }
  return null;
}

const pnpmPeerFixes = {
  "@expo/metro-runtime": resolvePackageDir("@expo/metro-runtime", "expo-router"),
};
const extraNodeModules = { ...(config.resolver.extraNodeModules || {}) };
for (const [name, dir] of Object.entries(pnpmPeerFixes)) {
  if (dir) extraNodeModules[name] = dir;
}
if (Object.keys(extraNodeModules).length > 0) {
  config.resolver.extraNodeModules = extraNodeModules;
}

// Windows + pnpm: Metro's FallbackWatcher crashes on Firebase's deep
// web-only subtrees (errno UNKNOWN on long .pnpm paths). Native/RN uses
// @react-native-firebase; web sign-in only needs firebase/app + firebase/auth.
const FIREBASE_WEB_ONLY =
  /[\\/]node_modules(?:[\\/]\.pnpm[\\/][^\\/]+[\\/]node_modules)?[\\/]firebase[\\/](?:auth[\\/]web-extension|auth[\\/]cordova|firestore[\\/]lite)(?:[\\/]|$)/;

/** Metro's exclusionList — inlined so pnpm does not need a hoisted metro-config. */
function exclusionList(additionalExclusions) {
  return new RegExp(
    "(?:"
      + additionalExclusions
        .map((exclusion) =>
          exclusion instanceof RegExp
            ? `(?:${exclusion.source})`
            : `(?:${String(exclusion)})`,
        )
        .join("|")
      + ")$",
  );
}

const blockPatterns = [FIREBASE_WEB_ONLY];
if (config.resolver.blockList) blockPatterns.unshift(config.resolver.blockList);
config.resolver.blockList = exclusionList(blockPatterns);

const defaultExclusions = config.watcher?.additionalExclusions;
config.watcher = {
  ...config.watcher,
  additionalExclusions: [
    ...(Array.isArray(defaultExclusions) ? defaultExclusions : []),
    FIREBASE_WEB_ONLY,
  ],
};

module.exports = config;
