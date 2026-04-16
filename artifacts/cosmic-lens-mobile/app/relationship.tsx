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

interface MainOption {
  key: string;
  title: string;
  subtitle: string;
  emoji: string;
  gradient: [string, string, string];
  glowColor: string;
  route: string;
  highlighted?: boolean;
  badge?: string;
  desc: string;
  items: string[];
}

const OPTIONS: MainOption[] = [
  {
    key: "love",
    title: "Love Reality Check",
    subtitle: "Reveal the hidden truth about your relationship",
    emoji: "🔥",
    gradient: ["#f97316", "#ec4899", "#ef4444"],
    glowColor: "#ef4444",
    route: "/love-reality",
    highlighted: true,
    badge: "🔥 Most Used",
    desc: "For current relationships & BF/GF",
    items: ["Love Compatibility", "Breakup Chances", "Loyalty Check", "Will X Return", "Future Outcome"],
  },
  {
    key: "marriage",
    title: "Marriage Compatibility",
    subtitle: "Check long-term marriage potential",
    emoji: "💍",
    gradient: ["#6366f1", "#818cf8", "#a78bfa"],
    glowColor: "#6366f1",
    route: "/marriage-compat",
    desc: "For serious & marriage decisions",
    items: ["Kundli Milan (Pro)"],
  },
];

