import type { UILang } from "@/lib/i18n";

export type RiskLevel = "low" | "med" | "high";

type RiskDetail = {
  cat: string;
  detail: string;
  avoid: string;
  karna: string;
  remedy: string;
};

type RiskBucket = {
  shorts: string[];
  details: RiskDetail[];
};

export type LuckyColorEntry = { name: string; emoji: string; hex: string };

const RISK_EN: Record<RiskLevel, RiskBucket> = {
  low: {
    shorts: [
      "Stable day — stay focused on your work",
      "Cosmic energies are working in your favour",
      "A smooth-flow day overall",
    ],
    details: [
      {
        cat: "Career",
        detail: "A safe day to start new projects or pitches. Important conversations should stay productive.",
        avoid:  "Negative advice, pessimistic news, or self-doubt.",
        karna:  "Meetings, presentations, networking, and pitching new ideas.",
        remedy: "5 minutes of Surya Namaskar in the morning for an energy boost.",
      },
      {
        cat: "Money",
        detail: "A good day for investments and savings. Long-term financial decisions can be taken with care.",
        avoid:  "Unnecessary spending, impulse purchases, and gambling.",
        karna:  "Review SIPs, savings plans, or clear pending bills. Check your budget.",
        remedy: "Wearing yellow or golden tones is supportive today.",
      },
      {
        cat: "Health",
        detail: "Vitality should stay high. A strong day to build workouts, meditation, or healthy habits.",
        avoid:  "Junk food, late-night screen time, and alcohol.",
        karna:  "Yoga, walks, a healthy meal plan, and better hydration.",
        remedy: "Tulsi water in the morning supports overall wellness.",
      },
    ],
  },
  med: {
    shorts: [
      "Mixed signals — think before you decide",
      "Keep communication clear today",
      "Patience is today's mantra",
    ],
    details: [
      {
        cat: "Communication",
        detail: "Misunderstandings are more likely today. Double-check important messages and stay clear.",
        avoid:  "Unprepared calls, rushed important texts, and gossip.",
        karna:  "Get written confirmation, note key points, and listen first.",
        remedy: "Take 5 deep breaths before an important call or meeting.",
      },
      {
        cat: "Decisions",
        detail: "Postpone major decisions. Continue routine work and avoid new commitments today.",
        avoid:  "Big purchases, signing contracts, and fresh commitments.",
        karna:  "Review documents, plan ahead, and make a pros-and-cons list.",
        remedy: "Pause for 2 minutes with a glass of water before deciding.",
      },
      {
        cat: "Relationships",
        detail: "Speak with patience to family or your partner. Small issues can become bigger misunderstandings.",
        avoid:  "Sensitive topics, criticism, anger, and blame.",
        karna:  "Make time to listen, express gratitude, and share quality time.",
        remedy: "Light a diya at home in the evening for peace.",
      },
    ],
  },
  high: {
    shorts: [
      "Stay alert — postpone important decisions",
      "Try to avoid unnecessary conflict",
      "Energy may feel low — take care of yourself",
    ],
    details: [
      {
        cat: "Conflict",
        detail: "Arguments and disputes are more likely today. Avoid confrontations — silence can be strength today.",
        avoid:  "Arguments, blame, sharp words, and social media debates.",
        karna:  "Take solo time, meditate, and use breathing exercises.",
        remedy: "Hanuman Chalisa or Maha Mrityunjaya mantra 11 times.",
      },
      {
        cat: "Money",
        detail: "Avoid financial decisions strictly. Postpone new loans, investments, and big purchases.",
        avoid:  "Loans, investments, large purchases, and lending money.",
        karna:  "Review your budget, track expenses, and keep savings safe.",
        remedy: "Give a small donation — even a little help to others counts.",
      },
      {
        cat: "Health",
        detail: "Energy and immunity may feel lower. Skip heavy workouts and prioritise rest and hydration.",
        avoid:  "Heavy workouts, late nights, junk food, and alcohol.",
        karna:  "Hydrate, sleep well, eat light meals, and do gentle stretches.",
        remedy: "Ginger-turmeric water twice during the day.",
      },
    ],
  },
};

