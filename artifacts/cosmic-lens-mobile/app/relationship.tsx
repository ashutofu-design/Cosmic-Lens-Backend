import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Easing,
  Modal,
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
import { useUser, type ProfileEntry } from "@/context/UserContext";

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
  depthLine?: string;
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
    subtitle: "See if this match is truly meant for marriage",
    emoji: "💍",
    gradient: ["#6366f1", "#818cf8", "#a78bfa"],
    glowColor: "#6366f1",
    route: "/kundli-milan",
    highlighted: true,
    badge: "💍 Deep Analysis",
    desc: "For serious & marriage decisions",
    items: ["Soul Sync", "Attraction Match", "Destiny Link", "Intimacy Score"],
    depthLine: "36 Gun Milan + deep compatibility insights",
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

  const loveWarm = option.key === "love";
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
        {isDark && (
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
          { borderRadius: bRadius, backgroundColor: "#111827" },
          {
            shadowColor: option.glowColor,
            shadowOpacity: isDark ? 0.5 : (isHL ? 0.25 : 0.1),
            shadowRadius: 30,
            shadowOffset: { width: 0, height: 10 },
            elevation: 14,
          },
        ]}>
          <LinearGradient
            colors={loveWarm
              ? ["#1a0a10", "#111827", "#110d14"]
              : ["#0d0f1e", "#111827", "#0f0d1a"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[StyleSheet.absoluteFill, { borderRadius: bRadius }]}
          />

          <Animated.View style={[StyleSheet.absoluteFill, { overflow: "hidden", borderRadius: bRadius, opacity: glowAnim }]}>
            <LinearGradient
              colors={[`${c1}20`, `${c2}10`, "transparent"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
          </Animated.View>

          <LinearGradient
            colors={[`${option.glowColor}10`, "transparent"]}
            start={{ x: 0.5, y: 1 }}
            end={{ x: 0.5, y: 0.2 }}
            style={[StyleSheet.absoluteFill, { borderRadius: bRadius }]}
          />

          <View style={[StyleSheet.absoluteFill, {
            borderRadius: bRadius,
            borderWidth: 1,
            borderColor: "rgba(255,255,255,0.1)",
          }]} />

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
                  { color: "#FFFFFF", fontFamily: "Nunito_800ExtraBold" },
                ]}>
                  {option.title}
                </Text>
                <Text style={[
                  s.cardSub,
                  isHL && s.cardSubHL,
                  { color: "#D1D5DB", fontFamily: "Nunito_600SemiBold" },
                ]} numberOfLines={1}>
                  {option.subtitle}
                </Text>
              </View>

              <Animated.View style={{
                transform: [{ scale: arrowPulse }],
                opacity: Animated.add(0.3, Animated.multiply(arrowGlow, 0.7)),
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
                backgroundColor: `${option.glowColor}18`,
                borderColor: `${option.glowColor}35`,
              }]}>
                <Text style={[s.descText, { color: option.glowColor, fontFamily: "Nunito_700Bold" }]}>
                  {option.desc}
                </Text>
              </View>
            </View>

            <View style={s.itemsRow}>
              {option.items.map((item, i) => {
                const chipBg = "rgba(255,255,255,0.08)";
                const chipBorder = "rgba(255,255,255,0.14)";
                const chipColor = "#F3F4F6";

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
                        fontFamily: "Nunito_700Bold",
                      }]}>{item}</Text>
                    </View>
                  </Animated.View>
                );
              })}
            </View>

            {option.depthLine ? (
              <View style={{flexDirection:"row",alignItems:"center",gap:5,marginTop:2,paddingHorizontal:2}}>
                <Feather name="zap" size={10} color={option.glowColor}/>
                <Text style={{color:"#D1D5DB",fontSize:10,fontFamily:"Nunito_700Bold"}}>
                  {option.depthLine}
                </Text>
              </View>
            ) : null}

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
  const { profiles, primaryProfileId } = useUser();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const hasP1 = !!primaryProfile?.kundli;
  const otherProfiles = profiles.filter(p => p.id !== primaryProfile?.id);

  const [selectedP2, setSelectedP2] = useState<ProfileEntry | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);

  const p1Glow = useRef(new Animated.Value(0)).current;
  const p2Glow = useRef(new Animated.Value(0)).current;
  const p2Scale = useRef(new Animated.Value(1)).current;

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
        contentContainerStyle={[s.content, { paddingTop: topPad + 50, paddingBottom: botPad + 30 }]}
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

        {/* ── Smart Person Slots ── */}
        <View style={{flexDirection:"row",gap:8,marginBottom:14}}>

          {/* ─ PERSON 1: Auto-loaded from primary profile ─ */}
          {hasP1 ? (
            <View style={{flex:1}}>
              <View style={{flex:1,flexDirection:"row",alignItems:"center",height:46,
                borderRadius:14,paddingHorizontal:10,gap:7,
                backgroundColor:"#151b2e",
                borderWidth:1,
                borderColor:"#2d3555"}}>
                <View style={{width:24,height:24,borderRadius:12,
                  backgroundColor:"#1e2744",
                  alignItems:"center",justifyContent:"center"}}>
                  <Text style={{fontSize:11}}>👤</Text>
                </View>
                <Text style={{color:"#E5E7EB",fontSize:11,fontFamily:"Nunito_700Bold",flex:1}} numberOfLines={1}>
                  {primaryProfile?.name || "You"}
                </Text>
                <Feather name="check-circle" size={12} color="#818cf8"/>
              </View>
            </Animated.View>
          ) : (
            <Pressable onPress={()=>router.push("/kundli-milan" as any)}
              style={({pressed})=>({opacity:pressed?0.7:1,flex:1,flexDirection:"row",alignItems:"center",height:46,
                borderRadius:14,paddingHorizontal:10,gap:7,
                backgroundColor:"#131929",
                borderWidth:0.5,borderStyle:"dashed" as any,
                borderColor:"#2d3555"})}>
              <Text style={{fontSize:13}}>👤</Text>
              <Text style={{color:"rgba(255,255,255,0.5)",fontSize:11,fontFamily:"Nunito_500Medium",flex:1}}>You</Text>
              <Text style={{color:"#818cf8",fontSize:9,fontFamily:"Nunito_700Bold"}}>+ Add</Text>
            </Pressable>
          )}

          {/* ─ PERSON 2: Smart — select from saved / add new ─ */}
          {selectedP2 ? (
            <Pressable onPress={()=>{
              Haptics.selectionAsync();
              if(otherProfiles.length>0) setPickerOpen(true);
              else { setSelectedP2(null); }
            }}
              style={({pressed})=>({opacity:pressed?0.85:1,flex:1,flexDirection:"row",alignItems:"center",height:46,
                borderRadius:14,paddingHorizontal:10,gap:7,
                backgroundColor:"#1a1525",
                borderWidth:1,
                borderColor:"#3d2545"})}>
              <View style={{width:24,height:24,borderRadius:12,
                backgroundColor:"#2a1a35",
                alignItems:"center",justifyContent:"center"}}>
                <Text style={{fontSize:11}}>💑</Text>
              </View>
              <Text style={{color:"#E5E7EB",fontSize:11,fontFamily:"Nunito_700Bold",flex:1}} numberOfLines={1}>
                {selectedP2.name}
              </Text>
              <Text style={{color:"#f472b6",fontSize:8,fontFamily:"Nunito_600SemiBold"}}>Change</Text>
            </Pressable>
          ) : otherProfiles.length > 0 ? (
            <Pressable onPress={()=>{
              Haptics.selectionAsync();
              setPickerOpen(true);
            }}
              style={({pressed})=>({opacity:pressed?0.7:1,flex:1,flexDirection:"row",alignItems:"center",height:46,
                borderRadius:14,paddingHorizontal:10,gap:7,
                backgroundColor:"#161020",
                borderWidth:0.5,
                borderColor:"#2d1f3a"})}>
              <Text style={{fontSize:13}}>💑</Text>
              <Text style={{color:"rgba(255,255,255,0.5)",fontSize:11,fontFamily:"Nunito_500Medium",flex:1}}>Select Partner</Text>
              <Feather name="chevron-down" size={12} color="#f472b6"/>
            </Pressable>
          ) : (
            <Pressable onPress={()=>router.push("/kundli-milan" as any)}
              style={({pressed})=>({opacity:pressed?0.7:1,flex:1,flexDirection:"row",alignItems:"center",height:46,
                borderRadius:14,paddingHorizontal:10,gap:7,
                backgroundColor:"#141020",
                borderWidth:0.5,borderStyle:"dashed" as any,
                borderColor:"#2d1f3a"})}>
              <Text style={{fontSize:13}}>💑</Text>
              <Text style={{color:"rgba(255,255,255,0.5)",fontSize:11,fontFamily:"Nunito_500Medium",flex:1}}>Person 2</Text>
              <Text style={{color:"#f472b6",fontSize:9,fontFamily:"Nunito_700Bold"}}>+ Add</Text>
            </Pressable>
          )}
        </View>

        {/* ── Profile Picker Modal ── */}
        <Modal visible={pickerOpen} transparent animationType="fade" onRequestClose={()=>setPickerOpen(false)}>
          <Pressable style={{flex:1,backgroundColor:"rgba(0,0,0,0.55)",justifyContent:"flex-end"}}
            onPress={()=>setPickerOpen(false)}>
            <Pressable onPress={()=>{}} style={{
              backgroundColor:isDark?"#1A2135":"#fff",
              borderTopLeftRadius:24,borderTopRightRadius:24,
              paddingTop:16,paddingBottom:40,paddingHorizontal:20,maxHeight:380}}>
              <View style={{width:40,height:4,borderRadius:2,backgroundColor:isDark?"rgba(255,255,255,0.15)":"rgba(0,0,0,0.12)",
                alignSelf:"center",marginBottom:16}}/>
              <Text style={{color:C.text,fontSize:15,fontFamily:"Nunito_800ExtraBold",marginBottom:14}}>
                Select Partner
              </Text>
              <ScrollView showsVerticalScrollIndicator={false}>
                {otherProfiles.map((prof)=>(
                  <Pressable key={prof.id} onPress={()=>{
                    setSelectedP2(prof);
                    setPickerOpen(false);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    Animated.sequence([
                      Animated.timing(p2Scale,{toValue:1.05,duration:120,useNativeDriver:true}),
                      Animated.timing(p2Scale,{toValue:1,duration:180,useNativeDriver:true}),
                    ]).start();
                  }}
                    style={({pressed})=>({opacity:pressed?0.7:1,flexDirection:"row",alignItems:"center",gap:10,
                      paddingVertical:11,paddingHorizontal:12,borderRadius:14,marginBottom:6,
                      backgroundColor:selectedP2?.id===prof.id
                        ?(isDark?"rgba(236,72,153,0.12)":"rgba(236,72,153,0.08)")
                        :(isDark?"rgba(255,255,255,0.04)":"rgba(0,0,0,0.03)"),
                      borderWidth:selectedP2?.id===prof.id?1:0.5,
                      borderColor:selectedP2?.id===prof.id
                        ?(isDark?"rgba(236,72,153,0.3)":"rgba(236,72,153,0.2)")
                        :(isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.06)")})}>
                    <View style={{width:32,height:32,borderRadius:16,
                      backgroundColor:isDark?"rgba(236,72,153,0.12)":"rgba(236,72,153,0.08)",
                      alignItems:"center",justifyContent:"center"}}>
                      <Text style={{fontSize:14}}>💑</Text>
                    </View>
                    <View style={{flex:1}}>
                      <Text style={{color:C.text,fontSize:13,fontFamily:"Nunito_700Bold"}}>{prof.name}</Text>
                      {prof.relation ? (
                        <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>{prof.relation}</Text>
                      ) : null}
                    </View>
                    {selectedP2?.id===prof.id && <Feather name="check-circle" size={14} color="#ec4899"/>}
                  </Pressable>
                ))}
              </ScrollView>
              <Pressable onPress={()=>{
                setPickerOpen(false);
                router.push("/kundli-milan" as any);
              }}
                style={({pressed})=>({opacity:pressed?0.7:1,flexDirection:"row",alignItems:"center",justifyContent:"center",
                  gap:6,marginTop:10,paddingVertical:11,borderRadius:14,
                  backgroundColor:isDark?"rgba(236,72,153,0.08)":"rgba(236,72,153,0.05)",
                  borderWidth:0.5,borderStyle:"dashed" as any,
                  borderColor:isDark?"rgba(236,72,153,0.2)":"rgba(236,72,153,0.12)"})}>
                <Feather name="plus" size={13} color="#ec4899"/>
                <Text style={{color:"#ec4899",fontSize:12,fontFamily:"Nunito_700Bold"}}>Add New Partner</Text>
              </Pressable>
            </Pressable>
          </Pressable>
        </Modal>

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

  heroWrap: { alignItems: "center", marginBottom: 14, gap: 6 },
  heroEmojiWrap: { alignItems: "center", justifyContent: "center", marginBottom: 4 },
  heroEmojiCircle: {
    width: 56, height: 56, borderRadius: 28,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.18)",
  },
  heroEmoji: { fontSize: 26 },
  heroEmojiGlow: {
    position: "absolute",
    width: 76, height: 76, borderRadius: 38,
    backgroundColor: "rgba(255,77,141,0.15)",
    zIndex: -1,
  },
  heroEmojiGlow2: {
    position: "absolute",
    width: 96, height: 96, borderRadius: 48,
    backgroundColor: "rgba(192,38,211,0.08)",
    zIndex: -2,
  },
  heroTitle: { fontSize: 24, letterSpacing: -0.5, textAlign: "center" },
  heroSub: { fontSize: 12, textAlign: "center", letterSpacing: 0.2, maxWidth: 270 },

  optionsList: { gap: 14 },

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

  cardContent: { padding: 16, paddingTop: 18, gap: 12 },
  cardContentHL: { padding: 18, paddingTop: 20 },

  cardTop: { flexDirection: "row", alignItems: "center", gap: 12 },

  emojiCircle: {
    width: 46, height: 46, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.14)",
  },
  emojiCircleHL: {
    width: 54, height: 54, borderRadius: 18,
  },
  emoji: { fontSize: 22 },
  emojiHL: { fontSize: 26 },

  titleArea: { flex: 1, gap: 3 },
  cardTitle: { fontSize: 16, letterSpacing: -0.2 },
  cardTitleHL: { fontSize: 18 },
  cardSub: { fontSize: 11, letterSpacing: 0.1 },
  cardSubHL: { fontSize: 11.5, lineHeight: 16 },

  arrowCircle: {
    width: 38, height: 38, borderRadius: 19,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1.5, borderColor: "rgba(255,255,255,0.2)",
  },
  arrowCircleHL: {
    width: 44, height: 44, borderRadius: 22,
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
