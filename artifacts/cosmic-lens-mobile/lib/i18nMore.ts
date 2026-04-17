// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Additional UI strings (Round 2)
// Covers all hardcoded strings that were leaking Hinglish/Hindi into other
// languages. en/hn/hi defined explicitly; all other 21 languages fall back
// to English (so Hinglish never leaks when user picked a non-Hindi language).
// ══════════════════════════════════════════════════════════════════════════════

import type { UILang } from "./i18n";

export interface MoreT {
  // ── MoreDrawer ────────────────────────────────────────────
  moreExplore:        string;
  moreSubtitle:       string;
  catRashifal:        string;
  catPanchang:        string;
  catKundliMilan:     string;
  catMuhurat:         string;
  catNumerology:      string;
  catRemedies:        string;
  catVastu:           string;
  mdRashifalTitle:    string;
  mdRashifalSub:      string;
  mdLuckyTitle:       string;
  mdLuckySub:         string;
  mdWeeklyTitle:      string;
  mdWeeklySub:        string;
  mdPanchangTitle:    string;
  mdPanchangSub:      string;
  mdRahukaalTitle:    string;
  mdRahukaalSub:      string;
  mdFestivalsTitle:   string;
  mdFestivalsSub:     string;
  mdMilanTitle:       string;
  mdMilanSub:         string;
  mdCompatTitle:      string;
  mdCompatSub:        string;
  mdMuhuratTitle:     string;
  mdMuhuratSub:       string;
  mdNumerologyTitle:  string;
  mdNumerologySub:    string;
  mdRemediesTitle:    string;
  mdRemediesSub:      string;
  mdVastuTitle:       string;
  mdVastuSub:         string;
  badgeNew:           string;

  // ── Subscription ──────────────────────────────────────────
  planBasicTagline:    string;
  planProTagline:      string;
  planFreeTagline:     string;
  planTrialTagline:    string;
  needLogin:           string;
  needLoginMsg:        string;
  perMonth:            string;
  perWeek:             string;
  mostPopular:         string;
  bestValue:           string;
  currentPlan:         string;
  startTrial:          string;
  selectPlan:          string;
  faqTitle:            string;
  comparePlans:        string;
  feature:             string;

  // ── Login / OTP ───────────────────────────────────────────
  enterPhone:          string;
  phonePromptSub:      string;
  sendOtp:             string;
  sendingOtp:          string;
  enterOtp:            string;
  otpPromptSub:        string;
  verifyOtp:           string;
  verifyingOtp:        string;
  resendOtp:           string;
  resendIn:            string;
  changeNumber:        string;
  invalidPhone:        string;
  otpSent:             string;
  otpFailed:           string;
  otpInvalid:          string;
  otpResent:           string;
  termsAccept:         string;
  termsLink:           string;
  privacyLink:         string;

  // ── Common analysis errors ───────────────────────────────
  needKundli:          string;
  needKundliSub:       string;
  needBothKundli:      string;
  needPartnerKundli:   string;
  analyzingChart:      string;
  fetchFailed:         string;
  reload:              string;
  upgradeToProMsg:     string;
  upgradeToPro:        string;

  // ── Analysis screen titles ────────────────────────────────
  careerTitle:         string;
  financeTitle:        string;
  healthTitle:         string;
  loveCompatTitle:     string;
  loyaltyTitle:        string;
  breakupTitle:        string;
  willReturnTitle:     string;
  futureOutcomeTitle:  string;

  // ── Ask AI ────────────────────────────────────────────────
  askLimitReached:     string;
  askWithoutKundli:    string;
  askDailyLimitOver:   string;
  askThinking:         string;
  askError:            string;

  // ── Recently deleted / Delete account ─────────────────────
  recentlyDeleted:     string;
  recentlyDeletedSub:  string;
  noDeletedItems:      string;
  restore:             string;
  restoreFailed:       string;
  pullToRefresh:       string;
  deletedAgo:          string;
  willBeDeletedIn:     string;
  deleteAccountTitle:  string;
  deleteAccountWarn:   string;
  deleteAccountConfirm:string;
  permanentlyDelete:   string;

  // ── Daily alerts ──────────────────────────────────────────
  dailyAlertsTitle:    string;
  energyGood:          string;
  energyNeutral:       string;
  energyChallenging:   string;

  // ── About / Legal ─────────────────────────────────────────
  aboutTitle:          string;
  aboutTagline:        string;
  versionLabel:        string;
  termsTitle:          string;
  privacyTitle:        string;

