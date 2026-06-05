// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — App-wide UI Translation (English, Hinglish, Hindi only)
// ══════════════════════════════════════════════════════════════════════════════

export type UILang = "en" | "hn" | "hi";

export const APP_LANG_CODES = ["en", "hn", "hi"] as const;
/** @deprecated use APP_LANG_CODES */
export const INDIA_LANG_CODES = APP_LANG_CODES;
/** @deprecated use APP_LANG_CODES */
export const GLOBAL_LANG_CODES = APP_LANG_CODES;

export interface Translations {
  tabHome: string; tabKundli: string; tabAsk: string;
  tabLifeMap: string; tabFuture: string; tabNotice: string; tabProfile: string;
  save: string; cancel: string; skip: string; back: string;
  next: string; done: string; retry: string; search: string;
  loading: string; close: string; confirm: string;
  delete: string; edit: string;
  logIn: string; createAccount: string;
  continueGuest: string; guestNote: string;
  emailAddr: string; password: string;
  yourName: string; loginSubtitle: string;
  birthDetails: string; birthSubtitle: string;
  dateOfBirth: string; timeOfBirth: string;
  birthPlace: string; gender: string;
  genderMale: string; genderFemale: string; genderOther: string;
  searchCity: string;
  generateKundli: string; generatingKundli: string;
  day: string; month: string; year: string;
  hour: string; minute: string; timeTip: string;
  todayEnergy: string; moonTransit: string;
  currentDasha: string; setupKundli: string; setupKundliSub: string;
  viewAll: string; viewDetails: string;
  forecast: string; today: string;
  natalChart: string; planets: string;
  dashaTimeline: string; nakshatra: string;
  ascendant: string; house: string;
  noKundli: string; noKundliSub: string;
  createKundli: string; chartType: string;
  settings: string; language: string; darkMode: string;
  myProfiles: string; subscription: string;
  addFamilyMember: string; addFamilySub: string;
  logOut: string; deleteAccount: string;
  freePlan: string; upgradeNow: string;
  selectLanguage: string; langSubtitle: string;
  langSearch: string; supported: string; comingSoon: string;
  askTitle: string; askPlaceholder: string;
  askSend: string; askSuggestions: string;
  lifeMapTitle: string; lifeMapSubtitle: string;
  lifeMapRelSub: string; lifeMapCarSub: string;
  lifeMapHealthSub: string; lifeMapFinSub: string;
  lifeMapComing: string; lifeMapComingSub: string;
  futureTitle: string; futureSubtitle: string;
  career: string; finance: string; relationship: string; health: string;
  noticeTitle: string; noNotices: string;
  errorGeneral: string; noInternet: string; tryAgain: string;
  prevDay: string; nextDay: string;
  unlockForecastTitle: string; unlockForecastSub: string; forecastError: string;
  chooseYourPlan: string; unlockVedicTitle: string;
  noResultFound: string; goBack: string;
  currentPlan: string; billingCycle: string;
  paymentGateway: string; securePayment: string; tryAgainBtn: string;
  monthly: string; yearly: string;
  settingEditProfile: string; profilesCount: string;
  settingSubscription: string; sectionSupport: string;
  settingAbout: string; settingHelp: string;
  settingRateUs: string; settingShareApp: string;
  sectionLegal: string; settingLegal: string;
  sectionDanger: string; settingDeleteAcc: string;
  logoutTitle: string; logoutConfirm: string; logoutCta: string;
  kundliRequired: string; kundliRequiredSub: string; futureDemoBanner: string;
  activeDashaPhase: string; phaseGood: string; phaseChallenging: string;
  phaseAverage: string; phaseSuffix: string; activeLabel: string;
  sadeSatiAlert: string; transitUnavailBanner: string;
  sixMonthTrend: string; transitUnavailShort: string;
  upcomingPD: string; whyThisScore: string;
  sixMonthAvg: string; basedOnNatal: string;
}

