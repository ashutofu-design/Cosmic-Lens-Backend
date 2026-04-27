/**
 * CardsCarousel — horizontal swipeable pager for v2 multi-intent responses.
 *
 * Renders a horizontal FlatList with one page per card. Each card shows:
 *   • Verdict tag chip   (🟠 SLOW BURN / 🟢 GREEN GO / etc.)
 *   • Intent label       (one-line ask paraphrase)
 *   • Narrative paragraph (50-80 words conversational prose)
 *   • Remedy line        (optional, ≤12 words)
 *   • Advisor line       (optional, ≤14 words — CA/SEBI/doctor/lawyer cite)
 *
 * Bottom strip: "N of M" indicator + dot pager.
 *
 * Backward compatible — only mounted when `cards.length > 0`. Legacy single
 * responses still flow through MarkdownReply.
 */
import React, { useMemo, useRef, useState } from "react";
import {
  FlatList,
  NativeScrollEvent,
  NativeSyntheticEvent,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { Feather } from "@expo/vector-icons";

import { useC } from "@/context/ThemeContext";

export type CardData = {
  intent_label?:   string;
  intent_bucket?:  string;
  intent_summary?: string;
  verdict_tag?:    string;
  narrative?:      string;
  remedy_line?:    string;
  advisor_line?:   string;
  text?:           string;     // legacy fallback if narrator failed
  source?:         string;
  error?:          string;
};

type Props = {
  cards: CardData[];
  trimmedCount?: number;
};

// Verdict tag → tint colour mapping. Falls back to accent.
function verdictTint(tag: string | undefined): { bg: string; fg: string } {
  if (!tag) return { bg: "#94A3B820", fg: "#475569" };
  if (tag.includes("🟢")) return { bg: "#10B98122", fg: "#059669" };
  if (tag.includes("🟡")) return { bg: "#F59E0B22", fg: "#B45309" };
  if (tag.includes("🟠")) return { bg: "#F9731622", fg: "#C2410C" };
  if (tag.includes("🔴")) return { bg: "#EF444422", fg: "#B91C1C" };
  if (tag.includes("⚪")) return { bg: "#94A3B822", fg: "#475569" };
  if (tag.includes("🔮")) return { bg: "#8B5CF622", fg: "#6D28D9" };
  return { bg: "#94A3B822", fg: "#475569" };
}

export function CardsCarousel({ cards, trimmedCount = 0 }: Props) {
  const C = useC();
  const { width: screenW } = useWindowDimensions();
  const [page, setPage] = useState(0);
  const listRef = useRef<FlatList>(null);

  const safeCards = useMemo(
    () => cards.filter((c) => c && (c.narrative || c.text)),
    [cards],
  );
  // Page is sized to the bubble container (which sits inside the assistant
  // bubble). We measure the parent width via onLayout to keep snap perfect
  // on small screens; default to ~screen-104 (insets + avatar).
  const [pageW, setPageW] = useState<number>(Math.max(220, screenW - 104));

  const onScroll = (e: NativeSyntheticEvent<NativeScrollEvent>) => {
    const x = e.nativeEvent.contentOffset.x;
    const next = Math.round(x / pageW);
    if (next !== page && next >= 0 && next < safeCards.length) setPage(next);
  };

  const styles = makeStyles(C);

  if (safeCards.length === 0) {
    return (
      <Text style={styles.emptyText}>
        Cosmic Intelligence ko abhi response generate karne mein dikkat aa
        rahi hai. Kripya thodi der baad dobara try karein.
      </Text>
    );
  }

  return (
    <View
      style={{ width: "100%" }}
      onLayout={(e) => {
        const w = e.nativeEvent.layout.width;
        if (w > 80 && Math.abs(w - pageW) > 2) setPageW(w);
      }}
    >
      {/* TOP indicator strip — ALWAYS visible above the carousel so the user
          immediately knows there are multiple answers and can swipe. The
          original bottom strip got pushed off-screen behind the input bar
          when narratives were long. */}
      {safeCards.length > 1 ? (
        <View style={[styles.topStrip, { borderColor: `${C.accent}40`, backgroundColor: `${C.accent}10` }]}>
          <View style={styles.topStripLeft}>
            <Feather name="layers" size={13} color={C.accent} />
            <Text style={[styles.topStripText, { color: C.accent }]}>
              {safeCards.length} jawab
              {trimmedCount > 0 ? `  · ${trimmedCount} aur trim` : ""}
            </Text>
          </View>
          <View style={styles.topStripRight}>
            <Text style={[styles.topStripHint, { color: C.textDim }]}>
              swipe karke dekho
            </Text>
            <Feather name="chevrons-right" size={14} color={C.accent} />
          </View>
        </View>
      ) : null}

      {/* Dot pager directly under the top strip — gives a persistent visual
          anchor for which card is active. */}
      {safeCards.length > 1 ? (
        <View style={styles.topDotsRow}>
          {safeCards.map((_, i) => (
            <View
              key={`tdot_${i}`}
              style={[
                styles.dot,
                {
                  backgroundColor: i === page ? C.accent : `${C.textDim}40`,
                  width: i === page ? 18 : 6,
                },
              ]}
            />
          ))}
          <Text style={[styles.topPageNum, { color: C.textDim }]}>
            {page + 1}/{safeCards.length}
          </Text>
        </View>
      ) : null}

      <FlatList
        ref={listRef}
        data={safeCards}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        snapToInterval={pageW}
        decelerationRate="fast"
        onScroll={onScroll}
        scrollEventThrottle={16}
        keyExtractor={(_, i) => `card_${i}`}
        getItemLayout={(_, i) => ({ length: pageW, offset: pageW * i, index: i })}
        renderItem={({ item, index }) => {
          const tint   = verdictTint(item.verdict_tag);
          const failed = item.source === "card_failed" || item.source === "narrator_failed";
          return (
            <View style={[styles.card, { width: pageW }]}>
              {/* Header row: verdict chip + intent label */}
              {item.verdict_tag ? (
                <View style={[styles.verdictChip, { backgroundColor: tint.bg }]}>
                  <Text style={[styles.verdictText, { color: tint.fg }]}>
                    {item.verdict_tag}
                  </Text>
                </View>
              ) : null}

              {item.intent_label ? (
                <Text style={[styles.intentLabel, { color: C.text }]}>
                  {item.intent_label}
                </Text>
              ) : null}

              {/* Narrative — falls back to legacy `text` if narrator failed */}
              <Text style={[styles.narrative, { color: C.textMid }]}>
                {item.narrative || item.text || ""}
              </Text>

              {/* Remedy */}
              {item.remedy_line ? (
                <View style={[styles.remedyRow, { borderColor: `${C.accent}30`, backgroundColor: C.accentBg }]}>
                  <Feather name="zap" size={12} color={C.accent} />
                  <Text style={[styles.remedyText, { color: C.text }]}>
                    {item.remedy_line}
                  </Text>
                </View>
              ) : null}

              {/* Advisor */}
              {item.advisor_line ? (
                <View style={[styles.advisorRow, { borderColor: C.border }]}>
                  <Feather name="info" size={11} color={C.textDim} />
                  <Text style={[styles.advisorText, { color: C.textDim }]}>
                    {item.advisor_line}
                  </Text>
                </View>
              ) : null}

              {failed ? (
                <Text style={[styles.failNote, { color: C.textDim }]}>
                  ⚠ Is intent ka conversational rendering abhi nahi mila — raw
                  guidance dikha rahe hain.
                </Text>
              ) : null}
            </View>
          );
        }}
      />

    </View>
  );
}

const makeStyles = (C: ReturnType<typeof useC>) =>
  StyleSheet.create({
    card: {
      paddingHorizontal: 2,
      paddingVertical: 2,
    },
    verdictChip: {
      alignSelf: "flex-start",
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 999,
      marginBottom: 8,
    },
    verdictText: {
      fontSize: 11,
      fontWeight: "800",
      letterSpacing: 0.4,
    },
    intentLabel: {
      fontSize: 13.5,
      fontWeight: "700",
      marginBottom: 6,
      lineHeight: 18,
    },
    narrative: {
      fontSize: 14.5,
      lineHeight: 21,
      marginBottom: 10,
    },
    remedyRow: {
      flexDirection: "row",
      alignItems: "flex-start",
      gap: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderWidth: 1,
      borderRadius: 8,
      marginBottom: 8,
    },
    remedyText: {
      flex: 1,
      fontSize: 13,
      lineHeight: 18,
      fontWeight: "600",
    },
    advisorRow: {
      flexDirection: "row",
      alignItems: "flex-start",
      gap: 6,
      paddingTop: 8,
      borderTopWidth: 1,
      marginTop: 4,
    },
    advisorText: {
      flex: 1,
      fontSize: 11.5,
      lineHeight: 16,
      fontStyle: "italic",
    },
    topStrip: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderWidth: 1,
      borderRadius: 8,
      marginBottom: 6,
      gap: 8,
    },
    topStripLeft: {
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
    },
    topStripRight: {
      flexDirection: "row",
      alignItems: "center",
      gap: 4,
    },
    topStripText: {
      fontSize: 12,
      fontWeight: "700",
      letterSpacing: 0.2,
    },
    topStripHint: {
      fontSize: 11,
      fontWeight: "500",
      fontStyle: "italic",
    },
    topDotsRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "center",
      gap: 4,
      marginBottom: 8,
    },
    topPageNum: {
      fontSize: 10,
      fontWeight: "600",
      marginLeft: 6,
    },
    dot: {
      height: 6,
      borderRadius: 3,
    },
    emptyText: {
      fontSize: 14,
      lineHeight: 20,
      color: "#94A3B8",
    },
    failNote: {
      fontSize: 11,
      marginTop: 6,
      fontStyle: "italic",
    },
  });
