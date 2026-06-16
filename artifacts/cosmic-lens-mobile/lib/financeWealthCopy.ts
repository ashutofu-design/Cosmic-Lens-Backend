import { coerceUILang, type UILang } from "@/lib/i18n";
import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";

function p(lang: UILang, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export type WealthTierKey = "middle_class" | "rich" | "ultra_rich" | "millionaire";

export const WEALTH_TIER_ORDER: readonly WealthTierKey[] = [
  "middle_class",
  "rich",
  "ultra_rich",
  "millionaire",
];

/** Wealth Builder score → tier (must match server wealth_tier_from_score). */
export function wealthTierFromScore(score: number): WealthTierKey {
  const c = Math.round(score);
  if (c >= 85) return "millionaire";
  if (c >= 72) return "ultra_rich";
  if (c >= 60) return "rich";
  return "middle_class";
}
export type LiquidityKey = "high" | "moderate" | "restricted";
export type LeakageKey =
  | "property_legal_loss_risk"
  | "speculation_trading_fraud_risk"
  | "expense_drain_active";

export type LeakChannelKey =
  | "subscriptions_small_spend"
  | "emi_debt"
  | "medical_hospital"
  | "property_legal"
  | "sudden_loss_tax"
  | "speculation_trading"
  | "partnership_client_loss"
  | "family_shared_money"
  | "foreign_online_spend"
  | "impulsive_fines"
  | "savings_dont_stick"
  | "income_not_retained"
  | "kp_savings_leak"
  | "kp_income_leak";

export function financeWealthCopy(lang: UILang) {
  const L = coerceUILang(lang);
  return {
    yogTitle: p(L, "Wealth Yogas", "Wealth yogas", "धन योग"),
    yogSub: p(
      L,
      "Prosperity and status combinations in your birth chart.",
      "Chart ke dhana aur raj yog — detail ke liye card tap karo.",
      "जन्म कुंडली के धन और राज योग — विवरण के लिए कार्ड दबाएँ।",
    ),
    activation: (pct: number) =>
      p(L, `${pct}% active now`, `${pct}% abhi active`, `अभी ${pct}% सक्रिय`),
    dhanCount: (n: number) =>
      p(L, `${n} dhana yogas`, `${n} dhana yog`, `${n} धन योग`),
    rajCount: (n: number) =>
      p(L, `${n} raj links`, `${n} raj yog link`, `${n} राज योग लिंक`),
    dhanYogCard: p(L, "Dhan Yog", "Dhan Yog", "धन योग"),
    rajYogCard: p(L, "Raj Yog", "Raj Yog", "राज योग"),
    inChart: p(L, "in your chart", "chart me", "आपकी कुंडली में"),
    tapDhanHint: p(L, "Tap Dhan Yog card for details", "Dhan Yog card tap karo — detail", "धन योग कार्ड दबाएँ — विवरण"),
    tapYogHint: p(L, "Tap Dhan or Raj Yog cards for details", "Dhan / Raj Yog card tap karo — detail", "धन या राज योग कार्ड दबाएँ — विवरण"),
    dhanDetailTitle: p(L, "How your Dhan Yogas formed", "Dhan yog kaise bane", "धन योग कैसे बने"),
    dhanDetailSub: p(
      L,
      "Each row shows the yoga name and the chart link that created it.",
      "Har line me yog ka naam aur chart link dikhega.",
      "हर पंक्ति में योग और कुंडली लिंक।",
    ),
    dhanEmpty: p(L, "No dhan yoga combination found in this chart.", "Is chart me dhan yog combo nahi.", "इस कुंडली में धन योग संयोग नहीं।"),
    rajDetailTitle: p(L, "How your Raj Yogas formed", "Raj yog kaise bane", "राज योग कैसे बने"),
    rajDetailSub: p(
      L,
      "Kendra-trikona links, placements, and special status yogas in your chart.",
      "Kendra-trikona link, placement aur status yog.",
      "केंद्र-त्रिकोण लिंक, स्थिति और विशेष राज योग।",
    ),
    rajEmpty: p(L, "No raj yoga combination found in this chart.", "Is chart me raj yog combo nahi.", "इस कुंडली में राज योग संयोग नहीं।"),
    close: p(L, "Close", "Band karo", "बंद करें"),
    linkType: {
      conjunction: p(L, "Same house", "Ek hi ghar me", "एक ही भाव में"),
      mutual_aspect: p(L, "Mutual aspect", "Mutual aspect", "परस्पर दृष्टि"),
      parivartana: p(L, "Lord exchange", "Lord parivartana", "स्वामी परिवर्तन"),
      karaka: p(L, "Strong karaka", "Strong karaka", "बलवान कारक"),
      placement: p(L, "House placement", "Ghar me baitha", "भाव में स्थित"),
    } as Record<string, string>,
    housePair: (a: number, b: number) =>
      p(L, `Houses ${a} & ${b} lords`, `${a} aur ${b} ghar ke lord`, `${a} और ${b} भाव के स्वामी`),
    housesLine: (houses: number[]) =>
      p(
        L,
        `Houses ${houses.join(", ")}`,
        `Ghar ${houses.join(", ")}`,
        `भाव ${houses.join(", ")}`,
      ),
    matrixTitle: p(L, "Wealth Chart Layers", "Wealth chart layers", "धन चार्ट परतें"),
    d1Label: p(L, "Visible wealth (D1)", "Dikhne wala dhana (D1)", "दृश्य धन (D1)"),
    d9Label: p(L, "Long-term stability (D9)", "Lambi stability (D9)", "दीर्घकालिक स्थिरता (D9)"),
    d2Label: p(L, "Asset style (D2)", "Asset style (D2)", "संपत्ति शैली (D2)"),
    d1Strong: p(L, "Strong", "Strong", "मजबूत"),
    d1Moderate: p(L, "Building", "Building", "बन रहा"),
    d9Stable: p(L, "Stable", "Stable", "स्थिर"),
    d9Building: p(L, "Growing", "Growing", "बढ़ रहा"),
    d2Chandra: p(L, "Smooth accumulation", "Smooth accumulation", "सहज संचय"),
    d2Surya: p(L, "Effort & authority build", "Mehnat se build", "परिश्रम से निर्माण"),
    d2Mixed: p(L, "Balanced mix", "Mixed style", "मिश्रित शैली"),
    tierTitle: p(L, "Wealth Tier", "Wealth tier", "धन स्तर"),
    dashaTimingView: p(L, "View", "Dekho", "देखें"),
    dashaTimingTitle: p(L, "Wealth Dasha Timing", "Wealth dasha timing", "धन दशा समय"),
    dashaTimingSub: p(
      L,
      "From your current Mahadasha forward (next 100 years). Higher score = better wealth flow in that MD/AD.",
      "Current MD se aage 100 saal — zyada score = us MD/AD me paisa flow better.",
      "वर्तमान MD से आगे 100 वर्ष — अधिक स्कोर = उस MD/AD में बेहतर धन प्रवाह।",
    ),
    dashaBaseLabel: p(L, "Birth wealth base", "Birth wealth base", "जन्म धन आधार"),
    dashaBestMd: p(L, "Best Mahadasha", "Best MD", "सर्वोत्तम महादशा"),
    dashaBestAd: p(L, "Best Antardasha", "Best AD", "सर्वोत्तम अंतर्दशा"),
    dashaWealthTag: p(L, "Wealth-linked", "Wealth-linked", "धन से जुड़ा"),
    dashaMdLabel: p(L, "MD", "MD", "MD"),
    dashaAdLabel: p(L, "AD", "AD", "AD"),
    dashaNoData: p(
      L,
      "Dasha timeline not available — complete birth chart first.",
      "Dasha data nahi — pehle birth chart poora karein.",
      "दशा डेटा उपलब्ध नहीं — पहले जन्म कुंडली पूरी करें।",
    ),
    leakageTitle: p(L, "Wealth Leak Alerts", "Paisa leak alerts", "धन रिसाव अलर्ट"),
    leakageEmpty: p(
      L,
      "No major leak signal in chart.",
      "Chart me major leak signal nahi.",
      "चार्ट में कोई बड़ा रिसाव संकेत नहीं।",
    ),
    liquidityTitle: p(L, "Cash Flow Mood", "Cash flow mood", "नकद प्रवाह"),
    liquidity: {
      high: p(L, "Supportive liquidity phase", "Cash flow supportive", "अनुकूल नकदी चरण"),
      moderate: p(L, "Steady — plan big moves", "Steady — bade plans soch ke", "स्थिर — बड़े निर्णय सोच समझकर"),
      restricted: p(L, "Tight flow — save first", "Tight — pehle bachat", "कमजोर प्रवाह — पहले बचत"),
    } as Record<LiquidityKey, string>,
    leakage: {
      property_legal_loss_risk: p(
        L,
        "Property or legal expense risk — double-check contracts.",
        "Property/legal kharcha risk — papers dhyaan se dekho.",
        "संपत्ति/कानूनी खर्च जोखिम — कागज़ ध्यान से देखें।",
      ),
      speculation_trading_fraud_risk: p(
        L,
        "Speculation or rushed trading risk — avoid impulsive bets.",
        "Trading/speculation risk — jaldi faisla mat lo.",
        "सट्टा/जल्दबाज़ी जोखिम — आवेग में निर्णय न लें।",
      ),
      expense_drain_active: p(
        L,
        "Expense drain active — track subscriptions and leaks.",
        "Kharcha zyada — subscriptions aur leak check karo.",
        "खर्च अधिक — सब्सक्रिप्शन और रिसाव देखें।",
      ),
    } as Record<LeakageKey, string>,
    leakChannels: {
      subscriptions_small_spend: p(
        L,
        "Small recurring spends — track subscriptions and micro-payments monthly.",
        "Chhote repeat kharcha — subscriptions aur micro-payment monthly track karo.",
        "छोटे बार-बार खर्च — सब्सक्रिप्शन और छोटे भुगतान मासिक देखें।",
      ),
      emi_debt: p(
        L,
        "EMI / debt pressure — cap loans and service bills before new commitments.",
        "EMI / karz pressure — naye kharcha se pehle loan aur bills limit karo.",
        "ईएमआई / कर्ज दबाव — नई जिम्मेदारी से पहले ऋण और बिल सीमित करें।",
      ),
      medical_hospital: p(
        L,
        "Medical / hospital spend — keep a health buffer; don't skip insurance review.",
        "Medical / hospital kharcha — health buffer rakho; insurance review mat chhodo.",
        "चिकित्सा / अस्पताल खर्च — स्वास्थ्य फंड रखें; बीमा समीक्षा करें।",
      ),
      property_legal: p(
        L,
        "Property / legal / rent — double-check papers before big asset moves.",
        "Property / legal / rent — bade asset move se pehle papers dhyaan se dekho.",
        "संपत्ति / कानूनी / किराया — बड़े फैसले से पहले कागज़ जाँचें।",
      ),
      sudden_loss_tax: p(
        L,
        "Sudden loss / tax / inheritance — avoid rushed joint-money decisions.",
        "Achanak loss / tax / virasat — jaldi joint-money faisla mat lo.",
        "अचानक नुकसान / कर / विरासत — जल्दबाज़ी संयुक्त धन निर्णय न लें।",
      ),
      speculation_trading: p(
        L,
        "Speculation / trading / crypto — no impulsive bets; use a strict loss limit.",
        "Trading / crypto / satta — jaldi bet mat; strict loss limit rakho.",
        "सट्टा / ट्रेडिंग / क्रिप्टो — आवेग में दांव न लें; सीमा तय करें।",
      ),
      partnership_client_loss: p(
        L,
        "Partnership / client leakage — put client and partner payouts in writing.",
        "Partnership / client leak — partner aur client payment likhit rakho.",
        "साझेदारी / ग्राहक रिसाव — भुगतान लिखित करार में रखें।",
      ),
      family_shared_money: p(
        L,
        "Family / shared money — separate personal savings from family pool.",
        "Family / shared paisa — apni bachat family pool se alag rakho.",
        "परिवार / साझा धन — निजी बचत परिवार के पैसे से अलग रखें।",
      ),
      foreign_online_spend: p(
        L,
        "Foreign / online / hidden spend — watch cross-border and app-store charges.",
        "Foreign / online / chhupa kharcha — cross-border aur app charges dekho.",
        "विदेश / ऑनलाइन / छिपा खर्च — विदेशी और ऐप शुल्क पर नज़र रखें।",
      ),
      impulsive_fines: p(
        L,
        "Impulsive / fines / accidents — pause before big purchases; avoid rash driving.",
        "Impulsive / fine / accident — badi shopping se pehle ruko; rash driving avoid.",
        "आवेग / जुर्माना / दुर्घटना — बड़ी खरीद से पहले रुकें; लापरवाही न करें।",
      ),
      savings_dont_stick: p(
        L,
        "Savings don't stick — auto-transfer to a separate account on payday.",
        "Bachat tikti nahi — salary aate hi alag account me auto-transfer.",
        "बचत नहीं टिकती — वेतन आते ही अलग खाते में स्वतः स्थानांतरण करें।",
      ),
      income_not_retained: p(
        L,
        "Income comes but doesn't stay — track inflow vs outflow every month.",
        "Income aata hai, bachta nahi — har mahine inflow vs outflow track karo.",
        "आय आती है, टिकती नहीं — हर महीने आमदनी बनाम खर्च देखें।",
      ),
      kp_savings_leak: p(
        L,
        "Savings may drain — guard accumulated wealth and review recurring commitments.",
        "Bachat slip ho sakti hai — jama paisa bachao aur repeat commitments review karo.",
        "बचत रिस सकती है — संचित धन सुरक्षित रखें और बार-बार की प्रतिबद्धता देखें।",
      ),
      kp_income_leak: p(
        L,
        "Income may slip — tighten payouts and review where gains go each month.",
        "Kamai slip ho sakti hai — payouts tight karo aur har mahine dekho paisa kahan ja raha hai.",
        "आय फिसल सकती है — खर्च कम करें और हर महीने देखें लाभ कहाँ जा रहा है।",
      ),
    } as Record<LeakChannelKey, string>,
    tierLabels: {
      middle_class: p(L, "Stable", "Stable", "स्थिर"),
      rich: p(L, "Rich", "Rich", "धनी"),
      ultra_rich: p(L, "Ultra Rich", "Ultra Rich", "अल्ट्रा धनी"),
      millionaire: p(L, "Millionaire Potential", "Crorepati potential", "करोड़पति संभावना"),
    } as Record<WealthTierKey, string>,
    tierSubtitle: p(
      L,
      "Highlighted tier = your current MD/AD wealth window. Birth chart score shown below.",
      "Jo tier highlight hai = abhi ki MD/AD wealth window. Neeche janam chart score.",
      "हाइलाइट स्तर = वर्तमान MD/AD धन खिड़की। नीचे जन्म कुंडली स्कोर।",
    ),
    tierCurrentDashaLine: (md: string, ad: string, score: number, label: string) =>
      p(
        L,
        `Current dasha ${md}${ad ? ` / ${ad}` : ""} · ${score} → ${label}`,
        `Abhi ${md}${ad ? ` / ${ad}` : ""} · ${score} → ${label}`,
        `अभी ${md}${ad ? ` / ${ad}` : ""} · ${score} → ${label}`,
      ),
    tierBirthLine: (score: number, label: string) =>
      p(
        L,
        `Birth Wealth Builder · ${score} → ${label}`,
        `Janam Wealth Builder · ${score} → ${label}`,
        `जन्म वेल्थ बिल्डर · ${score} → ${label}`,
      ),
    disclaimer: p(
      L,
      "Chart guidance only — not investment, tax or legal advice.",
      "Sirf chart guidance — investment/tax advice nahi.",
      "केवल कुंडली मार्गदर्शन — निवेश/कर सलाह नहीं।",
    ),
    habitsTitle: p(L, "Money Habits For You", "Aapke liye money habits", "आपके लिए धन आदतें"),
    noActiveYog: p(
      L,
      "Yogas are present but not strongly active in current dasha — steady effort phase.",
      "Yog hain par abhi dasha me zyada active nahi — steady phase.",
      "योग हैं पर अभी दशा में कम सक्रिय — स्थिर प्रयास चरण।",
    ),
  };
}