const RISK_HN: Record<RiskLevel, RiskBucket> = {
  low: {
    shorts: [
      "Stable din — apne kaam pe focus karo",
      "Cosmic energies aapke favor mein hain",
      "Smooth flow ka din hai",
    ],
    details: [
      {
        cat: "Career",
        detail: "Naye projects ya pitches start karne ka safe din. Important conversations productive rahengi.",
        avoid:  "Negative logon ki advice, pessimistic news, ya self-doubt.",
        karna:  "Meetings, presentations, networking, naye ideas pitch karein.",
        remedy: "Subah 5 minute Surya Namaskar — energy boost ke liye.",
      },
      {
        cat: "Money",
        detail: "Investments aur savings ke liye accha din. Long-term financial decisions safely le sakte hain.",
        avoid:  "Bekar ke kharch, impulse purchases, gambling.",
        karna:  "SIP, bachat schemes, ya bills clear karein. Budget review karein.",
        remedy: "Peeli ya golden kapde pehnna shubh rahega.",
      },
      {
        cat: "Health",
        detail: "Vitality high rahegi. Workout, meditation ya naye healthy habits build karne ka perfect time.",
        avoid:  "Junk food, late-night screen time, alcohol.",
        karna:  "Yoga, walk, healthy meal plan, hydration badhayein.",
        remedy: "Subah tulsi-paani — overall wellness ke liye.",
      },
    ],
  },
  med: {
    shorts: [
      "Mixed signals — soch samajh ke decisions lo",
      "Communication mein clarity rakhe",
      "Patience aaj ka mantra hai",
    ],
    details: [
      {
        cat: "Communication",
        detail: "Aaj misunderstandings hone ke chances zyada hain. Important messages double-check karein, clarity rakhein.",
        avoid:  "Voice calls bina prep ke, important texts jaldi mein, gossip.",
        karna:  "Written confirmation lein, points note karein, listen pehle.",
        remedy: "Important call ya meeting se pehle 5 deep breaths.",
      },
      {
        cat: "Decisions",
        detail: "Bade decisions postpone karein. Routine kaam continue, naye commitments aaj avoid karein.",
        avoid:  "Bade purchases, contracts sign karna, naye commitments.",
        karna:  "Documents review karein, planning karein, pros-cons list banayein.",
        remedy: "Decision se pehle paani peeke 2 min ruk jaayein.",
      },
      {
        cat: "Relations",
        detail: "Family ya partner se patience se baat karein. Choti baatein bade misunderstanding ban sakti hain.",
        avoid:  "Sensitive topics, criticism, gussa, blame game.",
        karna:  "Sunne ka time dein, gratitude express karein, quality time spend karein.",
        remedy: "Shaam ko ghar mein diya jalaayein — peace ke liye.",
      },
    ],
  },
  high: {
    shorts: [
      "Saavdhan rahe — important decisions postpone karo",
      "Conflicts avoid karne ki koshish kare",
      "Energy low — apna khayal rakhe",
    ],
    details: [
      {
        cat: "Conflict",
        detail: "Aaj arguments aur disputes hone ke chances bahut zyada hain. Confrontations avoid karein — silence is power aaj.",
        avoid:  "Arguments, blame game, sharp words, social media debates.",
        karna:  "Solo time lein, meditation karein, breathing exercises.",
        remedy: "Hanuman Chalisa ya Maha Mrityunjaya 11 baar.",
      },
      {
        cat: "Money",
        detail: "Financial decisions strictly avoid. Naye loans, investments aur big purchases postpone karein.",
        avoid:  "Loans, investments, bade purchases, kisi ko paisa udhaar dena.",
        karna:  "Budget review karein, expenses track karein, savings safe karein.",
        remedy: "Daan karein — chhota hi sahi, doosron ki madad.",
      },
      {
        cat: "Health",
        detail: "Energy aur immunity low rahegi. Heavy workouts skip karein, rest aur hydration priority dein.",
        avoid:  "Heavy workouts, late nights, junk food, alcohol.",
        karna:  "Hydration, neend, light meals, gentle stretches.",
        remedy: "Adrak-haldi paani din mein 2 baar.",
      },
    ],
  },
};

