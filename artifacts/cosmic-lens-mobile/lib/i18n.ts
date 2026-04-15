// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — App-wide UI Translation System
// India  : en hi bn mr ta te gu kn ml pa or as
// Global : en zh es ar fr pt de ru ja id ko tr
// ══════════════════════════════════════════════════════════════════════════════

export type UILang =
  | "en" | "hi" | "mr" | "bn" | "te" | "ta" | "gu" | "kn"
  | "ml" | "pa" | "or" | "as"
  | "zh" | "es" | "ar" | "fr" | "pt" | "de" | "ru" | "ja" | "id" | "ko" | "tr";

// ── Region buckets (English is in both) ───────────────────────────────────────
export const INDIA_LANG_CODES  = ["en","hi","bn","mr","ta","te","gu","kn","ml","or","pa","as"] as const;
export const GLOBAL_LANG_CODES = ["en","zh","es","ar","fr","pt","de","ru","ja","id","ko","tr"] as const;

export interface Translations {
  // ── Tab bar ──────────────────────────────────────────────
  tabHome:      string;
  tabKundli:    string;
  tabAsk:       string;
  tabLifeMap:   string;
  tabFuture:    string;
  tabNotice:    string;
  tabProfile:   string;

  // ── Common actions ────────────────────────────────────────
  save:     string;
  cancel:   string;
  skip:     string;
  back:     string;
  next:     string;
  done:     string;
  retry:    string;
  search:   string;
  loading:  string;
  close:    string;
  confirm:  string;
  delete:   string;
  edit:     string;

  // ── Auth / Login ──────────────────────────────────────────
  logIn:           string;
  createAccount:   string;
  continueGuest:   string;
  guestNote:       string;
  emailAddr:       string;
  password:        string;
  yourName:        string;
  loginSubtitle:   string;

  // ── Onboarding ────────────────────────────────────────────
  birthDetails:    string;
  birthSubtitle:   string;
  dateOfBirth:     string;
  timeOfBirth:     string;
  birthPlace:      string;
  gender:          string;
  genderMale:      string;
  genderFemale:    string;
  genderOther:     string;
  searchCity:      string;
  generateKundli:  string;
  generatingKundli:string;
  day:             string;
  month:           string;
  year:            string;
  hour:            string;
  minute:          string;
  timeTip:         string;

  // ── Home screen ───────────────────────────────────────────
  todayEnergy:     string;
  moonTransit:     string;
  currentDasha:    string;
  setupKundli:     string;
  setupKundliSub:  string;
  viewAll:         string;
  viewDetails:     string;
  forecast:        string;
  today:           string;

  // ── Kundli screen ─────────────────────────────────────────
  natalChart:      string;
  planets:         string;
  dashaTimeline:   string;
  nakshatra:       string;
  ascendant:       string;
  house:           string;
  noKundli:        string;
  noKundliSub:     string;
  createKundli:    string;
  chartType:       string;

  // ── Profile / Settings ────────────────────────────────────
  settings:        string;
  language:        string;
  darkMode:        string;
  myProfiles:      string;
  subscription:    string;
  addFamilyMember: string;
  addFamilySub:    string;
  logOut:          string;
  deleteAccount:   string;
  freePlan:        string;
  upgradeNow:      string;
  selectLanguage:  string;
  langSubtitle:    string;
  langSearch:      string;
  supported:       string;
  comingSoon:      string;

  // ── Ask AI ────────────────────────────────────────────────
  askTitle:        string;
  askPlaceholder:  string;
  askSend:         string;
  askSuggestions:  string;

  // ── Life Map ──────────────────────────────────────────────
  lifeMapTitle:      string;
  lifeMapSubtitle:   string;
  lifeMapRelSub:     string;
  lifeMapCarSub:     string;
  lifeMapHealthSub:  string;
  lifeMapFinSub:     string;
  lifeMapComing:     string;
  lifeMapComingSub:  string;

  // ── Future ────────────────────────────────────────────────
  futureTitle:     string;
  futureSubtitle:  string;
  career:          string;
  finance:         string;
  relationship:    string;
  health:          string;

  // ── Notice ────────────────────────────────────────────────
  noticeTitle:     string;
  noNotices:       string;

  // ── Errors / States ───────────────────────────────────────
  errorGeneral:    string;
  noInternet:      string;
  tryAgain:        string;
}

