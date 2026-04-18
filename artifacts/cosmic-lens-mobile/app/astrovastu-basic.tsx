/**
 * AstroVastu BASIC — Personalized Quick Check
 *
 * User picks a room + direction → backend runs deterministic kundli-aware
 * Vastu engine → returns verdict (Ideal / Acceptable / Adjustment Needed /
 * Avoid) with bilingual reasons, prioritised remedies and classical refs.
 *
 * No AI/LLM — pure rules engine. Cost ~₹0.50/check. Daily quota shared
 * with Q&A counter (free=3, basic=10, pro=unlimited).
 */
import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, Stack } from "expo-router";
import React, { useCallback, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";
import { AstroVastuWallet } from "@/components/AstroVastuWallet";

// ─────────────────────────────────────────────────────────────────────────
// Static option lists — bilingual labels (24-language migration: drop in i18n keys)
// ─────────────────────────────────────────────────────────────────────────
const ROOMS: { key: string; en: string; hi: string; icon: keyof typeof Feather.glyphMap }[] = [
  { key: "bedroom",  en: "Bedroom",       hi: "Shayan kaksh",  icon: "moon"      },
  { key: "kitchen",  en: "Kitchen",       hi: "Rasoi",         icon: "coffee"    },
  { key: "pooja",    en: "Pooja Room",    hi: "Pooja sthal",   icon: "sun"       },
  { key: "study",    en: "Study",         hi: "Adhyayan",      icon: "book-open" },
  { key: "bathroom", en: "Bathroom",      hi: "Snan-grih",     icon: "droplet"   },
  { key: "living",   en: "Living Room",   hi: "Baithak",       icon: "home"      },
  { key: "entrance", en: "Entrance",      hi: "Pravesh dwaar", icon: "log-in"    },
  { key: "store",    en: "Store",         hi: "Bhandaar",      icon: "package"   },
];

const DIRECTIONS: { key: string; short: string; en: string; hi: string }[] = [
  { key: "North",      short: "N",  en: "North",      hi: "Uttar"        },
  { key: "North-East", short: "NE", en: "North-East", hi: "Ishan"        },
  { key: "East",       short: "E",  en: "East",       hi: "Poorv"        },
  { key: "South-East", short: "SE", en: "South-East", hi: "Agneya"       },
  { key: "South",      short: "S",  en: "South",      hi: "Dakshin"      },
  { key: "South-West", short: "SW", en: "South-West", hi: "Nairutya"     },
  { key: "West",       short: "W",  en: "West",       hi: "Paschim"      },
  { key: "North-West", short: "NW", en: "North-West", hi: "Vayavya"      },
];

// Verdict tone → colour palette
const TONE_COLOR: Record<string, { bg: string; fg: string; border: string }> = {
  excellent: { bg: "rgba(16,185,129,0.18)", fg: "#10B981", border: "rgba(16,185,129,0.45)" },
  ok:        { bg: "rgba(59,130,246,0.18)", fg: "#3B82F6", border: "rgba(59,130,246,0.45)" },
  warning:   { bg: "rgba(245,158,11,0.18)", fg: "#F59E0B", border: "rgba(245,158,11,0.45)" },
  critical:  { bg: "rgba(239,68,68,0.18)",  fg: "#EF4444", border: "rgba(239,68,68,0.45)"  },
};

// ─────────────────────────────────────────────────────────────────────────
// Response types (mirror backend astrovastu_response.py)
// ─────────────────────────────────────────────────────────────────────────
type Remedy = {
  action: string;
  english: string;
  hindi: string;
  priority: number;
  classical_ref: string;
};
type ClassicalRef = { type: string; source: string };
type CheckResponse = {
  verdict: string;
  verdict_label: { en: string; hi: string };
  verdict_tone: string;
  generic_verdict: string;
  severity: { bucket: string; label: { en: string; hi: string }; multiplier: number; reasons: string[] };
  personalization_reason: { en: string; hi: string };
  remedies: Remedy[];
  classical_refs: ClassicalRef[];
  applied_tie_breakers: { id: string; rule: string; effect: string }[];
  meta: Record<string, unknown>;
  quota: { used: number; limit: number };
  plan: string;
};
type ErrorResponse = {
  error: string;
  message?: string;
  upgrade_required?: boolean;
  missing_fields?: string[];
  quota?: { used: number; limit: number };
};

// ─────────────────────────────────────────────────────────────────────────
// Screen
// ─────────────────────────────────────────────────────────────────────────
export default function AstroVastuBasicScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const { user } = useUser();

  const [room, setRoom]               = useState<string>("bedroom");
  const [direction, setDirection]     = useState<string>("North-East");
  const [loading, setLoading]         = useState(false);
  const [result, setResult]           = useState<CheckResponse | null>(null);
  const [errInfo, setErrInfo]         = useState<ErrorResponse | null>(null);
  const [walletKey, setWalletKey]     = useState(0);   // bump to refresh wallet after a scan

  const onSubmit = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setErrInfo({ error: "auth_required", message: "Login zaroori hai." });
      return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setLoading(true);
    setErrInfo(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/astrovastu-basic`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key":    user.api_key,
        },
        body: JSON.stringify({ user_id: user.id, room_type: room, direction }),
      });
      const body = await res.json();
      if (!res.ok) {
        setErrInfo(body as ErrorResponse);
        if ((body as ErrorResponse).upgrade_required) {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
        }
      } else {
        setResult(body as CheckResponse);
        setWalletKey((k) => k + 1);   // refresh wallet so credit decrement shows
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    } catch (e: any) {
      setErrInfo({ error: "network_error", message: e?.message || "Network error" });
    } finally {
      setLoading(false);
    }
  }, [user, room, direction]);

  const tone = useMemo(() => TONE_COLOR[result?.verdict_tone || "ok"] ?? TONE_COLOR.ok,
                       [result]);

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <Stack.Screen options={{ headerShown: false }} />
      <LinearGradient
        colors={C.isDark ? ["#0B0F19", "#10162A"] : ["#F5F5F8", "#EAE8FA"]}
        style={StyleSheet.absoluteFill}
      />

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} hitSlop={12}>
          <Feather name="chevron-left" size={26} color={C.text} />
        </Pressable>
        <Text style={[styles.headerTitle, { color: C.text }]}>Personalized Quick Check</Text>
        <View style={{ width: 26 }} />
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 80 }}
        showsVerticalScrollIndicator={false}
      >
        {/* ── AstroVastu Wallet (Phase 2: credits + buy CTAs) ─────── */}
        <AstroVastuWallet variant="basic" refreshKey={walletKey} />

        {/* ── Intro card ─────────────────────────────────────────────── */}
        <View style={[styles.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[styles.cardTitle, { color: C.text }]}>
            🪐  Kundli + Vastu = Personalized
          </Text>
          <Text style={[styles.bodyText, { color: C.textMid }]}>
            Aapki Lagna, Mahadasha, aur special yogas ke aadhaar par room placement
            ka deterministic verdict — classical sources ke saath.
          </Text>
        </View>

        {/* ── Room picker ──────────────────────────────────────────── */}
        <Text style={[styles.sectionTitle, { color: C.text }]}>1.  Kamra chunein</Text>
        <View style={styles.grid}>
          {ROOMS.map(r => {
            const sel = r.key === room;
            return (
              <Pressable
                key={r.key}
                onPress={() => { Haptics.selectionAsync(); setRoom(r.key); }}
                style={[
                  styles.gridChip,
                  {
                    backgroundColor: sel ? C.accent : C.bgCard,
                    borderColor:     sel ? C.accent : C.border,
                  },
                ]}
              >
                <Feather name={r.icon} size={18} color={sel ? "#fff" : C.text} />
                <Text style={[styles.gridChipText, { color: sel ? "#fff" : C.text }]}>
                  {r.en}
                </Text>
                <Text style={[styles.gridChipSub, { color: sel ? "#fff" : C.textMid }]}>
                  {r.hi}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* ── Direction wheel ──────────────────────────────────────── */}
        <Text style={[styles.sectionTitle, { color: C.text, marginTop: 18 }]}>
          2.  Disha chunein
        </Text>
        <View style={styles.dirGrid}>
          {DIRECTIONS.map(d => {
            const sel = d.key === direction;
            return (
              <Pressable
                key={d.key}
                onPress={() => { Haptics.selectionAsync(); setDirection(d.key); }}
                style={[
                  styles.dirChip,
                  {
                    backgroundColor: sel ? C.accent : C.bgCard,
                    borderColor:     sel ? C.accent : C.border,
                  },
                ]}
              >
                <Text style={[styles.dirShort, { color: sel ? "#fff" : C.text }]}>{d.short}</Text>
                <Text style={[styles.dirHi, { color: sel ? "#fff" : C.textMid }]}>{d.hi}</Text>
              </Pressable>
            );
          })}
        </View>

        {/* ── Submit button ──────────────────────────────────────── */}
        <Pressable
          onPress={onSubmit}
          disabled={loading}
          style={({ pressed }) => [
            styles.submitBtn,
            {
              backgroundColor: C.accent,
              opacity: loading ? 0.7 : pressed ? 0.85 : 1,
            },
          ]}
        >
          {loading
            ? <ActivityIndicator color="#fff" />
            : <Text style={styles.submitText}>Check Karein  ✨</Text>}
        </Pressable>

        {/* ── Error / upsell banner ─────────────────────────────── */}
        {errInfo && (
          <View style={[styles.errCard, {
            backgroundColor: errInfo.upgrade_required
              ? "rgba(245,158,11,0.15)"
              : "rgba(239,68,68,0.15)",
            borderColor: errInfo.upgrade_required ? "#F59E0B" : "#EF4444",
          }]}>
            <Feather
              name={errInfo.upgrade_required ? "zap" : "alert-triangle"}
              size={20}
              color={errInfo.upgrade_required ? "#F59E0B" : "#EF4444"}
            />
            <View style={{ flex: 1 }}>
              <Text style={[styles.errTitle, { color: C.text }]}>
                {errInfo.upgrade_required ? "Daily limit poora" : "Issue"}
              </Text>
              <Text style={[styles.errBody, { color: C.textMid }]}>
                {errInfo.message || errInfo.error}
              </Text>
              {errInfo.error === "profile_incomplete" && (
                <Pressable
                  onPress={() => router.push("/profile-edit" as any)}
                  style={[styles.upgradeBtn, { backgroundColor: C.accent, marginTop: 10 }]}
                >
                  <Text style={styles.upgradeText}>Profile Complete Karein</Text>
                </Pressable>
              )}
              {errInfo.upgrade_required && (
                <Pressable
                  onPress={() => router.push("/subscription" as any)}
                  style={[styles.upgradeBtn, { backgroundColor: "#F59E0B", marginTop: 10 }]}
                >
                  <Text style={styles.upgradeText}>
                    Upgrade — Basic ₹199 / Pro ₹499
                  </Text>
                </Pressable>
              )}
            </View>
          </View>
        )}

        {/* ── Result card ─────────────────────────────────────── */}
        {result && (
          <View style={[styles.resultCard, { backgroundColor: C.bgCard, borderColor: tone.border }]}>
            {/* Verdict pill */}
            <View style={[styles.verdictPill, { backgroundColor: tone.bg, borderColor: tone.border }]}>
              <Text style={[styles.verdictPillText, { color: tone.fg }]}>
                {result.verdict_label.en}
              </Text>
              <Text style={[styles.verdictPillHi, { color: tone.fg }]}>
                {result.verdict_label.hi}
              </Text>
            </View>

            {/* Severity meter */}
            <View style={styles.sevRow}>
              <Text style={[styles.metaLabel, { color: C.textMid }]}>Severity:</Text>
              <Text style={[styles.metaValue, { color: C.text }]}>
                {result.severity.label.en} ({result.severity.label.hi}) ·  ×{result.severity.multiplier.toFixed(1)}
              </Text>
            </View>

            {/* Personalization reason */}
            <View style={[styles.section, { borderTopColor: C.border }]}>
              <Text style={[styles.sectionLabel, { color: tone.fg }]}>Why this verdict?</Text>
              <Text style={[styles.bodyText, { color: C.text, marginTop: 4 }]}>
                {result.personalization_reason.hi}
              </Text>
              <Text style={[styles.bodyTextSmall, { color: C.textMid, marginTop: 4 }]}>
                {result.personalization_reason.en}
              </Text>
            </View>

            {/* Remedies */}
            {result.remedies.length > 0 && (
              <View style={[styles.section, { borderTopColor: C.border }]}>
                <Text style={[styles.sectionLabel, { color: tone.fg }]}>
                  Upaay ({result.remedies.length})
                </Text>
                {result.remedies.map((r, idx) => (
                  <View key={`${r.action}-${idx}`} style={[styles.remedyItem, { borderColor: C.border }]}>
                    <View style={[styles.remedyBullet, { backgroundColor: tone.fg }]}>
                      <Text style={styles.remedyBulletText}>{idx + 1}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[styles.bodyText, { color: C.text }]}>{r.hindi}</Text>
                      <Text style={[styles.bodyTextSmall, { color: C.textMid, marginTop: 2 }]}>
                        {r.english}
                      </Text>
                      <Text style={[styles.refText, { color: C.textMid }]}>📜  {r.classical_ref}</Text>
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Classical refs */}
            {result.classical_refs.length > 0 && (
              <View style={[styles.section, { borderTopColor: C.border }]}>
                <Text style={[styles.sectionLabel, { color: tone.fg }]}>
                  Shastra Pramaan
                </Text>
                {result.classical_refs.map((ref, i) => (
                  <Text key={i} style={[styles.refText, { color: C.textMid, marginTop: 4 }]}>
                    • {ref.type === "vastu" ? "🏛️" : "🔯"}  {ref.source}
                  </Text>
                ))}
              </View>
            )}

            {/* Quota footer */}
            <View style={[styles.section, { borderTopColor: C.border }]}>
              <Text style={[styles.bodyTextSmall, { color: C.textMid }]}>
                Aaj: {result.quota.used} / {result.quota.limit === -1 ? "Unlimited" : result.quota.limit}
                {"  ·  "}Plan: {result.plan.toUpperCase()}
              </Text>
            </View>
          </View>
        )}

        {/* ── Branding footer (NEVER reveal AI/LLM) ──────────────── */}
        <Text style={[styles.brandingFooter, { color: C.textMid }]}>
          ✨  Powered by Advanced Cosmic Intelligence
        </Text>
        <Text style={[styles.brandingFooterSmall, { color: C.textMid }]}>
          Cosmic AstroVastu Drishti Engine v1.0
        </Text>
      </ScrollView>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 10,
  },
  headerTitle:    { fontSize: 17, fontWeight: "700" },

  card:           {
    borderRadius: 14, borderWidth: 1, padding: 14, marginBottom: 14,
  },
  cardTitle:      { fontSize: 15, fontWeight: "700", marginBottom: 6 },
  bodyText:       { fontSize: 14, lineHeight: 20 },
  bodyTextSmall:  { fontSize: 12, lineHeight: 17 },

  sectionTitle:   { fontSize: 13, fontWeight: "700", marginBottom: 8, opacity: 0.85 },

  grid:           { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  gridChip:       {
    width: "31%", aspectRatio: 1.2, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center", padding: 6, gap: 3,
  },
  gridChipText:   { fontSize: 12, fontWeight: "600", textAlign: "center" },
  gridChipSub:    { fontSize: 10, textAlign: "center", opacity: 0.85 },

  dirGrid:        { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  dirChip:        {
    width: "23%", aspectRatio: 1, borderRadius: 12, borderWidth: 1,
    alignItems: "center", justifyContent: "center", gap: 2,
  },
  dirShort:       { fontSize: 16, fontWeight: "800" },
  dirHi:          { fontSize: 10 },

  submitBtn:      {
    height: 50, borderRadius: 14, alignItems: "center", justifyContent: "center",
    marginTop: 18, shadowOpacity: 0.2, shadowRadius: 8, shadowOffset: { width: 0, height: 4 },
    elevation: 3,
  },
  submitText:     { color: "#fff", fontSize: 16, fontWeight: "700" },

  errCard:        {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    borderRadius: 12, borderWidth: 1, padding: 12, marginTop: 16,
  },
  errTitle:       { fontSize: 14, fontWeight: "700", marginBottom: 2 },
  errBody:        { fontSize: 13, lineHeight: 18 },
  upgradeBtn:     {
    paddingVertical: 10, paddingHorizontal: 14, borderRadius: 10,
    alignItems: "center",
  },
  upgradeText:    { color: "#fff", fontWeight: "700", fontSize: 13 },

  resultCard:     { borderRadius: 16, borderWidth: 1, padding: 14, marginTop: 18 },
  verdictPill:    {
    alignSelf: "flex-start", paddingHorizontal: 14, paddingVertical: 8,
    borderRadius: 24, borderWidth: 1, alignItems: "center",
  },
  verdictPillText:{ fontSize: 16, fontWeight: "800" },
  verdictPillHi:  { fontSize: 12, fontWeight: "600", opacity: 0.85 },

  sevRow:         { flexDirection: "row", gap: 6, marginTop: 10, alignItems: "center" },
  metaLabel:      { fontSize: 12 },
  metaValue:      { fontSize: 12, fontWeight: "700" },

  section:        { borderTopWidth: 1, paddingTop: 12, marginTop: 14 },
  sectionLabel:   { fontSize: 12, fontWeight: "800", textTransform: "uppercase", letterSpacing: 0.5 },

  remedyItem:     {
    flexDirection: "row", gap: 10, paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  remedyBullet:   {
    width: 22, height: 22, borderRadius: 11,
    alignItems: "center", justifyContent: "center",
  },
  remedyBulletText:{ color: "#fff", fontSize: 11, fontWeight: "800" },
  refText:        { fontSize: 11, marginTop: 4, opacity: 0.85 },

  brandingFooter: {
    fontSize: 12, textAlign: "center", marginTop: 28, fontWeight: "600",
  },
  brandingFooterSmall: {
    fontSize: 10, textAlign: "center", marginTop: 4, opacity: 0.7,
  },
});