  // ── Errors / common ───────────────────────────────────────
  errReload:           string;
  errOops:             string;
  errSomething:        string;
  errNetwork:          string;
  errKundliRequired:   string;
}

// English — primary, complete
const EN: MoreT = {
  // MoreDrawer
  moreExplore:        "Explore",
  moreSubtitle:       "Everything in one place",
  catRashifal:        "🔮 Horoscope & Lucky",
  catPanchang:        "🌙 Panchang",
  catKundliMilan:     "💑 Match Making",
  catMuhurat:         "⏰ Auspicious Time",
  catNumerology:      "🔢 Numerology",
  catRemedies:        "💎 Remedies",
  catVastu:           "🏠 Vastu",
  mdRashifalTitle:    "Daily Horoscope",
  mdRashifalSub:      "Today's prediction by sign",
  mdLuckyTitle:       "Lucky Color & More",
  mdLuckySub:         "Color, number, day, gemstone",
  mdWeeklyTitle:      "Weekly Horoscope",
  mdWeeklySub:        "Next 7 days forecast",
  mdPanchangTitle:    "Today's Panchang",
  mdPanchangSub:      "Tithi, Nakshatra, Yoga",
  mdRahukaalTitle:    "Rahu Kaal",
  mdRahukaalSub:      "Today's inauspicious time",
  mdFestivalsTitle:   "Festivals & Vrat",
  mdFestivalsSub:     "Festival & fast calendar",
  mdMilanTitle:       "Kundli Milan",
  mdMilanSub:         "36 guna matching",
  mdCompatTitle:      "Sign Compatibility",
  mdCompatSub:        "Love & business match",
  mdMuhuratTitle:     "Auspicious Muhurat",
  mdMuhuratSub:       "Wedding, housewarming, business",
  mdNumerologyTitle:  "Numerology",
  mdNumerologySub:    "Life path, lucky number",
  mdRemediesTitle:    "Planet Remedies",
  mdRemediesSub:      "Mantra, charity, gemstones",
  mdVastuTitle:       "Vastu Tips",
  mdVastuSub:         "Home & direction guide",
  badgeNew:           "New",

  // Subscription
  planBasicTagline:   "Basics for daily use",
  planProTagline:     "Everything unlocked",
  planFreeTagline:    "Try the basics",
  planTrialTagline:   "7-day full access",
  needLogin:          "Login Required",
  needLoginMsg:       "Please login to continue.",
  perMonth:           "/month",
  perWeek:            "/week",
  mostPopular:        "Most Popular",
  bestValue:          "Best Value",
  currentPlan:        "Current Plan",
  startTrial:         "Start Trial",
  selectPlan:         "Select Plan",
  faqTitle:           "Frequently Asked Questions",
  comparePlans:       "Compare Plans",
  feature:            "Feature",

  // Login / OTP
  enterPhone:         "Enter your phone number",
  phonePromptSub:     "We'll send a verification code via SMS",
  sendOtp:            "Send OTP",
  sendingOtp:         "Sending OTP...",
  enterOtp:           "Enter the 6-digit code",
  otpPromptSub:       "We sent a code to your phone",
  verifyOtp:          "Verify",
  verifyingOtp:       "Verifying...",
  resendOtp:          "Resend OTP",
  resendIn:           "Resend in",
  changeNumber:       "Change number",
  invalidPhone:       "Please enter a valid 10-digit Indian mobile number.",
  otpSent:            "OTP sent successfully.",
  otpFailed:          "Could not send OTP. Try again.",
  otpInvalid:         "Incorrect OTP. Please try again.",
  otpResent:          "A new OTP has been sent.",
  termsAccept:        "By continuing, you agree to our",
  termsLink:          "Terms",
  privacyLink:        "Privacy Policy",

  // Common analysis
  needKundli:         "Kundli Required",
  needKundliSub:      "Your kundli is not ready yet. Please create it from the Kundli screen first.",
  needBothKundli:     "Both your kundli and your partner's kundli are required. Please create both kundlis from the Kundli screen first.",
  needPartnerKundli:  "Partner's kundli is required.",
  analyzingChart:     "Reading your chart...",
  fetchFailed:        "Could not load. Please try again.",
  reload:             "Reload",
  upgradeToProMsg:    "Upgrade to Pro to unlock this feature.",
  upgradeToPro:       "Upgrade to Pro",

  // Titles
  careerTitle:        "Career Analysis",
  financeTitle:       "Finance Analysis",
  healthTitle:        "Health Analysis",
  loveCompatTitle:    "Love Compatibility",
  loyaltyTitle:       "Loyalty Check",
  breakupTitle:       "Breakup Chances",
  willReturnTitle:    "Will They Return?",
  futureOutcomeTitle: "Future Outcome",

  // Ask AI
  askLimitReached:    "Daily limit reached",
  askWithoutKundli:   "Without a Kundli I can only give general information. Create your birth chart — then I'll give you a personalized analysis based on your active dasha.",
  askDailyLimitOver:  "Your daily limit is over.",
  askThinking:        "Thinking...",
  askError:           "Could not get an answer. Please try again.",

  // Recently deleted
  recentlyDeleted:    "Recently Deleted",
  recentlyDeletedSub: "Items deleted in the last 24 hours can be restored",
  noDeletedItems:     "Nothing deleted recently",
  restore:            "Restore",
  restoreFailed:      "Restore failed. Please try again.",
  pullToRefresh:      "Pull down to refresh",
  deletedAgo:         "Deleted",
  willBeDeletedIn:    "Will be permanently deleted in",
  deleteAccountTitle: "Delete Account",
  deleteAccountWarn:  "This will permanently delete your account and all your data. This action cannot be undone.",
  deleteAccountConfirm:"Type DELETE to confirm",
  permanentlyDelete:  "Permanently Delete",

  // Daily alerts
  dailyAlertsTitle:   "Daily Alerts",
  energyGood:         "Good",
  energyNeutral:      "Neutral",
  energyChallenging:  "Challenging",

  // About / Legal
  aboutTitle:         "About Cosmic Lens",
  aboutTagline:       "Your personal Vedic astrology guide",
  versionLabel:       "Version",
  termsTitle:         "Terms of Service",
  privacyTitle:       "Privacy Policy",

  // Errors
  errReload:          "Reload",
  errOops:            "Oops!",
  errSomething:       "Something went wrong.",
  errNetwork:         "Network error. Check your connection.",
  errKundliRequired:  "Please complete your Kundli first — add your birth details and come back.",
};

