import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React from "react";
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { CosmicBg } from "@/components/CosmicBg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

function oa(isDark: boolean, v: string): string { return isDark ? v : v; }

interface Category {
  key: string;
  icon: React.ComponentProps<typeof Feather>["name"];
  emoji: string;
  gradient: [string, string];
  route?: string;
}

const CATEGORIES: Category[] = [
  { key: "relationship", icon: "heart",       emoji: "💕", gradient: ["#ff6b6b", "#ee5a24"] },
  { key: "career",       icon: "briefcase",   emoji: "🚀", gradient: ["#f59e0b", "#d97706"] },
  { key: "health",       icon: "activity",    emoji: "🧘", gradient: ["#10b981", "#059669"] },
  { key: "finance",      icon: "dollar-sign", emoji: "💰", gradient: ["#6366f1", "#4f46e5"] },
];

function CategoryCard({
  cat, index, C, t, o,
}: {
  cat: Category;
  index: number;
  C: ReturnType<typeof useC>;
  t: ReturnType<typeof getT>;
  o: (v: string) => string;
}) {
  const titles: Record<string, string> = {
    relationship: t.relationship,
    career: t.career,
    health: t.health,
    finance: t.finance,
  };
  const subtitles: Record<string, string> = {
    relationship: t.lifeMapRelSub ?? "Love, compatibility & bonds",
    career: t.lifeMapCarSub ?? "Growth, success & purpose",
    health: t.lifeMapHealthSub ?? "Body, mind & vitality",
    finance: t.lifeMapFinSub ?? "Wealth, stability & flow",
  };

  const title = titles[cat.key] || cat.key;
  const sub = subtitles[cat.key];
  const [c1, c2] = cat.gradient;
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";

  return (
    <Pressable
      onPress={() => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        if (cat.route) router.push(cat.route as any);
      }}
      style={({ pressed }) => [pressed && { opacity: 0.85, transform: [{ scale: 0.98 }] }]}
    >
      <View style={[
        s.card,
        {
          backgroundColor: C.bgCard,
          borderColor: o(`${c1}30`),
          shadowColor: c1,
        },
      ]}>
        <View style={s.cardRow}>
          <View style={[s.iconWrap, { backgroundColor: o(`${c1}18`), borderColor: o(`${c1}35`) }]}>
            <Text style={s.emoji}>{cat.emoji}</Text>
          </View>

          <View style={s.cardText}>
            <Text style={[s.cardTitle, { color: C.text }]}>{title}</Text>
            <Text style={[s.cardSub, { color: C.textDim }]} numberOfLines={1}>{sub}</Text>
          </View>

          <View style={[s.arrow, { backgroundColor: o(`${c1}12`) }]}>
            <Feather name="chevron-right" size={16} color={o(c1)} />
          </View>
        </View>

        <View style={[s.bottomBar, { backgroundColor: c1 }]} />
      </View>
    </Pressable>
  );
}

export default function LifeMapScreen() {
  const C = useC();
  const { language } = useUser();
  const t = getT(language);
  const o = (v: string) => oa(C.isDark, v);
  const insets = useSafeAreaInsets();
  const topPad = insets.top;
  const botPad = insets.bottom;
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";

  return (
    <CosmicBg>
      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
        showsVerticalScrollIndicator={false}
      >
        <Text style={[s.heading, { color: C.text }]}>{t.lifeMapTitle ?? "Life Map"}</Text>
        <Text style={[s.subtitle, { color: C.textDim }]}>{t.lifeMapSubtitle ?? "Your life, mapped by the stars"}</Text>

        <View style={s.grid}>
          {CATEGORIES.map((cat, i) => (
            <CategoryCard key={cat.key} cat={cat} index={i} C={C} t={t} o={o} />
          ))}
        </View>

        <View style={[s.footerCard, { backgroundColor: C.bgCard, borderColor: o(`${ac}25`) }]}>
          <View style={s.footerRow}>
            <View style={[s.footerIcon, { backgroundColor: o(`${ac}15`) }]}>
              <Feather name="compass" size={18} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.footerTitle, { color: C.text }]}>
                {t.lifeMapComing ?? "More dimensions coming"}
              </Text>
              <Text style={[s.footerSub, { color: C.textDim }]}>
                {t.lifeMapComingSub ?? "Education, Travel, Spirituality & more"}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 16, gap: 12 },
  heading: { fontSize: 22, fontWeight: "700" },
  subtitle: { fontSize: 13, fontWeight: "400", opacity: 0.7, marginBottom: 4 },

  grid: { gap: 10 },

  card: {
    borderRadius: 16,
    borderWidth: 1,
    overflow: "hidden",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  cardRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    gap: 14,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  emoji: { fontSize: 22 },
  cardText: { flex: 1, gap: 2 },
  cardTitle: { fontSize: 16, fontWeight: "700" },
  cardSub: { fontSize: 12.5, fontWeight: "400" },
  arrow: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  bottomBar: {
    height: 3,
    borderRadius: 2,
    marginHorizontal: 16,
    marginBottom: 2,
    opacity: 0.35,
  },

  footerCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginTop: 6,
    opacity: 0.7,
  },
  footerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  footerIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  footerTitle: { fontSize: 13, fontWeight: "600" },
  footerSub: { fontSize: 11, fontWeight: "400", marginTop: 2 },
});
