import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";

interface Feature {
  key: string;
  title: string;
  subtitle: string;
  emoji: string;
  iconColor: string;
  gradient: [string, string];
  pro?: boolean;
  route?: string;
}

const MARRIAGE_FEATURES: Feature[] = [
  {
    key: "kundli-milan",
    title: "Kundli Milan",
    subtitle: "36 Gunas · Ashtakoot match analysis",
    emoji: "🔗",
    iconColor: "#818cf8",
    gradient: ["#6366f1", "#818cf8"],
    pro: true,
    route: "/kundli-milan",
  },
];

const LOVE_FEATURES: Feature[] = [
  {
    key: "love-compat",
    title: "Love Compatibility",
    subtitle: "How deep is your connection?",
    emoji: "💘",
    iconColor: "#f472b6",
    gradient: ["#ec4899", "#f472b6"],
  },
  {
    key: "breakup",
    title: "Breakup Chances",
    subtitle: "What threatens your bond?",
    emoji: "💔",
    iconColor: "#f87171",
    gradient: ["#ef4444", "#f87171"],
  },
  {
    key: "loyalty",
    title: "Loyalty Check",
    subtitle: "How faithful is the connection?",
    emoji: "🛡️",
    iconColor: "#fb923c",
    gradient: ["#f97316", "#fb923c"],
  },
  {
    key: "will-return",
    title: "Will X Return?",
    subtitle: "Chances of reconnection",
    emoji: "🪃",
    iconColor: "#fbbf24",
    gradient: ["#f59e0b", "#fbbf24"],
  },
  {
    key: "future-outcome",
    title: "Future Outcome",
    subtitle: "Where is this relationship headed?",
    emoji: "🔮",
    iconColor: "#c084fc",
    gradient: ["#a855f7", "#c084fc"],
  },
];