const RISK_HI: Record<RiskLevel, RiskBucket> = {
  low: {
    shorts: [
      "स्थिर दिन — अपने काम पर ध्यान दें",
      "ब्रह्मांडीय ऊर्जाएँ आपके पक्ष में हैं",
      "सहज प्रवाह का दिन है",
    ],
    details: [
      {
        cat: "करियर",
        detail: "नए प्रोजेक्ट या प्रस्ताव शुरू करने का सुरक्षित दिन। महत्वपूर्ण बातचीत उत्पादक रहेगी।",
        avoid:  "नकारात्मक सलाह, निराशाजनक समाचार या आत्म-संदेह।",
        karna:  "मीटिंग, प्रेज़ेंटेशन, नेटवर्किंग, नए विचार प्रस्तुत करें।",
        remedy: "सुबह ५ मिनट सूर्य नमस्कार — ऊर्जा बढ़ाने के लिए।",
      },
      {
        cat: "धन",
        detail: "निवेश और बचत के लिए अच्छा दिन। दीर्घकालिक वित्तीय निर्णय सुरक्षित रूप से ले सकते हैं।",
        avoid:  "अनावश्यक खर्च, आवेग में खरीदारी, जुआ।",
        karna:  "एसआईपी, बचत योजनाएँ या बिल चुकाएँ। बजट की समीक्षा करें।",
        remedy: "पीले या सुनहरे वस्त्र पहनना शुभ रहेगा।",
      },
      {
        cat: "स्वास्थ्य",
        detail: "ऊर्जा उच्च रहेगी। व्यायाम, ध्यान या नई स्वस्थ आदतें बनाने का उत्तम समय।",
        avoid:  "जंक फूड, देर रात स्क्रीन टाइम, शराब।",
        karna:  "योग, टहलना, स्वस्थ भोजन योजना, हाइड्रेशन बढ़ाएँ।",
        remedy: "सुबह तुलसी-जल — समग्र कल्याण के लिए।",
      },
    ],
  },
  med: {
    shorts: [
      "मिश्रित संकेत — सोच-समझकर निर्णय लें",
      "संवाद में स्पष्टता रखें",
      "धैर्य आज का मंत्र है",
    ],
    details: [
      {
        cat: "संवाद",
        detail: "आज गलतफ़हमियों की संभावना अधिक है। महत्वपूर्ण संदेश दोबारा जाँचें, स्पष्टता रखें।",
        avoid:  "बिना तैयारी के कॉल, जल्दबाज़ी में महत्वपूर्ण संदेश, गपशप।",
        karna:  "लिखित पुष्टि लें, बिंदु नोट करें, पहले सुनें।",
        remedy: "महत्वपूर्ण कॉल या मीटिंग से पहले ५ गहरी साँसें।",
      },
      {
        cat: "निर्णय",
        detail: "बड़े निर्णय टालें। नियमित काम जारी रखें, नई प्रतिबद्धताएँ आज टालें।",
        avoid:  "बड़ी खरीदारी, अनुबंध पर हस्ताक्षर, नई प्रतिबद्धताएँ।",
        karna:  "दस्तावेज़ समीक्षा करें, योजना बनाएँ, फायदे-नुकसान सूची बनाएँ।",
        remedy: "निर्णय से पहले पानी पीकर २ मिनट रुकें।",
      },
      {
        cat: "संबंध",
        detail: "परिवार या साथी से धैर्य से बात करें। छोटी बातें बड़ी गलतफ़हमी बना सकती हैं।",
        avoid:  "संवेदनशील विषय, आलोचना, क्रोध, दोषारोपण।",
        karna:  "सुनने का समय दें, कृतज्ञता व्यक्त करें, गुणवत्तापूर्ण समय बिताएँ।",
        remedy: "शाम को घर में दीप जलाएँ — शांति के लिए।",
      },
    ],
  },
  high: {
    shorts: [
      "सावधान रहें — महत्वपूर्ण निर्णय टालें",
      "विवादों से बचने की कोशिश करें",
      "ऊर्जा कम — अपना ख्याल रखें",
    ],
    details: [
      {
        cat: "विवाद",
        detail: "आज बहस और विवाद की संभावना बहुत अधिक है। टकराव से बचें — आज मौन ही शक्ति है।",
        avoid:  "बहस, दोषारोपण, तीखे शब्द, सोशल मीडिया पर बहस।",
        karna:  "अकेले समय लें, ध्यान करें, श्वास अभ्यास।",
        remedy: "हनुमान चालीसा या महामृत्युंजय ११ बार।",
      },
      {
        cat: "धन",
        detail: "वित्तीय निर्णय सख्ती से टालें। नए ऋण, निवेश और बड़ी खरीदारी स्थगित करें।",
        avoid:  "ऋण, निवेश, बड़ी खरीदारी, किसी को उधार देना।",
        karna:  "बजट समीक्षा करें, खर्च ट्रैक करें, बचत सुरक्षित रखें।",
        remedy: "दान करें — छोटा ही सही, दूसरों की मदद।",
      },
      {
        cat: "स्वास्थ्य",
        detail: "ऊर्जा और प्रतिरक्षा कम रहेगी। भारी व्यायाम छोड़ें, आराम और हाइड्रेशन को प्राथमिकता दें।",
        avoid:  "भारी व्यायाम, देर रात जागना, जंक फूड, शराब।",
        karna:  "हाइड्रेशन, नींद, हल्का भोजन, हल्के स्ट्रेच।",
        remedy: "अदरक-हल्दी पानी दिन में २ बार।",
      },
    ],
  },
};

