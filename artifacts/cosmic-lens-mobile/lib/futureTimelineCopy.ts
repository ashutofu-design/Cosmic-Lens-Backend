import { pName, type ProInsight, type Trend } from "./proInsightEngine";

type Lang = "en" | "hn" | "hi";

const PLANET_EMOJI: Record<string, string> = {
  Sun: "☀️", Moon: "🌙", Mars: "🔥", Mercury: "💬",
  Jupiter: "🪷", Venus: "💗", Saturn: "⏳", Rahu: "🌀", Ketu: "🔮",
};

const PLANET_THEME: Record<string, Record<Lang, string>> = {
  Sun:     { en: "authority, visibility, and self-confidence", hn: "authority, visibility aur self-confidence", hi: "अधिकार, पहचान और आत्मविश्वास" },
  Moon:    { en: "emotions, family, and inner peace", hn: "emotions, parivaar aur inner peace", hi: "भावनाएं, परिवार और मानसिक शांति" },
  Mars:    { en: "courage, action, and competition", hn: "himmat, action aur competition", hi: "साहस, कार्य और प्रतिस्पर्धा" },
  Mercury: { en: "communication, learning, and business deals", hn: "communication, learning aur deals", hi: "संवाद, सीख और व्यापारिक फैसले" },
  Jupiter: { en: "growth, wisdom, and good fortune", hn: "growth, wisdom aur achha luck", hi: "विकास, ज्ञान और सौभाग्य" },
  Venus:   { en: "love, comfort, and creative expression", hn: "pyaar, comfort aur creativity", hi: "प्रेम, सुख और रचनात्मकता" },
  Saturn:  { en: "discipline, hard work, and long-term results", hn: "discipline, mehnat aur lambe results", hi: "अनुशासन, परिश्रम और दीर्घकालिक परिणाम" },
  Rahu:    { en: "ambition, change, and unconventional paths", hn: "ambition, change aur naye raaste", hi: "महत्वाकांक्षा, बदलाव और अनोखे रास्ते" },
  Ketu:    { en: "detachment, spirituality, and inner clarity", hn: "detachment, spirituality aur clarity", hi: "वैराग्य, आध्यात्म और आंतरिक स्पष्टता" },
};

const PD_FOCUS: Record<string, Record<Lang, string>> = {
  Sun:     { en: "Lead from the front — visibility matters now.", hn: "Aage badho — aajkal visibility matter karti hai.", hi: "आगे बढ़ें — अभी दिखाई देना जरूरी है।" },
  Moon:    { en: "Protect your peace — home and emotions need care.", hn: "Apni peace bachao — ghar aur emotions par dhyan do.", hi: "अपनी शांति बचाएं — घर और भावनाओं पर ध्यान दें।" },
  Mars:    { en: "Act fast but avoid unnecessary fights.", hn: "Jaldi action lo par bekaar ladaai se bacho.", hi: "जल्दी कार्रवाई करें, पर अनावश्यक झगड़े से बचें।" },
  Mercury: { en: "Talk, negotiate, and learn — smart moves win.", hn: "Baat karo, negotiate karo — smart moves kaam aayenge.", hi: "बात करें, सीखें — समझदारी से फायदा होगा।" },
  Jupiter: { en: "Say yes to growth — mentors and learning help.", hn: "Growth ke opportunities haan bolo — guru/mentor se fayda.", hi: "विकास के अवसरों को हाँ कहें — गुरु/सीख से लाभ।" },
  Venus:   { en: "Relationships and aesthetics get extra power.", hn: "Rishte aur comfort par extra focus — achha time hai.", hi: "रिश्तों और सुख-सुविधा पर विशेष ध्यान — अच्छा समय।" },
  Saturn:  { en: "Slow and steady — shortcuts won't work now.", hn: "Dheere-dheere par pakka — shortcut ab kaam nahi karenge.", hi: "धीरे-धीरे पर मजबूती से — शॉर्टकट अभी काम नहीं करेंगे।" },
  Rahu:    { en: "Big dreams possible — stay grounded while chasing them.", hn: "Bade sapne possible hain — grounded rehkar chase karo.", hi: "बड़े सपने संभव — जमीन पर रहकर उन्हें पूरा करें।" },
  Ketu:    { en: "Let go of what drains you — simplify.", hn: "Jo drain karta hai chhodo — life simplify karo.", hi: "जो थकाता है छोड़ें — जीवन सरल बनाएं।" },
};

function L(lang: string): Lang {
  if (lang === "hi") return "hi";
  if (lang === "hn") return "hn";
  return "en";
}

function trendWord(trend: Trend, lang: Lang): string {
  if (lang === "hi") {
    if (trend === "UP") return "अनुकूल";
    if (trend === "DOWN") return "सावधान";
    return "मिश्रित";
  }
  if (lang === "hn") {
    if (trend === "UP") return "Accha phase";
    if (trend === "DOWN") return "Sambhal kar";
    return "Mixed phase";
  }
  if (trend === "UP") return "Supportive";
  if (trend === "DOWN") return "Needs caution";
  return "Mixed";
}

