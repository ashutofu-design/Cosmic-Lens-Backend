/**
 * MarkdownReply — themed markdown renderer for assistant messages.
 * Wraps react-native-markdown-display with theme-aware styles.
 */
import React from "react";
import { StyleSheet } from "react-native";
import Markdown from "react-native-markdown-display";

import { useC } from "@/context/ThemeContext";

type Props = { text: string };

export function MarkdownReply({ text }: Props) {
  const C = useC();
  const styles = StyleSheet.create({
    body:        { color: C.textMid, fontSize: 14.5, lineHeight: 21 },
    paragraph:   { marginTop: 0, marginBottom: 8 },
    strong:      { color: C.text, fontWeight: "800" },
    em:          { fontStyle: "italic", color: C.text },
    heading1:    { color: C.text, fontSize: 18, fontWeight: "800", marginTop: 4, marginBottom: 6 },
    heading2:    { color: C.text, fontSize: 16, fontWeight: "800", marginTop: 4, marginBottom: 6 },
    heading3:    { color: C.text, fontSize: 15, fontWeight: "700", marginTop: 4, marginBottom: 4 },
    bullet_list: { marginTop: 2, marginBottom: 6 },
    ordered_list:{ marginTop: 2, marginBottom: 6 },
    list_item:   { flexDirection: "row", marginBottom: 4 },
    bullet_list_icon: { color: C.accent, marginRight: 8, lineHeight: 21 },
    blockquote:  {
      backgroundColor: C.accentBg, borderLeftColor: C.accent, borderLeftWidth: 3,
      paddingHorizontal: 10, paddingVertical: 6, marginVertical: 6, borderRadius: 6,
    },
    code_inline: {
      backgroundColor: C.bgCard2, color: C.accent,
      paddingHorizontal: 5, paddingVertical: 1, borderRadius: 4,
      fontSize: 13,
    },
    fence: {
      backgroundColor: C.bgCard2, color: C.text,
      padding: 10, borderRadius: 8, fontSize: 13, marginVertical: 6,
    },
    hr: { backgroundColor: C.border, height: 1, marginVertical: 8 },
    link: { color: C.accent, textDecorationLine: "underline" },
  });

  return <Markdown style={styles}>{text || ""}</Markdown>;
}
