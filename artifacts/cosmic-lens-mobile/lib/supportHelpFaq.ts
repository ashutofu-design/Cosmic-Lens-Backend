/** Cosmic Help answers when the API has not posted a bot reply yet. */

function isHinglish(text: string): boolean {
  return /\b(kya|hai|hain|nahi|kaise|kahan|meri|mera|mujhe|kitna|kitne|paise|karun|chahiye|abhi)\b/i.test(
    text,
  );
}

function isEnglish(text: string): boolean {
  const letters = (text.match(/[A-Za-z]/g) || []).length;
  return letters >= 8 && !isHinglish(text) && !/[\u0900-\u097F]/.test(text);
}

function polite(body: string, hinglish: boolean): string {
  const t = body.trim();
  if (/^(ji[, ]|happy to help)/i.test(t)) return t;
  return hinglish ? `Ji, ${t}` : `Happy to help. ${t}`;
}

function normalizeCosmo(raw?: string): string {
  const s = (raw || "").trim().toUpperCase();
  if (!s) return "";
  if (s.startsWith("COSMO")) return s;
  if (/^\d+$/.test(s)) return `COSMO${s}`;
  return s;
}

type FaqRule = { test: RegExp; hn: string; en: string };

const FAQ_RULES: FaqRule[] = [
  {
    test: /(report|pdf).{0,80}\bai\b|\bai\b.{0,80}(report|pdf)|r[ea]+lationship|relatonship|love realit|couple (pdf|report)|breakup|loyalty|will return|future outcome|love compat/i,
    hn: "Love Reality / Milan / Numerology Pro PDF expert khud likhte hain pay ke baad — instant AI PDF nahi. Love Reality: Life Map → Relationship. Basic free. Pro ₹499, My Reports 24h/12h.",
    en: "Love Reality, Kundli Milan, and Numerology Pro PDFs are written by our expert after you pay — not instant AI PDFs. Love Reality: Life Map → Relationship. Basic is free. Pro is ₹499 in My Reports (24h / 12h).",
  },
  {
    test: /numerolog|numerlog|numarolog|life mastery|life path/i,
    hn: "Life Map → Explore → Numerology. Basic free numbers screen pe. Pro PDF expert likhte hain — instant AI nahi. ₹299, priority +₹100 (12h). My Reports mein aati hai.",
    en: "Life Map → Explore → Numerology. Basic = free numbers on screen. Pro PDF is expert-written, not instant AI. ₹299 (priority +₹100, 12h) in My Reports.",
  },
  {
    test: /milan|guna|ashtakoot|gun milan|36 gun|marriage compat/i,
    hn: "Life Map → Relationship → Kundli Milan. Basic 36-guna free. Pro PDF expert likhte hain — instant AI nahi. ₹699 (priority +₹300), My Reports 24h/12h.",
    en: "Life Map → Relationship → Kundli Milan. Basic 36-guna is free. Pro PDF is expert-written, not instant AI. ₹699 (priority +₹300) in My Reports (24h / 12h).",
  },
  {
    test: /business vastu|shop vastu|office vastu|factory vastu|dukaan|karkhana/i,
    hn: "Business Vastu: Shop ₹999, Office ₹1499, Factory ₹2999. Room photo ₹399/₹499/₹999. Full PDF ₹2999/₹6999/₹14999. Report My Reports mein.",
    en: "Business Vastu: Shop ₹999, Office ₹1499, Factory ₹2999. Room photos ₹399 / ₹499 / ₹999. Full plan PDFs ₹2999 / ₹6999 / ₹14999 in My Reports.",
  },
  {
    test: /vastu|astrovastu|floor plan|compass/i,
    hn: "Life Map → Explore → AstroVastu. Free compass Vastu pe. Home: 1 room ₹199, 3 rooms ₹499, expert photo ₹199, floor PDF ₹999, lifetime ₹2999. PDF My Reports mein.",
    en: "Life Map → Explore → AstroVastu. Free compass on Vastu. Home: 1 room ₹199, 3 rooms ₹499, expert photo ₹199/room, floor-plan PDF ₹999, lifetime ₹2999. PDFs in My Reports.",
  },
  {
    test: /\bcareer\b|naukri|job vs business/i,
    hn: "Life Map → Career. Free score screen pe. Deep Career Pro plan ₹499/month se. Yeh expert PDF nahi hai.",
    en: "Life Map → Career. Free on-screen score. Deeper Career is Pro plan ₹499/month. Not an expert PDF.",
  },
  {
    test: /\bhealth\b|tridosha|vata|pitta|kapha|sehat/i,
    hn: "Life Map → Health. Free score/tridosha screen pe. Full health Pro plan ₹499/month se.",
    en: "Life Map → Health. Free on-screen score and tridosha. Full detail is Pro plan ₹499/month.",
  },
  {
    test: /\bfinance\b|wealth score|money habit|dhan/i,
    hn: "Life Map → Finance. Free wealth score screen pe. Deep finance Pro plan ₹499/month se.",
    en: "Life Map → Finance. Free wealth score on screen. Deeper money detail is Pro plan ₹499/month.",
  },
  {
    test: /today.?s? energy|7[\s-]*day|forecast|dosh|risk radar|manglik|kaal sarp|home tab/i,
    hn: "Home tab free hai: Today’s Energy, 7-day Forecast, Dosh, Risk Radar. Demo dikhe to Profile pe birth details daalo.",
    en: "Home is free: Today’s Energy, 7-day Forecast, Dosh, Risk Radar. Add birth details in Profile if you see a demo.",
  },
  {
    test: /future tab|insights|mahadasha|antardasha|timeline/i,
    hn: "Future tab pe dasha timeline screen pe dikhta hai (kundli chahiye). Yeh PDF nahi. Sawaal Ask tab pe.",
    en: "Future tab shows your dasha timeline on screen (needs kundli). Not a PDF. Chart questions go on Ask.",
  },
  {
    test: /\bv3\b|live (chat|astro|guide)|talk to astro|cosmic guide/i,
    hn: "V3 Live Ask tab pe timed Cosmic Guide chat hai — 15 min ₹399, 30 ₹699, 45 ₹999, 60 ₹1299. Yeh Help chat V3 nahi hai.",
    en: "V3 Live is a timed Cosmic Guide chat on the Ask tab from ₹399. This Help chat is not V3. Transcripts go to My Reports.",
  },
  {
    test: /ask (pack|question|quota|tab)|cosmic pack|free question|\bv1\b|cosmic intelligence/i,
    hn: "Ask tab pe V1 chart Q&A. Signup pe 3 free questions. Packs ₹49/₹99/₹299 — Profile → Cosmic Packs. Kundli sawaal Ask pe.",
    en: "Ask tab = V1 chart Q&A. 3 free questions at signup. Packs ₹49 / ₹99 / ₹299 under Profile → Cosmic Packs. Chart questions go on Ask.",
  },
  {
    test: /rectif|birth time|janm samay|precision birth/i,
    hn: "Birth Time Rectification Ask tab pe hai (Profile → edit se bhi). Life events bharo, aaj ₹999 (pehle ₹2999).",
    en: "Birth Time Rectification is on Ask (also from Profile → edit). Fill life events, then ₹999 today (was ₹2999).",
  },
  {
    test: /divya prashna|prashna|horary/i,
    hn: "Divya Prashna Ask tab pe chhota link hai — on-screen jawab. Kundli sawaal Ask V1 pe poochho.",
    en: "Divya Prashna is a small Ask-tab link for an on-screen prashna. Full chart Q&A is Ask V1.",
  },
  {
    test: /balance|wallet|kitna.*account|account.*kitna|mere account/i,
    hn: "App mein wallet nahi hota. Paid orders Help → Transactions pe. Ask questions Profile → Cosmic Packs se.",
    en: "There is no wallet. Paid orders are on Help → Transactions. Ask credits are under Profile → Cosmic Packs.",
  },
  {
    test: /\bprices?\b|kitna.*price|pro ke price|price list|kitne ke/i,
    hn: "Numerology Pro ₹299. Love Reality Pro ₹499. Milan Pro ₹699. V3 ₹399 se. Ask packs ₹49/₹99/₹299. Vastu 1 room ₹199. Birth Time ₹999. Plans: Trial ₹1, Basic ₹199/mo, Pro ₹499/mo.",
    en: "Numerology Pro ₹299. Love Reality Pro ₹499. Milan Pro ₹699. V3 from ₹399. Ask packs ₹49/₹99/₹299. Vastu 1 room ₹199. Birth Time ₹999. Plans: Trial ₹1, Basic ₹199/mo, Pro ₹499/mo.",
  },
  {
    test: /pdf|my reports?|report kahan|where.*report/i,
    hn: "My Reports More se kholo. Paid expert PDF usually 24h (priority 12h). Ask/V3 chats Talked mein. Payment Help → Transactions pe.",
    en: "Open My Reports from More. Paid expert PDFs usually arrive within 24h (priority 12h). Ask/V3 chats are under Talked.",
  },
  {
    test: /payment|transaction|razorpay|cashfree|upi|gst|order id/i,
    hn: "Help → Transactions pe paid orders dikhte hain. Wallet nahi. Sheet band ho to dobara Pay. Paise kat gaye aur order nahi hai to team join karegi.",
    en: "Open Help → Transactions for paid orders. No wallet. If the sheet closed, tap Pay again. If money was cut and the order is missing, a team member will join.",
  },
  {
    test: /family|partner profile|add (husband|wife|boyfriend|girlfriend)|doosri kundli/i,
    hn: "Profile → edit pe family/partner kundli add karo. Love Reality aur Milan ke liye dono ki birth details chahiye.",
    en: "Profile → edit → add a family or partner profile. Love Reality and Kundli Milan need both people’s birth details.",
  },
  {
    test: /birth|dob|kundli edit|janm/i,
    hn: "Profile → edit pe name, DOB, time, place change karo. Time sure na ho to Ask pe Birth Time Rectification (₹999).",
    en: "Profile → edit to change name, DOB, time, and place. Unsure of birth time? Ask → Birth Time Rectification (₹999).",
  },
  {
    test: /login|otp|google sign|sign in|logout|log out/i,
    hn: "Login screen pe Continue with Google. Atki ho to Profile → Logout karke dubara sign in.",
    en: "Continue with Google on the login screen. If stuck, Profile → Logout, then sign in again.",
  },
  {
    test: /app (nahi|not|hang|crash|slow|open)|force close|update app|internet/i,
    hn: "App update karo, internet check karo, force-close karke kholo, phir login.",
    en: "Update Cosmic Lens, check internet, force-close the app and reopen, then sign in again.",
  },
  {
    test: /language|hindi|hinglish|bhasha/i,
    hn: "Profile → language: English, Hinglish, ya Hindi. Ask chat ki language alag pick hoti hai.",
    en: "Profile → language: English, Hinglish, or Hindi. Ask chat language is picked separately.",
  },
  {
    test: /refer|referral|\bearn\b|invite/i,
    hn: "Profile → Refer & Earn. Code CL + aapka number. Friend V1/V3 pack kharide to 3 extra Ask questions.",
    en: "Profile → Refer & Earn. Code is CL plus your number. Friend buys a V1/V3 pack → you get 3 extra Ask questions.",
  },
  {
    test: /subscription|pro plan|basic plan|trial|\bplans?\b|upgrade/i,
    hn: "Plans Career/Health/Finance upgrade se: Trial ₹1 / 7 din, Basic ₹199/month, Pro ₹499/month. Love Reality aur Milan Basic free rehte hain.",
    en: "Plans: Trial ₹1 / 7 days, Basic ₹199/month, Pro ₹499/month. Love Reality and Kundli Milan Basic stay free.",
  },
  {
    test: /face read|chehra|mukh/i,
    hn: "Face Reading Life Map → Explore pe hai. Pro abhi live nahi — soon aayega.",
    en: "Face Reading is on Life Map → Explore. Pro photo reading is coming soon — not live yet.",
  },
  {
    test: /notif|push|alert nahi/i,
    hn: "Phone Settings → Cosmic Lens → notifications on karo. Report ready push My Reports kholta hai.",
    en: "Phone Settings → Cosmic Lens → allow notifications. Report-ready push opens My Reports.",
  },
  {
    test: /panchang|muhurat|vrat|vivah|naam jaap|jaap/i,
    hn: "More → Panchang & Muhurat: Aaj, Muhurat, Vrat, Vivah, Naam Jaap.",
    en: "More → Panchang & Muhurat: Aaj, Muhurat, Vrat, Vivah, Naam Jaap.",
  },
  {
    test: /planet position|varga|divisional|gochar|ashtak|\bkp\b/i,
    hn: "More → Planet Position free hai: D1, varga, KP, ashtak, transit.",
    en: "More → Planet Position (free): D1, divisional, KP, ashtak, transit.",
  },
  {
    test: /gemstone|pukhraj|ratna|emerald|sapphire/i,
    hn: "More → Gemstones pe chart hint, kharidari WhatsApp pe certified stones. Pukhraj 5 ratti roughly ₹45,999 se.",
    en: "More → Gemstones shows a chart hint, then WhatsApp for certified stones. Pukhraj 5 ratti starts around ₹45,999.",
  },
  {
    test: /download|share pdf|pdf save|whatsapp share/i,
    hn: "More → My Reports → PDF kholo → download/WhatsApp share. List khali ho to 24h wait ho sakta hai.",
    en: "More → My Reports → open the PDF → download or WhatsApp share. Empty list usually means still in the 24h window.",
  },
  {
    test: /delete account|account delete|account hatao/i,
    hn: "Profile → About → Delete account, DELETE type karke confirm. Refund ke liye team join karegi.",
    en: "Profile → About → Delete account and type DELETE. For a refund first, a team member will join.",
  },
  {
    test: /talk to founder|founder|instagram|youtube/i,
    hn: "Talk to Founder More menu pe hai — Instagram / YouTube / WhatsApp (free). Paid live Ask → V3.",
    en: "Talk to Founder is under More (Instagram / YouTube / WhatsApp, free). Paid live astrology is Ask → V3 Live.",
  },
  {
    test: /whatsapp/i,
    hn: "WhatsApp More → Talk to Founder, Gemstones, aur My Reports PDF share ke liye hai.",
    en: "WhatsApp is used from More → Talk to Founder, Gemstones, and sharing a PDF from My Reports.",
  },
  {
    test: /lucky|shubh (ank|rang)|lucky (colour|color|number)/i,
    hn: "Lucky colour/number Home → Risk Radar pe (kundli chahiye). Demo ho to Profile → edit.",
    en: "Lucky colour and number are on Home → Risk Radar after your kundli is saved.",
  },
  {
    test: /remed|upay|totka|mantra/i,
    hn: "Dosh remedies Home → Dosh Analysis pe. Gemstones More pe WhatsApp. Kundli sawaal Ask pe.",
    en: "Dosh remedies are on Home → Dosh Analysis. Gemstones: More → WhatsApp. Chart questions: Ask tab.",
  },
  {
    test: /personalization|snapshot|demo banner|create kundli|kundli nahi|no kundli/i,
    hn: "Home pe Demo dikhe to Profile → edit pe name, DOB, time, place save karo.",
    en: "If Home shows Demo, Profile → edit and save name, DOB, time, and place.",
  },
  {
    test: /dark mode|light mode|theme/i,
    hn: "Dark/light theme Home tab pe sun/moon toggle se badlo.",
    en: "Switch dark or light theme with the sun/moon toggle on Home.",
  },
  {
    test: /privacy|terms|disclaimer|about page|website|cosmiclens\.app/i,
    hn: "Profile → About pe Privacy, Terms, Refund, Disclaimer. Website: https://cosmiclens.app",
    en: "Profile → About has Privacy, Terms, Refund, Disclaimer. Website: https://cosmiclens.app",
  },
  {
    test: /cancel (plan|sub|membership)|unsubscribe/i,
    hn: "Plan Career/Health/Finance upgrade → Plans se cancel anytime. Na ho to team join karegi.",
    en: "Cancel anytime from Plans (Career/Health/Finance upgrade). If it fails, a team member will join.",
  },
  {
    test: /camera|permission|photo access/i,
    hn: "AstroVastu room photo ke liye camera allow karo. Birth place Profile → edit pe search se.",
    en: "Allow camera when AstroVastu asks to photograph a room. Birth place is Profile → edit search.",
  },
  {
    test: /payment history|invoice|gst bill/i,
    hn: "Paid orders Help → Transactions pe. GST invoice copy ke liye team join karegi.",
    en: "Paid orders are on Help → Transactions. For a GST invoice copy, a team member will join.",
  },
  {
    test: /partner portrait|future partner/i,
    hn: "Future Partner Portrait hata diya gaya. Life Map → Relationship use karo.",
    en: "Future Partner Portrait was removed. Use Life Map → Relationship instead.",
  },
  {
    test: /life map|explore|where is|kahan (hai|he)|feature|screen|tabs?|app (me|mein)|cosmic lens|kya kya|what can|how to use|kaise use/i,
    hn: "Tabs: Home, Life Map, Ask, Future, More. Life Map pe Relationship, Career, Health, Finance, Explore. PDF: My Reports. Orders: Help → Transactions. Kundli sawaal: Ask. Kaunsa screen chahiye?",
    en: "Tabs: Home, Life Map, Ask, Future, plus More. Life Map has Relationship, Career, Health, Finance, Explore. PDFs: My Reports. Orders: Help → Transactions. Chart questions: Ask. Which screen do you need?",
  },
];

