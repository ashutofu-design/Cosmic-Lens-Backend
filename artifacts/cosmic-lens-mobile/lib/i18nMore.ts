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

  nm_proTools:        "PRO+ TOOLS",
  nm_premium:         "PREMIUM",
  nm_lifeMastery:     "Life Mastery Report",
  nm_yourNumbers:     "YOUR NUMBERS",
  nm_yourNumbersHint: "(at least one)",
  nm_whatsInside:     "WHAT'S INSIDE",
  nm_opening:         "Opening…",
  nm_generateBtn:     "Generate Life Mastery Report",

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
  fc_moonRashi:         "Moon Rashi",
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

  nm_proTools:        "PRO+ TOOLS",
  nm_premium:         "PREMIUM",
  nm_lifeMastery:     "Life Mastery Report",
  nm_yourNumbers:     "AAPKE NUMBERS",
  nm_yourNumbersHint: "(kam se kam ek)",
  nm_whatsInside:     "ANDAR KYA HAI",
  nm_opening:         "Khol raha…",
  nm_generateBtn:     "Life Mastery Report Generate Karein",

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
  fc_moonRashi:         "Moon Rashi",
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
  nm_lifeMastery:     "जीवन महारत रिपोर्ट",
  nm_yourNumbers:     "आपके अंक",
  nm_yourNumbersHint: "(कम से कम एक)",
  nm_whatsInside:     "अंदर क्या है",
  nm_opening:         "खुल रहा…",
  nm_generateBtn:     "जीवन महारत रिपोर्ट बनाएँ",

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
  fc_moonRashi:         "चंद्र राशि",
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
