// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Extended Translation Keys (for screens not in base i18n.ts)
// ══════════════════════════════════════════════════════════════════════════════
import type { UILang } from "./i18n";

export interface ExtTranslations {
  // ── Common / Shared UI ───────────────────────────────────────────────────
  calculating:       string;
  noData:            string;
  selectProfile:     string;
  birthDataNeeded:   string;
  goBack:            string;
  viewReport:        string;
  matchReport:       string;
  present:           string;
  notPresent:        string;
  auspicious:        string;
  inauspicious:      string;
  daily:             string;
  weekly:            string;
  monthly:           string;
  yearly:            string;
  selectSign:        string;

  // ── Rashifal ──────────────────────────────────────────────────────────────
  rashifalTitle:    string;
  todaysRashifal:   string;
  loveSection:      string;
  careerSection:    string;
  healthSection:    string;
  moneySection:     string;

  // ── Panchang ──────────────────────────────────────────────────────────────
  panchangTitle:    string;
  tithi:            string;
  vara:             string;
  yogaPanchang:     string;
  karana:           string;
  sunriseLabel:     string;
  sunsetLabel:      string;
  auspiciousTimes:  string;
  rahukaal:         string;
  moonSignLabel:    string;
  paksha:           string;
  festivals:        string;

  // ── Kundli Milan ──────────────────────────────────────────────────────────
  kundliMilanTitle:    string;
  kundliMilanSub:      string;
  groomLabel:          string;
  brideLabel:          string;
  checkCompatibility:  string;
  gunaScore:           string;
  outOf36:             string;
  manglikLabel:        string;
  selfProfile:         string;
  partnerProfile:      string;
  addPartner:          string;
  birthDataMissing:    string;

  // ── Milan Result ──────────────────────────────────────────────────────────
  milanResult:       string;
  strengthsLabel:    string;
  challengesLabel:   string;
  marriageOutlook:   string;
  cosmicInsight:     string;
  overallScore:      string;

  // ── Doshas ────────────────────────────────────────────────────────────────
  doshTitle:        string;
  manglikDosh:      string;
  kaalSarpDosh:     string;
  pitruDosh:        string;
  sadhesatiLabel:   string;
  remedyLabel:      string;
  doshPresent:      string;
  doshAbsent:       string;

  // ── Numerology ────────────────────────────────────────────────────────────
  numerologyTitle:    string;
  lifePathLabel:      string;
  destinyNumber:      string;
  soulNumber:         string;
  personalityNumber:  string;
  luckyNumbers:       string;
  luckyColors:        string;

  // ── Lucky ─────────────────────────────────────────────────────────────────
  luckyTitle:       string;
  luckyNumber:      string;
  luckyColor:       string;
  luckyGem:         string;
  luckyDay:         string;
  luckyDirection:   string;
  luckyMetal:       string;

  // ── Muhurat ───────────────────────────────────────────────────────────────
  muhuratTitle:     string;
  marriageMuhurat:  string;
  businessMuhurat:  string;
  travelMuhurat:    string;
  propertyMuhurat:  string;
  noMuhurat:        string;

  // ── Planet Positions ──────────────────────────────────────────────────────
  planetTitle:      string;
  retrograde:       string;
  directMotion:     string;
  transitLabel:     string;
  planetDignity:    string;
  exalted:          string;
  debilitated:      string;

  // ── Vastu ─────────────────────────────────────────────────────────────────
  vastuTitle:       string;
  northDir:         string;
  southDir:         string;
  eastDir:          string;
  westDir:          string;
  northEast:        string;
  northWest:        string;
  southEast:        string;
  southWest:        string;
  vastuTip:         string;

  // ── Remedies ──────────────────────────────────────────────────────────────
  remediesTitle:    string;
  gemstones:        string;
  mantrasLabel:     string;
  donationLabel:    string;
  fastingLabel:     string;
  yagyaLabel:       string;

  // ── Subscription ──────────────────────────────────────────────────────────
  subscriptionTitle: string;
  paymentTitle:      string;
  plansTitle:       string;
  perMonth:         string;
  perYear:          string;
  currentPlanLabel: string;
  upgradePlanLabel: string;
  mostPopular:      string;
  bestValue:        string;
  planFeatures:     string;

