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
  mdDivisionalTitle:  string;
  mdDivisionalSub:    string;
  viewChart:          string;
  hideChart:          string;
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
  numBirthDayLbl:     string;
  numBirthDayHi:      string;
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
  numCoreSummary:     string;
  numBasicLockedHint: string;
  numBasicCompareTitle: string;
  numBasicCompareBasicLine: string;
  numBasicCompareProLine: string;
  numProTeaseBtn:     string;
  numProfileFor:      string; // "{name}"

  // ── profile-edit.tsx ──────────────────────────────────────
  pe_primary:         string;
  pe_viewKundli:      string;
  pe_editProfile:     string;
  pe_setAsPrimary:    string;
  pe_delete:          string;
  pe_addNewKundli:    string;
  pe_editFamily:      string;
  pe_addFamily:       string;
  pe_lblName:         string;
  pe_phName:          string;
  pe_male:            string;
  pe_female:          string;
  pe_other:           string;
  pe_lblRelation:     string;
  pe_phSelect:        string;
  pe_lblDOB:          string;
  pe_phDD:            string;
  pe_phMonth:         string;
  pe_phYear:          string;
  pe_lblTOB:          string;
  pe_phHH:            string;
  pe_phMM:            string;
  pe_lblBirthPlace:   string;
  pe_phCity:          string;
  pe_search:          string;
  pe_pickDay:         string;
  pe_pickMonth:       string;
  pe_pickYear:        string;
  pe_pickHour:        string;
  pe_pickMinute:      string;
  pe_pickRelation:    string;
  pe_deleteMember:    string;
  pe_husband:         string;
  pe_wife:            string;
  pe_son:             string;
  pe_daughter:        string;
  pe_father:          string;
  pe_mother:          string;
  pe_brother:         string;
  pe_sister:          string;
  pe_friend:          string;

  // ── kundli-milan.tsx ──────────────────────────────────────
  km_unlockReveal:    string;
  km_onCalculate:     string;
  km_riskLevel:       string;
  km_soulBond:        string;
  km_karmaLink:       string;
  km_nadiNakBond:     string;
  km_ganaCompat:      string;
  km_yoniAnalysis:    string;
  km_noNegPatterns:   string;
  km_finalVerdict:    string;
  km_tapUnlock:       string;
  km_basic:           string;
  km_manglikDosh:     string;
  km_recalc:          string;

  // ── vastu.tsx (residual hardcoded strings) ────────────────
  vu_camera:          string;
  vu_gallery:         string;
  vu_takePhotoNow:    string;
  vu_chooseSavedPhoto:string;
  vu_initiateScan:    string;
  vu_chooseRoomType:  string;
  vu_liveCompass:     string;
  vu_deepScanTitle:   string;
  vu_fromGallery:     string;
  vu_noFloorPlan:     string;
  vu_remove:          string;
  vu_runDeepScan:     string;
  vu_deepScanBadge:   string;
  vu_startDeepScan:   string;
  vu_wallByWall:      string;
  vu_spatialEnergy:   string;
  vu_scanInconclusive:string;
  vu_imageClarity:    string;
  vu_recapture:       string;
  vu_drishtiName:     string;
  vu_scanOk:          string;
  vu_compliance:      string;
  vu_runNewScan:      string;
  vu_whatIsVastu:     string;
  vu_unlockPro:       string;
  vu_roomGuide:       string;
  vu_tapAnyCard:      string;
  vu_proHeader:       string;
  vu_proSubheader:    string;
  vu_proDesc:         string;
  vu_oneTime:         string;
  vu_genTipsTitle:    string;
  vu_genTip1:         string;
  vu_genTip2:         string;
  vu_genTip3:         string;
  vu_genTip4:         string;
  vu_genTip5:         string;
  vu_genTip6:         string;
  vu_disclaimer:      string;
  vu_astroVastuPro:   string;
  vu_personalizedSub: string;
  vu_cancelAnytime:   string;
  vu_talkExpert:      string;
  vu_new:             string;
  vu_cosmicDrishti:   string;

  // ── kundli-milan + profile-edit (round 2) ────────────────
  km_addYourKundli:   string;
  km_addPartnerKundli:string;
  km_errName:         string;
  km_errAllFields:    string;
  km_lblName:         string;
  km_lblDob:          string;
  km_lblTime:         string;
  km_lblPlace:        string;

  // ── kundli-milan (round 3 – sections, cards, badges, grades, bars) ──
  km_birthDetailsReq:  string;
  km_partnerBirth:     string;
  km_phName:           string;
  km_phDob:            string;
  km_phTime:           string;
  km_phPlace:          string;
  km_birthMissing:     string;
  km_calcFailed:       string;
  km_okBtn:            string;
  km_aap:              string;

  km_secTopInsights:   string;
  km_secDeepInsights:  string;
  km_secAdvAnalysis:   string;
  km_secFutInsights:   string;
  km_secHidPremium:    string;

  km_coreCompTitle:    string;
  km_coreCompDesc:     string;
  km_riskScanTitle:    string;
  km_riskScanDesc:     string;
  km_personMatchTitle: string;
  km_personMatchDesc:  string;
  km_soulKarmaTitle:   string;
  km_soulKarmaDesc:    string;
  km_intimacyTitle:    string;
  km_intimacyDesc:     string;
  km_doshaEngTitle:    string;
  km_doshaEngDesc:     string;
  km_negEnergyTitle:   string;
  km_negEnergyDesc:    string;
  km_strChalTitle:     string;
  km_strChalDesc:      string;
  km_remAdvTitle:      string;
  km_remAdvDesc:       string;

  km_marriageTime:     string;
  km_childPlan:        string;
  km_finCompat:        string;
  km_lifeStab:         string;
  km_finHarmony:       string;
  km_familyAccept:     string;

  km_karmRelTitle:     string;
  km_karmRelDesc:      string;
  km_pastLifeTitle:    string;
  km_pastLifeDesc:     string;
  km_divorceTitle:     string;
  km_divorceDesc:      string;
  km_loyaltyTitle:     string;
  km_loyaltyDesc:      string;

  km_badgeMostImp:     string;
  km_badgeCritCheck:   string;
  km_badgeDecCard:     string;
  km_badgeSecret:      string;

  km_gradeExcellent:   string;
  km_gradeVeryGood:    string;
  km_gradeAverage:     string;
  km_gradeBelowAvg:    string;
  km_gradeLowMatch:    string;

  km_kutaSahi:         string;
  km_kutaAnmatch:      string;
  km_kutaDono:         string;

  km_emotionalBond:    string;
  km_mentalConn:       string;
  km_intimacyHarm:     string;
  km_communication:    string;
  km_natureTemp:       string;
  km_socialAlign:      string;
  km_lifestyleHarm:    string;
  km_physicalHarm:     string;
  km_energeticAttr:    string;

  km_compMismatch:     string;
  km_doshaConflict:    string;
  km_longTermStab:     string;
  km_nadiDosh:         string;
  km_bhakootDosh:      string;
  km_ganaDosh:         string;
  km_grahaMaitri:      string;

  km_onePartMang:      string;
  km_noMangConf:       string;

  km_natTimingExp:     string;
  km_slightPatience:   string;
  km_medConsAdv:       string;
  km_strongFinAlign:   string;
  km_modBudgetHelp:    string;
  km_highlyLikely:     string;
  km_mayNeedTime:      string;
  km_marrAusp:         string;
  km_marrModerate:     string;
  km_marrDelay:        string;

  km_riskLow:          string;
  km_riskModerate:     string;
  km_riskHigh:         string;

  km_deepKarmTie:      string;
  km_growConn:         string;
  km_posPastLife:      string;
  km_neutralKarma:     string;

  km_planFriendStrong: string;
  km_sharedEnergies:   string;
  km_taraFav:          string;
  km_modTaraDest:      string;
  km_bhakSubh:         string;
  km_rashiAlign:       string;

  km_nadiHealth:       string;
  km_minorTempDiff:    string;
  km_ganaClash:        string;
  km_commPracNeeded:   string;
  km_bhakTimeCaut:     string;
  km_patienceConfl:    string;
  km_yoniMismatch:     string;
  km_qualityTimeNeeded:string;

  km_pastLifeScore:    string;
  km_ancestKarma:      string;
  km_nakDream:         string;
  km_advDoshaRev:      string;

  km_unlockComplete:   string;
  km_realTimeAnalysis: string;
  km_secFutTimeline:   string;
  km_secSoulKarma:     string;
  pe_otherProfiles:   string;
  pe_recentlyDeleted: string;
  pe_noKundliYet:     string;
  pe_manageProfile:   string;
  pe_tabKundli:       string;
  pe_tabPersonal:     string;
  pe_lblCosmoId:      string;
  pe_cosmoIdHint:     string;
  pe_lblGmail:        string;
  pe_lblPhone:        string;
  pe_phPhone:         string;
  pe_savePersonal:    string;
  pe_personalSaved:   string;
  pe_nameLockedHint:  string;
  pe_phoneLockedHint: string;
  pe_gmailLockedHint: string;
  pe_loginRequired:   string;

  // ── panchang (pn_*) ──
  pn_computing:       string;
  pn_dataSource:      string;
  pn_offline:         string;
  pn_today:           string;
  pn_parso:           string;
  pn_auspicious:      string;
  pn_megaFestival:    string;
  pn_bNational:       string;
  pn_bVrat:           string;
  pn_bMuhurat:        string;
  pn_bandExcellent:   string;
  pn_bandGood:        string;
  pn_bandMixed:       string;
  pn_bandCaution:     string;
  pn_tabToday:        string;
  pn_tabMuhurat:      string;
  pn_tabGochar:       string;
  pn_tabVrat:         string;
  pn_tabVivah:        string;
  pn_ekadashiSub:     string;
  pn_ekadashiCount:   string;
  pn_ekadashiNote:    string;
  pn_vivahCount:      string;
  pn_gocharBundled:   string;
  pn_currentMonth:    string;
  pn_noEkadashiMonth: string;
  pn_tagToday:        string;
  pn_pakshaWord:      string;
  pn_ekadashiTodayHdr:string;
  pn_tarabalaHdr:     string;
  pn_tarabalaHint:    string;
  pn_loadPanchang:    string;
  pn_loadEkadashi:    string;
  pn_loadFail:        string;
  pn_brahmaMuhurta:   string;
  pn_gulika:          string;
  pn_abhijit:         string;
  pn_muhuratFail:     string;
  pn_muhuratLoc:      string;
  pn_gocharFail:      string;
  pn_gocharDeploy:    string;
  pn_gocharApiFail:   string;
  pn_vivahSub:        string;
  pn_vivahEmpty:      string;
  pn_vivahLoading:    string;
  pn_vivahWindow:     string;
  pn_vivahConf:       string;
  pn_vivahCoupleHint: string;
  pn_vivahBlockedChaturmas: string;
  pn_vivahBlockedMeena:     string;
  pn_planetSun:       string;
  pn_planetMoon:      string;
  pn_planetMars:      string;
  pn_planetMercury:   string;
  pn_planetJupiter:   string;
  pn_planetVenus:     string;
  pn_planetSaturn:    string;
  pn_planetRahu:      string;
  pn_planetKetu:      string;
  pn_motionRetro:     string;

  // ── numerology (nm_*) ──
  nm_proTools:        string;
  nm_premium:         string;
  nm_lifeMastery:     string;
  nm_yourNumbers:     string;
  nm_yourNumbersHint: string;
  nm_whatsInside:     string;
  nm_opening:         string;
  nm_generateBtn:     string;

  // ── career (cr_*) ──
  cr_pageTitle:       string;
  cr_loading:         string;
  cr_loginRequired:   string;
  cr_addProfile:      string;
  cr_scoreLabel:      string;
  cr_strongPhase:     string;
  cr_cautionPhase:    string;
  cr_mixedPhase:      string;
  cr_quickReading:    string;
  cr_hiddenInsight:   string;
  cr_proCta:          string;
  cr_upgradeBtn:      string;
  cr_houses:          string;
  cr_lord:            string;
  cr_inHouse:         string;
  cr_planets:         string;
  cr_dasha:           string;
  cr_mahadasha:       string;
  cr_antardasha:      string;
  cr_ends:            string;
  cr_transit:         string;
  cr_growth:          string;
  cr_jobChange:       string;
  cr_struggle:        string;
  cr_reasoning:       string;
  cr_pathTitle:       string;
  cr_jobLabel:        string;
  cr_businessLabel:   string;
  cr_pathConfidence:  string;
  cr_pathMode:        string;
  cr_bestOptions:     string;
  cr_topStrengths:    string;
  cr_weakness:        string;
  cr_risk:            string;

  // ── health (hl_*) ──
  hl_pageTitle:       string;
  hl_loginRequired:   string;
  hl_healthyPhase:    string;
  hl_careNeeded:      string;
  hl_mixedPhase:      string;
  hl_scoreLabel:      string;
  hl_riskLabel:       string;
  hl_houses:          string;
  hl_planets:         string;
  hl_riskPeriods:     string;
  hl_nature:          string;
  hl_recovery:        string;
  hl_prevent:         string;
  hl_organs:          string;
  hl_remedies:        string;

  // ── finance (fn_*) ──
  fn_pageTitle:       string;
  fn_growthPhase:     string;
  fn_cautionPhase:    string;
  fn_stablePhase:     string;
  fn_scoreLabel:      string;
  fn_houses:          string;
  fn_planets:         string;
  fn_inflow:          string;
  fn_expense:         string;
  fn_invest:          string;
  fn_sudden:          string;
  fn_stability:       string;
  fn_income:          string;

  // ── relationship (rl_*) ──
  rl_loveTitle:       string;
  rl_loveSub:         string;
  rl_mostUsed:        string;
  rl_loveDesc:        string;
  rl_marriageTitle:   string;
  rl_marriageSub:     string;
  rl_deepBadge:       string;
  rl_partnerTitle:    string;
  rl_partnerSub:      string;
  rl_partnerDesc:     string;
  rl_newBadge:        string;
  rl_pageHeader:      string;
  rl_selfLabel:       string;
  rl_partnerSelect:   string;
  rl_change:          string;

  // ── my-reports (mr_*) ──
  mr_loginRequired:   string;
  mr_loadError:       string;
  mr_networkError:    string;
  mr_waLinkPrefix:    string;
  mr_waErrorTitle:    string;
  mr_openPdf:         string;
  mr_whatsapp:        string;
  mr_pageTitle:       string;
  mr_loading:         string;
  mr_emptyTitle:      string;
  mr_footer:          string;

  // ── my-kundli (mk_*) ──
  mk_savedCount:      string;
  mk_emptyTitle:      string;
  mk_emptyDesc:       string;
  mk_addNew:          string;
  mk_primary:         string;
  mk_deleteTitle:     string;
  mk_deleteDesc:      string;
  mk_cancel:          string;
  mk_delete:          string;

  // ── my-reports kind labels ──
  mr_kindHomePro:     string;
  mr_kindShop:        string;
  mr_kindOffice:      string;
  mr_kindFactory:     string;
  mr_kindBusiness:    string;

  // ── relationship Alert ──
  rl_kundliReqTitle:        string;
  rl_kundliReqBoth:         string;
  rl_kundliReqSelf:         string;
  rl_kundliReqSelectFirst:  string;
  rl_kundliReqPartnerMissing: string;
  rl_kundliReqAddBtn:       string;
  rl_kundliReqCancel:       string;

  // ── numerology What's Inside (12 sections) ──
  nm_wi1Title: string;  nm_wi1Sub: string;
  nm_wi2Title: string;  nm_wi2Sub: string;
  nm_wi3Title: string;  nm_wi3Sub: string;
  nm_wi4Title: string;  nm_wi4Sub: string;
  nm_wi5Title: string;  nm_wi5Sub: string;
  nm_wi6Title: string;  nm_wi6Sub: string;
  nm_wi7Title: string;  nm_wi7Sub: string;
  nm_wi8Title: string;  nm_wi8Sub: string;
  nm_wi9Title: string;  nm_wi9Sub: string;
  nm_wi10Title: string; nm_wi10Sub: string;
  nm_wi11Title: string; nm_wi11Sub: string;
  nm_wi12Title: string; nm_wi12Sub: string;

  // ── forecast widget ──
  fc_demo:              string;
  fc_dailyEnergyScore:  string;
  fc_moonRashi:         string;
  fc_paksha:            string;
  fc_energy:            string;
  fc_activeDasha:       string;

  // ── subscription screen ──
  sub_active:           string;
  sub_upgradeBtn:       string;
  sub_getBasic:         string;
  sub_free:             string;
  sub_alwaysFree:       string;
  sub_cmpJyotishQ:      string;
  sub_cmpMarriage:      string;
  sub_cmpTimeline:      string;
  sub_cmpDasha:         string;
  sub_cmpKarmic:        string;
  sub_cmpPdf:           string;
  sub_cmpProfiles:      string;

  // ── daily-alerts energy legend ──
  da_energyLevels:      string;
  da_energyGood:        string;
  da_energyNeutral:     string;
  da_energyChallenging: string;

  // ── profile-edit relation labels ──
  pe_relSelf:      string;
  pe_relHusband:   string;
  pe_relWife:      string;
  pe_relSon:       string;
  pe_relDaughter:  string;
  pe_relFather:    string;
  pe_relMother:    string;
  pe_relBrother:   string;
  pe_relSister:    string;
  pe_relFriend:    string;
  pe_relOther:     string;

  // ── subscription plan names + tagline ──
  sub_planBasicName:    string;
  sub_planProName:      string;
  sub_planBasicTag:     string;
  sub_planProTag:       string;

  // ── subscription Basic plan features (6) ──
  sub_bF1: string; sub_bF2: string; sub_bF3: string;
  sub_bF4: string; sub_bF5: string; sub_bF6: string;

  // ── subscription Basic plan locked items (4) ──
  sub_bL1: string; sub_bL2: string; sub_bL3: string; sub_bL4: string;

  // ── subscription Pro plan features (9) ──
  sub_pF1: string; sub_pF2: string; sub_pF3: string; sub_pF4: string; sub_pF5: string;
  sub_pF6: string; sub_pF7: string; sub_pF8: string; sub_pF9: string;

  // ── vastu UI strings ──
  vu_camSub:     string;
  vu_galSub:     string;
  vu_roomPicker: string;
  vu_review:     string;
  vu_reviewSub:  string;
  vu_tabBasic:   string;
  vu_tabPro:     string;
  vu_introBody:  string;

  // ── kundli-milan additional (km2_*) ──
  km2_secRiskScan:        string;
  km2_secPersMatch:       string;
  km2_secIntimacyComp:    string;
  km2_secNegEnergy:       string;
  km2_chipClear:          string;
  km2_chipMild:           string;
  km2_chipPresent:        string;
  km2_strengthsHdr:       string;
  km2_challengesHdr:      string;
  km2_persExcellent:      string;
  km2_persModerate:       string;
  km2_persChallenging:    string;
  km2_yoniExceptional:    string;
  km2_yoniComplementary:  string;
  km2_yoniDifferent:      string;
  km2_concernSing:        string;
  km2_concernPlural:      string;
  km2_concernsFound:      string;
  km2_negPatExcell:       string;
  km2_negPatMinor:        string;
  km2_negPatMulti:        string;
  km2_doshDetect:         string;
  km2_nadiAuspProgeny:    string;
  km2_nadiDeepEmpathy:    string;
  km2_remKumbhVivah:      string;
  km2_remEkadashi:        string;
  km2_remChandraMantra:   string;
  km2_remRudrabhishek:    string;
  km2_remGemstones:       string;
  km2_remSunderkand:      string;
  km2_fvExceptional:      string;
  km2_fvVeryPositive:     string;
  km2_fvModerate:         string;
  km2_fvChallenging:      string;
  km2_ashtakootScoreLbl:  string;
  km2_concernDetSuffix:   string;
  km2_addBothFirst:       string;
  km2_unlockFullAnal:     string;
  km2_youPlaceholder:     string;
  km2_birthMissingBody:   string;
  km2_calcFailedBody:     string;
  km2_matchingWith:       string;
  km3_yourPersAnalysis:   string;
  km3_insEmotional:       string;
  km3_insMarriage:        string;
  km3_insRisks:           string;
  km3_insKarmic:          string;
  km3_insStrength:        string;
  km3_insTriggers:        string;
  km3_insStability:       string;
  km3_insFinal:           string;
  km3_unlEmotional:       string;
  km3_unlMarriage:        string;
  km3_unlRisks:           string;
  km3_unlKarmic:          string;
  km3_unlStrength:        string;
  km3_unlTriggers:        string;
  km3_unlStability:       string;
  km3_unlFinal:           string;
  km3_nadiAlag:           string;
  km3_nadiSama:           string;
  km3_personFallback:     string;
  km3_errTryAgain:        string;
  km3_proTrailMore:       string;
  km3_kundliBased:        string;
  km3_truthsBelow:        string;
  km3_unlockToSee:        string;
  km3_whatYouUnlock:      string;
  km3_lockedPreview:      string;
  km3_addBothToUnlock:    string;
  km3_addBothSubtext:     string;

  // ── Phase 2 screen localization ──
  vu_alPermNeeded: string;
  vu_alGalleryMsg: string;
  vu_alCameraMsg: string;
  vu_alError: string;
  vu_alPhotoFailed: string;
  vu_alCamFailed: string;
  vu_alPhotoMissing: string;
  vu_alPhotoMissingMsg: string;
  vu_alScanFailed: string;
  vu_alScanFailedMsg: string;
  vu_alDailyLimitMsg: string;
  vu_alStepHint: string;
  ku_ashtakWhat: string;
  ku_ashtakWhatBody: string;
  ku_approxTransit: string;
  ku_houseLabel: string;
  ku_bavStrong: string;
  ku_bavGood: string;
  ku_bavAverage: string;
  ku_bavWeak: string;
  ku_bavLegStrong: string;
  ku_bavLegGood: string;
  ku_bavLegAverage: string;
  ku_bavLegWeak: string;
  ku_transitDisclaimer: string;
  pr_tabIndia: string;
  pr_tabGlobal: string;
  pr_active: string;
  pr_free: string;
  pr_freePlan: string;
  pr_myData: string;
  pr_myKundli: string;
  pr_saved: string;
  pr_perYear: string;
  pr_perMonth: string;
  sub_premiumBadge: string;
  sub_bestValueBadge: string;
  vu_compassTitle: string;
  vu_compassSubtitle: string;
  vu_sensorActive: string;
  vu_aligning: string;
  vu_sensorInactive: string;
  vu_moveDevice: string;
  vu_idealDirLbl: string;
  vu_northEast: string;
  vu_tabDos: string;
  vu_tabDonts: string;
  vu_tabRemedies: string;
  ku_mahadasha: string;
  ku_antardasha: string;
  ku_pratyantardasha: string;
  ku_mahaTimeline: string;
  ku_activeNow: string;
  ku_active: string;
  ku_yearsSuffix: string;
  ku_whatNavatara: string;
  ku_navataraDesc: string;
  ku_chandraNakBase: string;
  ku_whatJaimini: string;
  ku_jaiminiDesc: string;
  ku_atmakaraka: string;
  ku_jaiminiLagna: string;
  ku_jaiminiLagnaDesc: string;
  ku_liveChandraTransit: string;
  ku_natalConj: string;
  ku_whatKP: string;
  ku_kpSignificators: string;
  ku_birthChartSnap: string;
  ku_planetPosition: string;
  ku_planetPositionSub: string;
  ku_gemstones: string;
  ku_gemstonesSub: string;
  ku_gemstonesBadge: string;
  ku_gemstonesHero: string;
  ku_gemstonesAll: string;
  gs_buyTitle: string;
  gs_youSave: string;
  gs_offerSelf: string;
  gs_offerReferral: string;
  gs_selfBuy: string;
  gs_referralBuy: string;
  gs_flatOff: string;
  gs_referrerGets: string;
  gs_referralPlaceholder: string;
  gs_selfReferralErr: string;
  gs_referralHint: string;
  gs_yourReferral: string;
  gs_referralEarn: string;
  gs_afterDelivery: string;
  gs_payNow: string;
  gs_disclaimer: string;
  gs_shopTitle: string;
  gs_buyCta: string;
  gs_selectRatti: string;
  gs_ratti: string;
  gs_shopFrom: string;
  gs_shopSizes: string;
  gs_certified: string;
  gs_benefitTag: string;
  gs_whatsappPhotos: string;
  gs_whatsappCta: string;
  gs_productSpecs: string;
  gs_howToWear: string;
  gs_careTitle: string;
  gs_whyWear: string;
  gs_deliveryNote: string;
  gs_authenticPromise: string;
  ku_dailyAlertsLink: string;
  ku_dailyAlertsLinkSub: string;
  ku_house: string;
  ku_nakshatraLabel: string;
  ku_btnKundli: string;
  ku_btnAshtak: string;
  ku_btnNavatara: string;
  ku_btnJaimini: string;
  ku_btnTransit: string;
  ku_btnKP: string;
  ku_secDashaTimeline: string;
  ku_secAshtakavarga: string;
  ku_secNavatara9Tara: string;
  ku_secJaiminiKarakas: string;
  ku_secGrahaTransit: string;
  ku_secKpPaddhati: string;
  ku_snapAscendant: string;
  ku_snapMoonSign: string;
  ku_snapNakshatra: string;
  ku_snapNakshatraLord: string;
  ku_snapDashaBalance: string;
  ku_snapLiveMoonTransit: string;
  // Phase 2.8.59 — optional, fall back to English in kundli.tsx if a locale
  // file does not yet provide a translation. Keeps the i18n contract
  // backward-compatible across all 20+ language objects.
  ku_snapLiveJupiterTransit?: string;
  ku_snapLiveSaturnTransit?: string;
  ku_padaLabel: string;
  ku_jaiminiDegPre: string;
  ku_jaiminiDegSuf: string;
  ku_kpDesc: string;
  ku_kpFooter: string;
  ku_kpStar: string;
  ku_kpSub: string;
  ku_kpSubSub: string;
  ku_kpAsc: string;
  ku_savHeading: string;
  vu_alNetError: string;
  vu_alNetErrorMsg: string;
  vu_alCompassCalib: string;
  vu_alCompassCalibMsg: string;
  vu_alWallDirection: string;
  vu_alCamPermNeeded: string;
  vu_alGalPermNeeded: string;
  vu_alPhotoUnreadable: string;
  vu_alFloorUploadFail: string;
  vu_alWallPhotoFirst: string;
  vu_alMin2Walls: string;
  vu_alLoginReq: string;
  vu_alLoginReqMsg: string;
  vu_alServerNoTalk: string;
  vu_alDailyLimit: string;
  vu_alDeepScanFail: string;
  vu_alTryAgain: string;
  prof_alNotifOff: string;
  prof_alNotifOffMsg: string;
  prof_alTestSent: string;
  prof_alTestSentMsg: string;
  prof_alSendFail: string;
  prof_alTokenMissing: string;
  ds_title: string;
  ds_subtitle: string;
  ds_demo: string;
  ds_totalDosh: string;
  ds_present: string;
  ds_notPresent: string;
  ds_scanning: string;
  ds_analyzing: string;
  ds_checking: string;
  ds_analysis: string;
  ds_active: string;
  ds_mild: string;
  ds_clear: string;
  ds_detected: string;
  ds_remedies: string;
  ds_disclaimer: string;
  prof_madeWith: string;
  sub_avPricing: string;
  sub_avSubtitle: string;
  sub_proSubsLabel: string;
  sub_proGetSuffix: string;
  sub_offSuffix: string;
  sub_openAv: string;
  car_karmaStrength: string;
  fn_hidden: string;
  fn_wealthKarma: string;
  hl_hidden: string;
  dl_luckyColor: string;
  dl_luckyNumbers: string;
  rl_addPartner: string;
  pe2_cancel: string;
  pe2_delete: string;
  pe2_deleteSuffix: string;

  // ── Phase 4 additions ─────────────────────────
  nf_title: string;
  nf_doesntExist: string;
  nf_goHome: string;
  ab_title: string;
  ab_subtitle: string;
  ab_secMission: string;
  ab_pMission1: string;
  ab_pMission2: string;
  ab_secDifferent: string;
  ab_pDifferent: string;
  ab_secConnect: string;
  ab_lblSupportEmail: string;
  ab_lblWebsite: string;
  ab_secLegal: string;
  ab_linkPrivacy: string;
  ab_linkTerms: string;
  ab_linkRefund: string;
  ab_linkDisclaimer: string;
  ab_linkDelete: string;
  ab_lblAppVersion: string;
  ab_versionFoot: string;
  da_title: string;
  da_subtitle: string;
  da_calloutDanger: string;
  da_secWhatHappens: string;
  da_wb1: string;
  da_wb2: string;
  da_wb3: string;
  da_wb4: string;
  da_wb5: string;
  da_secBefore: string;
  da_pBefore: string;
  da_bb1: string;
  da_bb2: string;
  da_bb3: string;
  da_bb4: string;
  da_secConfirm: string;
  da_pConfirm: string;
  da_inputPh: string;
  da_btnDelete: string;
  da_btnDeleting: string;
  da_btnCancelBack: string;
  da_secNeedHelp: string;
  da_pNeedHelp: string;
  da_alertNotSignedIn: string;
  da_alertLoginFirst: string;
  da_alertConfirmTtl: string;
  da_alertConfirmMsg: string;
  da_alertCancel: string;
  da_alertYesDelete: string;
  da_alertDeletedTtl: string;
  da_alertDeletedMsg: string;
  da_alertOk: string;
  da_alertFailedTtl: string;
  da_alertFailedMsg: string;
  smf_title: string;
  smf_loadingMsg: string;
  smf_unavailableTtl: string;
  smf_tryAgain: string;
  smf_kundliFirst: string;
  smf_activeChain: string;
  smf_lblMaha: string;
  smf_lblAntar: string;
  smf_lblPratyantar: string;
  smf_adWindow: string;
  smf_pdShift: string;
  smf_lblMD: string;
  smf_lblAD: string;
  smf_lblPD: string;
  smf_rulesPrefix: string;
  smf_sitsIn: string;
  smf_pdActiveWindow: string;
  smf_lifeAreas: string;
  smf_whyPrefix: string;
  smf_opportunities: string;
  smf_cautions: string;
  smf_remedyLabel: string;
  smf_remedyFocused: string;
  smf_generated: string;
  smf_pureEngine: string;
  smf_areaCareer: string;
  smf_areaFinance: string;
  smf_areaHealth: string;
  smf_areaRelationship: string;
  smf_areaSpirituality: string;
  dp_title: string;
  dp_subtitle: string;
  dp_metaCity: string;
  dp_quickQuestion: string;
  dp_orType: string;
  dp_inputPh: string;
  dp_btnGetAnswer: string;
  dp_alertEmptyTtl: string;
  dp_alertEmptyMsg: string;
  dp_errNoticeTtl: string;
  dp_errQuotaPro: string;
  dp_errSession: string;
  dp_errFetch: string;
  dp_btnSeeUpgrade: string;
  dp_immatureTitle: string;
  dp_refPrefix: string;
  dp_retryAfter: string;
  dp_minutesLater: string;
  dp_chartTitle: string;
  dp_chartLagna: string;
  dp_chartPlace: string;
  dp_chartCategory: string;
  dp_cuspTitle: string;
  dp_houseSuffix: string;
  dp_subLord: string;
  dp_starLord: string;
  dp_signifies: string;
  dp_classicalTitle: string;
  dp_cat_stolen: string;
  dp_cat_partner: string;
  dp_cat_job: string;
  dp_cat_marriage: string;
  dp_cat_health: string;
  dp_cat_litigation: string;
  dp_cat_travel: string;
  dp_cat_general: string;
  dp_pr_stolen: string;
  dp_pr_partner: string;
  dp_pr_job: string;
  dp_pr_marriage: string;
  dp_pr_health: string;
  dp_pr_litigation: string;
  dp_pr_travel: string;
  pk_headerTitle: string;
  pk_headerSub: string;
  pk_modeAsk: string;
  pk_modeNumber: string;
  pk_initMsg: string;
  pk_invalidNumber: string;
  pk_qLimit: string;
  pk_genErr: string;
  pk_netErr: string;
  pk_sankhyaPrefix: string;
  pk_warnTitle: string;
  pk_warnDefault: string;
  pk_warnRef: string;
  pk_forcedLagna: string;
  pk_lblRashi: string;
  pk_lblNakshatra: string;
  pk_cuspKpTitle: string;
  pk_houseSt: string;
  pk_houseNd: string;
  pk_houseRd: string;
  pk_houseTh: string;
  pk_houseWord: string;
  pk_subLord: string;
  pk_timingTitle: string;
  pk_classicalTitle: string;
  pk_numPlaceholder: string;
  pk_numHint: string;
  pk_qInputPh: string;
  pk_cat_stolen: string;
  pk_cat_partner: string;
  pk_cat_job: string;
  pk_cat_marriage: string;
  pk_cat_health: string;
  pk_cat_litigation: string;
  pk_cat_travel: string;
  pk_cat_general: string;
  fr_headerTitle: string;
  fr_heroEyebrow: string;
  fr_heroTitle: string;
  fr_heroSub: string;
  fr_priceLive: string;
  fr_statPages: string;
  fr_statSections: string;
  fr_statEngines: string;
  fr_statLandmarks: string;
  fr_capInside: string;
  fr_pv1Title: string;
  fr_pv1Sub: string;
  fr_pv2Title: string;
  fr_pv2Sub: string;
  fr_pv3Title: string;
  fr_pv3Sub: string;
  fr_pv4Title: string;
  fr_pv4Sub: string;
  fr_capEngines: string;
  fr_eng1Group: string;
  fr_eng1Body: string;
  fr_eng2Group: string;
  fr_eng2Body: string;
  fr_eng3Group: string;
  fr_eng3Body: string;
  fr_capHow: string;
  fr_step1Title: string;
  fr_step1Body: string;
  fr_step2Title: string;
  fr_step2Body: string;
  fr_step3Title: string;
  fr_step3Body: string;
  fr_step4Title: string;
  fr_step4Body: string;
  fr_capBuilt: string;
  fr_honest100: string;
  fr_honest75: string;
  fr_honest20: string;
  fr_honest5: string;
  fr_honestFoot: string;
  fr_ctaText: string;
  fr_ctaSub: string;
  fr_wipBadge: string;
  fr_wipTitle: string;
  fr_wipBody: string;
  fr_wipHint: string;
  mdFaceReadingSubSoon: string;
  fu_introEyebrow: string;
  fu_introTitle: string;
  fu_introSub: string;
  fu_slotFrontLbl: string;
  fu_slotFrontHint: string;
  fu_slotLeftLbl: string;
  fu_slotLeftHint: string;
  fu_slotRightLbl: string;
  fu_slotRightHint: string;
  fu_addedTap: string;
  fu_capOptional: string;
  fu_lblAge: string;
  fu_phAge: string;
  fu_lblGender: string;
  fu_male: string;
  fu_female: string;
  fu_lblLanguage: string;
  fu_camPermNeeded: string;
  fu_galPermNeeded: string;
  fu_couldNotPick: string;
  fu_addPhotoTtl: string;
  fu_addPhotoMsg: string;
  fu_btnCamera: string;
  fu_btnGallery: string;
  fu_btnCancel: string;
  fu_addAllFirst: string;
  fu_progUpload: string;
  fu_progAnalyze: string;
  fu_progRender: string;
  fu_progSub: string;
  fu_errSomething: string;
  fu_doneTitle: string;
  fu_doneSub: string;
  fu_btnOpenShare: string;
  fu_btnAnother: string;
  fu_processing: string;
  fu_btnTryAgain: string;
  fu_btnGenerate: string;
  fu_legalLine: string;
  fu_shareNotAvail: string;
  fu_sessIdMissing: string;
  fpp_headerTitle: string;
  fpp_heroTitle: string;
  fpp_heroSubMale: string;
  fpp_heroSubFemale: string;
  fpp_primaryKundli: string;
  fpp_btnReveal: string;
  fpp_warnNoKundli: string;
  fpp_infoTitle: string;
  fpp_b1: string;
  fpp_b2: string;
  fpp_b3: string;
  fpp_b4: string;
  fpp_b5: string;
  fpp_b6: string;
  fpp_disclaimer1: string;
  fpp_loadingTitle: string;
  fpp_msgAlign: string;
  fpp_msgAlignFull: string;
  fpp_msgComputing: string;
  fpp_msgKundliQuota: string;
  fpp_msgKundliFail: string;
  fpp_msgTaskExpire: string;
  fpp_msgTaskIdMiss: string;
  fpp_msgNetSlow: string;
  fpp_msgStarsBusy: string;
  fpp_tipText: string;
  fpp_btnCancel: string;
  fpp_imgFailed: string;
  fpp_imgBadge: string;
  fpp_traitTitle: string;
  fpp_lblFace: string;
  fpp_lblComplexion: string;
  fpp_lblBuild: string;
  fpp_lblEyes: string;
  fpp_lblEyebrows: string;
  fpp_lblNose: string;
  fpp_lblLips: string;
  fpp_lblHair: string;
  fpp_lblVibe: string;
  fpp_vargottama: string;
  fpp_practTitle: string;
  fpp_lblAge: string;
  fpp_lblDirection: string;
  fpp_lblProfHint: string;
  fpp_lblAttraction: string;
  fpp_classicalTtl: string;
  fpp_disclaimer2: string;
  fpp_btnRevealAgain: string;
  fpp_errTitle: string;
  fpp_errDefault: string;
  fpp_errPortraitFail: string;
  fpp_btnTryAgain: string;
  fpp_alertBirthTtl: string;
  fpp_alertBirthMsg: string;
  fpp_errTimeout: string;
  lg_title: string;
  lg_subtitle: string;
  lg_lastUpdated: string;
  lg_h_privacy: string;
  lg_p_privacyIntro: string;
  lg_callout_privacy: string;
  lg_s1_title: string;
  lg_s1_a: string;
  lg_s1_b: string;
  lg_s1_c: string;
  lg_s1_d: string;
  lg_s1_e: string;
  lg_s2_title: string;
  lg_s2_b1: string;
  lg_s2_b2: string;
  lg_s2_b3: string;
  lg_s2_b4: string;
  lg_s2_b5: string;
  lg_s2_b6: string;
  lg_s2_b7: string;
  lg_s2_b8: string;
  lg_s3_title: string;
  lg_s3_intro: string;
  lg_s3_b1: string;
  lg_s3_b2: string;
  lg_s3_b3: string;
  lg_s3_b4: string;
  lg_s3_outro: string;
  lg_s4_title: string;
  lg_s4_p: string;
  lg_s5_title: string;
  lg_s5_b1: string;
  lg_s5_b2: string;
  lg_s5_b3: string;
  lg_s5_b4: string;
  lg_s5_b5: string;
  lg_s6_title: string;
  lg_s6_intro: string;
  lg_s6_b1: string;
  lg_s6_b2: string;
  lg_s6_b3: string;
  lg_s6_b4: string;
  lg_s6_b5: string;
  lg_s6_outro: string;
  lg_s7_title: string;
  lg_s7_p: string;
  lg_s8_title: string;
  lg_s8_p: string;
  lg_s9_title: string;
  lg_s9_p: string;
  lg_s10_title: string;
  lg_s10_p: string;
  lg_s11_title: string;
  lg_s11_intro: string;
  lg_s11_b1: string;
  lg_s11_b2: string;
  lg_h_terms: string;
  lg_p_termsIntro: string;
  lg_t1_title: string;
  lg_t1_b1: string;
  lg_t1_b2: string;
  lg_t1_b3: string;
  lg_t2_title: string;
  lg_t2_b1: string;
  lg_t2_b2: string;
  lg_t2_b3: string;
  lg_t2_b4: string;
  lg_t3_title: string;
  lg_t3_p: string;
  lg_t4_title: string;
  lg_t4_intro: string;
  lg_t4_b1: string;
  lg_t4_b2: string;
  lg_t4_b3: string;
  lg_t4_b4: string;
  lg_t4_outro: string;
  lg_t5_title: string;
  lg_t5_p: string;
  lg_t6_title: string;
  lg_t6_p: string;
  lg_t7_title: string;
  lg_t7_b1: string;
  lg_t7_b2: string;
  lg_t7_b3: string;
  lg_t7_b4: string;
  lg_t7_b5: string;
  lg_t7_b6: string;
  lg_t8_title: string;
  lg_t8_p: string;
  lg_t9_title: string;
  lg_t9_p: string;
  lg_t10_title: string;
  lg_t10_callout: string;
  lg_t11_title: string;
  lg_t11_p: string;
  lg_t12_title: string;
  lg_t12_p: string;
  lg_t13_title: string;
  lg_t13_p: string;
  lg_t14_title: string;
  lg_t14_p: string;
  lg_t15_title: string;
  lg_t15_p: string;
  lg_t16_title: string;
  lg_t16_p: string;
  lg_h_refund: string;
  lg_p_refundIntro: string;
  lg_callout_refund: string;
  lg_r1_title: string;
  lg_r1_intro: string;
  lg_r1_b1: string;
  lg_r1_b2: string;
  lg_r1_outro: string;
  lg_r2_title: string;
  lg_r2_intro: string;
  lg_r2_b1: string;
  lg_r2_b2: string;
  lg_r2_b3: string;
  lg_r2_b4: string;
  lg_r3_title: string;
  lg_r3_b1: string;
  lg_r3_b2: string;
  lg_r3_b3: string;
  lg_r3_b4: string;
  lg_r3_b5: string;
  lg_r3_b6: string;
  lg_r4_title: string;
  lg_r4_intro: string;
  lg_r4_b1: string;
  lg_r4_b2: string;
  lg_r4_b3: string;
  lg_r4_outro: string;
  lg_r5_title: string;
  lg_r5_p: string;
  lg_r6_title: string;
  lg_r6_p: string;
  lg_r7_title: string;
  lg_r7_p: string;
  lg_r8_title: string;
  lg_r8_b1: string;
  lg_r8_b2: string;
  lg_r8_b3: string;
  lg_h_disclaimer: string;
  lg_callout_disc: string;
  lg_d1_title: string;
  lg_d1_p: string;
  lg_d2_title: string;
  lg_d2_p: string;
  lg_d3_title: string;
  lg_d3_intro: string;
  lg_d3_b1: string;
  lg_d3_b2: string;
  lg_d3_b3: string;
  lg_d3_b4: string;
  lg_d3_b5: string;
  lg_d4_title: string;
  lg_d4_p: string;
  lg_d5_title: string;
  lg_d5_p: string;
  lg_d6_title: string;
  lg_d6_p: string;
  lg_d7_title: string;
  lg_d7_p: string;
  lg_d8_title: string;
  lg_d8_callout: string;
  lg_d9_title: string;
  lg_d9_p: string;
  bv_headerTitle: string;
  bv_cardTitle: string;
  bv_cardBody: string;
  bv_cardBodySmall: string;
  bv_secBizType: string;
  bv_secPremiseName: string;
  bv_phPremiseName: string;
  bv_premiseHint: string;
  bv_refineRooms: string;
  bv_premiseLayout: string;
  bv_engineWillDetect: string;
  bv_lblDirection: string;
  bv_selectDirection: string;
  bv_addRoom: string;
  bv_runScanPrefix: string;
  bv_runScanSuffix: string;
  bv_biz_shop: string;
  bv_biz_office: string;
  bv_biz_factory: string;
  bv_dir_N: string;
  bv_dir_NE: string;
  bv_dir_E: string;
  bv_dir_SE: string;
  bv_dir_S: string;
  bv_dir_SW: string;
  bv_dir_W: string;
  bv_dir_NW: string;
  bv_room_entrance: string;
  bv_room_owner_seat: string;
  bv_room_cash_counter: string;
  bv_room_billing_counter: string;
  bv_room_vault: string;
  bv_room_stock_storage: string;
  bv_room_display: string;
  bv_room_pooja: string;
  bv_room_back_office: string;
  bv_room_staff_room: string;
  bv_room_toilet: string;
  bv_room_owner_cabin: string;
  bv_room_reception: string;
  bv_room_conference: string;
  bv_room_accounts: string;
  bv_room_server_room: string;
  bv_room_pantry: string;
  bv_room_machinery: string;
  bv_room_heavy_machine: string;
  bv_room_raw_storage: string;
  bv_room_finished_goods: string;
  bv_room_boiler: string;
  bv_room_labour_quarter: string;
  bv_errAuthRequired: string;
  bv_errValidationRooms: string;
  bv_btnUploadShopPdf: string;
  bv_btnUploadOfficePdf: string;
  bv_btnUploadOfficePhoto: string;
  bv_btnUploadFactoryPdf: string;
  bv_btnUploadFactoryPhoto: string;
  bv_planNorthHint: string;
  bv_secUploadedPhotos: string;
  bv_btnSubmitReview: string;
  bv_submitSuccessTitle: string;
  bv_submitSuccessBody: string;
  bv_errValidationName: string;
  bv_errUnlockTitle: string;
  bv_errProfileTitle: string;
  bv_errValidTitle: string;
  bv_errScanFailed: string;
  bv_errTryAgain: string;
  bv_btnCompleteProfile: string;
  bv_walletHintPrefix: string;
  bv_walletHintSuffix: string;
  bv_overallScore: string;
  bv_grade: string;
  bv_pdfReady: string;
  bv_pdfBodyHi: string;
  bv_pdfBodyEn: string;
  bv_btnOpenPdf: string;
  bv_footerBrand: string;
  bv_lblIdeal: string;
  bv_lblAcceptable: string;
  bv_lblAdjust: string;
  bv_lblAvoid: string;
  bv_lblOwnerMd: string;
  bv_lblStakeholder: string;
  bv_lblMuhuratAlign: string;
  bv_secPriority: string;
  bv_lblCritical: string;
  bv_secRoomByRoom: string;
  bv_lblZone: string;
  bv_secClassicalRefs: string;
  avp_headerTitle: string;
  avp_heroTitle: string;
  avp_heroBody: string;
  avp_modeCameraTitle: string;
  avp_modeCameraSub: string;
  avp_modeSingleTitle: string;
  avp_modeSingleSub: string;
  avp_modeWholeTitle: string;
  avp_modeWholeSub: string;
  avp_introCameraTitle: string;
  avp_introCameraBody: string;
  avp_pickerLabel: string;
  avp_pickerHint: string;
  avp_camHintPrefix: string;
  avp_camHintNoRoom: string;
  avp_btnSmartScan: string;
  avp_btnUploadPhoto: string;
  avp_btnUploadHomePdf: string;
  avp_badgeSingleRoom: string;
  avp_badgeWholeHome: string;
  avp_uploadPricePerRoom: string;
  avp_uploadPaySubmit: string;
  avp_uploadSubmitted: string;
  avp_introSingleTitle: string;
  avp_introSingleBody: string;
  avp_introWholeTitle: string;
  avp_introWholeBody: string;
  avp_btnRunWhole: string;
  avp_btnAnalysing: string;
  avp_room_bedroom: string;
  avp_room_kitchen: string;
  avp_room_pooja: string;
  avp_room_living: string;
  avp_room_bathroom: string;
  avp_room_entrance: string;
  avp_room_study: string;
  avp_room_store: string;
  avp_errAuthRequired: string;
  avp_errMonthlyLimit: string;
  avp_errUpgradeReq: string;
  avp_errProfile: string;
  avp_errVisionNoRoom: string;
  avp_errScanFailed: string;
  avp_errBodyDefault: string;
  avp_btnCompleteProfile: string;
  avp_btnUpgradePro: string;
  avp_overallScore: string;
  avp_pdfReady: string;
  avp_pdfBody: string;
  avp_btnOpenPdf: string;
  avp_footerBrand: string;
  avp_secPriority: string;
  avp_secRoomByRoom: string;
  avp_lblMdAlert: string;
  avp_quotaUnlimited: string;
  avp_quotaPrefix: string;
  avp_quotaThisMonth: string;
  avp_brandFooter: string;
  avp_brandFooterSub: string;
  avp_lblIdeal: string;
  avp_lblAcceptable: string;
  avp_lblAdjust: string;
  avp_lblAvoid: string;
  avr_emptyTitle: string;
  avr_emptyBody: string;
  avr_btnOpenPro: string;
  avr_headerTitle: string;
  avr_outOf100: string;
  avr_grade: string;
  avr_btnOpenPdf: string;
  avr_btnWhatsApp: string;
  avr_secPriorityHi: string;
  avr_secRoomByRoom: string;
  avr_brandFooter: string;
  avr_shareTitle: string;
  avr_shareScoreLbl: string;
  avr_shareOpenLbl: string;
  avr_shareBrandLbl: string;
  avr_alertShareErr: string;

  // ── Risk Radar — Lucky / Best-Avoid Time card ─────────────────────────────
  // Headline labels for the "Aaj Ka Shubh Ank + Rang" panel + Best/Avoid
  // chips + the loading/empty/CTA states inside the card.
  rrLuckyAajShubhAnk:        string;  // "AAJ KA SHUBH ANK"
  rrLuckyAajShubhRang:       string;  // "AAJ KA SHUBH RANG"
  rrLuckyShubhAnk:           string;  // "SHUBH ANK" (for non-today days)
  rrLuckyShubhRang:          string;  // "SHUBH RANG" (for non-today days)
  rrLuckyBestTime:           string;  // "⏰ BEST TIME"
  rrLuckyAvoidTime:          string;  // "🚫 AVOID TIME"
  rrLuckyPoweredBy:          string;  // "✨ Powered by Advanced Cosmic Intelligence"
  rrLuckyHeaderToday:        string;  // "AAJ KA SHUBH ANK + RANG" (header for empty state)
  rrLuckyHeaderOther:        string;  // "SHUBH ANK + RANG" (header for other days)
  rrLuckyCalculating:        string;  // "Aapka shubh ank aur rang calculate ho raha hai…"
  rrLuckyCreateKundliPrompt: string;  // "Apni kundli banayein — aapke janm ke nakshatra se aaj ka personal shubh ank aur rang dekhein."
  rrLuckyCreateKundliCta:    string;  // "KUNDLI BANAYEIN →"
  rrLuckyDetailsUnavail:     string;  // "Lucky details abhi available nahi hain."
  rrLuckyDayUnavail:         string;  // "Is din ke liye shubh ank aur rang abhi available nahi hain."

  // Forecast — Lucky highlights card (lives on Forecast, not Risk Radar)
  fc_luckyBestTimeLabel:     string;  // "BEST TIME"  (no emoji)
  fc_luckyAvoidTimeLabel:    string;  // "AVOID TIME" (no emoji)
  fc_luckyReason:            string;  // template — "On {date} — lucky number {n} and {colour} colour align with the day's cosmic energy."
  // Lucky colour name → localized (canonical Hinglish names from engine)
  fc_luckyClrHara:           string;  // "Hara"      → Green
  fc_luckyClrPila:           string;  // "Pila"      → Yellow
  fc_luckyClrSafed:          string;  // "Safed"     → White
  fc_luckyClrNeela:          string;  // "Neela"     → Blue
  fc_luckyClrSuneheri:       string;  // "Suneheri"  → Golden
  fc_luckyClrKesari:         string;  // "Kesari"    → Saffron

  // Risk Radar — 24-hour breakdown / level badges
  rrSection24hToday:          string;
  rrSection24hWithDate:       string;
  rrLabelKyaRisk:             string;
  rrLabelKyaAvoid:            string;
  rrLabelKyaKarna:            string;
  rrLabelUpay:                string;
  rrLevelLow:                 string;
  rrLevelMed:                 string;
  rrLevelHigh:                string;
  rrLabelRiskLevel:           string;
  radarHeaderSub:             string;
  radarLoadingTxt:            string;
  radarEmptyTitle:            string;
  radarEmptyBody:             string;
  radarPickerLabel:           string;
  radarDayToday:              string;
  radarDayTomorrow:           string;
  radarTotalLabel:            string;
  radarBadgeHigh:             string;
  radarBadgeMed:              string;
  radarBadgeLow:              string;
  radarSubToday:              string;
  radarSubOther:              string;
  radarStatusActive:          string;
  radarSignalSingular:        string;
  radarSignalPlural:          string;
  radarAllClear:              string;
  radarAllClearSub:           string;
  radarTitle:                 string;
  rrCardTitle:                string;
  rrSafestChip:               string;
  rrChallengingChip:          string;
  rrDayOf7:                   string;
  rrLockedTitle:              string;
  rrLockedSub:                string;
  rrLockedHint:               string;
  rrLockedCta:                string;
  rrScoreUp:                  string;
  rrScoreMixed:               string;
  rrScoreDown:                string;
  rrDotPrimary:               string;
  rrDotSecondary:             string;
  rrDotWatch:                 string;
  rrDotStable:                string;
  rrDotRoutine:               string;
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
  mdVastuTitle:       "Astrovastu Pro",
  mdVastuSub:         "Personalized vastu by your kundli",
  mdDivisionalTitle:  "Divisional Charts",
  mdDivisionalSub:    "D9 Navamsa, D10 Dashamsha, D7 & all vargas",
  viewChart:          "View Chart",
  hideChart:          "Hide Chart",
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
  numFreeSection:     "BASIC NUMEROLOGY",
  numTapHint:         "Tap any card to expand full details",
  numLifePathLbl:     "LIFE PATH NUMBER",
  numLifePathHi:      "Life Path",
  numBirthDayLbl:     "BIRTH DAY NUMBER",
  numBirthDayHi:      "Birth Day",
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
  numCoreSummary:     "YOUR 4 CORE NUMBERS",
  numBasicLockedHint: "Career blueprint, phone numerology & lucky colours are in your Pro PDF report.",
  numBasicCompareTitle: "BASIC VS PRO",
  numBasicCompareBasicLine: "4 core numbers · traits · strength & weakness",
  numBasicCompareProLine: "Full PDF · career blueprint · phone & lucky numbers · remedies",
  numProTeaseBtn:     "Get Numerology Pro Report",
  numProfileFor:      "Numbers for {name}",

  // profile-edit.tsx
  pe_primary:         "PRIMARY",
  pe_viewKundli:      "View Kundli",
  pe_editProfile:     "Edit Profile",
  pe_setAsPrimary:    "Set as Primary",
  pe_delete:          "Delete",
  pe_addNewKundli:    "Add New Kundli",
  pe_editFamily:      "Edit Family Member",
  pe_addFamily:       "Add Family Member",
  pe_lblName:         "NAME",
  pe_phName:          "Full name",
  pe_male:            "Male",
  pe_female:          "Female",
  pe_other:           "Other",
  pe_lblRelation:     "RELATION",
  pe_phSelect:        "Select",
  pe_lblDOB:          "DATE OF BIRTH",
  pe_phDD:            "DD",
  pe_phMonth:         "Month",
  pe_phYear:          "Year",
  pe_lblTOB:          "TIME OF BIRTH",
  pe_phHH:            "HH",
  pe_phMM:            "MM",
  pe_lblBirthPlace:   "BIRTH PLACE",
  pe_phCity:          "City, Country",
  pe_search:          "Search",
  pe_pickDay:         "Select Day",
  pe_pickMonth:       "Select Month",
  pe_pickYear:        "Select Birth Year",
  pe_pickHour:        "Select Hour",
  pe_pickMinute:      "Select Minute",
  pe_pickRelation:    "Select Relation",
  pe_deleteMember:    "Delete Member?",
  pe_husband:         "Husband",
  pe_wife:            "Wife",
  pe_son:             "Son",
  pe_daughter:        "Daughter",
  pe_father:          "Father",
  pe_mother:          "Mother",
  pe_brother:         "Brother",
  pe_sister:          "Sister",
  pe_friend:          "Friend",

  // kundli-milan.tsx
  km_unlockReveal:    "Unlock to reveal hidden truths",
  km_onCalculate:     "ON CALCULATE",
  km_riskLevel:       "Risk Level",
  km_soulBond:        "Soul Bond",
  km_karmaLink:       "Karma Link",
  km_nadiNakBond:     "Nadi Nakshatra Bond",
  km_ganaCompat:      "Gana Compatibility",
  km_yoniAnalysis:    "Yoni Analysis",
  km_noNegPatterns:   "No major negative patterns found",
  km_finalVerdict:    "Final Verdict",
  km_tapUnlock:       "Tap below to unlock everything",
  km_basic:           "Basic",
  km_manglikDosh:     "Manglik Dosh",
  km_recalc:          "Recalculate / Change Details",

  // vastu.tsx
  vu_camera:          "Camera",
  vu_gallery:         "Gallery",
  vu_takePhotoNow:    "Take a photo now",
  vu_chooseSavedPhoto:"Choose a saved photo",
  vu_initiateScan:    "Initiate Vastu Drishti Scan",
  vu_chooseRoomType:  "Choose room type",
  vu_liveCompass:     "LIVE COMPASS",
  vu_deepScanTitle:   "Cosmic Vastu Deep Scan",
  vu_fromGallery:     "From Gallery",
  vu_noFloorPlan:     "No floor plan added",
  vu_remove:          "Remove",
  vu_runDeepScan:     "Run Cosmic Deep Scan",
  vu_deepScanBadge:   "DEEP SCAN",
  vu_startDeepScan:   "Start Deep Scan",
  vu_wallByWall:      "WALL-BY-WALL ANALYSIS",
  vu_spatialEnergy:   "SPATIAL ENERGY MAP",
  vu_scanInconclusive:"SCAN INCONCLUSIVE",
  vu_imageClarity:    "Image clarity insufficient",
  vu_recapture:       "Recapture and scan again",
  vu_drishtiName:     "COSMIC VASTU DRISHTI",
  vu_scanOk:          "SCAN OK",
  vu_compliance:      "VASTU COMPLIANCE",
  vu_runNewScan:      "Run new scan",
  vu_whatIsVastu:     "What is Vastu Shastra?",
  vu_unlockPro:       "Unlock PRO",
  vu_roomGuide:       "ROOM-WISE VASTU GUIDE",
  vu_tapAnyCard:      "Tap any card to see dos, don'ts, and remedies",
  vu_proHeader:       "AstroVastu PRO — Whole Home Scan",
  vu_proSubheader:    "Photo Engine + your Kundli + Mahadasha layer",
  vu_proDesc:         "Floor-plan upload, room photos with compass, deterministic Vastu Shastra rules cited from Brihat Samhita / Mayamatam, personalised priority actions for your chart.",
  vu_oneTime:         "one-time",
  vu_genTipsTitle:    "⚡ General Vastu Tips",
  vu_genTip1:         "Keep the home free of clutter — blocked spaces block energy flow",
  vu_genTip2:         "Ensure your home is well-lit — darkness invites negativity",
  vu_genTip3:         "Fix squeaky or broken doors promptly",
  vu_genTip4:         "Keep indoor plants — they bring life energy into the home",
  vu_genTip5:         "Remove broken or damaged items immediately",
  vu_genTip6:         "A running water feature (fountain or aquarium) in the North is auspicious",
  vu_disclaimer:      "This is a general Vastu guide. For your home specifically, always consult a qualified Vastu expert for personalized advice.",
  vu_astroVastuPro:   "AstroVastu Pro",
  vu_personalizedSub: "Personalized premium Vastu analysis",
  vu_cancelAnytime:   "Cancel anytime",
  vu_talkExpert:      "Talk to Vastu Expert on WhatsApp",
  vu_new:             "NEW",
  vu_cosmicDrishti:   "COSMIC VASTU DRISHTI",

  km_addYourKundli:   "Add Your Kundli",
  km_addPartnerKundli:"Add Partner Kundli",
  km_errName:         "Name is required.",
  km_errAllFields:    "All fields are required.",
  km_lblName:         "NAME",
  km_lblDob:          "DATE OF BIRTH",
  km_lblTime:         "TIME OF BIRTH",
  km_lblPlace:        "BIRTH PLACE",

  km_birthDetailsReq:  "Birth details required",
  km_partnerBirth:     "Partner's birth details",
  km_phName:           "Full name",
  km_phDob:            "DD/MM/YYYY",
  km_phTime:           "HH:MM  AM / PM",
  km_phPlace:          "E.g. Delhi, India",
  km_birthMissing:     "Birth Data Missing",
  km_calcFailed:       "Calculation Failed",
  km_okBtn:            "OK",
  km_aap:              "You",

  km_secTopInsights:   "TOP INSIGHTS",
  km_secDeepInsights:  "DEEP INSIGHTS",
  km_secAdvAnalysis:   "ADVANCED ANALYSIS",
  km_secFutInsights:   "FUTURE INSIGHTS",
  km_secHidPremium:    "HIDDEN PREMIUM",

  km_coreCompTitle:    "Core Compatibility",
  km_coreCompDesc:     "Are your hearts, minds & souls truly aligned for a lifetime together?",
  km_riskScanTitle:    "Risk Scan",
  km_riskScanDesc:     "This insight may change your decision — hidden risks revealed",
  km_personMatchTitle: "Personality Match",
  km_personMatchDesc:  "This insight may change your decision — see if you truly understand each other",
  km_soulKarmaTitle:   "Soul & Karma",
  km_soulKarmaDesc:    "Are you destined? Or is this just timing? Real-time analysis based on your birth chart",
  km_intimacyTitle:    "Intimacy Score",
  km_intimacyDesc:     "Physical & emotional bonding — the truth most couples never discover",
  km_doshaEngTitle:    "Dosha Engine",
  km_doshaEngDesc:     "Mangal, Nadi & Bhakoot — conflicts that silently destroy marriages",
  km_negEnergyTitle:   "Negative Energy",
  km_negEnergyDesc:    "Hidden doshas even your astrologer may have missed — don't ignore this",
  km_strChalTitle:     "Strengths & Challenges",
  km_strChalDesc:      "What will keep you together — and what may quietly pull you apart",
  km_remAdvTitle:      "Remedies & Advice",
  km_remAdvDesc:       "Exact pujas, stones & mantras to remove obstacles before they grow",

  km_marriageTime:     "Marriage Timing",
  km_childPlan:        "Child Planning",
  km_finCompat:        "Financial Compat",
  km_lifeStab:         "Life Stability",
  km_finHarmony:       "Financial Harmony",
  km_familyAccept:     "Family Acceptance",

  km_karmRelTitle:     "Karmic Relationship Check",
  km_karmRelDesc:      "Are you meant to meet in this lifetime?",
  km_pastLifeTitle:    "Past Life Connection",
  km_pastLifeDesc:     "Spiritual bond from a previous birth",
  km_divorceTitle:     "Divorce / Separation Risk",
  km_divorceDesc:      "Probability based on planetary conflict",
  km_loyaltyTitle:     "Loyalty & Trust Index",
  km_loyaltyDesc:      "Chances of betrayal or long-term loyalty",

  km_badgeMostImp:     "MOST IMPORTANT",
  km_badgeCritCheck:   "CRITICAL CHECK",
  km_badgeDecCard:     "DECISION CARD",
  km_badgeSecret:      "SECRET",

  km_gradeExcellent:   "Excellent",
  km_gradeVeryGood:    "Very Good",
  km_gradeAverage:     "Average",
  km_gradeBelowAvg:    "Below Avg",
  km_gradeLowMatch:    "Low Match",

  km_kutaSahi:         "Match",
  km_kutaAnmatch:      "Mismatch",
  km_kutaDono:         "Both",

  km_emotionalBond:    "Emotional Bond",
  km_mentalConn:       "Mental Connection",
  km_intimacyHarm:     "Intimacy Harmony",
  km_communication:    "Communication",
  km_natureTemp:       "Nature & Temperament",
  km_socialAlign:      "Social Alignment",
  km_lifestyleHarm:    "Lifestyle Harmony",
  km_physicalHarm:     "Physical Harmony",
  km_energeticAttr:    "Energetic Attraction",

  km_compMismatch:     "Compatibility Mismatch",
  km_doshaConflict:    "Dosha Conflict",
  km_longTermStab:     "Long-term Stability",
  km_nadiDosh:         "Nadi Dosh",
  km_bhakootDosh:      "Bhakoot Dosh",
  km_ganaDosh:         "Gana Dosh",
  km_grahaMaitri:      "Graha Maitri",

  km_onePartMang:      "One partner is Manglik",
  km_noMangConf:       "No Manglik conflict",

  km_natTimingExp:     "Natural timing expected",
  km_slightPatience:   "Slight patience recommended",
  km_medConsAdv:       "Medical/expert consultation advised",
  km_strongFinAlign:   "Strong financial alignment",
  km_modBudgetHelp:    "Moderate — budget planning helps",
  km_highlyLikely:     "Highly likely",
  km_mayNeedTime:      "May need time and effort",
  km_marrAusp:         "2025–2026 auspicious",
  km_marrModerate:     "2026–2027 moderate",
  km_marrDelay:        "Delay advised — seek guidance",

  km_riskLow:          "Low",
  km_riskModerate:     "Moderate",
  km_riskHigh:         "High",

  km_deepKarmTie:      "Deep karmic tie",
  km_growConn:         "Growing connection",
  km_posPastLife:      "Positive past life",
  km_neutralKarma:     "Neutral karma",

  km_planFriendStrong: "Planetary friendship is strong",
  km_sharedEnergies:   "Shared planetary energies",
  km_taraFav:          "Tara nakshatra is favourable",
  km_modTaraDest:      "Moderate tara destiny",
  km_bhakSubh:         "Bhakoot shubh — no rashi conflict",
  km_rashiAlign:       "Rashi energies align",

  km_nadiHealth:       "Nadi dosh — health awareness needed",
  km_minorTempDiff:    "Minor temperament differences",
  km_ganaClash:        "Gana clash — nature divergence",
  km_commPracNeeded:   "Communication practice needed",
  km_bhakTimeCaut:     "Bhakoot dosh — timing caution",
  km_patienceConfl:    "Some patience during conflicts",
  km_yoniMismatch:     "Yoni mismatch — energy adjustment",
  km_qualityTimeNeeded:"Regular quality time needed",

  km_pastLifeScore:    "Past Life Connection Score",
  km_ancestKarma:      "Ancestral Karma Patterns",
  km_nakDream:         "Nakshatra Dream Compatibility",
  km_advDoshaRev:      "Advanced Dosha Reversal Plan",

  km_unlockComplete:   "Unlock Complete Report",
  km_realTimeAnalysis: "Real-time analysis based on your birth chart",
  km_secFutTimeline:   "FUTURE TIMELINE",
  km_secSoulKarma:     "SOUL & KARMA ANALYSIS",
  pe_otherProfiles:   "OTHER PROFILES",
  pe_recentlyDeleted: "Recently Deleted",
  pe_noKundliYet:     "No Kundli Yet",
  pe_manageProfile:   "Manage your profile & family members",
  pe_tabKundli:       "Kundli",
  pe_tabPersonal:     "Personal Details",
  pe_lblCosmoId:      "USER ID",
  pe_cosmoIdHint:     "Your unique Cosmic Lens ID — assigned when you join.",
  pe_lblGmail:        "GMAIL",
  pe_lblPhone:        "MOBILE NUMBER",
  pe_phPhone:         "+91 98765 43210",
  pe_savePersonal:    "Save",
  pe_personalSaved:   "Saved",
  pe_nameLockedHint:  "Name can only be set once.",
  pe_phoneLockedHint: "Mobile can only be added once.",
  pe_gmailLockedHint: "From your Google sign-in — cannot be changed.",
  pe_loginRequired:   "Sign in to manage personal details.",

  pn_computing:       "Computing…",
  pn_dataSource:      "Swiss Ephemeris · Lahiri",
  pn_offline:         "Offline · approx values",
  pn_today:           "Today",
  pn_parso:           "Day after",
  pn_auspicious:      "TODAY'S AUSPICIOUSNESS",
  pn_megaFestival:    "Major Festival",
  pn_bNational:       "National",
  pn_bVrat:           "Vrat",
  pn_bMuhurat:        "Muhurat",
  pn_bandExcellent:   "Excellent",
  pn_bandGood:        "Good",
  pn_bandMixed:       "Mixed",
  pn_bandCaution:     "Caution",
  pn_tabToday:        "Today",
  pn_tabMuhurat:      "Muhurat",
  pn_tabGochar:       "Transits",
  pn_tabVrat:         "Ekadashi",
  pn_tabVivah:        "Marriage",
  pn_ekadashiSub:     "Ekadashi at sunrise · next 5 years",
  pn_ekadashiCount:   "Ekadashi (sunrise tithi) · next 5 years · {n} dates",
  pn_ekadashiNote:    "Two Ekadashis per lunar month; a Gregorian month may show one or two.",
  pn_vivahCount:      "{n} verified vivah days · next 5 years",
  pn_gocharBundled:   "Legacy /api/panchang response — transits are not bundled there.",
  pn_currentMonth:    "CURRENT MONTH",
  pn_noEkadashiMonth: "No Ekadashi this month",
  pn_tagToday:        "Today",
  pn_pakshaWord:      "paksha",
  pn_ekadashiTodayHdr:"TODAY'S EKADASHI VRAT",
  pn_tarabalaHdr:     "YOUR TARABALA / CHANDRABALA",
  pn_tarabalaHint:    "Complete your kundli in profile for Tarabala.",
  pn_loadPanchang:    "Loading Panchang…",
  pn_loadEkadashi:    "Calculating Ekadashi…",
  pn_loadFail:        "Could not load Panchang — check server",
  pn_brahmaMuhurta:   "Brahma Muhurta",
  pn_gulika:          "Gulika Kaal",
  pn_abhijit:         "Abhijit Muhurat",
  pn_muhuratFail:     "Muhurat could not load — set your location",
  pn_muhuratLoc:      "From sunrise–sunset at your location",
  pn_gocharFail:      "Transits could not load",
  pn_gocharDeploy:    "Server needs an update — deploy latest API for /api/panchang/gochar",
  pn_gocharApiFail:   "Could not reach API — restart Metro and try again",
  pn_vivahSub:        "Drik vivah muhurat · sunrise tithi · lagna windows · 5 years",
  pn_vivahEmpty:      "No highly favorable marriage days in this range",
  pn_vivahLoading:    "Scanning vivah muhurat (year {y}/{t})…",
  pn_vivahWindow:     "Ceremony window",
  pn_vivahConf:       "confidence",
  pn_vivahCoupleHint: "Add a second profile with kundli for couple tarabala.",
  pn_vivahBlockedChaturmas: "Chaturmas (Jul–Oct) — classical vivah not recommended. Sun in Kark–Tula; resumes when Sun enters Vrishchik (~Nov).",
  pn_vivahBlockedMeena:     "Meena maas (Feb–Mar) — classical vivah window closed.",
  pn_planetSun:       "Sun",
  pn_planetMoon:      "Moon",
  pn_planetMars:      "Mars",
  pn_planetMercury:   "Mercury",
  pn_planetJupiter:   "Jupiter",
  pn_planetVenus:     "Venus",
  pn_planetSaturn:    "Saturn",
  pn_planetRahu:      "Rahu",
  pn_planetKetu:      "Ketu",
  pn_motionRetro:     "Retrograde",

  nm_proTools:        "PRO+ TOOLS",
  nm_premium:         "PREMIUM",
  nm_lifeMastery:     "Numerology Pro Report",
  nm_yourNumbers:     "YOUR NUMBERS",
  nm_yourNumbersHint: "(at least one)",
  nm_whatsInside:     "WHAT'S INSIDE",
  nm_opening:         "Opening…",
  nm_generateBtn:     "Generate Numerology Pro Report",

  cr_pageTitle:       "Career Analysis",
  cr_loading:         "Reading your chart…",
  cr_loginRequired:   "Please log in to view your career analysis.",
  cr_addProfile:      "Add Birth Details",
  cr_scoreLabel:      "CAREER SCORE",
  cr_strongPhase:     "Strong Phase",
  cr_cautionPhase:    "Caution Phase",
  cr_mixedPhase:      "Mixed Phase",
  cr_quickReading:    "Quick Reading",
  cr_hiddenInsight:   "HIDDEN INSIGHT",
  cr_proCta:          "Unlock full career analysis with Pro",
  cr_upgradeBtn:      "Upgrade to Pro",
  cr_houses:          "Career Houses",
  cr_lord:            "Lord:",
  cr_inHouse:         "In house:",
  cr_planets:         "Career Planets",
  cr_dasha:           "Current Dasha Impact",
  cr_mahadasha:       "Mahadasha",
  cr_antardasha:      "Antardasha",
  cr_ends:            "Ends",
  cr_transit:         "Live Planetary Transit",
  cr_growth:          "Career Growth Periods",
  cr_jobChange:       "Job Change Timing",
  cr_struggle:        "Struggle Phases & Hidden Risks",
  cr_reasoning:       "Why This Reading",
  cr_pathTitle:       "Job vs Business",
  cr_jobLabel:        "Job",
  cr_businessLabel:   "Business",
  cr_pathConfidence:  "Chart confidence",
  cr_pathMode:        "Career mode",
  cr_bestOptions:     "Best suitable career options",
  cr_topStrengths:    "Top strengths",
  cr_weakness:        "Weakness",
  cr_risk:            "Risk",

  hl_pageTitle:       "Health Analysis",
  hl_loginRequired:   "Please log in to view your health analysis.",
  hl_healthyPhase:    "Healthy Phase",
  hl_careNeeded:      "Care Needed",
  hl_mixedPhase:      "Mixed Phase",
  hl_scoreLabel:      "HEALTH SCORE",
  hl_riskLabel:       "Risk:",
  hl_houses:          "Health Houses",
  hl_planets:         "Health Planets",
  hl_riskPeriods:     "Risk Periods",
  hl_nature:          "Nature of Issues",
  hl_recovery:        "Recovery Strength",
  hl_prevent:         "Preventive Guidance",
  hl_organs:          "Vulnerable Body Areas",
  hl_remedies:        "Remedies (Mantra & Lifestyle)",

  fn_pageTitle:       "Finance Analysis",
  fn_growthPhase:     "Growth Phase",
  fn_cautionPhase:    "Caution Phase",
  fn_stablePhase:     "Stable Phase",
  fn_scoreLabel:      "FINANCE SCORE",
  fn_houses:          "Wealth Houses",
  fn_planets:         "Wealth Planets",
  fn_inflow:          "Money Inflow Periods",
  fn_expense:         "Expense / Loss Phases",
  fn_invest:          "Investment Opportunities",
  fn_sudden:          "Sudden Gain / Loss Chances",
  fn_stability:       "Wealth Stability",
  fn_income:          "Income Sources",

  rl_loveTitle:       "Love Reality Check",
  rl_loveSub:         "Reveal the hidden truth about your relationship",
  rl_mostUsed:        "Most Used",
  rl_loveDesc:        "For current relationships & BF/GF",
  rl_marriageTitle:   "Marriage Compatibility",
  rl_marriageSub:     "Soul Sync, Attraction Match",
  rl_deepBadge:       "Deep Analysis",
  rl_partnerTitle:    "Future Partner Portrait",
  rl_partnerSub:      "Form, nature & direction",
  rl_partnerDesc:     "A divine glimpse of your life partner from your kundli",
  rl_newBadge:        "NEW · Cosmic Portrait",
  rl_pageHeader:      "Relationship",
  rl_selfLabel:       "You",
  rl_partnerSelect:   "Select Partner",
  rl_change:          "Change",

  mr_loginRequired:   "Login required to view reports.",
  mr_loadError:       "Could not load your reports.",
  mr_networkError:    "Network error.",
  mr_waLinkPrefix:    "Open report:",
  mr_waErrorTitle:    "WhatsApp not available",
  mr_openPdf:         "Open PDF",
  mr_whatsapp:        "WhatsApp",
  mr_pageTitle:       "My Reports",
  mr_loading:         "Loading your reports…",
  mr_emptyTitle:      "No reports yet",
  mr_footer:          "Powered by Advanced Cosmic Intelligence",

  mk_savedCount:      "kundli saved",
  mk_emptyTitle:      "No Kundli Yet",
  mk_emptyDesc:       "Add a profile with birth details to generate kundli",
  mk_addNew:          "Add New Kundli",
  mk_primary:         "PRIMARY",
  mk_deleteTitle:     "Delete Kundli?",
  mk_deleteDesc:      "Kundli will be permanently deleted. This action cannot be undone.",
  mk_cancel:          "Cancel",
  mk_delete:          "Delete",

  mr_kindHomePro:     "Home AstroVastu PRO",
  mr_kindShop:        "Business Vastu — Shop",
  mr_kindOffice:      "Business Vastu — Office",
  mr_kindFactory:     "Business Vastu — Factory",
  mr_kindBusiness:    "Business Vastu",

  rl_kundliReqTitle:        "Kundli required",
  rl_kundliReqBoth:         "Both your kundli and partner's kundli are required. Please create both kundlis from the Kundli screen first.",
  rl_kundliReqSelf:         "Your kundli is not ready. Please generate it from the Kundli screen first.",
  rl_kundliReqSelectFirst:  "Please select your partner above to proceed.",
  rl_kundliReqPartnerMissing: "Partner does not have a kundli yet. Please create their kundli from the Kundli screen first.",
  rl_kundliReqAddBtn:       "Add Kundli",
  rl_kundliReqCancel:       "Cancel",

  nm_wi1Title:  "Life Blueprint Card",       nm_wi1Sub:  "Core personality + 2026 focus + biggest strength/challenge",
  nm_wi2Title:  "Who You Are — Identity",    nm_wi2Sub:  "3-paragraph story + 5 hidden strengths + 5 challenges",
  nm_wi3Title:  "Career Blueprint",          nm_wi3Sub:  "Best fields, common mistakes, growth timing, money pattern",
  nm_wi4Title:  "Love Pattern — Deep",       nm_wi4Sub:  "Relationship style, breakup triggers, ideal partner number",
  nm_wi5Title:  "Health & Spiritual Path",   nm_wi5Sub:  "Body signals + dharma + mantra + donation schedule",
  nm_wi6Title:  "Risk Alerts + Golden Period", nm_wi6Sub: "5 specific risks + when to make biggest moves",
  nm_wi7Title:  "Mobile Number — Deep",      nm_wi7Sub:  "Why · Impact · Action format + Cheiro last-4 + alternatives",
  nm_wi8Title:  "Vehicle Number — Deep",     nm_wi8Sub:  "Why · Impact · Action + favourable plate suggestions",
  nm_wi9Title:  "House Number — Deep",       nm_wi9Sub:  "Why · Impact · Action + remedy schedule",
  nm_wi10Title: "Compatibility Matrix",      nm_wi10Sub: "Your Driver vs all 1-9 (friend/enemy/neutral)",
  nm_wi11Title: "Name Numerology + Letters", nm_wi11Sub: "Pythagorean + Chaldean + letter-by-letter breakdown",
  nm_wi12Title: "Signature & 90-Day Plan",   nm_wi12Sub: "Signature design + step-by-step implementation",

  fc_demo:              "Demo",
  fc_dailyEnergyScore:  "Daily Energy Score",
  fc_moonRashi:         "Transit Moon",
  fc_paksha:            "Paksha",
  fc_energy:            "Energy",
  fc_activeDasha:       "Active Dasha",

  sub_active:           "ACTIVE",
  sub_upgradeBtn:       "Upgrade to Pro 🔓",
  sub_getBasic:         "Get Basic",
  sub_free:             "FREE",
  sub_alwaysFree:       "Always free",
  sub_cmpJyotishQ:      "Jyotish Questions",
  sub_cmpMarriage:      "Marriage Compat",
  sub_cmpTimeline:      "Future Timeline",
  sub_cmpDasha:         "Dasha Analysis",
  sub_cmpKarmic:        "Karmic Insights",
  sub_cmpPdf:           "PDF Report",
  sub_cmpProfiles:      "Saved Profiles",

  da_energyLevels:      "Energy Levels",
  da_energyGood:        "Good",
  da_energyNeutral:     "Neutral",
  da_energyChallenging: "Challenging",

  pe_relSelf:      "Self",
  pe_relHusband:   "Husband",
  pe_relWife:      "Wife",
  pe_relSon:       "Son",
  pe_relDaughter:  "Daughter",
  pe_relFather:    "Father",
  pe_relMother:    "Mother",
  pe_relBrother:   "Brother",
  pe_relSister:    "Sister",
  pe_relFriend:    "Friend",
  pe_relOther:     "Other",

  sub_planBasicName:    "Basic",
  sub_planProName:      "Pro",
  sub_planBasicTag:     "Essential Vedic guidance",
  sub_planProTag:       "Full power Vedic insights",

  sub_bF1: "10 Jyotish Questions / day",
  sub_bF2: "Marriage Compatibility (Basic)",
  sub_bF3: "Love Compatibility (Basic)",
  sub_bF4: "Career, Health, Finance — short summary",
  sub_bF5: "Future Timeline — 1 month",
  sub_bF6: "5 saved profiles",

  sub_bL1: "Unlimited Questions",
  sub_bL2: "Deep analysis with reasoning",
  sub_bL3: "Full 6-month timeline",
  sub_bL4: "Karmic insights & PDF report",

  sub_pF1: "Unlimited Jyotish Questions",
  sub_pF2: "Marriage & Love — Full deep analysis",
  sub_pF3: "Career, Health, Finance — Detailed",
  sub_pF4: "Future Timeline — 6 months full",
  sub_pF5: "D1 + D9 chart analysis",
  sub_pF6: "Dasha (MD + AD + PD) full breakdown",
  sub_pF7: "Karmic patterns & hidden insights",
  sub_pF8: "PDF report download",
  sub_pF9: "Unlimited saved profiles",

  vu_camSub:     "Take photo instantly",
  vu_galSub:     "Choose a saved photo",
  vu_roomPicker: "Choose room type",
  vu_review:     "Review & Submit",
  vu_reviewSub:  "Confirm your captures, then run Deep Scan.",
  vu_tabBasic:   "Basic",
  vu_tabPro:     "Pro",
  vu_introBody:  "Vastu Shastra is an ancient Indian science of architecture. Correct directions bring positive energy, happiness, health, and prosperity to your home.",

  // ── kundli-milan additional (km2_*) ──
  km2_secRiskScan:        "RELATIONSHIP RISK SCAN",
  km2_secPersMatch:       "PERSONALITY MATCH",
  km2_secIntimacyComp:    "INTIMACY COMPATIBILITY",
  km2_secNegEnergy:       "NEGATIVE ENERGY CHECK",
  km2_chipClear:          "Clear",
  km2_chipMild:           "Mild",
  km2_chipPresent:        "Present",
  km2_strengthsHdr:       "STRENGTHS 💚",
  km2_challengesHdr:      "CHALLENGES ⚡",
  km2_persExcellent:      "Excellent — both share similar life approach and values.",
  km2_persModerate:       "Moderate — differences exist but can be harmonised with effort.",
  km2_persChallenging:    "Challenging — temperament differences need active work.",
  km2_yoniExceptional:    "Same Yoni — exceptional physical and energetic alignment.",
  km2_yoniComplementary:  "Complementary energies — good compatibility with some adjustments.",
  km2_yoniDifferent:      "Different energies — patience and understanding will strengthen this bond.",
  km2_concernSing:        "Concern",
  km2_concernPlural:      "Concerns",
  km2_concernsFound:      "Found",
  km2_negPatExcell:       "Excellent — no major negative patterns.",
  km2_negPatMinor:        "Minor concerns — manageable with awareness.",
  km2_negPatMulti:        "Multiple concerns — remedies strongly advised.",
  km2_doshDetect:         "Dosh Detected",
  km2_nadiAuspProgeny:    "Nadi alag — auspicious progeny",
  km2_nadiDeepEmpathy:    "Nadi matched — deep empathy",
  km2_remKumbhVivah:      "Kumbh Vivah or Mangal puja recommended before marriage.",
  km2_remEkadashi:        "Fast on Ekadashi — avoid Nadi imbalance with Shiva puja.",
  km2_remChandraMantra:   "Chant Chandra mantra — Om Chandraya Namah 108 times.",
  km2_remRudrabhishek:    "Perform Rudrabhishek together before marriage.",
  km2_remGemstones:       "Both should wear compatible gemstones — consult a Jyotishi.",
  km2_remSunderkand:      "Joint puja and regular reading of Sunderkand will strengthen bond.",
  km2_fvExceptional:      "Exceptional match. Stars align strongly in your favour. A joyful and fulfilling union is indicated.",
  km2_fvVeryPositive:     "Very positive match. With mutual respect and love, this relationship has great potential.",
  km2_fvModerate:         "Moderate match. Awareness, effort, and expert guidance will help this bond flourish.",
  km2_fvChallenging:      "Challenging match. Remedies, patience, and consulting a Jyotishi are strongly advised before proceeding.",
  km2_ashtakootScoreLbl:  "Ashtakoot Score",
  km2_concernDetSuffix:   "detected",
  km2_addBothFirst:       "Add Both Kundlis First",
  km2_unlockFullAnal:     "Unlock Full Analysis",
  km2_youPlaceholder:     "You",
  km2_birthMissingBody:   "Both partners need complete birth data (date, time, place) for accurate matching.",
  km2_calcFailedBody:     "Could not calculate match. Please try again.",
  km2_matchingWith:       "MATCHING WITH",
  km3_yourPersAnalysis:   "Your Personalised Analysis",
  km3_insEmotional:       "Emotional Compatibility",
  km3_insMarriage:        "Marriage Future",
  km3_insRisks:           "Hidden Risks",
  km3_insKarmic:          "Karmic Bond",
  km3_insStrength:        "Strength Factors",
  km3_insTriggers:        "Conflict Triggers",
  km3_insStability:       "Long-term Stability",
  km3_insFinal:           "Final Outcome",
  km3_unlEmotional:       "Emotional Compatibility — what truly connects or disconnects you",
  km3_unlMarriage:        "Marriage Future — real direction of this relationship",
  km3_unlRisks:           "Hidden Risks — patterns creating problems",
  km3_unlKarmic:          "Karmic Bond — deeper purpose of this connection",
  km3_unlStrength:        "Strength Factors — what holds this together",
  km3_unlTriggers:        "Conflict Triggers — what causes repeated issues",
  km3_unlStability:       "Long-term Stability — will it last or break",
  km3_unlFinal:           "Final Outcome — actual future direction",
  km3_nadiAlag:           "Different nadi — auspicious for healthy progeny and long life together.",
  km3_nadiSama:           "Same nadi — strong emotional mirroring, some health caution advised.",
  km3_personFallback:     "Person",
  km3_errTryAgain:        "Error. Please try again.",
  km3_proTrailMore:       "Full detail and remedy will appear in the Pro report.",
  km3_kundliBased:        "This analysis is based on your real kundli and reveals patterns that directly affect your relationship.",
  km3_truthsBelow:        "The most important truths of this connection are hidden below.",
  km3_unlockToSee:        "Unlock to see the full picture.",
  km3_whatYouUnlock:      "WHAT YOU WILL UNLOCK",
  km3_lockedPreview:      "🔒 LOCKED PREVIEW",
  km3_addBothToUnlock:    "Add Both Kundlis to Unlock Preview",
  km3_addBothSubtext:     "Add birth details for both — your personal hooks will then be generated",

  // ── Phase 2 screen localization ──
  vu_alPermNeeded: "Permission needed",
  vu_alGalleryMsg: "Please allow photo gallery access so Vastu Drishti can see your room.",
  vu_alCameraMsg: "Please allow camera access to take a photo immediately.",
  vu_alError: "Error",
  vu_alPhotoFailed: "Could not take the photo.",
  vu_alCamFailed: "Could not open the camera.",
  vu_alPhotoMissing: "Photo missing",
  vu_alPhotoMissingMsg: "Please first take a room photo or pick from gallery.",
  vu_alScanFailed: "Scan failed",
  vu_alScanFailedMsg: "Could not analyze photo. Please retry in good lighting.",
  vu_alDailyLimitMsg: "Today's free limit is over — try again tomorrow or get Pro.",
  vu_alStepHint: "Move ahead step by step.",
  ku_ashtakWhat: "What is Ashtakavarga?",
  ku_ashtakWhatBody: "Each planet awards benefic/malefic points to all 12 signs from 8 houses. SAV = total of all 7 planets. More points = stronger sign.",
  ku_approxTransit: "Approximate Transit",
  ku_houseLabel: "House",
  ku_bavStrong: "Strong",
  ku_bavGood: "Good",
  ku_bavAverage: "Average",
  ku_bavWeak: "Weak",
  ku_bavLegStrong: "7-8 (Strong)",
  ku_bavLegGood: "5-6 (Good)",
  ku_bavLegAverage: "3-4 (Average)",
  ku_bavLegWeak: "0-2 (Weak)",
  ku_transitDisclaimer: "These transits are computed from mean orbital motion — useful for broad guidance only.",
  ku_btnKundli: "Kundli",
  ku_btnAshtak: "Ashtakavarga",
  ku_btnNavatara: "Navatara",
  ku_btnJaimini: "Jaimini",
  ku_btnTransit: "Transit",
  ku_btnKP: "KP",
  ku_secDashaTimeline: "DASHA TIMELINE",
  ku_secAshtakavarga: "ASHTAKAVARGA",
  ku_secNavatara9Tara: "NAVATARA — 9 TARA",
  ku_secJaiminiKarakas: "JAIMINI KARAKAS",
  ku_secGrahaTransit: "GRAHA TRANSIT",
  ku_secKpPaddhati: "KP PADDHATI",
  ku_snapAscendant: "ASCENDANT (LAGNA)",
  ku_snapMoonSign: "MOON SIGN (RASHI)",
  ku_snapNakshatra: "NAKSHATRA",
  ku_snapNakshatraLord: "NAKSHATRA LORD",
  ku_snapDashaBalance: "DASHA BALANCE",
  ku_snapLiveMoonTransit: "LIVE MOON TRANSIT",
  ku_padaLabel: "Pada",
  ku_jaiminiDegPre: "Degree within sign:",
  ku_jaiminiDegSuf: "highest in chart",
  ku_kpDesc: "Krishnamurti Paddhati uses proportional sub-divisions of Vimshottari dasha for precision timing of events.",
  ku_kpFooter: "For any event, check: relationship of Star-lord and Sub-lord. If 3 lords agree → event is confirmed.",
  ku_kpStar: "Star",
  ku_kpSub: "Sub",
  ku_kpSubSub: "Sub-Sub",
  ku_kpAsc: "Asc",
  ku_savHeading: "Sarvashtakavarga",
  pr_tabIndia: "India",
  pr_tabGlobal: "Global",
  pr_active: "ACTIVE",
  pr_free: "FREE",
  pr_freePlan: "FREE PLAN",
  pr_myData: "MY DATA",
  pr_myKundli: "My Kundli",
  pr_saved: "saved",
  pr_perYear: "year",
  pr_perMonth: "month",
  sub_premiumBadge: "PREMIUM",
  sub_bestValueBadge: "BEST VALUE",
  vu_compassTitle: "Vastu Compass",
  vu_compassSubtitle: "Sacred Direction Finder",
  vu_sensorActive: "SENSOR ACTIVE",
  vu_aligning: "ALIGNING…",
  vu_sensorInactive: "Sensor inactive",
  vu_moveDevice: "Move device to activate",
  vu_idealDirLbl: "Ideal Direction",
  vu_northEast: "North-East",
  vu_tabDos: "Do ✅",
  vu_tabDonts: "Don't ❌",
  vu_tabRemedies: "Remedies 🙏",
  ku_mahadasha: "MAHADASHA",
  ku_antardasha: "ANTARDASHA",
  ku_pratyantardasha: "PRATYANTARDASHA",
  ku_mahaTimeline: "MAHADASHA TIMELINE",
  ku_activeNow: "● ACTIVE NOW",
  ku_active: "ACTIVE",
  ku_yearsSuffix: "years",
  ku_whatNavatara: "What is Navatara?",
  ku_navataraDesc: "Starting from the Moon's nakshatra, 27 nakshatras are grouped into 9-star cycles called Tara.",
  ku_chandraNakBase: "CHANDRA NAKSHATRA (BASE)",
  ku_whatJaimini: "What are Jaimini Chara Karakas?",
  ku_jaiminiDesc: "In Jaimini Jyotish, 7 planets get karaka roles based on their rashi-degrees. The planet with the highest degree becomes Atmakaraka.",
  ku_atmakaraka: "ATMAKARAKA",
  ku_jaiminiLagna: "Jaimini Lagna",
  ku_jaiminiLagnaDesc: "Atmakaraka's rashi forms a special Jaimini Lagna. AK's navamsha position shows the soul's spiritual path. For full analysis, consult an astrologer.",
  ku_liveChandraTransit: "LIVE — CHANDRA TRANSIT",
  ku_natalConj: "NATAL CONJ",
  ku_whatKP: "What is KP Paddhati?",
  ku_kpSignificators: "KP Significators",
  ku_birthChartSnap: "BIRTH CHART SNAPSHOT",
  ku_planetPosition: "Planet Position",
  ku_planetPositionSub: "Live planetary degrees and rashi",
  ku_gemstones: "Gemstones",
  ku_gemstonesSub: "Navratna gems for each graha — finger, metal & benefits",
  ku_gemstonesBadge: "NAVRATNA GEMS",
  ku_gemstonesHero: "Vedic Gemstone Guide",
  ku_gemstonesAll: "All Navratna Gems",
  gs_buyTitle: "Buy Gemstone",
  gs_youSave: "You save",
  gs_offerSelf: "Direct purchase",
  gs_offerReferral: "Referral offer",
  gs_selfBuy: "Buy yourself",
  gs_referralBuy: "Have a referral code?",
  gs_flatOff: "flat off",
  gs_referrerGets: "Referrer gets",
  gs_referralPlaceholder: "Enter code e.g. CL123",
  gs_selfReferralErr: "You cannot use your own referral code.",
  gs_referralHint: "Referrer reward is paid to bank after delivery + 7 days. Self-buy and referral discounts cannot be combined.",
  gs_yourReferral: "Your referral code",
  gs_referralEarn: "Earn",
  gs_afterDelivery: "in bank after friend's order is delivered.",
  gs_payNow: "Pay",
  gs_disclaimer: "Natural gemstones — consult a Jyotishi before wearing. Referral payout after verified delivery.",
  gs_shopTitle: "Certified Gems",
  gs_buyCta: "Buy Now",
  gs_selectRatti: "Ratti",
  gs_ratti: "Ratti",
  gs_shopFrom: "from",
  gs_shopSizes: "5 – 10 Ratti · Certified Ceylon",
  gs_certified: "Lab Certified",
  gs_benefitTag: "Attracts Wealth & Guru Blessings",
  gs_whatsappPhotos: "Get real photos & videos on WhatsApp before you pay",
  gs_whatsappCta: "Request on WhatsApp",
  gs_productSpecs: "Product specifications",
  gs_howToWear: "How to wear",
  gs_careTitle: "Gemstone care",
  gs_whyWear: "Why Ceylon Pukhraj?",
  gs_deliveryNote: "Prepaid orders ship on priority · insured delivery in 7–10 days",
  gs_authenticPromise: "Natural Ceylon origin · certificate with every order · unheated & untreated",
  ku_dailyAlertsLink: "Daily Alerts",
  ku_dailyAlertsLinkSub: "4-day planetary guidance",
  ku_house: "House",
  ku_nakshatraLabel: "Nakshatra",
  vu_alNetError: "Network error",
  vu_alNetErrorMsg: "Please check your internet connection.",
  vu_alCompassCalib: "Compass calibrating",
  vu_alCompassCalibMsg: "Move your phone in an infinity (∞) shape, then the compass will be ready.",
  vu_alWallDirection: "Face the correct direction",
  vu_alCamPermNeeded: "Camera permission needed",
  vu_alGalPermNeeded: "Gallery permission needed",
  vu_alPhotoUnreadable: "Could not read the photo",
  vu_alFloorUploadFail: "Floor plan could not be uploaded.",
  vu_alWallPhotoFirst: "First take a photo of this wall",
  vu_alMin2Walls: "Capture at least 2 walls",
  vu_alLoginReq: "Login required",
  vu_alLoginReqMsg: "Login is required for Deep Scan — this is advanced multi-photo analysis.",
  vu_alServerNoTalk: "Could not contact the server.",
  vu_alDailyLimit: "Daily limit reached",
  vu_alDeepScanFail: "Deep scan failed",
  vu_alTryAgain: "Try again.",
  prof_alNotifOff: "Notifications off",
  prof_alNotifOffMsg: "Permission denied. Open Phone Settings → Cosmic Lens → Notifications and enable them.",
  prof_alTestSent: "Test sent ✨",
  prof_alTestSentMsg: "Notification will appear in 1-2 seconds.",
  prof_alSendFail: "Send failed",
  prof_alTokenMissing: "Token not registered. Toggle off→on.",
  ds_title: "Dosh Analysis",
  ds_subtitle: "Complete Dosha Analysis ({count} Doshas)",
  ds_demo: "Demo",
  ds_totalDosh: "Total Dosh",
  ds_present: "Present",
  ds_notPresent: "Not Present",
  ds_scanning: "Scanning…",
  ds_analyzing: "Analysing your kundli…",
  ds_checking: "Checking all {count} dosh conditions",
  ds_analysis: "Dosh Analysis",
  ds_active: "Active",
  ds_mild: "Mild",
  ds_clear: "Clear",
  ds_detected: "{found} of {total} doshas detected",
  ds_remedies: "REMEDIES",
  ds_disclaimer: "Dosh analysis is based on classical Vedic astrology principles. Always consult a qualified Jyotishi for important life decisions.",
  prof_madeWith: "Cosmic Lens v1.0.0 · Made with ♥ in India",
  sub_avPricing: "AstroVastu Pricing",
  sub_avSubtitle: "Vastu products — all one-time, no monthly (because Vastu is set once)",
  sub_proSubsLabel: "Pro subscribers",
  sub_proGetSuffix: "get",
  sub_offSuffix: "off on all AstroVastu purchases above.",
  sub_openAv: "Open AstroVastu",
  car_karmaStrength: "Career karma strength",
  fn_hidden: "HIDDEN INSIGHT",
  fn_wealthKarma: "Wealth karma score",
  hl_hidden: "HIDDEN INSIGHT",
  dl_luckyColor: "Lucky Color",
  dl_luckyNumbers: "Lucky Numbers",
  rl_addPartner: "Add New Partner",
  pe2_cancel: "Cancel",
  pe2_delete: "Delete",
  pe2_deleteSuffix: "chart data will be permanently deleted.",

  // ── Phase 4 additions ─────────────────────────
  nf_title: "Oops!",
  nf_doesntExist: "This screen doesn't exist.",
  nf_goHome: "Go to home screen!",
  ab_title: "About Cosmic Lens",
  ab_subtitle: "Vedic astrology, modernised",
  ab_secMission: "Our Mission",
  ab_pMission1: "Cosmic Lens brings the timeless wisdom of Vedic Jyotish to your pocket. We combine classical Parashari principles with modern ephemeris computations and expert Jyotish interpretation to give you accurate, accessible, and personal astrological guidance — in your language.",
  ab_pMission2: "Whether you're curious about your kundli, planning a marriage, exploring career options, or simply seeking daily insight, our mission is to help you navigate life with clarity and intention.",
  ab_secDifferent: "What Makes Us Different",
  ab_pDifferent: "• Calculations use the traditional Lahiri ayanamsa with high-precision Swiss Ephemeris data.\n• Available in 24 languages including 13 Indian regional languages and Hinglish.\n• Honest, transparent pricing — no in-app currency, no surprise charges.\n• Privacy-first — we never sell your kundli or chat data.\n• 7-day free trial so you can experience before paying.",
  ab_secConnect: "Connect With Us",
  ab_lblSupportEmail: "Support Email",
  ab_lblWebsite: "Website",
  ab_secLegal: "Legal & Policies",
  ab_linkPrivacy: "Privacy Policy",
  ab_linkTerms: "Terms of Service",
  ab_linkRefund: "Refund & Cancellation",
  ab_linkDisclaimer: "Astrology Disclaimer",
  ab_linkDelete: "Delete My Account",
  ab_lblAppVersion: "App Version",
  ab_versionFoot: "Made with ♥ in India · © 2026 Cosmic Lens",
  da_title: "Delete Account",
  da_subtitle: "Permanent and irreversible",
  da_calloutDanger: "This action is permanent. Once deleted, your data cannot be recovered.",
  da_secWhatHappens: "What happens when you delete",
  da_wb1: "Your account login (email / mobile / Google) is removed immediately.",
  da_wb2: "All saved kundlis, profiles, and chat history are erased within 30 days.",
  da_wb3: "Active subscriptions are cancelled — no further charges.",
  da_wb4: "Tax invoices for past payments may be retained for 7 years per Indian law (GST records).",
  da_wb5: "You will need to create a new account if you wish to use Cosmic Lens again.",
  da_secBefore: "Before you delete",
  da_pBefore: "Consider these alternatives — they may solve your concern without losing your data:",
  da_bb1: "Cancel subscription only — Profile → Subscription → Cancel. Your account stays free.",
  da_bb2: "Disable notifications — Profile → Notifications → Off.",
  da_bb3: "Need a refund? See our Refund Policy first — we may help.",
  da_bb4: "Privacy concern? Email support@cosmiclens.app.",
  da_secConfirm: "Confirm deletion",
  da_pConfirm: "To proceed, type DELETE in the box below and tap the delete button.",
  da_inputPh: "Type DELETE to confirm",
  da_btnDelete: "Delete My Account Permanently",
  da_btnDeleting: "Deleting…",
  da_btnCancelBack: "Cancel and go back",
  da_secNeedHelp: "Need help instead?",
  da_pNeedHelp: "If you have any concern, we'd love to hear from you before you go. Reach us at support@cosmiclens.app — most issues are resolved within 24 hours.",
  da_alertNotSignedIn: "Not signed in",
  da_alertLoginFirst: "Please log in first.",
  da_alertConfirmTtl: "Delete account permanently?",
  da_alertConfirmMsg: "This action cannot be undone. All your kundlis, profiles, chat history and personal data will be erased within 30 days.",
  da_alertCancel: "Cancel",
  da_alertYesDelete: "Yes, delete forever",
  da_alertDeletedTtl: "Account Deleted",
  da_alertDeletedMsg: "Your account has been permanently deleted. Thank you for using Cosmic Lens.",
  da_alertOk: "OK",
  da_alertFailedTtl: "Deletion failed",
  da_alertFailedMsg: "Please try again or contact support.",
  smf_title: "6-Month Deep Future",
  smf_loadingMsg: "MD/AD/PD chain compute ho raha hai…",
  smf_unavailableTtl: "Future data unavailable",
  smf_tryAgain: "Try again later.",
  smf_kundliFirst: "Please complete your kundli first.",
  smf_activeChain: "Active Dasha Chain",
  smf_lblMaha: "Maha",
  smf_lblAntar: "Antar",
  smf_lblPratyantar: "Pratyantar",
  smf_adWindow: "AD window",
  smf_pdShift: "PD shift",
  smf_lblMD: "MD",
  smf_lblAD: "AD",
  smf_lblPD: "PD",
  smf_rulesPrefix: "Rules",
  smf_sitsIn: "Sits in",
  smf_pdActiveWindow: "Active PD window",
  smf_lifeAreas: "Life Areas this month",
  smf_whyPrefix: "Why",
  smf_opportunities: "Opportunities",
  smf_cautions: "Cautions",
  smf_remedyLabel: "Remedy",
  smf_remedyFocused: "focused",
  smf_generated: "Generated",
  smf_pureEngine: "Pure Vedic engine — MD/AD/PD + house lords + natal placements.",
  smf_areaCareer: "Career",
  smf_areaFinance: "Finance",
  smf_areaHealth: "Health",
  smf_areaRelationship: "Relationship",
  smf_areaSpirituality: "Spirituality",
  dp_title: "🔮 Divya Prashna",
  dp_subtitle: "Ask your question — instant Vedic answer",
  dp_metaCity: "Bhubaneswar, Odisha · Server time",
  dp_quickQuestion: "Quick question",
  dp_orType: "Or type your own question",
  dp_inputPh: "e.g. Will I find my lost phone?",
  dp_btnGetAnswer: "Get Answer",
  dp_alertEmptyTtl: "Write your question",
  dp_alertEmptyMsg: "Write what you want to ask.",
  dp_errNoticeTtl: "⚠️ Notice",
  dp_errQuotaPro: "Today's question limit reached. Upgrade to Pro.",
  dp_errSession: "Session expired. Please log in again.",
  dp_errFetch: "Couldn't fetch answer. Please try again.",
  dp_btnSeeUpgrade: "See upgrade →",
  dp_immatureTitle: "⚠️ Question not yet ripe",
  dp_refPrefix: "Ref",
  dp_retryAfter: "Try again",
  dp_minutesLater: "minutes later",
  dp_chartTitle: "📊 Prashna Chart",
  dp_chartLagna: "Lagna",
  dp_chartPlace: "Place",
  dp_chartCategory: "Category",
  dp_cuspTitle: "🪔 Cusp Analysis",
  dp_houseSuffix: "Bhava",
  dp_subLord: "Sub-Lord",
  dp_starLord: "Star-Lord",
  dp_signifies: "Signifies houses",
  dp_classicalTitle: "📖 Classical Reference",
  dp_cat_stolen: "Will lost item return?",
  dp_cat_partner: "Partner's feelings",
  dp_cat_job: "Will I get the job?",
  dp_cat_marriage: "When will I marry?",
  dp_cat_health: "Will illness be cured?",
  dp_cat_litigation: "Will I win the case?",
  dp_cat_travel: "Will the journey happen?",
  dp_cat_general: "General question",
  dp_pr_stolen: "My gold / money is lost — will it return?",
  dp_pr_partner: "What is my partner thinking about me right now?",
  dp_pr_job: "Will I get this job / new role?",
  dp_pr_marriage: "By when will my marriage happen?",
  dp_pr_health: "Will my / my loved one's illness be cured?",
  dp_pr_litigation: "Will I win my litigation?",
  dp_pr_travel: "Will my planned journey complete successfully?",
  pk_headerTitle: "Prashna Kundli",
  pk_headerSub: "Simple chart Q&A · separate from Ask",
  pk_modeAsk: "Ask Anything",
  pk_modeNumber: "Prashna Kundli",
  pk_initMsg: "🔮 Hello! Ask your question directly. Personal questions use your D1 chart + dasha. General Jyotish theory gets a short simple answer. This is separate from Ask Anything.",
  pk_invalidNumber: "⚠️ Number must be between 1 and 249. Think once more.",
  pk_qLimit: "Today's question limit reached. Upgrade subscription.",
  pk_genErr: "Something went wrong — please try again.",
  pk_netErr: "📡 Network error — check internet and try again.",
  pk_sankhyaPrefix: "Number",
  pk_warnTitle: "Prashna kaal — caution",
  pk_warnDefault: "Take it as guidance, not the final verdict.",
  pk_warnRef: "Source",
  pk_forcedLagna: "Forced Lagna",
  pk_lblRashi: "Rashi",
  pk_lblNakshatra: "Nakshatra",
  pk_cuspKpTitle: "Cusp Analysis (KP Sub-Lord)",
  pk_houseSt: "st",
  pk_houseNd: "nd",
  pk_houseRd: "rd",
  pk_houseTh: "th",
  pk_houseWord: "House",
  pk_subLord: "Sub-Lord",
  pk_timingTitle: "⏳ Timing",
  pk_classicalTitle: "📜 Classical Basis",
  pk_numPlaceholder: "1 — 249",
  pk_numHint: "Think a number",
  pk_qInputPh: "Type your question…",
  pk_cat_stolen: "Item return?",
  pk_cat_partner: "Partner feelings",
  pk_cat_job: "Job?",
  pk_cat_marriage: "Marriage when?",
  pk_cat_health: "Health ok?",
  pk_cat_litigation: "Win case?",
  pk_cat_travel: "Travel?",
  pk_cat_general: "General",
  fr_headerTitle: "Face Reading Pro",
  fr_heroEyebrow: "WORLD'S FIRST",
  fr_heroTitle: "Vedic + Science\nFace Reading Fusion",
  fr_heroSub: "40-page premium PDF report combining 19 ancient & modern frameworks — narrated in storytelling.",
  fr_priceLive: " · Live Now",
  fr_statPages: "pages",
  fr_statSections: "sections",
  fr_statEngines: "engines",
  fr_statLandmarks: "landmarks",
  fr_capInside: "INSIDE YOUR REPORT",
  fr_pv1Title: "Branded Cover",
  fr_pv1Sub: "Your photo · personalized seal",
  fr_pv2Title: "7-Zone Face Map",
  fr_pv2Sub: "Annotated landmarks + callouts",
  fr_pv3Title: "Visual Snapshot",
  fr_pv3Sub: "OCEAN radar + 5-score chart",
  fr_pv4Title: "Celeb Match",
  fr_pv4Sub: "Archetype × element library",
  fr_capEngines: "19 ANALYSIS ENGINES",
  fr_eng1Group: "Cosmic Intelligences",
  fr_eng1Body: "Samudrika Shastra · Mukha Lakshana · Lalat Rekha · Netra Vigyan · Ayurvedic Prakriti · Mian Xiang · 100-Year Age Map · Wu Xing 5 Elements",
  fr_eng2Group: "Scientific Engines",
  fr_eng2Body: "Anthropometry (32 pts) · Symmetry · Golden Ratio (φ) · fWHR · Health Indicators · Big Five OCEAN · First Impression · Phenotype Profile",
  fr_eng3Group: "Fusion Engines",
  fr_eng3Body: "Vedic-Science Cross-Validation · Numerology Combo · Predictive Synthesis (career, marriage, wealth, health)",
  fr_capHow: "HOW IT WORKS",
  fr_step1Title: "Upload 3 selfies",
  fr_step1Body: "Front + left + right profile (guided capture, lighting & angle check)",
  fr_step2Title: "468 landmarks extracted",
  fr_step2Body: "Google Mediapipe — runs on-device for privacy",
  fr_step3Title: "19 engines analyze in parallel",
  fr_step3Body: "~75% real CV measurements · 0% fake or hardcoded data",
  fr_step4Title: "40-page PDF generated",
  fr_step4Body: "Visual charts, face map, narrative · ready in ~45 seconds",
  fr_capBuilt: "BUILT ON",
  fr_honest100: "100% Honest Data",
  fr_honest75: "75% real CV measurements",
  fr_honest20: "20% derived (real numbers + prose)",
  fr_honest5: "5% curated (celeb library, combo titles)",
  fr_honestFoot: "Zero fake or hardcoded readings — everything comes from your actual photo.",
  fr_ctaText: "Start My Face Reading",
  fr_ctaSub: "Upload 3 selfies → 30-60 seconds and a 40-page PDF report on your device.",
  fr_wipBadge: "Coming Soon",
  fr_wipTitle: "Face Reading Pro is being built",
  fr_wipBody: "We're finalizing the Vedic + Science face-reading report and your 40-page PDF. Upload and payment stay paused until launch.",
  fr_wipHint: "Check Life Map again after the next app update.",
  mdFaceReadingSubSoon: "Coming soon · Vedic + Science fusion",
  fu_introEyebrow: "STEP 1 OF 2",
  fu_introTitle: "Upload 3 selfies",
  fu_introSub: "Front + left + right profile. Use good lighting, remove glasses, push hair back from forehead.",
  fu_slotFrontLbl: "Front Selfie",
  fu_slotFrontHint: "Look straight at the camera",
  fu_slotLeftLbl: "Left Profile",
  fu_slotLeftHint: "Show your left side to the camera",
  fu_slotRightLbl: "Right Profile",
  fu_slotRightHint: "Show your right side to the camera",
  fu_addedTap: "Added · tap to change",
  fu_capOptional: "OPTIONAL — BETTER ACCURACY",
  fu_lblAge: "Age",
  fu_phAge: "e.g. 28",
  fu_lblGender: "Gender",
  fu_male: "Male",
  fu_female: "Female",
  fu_lblLanguage: "Language",
  fu_camPermNeeded: "Camera permission needed",
  fu_galPermNeeded: "Gallery permission needed",
  fu_couldNotPick: "Could not pick photo",
  fu_addPhotoTtl: "Add photo",
  fu_addPhotoMsg: "Choose camera or gallery",
  fu_btnCamera: "Camera",
  fu_btnGallery: "Gallery",
  fu_btnCancel: "Cancel",
  fu_addAllFirst: "Add 3 photos first",
  fu_progUpload: "Uploading photos…",
  fu_progAnalyze: "19 engines analysis in progress…",
  fu_progRender: "40-page PDF report being generated…",
  fu_progSub: "This can take ~30-60 seconds. Don't close the app.",
  fu_errSomething: "Something went wrong",
  fu_doneTitle: "Report ready!",
  fu_doneSub: "40-page PDF generated.",
  fu_btnOpenShare: "Open / Share PDF",
  fu_btnAnother: "Generate another report",
  fu_processing: "Processing…",
  fu_btnTryAgain: "Try Again",
  fu_btnGenerate: "Generate My Report",
  fu_legalLine: "Your photos are used for analysis only · auto-deleted after 24 hours · encrypted on server",
  fu_shareNotAvail: "Sharing not available on this device",
  fu_sessIdMissing: "Session ID missing from server",
  fpp_headerTitle: "Cosmic Portrait",
  fpp_heroTitle: "Your Future Life Partner",
  fpp_heroSubMale: "Through 30+ classical rules of your kundli, his form, nature and direction will be revealed — D1, D9 Navamsa, D3 Drekkana, D30 Trimsamsa, KP 7th cuspal sub-lord, Upapada Lagna, Darakaraka, Arudha A7, Vargottama and Ashtakavarga deep analysis.",
  fpp_heroSubFemale: "Through 30+ classical rules of your kundli, her form, nature and direction will be revealed — D1, D9 Navamsa, D3 Drekkana, D30 Trimsamsa, KP 7th cuspal sub-lord, Upapada Lagna, Darakaraka, Arudha A7, Vargottama and Ashtakavarga deep analysis.",
  fpp_primaryKundli: "Primary kundli",
  fpp_btnReveal: "Reveal My Future Partner",
  fpp_warnNoKundli: "Please create your primary kundli first. Profile → Add kundli.",
  fpp_infoTitle: "💎 What this will tell",
  fpp_b1: "Appearance: face, complexion, eyes, hair, body",
  fpp_b2: "Nature: vibe, qualities, strengths of feminine/masculine",
  fpp_b3: "Profession direction (D10 + 7th lord)",
  fpp_b4: "Age difference from you (younger / equal / older)",
  fpp_b5: "Direction they'll come from (East / North / etc.)",
  fpp_b6: "Ashtakavarga 7th bindu — attraction strength",
  fpp_disclaimer1: "* This is a divine glimpse — an artistic depiction of classical signature. Exact match with the actual person not required. Personality, vibe and direction are based on classical rules.",
  fpp_loadingTitle: "Cosmic Portrait being prepared",
  fpp_msgAlign: "Stars are aligning…",
  fpp_msgAlignFull: "Your kundli is aligning with the stars…",
  fpp_msgComputing: "Computing your kundli first…",
  fpp_msgKundliQuota: "Your kundli quota is exhausted. Upgrade subscription.",
  fpp_msgKundliFail: "Could not compute kundli. Check network and try again.",
  fpp_msgTaskExpire: "Task expired. Please start again.",
  fpp_msgTaskIdMiss: "Task ID missing. Please try again.",
  fpp_msgNetSlow: "Network slow. Check internet and try again.",
  fpp_msgStarsBusy: "Stars are busy right now",
  fpp_tipText: "Please wait… The stars are reading the essence of your life partner.\nApprox 15-25 sec.",
  fpp_btnCancel: "Cancel",
  fpp_imgFailed: "Could not generate image.",
  fpp_imgBadge: "✨ COSMIC PORTRAIT — DIVINE GLIMPSE",
  fpp_traitTitle: "🌟 Appearance & Nature",
  fpp_lblFace: "Face",
  fpp_lblComplexion: "Complexion",
  fpp_lblBuild: "Build",
  fpp_lblEyes: "Eyes",
  fpp_lblEyebrows: "Eyebrows",
  fpp_lblNose: "Nose",
  fpp_lblLips: "Lips",
  fpp_lblHair: "Hair",
  fpp_lblVibe: "Vibe",
  fpp_vargottama: "✨ Vargottama amplified — features especially harmonious",
  fpp_practTitle: "🧭 Practical Insights",
  fpp_lblAge: "Age",
  fpp_lblDirection: "Direction",
  fpp_lblProfHint: "Profession hint",
  fpp_lblAttraction: "Attraction",
  fpp_classicalTtl: "📜 Classical Basis",
  fpp_disclaimer2: "* Cosmic Portrait — divine glimpse. This is an artistic analysis based on the 7th house, D9 Navamsa, KP cusp and Jaimini Upapada/Arudha sutras. Exact facial match may or may not occur — personality, vibe and direction will be accurate.",
  fpp_btnRevealAgain: "Reveal Again",
  fpp_errTitle: "Cosmic Portrait not ready yet",
  fpp_errDefault: "Stars are busy right now. Please try again in a while.",
  fpp_errPortraitFail: "Cosmic Portrait could not be prepared right now.",
  fpp_btnTryAgain: "Try Again",
  fpp_alertBirthTtl: "Birth details required",
  fpp_alertBirthMsg: "Please add birth date/time/place to your primary profile first, then reveal Cosmic Portrait.",
  fpp_errTimeout: "Deep stellar analysis is taking longer than expected. Please try again.",
  lg_title: "Legal & Policies",
  lg_subtitle: "Privacy, terms, refunds & disclaimer",
  lg_lastUpdated: "17 April 2026",
  lg_h_privacy: "Privacy Policy",
  lg_p_privacyIntro: "Cosmic Lens (\"we\", \"us\", \"our\") respects your privacy. This Privacy Policy explains what personal information we collect when you use our mobile application and related services (the \"Service\"), how we use it, and the choices you have. By using Cosmic Lens you agree to the practices described below.",
  lg_callout_privacy: "We do NOT sell your personal data. We do not share your kundli, birth details, or chat history with advertisers.",
  lg_s1_title: "1. Information We Collect",
  lg_s1_a: "(a) Account information — name, email address, mobile number (if you sign up with phone), Google account ID (if you use Google Sign-In). Stored securely with hashed passwords (scrypt).",
  lg_s1_b: "(b) Birth & profile data — full name, date of birth, time of birth, place of birth, gender, and language preference. This is the minimum required to compute your Vedic kundli.",
  lg_s1_c: "(c) Generated content — your kundli charts, dashas, compatibility reports, Jyotish question/answer history, and saved profiles.",
  lg_s1_d: "(d) Payment information — handled entirely by our payment processor Cashfree Payments. We only store the order ID, plan, amount, and success/failure status. We never store card numbers, UPI PINs, CVVs, or banking credentials.",
  lg_s1_e: "(e) Device & technical information — device model, OS version, app version, language, time zone, and crash logs. Used purely for diagnostics.",
  lg_s2_title: "2. How We Use Your Information",
  lg_s2_b1: "To create and maintain your account.",
  lg_s2_b2: "To compute your kundli, dashas, doshas, compatibility, and other astrological reports.",
  lg_s2_b3: "To provide Jyotish-based answers to your questions using only your kundli data — not your identity.",
  lg_s2_b4: "To process subscription payments through Cashfree.",
  lg_s2_b5: "To enforce daily question limits and fair-usage rules.",
  lg_s2_b6: "To send you optional notifications (daily horoscope, panchang, muhurat reminders) — you can disable these in Settings.",
  lg_s2_b7: "To prevent fraud, debug crashes, and improve service quality.",
  lg_s2_b8: "To comply with legal obligations.",
  lg_s3_title: "3. Third-Party Services",
  lg_s3_intro: "We share the minimum necessary data with these trusted partners:",
  lg_s3_b1: "Google Sign-In — verifies your identity if you choose Google login. We receive your name, email, and Google ID.",
  lg_s3_b2: "Cashfree Payments (India) — processes UPI, card, and net-banking transactions. PCI-DSS Level 1 compliant.",
  lg_s3_b3: "Expo / Google Play Services — push notification delivery only. No content is read by them.",
  lg_s3_b4: "Cloud hosting (Replit / AWS) — encrypted database storage in India region where possible.",
  lg_s3_outro: "These services have their own privacy policies which we encourage you to read.",
  lg_s4_title: "4. Data Retention",
  lg_s4_p: "We retain your account and kundli data for as long as your account is active. If you delete your account (see Section 7) we permanently erase your personal data within 30 days, except where retention is legally required (e.g. tax invoices for 7 years under Indian law).",
  lg_s5_title: "5. Data Security",
  lg_s5_b1: "All API traffic is encrypted with TLS 1.2+.",
  lg_s5_b2: "Passwords are hashed with scrypt (never stored in plain text).",
  lg_s5_b3: "API access requires a per-user API key validated on every request.",
  lg_s5_b4: "Database backups are encrypted at rest.",
  lg_s5_b5: "Access to production data is restricted to authorised engineers.",
  lg_s6_title: "6. Your Rights",
  lg_s6_intro: "Under the Digital Personal Data Protection Act, 2023 (India) and comparable laws, you have the right to:",
  lg_s6_b1: "Access the personal data we hold about you.",
  lg_s6_b2: "Correct inaccurate or outdated information.",
  lg_s6_b3: "Withdraw consent and delete your account.",
  lg_s6_b4: "Receive an export of your kundli data in JSON format.",
  lg_s6_b5: "Lodge a complaint with the Data Protection Board of India.",
  lg_s6_outro: "To exercise any of these rights, email us at support@cosmiclens.app.",
  lg_s7_title: "7. Account Deletion",
  lg_s7_p: "You can delete your account at any time from Profile → Delete Account. Deletion is permanent and removes all profiles, kundlis, chat history, and personal data within 30 days.",
  lg_s8_title: "8. Children",
  lg_s8_p: "Cosmic Lens is not directed to children under 13. We do not knowingly collect personal data from children. If you believe a child has created an account, please contact us and we will delete it promptly.",
  lg_s9_title: "9. International Users",
  lg_s9_p: "Cosmic Lens is operated from India. If you access the Service from outside India, your information will be transferred to and processed in India where data-protection laws may differ from your country.",
  lg_s10_title: "10. Changes to This Policy",
  lg_s10_p: "We may update this Privacy Policy from time to time. The \"Last updated\" date at the top will reflect the most recent changes. Material changes will be communicated in-app at least 7 days in advance.",
  lg_s11_title: "11. Contact Us",
  lg_s11_intro: "For privacy-related questions, requests, or grievances:",
  lg_s11_b1: "Email: support@cosmiclens.app",
  lg_s11_b2: "Grievance Officer: Available within 30 days of complaint receipt",
  lg_h_terms: "Terms of Service",
  lg_p_termsIntro: "These Terms of Service (\"Terms\") govern your access to and use of the Cosmic Lens mobile application and related services (the \"Service\"). By creating an account, downloading, or using the Service, you accept these Terms. If you do not agree, please do not use the Service.",
  lg_t1_title: "1. Eligibility",
  lg_t1_b1: "You must be at least 13 years old to use Cosmic Lens.",
  lg_t1_b2: "If you are under 18, you must have permission from a parent or guardian.",
  lg_t1_b3: "You confirm that the information you provide (name, date, time, place of birth) is true and accurate. Inaccurate birth data will produce inaccurate astrological results.",
  lg_t2_title: "2. Account & Security",
  lg_t2_b1: "You are responsible for keeping your login credentials safe.",
  lg_t2_b2: "You may not share your account or use someone else's account.",
  lg_t2_b3: "Notify us immediately of any unauthorised access.",
  lg_t2_b4: "We reserve the right to suspend accounts engaged in fraud, abuse, or violation of these Terms.",
  lg_t3_title: "3. The Service",
  lg_t3_p: "Cosmic Lens provides Vedic-astrology computations including kundli, dashas, doshas, marriage compatibility, panchang, muhurat, numerology, vastu, lucky elements, and Jyotish-based question answering. Calculations follow traditional Vedic principles (Lahiri ayanamsa) using accurate ephemeris data.",
  lg_t4_title: "4. Subscription Plans",
  lg_t4_intro: "Cosmic Lens offers the following plans:",
  lg_t4_b1: "Free — limited features, 1 Jyotish question/day",
  lg_t4_b2: "7-day Free Trial — Basic features for new users, one-time only, no payment required",
  lg_t4_b3: "Basic — ₹199/month or ₹1,799/year, includes 10 Jyotish questions/day and basic analysis",
  lg_t4_b4: "Pro — ₹399/month or ₹2,999/year, includes unlimited Jyotish questions, full deep analysis, 6-month timeline, karmic insights, PDF reports",
  lg_t4_outro: "Subscriptions auto-renew at the end of each billing period unless cancelled at least 24 hours before renewal. You can cancel any time from Profile → Subscription → Cancel or by contacting support.",
  lg_t5_title: "5. Payments",
  lg_t5_p: "Payments are processed by Cashfree Payments. By making a purchase you agree to Cashfree's terms in addition to ours. All prices are in Indian Rupees (₹) and inclusive of applicable GST.",
  lg_t6_title: "6. Refund Policy",
  lg_t6_p: "Please review our Refund & Cancellation section below for full details. In summary, all sales are generally final, but refunds may be granted for technical failures, double-charges, or unused service within 7 days of payment.",
  lg_t7_title: "7. User Conduct — You agree NOT to",
  lg_t7_b1: "Use the Service for any illegal or fraudulent purpose.",
  lg_t7_b2: "Reverse-engineer, decompile, or scrape the Service.",
  lg_t7_b3: "Use bots, scripts, or automated tools to abuse free or trial features.",
  lg_t7_b4: "Resell, sublicense, or republish content from the Service.",
  lg_t7_b5: "Submit false birth data on behalf of another person without consent.",
  lg_t7_b6: "Harass, threaten, or impersonate others.",
  lg_t8_title: "8. Intellectual Property",
  lg_t8_p: "All content, design, code, branding, algorithms, and computed reports in the Service are the intellectual property of Cosmic Lens or its licensors. You receive a limited, non-exclusive, non-transferable licence to use the Service for personal, non-commercial purposes only.",
  lg_t9_title: "9. Engine-Generated Answers",
  lg_t9_p: "The \"Ask\" feature uses rule-based and generative analysis of your kundli. Jyotish answers are produced by software and may contain errors, ambiguities, or contradictions. They are NOT a substitute for professional advice.",
  lg_t10_title: "10. No Professional Advice",
  lg_t10_callout: "Cosmic Lens is for spiritual and entertainment purposes only. Astrological insights are NOT a substitute for professional medical, legal, financial, psychological, or relationship advice. Always consult qualified professionals for important life decisions.",
  lg_t11_title: "11. Disclaimers",
  lg_t11_p: "The Service is provided \"as is\" and \"as available\" without warranties of any kind, express or implied. We do not guarantee that astrological predictions will come true, that the Service will be error-free, or that it will be available at all times. Past performance of any prediction does not indicate future results.",
  lg_t12_title: "12. Limitation of Liability",
  lg_t12_p: "To the maximum extent permitted by law, Cosmic Lens, its officers, employees, and partners shall not be liable for any indirect, incidental, consequential, or punitive damages arising from your use of the Service. Our total liability for any claim is limited to the amount you paid us in the 12 months preceding the claim, or ₹1,000, whichever is greater.",
  lg_t13_title: "13. Termination",
  lg_t13_p: "You may stop using the Service at any time by deleting your account. We may suspend or terminate your access immediately if you violate these Terms or engage in conduct harmful to other users or the Service.",
  lg_t14_title: "14. Changes to Terms",
  lg_t14_p: "We may update these Terms periodically. Continued use of the Service after changes become effective constitutes acceptance of the new Terms. Material changes will be notified in-app at least 7 days in advance.",
  lg_t15_title: "15. Governing Law & Jurisdiction",
  lg_t15_p: "These Terms are governed by the laws of India. Any disputes arising out of or related to these Terms or the Service shall be subject to the exclusive jurisdiction of the courts in your registered city, India.",
  lg_t16_title: "16. Contact",
  lg_t16_p: "For questions about these Terms, email support@cosmiclens.app.",
  lg_h_refund: "Refund & Cancellation",
  lg_p_refundIntro: "At Cosmic Lens we want every member to have a great experience. This policy explains when subscription fees are refundable and how to cancel your subscription.",
  lg_callout_refund: "Use the 7-day Free Trial before subscribing — it lets you experience Basic features at no cost so you can decide before paying.",
  lg_r1_title: "1. Subscription Cancellation",
  lg_r1_intro: "You can cancel your monthly or yearly subscription at any time:",
  lg_r1_b1: "Open Profile → Subscription and tap \"Cancel Subscription\".",
  lg_r1_b2: "Or email support@cosmiclens.app from your registered email.",
  lg_r1_outro: "After cancellation, you keep premium access until the end of the current billing period. No further charges will be made.",
  lg_r2_title: "2. When Refunds Are Granted",
  lg_r2_intro: "We will issue a full or pro-rated refund in these situations:",
  lg_r2_b1: "Double charge / duplicate payment — full refund of the duplicate amount, processed within 5–7 business days.",
  lg_r2_b2: "Payment succeeded but plan not activated — full refund or manual plan activation, your choice.",
  lg_r2_b3: "Technical failure preventing access for more than 72 hours — pro-rated refund for unused days.",
  lg_r2_b4: "Cancellation within 7 days of first paid subscription if you have used fewer than 5 paid features — full refund (one-time per user).",
  lg_r3_title: "3. When Refunds Are NOT Granted",
  lg_r3_b1: "Change of mind after the 7-day window.",
  lg_r3_b2: "Astrological prediction did not come true — predictions are interpretive guidance, not guarantees (see Disclaimer).",
  lg_r3_b3: "You forgot to cancel before auto-renewal — but we will cancel future renewals immediately on request.",
  lg_r3_b4: "Partial-month refunds for monthly plans cancelled mid-cycle.",
  lg_r3_b5: "Refunds for the Free or Trial plans (no payment was made).",
  lg_r3_b6: "Refunds requested more than 30 days after payment.",
  lg_r4_title: "4. How to Request a Refund",
  lg_r4_intro: "Email support@cosmiclens.app with:",
  lg_r4_b1: "Your registered email address or mobile number",
  lg_r4_b2: "The order ID (visible in Profile → Subscription → Payment History)",
  lg_r4_b3: "Reason for the refund request",
  lg_r4_outro: "We respond to all refund requests within 3 business days. Approved refunds are processed by Cashfree to your original payment method within 5–10 business days.",
  lg_r5_title: "5. Failed Payments",
  lg_r5_p: "If a payment fails, no charge is made. If your bank shows a \"pending\" charge, it is automatically reversed within 5–7 business days per RBI guidelines. You do not need to contact us for these.",
  lg_r6_title: "6. Subscription Auto-Renewal",
  lg_r6_p: "Monthly and yearly plans renew automatically. We will send a reminder via email or in-app notification before each renewal. To stop renewal, simply cancel before the renewal date — no action will be charged.",
  lg_r7_title: "7. Chargebacks",
  lg_r7_p: "If you initiate a chargeback through your bank instead of contacting us first, your account will be suspended pending investigation. We always prefer to resolve issues directly — please email us first.",
  lg_r8_title: "8. Contact for Refunds",
  lg_r8_b1: "Email: support@cosmiclens.app",
  lg_r8_b2: "Subject line: \"Refund Request — [Order ID]\"",
  lg_r8_b3: "Response time: within 3 business days",
  lg_h_disclaimer: "Astrology Disclaimer",
  lg_callout_disc: "Cosmic Lens is intended for spiritual exploration, self-reflection, and entertainment purposes only. It is not a substitute for professional medical, legal, financial, psychological, or relationship advice.",
  lg_d1_title: "1. Nature of Astrology",
  lg_d1_p: "Vedic astrology (Jyotish) is an ancient art and philosophical tradition. The interpretations, predictions, dashas, doshas, muhurats, and remedies provided in Cosmic Lens reflect classical principles and modern algorithmic analysis. They are interpretive in nature and not scientifically verifiable.",
  lg_d2_title: "2. No Guaranteed Outcomes",
  lg_d2_p: "No astrological prediction or insight is guaranteed to come true. Outcomes in life depend on many factors — your free will, choices, actions, environment, and circumstances — that astrology cannot fully capture.",
  lg_d3_title: "3. Not a Substitute for Professionals",
  lg_d3_intro: "Cosmic Lens content must NEVER be used as the sole basis for important life decisions. Always consult appropriately qualified professionals:",
  lg_d3_b1: "Health concerns — see a registered medical doctor. Do not stop or alter medication based on astrological readings.",
  lg_d3_b2: "Mental health — speak to a licensed psychologist or psychiatrist. If you are in crisis, call iCall (India) at 9152987821 or your local helpline.",
  lg_d3_b3: "Legal matters — consult a qualified lawyer.",
  lg_d3_b4: "Financial / investment decisions — consult a SEBI-registered investment advisor.",
  lg_d3_b5: "Relationship & marriage — consult a counsellor; compatibility scores should never replace open communication and consent.",
  lg_d4_title: "4. Engine-Generated Content",
  lg_d4_p: "The \"Ask\" feature uses automated software (rule-based engine) to analyse your kundli. Answers are generated by code and may contain errors, omissions, contradictions, or culturally inappropriate phrasing. They are not endorsed by any individual astrologer.",
  lg_d5_title: "5. Remedies",
  lg_d5_p: "Suggested remedies (mantras, gemstones, donations, fasting, pujas) are drawn from classical texts. We do not guarantee any specific result from following them. Consult a qualified Vedic astrologer or guru before adopting any remedy, especially gemstones and mantras with seed-syllables (beej mantras).",
  lg_d6_title: "6. Birth-Data Accuracy",
  lg_d6_p: "Astrological calculations are highly sensitive to your time and place of birth. Even a 4-minute error in birth time can change your ascendant. We recommend verifying your birth time from a hospital record or birth certificate. Inaccurate input will produce inaccurate results.",
  lg_d7_title: "7. Cultural & Regional Differences",
  lg_d7_p: "Cosmic Lens uses traditional Vedic (Lahiri / Chitrapaksha) ayanamsa. Western, Tropical, KP, Krishnamurti, and Tantric astrologers may use different systems and arrive at different conclusions. None of these systems is \"wrong\" — they are different lenses.",
  lg_d8_title: "8. Emergency Situations",
  lg_d8_callout: "If you are experiencing a medical emergency or thoughts of self-harm, please call your local emergency services immediately. Do not rely on this app for crisis support. India: 112 (emergency), iCall 9152987821 (mental health).",
  lg_d9_title: "9. Acceptance",
  lg_d9_p: "By using Cosmic Lens you acknowledge that you have read and understood this disclaimer and agree to use the Service responsibly.",
  bv_headerTitle: "Business Vastu",
  bv_cardTitle: "Premium Business Vastu",
  bv_cardBody: "Combine your premise layout with the owner Kundli + active Mahadasha to get a personalised, lifetime priority plan.",
  bv_cardBodySmall: "Aapke vyapar sthal ko swami ki Kundli aur chal rahi Mahadasha ke saath milakar ek vyaktigat sudhar yojana banayi jaati hai.",
  bv_secBizType: "Business Type",
  bv_secPremiseName: "Premise Name",
  bv_phPremiseName: "e.g. Andheri Shop, Powai HQ",
  bv_premiseHint: "Required — your one-time unlock is matched to this premise name.",
  bv_refineRooms: "Optional: Refine Rooms",
  bv_premiseLayout: "Premise Layout",
  bv_engineWillDetect: "Photo Engine will detect rooms from your upload. You can also list rooms here to override.",
  bv_lblDirection: "Direction:",
  bv_selectDirection: "Select direction",
  bv_addRoom: "Add Room (★ = critical)",
  bv_runScanPrefix: "Run",
  bv_runScanSuffix: "Vastu Scan",
  bv_biz_shop: "Shop",
  bv_biz_office: "Office",
  bv_biz_factory: "Factory",
  bv_dir_N: "North",
  bv_dir_NE: "North-East",
  bv_dir_E: "East",
  bv_dir_SE: "South-East",
  bv_dir_S: "South",
  bv_dir_SW: "South-West",
  bv_dir_W: "West",
  bv_dir_NW: "North-West",
  bv_room_entrance: "Entrance",
  bv_room_owner_seat: "Owner Seat",
  bv_room_cash_counter: "Cash Counter",
  bv_room_billing_counter: "Billing Counter",
  bv_room_vault: "Vault",
  bv_room_stock_storage: "Stock Storage",
  bv_room_display: "Display Area",
  bv_room_pooja: "Mandir / Pooja",
  bv_room_back_office: "Back Office",
  bv_room_staff_room: "Staff Room",
  bv_room_toilet: "Toilet",
  bv_room_owner_cabin: "Owner Cabin",
  bv_room_reception: "Reception",
  bv_room_conference: "Conference",
  bv_room_accounts: "Accounts",
  bv_room_server_room: "Server Room",
  bv_room_pantry: "Pantry",
  bv_room_machinery: "Machinery",
  bv_room_heavy_machine: "Heavy Machine",
  bv_room_raw_storage: "Raw Storage",
  bv_room_finished_goods: "Finished Goods",
  bv_room_boiler: "Boiler",
  bv_room_labour_quarter: "Labour Quarter",
  bv_errAuthRequired: "Please log in to run a Business Vastu scan.",
  bv_errValidationRooms: "Add at least 2 room photos, or upload your full shop floor plan PDF.",
  bv_btnUploadShopPdf: "Upload Full Shop PDF",
  bv_btnUploadOfficePdf: "Upload Full Office PDF",
  bv_btnUploadOfficePhoto: "Upload Office Room Photo",
  bv_btnUploadFactoryPdf: "Upload Full Factory PDF",
  bv_btnUploadFactoryPhoto: "Upload Factory Photo",
  bv_planNorthHint: "Where is North on this plan?",
  bv_secUploadedPhotos: "Uploaded Photos",
  bv_btnSubmitReview: "Pay Now",
  bv_submitSuccessTitle: "Payment received",
  bv_submitSuccessBody: "Our Vastu expert will review your photos and prepare your report within 24–48 hours.",
  bv_errValidationName: "Naam your premise (e.g. 'Andheri Shop') — needed to match your unlock.",
  bv_errUnlockTitle: "Unlock Required",
  bv_errProfileTitle: "Complete your profile",
  bv_errValidTitle: "Check your inputs",
  bv_errScanFailed: "Scan failed",
  bv_errTryAgain: "Please try again.",
  bv_btnCompleteProfile: "Complete Profile",
  bv_walletHintPrefix: "Use the wallet above to unlock",
  bv_walletHintSuffix: "Vastu (lifetime).",
  bv_overallScore: "OVERALL PREMISE SCORE",
  bv_grade: "Grade",
  bv_pdfReady: "Detailed PDF Report Ready",
  bv_pdfBodyHi: "Aapka full Business Vastu report PDF me ready hai — room-by-room verdict, Mahadasha alert, stakeholder synergy, priority actions sab kuch.",
  bv_pdfBodyEn: "Your full Business Vastu report is available as a PDF — open, save, or share it.",
  bv_btnOpenPdf: "Open PDF Report",
  bv_footerBrand: "Powered by Advanced Cosmic Intelligence",
  bv_lblIdeal: "Ideal",
  bv_lblAcceptable: "Acceptable",
  bv_lblAdjust: "Adjust",
  bv_lblAvoid: "Avoid",
  bv_lblOwnerMd: "Owner Mahadasha",
  bv_lblStakeholder: "Stakeholder Synergy",
  bv_lblMuhuratAlign: "Muhurat Alignment",
  bv_secPriority: "Priority Actions",
  bv_lblCritical: "★ CRITICAL",
  bv_secRoomByRoom: "Room-by-room",
  bv_lblZone: "Zone:",
  bv_secClassicalRefs: "CLASSICAL REFERENCES",
  avp_headerTitle: "Home Vastu Premium",
  avp_heroTitle: "Home Vastu Premium",
  avp_heroBody: "Choose what you want to scan — a single room photo, or your full home floor plan. Get personalised Vastu × Kundli guidance with clear next steps.",
  avp_modeCameraTitle: "Home Vastu",
  avp_modeCameraSub: "Single room (camera)",
  avp_modeSingleTitle: "Individual Room",
  avp_modeSingleSub: "Photo / PDF",
  avp_modeWholeTitle: "Full Home Plan",
  avp_modeWholeSub: "Whole home (PDF/JPG)",
  avp_introCameraTitle: "Home Vastu — Live Camera",
  avp_introCameraBody: "This is for one room only. Pick the room name, open the camera, stand inside that room, and capture the photo — the compass locks direction at shutter time.",
  avp_pickerLabel: "Which room is this photo of?",
  avp_pickerHint: "Pick a room above to enable the camera.",
  avp_camHintPrefix: "Camera + compass · Photographing",
  avp_camHintNoRoom: "Pick a room first",
  avp_btnSmartScan: "Open Camera",
  avp_btnUploadPhoto: "Upload Room Photo",
  avp_btnUploadHomePdf: "Upload Full Home PDF",
  avp_badgeSingleRoom: "Single room",
  avp_badgeWholeHome: "Whole home",
  avp_uploadPricePerRoom: "per room",
  avp_uploadPaySubmit: "Pay ₹{amount}",
  avp_uploadSubmitted: "Done! Check My Reports soon.",
  avp_introSingleTitle: "Individual Room — Photo or PDF",
  avp_introSingleBody: "Not at home? Pick a photo or PDF from your gallery and tag the room + direction manually. Best when you want to check one specific room.",
  avp_introWholeTitle: "Full Home Plan — Photo Engine",
  avp_introWholeBody: "Upload your complete home floor plan (architect PDF/JPG). Photo Engine will detect rooms and generate a consolidated direction-wise report, personalised to your kundli.",
  avp_btnRunWhole: "Run Full Home Scan",
  avp_btnAnalysing: "Analysing…",
  avp_room_bedroom: "Bedroom",
  avp_room_kitchen: "Kitchen",
  avp_room_pooja: "Pooja",
  avp_room_living: "Living",
  avp_room_bathroom: "Bathroom",
  avp_room_entrance: "Entrance",
  avp_room_study: "Study",
  avp_room_store: "Store",
  avp_errAuthRequired: "Please log in to run a Smart Scan.",
  avp_errMonthlyLimit: "Monthly limit reached",
  avp_errUpgradeReq: "Upgrade required",
  avp_errProfile: "Complete your profile",
  avp_errVisionNoRoom: "Couldn't read this photo",
  avp_errScanFailed: "Smart Scan failed",
  avp_errBodyDefault: "Please try a clearer photo of your floor plan or the full room.",
  avp_btnCompleteProfile: "Complete Profile",
  avp_btnUpgradePro: "Upgrade to Pro — Unlimited",
  avp_overallScore: "OVERALL HOUSE SCORE",
  avp_pdfReady: "Detailed PDF Report Ready",
  avp_pdfBody: "Aapka full AstroVastu PRO report PDF me ready hai — har room ka deep verdict, Mahadasha layer, priority actions aur classical references.",
  avp_btnOpenPdf: "Open PDF Report",
  avp_footerBrand: "Powered by Advanced Cosmic Intelligence",
  avp_secPriority: "PRIORITY ACTIONS",
  avp_secRoomByRoom: "ROOM-BY-ROOM BREAKDOWN",
  avp_lblMdAlert: "Mahadasha Alert",
  avp_quotaUnlimited: "Unlimited PRO scans (Pro plan)",
  avp_quotaPrefix: "Scan",
  avp_quotaThisMonth: "this month",
  avp_brandFooter: "✨ Powered by Advanced Cosmic Intelligence",
  avp_brandFooterSub: "Cosmic AstroVastu Drishti — PRO Engine v1.0",
  avp_lblIdeal: "Ideal",
  avp_lblAcceptable: "Acceptable",
  avp_lblAdjust: "Adjust",
  avp_lblAvoid: "Avoid",
  avr_emptyTitle: "No report loaded",
  avr_emptyBody: "Please run a Smart Scan first to view the result here.",
  avr_btnOpenPro: "Open AstroVastu PRO",
  avr_headerTitle: "Your AstroVastu Report",
  avr_outOf100: "OUT OF 100",
  avr_grade: "Grade",
  avr_btnOpenPdf: "Open PDF",
  avr_btnWhatsApp: "WhatsApp",
  avr_secPriorityHi: "SABSE PEHLE YE 3 CHEEZEIN THEEK KARO",
  avr_secRoomByRoom: "ROOM-BY-ROOM",
  avr_brandFooter: "✨ Powered by Advanced Cosmic Intelligence",
  avr_shareTitle: "🪔 *AstroVastu PRO Report*",
  avr_shareScoreLbl: "📊 Score:",
  avr_shareOpenLbl: "📄 Open report:",
  avr_shareBrandLbl: "_Powered by Advanced Cosmic Intelligence_",
  avr_alertShareErr: "Couldn't share",

  // Risk Radar — Lucky / Best-Avoid Time card
  rrLuckyAajShubhAnk:        "TODAY'S LUCKY NUMBER",
  rrLuckyAajShubhRang:       "TODAY'S LUCKY COLOUR",
  rrLuckyShubhAnk:           "LUCKY NUMBER",
  rrLuckyShubhRang:          "LUCKY COLOUR",
  rrLuckyBestTime:           "⏰ BEST TIME",
  rrLuckyAvoidTime:          "🚫 AVOID TIME",
  rrLuckyPoweredBy:          "✨ Powered by Advanced Cosmic Intelligence",
  rrLuckyHeaderToday:        "TODAY'S LUCKY NUMBER + COLOUR",
  rrLuckyHeaderOther:        "LUCKY NUMBER + COLOUR",
  rrLuckyCalculating:        "Calculating your lucky number and colour…",
  rrLuckyCreateKundliPrompt: "Create your kundli — see your personal lucky number and colour for today, based on your birth nakshatra.",
  rrLuckyCreateKundliCta:    "CREATE KUNDLI →",
  rrLuckyDetailsUnavail:     "Lucky details aren't available right now.",
  rrLuckyDayUnavail:         "Lucky number and colour aren't available for this day yet.",

  // Forecast — Lucky highlights card
  fc_luckyBestTimeLabel:     "BEST TIME",
  fc_luckyAvoidTimeLabel:    "AVOID TIME",
  fc_luckyReason:            "On {date} — lucky number {n} and {colour} colour align with the day's cosmic energy.",
  fc_luckyClrHara:           "Green",
  fc_luckyClrPila:           "Yellow",
  fc_luckyClrSafed:          "White",
  fc_luckyClrNeela:          "Blue",
  fc_luckyClrSuneheri:       "Golden",
  fc_luckyClrKesari:         "Saffron",

  // Risk Radar — 24-hour breakdown labels (EN)
  rrSection24hToday:          "NEXT 24 HOURS",
  rrSection24hWithDate:       "{date} — 24 HOURS",
  rrLabelKyaRisk:             "WHAT'S THE RISK",
  rrLabelKyaAvoid:            "WHAT TO AVOID",
  rrLabelKyaKarna:            "WHAT TO DO",
  rrLabelUpay:                "REMEDY",
  rrLevelLow:                 "Low",
  rrLevelMed:                 "Med",
  rrLevelHigh:                "High",
  rrLabelRiskLevel:           "RISK LEVEL",
  radarHeaderSub:             "Cosmic radar for the next 7 days",
  radarLoadingTxt:            "Preparing your radar…",
  radarEmptyTitle:            "Couldn't load radar",
  radarEmptyBody:             "Check your internet or try again in a moment.",
  radarPickerLabel:           "CHOOSE YOUR DAY",
  radarDayToday:              "Today",
  radarDayTomorrow:           "Tomorrow",
  radarTotalLabel:            "TOTAL RISK SIGNALS",
  radarBadgeHigh:             "HIGH ALERT",
  radarBadgeMed:              "ELEVATED",
  radarBadgeLow:              "STABLE",
  radarSubToday:              "Active threat signals in the next 24 hours",
  radarSubOther:              "Active signals in the 24 hours of {date}",
  radarStatusActive:          "THREAT SCAN ACTIVE",
  radarSignalSingular:        "SIGNAL",
  radarSignalPlural:          "SIGNALS",
  radarAllClear:              "ALL CLEAR",
  radarAllClearSub:           "No major signals today",
  radarTitle:                 "Risk Radar",
  rrCardTitle:                "Cosmic Risk Radar",
  rrSafestChip:               "SAFEST",
  rrChallengingChip:          "CHALLENGING",
  rrDayOf7:                   "Day {n} of 7",
  rrLockedTitle:              "{date} radar locked",
  rrLockedSub:                "Unlock the full radar for upcoming days — risk level, what to do/avoid, lucky numbers, best time and remedies — with Premium.",
  rrLockedHint:               "💡 Day 1 is free — tap to preview",
  rrLockedCta:                "UNLOCK PREMIUM",
  rrScoreUp:                  "Today is filled with positive energy. A great day to start new ventures.",
  rrScoreMixed:               "A mixed day — some opportunities, some things to watch out for.",
  rrScoreDown:                "Slightly challenging energy today. Stay patient, avoid being reactive.",
  rrDotPrimary:               "Primary",
  rrDotSecondary:             "Secondary",
  rrDotWatch:                 "Watch",
  rrDotStable:                "Stable",
  rrDotRoutine:               "Routine check",
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
  mdVastuTitle:       "Astrovastu Pro",
  mdVastuSub:         "Aapki kundli ke hisaab se vastu",
  mdDivisionalTitle:  "Divisional Charts",
  mdDivisionalSub:    "D9 Navamsa, D10 Dashamsha, D7 aur saari vargas",
  viewChart:          "Chart dekhein",
  hideChart:          "Chart chhupayein",
  ds_title: "Dosh Analysis",
  ds_subtitle: "Poora Dosh Analysis ({count} dosh)",
  ds_demo: "Demo",
  ds_totalDosh: "Kul Dosh",
  ds_present: "Maujood",
  ds_notPresent: "Nahi",
  ds_scanning: "Scan ho raha…",
  ds_analyzing: "Aapki kundli analyse ho rahi…",
  ds_checking: "Saare {count} dosh conditions check ho rahe",
  ds_analysis: "Dosh Analysis",
  ds_active: "Sakriya",
  ds_mild: "Halka",
  ds_clear: "Saf",
  ds_detected: "{total} me se {found} dosh mile",
  ds_remedies: "UPAY",
  ds_disclaimer: "Dosh vishleshan classical Vedic jyotish par adharit hai. Bade faislon ke liye qualified Jyotishi se salah lein.",
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
  numFreeSection:     "BASIC NUMEROLOGY",
  numTapHint:         "Poori details ke liye kisi bhi card par tap karein",
  numLifePathLbl:     "LIFE PATH NUMBER",
  numLifePathHi:      "Jeevan Path Sankhya",
  numBirthDayLbl:     "BIRTH DAY NUMBER",
  numBirthDayHi:      "Janm Din Sankhya",
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
  numCoreSummary:     "AAPKE 4 CORE NUMBERS",
  numBasicLockedHint: "Career blueprint, phone numerology aur lucky colours — Pro PDF report mein.",
  numBasicCompareTitle: "BASIC VS PRO",
  numBasicCompareBasicLine: "4 core numbers · traits · strength & weakness",
  numBasicCompareProLine: "Full PDF · career blueprint · phone & lucky numbers · remedies",
  numProTeaseBtn:     "Numerology Pro Report Lein",
  numProfileFor:      "{name} ke numbers",

  km_addYourKundli:   "Apni Kundli Add karein",
  km_addPartnerKundli:"Saathi ki Kundli Add karein",
  km_errName:         "Naam zaroori hai.",
  km_errAllFields:    "Sab fields zaroori hain.",
  km_lblName:         "NAAM",
  km_lblDob:          "JANAM TAREEKH",
  km_lblTime:         "JANAM SAMAY",
  km_lblPlace:        "JANAM STHAAN",

  km_birthDetailsReq:  "Janam vivran zaroori",
  km_partnerBirth:     "Saathi ke janam vivran",
  km_phName:           "Poora naam",
  km_phDob:            "DD/MM/YYYY",
  km_phTime:           "HH:MM  AM / PM",
  km_phPlace:          "Jaise: Delhi, India",
  km_birthMissing:     "Janam Data Maujood Nahi",
  km_calcFailed:       "Calculation Vifal",
  km_okBtn:            "OK",
  km_aap:              "Aap",

  km_secTopInsights:   "MUKHYA INSIGHTS",
  km_secDeepInsights:  "GEHRE INSIGHTS",
  km_secAdvAnalysis:   "ADVANCED VISHLESHAN",
  km_secFutInsights:   "BHAVISHYA INSIGHTS",
  km_secHidPremium:    "CHHUPE PREMIUM",

  km_coreCompTitle:    "Mukhya Compatibility",
  km_coreCompDesc:     "Kya aapke dil, mann aur aatma jeevan bhar ke liye sach me jude hain?",
  km_riskScanTitle:    "Risk Scan",
  km_riskScanDesc:     "Yeh insight aapka faisla badal sakti hai — chhupe risks samne aayenge",
  km_personMatchTitle: "Personality Match",
  km_personMatchDesc:  "Yeh insight aapka faisla badal sakti hai — dekho kya aap ek doosre ko sach me samajhte ho",
  km_soulKarmaTitle:   "Aatma & Karma",
  km_soulKarmaDesc:    "Kya aap niyati ke saathi ho? Ya bas timing? Aapki janam patrika par real-time vishleshan",
  km_intimacyTitle:    "Intimacy Score",
  km_intimacyDesc:     "Sharirik aur bhavnatmak bandhan — woh sach jo zyadatar joday kabhi nahi jaante",
  km_doshaEngTitle:    "Dosha Engine",
  km_doshaEngDesc:     "Mangal, Nadi aur Bhakoot — woh tanav jo chup-chap shaadiyon ko todte hain",
  km_negEnergyTitle:   "Negative Urja",
  km_negEnergyDesc:    "Chhupe dosh jo aapke pandit bhi miss kar sakte hain — ignore mat karna",
  km_strChalTitle:     "Shaktiyaan & Chunautiyaan",
  km_strChalDesc:      "Kya aapko jod ke rakhega — aur kya chup-chap door kar sakta hai",
  km_remAdvTitle:      "Upay & Salaah",
  km_remAdvDesc:       "Sahi puja, ratna aur mantra — badhne se pehle hi rukawatein hatayein",

  km_marriageTime:     "Vivah Samay",
  km_childPlan:        "Santaan Yojna",
  km_finCompat:        "Aarthik Mel",
  km_lifeStab:         "Jeevan Sthirta",
  km_finHarmony:       "Aarthik Samanvay",
  km_familyAccept:     "Parivar Sweekarya",

  km_karmRelTitle:     "Karmic Rishta Janch",
  km_karmRelDesc:      "Kya is janam me milne ka yog tha?",
  km_pastLifeTitle:    "Pichle Janam ka Sambandh",
  km_pastLifeDesc:     "Pichle janam se aatmik bandhan",
  km_divorceTitle:     "Talaq / Vichhed Risk",
  km_divorceDesc:      "Grah-tanav par adharit sambhavna",
  km_loyaltyTitle:     "Wafadari & Vishwas Index",
  km_loyaltyDesc:      "Vishwasghaat ya lambe samay tak wafadari ki sambhavna",

  km_badgeMostImp:     "SABSE ZAROORI",
  km_badgeCritCheck:   "GAMBHEER JANCH",
  km_badgeDecCard:     "FAISLA CARD",
  km_badgeSecret:      "GUPT",

  km_gradeExcellent:   "Behtareen",
  km_gradeVeryGood:    "Bahut Achha",
  km_gradeAverage:     "Saamanya",
  km_gradeBelowAvg:    "Kam",
  km_gradeLowMatch:    "Bahut Kam",

  km_kutaSahi:         "Sahi",
  km_kutaAnmatch:      "Anmel",
  km_kutaDono:         "Dono",

  km_emotionalBond:    "Bhavnatmak Bandhan",
  km_mentalConn:       "Maansik Sambandh",
  km_intimacyHarm:     "Intimacy Samanvay",
  km_communication:    "Sanvad",
  km_natureTemp:       "Swabhav & Mizaaj",
  km_socialAlign:      "Saamajik Mel",
  km_lifestyleHarm:    "Lifestyle Samanvay",
  km_physicalHarm:     "Sharirik Samanvay",
  km_energeticAttr:    "Urja Aakarshan",

  km_compMismatch:     "Compatibility Anmel",
  km_doshaConflict:    "Dosha Tanav",
  km_longTermStab:     "Lambi-Avadhi Sthirta",
  km_nadiDosh:         "Nadi Dosh",
  km_bhakootDosh:      "Bhakoot Dosh",
  km_ganaDosh:         "Gana Dosh",
  km_grahaMaitri:      "Graha Maitri",

  km_onePartMang:      "Ek saathi Manglik hai",
  km_noMangConf:       "Manglik tanav nahi",

  km_natTimingExp:     "Natural samay sambhav",
  km_slightPatience:   "Thoda sabr karein",
  km_medConsAdv:       "Medical/expert salaah lein",
  km_strongFinAlign:   "Mazbut aarthik mel",
  km_modBudgetHelp:    "Saamanya — budget planning faayademan",
  km_highlyLikely:     "Bahut sambhav",
  km_mayNeedTime:      "Samay aur mehnat lag sakti hai",
  km_marrAusp:         "2025–2026 shubh",
  km_marrModerate:     "2026–2027 saamanya",
  km_marrDelay:        "Der karein — margdarshan lein",

  km_riskLow:          "Kam",
  km_riskModerate:     "Saamanya",
  km_riskHigh:         "Adhik",

  km_deepKarmTie:      "Gehra karmic bandhan",
  km_growConn:         "Badhta sambandh",
  km_posPastLife:      "Shubh purva-janam",
  km_neutralKarma:     "Tatasth karma",

  km_planFriendStrong: "Grah maitri mazbut hai",
  km_sharedEnergies:   "Saanjhi grah urja",
  km_taraFav:          "Tara nakshatra shubh hai",
  km_modTaraDest:      "Saamanya tara bhagya",
  km_bhakSubh:         "Bhakoot shubh — koi rashi tanav nahi",
  km_rashiAlign:       "Rashi urja milti hai",

  km_nadiHealth:       "Nadi dosh — swasthya jagrukta zaroori",
  km_minorTempDiff:    "Halki swabhav antar",
  km_ganaClash:        "Gana tanav — prakriti antar",
  km_commPracNeeded:   "Sanvad ka abhyas zaroori",
  km_bhakTimeCaut:     "Bhakoot dosh — samay savdhani",
  km_patienceConfl:    "Conflict me thoda sabr",
  km_yoniMismatch:     "Yoni anmel — urja samayojan",
  km_qualityTimeNeeded:"Niyamit quality time zaroori",

  km_pastLifeScore:    "Pichle Janam Sambandh Score",
  km_ancestKarma:      "Vanshik Karma Pattern",
  km_nakDream:         "Nakshatra Sapna Compatibility",
  km_advDoshaRev:      "Advanced Dosha Reversal Plan",

  km_unlockComplete:   "Poori Report Unlock Karein",
  km_realTimeAnalysis: "Aapki janam patrika par real-time vishleshan",
  km_secFutTimeline:   "BHAVISHYA TIMELINE",
  km_secSoulKarma:     "AATMA & KARMA VISHLESHAN",
  pe_otherProfiles:   "ANYA PROFILES",
  pe_recentlyDeleted: "Haal mein Hataye",
  pe_noKundliYet:     "Abhi tak koi Kundli nahi",
  pe_manageProfile:   "Apna profile aur family members manage karein",
  pe_tabKundli:       "Kundli",
  pe_tabPersonal:     "Personal Details",
  pe_lblCosmoId:      "USER ID",
  pe_cosmoIdHint:     "Aapka unique Cosmic Lens ID — join karte hi milta hai.",
  pe_lblGmail:        "GMAIL",
  pe_lblPhone:        "MOBILE NUMBER",
  pe_phPhone:         "+91 98765 43210",
  pe_savePersonal:    "Save karein",
  pe_personalSaved:   "Save ho gaya",
  pe_nameLockedHint:  "Naam sirf ek baar badla ja sakta hai.",
  pe_phoneLockedHint:  "Mobile sirf ek baar add ho sakta hai.",
  pe_gmailLockedHint: "Google login se — change nahi hoga.",
  pe_loginRequired:   "Personal details ke liye login karein.",

  pn_computing:       "Calculate ho raha…",
  pn_dataSource:      "Swiss Ephemeris · Lahiri",
  pn_offline:         "Offline · approx values",
  pn_today:           "Aaj",
  pn_parso:           "Parso",
  pn_auspicious:      "AAJ KI SHUBHATA",
  pn_megaFestival:    "Mahaparv",
  pn_bNational:       "Rashtriya",
  pn_bVrat:           "Vrat",
  pn_bMuhurat:        "Muhurat",
  pn_bandExcellent:   "Bahut Shubh",
  pn_bandGood:        "Shubh",
  pn_bandMixed:       "Mishrit",
  pn_bandCaution:     "Saavdhani",
  pn_tabToday:        "Aaj",
  pn_tabMuhurat:      "Muhurat",
  pn_tabGochar:       "Gochar",
  pn_tabVrat:         "Ekadashi",
  pn_tabVivah:        "Vivah",
  pn_ekadashiSub:     "Sunrise tithi · agle 5 saal",
  pn_ekadashiCount:   "Ekadashi (sunrise tithi) · aaj se 5 saal · kul {n} din",
  pn_ekadashiNote:    "Har lunar mahine 2 Ekadashi; Gregorian mahine mein 1 ya 2 dikhengi.",
  pn_vivahCount:      "{n} verified vivah din · agle 5 saal",
  pn_gocharBundled:   "Purana /api/panchang — gochar usme bundled nahi hai.",
  pn_currentMonth:    "ABHI KA MAHINA",
  pn_noEkadashiMonth: "Is mahine koi Ekadashi nahi",
  pn_tagToday:        "Aaj",
  pn_pakshaWord:      "paksha",
  pn_ekadashiTodayHdr:"AAJ EKADASHI VRAT",
  pn_tarabalaHdr:     "AAPKI TARABALA / CHANDRABALA",
  pn_tarabalaHint:    "Tarabala ke liye profile mein kundli complete karein.",
  pn_loadPanchang:    "Panchang load ho raha hai…",
  pn_loadEkadashi:    "Ekadashi gin raha hai…",
  pn_loadFail:        "Panchang load nahi hua — server check karein",
  pn_brahmaMuhurta:   "Brahma Muhurta",
  pn_gulika:          "Gulika Kaal",
  pn_abhijit:         "Abhijit Muhurat",
  pn_muhuratFail:     "Muhurat load nahi hua — location set karein",
  pn_muhuratLoc:      "Sunrise/sunset se 8 hisse — aapke location par",
  pn_gocharFail:      "Gochar load nahi hua",
  pn_gocharDeploy:    "Server purana hai — naya API deploy karein",
  pn_gocharApiFail:   "API connect nahi hua — Metro restart karein",
  pn_vivahSub:        "Drik vivah muhurat · sunrise tithi · lagna · 5 saal",
  pn_vivahEmpty:      "Is range mein highly favorable din nahi mile",
  pn_vivahLoading:    "Vivah muhurat scan (saal {y}/{t})…",
  pn_vivahWindow:     "Ceremony samay",
  pn_vivahConf:       "confidence",
  pn_vivahCoupleHint: "Couple tarabala ke liye doosra profile + kundli add karein.",
  pn_vivahBlockedChaturmas: "Chaturmas (Jul–Oct) — shastriya vivah varjit. Surya Kark–Tula mein; Vrishchik (~Nov) ke baad phir shuru.",
  pn_vivahBlockedMeena:     "Meena maas (Feb–Mar) — classical vivah band.",
  pn_planetSun:       "Surya",
  pn_planetMoon:      "Chandra",
  pn_planetMars:      "Mangal",
  pn_planetMercury:   "Budh",
  pn_planetJupiter:   "Guru",
  pn_planetVenus:     "Shukra",
  pn_planetSaturn:    "Shani",
  pn_planetRahu:      "Rahu",
  pn_planetKetu:      "Ketu",
  pn_motionRetro:     "Vakri",

  nm_proTools:        "PRO+ TOOLS",
  nm_premium:         "PREMIUM",
  nm_lifeMastery:     "Numerology Pro Report",
  nm_yourNumbers:     "AAPKE NUMBERS",
  nm_yourNumbersHint: "(kam se kam ek)",
  nm_whatsInside:     "ANDAR KYA HAI",
  nm_opening:         "Khol raha…",
  nm_generateBtn:     "Numerology Pro Report Generate Karein",

  cr_pageTitle:       "Career Analysis",
  cr_loading:         "Aapki kundli read ho rahi…",
  cr_loginRequired:   "Career analysis dekhne ke liye login karein.",
  cr_addProfile:      "Birth Details Add Karein",
  cr_scoreLabel:      "CAREER SCORE",
  cr_strongPhase:     "Mazboot Phase",
  cr_cautionPhase:    "Saavdhani Phase",
  cr_mixedPhase:      "Mishrit Phase",
  cr_quickReading:    "Quick Reading",
  cr_hiddenInsight:   "CHHUPI HUI INSIGHT",
  cr_proCta:          "Poori career analysis Pro mein unlock karein",
  cr_upgradeBtn:      "Pro mein Upgrade karein",
  cr_houses:          "Career Houses",
  cr_lord:            "Lord:",
  cr_inHouse:         "Ghar mein:",
  cr_planets:         "Career Planets",
  cr_dasha:           "Current Dasha Effect",
  cr_mahadasha:       "Mahadasha",
  cr_antardasha:      "Antardasha",
  cr_ends:            "Khatm",
  cr_transit:         "Live Planetary Transit",
  cr_growth:          "Career Growth ke samay",
  cr_jobChange:       "Job Change Timing",
  cr_struggle:        "Sangharsh aur Chhupe Risks",
  cr_reasoning:       "Yeh Reading Kyun",
  cr_pathTitle:       "Job vs Business",
  cr_jobLabel:        "Job",
  cr_businessLabel:   "Business",
  cr_pathConfidence:  "Chart confidence",
  cr_pathMode:        "Career mode",
  cr_bestOptions:     "Best suitable career options",
  cr_topStrengths:    "Top strengths",
  cr_weakness:        "Weakness",
  cr_risk:            "Risk",

  hl_pageTitle:       "Health Analysis",
  hl_loginRequired:   "Health analysis dekhne ke liye login karein.",
  hl_healthyPhase:    "Swasth Phase",
  hl_careNeeded:      "Dhyan ki zaroorat",
  hl_mixedPhase:      "Mishrit Phase",
  hl_scoreLabel:      "HEALTH SCORE",
  hl_riskLabel:       "Risk:",
  hl_houses:          "Health Houses",
  hl_planets:         "Health Planets",
  hl_riskPeriods:     "Risk ke samay",
  hl_nature:          "Issues ki nature",
  hl_recovery:        "Recovery Strength",
  hl_prevent:         "Preventive Guidance",
  hl_organs:          "Kamzor Body Areas",
  hl_remedies:        "Upay (Mantra aur Lifestyle)",

  fn_pageTitle:       "Finance Analysis",
  fn_growthPhase:     "Growth Phase",
  fn_cautionPhase:    "Saavdhani Phase",
  fn_stablePhase:     "Sthir Phase",
  fn_scoreLabel:      "FINANCE SCORE",
  fn_houses:          "Dhan Houses",
  fn_planets:         "Dhan Planets",
  fn_inflow:          "Paisa Aane ke samay",
  fn_expense:         "Kharch / Nuksaan Phase",
  fn_invest:          "Investment Opportunities",
  fn_sudden:          "Achanak Laabh / Haani",
  fn_stability:       "Dhan Sthirta",
  fn_income:          "Income Sources",

  rl_loveTitle:       "Love Reality Check",
  rl_loveSub:         "Aapke rishte ki chhupi sachchai jaaniye",
  rl_mostUsed:        "Sabse popular",
  rl_loveDesc:        "Current relationship aur BF/GF ke liye",
  rl_marriageTitle:   "Shaadi Compatibility",
  rl_marriageSub:     "Soul Sync, Attraction Match",
  rl_deepBadge:       "Deep Analysis",
  rl_partnerTitle:    "Future Partner Portrait",
  rl_partnerSub:      "roop, swabhav aur disha",
  rl_partnerDesc:     "Aapki kundli se jeevansaathi ki divya jhalak",
  rl_newBadge:        "NEW · Cosmic Portrait",
  rl_pageHeader:      "Relationship",
  rl_selfLabel:       "Aap",
  rl_partnerSelect:   "Partner Chuniye",
  rl_change:          "Badlein",

  mr_loginRequired:   "Reports dekhne ke liye login zaroori.",
  mr_loadError:       "Aapki reports load nahi hui.",
  mr_networkError:    "Network error.",
  mr_waLinkPrefix:    "Report kholiye:",
  mr_waErrorTitle:    "WhatsApp uplabdh nahi",
  mr_openPdf:         "PDF Kholiye",
  mr_whatsapp:        "WhatsApp",
  mr_pageTitle:       "Meri Reports",
  mr_loading:         "Reports load ho rahi…",
  mr_emptyTitle:      "Abhi koi report nahi",
  mr_footer:          "Powered by Advanced Cosmic Intelligence",

  mk_savedCount:      "kundli saved",
  mk_emptyTitle:      "Abhi koi Kundli nahi",
  mk_emptyDesc:       "Birth details ke saath profile add karke kundli generate karein",
  mk_addNew:          "Nayi Kundli Add karein",
  mk_primary:         "PRIMARY",
  mk_deleteTitle:     "Kundli Delete karein?",
  mk_deleteDesc:      "Kundli permanently delete ho jayegi. Yeh action undo nahi hoga.",
  mk_cancel:          "Cancel",
  mk_delete:          "Delete",

  mr_kindHomePro:     "Home AstroVastu PRO",
  mr_kindShop:        "Business Vastu — Dukaan",
  mr_kindOffice:      "Business Vastu — Office",
  mr_kindFactory:     "Business Vastu — Factory",
  mr_kindBusiness:    "Business Vastu",

  rl_kundliReqTitle:        "Kundli zaruri hai",
  rl_kundliReqBoth:         "Aapki aur partner ki dono kundli chahiye. Pehle Kundli screen se dono banayein.",
  rl_kundliReqSelf:         "Aapki kundli ready nahi hai. Pehle Kundli screen se generate karein.",
  rl_kundliReqSelectFirst:  "Aage badhne ke liye upar se apna partner chuniye.",
  rl_kundliReqPartnerMissing: "Partner ki kundli abhi tak nahi bani. Pehle Kundli screen se unki kundli banayein.",
  rl_kundliReqAddBtn:        "Kundli Banayein",
  rl_kundliReqCancel:        "Cancel",

  nm_wi1Title:  "Life Blueprint Card",          nm_wi1Sub:  "Core personality + 2026 focus + sabse badi strength/challenge",
  nm_wi2Title:  "Aap Kaun Ho — Identity",       nm_wi2Sub:  "3-paragraph kahani + 5 chhupi strengths + 5 challenges",
  nm_wi3Title:  "Career Blueprint",             nm_wi3Sub:  "Best fields, common galtiyan, growth timing, money pattern",
  nm_wi4Title:  "Love Pattern — Deep",          nm_wi4Sub:  "Rishtey ka style, breakup triggers, ideal partner number",
  nm_wi5Title:  "Health & Spiritual Path",      nm_wi5Sub:  "Body signals + dharma + mantra + daan schedule",
  nm_wi6Title:  "Risk Alerts + Golden Period",  nm_wi6Sub:  "5 specific risks + sabse bade moves kab karein",
  nm_wi7Title:  "Mobile Number — Deep",         nm_wi7Sub:  "Why · Impact · Action format + Cheiro last-4 + alternatives",
  nm_wi8Title:  "Vehicle Number — Deep",        nm_wi8Sub:  "Why · Impact · Action + favourable plate suggestions",
  nm_wi9Title:  "House Number — Deep",          nm_wi9Sub:  "Why · Impact · Action + remedy schedule",
  nm_wi10Title: "Compatibility Matrix",         nm_wi10Sub: "Aapka Driver vs sabhi 1-9 (mitra/shatru/neutral)",
  nm_wi11Title: "Name Numerology + Letters",    nm_wi11Sub: "Pythagorean + Chaldean + letter-by-letter breakdown",
  nm_wi12Title: "Signature & 90-Day Plan",      nm_wi12Sub: "Signature design + step-by-step implementation",

  fc_demo:              "Demo",
  fc_dailyEnergyScore:  "Daily Energy Score",
  fc_moonRashi:         "Transit Moon",
  fc_paksha:            "Paksha",
  fc_energy:            "Urja",
  fc_activeDasha:       "Active Dasha",

  sub_active:           "ACTIVE",
  sub_upgradeBtn:       "Pro me Upgrade karein 🔓",
  sub_getBasic:         "Basic Lein",
  sub_free:             "FREE",
  sub_alwaysFree:       "Hamesha free",
  sub_cmpJyotishQ:      "Jyotish Sawal",
  sub_cmpMarriage:      "Vivah Milan",
  sub_cmpTimeline:      "Bhavishya Timeline",
  sub_cmpDasha:         "Dasha Vishleshan",
  sub_cmpKarmic:        "Karmic Insights",
  sub_cmpPdf:           "PDF Report",
  sub_cmpProfiles:      "Save Profiles",

  da_energyLevels:      "Urja Star",
  da_energyGood:        "Achha",
  da_energyNeutral:     "Sama",
  da_energyChallenging: "Mushkil",

  pe_relSelf:      "Swayam",
  pe_relHusband:   "Pati",
  pe_relWife:      "Patni",
  pe_relSon:       "Beta",
  pe_relDaughter:  "Beti",
  pe_relFather:    "Pita",
  pe_relMother:    "Mata",
  pe_relBrother:   "Bhai",
  pe_relSister:    "Behen",
  pe_relFriend:    "Dost",
  pe_relOther:     "Anya",

  sub_planBasicName:    "Basic",
  sub_planProName:      "Pro",
  sub_planBasicTag:     "Zaruri Vedic margdarshan",
  sub_planProTag:       "Pura Vedic gyaan",

  sub_bF1: "10 Jyotish Sawal / din",
  sub_bF2: "Vivah Milan (Basic)",
  sub_bF3: "Prem Milan (Basic)",
  sub_bF4: "Career, Health, Finance — chhota saaransh",
  sub_bF5: "Bhavishya Timeline — 1 mahina",
  sub_bF6: "5 save profiles",

  sub_bL1: "Unlimited Sawal",
  sub_bL2: "Gehri vishleshan reasoning ke saath",
  sub_bL3: "Pura 6-mahine ka timeline",
  sub_bL4: "Karmic insights & PDF report",

  sub_pF1: "Unlimited Jyotish Sawal",
  sub_pF2: "Vivah & Prem — Pura gehra vishleshan",
  sub_pF3: "Career, Health, Finance — Vistrit",
  sub_pF4: "Bhavishya Timeline — 6 mahine pura",
  sub_pF5: "D1 + D9 chart vishleshan",
  sub_pF6: "Dasha (MD + AD + PD) pura breakdown",
  sub_pF7: "Karmic patterns & chhupi jankari",
  sub_pF8: "PDF report download",
  sub_pF9: "Unlimited save profiles",

  vu_camSub:     "Turant photo lein",
  vu_galSub:     "Saved photo chuniye",
  vu_roomPicker: "Room type chuniye",
  vu_review:     "Review aur Submit",
  vu_reviewSub:  "Apni photos confirm karein, phir Deep Scan chalayein.",
  vu_tabBasic:   "Basic",
  vu_tabPro:     "Pro",
  vu_introBody:  "Vastu Shastra ek prachin Bhartiya vastu-vigyan hai. Sahi dishaayein ghar mein positive urja, khushiyan, swasthya aur samriddhi laati hain.",

  // ── kundli-milan additional (km2_*) ──
  km2_secRiskScan:        "RISHTE KA RISK SCAN",
  km2_secPersMatch:       "PERSONALITY MATCH",
  km2_secIntimacyComp:    "INTIMACY COMPATIBILITY",
  km2_secNegEnergy:       "NEGATIVE ENERGY CHECK",
  km2_chipClear:          "Saaf",
  km2_chipMild:           "Halka",
  km2_chipPresent:        "Maujood",
  km2_strengthsHdr:       "MAZBOOTI 💚",
  km2_challengesHdr:      "CHUNAUTIYAN ⚡",
  km2_persExcellent:      "Behtareen — dono ka jeevan ke prati nazariya aur values ek jaisi hain.",
  km2_persModerate:       "Saamanya — kuch farak hain par mehnat se sambhal sakte hain.",
  km2_persChallenging:    "Mushkil — swabhav ke farak par kaam karna padega.",
  km2_yoniExceptional:    "Same Yoni — shaaririk aur urja ka behtareen taalmel.",
  km2_yoniComplementary:  "Ek doosre ki purak urja — thoda adjustment ke saath achhi compatibility.",
  km2_yoniDifferent:      "Alag urja — sabar aur samajh se yeh bond mazboot hoga.",
  km2_concernSing:        "Chinta",
  km2_concernPlural:      "Chintayein",
  km2_concernsFound:      "Mili",
  km2_negPatExcell:       "Behtareen — koi badi negative pattern nahi.",
  km2_negPatMinor:        "Choti chintayein — jagrukta se sambhal sakti hain.",
  km2_negPatMulti:        "Kai chintayein — upay zaruri hain.",
  km2_doshDetect:         "Dosh Mila",
  km2_nadiAuspProgeny:    "Nadi alag — santaan ke liye shubh",
  km2_nadiDeepEmpathy:    "Nadi mili — gehri samajh",
  km2_remKumbhVivah:      "Vivah se pehle Kumbh Vivah ya Mangal puja karein.",
  km2_remEkadashi:        "Ekadashi ka vrat rakhein — Shiv puja se Nadi imbalance se bachein.",
  km2_remChandraMantra:   "Chandra mantra japein — Om Chandraya Namah 108 baar.",
  km2_remRudrabhishek:    "Vivah se pehle saath mein Rudrabhishek karein.",
  km2_remGemstones:       "Dono ko compatible ratan pehnein — Jyotishi se salah lein.",
  km2_remSunderkand:      "Saath mein puja aur Sunderkand padhne se bond mazboot hoga.",
  km2_fvExceptional:      "Behtareen match. Sitare aapke favour mein hain. Khushhaal aur safal vivah ka sanket hai.",
  km2_fvVeryPositive:     "Bahut positive match. Aapsi izzat aur pyaar se yeh rishta bahut achha hoga.",
  km2_fvModerate:         "Saamanya match. Jagrukta, mehnat aur expert salah se yeh bond achha banega.",
  km2_fvChallenging:      "Mushkil match. Aage badhne se pehle upay, sabar aur Jyotishi se salah lena zaruri hai.",
  km2_ashtakootScoreLbl:  "Ashtakoot Score",
  km2_concernDetSuffix:   "mili",
  km2_addBothFirst:       "Pehle Dono Kundli Add Karein",
  km2_unlockFullAnal:     "Poori Analysis Khole",
  km2_youPlaceholder:     "Aap",
  km2_birthMissingBody:   "Sahi milan ke liye dono partners ka complete birth data (date, samay, jagah) chahiye.",
  km2_calcFailedBody:     "Match calculate nahi ho saka. Dobara try karein.",
  km2_matchingWith:       "MATCH HO RAHA HAI",
  km3_yourPersAnalysis:   "Aapka Personalised Analysis",
  km3_insEmotional:       "Emotional Compatibility",
  km3_insMarriage:        "Shaadi Ka Future",
  km3_insRisks:           "Chhupe Risks",
  km3_insKarmic:          "Karmic Bond",
  km3_insStrength:        "Strength Factors",
  km3_insTriggers:        "Conflict Triggers",
  km3_insStability:       "Long-term Stability",
  km3_insFinal:           "Final Outcome",
  km3_unlEmotional:       "Emotional Compatibility — kya sach me ek doosre se judte ho ya nahi",
  km3_unlMarriage:        "Shaadi Ka Future — is rishte ki asli direction",
  km3_unlRisks:           "Chhupe Risks — woh patterns jo problems la rahe hain",
  km3_unlKarmic:          "Karmic Bond — is connection ka deeper purpose",
  km3_unlStrength:        "Strength Factors — kya cheez is rishte ko jodi rakhti hai",
  km3_unlTriggers:        "Conflict Triggers — kya cheez baar baar issues paida karti hai",
  km3_unlStability:       "Long-term Stability — chalega ya tootega",
  km3_unlFinal:           "Final Outcome — actual future direction",
  km3_nadiAlag:           "Alag nadi — auspicious for healthy progeny and long life together.",
  km3_nadiSama:           "Sama nadi — strong emotional mirroring, some health caution advised.",
  km3_personFallback:     "Person",
  km3_errTryAgain:        "Error. Dobara try karein.",
  km3_proTrailMore:       "Poori detail aur remedy Pro report me dikhegi.",
  km3_kundliBased:        "Yeh analysis aapki asli kundli par based hai aur un patterns ko reveal karta hai jo seedha aapke rishte par asar dalte hain.",
  km3_truthsBelow:        "Is connection ke sabse important sach neeche chhupe hain.",
  km3_unlockToSee:        "Unlock karke poori picture dekhein.",
  km3_whatYouUnlock:      "WHAT YOU WILL UNLOCK",
  km3_lockedPreview:      "🔒 LOCKED PREVIEW",
  km3_addBothToUnlock:    "Add Both Kundlis to Unlock Preview",
  km3_addBothSubtext:     "Dono ki birth details add karein — phir aapki personal hooks generate hongi",
  vu_tapAnyCard:      "Dos, don'ts aur remedies dekhne ke liye kisi bhi card par tap karein",
  vu_proHeader:       "AstroVastu PRO — Pura Ghar Scan",
  vu_proSubheader:    "Photo Engine + aapki Kundli + Mahadasha layer",
  vu_proDesc:         "Floor-plan upload, compass ke saath room photos, Brihat Samhita / Mayamatam se cited deterministic Vastu Shastra rules, aapki chart ke liye personalised priority actions.",
  vu_oneTime:         "one-time",
  vu_genTipsTitle:    "⚡ General Vastu Tips",
  vu_genTip1:         "Ghar ko clutter-free rakhein — blocked spaces energy flow rokte hain",
  vu_genTip2:         "Ghar hamesha well-lit ho — andhera negativity ko invite karta hai",
  vu_genTip3:         "Chee-chee karte ya toote darwaze turant theek karein",
  vu_genTip4:         "Indoor plants rakhein — ye ghar me jeevan-urja late hain",
  vu_genTip5:         "Toot-foot wali cheezein turant hatayein",
  vu_genTip6:         "North me running water (fountain ya aquarium) shubh hai",
  vu_disclaimer:      "Yeh ek general Vastu guide hai. Apne ghar ke liye specifically, hamesha ek qualified Vastu expert se personalised advice lein.",
  ku_btnKundli:           "Kundli",
  ku_btnAshtak:           "Ashtakavarga",
  ku_btnNavatara:         "Navatara",
  ku_btnJaimini:          "Jaimini",
  ku_btnTransit:          "Transit",
  ku_btnKP:               "KP",
  ku_secDashaTimeline:    "DASHA TIMELINE",
  ku_secAshtakavarga:     "ASHTAKAVARGA",
  ku_secNavatara9Tara:    "NAVATARA — 9 TARA",
  ku_secJaiminiKarakas:   "JAIMINI KARAKAS",
  ku_secGrahaTransit:     "GRAHA TRANSIT",
  ku_secKpPaddhati:       "KP PADDHATI",
  ku_snapAscendant:       "ASCENDANT (LAGNA)",
  ku_snapMoonSign:        "MOON SIGN (RASHI)",
  ku_snapNakshatra:       "NAKSHATRA",
  ku_snapNakshatraLord:   "NAKSHATRA SWAMI",
  ku_snapDashaBalance:    "DASHA BALANCE",
  ku_snapLiveMoonTransit: "CHANDRA TRANSIT — LIVE",
  ku_padaLabel:           "Pada",
  ku_jaiminiDegPre:       "Sign ke andar degree:",
  ku_jaiminiDegSuf:       "chart me sabse zyada",
  ku_kpDesc:              "Krishnamurti Paddhati Vimshottari dasha ke proportional sub-divisions ka use karke events ki precise timing batati hai.",
  ku_kpFooter:            "Kisi bhi event ke liye dekhein: Star-lord aur Sub-lord ka relationship. 3 lord agree → event pakka.",
  ku_kpStar:              "Star",
  ku_kpSub:               "Sub",
  ku_kpSubSub:            "Sub-Sub",
  ku_kpAsc:               "Asc",
  ku_savHeading:          "Sarvashtakavarga",

  // ── Phase 4 additions ─────────────────────────
  nf_title: "Oops!",
  nf_doesntExist: "Ye screen exist nahi karti.",
  nf_goHome: "Home screen par jaayein!",
  ab_title: "Cosmic Lens ke baare mein",
  ab_subtitle: "Vedic astrology, modern andaaz mein",
  ab_secMission: "Hamara Mission",
  ab_pMission1: "Cosmic Lens Vedic Jyotish ki timeless wisdom aapki pocket mein laata hai. Hum classical Parashari principles ko modern ephemeris computations aur expert Jyotish interpretation ke saath jodte hain, taaki aapko accurate, accessible aur personal astrological guidance mile — aapki bhasha mein.",
  ab_pMission2: "Chahe aap apni kundli ke baare mein curious ho, shaadi plan kar rahe ho, career options explore kar rahe ho, ya bas daily insight chahte ho — hamara mission hai aapko clarity aur intention ke saath jeevan navigate karne mein madad karna.",
  ab_secDifferent: "Hum kyun alag hain",
  ab_pDifferent: "• Calculations traditional Lahiri ayanamsa aur high-precision Swiss Ephemeris data use karte hain.\n• 24 bhashaon mein available — 13 Indian regional languages aur Hinglish bhi.\n• Honest, transparent pricing — no in-app currency, no surprise charges.\n• Privacy-first — hum aapki kundli ya chat data kabhi nahi bechte.\n• 7-din ka free trial — paise dene se pehle experience karein.",
  ab_secConnect: "Humse jude",
  ab_lblSupportEmail: "Support Email",
  ab_lblWebsite: "Website",
  ab_secLegal: "Legal & Policies",
  ab_linkPrivacy: "Privacy Policy",
  ab_linkTerms: "Terms of Service",
  ab_linkRefund: "Refund & Cancellation",
  ab_linkDisclaimer: "Astrology Disclaimer",
  ab_linkDelete: "Mera account delete karein",
  ab_lblAppVersion: "App Version",
  ab_versionFoot: "Made with ♥ in India · © 2026 Cosmic Lens",
  da_title: "Account Delete Karein",
  da_subtitle: "Permanent aur wapas nahi le sakte",
  da_calloutDanger: "Ye action permanent hai. Delete karne ke baad data wapas nahi milega.",
  da_secWhatHappens: "Delete karne par kya hoga",
  da_wb1: "Aapka account login (email / mobile / Google) turant hata diya jaata hai.",
  da_wb2: "Saari saved kundlis, profiles aur chat history 30 dino mein erase ho jaati hai.",
  da_wb3: "Active subscriptions cancel ho jaate hain — aage koi charge nahi.",
  da_wb4: "Past payments ke tax invoices Indian law (GST records) ke hisaab se 7 saal tak rakhe ja sakte hain.",
  da_wb5: "Agar dobara Cosmic Lens use karna ho, to nayi account banani padegi.",
  da_secBefore: "Delete karne se pehle",
  da_pBefore: "Ye alternatives consider karein — shayad inse aapki problem bina data lose kiye solve ho jaaye:",
  da_bb1: "Sirf subscription cancel karein — Profile → Subscription → Cancel. Account free rahega.",
  da_bb2: "Notifications band karein — Profile → Notifications → Off.",
  da_bb3: "Refund chahiye? Pehle Refund Policy dekhein — hum madad kar sakte hain.",
  da_bb4: "Privacy concern? Email karein support@cosmiclens.app.",
  da_secConfirm: "Deletion confirm karein",
  da_pConfirm: "Aage badhne ke liye, neeche box mein DELETE type karein aur delete button tap karein.",
  da_inputPh: "Confirm karne ke liye DELETE type karein",
  da_btnDelete: "Mera Account Permanently Delete Karein",
  da_btnDeleting: "Delete ho raha hai…",
  da_btnCancelBack: "Cancel karein aur wapas jaayein",
  da_secNeedHelp: "Iske bajaye madad chahiye?",
  da_pNeedHelp: "Agar koi concern hai, to jaane se pehle hum sun-na chahenge. Reach karein support@cosmiclens.app — zyadatar issues 24 ghante mein resolve ho jaate hain.",
  da_alertNotSignedIn: "Sign in nahi hain",
  da_alertLoginFirst: "Pehle log in karein.",
  da_alertConfirmTtl: "Account permanently delete karein?",
  da_alertConfirmMsg: "Ye action wapas nahi le sakte. Saari kundlis, profiles, chat history aur personal data 30 dino mein erase ho jaayega.",
  da_alertCancel: "Cancel",
  da_alertYesDelete: "Haan, hamesha ke liye delete",
  da_alertDeletedTtl: "Account Delete Ho Gaya",
  da_alertDeletedMsg: "Aapka account permanently delete ho gaya hai. Cosmic Lens use karne ke liye dhanyawaad.",
  da_alertOk: "OK",
  da_alertFailedTtl: "Deletion fail ho gayi",
  da_alertFailedMsg: "Phir se try karein ya support se contact karein.",
  smf_title: "6-Mahine ka Deep Future",
  smf_loadingMsg: "MD/AD/PD chain compute ho raha hai…",
  smf_unavailableTtl: "Future data available nahi hai",
  smf_tryAgain: "Baad mein phir try karein.",
  smf_kundliFirst: "Pehle kundli complete karein.",
  smf_activeChain: "Active Dasha Chain",
  smf_lblMaha: "Maha",
  smf_lblAntar: "Antar",
  smf_lblPratyantar: "Pratyantar",
  smf_adWindow: "AD window",
  smf_pdShift: "PD shift",
  smf_lblMD: "MD",
  smf_lblAD: "AD",
  smf_lblPD: "PD",
  smf_rulesPrefix: "Rules",
  smf_sitsIn: "Sits in",
  smf_pdActiveWindow: "Active PD window",
  smf_lifeAreas: "Is mahine ke Life Areas",
  smf_whyPrefix: "Kyun",
  smf_opportunities: "Opportunities",
  smf_cautions: "Cautions",
  smf_remedyLabel: "Upay",
  smf_remedyFocused: "focused",
  smf_generated: "Generated",
  smf_pureEngine: "Pure Vedic engine — MD/AD/PD + house lords + natal placements.",
  smf_areaCareer: "Career",
  smf_areaFinance: "Finance",
  smf_areaHealth: "Health",
  smf_areaRelationship: "Relationship",
  smf_areaSpirituality: "Spirituality",
  dp_title: "🔮 Divya Prashna",
  dp_subtitle: "Apna sawaal pucho — turant Vedic jawab",
  dp_metaCity: "Bhubaneswar, Odisha · Server time",
  dp_quickQuestion: "Quick sawaal",
  dp_orType: "Ya apna sawaal type karo",
  dp_inputPh: "Jaise: Mera kho gaya phone milega kya?",
  dp_btnGetAnswer: "Jawab Pao",
  dp_alertEmptyTtl: "Sawaal likhein",
  dp_alertEmptyMsg: "Kya pucchna chahte ho woh likhein.",
  dp_errNoticeTtl: "⚠️ Suchana",
  dp_errQuotaPro: "Aaj ka prashna limit poora ho gaya. Pro upgrade karein.",
  dp_errSession: "Session khatm ho gayi. Punah login karein.",
  dp_errFetch: "Jawab nahi mil saka. Punah prayaas karein.",
  dp_btnSeeUpgrade: "Upgrade dekho →",
  dp_immatureTitle: "⚠️ Prashna abhi paripakv nahi",
  dp_refPrefix: "Ref",
  dp_retryAfter: "Punah prayaas",
  dp_minutesLater: "minute baad",
  dp_chartTitle: "📊 Prashna Chart",
  dp_chartLagna: "Lagna",
  dp_chartPlace: "Sthan",
  dp_chartCategory: "Vargi-karan",
  dp_cuspTitle: "🪔 Cusp Vishleshan",
  dp_houseSuffix: "Bhava",
  dp_subLord: "Sub-Lord",
  dp_starLord: "Star-Lord",
  dp_signifies: "Signifies houses",
  dp_classicalTitle: "📖 Aadhar Granth",
  dp_cat_stolen: "Sona / saaman milega?",
  dp_cat_partner: "Partner ke feelings",
  dp_cat_job: "Naukri lagegi?",
  dp_cat_marriage: "Shaadi kab?",
  dp_cat_health: "Bimari theek hogi?",
  dp_cat_litigation: "Mukadma jeetenge?",
  dp_cat_travel: "Yatra hogi?",
  dp_cat_general: "Aam sawaal",
  dp_pr_stolen: "Mera sona / paisa chori ho gaya, wapas milega ya nahi?",
  dp_pr_partner: "Mera partner mere bare me abhi kya soch raha hai?",
  dp_pr_job: "Mujhe yeh job / naya role milega ya nahi?",
  dp_pr_marriage: "Meri shaadi kab tak ho jayegi?",
  dp_pr_health: "Meri / mere apno ki bimari theek hogi?",
  dp_pr_litigation: "Mera mukadma main jeetunga ya nahi?",
  dp_pr_travel: "Meri planned yatra sampann hogi?",
  pk_headerTitle: "Prashna Kundli",
  pk_headerSub: "Simple chart Q&A · Ask se alag",
  pk_modeAsk: "Ask Anything",
  pk_modeNumber: "Prashna Kundli",
  pk_initMsg: "🔮 Pranam! Apna sawal seedha likhiye. Apne liye personal sawal → aapki D1 kundli + dasha se jawab. General jyotish theory → short simple answer. Yeh Ask Anything se alag hai.",
  pk_invalidNumber: "⚠️ Number 1 se 249 ke beech hona chahiye. Ek baar aur sochiye.",
  pk_qLimit: "Aaj ka prashna limit poora ho gaya. Subscription upgrade karein.",
  pk_genErr: "Kuch galti hui — phir try karein.",
  pk_netErr: "📡 Network error — internet check karke phir try karein.",
  pk_sankhyaPrefix: "Sankhya",
  pk_warnTitle: "Prashna kaal — saavdhani",
  pk_warnDefault: "Margdarshan-roop mein lijiye, antim nirnaay nahi.",
  pk_warnRef: "Aadhar",
  pk_forcedLagna: "Forced Lagna",
  pk_lblRashi: "Rashi",
  pk_lblNakshatra: "Nakshatra",
  pk_cuspKpTitle: "Cusp Analysis (KP Sub-Lord)",
  pk_houseWord: "House",
  pk_subLord: "Sub-Lord",
  pk_timingTitle: "⏳ Samay (Timing)",
  pk_classicalTitle: "📜 Shastriya Adhar",
  pk_numPlaceholder: "1 — 249",
  pk_numHint: "Sankhya sochiye",
  pk_qInputPh: "Apna prashna likhiye…",
  pk_cat_stolen: "Saaman milega?",
  pk_cat_partner: "Partner feelings",
  pk_cat_job: "Naukri lagegi?",
  pk_cat_marriage: "Shaadi kab?",
  pk_cat_health: "Bimari theek?",
  pk_cat_litigation: "Mukadma jeet?",
  pk_cat_travel: "Yatra hogi?",
  pk_cat_general: "Aam sawaal",
  fr_headerTitle: "Face Reading Pro",
  fr_heroEyebrow: "WORLD'S FIRST",
  fr_heroTitle: "Vedic + Science\nFace Reading Fusion",
  fr_heroSub: "40-page premium PDF report — 19 ancient + modern frameworks ka mela, storytelling style mein.",
  fr_priceLive: " · Live Now",
  fr_statPages: "pages",
  fr_statSections: "sections",
  fr_statEngines: "engines",
  fr_statLandmarks: "landmarks",
  fr_capInside: "INSIDE YOUR REPORT",
  fr_pv1Title: "Branded Cover",
  fr_pv1Sub: "Aapki photo · personalized seal",
  fr_pv2Title: "7-Zone Face Map",
  fr_pv2Sub: "Annotated landmarks + callouts",
  fr_pv3Title: "Visual Snapshot",
  fr_pv3Sub: "OCEAN radar + 5-score chart",
  fr_pv4Title: "Celeb Match",
  fr_pv4Sub: "Archetype × element library",
  fr_capEngines: "19 ANALYSIS ENGINES",
  fr_eng1Group: "Cosmic Intelligences",
  fr_eng1Body: "Samudrika Shastra · Mukha Lakshana · Lalat Rekha · Netra Vigyan · Ayurvedic Prakriti · Mian Xiang · 100-Year Age Map · Wu Xing 5 Elements",
  fr_eng2Group: "Scientific Engines",
  fr_eng2Body: "Anthropometry (32 pts) · Symmetry · Golden Ratio (φ) · fWHR · Health Indicators · Big Five OCEAN · First Impression · Phenotype Profile",
  fr_eng3Group: "Fusion Engines",
  fr_eng3Body: "Vedic-Science Cross-Validation · Numerology Combo · Predictive Synthesis (career, marriage, wealth, health)",
  fr_capHow: "HOW IT WORKS",
  fr_step1Title: "3 selfies upload karein",
  fr_step1Body: "Front + left + right profile (guided capture, lighting & angle check)",
  fr_step2Title: "468 landmarks nikaale jaate hain",
  fr_step2Body: "Google Mediapipe — privacy ke liye on-device chalta hai",
  fr_step3Title: "19 engines parallel analyze karte hain",
  fr_step3Body: "~75% real CV measurements · 0% fake ya hardcoded data",
  fr_step4Title: "40-page PDF banti hai",
  fr_step4Body: "Visual charts, face map, narrative · ~45 seconds mein ready",
  fr_capBuilt: "BUILT ON",
  fr_honest100: "100% Honest Data",
  fr_honest75: "75% real CV measurements",
  fr_honest20: "20% derived (real numbers + prose)",
  fr_honest5: "5% curated (celeb library, combo titles)",
  fr_honestFoot: "Zero fake ya hardcoded readings — sab kuch aapki actual photo se nikalta hai.",
  fr_ctaText: "Mera Face Reading Shuru Karein",
  fr_ctaSub: "3 selfies upload karein → 30-60 seconds mein 40-page PDF report aapke device pe.",
  fr_wipBadge: "Jald aa raha hai",
  fr_wipTitle: "Face Reading Pro abhi tayyar ho raha hai",
  fr_wipBody: "Hum Vedic + Science face-reading report aur 40-page PDF final kar rahe hain. Launch tak upload aur payment band hai.",
  fr_wipHint: "Agle app update ke baad Life Map se dobara check karein.",
  mdFaceReadingSubSoon: "Jald aa raha hai · Vedic + Science fusion",
  fu_introEyebrow: "STEP 1 OF 2",
  fu_introTitle: "3 selfies upload karein",
  fu_introSub: "Front + left + right profile. Achi roshni mein lein, chashma utar dein, baal forehead se hata lein.",
  fu_slotFrontLbl: "Front Selfie",
  fu_slotFrontHint: "Camera ki taraf seedha dekhein",
  fu_slotLeftLbl: "Left Profile",
  fu_slotLeftHint: "Apna left side camera ke saamne",
  fu_slotRightLbl: "Right Profile",
  fu_slotRightHint: "Apna right side camera ke saamne",
  fu_addedTap: "Added · tap to change",
  fu_capOptional: "OPTIONAL — BETTER ACCURACY",
  fu_lblAge: "Age",
  fu_phAge: "Jaise 28",
  fu_lblGender: "Gender",
  fu_male: "Male",
  fu_female: "Female",
  fu_lblLanguage: "Bhasha",
  fu_camPermNeeded: "Camera permission chahiye",
  fu_galPermNeeded: "Gallery permission chahiye",
  fu_couldNotPick: "Photo nahi mil saki",
  fu_addPhotoTtl: "Photo add karein",
  fu_addPhotoMsg: "Camera ya gallery se choose karein",
  fu_btnCamera: "Camera",
  fu_btnGallery: "Gallery",
  fu_btnCancel: "Cancel",
  fu_addAllFirst: "Pehle 3 photos add karein",
  fu_progUpload: "Photos upload kar rahe hain…",
  fu_progAnalyze: "19 engines analysis chal raha hai…",
  fu_progRender: "40-page PDF report ban rahi hai…",
  fu_progSub: "Yeh ~30-60 seconds le sakta hai. App ko close mat karein.",
  fu_errSomething: "Kuch galat hua",
  fu_doneTitle: "Report ready!",
  fu_doneSub: "40-page PDF generate ho gayi.",
  fu_btnOpenShare: "Open / Share PDF",
  fu_btnAnother: "Doosri report generate karein",
  fu_processing: "Processing…",
  fu_btnTryAgain: "Phir Try Karein",
  fu_btnGenerate: "Meri Report Generate Karein",
  fu_legalLine: "Aapki photos sirf analysis ke liye use hoti hain · 24 ghante ke baad auto-delete · server pe encrypted",
  fu_shareNotAvail: "Is device par sharing available nahi hai",
  fu_sessIdMissing: "Session ID server se nahi mili",
  fpp_headerTitle: "Cosmic Portrait",
  fpp_heroTitle: "Aapka Future Life Partner",
  fpp_heroSubMale: "Aapki kundli ke 30+ shastriya rules se uska roop, swabhav aur direction reveal hoga — D1, D9 Navamsa, D3 Drekkana, D30 Trimsamsa, KP 7th cuspal sub-lord, Upapada Lagna, Darakaraka, Arudha A7, Vargottama aur Ashtakavarga ka samuchit vishleshan.",
  fpp_heroSubFemale: "Aapki kundli ke 30+ shastriya rules se uski roop, swabhav aur direction reveal hoga — D1, D9 Navamsa, D3 Drekkana, D30 Trimsamsa, KP 7th cuspal sub-lord, Upapada Lagna, Darakaraka, Arudha A7, Vargottama aur Ashtakavarga ka samuchit vishleshan.",
  fpp_primaryKundli: "Primary kundli",
  fpp_btnReveal: "Mera Future Partner Reveal Karein",
  fpp_warnNoKundli: "Pehle apni primary kundli banayein. Profile → Add kundli.",
  fpp_infoTitle: "💎 Yeh kya batayega",
  fpp_b1: "Roop-rang: chehra, complexion, aankhein, baal, sharir",
  fpp_b2: "Swabhav: vibe, gun, stree/purush ke takat",
  fpp_b3: "Vyavsay ki disha (D10 + 7th lord)",
  fpp_b4: "Aapse umar ka antar (chhota / barabar / bada)",
  fpp_b5: "Disha jis or se aayega (East / North / etc.)",
  fpp_b6: "Ashtakavarga 7th bindu — attraction strength",
  fpp_disclaimer1: "* Yeh ek divya jhalak hai — shastriya signature ka kalatmak chitran. Vastavik vyakti se haru-bahu mel zaroori nahi. Vyaktitva, vibe aur disha shastriya rules par adhrit hain.",
  fpp_loadingTitle: "Cosmic Portrait taiyar ho raha hai",
  fpp_msgAlign: "Sitaare align ho rahe hain...",
  fpp_msgAlignFull: "Aapki kundli sitaaron ke saath align ho rahi hai...",
  fpp_msgComputing: "Pehle aapki kundli compute kar raha hu...",
  fpp_msgKundliQuota: "Aapka kundli quota khatam ho gaya. Subscription upgrade karein.",
  fpp_msgKundliFail: "Kundli compute nahi ho saki. Network check karke punah prayaas karein.",
  fpp_msgTaskExpire: "Task expire ho gaya. Punah shuru karein.",
  fpp_msgTaskIdMiss: "Task ID nahi mila. Punah prayaas karein.",
  fpp_msgNetSlow: "Network slow hai. Internet check karke punah prayaas karein.",
  fpp_msgStarsBusy: "Sitaare abhi vyast hain",
  fpp_tipText: "Pls wait... Sitaare aapke jeevansaathi ki essence padh rahe hain.\nLag-bhag 15-25 sec lagenge.",
  fpp_btnCancel: "Cancel",
  fpp_imgFailed: "Image taiyar nahi ho saki.",
  fpp_imgBadge: "✨ COSMIC PORTRAIT — DIVYA JHALAK",
  fpp_traitTitle: "🌟 Roop-rang & Swabhav",
  fpp_lblFace: "Chehra",
  fpp_lblComplexion: "Complexion",
  fpp_lblBuild: "Build",
  fpp_lblEyes: "Aankhein",
  fpp_lblEyebrows: "Bhauein",
  fpp_lblNose: "Naak",
  fpp_lblLips: "Honth",
  fpp_lblHair: "Baal",
  fpp_lblVibe: "Vibe",
  fpp_vargottama: "✨ Vargottama amplified — features especially harmonious",
  fpp_practTitle: "🧭 Practical Insights",
  fpp_lblAge: "Umar",
  fpp_lblDirection: "Disha",
  fpp_lblProfHint: "Vyavsay hint",
  fpp_lblAttraction: "Attraction",
  fpp_classicalTtl: "📜 Shastriya Adhar",
  fpp_disclaimer2: "* Cosmic Portrait — divya jhalak. Yeh ek kalatmak vishleshan hai jo aapki kundli ke 7th house, D9 Navamsa, KP cusp aur Jaimini ke Upapada/Arudha sutron par adhrit hai. Vastavik chehre se haru-bahu mel ho ya na ho — vyaktitva, vibe aur disha sahi hogi.",
  fpp_btnRevealAgain: "Phir Reveal Karein",
  fpp_errTitle: "Cosmic Portrait abhi taiyar nahi",
  fpp_errDefault: "Sitaare abhi vyast hain. Kuch der baad punah prayaas karein.",
  fpp_errPortraitFail: "Cosmic Portrait abhi taiyar nahi ho saka.",
  fpp_btnTryAgain: "Punah Prayaas Karein",
  fpp_alertBirthTtl: "Birth details zaroori hain",
  fpp_alertBirthMsg: "Apni primary profile me birth date/time/place pehle add karein, fir Cosmic Portrait reveal karein.",
  fpp_errTimeout: "Sitaaron ki gehri jaanch me samay zyada lag gaya. Punah prayaas karein.",
  lg_title: "Legal & Policies",
  lg_subtitle: "Privacy, terms, refund aur disclaimer",
  lg_lastUpdated: "17 April 2026",
  lg_h_privacy: "Privacy Policy",
  lg_p_privacyIntro: "Cosmic Lens (\"we\", \"us\", \"our\") aapki privacy ka samman karta hai. Ye Privacy Policy bataati hai ki jab aap hamari mobile application aur related services (\"Service\") use karte ho, hum kaunsi personal information collect karte hain, use kaise istemal karte hain, aur aapke paas kya choices hain. Cosmic Lens use karke aap niche likhi practices se sahmat hote ho.",
  lg_callout_privacy: "Hum aapka personal data NAHI bechte. Hum aapki kundli, birth details, ya chat history advertisers ke saath share nahi karte.",
  lg_s1_title: "1. Hum kaunsi Information collect karte hain",
  lg_s1_a: "(a) Account information — naam, email address, mobile number (agar phone se signup karein), Google account ID (agar Google Sign-In use karein). Hashed passwords (scrypt) ke saath surakshit store kiya jaata hai.",
  lg_s1_b: "(b) Birth aur profile data — poora naam, janma tithi, janma samay, janma sthal, gender, aur language preference. Ye aapki Vedic kundli ki ganana ke liye minimum zaroori hai.",
  lg_s1_c: "(c) Generated content — aapki kundli charts, dashas, compatibility reports, Jyotish question/answer history, aur saved profiles.",
  lg_s1_d: "(d) Payment information — poori tarah hamare payment processor Cashfree Payments ke through handle hoti hai. Hum sirf order ID, plan, amount aur success/failure status store karte hain. Hum kabhi card numbers, UPI PINs, CVVs ya banking credentials store nahi karte.",
  lg_s1_e: "(e) Device aur technical information — device model, OS version, app version, language, time zone, aur crash logs. Sirf diagnostics ke liye use karte hain.",
  lg_s2_title: "2. Hum aapki Information kaise use karte hain",
  lg_s2_b1: "Aapka account banane aur maintain karne ke liye.",
  lg_s2_b2: "Aapki kundli, dashas, doshas, compatibility aur dusri astrological reports compute karne ke liye.",
  lg_s2_b3: "Aapke sawalon ke Jyotish-based jawab dene ke liye, sirf aapki kundli data se — aapki identity se nahi.",
  lg_s2_b4: "Cashfree ke through subscription payments process karne ke liye.",
  lg_s2_b5: "Daily question limits aur fair-usage rules lagaane ke liye.",
  lg_s2_b6: "Optional notifications bhejne ke liye (daily horoscope, panchang, muhurat reminders) — Settings me disable kar sakte ho.",
  lg_s2_b7: "Fraud rokne, crashes debug karne aur service quality improve karne ke liye.",
  lg_s2_b8: "Legal obligations poori karne ke liye.",
  lg_s3_title: "3. Third-Party Services",
  lg_s3_intro: "Hum in trusted partners ke saath sirf zaroori minimum data share karte hain:",
  lg_s3_b1: "Google Sign-In — agar aap Google login chunte ho to aapki identity verify karta hai. Humein aapka naam, email aur Google ID milti hai.",
  lg_s3_b2: "Cashfree Payments (India) — UPI, card aur net-banking transactions process karta hai. PCI-DSS Level 1 compliant.",
  lg_s3_b3: "Expo / Google Play Services — sirf push notification delivery. Wo koi content nahi padhte.",
  lg_s3_b4: "Cloud hosting (Replit / AWS) — jahan possible ho India region me encrypted database storage.",
  lg_s3_outro: "In services ki apni privacy policies hain jo aap padhne ke liye encourage karte hain.",
  lg_s4_title: "4. Data Retention",
  lg_s4_p: "Jab tak aapka account active hai tab tak aapka account aur kundli data retain karte hain. Account delete karne par (Section 7 dekho) aapka personal data 30 din me permanently mita diya jaata hai, jahan retention legally zaroori ho (jaise Indian law ke under tax invoices 7 saal) usko chhodkar.",
  lg_s5_title: "5. Data Security",
  lg_s5_b1: "Sara API traffic TLS 1.2+ se encrypted hai.",
  lg_s5_b2: "Passwords scrypt se hashed hote hain (kabhi plain text me store nahi hote).",
  lg_s5_b3: "API access har request par per-user API key validate karta hai.",
  lg_s5_b4: "Database backups rest par encrypted hote hain.",
  lg_s5_b5: "Production data ka access sirf authorised engineers tak limited hai.",
  lg_s6_title: "6. Aapke Rights",
  lg_s6_intro: "Digital Personal Data Protection Act, 2023 (India) aur similar laws ke under, aapke paas ye rights hain:",
  lg_s6_b1: "Hum aapke baare me jo personal data rakhte hain use access karna.",
  lg_s6_b2: "Galat ya purani information correct karna.",
  lg_s6_b3: "Consent withdraw karna aur account delete karna.",
  lg_s6_b4: "Apni kundli data ka JSON format me export lena.",
  lg_s6_b5: "Data Protection Board of India me shikayat darj karwana.",
  lg_s6_outro: "In rights ka istemal karne ke liye, support@cosmiclens.app par email karein.",
  lg_s7_title: "7. Account Delete karna",
  lg_s7_p: "Aap kabhi bhi Profile → Delete Account se account delete kar sakte ho. Deletion permanent hai aur 30 din ke andar saari profiles, kundlis, chat history aur personal data hata deta hai.",
  lg_s8_title: "8. Bachche",
  lg_s8_p: "Cosmic Lens 13 saal se kam ke bachchon ke liye nahi hai. Hum jaan-bujhkar bachchon ka personal data collect nahi karte. Agar lagta hai kisi bachche ne account banaya hai, hamse contact karein, hum turant delete kar denge.",
  lg_s9_title: "9. International Users",
  lg_s9_p: "Cosmic Lens India se operate hota hai. Agar aap Service ko India ke bahar se access karte ho, aapki information India me transfer aur process hogi, jahan data-protection laws aapke desh se alag ho sakte hain.",
  lg_s10_title: "10. Is Policy me Badlav",
  lg_s10_p: "Hum is Privacy Policy ko samay-samay par update kar sakte hain. Top par \"Last updated\" date latest changes dikhayegi. Material changes in-app me kam se kam 7 din pehle batayi jaayengi.",
  lg_s11_title: "11. Humse Contact karein",
  lg_s11_intro: "Privacy se related questions, requests ya grievances ke liye:",
  lg_s11_b1: "Email: support@cosmiclens.app",
  lg_s11_b2: "Grievance Officer: shikayat milne ke 30 din ke andar uplabdh",
  lg_h_terms: "Terms of Service",
  lg_p_termsIntro: "Ye Terms of Service (\"Terms\") Cosmic Lens mobile application aur related services (\"Service\") ke aapke access aur use ko govern karti hain. Account banakar, download karke ya Service use karke aap in Terms ko accept karte ho. Agar sahmat nahi ho, to Service istemal na karein.",
  lg_t1_title: "1. Eligibility",
  lg_t1_b1: "Cosmic Lens use karne ke liye aap kam se kam 13 saal ke hone chahiye.",
  lg_t1_b2: "Agar 18 saal se kam ho, to maa-baap ya guardian ki permission honi chahiye.",
  lg_t1_b3: "Aap confirm karte hain ki di gayi information (naam, janma tithi, samay, sthal) sahi aur accurate hai. Galat birth data se galat astrological results milenge.",
  lg_t2_title: "2. Account aur Security",
  lg_t2_b1: "Login credentials safe rakhne ki zimmedari aapki hai.",
  lg_t2_b2: "Aap apna account share nahi kar sakte ya kisi aur ka account use nahi kar sakte.",
  lg_t2_b3: "Kisi bhi unauthorised access ke baare me hamein turant batayein.",
  lg_t2_b4: "Hum un accounts ko suspend karne ka right rakhte hain jo fraud, abuse ya in Terms ka violation karte hain.",
  lg_t3_title: "3. Service",
  lg_t3_p: "Cosmic Lens Vedic-astrology computations deta hai jaise kundli, dashas, doshas, vivah compatibility, panchang, muhurat, numerology, vastu, lucky elements, aur Jyotish-based question answering. Calculations traditional Vedic principles (Lahiri ayanamsa) follow karte hain accurate ephemeris data ke saath.",
  lg_t4_title: "4. Subscription Plans",
  lg_t4_intro: "Cosmic Lens ye plans deta hai:",
  lg_t4_b1: "Free — limited features, 1 Jyotish question/din",
  lg_t4_b2: "7-din Free Trial — naye users ke liye Basic features, ek baar, koi payment nahi",
  lg_t4_b3: "Basic — ₹199/maah ya ₹1,799/saal, 10 Jyotish questions/din aur basic analysis",
  lg_t4_b4: "Pro — ₹399/maah ya ₹2,999/saal, unlimited Jyotish questions, full deep analysis, 6-maah timeline, karmic insights, PDF reports",
  lg_t4_outro: "Subscriptions har billing period ke end par auto-renew hoti hain, jab tak renewal se kam se kam 24 ghante pehle cancel na ki jaayein. Aap Profile → Subscription → Cancel se ya support se contact karke kabhi bhi cancel kar sakte ho.",
  lg_t5_title: "5. Payments",
  lg_t5_p: "Payments Cashfree Payments dwara process hote hain. Purchase karke aap hamari aur Cashfree dono ki terms se sahmat hote ho. Saari prices Indian Rupees (₹) me hain aur applicable GST sahit.",
  lg_t6_title: "6. Refund Policy",
  lg_t6_p: "Poori details ke liye niche Refund & Cancellation section dekhein. Summary me, saari sales generally final hain, lekin technical failures, double-charges ya payment ke 7 din ke andar unused service ke liye refunds mil sakte hain.",
  lg_t7_title: "7. User Conduct — Aap NAHI karenge",
  lg_t7_b1: "Service ka koi illegal ya fraudulent kaam ke liye use karna.",
  lg_t7_b2: "Service ko reverse-engineer, decompile ya scrape karna.",
  lg_t7_b3: "Bots, scripts ya automated tools se free ya trial features ka galat istemal karna.",
  lg_t7_b4: "Service ka content resell, sublicense ya republish karna.",
  lg_t7_b5: "Bina consent ke kisi aur ke birth data ko galat tarah submit karna.",
  lg_t7_b6: "Doosron ko harass, threaten ya impersonate karna.",
  lg_t8_title: "8. Intellectual Property",
  lg_t8_p: "Service me saara content, design, code, branding, algorithms aur computed reports Cosmic Lens ya uske licensors ki intellectual property hain. Aapko sirf personal, non-commercial use ke liye limited, non-exclusive, non-transferable licence milta hai.",
  lg_t9_title: "9. Engine-Generated Answers",
  lg_t9_p: "\"Ask\" feature aapki kundli ka rule-based aur generative analysis use karta hai. Jyotish answers software dwara banaye jaate hain aur unme errors, ambiguities ya contradictions ho sakte hain. Ye professional advice ka substitute NAHI hain.",
  lg_t10_title: "10. Professional Advice nahi hai",
  lg_t10_callout: "Cosmic Lens sirf spiritual aur entertainment purposes ke liye hai. Astrological insights professional medical, legal, financial, psychological ya relationship advice ka substitute NAHI hain. Important life decisions ke liye hamesha qualified professionals se consult karein.",
  lg_t11_title: "11. Disclaimers",
  lg_t11_p: "Service \"as is\" aur \"as available\" ke roop me di jaati hai, koi express ya implied warranties ke bina. Hum guarantee nahi dete ki astrological predictions sach hongi, Service error-free hogi ya hamesha available hogi. Kisi prediction ki past performance future results indicate nahi karti.",
  lg_t12_title: "12. Liability ki Seema",
  lg_t12_p: "Law dwara maximum extent tak, Cosmic Lens, iske officers, employees aur partners aapke Service use se utpann kisi indirect, incidental, consequential ya punitive damages ke liye liable nahi honge. Kisi claim ke liye hamari total liability claim se 12 maah pehle aapne hamein jo paid kiya, ya ₹1,000, jo zyada ho, tak limited hai.",
  lg_t13_title: "13. Termination",
  lg_t13_p: "Aap kabhi bhi account delete karke Service use karna band kar sakte ho. Agar aap in Terms ka violation karte ho ya doosre users ya Service ke liye harmful conduct karte ho, hum aapka access turant suspend ya terminate kar sakte hain.",
  lg_t14_title: "14. Terms me Badlav",
  lg_t14_p: "Hum in Terms ko periodically update kar sakte hain. Changes effective hone ke baad Service use jaari rakhna nayi Terms ka acceptance maana jaayega. Material changes in-app me kam se kam 7 din pehle notify ki jaayengi.",
  lg_t15_title: "15. Governing Law aur Jurisdiction",
  lg_t15_p: "Ye Terms India ke laws se govern hoti hain. In Terms ya Service se utpann ya related koi bhi disputes aapke registered city, India ke courts ke exclusive jurisdiction me honge.",
  lg_t16_title: "16. Contact",
  lg_t16_p: "In Terms ke baare me sawaalon ke liye, support@cosmiclens.app par email karein.",
  lg_h_refund: "Refund aur Cancellation",
  lg_p_refundIntro: "Cosmic Lens me hum chahte hain har member ka achha experience ho. Ye policy bataati hai ki subscription fees kab refundable hain aur subscription kaise cancel karein.",
  lg_callout_refund: "Subscribe karne se pehle 7-day Free Trial use karein — ye aapko Basic features ka experience bina koi cost ke deta hai, taaki paise dene se pehle aap decide kar sako.",
  lg_r1_title: "1. Subscription Cancellation",
  lg_r1_intro: "Aap monthly ya yearly subscription kabhi bhi cancel kar sakte ho:",
  lg_r1_b1: "Profile → Subscription kholein aur \"Cancel Subscription\" tap karein.",
  lg_r1_b2: "Ya apni registered email se support@cosmiclens.app par email karein.",
  lg_r1_outro: "Cancellation ke baad current billing period ke end tak premium access milta rahega. Aage koi charges nahi liye jaayenge.",
  lg_r2_title: "2. Refunds kab milte hain",
  lg_r2_intro: "In situations me hum full ya pro-rated refund denge:",
  lg_r2_b1: "Double charge / duplicate payment — duplicate amount ka full refund, 5–7 business days me process.",
  lg_r2_b2: "Payment successful par plan activate nahi hua — full refund ya manual plan activation, aapki choice.",
  lg_r2_b3: "Technical failure jiski wajah se 72 ghante se zyada access nahi mila — unused days ka pro-rated refund.",
  lg_r2_b4: "Pehle paid subscription ke 7 din ke andar cancellation, agar 5 se kam paid features use kiye hain — full refund (per user ek baar).",
  lg_r3_title: "3. Refunds kab NAHI milte",
  lg_r3_b1: "7-din window ke baad change of mind.",
  lg_r3_b2: "Astrological prediction sach nahi nikli — predictions interpretive guidance hain, guarantee nahi (Disclaimer dekho).",
  lg_r3_b3: "Auto-renewal se pehle cancel karna bhool gaye — par hum request par future renewals turant cancel kar denge.",
  lg_r3_b4: "Mid-cycle me cancel ki gayi monthly plans ke partial-month refunds.",
  lg_r3_b5: "Free ya Trial plans ke refunds (koi payment hi nahi hua).",
  lg_r3_b6: "Payment ke 30 din se zyada baad refund request.",
  lg_r4_title: "4. Refund Request Kaise Karein",
  lg_r4_intro: "support@cosmiclens.app par ye saath bhejein:",
  lg_r4_b1: "Aapki registered email address ya mobile number",
  lg_r4_b2: "Order ID (Profile → Subscription → Payment History me dikhti hai)",
  lg_r4_b3: "Refund request ka reason",
  lg_r4_outro: "Hum saari refund requests ka 3 business days me jawab dete hain. Approved refunds Cashfree dwara aapke original payment method par 5–10 business days me process hote hain.",
  lg_r5_title: "5. Failed Payments",
  lg_r5_p: "Agar payment fail ho jaaye, koi charge nahi hota. Agar bank \"pending\" charge dikhata hai, to RBI guidelines ke according 5–7 business days me automatically reverse ho jaata hai. Inke liye humse contact karne ki zaroorat nahi.",
  lg_r6_title: "6. Subscription Auto-Renewal",
  lg_r6_p: "Monthly aur yearly plans automatically renew hote hain. Hum har renewal se pehle email ya in-app notification se reminder bhejenge. Renewal rokne ke liye, bas renewal date se pehle cancel karein — koi charge nahi hoga.",
  lg_r7_title: "7. Chargebacks",
  lg_r7_p: "Agar aap pehle humse contact karne ki jagah seedha bank ke through chargeback initiate karte ho, to aapka account investigation pending suspend ho jaayega. Hum hamesha issues directly resolve karna prefer karte hain — pehle hamein email karein.",
  lg_r8_title: "8. Refunds ke liye Contact",
  lg_r8_b1: "Email: support@cosmiclens.app",
  lg_r8_b2: "Subject line: \"Refund Request — [Order ID]\"",
  lg_r8_b3: "Response time: 3 business days me",
  lg_h_disclaimer: "Astrology Disclaimer",
  lg_callout_disc: "Cosmic Lens sirf spiritual exploration, self-reflection aur entertainment purposes ke liye hai. Ye professional medical, legal, financial, psychological ya relationship advice ka substitute nahi hai.",
  lg_d1_title: "1. Astrology ka Swaroop",
  lg_d1_p: "Vedic astrology (Jyotish) ek pracheen kala aur philosophical parampara hai. Cosmic Lens me di gayi interpretations, predictions, dashas, doshas, muhurats aur remedies classical principles aur modern algorithmic analysis ko reflect karti hain. Ye nature me interpretive hain aur scientifically verifiable nahi hain.",
  lg_d2_title: "2. Koi Guaranteed Outcomes nahi",
  lg_d2_p: "Koi bhi astrological prediction ya insight sach hone ki guarantee nahi hai. Jeevan me outcomes kayi factors par depend karte hain — aapki free will, choices, actions, environment aur circumstances — jise astrology poori tarah nahi pakad sakti.",
  lg_d3_title: "3. Professionals ka Substitute Nahi",
  lg_d3_intro: "Cosmic Lens content ko important life decisions ke liye sole basis ke roop me KABHI use nahi karna chahiye. Hamesha appropriate qualified professionals se consult karein:",
  lg_d3_b1: "Health concerns — registered medical doctor se milein. Astrological readings ke aadhar par medication band ya badlein nahi.",
  lg_d3_b2: "Mental health — licensed psychologist ya psychiatrist se baat karein. Crisis me ho to iCall (India) 9152987821 ya apni local helpline call karein.",
  lg_d3_b3: "Legal matters — qualified lawyer se consult karein.",
  lg_d3_b4: "Financial / investment decisions — SEBI-registered investment advisor se consult karein.",
  lg_d3_b5: "Relationship aur marriage — counsellor se consult karein; compatibility scores kabhi bhi open communication aur consent ko replace nahi karne chahiye.",
  lg_d4_title: "4. Engine-Generated Content",
  lg_d4_p: "\"Ask\" feature aapki kundli analyse karne ke liye automated software (rule-based engine) use karta hai. Answers code dwara generate hote hain aur unme errors, omissions, contradictions ya culturally inappropriate phrasing ho sakti hai. Ye kisi individual astrologer dwara endorsed nahi hain.",
  lg_d5_title: "5. Upay (Remedies)",
  lg_d5_p: "Suggest kiye gaye upay (mantras, ratan, daan, vrat, pujas) classical granthon se liye gaye hain. Inko follow karne se kisi specific result ki guarantee hum nahi dete. Koi bhi upay apnaane se pehle qualified Vedic astrologer ya guru se consult karein, khaaskar ratan aur beej mantras.",
  lg_d6_title: "6. Birth-Data Sahi hona",
  lg_d6_p: "Astrological calculations aapke janma samay aur sthal ke prati bahut sensitive hain. Sirf 4-minute ki error bhi aapka ascendant badal sakti hai. Hum recommend karte hain ki janma samay hospital record ya birth certificate se verify karein. Galat input se galat results aayenge.",
  lg_d7_title: "7. Cultural aur Regional Antar",
  lg_d7_p: "Cosmic Lens traditional Vedic (Lahiri / Chitrapaksha) ayanamsa use karta hai. Western, Tropical, KP, Krishnamurti aur Tantric astrologers alag systems use kar sakte hain aur alag conclusions nikal sakte hain. Inme se koi bhi system \"galat\" nahi hai — ye alag lenses hain.",
  lg_d8_title: "8. Emergency Situations",
  lg_d8_callout: "Agar aap medical emergency ya self-harm ke vicharon ka anubhav kar rahe hain, kripaya turant apni local emergency services call karein. Crisis support ke liye is app par bharosa na karein. India: 112 (emergency), iCall 9152987821 (mental health).",
  lg_d9_title: "9. Sweekriti",
  lg_d9_p: "Cosmic Lens use karke aap acknowledge karte hain ki aapne ye disclaimer padhi aur samjhi hai aur Service ko responsibly use karne ke liye sahmat hain.",
  bv_headerTitle: "Business Vastu",
  bv_cardTitle: "Premium Business Vastu",
  bv_cardBody: "Apne premise layout ko owner Kundli aur active Mahadasha ke saath jodkar ek personalised lifetime priority plan paayein.",
  bv_cardBodySmall: "Aapke vyapar sthal ko swami ki Kundli aur chal rahi Mahadasha ke saath milakar ek vyaktigat sudhar yojana banayi jaati hai.",
  bv_secBizType: "Business Type",
  bv_secPremiseName: "Sthal ka Naam",
  bv_phPremiseName: "jaise Andheri Shop, Powai HQ",
  bv_premiseHint: "Zaroori hai — aapka one-time unlock isi premise name se match hota hai.",
  bv_refineRooms: "Optional: Rooms Refine karein",
  bv_premiseLayout: "Sthal Layout",
  bv_engineWillDetect: "Photo Engine aapke upload se rooms detect karega. Aap yahan rooms list karke override bhi kar sakte ho.",
  bv_lblDirection: "Disha:",
  bv_selectDirection: "Disha chunein",
  bv_addRoom: "Room joden (★ = critical)",
  bv_runScanPrefix: "Chalaayein",
  bv_runScanSuffix: "Vastu Scan",
  bv_biz_shop: "Dukaan",
  bv_biz_office: "Office",
  bv_biz_factory: "Karkhana",
  bv_dir_N: "Uttar",
  bv_dir_NE: "Ishan",
  bv_dir_E: "Poorv",
  bv_dir_SE: "Agneya",
  bv_dir_S: "Dakshin",
  bv_dir_SW: "Nairutya",
  bv_dir_W: "Paschim",
  bv_dir_NW: "Vayavya",
  bv_room_entrance: "Pravesh",
  bv_room_owner_seat: "Swami Sthaan",
  bv_room_cash_counter: "Golak",
  bv_room_billing_counter: "Billing Counter",
  bv_room_vault: "Tijori",
  bv_room_stock_storage: "Bhandaar",
  bv_room_display: "Pradarshan",
  bv_room_pooja: "Mandir / Pooja",
  bv_room_back_office: "Peeche Office",
  bv_room_staff_room: "Staff Room",
  bv_room_toilet: "Shauchalaya",
  bv_room_owner_cabin: "Swami Cabin",
  bv_room_reception: "Swagat",
  bv_room_conference: "Sammelan",
  bv_room_accounts: "Lekha",
  bv_room_server_room: "Server Kaksh",
  bv_room_pantry: "Pantry",
  bv_room_machinery: "Yantra",
  bv_room_heavy_machine: "Bhari Yantra",
  bv_room_raw_storage: "Kachcha Maal",
  bv_room_finished_goods: "Tayar Maal",
  bv_room_boiler: "Boiler",
  bv_room_labour_quarter: "Shramik",
  bv_errAuthRequired: "Business Vastu scan chalaane ke liye kripaya login karein.",
  bv_errValidationRooms: "Kam se kam 2 room photos joden, ya apna full shop floor plan PDF upload karein.",
  bv_btnUploadShopPdf: "Full Shop PDF Upload",
  bv_btnUploadOfficePdf: "Full Office PDF Upload",
  bv_btnUploadOfficePhoto: "Office Room Photo Upload",
  bv_btnUploadFactoryPdf: "Full Factory PDF Upload",
  bv_btnUploadFactoryPhoto: "Factory Photo Upload",
  bv_planNorthHint: "Is plan par North kahan hai?",
  bv_secUploadedPhotos: "Upload ki gayi Photos",
  bv_btnSubmitReview: "Pay Now",
  bv_submitSuccessTitle: "Admin ko bhej diya",
  bv_submitSuccessBody: "Hamare Vastu expert aapki photos review karke 24–48 ghante me report taiyar karenge.",
  bv_errValidationName: "Apne sthal ka naam dein (jaise 'Andheri Shop') — unlock match karne ke liye zaroori hai.",
  bv_errUnlockTitle: "Unlock Zaroori",
  bv_errProfileTitle: "Apni profile poori karein",
  bv_errValidTitle: "Apne inputs check karein",
  bv_errScanFailed: "Scan fail ho gaya",
  bv_errTryAgain: "Kripaya phir se try karein.",
  bv_btnCompleteProfile: "Profile Poori Karein",
  bv_walletHintPrefix: "Upar wallet se unlock karein",
  bv_walletHintSuffix: "Vastu (lifetime).",
  bv_overallScore: "OVERALL PREMISE SCORE",
  bv_grade: "Grade",
  bv_pdfReady: "Detailed PDF Report Tayyar",
  bv_pdfBodyHi: "Aapka full Business Vastu report PDF me ready hai — room-by-room verdict, Mahadasha alert, stakeholder synergy, priority actions sab kuch.",
  bv_pdfBodyEn: "Aapki full Business Vastu report PDF ke roop me available hai — kholein, save karein ya share karein.",
  bv_btnOpenPdf: "PDF Report Kholein",
  bv_footerBrand: "Powered by Advanced Cosmic Intelligence",
  bv_lblIdeal: "Ideal",
  bv_lblAcceptable: "Acceptable",
  bv_lblAdjust: "Adjust",
  bv_lblAvoid: "Avoid",
  bv_lblOwnerMd: "Owner Mahadasha",
  bv_lblStakeholder: "Stakeholder Sahyog",
  bv_lblMuhuratAlign: "Muhurat Alignment",
  bv_secPriority: "Priority Actions",
  bv_lblCritical: "★ CRITICAL",
  bv_secRoomByRoom: "Kamra-dar-Kamra",
  bv_lblZone: "Kshetra:",
  bv_secClassicalRefs: "CLASSICAL REFERENCES",
  avp_headerTitle: "Home Vastu Premium",
  avp_heroTitle: "Home Vastu Premium",
  avp_heroBody: "Kya scan karna hai chunein — ek room ki photo, ya poora ghar ka floor plan. Aapki Kundli ke hisaab se personalised Vastu guidance aur clear next steps milenge.",
  avp_modeCameraTitle: "Home Vastu",
  avp_modeCameraSub: "Ek room (camera)",
  avp_modeSingleTitle: "Ek Room",
  avp_modeSingleSub: "Photo / PDF",
  avp_modeWholeTitle: "Full Home Plan",
  avp_modeWholeSub: "Poora ghar (PDF/JPG)",
  avp_introCameraTitle: "Home Vastu — Live Camera",
  avp_introCameraBody: "Ye sirf ek room ke liye hai. Room name chunein, camera kholein, us room ke andar khade hon aur photo lein — shutter time par compass direction lock kar deta hai.",
  avp_pickerLabel: "Ye photo kis room ki hai?",
  avp_pickerHint: "Camera enable karne ke liye upar room chunein.",
  avp_camHintPrefix: "Camera + compass · Photo le rahe",
  avp_camHintNoRoom: "Pehle room chunein",
  avp_btnSmartScan: "Camera Kholein",
  avp_btnUploadPhoto: "Room Photo Upload",
  avp_btnUploadHomePdf: "Full Home PDF Upload",
  avp_badgeSingleRoom: "Ek room",
  avp_badgeWholeHome: "Poora ghar",
  avp_uploadPricePerRoom: "per room",
  avp_uploadPaySubmit: "₹{amount} Pay karein",
  avp_uploadSubmitted: "Ho gaya! My Reports check karein.",
  avp_introSingleTitle: "Ek Room — Photo ya PDF",
  avp_introSingleBody: "Ghar par nahi ho? Gallery se photo ya PDF chunein aur room + direction manually tag karein. Tab best jab aap kisi ek room ko check karna chahte ho.",
  avp_introWholeTitle: "Full Home Plan — Photo Engine",
  avp_introWholeBody: "Poore ghar ka floor plan (architect PDF/JPG) upload karein. Photo Engine rooms detect karke ek consolidated direction-wise report banata hai, aapki kundli ke hisaab se.",
  avp_btnRunWhole: "Full Home Scan Chalayein",
  avp_btnAnalysing: "Analyse ho raha hai…",
  avp_room_bedroom: "Bedroom",
  avp_room_kitchen: "Kitchen",
  avp_room_pooja: "Pooja",
  avp_room_living: "Baithak",
  avp_room_bathroom: "Bathroom",
  avp_room_entrance: "Pravesh",
  avp_room_study: "Adhyayan",
  avp_room_store: "Bhandaar",
  avp_errAuthRequired: "Smart Scan chalaane ke liye kripaya login karein.",
  avp_errMonthlyLimit: "Maasik limit poori",
  avp_errUpgradeReq: "Upgrade zaroori",
  avp_errProfile: "Apni profile poori karein",
  avp_errVisionNoRoom: "Ye photo padhi nahi ja saki",
  avp_errScanFailed: "Smart Scan fail ho gaya",
  avp_errBodyDefault: "Apne floor plan ya poore room ki saaf photo try karein.",
  avp_btnCompleteProfile: "Profile Poori Karein",
  avp_btnUpgradePro: "Pro me Upgrade — Unlimited",
  avp_overallScore: "OVERALL HOUSE SCORE",
  avp_pdfReady: "Detailed PDF Report Tayyar",
  avp_pdfBody: "Aapka full AstroVastu PRO report PDF me ready hai — har room ka deep verdict, Mahadasha layer, priority actions aur classical references.",
  avp_btnOpenPdf: "PDF Report Kholein",
  avp_footerBrand: "Powered by Advanced Cosmic Intelligence",
  avp_secPriority: "PRIORITY ACTIONS",
  avp_secRoomByRoom: "KAMRA-DAR-KAMRA BREAKDOWN",
  avp_lblMdAlert: "Mahadasha Alert",
  avp_quotaUnlimited: "Unlimited PRO scans (Pro plan)",
  avp_quotaPrefix: "Scan",
  avp_quotaThisMonth: "is maah",
  avp_brandFooter: "✨ Powered by Advanced Cosmic Intelligence",
  avp_brandFooterSub: "Cosmic AstroVastu Drishti — PRO Engine v1.0",
  avp_lblIdeal: "Ideal",
  avp_lblAcceptable: "Acceptable",
  avp_lblAdjust: "Adjust",
  avp_lblAvoid: "Avoid",
  avr_emptyTitle: "Koi report load nahi hui",
  avr_emptyBody: "Yahaan result dekhne ke liye pehle Smart Scan chalayein.",
  avr_btnOpenPro: "AstroVastu PRO Kholein",
  avr_headerTitle: "Aapki AstroVastu Report",
  avr_outOf100: "100 me se",
  avr_grade: "Grade",
  avr_btnOpenPdf: "PDF Kholein",
  avr_btnWhatsApp: "WhatsApp",
  avr_secPriorityHi: "SABSE PEHLE YE 3 CHEEZEIN THEEK KARO",
  avr_secRoomByRoom: "KAMRA-DAR-KAMRA",
  avr_brandFooter: "✨ Powered by Advanced Cosmic Intelligence",
  avr_shareTitle: "🪔 *AstroVastu PRO Report*",
  avr_shareScoreLbl: "📊 Score:",
  avr_shareOpenLbl: "📄 Report kholein:",
  avr_shareBrandLbl: "_Powered by Advanced Cosmic Intelligence_",
  avr_alertShareErr: "Share nahi ho saka",

  // Risk Radar — Lucky / Best-Avoid Time card (Hinglish — original brand voice)
  rrLuckyAajShubhAnk:        "AAJ KA SHUBH ANK",
  rrLuckyAajShubhRang:       "AAJ KA SHUBH RANG",
  rrLuckyShubhAnk:           "SHUBH ANK",
  rrLuckyShubhRang:          "SHUBH RANG",
  rrLuckyBestTime:           "⏰ BEST TIME",
  rrLuckyAvoidTime:          "🚫 AVOID TIME",
  rrLuckyPoweredBy:          "✨ Powered by Advanced Cosmic Intelligence",
  rrLuckyHeaderToday:        "AAJ KA SHUBH ANK + RANG",
  rrLuckyHeaderOther:        "SHUBH ANK + RANG",
  rrLuckyCalculating:        "Aapka shubh ank aur rang calculate ho raha hai…",
  rrLuckyCreateKundliPrompt: "Apni kundli banayein — aapke janm ke nakshatra se aaj ka personal shubh ank aur rang dekhein.",
  rrLuckyCreateKundliCta:    "KUNDLI BANAYEIN →",
  rrLuckyDetailsUnavail:     "Lucky details abhi available nahi hain.",
  rrLuckyDayUnavail:         "Is din ke liye shubh ank aur rang abhi available nahi hain.",

  // Forecast — Lucky highlights card (Hinglish)
  fc_luckyBestTimeLabel:     "SHUBH SAMAY",
  fc_luckyAvoidTimeLabel:    "ASHUBH SAMAY",
  fc_luckyReason:            "{date} ko — shubh ank {n} aur {colour} rang aaj ki cosmic energy ke saath align hain.",
  fc_luckyClrHara:           "Hara",
  fc_luckyClrPila:           "Pila",
  fc_luckyClrSafed:          "Safed",
  fc_luckyClrNeela:          "Neela",
  fc_luckyClrSuneheri:       "Suneheri",
  fc_luckyClrKesari:         "Kesari",

  // Risk Radar — 24-hour breakdown labels (HN)
  rrSection24hToday:          "AAJ KE 24 GHANTE",
  rrSection24hWithDate:       "{date} KE 24 GHANTE",
  rrLabelKyaRisk:             "KYA RISK HAI",
  rrLabelKyaAvoid:            "KYA AVOID KARNA HAI",
  rrLabelKyaKarna:            "KYA KARNA HAI",
  rrLabelUpay:                "UPAY",
  rrLevelLow:                 "Low",
  rrLevelMed:                 "Med",
  rrLevelHigh:                "High",
  rrLabelRiskLevel:           "RISK LEVEL",
  radarHeaderSub:             "Aane wale 7 dino ka cosmic radar",
  radarLoadingTxt:            "Aapka radar tayyar kar rahe hain…",
  radarEmptyTitle:            "Radar load nahi ho saka",
  radarEmptyBody:             "Internet check karein ya thodi der baad phir try karein.",
  radarPickerLabel:           "APNA DIN CHUNEIN",
  radarDayToday:              "Aaj",
  radarDayTomorrow:           "Kal",
  radarTotalLabel:            "TOTAL RISK SIGNALS",
  radarBadgeHigh:             "HIGH ALERT",
  radarBadgeMed:              "ELEVATED",
  radarBadgeLow:              "STABLE",
  radarSubToday:              "Aaj 24 ghante mein active threat signals",
  radarSubOther:              "{date} ke 24 ghante mein active signals",
  radarStatusActive:          "THREAT SCAN ACTIVE",
  radarSignalSingular:        "SIGNAL",
  radarSignalPlural:          "SIGNALS",
  radarAllClear:              "ALL CLEAR",
  radarAllClearSub:           "Aaj koi major signal nahi",
  radarTitle:                 "Risk Radar",
  rrCardTitle:                "Cosmic Risk Radar",
  rrSafestChip:               "SAFEST",
  rrChallengingChip:          "CHALLENGING",
  rrDayOf7:                   "Day {n} of 7",
  rrLockedTitle:              "{date} ka radar locked",
  rrLockedSub:                "Aane wale dino ka full radar — risk level, kya karna/avoid karna, lucky numbers, best time aur upay — Premium se unlock karein.",
  rrLockedHint:               "💡 Day 1 free hai — preview ke liye tap karein",
  rrLockedCta:                "UNLOCK PREMIUM",
  rrScoreUp:                  "Aaj positive energy bhari hai. Naye kaam shuru karne ka accha din.",
  rrScoreMixed:               "Mixed din — kuch mauke, kuch cheezein dhyaan se.",
  rrScoreDown:                "Aaj thodi challenging energy. Patient rahein, reactive na ho.",
  rrDotPrimary:               "Primary",
  rrDotSecondary:             "Secondary",
  rrDotWatch:                 "Watch",
  rrDotStable:                "Stable",
  rrDotRoutine:               "Routine check",
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
  mdVastuTitle:       "एस्ट्रोवास्तु प्रो",
  mdVastuSub:         "आपकी कुंडली के अनुसार वास्तु",
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
  numFreeSection:     "🆓 बेसिक अंकज्योतिष",
  numTapHint:         "पूरी जानकारी के लिए किसी भी कार्ड पर टैप करें",
  numLifePathLbl:     "जीवन पथ संख्या",
  numLifePathHi:      "जीवन पथ",
  numBirthDayLbl:     "जन्म दिन संख्या",
  numBirthDayHi:      "जन्म दिन",
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
  numCoreSummary:     "आपकी 4 मुख्य संख्याएं",
  numBasicLockedHint: "करियर ब्लूप्रिंट, फ़ोन न्यूमरोलॉजी और लकी कलर — प्रो PDF रिपोर्ट में।",
  numBasicCompareTitle: "बेसिक बनाम प्रो",
  numBasicCompareBasicLine: "4 मुख्य संख्याएं · लक्षण · ताकत और कमज़ोरी",
  numBasicCompareProLine: "पूरी PDF · करियर ब्लूप्रिंट · फ़ोन और लकी नंबर · उपाय",
  numProTeaseBtn:     "न्यूमरोलॉजी प्रो रिपोर्ट लें",
  numProfileFor:      "{name} की संख्याएं",

  // profile-edit.tsx
  pe_primary:         "मुख्य",
  pe_viewKundli:      "कुंडली देखें",
  pe_editProfile:     "प्रोफ़ाइल संपादित करें",
  pe_setAsPrimary:    "मुख्य बनाएं",
  pe_delete:          "हटाएं",
  pe_addNewKundli:    "नई कुंडली जोड़ें",
  pe_editFamily:      "परिवार सदस्य संपादित करें",
  pe_addFamily:       "परिवार सदस्य जोड़ें",
  pe_lblName:         "नाम",
  pe_phName:          "पूरा नाम",
  pe_male:            "पुरुष",
  pe_female:          "स्त्री",
  pe_other:           "अन्य",
  pe_lblRelation:     "रिश्ता",
  pe_phSelect:        "चुनें",
  pe_lblDOB:          "जन्म तिथि",
  pe_phDD:            "दिन",
  pe_phMonth:         "माह",
  pe_phYear:          "वर्ष",
  pe_lblTOB:          "जन्म समय",
  pe_phHH:            "घं",
  pe_phMM:            "मि",
  pe_lblBirthPlace:   "जन्म स्थान",
  pe_phCity:          "शहर, देश",
  pe_search:          "खोजें",
  pe_pickDay:         "दिन चुनें",
  pe_pickMonth:       "माह चुनें",
  pe_pickYear:        "जन्म वर्ष चुनें",
  pe_pickHour:        "घंटा चुनें",
  pe_pickMinute:      "मिनट चुनें",
  pe_pickRelation:    "रिश्ता चुनें",
  pe_deleteMember:    "सदस्य हटाएं?",
  pe_husband:         "पति",
  pe_wife:            "पत्नी",
  pe_son:             "पुत्र",
  pe_daughter:        "पुत्री",
  pe_father:          "पिता",
  pe_mother:          "माता",
  pe_brother:         "भाई",
  pe_sister:          "बहन",
  pe_friend:          "मित्र",

  // kundli-milan.tsx
  km_unlockReveal:    "छिपी सच्चाई जानने के लिए अनलॉक करें",
  km_onCalculate:     "गणना पर",
  km_riskLevel:       "जोखिम स्तर",
  km_soulBond:        "आत्मा बंधन",
  km_karmaLink:       "कर्म संबंध",
  km_nadiNakBond:     "नाड़ी नक्षत्र बंधन",
  km_ganaCompat:      "गण मेल",
  km_yoniAnalysis:    "योनि विश्लेषण",
  km_noNegPatterns:   "कोई बड़ा नकारात्मक पैटर्न नहीं मिला",
  km_finalVerdict:    "अंतिम निर्णय",
  km_tapUnlock:       "सब अनलॉक करने के लिए नीचे टैप करें",
  km_basic:           "बेसिक",
  km_manglikDosh:     "मांगलिक दोष",
  km_recalc:          "पुनर्गणना / विवरण बदलें",

  // vastu.tsx
  vu_camera:          "कैमरा",
  vu_gallery:         "गैलरी",
  vu_takePhotoNow:    "अभी फोटो लें",
  vu_chooseSavedPhoto:"सहेजी फोटो चुनें",
  vu_initiateScan:    "वास्तु दृष्टि स्कैन शुरू करें",
  vu_chooseRoomType:  "कमरे का प्रकार चुनें",
  vu_liveCompass:     "लाइव कम्पास",
  vu_deepScanTitle:   "कॉस्मिक वास्तु डीप स्कैन",
  vu_fromGallery:     "गैलरी से",
  vu_noFloorPlan:     "कोई फ्लोर प्लान नहीं जोड़ा",
  vu_remove:          "हटाएं",
  vu_runDeepScan:     "कॉस्मिक डीप स्कैन चलाएं",
  vu_deepScanBadge:   "डीप स्कैन",
  vu_startDeepScan:   "डीप स्कैन शुरू करें",
  vu_wallByWall:      "दीवार-दर-दीवार विश्लेषण",
  vu_spatialEnergy:   "स्थानिक ऊर्जा मानचित्र",
  vu_scanInconclusive:"स्कैन अस्पष्ट",
  vu_imageClarity:    "छवि स्पष्टता अपर्याप्त",
  vu_recapture:       "पुनः कैप्चर करें और स्कैन करें",
  vu_drishtiName:     "कॉस्मिक वास्तु दृष्टि",
  vu_scanOk:          "स्कैन सफल",
  vu_compliance:      "वास्तु अनुपालन",
  vu_runNewScan:      "नया स्कैन चलाएं",
  vu_whatIsVastu:     "वास्तु शास्त्र क्या है?",
  vu_unlockPro:       "PRO अनलॉक करें",
  vu_roomGuide:       "कमरा-वार वास्तु गाइड",
  vu_tapAnyCard:      "करने योग्य, न करने योग्य और उपाय देखने हेतु किसी भी कार्ड पर टैप करें",
  vu_proHeader:       "AstroVastu PRO — पूरे घर का स्कैन",
  vu_proSubheader:    "फ़ोटो इंजन + आपकी कुंडली + महादशा परत",
  vu_proDesc:         "फ्लोर-प्लान अपलोड, कम्पास सहित कमरे की तस्वीरें, बृहत् संहिता / मयमतम् से उद्धृत निश्चित वास्तु शास्त्र नियम, आपकी कुंडली हेतु व्यक्तिगत प्राथमिकता-कार्य।",
  vu_oneTime:         "एक-बार",
  vu_genTipsTitle:    "⚡ सामान्य वास्तु सुझाव",
  vu_genTip1:         "घर को अव्यवस्था-मुक्त रखें — अवरुद्ध स्थान ऊर्जा-प्रवाह रोकते हैं",
  vu_genTip2:         "घर अच्छी तरह प्रकाशित हो — अंधेरा नकारात्मकता को आमंत्रित करता है",
  vu_genTip3:         "चरमराते या टूटे दरवाज़े तुरंत ठीक करें",
  vu_genTip4:         "इनडोर पौधे रखें — वे घर में जीवन-ऊर्जा लाते हैं",
  vu_genTip5:         "टूटी या क्षतिग्रस्त वस्तुएँ तुरंत हटाएँ",
  vu_genTip6:         "उत्तर में जल-धारा (फव्वारा या एक्वेरियम) शुभ है",
  vu_disclaimer:      "यह सामान्य वास्तु मार्गदर्शिका है। अपने घर के लिए विशेष रूप से, सदैव योग्य वास्तु विशेषज्ञ से व्यक्तिगत सलाह लें।",
  vu_astroVastuPro:   "एस्ट्रोवास्तु प्रो",
  vu_personalizedSub: "व्यक्तिगत प्रीमियम वास्तु विश्लेषण",
  vu_cancelAnytime:   "कभी भी रद्द करें",
  vu_talkExpert:      "वास्तु विशेषज्ञ से व्हाट्सएप पर बात करें",
  vu_new:             "नया",
  vu_cosmicDrishti:   "कॉस्मिक वास्तु दृष्टि",

  km_addYourKundli:   "अपनी कुंडली जोड़ें",
  km_addPartnerKundli:"साथी की कुंडली जोड़ें",
  km_errName:         "नाम ज़रूरी है।",
  km_errAllFields:    "सभी फ़ील्ड ज़रूरी हैं।",
  km_lblName:         "नाम",
  km_lblDob:          "जन्म तिथि",
  km_lblTime:         "जन्म समय",
  km_lblPlace:        "जन्म स्थान",

  km_birthDetailsReq:  "जन्म विवरण आवश्यक",
  km_partnerBirth:     "साथी के जन्म विवरण",
  km_phName:           "पूरा नाम",
  km_phDob:            "DD/MM/YYYY",
  km_phTime:           "HH:MM  AM / PM",
  km_phPlace:          "जैसे: दिल्ली, भारत",
  km_birthMissing:     "जन्म डेटा नहीं मिला",
  km_calcFailed:       "गणना विफल",
  km_okBtn:            "ठीक है",
  km_aap:              "आप",

  km_secTopInsights:   "मुख्य अंतर्दृष्टि",
  km_secDeepInsights:  "गहरी अंतर्दृष्टि",
  km_secAdvAnalysis:   "उन्नत विश्लेषण",
  km_secFutInsights:   "भविष्य अंतर्दृष्टि",
  km_secHidPremium:    "छुपे प्रीमियम",

  km_coreCompTitle:    "मुख्य अनुकूलता",
  km_coreCompDesc:     "क्या आपके दिल, मन और आत्मा जीवन भर के लिए सच में जुड़े हैं?",
  km_riskScanTitle:    "जोखिम स्कैन",
  km_riskScanDesc:     "यह अंतर्दृष्टि आपका निर्णय बदल सकती है — छुपे जोखिम सामने आएँगे",
  km_personMatchTitle: "व्यक्तित्व मेल",
  km_personMatchDesc:  "यह अंतर्दृष्टि आपका निर्णय बदल सकती है — देखें क्या आप एक-दूसरे को सच में समझते हैं",
  km_soulKarmaTitle:   "आत्मा एवं कर्म",
  km_soulKarmaDesc:    "क्या आप नियति के साथी हैं? या केवल समय? आपकी जन्म पत्रिका पर रीयल-टाइम विश्लेषण",
  km_intimacyTitle:    "अंतरंगता स्कोर",
  km_intimacyDesc:     "शारीरिक एवं भावनात्मक बंधन — वह सत्य जो अधिकांश जोड़े कभी नहीं जान पाते",
  km_doshaEngTitle:    "दोष इंजन",
  km_doshaEngDesc:     "मंगल, नाड़ी और भकूट — वे संघर्ष जो चुपचाप विवाह तोड़ देते हैं",
  km_negEnergyTitle:   "नकारात्मक ऊर्जा",
  km_negEnergyDesc:    "छुपे दोष जो आपके पंडित भी चूक सकते हैं — इन्हें अनदेखा न करें",
  km_strChalTitle:     "शक्तियाँ एवं चुनौतियाँ",
  km_strChalDesc:      "क्या आपको जोड़े रखेगा — और क्या चुपचाप दूर कर सकता है",
  km_remAdvTitle:      "उपाय एवं सलाह",
  km_remAdvDesc:       "सही पूजा, रत्न और मंत्र — रुकावटें बढ़ने से पहले ही हटाएँ",

  km_marriageTime:     "विवाह समय",
  km_childPlan:        "संतान योजना",
  km_finCompat:        "आर्थिक मेल",
  km_lifeStab:         "जीवन स्थिरता",
  km_finHarmony:       "आर्थिक सामंजस्य",
  km_familyAccept:     "परिवार स्वीकार्यता",

  km_karmRelTitle:     "कार्मिक रिश्ता जाँच",
  km_karmRelDesc:      "क्या इस जन्म में मिलने का योग था?",
  km_pastLifeTitle:    "पूर्व जन्म संबंध",
  km_pastLifeDesc:     "पिछले जन्म से आत्मिक बंधन",
  km_divorceTitle:     "तलाक / वियोग जोखिम",
  km_divorceDesc:      "ग्रह-संघर्ष पर आधारित संभावना",
  km_loyaltyTitle:     "वफ़ादारी एवं विश्वास सूचकांक",
  km_loyaltyDesc:      "विश्वासघात या लंबे समय की वफ़ादारी की संभावना",

  km_badgeMostImp:     "सबसे महत्वपूर्ण",
  km_badgeCritCheck:   "गंभीर जाँच",
  km_badgeDecCard:     "निर्णय कार्ड",
  km_badgeSecret:      "गुप्त",

  km_gradeExcellent:   "उत्कृष्ट",
  km_gradeVeryGood:    "बहुत अच्छा",
  km_gradeAverage:     "सामान्य",
  km_gradeBelowAvg:    "कम",
  km_gradeLowMatch:    "बहुत कम",

  km_kutaSahi:         "सही",
  km_kutaAnmatch:      "अनमेल",
  km_kutaDono:         "दोनों",

  km_emotionalBond:    "भावनात्मक बंधन",
  km_mentalConn:       "मानसिक संबंध",
  km_intimacyHarm:     "अंतरंगता सामंजस्य",
  km_communication:    "संवाद",
  km_natureTemp:       "स्वभाव एवं मिज़ाज",
  km_socialAlign:      "सामाजिक मेल",
  km_lifestyleHarm:    "जीवनशैली सामंजस्य",
  km_physicalHarm:     "शारीरिक सामंजस्य",
  km_energeticAttr:    "ऊर्जा आकर्षण",

  km_compMismatch:     "अनुकूलता बेमेल",
  km_doshaConflict:    "दोष संघर्ष",
  km_longTermStab:     "दीर्घकालिक स्थिरता",
  km_nadiDosh:         "नाड़ी दोष",
  km_bhakootDosh:      "भकूट दोष",
  km_ganaDosh:         "गण दोष",
  km_grahaMaitri:      "ग्रह मैत्री",

  km_onePartMang:      "एक साथी मांगलिक है",
  km_noMangConf:       "मांगलिक संघर्ष नहीं",

  km_natTimingExp:     "प्राकृतिक समय संभव",
  km_slightPatience:   "थोड़ा धैर्य रखें",
  km_medConsAdv:       "चिकित्सा/विशेषज्ञ सलाह लें",
  km_strongFinAlign:   "मज़बूत आर्थिक मेल",
  km_modBudgetHelp:    "सामान्य — बजट योजना लाभदायक",
  km_highlyLikely:     "बहुत संभव",
  km_mayNeedTime:      "समय और प्रयास लग सकता है",
  km_marrAusp:         "2025–2026 शुभ",
  km_marrModerate:     "2026–2027 सामान्य",
  km_marrDelay:        "देर करें — मार्गदर्शन लें",

  km_riskLow:          "कम",
  km_riskModerate:     "सामान्य",
  km_riskHigh:         "अधिक",

  km_deepKarmTie:      "गहरा कार्मिक बंधन",
  km_growConn:         "बढ़ता संबंध",
  km_posPastLife:      "शुभ पूर्व-जन्म",
  km_neutralKarma:     "तटस्थ कर्म",

  km_planFriendStrong: "ग्रह मैत्री मज़बूत है",
  km_sharedEnergies:   "साझी ग्रह ऊर्जा",
  km_taraFav:          "तारा नक्षत्र शुभ है",
  km_modTaraDest:      "सामान्य तारा भाग्य",
  km_bhakSubh:         "भकूट शुभ — कोई राशि संघर्ष नहीं",
  km_rashiAlign:       "राशि ऊर्जा मिलती है",

  km_nadiHealth:       "नाड़ी दोष — स्वास्थ्य जागरूकता आवश्यक",
  km_minorTempDiff:    "हल्के स्वभाव अंतर",
  km_ganaClash:        "गण संघर्ष — प्रकृति अंतर",
  km_commPracNeeded:   "संवाद का अभ्यास आवश्यक",
  km_bhakTimeCaut:     "भकूट दोष — समय सावधानी",
  km_patienceConfl:    "संघर्ष में थोड़ा धैर्य",
  km_yoniMismatch:     "योनि बेमेल — ऊर्जा समायोजन",
  km_qualityTimeNeeded:"नियमित गुणवत्ता समय आवश्यक",

  km_pastLifeScore:    "पूर्व जन्म संबंध स्कोर",
  km_ancestKarma:      "वंशानुगत कर्म पैटर्न",
  km_nakDream:         "नक्षत्र स्वप्न अनुकूलता",
  km_advDoshaRev:      "उन्नत दोष निवारण योजना",

  km_unlockComplete:   "पूरी रिपोर्ट अनलॉक करें",
  km_realTimeAnalysis: "आपकी जन्म पत्रिका पर रीयल-टाइम विश्लेषण",
  km_secFutTimeline:   "भविष्य समयरेखा",
  km_secSoulKarma:     "आत्मा एवं कर्म विश्लेषण",
  pe_otherProfiles:   "अन्य प्रोफ़ाइल",
  pe_recentlyDeleted: "हाल में हटाए गए",
  pe_noKundliYet:     "अभी तक कोई कुंडली नहीं",
  pe_manageProfile:   "अपना प्रोफ़ाइल और परिवार के सदस्य प्रबंधित करें",

  pn_computing:       "गणना हो रही है…",
  pn_dataSource:      "स्विस एफेमेरिस · लाहिरी",
  pn_offline:         "ऑफ़लाइन · अनुमानित मान",
  pn_today:           "आज",
  pn_parso:           "परसों",
  pn_auspicious:      "आज की शुभता",
  pn_megaFestival:    "महापर्व",
  pn_bNational:       "राष्ट्रीय",
  pn_bVrat:           "व्रत",
  pn_bMuhurat:        "मुहूर्त",
  pn_bandExcellent:   "बहुत शुभ",
  pn_bandGood:        "शुभ",
  pn_bandMixed:       "मिश्रित",
  pn_bandCaution:     "सावधानी",

  nm_proTools:        "प्रो+ टूल्स",
  nm_premium:         "प्रीमियम",
  nm_lifeMastery:     "न्यूमरोलॉजी प्रो रिपोर्ट",
  nm_yourNumbers:     "आपके अंक",
  nm_yourNumbersHint: "(कम से कम एक)",
  nm_whatsInside:     "अंदर क्या है",
  nm_opening:         "खुल रहा…",
  nm_generateBtn:     "न्यूमरोलॉजी प्रो रिपोर्ट बनाएँ",

  cr_pageTitle:       "करियर विश्लेषण",
  cr_loading:         "आपकी कुंडली पढ़ी जा रही है…",
  cr_loginRequired:   "करियर विश्लेषण देखने के लिए लॉगिन करें।",
  cr_addProfile:      "जन्म विवरण जोड़ें",
  cr_scoreLabel:      "करियर स्कोर",
  cr_strongPhase:     "मज़बूत दौर",
  cr_cautionPhase:    "सावधानी दौर",
  cr_mixedPhase:      "मिश्रित दौर",
  cr_quickReading:    "त्वरित पठन",
  cr_hiddenInsight:   "गुप्त अंतर्दृष्टि",
  cr_proCta:          "प्रो में पूरा करियर विश्लेषण अनलॉक करें",
  cr_upgradeBtn:      "प्रो में अपग्रेड करें",
  cr_houses:          "करियर भाव",
  cr_lord:            "स्वामी:",
  cr_inHouse:         "भाव में:",
  cr_planets:         "करियर ग्रह",
  cr_dasha:           "वर्तमान दशा प्रभाव",
  cr_mahadasha:       "महादशा",
  cr_antardasha:      "अंतर्दशा",
  cr_ends:            "समाप्ति",
  cr_transit:         "लाइव ग्रह गोचर",
  cr_growth:          "करियर वृद्धि के समय",
  cr_jobChange:       "नौकरी बदलने का समय",
  cr_struggle:        "संघर्ष और छिपे जोखिम",
  cr_reasoning:       "यह पठन क्यों",
  cr_pathTitle:       "नौकरी बनाम व्यवसाय",
  cr_jobLabel:        "नौकरी",
  cr_businessLabel:   "व्यवसाय",
  cr_pathConfidence:  "कुंडली विश्वास",
  cr_pathMode:        "करियर प्रकार",
  cr_bestOptions:     "सबसे उपयुक्त करियर विकल्प",
  cr_topStrengths:    "टॉप ताकत",
  cr_weakness:        "कमज़ोरी",
  cr_risk:            "जोखिम",

  hl_pageTitle:       "स्वास्थ्य विश्लेषण",
  hl_loginRequired:   "स्वास्थ्य विश्लेषण देखने के लिए लॉगिन करें।",
  hl_healthyPhase:    "स्वस्थ दौर",
  hl_careNeeded:      "ध्यान की आवश्यकता",
  hl_mixedPhase:      "मिश्रित दौर",
  hl_scoreLabel:      "स्वास्थ्य स्कोर",
  hl_riskLabel:       "जोखिम:",
  hl_houses:          "स्वास्थ्य भाव",
  hl_planets:         "स्वास्थ्य ग्रह",
  hl_riskPeriods:     "जोखिम के समय",
  hl_nature:          "समस्याओं का स्वरूप",
  hl_recovery:        "स्वास्थ्य सुधार शक्ति",
  hl_prevent:         "रोकथाम मार्गदर्शन",
  hl_organs:          "कमज़ोर शरीर के अंग",
  hl_remedies:        "उपाय (मंत्र और जीवनशैली)",

  fn_pageTitle:       "धन विश्लेषण",
  fn_growthPhase:     "वृद्धि दौर",
  fn_cautionPhase:    "सावधानी दौर",
  fn_stablePhase:     "स्थिर दौर",
  fn_scoreLabel:      "धन स्कोर",
  fn_houses:          "धन भाव",
  fn_planets:         "धन ग्रह",
  fn_inflow:          "धन आगमन समय",
  fn_expense:         "व्यय / हानि दौर",
  fn_invest:          "निवेश अवसर",
  fn_sudden:          "अचानक लाभ / हानि",
  fn_stability:       "धन स्थिरता",
  fn_income:          "आय स्रोत",

  rl_loveTitle:       "प्रेम वास्तविकता जाँच",
  rl_loveSub:         "अपने रिश्ते की छुपी सच्चाई जानें",
  rl_mostUsed:        "सबसे लोकप्रिय",
  rl_loveDesc:        "मौजूदा रिश्ते और BF/GF के लिए",
  rl_marriageTitle:   "विवाह अनुकूलता",
  rl_marriageSub:     "आत्मा सिंक, आकर्षण मेल",
  rl_deepBadge:       "गहन विश्लेषण",
  rl_partnerTitle:    "भावी जीवनसाथी चित्रण",
  rl_partnerSub:      "रूप, स्वभाव और दिशा",
  rl_partnerDesc:     "आपकी कुंडली से जीवनसाथी की दिव्य झलक",
  rl_newBadge:        "नया · ब्रह्मांडीय चित्रण",
  rl_pageHeader:      "रिश्ता",
  rl_selfLabel:       "आप",
  rl_partnerSelect:   "साथी चुनें",
  rl_change:          "बदलें",

  mr_loginRequired:   "रिपोर्ट देखने के लिए लॉगिन ज़रूरी।",
  mr_loadError:       "आपकी रिपोर्ट लोड नहीं हुईं।",
  mr_networkError:    "नेटवर्क त्रुटि।",
  mr_waLinkPrefix:    "रिपोर्ट खोलें:",
  mr_waErrorTitle:    "व्हाट्सएप उपलब्ध नहीं",
  mr_openPdf:         "PDF खोलें",
  mr_whatsapp:        "व्हाट्सएप",
  mr_pageTitle:       "मेरी रिपोर्ट्स",
  mr_loading:         "रिपोर्ट्स लोड हो रही…",
  mr_emptyTitle:      "अभी कोई रिपोर्ट नहीं",
  mr_footer:          "उन्नत कॉस्मिक इंटेलिजेंस द्वारा संचालित",

  mk_savedCount:      "कुंडली सहेजी गई",
  mk_emptyTitle:      "अभी कोई कुंडली नहीं",
  mk_emptyDesc:       "जन्म विवरण के साथ प्रोफ़ाइल जोड़कर कुंडली बनाएँ",
  mk_addNew:          "नई कुंडली जोड़ें",
  mk_primary:         "मुख्य",
  mk_deleteTitle:     "कुंडली हटाएँ?",
  mk_deleteDesc:      "कुंडली स्थायी रूप से हट जाएगी। यह क्रिया वापस नहीं होगी।",
  mk_cancel:          "रद्द करें",
  mk_delete:          "हटाएँ",

  mr_kindHomePro:     "गृह वास्तु प्रो",
  mr_kindShop:        "व्यवसाय वास्तु — दुकान",
  mr_kindOffice:      "व्यवसाय वास्तु — कार्यालय",
  mr_kindFactory:     "व्यवसाय वास्तु — कारख़ाना",
  mr_kindBusiness:    "व्यवसाय वास्तु",

  rl_kundliReqTitle:        "कुंडली आवश्यक",
  rl_kundliReqBoth:         "आपकी और साथी की दोनों कुंडली चाहिए। पहले कुंडली स्क्रीन से दोनों बनाएँ।",
  rl_kundliReqSelf:         "आपकी कुंडली तैयार नहीं है। पहले कुंडली स्क्रीन से जनरेट करें।",
  rl_kundliReqSelectFirst:  "आगे बढ़ने के लिए ऊपर से अपना साथी चुनें।",
  rl_kundliReqPartnerMissing: "साथी की कुंडली अभी तक नहीं बनी है। पहले कुंडली स्क्रीन से उनकी कुंडली बनाएँ।",
  rl_kundliReqAddBtn:        "कुंडली जोड़ें",
  rl_kundliReqCancel:        "रद्द करें",

  nm_wi1Title:  "जीवन ब्लूप्रिंट कार्ड",        nm_wi1Sub:  "मूल व्यक्तित्व + 2026 फोकस + सबसे बड़ी शक्ति/चुनौती",
  nm_wi2Title:  "आप कौन हैं — पहचान",          nm_wi2Sub:  "3-पैराग्राफ कहानी + 5 छुपी शक्तियाँ + 5 चुनौतियाँ",
  nm_wi3Title:  "करियर ब्लूप्रिंट",              nm_wi3Sub:  "बेहतरीन क्षेत्र, सामान्य ग़लतियाँ, ग्रोथ टाइमिंग, धन पैटर्न",
  nm_wi4Title:  "प्रेम पैटर्न — गहन",            nm_wi4Sub:  "रिश्ते की शैली, ब्रेकअप ट्रिगर्स, आदर्श साथी संख्या",
  nm_wi5Title:  "स्वास्थ्य और आध्यात्मिक मार्ग", nm_wi5Sub:  "शरीर के संकेत + धर्म + मंत्र + दान कार्यक्रम",
  nm_wi6Title:  "जोखिम चेतावनी + स्वर्णिम काल",  nm_wi6Sub:  "5 विशिष्ट जोखिम + बड़े निर्णय कब लें",
  nm_wi7Title:  "मोबाइल नंबर — गहन",            nm_wi7Sub:  "क्यों · प्रभाव · कार्य + चीरो अंतिम-4 + विकल्प",
  nm_wi8Title:  "वाहन नंबर — गहन",              nm_wi8Sub:  "क्यों · प्रभाव · कार्य + अनुकूल प्लेट सुझाव",
  nm_wi9Title:  "घर नंबर — गहन",                nm_wi9Sub:  "क्यों · प्रभाव · कार्य + उपाय कार्यक्रम",
  nm_wi10Title: "अनुकूलता मैट्रिक्स",            nm_wi10Sub: "आपका ड्राइवर बनाम सभी 1-9 (मित्र/शत्रु/तटस्थ)",
  nm_wi11Title: "नाम अंकशास्त्र + अक्षर",         nm_wi11Sub: "पाइथागोरियन + चाल्डियन + अक्षर-दर-अक्षर विश्लेषण",
  nm_wi12Title: "हस्ताक्षर और 90-दिन योजना",     nm_wi12Sub: "हस्ताक्षर डिज़ाइन + चरण-दर-चरण कार्यान्वयन",

  fc_demo:              "डेमो",
  fc_dailyEnergyScore:  "दैनिक ऊर्जा स्कोर",
  fc_moonRashi:         "गोचर चंद्र",
  fc_paksha:            "पक्ष",
  fc_energy:            "ऊर्जा",
  fc_activeDasha:       "सक्रिय दशा",

  sub_active:           "सक्रिय",
  sub_upgradeBtn:       "प्रो में अपग्रेड करें 🔓",
  sub_getBasic:         "बेसिक लें",
  sub_free:             "निःशुल्क",
  sub_alwaysFree:       "हमेशा निःशुल्क",
  sub_cmpJyotishQ:      "ज्योतिष प्रश्न",
  sub_cmpMarriage:      "विवाह मिलान",
  sub_cmpTimeline:      "भविष्य टाइमलाइन",
  sub_cmpDasha:         "दशा विश्लेषण",
  sub_cmpKarmic:        "कार्मिक अंतर्दृष्टि",
  sub_cmpPdf:           "पीडीएफ रिपोर्ट",
  sub_cmpProfiles:      "सहेजी गई प्रोफ़ाइल",

  da_energyLevels:      "ऊर्जा स्तर",
  da_energyGood:        "अच्छा",
  da_energyNeutral:     "सामान्य",
  da_energyChallenging: "कठिन",

  pe_relSelf:      "स्वयं",
  pe_relHusband:   "पति",
  pe_relWife:      "पत्नी",
  pe_relSon:       "पुत्र",
  pe_relDaughter:  "पुत्री",
  pe_relFather:    "पिता",
  pe_relMother:    "माता",
  pe_relBrother:   "भाई",
  pe_relSister:    "बहन",
  pe_relFriend:    "मित्र",
  pe_relOther:     "अन्य",

  sub_planBasicName:    "बेसिक",
  sub_planProName:      "प्रो",
  sub_planBasicTag:     "आवश्यक वैदिक मार्गदर्शन",
  sub_planProTag:       "संपूर्ण वैदिक ज्ञान",

  sub_bF1: "10 ज्योतिष प्रश्न / दिन",
  sub_bF2: "विवाह मिलान (बेसिक)",
  sub_bF3: "प्रेम मिलान (बेसिक)",
  sub_bF4: "करियर, स्वास्थ्य, धन — संक्षिप्त सारांश",
  sub_bF5: "भविष्य टाइमलाइन — 1 माह",
  sub_bF6: "5 सहेजी गई प्रोफ़ाइल",

  sub_bL1: "असीमित प्रश्न",
  sub_bL2: "तर्क के साथ गहन विश्लेषण",
  sub_bL3: "पूर्ण 6-माह की टाइमलाइन",
  sub_bL4: "कार्मिक अंतर्दृष्टि और पीडीएफ रिपोर्ट",

  sub_pF1: "असीमित ज्योतिष प्रश्न",
  sub_pF2: "विवाह और प्रेम — पूर्ण गहन विश्लेषण",
  sub_pF3: "करियर, स्वास्थ्य, धन — विस्तृत",
  sub_pF4: "भविष्य टाइमलाइन — 6 माह पूर्ण",
  sub_pF5: "डी1 + डी9 कुंडली विश्लेषण",
  sub_pF6: "दशा (एमडी + एडी + पीडी) पूर्ण विवरण",
  sub_pF7: "कार्मिक पैटर्न और छिपी अंतर्दृष्टि",
  sub_pF8: "पीडीएफ रिपोर्ट डाउनलोड",
  sub_pF9: "असीमित सहेजी गई प्रोफ़ाइल",

  vu_camSub:     "तुरंत फ़ोटो लें",
  vu_galSub:     "सहेजी गई फ़ोटो चुनें",
  vu_roomPicker: "कमरा चुनें",
  vu_review:     "समीक्षा करें और भेजें",
  vu_reviewSub:  "अपनी फ़ोटो की पुष्टि करें, फिर डीप स्कैन चलाएँ।",
  vu_tabBasic:   "बेसिक",
  vu_tabPro:     "प्रो",
  vu_introBody:  "वास्तु शास्त्र वास्तुकला का एक प्राचीन भारतीय विज्ञान है। सही दिशाएँ घर में सकारात्मक ऊर्जा, सुख, स्वास्थ्य और समृद्धि लाती हैं।",

  // ── kundli-milan additional (km2_*) ──
  km2_secRiskScan:        "रिश्ते का जोखिम स्कैन",
  km2_secPersMatch:       "व्यक्तित्व मेल",
  km2_secIntimacyComp:    "अंतरंगता अनुकूलता",
  km2_secNegEnergy:       "नकारात्मक ऊर्जा जाँच",
  km2_chipClear:          "साफ़",
  km2_chipMild:           "हल्का",
  km2_chipPresent:        "मौजूद",
  km2_strengthsHdr:       "शक्तियाँ 💚",
  km2_challengesHdr:      "चुनौतियाँ ⚡",
  km2_persExcellent:      "उत्कृष्ट — दोनों का जीवन के प्रति दृष्टिकोण और मूल्य समान हैं।",
  km2_persModerate:       "मध्यम — कुछ अंतर हैं पर प्रयास से सामंजस्य बन सकता है।",
  km2_persChallenging:    "चुनौतीपूर्ण — स्वभाव के अंतर पर सक्रिय रूप से कार्य करना होगा।",
  km2_yoniExceptional:    "समान योनि — असाधारण शारीरिक और ऊर्जा का तालमेल।",
  km2_yoniComplementary:  "पूरक ऊर्जाएँ — कुछ समायोजन के साथ अच्छी अनुकूलता।",
  km2_yoniDifferent:      "अलग ऊर्जाएँ — धैर्य और समझ से यह बंधन मज़बूत होगा।",
  km2_concernSing:        "चिंता",
  km2_concernPlural:      "चिंताएँ",
  km2_concernsFound:      "मिलीं",
  km2_negPatExcell:       "उत्कृष्ट — कोई बड़ा नकारात्मक पैटर्न नहीं।",
  km2_negPatMinor:        "छोटी चिंताएँ — जागरूकता से संभाली जा सकती हैं।",
  km2_negPatMulti:        "कई चिंताएँ — उपाय अत्यधिक अनुशंसित हैं।",
  km2_doshDetect:         "दोष मिला",
  ds_title: "दोष विश्लेषण",
  ds_subtitle: "पूर्ण दोष विश्लेषण ({count} दोष)",
  ds_demo: "डेमो",
  ds_totalDosh: "कुल दोष",
  ds_present: "मौजूद",
  ds_notPresent: "नहीं",
  ds_scanning: "स्कैन…",
  ds_analyzing: "आपकी कुंडली का विश्लेषण…",
  ds_checking: "सभी {count} दोष शर्तें जाँची जा रही हैं",
  ds_analysis: "दोष विश्लेषण",
  ds_active: "सक्रिय",
  ds_mild: "हल्का",
  ds_clear: "साफ",
  ds_detected: "{total} में से {found} दोष मिले",
  ds_remedies: "उपाय",
  ds_disclaimer: "दोष विश्लेषण शास्त्रीय वैदिक ज्योतिष पर आधारित है। महत्वपूर्ण निर्णयों के लिए योग्य ज्योतिषी से सलाह लें।",
  km2_nadiAuspProgeny:    "नाड़ी अलग — संतान के लिए शुभ",
  km2_nadiDeepEmpathy:    "नाड़ी मिली — गहरी समझ",
  km2_remKumbhVivah:      "विवाह से पूर्व कुम्भ विवाह या मंगल पूजा करें।",
  km2_remEkadashi:        "एकादशी का व्रत रखें — शिव पूजा से नाड़ी असंतुलन से बचें।",
  km2_remChandraMantra:   "चंद्र मंत्र जपें — ॐ चंद्राय नमः 108 बार।",
  km2_remRudrabhishek:    "विवाह से पूर्व साथ में रुद्राभिषेक करें।",
  km2_remGemstones:       "दोनों को अनुकूल रत्न पहनने चाहिए — ज्योतिषी से सलाह लें।",
  km2_remSunderkand:      "साथ में पूजा और सुंदरकांड का नियमित पाठ बंधन को मज़बूत करेगा।",
  km2_fvExceptional:      "असाधारण मिलान। तारे आपके पक्ष में हैं। आनंदमय और सफल विवाह का संकेत है।",
  km2_fvVeryPositive:     "बहुत सकारात्मक मिलान। आपसी सम्मान और प्रेम से यह रिश्ता बहुत अच्छा होगा।",
  km2_fvModerate:         "मध्यम मिलान। जागरूकता, प्रयास और विशेषज्ञ मार्गदर्शन से यह बंधन फले-फूलेगा।",
  km2_fvChallenging:      "चुनौतीपूर्ण मिलान। आगे बढ़ने से पूर्व उपाय, धैर्य और ज्योतिषी से सलाह अनिवार्य है।",
  km2_ashtakootScoreLbl:  "अष्टकूट स्कोर",
  km2_concernDetSuffix:   "मिलीं",
  km2_addBothFirst:       "पहले दोनों कुंडली जोड़ें",
  km2_unlockFullAnal:     "पूरा विश्लेषण खोलें",
  km2_youPlaceholder:     "आप",
  km2_birthMissingBody:   "सही मिलान के लिए दोनों साथियों का पूर्ण जन्म डेटा (तारीख़, समय, स्थान) चाहिए।",
  km2_calcFailedBody:     "मिलान गणना नहीं हो सकी। कृपया पुनः प्रयास करें।",
  km2_matchingWith:       "मिलान",
  km3_yourPersAnalysis:   "आपका व्यक्तिगत विश्लेषण",
  km3_insEmotional:       "भावनात्मक अनुकूलता",
  km3_insMarriage:        "विवाह का भविष्य",
  km3_insRisks:           "छुपे जोखिम",
  km3_insKarmic:          "कर्मिक बंधन",
  km3_insStrength:        "शक्ति कारक",
  km3_insTriggers:        "विवाद के कारण",
  km3_insStability:       "दीर्घकालीन स्थिरता",
  km3_insFinal:           "अंतिम परिणाम",
  km3_unlEmotional:       "भावनात्मक अनुकूलता — क्या वास्तव में जुड़ते हो या नहीं",
  km3_unlMarriage:        "विवाह का भविष्य — इस रिश्ते की वास्तविक दिशा",
  km3_unlRisks:           "छुपे जोखिम — वे पैटर्न जो समस्याएँ ला रहे हैं",
  km3_unlKarmic:          "कर्मिक बंधन — इस संबंध का गहरा उद्देश्य",
  km3_unlStrength:        "शक्ति कारक — क्या इस रिश्ते को जोड़े रखता है",
  km3_unlTriggers:        "विवाद के कारण — क्या बार-बार समस्याएँ पैदा करता है",
  km3_unlStability:       "दीर्घकालीन स्थिरता — टिकेगा या टूटेगा",
  km3_unlFinal:           "अंतिम परिणाम — वास्तविक भविष्य की दिशा",
  km3_nadiAlag:           "अलग नाड़ी — स्वस्थ संतान और दीर्घ जीवन के लिए शुभ।",
  km3_nadiSama:           "सम नाड़ी — गहरा भावनात्मक मेल, स्वास्थ्य के प्रति सावधानी सलाह।",
  km3_personFallback:     "व्यक्ति",
  km3_errTryAgain:        "त्रुटि। कृपया पुनः प्रयास करें।",
  km3_proTrailMore:       "पूरी जानकारी और उपाय Pro रिपोर्ट में दिखेंगे।",
  km3_kundliBased:        "यह विश्लेषण आपकी असली कुंडली पर आधारित है और उन पैटर्न्स को उजागर करता है जो सीधे आपके रिश्ते को प्रभावित करते हैं।",
  km3_truthsBelow:        "इस संबंध के सबसे महत्वपूर्ण सत्य नीचे छुपे हुए हैं।",
  km3_unlockToSee:        "अनलॉक करके पूरी तस्वीर देखें।",
  km3_whatYouUnlock:      "आप क्या अनलॉक करेंगे",
  km3_lockedPreview:      "🔒 लॉक्ड प्रीव्यू",
  km3_addBothToUnlock:    "प्रीव्यू अनलॉक करने के लिए दोनों कुंडलियाँ जोड़ें",
  km3_addBothSubtext:     "दोनों की जन्म-विवरण जोड़ें — फिर आपके व्यक्तिगत हुक्स बनेंगे",
  ku_btnKundli:           "कुंडली",
  ku_btnAshtak:           "अष्टकवर्ग",
  ku_btnNavatara:         "नवतारा",
  ku_btnJaimini:          "जैमिनी",
  ku_btnTransit:          "गोचर",
  ku_btnKP:               "KP",
  ku_secDashaTimeline:    "दशा टाइमलाइन",
  ku_secAshtakavarga:     "अष्टकवर्ग",
  ku_secNavatara9Tara:    "नवतारा — 9 तारा",
  ku_secJaiminiKarakas:   "जैमिनी कारक",
  ku_secGrahaTransit:     "ग्रह गोचर",
  ku_secKpPaddhati:       "KP पद्धति",
  ku_snapAscendant:       "लग्न (आरोही)",
  ku_snapMoonSign:        "चंद्र राशि",
  ku_snapNakshatra:       "नक्षत्र",
  ku_snapNakshatraLord:   "नक्षत्र स्वामी",
  ku_snapDashaBalance:    "दशा शेष",
  ku_snapLiveMoonTransit: "चंद्र गोचर — लाइव",
  ku_padaLabel:           "पाद",
  ku_jaiminiDegPre:       "राशि के अंदर अंश:",
  ku_jaiminiDegSuf:       "चार्ट में सर्वाधिक",
  ku_kpDesc:              "कृष्णमूर्ति पद्धति विमशोत्तरी दशा के आनुपातिक उप-विभाजनों का उपयोग करके घटनाओं की सटीक समय-गणना करती है।",
  ku_kpFooter:            "किसी भी घटना के लिए देखें: स्टार-स्वामी और सब-स्वामी का संबंध। यदि 3 स्वामी सहमत हों → घटना निश्चित।",
  ku_kpStar:              "तारा",
  ku_kpSub:               "उप",
  ku_kpSubSub:            "उप-उप",
  ku_kpAsc:               "लग्न",
  ku_savHeading:          "सर्वाष्टकवर्ग",

  // ── Phase 4 additions ─────────────────────────
  nf_title: "अरे!",
  nf_doesntExist: "यह स्क्रीन मौजूद नहीं है।",
  nf_goHome: "होम स्क्रीन पर जाएँ!",
  ab_title: "Cosmic Lens के बारे में",
  ab_subtitle: "वैदिक ज्योतिष, आधुनिक रूप में",
  ab_secMission: "हमारा मिशन",
  ab_pMission1: "Cosmic Lens वैदिक ज्योतिष के सनातन ज्ञान को आपकी जेब में लाता है। हम शास्त्रीय पाराशरी सिद्धांतों को आधुनिक एफेमेरिस गणनाओं और विशेषज्ञ ज्योतिष व्याख्या के साथ जोड़ते हैं, ताकि आपको सटीक, सुलभ और व्यक्तिगत ज्योतिषीय मार्गदर्शन मिले — आपकी भाषा में।",
  ab_pMission2: "चाहे आप अपनी कुंडली के बारे में जिज्ञासु हों, विवाह की योजना बना रहे हों, करियर विकल्प तलाश रहे हों, या केवल दैनिक अंतर्दृष्टि चाहते हों — हमारा मिशन है आपको स्पष्टता और संकल्प के साथ जीवन में मार्गदर्शन देना।",
  ab_secDifferent: "हम क्यों अलग हैं",
  ab_pDifferent: "• गणनाएँ पारंपरिक लाहिरी अयनांश और उच्च-परिशुद्धता स्विस एफेमेरिस डेटा का उपयोग करती हैं।\n• 24 भाषाओं में उपलब्ध — 13 भारतीय क्षेत्रीय भाषाएँ और हिंग्लिश सहित।\n• ईमानदार, पारदर्शी मूल्य निर्धारण — कोई इन-ऐप मुद्रा नहीं, कोई आश्चर्यजनक शुल्क नहीं।\n• गोपनीयता-प्रथम — हम आपकी कुंडली या चैट डेटा कभी नहीं बेचते।\n• 7-दिवसीय निःशुल्क परीक्षण — भुगतान से पहले अनुभव करें।",
  ab_secConnect: "हमसे जुड़ें",
  ab_lblSupportEmail: "सहायता ईमेल",
  ab_lblWebsite: "वेबसाइट",
  ab_secLegal: "क़ानूनी और नीतियाँ",
  ab_linkPrivacy: "गोपनीयता नीति",
  ab_linkTerms: "सेवा की शर्तें",
  ab_linkRefund: "रिफंड और रद्दीकरण",
  ab_linkDisclaimer: "ज्योतिष अस्वीकरण",
  ab_linkDelete: "मेरा खाता हटाएँ",
  ab_lblAppVersion: "ऐप संस्करण",
  ab_versionFoot: "भारत में ♥ के साथ निर्मित · © 2026 Cosmic Lens",
  da_title: "खाता हटाएँ",
  da_subtitle: "स्थायी और अपरिवर्तनीय",
  da_calloutDanger: "यह क्रिया स्थायी है। एक बार हटाने के बाद आपका डेटा पुनः प्राप्त नहीं किया जा सकता।",
  da_secWhatHappens: "हटाने पर क्या होगा",
  da_wb1: "आपका खाता लॉगिन (ईमेल / मोबाइल / Google) तुरंत हटा दिया जाता है।",
  da_wb2: "सभी सहेजी गई कुंडलियाँ, प्रोफ़ाइल और चैट इतिहास 30 दिनों के भीतर मिटा दिया जाता है।",
  da_wb3: "सक्रिय सदस्यताएँ रद्द कर दी जाती हैं — आगे कोई शुल्क नहीं।",
  da_wb4: "भारतीय कानून (GST रिकॉर्ड) के अनुसार पिछले भुगतानों के टैक्स इनवॉइस 7 वर्षों तक रखे जा सकते हैं।",
  da_wb5: "यदि आप पुनः Cosmic Lens का उपयोग करना चाहते हैं, तो आपको एक नया खाता बनाना होगा।",
  da_secBefore: "हटाने से पहले",
  da_pBefore: "इन विकल्पों पर विचार करें — हो सकता है ये बिना डेटा खोए आपकी चिंता हल कर दें:",
  da_bb1: "केवल सदस्यता रद्द करें — प्रोफ़ाइल → सदस्यता → रद्द करें। आपका खाता निःशुल्क बना रहेगा।",
  da_bb2: "सूचनाएँ बंद करें — प्रोफ़ाइल → सूचनाएँ → बंद।",
  da_bb3: "रिफंड चाहिए? पहले हमारी रिफंड नीति देखें — हम मदद कर सकते हैं।",
  da_bb4: "गोपनीयता चिंता? support@cosmiclens.app पर ईमेल करें।",
  da_secConfirm: "हटाने की पुष्टि करें",
  da_pConfirm: "आगे बढ़ने के लिए, नीचे बॉक्स में DELETE टाइप करें और हटाएँ बटन दबाएँ।",
  da_inputPh: "पुष्टि के लिए DELETE टाइप करें",
  da_btnDelete: "मेरा खाता स्थायी रूप से हटाएँ",
  da_btnDeleting: "हटाया जा रहा है…",
  da_btnCancelBack: "रद्द करें और वापस जाएँ",
  da_secNeedHelp: "इसके बजाय मदद चाहिए?",
  da_pNeedHelp: "यदि आपकी कोई चिंता है, तो जाने से पहले हम आपकी बात सुनना चाहेंगे। हमसे support@cosmiclens.app पर संपर्क करें — अधिकांश समस्याएँ 24 घंटों के भीतर हल हो जाती हैं।",
  da_alertNotSignedIn: "साइन इन नहीं हैं",
  da_alertLoginFirst: "कृपया पहले लॉग इन करें।",
  da_alertConfirmTtl: "खाता स्थायी रूप से हटाएँ?",
  da_alertConfirmMsg: "यह क्रिया वापस नहीं ली जा सकती। आपकी सभी कुंडलियाँ, प्रोफ़ाइल, चैट इतिहास और व्यक्तिगत डेटा 30 दिनों के भीतर मिटा दिया जाएगा।",
  da_alertCancel: "रद्द करें",
  da_alertYesDelete: "हाँ, हमेशा के लिए हटाएँ",
  da_alertDeletedTtl: "खाता हटा दिया गया",
  da_alertDeletedMsg: "आपका खाता स्थायी रूप से हटा दिया गया है। Cosmic Lens का उपयोग करने के लिए धन्यवाद।",
  da_alertOk: "ठीक है",
  da_alertFailedTtl: "हटाना विफल",
  da_alertFailedMsg: "कृपया पुनः प्रयास करें या सहायता से संपर्क करें।",
  smf_title: "6-महीने का गहन भविष्य",
  smf_loadingMsg: "MD/AD/PD श्रृंखला गणना हो रही है…",
  smf_unavailableTtl: "भविष्य डेटा उपलब्ध नहीं",
  smf_tryAgain: "बाद में पुनः प्रयास करें।",
  smf_kundliFirst: "कृपया पहले अपनी कुंडली पूरी करें।",
  smf_activeChain: "सक्रिय दशा श्रृंखला",
  smf_lblMaha: "महा",
  smf_lblAntar: "अंतर",
  smf_lblPratyantar: "प्रत्यंतर",
  smf_adWindow: "AD अवधि",
  smf_pdShift: "PD परिवर्तन",
  smf_lblMD: "MD",
  smf_lblAD: "AD",
  smf_lblPD: "PD",
  smf_rulesPrefix: "शासन",
  smf_sitsIn: "स्थित है",
  smf_pdActiveWindow: "सक्रिय PD अवधि",
  smf_lifeAreas: "इस महीने के जीवन क्षेत्र",
  smf_whyPrefix: "क्यों",
  smf_opportunities: "अवसर",
  smf_cautions: "सावधानियाँ",
  smf_remedyLabel: "उपाय",
  smf_remedyFocused: "केंद्रित",
  smf_generated: "तैयार",
  smf_pureEngine: "शुद्ध वैदिक इंजन — MD/AD/PD + भाव स्वामी + जन्मकालीन स्थितियाँ।",
  smf_areaCareer: "करियर",
  smf_areaFinance: "वित्त",
  smf_areaHealth: "स्वास्थ्य",
  smf_areaRelationship: "रिश्ते",
  smf_areaSpirituality: "आध्यात्म",
  dp_title: "🔮 दिव्य प्रश्न",
  dp_subtitle: "अपना प्रश्न पूछें — तुरंत वैदिक उत्तर",
  dp_metaCity: "भुवनेश्वर, ओडिशा · सर्वर समय",
  dp_quickQuestion: "त्वरित प्रश्न",
  dp_orType: "या अपना प्रश्न टाइप करें",
  dp_inputPh: "जैसे: क्या मेरा खोया फ़ोन मिलेगा?",
  dp_btnGetAnswer: "उत्तर पाएँ",
  dp_alertEmptyTtl: "अपना प्रश्न लिखें",
  dp_alertEmptyMsg: "जो पूछना चाहते हैं वह लिखें।",
  dp_errNoticeTtl: "⚠️ सूचना",
  dp_errQuotaPro: "आज का प्रश्न सीमा पूर्ण हो गई। Pro में अपग्रेड करें।",
  dp_errSession: "सत्र समाप्त हो गया। कृपया पुनः लॉगिन करें।",
  dp_errFetch: "उत्तर नहीं मिला। कृपया पुनः प्रयास करें।",
  dp_btnSeeUpgrade: "अपग्रेड देखें →",
  dp_immatureTitle: "⚠️ प्रश्न अभी परिपक्व नहीं",
  dp_refPrefix: "संदर्भ",
  dp_retryAfter: "पुनः प्रयास",
  dp_minutesLater: "मिनट बाद",
  dp_chartTitle: "📊 प्रश्न कुंडली",
  dp_chartLagna: "लग्न",
  dp_chartPlace: "स्थान",
  dp_chartCategory: "वर्गीकरण",
  dp_cuspTitle: "🪔 कस्प विश्लेषण",
  dp_houseSuffix: "भाव",
  dp_subLord: "सब-लॉर्ड",
  dp_starLord: "नक्षत्र-स्वामी",
  dp_signifies: "सूचक भाव",
  dp_classicalTitle: "📖 शास्त्रीय संदर्भ",
  dp_cat_stolen: "खोया सामान मिलेगा?",
  dp_cat_partner: "साथी की भावनाएँ",
  dp_cat_job: "नौकरी मिलेगी?",
  dp_cat_marriage: "विवाह कब?",
  dp_cat_health: "रोग ठीक होगा?",
  dp_cat_litigation: "मुकदमा जीतेंगे?",
  dp_cat_travel: "यात्रा होगी?",
  dp_cat_general: "सामान्य प्रश्न",
  dp_pr_stolen: "मेरा सोना / पैसा चोरी हो गया — वापस मिलेगा या नहीं?",
  dp_pr_partner: "मेरा साथी अभी मेरे बारे में क्या सोच रहा है?",
  dp_pr_job: "क्या मुझे यह नौकरी / नया पद मिलेगा?",
  dp_pr_marriage: "मेरा विवाह कब तक होगा?",
  dp_pr_health: "मेरी / मेरे प्रियजन की बीमारी ठीक होगी?",
  dp_pr_litigation: "क्या मैं अपना मुकदमा जीतूँगा?",
  dp_pr_travel: "क्या मेरी नियोजित यात्रा सफलतापूर्वक पूरी होगी?",
  pk_headerTitle: "प्रश्न कुंडली",
  pk_headerSub: "सरल कुंडली प्रश्न · Ask से अलग",
  pk_modeAsk: "कुछ भी पूछें",
  pk_modeNumber: "प्रश्न कुंडली",
  pk_initMsg: "🔮 प्रणाम! अपना प्रश्न सीधे लिखें। व्यक्तिगत प्रश्न → आपकी D1 कुंडली + दशा से उत्तर। सामान्य ज्योतिष सिद्धांत → छोटा सरल उत्तर। यह Ask Anything से अलग है।",
  pk_invalidNumber: "⚠️ संख्या 1 से 249 के बीच होनी चाहिए। एक बार और सोचें।",
  pk_qLimit: "आज का प्रश्न सीमा पूर्ण हो गई। सदस्यता अपग्रेड करें।",
  pk_genErr: "कुछ गड़बड़ हुई — पुनः प्रयास करें।",
  pk_netErr: "📡 नेटवर्क त्रुटि — इंटरनेट जाँच कर पुनः प्रयास करें।",
  pk_sankhyaPrefix: "संख्या",
  pk_warnTitle: "प्रश्न काल — सावधानी",
  pk_warnDefault: "मार्गदर्शन के रूप में लें, अंतिम निर्णय नहीं।",
  pk_warnRef: "स्रोत",
  pk_forcedLagna: "बलात लग्न",
  pk_lblRashi: "राशि",
  pk_lblNakshatra: "नक्षत्र",
  pk_cuspKpTitle: "कस्प विश्लेषण (KP सब-लॉर्ड)",
  pk_houseWord: "भाव",
  pk_subLord: "सब-लॉर्ड",
  pk_timingTitle: "⏳ समय (टाइमिंग)",
  pk_classicalTitle: "📜 शास्त्रीय आधार",
  pk_numPlaceholder: "1 — 249",
  pk_numHint: "एक संख्या सोचें",
  pk_qInputPh: "अपना प्रश्न लिखिए…",
  pk_cat_stolen: "सामान मिलेगा?",
  pk_cat_partner: "साथी भावनाएँ",
  pk_cat_job: "नौकरी?",
  pk_cat_marriage: "विवाह कब?",
  pk_cat_health: "स्वास्थ्य?",
  pk_cat_litigation: "केस जीत?",
  pk_cat_travel: "यात्रा?",
  pk_cat_general: "सामान्य",
  fr_headerTitle: "फेस रीडिंग Pro",
  fr_heroEyebrow: "विश्व का प्रथम",
  fr_heroTitle: "वैदिक + विज्ञान\nफेस रीडिंग फ्यूज़न",
  fr_heroSub: "40-पृष्ठीय प्रीमियम PDF रिपोर्ट — 19 प्राचीन और आधुनिक ढाँचों का संगम, कथात्मक शैली में।",
  fr_priceLive: " · अभी उपलब्ध",
  fr_statPages: "पृष्ठ",
  fr_statSections: "अनुभाग",
  fr_statEngines: "इंजन",
  fr_statLandmarks: "लैंडमार्क",
  fr_capInside: "रिपोर्ट के अंदर",
  fr_pv1Title: "ब्रांडेड कवर",
  fr_pv1Sub: "आपकी फ़ोटो · व्यक्तिगत मुहर",
  fr_pv2Title: "7-क्षेत्रीय फेस मैप",
  fr_pv2Sub: "लेबल लैंडमार्क + टिप्पणियाँ",
  fr_pv3Title: "विज़ुअल स्नैपशॉट",
  fr_pv3Sub: "OCEAN रडार + 5-स्कोर चार्ट",
  fr_pv4Title: "सेलेब मैच",
  fr_pv4Sub: "आर्किटाइप × तत्व पुस्तकालय",
  fr_capEngines: "19 विश्लेषण इंजन",
  fr_eng1Group: "ब्रह्मांडीय बुद्धिमत्ताएँ",
  fr_eng1Body: "सामुद्रिक शास्त्र · मुख लक्षण · ललाट रेखा · नेत्र विज्ञान · आयुर्वेदिक प्रकृति · Mian Xiang · 100-वर्ष आयु मानचित्र · Wu Xing 5 तत्व",
  fr_eng2Group: "वैज्ञानिक इंजन",
  fr_eng2Body: "मानवमिति (32 बिंदु) · समरूपता · स्वर्ण अनुपात (φ) · fWHR · स्वास्थ्य संकेतक · Big Five OCEAN · प्रथम प्रभाव · फ़िनोटाइप प्रोफ़ाइल",
  fr_eng3Group: "फ्यूज़न इंजन",
  fr_eng3Body: "वैदिक-विज्ञान क्रॉस-वैलिडेशन · अंक ज्योतिष Combo · भविष्यसूचक संश्लेषण (करियर, विवाह, धन, स्वास्थ्य)",
  fr_capHow: "यह कैसे काम करता है",
  fr_step1Title: "3 सेल्फ़ी अपलोड करें",
  fr_step1Body: "सामने + बायाँ + दायाँ प्रोफ़ाइल (निर्देशित कैप्चर, प्रकाश और कोण जाँच)",
  fr_step2Title: "468 लैंडमार्क निकाले जाते हैं",
  fr_step2Body: "Google Mediapipe — गोपनीयता के लिए डिवाइस पर चलता है",
  fr_step3Title: "19 इंजन समानांतर विश्लेषण करते हैं",
  fr_step3Body: "~75% वास्तविक CV मापन · 0% नकली या हार्डकोड डेटा",
  fr_step4Title: "40-पृष्ठीय PDF बनती है",
  fr_step4Body: "विज़ुअल चार्ट, फेस मैप, कथन · ~45 सेकंड में तैयार",
  fr_capBuilt: "आधारित",
  fr_honest100: "100% ईमानदार डेटा",
  fr_honest75: "75% वास्तविक CV मापन",
  fr_honest20: "20% व्युत्पन्न (वास्तविक संख्याएँ + वर्णन)",
  fr_honest5: "5% क्यूरेटेड (सेलेब लाइब्रेरी, कॉम्बो शीर्षक)",
  fr_honestFoot: "कोई नकली या हार्डकोड रीडिंग नहीं — सब कुछ आपकी वास्तविक फ़ोटो से निकलता है।",
  fr_ctaText: "मेरा फेस रीडिंग शुरू करें",
  fr_ctaSub: "3 सेल्फ़ी अपलोड करें → 30-60 सेकंड में आपके डिवाइस पर 40-पृष्ठीय PDF रिपोर्ट।",
  fr_wipBadge: "जल्द आ रहा है",
  fr_wipTitle: "फेस रीडिंग Pro अभी तैयार हो रहा है",
  fr_wipBody: "हम वैदिक + विज्ञान फेस रीडिंग रिपोर्ट और 40-पृष्ठीय PDF को अंतिम रूप दे रहे हैं। लॉन्च तक अपलोड और भुगतान रोक दिया गया है।",
  fr_wipHint: "अगले ऐप अपडेट के बाद Life Map से फिर देखें।",
  mdFaceReadingSubSoon: "जल्द आ रहा है · वैदिक + विज्ञान फ्यूजन",
  fu_introEyebrow: "चरण 1 / 2",
  fu_introTitle: "3 सेल्फ़ी अपलोड करें",
  fu_introSub: "सामने + बायाँ + दायाँ प्रोफ़ाइल। अच्छी रोशनी में लें, चश्मा उतार दें, बाल माथे से हटा लें।",
  fu_slotFrontLbl: "सामने की सेल्फ़ी",
  fu_slotFrontHint: "कैमरे की ओर सीधे देखें",
  fu_slotLeftLbl: "बायाँ प्रोफ़ाइल",
  fu_slotLeftHint: "अपना बायाँ हिस्सा कैमरे के सामने",
  fu_slotRightLbl: "दायाँ प्रोफ़ाइल",
  fu_slotRightHint: "अपना दायाँ हिस्सा कैमरे के सामने",
  fu_addedTap: "जोड़ा गया · बदलने के लिए दबाएँ",
  fu_capOptional: "वैकल्पिक — बेहतर सटीकता",
  fu_lblAge: "आयु",
  fu_phAge: "जैसे 28",
  fu_lblGender: "लिंग",
  fu_male: "पुरुष",
  fu_female: "महिला",
  fu_lblLanguage: "भाषा",
  fu_camPermNeeded: "कैमरा अनुमति आवश्यक",
  fu_galPermNeeded: "गैलरी अनुमति आवश्यक",
  fu_couldNotPick: "फ़ोटो नहीं ली जा सकी",
  fu_addPhotoTtl: "फ़ोटो जोड़ें",
  fu_addPhotoMsg: "कैमरा या गैलरी से चुनें",
  fu_btnCamera: "कैमरा",
  fu_btnGallery: "गैलरी",
  fu_btnCancel: "रद्द करें",
  fu_addAllFirst: "पहले 3 फ़ोटो जोड़ें",
  fu_progUpload: "फ़ोटो अपलोड हो रही हैं…",
  fu_progAnalyze: "19 इंजन विश्लेषण चल रहा है…",
  fu_progRender: "40-पृष्ठीय PDF रिपोर्ट बन रही है…",
  fu_progSub: "इसमें ~30-60 सेकंड लग सकते हैं। ऐप बंद न करें।",
  fu_errSomething: "कुछ गड़बड़ हुई",
  fu_doneTitle: "रिपोर्ट तैयार!",
  fu_doneSub: "40-पृष्ठीय PDF तैयार हो गई।",
  fu_btnOpenShare: "खोलें / PDF साझा करें",
  fu_btnAnother: "एक और रिपोर्ट बनाएँ",
  fu_processing: "प्रोसेसिंग…",
  fu_btnTryAgain: "पुनः प्रयास करें",
  fu_btnGenerate: "मेरी रिपोर्ट बनाएँ",
  fu_legalLine: "आपकी फ़ोटो केवल विश्लेषण के लिए उपयोग होती हैं · 24 घंटे बाद स्वतः हटा दी जाती हैं · सर्वर पर एन्क्रिप्टेड",
  fu_shareNotAvail: "इस डिवाइस पर साझा करना उपलब्ध नहीं है",
  fu_sessIdMissing: "सर्वर से सत्र ID नहीं मिली",
  fpp_headerTitle: "Cosmic Portrait",
  fpp_heroTitle: "आपका भावी जीवनसाथी",
  fpp_heroSubMale: "आपकी कुंडली के 30+ शास्त्रीय नियमों से उनका रूप, स्वभाव और दिशा प्रकट होगी — D1, D9 नवमांश, D3 द्रेक्काण, D30 त्रिंशांश, KP 7वें कस्पल सब-लॉर्ड, उपपद लग्न, दाराकारक, आरूढ़ A7, वर्गोत्तम और अष्टकवर्ग का गहन विश्लेषण।",
  fpp_heroSubFemale: "आपकी कुंडली के 30+ शास्त्रीय नियमों से उनका रूप, स्वभाव और दिशा प्रकट होगी — D1, D9 नवमांश, D3 द्रेक्काण, D30 त्रिंशांश, KP 7वें कस्पल सब-लॉर्ड, उपपद लग्न, दाराकारक, आरूढ़ A7, वर्गोत्तम और अष्टकवर्ग का गहन विश्लेषण।",
  fpp_primaryKundli: "मुख्य कुंडली",
  fpp_btnReveal: "मेरा भावी साथी प्रकट करें",
  fpp_warnNoKundli: "कृपया पहले अपनी मुख्य कुंडली बनाएँ। प्रोफ़ाइल → कुंडली जोड़ें।",
  fpp_infoTitle: "💎 यह क्या बताएगा",
  fpp_b1: "रूप-रंग: चेहरा, रंगत, आँखें, बाल, शरीर",
  fpp_b2: "स्वभाव: vibe, गुण, स्त्री/पुरुष की शक्ति",
  fpp_b3: "व्यवसाय की दिशा (D10 + 7वाँ स्वामी)",
  fpp_b4: "आपसे आयु अंतर (छोटा / बराबर / बड़ा)",
  fpp_b5: "दिशा जिस ओर से आएँगे (पूर्व / उत्तर / आदि)",
  fpp_b6: "अष्टकवर्ग 7वाँ बिंदु — आकर्षण शक्ति",
  fpp_disclaimer1: "* यह एक दिव्य झलक है — शास्त्रीय हस्ताक्षर का कलात्मक चित्रण। वास्तविक व्यक्ति से हू-ब-हू मेल आवश्यक नहीं। व्यक्तित्व, vibe और दिशा शास्त्रीय नियमों पर आधारित हैं।",
  fpp_loadingTitle: "Cosmic Portrait तैयार हो रहा है",
  fpp_msgAlign: "तारे संरेखित हो रहे हैं…",
  fpp_msgAlignFull: "आपकी कुंडली तारों के साथ संरेखित हो रही है…",
  fpp_msgComputing: "पहले आपकी कुंडली गणना हो रही है…",
  fpp_msgKundliQuota: "आपका कुंडली कोटा समाप्त हो गया। सदस्यता अपग्रेड करें।",
  fpp_msgKundliFail: "कुंडली की गणना नहीं हो सकी। नेटवर्क जाँच कर पुनः प्रयास करें।",
  fpp_msgTaskExpire: "कार्य समाप्त हो गया। कृपया पुनः शुरू करें।",
  fpp_msgTaskIdMiss: "कार्य ID नहीं मिली। पुनः प्रयास करें।",
  fpp_msgNetSlow: "नेटवर्क धीमा है। इंटरनेट जाँच कर पुनः प्रयास करें।",
  fpp_msgStarsBusy: "तारे अभी व्यस्त हैं",
  fpp_tipText: "कृपया प्रतीक्षा करें… तारे आपके जीवनसाथी का सार पढ़ रहे हैं।\nलगभग 15-25 सेकंड।",
  fpp_btnCancel: "रद्द करें",
  fpp_imgFailed: "छवि तैयार नहीं हो सकी।",
  fpp_imgBadge: "✨ COSMIC PORTRAIT — दिव्य झलक",
  fpp_traitTitle: "🌟 रूप-रंग और स्वभाव",
  fpp_lblFace: "चेहरा",
  fpp_lblComplexion: "रंगत",
  fpp_lblBuild: "गठन",
  fpp_lblEyes: "आँखें",
  fpp_lblEyebrows: "भौंहें",
  fpp_lblNose: "नाक",
  fpp_lblLips: "होंठ",
  fpp_lblHair: "बाल",
  fpp_lblVibe: "Vibe",
  fpp_vargottama: "✨ वर्गोत्तम प्रबल — विशेषताएँ विशेष रूप से सामंजस्यपूर्ण",
  fpp_practTitle: "🧭 व्यावहारिक अंतर्दृष्टि",
  fpp_lblAge: "आयु",
  fpp_lblDirection: "दिशा",
  fpp_lblProfHint: "व्यवसाय संकेत",
  fpp_lblAttraction: "आकर्षण",
  fpp_classicalTtl: "📜 शास्त्रीय आधार",
  fpp_disclaimer2: "* Cosmic Portrait — दिव्य झलक। यह एक कलात्मक विश्लेषण है जो आपकी कुंडली के 7वें भाव, D9 नवमांश, KP कस्प और जैमिनी उपपद/आरूढ़ सूत्रों पर आधारित है। वास्तविक चेहरे से हू-ब-हू मेल हो या न हो — व्यक्तित्व, vibe और दिशा सही होगी।",
  fpp_btnRevealAgain: "फिर प्रकट करें",
  fpp_errTitle: "Cosmic Portrait अभी तैयार नहीं",
  fpp_errDefault: "तारे अभी व्यस्त हैं। कृपया कुछ देर बाद पुनः प्रयास करें।",
  fpp_errPortraitFail: "Cosmic Portrait अभी तैयार नहीं हो सका।",
  fpp_btnTryAgain: "पुनः प्रयास करें",
  fpp_alertBirthTtl: "जन्म विवरण आवश्यक",
  fpp_alertBirthMsg: "कृपया अपनी मुख्य प्रोफ़ाइल में जन्म तिथि/समय/स्थान पहले जोड़ें, फिर Cosmic Portrait प्रकट करें।",
  fpp_errTimeout: "गहन तारकीय विश्लेषण में अधिक समय लग रहा है। कृपया पुनः प्रयास करें।",
  lg_title: "क़ानूनी और नीतियाँ",
  lg_subtitle: "गोपनीयता, शर्तें, रिफंड और अस्वीकरण",
  lg_lastUpdated: "17 अप्रैल 2026",
  lg_h_privacy: "गोपनीयता नीति",
  lg_p_privacyIntro: "Cosmic Lens (\"हम\", \"हमें\", \"हमारा\") आपकी गोपनीयता का सम्मान करता है। यह गोपनीयता नीति बताती है कि जब आप हमारे मोबाइल ऐप और संबंधित सेवाओं (\"सेवा\") का उपयोग करते हैं, तो हम कौन-सी व्यक्तिगत जानकारी एकत्र करते हैं, उसका उपयोग कैसे करते हैं, और आपके पास क्या विकल्प हैं। Cosmic Lens का उपयोग करके आप नीचे वर्णित प्रथाओं से सहमत होते हैं।",
  lg_callout_privacy: "हम आपका व्यक्तिगत डेटा नहीं बेचते। हम आपकी कुंडली, जन्म विवरण या चैट इतिहास विज्ञापनदाताओं के साथ साझा नहीं करते।",
  lg_s1_title: "1. हम कौन-सी जानकारी एकत्र करते हैं",
  lg_s1_a: "(क) खाता जानकारी — नाम, ईमेल पता, मोबाइल नंबर (फ़ोन से साइन अप करने पर), Google खाता ID (Google साइन-इन के साथ)। पासवर्ड scrypt से हैश करके सुरक्षित रूप से संग्रहीत।",
  lg_s1_b: "(ख) जन्म एवं प्रोफ़ाइल डेटा — पूरा नाम, जन्म तिथि, जन्म समय, जन्म स्थान, लिंग, और भाषा वरीयता। यह आपकी वैदिक कुंडली गणना के लिए न्यूनतम आवश्यक है।",
  lg_s1_c: "(ग) उत्पन्न सामग्री — आपकी कुंडली चार्ट, दशाएँ, अनुकूलता रिपोर्ट, ज्योतिष प्रश्न/उत्तर इतिहास, और सहेजी गई प्रोफ़ाइलें।",
  lg_s1_d: "(घ) भुगतान जानकारी — पूरी तरह हमारे भुगतान प्रोसेसर Cashfree Payments द्वारा संभाली जाती है। हम केवल ऑर्डर ID, प्लान, राशि और सफलता/विफलता स्थिति संग्रहीत करते हैं। हम कभी कार्ड नंबर, UPI PIN, CVV या बैंकिंग क्रेडेंशियल संग्रहीत नहीं करते।",
  lg_s1_e: "(ङ) डिवाइस एवं तकनीकी जानकारी — डिवाइस मॉडल, OS संस्करण, ऐप संस्करण, भाषा, समय क्षेत्र, और क्रैश लॉग। केवल डायग्नोस्टिक्स के लिए।",
  lg_s2_title: "2. हम आपकी जानकारी का उपयोग कैसे करते हैं",
  lg_s2_b1: "आपका खाता बनाने और बनाए रखने के लिए।",
  lg_s2_b2: "आपकी कुंडली, दशाएँ, दोष, अनुकूलता और अन्य ज्योतिषीय रिपोर्ट गणना के लिए।",
  lg_s2_b3: "आपके प्रश्नों के ज्योतिष-आधारित उत्तर देने के लिए, केवल आपकी कुंडली डेटा से — आपकी पहचान से नहीं।",
  lg_s2_b4: "Cashfree के माध्यम से सदस्यता भुगतान संसाधित करने के लिए।",
  lg_s2_b5: "दैनिक प्रश्न सीमाएँ और उचित-उपयोग नियम लागू करने के लिए।",
  lg_s2_b6: "वैकल्पिक सूचनाएँ भेजने के लिए (दैनिक राशिफल, पंचांग, मुहूर्त रिमाइंडर) — सेटिंग्स में बंद कर सकते हैं।",
  lg_s2_b7: "धोखाधड़ी रोकने, क्रैश डीबग करने और सेवा गुणवत्ता सुधारने के लिए।",
  lg_s2_b8: "क़ानूनी दायित्वों का पालन करने के लिए।",
  lg_s3_title: "3. तृतीय-पक्ष सेवाएँ",
  lg_s3_intro: "हम इन विश्वसनीय भागीदारों के साथ केवल आवश्यक न्यूनतम डेटा साझा करते हैं:",
  lg_s3_b1: "Google Sign-In — Google लॉगिन चुनने पर पहचान सत्यापित करता है। हमें आपका नाम, ईमेल और Google ID मिलती है।",
  lg_s3_b2: "Cashfree Payments (भारत) — UPI, कार्ड और नेट-बैंकिंग लेनदेन संसाधित करता है। PCI-DSS Level 1 अनुपालक।",
  lg_s3_b3: "Expo / Google Play Services — केवल पुश नोटिफिकेशन डिलीवरी। वे कोई सामग्री नहीं पढ़ते।",
  lg_s3_b4: "क्लाउड होस्टिंग (Replit / AWS) — जहाँ संभव हो भारत क्षेत्र में एन्क्रिप्टेड डेटाबेस स्टोरेज।",
  lg_s3_outro: "इन सेवाओं की अपनी गोपनीयता नीतियाँ हैं जिन्हें आप पढ़ें — हम प्रोत्साहित करते हैं।",
  lg_s4_title: "4. डेटा प्रतिधारण",
  lg_s4_p: "जब तक आपका खाता सक्रिय है तब तक हम आपका खाता और कुंडली डेटा बनाए रखते हैं। यदि आप खाता हटाते हैं (अनुभाग 7 देखें) तो हम 30 दिन के भीतर आपका व्यक्तिगत डेटा स्थायी रूप से मिटा देते हैं, सिवाय जहाँ कानूनी रूप से प्रतिधारण आवश्यक हो (जैसे भारतीय कानून के तहत कर चालान 7 वर्ष)।",
  lg_s5_title: "5. डेटा सुरक्षा",
  lg_s5_b1: "सारा API ट्रैफ़िक TLS 1.2+ से एन्क्रिप्टेड है।",
  lg_s5_b2: "पासवर्ड scrypt से हैश किए जाते हैं (कभी प्लेन टेक्स्ट में संग्रहीत नहीं)।",
  lg_s5_b3: "API पहुँच के लिए हर अनुरोध पर प्रति-उपयोगकर्ता API key सत्यापित होती है।",
  lg_s5_b4: "डेटाबेस बैकअप विश्राम पर एन्क्रिप्टेड हैं।",
  lg_s5_b5: "प्रोडक्शन डेटा तक पहुँच केवल अधिकृत इंजीनियरों तक सीमित है।",
  lg_s6_title: "6. आपके अधिकार",
  lg_s6_intro: "Digital Personal Data Protection Act, 2023 (भारत) और समान कानूनों के तहत, आपके पास ये अधिकार हैं:",
  lg_s6_b1: "आपके बारे में हमारे पास मौजूद व्यक्तिगत डेटा तक पहुँच।",
  lg_s6_b2: "ग़लत या पुरानी जानकारी सुधारना।",
  lg_s6_b3: "सहमति वापस लेना और खाता हटाना।",
  lg_s6_b4: "अपनी कुंडली डेटा का JSON प्रारूप में निर्यात प्राप्त करना।",
  lg_s6_b5: "भारत के डेटा प्रोटेक्शन बोर्ड में शिकायत दर्ज करना।",
  lg_s6_outro: "इनमें से किसी अधिकार का प्रयोग करने के लिए, support@cosmiclens.app पर ईमेल करें।",
  lg_s7_title: "7. खाता हटाना",
  lg_s7_p: "आप कभी भी Profile → Delete Account से खाता हटा सकते हैं। हटाना स्थायी है और 30 दिन के भीतर सभी प्रोफ़ाइल, कुंडलियाँ, चैट इतिहास और व्यक्तिगत डेटा हटा देता है।",
  lg_s8_title: "8. बच्चे",
  lg_s8_p: "Cosmic Lens 13 वर्ष से कम के बच्चों के लिए नहीं है। हम जानबूझकर बच्चों का व्यक्तिगत डेटा एकत्र नहीं करते। यदि किसी बच्चे ने खाता बनाया है, हमसे संपर्क करें, हम तुरंत हटा देंगे।",
  lg_s9_title: "9. अंतर्राष्ट्रीय उपयोगकर्ता",
  lg_s9_p: "Cosmic Lens भारत से संचालित है। यदि आप भारत के बाहर से Service उपयोग करते हैं, तो आपकी जानकारी भारत में स्थानांतरित और संसाधित होगी, जहाँ डेटा-संरक्षण कानून आपके देश से भिन्न हो सकते हैं।",
  lg_s10_title: "10. इस नीति में परिवर्तन",
  lg_s10_p: "हम इस गोपनीयता नीति को समय-समय पर अपडेट कर सकते हैं। शीर्ष पर \"अंतिम अद्यतन\" तिथि नवीनतम परिवर्तन दिखाएगी। महत्वपूर्ण परिवर्तन ऐप में कम से कम 7 दिन पहले बताए जाएँगे।",
  lg_s11_title: "11. हमसे संपर्क करें",
  lg_s11_intro: "गोपनीयता-संबंधी प्रश्न, अनुरोध या शिकायतों के लिए:",
  lg_s11_b1: "ईमेल: support@cosmiclens.app",
  lg_s11_b2: "शिकायत अधिकारी: शिकायत प्राप्ति के 30 दिन के भीतर उपलब्ध",
  lg_h_terms: "सेवा की शर्तें",
  lg_p_termsIntro: "ये Terms of Service (\"शर्तें\") Cosmic Lens मोबाइल ऐप और संबंधित सेवाओं (\"सेवा\") तक आपकी पहुँच और उपयोग को नियंत्रित करती हैं। खाता बनाकर, डाउनलोड करके या सेवा उपयोग करके आप इन शर्तों को स्वीकार करते हैं। यदि सहमत नहीं हैं, तो कृपया सेवा का उपयोग न करें।",
  lg_t1_title: "1. पात्रता",
  lg_t1_b1: "Cosmic Lens उपयोग के लिए आप कम से कम 13 वर्ष के होने चाहिए।",
  lg_t1_b2: "यदि 18 वर्ष से कम हैं, तो माता-पिता या अभिभावक की अनुमति होनी चाहिए।",
  lg_t1_b3: "आप पुष्टि करते हैं कि आपके द्वारा दी गई जानकारी (नाम, जन्म तिथि, समय, स्थान) सत्य और सटीक है। ग़लत जन्म डेटा से ग़लत ज्योतिषीय परिणाम मिलेंगे।",
  lg_t2_title: "2. खाता और सुरक्षा",
  lg_t2_b1: "लॉगिन क्रेडेंशियल सुरक्षित रखने की ज़िम्मेदारी आपकी है।",
  lg_t2_b2: "आप अपना खाता साझा नहीं कर सकते या किसी और का खाता उपयोग नहीं कर सकते।",
  lg_t2_b3: "किसी भी अनधिकृत पहुँच के बारे में हमें तुरंत सूचित करें।",
  lg_t2_b4: "हम उन खातों को निलंबित करने का अधिकार रखते हैं जो धोखाधड़ी, दुरुपयोग या इन शर्तों के उल्लंघन में संलग्न हैं।",
  lg_t3_title: "3. सेवा",
  lg_t3_p: "Cosmic Lens वैदिक-ज्योतिष गणनाएँ देता है — कुंडली, दशाएँ, दोष, विवाह अनुकूलता, पंचांग, मुहूर्त, अंक ज्योतिष, वास्तु, शुभ तत्व और ज्योतिष-आधारित प्रश्नोत्तर। गणनाएँ पारंपरिक वैदिक सिद्धांतों (लाहिरी अयनांश) का सटीक एफेमेरिस डेटा के साथ पालन करती हैं।",
  lg_t4_title: "4. सदस्यता योजनाएँ",
  lg_t4_intro: "Cosmic Lens निम्न योजनाएँ प्रदान करता है:",
  lg_t4_b1: "Free — सीमित सुविधाएँ, 1 ज्योतिष प्रश्न/दिन",
  lg_t4_b2: "7-दिवसीय फ़्री ट्रायल — नए उपयोगकर्ताओं के लिए Basic सुविधाएँ, एकमात्र, कोई भुगतान नहीं",
  lg_t4_b3: "Basic — ₹199/माह या ₹1,799/वर्ष, 10 ज्योतिष प्रश्न/दिन और बुनियादी विश्लेषण",
  lg_t4_b4: "Pro — ₹399/माह या ₹2,999/वर्ष, असीमित ज्योतिष प्रश्न, पूर्ण गहन विश्लेषण, 6-माह टाइमलाइन, कार्मिक अंतर्दृष्टि, PDF रिपोर्ट",
  lg_t4_outro: "सदस्यताएँ हर बिलिंग अवधि के अंत में स्वतः नवीनीकृत होती हैं, जब तक नवीनीकरण से कम से कम 24 घंटे पहले रद्द न की जाएँ। आप Profile → Subscription → Cancel से या सहायता से संपर्क करके कभी भी रद्द कर सकते हैं।",
  lg_t5_title: "5. भुगतान",
  lg_t5_p: "भुगतान Cashfree Payments द्वारा संसाधित होते हैं। खरीदारी करके आप हमारी और Cashfree दोनों की शर्तों से सहमत होते हैं। सभी मूल्य भारतीय रुपये (₹) में और लागू GST सहित हैं।",
  lg_t6_title: "6. रिफंड नीति",
  lg_t6_p: "कृपया पूर्ण विवरण के लिए नीचे रिफंड एवं रद्दीकरण अनुभाग देखें। सारांश में, सभी बिक्री सामान्यतः अंतिम हैं, लेकिन तकनीकी विफलताओं, दोहरे शुल्कों या भुगतान के 7 दिनों के भीतर अप्रयुक्त सेवा के लिए रिफंड दिए जा सकते हैं।",
  lg_t7_title: "7. उपयोगकर्ता आचरण — आप ये नहीं करेंगे",
  lg_t7_b1: "सेवा का कोई अवैध या धोखाधड़ी उद्देश्य के लिए उपयोग।",
  lg_t7_b2: "सेवा को रिवर्स-इंजीनियर, डीकंपाइल या स्क्रैप करना।",
  lg_t7_b3: "फ़्री या ट्रायल सुविधाओं के दुरुपयोग के लिए बॉट्स, स्क्रिप्ट्स या स्वचालित उपकरण।",
  lg_t7_b4: "सेवा से सामग्री को पुनः बेचना, सबलाइसेंस या पुनः प्रकाशित करना।",
  lg_t7_b5: "सहमति के बिना किसी अन्य व्यक्ति के झूठे जन्म डेटा प्रस्तुत करना।",
  lg_t7_b6: "दूसरों को परेशान, धमकाना या प्रतिरूपण करना।",
  lg_t8_title: "8. बौद्धिक संपदा",
  lg_t8_p: "सेवा में सभी सामग्री, डिज़ाइन, कोड, ब्रांडिंग, एल्गोरिदम और गणित रिपोर्ट Cosmic Lens या इसके लाइसेंसकर्ताओं की बौद्धिक संपदा हैं। आपको केवल व्यक्तिगत, गैर-वाणिज्यिक उपयोग के लिए सीमित, गैर-अनन्य, गैर-हस्तांतरणीय लाइसेंस मिलता है।",
  lg_t9_title: "9. इंजन-जनित उत्तर",
  lg_t9_p: "\"Ask\" सुविधा आपकी कुंडली का नियम-आधारित और जनरेटिव विश्लेषण उपयोग करती है। ज्योतिष उत्तर सॉफ़्टवेयर द्वारा उत्पन्न होते हैं और उनमें त्रुटियाँ, अस्पष्टताएँ या विरोधाभास हो सकते हैं। वे पेशेवर सलाह का विकल्प नहीं हैं।",
  lg_t10_title: "10. कोई पेशेवर सलाह नहीं",
  lg_t10_callout: "Cosmic Lens केवल आध्यात्मिक और मनोरंजन उद्देश्यों के लिए है। ज्योतिषीय अंतर्दृष्टि पेशेवर चिकित्सा, क़ानूनी, वित्तीय, मनोवैज्ञानिक या संबंध सलाह का विकल्प नहीं है। महत्वपूर्ण जीवन निर्णयों के लिए हमेशा योग्य पेशेवरों से परामर्श करें।",
  lg_t11_title: "11. अस्वीकरण",
  lg_t11_p: "सेवा \"जैसी है\" और \"जैसी उपलब्ध है\" के रूप में बिना किसी प्रत्यक्ष या निहित वारंटी के प्रदान की जाती है। हम गारंटी नहीं देते कि ज्योतिषीय भविष्यवाणियाँ सच होंगी, सेवा त्रुटि-मुक्त होगी या हमेशा उपलब्ध होगी। किसी भविष्यवाणी का पिछला प्रदर्शन भविष्य के परिणामों का संकेत नहीं देता।",
  lg_t12_title: "12. दायित्व की सीमा",
  lg_t12_p: "कानून द्वारा अधिकतम सीमा तक, Cosmic Lens, इसके अधिकारी, कर्मचारी और भागीदार आपके सेवा उपयोग से उत्पन्न किसी अप्रत्यक्ष, आकस्मिक, परिणामी या दंडात्मक हानि के लिए उत्तरदायी नहीं होंगे। किसी दावे के लिए हमारी कुल देयता दावे से 12 माह पहले आपने हमें भुगतान की राशि, या ₹1,000, जो भी अधिक हो, तक सीमित है।",
  lg_t13_title: "13. समाप्ति",
  lg_t13_p: "आप कभी भी खाता हटाकर सेवा का उपयोग बंद कर सकते हैं। यदि आप इन शर्तों का उल्लंघन करते हैं या अन्य उपयोगकर्ताओं या सेवा के लिए हानिकारक आचरण में संलग्न होते हैं, तो हम आपकी पहुँच तुरंत निलंबित या समाप्त कर सकते हैं।",
  lg_t14_title: "14. शर्तों में परिवर्तन",
  lg_t14_p: "हम इन शर्तों को समय-समय पर अपडेट कर सकते हैं। परिवर्तन प्रभावी होने के बाद सेवा का निरंतर उपयोग नई शर्तों की स्वीकृति माना जाएगा। महत्वपूर्ण परिवर्तन ऐप में कम से कम 7 दिन पहले सूचित किए जाएँगे।",
  lg_t15_title: "15. शासी क़ानून और क्षेत्राधिकार",
  lg_t15_p: "ये शर्तें भारत के कानूनों द्वारा शासित हैं। इन शर्तों या सेवा से उत्पन्न या संबंधित कोई भी विवाद आपके पंजीकृत शहर, भारत के न्यायालयों के विशेष क्षेत्राधिकार के अधीन होंगे।",
  lg_t16_title: "16. संपर्क",
  lg_t16_p: "इन शर्तों के बारे में प्रश्नों के लिए, support@cosmiclens.app पर ईमेल करें।",
  lg_h_refund: "रिफंड और रद्दीकरण",
  lg_p_refundIntro: "Cosmic Lens में हम चाहते हैं हर सदस्य का अच्छा अनुभव हो। यह नीति बताती है कि सदस्यता शुल्क कब रिफंडेबल हैं और सदस्यता कैसे रद्द करें।",
  lg_callout_refund: "सदस्यता लेने से पहले 7-दिवसीय फ़्री ट्रायल का उपयोग करें — यह आपको Basic सुविधाओं का अनुभव बिना कोई शुल्क के देता है ताकि भुगतान से पहले आप निर्णय ले सकें।",
  lg_r1_title: "1. सदस्यता रद्दीकरण",
  lg_r1_intro: "आप मासिक या वार्षिक सदस्यता कभी भी रद्द कर सकते हैं:",
  lg_r1_b1: "Profile → Subscription खोलें और \"Cancel Subscription\" टैप करें।",
  lg_r1_b2: "या अपनी पंजीकृत ईमेल से support@cosmiclens.app पर ईमेल करें।",
  lg_r1_outro: "रद्दीकरण के बाद, वर्तमान बिलिंग अवधि के अंत तक प्रीमियम पहुँच बनी रहेगी। आगे कोई शुल्क नहीं लिया जाएगा।",
  lg_r2_title: "2. रिफंड कब दिए जाते हैं",
  lg_r2_intro: "इन स्थितियों में हम पूर्ण या आनुपातिक रिफंड देंगे:",
  lg_r2_b1: "दोहरा शुल्क / डुप्लीकेट भुगतान — डुप्लीकेट राशि का पूर्ण रिफंड, 5–7 कार्य दिवसों में संसाधित।",
  lg_r2_b2: "भुगतान सफल पर प्लान सक्रिय नहीं हुआ — पूर्ण रिफंड या मैन्युअल प्लान सक्रियण, आपकी पसंद।",
  lg_r2_b3: "तकनीकी विफलता जो 72 घंटे से अधिक पहुँच रोकती है — अप्रयुक्त दिनों का आनुपातिक रिफंड।",
  lg_r2_b4: "पहली सशुल्क सदस्यता के 7 दिनों के भीतर रद्द करने पर यदि 5 से कम सशुल्क सुविधाएँ उपयोग की हैं — पूर्ण रिफंड (प्रति उपयोगकर्ता एक बार)।",
  lg_r3_title: "3. रिफंड कब नहीं दिए जाते",
  lg_r3_b1: "7-दिन की अवधि के बाद विचार बदलना।",
  lg_r3_b2: "ज्योतिषीय भविष्यवाणी सच नहीं हुई — भविष्यवाणियाँ व्याख्यात्मक मार्गदर्शन हैं, गारंटी नहीं (अस्वीकरण देखें)।",
  lg_r3_b3: "ऑटो-नवीनीकरण से पहले रद्द करना भूल गए — परंतु हम अनुरोध पर भविष्य के नवीनीकरण तुरंत रद्द कर देंगे।",
  lg_r3_b4: "मासिक योजनाओं के मध्य-चक्र में रद्द होने पर आंशिक-माह रिफंड।",
  lg_r3_b5: "Free या Trial योजनाओं के लिए रिफंड (कोई भुगतान नहीं हुआ था)।",
  lg_r3_b6: "भुगतान के 30 दिनों के बाद अनुरोधित रिफंड।",
  lg_r4_title: "4. रिफंड का अनुरोध कैसे करें",
  lg_r4_intro: "support@cosmiclens.app पर इसके साथ ईमेल करें:",
  lg_r4_b1: "आपका पंजीकृत ईमेल पता या मोबाइल नंबर",
  lg_r4_b2: "ऑर्डर ID (Profile → Subscription → Payment History में दिखती है)",
  lg_r4_b3: "रिफंड अनुरोध का कारण",
  lg_r4_outro: "हम सभी रिफंड अनुरोधों का 3 कार्य दिवसों के भीतर उत्तर देते हैं। स्वीकृत रिफंड Cashfree द्वारा आपकी मूल भुगतान विधि पर 5–10 कार्य दिवसों में संसाधित होते हैं।",
  lg_r5_title: "5. विफल भुगतान",
  lg_r5_p: "यदि कोई भुगतान विफल हो, तो कोई शुल्क नहीं लिया जाता। यदि बैंक \"लंबित\" शुल्क दिखाता है, तो RBI दिशानिर्देशों के अनुसार 5–7 कार्य दिवसों में स्वतः उलट जाता है। इनके लिए हमसे संपर्क करने की आवश्यकता नहीं है।",
  lg_r6_title: "6. सदस्यता ऑटो-नवीनीकरण",
  lg_r6_p: "मासिक और वार्षिक योजनाएँ स्वतः नवीनीकृत होती हैं। हम हर नवीनीकरण से पहले ईमेल या ऐप सूचना द्वारा रिमाइंडर भेजेंगे। नवीनीकरण रोकने के लिए, बस नवीनीकरण तिथि से पहले रद्द करें — कोई शुल्क नहीं लिया जाएगा।",
  lg_r7_title: "7. चार्जबैक",
  lg_r7_p: "यदि आप पहले हमसे संपर्क करने के बजाय सीधे बैंक के माध्यम से चार्जबैक शुरू करते हैं, तो आपका खाता जाँच लंबित रहने तक निलंबित कर दिया जाएगा। हम हमेशा सीधे समस्याओं को हल करना पसंद करते हैं — पहले हमें ईमेल करें।",
  lg_r8_title: "8. रिफंड के लिए संपर्क",
  lg_r8_b1: "ईमेल: support@cosmiclens.app",
  lg_r8_b2: "विषय पंक्ति: \"Refund Request — [Order ID]\"",
  lg_r8_b3: "प्रतिक्रिया समय: 3 कार्य दिवसों के भीतर",
  lg_h_disclaimer: "ज्योतिष अस्वीकरण",
  lg_callout_disc: "Cosmic Lens केवल आध्यात्मिक अन्वेषण, आत्म-चिंतन और मनोरंजन उद्देश्यों के लिए है। यह पेशेवर चिकित्सा, क़ानूनी, वित्तीय, मनोवैज्ञानिक या संबंध सलाह का विकल्प नहीं है।",
  lg_d1_title: "1. ज्योतिष की प्रकृति",
  lg_d1_p: "वैदिक ज्योतिष (Jyotish) एक प्राचीन कला और दार्शनिक परंपरा है। Cosmic Lens में दी गई व्याख्याएँ, भविष्यवाणियाँ, दशाएँ, दोष, मुहूर्त और उपाय शास्त्रीय सिद्धांतों और आधुनिक एल्गोरिथमिक विश्लेषण को प्रतिबिंबित करते हैं। ये प्रकृति में व्याख्यात्मक हैं और वैज्ञानिक रूप से सत्यापन योग्य नहीं हैं।",
  lg_d2_title: "2. कोई गारंटीकृत परिणाम नहीं",
  lg_d2_p: "कोई भी ज्योतिषीय भविष्यवाणी या अंतर्दृष्टि सच होने की गारंटी नहीं देती। जीवन में परिणाम कई कारकों पर निर्भर करते हैं — आपकी स्वतंत्र इच्छा, विकल्प, कर्म, परिवेश और परिस्थितियाँ — जिन्हें ज्योतिष पूरी तरह नहीं पकड़ सकता।",
  lg_d3_title: "3. पेशेवरों का विकल्प नहीं",
  lg_d3_intro: "Cosmic Lens सामग्री का उपयोग महत्वपूर्ण जीवन निर्णयों के एकमात्र आधार के रूप में कभी नहीं किया जाना चाहिए। हमेशा उपयुक्त योग्य पेशेवरों से परामर्श करें:",
  lg_d3_b1: "स्वास्थ्य संबंधी चिंताएँ — पंजीकृत चिकित्सक से मिलें। ज्योतिषीय पठन के आधार पर दवा बंद या परिवर्तित न करें।",
  lg_d3_b2: "मानसिक स्वास्थ्य — लाइसेंस प्राप्त मनोवैज्ञानिक या मनोचिकित्सक से बात करें। यदि संकट में हैं, तो iCall (भारत) 9152987821 या अपनी स्थानीय हेल्पलाइन कॉल करें।",
  lg_d3_b3: "क़ानूनी मामले — योग्य वकील से परामर्श करें।",
  lg_d3_b4: "वित्तीय / निवेश निर्णय — SEBI-पंजीकृत निवेश सलाहकार से परामर्श करें।",
  lg_d3_b5: "संबंध और विवाह — काउंसलर से परामर्श करें; अनुकूलता स्कोर कभी भी खुले संवाद और सहमति का स्थान नहीं ले सकते।",
  lg_d4_title: "4. इंजन-जनित सामग्री",
  lg_d4_p: "\"Ask\" सुविधा आपकी कुंडली का विश्लेषण करने के लिए स्वचालित सॉफ़्टवेयर (नियम-आधारित इंजन) का उपयोग करती है। उत्तर कोड द्वारा उत्पन्न होते हैं और उनमें त्रुटियाँ, चूक, विरोधाभास या सांस्कृतिक रूप से अनुपयुक्त शब्दावली हो सकती है। ये किसी व्यक्तिगत ज्योतिषी द्वारा समर्थित नहीं हैं।",
  lg_d5_title: "5. उपाय",
  lg_d5_p: "सुझाए गए उपाय (मंत्र, रत्न, दान, व्रत, पूजा) शास्त्रीय ग्रंथों से लिए गए हैं। उन्हें अपनाने से किसी विशिष्ट परिणाम की हम गारंटी नहीं देते। किसी भी उपाय को अपनाने से पहले किसी योग्य वैदिक ज्योतिषी या गुरु से परामर्श करें, विशेष रूप से रत्न और बीज मंत्र।",
  lg_d6_title: "6. जन्म-डेटा की सटीकता",
  lg_d6_p: "ज्योतिषीय गणनाएँ आपके जन्म समय और स्थान के प्रति अत्यंत संवेदनशील हैं। केवल 4-मिनट की त्रुटि भी आपका लग्न बदल सकती है। हम सलाह देते हैं कि अस्पताल रिकॉर्ड या जन्म प्रमाण पत्र से जन्म समय सत्यापित करें। ग़लत इनपुट से ग़लत परिणाम उत्पन्न होंगे।",
  lg_d7_title: "7. सांस्कृतिक और क्षेत्रीय भिन्नताएँ",
  lg_d7_p: "Cosmic Lens पारंपरिक वैदिक (लाहिरी / चित्रपक्ष) अयनांश का उपयोग करता है। पाश्चात्य, उष्णकटिबंधीय, KP, कृष्णमूर्ति और तांत्रिक ज्योतिषी विभिन्न प्रणालियों का उपयोग कर सकते हैं और भिन्न निष्कर्ष पर पहुँच सकते हैं। इनमें से कोई भी प्रणाली \"ग़लत\" नहीं है — ये भिन्न लेंस हैं।",
  lg_d8_title: "8. आपातकालीन स्थितियाँ",
  lg_d8_callout: "यदि आप किसी चिकित्सा आपातकाल या आत्म-हानि के विचारों का अनुभव कर रहे हैं, कृपया तुरंत अपनी स्थानीय आपातकालीन सेवाओं को कॉल करें। संकट सहायता के लिए इस ऐप पर निर्भर न रहें। भारत: 112 (आपातकाल), iCall 9152987821 (मानसिक स्वास्थ्य)।",
  lg_d9_title: "9. स्वीकृति",
  lg_d9_p: "Cosmic Lens का उपयोग करके आप स्वीकार करते हैं कि आपने यह अस्वीकरण पढ़ और समझ लिया है तथा सेवा का जिम्मेदारी से उपयोग करने हेतु सहमत हैं।",
  bv_headerTitle: "बिज़नेस वास्तु",
  bv_cardTitle: "प्रीमियम बिज़नेस वास्तु",
  bv_cardBody: "अपने स्थल लेआउट को स्वामी की कुंडली और चल रही महादशा के साथ मिलाकर एक व्यक्तिगत, आजीवन प्राथमिकता योजना प्राप्त करें।",
  bv_cardBodySmall: "आपके व्यापार स्थल को स्वामी की कुंडली और चल रही महादशा के साथ मिलाकर एक व्यक्तिगत सुधार योजना बनाई जाती है।",
  bv_secBizType: "व्यवसाय प्रकार",
  bv_secPremiseName: "स्थल का नाम",
  bv_phPremiseName: "जैसे अंधेरी दुकान, पवई HQ",
  bv_premiseHint: "आवश्यक — आपका एक-बार-अनलॉक इसी स्थल नाम से मिलाया जाता है।",
  bv_refineRooms: "वैकल्पिक: रूम्स परिष्कृत करें",
  bv_premiseLayout: "स्थल लेआउट",
  bv_engineWillDetect: "Photo Engine आपके अपलोड से रूम्स पहचानेगा। आप यहाँ रूम्स सूचीबद्ध करके ओवरराइड भी कर सकते हैं।",
  bv_lblDirection: "दिशा:",
  bv_selectDirection: "दिशा चुनें",
  bv_addRoom: "रूम जोड़ें (★ = महत्वपूर्ण)",
  bv_runScanPrefix: "चलाएँ",
  bv_runScanSuffix: "वास्तु स्कैन",
  bv_biz_shop: "दुकान",
  bv_biz_office: "कार्यालय",
  bv_biz_factory: "कारख़ाना",
  bv_dir_N: "उत्तर",
  bv_dir_NE: "ईशान",
  bv_dir_E: "पूर्व",
  bv_dir_SE: "आग्नेय",
  bv_dir_S: "दक्षिण",
  bv_dir_SW: "नैऋत्य",
  bv_dir_W: "पश्चिम",
  bv_dir_NW: "वायव्य",
  bv_room_entrance: "प्रवेश",
  bv_room_owner_seat: "स्वामी स्थान",
  bv_room_cash_counter: "गोलक",
  bv_room_billing_counter: "बिलिंग काउंटर",
  bv_room_vault: "तिजोरी",
  bv_room_stock_storage: "भंडार",
  bv_room_display: "प्रदर्शन क्षेत्र",
  bv_room_pooja: "मंदिर / पूजा",
  bv_room_back_office: "पीछे का कार्यालय",
  bv_room_staff_room: "स्टाफ रूम",
  bv_room_toilet: "शौचालय",
  bv_room_owner_cabin: "स्वामी केबिन",
  bv_room_reception: "स्वागत",
  bv_room_conference: "सम्मेलन",
  bv_room_accounts: "लेखा",
  bv_room_server_room: "सर्वर कक्ष",
  bv_room_pantry: "पेंट्री",
  bv_room_machinery: "यंत्र",
  bv_room_heavy_machine: "भारी यंत्र",
  bv_room_raw_storage: "कच्चा माल",
  bv_room_finished_goods: "तैयार माल",
  bv_room_boiler: "बॉयलर",
  bv_room_labour_quarter: "श्रमिक क्वार्टर",
  bv_errAuthRequired: "Business Vastu स्कैन चलाने के लिए कृपया लॉगिन करें।",
  bv_errValidationRooms: "कम से कम 2 रूम फोटो जोड़ें, या अपना पूरा शॉप फ़्लोर प्लान PDF अपलोड करें।",
  bv_btnUploadShopPdf: "पूरा शॉप PDF अपलोड",
  bv_btnUploadOfficePdf: "पूरा ऑफिस PDF अपलोड",
  bv_btnUploadOfficePhoto: "ऑफिस रूम फ़ोटो अपलोड",
  bv_btnUploadFactoryPdf: "पूरा फैक्टरी PDF अपलोड",
  bv_btnUploadFactoryPhoto: "फैक्टरी फ़ोटो अपलोड",
  bv_planNorthHint: "इस प्लान पर उत्तर (North) कहाँ है?",
  bv_secUploadedPhotos: "अपलोड की गई फ़ोटो",
  bv_btnSubmitReview: "Pay Now",
  bv_submitSuccessTitle: "एडमिन को भेज दिया",
  bv_submitSuccessBody: "हमारे वास्तु विशेषज्ञ आपकी फ़ोटो देखकर 24–48 घंटे में रिपोर्ट तैयार करेंगे।",
  bv_errValidationName: "अपने स्थल का नाम दें (जैसे 'अंधेरी दुकान') — अनलॉक मिलाने के लिए आवश्यक।",
  bv_errUnlockTitle: "अनलॉक आवश्यक",
  bv_errProfileTitle: "अपनी प्रोफ़ाइल पूरी करें",
  bv_errValidTitle: "अपने इनपुट जाँचें",
  bv_errScanFailed: "स्कैन विफल",
  bv_errTryAgain: "कृपया पुनः प्रयास करें।",
  bv_btnCompleteProfile: "प्रोफ़ाइल पूरी करें",
  bv_walletHintPrefix: "ऊपर वॉलेट से अनलॉक करें",
  bv_walletHintSuffix: "वास्तु (आजीवन)।",
  bv_overallScore: "समग्र स्थल अंक",
  bv_grade: "ग्रेड",
  bv_pdfReady: "विस्तृत PDF रिपोर्ट तैयार",
  bv_pdfBodyHi: "आपकी पूरी Business Vastu रिपोर्ट PDF में तैयार है — कमरा-दर-कमरा निर्णय, महादशा अलर्ट, हितधारक सामंजस्य, प्राथमिकता क्रियाएँ सब कुछ।",
  bv_pdfBodyEn: "आपकी पूरी Business Vastu रिपोर्ट PDF के रूप में उपलब्ध है — खोलें, सहेजें या साझा करें।",
  bv_btnOpenPdf: "PDF रिपोर्ट खोलें",
  bv_footerBrand: "Advanced Cosmic Intelligence द्वारा संचालित",
  bv_lblIdeal: "आदर्श",
  bv_lblAcceptable: "स्वीकार्य",
  bv_lblAdjust: "समायोजन",
  bv_lblAvoid: "टालें",
  bv_lblOwnerMd: "स्वामी महादशा",
  bv_lblStakeholder: "हितधारक सामंजस्य",
  bv_lblMuhuratAlign: "मुहूर्त संरेखण",
  bv_secPriority: "प्राथमिकता क्रियाएँ",
  bv_lblCritical: "★ महत्वपूर्ण",
  bv_secRoomByRoom: "कमरा-दर-कमरा",
  bv_lblZone: "क्षेत्र:",
  bv_secClassicalRefs: "शास्त्रीय संदर्भ",
  avp_headerTitle: "Home Vastu Premium",
  avp_heroTitle: "Home Vastu Premium",
  avp_heroBody: "क्या स्कैन करना है चुनें — एक रूम की फ़ोटो, या पूरे घर का फ़्लोर प्लान। कुंडली के अनुसार व्यक्तिगत वास्तु मार्गदर्शन और स्पष्ट next steps मिलेंगे।",
  avp_modeCameraTitle: "होम वास्तु",
  avp_modeCameraSub: "एक रूम (कैमरा)",
  avp_modeSingleTitle: "एक रूम",
  avp_modeSingleSub: "फ़ोटो / PDF",
  avp_modeWholeTitle: "Full Home Plan",
  avp_modeWholeSub: "पूरा घर (PDF/JPG)",
  avp_introCameraTitle: "होम वास्तु — लाइव कैमरा",
  avp_introCameraBody: "यह सिर्फ़ एक रूम के लिए है। रूम चुनें, कैमरा खोलें, उसी रूम के अंदर खड़े होकर फ़ोटो लें — शटर के समय कम्पास दिशा लॉक कर देता है।",
  avp_pickerLabel: "यह फ़ोटो किस रूम की है?",
  avp_pickerHint: "कैमरा सक्षम करने के लिए ऊपर रूम चुनें।",
  avp_camHintPrefix: "कैमरा + कम्पास · फ़ोटो ले रहे",
  avp_camHintNoRoom: "पहले रूम चुनें",
  avp_btnSmartScan: "कैमरा खोलें",
  avp_btnUploadPhoto: "रूम फ़ोटो अपलोड",
  avp_btnUploadHomePdf: "Full Home PDF अपलोड",
  avp_badgeSingleRoom: "एक रूम",
  avp_badgeWholeHome: "पूरा घर",
  avp_uploadPricePerRoom: "प्रति रूम",
  avp_uploadPaySubmit: "₹{amount} भुगतान करें",
  avp_uploadSubmitted: "हो गया! My Reports देखें।",
  avp_introSingleTitle: "एक रूम — फ़ोटो या PDF",
  avp_introSingleBody: "घर पर नहीं हैं? गैलरी से फ़ोटो या PDF चुनें और रूम + दिशा मैन्युअल रूप से टैग करें। तब सर्वोत्तम जब आप किसी एक विशिष्ट रूम की जाँच करना चाहते हैं।",
  avp_introWholeTitle: "Full Home Plan — Photo Engine",
  avp_introWholeBody: "पूरे घर का फ़्लोर प्लान (architect PDF/JPG) अपलोड करें। Photo Engine rooms detect करके कुंडली के अनुसार एक संकलित दिशा-वार रिपोर्ट बनाता है।",
  avp_btnRunWhole: "Full Home Scan चलाएँ",
  avp_btnAnalysing: "विश्लेषण हो रहा है…",
  avp_room_bedroom: "शयन कक्ष",
  avp_room_kitchen: "रसोई",
  avp_room_pooja: "पूजा",
  avp_room_living: "बैठक",
  avp_room_bathroom: "स्नानघर",
  avp_room_entrance: "प्रवेश",
  avp_room_study: "अध्ययन कक्ष",
  avp_room_store: "भंडार",
  avp_errAuthRequired: "Smart Scan चलाने के लिए कृपया लॉगिन करें।",
  avp_errMonthlyLimit: "मासिक सीमा पूरी",
  avp_errUpgradeReq: "अपग्रेड आवश्यक",
  avp_errProfile: "अपनी प्रोफ़ाइल पूरी करें",
  avp_errVisionNoRoom: "यह फ़ोटो पढ़ी नहीं जा सकी",
  avp_errScanFailed: "स्मार्ट स्कैन विफल",
  avp_errBodyDefault: "अपने फ़्लोर प्लान या पूरे रूम की स्पष्ट फ़ोटो आज़माएँ।",
  avp_btnCompleteProfile: "प्रोफ़ाइल पूरी करें",
  avp_btnUpgradePro: "Pro में अपग्रेड — असीमित",
  avp_overallScore: "समग्र घर अंक",
  avp_pdfReady: "विस्तृत PDF रिपोर्ट तैयार",
  avp_pdfBody: "आपकी पूरी AstroVastu PRO रिपोर्ट PDF में तैयार है — हर रूम का गहन निर्णय, महादशा परत, प्राथमिकता क्रियाएँ और शास्त्रीय संदर्भ।",
  avp_btnOpenPdf: "PDF रिपोर्ट खोलें",
  avp_footerBrand: "Advanced Cosmic Intelligence द्वारा संचालित",
  avp_secPriority: "प्राथमिकता क्रियाएँ",
  avp_secRoomByRoom: "कमरा-दर-कमरा विवरण",
  avp_lblMdAlert: "महादशा अलर्ट",
  avp_quotaUnlimited: "असीमित PRO स्कैन (Pro योजना)",
  avp_quotaPrefix: "स्कैन",
  avp_quotaThisMonth: "इस माह",
  avp_brandFooter: "✨ Advanced Cosmic Intelligence द्वारा संचालित",
  avp_brandFooterSub: "Cosmic AstroVastu Drishti — PRO Engine v1.0",
  avp_lblIdeal: "आदर्श",
  avp_lblAcceptable: "स्वीकार्य",
  avp_lblAdjust: "समायोजन",
  avp_lblAvoid: "टालें",
  avr_emptyTitle: "कोई रिपोर्ट लोड नहीं हुई",
  avr_emptyBody: "यहाँ परिणाम देखने के लिए पहले Smart Scan चलाएँ।",
  avr_btnOpenPro: "AstroVastu PRO खोलें",
  avr_headerTitle: "आपकी AstroVastu रिपोर्ट",
  avr_outOf100: "100 में से",
  avr_grade: "ग्रेड",
  avr_btnOpenPdf: "PDF खोलें",
  avr_btnWhatsApp: "WhatsApp",
  avr_secPriorityHi: "सबसे पहले ये 3 चीज़ें ठीक करें",
  avr_secRoomByRoom: "कमरा-दर-कमरा",
  avr_brandFooter: "✨ Advanced Cosmic Intelligence द्वारा संचालित",
  avr_shareTitle: "🪔 *AstroVastu PRO रिपोर्ट*",
  avr_shareScoreLbl: "📊 अंक:",
  avr_shareOpenLbl: "📄 रिपोर्ट खोलें:",
  avr_shareBrandLbl: "_Advanced Cosmic Intelligence द्वारा संचालित_",
  avr_alertShareErr: "साझा नहीं हो सका",

  // Risk Radar — Lucky / Best-Avoid Time card
  rrLuckyAajShubhAnk:        "आज का शुभ अंक",
  rrLuckyAajShubhRang:       "आज का शुभ रंग",
  rrLuckyShubhAnk:           "शुभ अंक",
  rrLuckyShubhRang:          "शुभ रंग",
  rrLuckyBestTime:           "⏰ शुभ समय",
  rrLuckyAvoidTime:          "🚫 अशुभ समय",
  rrLuckyPoweredBy:          "✨ Advanced Cosmic Intelligence द्वारा संचालित",
  rrLuckyHeaderToday:        "आज का शुभ अंक + रंग",
  rrLuckyHeaderOther:        "शुभ अंक + रंग",
  rrLuckyCalculating:        "आपका शुभ अंक और रंग गणना हो रही है…",
  rrLuckyCreateKundliPrompt: "अपनी कुंडली बनाएँ — जन्म नक्षत्र से आज का व्यक्तिगत शुभ अंक और रंग देखें।",
  rrLuckyCreateKundliCta:    "कुंडली बनाएँ →",
  rrLuckyDetailsUnavail:     "शुभ विवरण अभी उपलब्ध नहीं हैं।",
  rrLuckyDayUnavail:         "इस दिन के लिए शुभ अंक और रंग अभी उपलब्ध नहीं हैं।",

  // Forecast — Lucky highlights card (Hindi)
  fc_luckyBestTimeLabel:     "शुभ समय",
  fc_luckyAvoidTimeLabel:    "अशुभ समय",
  fc_luckyReason:            "{date} को — शुभ अंक {n} और {colour} रंग आज की कॉस्मिक ऊर्जा के साथ संरेखित हैं।",
  fc_luckyClrHara:           "हरा",
  fc_luckyClrPila:           "पीला",
  fc_luckyClrSafed:          "सफेद",
  fc_luckyClrNeela:          "नीला",
  fc_luckyClrSuneheri:       "सुनहरा",
  fc_luckyClrKesari:         "केसरी",

  // Risk Radar — 24-hour breakdown labels (HI)
  rrSection24hToday:          "आज के 24 घंटे",
  rrSection24hWithDate:       "{date} के 24 घंटे",
  rrLabelKyaRisk:             "क्या जोखिम है",
  rrLabelKyaAvoid:            "क्या टालना है",
  rrLabelKyaKarna:            "क्या करना है",
  rrLabelUpay:                "उपाय",
  rrLevelLow:                 "कम",
  rrLevelMed:                 "मध्यम",
  rrLevelHigh:                "उच्च",
  rrLabelRiskLevel:           "जोखिम स्तर",
  radarHeaderSub:             "अगले 7 दिनों का कॉस्मिक रडार",
  radarLoadingTxt:            "आपका रडार तैयार हो रहा है…",
  radarEmptyTitle:            "रडार लोड नहीं हो सका",
  radarEmptyBody:             "इंटरनेट जाँचें या थोड़ी देर बाद फिर से कोशिश करें।",
  radarPickerLabel:           "अपना दिन चुनें",
  radarDayToday:              "आज",
  radarDayTomorrow:           "कल",
  radarTotalLabel:            "कुल जोखिम संकेत",
  radarBadgeHigh:             "उच्च चेतावनी",
  radarBadgeMed:              "उन्नत",
  radarBadgeLow:              "स्थिर",
  radarSubToday:              "अगले 24 घंटों में सक्रिय खतरा संकेत",
  radarSubOther:              "{date} के 24 घंटों में सक्रिय संकेत",
  radarStatusActive:          "खतरा स्कैन सक्रिय",
  radarSignalSingular:        "संकेत",
  radarSignalPlural:          "संकेत",
  radarAllClear:              "सब सुरक्षित",
  radarAllClearSub:           "आज कोई बड़ा संकेत नहीं",
  radarTitle:                 "जोखिम रडार",
  rrCardTitle:                "कॉस्मिक जोखिम रडार",
  rrSafestChip:               "सबसे सुरक्षित",
  rrChallengingChip:          "चुनौतीपूर्ण",
  rrDayOf7:                   "दिन {n} / ७",
  rrLockedTitle:              "{date} का रडार लॉक",
  rrLockedSub:                "आने वाले दिनों का पूरा रडार — जोखिम स्तर, क्या करना/टालना, शुभ अंक, शुभ समय और उपाय — प्रीमियम से अनलॉक करें।",
  rrLockedHint:               "💡 दिन १ मुफ़्त — पूर्वावलोकन के लिए टैप करें",
  rrLockedCta:                "प्रीमियम अनलॉक करें",
  rrScoreUp:                  "आज सकारात्मक ऊर्जा भरी है। नए कार्य शुरू करने का अच्छा दिन।",
  rrScoreMixed:               "मिश्रित दिन — कुछ अवसर, कुछ बातें सावधानी से।",
  rrScoreDown:                "आज थोड़ी चुनौतीपूर्ण ऊर्जा। धैर्य रखें, प्रतिक्रियाशील न हों।",
  rrDotPrimary:               "प्राथमिक",
  rrDotSecondary:             "द्वितीयक",
  rrDotWatch:                 "निगरानी",
  rrDotStable:                "स्थिर",
  rrDotRoutine:               "नियमित जाँच",
  pn_vivahBlockedChaturmas: "चातुर्मास (जुलाई–अक्टूबर) — शास्त्रीय विवाह वर्जित। सूर्य कर्क–तुला में; वृश्चिक (~नवंबर) के बाद पुनः शुरू।",
  pn_vivahBlockedMeena:     "मीन मास (फ़रवरी–मार्च) — शास्त्रीय विवाह बंद।",
};


// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────






















// ── Auto-generated translations (21 langs) ──────────────────────























/** Get additional strings — English, Hinglish, Hindi only. */
export function getTM(lang: string): MoreT {
  const c = (lang || "en").trim().toLowerCase();
  const bucket =
    c === "hn" || c === "hinglish" ? "hn" :
    c === "hi" || c === "hindi" ? "hi" :
    "en";
  switch (bucket) {
    case "hn": return { ...EN, ...HN };
    case "hi": return { ...EN, ...HI };
    default:   return EN;
  }
}
