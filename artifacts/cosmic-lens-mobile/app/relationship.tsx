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
  gradient: [string, string];
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
    subtitle: "Know the truth about your relationship",
    emoji: "🔥",
    gradient: ["#ef4444", "#f97316"],
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
    gradient: ["#6366f1", "#818cf8"],
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
  const slideAnim = useRef(new Animated.Value(30)).current;
  const glowAnim = useRef(new Animated.Value(0.15)).current;
  const arrowPulse = useRef(new Animated.Value(1)).current;
  const arrowGlow = useRef(new Animated.Value(0.6)).current;

  const isHL = !!option.highlighted;
  const [c1, c2] = option.gradient;

  useEffect(() => {
    const entrance = Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        delay: 200 + index * 150,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        delay: 200 + index * 150,
        useNativeDriver: true,
        speed: 14,
        bounciness: 5,
      }),
    ]);
    const glow = Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: isHL ? 0.55 : 0.3,
          duration: 2800,
          delay: index * 300,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowAnim, {
          toValue: isHL ? 0.2 : 0.08,
          duration: 2800,
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
    const aGlow = Animated.loop(
      Animated.sequence([
        Animated.timing(arrowGlow, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(arrowGlow, {
          toValue: 0.5,
          duration: 1500,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ])
    );
    entrance.start();
    glow.start();
    arrow.start();
    aGlow.start();
    return () => { glow.stop(); arrow.stop(); aGlow.stop(); };
  }, []);

  function handlePressIn() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 0.96, useNativeDriver: true, speed: 50, bounciness: 4 }),
      Animated.timing(glowAnim, { toValue: 0.8, duration: 100, useNativeDriver: true }),
    ]).start();
  }
  function handlePressOut() {
    Animated.parallel([
      Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, speed: 18, bounciness: 10 }),
      Animated.timing(glowAnim, { toValue: isHL ? 0.25 : 0.1, duration: 400, useNativeDriver: true }),
    ]).start();
  }

  const cardBg = isDark
    ? isHL ? "rgba(28,10,18,0.75)" : "rgba(12,16,34,0.65)"
    : isHL ? "rgba(255,242,248,0.96)" : "rgba(248,248,255,0.95)";

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
        <View style={[
          s.card,
          {
            shadowColor: option.glowColor,
            shadowOpacity: isDark ? (isHL ? 0.5 : 0.25) : (isHL ? 0.2 : 0.1),
            shadowRadius: isHL ? 30 : 18,
            shadowOffset: { width: 0, height: isHL ? 10 : 6 },
            elevation: isHL ? 12 : 7,
          },
        ]}>
          {Platform.OS !== "web" ? (
            <BlurView
              intensity={isDark ? 40 : 55}
              tint={isDark ? "dark" : "light"}
              style={StyleSheet.absoluteFill}
            />
          ) : null}
          <View style={[StyleSheet.absoluteFill, { backgroundColor: cardBg, borderRadius: isHL ? 26 : 22 }]} />

          <Animated.View style={[StyleSheet.absoluteFill, { overflow: "hidden", borderRadius: isHL ? 26 : 22, opacity: glowAnim }]}>
            <LinearGradient
              colors={isDark
                ? [`${option.glowColor}22`, `${option.glowColor}0A`, "transparent"]
                : [`${option.glowColor}12`, `${option.glowColor}04`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          {isDark && (
            <LinearGradient
              colors={[`${option.glowColor}08`, "transparent"]}
              start={{ x: 0.5, y: 1 }}
              end={{ x: 0.5, y: 0.3 }}
              style={[StyleSheet.absoluteFill, { borderRadius: isHL ? 26 : 22 }]}
            />
          )}

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: isHL ? 26 : 22,
            borderWidth: isDark ? 1.2 : 0.5,
            borderColor: isDark
              ? `${option.glowColor}${isHL ? "40" : "20"}`
              : `${option.glowColor}${isHL ? "1A" : "0A"}`,
          }]} />

          <LinearGradient
            colors={isDark
              ? ["rgba(255,255,255,0.05)", "transparent"]
              : ["rgba(255,255,255,0.4)", "transparent"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 0, y: 1 }}
            style={[StyleSheet.absoluteFill, { borderRadius: isHL ? 26 : 22, height: "40%" }]}
          />

          {isHL && option.badge && (
            <View style={s.badgeWrap}>
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={s.badgePill}
              >
                <Text style={s.badgeText}>{option.badge.toUpperCase()}</Text>
              </LinearGradient>
            </View>
          )}

          <View style={[s.cardContent, isHL && s.cardContentHL]}>
            <View style={s.cardTop}>
              <LinearGradient
                colors={[c1, c2]}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={[s.emojiCircle, isHL && s.emojiCircleHL]}
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
                  { color: isDark ? "rgba(203,213,225,0.65)" : "#64748B", fontFamily: "Nunito_500Medium" },
                ]} numberOfLines={1}>
                  {option.subtitle}
                </Text>
              </View>

              <Animated.View style={{
                transform: [{ scale: arrowPulse }],
                opacity: arrowGlow,
                shadowColor: option.glowColor,
                shadowOpacity: isDark ? 0.6 : 0.25,
                shadowRadius: 14,
                shadowOffset: { width: 0, height: 3 },
                elevation: 6,
              }}>
                <LinearGradient
                  colors={[c1, c2]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={[s.arrowCircle, isHL && s.arrowCircleHL]}
                >
                  <Feather name="chevron-right" size={isHL ? 20 : 16} color="#fff" />
                </LinearGradient>
              </Animated.View>
            </View>

            <View style={s.descRow}>
              <View style={[s.descTag, {
                backgroundColor: isDark ? `${option.glowColor}12` : `${option.glowColor}08`,
                borderColor: isDark ? `${option.glowColor}25` : `${option.glowColor}12`,
              }]}>
                <Text style={[s.descText, { color: isDark ? `${option.glowColor}CC` : option.glowColor, fontFamily: "Nunito_600SemiBold" }]}>
                  {option.desc}
                </Text>
              </View>
            </View>

            <View style={s.itemsRow}>
              {option.items.map((item, i) => (
                <View key={i} style={[s.itemChip, {
                  backgroundColor: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.03)",
                  borderColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
                }]}>
                  <Text style={[s.itemText, {
                    color: isDark ? "rgba(255,255,255,0.5)" : "#64748B",
                    fontFamily: "Nunito_500Medium",
                  }]}>{item}</Text>
                </View>
              ))}
            </View>

            <LinearGradient
              colors={[c1, c2]}
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
  const headerSlide = useRef(new Animated.Value(-20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, { toValue: 1, duration: 700, useNativeDriver: true }),
      Animated.spring(headerSlide, { toValue: 0, useNativeDriver: true, speed: 12, bounciness: 5 }),
    ]).start();
  }, []);

  return (
    <CosmicBg>
      <LinearGradient
        colors={isDark
          ? ["rgba(0,0,0,0.35)", "transparent", "rgba(0,0,0,0.2)"]
          : ["rgba(255,255,255,0.15)", "transparent", "rgba(255,255,255,0.08)"]}
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
            borderColor: isDark ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
          }]}>
            <Feather name="arrow-left" size={20} color={isDark ? "#fff" : "#0F172A"} />
          </View>
        </Pressable>
      </View>

      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 60, paddingBottom: botPad + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[s.heroWrap, { opacity: headerFade, transform: [{ translateY: headerSlide }] }]}>
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
          <Text style={[s.heroTitle, { color: isDark ? "#fff" : "#0F172A", fontFamily: "Nunito_700Bold" }]}>
            Relationship
          </Text>
          <Text style={[s.heroSub, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B", fontFamily: "Nunito_400Regular" }]}>
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
  content: { paddingHorizontal: 18 },

  topBar: {
    position: "absolute",
    top: 0, left: 0, right: 0,
    zIndex: 20,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  backBtn: { alignSelf: "flex-start" },
  backCircle: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },

  heroWrap: { alignItems: "center", marginBottom: 28, gap: 8 },
  heroEmojiWrap: { alignItems: "center", justifyContent: "center", marginBottom: 8 },
  heroEmojiCircle: {
    width: 76, height: 76, borderRadius: 38,
    alignItems: "center", justifyContent: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.15)",
  },
  heroEmoji: { fontSize: 36 },
  heroEmojiGlow: {
    position: "absolute",
    width: 96, height: 96, borderRadius: 48,
    backgroundColor: "rgba(255,77,141,0.12)",
    zIndex: -1,
  },
  heroTitle: { fontSize: 28, letterSpacing: -0.5, textAlign: "center" },
  heroSub: { fontSize: 13.5, textAlign: "center", letterSpacing: 0.2, maxWidth: 260 },

  optionsList: { gap: 22 },

  card: {
    borderRadius: 22,
    overflow: "hidden",
  },

  badgeWrap: {
    position: "absolute",
    top: 0, right: 0,
    zIndex: 10,
  },
  badgePill: {
    paddingHorizontal: 12, paddingVertical: 5,
    borderBottomLeftRadius: 14,
    borderTopRightRadius: 24,
  },
  badgeText: {
    color: "#fff",
    fontSize: 8,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 1.2,
  },

  cardContent: { padding: 20, paddingTop: 22, gap: 14 },
  cardContentHL: { padding: 22, paddingTop: 24 },

  cardTop: { flexDirection: "row", alignItems: "center", gap: 14 },

  emojiCircle: {
    width: 54, height: 54, borderRadius: 18,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
  },
  emojiCircleHL: {
    width: 62, height: 62, borderRadius: 21,
  },
  emoji: { fontSize: 24 },
  emojiHL: { fontSize: 28 },

  titleArea: { flex: 1, gap: 4 },
  cardTitle: { fontSize: 18, letterSpacing: -0.2 },
  cardTitleHL: { fontSize: 20 },
  cardSub: { fontSize: 12, letterSpacing: 0.1 },

  arrowCircle: {
    width: 40, height: 40, borderRadius: 20,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.18)",
  },
  arrowCircleHL: {
    width: 46, height: 46, borderRadius: 23,
  },

  descRow: { marginTop: -2 },
  descTag: {
    alignSelf: "flex-start",
    paddingHorizontal: 12, paddingVertical: 5,
    borderRadius: 12,
    borderWidth: 1,
  },
  descText: { fontSize: 10.5, letterSpacing: 0.2 },

  itemsRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  itemChip: {
    paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 10,
    borderWidth: 1,
  },
  itemText: { fontSize: 10, letterSpacing: 0.1 },

  bottomBar: {
    height: 3, borderRadius: 2,
    opacity: 0.5, marginTop: 2,
  },
  bottomBarHL: {
    height: 3.5, opacity: 0.7,
  },
});
