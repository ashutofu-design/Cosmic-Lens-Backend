import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useC } from "@/context/ThemeContext";
import { LOVE_REALITY_DELIVERY_OPTIONS } from "@/lib/loveRealityProCopy";
import { LOVE_REALITY_URGENT_SURCHARGE_INR } from "@/lib/loveRealityProOffer";
import {
  coerceProPdfLang,
  PRO_PDF_LANG_OPTIONS,
  proPdfLangOptionExplain,
  proPdfLangPickerUi,
  type ProPdfLangCode,
} from "@/lib/proPdfLang";

export type ProPdfDeliveryDetails = {
  contactMethod: "whatsapp" | "email";
  onContactMethodChange: (method: "whatsapp" | "email") => void;
  contactValue: string;
  onContactValueChange: (value: string) => void;
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
                  paddingHorizontal: 18,
                  paddingVertical: 22,
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
                  <Feather name="globe" size={22} color="#fff" />
                </LinearGradient>
                <Text style={[s.title, { color: C.text }]}>{titleText}</Text>
                <Text style={[s.sub, { color: C.textDim }]}>{subtitleText}</Text>
              </View>

              <ScrollView
                style={{ maxHeight: delivery ? 420 : 340, marginTop: 14, marginBottom: 14 }}
                contentContainerStyle={{ paddingVertical: 4 }}
                showsVerticalScrollIndicator={false}
                keyboardShouldPersistTaps="handled"
              >
                {PRO_PDF_LANG_OPTIONS.map(L => {
                  const sel = selectedLang === L.code;
                  return (
                    <Pressable
                      key={L.code}
                      onPress={() => {
                        Haptics.selectionAsync();
                        onSelectLang(L.code);
                      }}
                      style={({ pressed }) => ({
                        flexDirection: "row",
                        alignItems: "center",
                        paddingVertical: 12,
                        paddingHorizontal: 14,
                        marginBottom: 8,
                        borderRadius: 12,
                        borderWidth: sel ? 1.5 : 1,
                        borderColor: sel ? "#8B5CF6" : C.isDark ? "rgba(255,255,255,0.10)" : "#E5E7EB",
                        backgroundColor: sel
                          ? C.isDark
                            ? "rgba(139,92,246,0.18)"
                            : "rgba(139,92,246,0.08)"
                          : C.isDark
                            ? "rgba(255,255,255,0.03)"
                            : "#F9FAFB",
                        opacity: pressed ? 0.85 : 1,
                      })}
                    >
                      <View style={{ flex: 1 }}>
                        <Text
                          style={{
                            color: C.text,
                            fontSize: 16,
                            fontFamily: "Nunito_700Bold",
                          }}
                          numberOfLines={1}
                        >
                          {L.native}
                        </Text>
                        <Text
                          style={{
                            color: C.textDim,
                            fontSize: 11,
                            fontFamily: "Nunito_400Regular",
                            marginTop: 2,
                          }}
                          numberOfLines={2}
                        >
                          {proPdfLangOptionExplain(L.code as ProPdfLangCode, uiLang)}
                        </Text>
                      </View>
                      {sel ? (
                        <View
                          style={{
                            width: 22,
                            height: 22,
                            borderRadius: 11,
                            backgroundColor: "#8B5CF6",
                            alignItems: "center",
                            justifyContent: "center",
                          }}
                        >
                          <Feather name="check" size={13} color="#fff" />
                        </View>
                      ) : (
                        <View
                          style={{
                            width: 22,
                            height: 22,
                            borderRadius: 11,
                            borderWidth: 1.5,
                            borderColor: C.isDark ? "rgba(255,255,255,0.18)" : "#D1D5DB",
                          }}
                        />
                      )}
                    </Pressable>
                  );
                })}

                {delivery ? (
                  <View
                    style={[
                      s.deliveryCard,
                      {
                        borderColor: C.isDark ? "rgba(255,255,255,0.12)" : "#E5E7EB",
                        backgroundColor: C.isDark ? "rgba(255,255,255,0.03)" : "#F9FAFB",
                      },
                    ]}
                  >
                    <Text style={[s.deliveryHead, { color: C.text }]}>{ui.deliveryHead}</Text>
                    <View style={s.methodRow}>
                      {(["whatsapp", "email"] as const).map(m => (
                        <Pressable
                          key={m}
                          onPress={() => {
                            delivery.onContactMethodChange(m);
                            Haptics.selectionAsync();
                          }}
                          style={[
                            s.methodBtn,
                            {
                              borderColor: delivery.contactMethod === m ? "#ec4899" : C.border,
                              backgroundColor:
                                delivery.contactMethod === m ? "rgba(236,72,153,0.12)" : "transparent",
                            },
                          ]}
                        >
                          <Feather
                            name={m === "whatsapp" ? "message-circle" : "mail"}
                            size={14}
                            color="#ec4899"
                          />
                          <Text style={[s.methodTxt, { color: C.text }]}>
                            {m === "whatsapp" ? ui.whatsapp : ui.email}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                    <TextInput
                      value={delivery.contactValue}
                      onChangeText={delivery.onContactValueChange}
                      placeholder={
                        delivery.contactMethod === "whatsapp"
                          ? ui.whatsappPlaceholder
                          : ui.emailPlaceholder
                      }
                      placeholderTextColor={C.textMuted}
                      keyboardType={delivery.contactMethod === "whatsapp" ? "phone-pad" : "email-address"}
                      autoCapitalize="none"
                      style={[
                        s.input,
                        { color: C.text, borderColor: C.border, backgroundColor: C.bg },
                      ]}
                    />
                    <Pressable
                      onPress={() => {
                        delivery.onPriorityDeliveryChange(!delivery.priorityDelivery);
                        Haptics.selectionAsync();
                      }}
                      style={[
                        s.urgentRow,
                        { borderColor: delivery.priorityDelivery ? "#f59e0b" : C.border },
                      ]}
                    >
                      <View style={{ flex: 1 }}>
                        <Text style={[s.urgentTitle, { color: C.text }]}>
                          {priorityOption.emoji} {priorityOption.title}
                        </Text>
                        <Text style={[s.urgentSub, { color: C.textDim }]}>
                          {priorityOption.eta} · +₹{LOVE_REALITY_URGENT_SURCHARGE_INR}
                        </Text>
                      </View>
                      <View
                        style={[
                          s.check,
                          {
                            borderColor: delivery.priorityDelivery ? "#f59e0b" : C.border,
                            backgroundColor: delivery.priorityDelivery ? "#f59e0b" : "transparent",
                          },
                        ]}
                      >
                        {delivery.priorityDelivery ? <Feather name="check" size={14} color="#fff" /> : null}
                      </View>
                    </Pressable>
                  </View>
                ) : null}
              </ScrollView>

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
                  <Feather name="x" size={14} color={C.text} />
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
                    <Feather name="arrow-right" size={15} color="#fff" />
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
  cardWrap: { width: "100%", maxWidth: 420 },
  borderGradient: { borderRadius: 26, padding: 1.5 },
  card: { borderRadius: 24, padding: 22 },
  header: { alignItems: "center", marginBottom: 20 },
  iconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
    shadowColor: "#8B5CF6",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5,
    shadowRadius: 12,
    elevation: 8,
  },
  title: { fontSize: 20, fontFamily: "Nunito_700Bold", letterSpacing: -0.4, marginBottom: 6 },
  sub: {
    fontSize: 12,
    fontFamily: "Nunito_400Regular",
    textAlign: "center",
    lineHeight: 17,
    paddingHorizontal: 8,
  },
  deliveryCard: {
    marginTop: 4,
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    gap: 10,
  },
  deliveryHead: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  methodRow: { flexDirection: "row", gap: 10 },
  methodBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  methodTxt: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },
  input: {
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === "ios" ? 12 : 10,
    fontFamily: "Nunito_500Medium",
    fontSize: 15,
  },
  urgentRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
  },
  urgentTitle: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  urgentSub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 2 },
  check: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
  },
  actions: { flexDirection: "row", gap: 10 },
  changeBtn: {
    flex: 0.8,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 7,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
  },
  changeTxt: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  continueBtn: {
    flex: 1.2,
    height: 48,
    borderRadius: 14,
    overflow: "hidden",
    shadowColor: "#8B5CF6",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 10,
    elevation: 6,
  },
  continueGrad: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  continueTxt: { color: "#fff", fontSize: 14, fontFamily: "Nunito_700Bold", letterSpacing: 0.2 },
});