// Hinglish overrides (only differing keys)
const HN: Partial<MoreT> = {
  moreExplore:        "Explore",
  moreSubtitle:       "Sab kuch ek jagah",
  catRashifal:        "🔮 Rashifal & Lucky",
  catPanchang:        "🌙 Panchang",
  catKundliMilan:     "💑 Kundli Milan",
  catMuhurat:         "⏰ Muhurat",
  catNumerology:      "🔢 Numerology",
  catRemedies:        "💎 Upay & Remedies",
  catVastu:           "🏠 Vastu",
  mdRashifalTitle:    "Daily Rashifal",
  mdRashifalSub:      "Aaj ka rashi phal",
  mdLuckyTitle:       "Lucky Color & More",
  mdLuckySub:         "Rang, number, din, ratan",
  mdWeeklyTitle:      "Weekly Rashifal",
  mdWeeklySub:        "7 din ka bhavishya",
  mdPanchangTitle:    "Aaj ka Panchang",
  mdPanchangSub:      "Tithi, Nakshatra, Yoga",
  mdRahukaalTitle:    "Rahu Kaal",
  mdRahukaalSub:      "Aaj ka ashubh samay",
  mdFestivalsTitle:   "Tyohar & Vrat",
  mdFestivalsSub:     "Festival & vrat calendar",
  mdMilanTitle:       "Kundli Milan",
  mdMilanSub:         "36 guna matching",
  mdCompatTitle:      "Rashi Compatibility",
  mdCompatSub:        "Love aur business match",
  mdMuhuratTitle:     "Shubh Muhurat",
  mdMuhuratSub:       "Shadi, Griha, Business",
  mdNumerologyTitle:  "Numerology",
  mdNumerologySub:    "Life path, lucky number",
  mdRemediesTitle:    "Graha Upay",
  mdRemediesSub:      "Mantra, daan, ratan",
  mdVastuTitle:       "Vastu Tips",
  mdVastuSub:         "Ghar aur disha guide",
  badgeNew:           "New",

  planBasicTagline:   "Roz ke liye basics",
  planProTagline:     "Sab kuch unlock",
  planFreeTagline:    "Basics try karein",
  planTrialTagline:   "7-din full access",
  needLogin:          "Login zaroori",
  needLoginMsg:       "Continue karne ke liye login karein.",
  perMonth:           "/mahina",
  perWeek:            "/hafta",
  mostPopular:        "Sabse Popular",
  bestValue:          "Best Value",
  currentPlan:        "Current Plan",
  startTrial:         "Trial Start karein",
  selectPlan:         "Plan chunein",
  faqTitle:           "Aksar Pooche Jaane Wale Sawaal",
  comparePlans:       "Plans compare karein",
  feature:            "Feature",

  enterPhone:         "Apna phone number daalein",
  phonePromptSub:     "Hum SMS pe verification code bhejenge",
  sendOtp:            "OTP bhejein",
  sendingOtp:         "OTP bhej rahe hain...",
  enterOtp:           "6-digit code daalein",
  otpPromptSub:       "Aapke phone par code bhej diya hai",
  verifyOtp:          "Verify karein",
  verifyingOtp:       "Verify ho raha hai...",
  resendOtp:          "OTP dobara bhejein",
  resendIn:           "Dobara bhejein",
  changeNumber:       "Number badlein",
  invalidPhone:       "Sahi 10-digit Indian mobile number daalein.",
  otpSent:            "OTP bhej diya gaya.",
  otpFailed:          "OTP nahi bhej paaye. Dobara try karein.",
  otpInvalid:         "Galat OTP. Dobara try karein.",
  otpResent:          "Naya OTP bhej diya gaya.",
  termsAccept:        "Continue karke aap maante hain hamare",
  termsLink:          "Terms",
  privacyLink:        "Privacy Policy",

  needKundli:         "Kundli zaroori",
  needKundliSub:      "Aapki kundli abhi ready nahi hai. Pehle Kundli screen se banayein.",
  needBothKundli:     "Aapki aur aapke partner ki dono kundli zaroori hain. Dono Kundli screen se banayein.",
  needPartnerKundli:  "Partner ki kundli zaroori hai.",
  analyzingChart:     "Aapka chart padh rahe hain...",
  fetchFailed:        "Load nahi ho paaya. Dobara try karein.",
  reload:             "Reload",
  upgradeToProMsg:    "Yeh feature unlock karne ke liye Pro pe upgrade karein.",
  upgradeToPro:       "Pro pe Upgrade karein",

  careerTitle:        "Career Analysis",
  financeTitle:       "Paisa Analysis",
  healthTitle:        "Swasthya Analysis",
  loveCompatTitle:    "Love Compatibility",
  loyaltyTitle:       "Vafadari Check",
  breakupTitle:       "Breakup Chances",
  willReturnTitle:    "Wapas Aayenge?",
  futureOutcomeTitle: "Bhavishya ka Phal",

  askLimitReached:    "Daily limit khatam",
  askWithoutKundli:   "Bina Kundli ke main sirf general information de sakta hu. Apna birth chart banayein — phir main aapki active dasha ke aadhar par personalized analysis dunga.",
  askDailyLimitOver:  "Aaj ka daily limit poora ho gaya.",
  askThinking:        "Soch raha hu...",
  askError:           "Jawab nahi mil paaya. Dobara try karein.",

  recentlyDeleted:    "Haal mein delete kiye",
  recentlyDeletedSub: "Pichhle 24 ghante mein delete kiye items wapas la sakte hain",
  noDeletedItems:     "Haal mein kuch delete nahi kiya",
  restore:            "Wapas laayein",
  restoreFailed:      "Restore nahi ho paaya. Dobara try karein.",
  pullToRefresh:      "Refresh karne ke liye neeche kheechein",
  deletedAgo:         "Delete kiya",
  willBeDeletedIn:    "Permanently delete hoga",
  deleteAccountTitle: "Account Delete karein",
  deleteAccountWarn:  "Aapka account aur saara data permanently delete ho jayega. Yeh wapas nahi laaya ja sakta.",
  deleteAccountConfirm:"Pushti ke liye DELETE type karein",
  permanentlyDelete:  "Permanently Delete karein",

  dailyAlertsTitle:   "Daily Alerts",
  energyGood:         "Achha",
  energyNeutral:      "Saadharan",
  energyChallenging:  "Challenging",

  aboutTitle:         "Cosmic Lens ke baare mein",
  aboutTagline:       "Aapka personal Vedic astrology guide",
  versionLabel:       "Version",
  termsTitle:         "Terms of Service",
  privacyTitle:       "Privacy Policy",

  errReload:          "Reload",
  errOops:            "Oops!",
  errSomething:       "Kuch galat ho gaya.",
  errNetwork:         "Network error. Connection check karein.",
  errKundliRequired:  "Apni Kundli pehle complete karein — birth details add karke aaiye.",
};

