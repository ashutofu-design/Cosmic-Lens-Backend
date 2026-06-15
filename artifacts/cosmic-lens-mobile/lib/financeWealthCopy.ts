import { coerceUILang, type UILang } from "@/lib/i18n";
import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";

function p(lang: UILang, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export type WealthTierKey = "middle_class" | "rich" | "ultra_rich" | "millionaire";
export type LiquidityKey = "high" | "moderate" | "restricted";
export type LeakageKey =
  | "property_legal_loss_risk"
  | "speculation_trading_fraud_risk"
  | "expense_drain_active";

export function financeWealthCopy(lang: UILang) {
  const L = coerceUILang(lang);
  return {
    yogTitle: p(L, "Wealth Yogas", "Wealth yogas", "धन योग"),
    yogSub: p(
      L,
      "Prosperity combinations in your chart and how active they are now.",
      "Chart ke dhana yog aur ab kitne active hain.",
      "कुंडली के धन योग और अभी कितने सक्रिय हैं।",
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
    sourceTitle: p(L, "Money Will Come From", "Paisa kahan se aayega", "धन कहाँ से आएगा"),
    leakageTitle: p(L, "Wealth Leak Alerts", "Paisa leak alerts", "धन रिसाव अलर्ट"),
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
    tierLabels: {
      middle_class: p(L, "Average", "Average", "औसत"),
      rich: p(L, "Rich", "Rich", "धनी"),
      ultra_rich: p(L, "Ultra Rich", "Ultra rich", "अति धनी"),
      millionaire: p(L, "Millionaire Potential", "Crorepati potential", "करोड़पति संभावना"),
    } as Record<WealthTierKey, string>,
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