const T: Record<UILang, Translations> = {
  // ── ENGLISH (default) ───────────────────────────────────────────────────────
  en: {
    tabHome: "Home", tabKundli: "Kundli", tabAsk: "Ask",
    tabLifeMap: "Life Map", tabFuture: "Future", tabNotice: "Notice", tabProfile: "Profile",

    save: "Save", cancel: "Cancel", skip: "Skip", back: "Back",
    next: "Next", done: "Done", retry: "Retry", search: "Search",
    loading: "Loading...", close: "Close", confirm: "Confirm",
    delete: "Delete", edit: "Edit",

    logIn: "Log In", createAccount: "Create Account",
    continueGuest: "Continue without account",
    guestNote: "Your charts will be saved locally on this device only",
    emailAddr: "Email Address", password: "Password",
    yourName: "Your Name", loginSubtitle: "Your personal Vedic astrology guide",

    birthDetails: "Birth Details",
    birthSubtitle: "Accurate birth details are needed for a correct Kundli.",
    dateOfBirth: "Date of Birth", timeOfBirth: "Time of Birth",
    birthPlace: "Birth Place", gender: "Gender",
    genderMale: "Male", genderFemale: "Female", genderOther: "Other",
    searchCity: "Search city or village...",
    generateKundli: "Generate Kundli", generatingKundli: "Generating Kundli...",
    day: "Day", month: "Month", year: "Year",
    hour: "Hour", minute: "Minute",
    timeTip: "Birth time directly affects Mahadasha. Please verify AM or PM carefully.",

    todayEnergy: "Today's Cosmic Energy", moonTransit: "Moon Transit",
    currentDasha: "Current Dasha", setupKundli: "Set Up Your Kundli",
    setupKundliSub: "Enter your birth details to generate your Vedic chart",
    viewAll: "View All", viewDetails: "View Details",
    forecast: "Forecast", today: "Today",

    natalChart: "Natal Chart", planets: "Planets",
    dashaTimeline: "Dasha Timeline", nakshatra: "Nakshatra",
    ascendant: "Ascendant", house: "House",
    noKundli: "No Kundli Yet", noKundliSub: "Set up your birth chart to unlock all features",
    createKundli: "Create Kundli", chartType: "Chart Type",

    settings: "Settings", language: "Language", darkMode: "Dark Mode",
    myProfiles: "My Profiles", subscription: "Subscription",
    addFamilyMember: "Add Family Member",
    addFamilySub: "Son, Daughter, Spouse, Parents, Friend & more",
    logOut: "Log Out", deleteAccount: "Delete Account",
    freePlan: "Free Plan", upgradeNow: "Upgrade Now",
    selectLanguage: "Select Language", langSubtitle: "App language will change instantly",
    langSearch: "Search language...", supported: "Supported", comingSoon: "Coming Soon",

    askTitle: "Ask Jyotish", askPlaceholder: "Ask anything about your chart...",
    askSend: "Send", askSuggestions: "Try asking...",

    lifeMapTitle: "Life Map", lifeMapSubtitle: "Your life, mapped by the stars",
    lifeMapRelSub: "Love, compatibility & bonds", lifeMapCarSub: "Growth, success & purpose",
    lifeMapHealthSub: "Body, mind & vitality", lifeMapFinSub: "Wealth, stability & flow",
    lifeMapComing: "More dimensions coming", lifeMapComingSub: "Education, Travel, Spirituality & more",

    futureTitle: "Future Timeline", futureSubtitle: "Your next 6 months decoded",
    career: "Career", finance: "Finance", relationship: "Relationship", health: "Health",

    noticeTitle: "Notices", noNotices: "No notices yet",

    errorGeneral: "Something went wrong. Please try again.",
    noInternet: "No internet connection.", tryAgain: "Try Again",
    prevDay: "Previous Day",
    nextDay: "Next Day",
    unlockForecastTitle: "Unlock Personalized Forecast",
    unlockForecastSub: "Get a daily energy score based on your Kundli",
    forecastError: "Could not load forecast. Check internet and try again.",
    chooseYourPlan: "Choose your plan",
    unlockVedicTitle: "Unlock Complete\nVedic Astrology",
    noResultFound: "No result found. Go back and calculate again.",
    goBack: "Go Back",
    currentPlan: "Current Plan",
    billingCycle: "Billing Cycle",
    paymentGateway: "Payment Gateway",
    securePayment: "Secure Payment",
    tryAgainBtn: "Try Again",
    monthly: "Monthly",
    yearly: "Yearly",
    settingEditProfile: "Edit Profile",
    profilesCount: "profiles",
    settingSubscription: "Subscription",
    sectionSupport: "SUPPORT",
    settingAbout: "About",
    settingHelp: "Help & Support",
    settingRateUs: "Rate Us",
    settingShareApp: "Share App",
    sectionLegal: "LEGAL",
    settingLegal: "Terms & Privacy",
    sectionDanger: "DANGER ZONE",
    settingDeleteAcc: "Delete Account",
    logoutTitle: "Log Out",
    logoutConfirm: "Are you sure you want to log out?",
    logoutCta: "Log Out",
    kundliRequired: "Kundli required",
    kundliRequiredSub: "Enter your birth details to see your real Mahadasha, Antardasha and Pratyantar Dasha predictions with live planetary transits.",
    futureDemoBanner: "Create your kundli — for personalized dasha predictions",
    activeDashaPhase: "Active Dasha Phase",
    phaseGood: "Good",
    phaseChallenging: "Challenging",
    phaseAverage: "Average",
    phaseSuffix: "phase",
    activeLabel: "Active",
    sadeSatiAlert: "Sade Sati active — Saturn's 7.5-year transit over your natal Moon. Health and finances need extra attention.",
    transitUnavailBanner: "Transit data unavailable — chart shows natal dasha strength only, not live planetary transits.",
    sixMonthTrend: "6-Month Trend",
    transitUnavailShort: "Transit data unavailable",
    upcomingPD: "Upcoming Pratyantardasha",
    whyThisScore: "Why this score?",
    sixMonthAvg: "6-month average score",
    basedOnNatal: "Based on natal dasha only",
  },

  // ── HINGLISH (Hindi in Roman script) ────────────────────────────────────────
  hn: {
    tabHome: "Home", tabKundli: "Kundli", tabAsk: "Poochein",
    tabLifeMap: "Life Map", tabFuture: "Future", tabNotice: "Notice", tabProfile: "Profile",

    save: "Save karein", cancel: "Cancel", skip: "Skip", back: "Wapas",
    next: "Aage", done: "Ho gaya", retry: "Dobara try karein", search: "Search",
    loading: "Load ho raha hai...", close: "Band karein", confirm: "Confirm",
    delete: "Delete", edit: "Edit",

    logIn: "Log In", createAccount: "Account banaayein",
    continueGuest: "Bina account ke continue karein",
    guestNote: "Aapke charts sirf is device par save honge",
    emailAddr: "Email Address", password: "Password",
    yourName: "Aapka naam", loginSubtitle: "Aapka personal Vedic astrology guide",

    birthDetails: "Birth Details",
    birthSubtitle: "Sahi Kundli ke liye accurate birth details zaroori hain.",
    dateOfBirth: "Janam ki Date", timeOfBirth: "Janam ka Time",
    birthPlace: "Janam Sthan", gender: "Gender",
    genderMale: "Male", genderFemale: "Female", genderOther: "Other",
    searchCity: "Sheher ya gaon search karein...",
    generateKundli: "Kundli banayein", generatingKundli: "Kundli ban rahi hai...",
    day: "Din", month: "Mahina", year: "Saal",
    hour: "Ghanta", minute: "Minute",
    timeTip: "Janam ka time Mahadasha ko directly affect karta hai. AM ya PM dhyan se check karein.",

    todayEnergy: "Aaj ki Cosmic Energy", moonTransit: "Chandra Gochar",
    currentDasha: "Current Dasha", setupKundli: "Apni Kundli Setup karein",
    setupKundliSub: "Vedic chart banane ke liye birth details daalein",
    viewAll: "Sab dekhein", viewDetails: "Details dekhein",
    forecast: "Bhavishyafal", today: "Aaj",

    natalChart: "Janam Kundli", planets: "Grah",
    dashaTimeline: "Dasha Timeline", nakshatra: "Nakshatra",
    ascendant: "Lagna", house: "Bhav",
    noKundli: "Abhi Kundli nahi hai", noKundliSub: "Saare features unlock karne ke liye Kundli banayein",
    createKundli: "Kundli banayein", chartType: "Chart Type",

    settings: "Settings", language: "Bhasha", darkMode: "Dark Mode",
    myProfiles: "Meri Profiles", subscription: "Subscription",
    addFamilyMember: "Family Member add karein",
    addFamilySub: "Beta, Beti, Jeevansathi, Maa-Baap, Dost aur bahut kuch",
    logOut: "Log Out", deleteAccount: "Account delete karein",
    freePlan: "Free Plan", upgradeNow: "Abhi Upgrade karein",
    selectLanguage: "Bhasha chunein", langSubtitle: "App ki bhasha turant badal jaayegi",
    langSearch: "Bhasha search karein...", supported: "Supported", comingSoon: "Jald aa raha hai",

    askTitle: "Jyotish se poochein", askPlaceholder: "Apni kundli ke baare mein kuch bhi poochein...",
    askSend: "Bhejein", askSuggestions: "Yeh poochein...",

    lifeMapTitle: "Life Map", lifeMapSubtitle: "Sitaaron dwara mapped aapki zindagi",
    lifeMapRelSub: "Pyaar, compatibility aur rishte", lifeMapCarSub: "Growth, success aur purpose",
    lifeMapHealthSub: "Sharir, mann aur energy", lifeMapFinSub: "Dhan, stability aur flow",
    lifeMapComing: "Aur dimensions aa rahe hain", lifeMapComingSub: "Education, Travel, Spirituality aur bahut kuch",

    futureTitle: "Future Timeline", futureSubtitle: "Agle 6 mahine decoded",
    career: "Career", finance: "Paisa", relationship: "Rishta", health: "Swasthya",

    noticeTitle: "Notices", noNotices: "Abhi koi notice nahi",

    errorGeneral: "Kuch galat ho gaya. Dobara try karein.",
    noInternet: "Internet connection nahi hai.", tryAgain: "Dobara try karein",
    prevDay: "Pehle Din",
    nextDay: "Agle Din",
    unlockForecastTitle: "Personalized Forecast Unlock Karein",
    unlockForecastSub: "Apni Kundli ke hisaab se daily energy score milega",
    forecastError: "Forecast load nahi ho saka. Internet check karke wapas try karein.",
    chooseYourPlan: "Apna plan choose karein",
    unlockVedicTitle: "Poori Vedic Astrology\nUnlock Karein",
    noResultFound: "Koi result nahi mila. Wapas jao aur dobara calculate karein.",
    goBack: "Wapas Jao",
    currentPlan: "Current Plan",
    billingCycle: "Billing Cycle",
    paymentGateway: "Payment Gateway",
    securePayment: "Surakshit Payment",
    tryAgainBtn: "Dobara Try Karein",
    monthly: "Mahina",
    yearly: "Saal",
    settingEditProfile: "Profile Edit Karein",
    profilesCount: "profiles",
    settingSubscription: "Subscription",
    sectionSupport: "SUPPORT",
    settingAbout: "Humare Baare Mein",
    settingHelp: "Help & Support",
    settingRateUs: "Rate Karein",
    settingShareApp: "App Share Karein",
    sectionLegal: "LEGAL",
    settingLegal: "Terms & Privacy",
    sectionDanger: "DANGER ZONE",
    settingDeleteAcc: "Account Delete Karein",
    logoutTitle: "Log Out",
    logoutConfirm: "Kya aap sach mein log out karna chahte hain?",
    logoutCta: "Log Out",
    kundliRequired: "Kundli zaroori hai",
    kundliRequiredSub: "Apni real Mahadasha, Antardasha aur Pratyantar Dasha predictions ke liye apne birth details daalein.",
    futureDemoBanner: "Apni kundli banao — personalized dasha predictions ke liye",
    activeDashaPhase: "Active Dasha Phase",
    phaseGood: "Accha",
    phaseChallenging: "Chunautiyan",
    phaseAverage: "Average",
    phaseSuffix: "phase",
    activeLabel: "Active",
    sadeSatiAlert: "Sade Sati active — Shani ka 7.5 saal ka transit aapke natal Chandra par. Sehat aur paiso par dhyan dein.",
    transitUnavailBanner: "Transit data unavailable — chart sirf natal dasha strength dikha raha hai, live planetary transits nahi.",
    sixMonthTrend: "6-Month Trend",
    transitUnavailShort: "Transit data unavailable",
    upcomingPD: "Aane waali Pratyantardasha",
    whyThisScore: "Yeh score kyun?",
    sixMonthAvg: "6-month average score",
    basedOnNatal: "Natal dasha par based",
  },

  // ── HINDI ───────────────────────────────────────────────────────────────────
  hi: {
    tabHome: "होम", tabKundli: "कुंडली", tabAsk: "पूछें",
    tabLifeMap: "लाइफ मैप", tabFuture: "भविष्य", tabNotice: "सूचना", tabProfile: "प्रोफाइल",

    save: "सहेजें", cancel: "रद्द करें", skip: "छोड़ें", back: "वापस",
    next: "आगे", done: "हो गया", retry: "दोबारा कोशिश करें", search: "खोजें",
    loading: "लोड हो रहा है...", close: "बंद करें", confirm: "पुष्टि करें",
    delete: "हटाएं", edit: "संपादित करें",

    logIn: "लॉग इन करें", createAccount: "खाता बनाएं",
    continueGuest: "बिना खाते के जारी रखें",
    guestNote: "आपके चार्ट केवल इस डिवाइस पर सहेजे जाएंगे",
    emailAddr: "ईमेल पता", password: "पासवर्ड",
    yourName: "आपका नाम", loginSubtitle: "आपका व्यक्तिगत वैदिक ज्योतिष मार्गदर्शक",

    birthDetails: "जन्म विवरण",
    birthSubtitle: "सटीक कुंडली के लिए सही जन्म विवरण आवश्यक है।",
    dateOfBirth: "जन्म तिथि", timeOfBirth: "जन्म समय",
    birthPlace: "जन्म स्थान", gender: "लिंग",
    genderMale: "पुरुष", genderFemale: "महिला", genderOther: "अन्य",
    searchCity: "शहर या गाँव खोजें...",
    generateKundli: "कुंडली बनाएं", generatingKundli: "कुंडली बन रही है...",
    day: "दिन", month: "महीना", year: "वर्ष",
    hour: "घंटा", minute: "मिनट",
    timeTip: "जन्म समय महादशा को सीधे प्रभावित करता है। AM या PM ध्यान से जाँचें।",

    todayEnergy: "आज की ब्रह्मांड ऊर्जा", moonTransit: "चंद्र गोचर",
    currentDasha: "वर्तमान दशा", setupKundli: "अपनी कुंडली सेट करें",
    setupKundliSub: "वैदिक चार्ट बनाने के लिए जन्म विवरण दर्ज करें",
    viewAll: "सब देखें", viewDetails: "विवरण देखें",
    forecast: "भविष्यफल", today: "आज",

    natalChart: "जन्म कुंडली", planets: "ग्रह",
    dashaTimeline: "दशा समयरेखा", nakshatra: "नक्षत्र",
    ascendant: "लग्न", house: "भाव",
    noKundli: "अभी कुंडली नहीं", noKundliSub: "सभी सुविधाएं अनलॉक करने के लिए कुंडली बनाएं",
    createKundli: "कुंडली बनाएं", chartType: "चार्ट प्रकार",

    settings: "सेटिंग्स", language: "भाषा", darkMode: "डार्क मोड",
    myProfiles: "मेरी प्रोफाइल", subscription: "सदस्यता",
    addFamilyMember: "परिवार सदस्य जोड़ें",
    addFamilySub: "बेटा, बेटी, जीवनसाथी, माता-पिता, मित्र और अधिक",
    logOut: "लॉग आउट", deleteAccount: "खाता हटाएं",
    freePlan: "मुफ़्त योजना", upgradeNow: "अभी अपग्रेड करें",
    selectLanguage: "भाषा चुनें", langSubtitle: "ऐप की भाषा तुरंत बदल जाएगी",
    langSearch: "भाषा खोजें...", supported: "समर्थित", comingSoon: "जल्द आ रहा है",

    askTitle: "ज्योतिष से पूछें", askPlaceholder: "अपनी कुंडली के बारे में कुछ भी पूछें...",
    askSend: "भेजें", askSuggestions: "ये पूछें...",

    lifeMapTitle: "लाइफ मैप", lifeMapSubtitle: "सितारों द्वारा मैप किया जीवन",
    lifeMapRelSub: "प्रेम, अनुकूलता और बंधन", lifeMapCarSub: "विकास, सफलता और उद्देश्य",
    lifeMapHealthSub: "शरीर, मन और ऊर्जा", lifeMapFinSub: "धन, स्थिरता और प्रवाह",
    lifeMapComing: "और आयाम आ रहे हैं", lifeMapComingSub: "शिक्षा, यात्रा, अध्यात्म और अधिक",
    futureTitle: "भविष्य टाइमलाइन", futureSubtitle: "अगले 6 महीने डिकोड", career: "करियर",
    finance: "वित्त", relationship: "संबंध", health: "स्वास्थ्य",

    noticeTitle: "सूचनाएं", noNotices: "अभी कोई सूचना नहीं",

    errorGeneral: "कुछ गलत हुआ। कृपया दोबारा कोशिश करें।",
    noInternet: "इंटरनेट कनेक्शन नहीं।", tryAgain: "दोबारा कोशिश करें",
    prevDay: "पिछला दिन",
    nextDay: "अगला दिन",
    unlockForecastTitle: "व्यक्तिगत भविष्यवाणी अनलॉक करें",
    unlockForecastSub: "अपनी कुंडली के अनुसार दैनिक ऊर्जा स्कोर प्राप्त करें",
    forecastError: "भविष्यवाणी लोड नहीं हो सकी। इंटरनेट जांचकर पुनः प्रयास करें।",
    chooseYourPlan: "अपना प्लान चुनें",
    unlockVedicTitle: "संपूर्ण वैदिक ज्योतिष\nअनलॉक करें",
    noResultFound: "कोई परिणाम नहीं मिला। वापस जाकर पुनः गणना करें।",
    goBack: "वापस जाएं",
    currentPlan: "वर्तमान प्लान",
    billingCycle: "बिलिंग चक्र",
    paymentGateway: "पेमेंट गेटवे",
    securePayment: "सुरक्षित भुगतान",
    tryAgainBtn: "पुनः प्रयास करें",
    monthly: "मासिक",
    yearly: "वार्षिक",
    settingEditProfile: "प्रोफ़ाइल संपादित करें",
    profilesCount: "प्रोफ़ाइल",
    settingSubscription: "सब्सक्रिप्शन",
    sectionSupport: "सहायता",
    settingAbout: "हमारे बारे में",
    settingHelp: "सहायता और समर्थन",
    settingRateUs: "हमें रेट करें",
    settingShareApp: "ऐप शेयर करें",
    sectionLegal: "कानूनी",
    settingLegal: "शर्तें और गोपनीयता",
    sectionDanger: "खतरा क्षेत्र",
    settingDeleteAcc: "खाता हटाएँ",
    logoutTitle: "लॉग आउट",
    logoutConfirm: "क्या आप वाकई लॉग आउट करना चाहते हैं?",
    logoutCta: "लॉग आउट",
    kundliRequired: "कुंडली आवश्यक",
    kundliRequiredSub: "अपनी वास्तविक महादशा, अंतर्दशा और प्रत्यंतर दशा भविष्यवाणियों के लिए अपनी जन्म जानकारी दर्ज करें।",
    futureDemoBanner: "व्यक्तिगत दशा भविष्यवाणी के लिए अपनी कुंडली बनाएँ",
    activeDashaPhase: "सक्रिय दशा चरण",
    phaseGood: "अच्छा",
    phaseChallenging: "चुनौतीपूर्ण",
    phaseAverage: "औसत",
    phaseSuffix: "चरण",
    activeLabel: "सक्रिय",
    sadeSatiAlert: "साढ़े साती सक्रिय — शनि का 7.5 वर्ष का गोचर आपके जन्म चंद्रमा पर। स्वास्थ्य व वित्त पर ध्यान दें।",
    transitUnavailBanner: "गोचर डेटा अनुपलब्ध — चार्ट केवल जन्म दशा शक्ति दिखा रहा है, वास्तविक ग्रह गोचर नहीं।",
    sixMonthTrend: "6-महीने का रुझान",
    transitUnavailShort: "गोचर डेटा अनुपलब्ध",
    upcomingPD: "आगामी प्रत्यंतर दशा",
    whyThisScore: "यह स्कोर क्यों?",
    sixMonthAvg: "6-महीने का औसत स्कोर",
    basedOnNatal: "केवल जन्म दशा पर आधारित",
  },
};

/** BCP-47 locale for `Date#toLocaleDateString` / `toLocaleString` from app language. */
export function uiDateLocale(lang: UILang | string): string {
  const map: Partial<Record<UILang, string>> = {
    hi: "hi-IN", hn: "hi-IN", en: "en-IN",
  };
  return map[lang as UILang] ?? "en-IN";
}

/** Map any stored/legacy language code to en, hn, or hi. */
export function coerceUILang(lang: string): UILang {
  const c = (lang || "en").trim().toLowerCase();
  if (c === "en" || c === "english") return "en";
  if (c === "hn" || c === "hinglish") return "hn";
  if (c === "hi" || c === "hindi") return "hi";
  return "en";
}

// ── Helper: get translations for a given language code ────────────────────────
// Falls back to "en" for any unsupported/unknown code
export function getT(lang: string): Translations {
  return T[coerceUILang(lang)];
}
