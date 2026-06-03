import React from "react";
import { Platform, StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";

import { GalaxyCinematicCanvas } from "@/components/GalaxyCinematicCanvas";
import { GALAXY_CINEMATIC_HTML } from "@/lib/galaxyCinematicHtml";

function GalaxyNativeCanvas() {
  return (
    <WebView
      source={{ html: GALAXY_CINEMATIC_HTML }}
      style={StyleSheet.absoluteFill}
      containerStyle={styles.webviewContainer}
      scrollEnabled={false}
      bounces={false}
      overScrollMode="never"
      showsHorizontalScrollIndicator={false}
      showsVerticalScrollIndicator={false}
      pointerEvents="none"
      originWhitelist={["*"]}
      javaScriptEnabled
      domStorageEnabled
      cacheEnabled={false}
      allowsInlineMediaPlayback
      mediaPlaybackRequiresUserAction={false}
      setSupportMultipleWindows={false}
      startInLoadingState={false}
      backgroundColor="#000000"
    />
  );
}

export function GalaxyStarfield() {
  const isWeb = Platform.OS === "web";

  return (
    <View style={[StyleSheet.absoluteFill, styles.root]} pointerEvents="none">
      <View style={styles.canvasLayer}>
        {isWeb ? <GalaxyCinematicCanvas /> : <GalaxyNativeCanvas />}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    backgroundColor: "#000000",
  },
  canvasLayer: {
    ...StyleSheet.absoluteFillObject,
  },
  webviewContainer: {
    backgroundColor: "transparent",
  },
});