  // ── Profile Edit ──────────────────────────────────────────────────────────
  editProfileTitle:  string;
  saveChanges:       string;
  nameLabel:         string;
  relationLabel:     string;
  profileUpdated:    string;

  // ── Relationship / Love ───────────────────────────────────────────────────
  relationshipTitle:    string;
  loveTitle:            string;
  marriageCompatTitle:  string;
  synastrySub:          string;

  // ── My Kundli ─────────────────────────────────────────────────────────────
  myKundliTitle:    string;
  chartDetails:     string;
  planetaryStrength:string;
  houseAnalysis:    string;

  // ── Daily Alerts ──────────────────────────────────────────────────────────
  alertsTitle:      string;
  enableAlerts:     string;
  alertTime:        string;
  alertsEnabled:    string;
  alertsDisabled:   string;

  // ── Forecast ──────────────────────────────────────────────────────────────
  forecastTitle:    string;
  forecastSub:      string;
  upcomingEvents:   string;
  nextSixMonths:    string;
}

// ══════════════════════════════════════════════════════════════════════════════
// TRANSLATION TABLE
// ══════════════════════════════════════════════════════════════════════════════
const TE: Record<UILang, ExtTranslations> = {

  // ── ENGLISH ───────────────────────────────────────────────────────────────
  en: {
    calculating: "Calculating...", noData: "No data available",
    selectProfile: "Select Profile", birthDataNeeded: "Birth data required",
    goBack: "Go Back", viewReport: "View Report", matchReport: "Match Report",
    present: "Present", notPresent: "Not Present",
    auspicious: "Auspicious", inauspicious: "Inauspicious",
    daily: "Daily", weekly: "Weekly", monthly: "Monthly", yearly: "Yearly",
    selectSign: "Select Your Sign",

    rashifalTitle: "Rashifal", todaysRashifal: "Today's Horoscope",
    loveSection: "Love", careerSection: "Career",
    healthSection: "Health", moneySection: "Money",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Vara (Day)",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Sunrise", sunsetLabel: "Sunset",
    auspiciousTimes: "Auspicious Times", rahukaal: "Rahu Kaal",
    moonSignLabel: "Moon Sign", paksha: "Paksha", festivals: "Festivals",

    kundliMilanTitle: "Kundli Milan", kundliMilanSub: "Ashtakoot Compatibility",
    groomLabel: "Groom", brideLabel: "Bride",
    checkCompatibility: "Check Compatibility",
    gunaScore: "Guna Score", outOf36: "out of 36",
    manglikLabel: "Manglik", selfProfile: "Your Profile",
    partnerProfile: "Partner's Profile", addPartner: "Add Partner",
    birthDataMissing: "Birth data missing for one or both persons",

    milanResult: "Compatibility Result", strengthsLabel: "Strengths",
    challengesLabel: "Challenges", marriageOutlook: "Marriage Outlook",
    cosmicInsight: "Cosmic Insight", overallScore: "Overall Score",

    doshTitle: "Doshas", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Remedy",
    doshPresent: "Present", doshAbsent: "Not Present",

    numerologyTitle: "Numerology", lifePathLabel: "Life Path Number",
    destinyNumber: "Destiny Number", soulNumber: "Soul Number",
    personalityNumber: "Personality Number",
    luckyNumbers: "Lucky Numbers", luckyColors: "Lucky Colors",

    luckyTitle: "Lucky Elements", luckyNumber: "Lucky Number",
    luckyColor: "Lucky Color", luckyGem: "Lucky Gemstone",
    luckyDay: "Lucky Day", luckyDirection: "Lucky Direction",
    luckyMetal: "Lucky Metal",

    muhuratTitle: "Muhurat", marriageMuhurat: "Marriage Muhurat",
    businessMuhurat: "Business Muhurat", travelMuhurat: "Travel Muhurat",
    propertyMuhurat: "Griha Pravesh", noMuhurat: "No Muhurat today",

    planetTitle: "Planet Positions", retrograde: "Retrograde",
    directMotion: "Direct", transitLabel: "Transit",
    planetDignity: "Dignity", exalted: "Exalted", debilitated: "Debilitated",

    vastuTitle: "Vastu Shastra", northDir: "North", southDir: "South",
    eastDir: "East", westDir: "West", northEast: "North-East",
    northWest: "North-West", southEast: "South-East", southWest: "South-West",
    vastuTip: "Vastu Tip",

    remediesTitle: "Remedies", gemstones: "Gemstones",
    mantrasLabel: "Mantras", donationLabel: "Donation",
    fastingLabel: "Fasting", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Subscription", paymentTitle: "Secure Payment",
    plansTitle: "Plans & Pricing", perMonth: "/ month", perYear: "/ year",
    currentPlanLabel: "Current Plan", upgradePlanLabel: "Upgrade Plan",
    mostPopular: "Most Popular", bestValue: "Best Value",
    planFeatures: "What's included",

    editProfileTitle: "Edit Profile", saveChanges: "Save Changes",
    nameLabel: "Name", relationLabel: "Relation", profileUpdated: "Profile updated",

    relationshipTitle: "Relationship Analysis", loveTitle: "Love & Reality",
    marriageCompatTitle: "Marriage Compatibility",
    synastrySub: "Cosmic connection between two charts",

    myKundliTitle: "My Kundli", chartDetails: "Chart Details",
    planetaryStrength: "Planetary Strength", houseAnalysis: "House Analysis",

    alertsTitle: "Daily Alerts", enableAlerts: "Enable Daily Alerts",
    alertTime: "Alert Time", alertsEnabled: "Alerts enabled",
    alertsDisabled: "Alerts disabled",

    forecastTitle: "Forecast", forecastSub: "Your next 6 months decoded",
    upcomingEvents: "Upcoming Events", nextSixMonths: "Next 6 Months",
  },

  // ── HINGLISH (Hindi in Roman script) ───────────────────────────────────────
  hn: {
    calculating: "Calculate ho raha hai...", noData: "Koi data nahi hai",
    selectProfile: "Profile chunein", birthDataNeeded: "Birth data chahiye",
    goBack: "Wapas jaayein", viewReport: "Report dekhein", matchReport: "Match Report",
    present: "Maujood", notPresent: "Maujood nahi",
    auspicious: "Shubh", inauspicious: "Ashubh",
    daily: "Daily", weekly: "Weekly", monthly: "Monthly", yearly: "Yearly",
    selectSign: "Apni Rashi chunein",

    rashifalTitle: "Rashifal", todaysRashifal: "Aaj ka Rashifal",
    loveSection: "Pyaar", careerSection: "Career",
    healthSection: "Swasthya", moneySection: "Paisa",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Vaar (Din)",
    yogaPanchang: "Yog", karana: "Karan",
    sunriseLabel: "Sooryodaya", sunsetLabel: "Sooryaast",
    auspiciousTimes: "Shubh Muhurat", rahukaal: "Rahu Kaal",
    moonSignLabel: "Chandra Rashi", paksha: "Paksha", festivals: "Tyohaar",

    kundliMilanTitle: "Kundli Milan", kundliMilanSub: "Ashtakoot Compatibility",
    groomLabel: "Dulha", brideLabel: "Dulhan",
    checkCompatibility: "Compatibility check karein",
    gunaScore: "Guna Score", outOf36: "36 me se",
    manglikLabel: "Manglik", selfProfile: "Aapki Profile",
    partnerProfile: "Partner ki Profile", addPartner: "Partner add karein",
    birthDataMissing: "Ek ya dono logon ka birth data missing hai",

    milanResult: "Compatibility Result", strengthsLabel: "Strengths",
    challengesLabel: "Challenges", marriageOutlook: "Shaadi ka Outlook",
    cosmicInsight: "Cosmic Insight", overallScore: "Overall Score",

    doshTitle: "Dosh", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhe Sati", remedyLabel: "Upay",
    doshPresent: "Maujood", doshAbsent: "Maujood nahi",

    numerologyTitle: "Numerology", lifePathLabel: "Life Path Number",
    destinyNumber: "Destiny Number", soulNumber: "Soul Number",
    personalityNumber: "Personality Number",
    luckyNumbers: "Lucky Numbers", luckyColors: "Lucky Colors",

    luckyTitle: "Lucky Cheezein", luckyNumber: "Lucky Number",
    luckyColor: "Lucky Rang", luckyGem: "Lucky Ratna",
    luckyDay: "Lucky Din", luckyDirection: "Lucky Disha",
    luckyMetal: "Lucky Dhatu",

    muhuratTitle: "Muhurat", marriageMuhurat: "Shaadi Muhurat",
    businessMuhurat: "Business Muhurat", travelMuhurat: "Yatra Muhurat",
    propertyMuhurat: "Griha Pravesh", noMuhurat: "Aaj koi muhurat nahi",

    planetTitle: "Grahon ki Position", retrograde: "Vakri",
    directMotion: "Margi", transitLabel: "Gochar",
    planetDignity: "Sthiti", exalted: "Uchch", debilitated: "Neech",

    vastuTitle: "Vastu Shastra", northDir: "Uttar", southDir: "Dakshin",
    eastDir: "Poorv", westDir: "Paschim", northEast: "Ishaan",
    northWest: "Vayavya", southEast: "Agni", southWest: "Nairutya",
    vastuTip: "Vastu Tip",

    remediesTitle: "Upay", gemstones: "Ratna",
    mantrasLabel: "Mantra", donationLabel: "Daan",
    fastingLabel: "Vrat", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Subscription", paymentTitle: "Safe Payment",
    plansTitle: "Plans aur Pricing", perMonth: "/ mahina", perYear: "/ saal",
    currentPlanLabel: "Current Plan", upgradePlanLabel: "Plan Upgrade karein",
    mostPopular: "Sabse Popular", bestValue: "Best Value",
    planFeatures: "Kya-kya milega",

    editProfileTitle: "Profile Edit karein", saveChanges: "Changes save karein",
    nameLabel: "Naam", relationLabel: "Rishta", profileUpdated: "Profile update ho gayi",

    relationshipTitle: "Rishta Analysis", loveTitle: "Pyaar aur Sachai",
    marriageCompatTitle: "Shaadi Compatibility",
    synastrySub: "Do charts ke beech cosmic connection",

    myKundliTitle: "Meri Kundli", chartDetails: "Chart Details",
    planetaryStrength: "Grahon ki Takat", houseAnalysis: "Bhav Analysis",

    alertsTitle: "Daily Alerts", enableAlerts: "Daily Alerts chalu karein",
    alertTime: "Alert Time", alertsEnabled: "Alerts chalu hain",
    alertsDisabled: "Alerts band hain",

    forecastTitle: "Forecast", forecastSub: "Aapke agle 6 mahine decoded",
    upcomingEvents: "Aane Waale Events", nextSixMonths: "Agle 6 Mahine",
  },

  // ── HINDI ──────────────────────────────────────────────────────────────────
  hi: {
    calculating: "गणना हो रही है...", noData: "कोई डेटा उपलब्ध नहीं",
    selectProfile: "प्रोफाइल चुनें", birthDataNeeded: "जन्म विवरण आवश्यक है",
    goBack: "वापस जाएं", viewReport: "रिपोर्ट देखें", matchReport: "मिलान रिपोर्ट",
    present: "है", notPresent: "नहीं है",
    auspicious: "शुभ", inauspicious: "अशुभ",
    daily: "दैनिक", weekly: "साप्ताहिक", monthly: "मासिक", yearly: "वार्षिक",
    selectSign: "अपनी राशि चुनें",

    rashifalTitle: "राशिफल", todaysRashifal: "आज का राशिफल",
    loveSection: "प्रेम", careerSection: "करियर",
    healthSection: "स्वास्थ्य", moneySection: "धन",

    panchangTitle: "पंचांग", tithi: "तिथि", vara: "वार",
    yogaPanchang: "योग", karana: "करण",
    sunriseLabel: "सूर्योदय", sunsetLabel: "सूर्यास्त",
    auspiciousTimes: "शुभ मुहूर्त", rahukaal: "राहु काल",
    moonSignLabel: "चंद्र राशि", paksha: "पक्ष", festivals: "त्योहार",

    kundliMilanTitle: "कुंडली मिलान", kundliMilanSub: "अष्टकूट गुण मिलान",
    groomLabel: "वर", brideLabel: "वधू",
    checkCompatibility: "मिलान करें",
    gunaScore: "गुण अंक", outOf36: "36 में से",
    manglikLabel: "मांगलिक", selfProfile: "आपकी कुंडली",
    partnerProfile: "साथी की कुंडली", addPartner: "साथी जोड़ें",
    birthDataMissing: "एक या दोनों के जन्म विवरण अनुपलब्ध हैं",

    milanResult: "मिलान परिणाम", strengthsLabel: "सकारात्मक पक्ष",
    challengesLabel: "चुनौतियाँ", marriageOutlook: "विवाह संभावना",
    cosmicInsight: "ज्योतिष अंतर्दृष्टि", overallScore: "कुल अंक",

    doshTitle: "दोष", manglikDosh: "मांगलिक दोष",
    kaalSarpDosh: "काल सर्प दोष", pitruDosh: "पितृ दोष",
    sadhesatiLabel: "साढ़े साती", remedyLabel: "उपाय",
    doshPresent: "है", doshAbsent: "नहीं है",

    numerologyTitle: "अंक ज्योतिष", lifePathLabel: "जीवन पथ संख्या",
    destinyNumber: "भाग्यांक", soulNumber: "आत्मांक",
    personalityNumber: "व्यक्तित्व अंक",
    luckyNumbers: "शुभ अंक", luckyColors: "शुभ रंग",

    luckyTitle: "शुभ तत्व", luckyNumber: "शुभ अंक",
    luckyColor: "शुभ रंग", luckyGem: "शुभ रत्न",
    luckyDay: "शुभ दिन", luckyDirection: "शुभ दिशा",
    luckyMetal: "शुभ धातु",

    muhuratTitle: "मुहूर्त", marriageMuhurat: "विवाह मुहूर्त",
    businessMuhurat: "व्यवसाय मुहूर्त", travelMuhurat: "यात्रा मुहूर्त",
    propertyMuhurat: "गृह प्रवेश", noMuhurat: "आज कोई मुहूर्त नहीं",

    planetTitle: "ग्रह स्थिति", retrograde: "वक्री",
    directMotion: "मार्गी", transitLabel: "गोचर",
    planetDignity: "ग्रह बल", exalted: "उच्च", debilitated: "नीच",

    vastuTitle: "वास्तु शास्त्र", northDir: "उत्तर", southDir: "दक्षिण",
    eastDir: "पूर्व", westDir: "पश्चिम", northEast: "ईशान (उत्तर-पूर्व)",
    northWest: "वायव्य (उत्तर-पश्चिम)", southEast: "आग्नेय (दक्षिण-पूर्व)",
    southWest: "नैऋत्य (दक्षिण-पश्चिम)", vastuTip: "वास्तु टिप",

    remediesTitle: "उपाय", gemstones: "रत्न",
    mantrasLabel: "मंत्र", donationLabel: "दान",
    fastingLabel: "व्रत", yagyaLabel: "यज्ञ / हवन",

    subscriptionTitle: "सदस्यता", paymentTitle: "सुरक्षित भुगतान",
    plansTitle: "सदस्यता योजनाएं", perMonth: "/ माह", perYear: "/ वर्ष",
    currentPlanLabel: "वर्तमान योजना", upgradePlanLabel: "अपग्रेड करें",
    mostPopular: "सबसे लोकप्रिय", bestValue: "सर्वोत्तम मूल्य",
    planFeatures: "क्या शामिल है",

    editProfileTitle: "प्रोफाइल संपादित करें", saveChanges: "बदलाव सहेजें",
    nameLabel: "नाम", relationLabel: "संबंध", profileUpdated: "प्रोफाइल अपडेट हुई",

    relationshipTitle: "संबंध विश्लेषण", loveTitle: "प्रेम और वास्तविकता",
    marriageCompatTitle: "विवाह अनुकूलता",
    synastrySub: "दो कुंडलियों के बीच का कोस्मिक संबंध",

    myKundliTitle: "मेरी कुंडली", chartDetails: "चार्ट विवरण",
    planetaryStrength: "ग्रह बल", houseAnalysis: "भाव विश्लेषण",

    alertsTitle: "दैनिक अलर्ट", enableAlerts: "दैनिक अलर्ट चालू करें",
    alertTime: "अलर्ट समय", alertsEnabled: "अलर्ट सक्रिय",
    alertsDisabled: "अलर्ट बंद",

    forecastTitle: "भविष्यफल", forecastSub: "आपके अगले 6 महीने",
    upcomingEvents: "आगामी घटनाएं", nextSixMonths: "अगले 6 महीने",
  },
};

export function getTE(lang: string): ExtTranslations {
  const c = lang === "hn" || lang === "hi" ? lang : "en";
  return TE[c as UILang] ?? TE.en;
}
