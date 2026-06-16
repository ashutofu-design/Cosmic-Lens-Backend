/** One-time helper: extract Love Reality result widgets to separate file (breaks circular import). */
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const src = path.join(root, "components/loveReality/LoveRealityBasicScreen.tsx");
const out = path.join(root, "components/loveReality/LoveRealityResultWidgets.tsx");

const lines = fs.readFileSync(src, "utf8").split(/\r?\n/);
const header = `import React, { useEffect, useRef, useState } from "react";
import { Animated, Easing, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Circle } from "react-native-svg";
import type { ChartProof } from "@/lib/loveRealityChartProof";
import {
  loyaltyCompareVerdict,
  type FutureOutcomeDetail,
  type LoveCompatDetail,
  type LoveRealityBasicDisplay,
  type LoyaltyCompareData,
} from "@/lib/loveRealityToolMappers";

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
`;

const body = lines.slice(71, 929).join("\n");
fs.writeFileSync(out, header + body + "\n", "utf8");
console.log("Wrote", out);