function OptionCard({
  option,
  index,
  isDark,
}: {
  option: MainOption;
  index: number;
  isDark: boolean;
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(40)).current;
  const glowAnim = useRef(new Animated.Value(0.15)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;
  const arrowGlow = useRef(new Animated.Value(0.7)).current;
  const chipGlow = useRef(new Animated.Value(0)).current;

  const isHL = !!option.highlighted;
  const [c1, c2, c3] = option.gradient;

  useEffect(() => {
    const entrance = Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 700,
        delay: 250 + index * 180,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        delay: 250 + index * 180,
        useNativeDriver: true,
        speed: 12,
        bounciness: 6,
      }),
    ]);
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: isHL ? 0.65 : 0.35,
          duration: 3000,
          delay: index * 350,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: isHL ? 0.2 : 0.08,
          duration: 3000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const arrow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowPulse, {
          toValue: isHL ? 1.18 : 1.1,
          duration: 1400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowPulse, {
          toValue: 1,
          duration: 1400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const aGlow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowGlow, {
          toValue: 1,
          duration: 1600,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowGlow, {
          toValue: 0.55,
          duration: 1600,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    const cGlow = Animated.loop(
      Animated.sequence([
        Animated.timing(chipGlow, {
          toValue: 1,
          duration: 2200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(chipGlow, {
          toValue: 0,
          duration: 2200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    entrance.start();
    glow.start();
    arrow.start();
    aGlow.start();
    if (isHL) cGlow.start();
    return () => { glow.stop(); arrow.stop(); aGlow.stop(); cGlow.stop(); };
  }, []);

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.9, duration: 100, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 14, bounciness: 12 }),
      Animated.timing(glowAnim, { toValue: isHL ? 0.3 : 0.12, duration: 500, useNativeDriver: true }),
    ]).start();
  }

  const cardBg = isDark
    ? isHL ? "rgba(35,10,20,0.8)" : "rgba(12,16,34,0.65)"
    : isHL ? "rgba(255,242,248,0.96)" : "rgba(248,248,255,0.95)";

  const bRadius = isHL ? 28 : 22;

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }, { translateY: slideAnim }], opacity: fadeAnim }}>
      <Pressable
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          router.push(option.route as any);
        }}
      >
        {isHL && isDark && (
          <Animated.View style={[s.radialGlow, { opacity: glowAnim }]}>
            <LinearGradient
              colors={[`${c1}30`, `${c2}18`, "transparent"]}
              start={{ x: 0.5, y: 0.5 }}
              end={{ x: 0.5, y: 0 }}
              style={[StyleSheet.absoluteFill, { borderRadius: 60 }]}
            />
          </Animated.View>
        )}

        <View style={[
          s.card,
          { borderRadius: bRadius },
          {
            shadowColor: option.glowColor,
            shadowOpacity: isDark ? (isHL ? 0.6 : 0.25) : (isHL ? 0.25 : 0.1),
            shadowRadius: isHL ? 40 : 20,
            shadowOffset: { width: 0, height: isHL ? 14 : 6 },
            elevation: isHL ? 16 : 8,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 45 : 60}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, { backgroundColor: cardBg, borderRadius: bRadius }]} />

          <Animated.View style={[StyleSheet.absoluteFill, { overflow: "hidden", borderRadius: bRadius, opacity: glowAnim }]}>
            <LinearGradient
              colors={isDark
                ? [`${c1}30`, `${c2}15`, `${c3}08`, "transparent"]
                : [`${c1}18`, `${c2}0A`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          {isDark && (
            <LinearGradient
              colors={[`${option.glowColor}0C`, "transparent"]}
              start={{ x: 0.5, y: 1 }}
              end={{ x: 0.5, y: 0.2 }}
              style={[StyleSheet.absoluteFill, { borderRadius: bRadius }]}
            />
          )}

          {isHL && isDark && (
            <Animated.View style={[StyleSheet.absoluteFill, { borderRadius: bRadius, opacity: glowAnim }]}>
              <LinearGradient
                colors={[`${c1}12`, `${c2}08`, "transparent", `${c3}06`]}
                start={{ x: 0, y: 1 }}
                end={{ x: 1, y: 0 }}
                locations={[0, 0.3, 0.6, 1]}
                style={StyleSheet.absoluteFill}
              />
            </Animated.View>
          )}

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: bRadius,
            borderWidth: isDark ? 1.5 : 0.5,
            borderColor: isDark
              ? `${option.glowColor}${isHL ? "50" : "22"}`
              : `${option.glowColor}${isHL ? "20" : "0C"}`,
          }]} />

          <LinearGradient
            colors={isDark
              ? ["rgba(255,255,255,0.06)", "transparent"]
              : ["rgba(255,255,255,0.5)", "transparent"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 0, y: 1 }}
            style={[StyleSheet.absoluteFill, { borderRadius: bRadius, height: "35%" }]}
          />

          {isHL && option.badge && (
            <View style={s.badgeWrap}>
              <Animated.View style={{ opacity: Animated.add(0.85, Animated.multiply(chipGlow, 0.15)) }}>
                <LinearGradient
                  colors={[c1, c2]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[s.badgePill, {
                    shadowColor: c1,
                    shadowOpacity: isDark ? 0.5 : 0.2,
                    shadowRadius: 10,
                    shadowOffset: { width: 0, height: 3 },
                    elevation: 6,
                  }]}
                >
                  <Text style={s.badgeText}>{option.badge.toUpperCase()}</Text>
                </LinearGradient>
              </Animated.View>
            </View>
          )}

          <View style={[s.cardContent, isHL && s.cardContentHL]}>
            <View style={s.cardTop}>
              <LinearGradient
                colors={[c1, c2, c3]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.emojiCircle, isHL && s.emojiCircleHL, {
                  shadowColor: c1,
                  shadowOpacity: isDark ? 0.5 : 0.2,
                  shadowRadius: isHL ? 16 : 10,
                  shadowOffset: { width: 0, height: 4 },
                  elevation: isHL ? 10 : 5,
                }]}
              >
                <Text style={[s.emoji, isHL && s.emojiHL]}>{option.emoji}</Text>
              </LinearGradient>

              <View style={s.titleArea}>
                <Text style={[
                  s.cardTitle,
                  isHL && s.cardTitleHL,
                  { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" },
                ]}>
                  {option.title}
                </Text>
                <Text style={[
                  s.cardSub,
                  isHL && s.cardSubHL,
                  { color: isDark ? "rgba(203,213,225,0.7)" : "#64748B", fontFamily: "Nunito_500Medium" },
                ]} numberOfLines={2}>
                  {option.subtitle}
                </Text>
              </View>

              <Animated.View style={{
                transform: [{ scale: arrowPulse }],
                opacity: arrowGlow,
              }}>
                <LinearGradient
                  colors={[c1, c2]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={[s.arrowCircle, isHL && s.arrowCircleHL, {
                    shadowColor: option.glowColor,
                    shadowOpacity: isDark ? 0.7 : 0.3,
                    shadowRadius: isHL ? 20 : 12,
                    shadowOffset: { width: 0, height: 4 },
                    elevation: isHL ? 10 : 6,
                  }]}
                >
                  <Feather name="chevron-right" size={isHL ? 22 : 17} color="#fff" />
                </LinearGradient>
              </Animated.View>
            </View>

            <View style={s.descRow}>
              <View style={[s.descTag, {
                backgroundColor: isDark ? `${option.glowColor}14` : `${option.glowColor}0A`,
                borderColor: isDark ? `${option.glowColor}28` : `${option.glowColor}14`,
              }]}>
                <Text style={[s.descText, { color: isDark ? `${option.glowColor}CC` : option.glowColor, fontFamily: "Nunito_600SemiBold" }]}>
                  {option.desc}
                </Text>
              </View>
            </View>

            <View style={s.itemsRow}>
              {option.items.map((item, i) => {
                const chipBg = isDark
                  ? isHL ? `${option.glowColor}0E` : "rgba(255,255,255,0.05)"
                  : isHL ? `${option.glowColor}08` : "rgba(0,0,0,0.03)";
                const chipBorder = isDark
                  ? isHL ? `${option.glowColor}22` : "rgba(255,255,255,0.08)"
                  : isHL ? `${option.glowColor}14` : "rgba(0,0,0,0.05)";
                const chipColor = isDark
                  ? isHL ? "rgba(255,255,255,0.65)" : "rgba(255,255,255,0.5)"
                  : isHL ? "#475569" : "#64748B";

                return (
                  <Animated.View key={i} style={isHL ? {
                    shadowColor: option.glowColor,
                    shadowOpacity: Animated.multiply(chipGlow, isDark ? 0.25 : 0.1) as any,
                    shadowRadius: 6,
                    shadowOffset: { width: 0, height: 2 },
                  } : undefined}>
                    <View style={[s.itemChip, {
                      backgroundColor: chipBg,
                      borderColor: chipBorder,
                    }]}>
                      <Text style={[s.itemText, {
                        color: chipColor,
                        fontFamily: "Nunito_500Medium",
                      }]}>{item}</Text>
                    </View>
                  </Animated.View>
                );
              })}
            </View>

            <LinearGradient
              colors={[c1, c2, c3]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[s.bottomBar, isHL && s.bottomBarHL]}
            />
          </View>
        </View>
      </Pressable>
    </Animated.View>
  );
}

