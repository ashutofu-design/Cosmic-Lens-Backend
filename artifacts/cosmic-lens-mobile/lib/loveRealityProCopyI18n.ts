import type { ProPdfLangCode } from "@/lib/proPdfLang";
import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";
import type { LoveProUnlockItem } from "@/lib/loveRealityProCopy";

function p(lang: ProPdfLangCode, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export function loveRealityProScreenCopy(lang: ProPdfLangCode) {
  return {
    title: p(lang, "Love Reality Pro", "Love Reality Pro", "लव रियलिटी प्रो"),
    subtitle: p(
      lang,
      "Founder-verified relationship report",
      "Founder-verified rishta report",
      "संस्थापक-सत्यापित रिश्ता रिपोर्ट",
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
        `Your verified Love Reality PDF (${langLabel}) will be prepared within ${etaLabel}. You'll get a notification when it's ready and it will auto-save in My Reports.`,
        `Aapki verified Love Reality PDF (${langLabel}) ${etaLabel} mein tayyar hogi. Ready hote hi notification milegi aur My Reports mein auto-save hogi.`,
        `आपकी सत्यापित लव रियलिटी PDF (${langLabel}) ${etaLabel} में तैयार होगी। तैयार होते ही सूचना मिलेगी और My Reports में सेव होगी।`,
      ),
    loginRequired: p(
      lang,
      "Please sign in to order your verified Love Reality PDF.",
      "Verified Love Reality PDF order ke liye login karein.",
      "सत्यापित PDF ऑर्डर के लिए लॉगिन करें।",
    ),
    addPartnerCta: p(lang, "Add partner kundli", "Partner kundli add karein", "साथी कुंडली जोड़ें"),
    basicLockedHint: p(
      lang,
      "*Exact reason for this score is locked in your Pro PDF.",
      "*Is score ka exact reason aapki Pro PDF mein locked hai.",
      "*इस स्कोर का सटीक कारण आपकी प्रो PDF में लॉक है।",
    ),
  };
}

export function loveRealityProPurchaseCopy(lang: ProPdfLangCode) {
  const partnerMeta = p(
    lang,
    " · Basic scores → full answers",
    " · Basic scores → poori answers",
    " · बेसिक स्कोर → पूरी जानकारी",
  );
  return {
    partnerMeta,
    hero: {
      emoji: "🔄",
      title: p(lang, "Return or Move On?", "Wapas aayenge ya move on?", "वापस आएंगे या आगे बढ़ें?"),
      line: p(
        lang,
        "#1 reason people order — wait, reconcile, or move on?",
        "#1 reason log order karte hain — wait, patch up, ya move on?",
        "#1 कारण लोग ऑर्डर करते हैं — इंतज़ार, मिलान, या आगे बढ़ना?",
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
        "Every report is manually reviewed and prepared after studying both charts. This is not an auto-generated AI report.",
        "Har report manually review hoti hai dono charts dekh kar. Ye auto AI report nahi hai.",
        "हर रिपोर्ट दोनों कुंडली देखकर मैन्युअल तैयार होती है। यह ऑटो AI रिपोर्ट नहीं है।",
      ),
      bullets: [
        p(lang, "Founder-reviewed", "Founder-reviewed", "संस्थापक-समीक्षित"),
        p(lang, "Personalized PDF", "Personalized PDF", "व्यक्तिगत PDF"),
        p(lang, "Remedies included", "Upay included", "उपाय शामिल"),
        p(lang, "Saved in My Reports", "My Reports mein save", "My Reports में सेव"),
      ],
    },
    coreQuestionsTitle: p(
      lang,
      "Your Report Answers These 3 Questions",
      "Aapki report ye 3 sawal answer karti hai",
      "आपकी रिपोर्ट ये ३ सवालों के जवाब देती है",
    ),
    coreQuestions: [
      p(lang, "Do they really love me?", "Kya wo sach mein mujhse pyar karte hain?", "क्या वे सच में मुझसे प्यार करते हैं?"),
      p(lang, "Will we survive or break up?", "Kya hum tikenge ya breakup hoga?", "क्या हम टिकेंगे या अलग होंगे?"),
      p(lang, "Should I wait or move on?", "Wait karun ya move on karun?", "इंतज़ार करूँ या आगे बढ़ूँ?"),
    ],
    reportSectionTitle: p(
      lang,
      "What's Inside Your Report",
      "Report mein kya hai",
      "रिपोर्ट में क्या है",
    ),
    unlockItems: [
      {
        emoji: "❤️",
        title: p(lang, "Emotional Reality", "Emotional Reality", "भावनात्मक सच्चाई"),
        description: p(
          lang,
          "What they actually feel for you — beyond surface behaviour.",
          "Wo aapke liye asli mein kya feel karte hain — surface behaviour se aage.",
          "वे आपके लिए वास्तव में क्या महसूस करते हैं — ऊपरी व्यवहार से आगे।",
        ),
        shortHook: p(
          lang,
          "What they truly feel — not just what they show",
          "Asli feelings — jo dikhate hain sirf woh nahi",
          "असली भाव — सिर्फ जो दिखाते हैं वही नहीं",
        ),
      },
      {
        emoji: "🛡️",
        title: p(lang, "Loyalty & Intentions", "Loyalty & Intentions", "निष्ठा और इरादे"),
        description: p(
          lang,
          "Real intent behind their actions — devoted, tempted, or unsure.",
          "Actions ke peeche asli intent — loyal, tempted, ya unsure.",
          "कर्मों के पीछे असली इरादा — वफ़ादार, प्रलोभित, या अनिश्चित।",
        ),
        shortHook: p(
          lang,
          "Real intent — loyal, tempted, or unsure",
          "Asli intent — loyal, tempted, ya unsure",
          "असली इरादा — वफ़ादार, प्रलोभित, या अनिश्चित",
        ),
      },
      {
        emoji: "💔",
        title: p(lang, "Breakup / Critical Window", "Breakup / Critical Window", "ब्रेकअप / महत्वपूर्ण समय"),
        description: p(
          lang,
          "Whether this bond can survive — and when risk peaks.",
          "Kya ye rishta tik sakta hai — aur risk kab peak hota hai.",
          "क्या यह बंधन टिक सकता है — और जोखिम कब चरम पर होता है।",
        ),
        shortHook: p(
          lang,
          "Survive together or break — and when risk peaks",
          "Saath tikoge ya break — risk kab peak",
          "साथ टिकोगे या अलग — जोखिम कब चरम",
        ),
      },
      {
        emoji: "🔄",
        title: p(lang, "Return or Move On", "Return or Move On", "वापसी या आगे बढ़ना"),
        description: p(
          lang,
          "Your clearest wait-or-go answer — reconcile or walk away.",
          "Sabse clear wait-or-go answer — patch up ya walk away.",
          "सबसे स्पष्ट इंतज़ार या आगे का जवाब — मिलान या अलग होना।",
        ),
        shortHook: p(
          lang,
          "Wait, patch up, or walk away for good",
          "Wait, patch up, ya hamesha ke liye move on",
          "इंतज़ार, मिलान, या हमेशा के लिए आगे बढ़ना",
        ),
      },
      {
        emoji: "🔮",
        title: p(lang, "Future Timeline", "Future Timeline", "भविष्य समयरेखा"),
        description: p(
          lang,
          "Next 3 months, 12 months, and major turning points.",
          "Agle 3 mahine, 12 mahine, aur major turning points.",
          "अगले ३ महीने, १२ महीने, और बड़े मोड़।",
        ),
        shortHook: p(
          lang,
          "3 months, 12 months, and major turning points",
          "3 mahine, 12 mahine, major turning points",
          "३ महीने, १२ महीने, बड़े मोड़",
        ),
      },
      {
        emoji: "🚩",
        title: p(lang, "Red Flags & Remedies", "Red Flags & Upay", "चेतावनी और उपाय"),
        description: p(
          lang,
          "Hidden risks plus personalized upay — what to watch and what to do.",
          "Hidden risks + personalized upay — kya dekhein aur kya karein.",
          "छिपे जोखिम + व्यक्तिगत उपाय — क्या देखें और क्या करें।",
        ),
        shortHook: p(
          lang,
          "What to watch and what to do",
          "Kya dekhein aur kya karein",
          "क्या देखें और क्या करें",
        ),
      },
    ] as LoveProUnlockItem[],
    deliveryOptions: [
      {
        emoji: "📦",
        title: p(lang, "Standard Delivery", "Standard Delivery", "स्टैंडर्ड डिलीवरी"),
        eta: p(lang, "Within 24 hours", "24 ghante mein", "२४ घंटे में"),
        surchargeInr: 0,
      },
      {
        emoji: "⚡",
        title: p(lang, "Priority Delivery", "Priority Delivery", "प्राथमिकता डिलीवरी"),
        eta: p(lang, "Within 12 hours", "12 ghante mein", "१२ घंटे में"),
        surchargeInr: 300,
      },
    ],
    priorityRefund: p(
      lang,
      "Not in My Reports within 12 hours? ₹300 priority fee refunded.",
      "12 ghante mein My Reports mein nahi? ₹300 priority fee refund.",
      "१२ घंटे में My Reports में नहीं? ₹३०० प्राथमिकता शुल्क वापस।",
    ),
    trustBar: p(
      lang,
      "🔒 Secure Payment • Founder Reviewed • Delivered in My Reports",
      "🔒 Secure Payment • Founder Reviewed • My Reports mein deliver",
      "🔒 सुरक्षित भुगतान • संस्थापक समीक्षा • My Reports में डिलीवरी",
    ),
    ctaTitle: p(
      lang,
      "Get My Personalized Relationship Report",
      "Meri Personalized Relationship Report lo",
      "मेरी व्यक्तिगत रिश्ता रिपोर्ट लें",
    ),
    addPartnerCta: p(lang, "Add partner kundli", "Partner kundli add karein", "साथी कुंडली जोड़ें"),
    ctaMicrocopy: p(
      lang,
      "Prepared manually after reviewing both charts. No generic AI-generated report is delivered.",
      "Dono charts review ke baad manually tayyar. Generic AI report deliver nahi hoti.",
      "दोनों कुंडली समीक्षा के बाद मैन्युअल तैयार। जेनेरिक AI रिपोर्ट नहीं मिलती।",
    ),
    savings: (savingsInr: number) =>
      p(lang, `You saved ₹${savingsInr} today`, `Aaj ₹${savingsInr} bachaye`, `आज ₹${savingsInr} बचाए`),
    basicBridge: p(
      lang,
      "You saw your Basic scores — this report explains what they mean and what to do next.",
      "Aapne Basic scores dekhe — ye report batati hai unka matlab aur aage kya karein.",
      "आपने बेसिक स्कोर देखे — यह रिपोर्ट उनका मतलब और आगे क्या करें बताती है।",
    ),
  };
}

export function loveRealityProLoadSteps(lang: ProPdfLangCode) {
  return [
    { n: 1, pct: 10, label: p(lang, "Preparing your report…", "Report tayyar ho rahi hai…", "रिपोर्ट तैयार हो रही है…") },
    { n: 2, pct: 20, label: p(lang, "Checking saved report…", "Saved report check…", "सेव्ड रिपोर्ट जाँच…") },
    { n: 3, pct: 30, label: p(lang, "Loading birth charts…", "Birth charts load…", "जन्म कुंडली लोड…") },
    { n: 4, pct: 40, label: p(lang, "Connecting to server…", "Server se connect…", "सर्वर से कनेक्ट…") },
    {
      n: 5,
      pct: 50,
      label: p(lang, "Writing personalized insights…", "Personalized insights likh rahe hain…", "व्यक्तिगत अंतर्दृष्टि लिख रहे हैं…"),
      llm: true,
      creepCap: 82,
    },
    { n: 6, pct: 88, label: p(lang, "Building report sections…", "Report sections bana rahe hain…", "रिपोर्ट सेक्शन बना रहे हैं…") },
    { n: 7, pct: 94, label: p(lang, "Almost ready…", "Almost ready…", "लगभग तैयार…") },
  ] as const;
}