// ══════════════════════════════════════════════════════════════════════════════
// TRANSLATION TABLE
// ══════════════════════════════════════════════════════════════════════════════

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

    askTitle: "Ask Jyotish AI", askPlaceholder: "Ask anything about your chart...",
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
  },

  // ── HINDI ───────────────────────────────────────────────────────────────────
  hi: {
    tabHome: "होम", tabKundli: "कुंडली", tabAsk: "पूछें",
    tabLifeMap: "लाइफ मैप", tabLifeMap: "लाइफ मॅप", tabFuture: "भविष्य", tabNotice: "सूचना", tabProfile: "प्रोफाइल",

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

    askTitle: "ज्योतिष AI से पूछें", askPlaceholder: "अपनी कुंडली के बारे में कुछ भी पूछें...",
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
  },

  // ── MARATHI ─────────────────────────────────────────────────────────────────
  mr: {
    tabHome: "होम", tabKundli: "कुंडली", tabAsk: "विचारा",
    tabLifeMap: "लाइफ मैप", tabLifeMap: "लाइफ मॅप", tabFuture: "भविष्य", tabNotice: "सूचना", tabProfile: "प्रोफाइल",

    save: "जतन करा", cancel: "रद्द करा", skip: "वगळा", back: "मागे",
    next: "पुढे", done: "झाले", retry: "पुन्हा प्रयत्न करा", search: "शोधा",
    loading: "लोड होत आहे...", close: "बंद करा", confirm: "पुष्टी करा",
    delete: "हटवा", edit: "संपादित करा",

    logIn: "लॉग इन करा", createAccount: "खाते बनवा",
    continueGuest: "खात्याशिवाय पुढे जा",
    guestNote: "तुमचे चार्ट फक्त या डिव्हाइसवर जतन होतील",
    emailAddr: "ईमेल पत्ता", password: "पासवर्ड",
    yourName: "तुमचे नाव", loginSubtitle: "तुमचे वैयक्तिक वैदिक ज्योतिष मार्गदर्शक",

    birthDetails: "जन्म तपशील",
    birthSubtitle: "अचूक कुंडलीसाठी योग्य जन्म तपशील आवश्यक आहे.",
    dateOfBirth: "जन्म तारीख", timeOfBirth: "जन्म वेळ",
    birthPlace: "जन्म ठिकाण", gender: "लिंग",
    genderMale: "पुरुष", genderFemale: "महिला", genderOther: "इतर",
    searchCity: "शहर किंवा गाव शोधा...",
    generateKundli: "कुंडली बनवा", generatingKundli: "कुंडली बनत आहे...",
    day: "दिवस", month: "महिना", year: "वर्ष",
    hour: "तास", minute: "मिनिट",
    timeTip: "जन्म वेळ महादशेवर थेट परिणाम करते. AM किंवा PM काळजीपूर्वक तपासा.",

    todayEnergy: "आजची ब्रह्मांड ऊर्जा", moonTransit: "चंद्र गोचर",
    currentDasha: "सध्याची दशा", setupKundli: "तुमची कुंडली सेट करा",
    setupKundliSub: "वैदिक चार्ट तयार करण्यासाठी जन्म तपशील द्या",
    viewAll: "सर्व पाहा", viewDetails: "तपशील पाहा",
    forecast: "भविष्यवाणी", today: "आज",

    natalChart: "जन्म कुंडली", planets: "ग्रह",
    dashaTimeline: "दशा वेळरेषा", nakshatra: "नक्षत्र",
    ascendant: "लग्न", house: "भाव",
    noKundli: "अजून कुंडली नाही", noKundliSub: "सर्व वैशिष्ट्ये अनलॉक करण्यासाठी कुंडली बनवा",
    createKundli: "कुंडली बनवा", chartType: "चार्ट प्रकार",

    settings: "सेटिंग्ज", language: "भाषा", darkMode: "डार्क मोड",
    myProfiles: "माझे प्रोफाइल", subscription: "सदस्यत्व",
    addFamilyMember: "कुटुंब सदस्य जोडा",
    addFamilySub: "मुलगा, मुलगी, जोडीदार, पालक, मित्र आणि अधिक",
    logOut: "लॉग आउट", deleteAccount: "खाते हटवा",
    freePlan: "मोफत योजना", upgradeNow: "आत्ता अपग्रेड करा",
    selectLanguage: "भाषा निवडा", langSubtitle: "ऐपची भाषा लगेच बदलेल",
    langSearch: "भाषा शोधा...", supported: "समर्थित", comingSoon: "लवकरच येत आहे",

    askTitle: "ज्योतिष AI ला विचारा", askPlaceholder: "तुमच्या चार्टबद्दल काहीही विचारा...",
    askSend: "पाठवा", askSuggestions: "हे विचारून पाहा...",

    lifeMapTitle: "लाइफ मॅप", lifeMapSubtitle: "ताऱ्यांनी मॅप केलेले जीवन",
    lifeMapRelSub: "प्रेम, सुसंगतता आणि बंध", lifeMapCarSub: "वाढ, यश आणि उद्देश",
    lifeMapHealthSub: "शरीर, मन आणि ऊर्जा", lifeMapFinSub: "संपत्ती, स्थिरता आणि प्रवाह",
    lifeMapComing: "अधिक आयाम येत आहेत", lifeMapComingSub: "शिक्षण, प्रवास, अध्यात्म आणि अधिक",
    futureTitle: "भविष्य टाइमलाइन", futureSubtitle: "पुढचे 6 महिने डिकोड", career: "करिअर",
    finance: "वित्त", relationship: "नाते", health: "आरोग्य",

    noticeTitle: "सूचना", noNotices: "अजून कोणतीही सूचना नाही",

    errorGeneral: "काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.",
    noInternet: "इंटरनेट कनेक्शन नाही.", tryAgain: "पुन्हा प्रयत्न करा",
  },

  // ── BENGALI ─────────────────────────────────────────────────────────────────
  bn: {
    tabHome: "হোম", tabKundli: "কুণ্ডলী", tabAsk: "জিজ্ঞেস করুন",
    tabLifeMap: "লাইফ ম্যাপ", tabLifeMap: "লাইফ মেপ", tabFuture: "ভবিষ্যৎ", tabNotice: "বিজ্ঞপ্তি", tabProfile: "প্রোফাইল",

    save: "সংরক্ষণ করুন", cancel: "বাতিল করুন", skip: "এড়িয়ে যান", back: "পিছনে",
    next: "পরবর্তী", done: "সম্পন্ন", retry: "আবার চেষ্টা করুন", search: "খোঁজুন",
    loading: "লোড হচ্ছে...", close: "বন্ধ করুন", confirm: "নিশ্চিত করুন",
    delete: "মুছুন", edit: "সম্পাদনা করুন",

    logIn: "লগ ইন করুন", createAccount: "অ্যাকাউন্ট তৈরি করুন",
    continueGuest: "অ্যাকাউন্ট ছাড়াই চালিয়ে যান",
    guestNote: "আপনার চার্ট শুধুমাত্র এই ডিভাইসে সংরক্ষিত হবে",
    emailAddr: "ইমেইল ঠিকানা", password: "পাসওয়ার্ড",
    yourName: "আপনার নাম", loginSubtitle: "আপনার ব্যক্তিগত বৈদিক জ্যোতিষ গাইড",

    birthDetails: "জন্ম বিবরণ",
    birthSubtitle: "সঠিক কুণ্ডলীর জন্য সঠিক জন্ম বিবরণ প্রয়োজন।",
    dateOfBirth: "জন্ম তারিখ", timeOfBirth: "জন্ম সময়",
    birthPlace: "জন্মস্থান", gender: "লিঙ্গ",
    genderMale: "পুরুষ", genderFemale: "মহিলা", genderOther: "অন্যান্য",
    searchCity: "শহর বা গ্রাম খুঁজুন...",
    generateKundli: "কুণ্ডলী তৈরি করুন", generatingKundli: "কুণ্ডলী তৈরি হচ্ছে...",
    day: "দিন", month: "মাস", year: "বছর",
    hour: "ঘণ্টা", minute: "মিনিট",
    timeTip: "জন্ম সময় সরাসরি মহাদশাকে প্রভাবিত করে। AM বা PM সতর্কতার সাথে যাচাই করুন।",

    todayEnergy: "আজকের মহাজাগতিক শক্তি", moonTransit: "চন্দ্র গোচর",
    currentDasha: "বর্তমান দশা", setupKundli: "আপনার কুণ্ডলী সেট আপ করুন",
    setupKundliSub: "বৈদিক চার্ট তৈরির জন্য জন্ম বিবরণ দিন",
    viewAll: "সব দেখুন", viewDetails: "বিবরণ দেখুন",
    forecast: "পূর্বাভাস", today: "আজ",

    natalChart: "জন্ম কুণ্ডলী", planets: "গ্রহ",
    dashaTimeline: "দশা সময়রেখা", nakshatra: "নক্ষত্র",
    ascendant: "লগ্ন", house: "ভাব",
    noKundli: "এখনো কোনো কুণ্ডলী নেই", noKundliSub: "সব ফিচার আনলক করতে কুণ্ডলী সেট আপ করুন",
    createKundli: "কুণ্ডলী তৈরি করুন", chartType: "চার্টের ধরন",

    settings: "সেটিংস", language: "ভাষা", darkMode: "ডার্ক মোড",
    myProfiles: "আমার প্রোফাইল", subscription: "সাবস্ক্রিপশন",
    addFamilyMember: "পরিবারের সদস্য যোগ করুন",
    addFamilySub: "ছেলে, মেয়ে, স্বামী/স্ত্রী, অভিভাবক, বন্ধু ও আরও",
    logOut: "লগ আউট", deleteAccount: "অ্যাকাউন্ট মুছুন",
    freePlan: "বিনামূল্যে পরিকল্পনা", upgradeNow: "এখনই আপগ্রেড করুন",
    selectLanguage: "ভাষা নির্বাচন করুন", langSubtitle: "অ্যাপের ভাষা তাৎক্ষণিকভাবে পরিবর্তন হবে",
    langSearch: "ভাষা খুঁজুন...", supported: "সমর্থিত", comingSoon: "শীঘ্রই আসছে",

    askTitle: "জ্যোতিষ AI কে জিজ্ঞেস করুন", askPlaceholder: "আপনার চার্ট সম্পর্কে যা খুশি জিজ্ঞেস করুন...",
    askSend: "পাঠান", askSuggestions: "এগুলো জিজ্ঞেস করে দেখুন...",

    lifeMapTitle: "লাইফ ম্যাপ", lifeMapSubtitle: "তারার দ্বারা ম্যাপ করা জীবন",
    lifeMapRelSub: "প্রেম, সামঞ্জস্য ও বন্ধন", lifeMapCarSub: "বৃদ্ধি, সাফল্য ও উদ্দেশ্য",
    lifeMapHealthSub: "শরীর, মন ও শক্তি", lifeMapFinSub: "সম্পদ, স্থিতি ও প্রবাহ",
    lifeMapComing: "আরও মাত্রা আসছে", lifeMapComingSub: "শিক্ষা, ভ্রমণ, আধ্যাত্মিকতা ও আরও",
    futureTitle: "ভবিষ্যৎ টাইমলাইন", futureSubtitle: "আগামী ৬ মাস ডিকোড", career: "ক্যারিয়ার",
    finance: "অর্থ", relationship: "সম্পর্ক", health: "স্বাস্থ্য",

    noticeTitle: "বিজ্ঞপ্তি", noNotices: "এখনো কোনো বিজ্ঞপ্তি নেই",

    errorGeneral: "কিছু একটা ভুল হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
    noInternet: "ইন্টারনেট সংযোগ নেই।", tryAgain: "আবার চেষ্টা করুন",
  },

  // ── TELUGU ──────────────────────────────────────────────────────────────────
  te: {
    tabHome: "హోమ్", tabKundli: "కుండలి", tabAsk: "అడగండి",
    tabLifeMap: "లైఫ్ మ్యాప్", tabFuture: "భవిష్యత్", tabNotice: "నోటీసు", tabProfile: "ప్రొఫైల్",

    save: "సేవ్ చేయండి", cancel: "రద్దు చేయండి", skip: "దాటవేయండి", back: "వెనుకకు",
    next: "తదుపరి", done: "పూర్తయింది", retry: "మళ్ళీ ప్రయత్నించండి", search: "వెతకండి",
    loading: "లోడ్ అవుతోంది...", close: "మూసేయండి", confirm: "నిర్ధారించండి",
    delete: "తొలగించండి", edit: "సవరించండి",

    logIn: "లాగిన్ అవ్వండి", createAccount: "ఖాతా సృష్టించండి",
    continueGuest: "ఖాతా లేకుండా కొనసాగండి",
    guestNote: "మీ చార్ట్‌లు ఈ పరికరంలో మాత్రమే సేవ్ అవుతాయి",
    emailAddr: "ఇమెయిల్ చిరునామా", password: "పాస్‌వర్డ్",
    yourName: "మీ పేరు", loginSubtitle: "మీ వ్యక్తిగత వేద జ్యోతిష్య మార్గదర్శి",

    birthDetails: "జన్మ వివరాలు",
    birthSubtitle: "సరైన కుండలి కోసం ఖచ్చితమైన జన్మ వివరాలు అవసరం.",
    dateOfBirth: "పుట్టిన తేదీ", timeOfBirth: "పుట్టిన సమయం",
    birthPlace: "జన్మ స్థలం", gender: "లింగం",
    genderMale: "పురుషుడు", genderFemale: "స్త్రీ", genderOther: "ఇతర",
    searchCity: "నగరం లేదా గ్రామాన్ని వెతకండి...",
    generateKundli: "కుండలి రూపొందించండి", generatingKundli: "కుండలి రూపొందిస్తోంది...",
    day: "రోజు", month: "నెల", year: "సంవత్సరం",
    hour: "గంట", minute: "నిమిషం",
    timeTip: "జన్మ సమయం మహాదశను నేరుగా ప్రభావితం చేస్తుంది. AM లేదా PM జాగ్రత్తగా తనిఖీ చేయండి.",

    todayEnergy: "నేటి విశ్వ శక్తి", moonTransit: "చంద్ర గోచారం",
    currentDasha: "ప్రస్తుత దశ", setupKundli: "మీ కుండలి సెటప్ చేయండి",
    setupKundliSub: "వేద చార్ట్ రూపొందించడానికి జన్మ వివరాలు నమోదు చేయండి",
    viewAll: "అన్నీ చూడండి", viewDetails: "వివరాలు చూడండి",
    forecast: "రాశిఫలం", today: "ఈరోజు",

    natalChart: "జన్మ కుండలి", planets: "గ్రహాలు",
    dashaTimeline: "దశ కాలరేఖ", nakshatra: "నక్షత్రం",
    ascendant: "లగ్నం", house: "భావం",
    noKundli: "ఇంకా కుండలి లేదు", noKundliSub: "అన్ని ఫీచర్లు అన్‌లాక్ చేయడానికి కుండలి సెటప్ చేయండి",
    createKundli: "కుండలి సృష్టించండి", chartType: "చార్ట్ రకం",

    settings: "సెట్టింగ్‌లు", language: "భాష", darkMode: "డార్క్ మోడ్",
    myProfiles: "నా ప్రొఫైల్‌లు", subscription: "సభ్యత్వం",
    addFamilyMember: "కుటుంబ సభ్యుడిని జోడించండి",
    addFamilySub: "కొడుకు, కూతురు, జీవిత భాగస్వామి, తల్లిదండ్రులు, స్నేహితుడు మరియు మరిన్ని",
    logOut: "లాగ్ అవుట్", deleteAccount: "ఖాతా తొలగించండి",
    freePlan: "ఉచిత ప్లాన్", upgradeNow: "ఇప్పుడే అప్‌గ్రేడ్ చేయండి",
    selectLanguage: "భాష ఎంచుకోండి", langSubtitle: "యాప్ భాష వెంటనే మారుతుంది",
    langSearch: "భాష వెతకండి...", supported: "మద్దతు ఉంది", comingSoon: "త్వరలో వస్తోంది",

    askTitle: "జ్యోతిష్య AI ని అడగండి", askPlaceholder: "మీ చార్ట్ గురించి ఏదైనా అడగండి...",
    askSend: "పంపండి", askSuggestions: "ఇవి అడిగి చూడండి...",

    lifeMapTitle: "లైఫ్ మ్యాప్", lifeMapSubtitle: "నక్షత్రాలతో మ్యాప్ చేయబడిన జీవితం",
    lifeMapRelSub: "ప్రేమ, అనుకూలత మరియు బంధాలు", lifeMapCarSub: "వృద్ధి, విజయం మరియు ఉద్దేశ్యం",
    lifeMapHealthSub: "శరీరం, మనసు మరియు శక్తి", lifeMapFinSub: "సంపద, స్థిరత్వం మరియు ప్రవాహం",
    lifeMapComing: "మరిన్ని కోణాలు వస్తున్నాయి", lifeMapComingSub: "విద్య, ప్రయాణం, ఆధ్యాత్మికత మరియు మరిన్ని",
    futureTitle: "భవిష్యత్ టైమ్‌లైన్", futureSubtitle: "మీ తదుపరి 6 నెలలు డీకోడ్", career: "కెరీర్",
    finance: "ఆర్థికం", relationship: "సంబంధం", health: "ఆరోగ్యం",

    noticeTitle: "నోటీసులు", noNotices: "ఇంకా నోటీసులు లేవు",

    errorGeneral: "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    noInternet: "ఇంటర్నెట్ కనెక్షన్ లేదు.", tryAgain: "మళ్ళీ ప్రయత్నించండి",
  },

  // ── TAMIL ───────────────────────────────────────────────────────────────────
  ta: {
    tabHome: "முகப்பு", tabKundli: "ஜாதகம்", tabAsk: "கேளுங்கள்",
    tabLifeMap: "லைஃப் மேப்", tabFuture: "எதிர்காலம்", tabNotice: "அறிவிப்பு", tabProfile: "சுயவிவரம்",

    save: "சேமிக்கவும்", cancel: "ரத்து செய்யவும்", skip: "தவிர்க்கவும்", back: "பின்செல்",
    next: "அடுத்து", done: "முடிந்தது", retry: "மீண்டும் முயற்சிக்கவும்", search: "தேடவும்",
    loading: "ஏற்றுகிறது...", close: "மூடவும்", confirm: "உறுதிப்படுத்தவும்",
    delete: "நீக்கவும்", edit: "திருத்தவும்",

    logIn: "உள்நுழையவும்", createAccount: "கணக்கு உருவாக்கவும்",
    continueGuest: "கணக்கு இல்லாமல் தொடரவும்",
    guestNote: "உங்கள் சார்ட்கள் இந்த சாதனத்தில் மட்டுமே சேமிக்கப்படும்",
    emailAddr: "மின்னஞ்சல் முகவரி", password: "கடவுச்சொல்",
    yourName: "உங்கள் பெயர்", loginSubtitle: "உங்கள் தனிப்பட்ட வேத ஜோதிட வழிகாட்டி",

    birthDetails: "பிறப்பு விவரங்கள்",
    birthSubtitle: "சரியான ஜாதகத்திற்கு துல்லியமான பிறப்பு விவரங்கள் தேவை.",
    dateOfBirth: "பிறந்த தேதி", timeOfBirth: "பிறந்த நேரம்",
    birthPlace: "பிறந்த இடம்", gender: "பாலினம்",
    genderMale: "ஆண்", genderFemale: "பெண்", genderOther: "மற்றவை",
    searchCity: "நகரம் அல்லது கிராமம் தேடவும்...",
    generateKundli: "ஜாதகம் உருவாக்கவும்", generatingKundli: "ஜாதகம் உருவாக்குகிறது...",
    day: "நாள்", month: "மாதம்", year: "ஆண்டு",
    hour: "மணி", minute: "நிமிடம்",
    timeTip: "பிறந்த நேரம் மகாதசையை நேரடியாக பாதிக்கிறது. AM அல்லது PM கவனமாக சரிபார்க்கவும்.",

    todayEnergy: "இன்றைய பிரபஞ்ச ஆற்றல்", moonTransit: "சந்திர கோசாரம்",
    currentDasha: "தற்போதைய தசை", setupKundli: "உங்கள் ஜாதகம் அமைக்கவும்",
    setupKundliSub: "வேத சார்ட் உருவாக்க பிறப்பு விவரங்கள் உள்ளிடவும்",
    viewAll: "அனைத்தும் காண்க", viewDetails: "விவரங்கள் காண்க",
    forecast: "வானிலை அறிவிப்பு", today: "இன்று",

    natalChart: "ஜாதக சக்கரம்", planets: "கிரகங்கள்",
    dashaTimeline: "தசை காலவரிசை", nakshatra: "நட்சத்திரம்",
    ascendant: "லக்னம்", house: "பாவம்",
    noKundli: "இன்னும் ஜாதகம் இல்லை", noKundliSub: "அனைத்து அம்சங்களையும் திறக்க ஜாதகம் அமைக்கவும்",
    createKundli: "ஜாதகம் உருவாக்கவும்", chartType: "சார்ட் வகை",

    settings: "அமைப்புகள்", language: "மொழி", darkMode: "இருண்ட பயன்முறை",
    myProfiles: "என் சுயவிவரங்கள்", subscription: "சந்தா",
    addFamilyMember: "குடும்ப உறுப்பினரை சேர்க்கவும்",
    addFamilySub: "மகன், மகள், வாழ்க்கைத்துணை, பெற்றோர், நண்பர் மற்றும் மேலும்",
    logOut: "வெளியேறவும்", deleteAccount: "கணக்கை நீக்கவும்",
    freePlan: "இலவச திட்டம்", upgradeNow: "இப்போதே மேம்படுத்தவும்",
    selectLanguage: "மொழி தேர்ந்தெடுக்கவும்", langSubtitle: "செயலி மொழி உடனடியாக மாறும்",
    langSearch: "மொழி தேடவும்...", supported: "ஆதரிக்கப்படுகிறது", comingSoon: "விரைவில் வருகிறது",

    askTitle: "ஜோதிட AI ஐ கேளுங்கள்", askPlaceholder: "உங்கள் சார்ட் பற்றி எதுவும் கேளுங்கள்...",
    askSend: "அனுப்பவும்", askSuggestions: "இவற்றை கேளுங்கள்...",

    lifeMapTitle: "லைஃப் மேப்", lifeMapSubtitle: "நட்சத்திரங்களால் வரைபடமான வாழ்க்கை",
    lifeMapRelSub: "காதல், பொருத்தம் மற்றும் பிணைப்பு", lifeMapCarSub: "வளர்ச்சி, வெற்றி மற்றும் நோக்கம்",
    lifeMapHealthSub: "உடல், மனம் மற்றும் உயிர்ச்சக்தி", lifeMapFinSub: "செல்வம், நிலைத்தன்மை மற்றும் ஓட்டம்",
    lifeMapComing: "மேலும் பரிமாணங்கள் வருகின்றன", lifeMapComingSub: "கல்வி, பயணம், ஆன்மீகம் மற்றும் மேலும்",
    futureTitle: "எதிர்காலம் டைம்லைன்", futureSubtitle: "அடுத்த 6 மாதங்கள் டிகோடு", career: "தொழில்",
    finance: "நிதி", relationship: "உறவு", health: "ஆரோக்கியம்",

    noticeTitle: "அறிவிப்புகள்", noNotices: "இன்னும் அறிவிப்புகள் இல்லை",

    errorGeneral: "ஏதோ தவறு ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.",
    noInternet: "இணைய இணைப்பு இல்லை.", tryAgain: "மீண்டும் முயற்சிக்கவும்",
  },

  // ── GUJARATI ────────────────────────────────────────────────────────────────
  gu: {
    tabHome: "હોમ", tabKundli: "કુંડળી", tabAsk: "પૂછો",
    tabLifeMap: "લાઇફ મેપ", tabFuture: "ભવિષ્ય", tabNotice: "સૂચના", tabProfile: "પ્રોફાઇલ",

    save: "સાચવો", cancel: "રદ કરો", skip: "છોડો", back: "પાછળ",
    next: "આગળ", done: "થઈ ગયું", retry: "ફરી પ્રયાસ કરો", search: "શોધો",
    loading: "લોડ થઈ રહ્યું છે...", close: "બંધ કરો", confirm: "પુષ્ટિ કરો",
    delete: "કાઢી નાખો", edit: "સંપાદિત કરો",

    logIn: "લૉગ ઇન કરો", createAccount: "ખાતું બનાવો",
    continueGuest: "ખાતા વિના આગળ વધો",
    guestNote: "તમારા ચાર્ટ ફક્ત આ ઉપકરણ પર સાચવવામાં આવશે",
    emailAddr: "ઈ-મેઈલ સરનામું", password: "પાસવર્ડ",
    yourName: "તમારું નામ", loginSubtitle: "તમારો વ્યક્તિગત વૈદિક જ્યોતિષ માર્ગદર્શક",

    birthDetails: "જન્મ વિગતો",
    birthSubtitle: "સાચી કુંડળી માટે ચોક્કસ જન્મ વિગતો જરૂરી છે.",
    dateOfBirth: "જન્મ તારીખ", timeOfBirth: "જન્મ સમય",
    birthPlace: "જન્મ સ્થળ", gender: "લિંગ",
    genderMale: "પુરુષ", genderFemale: "સ્ત્રી", genderOther: "અન્ય",
    searchCity: "શહેર અથવા ગામ શોધો...",
    generateKundli: "કુંડળી બનાવો", generatingKundli: "કુંડળી બની રહી છે...",
    day: "દિવસ", month: "મહિનો", year: "વર્ષ",
    hour: "કલાક", minute: "મિનિટ",
    timeTip: "જન્મ સમય મહાદશાને સીધો પ્રભાવિત કરે છે. AM અથવા PM કાળજીપૂર્વક ચકાસો.",

    todayEnergy: "આજની બ્રહ્માંડ ઊર્જા", moonTransit: "ચંદ્ર ગોચર",
    currentDasha: "વર્તમાન દશા", setupKundli: "તમારી કુંડળી સેટ કરો",
    setupKundliSub: "વૈદિક ચાર્ટ બનાવવા માટે જન્મ વિગતો દાખલ કરો",
    viewAll: "બધા જુઓ", viewDetails: "વિગતો જુઓ",
    forecast: "ભવિષ્ય", today: "આજ",

    natalChart: "જન્મ કુંડળી", planets: "ગ્રહ",
    dashaTimeline: "દશા સમયરેખા", nakshatra: "નક્ષત્ર",
    ascendant: "લગ્ન", house: "ભાવ",
    noKundli: "હજી કોઈ કુંડળી નથી", noKundliSub: "બધી સુવિધાઓ અનલૉક કરવા કુંડળી સેટ કરો",
    createKundli: "કુંડળી બનાવો", chartType: "ચાર્ટ પ્રકાર",

    settings: "સેટિંગ્સ", language: "ભાષા", darkMode: "ડાર્ક મોડ",
    myProfiles: "મારી પ્રોફાઇલ", subscription: "સભ્યપદ",
    addFamilyMember: "પરિવારના સભ્ય ઉમેરો",
    addFamilySub: "દીકરો, દીકરી, જીવનસાથી, માતા-પિતા, મિત્ર અને વધુ",
    logOut: "લૉગ આઉટ", deleteAccount: "ખાતું કાઢી નાખો",
    freePlan: "મફત યોજના", upgradeNow: "હમણાં અપગ્રેડ કરો",
    selectLanguage: "ભાષા પસંદ કરો", langSubtitle: "ઍપ ભાષા તુરંત બદલાશે",
    langSearch: "ભાષા શોધો...", supported: "સમર્થિત", comingSoon: "ટૂંક સમયમાં",

    askTitle: "જ્યોતિષ AI ને પૂછો", askPlaceholder: "તમારા ચાર્ટ વિશે કંઈ પણ પૂછો...",
    askSend: "મોકલો", askSuggestions: "આ પૂછો...",

    lifeMapTitle: "લાઇફ મેપ", lifeMapSubtitle: "તારાઓ દ્વારા મેપ કરેલ જીવન",
    lifeMapRelSub: "પ્રેમ, સુસંગતતા અને બંધન", lifeMapCarSub: "વૃદ્ધિ, સફળતા અને હેતુ",
    lifeMapHealthSub: "શરીર, મન અને ઊર્જા", lifeMapFinSub: "સંપત્તિ, સ્થિરતા અને પ્રવાહ",
    lifeMapComing: "વધુ પરિમાણો આવી રહ્યા છે", lifeMapComingSub: "શિક્ષણ, મુસાફરી, અધ્યાત્મ અને વધુ",
    futureTitle: "ભવિષ્ય ટાઇમલાઇન", futureSubtitle: "આગામી 6 મહિના ડીકોડ", career: "કારકિર્દી",
    finance: "નાણાં", relationship: "સંબંધ", health: "આરોગ્ય",

    noticeTitle: "સૂચનાઓ", noNotices: "હજી કોઈ સૂચના નથી",

    errorGeneral: "કંઈ ખોટું થયું. કૃપા કરી ફરી પ્રયાસ કરો.",
    noInternet: "ઇન્ટરનેટ કનેક્શન નથી.", tryAgain: "ફરી પ્રયાસ કરો",
  },

  // ── KANNADA ─────────────────────────────────────────────────────────────────
  kn: {
    tabHome: "ಹೋಮ್", tabKundli: "ಕುಂಡಲಿ", tabAsk: "ಕೇಳಿ",
    tabLifeMap: "ಲೈಫ್ ಮ್ಯಾಪ್", tabFuture: "ಭವಿಷ್ಯ", tabNotice: "ಸೂಚನೆ", tabProfile: "ಪ್ರೊಫೈಲ್",

    save: "ಉಳಿಸಿ", cancel: "ರದ್ದು ಮಾಡಿ", skip: "ಬಿಟ್ಟುಬಿಡಿ", back: "ಹಿಂದಕ್ಕೆ",
    next: "ಮುಂದೆ", done: "ಮುಗಿಯಿತು", retry: "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ", search: "ಹುಡುಕಿ",
    loading: "ಲೋಡ್ ಆಗುತ್ತಿದೆ...", close: "ಮುಚ್ಚಿ", confirm: "ದೃಢಪಡಿಸಿ",
    delete: "ಅಳಿಸಿ", edit: "ಸಂಪಾದಿಸಿ",

    logIn: "ಲಾಗಿನ್ ಮಾಡಿ", createAccount: "ಖಾತೆ ತೆರೆಯಿರಿ",
    continueGuest: "ಖಾತೆ ಇಲ್ಲದೆ ಮುಂದುವರಿಯಿರಿ",
    guestNote: "ನಿಮ್ಮ ಚಾರ್ಟ್‌ಗಳು ಈ ಸಾಧನದಲ್ಲಿ ಮಾತ್ರ ಉಳಿಸಲಾಗುತ್ತವೆ",
    emailAddr: "ಇಮೇಲ್ ವಿಳಾಸ", password: "ಪಾಸ್‌ವರ್ಡ್",
    yourName: "ನಿಮ್ಮ ಹೆಸರು", loginSubtitle: "ನಿಮ್ಮ ವೈಯಕ್ತಿಕ ವೈದಿಕ ಜ್ಯೋತಿಷ ಮಾರ್ಗದರ್ಶಿ",

    birthDetails: "ಜನ್ಮ ವಿವರಗಳು",
    birthSubtitle: "ಸರಿಯಾದ ಕುಂಡಲಿಗಾಗಿ ನಿಖರವಾದ ಜನ್ಮ ವಿವರಗಳು ಅಗತ್ಯ.",
    dateOfBirth: "ಜನ್ಮ ದಿನಾಂಕ", timeOfBirth: "ಜನ್ಮ ಸಮಯ",
    birthPlace: "ಜನ್ಮ ಸ್ಥಳ", gender: "ಲಿಂಗ",
    genderMale: "ಪುರುಷ", genderFemale: "ಮಹಿಳೆ", genderOther: "ಇತರ",
    searchCity: "ನಗರ ಅಥವಾ ಗ್ರಾಮ ಹುಡುಕಿ...",
    generateKundli: "ಕುಂಡಲಿ ತಯಾರಿಸಿ", generatingKundli: "ಕುಂಡಲಿ ತಯಾರಾಗುತ್ತಿದೆ...",
    day: "ದಿನ", month: "ತಿಂಗಳು", year: "ವರ್ಷ",
    hour: "ಗಂಟೆ", minute: "ನಿಮಿಷ",
    timeTip: "ಜನ್ಮ ಸಮಯ ಮಹಾದಶೆಯನ್ನು ನೇರವಾಗಿ ಪ್ರಭಾವಿಸುತ್ತದೆ. AM ಅಥವಾ PM ಎಚ್ಚರಿಕೆಯಿಂದ ಪರಿಶೀಲಿಸಿ.",

    todayEnergy: "ಇಂದಿನ ಬ್ರಹ್ಮಾಂಡ ಶಕ್ತಿ", moonTransit: "ಚಂದ್ರ ಗೋಚಾರ",
    currentDasha: "ಪ್ರಸ್ತುತ ದಶೆ", setupKundli: "ನಿಮ್ಮ ಕುಂಡಲಿ ಸ್ಥಾಪಿಸಿ",
    setupKundliSub: "ನಿಮ್ಮ ವೈದಿಕ ಚಾರ್ಟ್‌ಗಾಗಿ ಜನ್ಮ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ",
    viewAll: "ಎಲ್ಲ ನೋಡಿ", viewDetails: "ವಿವರಗಳು ನೋಡಿ",
    forecast: "ಮುನ್ಸೂಚನೆ", today: "ಇಂದು",

    natalChart: "ಜನ್ಮ ಕುಂಡಲಿ", planets: "ಗ್ರಹಗಳು",
    dashaTimeline: "ದಶೆ ಸಮಯ-ರೇಖೆ", nakshatra: "ನಕ್ಷತ್ರ",
    ascendant: "ಲಗ್ನ", house: "ಭಾವ",
    noKundli: "ಕುಂಡಲಿ ಇಲ್ಲ", noKundliSub: "ಎಲ್ಲ ವೈಶಿಷ್ಟ್ಯಗಳನ್ನು ತೆರೆಯಲು ಕುಂಡಲಿ ಸ್ಥಾಪಿಸಿ",
    createKundli: "ಕುಂಡಲಿ ತಯಾರಿಸಿ", chartType: "ಚಾರ್ಟ್ ಪ್ರಕಾರ",

    settings: "ಸೆಟ್ಟಿಂಗ್ಸ್", language: "ಭಾಷೆ", darkMode: "ಡಾರ್ಕ್ ಮೋಡ್",
    myProfiles: "ನನ್ನ ಪ್ರೊಫೈಲ್‌ಗಳು", subscription: "ಚಂದಾದಾರಿಕೆ",
    addFamilyMember: "ಕುಟುಂಬ ಸದಸ್ಯ ಸೇರಿಸಿ",
    addFamilySub: "ಮಗ, ಮಗಳು, ಜೀವನಸಾಥಿ, ಪಾಲಕರು, ಸ್ನೇಹಿತ ಮತ್ತು ಇನ್ನಷ್ಟು",
    logOut: "ಲಾಗ್ ಔಟ್", deleteAccount: "ಖಾತೆ ಅಳಿಸಿ",
    freePlan: "ಉಚಿತ ಯೋಜನೆ", upgradeNow: "ಈಗ ಅಪ್‌ಗ್ರೇಡ್",
    selectLanguage: "ಭಾಷೆ ಆಯ್ಕೆ ಮಾಡಿ", langSubtitle: "ಅಪ್ಲಿಕೇಶನ್ ಭಾಷೆ ತಕ್ಷಣ ಬದಲಾಗುತ್ತದೆ",
    langSearch: "ಭಾಷೆ ಹುಡುಕಿ...", supported: "ಬೆಂಬಲಿಸಲಾಗಿದೆ", comingSoon: "ಶೀಘ್ರದಲ್ಲಿ",

    askTitle: "ಜ್ಯೋತಿಷ AI ಕೇಳಿ", askPlaceholder: "ನಿಮ್ಮ ಚಾರ್ಟ್ ಬಗ್ಗೆ ಏನಾದರೂ ಕೇಳಿ...",
    askSend: "ಕಳುಹಿಸಿ", askSuggestions: "ಕೇಳಿ ನೋಡಿ...",

    lifeMapTitle: "ಲೈಫ್ ಮ್ಯಾಪ್", lifeMapSubtitle: "ನಕ್ಷತ್ರಗಳಿಂದ ಮ್ಯಾಪ್ ಮಾಡಿದ ಜೀವನ",
    lifeMapRelSub: "ಪ್ರೀತಿ, ಹೊಂದಾಣಿಕೆ ಮತ್ತು ಬಂಧಗಳು", lifeMapCarSub: "ಬೆಳವಣಿಗೆ, ಯಶಸ್ಸು ಮತ್ತು ಉದ್ದೇಶ",
    lifeMapHealthSub: "ದೇಹ, ಮನಸ್ಸು ಮತ್ತು ಶಕ್ತಿ", lifeMapFinSub: "ಸಂಪತ್ತು, ಸ್ಥಿರತೆ ಮತ್ತು ಹರಿವು",
    lifeMapComing: "ಇನ್ನಷ್ಟು ಆಯಾಮಗಳು ಬರುತ್ತಿವೆ", lifeMapComingSub: "ಶಿಕ್ಷಣ, ಪ್ರಯಾಣ, ಆಧ್ಯಾತ್ಮಿಕತೆ ಮತ್ತು ಇನ್ನಷ್ಟು",
    futureTitle: "ಭವಿಷ್ಯ ಟೈಮ್‌ಲೈನ್", futureSubtitle: "ಮುಂದಿನ 6 ತಿಂಗಳು ಡಿಕೋಡ್", career: "ವೃತ್ತಿ",
    finance: "ಹಣಕಾಸು", relationship: "ಸಂಬಂಧ", health: "ಆರೋಗ್ಯ",

    noticeTitle: "ಸೂಚನೆಗಳು", noNotices: "ಇನ್ನೂ ಯಾವುದೇ ಸೂಚನೆಗಳಿಲ್ಲ",

    errorGeneral: "ಏನೋ ತಪ್ಪಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    noInternet: "ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಇಲ್ಲ.", tryAgain: "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ",
  },

  // ── MALAYALAM ───────────────────────────────────────────────────────────────
  ml: {
    tabHome: "ഹോം", tabKundli: "കുണ്ഡലി", tabAsk: "ചോദിക്കൂ",
    tabLifeMap: "ലൈഫ് മാപ്പ്", tabFuture: "ഭാവി", tabNotice: "അറിയിപ്പ്", tabProfile: "പ്രൊഫൈൽ",

    save: "സേവ് ചെയ്യൂ", cancel: "റദ്ദ് ചെയ്യൂ", skip: "ഒഴിവാക്കൂ", back: "തിരിക",
    next: "അടുത്തത്", done: "പൂർത്തിയായി", retry: "വീണ്ടും ശ്രമിക്കൂ", search: "തിരയൂ",
    loading: "ലോഡ് ആകുന്നു...", close: "അടക്കൂ", confirm: "ഉറപ്പാക്കൂ",
    delete: "ഇല്ലാതാക്കൂ", edit: "തിരുത്തൂ",

    logIn: "ലോഗ് ഇൻ ചെയ്യൂ", createAccount: "അക്കൗണ്ട് ഉണ്ടാക്കൂ",
    continueGuest: "അക്കൗണ്ട് ഇല്ലാതെ തുടരൂ",
    guestNote: "നിങ്ങളുടെ ചാർട്ടുകൾ ഈ ഉപകരണത്തിൽ മാത്രം സേവ് ആകും",
    emailAddr: "ഇമെയിൽ വിലാസം", password: "പാസ്‌വേഡ്",
    yourName: "നിങ്ങളുടെ പേര്", loginSubtitle: "നിങ്ങളുടെ വ്യക്തിഗത വൈദിക ജ്യോതിഷ ഗൈഡ്",

    birthDetails: "ജനന വിവരങ്ങൾ",
    birthSubtitle: "കൃത്യമായ കുണ്ഡലിക്ക് ശരിയായ ജനന വിവരങ്ങൾ ആവശ്യമാണ്.",
    dateOfBirth: "ജനനത്തീയതി", timeOfBirth: "ജനന സമയം",
    birthPlace: "ജന്മസ്ഥലം", gender: "ലിംഗം",
    genderMale: "പുരുഷൻ", genderFemale: "സ്ത്രീ", genderOther: "മറ്റുള്ളവ",
    searchCity: "നഗരം അല്ലെങ്കിൽ ഗ്രാമം തിരയൂ...",
    generateKundli: "കുണ്ഡലി ഉണ്ടാക്കൂ", generatingKundli: "കുണ്ഡലി ഉണ്ടാകുന്നു...",
    day: "ദിവസം", month: "മാസം", year: "വർഷം",
    hour: "മണിക്കൂർ", minute: "മിനിറ്റ്",
    timeTip: "ജനന സമയം മഹാദശയെ നേരിട്ട് ബാധിക്കുന്നു. AM അല്ലെങ്കിൽ PM ശ്രദ്ധയോടെ പരിശോധിക്കൂ.",

    todayEnergy: "ഇന്നത്തെ പ്രപഞ്ച ഊർജ്ജം", moonTransit: "ചന്ദ്ര ഗോചാരം",
    currentDasha: "നിലവിലെ ദശ", setupKundli: "നിങ്ങളുടെ കുണ്ഡലി സജ്ജമാക്കൂ",
    setupKundliSub: "വൈദിക ചാർട്ട് ഉണ്ടാക്കാൻ ജനന വിവരങ്ങൾ നൽകൂ",
    viewAll: "എല്ലാം കാണൂ", viewDetails: "വിവരങ്ങൾ കാണൂ",
    forecast: "പ്രവചനം", today: "ഇന്ന്",

    natalChart: "ജന്മ കുണ്ഡലി", planets: "ഗ്രഹങ്ങൾ",
    dashaTimeline: "ദശ ടൈംലൈൻ", nakshatra: "നക്ഷത്രം",
    ascendant: "ലഗ്നം", house: "ഭാവം",
    noKundli: "ഇനിയും കുണ്ഡലി ഇല്ല", noKundliSub: "എല്ലാ ഫീച്ചറുകളും അൺലോക്ക് ചെയ്യാൻ കുണ്ഡലി സജ്ജമാക്കൂ",
    createKundli: "കുണ്ഡലി ഉണ്ടാക്കൂ", chartType: "ചാർട്ട് തരം",

    settings: "ക്രമീകരണങ്ങൾ", language: "ഭാഷ", darkMode: "ഡാർക്ക് മോഡ്",
    myProfiles: "എന്റെ പ്രൊഫൈലുകൾ", subscription: "സബ്സ്ക്രിപ്ഷൻ",
    addFamilyMember: "കുടുംബ അംഗത്തെ ചേർക്കൂ",
    addFamilySub: "മകൻ, മകൾ, ജീവിതപങ്കാളി, മാതാപിതാക്കൾ, സുഹൃത്ത് മറ്റും",
    logOut: "ലോഗ് ഔട്ട്", deleteAccount: "അക്കൗണ്ട് ഇല്ലാതാക്കൂ",
    freePlan: "സൗജന്യ പ്ലാൻ", upgradeNow: "ഇപ്പോൾ അപ്‌ഗ്രേഡ് ചെയ്യൂ",
    selectLanguage: "ഭാഷ തിരഞ്ഞെടുക്കൂ", langSubtitle: "ആപ്പ് ഭാഷ ഉടൻ മാറും",
    langSearch: "ഭാഷ തിരയൂ...", supported: "പിന്തുണയ്ക്കുന്നു", comingSoon: "ഉടൻ വരുന്നു",

    askTitle: "ജ്യോതിഷ AI യോട് ചോദിക്കൂ", askPlaceholder: "നിങ്ങളുടെ ചാർട്ടിനെ കുറിച്ച് എന്തും ചോദിക്കൂ...",
    askSend: "അയക്കൂ", askSuggestions: "ഇവ ചോദിക്കൂ...",

    lifeMapTitle: "ലൈഫ് മാപ്പ്", lifeMapSubtitle: "നക്ഷത്രങ്ങളാൽ മാപ്പ് ചെയ്ത ജീവിതം",
    lifeMapRelSub: "പ്രണയം, പൊരുത്തം, ബന്ധങ്ങൾ", lifeMapCarSub: "വളർച്ച, വിജയം, ഉദ്ദേശ്യം",
    lifeMapHealthSub: "ശരീരം, മനസ്സ്, ഊർജ്ജം", lifeMapFinSub: "സമ്പത്ത്, സ്ഥിരത, പ്രവാഹം",
    lifeMapComing: "കൂടുതൽ മാനങ്ങൾ വരുന്നു", lifeMapComingSub: "വിദ്യാഭ്യാസം, യാത്ര, ആത്മീയത, കൂടുതൽ",
    futureTitle: "ഭാവി ടൈംലൈൻ", futureSubtitle: "അടുത്ത 6 മാസം ഡീകോഡ്", career: "കരിയർ",
    finance: "ധനം", relationship: "ബന്ധം", health: "ആരോഗ്യം",

    noticeTitle: "അറിയിപ്പുകൾ", noNotices: "ഇനിയും അറിയിപ്പുകൾ ഇല്ല",

    errorGeneral: "എന്തോ തെറ്റ് സംഭവിച്ചു. ദയവായി വീണ്ടും ശ്രമിക്കൂ.",
    noInternet: "ഇന്റർനെറ്റ് കണക്ഷൻ ഇല്ല.", tryAgain: "വീണ്ടും ശ്രമിക്കൂ",
  },

  // ── PUNJABI ─────────────────────────────────────────────────────────────────
  pa: {
    tabHome: "ਹੋਮ", tabKundli: "ਕੁੰਡਲੀ", tabAsk: "ਪੁੱਛੋ",
    tabLifeMap: "ਲਾਈਫ ਮੈਪ", tabFuture: "ਭਵਿੱਖ", tabNotice: "ਸੂਚਨਾ", tabProfile: "ਪ੍ਰੋਫਾਈਲ",

    save: "ਸੇਵ ਕਰੋ", cancel: "ਰੱਦ ਕਰੋ", skip: "ਛੱਡੋ", back: "ਵਾਪਸ",
    next: "ਅਗਲਾ", done: "ਹੋ ਗਿਆ", retry: "ਮੁੜ ਕੋਸ਼ਿਸ਼ ਕਰੋ", search: "ਲੱਭੋ",
    loading: "ਲੋਡ ਹੋ ਰਿਹਾ ਹੈ...", close: "ਬੰਦ ਕਰੋ", confirm: "ਪੁਸ਼ਟੀ ਕਰੋ",
    delete: "ਮਿਟਾਓ", edit: "ਸੰਪਾਦਿਤ ਕਰੋ",

    logIn: "ਲਾਗਇਨ ਕਰੋ", createAccount: "ਖਾਤਾ ਬਣਾਓ",
    continueGuest: "ਖਾਤੇ ਤੋਂ ਬਿਨਾਂ ਜਾਰੀ ਰੱਖੋ",
    guestNote: "ਤੁਹਾਡੇ ਚਾਰਟ ਸਿਰਫ਼ ਇਸ ਡਿਵਾਈਸ 'ਤੇ ਸੇਵ ਹੋਣਗੇ",
    emailAddr: "ਈਮੇਲ ਪਤਾ", password: "ਪਾਸਵਰਡ",
    yourName: "ਤੁਹਾਡਾ ਨਾਮ", loginSubtitle: "ਤੁਹਾਡਾ ਨਿੱਜੀ ਵੈਦਿਕ ਜੋਤਿਸ਼ ਗਾਈਡ",

    birthDetails: "ਜਨਮ ਵੇਰਵੇ",
    birthSubtitle: "ਸਹੀ ਕੁੰਡਲੀ ਲਈ ਸਟੀਕ ਜਨਮ ਵੇਰਵੇ ਜ਼ਰੂਰੀ ਹਨ।",
    dateOfBirth: "ਜਨਮ ਮਿਤੀ", timeOfBirth: "ਜਨਮ ਸਮਾਂ",
    birthPlace: "ਜਨਮ ਅਸਥਾਨ", gender: "ਲਿੰਗ",
    genderMale: "ਪੁਰਸ਼", genderFemale: "ਇਸਤਰੀ", genderOther: "ਹੋਰ",
    searchCity: "ਸ਼ਹਿਰ ਜਾਂ ਪਿੰਡ ਲੱਭੋ...",
    generateKundli: "ਕੁੰਡਲੀ ਬਣਾਓ", generatingKundli: "ਕੁੰਡਲੀ ਬਣ ਰਹੀ ਹੈ...",
    day: "ਦਿਨ", month: "ਮਹੀਨਾ", year: "ਸਾਲ",
    hour: "ਘੰਟਾ", minute: "ਮਿੰਟ",
    timeTip: "ਜਨਮ ਸਮਾਂ ਮਹਾਦਸ਼ਾ ਨੂੰ ਸਿੱਧੇ ਪ੍ਰਭਾਵਿਤ ਕਰਦਾ ਹੈ। AM ਜਾਂ PM ਧਿਆਨ ਨਾਲ ਜਾਂਚੋ।",

    todayEnergy: "ਅੱਜ ਦੀ ਬ੍ਰਹਿਮੰਡੀ ਊਰਜਾ", moonTransit: "ਚੰਦਰਮਾ ਗੋਚਰ",
    currentDasha: "ਮੌਜੂਦਾ ਦਸ਼ਾ", setupKundli: "ਆਪਣੀ ਕੁੰਡਲੀ ਸੈੱਟ ਕਰੋ",
    setupKundliSub: "ਵੈਦਿਕ ਚਾਰਟ ਬਣਾਉਣ ਲਈ ਜਨਮ ਵੇਰਵੇ ਦਿਓ",
    viewAll: "ਸਭ ਦੇਖੋ", viewDetails: "ਵੇਰਵੇ ਦੇਖੋ",
    forecast: "ਭਵਿੱਖਬਾਣੀ", today: "ਅੱਜ",

    natalChart: "ਜਨਮ ਕੁੰਡਲੀ", planets: "ਗ੍ਰਹਿ",
    dashaTimeline: "ਦਸ਼ਾ ਸਮਾਂਰੇਖਾ", nakshatra: "ਨਕਸ਼ੱਤਰ",
    ascendant: "ਲਗਨ", house: "ਭਾਵ",
    noKundli: "ਅਜੇ ਕੁੰਡਲੀ ਨਹੀਂ", noKundliSub: "ਸਾਰੀਆਂ ਸੁਵਿਧਾਵਾਂ ਖੋਲ੍ਹਣ ਲਈ ਕੁੰਡਲੀ ਸੈੱਟ ਕਰੋ",
    createKundli: "ਕੁੰਡਲੀ ਬਣਾਓ", chartType: "ਚਾਰਟ ਕਿਸਮ",

    settings: "ਸੈਟਿੰਗਾਂ", language: "ਭਾਸ਼ਾ", darkMode: "ਡਾਰਕ ਮੋਡ",
    myProfiles: "ਮੇਰੇ ਪ੍ਰੋਫਾਈਲ", subscription: "ਸਬਸਕ੍ਰਿਪਸ਼ਨ",
    addFamilyMember: "ਪਰਿਵਾਰਕ ਮੈਂਬਰ ਜੋੜੋ",
    addFamilySub: "ਪੁੱਤਰ, ਧੀ, ਜੀਵਨ ਸਾਥੀ, ਮਾਪੇ, ਮਿੱਤਰ ਅਤੇ ਹੋਰ",
    logOut: "ਲਾਗਆਉਟ", deleteAccount: "ਖਾਤਾ ਮਿਟਾਓ",
    freePlan: "ਮੁਫ਼ਤ ਯੋਜਨਾ", upgradeNow: "ਹੁਣੇ ਅਪਗ੍ਰੇਡ ਕਰੋ",
    selectLanguage: "ਭਾਸ਼ਾ ਚੁਣੋ", langSubtitle: "ਐਪ ਭਾਸ਼ਾ ਤੁਰੰਤ ਬਦਲ ਜਾਵੇਗੀ",
    langSearch: "ਭਾਸ਼ਾ ਲੱਭੋ...", supported: "ਸਮਰਥਿਤ", comingSoon: "ਜਲਦੀ ਆ ਰਿਹਾ ਹੈ",

    askTitle: "ਜੋਤਿਸ਼ AI ਤੋਂ ਪੁੱਛੋ", askPlaceholder: "ਆਪਣੇ ਚਾਰਟ ਬਾਰੇ ਕੁਝ ਵੀ ਪੁੱਛੋ...",
    askSend: "ਭੇਜੋ", askSuggestions: "ਇਹ ਪੁੱਛ ਕੇ ਦੇਖੋ...",

    lifeMapTitle: "ਲਾਈਫ ਮੈਪ", lifeMapSubtitle: "ਤਾਰਿਆਂ ਦੁਆਰਾ ਮੈਪ ਕੀਤੀ ਜ਼ਿੰਦਗੀ",
    lifeMapRelSub: "ਪਿਆਰ, ਅਨੁਕੂਲਤਾ ਅਤੇ ਬੰਧਨ", lifeMapCarSub: "ਵਿਕਾਸ, ਸਫਲਤਾ ਅਤੇ ਉਦੇਸ਼",
    lifeMapHealthSub: "ਸਰੀਰ, ਮਨ ਅਤੇ ਊਰਜਾ", lifeMapFinSub: "ਧਨ, ਸਥਿਰਤਾ ਅਤੇ ਪ੍ਰਵਾਹ",
    lifeMapComing: "ਹੋਰ ਆਯਾਮ ਆ ਰਹੇ ਹਨ", lifeMapComingSub: "ਸਿੱਖਿਆ, ਯਾਤਰਾ, ਅਧਿਆਤਮ ਅਤੇ ਹੋਰ",
    futureTitle: "ਭਵਿੱਖ ਟਾਈਮਲਾਈਨ", futureSubtitle: "ਅਗਲੇ 6 ਮਹੀਨੇ ਡੀਕੋਡ", career: "ਕਰੀਅਰ",
    finance: "ਵਿੱਤ", relationship: "ਸੰਬੰਧ", health: "ਸਿਹਤ",

    noticeTitle: "ਸੂਚਨਾਵਾਂ", noNotices: "ਅਜੇ ਕੋਈ ਸੂਚਨਾ ਨਹੀਂ",

    errorGeneral: "ਕੁਝ ਗਲਤ ਹੋ ਗਿਆ। ਕਿਰਪਾ ਕਰਕੇ ਮੁੜ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    noInternet: "ਇੰਟਰਨੈੱਟ ਕਨੈਕਸ਼ਨ ਨਹੀਂ।", tryAgain: "ਮੁੜ ਕੋਸ਼ਿਸ਼ ਕਰੋ",
  },

  // ── ODIA ────────────────────────────────────────────────────────────────────
  or: {
    tabHome: "ହୋମ", tabKundli: "କୁଣ୍ଡଳୀ", tabAsk: "ପଚାରନ୍ତୁ",
    tabLifeMap: "ଲାଇଫ ମ୍ୟାପ", tabFuture: "ଭବିଷ୍ୟତ", tabNotice: "ବିଜ୍ଞପ୍ତି", tabProfile: "ପ୍ରୋଫାଇଲ",

    save: "ସଂରକ୍ଷଣ କରନ୍ତୁ", cancel: "ବାତିଲ କରନ୍ତୁ", skip: "ଛାଡ଼ନ୍ତୁ", back: "ପଛକୁ",
    next: "ପରବର୍ତ୍ତୀ", done: "ସଂପୂର୍ଣ୍ଣ", retry: "ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ", search: "ଖୋଜନ୍ତୁ",
    loading: "ଲୋଡ ହେଉଛି...", close: "ବନ୍ଦ କରନ୍ତୁ", confirm: "ନିଶ୍ଚିତ କରନ୍ତୁ",
    delete: "ଲିଭାନ୍ତୁ", edit: "ସମ୍ପାଦନ କରନ୍ତୁ",

    logIn: "ଲଗ ଇନ କରନ୍ତୁ", createAccount: "ଖାତା ତିଆରି କରନ୍ତୁ",
    continueGuest: "ଖାତା ବିନା ଜାରି ରଖନ୍ତୁ",
    guestNote: "ଆପଣଙ୍କ ଚାର୍ଟ ଏହି ଡିଭାଇସ୍‌ରେ ଯୋଡ଼ାଯିବ",
    emailAddr: "ଇମେଲ ଠିକଣା", password: "ପାସୱାର୍ଡ",
    yourName: "ଆପଣଙ୍କ ନାମ", loginSubtitle: "ଆପଣଙ୍କ ବ୍ୟକ୍ତିଗତ ବୈଦିକ ଜ୍ୟୋତିଷ ଗାଇଡ",

    birthDetails: "ଜନ୍ମ ବିବରଣୀ",
    birthSubtitle: "ସଠିକ ଜ୍ୟୋତିଷ ଫଳ ପାଇଁ ସଠିକ ଜନ୍ମ ବିବରଣୀ ଆବଶ୍ୟକ।",
    dateOfBirth: "ଜନ୍ମ ତାରିଖ", timeOfBirth: "ଜନ୍ମ ସମୟ",
    birthPlace: "ଜନ୍ମ ସ୍ଥାନ", gender: "ଲିଙ୍ଗ",
    genderMale: "ପୁରୁଷ", genderFemale: "ମହିଳା", genderOther: "ଅନ୍ୟ",
    searchCity: "ସହର ବା ଗ୍ରାମ ଖୋଜନ୍ତୁ...",
    generateKundli: "କୁଣ୍ଡଳୀ ତିଆରି କରନ୍ତୁ", generatingKundli: "କୁଣ୍ଡଳୀ ତିଆରି ହେଉଛି...",
    day: "ଦିନ", month: "ମାସ", year: "ବର୍ଷ",
    hour: "ଘଣ୍ଟା", minute: "ମିନିଟ",
    timeTip: "ଜନ୍ମ ସମୟ ମହାଦଶାକୁ ସିଧା ପ୍ରଭାବିତ କରେ। AM ବା PM ଧ୍ୟାନ ଦେଇ ଯାଞ୍ଚ କରନ୍ତୁ।",

    todayEnergy: "ଆଜର ବ୍ରହ୍ମାଣ୍ଡ ଶକ୍ତି", moonTransit: "ଚନ୍ଦ୍ର ଗୋଚର",
    currentDasha: "ବର୍ତ୍ତମାନ ଦଶା", setupKundli: "ଆପଣଙ୍କ କୁଣ୍ଡଳୀ ଯୋଡ଼ନ୍ତୁ",
    setupKundliSub: "ବୈଦିକ ଚାର୍ଟ ପ୍ରସ୍ତୁତ କରିବା ପାଇଁ ଜନ୍ମ ବିବରଣୀ ଦିଅନ୍ତୁ",
    viewAll: "ସବୁ ଦେଖନ୍ତୁ", viewDetails: "ବିବରଣୀ ଦେଖନ୍ତୁ",
    forecast: "ଭବିଷ୍ୟବାଣୀ", today: "ଆଜି",

    natalChart: "ଜନ୍ମ କୁଣ୍ଡଳୀ", planets: "ଗ୍ରହ",
    dashaTimeline: "ଦଶା ସମୟ-ରେଖା", nakshatra: "ନକ୍ଷତ୍ର",
    ascendant: "ଲଗ୍ନ", house: "ଭାବ",
    noKundli: "ଏ ପର୍ଯ୍ୟନ୍ତ କୁଣ୍ଡଳୀ ନାହିଁ", noKundliSub: "ସମସ୍ତ ସୁବିଧା ପାଇଁ କୁଣ୍ଡଳୀ ଯୋଡ଼ନ୍ତୁ",
    createKundli: "କୁଣ୍ଡଳୀ ତିଆରି କରନ୍ତୁ", chartType: "ଚାର୍ଟ ପ୍ରକାର",

    settings: "ସେଟିଂସ", language: "ଭାଷା", darkMode: "ଡାର୍କ ମୋଡ",
    myProfiles: "ମୋ ପ୍ରୋଫାଇଲ", subscription: "ସଦସ୍ୟତା",
    addFamilyMember: "ପରିବାର ସଦସ୍ୟ ଯୋଡ଼ନ୍ତୁ",
    addFamilySub: "ପୁଅ, ଝିଅ, ଜୀବନ ସଙ୍ଗୀ, ଅଭିଭାବକ, ବନ୍ଧୁ ଓ ଆହୁରି",
    logOut: "ଲଗ ଆଉଟ", deleteAccount: "ଖାତା ଲିଭାନ୍ତୁ",
    freePlan: "ମାଗଣା ଯୋଜନା", upgradeNow: "ଏବେ ଅପଗ୍ରେଡ କରନ୍ତୁ",
    selectLanguage: "ଭାଷା ବାଛନ୍ତୁ", langSubtitle: "ଆପ ଭାଷା ତୁରନ୍ତ ବଦଳିବ",
    langSearch: "ଭାଷା ଖୋଜନ୍ତୁ...", supported: "ସମର୍ଥିତ", comingSoon: "ଶୀଘ୍ର ଆସୁଛି",

    askTitle: "ଜ୍ୟୋତିଷ AI କୁ ପଚାରନ୍ତୁ", askPlaceholder: "ଆପଣଙ୍କ ଚାର୍ଟ ବିଷୟରେ ଯାହା ଚାହୁଁଛି ପଚାରନ୍ତୁ...",
    askSend: "ପଠାନ୍ତୁ", askSuggestions: "ଏହା ପଚାରନ୍ତୁ...",

    lifeMapTitle: "ଲାଇଫ ମ୍ୟାପ", lifeMapSubtitle: "ତାରାମାନଙ୍କ ଦ୍ୱାରା ମ୍ୟାପ କରାଯାଇଥିବା ଜୀବନ",
    lifeMapRelSub: "ପ୍ରେମ, ସୁସଙ୍ଗତତା ଏବଂ ବନ୍ଧନ", lifeMapCarSub: "ଅଭିବୃଦ୍ଧି, ସଫଳତା ଏବଂ ଉଦ୍ଦେଶ୍ୟ",
    lifeMapHealthSub: "ଶରୀର, ମନ ଏବଂ ଶକ୍ତି", lifeMapFinSub: "ସମ୍ପଦ, ସ୍ଥିରତା ଏବଂ ପ୍ରବାହ",
    lifeMapComing: "ଅଧିକ ମାତ୍ରା ଆସୁଛି", lifeMapComingSub: "ଶିକ୍ଷା, ଯାତ୍ରା, ଅଧ୍ୟାତ୍ମ ଏବଂ ଅଧିକ",
    futureTitle: "ଭବିଷ୍ୟତ ଟାଇମଲାଇନ", futureSubtitle: "ଆଗାମୀ 6 ମାସ ଡିକୋଡ", career: "କ୍ୟାରିୟର",
    finance: "ଅର୍ଥ", relationship: "ସମ୍ପର୍କ", health: "ସ୍ବାସ୍ଥ୍ୟ",

    noticeTitle: "ବିଜ୍ଞପ୍ତି", noNotices: "ଏ ପର୍ଯ୍ୟନ୍ତ କୌଣସି ବିଜ୍ଞପ୍ତି ନାହିଁ",

    errorGeneral: "କିଛି ଭୁଲ ହୋଇଗଲା। ଦୟାକରି ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ।",
    noInternet: "ଇଣ୍ଟରନେଟ ସଂଯୋଗ ନାହିଁ।", tryAgain: "ପୁଣି ଚେଷ୍ଟା କରନ୍ତୁ",
  },

  // ── ASSAMESE ────────────────────────────────────────────────────────────────
  as: {
    tabHome: "হোম", tabKundli: "কুণ্ডলী", tabAsk: "সুধক",
    tabLifeMap: "লাইফ ম্যাপ", tabLifeMap: "লাইফ মেপ", tabFuture: "ভবিষ্যৎ", tabNotice: "জাননী", tabProfile: "প্ৰফাইল",

    save: "সংৰক্ষণ কৰক", cancel: "বাতিল কৰক", skip: "এৰক", back: "পিছলৈ",
    next: "পৰৱৰ্তী", done: "সম্পূৰ্ণ", retry: "পুনৰ চেষ্টা কৰক", search: "বিচাৰক",
    loading: "লোড হৈছে...", close: "বন্ধ কৰক", confirm: "নিশ্চিত কৰক",
    delete: "মচক", edit: "সম্পাদনা কৰক",

    logIn: "লগ ইন কৰক", createAccount: "একাউণ্ট বনাওক",
    continueGuest: "একাউণ্ট নোহোৱাকৈ আগবাঢ়ক",
    guestNote: "আপোনাৰ চাৰ্টসমূহ কেৱল এই ডিভাইচত সংৰক্ষিত হ'ব",
    emailAddr: "ইমেইল ঠিকনা", password: "পাছৱৰ্ড",
    yourName: "আপোনাৰ নাম", loginSubtitle: "আপোনাৰ ব্যক্তিগত বৈদিক জ্যোতিষ গাইড",

    birthDetails: "জন্ম বিৱৰণ",
    birthSubtitle: "সঠিক কুণ্ডলীৰ বাবে সঠিক জন্ম বিৱৰণ প্ৰয়োজন।",
    dateOfBirth: "জন্ম তাৰিখ", timeOfBirth: "জন্ম সময়",
    birthPlace: "জন্মস্থান", gender: "লিংগ",
    genderMale: "পুৰুষ", genderFemale: "মহিলা", genderOther: "অন্যান্য",
    searchCity: "চহৰ বা গাঁও বিচাৰক...",
    generateKundli: "কুণ্ডলী তৈয়াৰ কৰক", generatingKundli: "কুণ্ডলী তৈয়াৰ হৈছে...",
    day: "দিন", month: "মাহ", year: "বছৰ",
    hour: "ঘণ্টা", minute: "মিনিট",
    timeTip: "জন্ম সময়ে মহাদশাক পোনপটীয়াকৈ প্ৰভাৱিত কৰে। AM বা PM সাৱধানে পৰীক্ষা কৰক।",

    todayEnergy: "আজিৰ ব্ৰহ্মাণ্ডীয় শক্তি", moonTransit: "চন্দ্ৰ গোচৰ",
    currentDasha: "বৰ্তমান দশা", setupKundli: "আপোনাৰ কুণ্ডলী স্থাপন কৰক",
    setupKundliSub: "বৈদিক চাৰ্ট তৈয়াৰৰ বাবে জন্ম বিৱৰণ দিয়ক",
    viewAll: "সকলো চাওক", viewDetails: "বিৱৰণ চাওক",
    forecast: "ভৱিষ্যদ্বাণী", today: "আজি",

    natalChart: "জন্ম কুণ্ডলী", planets: "গ্ৰহ",
    dashaTimeline: "দশা সময়ৰেখা", nakshatra: "নক্ষত্ৰ",
    ascendant: "লগ্ন", house: "ভাব",
    noKundli: "এতিয়ালৈকে কোনো কুণ্ডলী নাই", noKundliSub: "সকলো সুবিধা আনলক কৰিবলৈ কুণ্ডলী স্থাপন কৰক",
    createKundli: "কুণ্ডলী তৈয়াৰ কৰক", chartType: "চাৰ্টৰ ধৰণ",

    settings: "ছেটিংছ", language: "ভাষা", darkMode: "ডাৰ্ক মোড",
    myProfiles: "মোৰ প্ৰফাইলসমূহ", subscription: "চাবস্ক্ৰিপচন",
    addFamilyMember: "পৰিয়ালৰ সদস্য যোগ কৰক",
    addFamilySub: "পুত্ৰ, কন্যা, জীৱনসঙ্গী, অভিভাৱক, বন্ধু আৰু আৰু",
    logOut: "লগ আউট", deleteAccount: "একাউণ্ট মচক",
    freePlan: "বিনামূলীয়া পৰিকল্পনা", upgradeNow: "এতিয়াই আপগ্ৰেড কৰক",
    selectLanguage: "ভাষা বাছক", langSubtitle: "এপৰ ভাষা লগে লগে সলনি হ'ব",
    langSearch: "ভাষা বিচাৰক...", supported: "সমৰ্থিত", comingSoon: "সোনকালে আহিছে",

    askTitle: "জ্যোতিষ AI ক সুধক", askPlaceholder: "আপোনাৰ চাৰ্টৰ বিষয়ে যি মন যায় সুধক...",
    askSend: "পঠাওক", askSuggestions: "এইবোৰ সুধক...",

    lifeMapTitle: "লাইফ মেপ", lifeMapSubtitle: "তৰাৰ দ্বাৰা মেপ কৰা জীৱন",
    lifeMapRelSub: "প্ৰেম, সুসঙ্গতা আৰু বন্ধন", lifeMapCarSub: "বিকাশ, সাফল্য আৰু উদ্দেশ্য",
    lifeMapHealthSub: "শৰীৰ, মন আৰু শক্তি", lifeMapFinSub: "সম্পদ, স্থিৰতা আৰু প্ৰবাহ",
    lifeMapComing: "অধিক মাত্ৰা আহি আছে", lifeMapComingSub: "শিক্ষা, ভ্ৰমণ, আধ্যাত্মিকতা আৰু অধিক",
    futureTitle: "ভৱিষ্যত টাইমলাইন", futureSubtitle: "পৰৱৰ্তী ৬ মাহ ডিকোড", career: "কেৰিয়াৰ",
    finance: "বিত্ত", relationship: "সম্পৰ্ক", health: "স্বাস্থ্য",

    noticeTitle: "জাননী", noNotices: "এতিয়ালৈকে কোনো জাননী নাই",

    errorGeneral: "কিবা এটা ভুল হ'ল। অনুগ্ৰহ কৰি পুনৰ চেষ্টা কৰক।",
    noInternet: "ইণ্টাৰনেট সংযোগ নাই।", tryAgain: "পুনৰ চেষ্টা কৰক",
  },

  // ── CHINESE SIMPLIFIED ───────────────────────────────────────────────────────
  zh: {
    tabHome: "首页", tabKundli: "星盘", tabAsk: "咨询",
    tabLifeMap: "生命地图", tabLifeMap: "ライフマップ", tabFuture: "未来", tabNotice: "通知", tabProfile: "我的",

    save: "保存", cancel: "取消", skip: "跳过", back: "返回",
    next: "下一步", done: "完成", retry: "重试", search: "搜索",
    loading: "加载中...", close: "关闭", confirm: "确认",
    delete: "删除", edit: "编辑",

    logIn: "登录", createAccount: "注册账号",
    continueGuest: "游客模式",
    guestNote: "您的星盘仅保存在此设备上",
    emailAddr: "电子邮件", password: "密码",
    yourName: "您的姓名", loginSubtitle: "您的个人吠陀占星指南",

    birthDetails: "出生信息",
    birthSubtitle: "准确的出生信息是生成正确星盘的必要条件。",
    dateOfBirth: "出生日期", timeOfBirth: "出生时间",
    birthPlace: "出生地", gender: "性别",
    genderMale: "男", genderFemale: "女", genderOther: "其他",
    searchCity: "搜索城市或乡村...",
    generateKundli: "生成星盘", generatingKundli: "生成中...",
    day: "日", month: "月", year: "年",
    hour: "时", minute: "分",
    timeTip: "出生时间直接影响大运。请仔细核实 AM 或 PM。",

    todayEnergy: "今日宇宙能量", moonTransit: "月亮过境",
    currentDasha: "当前大运", setupKundli: "设置您的星盘",
    setupKundliSub: "输入出生信息生成吠陀星盘",
    viewAll: "查看全部", viewDetails: "查看详情",
    forecast: "运势预测", today: "今天",

    natalChart: "本命盘", planets: "行星",
    dashaTimeline: "大运时间线", nakshatra: "月宿",
    ascendant: "上升星座", house: "宫",
    noKundli: "尚无星盘", noKundliSub: "设置出生星盘以解锁所有功能",
    createKundli: "创建星盘", chartType: "星盘类型",

    settings: "设置", language: "语言", darkMode: "深色模式",
    myProfiles: "我的档案", subscription: "订阅",
    addFamilyMember: "添加家庭成员",
    addFamilySub: "儿子、女儿、配偶、父母、朋友等",
    logOut: "退出登录", deleteAccount: "删除账号",
    freePlan: "免费套餐", upgradeNow: "立即升级",
    selectLanguage: "选择语言", langSubtitle: "应用语言将立即更改",
    langSearch: "搜索语言...", supported: "已支持", comingSoon: "即将推出",

    askTitle: "咨询吠陀AI", askPlaceholder: "询问您星盘的任何问题...",
    askSend: "发送", askSuggestions: "试着问...",

    lifeMapTitle: "生命地图", lifeMapSubtitle: "星辰映照的人生",
    lifeMapRelSub: "爱情、缘分与羁绊", lifeMapCarSub: "成长、成功与目标",
    lifeMapHealthSub: "身体、心灵与活力", lifeMapFinSub: "财富、稳定与流通",
    lifeMapComing: "更多维度即将推出", lifeMapComingSub: "教育、旅行、灵性等",
    futureTitle: "未来时间线", futureSubtitle: "解码你的未来6个月", career: "事业",
    finance: "财务", relationship: "感情", health: "健康",

    noticeTitle: "通知", noNotices: "暂无通知",

    errorGeneral: "出现错误，请重试。", noInternet: "无网络连接。", tryAgain: "重试",
  },

  // ── SPANISH ─────────────────────────────────────────────────────────────────
  es: {
    tabHome: "Inicio", tabKundli: "Kundli", tabAsk: "Preguntar",
    tabLifeMap: "Mapa Vital", tabFuture: "Futuro", tabNotice: "Avisos", tabProfile: "Perfil",

    save: "Guardar", cancel: "Cancelar", skip: "Omitir", back: "Atrás",
    next: "Siguiente", done: "Listo", retry: "Reintentar", search: "Buscar",
    loading: "Cargando...", close: "Cerrar", confirm: "Confirmar",
    delete: "Eliminar", edit: "Editar",

    logIn: "Iniciar sesión", createAccount: "Crear cuenta",
    continueGuest: "Continuar sin cuenta",
    guestNote: "Tus cartas se guardarán solo en este dispositivo",
    emailAddr: "Correo electrónico", password: "Contraseña",
    yourName: "Tu nombre", loginSubtitle: "Tu guía personal de astrología védica",

    birthDetails: "Datos de nacimiento",
    birthSubtitle: "Los datos de nacimiento precisos son necesarios para un Kundli correcto.",
    dateOfBirth: "Fecha de nacimiento", timeOfBirth: "Hora de nacimiento",
    birthPlace: "Lugar de nacimiento", gender: "Género",
    genderMale: "Masculino", genderFemale: "Femenino", genderOther: "Otro",
    searchCity: "Buscar ciudad o pueblo...",
    generateKundli: "Generar Kundli", generatingKundli: "Generando Kundli...",
    day: "Día", month: "Mes", year: "Año",
    hour: "Hora", minute: "Minuto",
    timeTip: "La hora de nacimiento afecta directamente el Mahadasha. Verifica AM o PM cuidadosamente.",

    todayEnergy: "Energía Cósmica de Hoy", moonTransit: "Tránsito Lunar",
    currentDasha: "Dasha Actual", setupKundli: "Configura Tu Kundli",
    setupKundliSub: "Ingresa tus datos de nacimiento para generar tu carta védica",
    viewAll: "Ver todo", viewDetails: "Ver detalles",
    forecast: "Pronóstico", today: "Hoy",

    natalChart: "Carta Natal", planets: "Planetas",
    dashaTimeline: "Línea de tiempo Dasha", nakshatra: "Nakshatra",
    ascendant: "Ascendente", house: "Casa",
    noKundli: "Sin Kundli aún", noKundliSub: "Configura tu carta natal para desbloquear todas las funciones",
    createKundli: "Crear Kundli", chartType: "Tipo de carta",

    settings: "Configuración", language: "Idioma", darkMode: "Modo oscuro",
    myProfiles: "Mis perfiles", subscription: "Suscripción",
    addFamilyMember: "Agregar familiar",
    addFamilySub: "Hijo, hija, cónyuge, padres, amigo y más",
    logOut: "Cerrar sesión", deleteAccount: "Eliminar cuenta",
    freePlan: "Plan gratuito", upgradeNow: "Actualizar ahora",
    selectLanguage: "Seleccionar idioma", langSubtitle: "El idioma de la app cambiará al instante",
    langSearch: "Buscar idioma...", supported: "Compatible", comingSoon: "Próximamente",

    askTitle: "Consultar IA Jyotish", askPlaceholder: "Pregunta cualquier cosa sobre tu carta...",
    askSend: "Enviar", askSuggestions: "Intenta preguntar...",

    lifeMapTitle: "Mapa Vital", lifeMapSubtitle: "Tu vida, mapeada por las estrellas",
    lifeMapRelSub: "Amor, compatibilidad y vínculos", lifeMapCarSub: "Crecimiento, éxito y propósito",
    lifeMapHealthSub: "Cuerpo, mente y vitalidad", lifeMapFinSub: "Riqueza, estabilidad y flujo",
    lifeMapComing: "Más dimensiones próximamente", lifeMapComingSub: "Educación, Viajes, Espiritualidad y más",
    futureTitle: "Línea del Futuro", futureSubtitle: "Tus próximos 6 meses decodificados", career: "Carrera",
    finance: "Finanzas", relationship: "Relaciones", health: "Salud",

    noticeTitle: "Avisos", noNotices: "Sin avisos aún",

    errorGeneral: "Algo salió mal. Por favor, inténtalo de nuevo.",
    noInternet: "Sin conexión a internet.", tryAgain: "Intentar de nuevo",
  },

  // ── ARABIC ──────────────────────────────────────────────────────────────────
  ar: {
    tabHome: "الرئيسية", tabKundli: "الكوندلي", tabAsk: "اسأل",
    tabLifeMap: "خريطة الحياة", tabFuture: "المستقبل", tabNotice: "إشعارات", tabProfile: "الملف",

    save: "حفظ", cancel: "إلغاء", skip: "تخطي", back: "رجوع",
    next: "التالي", done: "تم", retry: "إعادة المحاولة", search: "بحث",
    loading: "جارٍ التحميل...", close: "إغلاق", confirm: "تأكيد",
    delete: "حذف", edit: "تعديل",

    logIn: "تسجيل الدخول", createAccount: "إنشاء حساب",
    continueGuest: "المتابعة بدون حساب",
    guestNote: "ستُحفظ مخططاتك على هذا الجهاز فقط",
    emailAddr: "البريد الإلكتروني", password: "كلمة المرور",
    yourName: "اسمك", loginSubtitle: "مرشدك الشخصي للتنجيم الفيدي",

    birthDetails: "تفاصيل الميلاد",
    birthSubtitle: "تفاصيل الميلاد الدقيقة ضرورية للحصول على كوندلي صحيح.",
    dateOfBirth: "تاريخ الميلاد", timeOfBirth: "وقت الميلاد",
    birthPlace: "مكان الميلاد", gender: "الجنس",
    genderMale: "ذكر", genderFemale: "أنثى", genderOther: "آخر",
    searchCity: "ابحث عن مدينة أو قرية...",
    generateKundli: "إنشاء الكوندلي", generatingKundli: "جارٍ إنشاء الكوندلي...",
    day: "يوم", month: "شهر", year: "سنة",
    hour: "ساعة", minute: "دقيقة",
    timeTip: "وقت الميلاد يؤثر مباشرة على الماهاداشا. تحقق من AM أو PM بعناية.",

    todayEnergy: "طاقة اليوم الكونية", moonTransit: "عبور القمر",
    currentDasha: "الداشا الحالية", setupKundli: "إعداد كوندليك",
    setupKundliSub: "أدخل تفاصيل ميلادك لإنشاء مخططك الفيدي",
    viewAll: "عرض الكل", viewDetails: "عرض التفاصيل",
    forecast: "التوقعات", today: "اليوم",

    natalChart: "مخطط الميلاد", planets: "الكواكب",
    dashaTimeline: "جدول زمني للداشا", nakshatra: "ناكشاترا",
    ascendant: "الطالع", house: "البيت",
    noKundli: "لا يوجد كوندلي بعد", noKundliSub: "أعد مخطط ميلادك لفتح جميع الميزات",
    createKundli: "إنشاء كوندلي", chartType: "نوع المخطط",

    settings: "الإعدادات", language: "اللغة", darkMode: "الوضع الداكن",
    myProfiles: "ملفاتي", subscription: "الاشتراك",
    addFamilyMember: "إضافة فرد من العائلة",
    addFamilySub: "ابن، ابنة، زوج/زوجة، والدان، صديق وأكثر",
    logOut: "تسجيل الخروج", deleteAccount: "حذف الحساب",
    freePlan: "الخطة المجانية", upgradeNow: "الترقية الآن",
    selectLanguage: "اختر اللغة", langSubtitle: "ستتغير لغة التطبيق فوراً",
    langSearch: "البحث عن لغة...", supported: "مدعوم", comingSoon: "قريباً",

    askTitle: "اسأل ذكاء جيوتيش", askPlaceholder: "اسأل أي شيء عن مخططك...",
    askSend: "إرسال", askSuggestions: "جرّب السؤال...",

    lifeMapTitle: "خريطة الحياة", lifeMapSubtitle: "حياتك مرسومة بالنجوم",
    lifeMapRelSub: "الحب والتوافق والروابط", lifeMapCarSub: "النمو والنجاح والهدف",
    lifeMapHealthSub: "الجسم والعقل والحيوية", lifeMapFinSub: "الثروة والاستقرار والتدفق",
    lifeMapComing: "المزيد من الأبعاد قادمة", lifeMapComingSub: "التعليم والسفر والروحانية والمزيد",
    futureTitle: "الجدول الزمني للمستقبل", futureSubtitle: "فك شفرة الأشهر الستة القادمة", career: "المسيرة المهنية",
    finance: "المالية", relationship: "العلاقات", health: "الصحة",

    noticeTitle: "الإشعارات", noNotices: "لا توجد إشعارات بعد",

    errorGeneral: "حدث خطأ ما. يرجى المحاولة مرة أخرى.",
    noInternet: "لا يوجد اتصال بالإنترنت.", tryAgain: "حاول مجدداً",
  },

  // ── FRENCH ──────────────────────────────────────────────────────────────────
  fr: {
    tabHome: "Accueil", tabKundli: "Kundli", tabAsk: "Demander",
    tabLifeMap: "Carte de Vie", tabFuture: "Futur", tabNotice: "Avis", tabProfile: "Profil",

    save: "Enregistrer", cancel: "Annuler", skip: "Passer", back: "Retour",
    next: "Suivant", done: "Terminé", retry: "Réessayer", search: "Rechercher",
    loading: "Chargement...", close: "Fermer", confirm: "Confirmer",
    delete: "Supprimer", edit: "Modifier",

    logIn: "Se connecter", createAccount: "Créer un compte",
    continueGuest: "Continuer sans compte",
    guestNote: "Vos thèmes seront sauvegardés uniquement sur cet appareil",
    emailAddr: "Adresse e-mail", password: "Mot de passe",
    yourName: "Votre nom", loginSubtitle: "Votre guide personnel d'astrologie védique",

    birthDetails: "Données de naissance",
    birthSubtitle: "Des données de naissance précises sont nécessaires pour un Kundli correct.",
    dateOfBirth: "Date de naissance", timeOfBirth: "Heure de naissance",
    birthPlace: "Lieu de naissance", gender: "Genre",
    genderMale: "Masculin", genderFemale: "Féminin", genderOther: "Autre",
    searchCity: "Rechercher une ville ou un village...",
    generateKundli: "Générer le Kundli", generatingKundli: "Génération du Kundli...",
    day: "Jour", month: "Mois", year: "Année",
    hour: "Heure", minute: "Minute",
    timeTip: "L'heure de naissance affecte directement le Mahadasha. Vérifiez soigneusement AM ou PM.",

    todayEnergy: "Énergie Cosmique du Jour", moonTransit: "Transit Lunaire",
    currentDasha: "Dasha Actuel", setupKundli: "Configurer Votre Kundli",
    setupKundliSub: "Entrez vos données de naissance pour générer votre thème védique",
    viewAll: "Voir tout", viewDetails: "Voir les détails",
    forecast: "Prévisions", today: "Aujourd'hui",

    natalChart: "Thème natal", planets: "Planètes",
    dashaTimeline: "Chronologie Dasha", nakshatra: "Nakshatra",
    ascendant: "Ascendant", house: "Maison",
    noKundli: "Pas encore de Kundli", noKundliSub: "Configurez votre thème natal pour débloquer toutes les fonctionnalités",
    createKundli: "Créer le Kundli", chartType: "Type de thème",

    settings: "Paramètres", language: "Langue", darkMode: "Mode sombre",
    myProfiles: "Mes profils", subscription: "Abonnement",
    addFamilyMember: "Ajouter un membre de la famille",
    addFamilySub: "Fils, fille, conjoint, parents, ami et plus",
    logOut: "Se déconnecter", deleteAccount: "Supprimer le compte",
    freePlan: "Plan gratuit", upgradeNow: "Mettre à niveau maintenant",
    selectLanguage: "Sélectionner la langue", langSubtitle: "La langue de l'app changera instantanément",
    langSearch: "Rechercher une langue...", supported: "Pris en charge", comingSoon: "Bientôt disponible",

    askTitle: "Consulter l'IA Jyotish", askPlaceholder: "Posez n'importe quelle question sur votre thème...",
    askSend: "Envoyer", askSuggestions: "Essayez de demander...",

    lifeMapTitle: "Carte de Vie", lifeMapSubtitle: "Votre vie, cartographiée par les étoiles",
    lifeMapRelSub: "Amour, compatibilité et liens", lifeMapCarSub: "Croissance, succès et objectif",
    lifeMapHealthSub: "Corps, esprit et vitalité", lifeMapFinSub: "Richesse, stabilité et flux",
    lifeMapComing: "Plus de dimensions à venir", lifeMapComingSub: "Éducation, Voyages, Spiritualité et plus",
    futureTitle: "Chronologie Future", futureSubtitle: "Vos 6 prochains mois décodés", career: "Carrière",
    finance: "Finances", relationship: "Relations", health: "Santé",

    noticeTitle: "Avis", noNotices: "Pas encore d'avis",

    errorGeneral: "Quelque chose s'est mal passé. Veuillez réessayer.",
    noInternet: "Pas de connexion internet.", tryAgain: "Réessayer",
  },

  // ── PORTUGUESE ──────────────────────────────────────────────────────────────
  pt: {
    tabHome: "Início", tabKundli: "Kundli", tabAsk: "Perguntar",
    tabLifeMap: "Mapa da Vida", tabFuture: "Futuro", tabNotice: "Avisos", tabProfile: "Perfil",

    save: "Salvar", cancel: "Cancelar", skip: "Pular", back: "Voltar",
    next: "Próximo", done: "Concluído", retry: "Tentar novamente", search: "Pesquisar",
    loading: "Carregando...", close: "Fechar", confirm: "Confirmar",
    delete: "Excluir", edit: "Editar",

    logIn: "Entrar", createAccount: "Criar conta",
    continueGuest: "Continuar sem conta",
    guestNote: "Seus mapas serão salvos apenas neste dispositivo",
    emailAddr: "Endereço de e-mail", password: "Senha",
    yourName: "Seu nome", loginSubtitle: "Seu guia pessoal de astrologia védica",

    birthDetails: "Dados de nascimento",
    birthSubtitle: "Dados de nascimento precisos são necessários para um Kundli correto.",
    dateOfBirth: "Data de nascimento", timeOfBirth: "Hora de nascimento",
    birthPlace: "Local de nascimento", gender: "Gênero",
    genderMale: "Masculino", genderFemale: "Feminino", genderOther: "Outro",
    searchCity: "Pesquisar cidade ou aldeia...",
    generateKundli: "Gerar Kundli", generatingKundli: "Gerando Kundli...",
    day: "Dia", month: "Mês", year: "Ano",
    hour: "Hora", minute: "Minuto",
    timeTip: "O horário de nascimento afeta diretamente o Mahadasha. Verifique AM ou PM com cuidado.",

    todayEnergy: "Energia Cósmica de Hoje", moonTransit: "Trânsito Lunar",
    currentDasha: "Dasha Atual", setupKundli: "Configure Seu Kundli",
    setupKundliSub: "Insira seus dados de nascimento para gerar seu mapa védico",
    viewAll: "Ver tudo", viewDetails: "Ver detalhes",
    forecast: "Previsão", today: "Hoje",

    natalChart: "Mapa natal", planets: "Planetas",
    dashaTimeline: "Linha do tempo Dasha", nakshatra: "Nakshatra",
    ascendant: "Ascendente", house: "Casa",
    noKundli: "Sem Kundli ainda", noKundliSub: "Configure seu mapa natal para desbloquear todos os recursos",
    createKundli: "Criar Kundli", chartType: "Tipo de mapa",

    settings: "Configurações", language: "Idioma", darkMode: "Modo escuro",
    myProfiles: "Meus perfis", subscription: "Assinatura",
    addFamilyMember: "Adicionar familiar",
    addFamilySub: "Filho, filha, cônjuge, pais, amigo e mais",
    logOut: "Sair", deleteAccount: "Excluir conta",
    freePlan: "Plano gratuito", upgradeNow: "Atualizar agora",
    selectLanguage: "Selecionar idioma", langSubtitle: "O idioma do app mudará instantaneamente",
    langSearch: "Pesquisar idioma...", supported: "Suportado", comingSoon: "Em breve",

    askTitle: "Consultar IA Jyotish", askPlaceholder: "Pergunte qualquer coisa sobre seu mapa...",
    askSend: "Enviar", askSuggestions: "Tente perguntar...",

    lifeMapTitle: "Mapa da Vida", lifeMapSubtitle: "Sua vida, mapeada pelas estrelas",
    lifeMapRelSub: "Amor, compatibilidade e vínculos", lifeMapCarSub: "Crescimento, sucesso e propósito",
    lifeMapHealthSub: "Corpo, mente e vitalidade", lifeMapFinSub: "Riqueza, estabilidade e fluxo",
    lifeMapComing: "Mais dimensões em breve", lifeMapComingSub: "Educação, Viagens, Espiritualidade e mais",
    futureTitle: "Linha do Futuro", futureSubtitle: "Seus próximos 6 meses decodificados", career: "Carreira",
    finance: "Finanças", relationship: "Relacionamentos", health: "Saúde",

    noticeTitle: "Avisos", noNotices: "Sem avisos ainda",

    errorGeneral: "Algo deu errado. Por favor, tente novamente.",
    noInternet: "Sem conexão com a internet.", tryAgain: "Tentar novamente",
  },

  // ── GERMAN ──────────────────────────────────────────────────────────────────
  de: {
    tabHome: "Start", tabKundli: "Kundli", tabAsk: "Fragen",
    tabLifeMap: "Lebenskarte", tabFuture: "Zukunft", tabNotice: "Hinweise", tabProfile: "Profil",

    save: "Speichern", cancel: "Abbrechen", skip: "Überspringen", back: "Zurück",
    next: "Weiter", done: "Fertig", retry: "Wiederholen", search: "Suchen",
    loading: "Laden...", close: "Schließen", confirm: "Bestätigen",
    delete: "Löschen", edit: "Bearbeiten",

    logIn: "Anmelden", createAccount: "Konto erstellen",
    continueGuest: "Ohne Konto fortfahren",
    guestNote: "Ihre Horoskope werden nur auf diesem Gerät gespeichert",
    emailAddr: "E-Mail-Adresse", password: "Passwort",
    yourName: "Ihr Name", loginSubtitle: "Ihr persönlicher vedischer Astrologieführer",

    birthDetails: "Geburtsdaten",
    birthSubtitle: "Genaue Geburtsdaten sind für ein korrektes Kundli erforderlich.",
    dateOfBirth: "Geburtsdatum", timeOfBirth: "Geburtszeit",
    birthPlace: "Geburtsort", gender: "Geschlecht",
    genderMale: "Männlich", genderFemale: "Weiblich", genderOther: "Divers",
    searchCity: "Stadt oder Dorf suchen...",
    generateKundli: "Kundli generieren", generatingKundli: "Kundli wird generiert...",
    day: "Tag", month: "Monat", year: "Jahr",
    hour: "Stunde", minute: "Minute",
    timeTip: "Die Geburtszeit beeinflusst direkt das Mahadasha. Bitte AM oder PM sorgfältig prüfen.",

    todayEnergy: "Heutige Kosmische Energie", moonTransit: "Mondtransit",
    currentDasha: "Aktuelles Dasha", setupKundli: "Ihr Kundli einrichten",
    setupKundliSub: "Geben Sie Ihre Geburtsdaten ein, um Ihr vedisches Horoskop zu erstellen",
    viewAll: "Alle anzeigen", viewDetails: "Details anzeigen",
    forecast: "Vorhersage", today: "Heute",

    natalChart: "Geburtshoroskop", planets: "Planeten",
    dashaTimeline: "Dasha-Zeitlinie", nakshatra: "Nakshatra",
    ascendant: "Aszendent", house: "Haus",
    noKundli: "Noch kein Kundli", noKundliSub: "Richten Sie Ihr Geburtshoroskop ein, um alle Funktionen freizuschalten",
    createKundli: "Kundli erstellen", chartType: "Horoskop-Typ",

    settings: "Einstellungen", language: "Sprache", darkMode: "Dunkler Modus",
    myProfiles: "Meine Profile", subscription: "Abonnement",
    addFamilyMember: "Familienmitglied hinzufügen",
    addFamilySub: "Sohn, Tochter, Partner, Eltern, Freund und mehr",
    logOut: "Abmelden", deleteAccount: "Konto löschen",
    freePlan: "Kostenloser Plan", upgradeNow: "Jetzt upgraden",
    selectLanguage: "Sprache auswählen", langSubtitle: "Die App-Sprache ändert sich sofort",
    langSearch: "Sprache suchen...", supported: "Unterstützt", comingSoon: "Demnächst",

    askTitle: "Jyotish KI fragen", askPlaceholder: "Stellen Sie Fragen zu Ihrem Horoskop...",
    askSend: "Senden", askSuggestions: "Versuchen Sie zu fragen...",

    lifeMapTitle: "Lebenskarte", lifeMapSubtitle: "Dein Leben, kartiert von den Sternen",
    lifeMapRelSub: "Liebe, Kompatibilität und Bindungen", lifeMapCarSub: "Wachstum, Erfolg und Zweck",
    lifeMapHealthSub: "Körper, Geist und Vitalität", lifeMapFinSub: "Wohlstand, Stabilität und Fluss",
    lifeMapComing: "Weitere Dimensionen folgen", lifeMapComingSub: "Bildung, Reisen, Spiritualität und mehr",
    futureTitle: "Zukunfts-Timeline", futureSubtitle: "Deine nächsten 6 Monate entschlüsselt", career: "Karriere",
    finance: "Finanzen", relationship: "Beziehungen", health: "Gesundheit",

    noticeTitle: "Hinweise", noNotices: "Noch keine Hinweise",

    errorGeneral: "Etwas ist schiefgelaufen. Bitte versuchen Sie es erneut.",
    noInternet: "Keine Internetverbindung.", tryAgain: "Erneut versuchen",
  },

  // ── RUSSIAN ─────────────────────────────────────────────────────────────────
  ru: {
    tabHome: "Главная", tabKundli: "Кундли", tabAsk: "Спросить",
    tabLifeMap: "Карта Жизни", tabFuture: "Будущее", tabNotice: "Уведомления", tabProfile: "Профиль",

    save: "Сохранить", cancel: "Отмена", skip: "Пропустить", back: "Назад",
    next: "Далее", done: "Готово", retry: "Повторить", search: "Поиск",
    loading: "Загрузка...", close: "Закрыть", confirm: "Подтвердить",
    delete: "Удалить", edit: "Изменить",

    logIn: "Войти", createAccount: "Создать аккаунт",
    continueGuest: "Продолжить без аккаунта",
    guestNote: "Ваши карты будут сохранены только на этом устройстве",
    emailAddr: "Электронная почта", password: "Пароль",
    yourName: "Ваше имя", loginSubtitle: "Ваш личный гид по ведической астрологии",

    birthDetails: "Данные о рождении",
    birthSubtitle: "Точные данные о рождении необходимы для правильного Кундли.",
    dateOfBirth: "Дата рождения", timeOfBirth: "Время рождения",
    birthPlace: "Место рождения", gender: "Пол",
    genderMale: "Мужской", genderFemale: "Женский", genderOther: "Другой",
    searchCity: "Поиск города или деревни...",
    generateKundli: "Сгенерировать Кундли", generatingKundli: "Создание Кундли...",
    day: "День", month: "Месяц", year: "Год",
    hour: "Час", minute: "Минута",
    timeTip: "Время рождения напрямую влияет на Маhadasha. Тщательно проверьте AM или PM.",

    todayEnergy: "Космическая Энергия Сегодня", moonTransit: "Транзит Луны",
    currentDasha: "Текущая Даша", setupKundli: "Настройте Ваше Кундли",
    setupKundliSub: "Введите данные о рождении для создания вашей ведической карты",
    viewAll: "Смотреть всё", viewDetails: "Смотреть детали",
    forecast: "Прогноз", today: "Сегодня",

    natalChart: "Натальная карта", planets: "Планеты",
    dashaTimeline: "Хронология Даши", nakshatra: "Накшатра",
    ascendant: "Асцендент", house: "Дом",
    noKundli: "Кундли ещё нет", noKundliSub: "Настройте натальную карту для доступа ко всем функциям",
    createKundli: "Создать Кундли", chartType: "Тип карты",

    settings: "Настройки", language: "Язык", darkMode: "Тёмный режим",
    myProfiles: "Мои профили", subscription: "Подписка",
    addFamilyMember: "Добавить члена семьи",
    addFamilySub: "Сын, дочь, супруг(а), родители, друг и другие",
    logOut: "Выйти", deleteAccount: "Удалить аккаунт",
    freePlan: "Бесплатный план", upgradeNow: "Улучшить сейчас",
    selectLanguage: "Выбрать язык", langSubtitle: "Язык приложения изменится мгновенно",
    langSearch: "Поиск языка...", supported: "Поддерживается", comingSoon: "Скоро",

    askTitle: "Спросить ИИ Джйотиш", askPlaceholder: "Спросите что-нибудь о вашей карте...",
    askSend: "Отправить", askSuggestions: "Попробуйте спросить...",

    lifeMapTitle: "Карта Жизни", lifeMapSubtitle: "Ваша жизнь, нарисованная звёздами",
    lifeMapRelSub: "Любовь, совместимость и связи", lifeMapCarSub: "Рост, успех и цель",
    lifeMapHealthSub: "Тело, разум и энергия", lifeMapFinSub: "Богатство, стабильность и поток",
    lifeMapComing: "Больше измерений скоро", lifeMapComingSub: "Образование, Путешествия, Духовность и другое",
    futureTitle: "Хронология Будущего", futureSubtitle: "Ваши следующие 6 месяцев расшифрованы", career: "Карьера",
    finance: "Финансы", relationship: "Отношения", health: "Здоровье",

    noticeTitle: "Уведомления", noNotices: "Уведомлений пока нет",

    errorGeneral: "Что-то пошло не так. Пожалуйста, попробуйте снова.",
    noInternet: "Нет подключения к интернету.", tryAgain: "Попробовать снова",
  },

  // ── JAPANESE ────────────────────────────────────────────────────────────────
  ja: {
    tabHome: "ホーム", tabKundli: "クンドリ", tabAsk: "質問",
    tabLifeMap: "生命地图", tabLifeMap: "ライフマップ", tabFuture: "未来", tabNotice: "お知らせ", tabProfile: "プロフィール",

    save: "保存", cancel: "キャンセル", skip: "スキップ", back: "戻る",
    next: "次へ", done: "完了", retry: "再試行", search: "検索",
    loading: "読み込み中...", close: "閉じる", confirm: "確認",
    delete: "削除", edit: "編集",

    logIn: "ログイン", createAccount: "アカウント作成",
    continueGuest: "アカウントなしで続行",
    guestNote: "チャートはこのデバイスにのみ保存されます",
    emailAddr: "メールアドレス", password: "パスワード",
    yourName: "お名前", loginSubtitle: "あなたのパーソナル・ヴェーダ占星術ガイド",

    birthDetails: "生年月日情報",
    birthSubtitle: "正確なクンドリには正確な出生情報が必要です。",
    dateOfBirth: "生年月日", timeOfBirth: "出生時刻",
    birthPlace: "出生地", gender: "性別",
    genderMale: "男性", genderFemale: "女性", genderOther: "その他",
    searchCity: "都市または村を検索...",
    generateKundli: "クンドリを作成", generatingKundli: "クンドリを作成中...",
    day: "日", month: "月", year: "年",
    hour: "時", minute: "分",
    timeTip: "出生時刻はマハーダシャーに直接影響します。AM/PMを慎重に確認してください。",

    todayEnergy: "今日の宇宙エネルギー", moonTransit: "月のトランジット",
    currentDasha: "現在のダシャー", setupKundli: "クンドリの設定",
    setupKundliSub: "ヴェーダチャートを作成するために出生情報を入力してください",
    viewAll: "すべて表示", viewDetails: "詳細を表示",
    forecast: "予測", today: "今日",

    natalChart: "ネイタルチャート", planets: "惑星",
    dashaTimeline: "ダシャー年表", nakshatra: "ナクシャトラ",
    ascendant: "アセンダント", house: "ハウス",
    noKundli: "クンドリはまだありません", noKundliSub: "すべての機能を解放するためにバースチャートを設定してください",
    createKundli: "クンドリを作成", chartType: "チャートタイプ",

    settings: "設定", language: "言語", darkMode: "ダークモード",
    myProfiles: "マイプロフィール", subscription: "サブスクリプション",
    addFamilyMember: "家族を追加",
    addFamilySub: "息子、娘、配偶者、両親、友人など",
    logOut: "ログアウト", deleteAccount: "アカウントを削除",
    freePlan: "無料プラン", upgradeNow: "今すぐアップグレード",
    selectLanguage: "言語を選択", langSubtitle: "アプリの言語が即座に変更されます",
    langSearch: "言語を検索...", supported: "サポート済み", comingSoon: "近日公開",

    askTitle: "ジョーティシュAIに質問", askPlaceholder: "チャートについて何でも質問してください...",
    askSend: "送信", askSuggestions: "質問してみましょう...",

    lifeMapTitle: "ライフマップ", lifeMapSubtitle: "星に導かれた人生の地図",
    lifeMapRelSub: "愛、相性、絆", lifeMapCarSub: "成長、成功、目的",
    lifeMapHealthSub: "体、心、活力", lifeMapFinSub: "富、安定、流れ",
    lifeMapComing: "さらなる次元が近日公開", lifeMapComingSub: "教育、旅行、スピリチュアリティなど",
    futureTitle: "未来タイムライン", futureSubtitle: "次の6ヶ月を解読", career: "キャリア",
    finance: "財務", relationship: "人間関係", health: "健康",

    noticeTitle: "お知らせ", noNotices: "まだお知らせはありません",

    errorGeneral: "何か問題が発生しました。もう一度お試しください。",
    noInternet: "インターネット接続がありません。", tryAgain: "再試行",
  },

  // ── INDONESIAN ──────────────────────────────────────────────────────────────
  id: {
    tabHome: "Beranda", tabKundli: "Kundli", tabAsk: "Tanya",
    tabLifeMap: "Peta Hidup", tabFuture: "Masa Depan", tabNotice: "Pemberitahuan", tabProfile: "Profil",

    save: "Simpan", cancel: "Batal", skip: "Lewati", back: "Kembali",
    next: "Berikutnya", done: "Selesai", retry: "Coba lagi", search: "Cari",
    loading: "Memuat...", close: "Tutup", confirm: "Konfirmasi",
    delete: "Hapus", edit: "Edit",

    logIn: "Masuk", createAccount: "Buat akun",
    continueGuest: "Lanjutkan tanpa akun",
    guestNote: "Grafik Anda hanya akan disimpan di perangkat ini",
    emailAddr: "Alamat email", password: "Kata sandi",
    yourName: "Nama Anda", loginSubtitle: "Panduan astrologi Veda pribadi Anda",

    birthDetails: "Data kelahiran",
    birthSubtitle: "Data kelahiran yang akurat diperlukan untuk Kundli yang benar.",
    dateOfBirth: "Tanggal lahir", timeOfBirth: "Waktu lahir",
    birthPlace: "Tempat lahir", gender: "Jenis kelamin",
    genderMale: "Laki-laki", genderFemale: "Perempuan", genderOther: "Lainnya",
    searchCity: "Cari kota atau desa...",
    generateKundli: "Buat Kundli", generatingKundli: "Membuat Kundli...",
    day: "Hari", month: "Bulan", year: "Tahun",
    hour: "Jam", minute: "Menit",
    timeTip: "Waktu lahir secara langsung mempengaruhi Mahadasha. Periksa AM atau PM dengan hati-hati.",

    todayEnergy: "Energi Kosmik Hari Ini", moonTransit: "Transit Bulan",
    currentDasha: "Dasha Saat Ini", setupKundli: "Siapkan Kundli Anda",
    setupKundliSub: "Masukkan data kelahiran untuk membuat peta Veda Anda",
    viewAll: "Lihat semua", viewDetails: "Lihat detail",
    forecast: "Ramalan", today: "Hari ini",

    natalChart: "Peta kelahiran", planets: "Planet",
    dashaTimeline: "Garis waktu Dasha", nakshatra: "Nakshatra",
    ascendant: "Asenden", house: "Rumah",
    noKundli: "Belum ada Kundli", noKundliSub: "Siapkan peta kelahiran Anda untuk membuka semua fitur",
    createKundli: "Buat Kundli", chartType: "Jenis peta",

    settings: "Pengaturan", language: "Bahasa", darkMode: "Mode gelap",
    myProfiles: "Profil saya", subscription: "Langganan",
    addFamilyMember: "Tambah anggota keluarga",
    addFamilySub: "Putra, putri, pasangan, orang tua, teman, dan lainnya",
    logOut: "Keluar", deleteAccount: "Hapus akun",
    freePlan: "Paket gratis", upgradeNow: "Upgrade sekarang",
    selectLanguage: "Pilih bahasa", langSubtitle: "Bahasa aplikasi akan berubah seketika",
    langSearch: "Cari bahasa...", supported: "Didukung", comingSoon: "Segera hadir",

    askTitle: "Tanya AI Jyotish", askPlaceholder: "Tanyakan apa saja tentang peta Anda...",
    askSend: "Kirim", askSuggestions: "Coba tanyakan...",

    lifeMapTitle: "Peta Hidup", lifeMapSubtitle: "Hidupmu, dipetakan oleh bintang",
    lifeMapRelSub: "Cinta, kecocokan & ikatan", lifeMapCarSub: "Pertumbuhan, kesuksesan & tujuan",
    lifeMapHealthSub: "Tubuh, pikiran & vitalitas", lifeMapFinSub: "Kekayaan, stabilitas & arus",
    lifeMapComing: "Lebih banyak dimensi segera", lifeMapComingSub: "Pendidikan, Perjalanan, Spiritualitas & lainnya",
    futureTitle: "Timeline Masa Depan", futureSubtitle: "6 bulan ke depan didekode", career: "Karier",
    finance: "Keuangan", relationship: "Hubungan", health: "Kesehatan",

    noticeTitle: "Pemberitahuan", noNotices: "Belum ada pemberitahuan",

    errorGeneral: "Terjadi kesalahan. Silakan coba lagi.",
    noInternet: "Tidak ada koneksi internet.", tryAgain: "Coba lagi",
  },

  // ── KOREAN ──────────────────────────────────────────────────────────────────
  ko: {
    tabHome: "홈", tabKundli: "쿤들리", tabAsk: "질문",
    tabLifeMap: "라이프 맵", tabFuture: "미래", tabNotice: "알림", tabProfile: "프로필",

    save: "저장", cancel: "취소", skip: "건너뛰기", back: "뒤로",
    next: "다음", done: "완료", retry: "다시 시도", search: "검색",
    loading: "로딩 중...", close: "닫기", confirm: "확인",
    delete: "삭제", edit: "편집",

    logIn: "로그인", createAccount: "계정 만들기",
    continueGuest: "계정 없이 계속하기",
    guestNote: "차트는 이 기기에만 저장됩니다",
    emailAddr: "이메일 주소", password: "비밀번호",
    yourName: "이름", loginSubtitle: "개인 베다 점성술 가이드",

    birthDetails: "출생 정보",
    birthSubtitle: "정확한 쿤들리를 위해 정확한 출생 정보가 필요합니다.",
    dateOfBirth: "생년월일", timeOfBirth: "출생 시간",
    birthPlace: "출생지", gender: "성별",
    genderMale: "남성", genderFemale: "여성", genderOther: "기타",
    searchCity: "도시 또는 마을 검색...",
    generateKundli: "쿤들리 생성", generatingKundli: "쿤들리 생성 중...",
    day: "일", month: "월", year: "년",
    hour: "시", minute: "분",
    timeTip: "출생 시간은 마하다샤에 직접 영향을 줍니다. AM 또는 PM을 주의 깊게 확인하세요.",

    todayEnergy: "오늘의 우주 에너지", moonTransit: "달의 이동",
    currentDasha: "현재 다샤", setupKundli: "쿤들리 설정",
    setupKundliSub: "베다 차트 생성을 위해 출생 정보를 입력하세요",
    viewAll: "전체 보기", viewDetails: "상세 보기",
    forecast: "예측", today: "오늘",

    natalChart: "출생 차트", planets: "행성",
    dashaTimeline: "다샤 타임라인", nakshatra: "낙샤트라",
    ascendant: "어센던트", house: "하우스",
    noKundli: "아직 쿤들리 없음", noKundliSub: "모든 기능을 잠금 해제하려면 출생 차트를 설정하세요",
    createKundli: "쿤들리 만들기", chartType: "차트 유형",

    settings: "설정", language: "언어", darkMode: "다크 모드",
    myProfiles: "내 프로필", subscription: "구독",
    addFamilyMember: "가족 구성원 추가",
    addFamilySub: "아들, 딸, 배우자, 부모, 친구 등",
    logOut: "로그아웃", deleteAccount: "계정 삭제",
    freePlan: "무료 플랜", upgradeNow: "지금 업그레이드",
    selectLanguage: "언어 선택", langSubtitle: "앱 언어가 즉시 변경됩니다",
    langSearch: "언어 검색...", supported: "지원됨", comingSoon: "출시 예정",

    askTitle: "조티시 AI에게 질문", askPlaceholder: "차트에 대해 무엇이든 물어보세요...",
    askSend: "보내기", askSuggestions: "물어보세요...",

    lifeMapTitle: "라이프 맵", lifeMapSubtitle: "별이 그린 당신의 삶",
    lifeMapRelSub: "사랑, 호환성, 유대", lifeMapCarSub: "성장, 성공, 목적",
    lifeMapHealthSub: "몸, 마음, 활력", lifeMapFinSub: "부, 안정, 흐름",
    lifeMapComing: "더 많은 차원이 곧 공개됩니다", lifeMapComingSub: "교육, 여행, 영성 등",
    futureTitle: "미래 타임라인", futureSubtitle: "다음 6개월 해독", career: "커리어",
    finance: "재무", relationship: "관계", health: "건강",

    noticeTitle: "알림", noNotices: "알림이 아직 없습니다",

    errorGeneral: "문제가 발생했습니다. 다시 시도해 주세요.",
    noInternet: "인터넷 연결이 없습니다.", tryAgain: "다시 시도",
  },

  // ── TURKISH ─────────────────────────────────────────────────────────────────
  tr: {
    tabHome: "Ana Sayfa", tabKundli: "Kundli", tabAsk: "Sor",
    tabLifeMap: "Yaşam Haritası", tabFuture: "Gelecek", tabNotice: "Bildirimler", tabProfile: "Profil",

    save: "Kaydet", cancel: "İptal", skip: "Atla", back: "Geri",
    next: "İleri", done: "Bitti", retry: "Tekrar dene", search: "Ara",
    loading: "Yükleniyor...", close: "Kapat", confirm: "Onayla",
    delete: "Sil", edit: "Düzenle",

    logIn: "Giriş yap", createAccount: "Hesap oluştur",
    continueGuest: "Hesap olmadan devam et",
    guestNote: "Haritalarınız yalnızca bu cihazda kaydedilecek",
    emailAddr: "E-posta adresi", password: "Şifre",
    yourName: "Adınız", loginSubtitle: "Kişisel Vedik astroloji rehberiniz",

    birthDetails: "Doğum bilgileri",
    birthSubtitle: "Doğru bir Kundli için doğru doğum bilgileri gereklidir.",
    dateOfBirth: "Doğum tarihi", timeOfBirth: "Doğum saati",
    birthPlace: "Doğum yeri", gender: "Cinsiyet",
    genderMale: "Erkek", genderFemale: "Kadın", genderOther: "Diğer",
    searchCity: "Şehir veya köy ara...",
    generateKundli: "Kundli oluştur", generatingKundli: "Kundli oluşturuluyor...",
    day: "Gün", month: "Ay", year: "Yıl",
    hour: "Saat", minute: "Dakika",
    timeTip: "Doğum saati Mahadasha'yı doğrudan etkiler. AM veya PM'yi dikkatlice doğrulayın.",

    todayEnergy: "Bugünün Kozmik Enerjisi", moonTransit: "Ay Transiti",
    currentDasha: "Mevcut Dasha", setupKundli: "Kundlinizi Ayarlayın",
    setupKundliSub: "Vedik haritanızı oluşturmak için doğum bilgilerinizi girin",
    viewAll: "Tümünü gör", viewDetails: "Detayları gör",
    forecast: "Tahmin", today: "Bugün",

    natalChart: "Doğum haritası", planets: "Gezegenler",
    dashaTimeline: "Dasha zaman çizelgesi", nakshatra: "Nakshatra",
    ascendant: "Yükselen", house: "Ev",
    noKundli: "Henüz Kundli yok", noKundliSub: "Tüm özellikleri açmak için doğum haritanızı ayarlayın",
    createKundli: "Kundli oluştur", chartType: "Harita türü",

    settings: "Ayarlar", language: "Dil", darkMode: "Karanlık mod",
    myProfiles: "Profillerim", subscription: "Abonelik",
    addFamilyMember: "Aile üyesi ekle",
    addFamilySub: "Oğul, kız, eş, ebeveynler, arkadaş ve daha fazlası",
    logOut: "Çıkış yap", deleteAccount: "Hesabı sil",
    freePlan: "Ücretsiz plan", upgradeNow: "Şimdi yükselt",
    selectLanguage: "Dil seç", langSubtitle: "Uygulama dili anında değişecek",
    langSearch: "Dil ara...", supported: "Destekleniyor", comingSoon: "Çok yakında",

    askTitle: "Jyotish AI'ya sor", askPlaceholder: "Haritanız hakkında her şeyi sorun...",
    askSend: "Gönder", askSuggestions: "Sormayı deneyin...",

    lifeMapTitle: "Yaşam Haritası", lifeMapSubtitle: "Yıldızlar tarafından haritalanan hayatın",
    lifeMapRelSub: "Aşk, uyumluluk ve bağlar", lifeMapCarSub: "Büyüme, başarı ve amaç",
    lifeMapHealthSub: "Beden, zihin ve canlılık", lifeMapFinSub: "Zenginlik, istikrar ve akış",
    lifeMapComing: "Daha fazla boyut yakında", lifeMapComingSub: "Eğitim, Seyahat, Maneviyat ve daha fazlası",
    futureTitle: "Gelecek Zaman Çizelgesi", futureSubtitle: "Önümüzdeki 6 ay çözüldü", career: "Kariyer",
    finance: "Finans", relationship: "İlişkiler", health: "Sağlık",

    noticeTitle: "Bildirimler", noNotices: "Henüz bildirim yok",

    errorGeneral: "Bir şeyler yanlış gitti. Lütfen tekrar deneyin.",
    noInternet: "İnternet bağlantısı yok.", tryAgain: "Tekrar dene",
  },
};

// ── Helper: get translations for a given language code ────────────────────────
// Falls back to "en" for any unsupported/unknown code
export function getT(lang: string): Translations {
  return T[(lang as UILang)] ?? T.en;
}