export function localSupportAnswer(
  text: string,
  opts?: { priorUserTexts?: string[]; cosmoId?: string },
): string {
  const t = (text || "").trim();
  const hn = isHinglish(t) || (!isEnglish(t) && !/[A-Za-z]{8,}/.test(t));
  const low = t.toLowerCase();
  const cid = normalizeCosmo(opts?.cosmoId);
  const prior = opts?.priorUserTexts || [];
  const stuck =
    prior.length > 0 &&
    /samajh nahi|solve nahi|still not|not working|clear nahi|kuch nahi hua/.test(low);
  if (stuck) {
    return polite(
      hn
        ? "Yeh yahan clear nahi ho paaya. Customer support abhi is chat mein aayenge — thoda wait kariye, yahin reply aayega."
        : "I couldn’t fully resolve this here. Customer support will join this chat shortly — please wait.",
      hn,
    );
  }
  if (
    /source code|calculation code|system prompt|api[_ -]?key|\.env\b|admin panel|numerology engine|show me the code|flask_app|openai|other user|sab users|telegram|github/i.test(
      t,
    )
  ) {
    return polite(
      hn
        ? "Internal system details, code, ya private data share nahi kar sakte. Sirf Cosmic Lens app how-to: payments, My Reports, Profile."
        : "I can’t share internal system details, code, or private data. I only help with the Cosmic Lens app — payments, My Reports, Profile, and how-to.",
      hn,
    );
  }
  const appSignal =
    /cosmic|kundli|numerolog|numerlog|vastu|milan|love realit|cosmo|life map|report|pdf|transaction|payment|profile|login|ask|v3|pack|dosh|forecast|energy|career|health|finance|founder|wallet|refer|app\b|help/i.test(
      t,
    );
  if (
    !appSignal &&
    /weather|mausam|cricket|ipl|football|bitcoin|crypto|stock market|recipe|cooking|homework|prime minister|netflix|lottery|satta|covid|vaccine|capital of|who won/i.test(
      t,
    )
  ) {
    return polite(
      hn
        ? "Main sirf Cosmic Lens app pe help karta hoon — Home, Life Map, Ask, Future, My Reports, payments, Profile. App ke bahar ke sawaal nahi le sakta."
        : "I only help with the Cosmic Lens app — Home, Life Map, Ask, Future, My Reports, payments, and Profile. I can’t answer questions outside the app.",
      hn,
    );
  }
  const cosmoFollow =
    /cosmo|user\s*id|userid/.test(low) &&
    (prior.some((p) => /cosmo|user\s*id|userid/i.test(p)) ||
      /(dikha|dikh raha|showing|mera to|lekin|\bbut\b|\d{2,4})/.test(low));

  if (cosmoFollow) {
    return polite(
      hn
        ? cid
          ? `Haan, ${cid} hi aapka User ID hai. Jo number Profile pe dikh raha hai (jaise 109) wahi COSMO ke saath hota hai. Pehle wala COSMO110 sirf example tha. Change nahi hota.`
          : "Jo number Profile pe dikh raha hai wahi aapka User ID hai. COSMO aur number ek hi cheez hai — 109 matlab COSMO109. COSMO110 sirf example tha. Change nahi hota."
        : cid
          ? `Yes — ${cid} is your User ID. The number on Profile is the same ID. COSMO110 was only an example.`
          : "The number on Profile is your User ID. 109 means COSMO109. COSMO110 was only an example.",
      hn,
    );
  }
  if (/cosmo|user\s*id|userid/.test(low)) {
    return polite(
      hn
        ? cid
          ? `Aapka User ID Profile pe ${cid} hai. Signup pe milta hai, change nahi hota.`
          : "Aapka User ID Profile pe COSMO number hai — jaise COSMO109. Signup pe milta hai, change nahi hota."
        : cid
          ? `Your User ID on Profile is ${cid}. It is assigned at signup and cannot be changed.`
          : "Your User ID is the COSMO number on Profile (COSMO109…). It is assigned at signup and cannot be changed.",
      hn,
    );
  }

  for (const rule of FAQ_RULES) {
    if (rule.test.test(t)) {
      return polite(hn ? rule.hn : rule.en, hn);
    }
  }

  return polite(
    hn
      ? "Main Home, Life Map, Ask, Future, My Reports, payments, Profile pe help kar sakta hoon. Kaunsa screen ya payment batao."
      : "I can help with Home, Life Map, Ask, Future, My Reports, payments, and Profile. Tell me which screen or payment.",
    hn,
  );
}

export function ensureBotReply(
  msgs: Array<{
    id: string;
    sender: string;
    text?: string;
    ts: string;
    image_url?: string;
  }>,
  userText: string,
  serverReply?: string,
  cosmoId?: string,
): typeof msgs {
  const out: typeof msgs = [];
  for (let i = 0; i < msgs.length; i += 1) {
    const m = msgs[i];
    out.push(m);
    if (m.sender !== "user") continue;
    const next = msgs[i + 1];
    if (next && (next.sender === "bot" || next.sender === "admin")) continue;
    const isLatestUser = !msgs.slice(i + 1).some((x) => x.sender === "user");
    const priorUserTexts = msgs
      .slice(0, i)
      .filter((x) => x.sender === "user")
      .map((x) => x.text || "");
    const text =
      (isLatestUser && (serverReply || "").trim()) ||
      localSupportAnswer(m.text || userText, { priorUserTexts, cosmoId });
    if (!text.trim()) continue;
    out.push({
      id: `local-bot-${m.id}`,
      sender: "bot",
      text,
      ts: new Date().toISOString(),
    });
  }
  return out;
}
