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

  // ── MARATHI ────────────────────────────────────────────────────────────────
  mr: {
    calculating: "गणना होत आहे...", noData: "माहिती उपलब्ध नाही",
    selectProfile: "प्रोफाइल निवडा", birthDataNeeded: "जन्म तपशील आवश्यक",
    goBack: "मागे जा", viewReport: "अहवाल पाहा", matchReport: "मिलान अहवाल",
    present: "आहे", notPresent: "नाही",
    auspicious: "शुभ", inauspicious: "अशुभ",
    daily: "दैनिक", weekly: "साप्ताहिक", monthly: "मासिक", yearly: "वार्षिक",
    selectSign: "आपली राशी निवडा",

    rashifalTitle: "राशीभविष्य", todaysRashifal: "आजचे राशीभविष्य",
    loveSection: "प्रेम", careerSection: "करिअर",
    healthSection: "आरोग्य", moneySection: "धन",

    panchangTitle: "पंचांग", tithi: "तिथी", vara: "वार",
    yogaPanchang: "योग", karana: "करण",
    sunriseLabel: "सूर्योदय", sunsetLabel: "सूर्यास्त",
    auspiciousTimes: "शुभ मुहूर्त", rahukaal: "राहू काळ",
    moonSignLabel: "चंद्र राशी", paksha: "पक्ष", festivals: "सण",

    kundliMilanTitle: "कुंडली मिलान", kundliMilanSub: "अष्टकूट गुण मिलान",
    groomLabel: "वर", brideLabel: "वधू",
    checkCompatibility: "मिलान करा",
    gunaScore: "गुण गुण", outOf36: "36 पैकी",
    manglikLabel: "मांगलिक", selfProfile: "तुमची कुंडली",
    partnerProfile: "जोडीदाराची कुंडली", addPartner: "जोडीदार जोडा",
    birthDataMissing: "एक किंवा दोघांचा जन्म तपशील अनुपलब्ध",

    milanResult: "मिलान निकाल", strengthsLabel: "सकारात्मक बाजू",
    challengesLabel: "आव्हाने", marriageOutlook: "विवाह शक्यता",
    cosmicInsight: "ज्योतिष अंतर्दृष्टी", overallScore: "एकूण गुण",

    doshTitle: "दोष", manglikDosh: "मांगलिक दोष",
    kaalSarpDosh: "काळ सर्प दोष", pitruDosh: "पितृ दोष",
    sadhesatiLabel: "साडेसाती", remedyLabel: "उपाय",
    doshPresent: "आहे", doshAbsent: "नाही",

    numerologyTitle: "अंकज्योतिष", lifePathLabel: "जीवन मार्ग क्रमांक",
    destinyNumber: "भाग्यांक", soulNumber: "आत्मांक",
    personalityNumber: "व्यक्तिमत्त्व अंक",
    luckyNumbers: "शुभ अंक", luckyColors: "शुभ रंग",

    luckyTitle: "शुभ घटक", luckyNumber: "शुभ अंक",
    luckyColor: "शुभ रंग", luckyGem: "शुभ रत्न",
    luckyDay: "शुभ दिवस", luckyDirection: "शुभ दिशा",
    luckyMetal: "शुभ धातू",

    muhuratTitle: "मुहूर्त", marriageMuhurat: "विवाह मुहूर्त",
    businessMuhurat: "व्यवसाय मुहूर्त", travelMuhurat: "प्रवास मुहूर्त",
    propertyMuhurat: "गृहप्रवेश", noMuhurat: "आज कोणताही मुहूर्त नाही",

    planetTitle: "ग्रह स्थिती", retrograde: "वक्री",
    directMotion: "मार्गी", transitLabel: "गोचर",
    planetDignity: "ग्रह बल", exalted: "उच्च", debilitated: "नीच",

    vastuTitle: "वास्तुशास्त्र", northDir: "उत्तर", southDir: "दक्षिण",
    eastDir: "पूर्व", westDir: "पश्चिम", northEast: "ईशान्य",
    northWest: "वायव्य", southEast: "आग्नेय", southWest: "नैऋत्य",
    vastuTip: "वास्तू टिप",

    remediesTitle: "उपाय", gemstones: "रत्नपाषाण",
    mantrasLabel: "मंत्र", donationLabel: "दान",
    fastingLabel: "उपवास", yagyaLabel: "यज्ञ / हवन",

    subscriptionTitle: "सदस्यत्व", paymentTitle: "सुरक्षित देयक",
    plansTitle: "सदस्यता योजना", perMonth: "/ महिना", perYear: "/ वर्ष",
    currentPlanLabel: "सध्याची योजना", upgradePlanLabel: "अपग्रेड करा",
    mostPopular: "सर्वाधिक लोकप्रिय", bestValue: "सर्वोत्तम मूल्य",
    planFeatures: "काय समाविष्ट आहे",

    editProfileTitle: "प्रोफाइल संपादित करा", saveChanges: "बदल जतन करा",
    nameLabel: "नाव", relationLabel: "नाते", profileUpdated: "प्रोफाइल अपडेट झाली",

    relationshipTitle: "संबंध विश्लेषण", loveTitle: "प्रेम आणि वास्तव",
    marriageCompatTitle: "विवाह अनुकूलता",
    synastrySub: "दोन कुंडल्यांमधील कोस्मिक संबंध",

    myKundliTitle: "माझी कुंडली", chartDetails: "चार्ट तपशील",
    planetaryStrength: "ग्रह बल", houseAnalysis: "भाव विश्लेषण",

    alertsTitle: "दैनिक अलर्ट", enableAlerts: "दैनिक अलर्ट सक्षम करा",
    alertTime: "अलर्ट वेळ", alertsEnabled: "अलर्ट सक्रिय",
    alertsDisabled: "अलर्ट बंद",

    forecastTitle: "भविष्यवाणी", forecastSub: "तुमचे पुढील 6 महिने",
    upcomingEvents: "आगामी घटना", nextSixMonths: "पुढील 6 महिने",
  },

  // ── BENGALI ────────────────────────────────────────────────────────────────
  bn: {
    calculating: "গণনা হচ্ছে...", noData: "কোনো তথ্য পাওয়া যায়নি",
    selectProfile: "প্রোফাইল বেছে নিন", birthDataNeeded: "জন্ম তথ্য প্রয়োজন",
    goBack: "ফিরে যান", viewReport: "রিপোর্ট দেখুন", matchReport: "মিলান রিপোর্ট",
    present: "আছে", notPresent: "নেই",
    auspicious: "শুভ", inauspicious: "অশুভ",
    daily: "দৈনিক", weekly: "সাপ্তাহিক", monthly: "মাসিক", yearly: "বার্ষিক",
    selectSign: "আপনার রাশি বেছে নিন",

    rashifalTitle: "রাশিফল", todaysRashifal: "আজকের রাশিফল",
    loveSection: "প্রেম", careerSection: "কর্মজীবন",
    healthSection: "স্বাস্থ্য", moneySection: "অর্থ",

    panchangTitle: "পঞ্চাং", tithi: "তিথি", vara: "বার",
    yogaPanchang: "যোগ", karana: "করণ",
    sunriseLabel: "সূর্যোদয়", sunsetLabel: "সূর্যাস্ত",
    auspiciousTimes: "শুভ মুহূর্ত", rahukaal: "রাহু কাল",
    moonSignLabel: "চন্দ্র রাশি", paksha: "পক্ষ", festivals: "উৎসব",

    kundliMilanTitle: "কুণ্ডলী মিলান", kundliMilanSub: "অষ্টকূট গুণ মিলান",
    groomLabel: "বর", brideLabel: "কনে",
    checkCompatibility: "মিলান করুন",
    gunaScore: "গুণ স্কোর", outOf36: "৩৬ এর মধ্যে",
    manglikLabel: "মাঙ্গলিক", selfProfile: "আপনার কুণ্ডলী",
    partnerProfile: "সঙ্গীর কুণ্ডলী", addPartner: "সঙ্গী যোগ করুন",
    birthDataMissing: "একজন বা উভয়ের জন্ম তথ্য অনুপলব্ধ",

    milanResult: "মিলান ফলাফল", strengthsLabel: "ইতিবাচক দিক",
    challengesLabel: "চ্যালেঞ্জ", marriageOutlook: "বিবাহ সম্ভাবনা",
    cosmicInsight: "জ্যোতিষ অন্তর্দৃষ্টি", overallScore: "মোট স্কোর",

    doshTitle: "দোষ", manglikDosh: "মাঙ্গলিক দোষ",
    kaalSarpDosh: "কাল সর্প দোষ", pitruDosh: "পিতৃ দোষ",
    sadhesatiLabel: "সাড়ে সাতি", remedyLabel: "প্রতিকার",
    doshPresent: "আছে", doshAbsent: "নেই",

    numerologyTitle: "সংখ্যাবিদ্যা", lifePathLabel: "জীবনপথ সংখ্যা",
    destinyNumber: "ভাগ্যাঙ্ক", soulNumber: "আত্মাঙ্ক",
    personalityNumber: "ব্যক্তিত্ব অঙ্ক",
    luckyNumbers: "শুভ সংখ্যা", luckyColors: "শুভ রঙ",

    luckyTitle: "শুভ উপাদান", luckyNumber: "শুভ সংখ্যা",
    luckyColor: "শুভ রঙ", luckyGem: "শুভ রত্নপাথর",
    luckyDay: "শুভ দিন", luckyDirection: "শুভ দিক",
    luckyMetal: "শুভ ধাতু",

    muhuratTitle: "মুহূর্ত", marriageMuhurat: "বিবাহ মুহূর্ত",
    businessMuhurat: "ব্যবসায়িক মুহূর্ত", travelMuhurat: "ভ্রমণ মুহূর্ত",
    propertyMuhurat: "গৃহপ্রবেশ", noMuhurat: "আজ কোনো মুহূর্ত নেই",

    planetTitle: "গ্রহের অবস্থান", retrograde: "বক্রী",
    directMotion: "মার্গী", transitLabel: "গোচর",
    planetDignity: "গ্রহ বল", exalted: "উচ্চ", debilitated: "নীচ",

    vastuTitle: "বাস্তু শাস্ত্র", northDir: "উত্তর", southDir: "দক্ষিণ",
    eastDir: "পূর্ব", westDir: "পশ্চিম", northEast: "ঈশান",
    northWest: "বায়ব্য", southEast: "অগ্নি", southWest: "নৈঋত",
    vastuTip: "বাস্তু টিপ",

    remediesTitle: "প্রতিকার", gemstones: "রত্নপাথর",
    mantrasLabel: "মন্ত্র", donationLabel: "দান",
    fastingLabel: "উপবাস", yagyaLabel: "যজ্ঞ / হাওয়ান",

    subscriptionTitle: "সদস্যতা", paymentTitle: "নিরাপদ পেমেন্ট",
    plansTitle: "সদস্যতা পরিকল্পনা", perMonth: "/ মাস", perYear: "/ বছর",
    currentPlanLabel: "বর্তমান পরিকল্পনা", upgradePlanLabel: "আপগ্রেড করুন",
    mostPopular: "সবচেয়ে জনপ্রিয়", bestValue: "সেরা মূল্য",
    planFeatures: "কী অন্তর্ভুক্ত",

    editProfileTitle: "প্রোফাইল সম্পাদনা করুন", saveChanges: "পরিবর্তন সংরক্ষণ করুন",
    nameLabel: "নাম", relationLabel: "সম্পর্ক", profileUpdated: "প্রোফাইল আপডেট হয়েছে",

    relationshipTitle: "সম্পর্ক বিশ্লেষণ", loveTitle: "প্রেম ও বাস্তবতা",
    marriageCompatTitle: "বিবাহ সামঞ্জস্যতা",
    synastrySub: "দুই কুণ্ডলীর মধ্যে মহাজাগতিক সংযোগ",

    myKundliTitle: "আমার কুণ্ডলী", chartDetails: "চার্টের বিবরণ",
    planetaryStrength: "গ্রহ শক্তি", houseAnalysis: "ভাব বিশ্লেষণ",

    alertsTitle: "দৈনিক অ্যালার্ট", enableAlerts: "দৈনিক অ্যালার্ট সক্রিয় করুন",
    alertTime: "অ্যালার্টের সময়", alertsEnabled: "অ্যালার্ট সক্রিয়",
    alertsDisabled: "অ্যালার্ট বন্ধ",

    forecastTitle: "ভবিষ্যদ্বাণী", forecastSub: "আপনার পরবর্তী ৬ মাস",
    upcomingEvents: "আসন্ন ঘটনা", nextSixMonths: "পরবর্তী ৬ মাস",
  },

  // ── TAMIL ──────────────────────────────────────────────────────────────────
  ta: {
    calculating: "கணக்கிடுகிறது...", noData: "தகவல் இல்லை",
    selectProfile: "சுயவிவரம் தேர்வு செய்யவும்", birthDataNeeded: "பிறந்த தேதி தேவை",
    goBack: "திரும்பு", viewReport: "அறிக்கை காண்க", matchReport: "பொருத்த அறிக்கை",
    present: "உள்ளது", notPresent: "இல்லை",
    auspicious: "சுப", inauspicious: "அசுப",
    daily: "தினசரி", weekly: "வாராந்திர", monthly: "மாதாந்திர", yearly: "வருடாந்திர",
    selectSign: "உங்கள் ராசியை தேர்வு செய்யவும்",

    rashifalTitle: "ராசி பலன்", todaysRashifal: "இன்றைய ராசி பலன்",
    loveSection: "காதல்", careerSection: "தொழில்",
    healthSection: "உடல்நலம்", moneySection: "பணம்",

    panchangTitle: "பஞ்சாங்கம்", tithi: "திதி", vara: "வாரம்",
    yogaPanchang: "யோகம்", karana: "கரணம்",
    sunriseLabel: "சூரிய உதயம்", sunsetLabel: "சூரிய அஸ்தமனம்",
    auspiciousTimes: "சுப நேரம்", rahukaal: "ராகு காலம்",
    moonSignLabel: "சந்திர ராசி", paksha: "பக்ஷம்", festivals: "திருவிழாக்கள்",

    kundliMilanTitle: "ஜாதக பொருத்தம்", kundliMilanSub: "அஷ்டகூட குண பொருத்தம்",
    groomLabel: "மணமகன்", brideLabel: "மணமகள்",
    checkCompatibility: "பொருத்தம் பார்க்க",
    gunaScore: "குண மதிப்பெண்", outOf36: "36 இல்",
    manglikLabel: "செவ்வாய் தோஷம்", selfProfile: "உங்கள் ஜாதகம்",
    partnerProfile: "துணையின் ஜாதகம்", addPartner: "துணை சேர்க்க",
    birthDataMissing: "ஒருவர் அல்லது இருவரின் பிறப்பு விவரங்கள் இல்லை",

    milanResult: "பொருத்த முடிவு", strengthsLabel: "நலன்கள்",
    challengesLabel: "சவால்கள்", marriageOutlook: "திருமண வாய்ப்பு",
    cosmicInsight: "ஜோதிட நுண்ணறிவு", overallScore: "மொத்த மதிப்பெண்",

    doshTitle: "தோஷங்கள்", manglikDosh: "செவ்வாய் தோஷம்",
    kaalSarpDosh: "காலசர்ப் தோஷம்", pitruDosh: "பித்ரு தோஷம்",
    sadhesatiLabel: "ஏழரை சனி", remedyLabel: "பரிகாரம்",
    doshPresent: "உள்ளது", doshAbsent: "இல்லை",

    numerologyTitle: "எண் ஜோதிடம்", lifePathLabel: "வாழ்க்கை பாதை எண்",
    destinyNumber: "விதி எண்", soulNumber: "ஆன்ம எண்",
    personalityNumber: "ஆளுமை எண்",
    luckyNumbers: "அதிர்ஷ்ட எண்கள்", luckyColors: "அதிர்ஷ்ட நிறங்கள்",

    luckyTitle: "அதிர்ஷ்ட தனிமங்கள்", luckyNumber: "அதிர்ஷ்ட எண்",
    luckyColor: "அதிர்ஷ்ட நிறம்", luckyGem: "அதிர்ஷ்ட கல்",
    luckyDay: "அதிர்ஷ்ட நாள்", luckyDirection: "அதிர்ஷ்ட திசை",
    luckyMetal: "அதிர்ஷ்ட உலோகம்",

    muhuratTitle: "முஹூர்த்தம்", marriageMuhurat: "திருமண முஹூர்த்தம்",
    businessMuhurat: "வணிக முஹூர்த்தம்", travelMuhurat: "பயண முஹூர்த்தம்",
    propertyMuhurat: "கிரஹ பிரவேசம்", noMuhurat: "இன்று முஹூர்த்தம் இல்லை",

    planetTitle: "கிரக நிலைகள்", retrograde: "வக்கிரம்",
    directMotion: "மார்கி", transitLabel: "கோசாரம்",
    planetDignity: "கிரக பலம்", exalted: "உச்சம்", debilitated: "நீசம்",

    vastuTitle: "வாஸ்து சாஸ்திரம்", northDir: "வடக்கு", southDir: "தெற்கு",
    eastDir: "கிழக்கு", westDir: "மேற்கு", northEast: "வடகிழக்கு",
    northWest: "வடமேற்கு", southEast: "தென்கிழக்கு", southWest: "தென்மேற்கு",
    vastuTip: "வாஸ்து குறிப்பு",

    remediesTitle: "பரிகாரங்கள்", gemstones: "ரத்தினக்கல்",
    mantrasLabel: "மந்திரங்கள்", donationLabel: "தானம்",
    fastingLabel: "விரதம்", yagyaLabel: "யாகம்",

    subscriptionTitle: "சந்தா", paymentTitle: "பாதுகாப்பான கட்டணம்",
    plansTitle: "திட்டங்கள் & விலை", perMonth: "/ மாதம்", perYear: "/ ஆண்டு",
    currentPlanLabel: "தற்போதைய திட்டம்", upgradePlanLabel: "மேம்படுத்து",
    mostPopular: "மிகவும் பிரபலமான", bestValue: "சிறந்த மதிப்பு",
    planFeatures: "என்ன சேர்க்கப்பட்டுள்ளது",

    editProfileTitle: "சுயவிவரம் திருத்து", saveChanges: "மாற்றங்களை சேமிக்கவும்",
    nameLabel: "பெயர்", relationLabel: "உறவு", profileUpdated: "சுயவிவரம் புதுப்பிக்கப்பட்டது",

    relationshipTitle: "உறவு பகுப்பாய்வு", loveTitle: "காதல் & யதார்த்தம்",
    marriageCompatTitle: "திருமண பொருத்தம்",
    synastrySub: "இரண்டு ஜாதகங்களுக்கிடையிலான அண்டவெளி தொடர்பு",

    myKundliTitle: "என் ஜாதகம்", chartDetails: "சார்ட் விவரங்கள்",
    planetaryStrength: "கிரக பலம்", houseAnalysis: "பாவ பகுப்பாய்வு",

    alertsTitle: "தினசரி விழிப்பூட்டல்கள்", enableAlerts: "தினசரி விழிப்பூட்டல்களை இயக்கு",
    alertTime: "விழிப்பூட்டல் நேரம்", alertsEnabled: "விழிப்பூட்டல்கள் இயக்கப்பட்டன",
    alertsDisabled: "விழிப்பூட்டல்கள் முடக்கப்பட்டன",

    forecastTitle: "எதிர்கால பலன்", forecastSub: "உங்கள் அடுத்த 6 மாதங்கள்",
    upcomingEvents: "வரவிருக்கும் நிகழ்வுகள்", nextSixMonths: "அடுத்த 6 மாதங்கள்",
  },

  // ── TELUGU ─────────────────────────────────────────────────────────────────
  te: {
    calculating: "లెక్కిస్తున్నాము...", noData: "డేటా అందుబాటులో లేదు",
    selectProfile: "ప్రొఫైల్ ఎంచుకోండి", birthDataNeeded: "జన్మ వివరాలు అవసరం",
    goBack: "వెనుకకు", viewReport: "నివేదిక చూడండి", matchReport: "మిలన్ నివేదిక",
    present: "ఉంది", notPresent: "లేదు",
    auspicious: "శుభ", inauspicious: "అశుభ",
    daily: "రోజువారీ", weekly: "వారపు", monthly: "నెలవారీ", yearly: "వార్షిక",
    selectSign: "మీ రాశిని ఎంచుకోండి",

    rashifalTitle: "రాశి ఫలాలు", todaysRashifal: "నేటి రాశి ఫలాలు",
    loveSection: "ప్రేమ", careerSection: "వృత్తి",
    healthSection: "ఆరోగ్యం", moneySection: "ధనం",

    panchangTitle: "పంచాంగం", tithi: "తిథి", vara: "వారం",
    yogaPanchang: "యోగం", karana: "కరణం",
    sunriseLabel: "సూర్యోదయం", sunsetLabel: "సూర్యాస్తమయం",
    auspiciousTimes: "శుభ ముహూర్తాలు", rahukaal: "రాహు కాలం",
    moonSignLabel: "చంద్ర రాశి", paksha: "పక్షం", festivals: "పండుగలు",

    kundliMilanTitle: "కుండలి మిలన్", kundliMilanSub: "అష్టకూట గుణ మిలన్",
    groomLabel: "వరుడు", brideLabel: "వధువు",
    checkCompatibility: "అనుకూలత తనిఖీ",
    gunaScore: "గుణ స్కోరు", outOf36: "36 లో",
    manglikLabel: "మాంగళిక్", selfProfile: "మీ కుండలి",
    partnerProfile: "భాగస్వామి కుండలి", addPartner: "భాగస్వామి జోడించండి",
    birthDataMissing: "ఒకరు లేదా ఇద్దరి జన్మ వివరాలు అందుబాటులో లేవు",

    milanResult: "మిలన్ ఫలితం", strengthsLabel: "బలాలు",
    challengesLabel: "సవాళ్ళు", marriageOutlook: "వివాహ అవకాశం",
    cosmicInsight: "జ్యోతిష్య అంతర్దృష్టి", overallScore: "మొత్తం స్కోరు",

    doshTitle: "దోషాలు", manglikDosh: "మాంగళిక దోషం",
    kaalSarpDosh: "కాల సర్ప దోషం", pitruDosh: "పితృ దోషం",
    sadhesatiLabel: "సాడేసాతి", remedyLabel: "పరిహారం",
    doshPresent: "ఉంది", doshAbsent: "లేదు",

    numerologyTitle: "సంఖ్యా శాస్త్రం", lifePathLabel: "జీవిత మార్గ సంఖ్య",
    destinyNumber: "భాగ్యాంకం", soulNumber: "ఆత్మాంకం",
    personalityNumber: "వ్యక్తిత్వ అంకం",
    luckyNumbers: "శుభ సంఖ్యలు", luckyColors: "శుభ రంగులు",

    luckyTitle: "శుభ అంశాలు", luckyNumber: "శుభ అంకం",
    luckyColor: "శుభ రంగు", luckyGem: "శుభ రత్నం",
    luckyDay: "శుభ రోజు", luckyDirection: "శుభ దిశ",
    luckyMetal: "శుభ లోహం",

    muhuratTitle: "ముహూర్తం", marriageMuhurat: "వివాహ ముహూర్తం",
    businessMuhurat: "వ్యాపార ముహూర్తం", travelMuhurat: "ప్రయాణ ముహూర్తం",
    propertyMuhurat: "గృహ ప్రవేశం", noMuhurat: "ఈరోజు ముహూర్తం లేదు",

    planetTitle: "గ్రహ స్థానాలు", retrograde: "వక్రి",
    directMotion: "మార్గి", transitLabel: "గోచారం",
    planetDignity: "గ్రహ బలం", exalted: "ఉచ్చం", debilitated: "నీచం",

    vastuTitle: "వాస్తు శాస్త్రం", northDir: "ఉత్తరం", southDir: "దక్షిణం",
    eastDir: "తూర్పు", westDir: "పడమర", northEast: "ఈశాన్యం",
    northWest: "వాయువ్యం", southEast: "ఆగ్నేయం", southWest: "నైఋతి",
    vastuTip: "వాస్తు చిట్కా",

    remediesTitle: "పరిహారాలు", gemstones: "రత్నాలు",
    mantrasLabel: "మంత్రాలు", donationLabel: "దానం",
    fastingLabel: "ఉపవాసం", yagyaLabel: "యజ్ఞం / హోమం",

    subscriptionTitle: "సభ్యత్వం", paymentTitle: "సురక్షిత చెల్లింపు",
    plansTitle: "ప్లాన్లు & ధరలు", perMonth: "/ నెల", perYear: "/ సంవత్సరం",
    currentPlanLabel: "ప్రస్తుత ప్లాన్", upgradePlanLabel: "అప్‌గ్రేడ్ చేయండి",
    mostPopular: "అత్యంత ప్రజాదరణ పొందింది", bestValue: "అత్యుత్తమ విలువ",
    planFeatures: "ఏమి చేర్చబడింది",

    editProfileTitle: "ప్రొఫైల్ సవరించు", saveChanges: "మార్పులు సేవ్ చేయండి",
    nameLabel: "పేరు", relationLabel: "సంబంధం", profileUpdated: "ప్రొఫైల్ అప్‌డేట్ చేయబడింది",

    relationshipTitle: "సంబంధ విశ్లేషణ", loveTitle: "ప్రేమ & వాస్తవం",
    marriageCompatTitle: "వివాహ అనుకూలత",
    synastrySub: "రెండు కుండలుల మధ్య విశ్వ సంబంధం",

    myKundliTitle: "నా కుండలి", chartDetails: "చార్ట్ వివరాలు",
    planetaryStrength: "గ్రహ బలం", houseAnalysis: "భావ విశ్లేషణ",

    alertsTitle: "రోజువారీ హెచ్చరికలు", enableAlerts: "రోజువారీ హెచ్చరికలు ప్రారంభించండి",
    alertTime: "హెచ్చరిక సమయం", alertsEnabled: "హెచ్చరికలు సక్రియంగా ఉన్నాయి",
    alertsDisabled: "హెచ్చరికలు నిష్క్రియంగా ఉన్నాయి",

    forecastTitle: "భవిష్యత్తు ఫలాలు", forecastSub: "మీ తదుపరి 6 నెలలు",
    upcomingEvents: "రాబోయే సంఘటనలు", nextSixMonths: "తదుపరి 6 నెలలు",
  },

  // ── GUJARATI ───────────────────────────────────────────────────────────────
  gu: {
    calculating: "ગણતરી ચાલુ છે...", noData: "કોઈ ડેટા ઉપલબ્ધ નથી",
    selectProfile: "પ્રોફાઇલ પસંદ કરો", birthDataNeeded: "જન્મ વિગત જરૂરી છે",
    goBack: "પાછા જાઓ", viewReport: "અહેવાલ જુઓ", matchReport: "મિલાન અહેવાલ",
    present: "છે", notPresent: "નથી",
    auspicious: "શુભ", inauspicious: "અશુભ",
    daily: "દૈનિક", weekly: "સાપ્તાહિક", monthly: "માસિક", yearly: "વાર્ષિક",
    selectSign: "તમારી રાશિ પસંદ કરો",

    rashifalTitle: "રાશિફળ", todaysRashifal: "આજનું રાશિફળ",
    loveSection: "પ્રેમ", careerSection: "કારકિર્દી",
    healthSection: "આરોગ્ય", moneySection: "ધન",

    panchangTitle: "પંચાંગ", tithi: "તિથિ", vara: "વાર",
    yogaPanchang: "યોગ", karana: "કરણ",
    sunriseLabel: "સૂર્યોદય", sunsetLabel: "સૂર્યાસ્ત",
    auspiciousTimes: "શુભ મુહૂર્ત", rahukaal: "રાહૂ કાળ",
    moonSignLabel: "ચંદ્ર રાશિ", paksha: "પક્ષ", festivals: "તહેવાર",

    kundliMilanTitle: "કુંડળી મિલાન", kundliMilanSub: "અષ્ટકૂટ ગુણ મિલાન",
    groomLabel: "વર", brideLabel: "કન્યા",
    checkCompatibility: "મિલાન કરો",
    gunaScore: "ગુણ સ્કોર", outOf36: "36 માંથી",
    manglikLabel: "માંગળિક", selfProfile: "તમારી કુંડળી",
    partnerProfile: "સાથીની કુંડળી", addPartner: "સાથી ઉમેરો",
    birthDataMissing: "એક અથવા બંનેની જન્મ વિગત ઉપલબ્ધ નથી",

    milanResult: "મિલાન પરિણામ", strengthsLabel: "સકારાત્મક પક્ષ",
    challengesLabel: "પડકારો", marriageOutlook: "વિવાહ સંભાવના",
    cosmicInsight: "જ્યોતિષ અંતર્દૃષ્ટિ", overallScore: "કુલ ગુણ",

    doshTitle: "દોષ", manglikDosh: "માંગળિક દોષ",
    kaalSarpDosh: "કાળ સર્પ દોષ", pitruDosh: "પિતૃ દોષ",
    sadhesatiLabel: "સાડાસાતી", remedyLabel: "ઉપાય",
    doshPresent: "છે", doshAbsent: "નથી",

    numerologyTitle: "અંકજ્યોતિષ", lifePathLabel: "જીવન માર્ગ સંખ્યા",
    destinyNumber: "ભાગ્યાંક", soulNumber: "આત્માંક",
    personalityNumber: "વ્યક્તિત્વ અંક",
    luckyNumbers: "શુભ અંક", luckyColors: "શુભ રંગ",

    luckyTitle: "શુભ તત્ત્વો", luckyNumber: "શુભ અંક",
    luckyColor: "શુભ રંગ", luckyGem: "શુભ રત્ન",
    luckyDay: "શુભ દિવસ", luckyDirection: "શુભ દિશા",
    luckyMetal: "શુભ ધાતુ",

    muhuratTitle: "મુહૂર્ત", marriageMuhurat: "વિવાહ મુહૂર્ત",
    businessMuhurat: "વ્યવસાય મુહૂર્ત", travelMuhurat: "પ્રવાસ મુહૂર્ત",
    propertyMuhurat: "ગૃહ પ્રવેશ", noMuhurat: "આજે કોઈ મુહૂર્ત નથી",

    planetTitle: "ગ્રહ સ્થિતિ", retrograde: "વક્રી",
    directMotion: "માર્ગી", transitLabel: "ગોચર",
    planetDignity: "ગ્રહ બળ", exalted: "ઉચ્ચ", debilitated: "નીચ",

    vastuTitle: "વાસ્તુ શાસ્ત્ર", northDir: "ઉત્તર", southDir: "દક્ષિણ",
    eastDir: "પૂર્વ", westDir: "પશ્ચિમ", northEast: "ઈશાન",
    northWest: "વાયવ્ય", southEast: "અગ્નિ", southWest: "નૈઋત્ય",
    vastuTip: "વાસ્તુ ટિપ",

    remediesTitle: "ઉપાય", gemstones: "રત્ન",
    mantrasLabel: "મંત્ર", donationLabel: "દાન",
    fastingLabel: "વ્રત", yagyaLabel: "યજ્ઞ / હવન",

    subscriptionTitle: "સભ્યપદ", paymentTitle: "સુरक्षিत ભुगतान",
    plansTitle: "સભ્યપદ યોજના", perMonth: "/ માસ", perYear: "/ વર્ષ",
    currentPlanLabel: "વર્તમાન યોજના", upgradePlanLabel: "અપગ્રેડ કરો",
    mostPopular: "સૌથી લોકપ્રિય", bestValue: "શ્રેષ્ઠ મૂલ્ય",
    planFeatures: "શું સામેલ છે",

    editProfileTitle: "પ્રોફાઇલ સંપાદિત કરો", saveChanges: "ફેરફારો સાચવો",
    nameLabel: "નામ", relationLabel: "સંબંધ", profileUpdated: "પ્રોફાઇલ અપડેટ થઈ",

    relationshipTitle: "સંબંધ વિશ્લેષણ", loveTitle: "પ્રેમ અને વાસ્તવ",
    marriageCompatTitle: "વિવાહ અનુકૂળતા",
    synastrySub: "બે કુંડળી વચ્ચેનો કોસ્મિક સંબંધ",

    myKundliTitle: "મારી કુંડળી", chartDetails: "ચાર્ટ વિગત",
    planetaryStrength: "ગ્રહ બળ", houseAnalysis: "ભાવ વિશ્લેષણ",

    alertsTitle: "દૈનિક અલર્ટ", enableAlerts: "દૈનિક અલર્ટ ચાલુ કરો",
    alertTime: "અલર્ટ સમય", alertsEnabled: "અલર્ટ સક્રિય",
    alertsDisabled: "અલર્ટ બંધ",

    forecastTitle: "ભવિષ્ય ફળ", forecastSub: "તમારા આગામી 6 મહિના",
    upcomingEvents: "આગામી ઘટનાઓ", nextSixMonths: "આગામી 6 મહિના",
  },

  // ── KANNADA ────────────────────────────────────────────────────────────────
  kn: {
    calculating: "ಲೆಕ್ಕಾಚಾರ ನಡೆಯುತ್ತಿದೆ...", noData: "ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ",
    selectProfile: "ಪ್ರೊಫೈಲ್ ಆಯ್ಕೆಮಾಡಿ", birthDataNeeded: "ಜನ್ಮ ವಿವರ ಅಗತ್ಯ",
    goBack: "ಹಿಂತಿರುಗಿ", viewReport: "ವರದಿ ನೋಡಿ", matchReport: "ಮಿಲಾನ್ ವರದಿ",
    present: "ಇದೆ", notPresent: "ಇಲ್ಲ",
    auspicious: "ಶುಭ", inauspicious: "ಅಶುಭ",
    daily: "ದೈನಂದಿನ", weekly: "ಸಾಪ್ತಾಹಿಕ", monthly: "ಮಾಸಿಕ", yearly: "ವಾರ್ಷಿಕ",
    selectSign: "ನಿಮ್ಮ ರಾಶಿ ಆಯ್ಕೆಮಾಡಿ",

    rashifalTitle: "ರಾಶಿ ಭವಿಷ್ಯ", todaysRashifal: "ಇಂದಿನ ರಾಶಿ ಭವಿಷ್ಯ",
    loveSection: "ಪ್ರೇಮ", careerSection: "ವೃತ್ತಿ",
    healthSection: "ಆರೋಗ್ಯ", moneySection: "ಹಣ",

    panchangTitle: "ಪಂಚಾಂಗ", tithi: "ತಿಥಿ", vara: "ವಾರ",
    yogaPanchang: "ಯೋಗ", karana: "ಕರಣ",
    sunriseLabel: "ಸೂರ್ಯೋದಯ", sunsetLabel: "ಸೂರ್ಯಾಸ್ತ",
    auspiciousTimes: "ಶುಭ ಮುಹೂರ್ತ", rahukaal: "ರಾಹು ಕಾಲ",
    moonSignLabel: "ಚಂದ್ರ ರಾಶಿ", paksha: "ಪಕ್ಷ", festivals: "ಹಬ್ಬಗಳು",

    kundliMilanTitle: "ಕುಂಡಲಿ ಮಿಲಾನ್", kundliMilanSub: "ಅಷ್ಟಕೂಟ ಗುಣ ಮಿಲಾನ್",
    groomLabel: "ವರ", brideLabel: "ವಧು",
    checkCompatibility: "ಹೊಂದಾಣಿಕೆ ಪರಿಶೀಲಿಸಿ",
    gunaScore: "ಗುಣ ಅಂಕ", outOf36: "36 ರಲ್ಲಿ",
    manglikLabel: "ಮಾಂಗಲಿಕ", selfProfile: "ನಿಮ್ಮ ಕುಂಡಲಿ",
    partnerProfile: "ಸಂಗಾತಿಯ ಕುಂಡಲಿ", addPartner: "ಸಂಗಾತಿ ಸೇರಿಸಿ",
    birthDataMissing: "ಒಬ್ಬರು ಅಥವಾ ಇಬ್ಬರ ಜನ್ಮ ವಿವರ ಲಭ್ಯವಿಲ್ಲ",

    milanResult: "ಮಿಲಾನ್ ಫಲಿತಾಂಶ", strengthsLabel: "ಸಕಾರಾತ್ಮಕ ಅಂಶಗಳು",
    challengesLabel: "ಸವಾಲುಗಳು", marriageOutlook: "ವಿವಾಹ ಸಂಭಾವ್ಯತೆ",
    cosmicInsight: "ಜ್ಯೋತಿಷ ಒಳನೋಟ", overallScore: "ಒಟ್ಟು ಅಂಕ",

    doshTitle: "ದೋಷಗಳು", manglikDosh: "ಮಾಂಗಲಿಕ ದೋಷ",
    kaalSarpDosh: "ಕಾಲ ಸರ್ಪ ದೋಷ", pitruDosh: "ಪಿತೃ ದೋಷ",
    sadhesatiLabel: "ಸಾಡೆ ಸಾತಿ", remedyLabel: "ಪರಿಹಾರ",
    doshPresent: "ಇದೆ", doshAbsent: "ಇಲ್ಲ",

    numerologyTitle: "ಅಂಕ ಜ್ಯೋತಿಷ", lifePathLabel: "ಜೀವನ ಮಾರ್ಗ ಸಂಖ್ಯೆ",
    destinyNumber: "ಭಾಗ್ಯಾಂಕ", soulNumber: "ಆತ್ಮಾಂಕ",
    personalityNumber: "ವ್ಯಕ್ತಿತ್ವ ಅಂಕ",
    luckyNumbers: "ಶುಭ ಸಂಖ್ಯೆಗಳು", luckyColors: "ಶುಭ ಬಣ್ಣಗಳು",

    luckyTitle: "ಶುಭ ಅಂಶಗಳು", luckyNumber: "ಶುಭ ಸಂಖ್ಯೆ",
    luckyColor: "ಶುಭ ಬಣ್ಣ", luckyGem: "ಶುಭ ರತ್ನ",
    luckyDay: "ಶುಭ ದಿನ", luckyDirection: "ಶುಭ ದಿಕ್ಕು",
    luckyMetal: "ಶುಭ ಲೋಹ",

    muhuratTitle: "ಮುಹೂರ್ತ", marriageMuhurat: "ವಿವಾಹ ಮುಹೂರ್ತ",
    businessMuhurat: "ವ್ಯವಹಾರ ಮುಹೂರ್ತ", travelMuhurat: "ಪ್ರಯಾಣ ಮುಹೂರ್ತ",
    propertyMuhurat: "ಗೃಹ ಪ್ರವೇಶ", noMuhurat: "ಇಂದು ಮುಹೂರ್ತ ಇಲ್ಲ",

    planetTitle: "ಗ್ರಹ ಸ್ಥಿತಿ", retrograde: "ವಕ್ರಿ",
    directMotion: "ಮಾರ್ಗಿ", transitLabel: "ಗೋಚರ",
    planetDignity: "ಗ್ರಹ ಬಲ", exalted: "ಉಚ್ಚ", debilitated: "ನೀಚ",

    vastuTitle: "ವಾಸ್ತು ಶಾಸ್ತ್ರ", northDir: "ಉತ್ತರ", southDir: "ದಕ್ಷಿಣ",
    eastDir: "ಪೂರ್ವ", westDir: "ಪಶ್ಚಿಮ", northEast: "ಈಶಾನ್ಯ",
    northWest: "ವಾಯವ್ಯ", southEast: "ಆಗ್ನೇಯ", southWest: "ನೈಋತ್ಯ",
    vastuTip: "ವಾಸ್ತು ಸಲಹೆ",

    remediesTitle: "ಪರಿಹಾರಗಳು", gemstones: "ರತ್ನಗಳು",
    mantrasLabel: "ಮಂತ್ರಗಳು", donationLabel: "ದಾನ",
    fastingLabel: "ಉಪವಾಸ", yagyaLabel: "ಯಜ್ಞ / ಹವನ",

    subscriptionTitle: "ಚಂದಾದಾರಿಕೆ", paymentTitle: "ಸುರಕ್ಷಿತ ಪಾವತಿ",
    plansTitle: "ಯೋಜನೆಗಳು & ಬೆಲೆ", perMonth: "/ ತಿಂಗಳು", perYear: "/ ವರ್ಷ",
    currentPlanLabel: "ಪ್ರಸ್ತುತ ಯೋಜನೆ", upgradePlanLabel: "ಅಪ್‌ಗ್ರೇಡ್ ಮಾಡಿ",
    mostPopular: "ಅತ್ಯಂತ ಜನಪ್ರಿಯ", bestValue: "ಅತ್ಯುತ್ತಮ ಮೌಲ್ಯ",
    planFeatures: "ಏನು ಸೇರಿಸಲಾಗಿದೆ",

    editProfileTitle: "ಪ್ರೊಫೈಲ್ ಸಂಪಾದಿಸಿ", saveChanges: "ಬದಲಾವಣೆಗಳನ್ನು ಉಳಿಸಿ",
    nameLabel: "ಹೆಸರು", relationLabel: "ಸಂಬಂಧ", profileUpdated: "ಪ್ರೊಫೈಲ್ ನವೀಕರಿಸಲಾಗಿದೆ",

    relationshipTitle: "ಸಂಬಂಧ ವಿಶ್ಲೇಷಣೆ", loveTitle: "ಪ್ರೇಮ & ವಾಸ್ತವ",
    marriageCompatTitle: "ವಿವಾಹ ಹೊಂದಾಣಿಕೆ",
    synastrySub: "ಎರಡು ಕುಂಡಲಿಗಳ ನಡುವಿನ ಬ್ರಹ್ಮಾಂಡ ಸಂಬಂಧ",

    myKundliTitle: "ನನ್ನ ಕುಂಡಲಿ", chartDetails: "ಚಾರ್ಟ್ ವಿವರಗಳು",
    planetaryStrength: "ಗ್ರಹ ಬಲ", houseAnalysis: "ಭಾವ ವಿಶ್ಲೇಷಣೆ",

    alertsTitle: "ದೈನಂದಿನ ಎಚ್ಚರಿಕೆಗಳು", enableAlerts: "ದೈನಂದಿನ ಎಚ್ಚರಿಕೆಗಳನ್ನು ಸಕ್ರಿಯಗೊಳಿಸಿ",
    alertTime: "ಎಚ್ಚರಿಕೆ ಸಮಯ", alertsEnabled: "ಎಚ್ಚರಿಕೆಗಳು ಸಕ್ರಿಯ",
    alertsDisabled: "ಎಚ್ಚರಿಕೆಗಳು ನಿಷ್ಕ್ರಿಯ",

    forecastTitle: "ಭವಿಷ್ಯ ಫಲ", forecastSub: "ನಿಮ್ಮ ಮುಂದಿನ 6 ತಿಂಗಳು",
    upcomingEvents: "ಮುಂಬರುವ ಘಟನೆಗಳು", nextSixMonths: "ಮುಂದಿನ 6 ತಿಂಗಳು",
  },

  // ── MALAYALAM ──────────────────────────────────────────────────────────────
  ml: {
    calculating: "കണക്കാക്കുന്നു...", noData: "ഡേറ്റ ലഭ്യമല്ല",
    selectProfile: "പ്രൊഫൈൽ തിരഞ്ഞെടുക്കുക", birthDataNeeded: "ജനന വിവരങ്ങൾ ആവശ്യമാണ്",
    goBack: "തിരിച്ചു പോകൂ", viewReport: "റിപ്പോർട്ട് കാണുക", matchReport: "മിലൻ റിപ്പോർട്ട്",
    present: "ഉണ്ട്", notPresent: "ഇല്ല",
    auspicious: "ശുഭ", inauspicious: "അശുഭ",
    daily: "ദൈനംദിന", weekly: "ആഴ്ചതോറും", monthly: "മാസം", yearly: "വാർഷിക",
    selectSign: "നിങ്ങളുടെ രാശി തിരഞ്ഞെടുക്കുക",

    rashifalTitle: "രാശി ഫലം", todaysRashifal: "ഇന്നത്തെ രാശി ഫലം",
    loveSection: "പ്രണയം", careerSection: "ജോലി",
    healthSection: "ആരോഗ്യം", moneySection: "ധനം",

    panchangTitle: "പഞ്ചാംഗം", tithi: "തിഥി", vara: "വാരം",
    yogaPanchang: "യോഗം", karana: "കരണം",
    sunriseLabel: "സൂര്യോദയം", sunsetLabel: "സൂര്യാസ്തമനം",
    auspiciousTimes: "ശുഭ മുഹൂർത്തം", rahukaal: "രാഹു കാലം",
    moonSignLabel: "ചന്ദ്ര രാശി", paksha: "പക്ഷം", festivals: "ഉൽസവങ്ങൾ",

    kundliMilanTitle: "കുണ്ഡലി മിലൻ", kundliMilanSub: "അഷ്ടകൂട ഗുണ മിലൻ",
    groomLabel: "വരൻ", brideLabel: "വധു",
    checkCompatibility: "പൊരുത്തം പരിശോധിക്കുക",
    gunaScore: "ഗുണ സ്കോർ", outOf36: "36 ൽ",
    manglikLabel: "ചൊവ്വദോഷം", selfProfile: "നിങ്ങളുടെ കുണ്ഡലി",
    partnerProfile: "പങ്കാളിയുടെ കുണ്ഡലി", addPartner: "പങ്കാളി ചേർക്കുക",
    birthDataMissing: "ഒരാളുടെ അല്ലെങ്കിൽ ഇരുവരുടെ ജനന വിവരങ്ങൾ ലഭ്യമല്ല",

    milanResult: "മിലൻ ഫലം", strengthsLabel: "ഗുണകരമായ വശങ്ങൾ",
    challengesLabel: "വെല്ലുവിളികൾ", marriageOutlook: "വിവാഹ സാധ്യത",
    cosmicInsight: "ജ്യോതിഷ ഉൾക്കാഴ്ച", overallScore: "മൊത്തം സ്കോർ",

    doshTitle: "ദോഷങ്ങൾ", manglikDosh: "ചൊവ്വദോഷം",
    kaalSarpDosh: "കാല സർപ്പ ദോഷം", pitruDosh: "പിതൃ ദോഷം",
    sadhesatiLabel: "ഏഴരശനി", remedyLabel: "പ്രതിവിധി",
    doshPresent: "ഉണ്ട്", doshAbsent: "ഇല്ല",

    numerologyTitle: "അക്ക ജ്യോതിഷം", lifePathLabel: "ജീവിത പഥ സംഖ്യ",
    destinyNumber: "വിധി സംഖ്യ", soulNumber: "ആത്മ സംഖ്യ",
    personalityNumber: "വ്യക്തിത്വ സംഖ്യ",
    luckyNumbers: "ഭാഗ്യ സംഖ്യകൾ", luckyColors: "ഭാഗ്യ നിറങ്ങൾ",

    luckyTitle: "ഭാഗ്യ ഘടകങ്ങൾ", luckyNumber: "ഭാഗ്യ സംഖ്യ",
    luckyColor: "ഭാഗ്യ നിറം", luckyGem: "ഭാഗ്യ രത്നം",
    luckyDay: "ഭാഗ്യ ദിവസം", luckyDirection: "ഭാഗ്യ ദിശ",
    luckyMetal: "ഭാഗ്യ ലോഹം",

    muhuratTitle: "മുഹൂർത്തം", marriageMuhurat: "വിവാഹ മുഹൂർത്തം",
    businessMuhurat: "ബിസിനസ് മുഹൂർത്തം", travelMuhurat: "യാത്രാ മുഹൂർത്തം",
    propertyMuhurat: "ഗൃഹ പ്രവേശം", noMuhurat: "ഇന്ന് മുഹൂർത്തം ഇല്ല",

    planetTitle: "ഗ്രഹ സ്ഥാനങ്ങൾ", retrograde: "വക്രി",
    directMotion: "മാർഗി", transitLabel: "ഗോചരം",
    planetDignity: "ഗ്രഹ ബലം", exalted: "ഉച്ചം", debilitated: "നീചം",

    vastuTitle: "വാസ്തു ശാസ്ത്രം", northDir: "വടക്ക്", southDir: "തെക്ക്",
    eastDir: "കിഴക്ക്", westDir: "പടിഞ്ഞാറ്", northEast: "വടക്ക്-കിഴക്ക്",
    northWest: "വടക്ക്-പടിഞ്ഞാറ്", southEast: "തെക്ക്-കിഴക്ക്", southWest: "തെക്ക്-പടിഞ്ഞാറ്",
    vastuTip: "വാസ്തു നുറുങ്ങ്",

    remediesTitle: "പ്രതിവിധികൾ", gemstones: "രത്നക്കല്ലുകൾ",
    mantrasLabel: "മന്ത്രങ്ങൾ", donationLabel: "ദാനം",
    fastingLabel: "ഉപവാസം", yagyaLabel: "യജ്ഞം / ഹവനം",

    subscriptionTitle: "സബ്‌സ്ക്രിപ്ഷൻ", paymentTitle: "സുരക്ഷിത പേയ്‌മെന്റ്",
    plansTitle: "പ്ലാനുകൾ & വില", perMonth: "/ മാസം", perYear: "/ വർഷം",
    currentPlanLabel: "നിലവിലെ പ്ലാൻ", upgradePlanLabel: "അപ്‌ഗ്രേഡ് ചെയ്യുക",
    mostPopular: "ഏറ്റവും ജനപ്രിയം", bestValue: "ഏറ്റവും മൂല്യം",
    planFeatures: "എന്ത് ഉൾപ്പെടുന്നു",

    editProfileTitle: "പ്രൊഫൈൽ എഡിറ്റ് ചെയ്യുക", saveChanges: "മാറ്റങ്ങൾ സംരക്ഷിക്കുക",
    nameLabel: "പേര്", relationLabel: "ബന്ധം", profileUpdated: "പ്രൊഫൈൽ അപ്‌ഡേറ്റ് ചെയ്തു",

    relationshipTitle: "ബന്ധ വിശകലനം", loveTitle: "പ്രണയം & യാഥാർഥ്യം",
    marriageCompatTitle: "വിവാഹ അനുകൂലത",
    synastrySub: "രണ്ട് കുണ്ഡലികൾ തമ്മിലുള്ള പ്രപഞ്ച ബന്ധം",

    myKundliTitle: "എന്റെ കുണ്ഡലി", chartDetails: "ചാർട്ട് വിശദാംശങ്ങൾ",
    planetaryStrength: "ഗ്രഹ ബലം", houseAnalysis: "ഭാവ വിശകലനം",

    alertsTitle: "ദൈനം ദിന അലേർട്ടുകൾ", enableAlerts: "ദൈനം ദിന അലേർട്ടുകൾ പ്രവർത്തനക്ഷമമാക്കുക",
    alertTime: "അലേർട്ട് സമയം", alertsEnabled: "അലേർട്ടുകൾ സജീവം",
    alertsDisabled: "അലേർട്ടുകൾ നിഷ്ക്രിയം",

    forecastTitle: "ഭാവി ഫലം", forecastSub: "നിങ്ങളുടെ അടുത്ത 6 മാസം",
    upcomingEvents: "വരാനിരിക്കുന്ന സംഭവങ്ങൾ", nextSixMonths: "അടുത്ത 6 മാസം",
  },

  // ── PUNJABI ────────────────────────────────────────────────────────────────
  pa: {
    calculating: "ਗਣਨਾ ਹੋ ਰਹੀ ਹੈ...", noData: "ਕੋਈ ਡੇਟਾ ਉਪਲਬਧ ਨਹੀਂ",
    selectProfile: "ਪ੍ਰੋਫਾਈਲ ਚੁਣੋ", birthDataNeeded: "ਜਨਮ ਵੇਰਵਾ ਜ਼ਰੂਰੀ ਹੈ",
    goBack: "ਵਾਪਸ ਜਾਓ", viewReport: "ਰਿਪੋਰਟ ਦੇਖੋ", matchReport: "ਮਿਲਾਨ ਰਿਪੋਰਟ",
    present: "ਹੈ", notPresent: "ਨਹੀਂ ਹੈ",
    auspicious: "ਸ਼ੁਭ", inauspicious: "ਅਸ਼ੁਭ",
    daily: "ਰੋਜ਼ਾਨਾ", weekly: "ਹਫ਼ਤਾਵਾਰੀ", monthly: "ਮਹੀਨਾਵਾਰੀ", yearly: "ਸਾਲਾਨਾ",
    selectSign: "ਆਪਣੀ ਰਾਸ਼ੀ ਚੁਣੋ",

    rashifalTitle: "ਰਾਸ਼ੀਫਲ", todaysRashifal: "ਅੱਜ ਦਾ ਰਾਸ਼ੀਫਲ",
    loveSection: "ਪਿਆਰ", careerSection: "ਕਰੀਅਰ",
    healthSection: "ਸਿਹਤ", moneySection: "ਧਨ",

    panchangTitle: "ਪੰਚਾਂਗ", tithi: "ਤਿੱਥ", vara: "ਵਾਰ",
    yogaPanchang: "ਯੋਗ", karana: "ਕਰਨ",
    sunriseLabel: "ਸੂਰਜ ਚੜ੍ਹਨਾ", sunsetLabel: "ਸੂਰਜ ਡੁੱਬਣਾ",
    auspiciousTimes: "ਸ਼ੁਭ ਮੁਹੂਰਤ", rahukaal: "ਰਾਹੂ ਕਾਲ",
    moonSignLabel: "ਚੰਦਰ ਰਾਸ਼ੀ", paksha: "ਪੱਖ", festivals: "ਤਿਉਹਾਰ",

    kundliMilanTitle: "ਕੁੰਡਲੀ ਮਿਲਾਨ", kundliMilanSub: "ਅਸ਼ਟਕੂਟ ਗੁਣ ਮਿਲਾਨ",
    groomLabel: "ਵਰ", brideLabel: "ਕੁੜੀ",
    checkCompatibility: "ਮਿਲਾਨ ਕਰੋ",
    gunaScore: "ਗੁਣ ਸਕੋਰ", outOf36: "36 ਵਿੱਚੋਂ",
    manglikLabel: "ਮੰਗਲਿਕ", selfProfile: "ਤੁਹਾਡੀ ਕੁੰਡਲੀ",
    partnerProfile: "ਸਾਥੀ ਦੀ ਕੁੰਡਲੀ", addPartner: "ਸਾਥੀ ਜੋੜੋ",
    birthDataMissing: "ਇੱਕ ਜਾਂ ਦੋਵਾਂ ਦਾ ਜਨਮ ਵੇਰਵਾ ਉਪਲਬਧ ਨਹੀਂ",

    milanResult: "ਮਿਲਾਨ ਨਤੀਜਾ", strengthsLabel: "ਸਕਾਰਾਤਮਕ ਪੱਖ",
    challengesLabel: "ਚੁਣੌਤੀਆਂ", marriageOutlook: "ਵਿਆਹ ਸੰਭਾਵਨਾ",
    cosmicInsight: "ਜੋਤਿਸ਼ ਅੰਤਰਦ੍ਰਿਸ਼ਟੀ", overallScore: "ਕੁੱਲ ਅੰਕ",

    doshTitle: "ਦੋਸ਼", manglikDosh: "ਮੰਗਲਿਕ ਦੋਸ਼",
    kaalSarpDosh: "ਕਾਲ ਸਰਪ ਦੋਸ਼", pitruDosh: "ਪਿਤਰੂ ਦੋਸ਼",
    sadhesatiLabel: "ਸਾਢੇ ਸਾਤੀ", remedyLabel: "ਉਪਾਅ",
    doshPresent: "ਹੈ", doshAbsent: "ਨਹੀਂ ਹੈ",

    numerologyTitle: "ਅੰਕ ਜੋਤਿਸ਼", lifePathLabel: "ਜੀਵਨ ਮਾਰਗ ਅੰਕ",
    destinyNumber: "ਭਾਗ ਅੰਕ", soulNumber: "ਆਤਮਾ ਅੰਕ",
    personalityNumber: "ਸ਼ਖ਼ਸੀਅਤ ਅੰਕ",
    luckyNumbers: "ਸ਼ੁਭ ਅੰਕ", luckyColors: "ਸ਼ੁਭ ਰੰਗ",

    luckyTitle: "ਸ਼ੁਭ ਤੱਤ", luckyNumber: "ਸ਼ੁਭ ਅੰਕ",
    luckyColor: "ਸ਼ੁਭ ਰੰਗ", luckyGem: "ਸ਼ੁਭ ਰਤਨ",
    luckyDay: "ਸ਼ੁਭ ਦਿਨ", luckyDirection: "ਸ਼ੁਭ ਦਿਸ਼ਾ",
    luckyMetal: "ਸ਼ੁਭ ਧਾਤੂ",

    muhuratTitle: "ਮੁਹੂਰਤ", marriageMuhurat: "ਵਿਆਹ ਮੁਹੂਰਤ",
    businessMuhurat: "ਕਾਰੋਬਾਰ ਮੁਹੂਰਤ", travelMuhurat: "ਯਾਤਰਾ ਮੁਹੂਰਤ",
    propertyMuhurat: "ਗ੍ਰਹਿ ਪ੍ਰਵੇਸ਼", noMuhurat: "ਅੱਜ ਕੋਈ ਮੁਹੂਰਤ ਨਹੀਂ",

    planetTitle: "ਗ੍ਰਹਿ ਸਥਿਤੀ", retrograde: "ਵਕ੍ਰੀ",
    directMotion: "ਮਾਰਗੀ", transitLabel: "ਗੋਚਰ",
    planetDignity: "ਗ੍ਰਹਿ ਬਲ", exalted: "ਉੱਚ", debilitated: "ਨੀਚ",

    vastuTitle: "ਵਾਸਤੂ ਸ਼ਾਸਤਰ", northDir: "ਉੱਤਰ", southDir: "ਦੱਖਣ",
    eastDir: "ਪੂਰਬ", westDir: "ਪੱਛਮ", northEast: "ਈਸ਼ਾਨ",
    northWest: "ਵਾਯਵ੍ਯ", southEast: "ਅਗਨੇਯ", southWest: "ਨੈਰ੍ਰਿਤ੍ਯ",
    vastuTip: "ਵਾਸਤੂ ਟਿਪ",

    remediesTitle: "ਉਪਾਅ", gemstones: "ਰਤਨ",
    mantrasLabel: "ਮੰਤਰ", donationLabel: "ਦਾਨ",
    fastingLabel: "ਵਰਤ", yagyaLabel: "ਯੱਗ / ਹਵਨ",

    subscriptionTitle: "ਸਦੱਸਤਾ", paymentTitle: "ਸੁਰੱਖਿਅਤ ਭੁਗਤਾਨ",
    plansTitle: "ਯੋਜਨਾਵਾਂ ਅਤੇ ਕੀਮਤਾਂ", perMonth: "/ ਮਹੀਨਾ", perYear: "/ ਸਾਲ",
    currentPlanLabel: "ਮੌਜੂਦਾ ਯੋਜਨਾ", upgradePlanLabel: "ਅੱਪਗ੍ਰੇਡ ਕਰੋ",
    mostPopular: "ਸਭ ਤੋਂ ਵੱਧ ਪਸੰਦੀਦਾ", bestValue: "ਸਰਵੋਤਮ ਮੁੱਲ",
    planFeatures: "ਕੀ ਸ਼ਾਮਲ ਹੈ",

    editProfileTitle: "ਪ੍ਰੋਫਾਈਲ ਸੰਪਾਦਿਤ ਕਰੋ", saveChanges: "ਬਦਲਾਅ ਸੁਰੱਖਿਅਤ ਕਰੋ",
    nameLabel: "ਨਾਮ", relationLabel: "ਰਿਸ਼ਤਾ", profileUpdated: "ਪ੍ਰੋਫਾਈਲ ਅਪਡੇਟ ਹੋਈ",

    relationshipTitle: "ਰਿਸ਼ਤੇ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ", loveTitle: "ਪਿਆਰ ਅਤੇ ਹਕੀਕਤ",
    marriageCompatTitle: "ਵਿਆਹ ਅਨੁਕੂਲਤਾ",
    synastrySub: "ਦੋ ਕੁੰਡਲੀਆਂ ਵਿਚਕਾਰ ਬ੍ਰਹਿਮੰਡੀ ਸੰਬੰਧ",

    myKundliTitle: "ਮੇਰੀ ਕੁੰਡਲੀ", chartDetails: "ਚਾਰਟ ਵੇਰਵਾ",
    planetaryStrength: "ਗ੍ਰਹਿ ਬਲ", houseAnalysis: "ਭਾਵ ਵਿਸ਼ਲੇਸ਼ਣ",

    alertsTitle: "ਰੋਜ਼ਾਨਾ ਅਲਰਟ", enableAlerts: "ਰੋਜ਼ਾਨਾ ਅਲਰਟ ਚਾਲੂ ਕਰੋ",
    alertTime: "ਅਲਰਟ ਸਮਾਂ", alertsEnabled: "ਅਲਰਟ ਸਕਿਰਿਆ",
    alertsDisabled: "ਅਲਰਟ ਬੰਦ",

    forecastTitle: "ਭਵਿੱਖਫਲ", forecastSub: "ਤੁਹਾਡੇ ਅਗਲੇ 6 ਮਹੀਨੇ",
    upcomingEvents: "ਆਉਣ ਵਾਲੀਆਂ ਘਟਨਾਵਾਂ", nextSixMonths: "ਅਗਲੇ 6 ਮਹੀਨੇ",
  },

  // ── ODIA ───────────────────────────────────────────────────────────────────
  or: {
    calculating: "ଗଣନା ଚାଲୁ...", noData: "ତଥ୍ୟ ଉପଲବ୍ଧ ନଥିଲ",
    selectProfile: "ପ୍ରୋଫାଇଲ ବଛନ୍ତୁ", birthDataNeeded: "ଜନ୍ମ ବିବରଣ ଆବଶ୍ୟକ",
    goBack: "ଫେରି ଯାଆନ୍ତୁ", viewReport: "ରିପୋର୍ଟ ଦେଖନ୍ତୁ", matchReport: "ମିଳାନ ରିପୋର୍ଟ",
    present: "ଅଛି", notPresent: "ନଥିଲ",
    auspicious: "ଶୁଭ", inauspicious: "ଅଶୁଭ",
    daily: "ଦୈନିକ", weekly: "ସାପ୍ତାହିକ", monthly: "ମାସିକ", yearly: "ବାର୍ଷିକ",
    selectSign: "ଆପଣଙ୍କ ରାଶି ବଛନ୍ତୁ",

    rashifalTitle: "ରାଶିଫଳ", todaysRashifal: "ଆଜିର ରାଶିଫଳ",
    loveSection: "ପ୍ରେମ", careerSection: "କ୍ୟାରିଅର",
    healthSection: "ସ୍ୱାସ୍ଥ୍ୟ", moneySection: "ଧନ",

    panchangTitle: "ପଂଚାଙ୍ଗ", tithi: "ତିଥି", vara: "ବାର",
    yogaPanchang: "ଯୋଗ", karana: "କରଣ",
    sunriseLabel: "ସୂର୍ୟୋଦୟ", sunsetLabel: "ସୂର୍ୟାସ୍ତ",
    auspiciousTimes: "ଶୁଭ ମୁହୂର୍ତ", rahukaal: "ରାହୁ କାଳ",
    moonSignLabel: "ଚନ୍ଦ୍ର ରାଶି", paksha: "ପକ୍ଷ", festivals: "ପର୍ବ",

    kundliMilanTitle: "କୁଣ୍ଡଳୀ ମିଳାନ", kundliMilanSub: "ଅଷ୍ଟକୂଟ ଗୁଣ ମିଳାନ",
    groomLabel: "ବର", brideLabel: "କନ୍ୟା",
    checkCompatibility: "ମିଳାନ ଦେଖନ୍ତୁ",
    gunaScore: "ଗୁଣ ସ୍କୋର", outOf36: "36 ରୁ",
    manglikLabel: "ମାଙ୍ଗଳିକ", selfProfile: "ଆପଣଙ୍କ କୁଣ୍ଡଳୀ",
    partnerProfile: "ସାଥୀଙ୍କ କୁଣ୍ଡଳୀ", addPartner: "ସାଥୀ ଯୋଗ",
    birthDataMissing: "ଜଣ ବା ଉଭୟଙ୍କ ଜନ୍ମ ବିବରଣ ଅନୁପଲବ୍ଧ",

    milanResult: "ମିଳାନ ଫଳ", strengthsLabel: "ସକାରାତ୍ମକ ଦିଗ",
    challengesLabel: "ଚ୍ୟାଲେଞ୍ଜ", marriageOutlook: "ବିବାହ ସମ୍ଭାବ୍ୟ",
    cosmicInsight: "ଜ୍ୟୋତିଷ ଦ୍ରଷ୍ଟି", overallScore: "ମୋଟ ଗୁଣ",

    doshTitle: "ଦୋଷ", manglikDosh: "ମାଙ୍ଗଳିକ ଦୋଷ",
    kaalSarpDosh: "କାଳ ସର୍ପ ଦୋଷ", pitruDosh: "ପିତୃ ଦୋଷ",
    sadhesatiLabel: "ସାଢ଼େ ସାତି", remedyLabel: "ଉପାୟ",
    doshPresent: "ଅଛି", doshAbsent: "ନଥିଲ",

    numerologyTitle: "ଅଙ୍କ ଜ୍ୟୋତିଷ", lifePathLabel: "ଜୀବନ ପଥ ସଂଖ୍ୟା",
    destinyNumber: "ଭାଗ୍ୟ ଅଙ୍କ", soulNumber: "ଆତ୍ମ ଅଙ୍କ",
    personalityNumber: "ବ୍ୟକ୍ତିତ୍ୱ ଅଙ୍କ",
    luckyNumbers: "ଶୁଭ ଅଙ୍କ", luckyColors: "ଶୁଭ ରଙ୍ଗ",

    luckyTitle: "ଶୁଭ ତତ୍ତ୍ୱ", luckyNumber: "ଶୁଭ ଅଙ୍କ",
    luckyColor: "ଶୁଭ ରଙ୍ଗ", luckyGem: "ଶୁଭ ରତ୍ନ",
    luckyDay: "ଶୁଭ ଦିନ", luckyDirection: "ଶୁଭ ଦିଗ",
    luckyMetal: "ଶୁଭ ଧାତୁ",

    muhuratTitle: "ମୁହୂର୍ତ", marriageMuhurat: "ବିବାହ ମୁହୂର୍ତ",
    businessMuhurat: "ବ୍ୟବସାୟ ମୁହୂର୍ତ", travelMuhurat: "ଯାତ୍ରା ମୁହୂର୍ତ",
    propertyMuhurat: "ଗ୍ରହ ପ୍ରବେଶ", noMuhurat: "ଆଜି ମୁହୂର୍ତ ନାହିଁ",

    planetTitle: "ଗ୍ରହ ସ୍ଥିତି", retrograde: "ବକ୍ରୀ",
    directMotion: "ମାର୍ଗୀ", transitLabel: "ଗୋଚର",
    planetDignity: "ଗ୍ରହ ବଳ", exalted: "ଉଚ୍ଚ", debilitated: "ନୀଚ",

    vastuTitle: "ବାସ୍ତୁ ଶାସ୍ତ୍ର", northDir: "ଉତ୍ତର", southDir: "ଦକ୍ଷିଣ",
    eastDir: "ପୂର୍ବ", westDir: "ପଶ୍ଚିମ", northEast: "ଈଶାନ",
    northWest: "ବାୟବ୍ୟ", southEast: "ଅଗ୍ନି", southWest: "ନୈଋତ",
    vastuTip: "ବାସ୍ତୁ ଟିପ",

    remediesTitle: "ଉପାୟ", gemstones: "ରତ୍ନ",
    mantrasLabel: "ମନ୍ତ୍ର", donationLabel: "ଦାନ",
    fastingLabel: "ଉପବାସ", yagyaLabel: "ଯଜ୍ଞ / ହବନ",

    subscriptionTitle: "ସଦସ୍ୟତା", paymentTitle: "ନିରାପଦ ଭୁଗ୍ତାନ",
    plansTitle: "ସଦସ୍ୟ ଯୋଜନା", perMonth: "/ ମାସ", perYear: "/ ବର୍ଷ",
    currentPlanLabel: "ବର୍ତ୍ତମାନ ଯୋଜନା", upgradePlanLabel: "ଅପଗ୍ରେଡ",
    mostPopular: "ସବୁଠୁ ଲୋକପ୍ରିୟ", bestValue: "ସର୍ବୋତ୍ତମ ମୂଲ୍ୟ",
    planFeatures: "କ'ଣ ଅନ୍ତର୍ଭୁକ୍ତ",

    editProfileTitle: "ପ୍ରୋଫାଇଲ ସଂଶୋଧନ", saveChanges: "ପରିବର୍ତ୍ତନ ସଂରକ୍ଷଣ",
    nameLabel: "ନାମ", relationLabel: "ସମ୍ପର୍କ", profileUpdated: "ପ୍ରୋଫାଇଲ ଅଦ୍ୟତନ",

    relationshipTitle: "ସମ୍ପର୍କ ବିଶ୍ଳେଷଣ", loveTitle: "ପ୍ରେମ ଓ ବାସ୍ତବ",
    marriageCompatTitle: "ବିବାହ ଅନୁକୂଳ",
    synastrySub: "ଦୁଇ କୁଣ୍ଡଳୀ ମଧ୍ୟରେ ବ୍ରହ୍ମାଣ୍ଡ ସଂଯୋଗ",

    myKundliTitle: "ମୋ କୁଣ୍ଡଳୀ", chartDetails: "ଚାର୍ଟ ବିବରଣ",
    planetaryStrength: "ଗ୍ରହ ବଳ", houseAnalysis: "ଭାବ ବିଶ୍ଳେଷଣ",

    alertsTitle: "ଦୈନିକ ଆଲର୍ଟ", enableAlerts: "ଦୈନିକ ଆଲର୍ଟ ସକ୍ରିୟ",
    alertTime: "ଆଲର୍ଟ ସମୟ", alertsEnabled: "ଆଲର୍ଟ ସକ୍ରିୟ",
    alertsDisabled: "ଆଲର୍ଟ ବନ୍ଦ",

    forecastTitle: "ଭବିଷ୍ୟଫଳ", forecastSub: "ଆପଣଙ୍କ ପ୍ରାୟ 6 ମାସ",
    upcomingEvents: "ଆଗାମୀ ଘଟଣା", nextSixMonths: "ପ୍ରାୟ 6 ମାସ",
  },

  // ── ASSAMESE ───────────────────────────────────────────────────────────────
  as: {
    calculating: "গণনা কৰা হৈছে...", noData: "তথ্য পোৱা নাই",
    selectProfile: "প্ৰ'ফাইল বাছনি কৰক", birthDataNeeded: "জন্মৰ বিৱৰণ প্ৰয়োজন",
    goBack: "উভতি যাওক", viewReport: "ৰিপ'ৰ্ট চাওক", matchReport: "মিলান ৰিপ'ৰ্ট",
    present: "আছে", notPresent: "নাই",
    auspicious: "শুভ", inauspicious: "অশুভ",
    daily: "দৈনিক", weekly: "সাপ্তাহিক", monthly: "মাহিলী", yearly: "বাৰ্ষিক",
    selectSign: "আপোনাৰ ৰাশি বাছনি কৰক",

    rashifalTitle: "ৰাশিফল", todaysRashifal: "আজিৰ ৰাশিফল",
    loveSection: "প্ৰেম", careerSection: "কেৰিয়াৰ",
    healthSection: "স্বাস্থ্য", moneySection: "ধন",

    panchangTitle: "পঞ্চাং", tithi: "তিথি", vara: "বাৰ",
    yogaPanchang: "যোগ", karana: "কৰণ",
    sunriseLabel: "সূৰ্যোদয়", sunsetLabel: "সূৰ্যাস্ত",
    auspiciousTimes: "শুভ মুহূৰ্ত", rahukaal: "ৰাহু কাল",
    moonSignLabel: "চন্দ্ৰ ৰাশি", paksha: "পক্ষ", festivals: "উৎসৱ",

    kundliMilanTitle: "কুণ্ডলী মিলান", kundliMilanSub: "অষ্টকূট গুণ মিলান",
    groomLabel: "বৰ", brideLabel: "কইনা",
    checkCompatibility: "মিলান চাওক",
    gunaScore: "গুণ স্ক'ৰ", outOf36: "৩৬ৰ মাজত",
    manglikLabel: "মাংগলিক", selfProfile: "আপোনাৰ কুণ্ডলী",
    partnerProfile: "সংগীৰ কুণ্ডলী", addPartner: "সংগী যোগ কৰক",
    birthDataMissing: "এজন বা দুয়োজনৰ জন্মৰ বিৱৰণ পোৱা নাই",

    milanResult: "মিলান ফলাফল", strengthsLabel: "ইতিবাচক দিশ",
    challengesLabel: "প্ৰত্যাহ্বান", marriageOutlook: "বিবাহৰ সম্ভাৱনা",
    cosmicInsight: "জ্যোতিষ অন্তৰ্দৃষ্টি", overallScore: "মুঠ স্ক'ৰ",

    doshTitle: "দোষ", manglikDosh: "মাংগলিক দোষ",
    kaalSarpDosh: "কাল সৰ্প দোষ", pitruDosh: "পিতৃ দোষ",
    sadhesatiLabel: "সাঢ়ে সাতী", remedyLabel: "উপায়",
    doshPresent: "আছে", doshAbsent: "নাই",

    numerologyTitle: "অংক জ্যোতিষ", lifePathLabel: "জীৱন পথ সংখ্যা",
    destinyNumber: "ভাগ্যাংক", soulNumber: "আত্মাংক",
    personalityNumber: "ব্যক্তিত্ব অংক",
    luckyNumbers: "শুভ সংখ্যা", luckyColors: "শুভ ৰং",

    luckyTitle: "শুভ তত্ত্ব", luckyNumber: "শুভ সংখ্যা",
    luckyColor: "শুভ ৰং", luckyGem: "শুভ ৰত্ন",
    luckyDay: "শুভ দিন", luckyDirection: "শুভ দিশ",
    luckyMetal: "শুভ ধাতু",

    muhuratTitle: "মুহূৰ্ত", marriageMuhurat: "বিবাহ মুহূৰ্ত",
    businessMuhurat: "ব্যৱসায় মুহূৰ্ত", travelMuhurat: "যাত্ৰা মুহূৰ্ত",
    propertyMuhurat: "গৃহ প্ৰৱেশ", noMuhurat: "আজি কোনো মুহূৰ্ত নাই",

    planetTitle: "গ্ৰহৰ স্থিতি", retrograde: "বক্ৰী",
    directMotion: "মাৰ্গী", transitLabel: "গোচৰ",
    planetDignity: "গ্ৰহ বল", exalted: "উচ্চ", debilitated: "নীচ",

    vastuTitle: "বাস্তু শাস্ত্ৰ", northDir: "উত্তৰ", southDir: "দক্ষিণ",
    eastDir: "পূব", westDir: "পশ্চিম", northEast: "ঈশান",
    northWest: "বায়ব্য", southEast: "অগ্নি", southWest: "নৈৰিত্য",
    vastuTip: "বাস্তু টিপ",

    remediesTitle: "উপায়", gemstones: "ৰত্নপাথৰ",
    mantrasLabel: "মন্ত্ৰ", donationLabel: "দান",
    fastingLabel: "উপবাস", yagyaLabel: "যজ্ঞ / হোম",

    subscriptionTitle: "সদস্যতা", paymentTitle: "সুৰক্ষিত পেমেন্ট",
    plansTitle: "সদস্যতা পৰিকল্পনা", perMonth: "/ মাহ", perYear: "/ বছৰ",
    currentPlanLabel: "বৰ্তমান পৰিকল্পনা", upgradePlanLabel: "আপগ্ৰেড কৰক",
    mostPopular: "সবাতোকৈ জনপ্ৰিয়", bestValue: "সৰ্বোত্তম মূল্য",
    planFeatures: "কি অন্তৰ্ভুক্ত",

    editProfileTitle: "প্ৰ'ফাইল সম্পাদনা", saveChanges: "পৰিৱৰ্তন সংৰক্ষণ",
    nameLabel: "নাম", relationLabel: "সম্পৰ্ক", profileUpdated: "প্ৰ'ফাইল আপডেট হৈছে",

    relationshipTitle: "সম্পৰ্ক বিশ্লেষণ", loveTitle: "প্ৰেম আৰু বাস্তৱ",
    marriageCompatTitle: "বিবাহ অনুকূলতা",
    synastrySub: "দুটা কুণ্ডলীৰ মাজৰ মহাজাগতিক সম্পৰ্ক",

    myKundliTitle: "মোৰ কুণ্ডলী", chartDetails: "চাৰ্ট বিৱৰণ",
    planetaryStrength: "গ্ৰহ বল", houseAnalysis: "ভাৱ বিশ্লেষণ",

    alertsTitle: "দৈনিক সতৰ্কতা", enableAlerts: "দৈনিক সতৰ্কতা সক্ৰিয়",
    alertTime: "সতৰ্কতাৰ সময়", alertsEnabled: "সতৰ্কতা সক্ৰিয়",
    alertsDisabled: "সতৰ্কতা বন্ধ",

    forecastTitle: "ভৱিষ্যৎফল", forecastSub: "আপোনাৰ পৰৱৰ্তী ৬ মাহ",
    upcomingEvents: "আসন্ন ঘটনা", nextSixMonths: "পৰৱৰ্তী ৬ মাহ",
  },

  // ── CHINESE ────────────────────────────────────────────────────────────────
  zh: {
    calculating: "计算中...", noData: "暂无数据",
    selectProfile: "选择档案", birthDataNeeded: "需要出生资料",
    goBack: "返回", viewReport: "查看报告", matchReport: "配对报告",
    present: "存在", notPresent: "不存在",
    auspicious: "吉祥", inauspicious: "不吉",
    daily: "每日", weekly: "每周", monthly: "每月", yearly: "每年",
    selectSign: "选择你的星座",

    rashifalTitle: "星座运势", todaysRashifal: "今日运势",
    loveSection: "感情", careerSection: "事业",
    healthSection: "健康", moneySection: "财运",

    panchangTitle: "吠陀历法", tithi: "月相日", vara: "星期",
    yogaPanchang: "瑜伽", karana: "卡拉纳",
    sunriseLabel: "日出", sunsetLabel: "日落",
    auspiciousTimes: "吉时", rahukaal: "罗睺时",
    moonSignLabel: "月亮星座", paksha: "月份", festivals: "节日",

    kundliMilanTitle: "星盘配对", kundliMilanSub: "八因素相容性分析",
    groomLabel: "新郎", brideLabel: "新娘",
    checkCompatibility: "检测配对",
    gunaScore: "古纳分数", outOf36: "满分36",
    manglikLabel: "火星受损", selfProfile: "你的星盘",
    partnerProfile: "伴侣星盘", addPartner: "添加伴侣",
    birthDataMissing: "一人或双方出生资料缺失",

    milanResult: "配对结果", strengthsLabel: "优势",
    challengesLabel: "挑战", marriageOutlook: "婚姻展望",
    cosmicInsight: "星象洞察", overallScore: "综合分数",

    doshTitle: "不利因素", manglikDosh: "火星缺陷",
    kaalSarpDosh: "蛇神缺陷", pitruDosh: "祖先缺陷",
    sadhesatiLabel: "土星7.5年", remedyLabel: "化解",
    doshPresent: "存在", doshAbsent: "不存在",

    numerologyTitle: "数字命理", lifePathLabel: "生命数字",
    destinyNumber: "命运数字", soulNumber: "灵魂数字",
    personalityNumber: "个性数字",
    luckyNumbers: "幸运数字", luckyColors: "幸运色",

    luckyTitle: "幸运元素", luckyNumber: "幸运数字",
    luckyColor: "幸运颜色", luckyGem: "幸运宝石",
    luckyDay: "幸运日", luckyDirection: "幸运方向",
    luckyMetal: "幸运金属",

    muhuratTitle: "吉时", marriageMuhurat: "婚礼吉时",
    businessMuhurat: "开业吉时", travelMuhurat: "出行吉时",
    propertyMuhurat: "入宅吉时", noMuhurat: "今日无吉时",

    planetTitle: "行星位置", retrograde: "逆行",
    directMotion: "顺行", transitLabel: "过境",
    planetDignity: "行星力量", exalted: "入旺", debilitated: "入弱",

    vastuTitle: "吠陀风水", northDir: "北", southDir: "南",
    eastDir: "东", westDir: "西", northEast: "东北",
    northWest: "西北", southEast: "东南", southWest: "西南",
    vastuTip: "风水提示",

    remediesTitle: "化解之法", gemstones: "宝石",
    mantrasLabel: "咒语", donationLabel: "布施",
    fastingLabel: "斋戒", yagyaLabel: "火祭",

    subscriptionTitle: "订阅", paymentTitle: "安全支付",
    plansTitle: "订阅方案", perMonth: "/ 月", perYear: "/ 年",
    currentPlanLabel: "当前方案", upgradePlanLabel: "升级方案",
    mostPopular: "最受欢迎", bestValue: "最超值",
    planFeatures: "包含内容",

    editProfileTitle: "编辑档案", saveChanges: "保存更改",
    nameLabel: "姓名", relationLabel: "关系", profileUpdated: "档案已更新",

    relationshipTitle: "关系分析", loveTitle: "爱情与现实",
    marriageCompatTitle: "婚姻配对",
    synastrySub: "两张星盘之间的宇宙连接",

    myKundliTitle: "我的星盘", chartDetails: "星盘详情",
    planetaryStrength: "行星力量", houseAnalysis: "宫位分析",

    alertsTitle: "每日提醒", enableAlerts: "开启每日提醒",
    alertTime: "提醒时间", alertsEnabled: "提醒已开启",
    alertsDisabled: "提醒已关闭",

    forecastTitle: "运势预测", forecastSub: "未来6个月解析",
    upcomingEvents: "即将到来的事件", nextSixMonths: "未来6个月",
  },

  // ── SPANISH ────────────────────────────────────────────────────────────────
  es: {
    calculating: "Calculando...", noData: "Sin datos disponibles",
    selectProfile: "Seleccionar perfil", birthDataNeeded: "Se requieren datos de nacimiento",
    goBack: "Volver", viewReport: "Ver informe", matchReport: "Informe de compatibilidad",
    present: "Presente", notPresent: "Ausente",
    auspicious: "Auspicioso", inauspicious: "Inauspicioso",
    daily: "Diario", weekly: "Semanal", monthly: "Mensual", yearly: "Anual",
    selectSign: "Selecciona tu signo",

    rashifalTitle: "Horóscopo", todaysRashifal: "Horóscopo de hoy",
    loveSection: "Amor", careerSection: "Carrera",
    healthSection: "Salud", moneySection: "Dinero",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Día",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Amanecer", sunsetLabel: "Atardecer",
    auspiciousTimes: "Tiempos auspiciosos", rahukaal: "Rahu Kaal",
    moonSignLabel: "Signo lunar", paksha: "Paksha", festivals: "Festivales",

    kundliMilanTitle: "Compatibilidad Kundli", kundliMilanSub: "Análisis Ashtakoot",
    groomLabel: "Novio", brideLabel: "Novia",
    checkCompatibility: "Verificar compatibilidad",
    gunaScore: "Puntuación Guna", outOf36: "de 36",
    manglikLabel: "Manglik", selfProfile: "Tu Kundli",
    partnerProfile: "Kundli de tu pareja", addPartner: "Agregar pareja",
    birthDataMissing: "Faltan datos de nacimiento de uno o ambos",

    milanResult: "Resultado de compatibilidad", strengthsLabel: "Fortalezas",
    challengesLabel: "Desafíos", marriageOutlook: "Perspectiva matrimonial",
    cosmicInsight: "Visión cósmica", overallScore: "Puntuación total",

    doshTitle: "Doshas", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Remedio",
    doshPresent: "Presente", doshAbsent: "Ausente",

    numerologyTitle: "Numerología", lifePathLabel: "Número de camino de vida",
    destinyNumber: "Número del destino", soulNumber: "Número del alma",
    personalityNumber: "Número de personalidad",
    luckyNumbers: "Números de la suerte", luckyColors: "Colores de la suerte",

    luckyTitle: "Elementos de la suerte", luckyNumber: "Número de la suerte",
    luckyColor: "Color de la suerte", luckyGem: "Gema de la suerte",
    luckyDay: "Día de la suerte", luckyDirection: "Dirección de la suerte",
    luckyMetal: "Metal de la suerte",

    muhuratTitle: "Muhurat", marriageMuhurat: "Muhurat de bodas",
    businessMuhurat: "Muhurat de negocios", travelMuhurat: "Muhurat de viaje",
    propertyMuhurat: "Entrada al hogar", noMuhurat: "Sin Muhurat hoy",

    planetTitle: "Posiciones planetarias", retrograde: "Retrógrado",
    directMotion: "Directo", transitLabel: "Tránsito",
    planetDignity: "Dignidad planetaria", exalted: "Exaltado", debilitated: "Debilitado",

    vastuTitle: "Vastu Shastra", northDir: "Norte", southDir: "Sur",
    eastDir: "Este", westDir: "Oeste", northEast: "Noreste",
    northWest: "Noroeste", southEast: "Sureste", southWest: "Suroeste",
    vastuTip: "Consejo Vastu",

    remediesTitle: "Remedios", gemstones: "Gemas",
    mantrasLabel: "Mantras", donationLabel: "Donación",
    fastingLabel: "Ayuno", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Suscripción", paymentTitle: "Pago Seguro",
    plansTitle: "Planes y precios", perMonth: "/ mes", perYear: "/ año",
    currentPlanLabel: "Plan actual", upgradePlanLabel: "Actualizar plan",
    mostPopular: "Más popular", bestValue: "Mejor valor",
    planFeatures: "Qué incluye",

    editProfileTitle: "Editar perfil", saveChanges: "Guardar cambios",
    nameLabel: "Nombre", relationLabel: "Relación", profileUpdated: "Perfil actualizado",

    relationshipTitle: "Análisis de relación", loveTitle: "Amor y realidad",
    marriageCompatTitle: "Compatibilidad matrimonial",
    synastrySub: "Conexión cósmica entre dos cartas",

    myKundliTitle: "Mi Kundli", chartDetails: "Detalles del gráfico",
    planetaryStrength: "Fuerza planetaria", houseAnalysis: "Análisis de casas",

    alertsTitle: "Alertas diarias", enableAlerts: "Activar alertas diarias",
    alertTime: "Hora de alerta", alertsEnabled: "Alertas activadas",
    alertsDisabled: "Alertas desactivadas",

    forecastTitle: "Pronóstico", forecastSub: "Tus próximos 6 meses",
    upcomingEvents: "Próximos eventos", nextSixMonths: "Próximos 6 meses",
  },

  // ── ARABIC ─────────────────────────────────────────────────────────────────
  ar: {
    calculating: "جارٍ الحساب...", noData: "لا توجد بيانات",
    selectProfile: "اختر الملف الشخصي", birthDataNeeded: "بيانات الميلاد مطلوبة",
    goBack: "رجوع", viewReport: "عرض التقرير", matchReport: "تقرير التوافق",
    present: "موجود", notPresent: "غير موجود",
    auspicious: "مبارك", inauspicious: "غير مبارك",
    daily: "يومي", weekly: "أسبوعي", monthly: "شهري", yearly: "سنوي",
    selectSign: "اختر برجك",

    rashifalTitle: "التوقعات الفلكية", todaysRashifal: "توقعات اليوم",
    loveSection: "الحب", careerSection: "المهنة",
    healthSection: "الصحة", moneySection: "المال",

    panchangTitle: "التقويم الفيدي", tithi: "تيثي", vara: "اليوم",
    yogaPanchang: "يوغا", karana: "كارانا",
    sunriseLabel: "شروق الشمس", sunsetLabel: "غروب الشمس",
    auspiciousTimes: "الأوقات المباركة", rahukaal: "راهو كال",
    moonSignLabel: "برج القمر", paksha: "باكشا", festivals: "المهرجانات",

    kundliMilanTitle: "توافق الكوندلي", kundliMilanSub: "تحليل أشتاكوت",
    groomLabel: "العريس", brideLabel: "العروس",
    checkCompatibility: "التحقق من التوافق",
    gunaScore: "نقاط غونا", outOf36: "من 36",
    manglikLabel: "مانجليك", selfProfile: "كوندليك",
    partnerProfile: "كوندلي الشريك", addPartner: "إضافة شريك",
    birthDataMissing: "بيانات الميلاد مفقودة لأحد الشخصين أو كليهما",

    milanResult: "نتيجة التوافق", strengthsLabel: "نقاط القوة",
    challengesLabel: "التحديات", marriageOutlook: "توقعات الزواج",
    cosmicInsight: "رؤية كونية", overallScore: "المجموع الكلي",

    doshTitle: "العوائق الفلكية", manglikDosh: "عائق مانجليك",
    kaalSarpDosh: "عائق كال سارب", pitruDosh: "عائق الأسلاف",
    sadhesatiLabel: "ساده ساتي", remedyLabel: "العلاج",
    doshPresent: "موجود", doshAbsent: "غير موجود",

    numerologyTitle: "علم الأرقام", lifePathLabel: "رقم مسار الحياة",
    destinyNumber: "رقم المصير", soulNumber: "رقم الروح",
    personalityNumber: "رقم الشخصية",
    luckyNumbers: "الأرقام المحظوظة", luckyColors: "الألوان المحظوظة",

    luckyTitle: "العناصر المحظوظة", luckyNumber: "الرقم المحظوظ",
    luckyColor: "اللون المحظوظ", luckyGem: "الجوهرة المحظوظة",
    luckyDay: "اليوم المحظوظ", luckyDirection: "الاتجاه المحظوظ",
    luckyMetal: "المعدن المحظوظ",

    muhuratTitle: "الوقت المثالي", marriageMuhurat: "موعد الزفاف",
    businessMuhurat: "موعد العمل", travelMuhurat: "موعد السفر",
    propertyMuhurat: "الدخول للمنزل", noMuhurat: "لا يوجد موعد مثالي اليوم",

    planetTitle: "مواضع الكواكب", retrograde: "تراجعي",
    directMotion: "مباشر", transitLabel: "عبور",
    planetDignity: "قوة الكوكب", exalted: "رفيع", debilitated: "ضعيف",

    vastuTitle: "فاستو شاسترا", northDir: "شمال", southDir: "جنوب",
    eastDir: "شرق", westDir: "غرب", northEast: "شمال شرق",
    northWest: "شمال غرب", southEast: "جنوب شرق", southWest: "جنوب غرب",
    vastuTip: "نصيحة فاستو",

    remediesTitle: "العلاجات", gemstones: "الأحجار الكريمة",
    mantrasLabel: "المانترا", donationLabel: "الصدقة",
    fastingLabel: "الصيام", yagyaLabel: "يجنا / هافان",

    subscriptionTitle: "الاشتراك", paymentTitle: "دفع آمن",
    plansTitle: "الخطط والأسعار", perMonth: "/ شهر", perYear: "/ سنة",
    currentPlanLabel: "الخطة الحالية", upgradePlanLabel: "ترقية الخطة",
    mostPopular: "الأكثر شيوعاً", bestValue: "أفضل قيمة",
    planFeatures: "ما يشمل",

    editProfileTitle: "تعديل الملف", saveChanges: "حفظ التغييرات",
    nameLabel: "الاسم", relationLabel: "العلاقة", profileUpdated: "تم تحديث الملف",

    relationshipTitle: "تحليل العلاقة", loveTitle: "الحب والواقع",
    marriageCompatTitle: "توافق الزواج",
    synastrySub: "الرابط الكوني بين خريطتين",

    myKundliTitle: "كوندلي", chartDetails: "تفاصيل الخريطة",
    planetaryStrength: "قوة الكواكب", houseAnalysis: "تحليل البيوت",

    alertsTitle: "التنبيهات اليومية", enableAlerts: "تفعيل التنبيهات اليومية",
    alertTime: "وقت التنبيه", alertsEnabled: "التنبيهات مفعلة",
    alertsDisabled: "التنبيهات معطلة",

    forecastTitle: "التوقعات", forecastSub: "الأشهر الستة القادمة",
    upcomingEvents: "الأحداث القادمة", nextSixMonths: "الأشهر الستة القادمة",
  },

  // ── FRENCH ─────────────────────────────────────────────────────────────────
  fr: {
    calculating: "Calcul en cours...", noData: "Aucune donnée disponible",
    selectProfile: "Sélectionner un profil", birthDataNeeded: "Données de naissance requises",
    goBack: "Retour", viewReport: "Voir le rapport", matchReport: "Rapport de compatibilité",
    present: "Présent", notPresent: "Absent",
    auspicious: "Favorable", inauspicious: "Défavorable",
    daily: "Quotidien", weekly: "Hebdomadaire", monthly: "Mensuel", yearly: "Annuel",
    selectSign: "Choisissez votre signe",

    rashifalTitle: "Horoscope", todaysRashifal: "Horoscope du jour",
    loveSection: "Amour", careerSection: "Carrière",
    healthSection: "Santé", moneySection: "Argent",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Jour",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Lever du soleil", sunsetLabel: "Coucher du soleil",
    auspiciousTimes: "Moments favorables", rahukaal: "Rahu Kaal",
    moonSignLabel: "Signe lunaire", paksha: "Paksha", festivals: "Festivals",

    kundliMilanTitle: "Compatibilité Kundli", kundliMilanSub: "Analyse Ashtakoot",
    groomLabel: "Marié", brideLabel: "Mariée",
    checkCompatibility: "Vérifier la compatibilité",
    gunaScore: "Score Guna", outOf36: "sur 36",
    manglikLabel: "Manglik", selfProfile: "Votre Kundli",
    partnerProfile: "Kundli du partenaire", addPartner: "Ajouter un partenaire",
    birthDataMissing: "Données de naissance manquantes pour l'un ou les deux",

    milanResult: "Résultat de compatibilité", strengthsLabel: "Points forts",
    challengesLabel: "Défis", marriageOutlook: "Perspectives matrimoniales",
    cosmicInsight: "Aperçu cosmique", overallScore: "Score global",

    doshTitle: "Doshas", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Remède",
    doshPresent: "Présent", doshAbsent: "Absent",

    numerologyTitle: "Numérologie", lifePathLabel: "Nombre de chemin de vie",
    destinyNumber: "Nombre du destin", soulNumber: "Nombre de l'âme",
    personalityNumber: "Nombre de personnalité",
    luckyNumbers: "Nombres chanceux", luckyColors: "Couleurs chanceuses",

    luckyTitle: "Éléments chanceux", luckyNumber: "Nombre chanceux",
    luckyColor: "Couleur chanceuse", luckyGem: "Pierre précieuse chanceuse",
    luckyDay: "Jour chanceux", luckyDirection: "Direction chanceuse",
    luckyMetal: "Métal chanceux",

    muhuratTitle: "Muhurat", marriageMuhurat: "Muhurat de mariage",
    businessMuhurat: "Muhurat d'affaires", travelMuhurat: "Muhurat de voyage",
    propertyMuhurat: "Entrée dans le foyer", noMuhurat: "Pas de Muhurat aujourd'hui",

    planetTitle: "Positions planétaires", retrograde: "Rétrograde",
    directMotion: "Direct", transitLabel: "Transit",
    planetDignity: "Dignité planétaire", exalted: "Exalté", debilitated: "Affaibli",

    vastuTitle: "Vastu Shastra", northDir: "Nord", southDir: "Sud",
    eastDir: "Est", westDir: "Ouest", northEast: "Nord-Est",
    northWest: "Nord-Ouest", southEast: "Sud-Est", southWest: "Sud-Ouest",
    vastuTip: "Conseil Vastu",

    remediesTitle: "Remèdes", gemstones: "Pierres précieuses",
    mantrasLabel: "Mantras", donationLabel: "Don",
    fastingLabel: "Jeûne", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Abonnement", paymentTitle: "Paiement Sécurisé",
    plansTitle: "Plans et tarifs", perMonth: "/ mois", perYear: "/ an",
    currentPlanLabel: "Plan actuel", upgradePlanLabel: "Changer de plan",
    mostPopular: "Le plus populaire", bestValue: "Meilleure valeur",
    planFeatures: "Ce qui est inclus",

    editProfileTitle: "Modifier le profil", saveChanges: "Enregistrer les modifications",
    nameLabel: "Nom", relationLabel: "Relation", profileUpdated: "Profil mis à jour",

    relationshipTitle: "Analyse de relation", loveTitle: "Amour & Réalité",
    marriageCompatTitle: "Compatibilité matrimoniale",
    synastrySub: "Connexion cosmique entre deux thèmes",

    myKundliTitle: "Mon Kundli", chartDetails: "Détails du thème",
    planetaryStrength: "Force planétaire", houseAnalysis: "Analyse des maisons",

    alertsTitle: "Alertes quotidiennes", enableAlerts: "Activer les alertes quotidiennes",
    alertTime: "Heure d'alerte", alertsEnabled: "Alertes activées",
    alertsDisabled: "Alertes désactivées",

    forecastTitle: "Prévisions", forecastSub: "Vos 6 prochains mois",
    upcomingEvents: "Événements à venir", nextSixMonths: "6 prochains mois",
  },

  // ── PORTUGUESE ─────────────────────────────────────────────────────────────
  pt: {
    calculating: "Calculando...", noData: "Sem dados disponíveis",
    selectProfile: "Selecionar perfil", birthDataNeeded: "Dados de nascimento necessários",
    goBack: "Voltar", viewReport: "Ver relatório", matchReport: "Relatório de compatibilidade",
    present: "Presente", notPresent: "Ausente",
    auspicious: "Auspicioso", inauspicious: "Inauspicioso",
    daily: "Diário", weekly: "Semanal", monthly: "Mensal", yearly: "Anual",
    selectSign: "Selecione seu signo",

    rashifalTitle: "Horóscopo", todaysRashifal: "Horóscopo de hoje",
    loveSection: "Amor", careerSection: "Carreira",
    healthSection: "Saúde", moneySection: "Dinheiro",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Dia",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Nascer do sol", sunsetLabel: "Pôr do sol",
    auspiciousTimes: "Momentos auspiciosos", rahukaal: "Rahu Kaal",
    moonSignLabel: "Signo lunar", paksha: "Paksha", festivals: "Festivais",

    kundliMilanTitle: "Compatibilidade Kundli", kundliMilanSub: "Análise Ashtakoot",
    groomLabel: "Noivo", brideLabel: "Noiva",
    checkCompatibility: "Verificar compatibilidade",
    gunaScore: "Pontuação Guna", outOf36: "de 36",
    manglikLabel: "Manglik", selfProfile: "Seu Kundli",
    partnerProfile: "Kundli do parceiro", addPartner: "Adicionar parceiro",
    birthDataMissing: "Dados de nascimento ausentes para um ou ambos",

    milanResult: "Resultado de compatibilidade", strengthsLabel: "Pontos fortes",
    challengesLabel: "Desafios", marriageOutlook: "Perspectiva matrimonial",
    cosmicInsight: "Visão cósmica", overallScore: "Pontuação geral",

    doshTitle: "Doshas", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Remédio",
    doshPresent: "Presente", doshAbsent: "Ausente",

    numerologyTitle: "Numerologia", lifePathLabel: "Número do caminho de vida",
    destinyNumber: "Número do destino", soulNumber: "Número da alma",
    personalityNumber: "Número de personalidade",
    luckyNumbers: "Números da sorte", luckyColors: "Cores da sorte",

    luckyTitle: "Elementos da sorte", luckyNumber: "Número da sorte",
    luckyColor: "Cor da sorte", luckyGem: "Gema da sorte",
    luckyDay: "Dia da sorte", luckyDirection: "Direção da sorte",
    luckyMetal: "Metal da sorte",

    muhuratTitle: "Muhurat", marriageMuhurat: "Muhurat de casamento",
    businessMuhurat: "Muhurat de negócios", travelMuhurat: "Muhurat de viagem",
    propertyMuhurat: "Entrada na casa", noMuhurat: "Sem Muhurat hoje",

    planetTitle: "Posições planetárias", retrograde: "Retrógrado",
    directMotion: "Direto", transitLabel: "Trânsito",
    planetDignity: "Dignidade planetária", exalted: "Exaltado", debilitated: "Debilitado",

    vastuTitle: "Vastu Shastra", northDir: "Norte", southDir: "Sul",
    eastDir: "Leste", westDir: "Oeste", northEast: "Nordeste",
    northWest: "Noroeste", southEast: "Sudeste", southWest: "Sudoeste",
    vastuTip: "Dica Vastu",

    remediesTitle: "Remédios", gemstones: "Pedras preciosas",
    mantrasLabel: "Mantras", donationLabel: "Doação",
    fastingLabel: "Jejum", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Assinatura", paymentTitle: "Pagamento Seguro",
    plansTitle: "Planos e preços", perMonth: "/ mês", perYear: "/ ano",
    currentPlanLabel: "Plano atual", upgradePlanLabel: "Atualizar plano",
    mostPopular: "Mais popular", bestValue: "Melhor custo-benefício",
    planFeatures: "O que está incluído",

    editProfileTitle: "Editar perfil", saveChanges: "Salvar alterações",
    nameLabel: "Nome", relationLabel: "Relação", profileUpdated: "Perfil atualizado",

    relationshipTitle: "Análise de relacionamento", loveTitle: "Amor & Realidade",
    marriageCompatTitle: "Compatibilidade matrimonial",
    synastrySub: "Conexão cósmica entre dois mapas",

    myKundliTitle: "Meu Kundli", chartDetails: "Detalhes do mapa",
    planetaryStrength: "Força planetária", houseAnalysis: "Análise das casas",

    alertsTitle: "Alertas diários", enableAlerts: "Ativar alertas diários",
    alertTime: "Hora do alerta", alertsEnabled: "Alertas ativados",
    alertsDisabled: "Alertas desativados",

    forecastTitle: "Previsão", forecastSub: "Seus próximos 6 meses",
    upcomingEvents: "Próximos eventos", nextSixMonths: "Próximos 6 meses",
  },

  // ── GERMAN ─────────────────────────────────────────────────────────────────
  de: {
    calculating: "Wird berechnet...", noData: "Keine Daten verfügbar",
    selectProfile: "Profil auswählen", birthDataNeeded: "Geburtsdaten erforderlich",
    goBack: "Zurück", viewReport: "Bericht anzeigen", matchReport: "Kompatibilitätsbericht",
    present: "Vorhanden", notPresent: "Nicht vorhanden",
    auspicious: "Günstig", inauspicious: "Ungünstig",
    daily: "Täglich", weekly: "Wöchentlich", monthly: "Monatlich", yearly: "Jährlich",
    selectSign: "Wähle dein Zeichen",

    rashifalTitle: "Horoskop", todaysRashifal: "Heutiges Horoskop",
    loveSection: "Liebe", careerSection: "Karriere",
    healthSection: "Gesundheit", moneySection: "Geld",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Wochentag",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Sonnenaufgang", sunsetLabel: "Sonnenuntergang",
    auspiciousTimes: "Günstige Zeiten", rahukaal: "Rahu Kaal",
    moonSignLabel: "Mondzeichen", paksha: "Paksha", festivals: "Feste",

    kundliMilanTitle: "Kundli Kompatibilität", kundliMilanSub: "Ashtakoot Analyse",
    groomLabel: "Bräutigam", brideLabel: "Braut",
    checkCompatibility: "Kompatibilität prüfen",
    gunaScore: "Guna Punkte", outOf36: "von 36",
    manglikLabel: "Manglik", selfProfile: "Dein Kundli",
    partnerProfile: "Partner Kundli", addPartner: "Partner hinzufügen",
    birthDataMissing: "Geburtsdaten für eine oder beide Personen fehlen",

    milanResult: "Kompatibilitätsergebnis", strengthsLabel: "Stärken",
    challengesLabel: "Herausforderungen", marriageOutlook: "Heiratsaussichten",
    cosmicInsight: "Kosmische Einsicht", overallScore: "Gesamtpunktzahl",

    doshTitle: "Doshas", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Heilmittel",
    doshPresent: "Vorhanden", doshAbsent: "Nicht vorhanden",

    numerologyTitle: "Numerologie", lifePathLabel: "Lebenspfadnummer",
    destinyNumber: "Schicksalszahl", soulNumber: "Seelenzahl",
    personalityNumber: "Persönlichkeitszahl",
    luckyNumbers: "Glückszahlen", luckyColors: "Glücksfarben",

    luckyTitle: "Glückselemente", luckyNumber: "Glückszahl",
    luckyColor: "Glücksfarbe", luckyGem: "Glücksstein",
    luckyDay: "Glückstag", luckyDirection: "Glücksrichtung",
    luckyMetal: "Glücksmetall",

    muhuratTitle: "Muhurat", marriageMuhurat: "Hochzeits-Muhurat",
    businessMuhurat: "Geschäfts-Muhurat", travelMuhurat: "Reise-Muhurat",
    propertyMuhurat: "Einzug ins Haus", noMuhurat: "Heute kein Muhurat",

    planetTitle: "Planetenpositionen", retrograde: "Rückläufig",
    directMotion: "Direktläufig", transitLabel: "Transit",
    planetDignity: "Planetenstärke", exalted: "Erhöht", debilitated: "Geschwächt",

    vastuTitle: "Vastu Shastra", northDir: "Norden", southDir: "Süden",
    eastDir: "Osten", westDir: "Westen", northEast: "Nordosten",
    northWest: "Nordwesten", southEast: "Südosten", southWest: "Südwesten",
    vastuTip: "Vastu-Tipp",

    remediesTitle: "Heilmittel", gemstones: "Edelsteine",
    mantrasLabel: "Mantras", donationLabel: "Spende",
    fastingLabel: "Fasten", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Abonnement", paymentTitle: "Sichere Zahlung",
    plansTitle: "Pläne & Preise", perMonth: "/ Monat", perYear: "/ Jahr",
    currentPlanLabel: "Aktueller Plan", upgradePlanLabel: "Plan upgraden",
    mostPopular: "Beliebteste", bestValue: "Bestes Preis-Leistungs-Verhältnis",
    planFeatures: "Was enthalten ist",

    editProfileTitle: "Profil bearbeiten", saveChanges: "Änderungen speichern",
    nameLabel: "Name", relationLabel: "Beziehung", profileUpdated: "Profil aktualisiert",

    relationshipTitle: "Beziehungsanalyse", loveTitle: "Liebe & Realität",
    marriageCompatTitle: "Eheliche Kompatibilität",
    synastrySub: "Kosmische Verbindung zwischen zwei Karten",

    myKundliTitle: "Mein Kundli", chartDetails: "Diagrammdetails",
    planetaryStrength: "Planetenstärke", houseAnalysis: "Hausanalyse",

    alertsTitle: "Tägliche Benachrichtigungen", enableAlerts: "Tägliche Benachrichtigungen aktivieren",
    alertTime: "Benachrichtigungszeit", alertsEnabled: "Benachrichtigungen aktiviert",
    alertsDisabled: "Benachrichtigungen deaktiviert",

    forecastTitle: "Vorhersage", forecastSub: "Deine nächsten 6 Monate",
    upcomingEvents: "Bevorstehende Ereignisse", nextSixMonths: "Nächste 6 Monate",
  },

  // ── RUSSIAN ────────────────────────────────────────────────────────────────
  ru: {
    calculating: "Вычисляется...", noData: "Нет данных",
    selectProfile: "Выберите профиль", birthDataNeeded: "Требуются данные о рождении",
    goBack: "Назад", viewReport: "Просмотр отчёта", matchReport: "Отчёт о совместимости",
    present: "Присутствует", notPresent: "Отсутствует",
    auspicious: "Благоприятный", inauspicious: "Неблагоприятный",
    daily: "Ежедневно", weekly: "Еженедельно", monthly: "Ежемесячно", yearly: "Ежегодно",
    selectSign: "Выберите свой знак",

    rashifalTitle: "Гороскоп", todaysRashifal: "Гороскоп на сегодня",
    loveSection: "Любовь", careerSection: "Карьера",
    healthSection: "Здоровье", moneySection: "Деньги",

    panchangTitle: "Панчанг", tithi: "Титхи", vara: "День недели",
    yogaPanchang: "Йога", karana: "Карана",
    sunriseLabel: "Восход солнца", sunsetLabel: "Закат солнца",
    auspiciousTimes: "Благоприятное время", rahukaal: "Раху Кал",
    moonSignLabel: "Знак Луны", paksha: "Пакша", festivals: "Праздники",

    kundliMilanTitle: "Совместимость Кундли", kundliMilanSub: "Анализ Аштакута",
    groomLabel: "Жених", brideLabel: "Невеста",
    checkCompatibility: "Проверить совместимость",
    gunaScore: "Очки Гуна", outOf36: "из 36",
    manglikLabel: "Мангалик", selfProfile: "Ваш Кундли",
    partnerProfile: "Кундли партнёра", addPartner: "Добавить партнёра",
    birthDataMissing: "Данные о рождении отсутствуют для одного или обоих",

    milanResult: "Результат совместимости", strengthsLabel: "Сильные стороны",
    challengesLabel: "Трудности", marriageOutlook: "Перспективы брака",
    cosmicInsight: "Космическое понимание", overallScore: "Общий балл",

    doshTitle: "Доши", manglikDosh: "Мангалик Дош",
    kaalSarpDosh: "Кал Сарп Дош", pitruDosh: "Питру Дош",
    sadhesatiLabel: "Садхесати", remedyLabel: "Средство",
    doshPresent: "Присутствует", doshAbsent: "Отсутствует",

    numerologyTitle: "Нумерология", lifePathLabel: "Число жизненного пути",
    destinyNumber: "Число судьбы", soulNumber: "Число души",
    personalityNumber: "Число личности",
    luckyNumbers: "Счастливые числа", luckyColors: "Счастливые цвета",

    luckyTitle: "Счастливые элементы", luckyNumber: "Счастливое число",
    luckyColor: "Счастливый цвет", luckyGem: "Счастливый камень",
    luckyDay: "Счастливый день", luckyDirection: "Счастливое направление",
    luckyMetal: "Счастливый металл",

    muhuratTitle: "Мухурат", marriageMuhurat: "Мухурат для свадьбы",
    businessMuhurat: "Мухурат для бизнеса", travelMuhurat: "Мухурат для путешествия",
    propertyMuhurat: "Въезд в дом", noMuhurat: "Сегодня нет Мухурат",

    planetTitle: "Позиции планет", retrograde: "Ретроградный",
    directMotion: "Прямой", transitLabel: "Транзит",
    planetDignity: "Сила планеты", exalted: "Возвышенный", debilitated: "Ослабленный",

    vastuTitle: "Васту Шастра", northDir: "Север", southDir: "Юг",
    eastDir: "Восток", westDir: "Запад", northEast: "Северо-восток",
    northWest: "Северо-запад", southEast: "Юго-восток", southWest: "Юго-запад",
    vastuTip: "Совет Васту",

    remediesTitle: "Средства", gemstones: "Драгоценные камни",
    mantrasLabel: "Мантры", donationLabel: "Пожертвование",
    fastingLabel: "Пост", yagyaLabel: "Яджна / Хаван",

    subscriptionTitle: "Подписка", paymentTitle: "Безопасная оплата",
    plansTitle: "Планы и цены", perMonth: "/ месяц", perYear: "/ год",
    currentPlanLabel: "Текущий план", upgradePlanLabel: "Обновить план",
    mostPopular: "Самый популярный", bestValue: "Лучшее соотношение",
    planFeatures: "Что включено",

    editProfileTitle: "Редактировать профиль", saveChanges: "Сохранить изменения",
    nameLabel: "Имя", relationLabel: "Отношения", profileUpdated: "Профиль обновлён",

    relationshipTitle: "Анализ отношений", loveTitle: "Любовь и реальность",
    marriageCompatTitle: "Совместимость в браке",
    synastrySub: "Космическая связь между двумя картами",

    myKundliTitle: "Мой Кундли", chartDetails: "Детали карты",
    planetaryStrength: "Сила планет", houseAnalysis: "Анализ домов",

    alertsTitle: "Ежедневные уведомления", enableAlerts: "Включить ежедневные уведомления",
    alertTime: "Время уведомления", alertsEnabled: "Уведомления включены",
    alertsDisabled: "Уведомления отключены",

    forecastTitle: "Прогноз", forecastSub: "Ваши следующие 6 месяцев",
    upcomingEvents: "Предстоящие события", nextSixMonths: "Следующие 6 месяцев",
  },

  // ── JAPANESE ───────────────────────────────────────────────────────────────
  ja: {
    calculating: "計算中...", noData: "データがありません",
    selectProfile: "プロフィールを選択", birthDataNeeded: "生年月日が必要です",
    goBack: "戻る", viewReport: "レポートを見る", matchReport: "相性レポート",
    present: "あり", notPresent: "なし",
    auspicious: "吉", inauspicious: "凶",
    daily: "毎日", weekly: "毎週", monthly: "毎月", yearly: "毎年",
    selectSign: "星座を選んでください",

    rashifalTitle: "星占い", todaysRashifal: "今日の運勢",
    loveSection: "恋愛", careerSection: "仕事",
    healthSection: "健康", moneySection: "金運",

    panchangTitle: "パンチャン", tithi: "ティティ", vara: "曜日",
    yogaPanchang: "ヨーガ", karana: "カラナ",
    sunriseLabel: "日の出", sunsetLabel: "日の入り",
    auspiciousTimes: "吉時", rahukaal: "ラーフカール",
    moonSignLabel: "月星座", paksha: "パクシャ", festivals: "祭り",

    kundliMilanTitle: "クンドリ相性", kundliMilanSub: "アシュタクート分析",
    groomLabel: "新郎", brideLabel: "新婦",
    checkCompatibility: "相性を確認",
    gunaScore: "グナスコア", outOf36: "/ 36点",
    manglikLabel: "マンガリク", selfProfile: "あなたのクンドリ",
    partnerProfile: "パートナーのクンドリ", addPartner: "パートナーを追加",
    birthDataMissing: "一方または両方の生年月日データがありません",

    milanResult: "相性結果", strengthsLabel: "強み",
    challengesLabel: "課題", marriageOutlook: "結婚の見通し",
    cosmicInsight: "宇宙の洞察", overallScore: "総合スコア",

    doshTitle: "ドーシャ", manglikDosh: "マンガリクドーシャ",
    kaalSarpDosh: "カルサルプドーシャ", pitruDosh: "ピトルドーシャ",
    sadhesatiLabel: "サデサティ", remedyLabel: "対策",
    doshPresent: "あり", doshAbsent: "なし",

    numerologyTitle: "数秘術", lifePathLabel: "ライフパスナンバー",
    destinyNumber: "運命数", soulNumber: "ソウルナンバー",
    personalityNumber: "パーソナリティナンバー",
    luckyNumbers: "ラッキーナンバー", luckyColors: "ラッキーカラー",

    luckyTitle: "ラッキー要素", luckyNumber: "ラッキーナンバー",
    luckyColor: "ラッキーカラー", luckyGem: "ラッキーストーン",
    luckyDay: "ラッキーデイ", luckyDirection: "ラッキー方角",
    luckyMetal: "ラッキーメタル",

    muhuratTitle: "ムフールタ", marriageMuhurat: "結婚の吉日",
    businessMuhurat: "開業の吉日", travelMuhurat: "旅行の吉日",
    propertyMuhurat: "引越しの吉日", noMuhurat: "本日の吉時なし",

    planetTitle: "惑星の位置", retrograde: "逆行",
    directMotion: "順行", transitLabel: "トランジット",
    planetDignity: "惑星の強さ", exalted: "高揚", debilitated: "減弱",

    vastuTitle: "ヴァストゥ・シャーストラ", northDir: "北", southDir: "南",
    eastDir: "東", westDir: "西", northEast: "北東",
    northWest: "北西", southEast: "南東", southWest: "南西",
    vastuTip: "ヴァストゥのヒント",

    remediesTitle: "対策", gemstones: "宝石",
    mantrasLabel: "マントラ", donationLabel: "布施",
    fastingLabel: "断食", yagyaLabel: "ヤジュナ / ハヴァン",

    subscriptionTitle: "サブスクリプション", paymentTitle: "安全な支払い",
    plansTitle: "プランと料金", perMonth: "/ 月", perYear: "/ 年",
    currentPlanLabel: "現在のプラン", upgradePlanLabel: "プランを変更",
    mostPopular: "最も人気", bestValue: "最高コスパ",
    planFeatures: "含まれる内容",

    editProfileTitle: "プロフィール編集", saveChanges: "変更を保存",
    nameLabel: "名前", relationLabel: "続柄", profileUpdated: "プロフィールを更新しました",

    relationshipTitle: "相性分析", loveTitle: "恋愛と現実",
    marriageCompatTitle: "婚姻相性",
    synastrySub: "2つのチャート間の宇宙的つながり",

    myKundliTitle: "マイクンドリ", chartDetails: "チャート詳細",
    planetaryStrength: "惑星の強さ", houseAnalysis: "ハウス分析",

    alertsTitle: "毎日の通知", enableAlerts: "毎日の通知を有効にする",
    alertTime: "通知時刻", alertsEnabled: "通知が有効",
    alertsDisabled: "通知が無効",

    forecastTitle: "予報", forecastSub: "今後6ヶ月の解読",
    upcomingEvents: "今後のイベント", nextSixMonths: "今後6ヶ月",
  },

  // ── INDONESIAN ─────────────────────────────────────────────────────────────
  id: {
    calculating: "Menghitung...", noData: "Tidak ada data",
    selectProfile: "Pilih profil", birthDataNeeded: "Data kelahiran diperlukan",
    goBack: "Kembali", viewReport: "Lihat laporan", matchReport: "Laporan kecocokan",
    present: "Ada", notPresent: "Tidak ada",
    auspicious: "Menguntungkan", inauspicious: "Tidak menguntungkan",
    daily: "Harian", weekly: "Mingguan", monthly: "Bulanan", yearly: "Tahunan",
    selectSign: "Pilih tanda zodiak",

    rashifalTitle: "Horoskop", todaysRashifal: "Horoskop hari ini",
    loveSection: "Cinta", careerSection: "Karier",
    healthSection: "Kesehatan", moneySection: "Uang",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Hari",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Matahari terbit", sunsetLabel: "Matahari terbenam",
    auspiciousTimes: "Waktu auspicious", rahukaal: "Rahu Kaal",
    moonSignLabel: "Tanda bulan", paksha: "Paksha", festivals: "Festival",

    kundliMilanTitle: "Kompatibilitas Kundli", kundliMilanSub: "Analisis Ashtakoot",
    groomLabel: "Pria", brideLabel: "Wanita",
    checkCompatibility: "Periksa kecocokan",
    gunaScore: "Nilai Guna", outOf36: "dari 36",
    manglikLabel: "Manglik", selfProfile: "Kundli Anda",
    partnerProfile: "Kundli pasangan", addPartner: "Tambah pasangan",
    birthDataMissing: "Data kelahiran satu atau keduanya tidak tersedia",

    milanResult: "Hasil kecocokan", strengthsLabel: "Kekuatan",
    challengesLabel: "Tantangan", marriageOutlook: "Prospek pernikahan",
    cosmicInsight: "Wawasan kosmik", overallScore: "Skor keseluruhan",

    doshTitle: "Dosha", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Solusi",
    doshPresent: "Ada", doshAbsent: "Tidak ada",

    numerologyTitle: "Numerologi", lifePathLabel: "Nomor jalan hidup",
    destinyNumber: "Nomor takdir", soulNumber: "Nomor jiwa",
    personalityNumber: "Nomor kepribadian",
    luckyNumbers: "Angka keberuntungan", luckyColors: "Warna keberuntungan",

    luckyTitle: "Elemen keberuntungan", luckyNumber: "Angka keberuntungan",
    luckyColor: "Warna keberuntungan", luckyGem: "Batu keberuntungan",
    luckyDay: "Hari keberuntungan", luckyDirection: "Arah keberuntungan",
    luckyMetal: "Logam keberuntungan",

    muhuratTitle: "Muhurat", marriageMuhurat: "Muhurat pernikahan",
    businessMuhurat: "Muhurat bisnis", travelMuhurat: "Muhurat perjalanan",
    propertyMuhurat: "Masuk rumah baru", noMuhurat: "Tidak ada Muhurat hari ini",

    planetTitle: "Posisi planet", retrograde: "Retrograd",
    directMotion: "Langsung", transitLabel: "Transit",
    planetDignity: "Kekuatan planet", exalted: "Dimuliakan", debilitated: "Dilemahkan",

    vastuTitle: "Vastu Shastra", northDir: "Utara", southDir: "Selatan",
    eastDir: "Timur", westDir: "Barat", northEast: "Timur Laut",
    northWest: "Barat Laut", southEast: "Tenggara", southWest: "Barat Daya",
    vastuTip: "Tips Vastu",

    remediesTitle: "Solusi", gemstones: "Batu permata",
    mantrasLabel: "Mantra", donationLabel: "Sumbangan",
    fastingLabel: "Puasa", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Langganan", paymentTitle: "Pembayaran Aman",
    plansTitle: "Paket & Harga", perMonth: "/ bulan", perYear: "/ tahun",
    currentPlanLabel: "Paket saat ini", upgradePlanLabel: "Upgrade paket",
    mostPopular: "Paling populer", bestValue: "Nilai terbaik",
    planFeatures: "Yang termasuk",

    editProfileTitle: "Edit profil", saveChanges: "Simpan perubahan",
    nameLabel: "Nama", relationLabel: "Hubungan", profileUpdated: "Profil diperbarui",

    relationshipTitle: "Analisis hubungan", loveTitle: "Cinta & Realita",
    marriageCompatTitle: "Kecocokan pernikahan",
    synastrySub: "Hubungan kosmik antara dua peta",

    myKundliTitle: "Kundli saya", chartDetails: "Detail grafik",
    planetaryStrength: "Kekuatan planet", houseAnalysis: "Analisis rumah",

    alertsTitle: "Peringatan harian", enableAlerts: "Aktifkan peringatan harian",
    alertTime: "Waktu peringatan", alertsEnabled: "Peringatan aktif",
    alertsDisabled: "Peringatan nonaktif",

    forecastTitle: "Ramalan", forecastSub: "6 bulan ke depan",
    upcomingEvents: "Acara mendatang", nextSixMonths: "6 bulan ke depan",
  },

  // ── KOREAN ─────────────────────────────────────────────────────────────────
  ko: {
    calculating: "계산 중...", noData: "데이터가 없습니다",
    selectProfile: "프로필 선택", birthDataNeeded: "생년월일 정보가 필요합니다",
    goBack: "뒤로", viewReport: "보고서 보기", matchReport: "궁합 보고서",
    present: "있음", notPresent: "없음",
    auspicious: "길", inauspicious: "흉",
    daily: "매일", weekly: "매주", monthly: "매월", yearly: "매년",
    selectSign: "별자리를 선택하세요",

    rashifalTitle: "별자리 운세", todaysRashifal: "오늘의 운세",
    loveSection: "연애", careerSection: "커리어",
    healthSection: "건강", moneySection: "금전",

    panchangTitle: "판창", tithi: "티티", vara: "요일",
    yogaPanchang: "요가", karana: "카라나",
    sunriseLabel: "일출", sunsetLabel: "일몰",
    auspiciousTimes: "길한 시간", rahukaal: "라후 칼",
    moonSignLabel: "달 별자리", paksha: "팍샤", festivals: "축제",

    kundliMilanTitle: "궁합 분석", kundliMilanSub: "아슈타쿠트 분석",
    groomLabel: "신랑", brideLabel: "신부",
    checkCompatibility: "궁합 확인",
    gunaScore: "구나 점수", outOf36: "/ 36점",
    manglikLabel: "망갈릭", selfProfile: "내 쿤들리",
    partnerProfile: "파트너 쿤들리", addPartner: "파트너 추가",
    birthDataMissing: "한 명 또는 두 명의 생년월일 데이터 누락",

    milanResult: "궁합 결과", strengthsLabel: "강점",
    challengesLabel: "어려움", marriageOutlook: "결혼 전망",
    cosmicInsight: "우주적 통찰", overallScore: "총 점수",

    doshTitle: "도샤", manglikDosh: "망갈릭 도샤",
    kaalSarpDosh: "칼 사르프 도샤", pitruDosh: "피트루 도샤",
    sadhesatiLabel: "사데사티", remedyLabel: "해결책",
    doshPresent: "있음", doshAbsent: "없음",

    numerologyTitle: "수비학", lifePathLabel: "생명수",
    destinyNumber: "운명수", soulNumber: "영혼수",
    personalityNumber: "개성수",
    luckyNumbers: "행운의 숫자", luckyColors: "행운의 색",

    luckyTitle: "행운의 요소", luckyNumber: "행운의 숫자",
    luckyColor: "행운의 색", luckyGem: "행운의 보석",
    luckyDay: "행운의 날", luckyDirection: "행운의 방향",
    luckyMetal: "행운의 금속",

    muhuratTitle: "무후르타", marriageMuhurat: "결혼 길일",
    businessMuhurat: "사업 길일", travelMuhurat: "여행 길일",
    propertyMuhurat: "입주 길일", noMuhurat: "오늘은 길일이 없습니다",

    planetTitle: "행성 위치", retrograde: "역행",
    directMotion: "순행", transitLabel: "트랜싯",
    planetDignity: "행성 세기", exalted: "고양", debilitated: "약화",

    vastuTitle: "바스투 샤스트라", northDir: "북", southDir: "남",
    eastDir: "동", westDir: "서", northEast: "북동",
    northWest: "북서", southEast: "남동", southWest: "남서",
    vastuTip: "바스투 팁",

    remediesTitle: "해결책", gemstones: "보석",
    mantrasLabel: "만트라", donationLabel: "기부",
    fastingLabel: "단식", yagyaLabel: "야즈나 / 하반",

    subscriptionTitle: "구독", paymentTitle: "안전한 결제",
    plansTitle: "요금제", perMonth: "/ 월", perYear: "/ 년",
    currentPlanLabel: "현재 요금제", upgradePlanLabel: "요금제 업그레이드",
    mostPopular: "가장 인기 있는", bestValue: "최고의 가성비",
    planFeatures: "포함된 항목",

    editProfileTitle: "프로필 편집", saveChanges: "변경 사항 저장",
    nameLabel: "이름", relationLabel: "관계", profileUpdated: "프로필이 업데이트되었습니다",

    relationshipTitle: "관계 분석", loveTitle: "사랑과 현실",
    marriageCompatTitle: "결혼 궁합",
    synastrySub: "두 차트 간의 우주적 연결",

    myKundliTitle: "내 쿤들리", chartDetails: "차트 상세",
    planetaryStrength: "행성 세기", houseAnalysis: "하우스 분석",

    alertsTitle: "일일 알림", enableAlerts: "일일 알림 활성화",
    alertTime: "알림 시간", alertsEnabled: "알림이 활성화됨",
    alertsDisabled: "알림이 비활성화됨",

    forecastTitle: "예보", forecastSub: "다음 6개월 분석",
    upcomingEvents: "다가오는 이벤트", nextSixMonths: "다음 6개월",
  },

  // ── TURKISH ────────────────────────────────────────────────────────────────
  tr: {
    calculating: "Hesaplanıyor...", noData: "Veri mevcut değil",
    selectProfile: "Profil seçin", birthDataNeeded: "Doğum bilgisi gerekli",
    goBack: "Geri dön", viewReport: "Raporu gör", matchReport: "Uyumluluk raporu",
    present: "Mevcut", notPresent: "Mevcut değil",
    auspicious: "Şanslı", inauspicious: "Şanssız",
    daily: "Günlük", weekly: "Haftalık", monthly: "Aylık", yearly: "Yıllık",
    selectSign: "Burcunuzu seçin",

    rashifalTitle: "Burç Yorumu", todaysRashifal: "Bugünün Burç Yorumu",
    loveSection: "Aşk", careerSection: "Kariyer",
    healthSection: "Sağlık", moneySection: "Para",

    panchangTitle: "Panchang", tithi: "Tithi", vara: "Gün",
    yogaPanchang: "Yoga", karana: "Karana",
    sunriseLabel: "Gün doğumu", sunsetLabel: "Gün batımı",
    auspiciousTimes: "Şanslı zamanlar", rahukaal: "Rahu Kaal",
    moonSignLabel: "Ay burcu", paksha: "Paksha", festivals: "Festivaller",

    kundliMilanTitle: "Kundli Uyumu", kundliMilanSub: "Ashtakoot Analizi",
    groomLabel: "Damat", brideLabel: "Gelin",
    checkCompatibility: "Uyumluluğu kontrol et",
    gunaScore: "Guna Puanı", outOf36: "/ 36 üzerinden",
    manglikLabel: "Manglik", selfProfile: "Kundliniz",
    partnerProfile: "Partnerin Kundlisi", addPartner: "Partner ekle",
    birthDataMissing: "Bir veya her ikisinin doğum bilgileri eksik",

    milanResult: "Uyumluluk Sonucu", strengthsLabel: "Güçlü Yönler",
    challengesLabel: "Zorluklar", marriageOutlook: "Evlilik Görünümü",
    cosmicInsight: "Kozmik Görüş", overallScore: "Toplam Puan",

    doshTitle: "Doshas", manglikDosh: "Manglik Dosh",
    kaalSarpDosh: "Kaal Sarp Dosh", pitruDosh: "Pitru Dosh",
    sadhesatiLabel: "Sadhesati", remedyLabel: "Çözüm",
    doshPresent: "Mevcut", doshAbsent: "Mevcut değil",

    numerologyTitle: "Numeroloji", lifePathLabel: "Yaşam yolu numarası",
    destinyNumber: "Kader numarası", soulNumber: "Ruh numarası",
    personalityNumber: "Kişilik numarası",
    luckyNumbers: "Şanslı sayılar", luckyColors: "Şanslı renkler",

    luckyTitle: "Şanslı Elementler", luckyNumber: "Şanslı Sayı",
    luckyColor: "Şanslı Renk", luckyGem: "Şanslı Taş",
    luckyDay: "Şanslı Gün", luckyDirection: "Şanslı Yön",
    luckyMetal: "Şanslı Metal",

    muhuratTitle: "Muhurat", marriageMuhurat: "Düğün Muhurat",
    businessMuhurat: "İş Muhurat", travelMuhurat: "Seyahat Muhurat",
    propertyMuhurat: "Ev'e Giriş", noMuhurat: "Bugün Muhurat yok",

    planetTitle: "Gezegen Konumları", retrograde: "Gerilemede",
    directMotion: "Doğrudan", transitLabel: "Geçiş",
    planetDignity: "Gezegen Gücü", exalted: "Yükseltilmiş", debilitated: "Zayıflamış",

    vastuTitle: "Vastu Shastra", northDir: "Kuzey", southDir: "Güney",
    eastDir: "Doğu", westDir: "Batı", northEast: "Kuzeydoğu",
    northWest: "Kuzeybatı", southEast: "Güneydoğu", southWest: "Güneybatı",
    vastuTip: "Vastu İpucu",

    remediesTitle: "Çözümler", gemstones: "Mücevherler",
    mantrasLabel: "Mantralar", donationLabel: "Bağış",
    fastingLabel: "Oruç", yagyaLabel: "Yagya / Havan",

    subscriptionTitle: "Abonelik", paymentTitle: "Güvenli Ödeme",
    plansTitle: "Planlar ve Fiyatlar", perMonth: "/ ay", perYear: "/ yıl",
    currentPlanLabel: "Mevcut Plan", upgradePlanLabel: "Planı Yükselt",
    mostPopular: "En Popüler", bestValue: "En İyi Değer",
    planFeatures: "Neler dahil",

    editProfileTitle: "Profili Düzenle", saveChanges: "Değişiklikleri Kaydet",
    nameLabel: "Ad", relationLabel: "İlişki", profileUpdated: "Profil güncellendi",

    relationshipTitle: "İlişki Analizi", loveTitle: "Aşk & Gerçeklik",
    marriageCompatTitle: "Evlilik Uyumu",
    synastrySub: "İki harita arasındaki kozmik bağlantı",

    myKundliTitle: "Benim Kundlim", chartDetails: "Grafik Detayları",
    planetaryStrength: "Gezegen Gücü", houseAnalysis: "Ev Analizi",

    alertsTitle: "Günlük Bildirimler", enableAlerts: "Günlük bildirimleri etkinleştir",
    alertTime: "Bildirim Saati", alertsEnabled: "Bildirimler etkin",
    alertsDisabled: "Bildirimler devre dışı",

    forecastTitle: "Tahmin", forecastSub: "Sonraki 6 ayınız",
    upcomingEvents: "Yaklaşan Etkinlikler", nextSixMonths: "Sonraki 6 Ay",
  },
};

export function getTE(lang: string): ExtTranslations {
  return TE[(lang as UILang)] ?? TE.en;
}
