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
    gunLockHint: p(
      L,
      "Select both kundlis — scores preview here before you tap Check",
      "Dono kundli select karein — Check se pehle yahan preview dikhega",
      "दोनों कुंडली चुनें — जाँच से पहले यहाँ स्कोर दिखेंगे",
    ),
    partnerA: p(L, "PARTNER A", "PARTNER A", "साथी A"),
    partnerB: p(L, "PARTNER B", "PARTNER B", "साथी B"),
    genderMale: p(L, "Male", "Male", "पुरुष"),
    genderFemale: p(L, "Female", "Female", "महिला"),
    genderChart: p(L, "Chart", "Chart", "चार्ट"),
    unlockInPro: p(L, "Unlock in Pro →", "Unlock in Pro →", "प्रो में खोलें →"),
    proDetailSuffix: p(L, "full detail in Pro.", "poora detail Pro mein.", "पूर्ण विवरण प्रो में।"),
    coupleGapEyebrow: p(
      L,
      "TOGETHER — WHAT BASIC HIDES",
      "TOGETHER — BASIC KYA CHHUPATA HAI",
      "साथ में — बेसिक क्या छिपाता है",
    ),
    coupleBands: {
      Promising: p(L, "Promising", "Promising", "आशाजनक"),
      Workable: p(L, "Workable", "Workable", "काम चलने योग्य"),
      "High Effort": p(L, "High Effort", "High Effort", "उच्च प्रयास"),
    },
    coupleVerdict: {
      Promising: p(
        L,
        "Both marriage axes show supportive structure — if these two marry, long-term direction can grow well with steady effort.",
        "Dono marriage axes supportive structure dikhate hain — shaadi ke baad steady effort se long-term direction achhi ho sakti hai.",
        "दोनों विवाह अक्ष सहायक संरचना दिखाते हैं — यदि ये दो विवाह करें, तो निरंतर प्रयास से दीर्घकालिक दिशा अच्छी बढ़ सकती है।",
      ),
      Workable: p(
        L,
        "Marriage is workable but not effortless — strengths exist on both sides; friction points need conscious handling after wedding.",
        "Shaadi workable hai par effortless nahi — dono taraf strengths hain; friction points ko shaadi ke baad consciously handle karna hoga.",
        "विवाह संभव है पर सहज नहीं — दोनों ओर शक्तियाँ हैं; घर्षण बिंदुओं को विवाह के बाद सचेत रूप से संभालना होगा।",
      ),
      "High Effort": p(
        L,
        "High effort match — marriage is possible but demands patience, remedies, and realistic expectations on both charts.",
        "High effort match — shaadi possible hai par patience, upay aur realistic expectations dono charts par chahiye.",
        "उच्च प्रयास मिलान — विवाह संभव है पर धैर्य, उपाय और दोनों चार्ट पर यथार्थवादी अपेक्षाएँ ज़रूरी हैं।",
      ),
    },
    fallbackPositive: p(
      L,
      "Chart shows some supportive marriage signals.",
      "Chart me kuch supportive marriage signals hain.",
      "चार्ट में कुछ सहायक विवाह संकेत दिखते हैं।",
    ),
    fallbackWatchout: p(
      L,
      "Stay conscious before big decisions.",
      "Bade faislon se pehle sachet rahein.",
      "बड़े निर्णयों से पहले सचेत रहें।",
    ),
    fallbackProLock: p(
      L,
      "Deeper marriage timing + hidden alerts — unlock in Pro.",
      "Gehri marriage timing + hidden alerts — Pro mein unlock karein.",
      "गहरी विवाह समयरेखा + छिपे अलर्ट — प्रो में अनलॉक करें।",
    ),
    fallbackRemedy: p(
      L,
      "Full personalized remedy chain — Pro report mein.",
      "Poori personalized remedy chain — Pro report mein.",
      "पूर्ण व्यक्तिगत उपाय श्रृंखला — प्रो रिपोर्ट में।",
    ),
    fallbackProStrip: (name: string) =>
      p(
        L,
        `Pro for ${name}: full marriage consultation + PDF`,
        `Pro ${name} ke liye: poori marriage consultation + PDF`,
        `प्रो ${name} के लिए: पूर्ण विवाह परामर्श + PDF`,
      ),
    defaultGapTeaser: (score: number) =>
      p(
        L,
        `Together ${score}/100 — full cross-chart marriage read sirf Pro mein.`,
        `Saath mein ${score}/100 — poori cross-chart marriage read sirf Pro mein.`,
        `साथ में ${score}/100 — पूर्ण क्रॉस-चार्ट विवाह रीडिंग केवल प्रो में।`,
      ),
    defaultGapCta: p(
      L,
      "Unlock Full Match Report — synastry · dasha · remedies · PDF",
      "Poori Match Report unlock karein — synastry · dasha · upay · PDF",
      "पूर्ण मिलान रिपोर्ट अनलॉक करें — सिनैस्ट्री · दशा · उपाय · PDF",
    ),
    lockedHighlights: {
      alerts: (n: number) =>
        p(
          L,
          `${n} hidden alert(s) across both charts`,
          `Dono charts mein ${n} hidden alert(s)`,
          `दोनों चार्ट में ${n} छिपे अलर्ट`,
        ),
      synastry: p(
        L,
        "Cross-chart 7th lord synastry — how you affect each other",
        "Cross-chart 7th lord synastry — aap ek doosre ko kaise affect karte hain",
        "क्रॉस-चार्ट सप्तम स्वामी सिनैस्ट्री — आप एक-दूसरे को कैसे प्रभावित करते हैं",
      ),
      manglik: p(
        L,
        "Manglik balance & cancellation for both charts",
        "Dono charts ke liye Manglik balance aur cancellation",
        "दोनों चार्ट के लिए मांगलिक संतुलन और निवारण",
      ),
      dasha: p(
        L,
        "Marriage dasha windows — best & risky timing (both partners)",
        "Marriage dasha windows — best aur risky timing (dono partners)",
        "विवाह दशा विंडो — सर्वोत्तम और जोखिम भरा समय (दोनों साथी)",
      ),
      pdf: p(
        L,
        "Full remedy chain + downloadable PDF",
        "Poori remedy chain + downloadable PDF",
        "पूर्ण उपाय श्रृंखला + डाउनलोड योग्य PDF",
      ),
    },
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
    landing: {
      title: p(L, "Compatibility Check", "Compatibility Check", "अनुकूलता जाँच"),
      subtitle: p(
        L,
        "Scans 28+ Hidden Relationship Risks, Loyalty Flaws & Separation Dashas. Don't Risk Your Future with Just 36 Gun Milan",
        "28+ hidden relationship risks, loyalty flaws aur separation dashas scan karta hai. Sirf 36 Gun Milan par apna future risk mat lo",
        "28+ छिपे रिश्ते के जोखिम, निष्ठा की कमियाँ और अलगाव की दशाएँ स्कैन करता है। सिर्फ 36 गुण मिलान पर अपना भविष्य दाँव पर न लगाएँ",
      ),
      selectPartner: p(L, "Select Partner for Milan", "Milan ke liye Partner chunein", "मिलान के लिए साथी चुनें"),
      selectPartnerSub: p(
        L,
        "Both moon signs & nakshatras needed for Gun Milan scores",
        "Gun Milan scores ke liye dono ke moon sign aur nakshatra chahiye",
        "गुण मिलन स्कोर के लिए दोनों के चंद्र राशि और नक्षत्र ज़रूरी हैं",
      ),
      chartsReady: p(
        L,
        "Charts ready · tap Check Compatibility",
        "Charts ready · Check Compatibility dabayein",
        "चार्ट तैयार · अनुकूलता जाँच दबाएँ",
      ),
      checkBtn: p(L, "Check Compatibility", "Check Compatibility", "अनुकूलता जाँचें"),
      hintNoPartner: (youLabel: string) =>
        p(
          L,
          `Select ${youLabel} & partner first`,
          `Pehle ${youLabel} aur partner chunein`,
          `पहले ${youLabel} और साथी चुनें`,
        ),
      hintReady: p(
        L,
        "Tap Check Compatibility for full 36 Gun breakdown",
        "Poora 36 Gun breakdown ke liye Check Compatibility dabayein",
        "पूर्ण 36 गुण विवरण के लिए अनुकूलता जाँच दबाएँ",
      ),
      youAstroLabel: p(L, "You", "Aap", "आप"),
      partnerAstroLabel: p(L, "Partner", "Partner", "साथी"),
      rashiNakshatra: (rashi: string, nakshatra: string) =>
        p(L, `${rashi} · ${nakshatra}`, `${rashi} · ${nakshatra}`, `${rashi} · ${nakshatra}`),
      whatYouGetTitle: p(L, "WHAT YOU'LL GET", "AAPKO KYA MILEGA", "आपको क्या मिलेगा"),
      benefitStructure: p(
        L,
        "Marriage Structure score /100 — main chart reading",
        "Marriage Structure score /100 — main chart reading",
        "विवाह संरचना स्कोर /100 — मुख्य चार्ट रीडिंग",
      ),
      benefitGun: p(
        L,
        "8 Gun Milan dimensions — classical /36 breakdown",
        "8 Gun Milan dimensions — classical /36 breakdown",
        "8 गुण मिलान आयाम — शास्त्रीय /36 विवरण",
      ),
      benefitPartners: p(
        L,
        "Separate reading for both partners",
        "Dono partners ke liye alag reading",
        "दोनों साथियों की अलग-अलग रीडिंग",
      ),
      lensNoteShort: p(
        L,
        "Structure (/100) and Gun Milan (/36) can differ — both are normal.",
        "Structure (/100) aur Gun Milan (/36) alag ho sakte hain — normal hai.",
        "संरचना (/100) और गुण मिलन (/36) अलग हो सकते हैं — यह सामान्य है।",
      ),
      proTeaser: p(
        L,
        "Want dasha timing, synastry & PDF? Switch to Pro ↑",
        "Dasha timing, synastry aur PDF chahiye? Pro par jayein ↑",
        "दशा समय, सिनैस्ट्री और PDF चाहिए? प्रो पर जाएँ ↑",
      ),
      kootPreviewLabel: p(L, "8 MATCH DIMENSIONS", "8 MATCH DIMENSIONS", "8 मिलान आयाम"),
    },
  };
}

export type MilanResultScreenCopy = ReturnType<typeof milanResultScreenCopy>;

export type CoupleBandKey = keyof MilanResultScreenCopy["coupleBands"];