// Hindi overrides (Devanagari)
const HI: Partial<MoreT> = {
  moreExplore:        "एक्सप्लोर",
  moreSubtitle:       "सब कुछ एक जगह",
  catRashifal:        "🔮 राशिफल और लक्की",
  catPanchang:        "🌙 पंचांग",
  catKundliMilan:     "💑 कुंडली मिलान",
  catMuhurat:         "⏰ मुहूर्त",
  catNumerology:      "🔢 अंकशास्त्र",
  catRemedies:        "💎 उपाय और रत्न",
  catVastu:           "🏠 वास्तु",
  mdRashifalTitle:    "दैनिक राशिफल",
  mdRashifalSub:      "आज का राशि फल",
  mdLuckyTitle:       "लक्की रंग और बहुत कुछ",
  mdLuckySub:         "रंग, अंक, दिन, रत्न",
  mdWeeklyTitle:      "साप्ताहिक राशिफल",
  mdWeeklySub:        "अगले 7 दिनों का भविष्य",
  mdPanchangTitle:    "आज का पंचांग",
  mdPanchangSub:      "तिथि, नक्षत्र, योग",
  mdRahukaalTitle:    "राहु काल",
  mdRahukaalSub:      "आज का अशुभ समय",
  mdFestivalsTitle:   "त्यौहार और व्रत",
  mdFestivalsSub:     "त्यौहार और व्रत कैलेंडर",
  mdMilanTitle:       "कुंडली मिलान",
  mdMilanSub:         "36 गुण मिलान",
  mdCompatTitle:      "राशि अनुकूलता",
  mdCompatSub:        "प्रेम और व्यापार मेल",
  mdMuhuratTitle:     "शुभ मुहूर्त",
  mdMuhuratSub:       "विवाह, गृह, व्यापार",
  mdNumerologyTitle:  "अंकशास्त्र",
  mdNumerologySub:    "लाइफ पाथ, लक्की नंबर",
  mdRemediesTitle:    "ग्रह उपाय",
  mdRemediesSub:      "मंत्र, दान, रत्न",
  mdVastuTitle:       "वास्तु टिप्स",
  mdVastuSub:         "घर और दिशा गाइड",
  badgeNew:           "नया",

  planBasicTagline:   "रोज़मर्रा के लिए बेसिक्स",
  planProTagline:     "सब कुछ अनलॉक",
  planFreeTagline:    "बेसिक्स आज़माएं",
  planTrialTagline:   "7 दिन फुल एक्सेस",
  needLogin:          "लॉगिन आवश्यक",
  needLoginMsg:       "कृपया जारी रखने के लिए लॉगिन करें।",
  perMonth:           "/महीना",
  perWeek:            "/सप्ताह",
  mostPopular:        "सबसे लोकप्रिय",
  bestValue:          "सर्वोत्तम मूल्य",
  currentPlan:        "वर्तमान प्लान",
  startTrial:         "ट्रायल शुरू करें",
  selectPlan:         "प्लान चुनें",
  faqTitle:           "अक्सर पूछे जाने वाले प्रश्न",
  comparePlans:       "प्लान्स की तुलना करें",
  feature:            "विशेषता",

  enterPhone:         "अपना फ़ोन नंबर दर्ज करें",
  phonePromptSub:     "हम SMS पर वेरिफिकेशन कोड भेजेंगे",
  sendOtp:            "OTP भेजें",
  sendingOtp:         "OTP भेज रहे हैं...",
  enterOtp:           "6-अंकीय कोड दर्ज करें",
  otpPromptSub:       "हमने आपके फ़ोन पर कोड भेजा है",
  verifyOtp:          "वेरिफाई करें",
  verifyingOtp:       "वेरिफाई हो रहा है...",
  resendOtp:          "OTP फिर से भेजें",
  resendIn:           "फिर से भेजें",
  changeNumber:       "नंबर बदलें",
  invalidPhone:       "कृपया सही 10-अंकीय भारतीय मोबाइल नंबर दर्ज करें।",
  otpSent:            "OTP सफलतापूर्वक भेजा गया।",
  otpFailed:          "OTP नहीं भेज सके। फिर से कोशिश करें।",
  otpInvalid:         "गलत OTP। फिर से कोशिश करें।",
  otpResent:          "नया OTP भेज दिया गया।",
  termsAccept:        "जारी रखकर आप हमारी",
  termsLink:          "शर्तें",
  privacyLink:        "गोपनीयता नीति",

  needKundli:         "कुंडली आवश्यक",
  needKundliSub:      "आपकी कुंडली अभी तैयार नहीं है। कृपया पहले कुंडली स्क्रीन से बनाएं।",
  needBothKundli:     "आपकी और आपके साथी की दोनों कुंडलियाँ आवश्यक हैं। दोनों कुंडली स्क्रीन से बनाएं।",
  needPartnerKundli:  "साथी की कुंडली आवश्यक है।",
  analyzingChart:     "आपकी कुंडली पढ़ रहे हैं...",
  fetchFailed:        "लोड नहीं हो सका। फिर से कोशिश करें।",
  reload:             "रीलोड",
  upgradeToProMsg:    "इस सुविधा को अनलॉक करने के लिए Pro पर अपग्रेड करें।",
  upgradeToPro:       "Pro पर अपग्रेड करें",

  careerTitle:        "करियर विश्लेषण",
  financeTitle:       "धन विश्लेषण",
  healthTitle:        "स्वास्थ्य विश्लेषण",
  loveCompatTitle:    "प्रेम अनुकूलता",
  loyaltyTitle:       "वफ़ादारी जाँच",
  breakupTitle:       "ब्रेकअप की संभावना",
  willReturnTitle:    "क्या वे लौटेंगे?",
  futureOutcomeTitle: "भविष्य का परिणाम",

  askLimitReached:    "दैनिक सीमा समाप्त",
  askWithoutKundli:   "बिना कुंडली के मैं केवल सामान्य जानकारी दे सकता हूँ। अपनी जन्म कुंडली बनाएं — फिर मैं आपकी सक्रिय दशा के आधार पर व्यक्तिगत विश्लेषण दूँगा।",
  askDailyLimitOver:  "आज की दैनिक सीमा समाप्त हो गई।",
  askThinking:        "सोच रहा हूँ...",
  askError:           "उत्तर नहीं मिल सका। फिर से कोशिश करें।",

  recentlyDeleted:    "हाल ही में हटाए गए",
  recentlyDeletedSub: "पिछले 24 घंटों में हटाए गए आइटम पुनर्स्थापित किए जा सकते हैं",
  noDeletedItems:     "हाल ही में कुछ नहीं हटाया",
  restore:            "पुनर्स्थापित करें",
  restoreFailed:      "पुनर्स्थापित नहीं हो सका। फिर से कोशिश करें।",
  pullToRefresh:      "रिफ्रेश करने के लिए नीचे खींचें",
  deletedAgo:         "हटाया गया",
  willBeDeletedIn:    "स्थायी रूप से हटा दिया जाएगा",
  deleteAccountTitle: "खाता हटाएं",
  deleteAccountWarn:  "इससे आपका खाता और सारा डेटा स्थायी रूप से हट जाएगा। यह पूर्ववत नहीं किया जा सकता।",
  deleteAccountConfirm:"पुष्टि के लिए DELETE टाइप करें",
  permanentlyDelete:  "स्थायी रूप से हटाएं",

  dailyAlertsTitle:   "दैनिक अलर्ट",
  energyGood:         "अच्छा",
  energyNeutral:      "सामान्य",
  energyChallenging:  "चुनौतीपूर्ण",

  aboutTitle:         "Cosmic Lens के बारे में",
  aboutTagline:       "आपका व्यक्तिगत वैदिक ज्योतिष गाइड",
  versionLabel:       "वर्शन",
  termsTitle:         "सेवा की शर्तें",
  privacyTitle:       "गोपनीयता नीति",

  errReload:          "रीलोड",
  errOops:            "अरे!",
  errSomething:       "कुछ गलत हो गया।",
  errNetwork:         "नेटवर्क त्रुटि। अपना कनेक्शन जाँचें।",
  errKundliRequired:  "कृपया पहले अपनी कुंडली पूरी करें — जन्म विवरण जोड़कर वापस आएं।",
};

/**
 * Get the additional translation table for a language.
 * en/hn/hi are returned in their respective scripts.
 * All other 21 languages fall back to English (so Hinglish never leaks).
 */
export function getTM(lang: UILang): MoreT {
  if (lang === "hn") return { ...EN, ...HN };
  if (lang === "hi") return { ...EN, ...HI };
  return EN;
}
