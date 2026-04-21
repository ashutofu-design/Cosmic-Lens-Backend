// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Vastu UI strings (covers all 7 vastu screens)
//
// 24-language support model:
//   • en (English) + hn (Hinglish, Latin-Hindi) + hi (Devanagari Hindi) → explicit
//   • Other 21 languages → fall back to English (clean, no Hinglish leak)
//
// Used by:
//   • app/astrovastu.tsx              (chooser)
//   • app/astrovastu-pro-options.tsx  (Home / Business chooser)
//   • app/astrovastu-basic.tsx        (quick check form)
//   • app/astrovastu-pro.tsx          (PRO Smart Scan)
//   • app/astrovastu-pro-result.tsx   (PRO result)
//   • app/business-vastu.tsx          (Business form)
//   • app/vastu.tsx                   (compass + Vastu Drishti hub)
// ══════════════════════════════════════════════════════════════════════════════

import type { UILang } from "./i18n";

export interface VastuT {
  // ── Common ────────────────────────────────────────────────
  vt_appBranding:           string;   // "Powered by Vedic Engine"
  vt_back:                  string;
  vt_close:                 string;
  vt_cancel:                string;
  vt_retry:                 string;
  vt_next:                  string;
  vt_loading:               string;
  vt_required:              string;
  vt_optional:              string;
  vt_remove:                string;
  vt_save:                  string;
  vt_share:                 string;
  vt_open:                  string;

  // ── Page titles ──────────────────────────────────────────
  vt_titleAstroVastu:       string;
  vt_titleAstroVastuPro:    string;
  vt_titleAstroVastuProPremium: string;
  vt_titleHomeVastu:        string;
  vt_titleBusinessVastu:    string;
  vt_titleVastuCompass:     string;
  vt_titleVastuShastra:     string;
  vt_titleQuickCheck:       string;
  vt_titleSmartScan:        string;
  vt_titleDeepScan:         string;
  vt_titleVastuDrishti:     string;
  vt_titleYourReport:       string;
  vt_titleMyReports:        string;

  // ── Subtitles / taglines ─────────────────────────────────
  vt_subChooseJourney:      string;
  vt_subSacredCompass:      string;
  vt_subHomeOrBusiness:     string;
  vt_subBasicGuide:         string;
  vt_subKundliPersonalized: string;
  vt_subAdvancedAnalysis:   string;
  vt_subPremiumLine:        string;
  vt_subAskWhich:           string;

  // ── Tile / badge labels ──────────────────────────────────
  vt_tagFreeAlways:         string;
  vt_tagPremium:            string;
  vt_tagProPremium:         string;
  vt_tagForHome:            string;
  vt_tagForBusiness:        string;
  vt_tagComingSoon:         string;
  vt_tagNew:                string;

  // ── CTAs ─────────────────────────────────────────────────
  vt_ctaOpenFreeVastu:      string;
  vt_ctaOpenHomeVastu:      string;
  vt_ctaOpenBusinessVastu:  string;
  vt_ctaViewPremiumOptions: string;
  vt_ctaCheckKarein:        string;
  vt_ctaRunSmartScan:       string;
  vt_ctaRunDeepScan:        string;
  vt_ctaStartDeepScan:      string;
  vt_ctaInitiateDrishti:    string;
  vt_ctaScanning:           string;
  vt_ctaUploadFloorPlan:    string;
  vt_ctaTakePhoto:          string;
  vt_ctaFromGallery:        string;
  vt_ctaCamera:             string;
  vt_ctaGallery:            string;
  vt_ctaAddRoom:            string;
  vt_ctaNextReview:         string;
  vt_ctaOpenPdf:            string;
  vt_ctaOpenPdfReport:      string;
  vt_ctaShareWhatsApp:      string;
  vt_ctaCompleteProfile:    string;
  vt_ctaUpgrade:            string;
  vt_ctaUpgradeToPro:       string;
  vt_ctaTalkToExpert:       string;
  vt_ctaUnlockPro:          string;
  vt_ctaRecaptureScan:      string;
  vt_ctaRunNewScan:         string;
  vt_ctaProfileComplete:    string;

  // ── Section headers ──────────────────────────────────────
  vt_sectionRoomGuide:      string;
  vt_sectionRoomGuideSub:   string;
  vt_sectionPriorityActions:string;
  vt_sectionRoomByRoom:     string;
  vt_sectionFix3First:      string;
  vt_sectionClassicalRefs:  string;
  vt_sectionStakeholder:    string;
  vt_sectionOverallHouse:   string;
  vt_sectionOverallPremise: string;
  vt_sectionWhyVerdict:     string;
  vt_sectionRemedies:       string;
  vt_sectionShastraPramaan: string;
  vt_sectionPdfReady:       string;
  vt_sectionPickRoom:       string;
  vt_sectionPickDirection:  string;
  vt_sectionPickKamra:      string;     // "Kamra chunein" → "Pick a room"
  vt_sectionPickDisha:      string;
  vt_sectionFloorPlan:      string;
  vt_sectionFloorPlanOpt:   string;
  vt_sectionReviewSubmit:   string;
  vt_sectionReviewSubmitSub:string;
  vt_sectionRoomTypePicker: string;