function FeatureCard({
  feature,
  index,
  isDark,
  sectionDelay,
}: {
  feature: Feature;
  index: number;
  isDark: boolean;
  sectionDelay: number;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.15)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const entrance = Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        delay: sectionDelay + index * 90,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        delay: sectionDelay + index * 90,
        useNativeDriver: true,
        speed: 14,
        bounciness: 4,
      }),
    ]);
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 0.35,
          duration: 2500,
          delay: index * 200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: 0.1,
          duration: 2500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, {
          toValue: 1.12,
          duration: 1300,
          delay: index * 100,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowPulse, {
          toValue: 1,
          duration: 1300,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    entrance.start();
    glow.start();
    arrow.start();
    return () => {
      glow.stop();
      arrow.stop();
    };
  }, []);

  const [c1, c2] = feature.gradient;

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.96, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.7, duration: 100, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }),
      Animated.timing(glowAnim, { toValue: 0.15, duration: 400, useNativeDriver: true }),
    ]).start();
  }

  return (
    <Animated.View
      style={{
        transform: [{ scale: scaleAnim }, { translateY: slideAnim }],
        opacity: fadeAnim,
      }}
    >
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          if (feature.route) router.push(feature.route as any);
        }}
      >
        <View
          style={[
            s.featureCard,
            {
              shadowColor: feature.iconColor,
              shadowOpacity: isDark ? 0.3 : 0.12,
              shadowRadius: 18,
              shadowOffset: { width: 0, height: 5 },
              elevation: 7,
            },
          ]}
        >
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 40 : 55}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View
            style={[
              StyleSheet.absoluteFill,
              {
                backgroundColor: isDark ? "rgba(14,22,42,0.72)" : "rgba(255,255,255,0.94)",
                borderRadius: 20,
              },
            ]}
          />

          <Animated.View
            style={[
              StyleSheet.absoluteFill,
              { overflow: "hidden", borderRadius: 20, opacity: glowAnim },
            ]}
          >
            <LinearGradient
              colors={
                isDark
                  ? [`${feature.iconColor}20`, `${feature.iconColor}08`, "transparent"]
                  : [`${feature.iconColor}10`, `${feature.iconColor}04`, "transparent"]
              }
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          <View
            style={[
              StyleSheet.absoluteFill,
              {
                borderRadius: 20,
                borderWidth: isDark ? 1 : 0.5,
                borderColor: isDark ? `${feature.iconColor}28` : `${feature.iconColor}0C`,
              },
            ]}
          />

          {isDark && (
            <LinearGradient
              colors={["rgba(255,255,255,0.04)", "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={[StyleSheet.absoluteFill, { borderRadius: 20, height: "50%" }]}
            />
          )}

          <View style={s.featureRow}>
            <LinearGradient
              colors={[c1, c2]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.featureIcon}
            >
              <Text style={s.featureEmoji}>{feature.emoji}</Text>
            </LinearGradient>

            <View style={s.featureText}>
              <View style={s.featureTitleRow}>
                <Text
                  style={[
                    s.featureTitle,
                    {
                      color: isDark ? "#fff" : "#0F172A",
                      fontFamily: "Nunito_700Bold",
                    },
                  ]}
                >
                  {feature.title}
                </Text>
                {feature.pro && (
                  <LinearGradient
                    colors={["#f59e0b", "#d97706"]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={s.proBadge}
                  >
                    <Text style={s.proText}>PRO</Text>
                  </LinearGradient>
                )}
              </View>
              <Text
                style={[
                  s.featureSub,
                  {
                    color: isDark ? "rgba(203,213,225,0.7)" : "#64748B",
                    fontFamily: "Nunito_500Medium",
                  },
                ]}
                numberOfLines={1}
              >
                {feature.subtitle}
              </Text>
            </View>

            <Animated.View
              style={{
                transform: [{ scale: arrowPulse }],
                shadowColor: feature.iconColor,
                shadowOpacity: isDark ? 0.5 : 0.2,
                shadowRadius: 12,
                shadowOffset: { width: 0, height: 3 },
                elevation: 6,
              }}
            >
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={s.arrowCircle}
              >
                <Feather name="chevron-right" size={16} color="#fff" />
              </LinearGradient>
            </Animated.View>
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

function SectionBlock({
  title,
  subtitle,
  emoji,
  gradient,
  isDark,
  delay,
  features,
  sectionDelay,
  highlighted,
  highlightTag,
}: {
  title: string;
  subtitle: string;
  emoji: string;
  gradient: [string, string];
  isDark: boolean;
  delay: number;
  features: Feature[];
  sectionDelay: number;
  highlighted?: boolean;
  highlightTag?: string;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(-16)).current;
  const glowPulse = useRef(new Animated.Value(0.15)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        delay,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        delay,
        useNativeDriver: true,
        speed: 12,
        bounciness: 5,
      }),
    ]).start();

    if (highlighted) {
      const glow = Animated.loop(
        Animated.sequence([
          Animated.timing(glowPulse, {
            toValue: 0.35,
            duration: 2500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(glowPulse, {
            toValue: 0.12,
            duration: 2500,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ])
      );
      glow.start();
      return () => glow.stop();
    }
  }, []);

  const [g1, g2] = gradient;

  return (
    <Animated.View
      style={[
        s.sectionWrap,
        { opacity: fadeAnim, transform: [{ translateY: slideAnim }] },
      ]}
    >
      <View
        style={[
          s.sectionContainer,
          {
            shadowColor: highlighted ? g1 : "transparent",
            shadowOpacity: isDark && highlighted ? 0.25 : 0,
            shadowRadius: highlighted ? 24 : 0,
            shadowOffset: { width: 0, height: highlighted ? 8 : 0 },
            elevation: highlighted ? 6 : 0,
          },
        ]}
      >
        {Platform.OS !== "web" ? (
          <BlurView
            intensity={isDark ? 25 : 40}
            tint={isDark ? "dark" : "light"}
            style={StyleSheet.absoluteFill}
          />
        ) : null}
        <View
          style={[
            StyleSheet.absoluteFill,
            {
              backgroundColor: isDark
                ? highlighted ? "rgba(20,12,30,0.65)" : "rgba(10,16,32,0.5)"
                : highlighted ? "rgba(255,245,250,0.92)" : "rgba(248,250,255,0.9)",
              borderRadius: 24,
            },
          ]}
        />

        {highlighted && (
          <Animated.View
            style={[
              StyleSheet.absoluteFill,
              { overflow: "hidden", borderRadius: 24, opacity: glowPulse },
            ]}
          >
            <LinearGradient
              colors={isDark ? [`${g1}18`, `${g2}08`, "transparent"] : [`${g1}0C`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>
        )}

        <View
          style={[
            StyleSheet.absoluteFill,
            {
              borderRadius: 24,
              borderWidth: isDark ? 1 : 0.5,
              borderColor: isDark
                ? highlighted ? `${g1}30` : "rgba(255,255,255,0.06)"
                : highlighted ? `${g1}18` : "rgba(0,0,0,0.04)",
            },
          ]}
        />

        <View style={s.sectionInner}>
          <View style={s.sectionHeaderRow}>
            <LinearGradient
              colors={gradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.sectionBadge}
            >
              <Text style={s.sectionBadgeEmoji}>{emoji}</Text>
              <Text style={s.sectionBadgeText}>{title.toUpperCase()}</Text>
            </LinearGradient>

            {highlighted && highlightTag && (
              <View style={[s.hotTag, {
                backgroundColor: isDark ? "rgba(239,68,68,0.15)" : "rgba(239,68,68,0.1)",
                borderColor: isDark ? "rgba(239,68,68,0.3)" : "rgba(239,68,68,0.2)",
              }]}>
                <Text style={s.hotTagText}>🔥 {highlightTag}</Text>
              </View>
            )}
          </View>

          <Text
            style={[
              s.sectionTitle,
              {
                color: isDark ? "#fff" : "#0F172A",
                fontFamily: "Nunito_700Bold",
              },
            ]}
          >
            {title}
          </Text>
          <Text
            style={[
              s.sectionSub,
              {
                color: isDark ? "rgba(203,213,225,0.5)" : "#64748B",
                fontFamily: "Nunito_400Regular",
              },
            ]}
          >
            {subtitle}
          </Text>

          <View style={s.sectionDivider}>
            <LinearGradient
              colors={[
                "transparent",
                isDark ? `${g1}25` : `${g1}15`,
                "transparent",
              ]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.sectionDividerLine}
            />
          </View>

          <View style={s.featureList}>
            {features.map((f, i) => (
              <FeatureCard
                key={f.key}
                feature={f}
                index={i}
                isDark={isDark}
                sectionDelay={sectionDelay}
              />
            ))}
          </View>
        </View>
      </View>
    </Animated.View>
  );
}

function SectionSpacer({ isDark }: { isDark: boolean }) {
  return (
    <View style={s.spacerWrap}>
      <LinearGradient
        colors={[
          "transparent",
          isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
          "transparent",
        ]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={s.spacerLine}
      />
      <View style={[s.spacerIcon, {
        backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.03)",
      }]}>
        <Text style={{ fontSize: 10 }}>✦</Text>
      </View>
      <LinearGradient
        colors={[
          "transparent",
          isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
          "transparent",
        ]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
        style={s.spacerLine}
      />
    </View>
  );
}

export default function RelationshipScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad =
    Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;
  const ac = isDark ? "#f59e0b" : "#7C3AED";

  const headerFade = useRef(new Animated.Value(0)).current;
  const headerSlide = useRef(new Animated.Value(-20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, {
        toValue: 1,
        duration: 700,
        useNativeDriver: true,
      }),
      Animated.spring(headerSlide, {
        toValue: 0,
        useNativeDriver: true,
        speed: 12,
        bounciness: 5,
      }),
    ]).start();
  }, []);

  return (
    <CosmicBg>
      <LinearGradient
        colors={
          isDark
            ? ["rgba(0,0,0,0.35)", "transparent", "rgba(0,0,0,0.2)"]
            : ["rgba(255,255,255,0.15)", "transparent", "rgba(255,255,255,0.08)"]
        }
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View style={[s.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
          style={s.backBtn}
        >
          <View
            style={[
              s.backCircle,
              {
                backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
                borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
              },
            ]}
          >
            <Feather
              name="arrow-left"
              size={20}
              color={isDark ? "#fff" : "#0F172A"}
            />
          </View>
        </Pressable>
      </View>

      <ScrollView
        style={s.root}
        contentContainerStyle={[
          s.content,
          { paddingTop: topPad + 60, paddingBottom: botPad + 40 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View
          style={[
            s.heroWrap,
            { opacity: headerFade, transform: [{ translateY: headerSlide }] },
          ]}
        >
          <View style={s.heroEmojiWrap}>
            <LinearGradient
              colors={["#ff4d8d", "#c026d3"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.heroEmojiCircle}
            >
              <Text style={s.heroEmoji}>💕</Text>
            </LinearGradient>
            <View style={s.heroEmojiGlow} />
          </View>
          <Text
            style={[
              s.heroTitle,
              {
                color: isDark ? "#fff" : "#0F172A",
                fontFamily: "Nunito_700Bold",
              },
            ]}
          >
            Relationship
          </Text>
          <Text
            style={[
              s.heroSub,
              {
                color: isDark ? "rgba(203,213,225,0.5)" : "#64748B",
                fontFamily: "Nunito_400Regular",
              },
            ]}
          >
            Discover your love destiny & marriage potential
          </Text>

          <View style={s.pathHint}>
            <View style={[s.pathCard, {
              backgroundColor: isDark ? "rgba(239,68,68,0.12)" : "rgba(239,68,68,0.07)",
              borderColor: isDark ? "rgba(239,68,68,0.25)" : "rgba(239,68,68,0.15)",
            }]}>
              <Text style={[s.pathEmoji]}>🔥</Text>
              <Text style={[s.pathLabel, { color: isDark ? "rgba(255,255,255,0.7)" : "#475569", fontFamily: "Nunito_700Bold" }]}>Love / BF-GF</Text>
            </View>
            <View style={[s.pathDot, { backgroundColor: isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.1)" }]} />
            <View style={[s.pathCard, {
              backgroundColor: isDark ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.05)",
              borderColor: isDark ? "rgba(99,102,241,0.15)" : "rgba(99,102,241,0.08)",
            }]}>
              <Text style={[s.pathEmoji]}>💍</Text>
              <Text style={[s.pathLabel, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748B", fontFamily: "Nunito_600SemiBold" }]}>Marriage</Text>
            </View>
          </View>
        </Animated.View>

        <SectionBlock
          title="Love Reality Check"
          subtitle="Know the truth about your relationship"
          emoji="🔥"
          gradient={["#ef4444", "#f97316"]}
          isDark={isDark}
          delay={200}
          features={LOVE_FEATURES}
          sectionDelay={350}
          highlighted
          highlightTag="Most Used"
        />

        <SectionSpacer isDark={isDark} />

        <SectionBlock
          title="Marriage Compatibility"
          subtitle="Check long-term marriage potential"
          emoji="💍"
          gradient={["#6366f1", "#818cf8"]}
          isDark={isDark}
          delay={550}
          features={MARRIAGE_FEATURES}
          sectionDelay={650}
        />

        <View
          style={[
            s.comingSoonCard,
            {
              borderColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
              borderWidth: isDark ? 1 : 0,
              shadowColor: isDark ? ac : "rgba(80,60,120,0.12)",
              shadowOpacity: isDark ? 0.06 : 0.15,
              shadowRadius: 12,
              shadowOffset: { width: 0, height: 4 },
              elevation: 3,
            },
          ]}
        >
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 30 : 45}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View
            style={[
              StyleSheet.absoluteFill,
              {
                backgroundColor: isDark
                  ? "rgba(14,22,42,0.5)"
                  : "rgba(255,255,255,0.88)",
                borderRadius: 20,
              },
            ]}
          />
          <View style={s.comingSoonRow}>
            <View
              style={[
                s.comingSoonIcon,
                { backgroundColor: isDark ? `${ac}12` : `${ac}0A` },
              ]}
            >
              <Feather name="lock" size={16} color={ac} />
            </View>
            <View style={{ flex: 1 }}>
              <Text
                style={[
                  s.comingSoonTitle,
                  {
                    color: isDark ? "rgba(255,255,255,0.55)" : "#475569",
                    fontFamily: "Nunito_600SemiBold",
                  },
                ]}
              >
                More features coming soon
              </Text>
              <Text
                style={[
                  s.comingSoonSub,
                  {
                    color: isDark ? "rgba(255,255,255,0.3)" : "#94A3B8",
                    fontFamily: "Nunito_400Regular",
                  },
                ]}
              >
                Ex Analysis, Secret Crush & more
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
  content: { paddingHorizontal: 16 },

  topBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    zIndex: 20,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  backBtn: { alignSelf: "flex-start" },
  backCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },

  heroWrap: { alignItems: "center", marginBottom: 24, gap: 8 },
  heroEmojiWrap: { alignItems: "center", justifyContent: "center", marginBottom: 8 },
  heroEmojiCircle: {
    width: 76,
    height: 76,
    borderRadius: 38,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.15)",
  },
  heroEmoji: { fontSize: 36 },
  heroEmojiGlow: {
    position: "absolute",
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: "rgba(255,77,141,0.12)",
    zIndex: -1,
  },
  heroTitle: { fontSize: 28, letterSpacing: -0.5, textAlign: "center" },
  heroSub: { fontSize: 13.5, textAlign: "center", letterSpacing: 0.2, maxWidth: 260 },

  pathHint: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginTop: 14,
  },
  pathCard: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 14,
    borderWidth: 1,
  },
  pathEmoji: { fontSize: 14 },
  pathLabel: { fontSize: 11.5, letterSpacing: 0.1 },
  pathDot: { width: 4, height: 4, borderRadius: 2 },

  sectionWrap: { marginBottom: 6 },
  sectionContainer: {
    borderRadius: 24,
    overflow: "hidden",
  },
  sectionInner: { padding: 18, paddingTop: 16 },

  sectionHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  sectionBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 20,
  },
  sectionBadgeEmoji: { fontSize: 11 },
  sectionBadgeText: {
    color: "#fff",
    fontSize: 8.5,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.6,
  },
  sectionTitle: { fontSize: 21, letterSpacing: -0.3 },
  sectionSub: { fontSize: 12.5, marginTop: 3, letterSpacing: 0.15 },

  hotTag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  hotTagText: {
    fontSize: 9,
    fontFamily: "Nunito_700Bold",
    color: "#ef4444",
    letterSpacing: 0.3,
  },

  sectionDivider: { marginVertical: 14 },
  sectionDividerLine: { height: 1 },

  featureList: { gap: 12 },

  featureCard: {
    borderRadius: 20,
    overflow: "hidden",
  },
  featureRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    paddingVertical: 18,
    gap: 14,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  featureEmoji: { fontSize: 21 },
  featureText: { flex: 1, gap: 3 },
  featureTitleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  featureTitle: { fontSize: 16, letterSpacing: -0.2 },
  featureSub: { fontSize: 11.5, letterSpacing: 0.1 },

  proBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2.5,
    borderRadius: 8,
  },
  proText: {
    color: "#fff",
    fontSize: 8,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.2,
  },

  arrowCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: "rgba(255,255,255,0.18)",
  },

  spacerWrap: {
    flexDirection: "row",
    alignItems: "center",
    marginVertical: 18,
    gap: 8,
    paddingHorizontal: 20,
  },
  spacerLine: { flex: 1, height: 1 },
  spacerIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },

  comingSoonCard: {
    borderRadius: 20,
    overflow: "hidden",
    padding: 16,
    marginTop: 14,
    marginBottom: 20,
  },
  comingSoonRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  comingSoonIcon: {
    width: 40,
    height: 40,
    borderRadius: 13,
    alignItems: "center",
    justifyContent: "center",
  },
  comingSoonTitle: { fontSize: 13, letterSpacing: 0.1 },
  comingSoonSub: { fontSize: 11, marginTop: 2 },
});
