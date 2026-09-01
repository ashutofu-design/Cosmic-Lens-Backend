/** @type {import('expo/config').ExpoConfig} */
const appJson = require("./app.json");

function isInstalled(moduleName) {
  try {
    require.resolve(moduleName, { paths: [__dirname] });
    return true;
  } catch {
    return false;
  }
}

const optionalPlugins = new Set(["@react-native-google-signin/google-signin"]);

const isProductionBuild =
  process.env.EAS_BUILD_PROFILE === "production" ||
  process.env.NODE_ENV === "production";

const plugins = appJson.expo.plugins.filter((entry) => {
  const name = Array.isArray(entry) ? entry[0] : entry;
  if (name === "expo-dev-client" && isProductionBuild) {
    return false;
  }
  if (optionalPlugins.has(name)) {
    return isInstalled(name);
  }
  // Legacy custom plugin removed — do not reference even if file exists.
  if (name === "./app.plugin.js") {
    return false;
  }
  return true;
});

if (
  isInstalled("@react-native-google-signin/google-signin")
  && !plugins.some((entry) => {
    const name = Array.isArray(entry) ? entry[0] : entry;
    return name === "@react-native-google-signin/google-signin";
  })
) {
  plugins.push("@react-native-google-signin/google-signin");
}

const defaultApiUrl =
  process.env.EXPO_PUBLIC_API_URL || "https://api.coosmic.icu";

module.exports = {
  ...appJson,
  expo: {
    ...appJson.expo,
    plugins,
    extra: {
      ...(appJson.expo.extra || {}),
      apiUrl: defaultApiUrl,
    },
  },
};
