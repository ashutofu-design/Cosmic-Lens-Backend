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
  catFaceReading:     string;
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
  mdFaceReadingTitle: string;
  mdFaceReadingSub:   string;
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
  mobileNumberLabel:   string;
  mobileNumberPh:      string;
  otpAutoCreateNote:   string;
  orDivider:           string;
  demoLogin:           string;
  demoLoginSub:        string;
  authNotConfigured:   string;
  otpQuotaExceeded:    string;
  otpTooManyAttempts:  string;
  otpExpired:          string;
  otpVerifyTitle:      string;
  otpSentToHeading:    string;
  didntGetOtp:         string;
  loginGenericError:   string;

  // ── Profile / Settings rows ───────────────────────────────
  settingEditProfile:  string;
  settingSubscription: string;
  settingAbout:        string;
  settingHelp:         string;
  settingRateUs:       string;
  settingShareApp:     string;
  settingLegal:        string;
  settingDeleteAcc:    string;
  sectionSupport:      string;
  sectionLegal:        string;
  sectionDanger:       string;
  logoutTitle:         string;
  logoutConfirm:       string;
  logoutCta:           string;
  cancel:              string;
  profilesCount:       string;

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

  // ── Ask Jyotish ────────────────────────────────────────────────
  askLimitReached:     string;
  askWithoutKundli:    string;
  askDailyLimitOver:   string;
  askThinking:         string;
  askError:            string;

  // ── Ask Tab — mode picker + chat ──────────────────────────
  askGreeting:         string;   // "Pranam beta 🙏"
  askGreetingSub:      string;   // "Aaj kis vidhi se margdarshan chahte hain?"
  askModeChat:         string;   // "Ask Anything"
  askModeChatDesc:     string;   // chat description
  askModeChatMeta:     string;   // "Personalized chat · BPHS aadhar"
  askModePrashna:      string;   // "Prashna Kundli"
  askModePrashnaDesc:  string;   // KP number description
  askModePrashnaMeta:  string;   // "K. S. Krishnamurti · Cuspal Interlinks"
  askLegacyDivya:      string;   // "Time-based Divya Prashna (current moment)"
  askInitMessage:      string;   // Acharya intro when chat opens with kundli
  askDemo1:            string;   // Demo turn 1 (assistant)
  askDemo2:            string;   // Demo turn 2 (user sample question)
  askDemo3:            string;   // Demo turn 3 (assistant)
  askSessionExpired:   string;
  askPoweredBy:        string;   // "Powered by Advanced Cosmic Intelligence"
  askAcharyaName:      string;   // "Acharya Vidyasagar"

  // ── Language Picker — Primary indicator ───────────────────
  langPrimaryActive:   string;   // "PRIMARY"
  langPrimaryHint:     string;   // "Entire app uses this language"
  langCurrentBanner:   string;   // "Your primary language" (banner label)

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

  // ── Lucky screen ──────────────────────────────────────────
  luckyHeaderTodaysPulse: string;
  luckyHeaderColors:      string;
  luckyHeaderNumbers:     string;
  luckyHeaderDays:        string;
  luckyHeaderGemstone:    string;
  luckyHeaderDeity:       string;
  luckyHeaderMantra:      string;
  luckyLabelDirection:    string;
  luckyLabelMetal:        string;
  luckyLabelElement:      string;
  luckyGemstoneTip:       string;
  luckyDeityTip:          string;
  luckyMantraTip:         string;

  // ── Panchang screen ───────────────────────────────────────
  panSunrise:        string;
  panSunset:         string;
  panVaar:           string;
  panTithi:          string;
  panNakshatra:      string;
  panYoga:           string;
  panKarana:         string;
  panBrahmaMuhurta:  string;
  panBrahmaTip:      string;
  panRahuKaalLbl:    string;
  panRahuTip:        string;
  panYamaghanta:     string;
  panYamaTip:        string;
  panGulika:         string;
  panGulikaTip:      string;
  panAbhijitLbl:     string;
  panAbhijitTip:     string;
  panFestivalsYear:  string;
  panBadgeNational:  string;

  // ── Muhurat screen ────────────────────────────────────────
  muhSubtitle:    string;
  muhEmpty:       string;
  muhAvoid:       string;
  muhNakshatra:   string;
  muhNote:        string;
  muhCatShadi:    string;
  muhCatShadiSub: string;
  muhCatGriha:    string;
  muhCatGrihaSub: string;
  muhCatBiz:      string;
  muhCatBizSub:   string;
  muhCatVehicle:  string;
  muhCatVehSub:   string;
  muhCatNamkaran: string;
  muhCatNamSub:   string;
  muhCatMundan:   string;
  muhCatMundanSub:string;
  muhCatThread:   string;
  muhCatThreadSub:string;
  muhCatTravel:   string;
  muhCatTravelSub:string;

  // ── Remedies screen ───────────────────────────────────────
  remSubtitle:      string;
  remPujaDay:       string;
  remGemstoneLbl:   string;
  remGemstoneTip:   string;
  remMantraLbl:     string;
  remDaanLbl:       string;
  remDaanTip:       string;
  remUpayLbl:       string;
  remWeakSignsLbl:  string; // "Signs of weak {planet}"

  // ── Numerology screen ────────────────────────────────────
  numSubtitle:        string;
  numFreeBadge:       string;
  numSelectProfile:   string;
  numNoProfileTitle:  string;
  numNoProfileBody:   string;
  numSetupProfile:    string;
  numAutoSynced:      string;
  numFreeSection:     string;
  numTapHint:         string;
  numLifePathLbl:     string;
  numLifePathHi:      string;
  numDestinyLbl:      string;
  numDestinyHi:       string;
  numSoulUrgeLbl:     string;
  numSoulUrgeHi:      string;
  numPersonalYM:      string;
  numYearPrefix:      string; // "Year"
  numCareer:          string;
  numLove:            string;
  numStrength:        string;
  numWeakness:        string;
  numRemedy:          string;
  numLuckyNumbers:    string;
  numLuckyColor:      string;
  numPremiumDivider:  string;
  numUnlockTitle:     string;
  numUnlockBody:      string;
  numAdvancedSection: string;
  numLockPersonality: string;
  numLockMaturity:    string;
  numLockCareerFin:   string;
  numLockLoveCompat:  string;
  numLockNameCorr:    string;
  numLockChallenges:  string;
  numCtaTitle:        string;
  numCtaSub:          string;
  numFooterNote:      string;
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
  catFaceReading:     "👁️ Face Reading Pro",
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
  mdNumerologyTitle:  "Numerology Advanced",
  mdNumerologySub:    "Deep life path & destiny analysis",
  mdFaceReadingTitle: "Face Reading Pro",
  mdFaceReadingSub:   "Vedic + Science fusion · 80+ pages",
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
  mobileNumberLabel:  "MOBILE NUMBER",
  mobileNumberPh:     "10-digit number",
  otpAutoCreateNote:  "You'll receive a 6-digit OTP via SMS. First-time numbers get an account automatically.",
  orDivider:          "or",
  demoLogin:          "Demo Login",
  demoLoginSub:       "For testing — go straight in",
  authNotConfigured:  "Authentication setup pending. Please contact support.",
  otpQuotaExceeded:   "Today's SMS quota is full. Try again tomorrow.",
  otpTooManyAttempts: "Too many attempts. Please try again later.",
  otpExpired:         "OTP expired. Please resend.",
  otpVerifyTitle:     "Verify OTP",
  otpSentToHeading:   "We sent a 6-digit code to",
  didntGetOtp:        "Didn't get the OTP?",
  loginGenericError:  "Couldn't complete login. Please try again.",

  // Profile / Settings
  settingEditProfile: "Edit Profile",
  settingSubscription:"Subscription",
  settingAbout:       "About Cosmic Lens",
  settingHelp:        "Help & Support",
  settingRateUs:      "Rate Us ⭐",
  settingShareApp:    "Share App",
  settingLegal:       "Legal & Policies",
  settingDeleteAcc:   "Delete My Account",
  sectionSupport:     "SUPPORT & ABOUT",
  sectionLegal:       "LEGAL & POLICIES",
  sectionDanger:      "DANGER ZONE",
  logoutTitle:        "Logout",
  logoutConfirm:      "Are you sure you want to log out?",
  logoutCta:          "Logout",
  cancel:             "Cancel",
  profilesCount:      "profiles",

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

  // Ask Jyotish
  askLimitReached:    "Daily limit reached",
  askWithoutKundli:   "Without a Kundli I can only give general information. Create your birth chart — then I'll give you a personalized analysis based on your active dasha.",
  askDailyLimitOver:  "Your daily limit is over.",
  askThinking:        "Thinking...",
  askError:           "Could not get an answer. Please try again.",

  // Ask Tab — mode picker + chat
  askGreeting:        "Pranam 🙏",
  askGreetingSub:     "Which path of guidance would you like today?",
  askModeChat:        "Ask Anything",
  askModeChatDesc:    "Talk directly with the Acharya — kundli, dasha, marriage, career, health — ask anything.",
  askModeChatMeta:    "Personalized chat · Based on BPHS",
  askModePrashna:     "Prashna Kundli",
  askModePrashnaDesc: "Think of any number 1-249 — that number becomes the lagna of your chart, and the cusp's sub-lord gives the precise answer.",
  askModePrashnaMeta: "K. S. Krishnamurti · Cuspal Interlinks",
  askLegacyDivya:     "Time-based Divya Prashna (current moment)",
  askInitMessage:     "Pranam 🙏 I am Acharya Vidyasagar from Kashi. Your kundli is in front of me. Ask any question — marriage, career, health, wealth — without hesitation.",
  askDemo1:           "Pranam 🙏 I am Acharya Vidyasagar — reading kundlis in Kashi for 35 years. You may ask me anything about your kundli, dasha, marriage, career, or health.",
  askDemo2:           "How will my career be this year?",
  askDemo3:           "Without seeing your kundli I can only give general guidance. Please create your birth chart first — then I can give you a fully personalized analysis based on your active grahas, dasha and yogas.",
  askSessionExpired:  "Session expired — please log out and log in again.",
  askPoweredBy:       "Powered by Advanced Cosmic Intelligence",
  askAcharyaName:     "Acharya Vidyasagar",

  // Language Picker — Primary indicator
  langPrimaryActive:  "PRIMARY",
  langPrimaryHint:    "Entire app uses this language everywhere",
  langCurrentBanner:  "Your primary language",

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

  // Lucky screen
  luckyHeaderTodaysPulse: "✨ TODAY'S PULSE",
  luckyHeaderColors:      "🎨 LUCKY COLORS",
  luckyHeaderNumbers:     "🔢 LUCKY NUMBERS",
  luckyHeaderDays:        "📅 LUCKY DAYS",
  luckyHeaderGemstone:    "💎 LUCKY GEMSTONE",
  luckyHeaderDeity:       "🛕 GUARDIAN DEITY",
  luckyHeaderMantra:      "🔔 PLANETARY MANTRA",
  luckyLabelDirection:    "⬆️ DIRECTION",
  luckyLabelMetal:        "⚗️ METAL",
  luckyLabelElement:      "ELEMENT",
  luckyGemstoneTip:       "Wear in gold or silver",
  luckyDeityTip:          "Worship and meditation bring special blessings",
  luckyMantraTip:         "Chant 108 times during an auspicious time",

  // Panchang
  panSunrise:        "Sunrise",
  panSunset:         "Sunset",
  panVaar:           "Weekday",
  panTithi:          "Tithi",
  panNakshatra:      "Nakshatra",
  panYoga:           "Yoga",
  panKarana:         "Karana",
  panBrahmaMuhurta:  "🌟 BRAHMA MUHURTA",
  panBrahmaTip:      "Most auspicious time for worship, meditation and new beginnings",
  panRahuKaalLbl:    "Rahu Kaal",
  panRahuTip:        "Avoid any auspicious activity during this time",
  panYamaghanta:     "Yamaghanta",
  panYamaTip:        "Avoid auspicious work",
  panGulika:         "Gulika Kaal",
  panGulikaTip:      "Do not perform auspicious rituals",
  panAbhijitLbl:     "ℹ️ ABHIJIT MUHURTA (AUSPICIOUS)",
  panAbhijitTip:     "Best time for any auspicious work — the most auspicious muhurat of the day.",
  panFestivalsYear:  "📅 MAJOR FESTIVALS & NATIONAL HOLIDAYS",
  panBadgeNational:  "National",

  // Muhurat
  muhSubtitle:    "Auspicious time for every event",
  muhEmpty:       "No muhurats listed for this category yet. Coming soon.",
  muhAvoid:       "Avoid",
  muhNakshatra:   "Nakshatra",
  muhNote:        "Dates are approximate. Please confirm exact time and local timing with a pandit.",
  muhCatShadi:    "Wedding Muhurat",
  muhCatShadiSub: "Auspicious days for marriage",
  muhCatGriha:    "Griha Pravesh",
  muhCatGrihaSub: "Entering a new home",
  muhCatBiz:      "Business Start",
  muhCatBizSub:   "Day to start a business",
  muhCatVehicle:  "Vehicle Purchase",
  muhCatVehSub:   "Buying a new vehicle",
  muhCatNamkaran: "Naming Ceremony",
  muhCatNamSub:   "Naming the baby",
  muhCatMundan:   "Mundan Ceremony",
  muhCatMundanSub:"Baby's first haircut",
  muhCatThread:   "Yagyopavit",
  muhCatThreadSub:"Janeu / Upanayana",
  muhCatTravel:   "Travel Muhurat",
  muhCatTravelSub:"Auspicious time to travel",

  // Remedies
  remSubtitle:      "Mantra, charity and remedies",
  remPujaDay:       "Worship day",
  remGemstoneLbl:   "💎 GEMSTONE",
  remGemstoneTip:   "Wear in gold or silver during an auspicious muhurat",
  remMantraLbl:     "🔔 PLANETARY MANTRA",
  remDaanLbl:       "🤲 CHARITY (DAAN)",
  remDaanTip:       "Donating on this day or during an eclipse gives special benefit",
  remUpayLbl:       "⚡ REMEDIES",
  remWeakSignsLbl:  "⚠️ SIGNS OF WEAK {planet}",

  // Numerology
  numSubtitle:        "Vedic Number Science",
  numFreeBadge:       "FREE",
  numSelectProfile:   "SELECT PROFILE",
  numNoProfileTitle:  "No Kundli Profile Found",
  numNoProfileBody:   "Please create a Kundli profile first. Numerology reads directly from your birth details.",
  numSetupProfile:    "Set Up Profile →",
  numAutoSynced:      "Auto-synced",
  numFreeSection:     "🆓 FREE NUMEROLOGY",
  numTapHint:         "Tap any card to expand full details",
  numLifePathLbl:     "LIFE PATH NUMBER",
  numLifePathHi:      "Life Path",
  numDestinyLbl:      "DESTINY / EXPRESSION NUMBER",
  numDestinyHi:       "Destiny",
  numSoulUrgeLbl:     "SOUL URGE NUMBER",
  numSoulUrgeHi:      "Soul Urge",
  numPersonalYM:      "⏰ PERSONAL YEAR · MONTH",
  numYearPrefix:      "Year",
  numCareer:          "💼 Career",
  numLove:            "❤️ Love",
  numStrength:        "⚡ Strength",
  numWeakness:        "⚠️ Weakness",
  numRemedy:          "🙏 Remedy",
  numLuckyNumbers:    "Lucky Numbers",
  numLuckyColor:      "Lucky Color",
  numPremiumDivider:  "PREMIUM REPORT",
  numUnlockTitle:     "Unlock Your Full Report",
  numUnlockBody:      "Personality Number · Maturity Number · Name Correction · Career Insights · Love Compatibility · Challenges & Remedies",
  numAdvancedSection: "🔒 ADVANCED NUMEROLOGY",
  numLockPersonality: "Personality Number",
  numLockMaturity:    "Maturity Number",
  numLockCareerFin:   "Career & Finance Insights",
  numLockLoveCompat:  "Love Compatibility Report",
  numLockNameCorr:    "Name Correction Suggestions",
  numLockChallenges:  "Challenges, Weak Points & Remedies",
  numCtaTitle:        "Unlock Full Numerology Report",
  numCtaSub:          "Get Personality, Maturity, Love, Career & Remedies",
  numFooterNote:      "Calculations use the Pythagorean Numerology system. Life Path, Destiny, and Soul Urge numbers are derived from your Kundli profile data — no re-entry needed.",
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
  catFaceReading:     "👁️ Face Reading Pro",
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
  mdNumerologyTitle:  "Numerology Advanced",
  mdNumerologySub:    "Deep life path & destiny analysis",
  mdFaceReadingTitle: "Face Reading Pro",
  mdFaceReadingSub:   "Vedic + Science fusion · 80+ pages",
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
  mobileNumberLabel:  "MOBILE NUMBER",
  mobileNumberPh:     "10-digit number",
  otpAutoCreateNote:  "SMS se 6-digit OTP aayega. Pehli baar number daalne par account automatic ban jayega.",
  orDivider:          "ya phir",
  demoLogin:          "Demo Login",
  demoLoginSub:       "Testing ke liye — seedha andar jayein",
  authNotConfigured:  "Authentication setup pending. Admin se contact karein.",
  otpQuotaExceeded:   "Aaj ka SMS quota khatam. Kal try karein.",
  otpTooManyAttempts: "Bahut zyada attempts. Thodi der baad try karein.",
  otpExpired:         "OTP expire ho gaya. Resend karein.",
  otpVerifyTitle:     "OTP Verify Karein",
  otpSentToHeading:   "Hum ne 6-digit code bheja hai",
  didntGetOtp:        "OTP nahi mila?",
  loginGenericError:  "Login complete nahi ho saka. Dobara try karein.",

  // Profile / Settings
  settingEditProfile: "Profile Edit karein",
  settingSubscription:"Subscription",
  settingAbout:       "Cosmic Lens ke baare mein",
  settingHelp:        "Help & Support",
  settingRateUs:      "Rate karein ⭐",
  settingShareApp:    "App Share karein",
  settingLegal:       "Legal & Policies",
  settingDeleteAcc:   "Account Delete karein",
  sectionSupport:     "SUPPORT & ABOUT",
  sectionLegal:       "LEGAL & POLICIES",
  sectionDanger:      "DANGER ZONE",
  logoutTitle:        "Logout",
  logoutConfirm:      "Kya aap logout karna chahte hain?",
  logoutCta:          "Logout",
  cancel:             "Cancel",
  profilesCount:      "profiles",

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

  // Ask Tab — mode picker + chat
  askGreeting:        "Pranam beta 🙏",
  askGreetingSub:     "Aaj kis vidhi se margdarshan chahte hain?",
  askModeChat:        "Ask Anything",
  askModeChatDesc:    "Acharya se seedhi baat — kundli, dasha, vivah, karya, swasthya — koi bhi prashna poochho.",
  askModeChatMeta:    "Personalized chat · BPHS aadhar",
  askModePrashna:     "Prashna Kundli",
  askModePrashnaDesc: "Mann mein ek number 1-249 socho — wahi sankhya aapki kundli ka lagna banegi, cusp sub-lord se sahi jawab.",
  askModePrashnaMeta: "K. S. Krishnamurti · Cuspal Interlinks",
  askLegacyDivya:     "Time-based Divya Prashna (current moment)",
  askInitMessage:     "Pranam beta 🙏 Mai Acharya Vidyasagar — Kashi se. Aapki kundli mere saamne hai. Vivah, karya, swasthya, dhan — jo bhi prashna ho, nishankoch poochiye.",
  askDemo1:           "Pranam beta 🙏 Mai Acharya Vidyasagar — 35 saal se kundli padh raha hu Kashi mein. Aap apni kundli, dasha, vivah, karya, swasthya — kuch bhi pooch sakte hain, mai margdarshan dunga.",
  askDemo2:           "Mera career is saal kaisa rahega?",
  askDemo3:           "Beta, bina kundli dekhe mai sirf saamanya baat keh sakta hu. Aap pehle apni janm-kundli banaiye — phir mai aapke graha, dasha aur yog dekh ke ekdum personalized margdarshan dunga.",
  askSessionExpired:  "Session expired — kripya logout karke phir login karein.",
  askPoweredBy:       "Powered by Advanced Cosmic Intelligence",
  askAcharyaName:     "Acharya Vidyasagar",

  // Language Picker — Primary indicator
  langPrimaryActive:  "PRIMARY",
  langPrimaryHint:    "Poori app isi bhasha mein chalegi",
  langCurrentBanner:  "Aapki primary bhasha",

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

  // Lucky
  luckyHeaderTodaysPulse: "✨ AAJ KA YOG",
  luckyHeaderColors:      "🎨 LUCKY RANG",
  luckyHeaderNumbers:     "🔢 LUCKY ANK",
  luckyHeaderDays:        "📅 LUCKY DIN",
  luckyHeaderGemstone:    "💎 LUCKY RATAN",
  luckyHeaderDeity:       "🛕 ARADHYA DEVTA",
  luckyHeaderMantra:      "🔔 GRAHA MANTRA",
  luckyLabelDirection:    "⬆️ DISHA",
  luckyLabelMetal:        "⚗️ DHATU",
  luckyLabelElement:      "TATVA",
  luckyGemstoneTip:       "Sone ya Chandi mein dharan karein",
  luckyDeityTip:          "Puja aur dhyan se vishesh laabh milega",
  luckyMantraTip:         "Shubh muhurat mein 108 baar jaap karein",

  // Panchang
  panSunrise:       "Sunrise",
  panSunset:        "Sunset",
  panVaar:          "Vaar (Din)",
  panTithi:         "Tithi",
  panNakshatra:     "Nakshatra",
  panYoga:          "Yoga",
  panKarana:        "Karana",
  panBrahmaMuhurta: "🌟 BRAHMA MUHURTA",
  panBrahmaTip:     "Puja, dhyan aur naye kaaryon ke liye param shubh samay",
  panRahuKaalLbl:   "Rahu Kaal",
  panRahuTip:       "Is samay mein koi shubh kaarya na karein",
  panYamaghanta:    "Yamaghanta",
  panYamaTip:       "Shubh kaarya avoid karein",
  panGulika:        "Gulika Kaal",
  panGulikaTip:     "Maanglik kaarya na karein",
  panAbhijitLbl:    "ℹ️ ABHIJIT MUHURTA (SHUBH)",
  panAbhijitTip:    "Har shubh kaarya ke liye uchit samay. Din ka sabse shubh muhurta.",
  panFestivalsYear: "📅 PRAMUKH TYOHAR & RASHTRIYA PARV",
  panBadgeNational: "Rashtriya",

  // Muhurat
  muhSubtitle:    "Har kaarya ke liye shubh samay",
  muhEmpty:       "Is category ke liye abhi muhurat nahi hai. Jald aayenge.",
  muhAvoid:       "Avoid",
  muhNakshatra:   "Nakshatra",
  muhNote:        "Muhurat dates approximate hain. Pandit ji se exact time aur local timing confirm zaroor karein.",
  muhCatShadi:    "Vivah Muhurat",
  muhCatShadiSub: "Shadi ke shubh din",
  muhCatGriha:    "Griha Pravesh",
  muhCatGrihaSub: "Naye ghar mein pravesh",
  muhCatBiz:      "Vyapar Aarambh",
  muhCatBizSub:   "Business shuru karne ka din",
  muhCatVehicle:  "Vahan Kharidi",
  muhCatVehSub:   "Naya vahan kharidna",
  muhCatNamkaran: "Namkaran Muhurat",
  muhCatNamSub:   "Bacche ka naam rakhna",
  muhCatMundan:   "Mundan Muhurat",
  muhCatMundanSub:"Bacche ka pehla mudan",
  muhCatThread:   "Yagyopavit Muhurat",
  muhCatThreadSub:"Janeu / Upanayana",
  muhCatTravel:   "Yatra Muhurat",
  muhCatTravelSub:"Safar ke liye shubh samay",

  // Remedies
  remSubtitle:     "Mantra, Daan aur Remedies",
  remPujaDay:      "Puja ka din",
  remGemstoneLbl:  "💎 RATAN (GEMSTONE)",
  remGemstoneTip:  "Sone ya Chandi mein, shubh muhurat mein dharan karein",
  remMantraLbl:    "🔔 GRAHA MANTRA",
  remDaanLbl:      "🤲 DAAN (CHARITY)",
  remDaanTip:      "Is din ya grahan ke samay daan karna vishesh phal deta hai",
  remUpayLbl:      "⚡ UPAY (REMEDIES)",
  remWeakSignsLbl: "⚠️ WEAK {planet} KE LAKSHAN",

  // Numerology
  numSubtitle:        "Vedic Anka Vigyaan",
  numFreeBadge:       "FREE",
  numSelectProfile:   "PROFILE CHUNEIN",
  numNoProfileTitle:  "Koi Kundli Profile Nahi Mili",
  numNoProfileBody:   "Pehle Kundli profile banayein. Numerology aapki birth details se direct calculate hoti hai.",
  numSetupProfile:    "Profile Banayein →",
  numAutoSynced:      "Auto-synced",
  numFreeSection:     "🆓 FREE NUMEROLOGY",
  numTapHint:         "Poori details ke liye kisi bhi card par tap karein",
  numLifePathLbl:     "LIFE PATH NUMBER",
  numLifePathHi:      "Jeevan Path Sankhya",
  numDestinyLbl:      "DESTINY / EXPRESSION NUMBER",
  numDestinyHi:       "Bhagya Sankhya",
  numSoulUrgeLbl:     "SOUL URGE NUMBER",
  numSoulUrgeHi:      "Aatma ki Iccha",
  numPersonalYM:      "⏰ PERSONAL YEAR · MONTH",
  numYearPrefix:      "Saal",
  numCareer:          "💼 Career",
  numLove:            "❤️ Pyaar",
  numStrength:        "⚡ Shakti",
  numWeakness:        "⚠️ Kamzori",
  numRemedy:          "🙏 Upay",
  numLuckyNumbers:    "Lucky Numbers",
  numLuckyColor:      "Lucky Rang",
  numPremiumDivider:  "PREMIUM REPORT",
  numUnlockTitle:     "Apni Poori Report Unlock Karein",
  numUnlockBody:      "Personality Number · Maturity Number · Naam Sudhaar · Career Insights · Love Compatibility · Challenges & Upay",
  numAdvancedSection: "🔒 ADVANCED NUMEROLOGY",
  numLockPersonality: "Personality Number",
  numLockMaturity:    "Maturity Number",
  numLockCareerFin:   "Career & Finance Insights",
  numLockLoveCompat:  "Love Compatibility Report",
  numLockNameCorr:    "Naam Sudhaar Suggestions",
  numLockChallenges:  "Challenges, Weak Points & Upay",
  numCtaTitle:        "Poori Numerology Report Unlock Karein",
  numCtaSub:          "Personality, Maturity, Love, Career aur Upay paayein",
  numFooterNote:      "Calculations Pythagorean Numerology system pe based hain. Life Path, Destiny aur Soul Urge numbers aapki Kundli profile se aate hain — re-entry ki zaroorat nahi.",
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
  catFaceReading:     "👁️ फेस रीडिंग प्रो",
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
  mdNumerologyTitle:  "अंकशास्त्र Advanced",
  mdNumerologySub:    "गहरा लाइफ पाथ और भाग्य विश्लेषण",
  mdFaceReadingTitle: "फेस रीडिंग प्रो",
  mdFaceReadingSub:   "वैदिक + विज्ञान फ्यूजन · 80+ पेज",
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
  mobileNumberLabel:  "मोबाइल नंबर",
  mobileNumberPh:     "10-अंकीय नंबर",
  otpAutoCreateNote:  "SMS पर 6-अंकीय OTP आएगा। पहली बार नंबर डालने पर खाता अपने आप बन जाएगा।",
  orDivider:          "या",
  demoLogin:          "डेमो लॉगिन",
  demoLoginSub:       "टेस्टिंग के लिए — सीधे अंदर जाएं",
  authNotConfigured:  "ऑथेंटिकेशन सेटअप अभी पेंडिंग है। कृपया सपोर्ट से संपर्क करें।",
  otpQuotaExceeded:   "आज का SMS कोटा पूरा हो गया है। कल कोशिश करें।",
  otpTooManyAttempts: "बहुत ज़्यादा कोशिशें। थोड़ी देर बाद कोशिश करें।",
  otpExpired:         "OTP की अवधि समाप्त हो गई है। फिर से भेजें।",
  otpVerifyTitle:     "OTP वेरिफाई करें",
  otpSentToHeading:   "हमने 6-अंकीय कोड भेजा है",
  didntGetOtp:        "OTP नहीं मिला?",
  loginGenericError:  "लॉगिन पूरा नहीं हो सका। फिर से कोशिश करें।",

  // Profile / Settings
  settingEditProfile: "प्रोफ़ाइल एडिट करें",
  settingSubscription:"सब्सक्रिप्शन",
  settingAbout:       "Cosmic Lens के बारे में",
  settingHelp:        "मदद और सहायता",
  settingRateUs:      "रेट करें ⭐",
  settingShareApp:    "ऐप शेयर करें",
  settingLegal:       "कानूनी और नीतियाँ",
  settingDeleteAcc:   "मेरा अकाउंट डिलीट करें",
  sectionSupport:     "सहायता और जानकारी",
  sectionLegal:       "कानूनी और नीतियाँ",
  sectionDanger:      "ख़तरनाक ज़ोन",
  logoutTitle:        "लॉगआउट",
  logoutConfirm:      "क्या आप लॉगआउट करना चाहते हैं?",
  logoutCta:          "लॉगआउट",
  cancel:             "रद्द करें",
  profilesCount:      "प्रोफ़ाइल",

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

  // Ask Tab — mode picker + chat
  askGreeting:        "प्रणाम बेटा 🙏",
  askGreetingSub:     "आज किस विधि से मार्गदर्शन चाहते हैं?",
  askModeChat:        "कोई भी प्रश्न पूछें",
  askModeChatDesc:    "आचार्य से सीधी बात — कुंडली, दशा, विवाह, कार्य, स्वास्थ्य — कोई भी प्रश्न पूछें।",
  askModeChatMeta:    "व्यक्तिगत वार्ता · BPHS आधारित",
  askModePrashna:     "प्रश्न कुंडली",
  askModePrashnaDesc: "1 से 249 के बीच कोई संख्या सोचें — वही संख्या आपकी कुंडली का लग्न बनेगी, और कस्प के सब-लॉर्ड से सटीक उत्तर मिलेगा।",
  askModePrashnaMeta: "के. एस. कृष्णमूर्ति · कस्पल इंटरलिंक्स",
  askLegacyDivya:     "समय आधारित दिव्य प्रश्न (वर्तमान क्षण)",
  askInitMessage:     "प्रणाम बेटा 🙏 मैं आचार्य विद्यासागर — काशी से। आपकी कुंडली मेरे सामने है। विवाह, कार्य, स्वास्थ्य, धन — जो भी प्रश्न हो, निःसंकोच पूछिए।",
  askDemo1:           "प्रणाम बेटा 🙏 मैं आचार्य विद्यासागर — 35 वर्षों से कुंडली पढ़ रहा हूँ काशी में। आप अपनी कुंडली, दशा, विवाह, कार्य, स्वास्थ्य — कुछ भी पूछ सकते हैं, मैं मार्गदर्शन दूँगा।",
  askDemo2:           "इस वर्ष मेरा करियर कैसा रहेगा?",
  askDemo3:           "बेटा, बिना कुंडली देखे मैं केवल सामान्य बात कह सकता हूँ। आप पहले अपनी जन्म-कुंडली बनाइए — फिर मैं आपके ग्रह, दशा और योग देखकर एकदम व्यक्तिगत मार्गदर्शन दूँगा।",
  askSessionExpired:  "सत्र समाप्त — कृपया लॉगआउट करके पुनः लॉगिन करें।",
  askPoweredBy:       "Cosmic Intelligence द्वारा संचालित",
  askAcharyaName:     "आचार्य विद्यासागर",

  // Language Picker — Primary indicator
  langPrimaryActive:  "मुख्य",
  langPrimaryHint:    "पूरी ऐप इसी भाषा में चलेगी",
  langCurrentBanner:  "आपकी मुख्य भाषा",

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

  // Lucky
  luckyHeaderTodaysPulse: "✨ आज का योग",
  luckyHeaderColors:      "🎨 शुभ रंग",
  luckyHeaderNumbers:     "🔢 शुभ अंक",
  luckyHeaderDays:        "📅 शुभ दिन",
  luckyHeaderGemstone:    "💎 शुभ रत्न",
  luckyHeaderDeity:       "🛕 आराध्य देव",
  luckyHeaderMantra:      "🔔 ग्रह मंत्र",
  luckyLabelDirection:    "⬆️ दिशा",
  luckyLabelMetal:        "⚗️ धातु",
  luckyLabelElement:      "तत्व",
  luckyGemstoneTip:       "सोने या चाँदी में धारण करें",
  luckyDeityTip:          "पूजा और ध्यान से विशेष लाभ मिलेगा",
  luckyMantraTip:         "शुभ मुहूर्त में 108 बार जाप करें",

  // Panchang
  panSunrise:       "सूर्योदय",
  panSunset:        "सूर्यास्त",
  panVaar:          "वार (दिन)",
  panTithi:         "तिथि",
  panNakshatra:     "नक्षत्र",
  panYoga:          "योग",
  panKarana:        "करण",
  panBrahmaMuhurta: "🌟 ब्रह्म मुहूर्त",
  panBrahmaTip:     "पूजा, ध्यान और नए कार्यों के लिए परम शुभ समय",
  panRahuKaalLbl:   "राहु काल",
  panRahuTip:       "इस समय में कोई शुभ कार्य न करें",
  panYamaghanta:    "यमघण्ट",
  panYamaTip:       "शुभ कार्य न करें",
  panGulika:        "गुलिक काल",
  panGulikaTip:     "मांगलिक कार्य न करें",
  panAbhijitLbl:    "ℹ️ अभिजित मुहूर्त (शुभ)",
  panAbhijitTip:    "हर शुभ कार्य के लिए उचित समय। दिन का सबसे शुभ मुहूर्त।",
  panFestivalsYear: "📅 प्रमुख त्यौहार और राष्ट्रीय पर्व",
  panBadgeNational: "राष्ट्रीय",

  // Muhurat
  muhSubtitle:    "हर कार्य के लिए शुभ समय",
  muhEmpty:       "इस श्रेणी के लिए अभी मुहूर्त उपलब्ध नहीं हैं। जल्द आ रहे हैं।",
  muhAvoid:       "बचें",
  muhNakshatra:   "नक्षत्र",
  muhNote:        "मुहूर्त की तारीखें अनुमानित हैं। पंडित जी से सटीक समय और लोकल टाइमिंग अवश्य पुष्टि करें।",
  muhCatShadi:    "विवाह मुहूर्त",
  muhCatShadiSub: "शादी के शुभ दिन",
  muhCatGriha:    "गृह प्रवेश",
  muhCatGrihaSub: "नए घर में प्रवेश",
  muhCatBiz:      "व्यापार आरंभ",
  muhCatBizSub:   "व्यापार शुरू करने का दिन",
  muhCatVehicle:  "वाहन खरीद",
  muhCatVehSub:   "नया वाहन खरीदना",
  muhCatNamkaran: "नामकरण मुहूर्त",
  muhCatNamSub:   "बच्चे का नाम रखना",
  muhCatMundan:   "मुंडन मुहूर्त",
  muhCatMundanSub:"बच्चे का पहला मुंडन",
  muhCatThread:   "यज्ञोपवीत मुहूर्त",
  muhCatThreadSub:"जनेऊ / उपनयन",
  muhCatTravel:   "यात्रा मुहूर्त",
  muhCatTravelSub:"सफ़र के लिए शुभ समय",

  // Remedies
  remSubtitle:     "मंत्र, दान और उपाय",
  remPujaDay:      "पूजा का दिन",
  remGemstoneLbl:  "💎 रत्न",
  remGemstoneTip:  "सोने या चाँदी में, शुभ मुहूर्त में धारण करें",
  remMantraLbl:    "🔔 ग्रह मंत्र",
  remDaanLbl:      "🤲 दान",
  remDaanTip:      "इस दिन या ग्रहण के समय दान करना विशेष फल देता है",
  remUpayLbl:      "⚡ उपाय",
  remWeakSignsLbl: "⚠️ कमज़ोर {planet} के लक्षण",

  // Numerology
  numSubtitle:        "वैदिक अंक विज्ञान",
  numFreeBadge:       "निःशुल्क",
  numSelectProfile:   "प्रोफ़ाइल चुनें",
  numNoProfileTitle:  "कोई कुंडली प्रोफ़ाइल नहीं मिली",
  numNoProfileBody:   "कृपया पहले कुंडली प्रोफ़ाइल बनाएं। अंकज्योतिष आपकी जन्म जानकारी से सीधे गणना करता है।",
  numSetupProfile:    "प्रोफ़ाइल बनाएं →",
  numAutoSynced:      "ऑटो-सिंक",
  numFreeSection:     "🆓 निःशुल्क अंकज्योतिष",
  numTapHint:         "पूरी जानकारी के लिए किसी भी कार्ड पर टैप करें",
  numLifePathLbl:     "जीवन पथ संख्या",
  numLifePathHi:      "जीवन पथ",
  numDestinyLbl:      "भाग्य संख्या",
  numDestinyHi:       "भाग्य",
  numSoulUrgeLbl:     "आत्मा की इच्छा",
  numSoulUrgeHi:      "अंतर्मन",
  numPersonalYM:      "⏰ व्यक्तिगत वर्ष · माह",
  numYearPrefix:      "वर्ष",
  numCareer:          "💼 करियर",
  numLove:            "❤️ प्रेम",
  numStrength:        "⚡ शक्ति",
  numWeakness:        "⚠️ कमज़ोरी",
  numRemedy:          "🙏 उपाय",
  numLuckyNumbers:    "शुभ अंक",
  numLuckyColor:      "शुभ रंग",
  numPremiumDivider:  "प्रीमियम रिपोर्ट",
  numUnlockTitle:     "अपनी पूरी रिपोर्ट अनलॉक करें",
  numUnlockBody:      "व्यक्तित्व संख्या · परिपक्वता संख्या · नाम सुधार · करियर अंतर्दृष्टि · प्रेम संगति · चुनौतियां और उपाय",
  numAdvancedSection: "🔒 उन्नत अंकज्योतिष",
  numLockPersonality: "व्यक्तित्व संख्या",
  numLockMaturity:    "परिपक्वता संख्या",
  numLockCareerFin:   "करियर और वित्त अंतर्दृष्टि",
  numLockLoveCompat:  "प्रेम संगति रिपोर्ट",
  numLockNameCorr:    "नाम सुधार सुझाव",
  numLockChallenges:  "चुनौतियां, कमज़ोरियां और उपाय",
  numCtaTitle:        "पूरी अंकज्योतिष रिपोर्ट अनलॉक करें",
  numCtaSub:          "व्यक्तित्व, परिपक्वता, प्रेम, करियर और उपाय पाएं",
  numFooterNote:      "गणनाएं पाइथागोरस अंकज्योतिष प्रणाली पर आधारित हैं। जीवन पथ, भाग्य और आत्मा की इच्छा संख्याएं आपकी कुंडली प्रोफ़ाइल से ली जाती हैं — दोबारा दर्ज करने की आवश्यकता नहीं।",
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