  // ── Status badges ────────────────────────────────────────
  vt_badgeLiveCompass:      string;
  vt_badgeWallByWall:       string;
  vt_badgeSpatialEnergy:    string;
  vt_badgeDeepScan:         string;
  vt_badgeScanOk:           string;
  vt_badgeScanInconclusive: string;
  vt_badgeCosmicDrishti:    string;
  vt_badgeVastuCompliance:  string;
  vt_badgeImageInsufficient:string;
  vt_badgeIdealDir:         string;
  vt_badgeOutOf100:         string;
  vt_badgeGrade:            string;

  // ── Alerts (titles + messages) ───────────────────────────
  vt_alertPermissionTitle:  string;
  vt_alertPhotoPermNeed:    string;
  vt_alertCameraPermNeed:   string;
  vt_alertGalleryPermNeed:  string;
  vt_alertErrorTitle:       string;
  vt_alertNetworkErrorTitle:string;
  vt_alertNetworkErrorBody: string;
  vt_alertPhotoMissingTitle:string;
  vt_alertPhotoMissingBody: string;
  vt_alertPhotoFailed:      string;
  vt_alertCameraFailed:     string;
  vt_alertScanFailed:       string;
  vt_alertScanFailedBody:   string;
  vt_alertCalibrating:      string;
  vt_alertCalibratingBody:  string;
  vt_alertWrongDirection:   string;
  vt_alertWrongDirectionBody:(label: string, target: number, tol: number) => string;
  vt_alertPhotoUnreadable:  string;
  vt_alertFloorUploadFail:  string;
  vt_alertWallPhotoFirst:   string;
  vt_alertMin2Walls:        string;
  vt_alertLoginRequired:    string;
  vt_alertLoginRequiredBody:string;
  vt_alertDailyLimitFull:   string;
  vt_alertOpenPdfFail:      string;
  vt_alertCouldntShare:     string;
  vt_alertDailyLimitGeneric:string;
  vt_alertIssue:            string;

  // ── Result + verdict UI ──────────────────────────────────
  vt_verdictIdeal:          string;
  vt_verdictAcceptable:     string;
  vt_verdictAdjustment:     string;
  vt_verdictAvoid:          string;
  vt_severity:              string;
  vt_planLabel:             string;
  vt_quotaTodayPrefix:      string;     // "Aaj:"
  vt_quotaUnlimited:        string;
  vt_emptyReportTitle:      string;
  vt_emptyReportBody:       string;
  vt_emptyOpenScreen:       string;
  vt_pdfReadyDesc:          string;
  vt_noFloorPlan:           string;

  // ── Form labels ──────────────────────────────────────────
  vt_lblPropertyName:       string;
  vt_phPropertyName:        string;
  vt_lblDirection:          string;
  vt_lblCriticalRoomMark:   string;     // "(★ = critical)"

  // ── Pricing taglines (kept generic; numbers stay) ────────
  vt_priceSingleRoom:       string;     // "Single room (Quick Check) — ₹199"
  vt_priceThreeBundle:      string;
  vt_priceFullHome:         string;
  vt_priceBusinessShop:     string;
  vt_priceBusinessOffice:   string;
  vt_priceBusinessFactory:  string;
  vt_priceMahadashaConflict:string;
  vt_priceFamilyMatch:      string;
  vt_pricePdfShare:         string;
  vt_priceOwnerKundli:      string;
  vt_priceMuhurat:          string;

  // ── Discount note ───────────────────────────────────────
  vt_discountProSubs:       string;
  vt_discountAmount:        string;
  vt_discountSuffix:        string;     // "on all AstroVastu purchases above."

  // ── Reports tile ────────────────────────────────────────
  vt_reportsSub:            string;

  // ── AstroVastu chooser bullets ──────────────────────────
  vt_bulFreeMagnetometer:   string;
  vt_bulFreeRoomGuide:      string;
  vt_bulFreeDosDonts:       string;
  vt_bulFree8Directions:    string;

  // ── Compass screen ──────────────────────────────────────
  vt_compassHeading:        string;
  vt_compassSubhead:        string;