function domainDetail(
  area: "career" | "relationship" | "finance",
  trend: Trend,
  score: number,
  lang: Lang,
): string {
  const s = score >= 65 ? "high" : score <= 40 ? "low" : "mid";
  const lines: Record<typeof area, Record<Lang, Record<typeof s | "default", string>>> = {
    career: {
      en: {
        high: "Work momentum is strong — pitch ideas, ask for growth, or close pending deals.",
        mid: "Steady progress is possible — avoid rash job switches; build skills instead.",
        low: "Office friction or delays likely — don't quit impulsively; document your work.",
        default: "Career moves need patience this phase.",
      },
      hn: {
        high: "Kaam me momentum accha hai — naye ideas pitch karo ya pending deals close karo.",
        mid: "Steady progress ho sakta hai — jaldi job switch mat karo; skills build karo.",
        low: "Office me delay ya friction ho sakta hai — gusse me resign mat karo.",
        default: "Career me patience zaroori hai.",
      },
      hi: {
        high: "कार्य में गति अच्छी है — नए विचार रखें या लंबित काम पूरे करें।",
        mid: "धीरे-धीरे प्रगति संभव — जल्दबाजी में नौकरी न बदलें; कौशल बढ़ाएं।",
        low: "कार्यस्थल में देरी या तनाव संभव — गुस्से में इस्तीफा न दें।",
        default: "करियर में धैर्य जरूरी है।",
      },
    },
    relationship: {
      en: {
        high: "Warmth in bonds — good time to express feelings or plan together.",
        mid: "Mixed signals possible — listen more, react less in arguments.",
        low: "Emotional distance or misunderstandings — avoid ultimatums; give space.",
        default: "Relationships need gentle handling now.",
      },
      hn: {
        high: "Rishton me warmth hai — feelings express karo ya saath me plan banao.",
        mid: "Mixed signals ho sakte hain — zyada suno, jhagda me kam react karo.",
        low: "Misunderstanding ya distance — ultimatum mat do; space do.",
        default: "Rishton me naram approach rakho.",
      },
      hi: {
        high: "रिश्तों में गर्माहट — भावना व्यक्त करें या साथ मिलकर योजना बनाएं।",
        mid: "मिश्रित संकेत संभव — ज्यादा सुनें, झगड़े में कम प्रतिक्रिया दें।",
        low: "गलतफहमी या दूरी — अल्टीमेटम न दें; स्थान दें।",
        default: "रिश्तों में कोमल रवैया रखें।",
      },
    },
    finance: {
      en: {
        high: "Money flow can improve — invest wisely, don't overspend on impulse.",
        mid: "Stable but not explosive — budget carefully; avoid risky bets.",
        low: "Expenses or delays possible — postpone big purchases; save buffer.",
        default: "Finances need a cautious plan.",
      },
      hn: {
        high: "Paisa flow improve ho sakta hai — smart invest karo, impulse spend mat karo.",
        mid: "Stable hai par jackpot nahi — budget tight rakho; risky bet avoid.",
        low: "Kharcha ya delay ho sakta hai — badi shopping postpone karo; saving badhao.",
        default: "Paisa ke faisle carefully lo.",
      },
      hi: {
        high: "धन प्रवाह बेहतर हो सकता है — समझदारी से निवेश; आवेग में खर्च न करें।",
        mid: "स्थिर पर धमाकedaar नहीं — बजट सख्त रखें; जोखिम टालें।",
        low: "खर्च या देरी संभव — बड़ी खरीद टालें; बचत बढ़ाएं।",
        default: "वित्त के फैसले सावधानी से लें।",
      },
    },
  };
  const bucket = s as "high" | "mid" | "low";
  return lines[area][lang][bucket] ?? lines[area][lang].default;
}

function buildFocusTips(insight: ProInsight, lang: Lang): string[] {
  const tips: string[] = [];
  const pdTip = PD_FOCUS[insight.pdPlanet]?.[lang];
  if (pdTip) tips.push(pdTip);

  const areas = [
    { key: "career" as const, label: lang === "hi" ? "करियर" : lang === "hn" ? "Career" : "Career" },
    { key: "relationship" as const, label: lang === "hi" ? "रिश्ते" : lang === "hn" ? "Rishte" : "Love" },
    { key: "finance" as const, label: lang === "hi" ? "धन" : lang === "hn" ? "Paisa" : "Money" },
  ];

  const best = areas.reduce((a, b) =>
    insight[a.key].score >= insight[b.key].score ? a : b,
  );
  const weak = areas.reduce((a, b) =>
    insight[a.key].score <= insight[b.key].score ? a : b,
  );

  if (best.key !== weak.key) {
    if (lang === "hi") {
      tips.push(`${best.label} में energy अच्छी है — यहाँ proactive रहें।`);
      tips.push(`${weak.label} में सावधानी रखें — बड़े फैसले टालें।`);
    } else if (lang === "hn") {
      tips.push(`${best.label} me energy acchi hai — yahan proactive raho.`);
      tips.push(`${weak.label} me sambhal kar — bade decisions thoda delay karo.`);
    } else {
      tips.push(`Energy is strongest in ${best.label} — be proactive there.`);
      tips.push(`Go slower in ${weak.label} — delay major decisions if you can.`);
    }
  } else {
    if (lang === "hi") tips.push("सभी क्षेत्रों में संतुलन रखें — एक समय में एक बड़ा बदलाव करें।");
    else if (lang === "hn") tips.push("Sab areas me balance rakho — ek time par ek bada change karo.");
    else tips.push("Keep balance across areas — one big change at a time.");
  }

  if (lang === "hi") tips.push("नियमित दिनचर्या और ईमानदार मेहनत इस phase में सबसे ज्यादा काम आएगी।");
  else if (lang === "hn") tips.push("Regular routine aur honest mehnat is phase me sabse zyada kaam aayegi.");
  else tips.push("Consistent routine and honest effort pay off most in this phase.");

  return tips.slice(0, 3);
}

