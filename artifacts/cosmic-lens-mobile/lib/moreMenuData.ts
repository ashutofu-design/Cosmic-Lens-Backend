import type { useT } from "@/hooks/useT";

export type MoreFeatureItem = {
  id: string;
  icon: string;
  emoji: string;
  title: string;
  subtitle: string;
  route: string;
  accent: string;
  badge?: string;
};

export type MoreMenuCategory = {
  title: string;
  items: MoreFeatureItem[];
};

/** More drawer — daily tools, kundli charts, milan, saved reports. */
export function buildMoreDrawerCategories(t: ReturnType<typeof useT>): MoreMenuCategory[] {
  return [
    {
      title: `${t.catPanchang} & ${t.catMuhurat}`,
      items: [
        {
          id: "panchang",
          icon: "calendar",
          emoji: "🗓️",
          title: `${t.catPanchang} & ${t.catMuhurat}`,
          subtitle: `${t.mdPanchangSub} · ${t.mdMuhuratSub}`,
          route: "/panchang",
          accent: "#a78bfa",
          badge: "Daily",
        },
      ],
    },
    {
      title: "Kundli & Charts",
      items: [
        {
          id: "planet-position",
          icon: "target",
          emoji: "🪐",
          title: t.ku_planetPosition,
          subtitle: `${t.ku_planetPositionSub} · ${t.mdDivisionalSub}`,
          route: "/planet-position",
          accent: "#06b6d4",
          badge: "Live",
        },
      ],
    },
    {
      title: "My Library",
      items: [
        {
          id: "my-reports",
          icon: "folder",
          emoji: "📁",
          title: t.mr_pageTitle,
          subtitle: "Saved PDFs — Milan, Numerology, AstroVastu & more",
          route: "/my-reports",
          accent: "#f6c453",
        },
      ],
    },
  ];
}
