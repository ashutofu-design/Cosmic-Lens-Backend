// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — App-wide UI Translation System
// Supported: en, hi, ta, te, bn, mr, gu, kn
// ══════════════════════════════════════════════════════════════════════════════

export type UILang = "en" | "hi" | "ta" | "te" | "bn" | "mr" | "gu" | "kn";

export interface Translations {
  // ── Tab bar ──────────────────────────────────────────────
  tabHome:      string;
  tabKundli:    string;
  tabAsk:       string;
  tabInsights:  string;
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

  // ── Insights ──────────────────────────────────────────────
  insightsTitle:   string;
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
    tabInsights: "Insights", tabNotice: "Notice", tabProfile: "Profile",

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

    insightsTitle: "Cosmic Insights", career: "Career",
    finance: "Finance", relationship: "Relationship", health: "Health",

    noticeTitle: "Notices", noNotices: "No notices yet",

    errorGeneral: "Something went wrong. Please try again.",
    noInternet: "No internet connection.", tryAgain: "Try Again",
  },

  // ── HINDI ───────────────────────────────────────────────────────────────────
  hi: {
    tabHome: "होम", tabKundli: "कुंडली", tabAsk: "पूछें",
    tabInsights: "अंतर्दृष्टि", tabNotice: "सूचना", tabProfile: "प्रोफाइल",

    save: "सहेजें", cancel: "रद्द करें", skip: "छोड़ें", back: "वापस",
    next: "आगे", done: "हो गया", retry: "दोबारा कोशिश करें", search: "खोजें",
    loading: "लोड हो रहा है...", close: "बंद करें", confirm: "पुष्टि करें",
    delete: "मिटाएं", edit: "संपादित करें",

    logIn: "लॉग इन", createAccount: "खाता बनाएं",
    continueGuest: "बिना खाते के जारी रखें",
    guestNote: "आपकी कुंडली केवल इस डिवाइस पर सहेजी जाएगी",
    emailAddr: "ईमेल पता", password: "पासवर्ड",
    yourName: "आपका नाम", loginSubtitle: "आपका व्यक्तिगत वैदिक ज्योतिष मार्गदर्शक",

    birthDetails: "जन्म विवरण",
    birthSubtitle: "सही कुंडली के लिए सटीक जन्म विवरण जरूरी है।",
    dateOfBirth: "जन्म तिथि", timeOfBirth: "जन्म समय",
    birthPlace: "जन्म स्थान", gender: "लिंग",
    genderMale: "पुरुष", genderFemale: "महिला", genderOther: "अन्य",
    searchCity: "शहर या गाँव खोजें...",
    generateKundli: "कुंडली बनाएं", generatingKundli: "कुंडली बन रही है...",
    day: "दिन", month: "महीना", year: "वर्ष",
    hour: "घंटा", minute: "मिनट",
    timeTip: "जन्म समय महादशा को सीधे प्रभावित करता है। AM या PM ध्यान से जाँचें।",

    todayEnergy: "आज की ब्रह्मांडीय ऊर्जा", moonTransit: "चंद्र गोचर",
    currentDasha: "वर्तमान दशा", setupKundli: "अपनी कुंडली बनाएं",
    setupKundliSub: "अपनी वैदिक कुंडली के लिए जन्म विवरण दर्ज करें",
    viewAll: "सभी देखें", viewDetails: "विवरण देखें",
    forecast: "भविष्यवाणी", today: "आज",

    natalChart: "जन्म कुंडली", planets: "ग्रह",
    dashaTimeline: "दशा समयरेखा", nakshatra: "नक्षत्र",
    ascendant: "लग्न", house: "भाव",
    noKundli: "कुंडली नहीं है", noKundliSub: "सभी सुविधाएं अनलॉक करने के लिए कुंडली बनाएं",
    createKundli: "कुंडली बनाएं", chartType: "चार्ट प्रकार",

    settings: "सेटिंग्स", language: "भाषा", darkMode: "डार्क मोड",
    myProfiles: "मेरी प्रोफाइल्स", subscription: "सदस्यता",
    addFamilyMember: "परिवार सदस्य जोड़ें",
    addFamilySub: "बेटा, बेटी, जीवनसाथी, माता-पिता, मित्र और अधिक",
    logOut: "लॉग आउट", deleteAccount: "खाता मिटाएं",
    freePlan: "मुफ्त प्लान", upgradeNow: "अभी अपग्रेड करें",
    selectLanguage: "भाषा चुनें", langSubtitle: "ऐप की भाषा तुरंत बदल जाएगी",
    langSearch: "भाषा खोजें...", supported: "उपलब्ध", comingSoon: "जल्द आ रहा है",

    askTitle: "ज्योतिष AI से पूछें", askPlaceholder: "अपनी कुंडली के बारे में कुछ भी पूछें...",
    askSend: "भेजें", askSuggestions: "पूछकर देखें...",

    insightsTitle: "ब्रह्मांडीय अंतर्दृष्टि", career: "करियर",
    finance: "वित्त", relationship: "रिश्ते", health: "स्वास्थ्य",

    noticeTitle: "सूचनाएं", noNotices: "अभी कोई सूचना नहीं",

    errorGeneral: "कुछ गलत हुआ। कृपया दोबारा कोशिश करें।",
    noInternet: "इंटरनेट कनेक्शन नहीं है।", tryAgain: "दोबारा कोशिश करें",
  },

  // ── TAMIL ───────────────────────────────────────────────────────────────────
  ta: {
    tabHome: "முகப்பு", tabKundli: "ஜாதகம்", tabAsk: "கேளுங்கள்",
    tabInsights: "நுண்ணறிவு", tabNotice: "அறிவிப்பு", tabProfile: "சுயவிவரம்",

    save: "சேமி", cancel: "ரத்து", skip: "தவிர்", back: "பின்",
    next: "அடுத்து", done: "முடிந்தது", retry: "மீண்டும்", search: "தேடு",
    loading: "ஏற்றுகிறது...", close: "மூடு", confirm: "உறுதிப்படுத்து",
    delete: "நீக்கு", edit: "திருத்து",

    logIn: "உள்நுழைய", createAccount: "கணக்கு உருவாக்கு",
    continueGuest: "கணக்கில்லாமல் தொடரு",
    guestNote: "உங்கள் ஜாதகம் இந்த சாதனத்தில் மட்டும் சேமிக்கப்படும்",
    emailAddr: "மின்னஞ்சல் முகவரி", password: "கடவுச்சொல்",
    yourName: "உங்கள் பெயர்", loginSubtitle: "உங்கள் தனிப்பட்ட வேத ஜோதிட வழிகாட்டி",

    birthDetails: "பிறப்பு விவரங்கள்",
    birthSubtitle: "சரியான ஜாதகத்திற்கு துல்லியமான பிறப்பு விவரங்கள் தேவை.",
    dateOfBirth: "பிறந்த தேதி", timeOfBirth: "பிறந்த நேரம்",
    birthPlace: "பிறந்த இடம்", gender: "பாலினம்",
    genderMale: "ஆண்", genderFemale: "பெண்", genderOther: "மற்றவை",
    searchCity: "நகரம் அல்லது கிராமம் தேடு...",
    generateKundli: "ஜாதகம் தயாரி", generatingKundli: "ஜாதகம் தயாராகிறது...",
    day: "நாள்", month: "மாதம்", year: "ஆண்டு",
    hour: "மணி", minute: "நிமிடம்",
    timeTip: "பிறந்த நேரம் மகாதசையை நேரடியாக பாதிக்கும். AM அல்லது PM கவனமாக சரிபார்க்கவும்.",

    todayEnergy: "இன்றைய அண்ட சக்தி", moonTransit: "சந்திர கோசாரம்",
    currentDasha: "தற்போதைய தசை", setupKundli: "உங்கள் ஜாதகத்தை அமை",
    setupKundliSub: "உங்கள் வேத ஜாதகத்திற்கு பிறப்பு விவரங்களை உள்ளிடுங்கள்",
    viewAll: "அனைத்தும் பார்", viewDetails: "விவரங்கள் பார்",
    forecast: "எதிர்காலம்", today: "இன்று",

    natalChart: "ஜன்ம ஜாதகம்", planets: "கிரகங்கள்",
    dashaTimeline: "தசை காலவரிசை", nakshatra: "நட்சத்திரம்",
    ascendant: "லக்னம்", house: "வீடு",
    noKundli: "ஜாதகம் இல்லை", noKundliSub: "அனைத்து அம்சங்களையும் திறக்க ஜாதகம் தயாரிக்கவும்",
    createKundli: "ஜாதகம் தயாரி", chartType: "சார்ட் வகை",

    settings: "அமைப்புகள்", language: "மொழி", darkMode: "இருண்ட பயன்முறை",
    myProfiles: "என் சுயவிவரங்கள்", subscription: "சந்தா",
    addFamilyMember: "குடும்ப உறுப்பினர் சேர்க்க",
    addFamilySub: "மகன், மகள், கணவன்/மனைவி, பெற்றோர், நண்பர் மற்றும் பலர்",
    logOut: "வெளியேறு", deleteAccount: "கணக்கை நீக்கு",
    freePlan: "இலவச திட்டம்", upgradeNow: "இப்போது மேம்படுத்து",
    selectLanguage: "மொழியை தேர்வு செய்", langSubtitle: "ஆப் மொழி உடனடியாக மாறும்",
    langSearch: "மொழி தேடு...", supported: "ஆதரிக்கப்படுகிறது", comingSoon: "விரைவில் வருகிறது",

    askTitle: "ஜோதிட AI கேளுங்கள்", askPlaceholder: "உங்கள் ஜாதகத்தைப் பற்றி எதையும் கேளுங்கள்...",
    askSend: "அனுப்பு", askSuggestions: "கேட்டு பாருங்கள்...",

    insightsTitle: "அண்ட நுண்ணறிவு", career: "தொழில்",
    finance: "நிதி", relationship: "உறவு", health: "ஆரோக்கியம்",

    noticeTitle: "அறிவிப்புகள்", noNotices: "இன்னும் அறிவிப்புகள் இல்லை",

    errorGeneral: "ஏதோ தவறு நடந்தது. மீண்டும் முயற்சிக்கவும்.",
    noInternet: "இணைய இணைப்பு இல்லை.", tryAgain: "மீண்டும் முயற்சி",
  },

  // ── TELUGU ──────────────────────────────────────────────────────────────────
  te: {
    tabHome: "హోమ్", tabKundli: "కుండలి", tabAsk: "అడగండి",
    tabInsights: "అంతర్దృష్టి", tabNotice: "నోటీసు", tabProfile: "ప్రొఫైల్",

    save: "సేవ్", cancel: "రద్దు", skip: "దాటు", back: "వెనక్కి",
    next: "తదుపరి", done: "పూర్తయింది", retry: "మళ్ళీ", search: "వెతుకు",
    loading: "లోడ్ అవుతోంది...", close: "మూయి", confirm: "నిర్ధారించు",
    delete: "తొలగించు", edit: "సవరించు",

    logIn: "లాగిన్", createAccount: "ఖాతా తయారు చేయి",
    continueGuest: "ఖాతా లేకుండా కొనసాగించు",
    guestNote: "మీ చార్ట్ ఈ పరికరంలో మాత్రమే సేవ్ అవుతుంది",
    emailAddr: "ఈమెయిల్ చిరునామా", password: "పాస్‌వర్డ్",
    yourName: "మీ పేరు", loginSubtitle: "మీ వ్యక్తిగత వేద జ్యోతిష మార్గదర్శి",

    birthDetails: "జన్మ వివరాలు",
    birthSubtitle: "సరైన కుండలికి ఖచ్చితమైన జన్మ వివరాలు అవసరం.",
    dateOfBirth: "జన్మ తేదీ", timeOfBirth: "జన్మ సమయం",
    birthPlace: "జన్మ స్థలం", gender: "లింగం",
    genderMale: "పురుషుడు", genderFemale: "స్త్రీ", genderOther: "ఇతర",
    searchCity: "నగరం లేదా గ్రామం వెతుకు...",
    generateKundli: "కుండలి తయారు చేయి", generatingKundli: "కుండలి తయారవుతోంది...",
    day: "రోజు", month: "నెల", year: "సంవత్సరం",
    hour: "గంట", minute: "నిమిషం",
    timeTip: "జన్మ సమయం మహాదశను నేరుగా ప్రభావితం చేస్తుంది. AM లేదా PM జాగ్రత్తగా తనిఖీ చేయండి.",

    todayEnergy: "నేటి విశ్వ శక్తి", moonTransit: "చంద్ర గోచరం",
    currentDasha: "ప్రస్తుత దశ", setupKundli: "మీ కుండలి సెటప్ చేయండి",
    setupKundliSub: "మీ వేద చార్ట్ కోసం జన్మ వివరాలు నమోదు చేయండి",
    viewAll: "అన్నీ చూడు", viewDetails: "వివరాలు చూడు",
    forecast: "అంచనా", today: "ఈరోజు",

    natalChart: "జన్మ కుండలి", planets: "గ్రహాలు",
    dashaTimeline: "దశ కాల రేఖ", nakshatra: "నక్షత్రం",
    ascendant: "లగ్నం", house: "భావం",
    noKundli: "కుండలి లేదు", noKundliSub: "అన్ని ఫీచర్లు అన్‌లాక్ చేయడానికి కుండలి సెటప్ చేయండి",
    createKundli: "కుండలి తయారు చేయి", chartType: "చార్ట్ రకం",

    settings: "సెట్టింగులు", language: "భాష", darkMode: "డార్క్ మోడ్",
    myProfiles: "నా ప్రొఫైల్‌లు", subscription: "సభ్యత్వం",
    addFamilyMember: "కుటుంబ సభ్యుడిని జోడించు",
    addFamilySub: "కొడుకు, కూతురు, జీవిత భాగస్వామి, తల్లిదండ్రులు, స్నేహితుడు మరియు మరిన్ని",
    logOut: "లాగ్ అవుట్", deleteAccount: "ఖాతా తొలగించు",
    freePlan: "ఉచిత ప్లాన్", upgradeNow: "ఇప్పుడు అప్‌గ్రేడ్",
    selectLanguage: "భాష ఎంచుకోండి", langSubtitle: "యాప్ భాష వెంటనే మారుతుంది",
    langSearch: "భాష వెతుకు...", supported: "మద్దతు ఉంది", comingSoon: "త్వరలో వస్తోంది",

    askTitle: "జ్యోతిష AI ని అడగండి", askPlaceholder: "మీ చార్ట్ గురించి ఏదైనా అడగండి...",
    askSend: "పంపు", askSuggestions: "ఇలా అడగండి...",

    insightsTitle: "విశ్వ అంతర్దృష్టి", career: "వృత్తి",
    finance: "ఆర్థికం", relationship: "సంబంధాలు", health: "ఆరోగ్యం",

    noticeTitle: "నోటీసులు", noNotices: "ఇంకా నోటీసులు లేవు",

    errorGeneral: "ఏదో తప్పు జరిగింది. దయచేసి మళ్ళీ ప్రయత్నించండి.",
    noInternet: "ఇంటర్నెట్ కనెక్షన్ లేదు.", tryAgain: "మళ్ళీ ప్రయత్నించు",
  },

  // ── BENGALI ─────────────────────────────────────────────────────────────────
  bn: {
    tabHome: "হোম", tabKundli: "কুণ্ডলী", tabAsk: "জিজ্ঞাসা",
    tabInsights: "অন্তর্দৃষ্টি", tabNotice: "বিজ্ঞপ্তি", tabProfile: "প্রোফাইল",

    save: "সংরক্ষণ", cancel: "বাতিল", skip: "এড়িয়ে যান", back: "ফিরে যান",
    next: "পরবর্তী", done: "সম্পন্ন", retry: "আবার চেষ্টা", search: "খুঁজুন",
    loading: "লোড হচ্ছে...", close: "বন্ধ করুন", confirm: "নিশ্চিত করুন",
    delete: "মুছুন", edit: "সম্পাদনা করুন",

    logIn: "লগ ইন", createAccount: "অ্যাকাউন্ট তৈরি করুন",
    continueGuest: "অ্যাকাউন্ট ছাড়াই চালু রাখুন",
    guestNote: "আপনার চার্ট শুধুমাত্র এই ডিভাইসে সংরক্ষিত হবে",
    emailAddr: "ইমেল ঠিকানা", password: "পাসওয়ার্ড",
    yourName: "আপনার নাম", loginSubtitle: "আপনার ব্যক্তিগত বৈদিক জ্যোতিষ গাইড",

    birthDetails: "জন্ম বিবরণ",
    birthSubtitle: "সঠিক কুণ্ডলীর জন্য নির্ভুল জন্ম বিবরণ প্রয়োজন।",
    dateOfBirth: "জন্ম তারিখ", timeOfBirth: "জন্ম সময়",
    birthPlace: "জন্মস্থান", gender: "লিঙ্গ",
    genderMale: "পুরুষ", genderFemale: "মহিলা", genderOther: "অন্যান্য",
    searchCity: "শহর বা গ্রাম খুঁজুন...",
    generateKundli: "কুণ্ডলী তৈরি করুন", generatingKundli: "কুণ্ডলী তৈরি হচ্ছে...",
    day: "দিন", month: "মাস", year: "বছর",
    hour: "ঘণ্টা", minute: "মিনিট",
    timeTip: "জন্ম সময় মহাদশাকে সরাসরি প্রভাবিত করে। AM বা PM সাবধানে যাচাই করুন।",

    todayEnergy: "আজকের মহাজাগতিক শক্তি", moonTransit: "চন্দ্র গোচর",
    currentDasha: "বর্তমান দশা", setupKundli: "আপনার কুণ্ডলী সেট করুন",
    setupKundliSub: "আপনার বৈদিক চার্টের জন্য জন্ম বিবরণ লিখুন",
    viewAll: "সব দেখুন", viewDetails: "বিবরণ দেখুন",
    forecast: "পূর্বাভাস", today: "আজ",

    natalChart: "জন্ম কুণ্ডলী", planets: "গ্রহ",
    dashaTimeline: "দশা টাইমলাইন", nakshatra: "নক্ষত্র",
    ascendant: "লগ্ন", house: "ভাব",
    noKundli: "কুণ্ডলী নেই", noKundliSub: "সমস্ত ফিচার আনলক করতে কুণ্ডলী তৈরি করুন",
    createKundli: "কুণ্ডলী তৈরি করুন", chartType: "চার্ট প্রকার",

    settings: "সেটিংস", language: "ভাষা", darkMode: "ডার্ক মোড",
    myProfiles: "আমার প্রোফাইলগুলি", subscription: "সাবস্ক্রিপশন",
    addFamilyMember: "পরিবারের সদস্য যোগ করুন",
    addFamilySub: "ছেলে, মেয়ে, স্বামী/স্ত্রী, বাবা-মা, বন্ধু এবং আরও",
    logOut: "লগ আউট", deleteAccount: "অ্যাকাউন্ট মুছুন",
    freePlan: "বিনামূল্যে প্ল্যান", upgradeNow: "এখনই আপগ্রেড করুন",
    selectLanguage: "ভাষা নির্বাচন করুন", langSubtitle: "অ্যাপের ভাষা তাৎক্ষণিকভাবে পরিবর্তন হবে",
    langSearch: "ভাষা খুঁজুন...", supported: "সমর্থিত", comingSoon: "শীঘ্রই আসছে",

    askTitle: "জ্যোতিষ AI কে জিজ্ঞাসা করুন", askPlaceholder: "আপনার চার্ট সম্পর্কে যেকোনো কিছু জিজ্ঞাসা করুন...",
    askSend: "পাঠান", askSuggestions: "জিজ্ঞাসা করে দেখুন...",

    insightsTitle: "মহাজাগতিক অন্তর্দৃষ্টি", career: "ক্যারিয়ার",
    finance: "অর্থ", relationship: "সম্পর্ক", health: "স্বাস্থ্য",

    noticeTitle: "বিজ্ঞপ্তি", noNotices: "এখনো কোনো বিজ্ঞপ্তি নেই",

    errorGeneral: "কিছু ভুল হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।",
    noInternet: "ইন্টারনেট সংযোগ নেই।", tryAgain: "আবার চেষ্টা করুন",
  },

  // ── MARATHI ─────────────────────────────────────────────────────────────────
  mr: {
    tabHome: "होम", tabKundli: "कुंडली", tabAsk: "विचारा",
    tabInsights: "अंतर्ज्ञान", tabNotice: "सूचना", tabProfile: "प्रोफाइल",

    save: "जतन करा", cancel: "रद्द करा", skip: "वगळा", back: "मागे",
    next: "पुढे", done: "झाले", retry: "पुन्हा प्रयत्न", search: "शोधा",
    loading: "लोड होत आहे...", close: "बंद करा", confirm: "पुष्टी करा",
    delete: "हटवा", edit: "संपादित करा",

    logIn: "लॉग इन", createAccount: "खाते बनवा",
    continueGuest: "खाते शिवाय सुरू ठेवा",
    guestNote: "तुमचा चार्ट फक्त या डिव्हाइसवर सेव्ह होईल",
    emailAddr: "ईमेल पत्ता", password: "पासवर्ड",
    yourName: "तुमचे नाव", loginSubtitle: "तुमचा वैयक्तिक वैदिक ज्योतिष मार्गदर्शक",

    birthDetails: "जन्माचे तपशील",
    birthSubtitle: "अचूक कुंडलीसाठी अचूक जन्म तपशील आवश्यक आहेत.",
    dateOfBirth: "जन्म तारीख", timeOfBirth: "जन्म वेळ",
    birthPlace: "जन्म ठिकाण", gender: "लिंग",
    genderMale: "पुरुष", genderFemale: "स्त्री", genderOther: "इतर",
    searchCity: "शहर किंवा गाव शोधा...",
    generateKundli: "कुंडली बनवा", generatingKundli: "कुंडली बनत आहे...",
    day: "दिवस", month: "महिना", year: "वर्ष",
    hour: "तास", minute: "मिनिट",
    timeTip: "जन्म वेळ महादशेवर थेट परिणाम करते. AM किंवा PM काळजीपूर्वक तपासा.",

    todayEnergy: "आजची ब्रह्मांड ऊर्जा", moonTransit: "चंद्र गोचर",
    currentDasha: "सध्याची दशा", setupKundli: "तुमची कुंडली सेट करा",
    setupKundliSub: "तुमच्या वैदिक चार्टसाठी जन्म तपशील द्या",
    viewAll: "सर्व पहा", viewDetails: "तपशील पहा",
    forecast: "भविष्यवाणी", today: "आज",

    natalChart: "जन्म कुंडली", planets: "ग्रह",
    dashaTimeline: "दशा टाइमलाइन", nakshatra: "नक्षत्र",
    ascendant: "लग्न", house: "भाव",
    noKundli: "कुंडली नाही", noKundliSub: "सर्व वैशिष्ट्ये उघडण्यासाठी कुंडली बनवा",
    createKundli: "कुंडली बनवा", chartType: "चार्ट प्रकार",

    settings: "सेटिंग्ज", language: "भाषा", darkMode: "डार्क मोड",
    myProfiles: "माझे प्रोफाइल", subscription: "सदस्यता",
    addFamilyMember: "कुटुंब सदस्य जोडा",
    addFamilySub: "मुलगा, मुलगी, जोडीदार, पालक, मित्र आणि इतर",
    logOut: "लॉग आउट", deleteAccount: "खाते हटवा",
    freePlan: "मोफत योजना", upgradeNow: "आता अपग्रेड करा",
    selectLanguage: "भाषा निवडा", langSubtitle: "अॅपची भाषा लगेच बदलेल",
    langSearch: "भाषा शोधा...", supported: "उपलब्ध", comingSoon: "लवकरच येत आहे",

    askTitle: "ज्योतिष AI ला विचारा", askPlaceholder: "तुमच्या चार्टबद्दल काहीही विचारा...",
    askSend: "पाठवा", askSuggestions: "विचारून पहा...",

    insightsTitle: "ब्रह्मांड अंतर्ज्ञान", career: "करिअर",
    finance: "वित्त", relationship: "नाते", health: "आरोग्य",

    noticeTitle: "सूचना", noNotices: "अद्याप कोणत्याही सूचना नाहीत",

    errorGeneral: "काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.",
    noInternet: "इंटरनेट कनेक्शन नाही.", tryAgain: "पुन्हा प्रयत्न करा",
  },

  // ── GUJARATI ────────────────────────────────────────────────────────────────
  gu: {
    tabHome: "હોમ", tabKundli: "કુંડળી", tabAsk: "પૂછો",
    tabInsights: "સૂઝ", tabNotice: "સૂચના", tabProfile: "પ્રોફાઇલ",

    save: "સાચવો", cancel: "રદ કરો", skip: "છોડો", back: "પાછળ",
    next: "આગળ", done: "થઈ ગયું", retry: "ફરી પ્રયાસ", search: "શોધો",
    loading: "લોડ થઈ રહ્યું છે...", close: "બંધ કરો", confirm: "પુષ્ટિ કરો",
    delete: "કાઢી નાખો", edit: "સંપાદિત કરો",

    logIn: "લૉગ ઇન", createAccount: "ખાતું બનાવો",
    continueGuest: "ખાતા વગર આગળ",
    guestNote: "તમારો ચાર્ટ ફક્ત આ ઉપકરણ પર સંગ્રહ થશે",
    emailAddr: "ઈ-મેઈલ સરનામું", password: "પાસવર્ડ",
    yourName: "તમારું નામ", loginSubtitle: "તમારો વ્યક્તિગત વૈદિક જ્યોતિષ માર્ગદર્શક",

    birthDetails: "જન્મ વિગત",
    birthSubtitle: "સાચી કુંડળી માટે ચોક્કસ જન્મ વિગત જરૂરી છે.",
    dateOfBirth: "જન્મ તારીખ", timeOfBirth: "જન્મ સમય",
    birthPlace: "જન્મ સ્થળ", gender: "લિંગ",
    genderMale: "પુરુષ", genderFemale: "સ્ત્રી", genderOther: "અન્ય",
    searchCity: "શહેર અથવા ગામ શોધો...",
    generateKundli: "કુંડળી બનાવો", generatingKundli: "કુંડળી બની રહી છે...",
    day: "દિવસ", month: "મહિનો", year: "વર્ષ",
    hour: "કલાક", minute: "મિનિટ",
    timeTip: "જન્મ સમય મહાદશાને સીધો અસર કરે છે. AM કે PM ધ્યાનથી ચકાસો.",

    todayEnergy: "આજની બ્રહ્માંડ ઊર્જા", moonTransit: "ચંદ્ર ગોચર",
    currentDasha: "હાલની દશા", setupKundli: "તમારી કુંડળી સ્થાપિત કરો",
    setupKundliSub: "તમારા વૈદિક ચાર્ટ માટે જન્મ વિગત દાખલ કરો",
    viewAll: "બધું જુઓ", viewDetails: "વિગત જુઓ",
    forecast: "ભવિષ્ય", today: "આજ",

    natalChart: "જન્મ કુંડળી", planets: "ગ્રહો",
    dashaTimeline: "દશા ટાઈમ-લાઈન", nakshatra: "નક્ષત્ર",
    ascendant: "લગ્ન", house: "ભાવ",
    noKundli: "કુંડળી નથી", noKundliSub: "બધી સુવિધાઓ ખોલવા માટે કુંડળી બનાવો",
    createKundli: "કુંડળી બનાવો", chartType: "ચાર્ટ પ્રકાર",

    settings: "સેટિંગ્સ", language: "ભાષા", darkMode: "ડાર્ક મોડ",
    myProfiles: "મારા પ્રોફાઇલ", subscription: "સબ્સ્ક્રિપ્શન",
    addFamilyMember: "કુટુંબ સભ્ય ઉમેરો",
    addFamilySub: "દીકરો, દીકરી, જીવનસાથી, માતા-પિતા, મિત્ર અને વધુ",
    logOut: "લૉગ આઉટ", deleteAccount: "ખાતું ડૅ‍lete કરો",
    freePlan: "મફત પ્લાન", upgradeNow: "અત્યારે અપગ્રેડ",
    selectLanguage: "ભાષા પસંદ કરો", langSubtitle: "ઍપ ભાષા તરત બદલાઈ જશે",
    langSearch: "ભાષા શોધો...", supported: "ઉપલબ્ધ", comingSoon: "ટૂંક સમયમાં",

    askTitle: "જ્યોતિષ AI ને પૂછો", askPlaceholder: "તમારા ચાર્ટ વિશે ગમે તે પૂછો...",
    askSend: "મોકલો", askSuggestions: "પૂછીને જુઓ...",

    insightsTitle: "બ્રહ્માંડ સૂઝ", career: "કારકિર્દી",
    finance: "નાણાં", relationship: "સંબંધ", health: "આરોગ્ય",

    noticeTitle: "સૂચનાઓ", noNotices: "હજુ કોઈ સૂચના નથી",

    errorGeneral: "કંઈક ખોટું થયું. ફરી પ્રયાસ કરો.",
    noInternet: "ઇન્ટરનેટ કનેક્શન નથી.", tryAgain: "ફરી પ્રયાસ",
  },

  // ── KANNADA ─────────────────────────────────────────────────────────────────
  kn: {
    tabHome: "ಮನೆ", tabKundli: "ಕುಂಡಲಿ", tabAsk: "ಕೇಳಿ",
    tabInsights: "ಒಳನೋಟ", tabNotice: "ಸೂಚನೆ", tabProfile: "ಪ್ರೊಫೈಲ್",

    save: "ಉಳಿಸು", cancel: "ರದ್ದು", skip: "ಬಿಟ್ಟು ಹೋಗು", back: "ಹಿಂದೆ",
    next: "ಮುಂದೆ", done: "ಮುಗಿಯಿತು", retry: "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ", search: "ಹುಡುಕಿ",
    loading: "ಲೋಡ್ ಆಗುತ್ತಿದೆ...", close: "ಮುಚ್ಚಿ", confirm: "ದೃಢೀಕರಿಸಿ",
    delete: "ಅಳಿಸಿ", edit: "ಸಂಪಾದಿಸಿ",

    logIn: "ಲಾಗಿನ್", createAccount: "ಖಾತೆ ಮಾಡಿ",
    continueGuest: "ಖಾತೆ ಇಲ್ಲದೆ ಮುಂದುವರಿ",
    guestNote: "ನಿಮ್ಮ ಚಾರ್ಟ್ ಈ ಸಾಧನದಲ್ಲಿ ಮಾತ್ರ ಉಳಿಸಲಾಗುತ್ತದೆ",
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

    insightsTitle: "ಬ್ರಹ್ಮಾಂಡ ಒಳನೋಟ", career: "ವೃತ್ತಿ",
    finance: "ಹಣಕಾಸು", relationship: "ಸಂಬಂಧ", health: "ಆರೋಗ್ಯ",

    noticeTitle: "ಸೂಚನೆಗಳು", noNotices: "ಇನ್ನೂ ಯಾವುದೇ ಸೂಚನೆಗಳಿಲ್ಲ",

    errorGeneral: "ಏನೋ ತಪ್ಪಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    noInternet: "ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಇಲ್ಲ.", tryAgain: "ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ",
  },
};

// ── Helper: get translations for a given language code ────────────────────────
// Falls back to "en" for unsupported codes (e.g., "pa", "or", etc.)
export function getT(lang: string): Translations {
  return T[(lang as UILang)] ?? T.en;
}