const LUCKY_COLORS_EN: Record<RiskLevel, LuckyColorEntry[]> = {
  low: [
    { name: "Green",  emoji: "🟢", hex: "#4ade80" },
    { name: "Yellow", emoji: "🟡", hex: "#facc15" },
    { name: "White",  emoji: "⚪", hex: "#f3f4f6" },
  ],
  med: [
    { name: "Blue",   emoji: "🔵", hex: "#60a5fa" },
    { name: "Yellow", emoji: "🟡", hex: "#facc15" },
    { name: "Golden", emoji: "🟠", hex: "#fb923c" },
  ],
  high: [
    { name: "White",  emoji: "⚪", hex: "#f3f4f6" },
    { name: "Saffron", emoji: "🟠", hex: "#fb923c" },
    { name: "Yellow", emoji: "🟡", hex: "#facc15" },
  ],
};

const LUCKY_COLORS_HN: Record<RiskLevel, LuckyColorEntry[]> = {
  low: [
    { name: "Hara",     emoji: "🟢", hex: "#4ade80" },
    { name: "Pila",     emoji: "🟡", hex: "#facc15" },
    { name: "Safed",    emoji: "⚪", hex: "#f3f4f6" },
  ],
  med: [
    { name: "Neela",    emoji: "🔵", hex: "#60a5fa" },
    { name: "Pila",     emoji: "🟡", hex: "#facc15" },
    { name: "Suneheri", emoji: "🟠", hex: "#fb923c" },
  ],
  high: [
    { name: "Safed",    emoji: "⚪", hex: "#f3f4f6" },
    { name: "Kesari",   emoji: "🟠", hex: "#fb923c" },
    { name: "Pila",     emoji: "🟡", hex: "#facc15" },
  ],
};

const LUCKY_COLORS_HI: Record<RiskLevel, LuckyColorEntry[]> = {
  low: [
    { name: "हरा",     emoji: "🟢", hex: "#4ade80" },
    { name: "पीला",     emoji: "🟡", hex: "#facc15" },
    { name: "सफ़ेद",    emoji: "⚪", hex: "#f3f4f6" },
  ],
  med: [
    { name: "नीला",    emoji: "🔵", hex: "#60a5fa" },
    { name: "पीला",     emoji: "🟡", hex: "#facc15" },
    { name: "सुनहरा", emoji: "🟠", hex: "#fb923c" },
  ],
  high: [
    { name: "सफ़ेद",    emoji: "⚪", hex: "#f3f4f6" },
    { name: "केसरी",   emoji: "🟠", hex: "#fb923c" },
    { name: "पीला",     emoji: "🟡", hex: "#facc15" },
  ],
};

export function getRiskBucket(lang: UILang, level: RiskLevel): RiskBucket {
  if (lang === "hi") return RISK_HI[level];
  if (lang === "hn") return RISK_HN[level];
  return RISK_EN[level];
}

export function getLuckyColors(lang: UILang, level: RiskLevel): LuckyColorEntry[] {
  if (lang === "hi") return LUCKY_COLORS_HI[level];
  if (lang === "hn") return LUCKY_COLORS_HN[level];
  return LUCKY_COLORS_EN[level];
}
