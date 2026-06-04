import React from "react";
import { StyleSheet, View } from "react-native";

import { GalaxyCinematicCanvas } from "@/components/GalaxyCinematicCanvas";

export function GalaxyStarfield() {
  return (
    <View style={[StyleSheet.absoluteFill, styles.root]} pointerEvents="none">
      <View style={styles.canvasLayer}>
        <GalaxyCinematicCanvas />
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
});
