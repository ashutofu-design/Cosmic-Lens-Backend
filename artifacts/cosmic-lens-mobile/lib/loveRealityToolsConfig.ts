import type { LoveRealityToolKey } from "@/lib/loveRealityToolMappers";

export type LoveRealityToolDef = {
  key: LoveRealityToolKey;
  shortLabel: string;
  title: string;
  emoji: string;
  iconColor: string;
  gradient: [string, string];
  apiPath: string;
};

export const LOVE_REALITY_TOOLS: LoveRealityToolDef[] = [
  {
    key: "love-compat",
    shortLabel: "Love",
    title: "Love Compatibility",
    emoji: "💘",
    iconColor: "#f472b6",
    gradient: ["#ec4899", "#f472b6"],
    apiPath: "/api/love-compatibility",
  },
  {
    key: "breakup",
    shortLabel: "Breakup",
    title: "Breakup Chances",
    emoji: "💔",
    iconColor: "#f87171",
    gradient: ["#ef4444", "#f87171"],
    apiPath: "/api/breakup-chances",
  },
  {
    key: "loyalty",
    shortLabel: "Loyalty",
    title: "Loyalty Check",
    emoji: "🛡️",
    iconColor: "#fb923c",
    gradient: ["#f97316", "#fb923c"],
    apiPath: "/api/loyalty-check",
  },
  {
    key: "will-return",
    shortLabel: "Return",
    title: "Will X Return?",
    emoji: "🪃",
    iconColor: "#fbbf24",
    gradient: ["#f59e0b", "#fbbf24"],
    apiPath: "/api/will-return",
  },
  {
    key: "future-outcome",
    shortLabel: "Future",
    title: "Future Outcome",
    emoji: "🔮",
    iconColor: "#c084fc",
    gradient: ["#a855f7", "#c084fc"],
    apiPath: "/api/future-outcome",
  },
];

export function toolDefForKey(key: string): LoveRealityToolDef {
  return LOVE_REALITY_TOOLS.find(t => t.key === key) ?? LOVE_REALITY_TOOLS[0]!;
}
