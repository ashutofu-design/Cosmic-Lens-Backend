import { coerceUILang, type UILang } from "@/lib/i18n";
import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";

function p(lang: UILang, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export function milanResultScreenCopy(lang: UILang) {
  const L = coerceUILang(lang);
  return {
    basicMode: p(L, "YOU ARE IN BASIC MODE", "YOU ARE IN BASIC MODE", "आप बेसिक मोड में हैं"),
    primaryBadge: p(L, "PRIMARY SCORE", "PRIMARY SCORE", "मुख्य स्कोर"),
    structureTitle: p(L, "Marriage Structure", "Marriage Structure", "विवाह संरचना"),
    structureSubtitle: p(
      L,
      "7th house · D9 · chart depth — your main reading",
      "7th house · D9 · chart depth — aapka main reading",
      "सप्तम भाव · नवांश · चार्ट गहराई — आपकी मुख्य रीडिंग",
    ),
    twoLensExplainer: p(
      L,
      "Two different lenses. Structure (/100) = long-term marriage chart strength. Gun Milan (/36) = classical Moon match. Both can differ — that is normal.",
      "Do alag lenses. Structure (/100) = long-term marriage chart. Gun Milan (/36) = classical Moon match. Dono alag ho sakte hain — normal hai.",
      "दो अलग रीडिंग। संरचना (/100) = दीर्घकालिक विवाह चार्ट। गुण मिलन (/36) = शास्त्रीय चंद्र मिलान। दोनों अलग हो सकते हैं — यह सामान्य है।",
    ),
    gunReference: p(L, "REFERENCE", "REFERENCE", "संदर्भ"),
    gunTitle: p(L, "Traditional Gun Milan", "Traditional Gun Milan", "पारंपरिक गुण मिलन"),
    gunSubtitle: p(
      L,
      "Classical Moon match · 8 koots · out of 36",
      "Classical Moon match · 8 koots · out of 36",
      "शास्त्रीय चंद्र मिलान · 8 कूट · 36 में से",
    ),
    partnerA: p(L, "PARTNER A", "PARTNER A", "साथी A"),
    partnerB: p(L, "PARTNER B", "PARTNER B", "साथी B"),
    gunGrades: {
      excellent: p(L, "Excellent", "Excellent", "उत्कृष्ट"),
      veryGood: p(L, "Very Good", "Very Good", "बहुत अच्छा"),
      average: p(L, "Average", "Average", "औसत"),
      belowAvg: p(L, "Below Avg", "Below Avg", "औसत से कम"),
      lowMatch: p(L, "Low Match", "Low Match", "कम मिलान"),
    },
    kootTitles: {
      varna: p(L, "Life Path", "Life Path", "जीवन पथ"),
      vasya: p(L, "Mutual Pull", "Mutual Pull", "पारस्परिक खिंचाव"),
      tara: p(L, "Destiny Link", "Destiny Link", "भाग्य कड़ी"),
      yoni: p(L, "Intimacy Match", "Intimacy Match", "अंतरंगता मिलान"),
      maitri: p(L, "Mind Sync", "Mind Sync", "मन का मेल"),
      gana: p(L, "Temperament", "Temperament", "स्वभाव"),
      bhakut: p(L, "Emotional Bond", "Emotional Bond", "भावनात्मक बंधन"),
      nadi: p(L, "Soul Sync", "Soul Sync", "आत्मा मेल"),
    },
    kootClassical: {
      varna: p(L, "Varna", "Varna", "वर्ण"),
      vasya: p(L, "Vasya", "Vasya", "वश्य"),
      tara: p(L, "Tara", "Tara", "तारा"),
      yoni: p(L, "Yoni", "Yoni", "योनि"),
      maitri: p(L, "Graha Maitri", "Graha Maitri", "ग्रह मैत्री"),
      gana: p(L, "Gana", "Gana", "गण"),
      bhakut: p(L, "Bhakut", "Bhakut", "भकूट"),
      nadi: p(L, "Nadi", "Nadi", "नाड़ी"),
    },
  };
}

export type MilanResultScreenCopy = ReturnType<typeof milanResultScreenCopy>;
