import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import {
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useC } from "@/context/ThemeContext";
import { LOVE_REALITY_DELIVERY_OPTIONS } from "@/lib/loveRealityProCopy";
import { LOVE_REALITY_URGENT_SURCHARGE_INR } from "@/lib/loveRealityProOffer";
import {
  coerceProPdfLang,
  PRO_PDF_LANG_OPTIONS,
  proPdfLangPickerUi,
} from "@/lib/proPdfLang";

export type ProPdfDeliveryDetails = {
  priorityDelivery: boolean;
  onPriorityDeliveryChange: (value: boolean) => void;
};

export interface ProPdfLanguagePickerModalProps {
  visible: boolean;
  selectedLang: string;
  onSelectLang: (code: string) => void;
  onClose: () => void;
  onContinue: () => void;
  title?: string;
  subtitle?: string;
  delivery?: ProPdfDeliveryDetails;
}

/** Milan-style PDF language picker — English, Hinglish, Hindi. */
export function ProPdfLanguagePickerModal({
  visible,
  selectedLang,
  onSelectLang,
  onClose,
  onContinue,
  title,
  subtitle,
  delivery,
}: ProPdfLanguagePickerModalProps) {
  const C = useC();
  const uiLang = coerceProPdfLang(selectedLang);
  const ui = proPdfLangPickerUi(uiLang);
  const titleText = title ?? ui.title;
  const subtitleText = subtitle ?? ui.subtitle;
  const priorityOption = LOVE_REALITY_DELIVERY_OPTIONS[1];

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={s.backdrop} onPress={onClose}>
        <BlurView
          intensity={Platform.OS === "ios" ? 30 : 80}
          tint="dark"
          style={StyleSheet.absoluteFillObject}
        />
        <Pressable style={s.cardWrap} onPress={e => e.stopPropagation?.()}>
          <LinearGradient
            colors={["#8B5CF6", "#EC4899", "#F59E0B"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={s.borderGradient}
          >
            <View
              style={[
                s.card,
                {
                  backgroundColor: C.isDark ? "#0F0A1F" : "#FFFFFF",
                },
              ]}
            >
              <View style={s.header}>
                <LinearGradient
                  colors={["#8B5CF6", "#EC4899"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={s.iconCircle}
                >
                  <Feather name="globe" size={18} color="#fff" />
                </LinearGradient>
                <View style={s.headerText}>
                  <Text style={[s.title, { color: C.text }]}>{titleText}</Text>
                  <Text style={[s.sub, { color: C.textDim }]} numberOfLines={1}>
                    {subtitleText}
                  </Text>
                </View>
              </View>

              <Text style={[s.sectionLbl, { color: C.textDim }]}>Language</Text>
              <View style={s.langRow}>
                {PRO_PDF_LANG_OPTIONS.map(L => {
                  const sel = selectedLang === L.code;
                  return (
                    <Pressable
                      key={L.code}
                      onPress={() => {
                        Haptics.selectionAsync();
                        onSelectLang(L.code);
                      }}
                      style={({ pressed }) => [
                        s.langChip,
                        {
                          borderColor: sel ? "#8B5CF6" : C.isDark ? "rgba(255,255,255,0.12)" : "#E5E7EB",
                          backgroundColor: sel
                            ? C.isDark
                              ? "rgba(139,92,246,0.2)"
                              : "rgba(139,92,246,0.1)"
                            : C.isDark
                              ? "rgba(255,255,255,0.03)"
                              : "#F9FAFB",
                          opacity: pressed ? 0.85 : 1,
                        },
                      ]}
                    >
                      <Text
                        style={[
                          s.langChipTxt,
                          { color: sel ? (C.isDark ? "#e9d5ff" : "#6d28d9") : C.text },
                        ]}
                        numberOfLines={1}
                      >
                        {L.native}
                      </Text>
                      {sel ? <Feather name="check" size={11} color="#8B5CF6" /> : null}
                    </Pressable>
                  );
                })}
              </View>

              {delivery ? (
                <View
                  style={[
                    s.deliveryCard,
                    {
                      borderColor: C.isDark ? "rgba(255,255,255,0.1)" : "#E5E7EB",
                      backgroundColor: C.isDark ? "rgba(255,255,255,0.03)" : "#F9FAFB",
                    },
                  ]}
                >
                  <View style={s.deliveryTop}>
                    <Text style={[s.deliveryHead, { color: C.text }]}>{ui.deliveryHead}</Text>
                    <Text style={[s.deliveryLine, { color: C.textDim }]} numberOfLines={1}>
                      {ui.deliveryLine}
                    </Text>
                  </View>
                  <Pressable
                    onPress={() => {
                      delivery.onPriorityDeliveryChange(!delivery.priorityDelivery);
                      Haptics.selectionAsync();
                    }}
                    style={[
                      s.urgentRow,
                      {
                        borderColor: delivery.priorityDelivery ? "#f59e0b" : C.border,
                        backgroundColor: delivery.priorityDelivery
                          ? C.isDark
                            ? "rgba(245,158,11,0.1)"
                            : "rgba(245,158,11,0.06)"
                          : "transparent",
                      },
                    ]}
                  >
                    <Text style={[s.urgentTitle, { color: C.text }]} numberOfLines={1}>
                      {priorityOption.emoji} {priorityOption.title} · {priorityOption.eta} · +₹
                      {LOVE_REALITY_URGENT_SURCHARGE_INR}
                    </Text>
                    <View
                      style={[
                        s.check,
                        {
                          borderColor: delivery.priorityDelivery ? "#f59e0b" : C.border,
                          backgroundColor: delivery.priorityDelivery ? "#f59e0b" : "transparent",
                        },
                      ]}
                    >
                      {delivery.priorityDelivery ? (
                        <Feather name="check" size={11} color="#fff" />
                      ) : null}
                    </View>
                  </Pressable>
                  <Text style={[s.priorityRefund, { color: C.textMuted }]} numberOfLines={2}>
                    {ui.priorityRefund}
                  </Text>
                </View>
              ) : null}

              <View style={s.actions}>
                <Pressable
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    onClose();
                  }}
                  style={({ pressed }) => [
                    s.changeBtn,
                    {
                      backgroundColor: C.isDark ? "rgba(255,255,255,0.05)" : "#F3F4F6",
                      borderColor: C.isDark ? "rgba(255,255,255,0.12)" : "#E5E7EB",
                      opacity: pressed ? 0.7 : 1,
                    },
                  ]}
                >
                  <Feather name="x" size={13} color={C.text} />
                  <Text style={[s.changeTxt, { color: C.text }]}>{ui.cancel}</Text>
                </Pressable>
                <Pressable
                  onPress={() => {
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
                    onContinue();
                  }}
                  style={({ pressed }) => [s.continueBtn, { opacity: pressed ? 0.85 : 1 }]}
                >
                  <LinearGradient
                    colors={["#8B5CF6", "#EC4899", "#F59E0B"]}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={s.continueGrad}
                  >
                    <Feather name="arrow-right" size={14} color="#fff" />
                    <Text style={s.continueTxt}>{ui.continue}</Text>
                  </LinearGradient>
                </Pressable>
              </View>
            </View>
          </LinearGradient>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const s = StyleSheet.create({
  backdrop: { flex: 1, alignItems: "center", justifyContent: "center", padding: 20 },
  cardWrap: { width: "100%", maxWidth: 400 },
  borderGradient: { borderRadius: 22, padding: 1.5 },
  card: { borderRadius: 20, paddingHorizontal: 16, paddingTop: 14, paddingBottom: 14 },
  header: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 12 },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  headerText: { flex: 1, gap: 1 },
  title: { fontSize: 16, fontFamily: "Nunito_700Bold", letterSpacing: -0.3 },
  sub: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  sectionLbl: {
    fontSize: 10,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.6,
    textTransform: "uppercase",
    marginBottom: 6,
  },
  langRow: { flexDirection: "row", gap: 6 },
  langChip: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingVertical: 8,
    paddingHorizontal: 4,
    borderRadius: 10,
    borderWidth: 1,
  },
  langChipTxt: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  deliveryCard: {
    marginTop: 10,
    borderRadius: 12,
    borderWidth: 1,
    padding: 10,
    gap: 8,
  },
  deliveryTop: { gap: 2 },
  deliveryHead: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  deliveryLine: { fontSize: 10.5, fontFamily: "Nunito_400Regular" },
  urgentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 10,
  },
  urgentTitle: { flex: 1, fontSize: 11, fontFamily: "Nunito_600SemiBold" },
  priorityRefund: { fontSize: 10, fontFamily: "Nunito_500Medium", lineHeight: 14 },
  check: {
    width: 18,
    height: 18,
    borderRadius: 5,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  actions: { flexDirection: "row", gap: 8, marginTop: 12 },
  changeBtn: {
    flex: 0.75,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 5,
    height: 42,
    borderRadius: 12,
    borderWidth: 1,
  },
  changeTxt: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  continueBtn: {
    flex: 1.25,
    height: 42,
    borderRadius: 12,
    overflow: "hidden",
  },
  continueGrad: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  continueTxt: { color: "#fff", fontSize: 13, fontFamily: "Nunito_700Bold" },
});
