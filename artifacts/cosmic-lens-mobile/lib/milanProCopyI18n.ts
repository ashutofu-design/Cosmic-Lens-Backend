import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";
import type { MilanProUnlockItem } from "@/lib/milanProCopy";
import type { ProPdfLangCode } from "@/lib/proPdfLang";

function p(lang: ProPdfLangCode, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export function milanProScreenCopy(lang: ProPdfLangCode) {
  return {
    title: p(lang, "Marriage Compatibility Pro", "Marriage Compatibility Pro", "विवाह अनुकूलता प्रो"),
    subtitle: p(
      lang,
      "Founder-verified marriage report",
      "Founder-verified shaadi report",
      "संस्थापक-सत्यापित विवाह रिपोर्ट",
    ),
    partnerMissing: p(
      lang,
      "Select partner on Relationship screen",
      "Relationship screen par partner select karein",
      "रिलेशनशिप स्क्रीन पर साथी चुनें",
    ),
    kundliMissing: p(
      lang,
      "Complete both kundlis to unlock Pro",
      "Pro unlock ke liye dono kundli complete karein",
      "प्रो अनलॉक के लिए दोनों कुंडली पूरी करें",
    ),
    orderPlacedTitle: p(lang, "Order placed!", "Order ho gaya!", "ऑर्डर हो गया!"),
    orderPlacedBody: (langLabel: string, etaLabel: string) =>
      p(
        lang,
        `Your verified Marriage Compatibility PDF (${langLabel}) will be prepared within ${etaLabel}. You'll get a notification when it's ready and it will auto-save in My Reports.`,
        `Aapki verified Marriage Compatibility PDF (${langLabel}) ${etaLabel} mein tayyar hogi. Ready hote hi notification milegi aur My Reports mein auto-save hogi.`,
        `आपकी सत्यापित विवाह अनुकूलता PDF (${langLabel}) ${etaLabel} में तैयार होगी। तैयार होते ही सूचना मिलेगी और My Reports में सेव होगी।`,
      ),
    loginRequired: p(
      lang,
      "Please sign in to order your verified Marriage Compatibility PDF.",
      "Verified Marriage PDF order ke liye login karein.",
      "सत्यापित PDF ऑर्डर के लिए लॉगिन करें।",
    ),
  };
}

export function milanProPurchaseCopy(lang: ProPdfLangCode) {
  const partnerMeta = p(
    lang,
    " · Basic structure → full marriage answers",
    " · Basic structure → poori shaadi answers",
    " · बेसिक संरचना → पूरी विवाह जानकारी",
  );
  return {
    partnerMeta,
    hero: {
      emoji: "💍",
      title: p(lang, "Marry or Wait?", "Shaadi karein ya wait?", "शादी करें या इंतज़ार?"),
      line: p(
        lang,
        "#1 reason people order — right match and wedding timing?",
        "#1 reason log order karte hain — sahi match aur wedding timing?",
        "#1 कारण लोग ऑर्डर करते हैं — सही मिलान और शादी का समय?",
      ),
    },
    founderTrust: {
      title: p(
        lang,
        "Personally Prepared by Founder Astrologer",
        "Founder astrologer ne personally banaya",
        "संस्थापक ज्योतिषी ने व्यक्तिगत रूप से तैयार किया",
      ),
      description: p(
        lang,
        "Every report is manually reviewed after studying both charts. Not an auto-generated AI dump.",
        "Har report dono charts padh ke manually review hoti hai. Auto AI dump nahi.",
        "हर रिपोर्ट दोनों कुंडली पढ़कर मैन्युअल समीक्षा। ऑटो AI डंप नहीं।",
      ),
      bullets: [
        p(lang, "Founder-reviewed", "Founder-reviewed", "संस्थापक समीक्षा"),
        p(lang, "Marriage-focused PDF", "Shaadi-focused PDF", "विवाह केंद्रित PDF"),
        p(lang, "Remedies included", "Upay included", "उपाय शामिल"),
        p(lang, "Saved in My Reports", "My Reports mein save", "My Reports में सेव"),
      ],
    },
    coreQuestionsTitle: p(
      lang,
      "Your Report Answers These 3 Questions",
      "Aapki report ye 3 sawal jawab deti hai",
      "आपकी रिपोर्ट ये ३ सवालों के जवाब देती है",
    ),
    coreQuestions: [
      p(lang, "Should we get married?", "Kya shaadi karni chahiye?", "क्या शादी करनी चाहिए?"),
      p(lang, "Will this marriage last?", "Kya ye shaadi tikegi?", "क्या यह विवाह टिकेगा?"),
      p(lang, "When is the best wedding window?", "Best wedding window kab hai?", "सबसे अच्छा विवाह समय कब?"),
    ],
    reportSectionTitle: p(lang, "What's Inside Your Report", "Report mein kya hai", "रिपोर्ट में क्या है"),
    unlockItems: [
      {
        emoji: "🏠",
        title: p(lang, "D1 Marriage Structure", "D1 Marriage Structure", "D1 विवाह संरचना"),
        description: p(
          lang,
          "7th house & lord — marriage foundation for both.",
          "7th house & lord — dono ka marriage base.",
          "७वें भाव और स्वामी — दोनों का विवाह आधार।",
        ),
        shortHook: p(lang, "Birth chart marriage base", "Birth chart marriage base", "जन्म कुंडली विवाह आधार"),
      },
      {
        emoji: "💫",
        title: p(lang, "D9 Long-Term Bond", "D9 Long-Term Bond", "D9 दीर्घकालिक बंधन"),
        description: p(
          lang,
          "Navamsa tone — long married life together.",
          "Navamsa tone — saath ki long married life.",
          "नवांश स्वर — साथ की लंबी वैवाहिक जीवन।",
        ),
        shortHook: p(lang, "Inner chart long-term tone", "Inner chart long-term tone", "अंतर्कुंडली दीर्घकालिक स्वर"),
      },
      {
        emoji: "🔗",
        title: p(lang, "Cross-Chart Synastry", "Cross-Chart Synastry", "क्रॉस-चार्ट सिनास्ट्री"),
        description: p(
          lang,
          "How each partner's marriage ruler affects the other.",
          "Har partner ka marriage ruler doosre par kaise asar.",
          "प्रत्येक साथी का विवाह स्वामी दूसरे पर कैसे प्रभाव।",
        ),
        shortHook: p(lang, "How you affect each other", "Aapas mein kaise affect", "एक-दूसरे पर प्रभाव"),
      },
      {
        emoji: "🔥",
        title: p(lang, "Manglik & Alerts", "Manglik & Alerts", "मांगलिक और अलर्ट"),
        description: p(
          lang,
          "Manglik balance and hidden cross-chart warnings.",
          "Manglik balance aur hidden cross-chart warnings.",
          "मांगलिक संतुलन और छिपी चेतावनियाँ।",
        ),
        shortHook: p(lang, "Risks Basic hides", "Jo Basic chhupata hai", "जो बेसिक छुपाता है"),
      },
      {
        emoji: "📅",
        title: p(lang, "Marriage Dasha Windows", "Marriage Dasha Windows", "विवाह दशा खिड़कियाँ"),
        description: p(
          lang,
          "Best and risky wedding timing for both.",
          "Dono ke liye best aur risky wedding timing.",
          "दोनों के लिए शुभ और जोखिम भरा समय।",
        ),
        shortHook: p(lang, "When to marry — when to wait", "Kab shaadi — kab wait", "कब शादी — कब इंतज़ार"),
      },
      {
        emoji: "🪔",
        title: p(lang, "Remedies & Pro PDF", "Upay & Pro PDF", "उपाय और प्रो PDF"),
        description: p(
          lang,
          "Personalized upay + founder PDF in My Reports.",
          "Personalized upay + founder PDF My Reports mein.",
          "व्यक्तिगत उपाय + संस्थापक PDF My Reports में।",
        ),
        shortHook: p(lang, "Full remedy map", "Poora upay map", "पूरा उपाय मानचित्र"),
      },
    ] as MilanProUnlockItem[],
    deliveryOptions: [
      {
        emoji: "📦",
        title: p(lang, "Standard Delivery", "Standard Delivery", "स्टैंडर्ड डिलीवरी"),
        eta: p(lang, "4–6 business days", "4–6 business days", "४–६ कार्य दिवस"),
        surchargeInr: 0,
      },
      {
        emoji: "⚡",
        title: p(lang, "Priority Delivery", "Priority Delivery", "प्राथमिकता डिलीवरी"),
        eta: p(lang, "Within 12 hours", "12 ghante mein", "१२ घंटे में"),
        surchargeInr: 299,
      },
    ],
    priorityRefund: p(
      lang,
      "12-hour Priority Guarantee — If we miss the 12-hour delivery window, your Priority fee is 100% refunded.",
      "12-hour Priority Guarantee — 12 ghante miss hue to Priority fee 100% refund.",
      "१२-घंटे प्राथमिकता गारंटी — यदि १२ घंटे की डिलीवरी छूट गई तो केवल प्राथमिकता शुल्क १००% वापस।",
    ),
    trustBar: p(
      lang,
      "🔒 Secure Payment • Founder Reviewed • Delivered in My Reports",
      "🔒 Secure Payment • Founder Reviewed • My Reports mein deliver",
      "🔒 सुरक्षित भुगतान • संस्थापक समीक्षा • My Reports में डिलीवरी",
    ),
    ctaTitle: p(
      lang,
      "Get My Personalized Marriage Compatibility Report",
      "Meri Personalized Marriage Compatibility Report lo",
      "मेरी व्यक्तिगत विवाह अनुकूलता रिपोर्ट लें",
    ),
    addPartnerCta: p(lang, "Add partner kundli", "Partner kundli add karein", "साथी कुंडली जोड़ें"),
    productPickerTitle: p(
      lang,
      "Choose how you want it",
      "Kaise chahiye — choose karein",
      "कैसे चाहिए — चुनें",
    ),
    productPickerSubtitle: p(
      lang,
      "Most people start with the PDF report. Video is a personal WhatsApp explanation.",
      "Zyada log PDF report se shuru karte hain. Video personal WhatsApp explanation hai.",
      "ज़्यादा लोग PDF रिपोर्ट से शुरू करते हैं। वीडियो पर्सनल WhatsApp एक्सप्लेनेशन है।",
    ),
    productReportBadge: p(lang, "MOST POPULAR", "MOST POPULAR", "सबसे लोकप्रिय"),
    productVideoBadge: p(lang, "1:1 VIDEO", "1:1 VIDEO", "1:1 वीडियो"),
    productReportTitle: p(lang, "Kundli Milan Pro Report", "Kundli Milan Pro Report", "कुंडली मिलान प्रो रिपोर्ट"),
    productReportHint: p(
      lang,
      "Full PDF · saved in My Reports · re-read anytime",
      "Full PDF · My Reports mein save · kabhi bhi padho",
      "पूरी PDF · My Reports में सेव · कभी भी पढ़ें",
    ),
    productVideoTitle: p(lang, "Personalized Video Explanation", "Personalized Video Explanation", "पर्सनलाइज़्ड वीडियो एक्सप्लेनेशन"),
    productVideoHint: p(
      lang,
      "Founder explains on WhatsApp · no PDF included",
      "Founder WhatsApp par explain · PDF shamil nahi",
      "संस्थापक WhatsApp पर समझाएँगे · PDF शामिल नहीं",
    ),
    videoWhatsappTitle: p(lang, "WhatsApp number", "WhatsApp number", "WhatsApp नंबर"),
    videoWhatsappHint: p(
      lang,
      "We'll send your Personalized Video Explanation here.",
      "Personalized Video Explanation yahin bhejenge.",
      "पर्सनलाइज़्ड वीडियो एक्सप्लेनेशन यहीं भेजेंगे।",
    ),
    videoWhatsappPlaceholder: p(lang, "10-digit WhatsApp number", "10-digit WhatsApp number", "10 अंकों का WhatsApp नंबर"),
    videoStandardLine: p(
      lang,
      "📱 WhatsApp · 4–6 business days · no PDF/report",
      "📱 WhatsApp · 4–6 business days · PDF/report nahi",
      "📱 WhatsApp · ४–६ कार्य दिवस · PDF/रिपोर्ट नहीं",
    ),
    videoTrustBar: p(
      lang,
      "🔒 Secure Payment · Founder reviewed · Delivered on WhatsApp",
      "🔒 Secure Payment · Founder reviewed · WhatsApp par deliver",
      "🔒 सुरक्षित भुगतान · संस्थापक समीक्षा · WhatsApp पर डिलीवरी",
    ),
    ctaVideoTitle: p(
      lang,
      "Get Personalized Video Explanation",
      "Personalized Video Explanation lo",
      "पर्सनलाइज़्ड वीडियो एक्सप्लेनेशन लें",
    ),
    whatsappRequired: p(
      lang,
      "Enter your WhatsApp number to receive the video.",
      "Video ke liye WhatsApp number darj karein.",
      "वीडियो पाने के लिए WhatsApp नंबर दर्ज करें।",
    ),
    savings: (savingsInr: number) =>
      p(lang, `You saved ₹${savingsInr} today`, `Aaj ₹${savingsInr} bachaye`, `आज ₹${savingsInr} बचाए`),
  };
}