  // ── Vastu intro card ────────────────────────────────────
  vt_introWhatIsVastu:      string;
  vt_introKundliPersonalized:string;
  vt_introQuickCheckTitle:  string;
  vt_introQuickCheckBody:   string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Default English (used as base + as fallback for the 21 non-explicit langs)
// ─────────────────────────────────────────────────────────────────────────────
const en: VastuT = {
  vt_appBranding:           "Powered by Vedic Engine",
  vt_back:                  "Back",
  vt_close:                 "Close",
  vt_cancel:                "Cancel",
  vt_retry:                 "Try again",
  vt_next:                  "Next",
  vt_loading:               "Loading…",
  vt_required:              "Required",
  vt_optional:              "Optional",
  vt_remove:                "Remove",
  vt_save:                  "Save",
  vt_share:                 "Share",
  vt_open:                  "Open",

  vt_titleAstroVastu:       "AstroVastu",
  vt_titleAstroVastuPro:    "AstroVastu PRO",
  vt_titleAstroVastuProPremium: "AstroVastu Pro Premium",
  vt_titleHomeVastu:        "Home Vastu Advanced",
  vt_titleBusinessVastu:    "Business Vastu",
  vt_titleVastuCompass:     "Vastu Compass",
  vt_titleVastuShastra:     "What is Vastu Shastra?",
  vt_titleQuickCheck:       "Personalized Quick Check",
  vt_titleSmartScan:        "Smart Scan",
  vt_titleDeepScan:         "Cosmic Vastu Deep Scan",
  vt_titleVastuDrishti:     "Vastu Drishti Scanner",
  vt_titleYourReport:       "Your AstroVastu Report",
  vt_titleMyReports:        "My Reports",

  vt_subChooseJourney:      "Choose your Vastu journey",
  vt_subSacredCompass:      "Sacred Direction Finder",
  vt_subHomeOrBusiness:     "Home or Business — what to scan?",
  vt_subBasicGuide:         "Compass + basic Vastu guide",
  vt_subKundliPersonalized: "Kundli-personalized Vastu — Home & Business",
  vt_subAdvancedAnalysis:   "Everything in Basic + advanced personal analysis",
  vt_subPremiumLine:        "Sacred Compass · Room-wise Guidance",
  vt_subAskWhich:           "Which Vastu would you like?",

  vt_tagFreeAlways:         "FREE · ALWAYS",
  vt_tagPremium:            "PREMIUM",
  vt_tagProPremium:         "PRO PREMIUM",
  vt_tagForHome:            "FOR HOME / RESIDENCE",
  vt_tagForBusiness:        "FOR BUSINESS / COMMERCIAL",
  vt_tagComingSoon:         "Coming Soon",
  vt_tagNew:                "NEW",

  vt_ctaOpenFreeVastu:      "Open Free Vastu",
  vt_ctaOpenHomeVastu:      "Open Home Vastu",
  vt_ctaOpenBusinessVastu:  "Open Business Vastu",
  vt_ctaViewPremiumOptions: "View Premium Options",
  vt_ctaCheckKarein:        "Check now ✨",
  vt_ctaRunSmartScan:       "Run Smart Scan",
  vt_ctaRunDeepScan:        "Run Cosmic Deep Scan",
  vt_ctaStartDeepScan:      "Start Deep Scan",
  vt_ctaInitiateDrishti:    "Initiate Vastu Drishti Scan",
  vt_ctaScanning:           "Scanning spatial energy field…",
  vt_ctaUploadFloorPlan:    "Upload floor plan",
  vt_ctaTakePhoto:          "Take photo now",
  vt_ctaFromGallery:        "From gallery",
  vt_ctaCamera:             "Camera",
  vt_ctaGallery:            "Gallery",
  vt_ctaAddRoom:            "Add Room (★ = critical)",
  vt_ctaNextReview:         "Next: Review & Scan",
  vt_ctaOpenPdf:            "Open PDF",
  vt_ctaOpenPdfReport:      "Open PDF Report",
  vt_ctaShareWhatsApp:      "WhatsApp",
  vt_ctaCompleteProfile:    "Complete Profile",
  vt_ctaUpgrade:            "Upgrade — Basic ₹199 / Pro ₹499",
  vt_ctaUpgradeToPro:       "Upgrade to Pro — ₹499/mo",
  vt_ctaTalkToExpert:       "Talk to Vastu Expert on WhatsApp",
  vt_ctaUnlockPro:          "Unlock PRO",
  vt_ctaRecaptureScan:      "Recapture and scan again",
  vt_ctaRunNewScan:         "Run new scan",
  vt_ctaProfileComplete:    "Complete your profile",

  vt_sectionRoomGuide:      "ROOM-WISE VASTU GUIDE",
  vt_sectionRoomGuideSub:   "Tap any card to see do's, don'ts, and remedies",
  vt_sectionPriorityActions:"Priority Actions",
  vt_sectionRoomByRoom:     "Room-by-room",
  vt_sectionFix3First:      "FIX THESE 3 THINGS FIRST",
  vt_sectionClassicalRefs:  "CLASSICAL REFERENCES",
  vt_sectionStakeholder:    "Stakeholder Synergy",
  vt_sectionOverallHouse:   "OVERALL HOUSE SCORE",
  vt_sectionOverallPremise: "OVERALL PREMISE SCORE",
  vt_sectionWhyVerdict:     "Why this verdict?",
  vt_sectionRemedies:       "Remedies",
  vt_sectionShastraPramaan: "Shastra evidence",
  vt_sectionPdfReady:       "Detailed PDF Report Ready",
  vt_sectionPickRoom:       "Pick a room",
  vt_sectionPickDirection:  "Pick a direction",
  vt_sectionPickKamra:      "1.  Pick a room",
  vt_sectionPickDisha:      "2.  Pick a direction",
  vt_sectionFloorPlan:      "Floor Plan",
  vt_sectionFloorPlanOpt:   "Floor Plan (Optional)",
  vt_sectionReviewSubmit:   "Review & Submit",
  vt_sectionReviewSubmitSub:"Confirm your captures, then run Deep Scan.",
  vt_sectionRoomTypePicker: "Pick room type",

  vt_badgeLiveCompass:      "LIVE COMPASS",
  vt_badgeWallByWall:       "WALL-BY-WALL ANALYSIS",
  vt_badgeSpatialEnergy:    "SPATIAL ENERGY MAP",
  vt_badgeDeepScan:         "DEEP SCAN",
  vt_badgeScanOk:           "SCAN OK",
  vt_badgeScanInconclusive: "SCAN INCONCLUSIVE",
  vt_badgeCosmicDrishti:    "COSMIC VASTU DRISHTI",
  vt_badgeVastuCompliance:  "VASTU COMPLIANCE",
  vt_badgeImageInsufficient:"Image clarity insufficient",
  vt_badgeIdealDir:         "✨  Ideal Direction:",
  vt_badgeOutOf100:         "OUT OF 100",
  vt_badgeGrade:            "Grade",

  vt_alertPermissionTitle:  "Permission needed",
  vt_alertPhotoPermNeed:    "Please give photo gallery access so Vastu Drishti can read your room.",
  vt_alertCameraPermNeed:   "Please give camera access so we can take an instant photo.",
  vt_alertGalleryPermNeed:  "Please give gallery access to pick a saved photo.",
  vt_alertErrorTitle:       "Error",
  vt_alertNetworkErrorTitle:"Network error",
  vt_alertNetworkErrorBody: "Please check your internet connection.",
  vt_alertPhotoMissingTitle:"Photo missing",
  vt_alertPhotoMissingBody: "Please take or pick a room photo first.",
  vt_alertPhotoFailed:      "Could not capture the photo.",
  vt_alertCameraFailed:     "Could not open the camera.",
  vt_alertScanFailed:       "Scan failed",
  vt_alertScanFailedBody:   "Could not analyse the photo. Please try again in good light.",
  vt_alertCalibrating:      "Compass calibrating",
  vt_alertCalibratingBody:  "Move the phone in a figure-8 in the air, the compass will be ready.",
  vt_alertWrongDirection:   "Face the right direction",
  vt_alertWrongDirectionBody:(label, target, tol) =>
                            `Face ${label} (${target}°). Tolerance ±${tol}°.`,
  vt_alertPhotoUnreadable:  "Could not read the photo.",
  vt_alertFloorUploadFail:  "Floor plan upload failed.",
  vt_alertWallPhotoFirst:   "Please take a photo of this wall first.",
  vt_alertMin2Walls:        "Capture at least 2 walls.",
  vt_alertLoginRequired:    "Login required",
  vt_alertLoginRequiredBody:"Login is required for Deep Scan — this is an advanced multi-photo analysis.",
  vt_alertDailyLimitFull:   "Daily limit reached",
  vt_alertOpenPdfFail:      "Could not open the PDF.",
  vt_alertCouldntShare:     "Couldn't share",
  vt_alertDailyLimitGeneric:"Daily limit reached",
  vt_alertIssue:            "Issue",

  vt_verdictIdeal:          "Ideal",
  vt_verdictAcceptable:     "Acceptable",
  vt_verdictAdjustment:     "Adjustment Needed",
  vt_verdictAvoid:          "Avoid",
  vt_severity:              "Severity:",
  vt_planLabel:             "Plan:",
  vt_quotaTodayPrefix:      "Today:",
  vt_quotaUnlimited:        "Unlimited",
  vt_emptyReportTitle:      "No report loaded",
  vt_emptyReportBody:       "Please run a Smart Scan first to view the result here.",
  vt_emptyOpenScreen:       "Open AstroVastu PRO",
  vt_pdfReadyDesc:          "Your full detailed PDF report is ready to view and share.",
  vt_noFloorPlan:           "No floor plan added",

  vt_lblPropertyName:       "Property name",
  vt_phPropertyName:        "e.g. Andheri Shop, Powai HQ",
  vt_lblDirection:          "Direction:",
  vt_lblCriticalRoomMark:   "(★ = critical)",

  vt_priceSingleRoom:       "Single room (Quick Check) — ₹199",
  vt_priceThreeBundle:      "3-room bundle (Spot Check) — ₹499",
  vt_priceFullHome:         "Full Home Advanced — ₹2,999 lifetime per property",
  vt_priceBusinessShop:     "🏪 Shop Vastu — ₹999 (cash counter, entrance, owner seat)",
  vt_priceBusinessOffice:   "🏢 Office Vastu — ₹1,499 (CEO cabin, conference, locker)",
  vt_priceBusinessFactory:  "🏭 Factory Vastu — ₹2,999 (machinery, raw material, boiler)",
  vt_priceMahadashaConflict:"Mahadasha + Antardasha conflict alerts",
  vt_priceFamilyMatch:      "Family kundlis (up to 5) cross-match",
  vt_pricePdfShare:         "PDF download + history + WhatsApp share",
  vt_priceOwnerKundli:      "Owner kundli + up to 3 partners analysis",
  vt_priceMuhurat:          "Business start muhurat chart consideration",

  vt_discountProSubs:       "General Pro subscribers",
  vt_discountAmount:        "20% off",
  vt_discountSuffix:        "on all AstroVastu purchases above.",

  vt_reportsSub:            "View & share all your past PDF scans",

  vt_bulFreeMagnetometer:   "Real magnetometer compass — find your direction",
  vt_bulFreeRoomGuide:      "Room-wise guide: where the kitchen, bedroom, pooja should be",
  vt_bulFreeDosDonts:       "General do's & don'ts per direction",
  vt_bulFree8Directions:    "Deity, element & meaning of all 8 directions",

  vt_compassHeading:        "Vastu Compass",
  vt_compassSubhead:        "Sacred Direction Finder",

  vt_introWhatIsVastu:      "What is Vastu Shastra?",
  vt_introKundliPersonalized: "🪐  Kundli + Vastu = Personalized",
  vt_introQuickCheckTitle:  "Personalized Quick Check",
  vt_introQuickCheckBody:   "Based on your Lagna, Mahadasha, and special yogas — a deterministic verdict for room placement, with classical sources.",
};

// ─────────────────────────────────────────────────────────────────────────────
// Hinglish (hn) — original Hinglish copy preserved
// ─────────────────────────────────────────────────────────────────────────────
const hn: VastuT = {
  ...en,
  vt_subChooseJourney:      "Apni Vastu journey chuniye",
  vt_subSacredCompass:      "Sacred Direction Finder",
  vt_subHomeOrBusiness:     "Home ya Business — kya scan karna hai?",
  vt_subBasicGuide:         "Compass + basic Vastu guide",
  vt_subKundliPersonalized: "Kundli-personalized Vastu — Home & Business",
  vt_subAdvancedAnalysis:   "Basic ke saath sab kuch + advanced personal analysis",
  vt_subPremiumLine:        "Sacred Compass · Room-wise Guidance",
  vt_subAskWhich:           "Aap kaunsa Vastu chahte hain?",

  vt_ctaCheckKarein:        "Check Karein  ✨",
  vt_ctaScanning:           "Scanning spatial energy field…",
  vt_ctaTakePhoto:          "Turant photo lein",
  vt_ctaFromGallery:        "Saved photo chuniye",
  vt_ctaProfileComplete:    "Profile Complete Karein",
  vt_ctaTalkToExpert:       "Vastu Expert se WhatsApp par baat karein",
  vt_ctaRunDeepScan:        "Cosmic Deep Scan chalayein",
  vt_ctaStartDeepScan:      "Deep Scan shuru karein",

  vt_sectionFix3First:      "SABSE PEHLE YE 3 CHEEZEIN THEEK KARO",
  vt_sectionPickKamra:      "1.  Kamra chunein",
  vt_sectionPickDisha:      "2.  Disha chunein",
  vt_sectionRoomTypePicker: "Room type chuniye",
  vt_sectionReviewSubmitSub:"Apne captures confirm karein, fir Deep Scan chalayein.",
  vt_sectionWhyVerdict:     "Yeh verdict kyun?",
  vt_sectionRemedies:       "Upaay",
  vt_sectionShastraPramaan: "Shastra Pramaan",

  vt_alertPhotoPermNeed:    "Photo gallery access dijiye taaki Vastu Drishti aapka room dekh sake.",
  vt_alertCameraPermNeed:   "Camera access dijiye taaki turant photo le sakein.",
  vt_alertGalleryPermNeed:  "Gallery access dijiye taaki saved photo chun sakein.",
  vt_alertNetworkErrorBody: "Internet connection check kijiye.",
  vt_alertPhotoMissingTitle:"Photo missing",
  vt_alertPhotoMissingBody: "Pehle ek room ka photo lijiye ya gallery se chuniye.",
  vt_alertPhotoFailed:      "Photo nahi le payi.",
  vt_alertCameraFailed:     "Camera khol nahi payi.",
  vt_alertScanFailedBody:   "Photo analyze nahi ho payi. Acchi roshni mein dobara try karein.",
  vt_alertCalibrating:      "Compass calibrating",
  vt_alertCalibratingBody:  "Phone ko hawa mein ek '∞' shape mein ghoomayein, fir compass ready ho jayega.",
  vt_alertWrongDirection:   "Phone ko sahi direction mein karein",
  vt_alertWrongDirectionBody:(label, target, tol) =>
                            `${label} (${target}°) ki taraf face karein. Tolerance ±${tol}° hai.`,
  vt_alertPhotoUnreadable:  "Photo nahi padh sake",
  vt_alertFloorUploadFail:  "Floor plan upload nahi ho paya.",
  vt_alertWallPhotoFirst:   "Pehle is wall ki photo lijiye",
  vt_alertMin2Walls:        "Kam se kam 2 walls capture karein",
  vt_alertLoginRequired:    "Login required",
  vt_alertLoginRequiredBody:"Deep Scan ke liye login zaroori hai — yeh advanced multi-photo analysis hai.",
  vt_alertDailyLimitFull:   "Daily limit poora",
  vt_alertDailyLimitGeneric:"Daily limit poora",

  vt_quotaTodayPrefix:      "Aaj:",
  vt_emptyReportBody:       "Pehle ek Smart Scan chalayein taaki result yahan dikh sake.",

  vt_introKundliPersonalized: "🪐  Kundli + Vastu = Personalized",
  vt_introQuickCheckBody:   "Aapki Lagna, Mahadasha, aur special yogas ke aadhaar par room placement ka deterministic verdict — classical sources ke saath.",

  vt_priceMahadashaConflict:"Mahadasha + Antardasha conflict alerts",
  vt_priceFamilyMatch:      "Family kundlis (up to 5) cross-match",
  vt_pricePdfShare:         "PDF download + history + WhatsApp share",
  vt_priceOwnerKundli:      "Owner kundli + up to 3 partners ka analysis",
  vt_priceMuhurat:          "Business start muhurat chart consideration",

  vt_discountProSubs:       "General Pro subscribers",
  vt_discountAmount:        "20% off",
  vt_discountSuffix:        "sab AstroVastu purchases par milega.",

  vt_reportsSub:            "Apne saare past PDF scans dekhein & share karein",

  vt_bulFreeMagnetometer:   "Real magnetometer compass — direction find karein",
  vt_bulFreeRoomGuide:      "Room-wise guide: kitchen, bedroom, pooja kahan hona chahiye",
  vt_bulFreeDosDonts:       "Per direction general do's & don'ts",
  vt_bulFree8Directions:    "8 directions ka deity, element & meaning",
};

// ─────────────────────────────────────────────────────────────────────────────
// Hindi (Devanagari)
// ─────────────────────────────────────────────────────────────────────────────
const hi: VastuT = {
  ...en,
  vt_appBranding:           "Powered by Vedic Engine",
  vt_back:                  "वापस",
  vt_close:                 "बंद करें",
  vt_cancel:                "रद्द करें",
  vt_retry:                 "फिर से कोशिश करें",
  vt_next:                  "आगे",
  vt_loading:               "लोड हो रहा है…",
  vt_required:              "आवश्यक",
  vt_optional:              "वैकल्पिक",
  vt_remove:                "हटाएँ",
  vt_save:                  "सेव करें",
  vt_share:                 "शेयर करें",
  vt_open:                  "खोलें",

  vt_titleAstroVastu:       "एस्ट्रोवास्तु",
  vt_titleAstroVastuPro:    "एस्ट्रोवास्तु प्रो",
  vt_titleAstroVastuProPremium: "एस्ट्रोवास्तु प्रो प्रीमियम",
  vt_titleHomeVastu:        "होम वास्तु एडवांस्ड",
  vt_titleBusinessVastu:    "बिज़नेस वास्तु",
  vt_titleVastuCompass:     "वास्तु कम्पास",
  vt_titleVastuShastra:     "वास्तु शास्त्र क्या है?",
  vt_titleQuickCheck:       "व्यक्तिगत क्विक चेक",
  vt_titleSmartScan:        "स्मार्ट स्कैन",
  vt_titleDeepScan:         "कॉस्मिक वास्तु डीप स्कैन",
  vt_titleVastuDrishti:     "वास्तु दृष्टि स्कैनर",
  vt_titleYourReport:       "आपकी एस्ट्रोवास्तु रिपोर्ट",
  vt_titleMyReports:        "मेरी रिपोर्ट्स",

  vt_subChooseJourney:      "अपनी वास्तु यात्रा चुनें",
  vt_subSacredCompass:      "पवित्र दिशा खोजक",
  vt_subHomeOrBusiness:     "होम या बिज़नेस — क्या स्कैन करना है?",
  vt_subBasicGuide:         "कम्पास + बेसिक वास्तु गाइड",
  vt_subKundliPersonalized: "कुंडली-आधारित वास्तु — होम और बिज़नेस",
  vt_subAdvancedAnalysis:   "बेसिक के साथ-साथ एडवांस्ड व्यक्तिगत विश्लेषण",
  vt_subPremiumLine:        "पवित्र कम्पास · रूम-वार मार्गदर्शन",
  vt_subAskWhich:           "आप कौन-सा वास्तु चाहते हैं?",

  vt_tagFreeAlways:         "मुफ़्त · हमेशा",
  vt_tagPremium:            "प्रीमियम",
  vt_tagProPremium:         "प्रो प्रीमियम",
  vt_tagForHome:            "घर / निवास के लिए",
  vt_tagForBusiness:        "व्यवसाय / कमर्शियल के लिए",
  vt_tagComingSoon:         "जल्द आ रहा है",
  vt_tagNew:                "नया",

  vt_ctaOpenFreeVastu:      "मुफ़्त वास्तु खोलें",
  vt_ctaOpenHomeVastu:      "होम वास्तु खोलें",
  vt_ctaOpenBusinessVastu:  "बिज़नेस वास्तु खोलें",
  vt_ctaViewPremiumOptions: "प्रीमियम विकल्प देखें",
  vt_ctaCheckKarein:        "अभी जाँचें ✨",
  vt_ctaRunSmartScan:       "स्मार्ट स्कैन चलाएँ",
  vt_ctaRunDeepScan:        "कॉस्मिक डीप स्कैन चलाएँ",
  vt_ctaStartDeepScan:      "डीप स्कैन शुरू करें",
  vt_ctaInitiateDrishti:    "वास्तु दृष्टि स्कैन प्रारंभ करें",
  vt_ctaScanning:           "स्थानिक ऊर्जा क्षेत्र स्कैन हो रहा है…",
  vt_ctaUploadFloorPlan:    "फ्लोर प्लान अपलोड करें",
  vt_ctaTakePhoto:          "तुरंत फोटो लें",
  vt_ctaFromGallery:        "गैलरी से चुनें",
  vt_ctaCamera:             "कैमरा",
  vt_ctaGallery:            "गैलरी",
  vt_ctaAddRoom:            "कमरा जोड़ें (★ = महत्वपूर्ण)",
  vt_ctaNextReview:         "आगे: समीक्षा & स्कैन",
  vt_ctaOpenPdf:            "PDF खोलें",
  vt_ctaOpenPdfReport:      "PDF रिपोर्ट खोलें",
  vt_ctaShareWhatsApp:      "व्हाट्सएप",
  vt_ctaCompleteProfile:    "प्रोफ़ाइल पूरी करें",
  vt_ctaUpgrade:            "अपग्रेड — बेसिक ₹199 / प्रो ₹499",
  vt_ctaUpgradeToPro:       "प्रो में अपग्रेड करें — ₹499/माह",
  vt_ctaTalkToExpert:       "वास्तु विशेषज्ञ से व्हाट्सएप पर बात करें",
  vt_ctaUnlockPro:          "प्रो अनलॉक करें",
  vt_ctaRecaptureScan:      "फिर से कैप्चर करके स्कैन करें",
  vt_ctaRunNewScan:         "नया स्कैन चलाएँ",
  vt_ctaProfileComplete:    "अपनी प्रोफ़ाइल पूरी करें",

  vt_sectionRoomGuide:      "रूम-वार वास्तु गाइड",
  vt_sectionRoomGuideSub:   "किसी कार्ड पर टैप करके दिशा-निर्देश और उपाय देखें",
  vt_sectionPriorityActions:"प्राथमिक कार्य",
  vt_sectionRoomByRoom:     "रूम-बाय-रूम",
  vt_sectionFix3First:      "सबसे पहले ये 3 चीज़ें ठीक करें",
  vt_sectionClassicalRefs:  "शास्त्रीय संदर्भ",
  vt_sectionStakeholder:    "साझेदार समन्वय",
  vt_sectionOverallHouse:   "कुल घर का स्कोर",
  vt_sectionOverallPremise: "कुल परिसर का स्कोर",
  vt_sectionWhyVerdict:     "यह निर्णय क्यों?",
  vt_sectionRemedies:       "उपाय",
  vt_sectionShastraPramaan: "शास्त्र प्रमाण",
  vt_sectionPdfReady:       "विस्तृत PDF रिपोर्ट तैयार",
  vt_sectionPickRoom:       "कमरा चुनें",
  vt_sectionPickDirection:  "दिशा चुनें",
  vt_sectionPickKamra:      "1.  कमरा चुनें",
  vt_sectionPickDisha:      "2.  दिशा चुनें",
  vt_sectionFloorPlan:      "फ्लोर प्लान",
  vt_sectionFloorPlanOpt:   "फ्लोर प्लान (वैकल्पिक)",
  vt_sectionReviewSubmit:   "समीक्षा & सबमिट",
  vt_sectionReviewSubmitSub:"अपने कैप्चर की पुष्टि करें, फिर डीप स्कैन चलाएँ।",
  vt_sectionRoomTypePicker: "रूम टाइप चुनें",

  vt_badgeLiveCompass:      "लाइव कम्पास",
  vt_badgeWallByWall:       "दीवार-दर-दीवार विश्लेषण",
  vt_badgeSpatialEnergy:    "स्थानिक ऊर्जा मानचित्र",
  vt_badgeDeepScan:         "डीप स्कैन",
  vt_badgeScanOk:           "स्कैन सफल",
  vt_badgeScanInconclusive: "स्कैन अनिर्णायक",
  vt_badgeCosmicDrishti:    "कॉस्मिक वास्तु दृष्टि",
  vt_badgeVastuCompliance:  "वास्तु अनुपालन",
  vt_badgeImageInsufficient:"छवि स्पष्टता अपर्याप्त",
  vt_badgeIdealDir:         "✨  आदर्श दिशा:",
  vt_badgeOutOf100:         "100 में से",
  vt_badgeGrade:            "ग्रेड",

  vt_alertPermissionTitle:  "अनुमति आवश्यक",
  vt_alertPhotoPermNeed:    "कृपया फोटो गैलरी एक्सेस दें ताकि वास्तु दृष्टि आपका कमरा देख सके।",
  vt_alertCameraPermNeed:   "कृपया कैमरा एक्सेस दें ताकि तुरंत फोटो ले सकें।",
  vt_alertGalleryPermNeed:  "कृपया गैलरी एक्सेस दें ताकि सेव की हुई फोटो चुन सकें।",
  vt_alertErrorTitle:       "त्रुटि",
  vt_alertNetworkErrorTitle:"नेटवर्क त्रुटि",
  vt_alertNetworkErrorBody: "कृपया अपना इंटरनेट कनेक्शन जाँचें।",
  vt_alertPhotoMissingTitle:"फोटो उपलब्ध नहीं",
  vt_alertPhotoMissingBody: "पहले एक कमरे की फोटो लें या गैलरी से चुनें।",
  vt_alertPhotoFailed:      "फोटो नहीं ले सके।",
  vt_alertCameraFailed:     "कैमरा नहीं खुल सका।",
  vt_alertScanFailed:       "स्कैन असफल",
  vt_alertScanFailedBody:   "फोटो का विश्लेषण नहीं हो पाया। अच्छी रोशनी में फिर कोशिश करें।",
  vt_alertCalibrating:      "कम्पास कैलिब्रेट हो रहा है",
  vt_alertCalibratingBody:  "फोन को हवा में '∞' आकार में घुमाएँ, कम्पास तैयार हो जाएगा।",
  vt_alertWrongDirection:   "फोन को सही दिशा में करें",
  vt_alertWrongDirectionBody:(label, target, tol) =>
                            `${label} (${target}°) की ओर मुख करें। सहनशीलता ±${tol}°।`,
  vt_alertPhotoUnreadable:  "फोटो पढ़ नहीं सके",
  vt_alertFloorUploadFail:  "फ्लोर प्लान अपलोड नहीं हो सका।",
  vt_alertWallPhotoFirst:   "पहले इस दीवार की फोटो लें",
  vt_alertMin2Walls:        "कम से कम 2 दीवारें कैप्चर करें",
  vt_alertLoginRequired:    "लॉगिन आवश्यक",
  vt_alertLoginRequiredBody:"डीप स्कैन के लिए लॉगिन आवश्यक है — यह एडवांस्ड मल्टी-फोटो विश्लेषण है।",
  vt_alertDailyLimitFull:   "दैनिक सीमा पूरी",
  vt_alertOpenPdfFail:      "PDF नहीं खोल सके।",
  vt_alertCouldntShare:     "शेयर नहीं हो सका",
  vt_alertDailyLimitGeneric:"दैनिक सीमा पूरी",
  vt_alertIssue:            "समस्या",

  vt_verdictIdeal:          "आदर्श",
  vt_verdictAcceptable:     "स्वीकार्य",
  vt_verdictAdjustment:     "समायोजन आवश्यक",
  vt_verdictAvoid:          "टालें",
  vt_severity:              "गंभीरता:",
  vt_planLabel:             "योजना:",
  vt_quotaTodayPrefix:      "आज:",
  vt_quotaUnlimited:        "असीमित",
  vt_emptyReportTitle:      "कोई रिपोर्ट लोड नहीं",
  vt_emptyReportBody:       "यहाँ परिणाम देखने के लिए पहले एक स्मार्ट स्कैन चलाएँ।",
  vt_emptyOpenScreen:       "एस्ट्रोवास्तु प्रो खोलें",
  vt_pdfReadyDesc:          "आपकी पूर्ण विस्तृत PDF रिपोर्ट देखने और शेयर करने के लिए तैयार है।",
  vt_noFloorPlan:           "कोई फ्लोर प्लान नहीं जोड़ा",

  vt_lblPropertyName:       "संपत्ति का नाम",
  vt_phPropertyName:        "जैसे — अंधेरी शॉप, पवई HQ",
  vt_lblDirection:          "दिशा:",
  vt_lblCriticalRoomMark:   "(★ = महत्वपूर्ण)",

  vt_priceSingleRoom:       "एकल कमरा (क्विक चेक) — ₹199",
  vt_priceThreeBundle:      "3-कमरा बंडल (स्पॉट चेक) — ₹499",
  vt_priceFullHome:         "पूर्ण होम एडवांस्ड — ₹2,999 आजीवन प्रति संपत्ति",
  vt_priceBusinessShop:     "🏪 शॉप वास्तु — ₹999 (कैश काउंटर, प्रवेश, मालिक की सीट)",
  vt_priceBusinessOffice:   "🏢 ऑफिस वास्तु — ₹1,499 (CEO केबिन, कॉन्फ्रेंस, लॉकर)",
  vt_priceBusinessFactory:  "🏭 फैक्ट्री वास्तु — ₹2,999 (मशीनरी, कच्चा माल, बॉयलर)",
  vt_priceMahadashaConflict:"महादशा + अंतर्दशा संघर्ष अलर्ट",
  vt_priceFamilyMatch:      "परिवार की कुंडलियाँ (5 तक) क्रॉस-मैच",
  vt_pricePdfShare:         "PDF डाउनलोड + इतिहास + व्हाट्सएप शेयर",
  vt_priceOwnerKundli:      "मालिक कुंडली + 3 भागीदारों तक का विश्लेषण",
  vt_priceMuhurat:          "बिज़नेस आरंभ मुहूर्त चार्ट विचार",

  vt_discountProSubs:       "जनरल प्रो सब्सक्राइबर्स",
  vt_discountAmount:        "20% की छूट",
  vt_discountSuffix:        "ऊपर की सभी एस्ट्रोवास्तु खरीद पर।",

  vt_reportsSub:            "अपने सभी पिछले PDF स्कैन देखें और शेयर करें",

  vt_bulFreeMagnetometer:   "वास्तविक मैग्नेटोमीटर कम्पास — दिशा खोजें",
  vt_bulFreeRoomGuide:      "रूम-वार गाइड: किचन, बेडरूम, पूजा कहाँ होने चाहिए",
  vt_bulFreeDosDonts:       "हर दिशा के लिए सामान्य क्या करें / क्या न करें",
  vt_bulFree8Directions:    "8 दिशाओं के देवता, तत्व और अर्थ",

  vt_compassHeading:        "वास्तु कम्पास",
  vt_compassSubhead:        "पवित्र दिशा खोजक",

  vt_introWhatIsVastu:      "वास्तु शास्त्र क्या है?",
  vt_introKundliPersonalized: "🪐  कुंडली + वास्तु = व्यक्तिगत",
  vt_introQuickCheckTitle:  "व्यक्तिगत क्विक चेक",
  vt_introQuickCheckBody:   "आपकी लग्न, महादशा और विशेष योगों के आधार पर — कमरे की दिशा का निर्णायक फैसला, शास्त्रीय स्रोतों के साथ।",
};

// ─────────────────────────────────────────────────────────────────────────────
// Public getter — fall back to English for non-explicit langs (no Hinglish leak)
// ─────────────────────────────────────────────────────────────────────────────
export function getTV(lang: UILang | string | undefined | null): VastuT {
  switch ((lang || "en") as string) {
    case "hn": return hn;
    case "hi": return hi;
    default:   return en;
  }
}
