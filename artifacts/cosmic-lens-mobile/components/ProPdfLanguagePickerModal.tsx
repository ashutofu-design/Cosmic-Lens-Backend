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
  View,
} from "react-native";
import { useC } from "@/context/ThemeContext";
import { PRO_PDF_LANG_OPTIONS } from "@/lib/proPdfLang";

export interface ProPdfLanguagePickerModalProps {
  visible: boolean;
  selectedLang: string;
  onSelectLang: (code: string) => void;
  onClose: () => void;
  onContinue: () => void;
  title?: string;
  subtitle?: string;
}

/** Milan-style PDF language picker — English, Hinglish, Hindi. */
export function ProPdfLanguagePickerModal({
  visible,
  selectedLang,
  onSelectLang,
  onClose,
  onContinue,
  title = "PDF Language Chunein",
  subtitle = "Pro compatibility PDF: English, Roman Hinglish, या देवनागरी Hindi।",
}: ProPdfLanguagePickerModalProps) {
  const C = useC();

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
                <Text style={[s.title, { color: C.text }]}>{title}</Text>
                <Text style={[s.sub, { color: C.textDim }]}>{subtitle}</Text>
              </View>

              <ScrollView
                style={{ maxHeight: 340, marginTop: 14, marginBottom: 14 }}
                contentContainerStyle={{ paddingVertical: 4 }}
                showsVerticalScrollIndicator={false}
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
                          numberOfLines={1}
                        >
                          {L.english}
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
                  <Text style={[s.changeTxt, { color: C.text }]}>Cancel</Text>
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
                    <Text style={s.continueTxt}>Continue</Text>
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