export default function RelationshipScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const headerFade = useRef(new Animated.Value(0)).current;
  const headerSlide = useRef(new Animated.Value(-25)).current;
  const heroGlow = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const entrance = Animated.parallel([
      Animated.timing(headerFade, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.spring(headerSlide, { toValue: 0, useNativeDriver: true, speed: 10, bounciness: 6 }),
    ]);
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(heroGlow, { toValue: 0.6, duration: 2500, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(heroGlow, { toValue: 0.25, duration: 2500, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    );
    entrance.start();
    glow.start();
    return () => { glow.stop(); };
  }, []);

  return (
    <CosmicBg>
      <LinearGradient
        colors={isDark
          ? ["rgba(0,0,0,0.4)", "transparent", "rgba(0,0,0,0.25)"]
          : ["rgba(255,255,255,0.2)", "transparent", "rgba(255,255,255,0.1)"]}
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
          <View style={[s.backCircle, {
            backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            borderColor: isDark ? "rgba(255,255,255,0.14)" : "rgba(0,0,0,0.08)",
          }]}>
            <Feather name="arrow-left" size={20} color={isDark ? "#fff" : "#0F172A"} />
          </View>
        </Pressable>
      </View>

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 60, paddingBottom: botPad + 50 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[s.heroWrap, { opacity: headerFade, transform: [{ translateY: headerSlide }] }]}>
          <View style={s.heroEmojiWrap}>
            <LinearGradient
              colors={["#ff4d8d", "#c026d3", "#9333ea"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={s.heroEmojiCircle}
            >
              <Text style={s.heroEmoji}>💕</Text>
            </LinearGradient>
            <Animated.View style={[s.heroEmojiGlow, { opacity: heroGlow }]} />
            <Animated.View style={[s.heroEmojiGlow2, { opacity: Animated.multiply(heroGlow, 0.5) }]} />
          </View>
          <Text style={[s.heroTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
            Relationship
          </Text>
          <Text style={[s.heroSub, { color: isDark ? "rgba(203,213,225,0.55)" : "#64748B", fontFamily: "Nunito_400Regular" }]}>
            Choose your path to discover the truth
          </Text>
        </Animated.View>

        <View style={s.optionsList}>
          {OPTIONS.map((opt, i) => (
            <OptionCard key={opt.key} option={opt} index={i} isDark={isDark} />
          ))}
        </View>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 20 },

  topBar: {
    position: "absolute",
    top: 0, left: 0, right: 0,
    zIndex: 20,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  backBtn: { alignSelf: "flex-start" },
  backCircle: {
    width: 42, height: 42, borderRadius: 21,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },

  heroWrap: { alignItems: "center", marginBottom: 32, gap: 10 },
  heroEmojiWrap: { alignItems: "center", justifyContent: "center", marginBottom: 10 },
  heroEmojiCircle: {
    width: 80, height: 80, borderRadius: 40,
    alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.18)",
  },
  heroEmoji: { fontSize: 38 },
  heroEmojiGlow: {
    position: "absolute",
    width: 110, height: 110, borderRadius: 55,
    backgroundColor: "rgba(255,77,141,0.15)",
    zIndex: -1,
  },
  heroEmojiGlow2: {
    position: "absolute",
    width: 140, height: 140, borderRadius: 70,
    backgroundColor: "rgba(192,38,211,0.08)",
    zIndex: -2,
  },
  heroTitle: { fontSize: 30, letterSpacing: -0.5, textAlign: "center" },
  heroSub: { fontSize: 14, textAlign: "center", letterSpacing: 0.2, maxWidth: 270 },

  optionsList: { gap: 24 },

  radialGlow: {
    position: "absolute",
    top: -30, left: -20, right: -20, bottom: -30,
    zIndex: -1,
  },

  card: {
    overflow: "hidden",
  },

  badgeWrap: {
    position: "absolute",
    top: 0, right: 0,
    zIndex: 10,
  },
  badgePill: {
    paddingHorizontal: 14, paddingVertical: 6,
    borderBottomLeftRadius: 16,
    borderTopRightRadius: 28,
  },
  badgeText: {
    color: "#fff",
    fontSize: 8.5,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.3,
  },

  cardContent: { padding: 22, paddingTop: 24, gap: 16 },
  cardContentHL: { padding: 24, paddingTop: 26 },

  cardTop: { flexDirection: "row", alignItems: "center", gap: 14 },

  emojiCircle: {
    width: 56, height: 56, borderRadius: 19,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.14)",
  },
  emojiCircleHL: {
    width: 66, height: 66, borderRadius: 22,
  },
  emoji: { fontSize: 25 },
  emojiHL: { fontSize: 30 },

  titleArea: { flex: 1, gap: 5 },
  cardTitle: { fontSize: 18, letterSpacing: -0.2 },
  cardTitleHL: { fontSize: 21 },
  cardSub: { fontSize: 12, letterSpacing: 0.1 },
  cardSubHL: { fontSize: 12.5, lineHeight: 17 },

  arrowCircle: {
    width: 44, height: 44, borderRadius: 22,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.2)",
  },
  arrowCircleHL: {
    width: 52, height: 52, borderRadius: 26,
  },

  descRow: { marginTop: -2 },
  descTag: {
    alignSelf: "flex-start",
    paddingHorizontal: 13, paddingVertical: 6,
    borderRadius: 12,
    borderWidth: 1,
  },
  descText: { fontSize: 10.5, letterSpacing: 0.2 },

  itemsRow: { flexDirection: "row", flexWrap: "wrap", gap: 7 },
  itemChip: {
    paddingHorizontal: 11, paddingVertical: 6,
    borderRadius: 10,
    borderWidth: 1,
  },
  itemText: { fontSize: 10.5, letterSpacing: 0.1 },

  bottomBar: {
    height: 3, borderRadius: 2,
    opacity: 0.5, marginTop: 4,
  },
  bottomBarHL: {
    height: 4, opacity: 0.75,
  },
});
