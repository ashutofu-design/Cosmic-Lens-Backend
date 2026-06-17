import { Feather } from "@expo/vector-icons";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import React, { useRef, useState } from "react";
import {
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { PUKHRAJ_GALLERY, type GemstoneGalleryItem } from "@/lib/gemstoneProductImages";

const W = Dimensions.get("window").width;
const HERO_H = Math.round(W * 0.82);
const THUMB = 56;
const ACCENT = "#fbbf24";

const F = {
  semi: "Nunito_600SemiBold",
  bold: "Nunito_700Bold",
  extra: "Nunito_800ExtraBold",
} as const;

type Props = {
  trustLabel?: string;
  reviewHint?: string;
  product?: "pukhraj" | "emerald";
  accent?: string;
};

function EmeraldPlaceholder({ trustLabel, accent }: { trustLabel?: string; accent: string }) {
  return (
    <View style={[s.wrap, { height: HERO_H }]}>
      <LinearGradient
        colors={["#064e3b", "#047857", "#0f172a"]}
        style={StyleSheet.absoluteFill}
      />
      <View style={s.placeholderInner}>
        <Text style={{ fontSize: 56 }}>💚</Text>
        <Text style={[s.placeholderTitle, { color: accent }]}>Zambian Emerald</Text>
        <Text style={s.placeholderSub}>5 Ratti · Certified Natural</Text>
      </View>
      <View style={[s.certSeal, { borderColor: `${accent}66` }]} pointerEvents="none">
        <Feather name="award" size={14} color={accent} />
        <Text style={[s.certText, { color: accent }]}>{trustLabel ?? "CERTIFIED"}</Text>
      </View>
    </View>
  );
}

export function GemstoneProductGallery({ trustLabel, reviewHint, product = "pukhraj", accent = ACCENT }: Props) {
  if (product === "emerald") {
    return <EmeraldPlaceholder trustLabel={trustLabel} accent={accent} />;
  }

  const scrollRef = useRef<ScrollView>(null);
  const [active, setActive] = useState(0);
  const items = PUKHRAJ_GALLERY;

  function onScroll(e: NativeSyntheticEvent<NativeScrollEvent>) {
    const idx = Math.round(e.nativeEvent.contentOffset.x / W);
    if (idx !== active && idx >= 0 && idx < items.length) setActive(idx);
  }

  function goTo(i: number) {
    setActive(i);
    scrollRef.current?.scrollTo({ x: i * W, animated: true });
  }

  return (
    <View style={s.wrap}>
      <ScrollView
        ref={scrollRef}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onScroll}
        decelerationRate="fast"
      >
        {items.map(item => (
          <View key={item.id} style={{ width: W, height: HERO_H }}>
            <Image source={item.source} style={s.heroImg} contentFit="cover" transition={200} />
            <LinearGradient
              colors={["transparent", "rgba(8,6,18,0.55)", "rgba(8,6,18,0.92)"]}
              style={StyleSheet.absoluteFill}
              pointerEvents="none"
            />
          </View>
        ))}
      </ScrollView>

      <View style={s.certSeal} pointerEvents="none">
        <Feather name="award" size={14} color={ACCENT} />
        <Text style={s.certText}>{trustLabel ?? "CERTIFIED"}</Text>
      </View>

      {reviewHint ? (
        <View style={s.reviewPill} pointerEvents="none">
          <Feather name="star" size={11} color={ACCENT} />
          <Text style={s.reviewText}>{reviewHint}</Text>
        </View>
      ) : null}

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={s.thumbRow}
        style={s.thumbBar}
      >
        {items.map((item, i) => (
          <Thumb key={item.id} item={item} on={i === active} onPress={() => goTo(i)} />
        ))}
      </ScrollView>
    </View>
  );
}

function Thumb({ item, on, onPress }: { item: GemstoneGalleryItem; on: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[s.thumb, on && s.thumbOn]}>
      <Image source={item.source} style={s.thumbImg} contentFit="cover" />
    </Pressable>
  );
}

const s = StyleSheet.create({
  wrap: { marginBottom: 4 },
  placeholderInner: { flex: 1, alignItems: "center", justifyContent: "center", gap: 8 },
  placeholderTitle: { fontSize: 20, fontFamily: F.extra },
  placeholderSub: { color: "rgba(255,255,255,0.65)", fontSize: 12, fontFamily: F.semi },
  heroImg: { width: "100%", height: "100%", backgroundColor: "#1a1528" },
  certSeal: {
    position: "absolute", top: 12, right: 14, flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999,
    backgroundColor: "rgba(8,6,18,0.72)", borderWidth: 1, borderColor: "rgba(251,191,36,0.45)",
  },
  certText: { color: ACCENT, fontSize: 8.5, fontFamily: F.extra, letterSpacing: 0.8 },
  reviewPill: {
    position: "absolute", bottom: THUMB + 18, right: 14, flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, backgroundColor: "rgba(0,0,0,0.45)",
  },
  reviewText: { color: "rgba(255,255,255,0.85)", fontSize: 10, fontFamily: F.semi },
  thumbBar: { marginTop: -THUMB / 2 - 4 },
  thumbRow: { paddingHorizontal: 16, gap: 8 },
  thumb: {
    width: THUMB, height: THUMB, borderRadius: 10, overflow: "hidden",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.15)",
  },
  thumbOn: { borderColor: ACCENT },
  thumbImg: { width: "100%", height: "100%" },
});
