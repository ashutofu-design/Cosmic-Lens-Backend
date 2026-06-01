import * as Haptics from "expo-haptics";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { openBirthTimeRectificationWhatsApp } from "@/lib/founderWhatsApp";
import { vedicLang } from "@/lib/i18nVedic";

function labels(lang: ReturnType<typeof vedicLang>) {
  if (lang === "hi") {
    return {
      question: "सही जन्म समय नहीं पता?",
      click: "यहाँ क्लिक करें",
    };
  }
  if (lang === "hn") {
    return {
      question: "Sahi birth time nahi pata?",
      click: "Yahan click karein",
    };
  }
  return {
    question: "Don't know actual birth time?",
    click: "Click here",
  };
}

export function BirthTimeRectificationLink() {
  const C = useC();
  const { language } = useUser();
  const L = labels(vedicLang(language));

  return (
    <View style={s.row}>
      <Text style={[s.question, { color: C.textMuted }]}>{L.question} </Text>
      <Pressable
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
          void openBirthTimeRectificationWhatsApp();
        }}
        hitSlop={8}
      >
        <Text style={s.link}>{L.click}</Text>
      </Pressable>
    </View>
  );
}

const s = StyleSheet.create({
  row: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    marginTop: 10,
  },
  question: {
    fontSize: 12,
    lineHeight: 18,
  },
  link: {
    fontSize: 12,
    lineHeight: 18,
    fontWeight: "700",
    color: "#25D366",
    textDecorationLine: "underline",
  },
});
