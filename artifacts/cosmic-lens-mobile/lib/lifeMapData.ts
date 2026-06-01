import type { Feather } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import type { useT } from "@/hooks/useT";

export interface LifeMapCategory {
  key: string;
  icon: ComponentProps<typeof Feather>["name"];
  emoji: string;
  gradient: [string, string];
  glowOuter: [string, string];
  glowColor: string;
  badge: string;
  badgeIcon: string;
  subtitle: string;
  title?: string;
  primary?: boolean;
  route?: string;
  navTab?: string;
  priceInr?: number;
  paywall?: boolean;
}

export const LIFE_MAP_CATEGORIES: LifeMapCategory[] = [
  {
    key: "relationship",
    icon: "heart",
    emoji: "💕",
    gradient: ["#ff4d8d", "#c026d3"],
    glowOuter: ["rgba(255,77,141,0.25)", "rgba(192,38,211,0.12)"],
    glowColor: "#ff4d8d",
    badge: "Most Used",
    badgeIcon: "🔥",
    subtitle: "Love & marriage future insights",
    primary: true,
    route: "/relationship",
  },
  {
    key: "career",
    icon: "briefcase",
    emoji: "🚀",
    gradient: ["#ff7b00", "#fbbf24"],
    glowOuter: ["rgba(255,123,0,0.2)", "rgba(251,191,36,0.08)"],
    glowColor: "#ff9500",
    badge: "Trending",
    badgeIcon: "🚀",
    subtitle: "Career growth & breakthrough insights",
    route: "/career",
    priceInr: 1,
    paywall: true,
  },
  {
    key: "health",
    icon: "activity",
    emoji: "🧘",
    gradient: ["#00e676", "#14b8a6"],
    glowOuter: ["rgba(0,230,118,0.18)", "rgba(20,184,166,0.08)"],
    glowColor: "#00e676",
    badge: "Check Now",
    badgeIcon: "⚠️",
    subtitle: "Energy, sensitivities & wellness",
    route: "/health",
  },
  {
    key: "finance",
    icon: "dollar-sign",
    emoji: "💰",
    gradient: ["#448aff", "#fbbf24"],
    glowOuter: ["rgba(68,138,255,0.2)", "rgba(251,191,36,0.08)"],
    glowColor: "#448aff",
    badge: "Important",
    badgeIcon: "💰",
    subtitle: "Money flow & financial future",
    route: "/finance",
  },
  {
    key: "divya-prashna",
    icon: "help-circle",
    emoji: "🔮",
    gradient: ["#8b5cf6", "#f59e0b"],
    glowOuter: ["rgba(139,92,246,0.22)", "rgba(245,158,11,0.10)"],
    glowColor: "#8b5cf6",
    badge: "KP Horary",
    badgeIcon: "✨",
    subtitle: "Ek hi sawaal — instant verdict (KP 1-249 sub-lord)",
    route: "/divya-prashna",
  },
];

/** Life Map → Explore: PRO tools only (Panchang, reports, charts live in More drawer). */
export function buildExploreCategories(t: ReturnType<typeof useT>): LifeMapCategory[] {
  return [
    {
      key: "numerology-pro",
      icon: "hash",
      emoji: "🔢",
      gradient: ["#a855f7", "#6366f1"],
      glowOuter: ["rgba(168,85,247,0.22)", "rgba(99,102,241,0.1)"],
      glowColor: "#a855f7",
      badge: "PRO",
      badgeIcon: "✨",
      title: t.mdNumerologyTitle,
      subtitle: t.mdNumerologySub,
      route: "/numerology",
    },
    {
      key: "astrovastu-pro",
      icon: "home",
      emoji: "🏠",
      gradient: ["#f59e0b", "#14b8a6"],
      glowOuter: ["rgba(245,158,11,0.22)", "rgba(20,184,166,0.1)"],
      glowColor: "#f59e0b",
      badge: "PRO",
      badgeIcon: "📸",
      title: t.mdVastuTitle,
      subtitle: t.mdVastuSub,
      route: "/astrovastu-pro",
    },
    {
      key: "face-reading-pro",
      icon: "user",
      emoji: "👤",
      gradient: ["#ec4899", "#8b5cf6"],
      glowOuter: ["rgba(236,72,153,0.22)", "rgba(139,92,246,0.1)"],
      glowColor: "#ec4899",
      badge: "PRO",
      badgeIcon: "🔮",
      title: t.mdFaceReadingTitle,
      subtitle: t.mdFaceReadingSub,
      route: "/face-reading",
    },
  ];
}