export function planetEmoji(planet: string): string {
  return PLANET_EMOJI[planet] ?? "🪐";
}

export function buildPeriodMeaning(insight: ProInsight, lang: string): string {
  const l = L(lang);
  const md = pName(insight.mdPlanet);
  const ad = pName(insight.adPlanet);
  const mdTheme = PLANET_THEME[insight.mdPlanet]?.[l] ?? PLANET_THEME.Jupiter[l];
  const adTheme = PLANET_THEME[insight.adPlanet]?.[l] ?? PLANET_THEME.Saturn[l];

  if (l === "hi") {
    return `${md} महादशा का बड़ा थीम ${mdTheme} पर केंद्रित है। इसके अंदर ${ad} अंतर्दशा ${adTheme} को हल्का या गहरा कर रही है — यही आपके अगले महीनों की direction तय करेगा।`;
  }
  if (l === "hn") {
    return `${md} Mahadasha ka bada theme ${mdTheme} par focused hai. Iske andar ${ad} Antardasha ${adTheme} ko highlight kar rahi hai — yahi aapke agle mahino ki direction decide karegi.`;
  }
  return `Your ${md} Mahadasha centres on ${mdTheme}. Inside it, ${ad} Antardasha highlights ${adTheme} — that mix shapes your direction for the coming months.`;
}

export function buildMainInsight(insight: ProInsight, lang: string): string {
  const l = L(lang);
  const md = pName(insight.mdPlanet);
  const ad = pName(insight.adPlanet);
  const pd = pName(insight.pdPlanet);
  const c = trendWord(insight.career.trend, l);
  const r = trendWord(insight.relationship.trend, l);
  const f = trendWord(insight.finance.trend, l);

  if (l === "hi") {
    return `अभी ${md} · ${ad} · ${pd} प्रत्यंतर दशा चल रही है। करियर ${c}, रिश्ते ${r}, धन ${f} दिख रहा है। यह समय जल्दबाजी से बचकर, लगातार प्रयास पर भरोसा करने का है।`;
  }
  if (l === "hn") {
    return `Abhi ${md} · ${ad} · ${pd} Pratyantar Dasha chal rahi hai. Career ${c}, rishte ${r}, paison me ${f} phase hai. Jaldi faisle kam, steady effort zyada — isi se result aayega.`;
  }
  return `You're running ${md} · ${ad} · ${pd} Pratyantar Dasha. Career feels ${c.toLowerCase()}, love ${r.toLowerCase()}, money ${f.toLowerCase()}. Skip rushed calls — steady effort wins here.`;
}

export function buildAreaRows(insight: ProInsight, lang: string) {
  const l = L(lang);
  return [
    {
      icon: "💼",
      label: l === "hi" ? "करियर" : l === "hn" ? "Career" : "Career",
      trend: insight.career.trend,
      score: insight.career.score,
      text: domainDetail("career", insight.career.trend, insight.career.score, l),
    },
    {
      icon: "💞",
      label: l === "hi" ? "रिश्ते" : l === "hn" ? "Rishte" : "Love",
      trend: insight.relationship.trend,
      score: insight.relationship.score,
      text: domainDetail("relationship", insight.relationship.trend, insight.relationship.score, l),
    },
    {
      icon: "💰",
      label: l === "hi" ? "धन" : l === "hn" ? "Paisa" : "Money",
      trend: insight.finance.trend,
      score: insight.finance.score,
      text: domainDetail("finance", insight.finance.trend, insight.finance.score, l),
    },
  ];
}

export function buildFocusList(insight: ProInsight, lang: string): string[] {
  return buildFocusTips(insight, L(lang));
}

export function buildPdSummary(insight: ProInsight, lang: string): string {
  const l = L(lang);
  const pd = pName(insight.pdPlanet);
  const theme = PLANET_THEME[insight.pdPlanet]?.[l] ?? "";
  if (l === "hi") return `${pd} प्रत्यंतर दशा — ${theme} पर छोटे-छोटे फैसले तेजी से प्रभावित होते हैं।`;
  if (l === "hn") return `${pd} Pratyantar Dasha — ${theme} par chhote decisions jaldi impact karte hain.`;
  return `${pd} Pratyantar Dasha — small decisions around ${theme} move quickly now.`;
}

export function trendLabel(trend: Trend, lang: string): string {
  return trendWord(trend, L(lang));
}
