// ══════════════════════════════════════════════════════════════════════════════
// INSIGHT LANGUAGE PACKS — Full 7-language support for generated insight text
// ══════════════════════════════════════════════════════════════════════════════

export type LangCode = "hi" | "ta" | "te" | "bn" | "mr" | "gu" | "kn" | "en";

const fill = (tpl: string, v: Record<string, string>) =>
  tpl.replace(/\{(\w+)\}/g, (_, k) => v[k] ?? k);

// ── Sign names ────────────────────────────────────────────────────────────────
export const SIGNS: Record<LangCode, string[]> = {
  hi: ["मेष","वृषभ","मिथुन","कर्क","सिंह","कन्या","तुला","वृश्चिक","धनु","मकर","कुंभ","मीन"],
  ta: ["மேஷம்","ரிஷபம்","மிதுனம்","கடகம்","சிம்மம்","கன்னி","துலாம்","விருச்சிகம்","தனுசு","மகரம்","கும்பம்","மீனம்"],
  te: ["మేషం","వృషభం","మిథునం","కర్కాటకం","సింహం","కన్య","తుల","వృశ్చికం","ధనుసు","మకరం","కుంభం","మీనం"],
  bn: ["মেষ","বৃষ","মিথুন","কর্কট","সিংহ","কন্যা","তুলা","বৃশ্চিক","ধনু","মকর","কুম্ভ","মীন"],
  mr: ["मेष","वृषभ","मिथुन","कर्क","सिंह","कन्या","तुला","वृश्चिक","धनु","मकर","कुंभ","मीन"],
  gu: ["મેષ","વૃષભ","મિથુન","કર્ક","સિંહ","કન્યા","તુલા","વૃશ્ચિક","ધનુ","મકર","કુંભ","મીન"],
  kn: ["ಮೇಷ","ವೃಷಭ","ಮಿಥುನ","ಕರ್ಕ","ಸಿಂಹ","ಕನ್ಯಾ","ತುಲಾ","ವೃಶ್ಚಿಕ","ಧನು","ಮಕರ","ಕುಂಭ","ಮೀನ"],
  en: ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"],
};

// ── House ordinals (index 0 unused, 1-12 used) ────────────────────────────────
export const ORDINALS: Record<LangCode, string[]> = {
  hi: ["","पहले","दूसरे","तीसरे","चौथे","पाँचवें","छठे","सातवें","आठवें","नौवें","दसवें","ग्यारहवें","बारहवें"],
  ta: ["","1வது","2வது","3வது","4வது","5வது","6வது","7வது","8வது","9வது","10வது","11வது","12வது"],
  te: ["","1వ","2వ","3వ","4వ","5వ","6వ","7వ","8వ","9వ","10వ","11వ","12వ"],
  bn: ["","১ম","২য়","৩য়","৪র্থ","৫ম","৬ষ্ঠ","৭ম","৮ম","৯ম","১০ম","১১তম","১২তম"],
  mr: ["","पहिल्या","दुसऱ्या","तिसऱ्या","चौथ्या","पाचव्या","सहाव्या","सातव्या","आठव्या","नवव्या","दहाव्या","अकराव्या","बाराव्या"],
  gu: ["","1લા","2જા","3જા","4થા","5મા","6ઠ્ઠા","7મા","8મા","9મા","10મા","11મા","12મા"],
  kn: ["","1ನೇ","2ನೇ","3ನೇ","4ನೇ","5ನೇ","6ನೇ","7ನೇ","8ನೇ","9ನೇ","10ನೇ","11ನೇ","12ನೇ"],
  en: ["","1st","2nd","3rd","4th","5th","6th","7th","8th","9th","10th","11th","12th"],
};

// ── Planet names ──────────────────────────────────────────────────────────────
export const PLANET_NAMES: Record<LangCode, Record<string, string>> = {
  hi: { Sun:"सूर्य", Moon:"चंद्र", Mars:"मंगल", Mercury:"बुध", Jupiter:"गुरु", Venus:"शुक्र", Saturn:"शनि", Rahu:"राहु", Ketu:"केतु" },
  ta: { Sun:"சூரியன்", Moon:"சந்திரன்", Mars:"செவ்வாய்", Mercury:"புதன்", Jupiter:"குரு", Venus:"சுக்கிரன்", Saturn:"சனி", Rahu:"ராகு", Ketu:"கேது" },
  te: { Sun:"సూర్యుడు", Moon:"చంద్రుడు", Mars:"కుజుడు", Mercury:"బుధుడు", Jupiter:"గురువు", Venus:"శుక్రుడు", Saturn:"శని", Rahu:"రాహువు", Ketu:"కేతువు" },
  bn: { Sun:"সূর্য", Moon:"চন্দ্র", Mars:"মঙ্গল", Mercury:"বুধ", Jupiter:"বৃহস্পতি", Venus:"শুক্র", Saturn:"শনি", Rahu:"রাহু", Ketu:"কেতু" },
  mr: { Sun:"सूर्य", Moon:"चंद्र", Mars:"मंगळ", Mercury:"बुध", Jupiter:"गुरू", Venus:"शुक्र", Saturn:"शनी", Rahu:"राहू", Ketu:"केतू" },
  gu: { Sun:"સૂર્ય", Moon:"ચંદ્ર", Mars:"મંગળ", Mercury:"બુધ", Jupiter:"ગુરુ", Venus:"શુક્ર", Saturn:"શનિ", Rahu:"રાહુ", Ketu:"કેતુ" },
  kn: { Sun:"ಸೂರ್ಯ", Moon:"ಚಂದ್ರ", Mars:"ಮಂಗಳ", Mercury:"ಬುಧ", Jupiter:"ಗುರು", Venus:"ಶುಕ್ರ", Saturn:"ಶನಿ", Rahu:"ರಾಹು", Ketu:"ಕೇತು" },
  en: { Sun:"Sun", Moon:"Moon", Mars:"Mars", Mercury:"Mercury", Jupiter:"Jupiter", Venus:"Venus", Saturn:"Saturn", Rahu:"Rahu", Ketu:"Ketu" },
};

export function pName(lang: LangCode, planet: string): string {
  return PLANET_NAMES[lang]?.[planet] ?? planet;
}

// ── Domain keywords ───────────────────────────────────────────────────────────
export const DOMAIN_KW: Record<LangCode, Record<string, string>> = {
  hi: { career:"करियर", finance:"आर्थिक स्थिति", relationship:"रिश्ते", health:"स्वास्थ्य" },
  ta: { career:"தொழில்", finance:"நிதி நிலை", relationship:"உறவு", health:"ஆரோக்கியம்" },
  te: { career:"వృత్తి", finance:"ఆర్థిక స్థితి", relationship:"సంబంధాలు", health:"ఆరోగ్యం" },
  bn: { career:"ক্যারিয়ার", finance:"আর্থিক অবস্থা", relationship:"সম্পর্ক", health:"স্বাস্থ্য" },
  mr: { career:"करिअर", finance:"आर्थिक स्थिती", relationship:"नाते", health:"आरोग्य" },
  gu: { career:"કારકિર્દી", finance:"આર્થિક સ્થિતિ", relationship:"સંબંધ", health:"આરોગ્ય" },
  kn: { career:"ವೃತ್ತಿ", finance:"ಆರ್ಥಿಕ ಸ್ಥಿತಿ", relationship:"ಸಂಬಂಧ", health:"ಆರೋಗ್ಯ" },
  en: { career:"career", finance:"finances", relationship:"relationships", health:"health" },
};

// ── Dignity labels ────────────────────────────────────────────────────────────
const DIGNITY: Record<LangCode, Record<string, string>> = {
  hi: { exalted:"उच्च", debil:"नीच", own:"स्वराशि में", friendly:"मित्र राशि में", enemy:"शत्रु राशि में", neutral:"सम राशि में" },
  ta: { exalted:"உச்சம்", debil:"நீசம்", own:"சொந்த வீட்டில்", friendly:"நட்பு வீட்டில்", enemy:"பகை வீட்டில்", neutral:"நடுநிலையில்" },
  te: { exalted:"ఉచ్చ స్థితిలో", debil:"నీచ స్థితిలో", own:"స్వక్షేత్రంలో", friendly:"మిత్రక్షేత్రంలో", enemy:"శత్రుక్షేత్రంలో", neutral:"సమ స్థితిలో" },
  bn: { exalted:"উচ্চ", debil:"নীচ", own:"স্বরাশিতে", friendly:"মিত্ররাশিতে", enemy:"শত্রুরাশিতে", neutral:"সমরাশিতে" },
  mr: { exalted:"उच्च", debil:"नीच", own:"स्वराशीत", friendly:"मित्र राशीत", enemy:"शत्रू राशीत", neutral:"सम राशीत" },
  gu: { exalted:"ઉચ્ચ", debil:"નીચ", own:"સ્વ-રાશિ", friendly:"મિત્ર-રાશિ", enemy:"શત્રુ-રાશિ", neutral:"સમ-રાશિ" },
  kn: { exalted:"ಉಚ್ಚ", debil:"ನೀಚ", own:"ಸ್ವ-ರಾಶಿಯಲ್ಲಿ", friendly:"ಮಿತ್ರ ರಾಶಿಯಲ್ಲಿ", enemy:"ಶತ್ರು ರಾಶಿಯಲ್ಲಿ", neutral:"ಸಮ ರಾಶಿಯಲ್ಲಿ" },
  en: { exalted:"exalted", debil:"debilitated", own:"in own sign", friendly:"in a friendly sign", enemy:"in an enemy sign", neutral:"in a neutral sign" },
};

function dignityLabel(
  lang: LangCode, planet: string, signIdx: number,
  exalt: Record<string,number>, debil: Record<string,number>,
  own: Record<string,number[]>, lords: string[],
  friends: Record<string,string[]>, enemies: Record<string,string[]>,
): string {
  const d = DIGNITY[lang];
  if (exalt[planet] === signIdx) return d.exalted;
  if (debil[planet] === signIdx) return d.debil;
  if ((own[planet] ?? []).includes(signIdx)) return d.own;
  const lord = lords[signIdx];
  if ((friends[planet] ?? []).includes(lord)) return d.friendly;
  if ((enemies[planet] ?? []).includes(lord)) return d.enemy;
  return d.neutral;
}

// ── House type labels ─────────────────────────────────────────────────────────
const HOUSE_TYPES: Record<LangCode, Record<string,string>> = {
  hi: { angular:"केंद्र भाव", trikona:"त्रिकोण भाव", dusthana:"दुस्थान भाव", neutral:"सामान्य भाव" },
  ta: { angular:"கேந்திர வீடு", trikona:"திரிகோண வீடு", dusthana:"துஸ்தான வீடு", neutral:"சாதாரண வீடு" },
  te: { angular:"కేంద్ర స్థానం", trikona:"త్రికోణ స్థానం", dusthana:"దుస్థాన స్థానం", neutral:"సాధారణ స్థానం" },
  bn: { angular:"কেন্দ্র ভাব", trikona:"ত্রিকোণ ভাব", dusthana:"দুস্থান ভাব", neutral:"সাধারণ ভাব" },
  mr: { angular:"केंद्र भाव", trikona:"त्रिकोण भाव", dusthana:"दुस्थान भाव", neutral:"सामान्य भाव" },
  gu: { angular:"કેન્દ્ર ભાવ", trikona:"ત્રિકોણ ભાવ", dusthana:"દૂષ્ઠ ભાવ", neutral:"સામાન્ય ભાવ" },
  kn: { angular:"ಕೇಂದ್ರ ಭಾವ", trikona:"ತ್ರಿಕೋಣ ಭಾವ", dusthana:"ದುಸ್ಥಾನ ಭಾವ", neutral:"ಸಾಮಾನ್ಯ ಭಾವ" },
  en: { angular:"angular/kendra", trikona:"auspicious/trikona", dusthana:"challenging/dusthana", neutral:"neutral" },
};

function houseTypeLabel(lang: LangCode, h: number): string {
  const t = HOUSE_TYPES[lang];
  if ([1,4,7,10].includes(h)) return t.angular;
  if ([5,9].includes(h))      return t.trikona;
  if ([6,8,12].includes(h))   return t.dusthana;
  return t.neutral;
}

// ── Text templates ────────────────────────────────────────────────────────────
interface LangTemplates {
  placement:          string;
  retrograde:         string;
  noAspects:          string;
  beneficOnly:        string;
  maleficOnly:        string;
  bothAspects:        string;
  adStrong:           string;
  adModerate:         string;
  adWeak:             string;
  adVeryWeak:         string;
  conclusionGood:     string;
  conclusionMixed:    string;
  conclusionBad:      string;
  cautionDusthana:    string;
  cautionDebil:       string;
  cautionMalAspect:   string;
  cautionNone:        string;
  adCautionDusthana:  string;
  adCautionWeak:      string;
  behaviourCareer:    string;
  behaviourFinance:   string;
  behaviourRel:       string;
  behaviourHealth:    string;
  categoryGood:       string;
  categoryMixed:      string;
  categoryBad:        string;
  remedies:           Record<string, string>;
  practicals:         Record<string, string>;
}

const TEMPLATES: Record<LangCode, LangTemplates> = {

  hi: {
    placement:       "{planet} आपकी कुंडली में {ordinal} भाव में {sign} राशि में {dignity} स्थित हैं ({houseType})।",
    retrograde:      " इस समय {planet} वक्री चल रहे हैं।",
    noAspects:       "{planet} पर इस समय कोई बड़ी ग्रह दृष्टि नहीं है — फल मुख्यतः उनकी अपनी शक्ति से आएगा।",
    beneficOnly:     "{benefics} की शुभ दृष्टि {planet} को सहयोग दे रही है।",
    maleficOnly:     "{malefics} की अशुभ दृष्टि {planet} पर पड़ रही है, जिससे कुछ चुनौतियाँ आ सकती हैं।",
    bothAspects:     "{benefics} की शुभ दृष्टि {planet} को सहयोग दे रही है, साथ ही {malefics} की अशुभ दृष्टि भी पड़ रही है। इनका प्रभाव इस अवधि के परिणामों पर पड़ेगा।",
    adStrong:        "{adPlanet} अंतर्दशा मजबूत स्थिति में है — अतिरिक्त सहयोग मिल रहा है।",
    adModerate:      "{adPlanet} अंतर्दशा सामान्य स्थिति में है।",
    adWeak:          "{adPlanet} अंतर्दशा कुछ कठिन स्थिति में है — इसका भी असर पड़ेगा।",
    adVeryWeak:      "{adPlanet} अंतर्दशा काफी दबाव में है, जो इस अवधि की समग्र शक्ति कम कर रहा है।",
    conclusionGood:  "कुल मिलाकर {domain} के लिए यह अवधि अनुकूल है। निरंतर प्रयास से अच्छे परिणाम मिलने की संभावना है।",
    conclusionMixed: "यह एक मिश्रित चरण है — {domain} में कुछ लाभ और कुछ चुनौतियाँ दोनों आ सकती हैं। एक-एक कदम आगे बढ़ें।",
    conclusionBad:   "इस अवधि में {domain} में उल्लेखनीय चुनौतियाँ हैं। धैर्य और यथार्थवादी अपेक्षाओं से {planet} की दशा को अच्छे से पार किया जा सकता है।",
    cautionDusthana: "{planet} आपके {ordinal} भाव (दुस्थान) में {sign} में हैं — {domain} में परिणामों के लिए अतिरिक्त धैर्य और प्रयास जरूरी होगा।",
    cautionDebil:    "{planet} इस समय {sign} में नीच अवस्था में हैं — इस अवधि में उनकी स्वाभाविक क्षमता कुछ सीमित रहेगी।",
    cautionMalAspect:"{malefics} की सीधी दृष्टि {planet} पर है — {domain} में अप्रत्याशित बाधाएँ आ सकती हैं।",
    cautionNone:     "{planet} की वर्तमान स्थिति में कोई बड़ी कमजोरी नहीं है, पर आवेगपूर्ण निर्णयों से बचें।",
    adCautionDusthana:" {adPlanet} अंतर्दशा भी {ordinal} भाव में है — दोहरा दबाव हो सकता है, इसलिए सोच-समझकर कदम उठाएं।",
    adCautionWeak:   " {adPlanet} की अंतर्दशा भी कमजोर स्थिति में है — हर बड़े निर्णय पर ध्यानपूर्वक विचार करें।",
    behaviourCareer: " कार्यस्थल के विवादों और राजनीति से दूर रहें। अपने काम पर ध्यान केंद्रित रखें।",
    behaviourFinance:" बड़े वित्तीय निर्णयों में हमेशा दूसरी राय लें। FOMO से प्रेरित निवेश से बचें।",
    behaviourRel:    " अनुमान न लगाएं — जो मन में है, सीधे कहें। अनियंत्रित भावनाएं रिश्तों को नुकसान पहुँचाती हैं।",
    behaviourHealth: " शरीर के शुरुआती संकेतों को अनदेखा न करें। अत्यधिक परिश्रम और अनियमित दिनचर्या से सख्त परहेज करें।",
    categoryGood:    "{pdPlanet}–{adPlanet} चरण {domain} के लिए अनुकूल है। निरंतर प्रयास से अच्छे परिणाम मिलेंगे।",
    categoryMixed:   "{pdPlanet}–{adPlanet} चरण {domain} में मिश्रित परिणाम दे रहा है। केंद्रित रहने से सुधार हो सकता है।",
    categoryBad:     "{pdPlanet}–{adPlanet} चरण {domain} में चुनौतियाँ ला रहा है। धैर्य और यथार्थवादी दृष्टिकोण जरूरी है।",
    remedies: {
      Sun:     "सूर्योदय के समय उगते सूरज को जल चढ़ाएं। 'ॐ सूर्याय नमः' का नित्य जप करें। रविवार को तांबा या नारंगी रंग पहनें।",
      Moon:    "जल के पास या चाँदनी में ध्यान करें। 'ॐ सोम सोमाय नमः' का जप करें। सोमवार को सफेद पहनें।",
      Mars:    "अनुशासित शारीरिक अभ्यास में ऊर्जा लगाएं। नियमित हनुमान चालीसा पढ़ें। मंगलवार को लाल रंग पहनें।",
      Mercury: "अपने विचार लिखें। 'ॐ बुधाय नमः' का जप करें। बुधवार को हरा पहनें।",
      Jupiter: "रोज शास्त्र या दार्शनिक ग्रंथ पढ़ें। 'ॐ गुरवे नमः' का जप करें। गुरुवार को पीला पहनें। कृतज्ञता का अभ्यास करें।",
      Venus:   "रचनात्मक अभिव्यक्ति और आत्म-देखभाल में निवेश करें। 'ॐ शुक्राय नमः' का जप करें। शुक्रवार को सफेद या गुलाबी पहनें।",
      Saturn:  "दैनिक अनुशासन के प्रति प्रतिबद्ध रहें। 'ॐ शनैश्चराय नमः' का जप करें। जरूरतमंदों की सेवा करें। शनिवार को नीला पहनें।",
      Rahu:    "रोज ग्राउंडिंग करें — नंगे पैर चलना, गहरी सांस। 'ॐ राहवे नमः' का जप करें। अनिश्चितता को स्वीकार करें।",
      Ketu:    "ध्यान का अभ्यास गहरा करें। 'ॐ केतवे नमः' का जप करें। केतु आंतरिक आध्यात्मिक कार्य का पक्षधर है।",
    },
    practicals: {
      career:       "इस अवधि के लिए एक स्पष्ट करियर लक्ष्य निर्धारित करें और निरंतर दैनिक प्रयास से उसे पूरा करें।",
      finance:      "अभी रूढ़िवादी वित्तीय योजना सबसे अच्छी है। मासिक बजट बनाएं और आपातकालीन निधि रखें।",
      relationship: "सक्रिय श्रवण और खुला, सीधा संवाद रिश्तों को मजबूत करता है। अनुमान लगाने से बचें।",
      health:       "नियमित दिनचर्या — गुणवत्तापूर्ण नींद, संतुलित आहार और दैनिक व्यायाम — को प्राथमिकता दें।",
    },
  },

  ta: {
    placement:       "{planet} உங்கள் ஜாதகத்தில் {ordinal} வீட்டில் {sign} ராசியில் {dignity} உள்ளனர் ({houseType}).",
    retrograde:      " தற்போது {planet} வக்கிரகதியில் உள்ளனர்.",
    noAspects:       "{planet} மீது இப்போது எந்த முக்கிய கிரக பார்வையும் இல்லை — பலன்கள் அவர்களின் சொந்த வலிமையில் தங்கியுள்ளன.",
    beneficOnly:     "{benefics} {planet} மீது சுப பார்வை வைக்கிறார்கள், ஆதரவு கிடைக்கிறது.",
    maleficOnly:     "{malefics} {planet} மீது அசுப பார்வை வைக்கிறார்கள், சில இடர்கள் வரலாம்.",
    bothAspects:     "{benefics} {planet} மீது சுப பார்வை தருகிறார்கள், அதேநேரம் {malefics} அசுப பார்வை வைக்கிறார்கள். இந்த கிரக தாக்கங்கள் இக்காலத்தின் பலன்களை நிர்ணயிக்கும்.",
    adStrong:        "{adPlanet} அந்தர்தசை வலிமையான நிலையில் உள்ளது — கூடுதல் ஆதரவு கிடைக்கிறது.",
    adModerate:      "{adPlanet} அந்தர்தசை சராசரி நிலையில் உள்ளது.",
    adWeak:          "{adPlanet} அந்தர்தசை சிறிது சவாலான நிலையில் உள்ளது — இதன் தாக்கமும் இருக்கும்.",
    adVeryWeak:      "{adPlanet} அந்தர்தசை கடுமையான அழுத்தத்தில் உள்ளது, இக்காலத்தின் மொத்த வலிமையை குறைக்கிறது.",
    conclusionGood:  "மொத்தத்தில் {domain} க்கு இக்காலம் சாதகமானது. தொடர்ந்த முயற்சியால் நல்ல பலன்கள் கிடைக்கலாம்.",
    conclusionMixed: "இது கலவையான நிலை — {domain} ல் சில ஆதாயங்களும் சில சவால்களும் இருக்கும். ஒவ்வொரு அடியாக முன்னேறுங்கள்.",
    conclusionBad:   "இக்காலம் உங்கள் {domain} க்கு குறிப்பிடத்தக்க சவால்களை தருகிறது. பொறுமையும் யதார்த்தமான எதிர்பார்ப்பும் {planet} தசையை கடக்க உதவும்.",
    cautionDusthana: "{planet} உங்கள் {ordinal} வீட்டில் (துஸ்தானம்) {sign} ல் உள்ளனர் — {domain} ல் பலன்களுக்கு கூடுதல் பொறுமையும் முயற்சியும் தேவை.",
    cautionDebil:    "{planet} தற்போது {sign} ல் நீசமாக உள்ளனர் — இக்காலத்தில் இயற்கை திறன் சற்று குறையும்.",
    cautionMalAspect:"{malefics} {planet} மீது நேரடி பார்வை வைக்கிறார்கள் — {domain} ல் எதிர்பாராத தடைகள் வரலாம்.",
    cautionNone:     "{planet} இன் தற்போதைய நிலையில் பெரிய பலவீனம் இல்லை, ஆனால் உந்துதலான முடிவுகளை தவிர்க்கவும்.",
    adCautionDusthana:" {adPlanet} அந்தர்தசையும் {ordinal} வீட்டில் உள்ளது — இரட்டை அழுத்தம் இருக்கலாம், கவனமாக அடியெடுத்து வையுங்கள்.",
    adCautionWeak:   " {adPlanet} அந்தர்தசையும் பலவீனமான நிலையில் உள்ளது — ஒவ்வொரு முக்கிய முடிவையும் கவனமாக யோசியுங்கள்.",
    behaviourCareer: " பணியிட சர்ச்சைகளிலிருந்து விலகி இருங்கள். உங்கள் வேலையில் கவனம் செலுத்துங்கள்.",
    behaviourFinance:" பெரிய நிதி முடிவுகளில் எப்போதும் இரண்டாவது கருத்து பெறுங்கள். FOMO-வால் தூண்டப்படும் முதலீடுகளை தவிர்க்கவும்.",
    behaviourRel:    " அனுமானிக்காதீர்கள் — மனதில் இருப்பதை நேரடியாக சொல்லுங்கள். கட்டுப்படுத்தப்படாத உணர்வுகள் உறவுகளை பாதிக்கும்.",
    behaviourHealth: " உடலின் ஆரம்ப எச்சரிக்கை சமிக்ஞைகளை புறக்கணிக்காதீர்கள். அதிக உழைப்பு மற்றும் ஒழுங்கற்ற வழக்கத்தை கட்டாயம் தவிர்க்கவும்.",
    categoryGood:    "{pdPlanet}–{adPlanet} தசை {domain} க்கு சாதகமானது. தொடர் முயற்சியால் நல்ல பலன் கிடைக்கும்.",
    categoryMixed:   "{pdPlanet}–{adPlanet} தசை {domain} ல் கலவையான பலன் தருகிறது. கவனமாக முன்னேறுங்கள்.",
    categoryBad:     "{pdPlanet}–{adPlanet} தசை {domain} ல் சவால்களை தருகிறது. பொறுமையும் யதார்த்தமான அணுகுமுறையும் அவசியம்.",
    remedies: {
      Sun:     "அதிகாலையில் உதிக்கும் சூரியனுக்கு நீர் அர்ப்பணியுங்கள். தினமும் 'ஓம் சூர்யாய நம:' என்று ஜபியுங்கள். ஞாயிற்றுக்கிழமை செம்பு அல்லது ஆரஞ்சு நிறம் அணியுங்கள்.",
      Moon:    "நீர் அருகே அல்லது நிலாவொளியில் தியானியுங்கள். 'ஓம் சோம் சோமாய நம:' ஜபியுங்கள். திங்கட்கிழமை வெள்ளை அணியுங்கள்.",
      Mars:    "ஒழுக்கமான உடற்பயிற்சியில் ஆற்றலை செலுத்துங்கள். அஞ்சனேய சாலிசா தொடர்ந்து படியுங்கள். செவ்வாய்க்கிழமை சிவப்பு அணியுங்கள்.",
      Mercury: "உங்கள் எண்ணங்களை எழுதுங்கள். 'ஓம் புதாய நம:' ஜபியுங்கள். புதன்கிழமை பச்சை அணியுங்கள்.",
      Jupiter: "தினமும் சாஸ்திர நூல்களை படியுங்கள். 'ஓம் குரவே நம:' ஜபியுங்கள். வியாழக்கிழமை மஞ்சள் அணியுங்கள். நன்றியை கடைப்பிடியுங்கள்.",
      Venus:   "ஆக்கப்பூர்வமான வெளிப்பாட்டிலும் சுய-பராமரிப்பிலும் முதலிடுங்கள். 'ஓம் சுக்ராய நம:' ஜபியுங்கள். வெள்ளிக்கிழமை வெண்மை அல்லது இளஞ்சிவப்பு அணியுங்கள்.",
      Saturn:  "தினசரி ஒழுக்கத்தில் உறுதிப்படுங்கள். 'ஓம் சனைஸ்சராய நம:' ஜபியுங்கள். தேவைப்படுவோருக்கு சேவை செய்யுங்கள். சனிக்கிழமை நீலம் அணியுங்கள்.",
      Rahu:    "தினமும் நிலைப்படுத்துதல் பயிற்சி செய்யுங்கள். 'ஓம் ராஹவே நம:' ஜபியுங்கள். நிச்சயமற்ற தன்மையை ஏற்றுக்கொள்ளுங்கள்.",
      Ketu:    "உங்கள் தியான பயிற்சியை ஆழப்படுத்துங்கள். 'ஓம் கேதவே நம:' ஜபியுங்கள். கேது உள்ளான ஆன்மீக வேலையை விரும்புகிறது.",
    },
    practicals: {
      career:       "இக்காலத்திற்கு ஒரு தெளிவான தொழில் இலக்கை நிர்ணயித்து நிலையான தினசரி முயற்சியால் அதை அடையுங்கள்.",
      finance:      "தற்போது பழமையான நிதி திட்டமிடல் சிறந்தது. மாதாந்திர பட்ஜெட் வைத்திருங்கள் மற்றும் அவசரகால நிதி பராமரியுங்கள்.",
      relationship: "செயலில் கேட்பதும் திறந்த, நேரடி தொடர்பும் உறவுகளை வலுப்படுத்தும். அனுமானங்களை தவிர்க்கவும்.",
      health:       "நிலையான வழக்கம் — தரமான தூக்கம், சீரான உணவு, தினசரி இயக்கம் — க்கு முன்னுரிமை கொடுங்கள்.",
    },
  },

  te: {
    placement:       "{planet} మీ జాతకంలో {ordinal} స్థానంలో {sign} రాశిలో {dignity} ఉన్నారు ({houseType}).",
    retrograde:      " ప్రస్తుతం {planet} వక్రగతిలో ఉన్నారు.",
    noAspects:       "{planet}పై ఇప్పుడు పెద్ద గ్రహ దృష్టి లేదు — ఫలితాలు వారి స్వంత బలంపై ఆధారపడతాయి.",
    beneficOnly:     "{benefics} {planet}పై శుభ దృష్టి వేస్తున్నారు, అనుకూల మద్దతు లభిస్తోంది.",
    maleficOnly:     "{malefics} {planet}పై అశుభ దృష్టి వేస్తున్నారు, కొన్ని సవాళ్లు రావచ్చు.",
    bothAspects:     "{benefics} {planet}కు శుభ దృష్టి ఇస్తున్నారు, అదే సమయంలో {malefics} అశుభ దృష్టి వేస్తున్నారు. ఈ గ్రహ ప్రభావాలు ఈ కాలపు ఫలితాలను నిర్ణయిస్తాయి.",
    adStrong:        "{adPlanet} అంతర్దశ బలమైన స్థానంలో ఉంది — అదనపు మద్దతు అందుతోంది.",
    adModerate:      "{adPlanet} అంతర్దశ సామాన్య స్థానంలో ఉంది.",
    adWeak:          "{adPlanet} అంతర్దశ కొంచెం సవాలైన స్థానంలో ఉంది — దీని ప్రభావం కూడా ఉంటుంది.",
    adVeryWeak:      "{adPlanet} అంతర్దశ చాలా ఒత్తిడిలో ఉంది, ఈ కాలపు మొత్తం బలాన్ని తగ్గిస్తోంది.",
    conclusionGood:  "మొత్తంగా {domain} కోసం ఈ దశ అనుకూలంగా ఉంది. నిరంతర కృషితో మంచి ఫలితాలు రావచ్చు.",
    conclusionMixed: "ఇది మిశ్రమ దశ — {domain}లో కొన్ని లాభాలు, కొన్ని సవాళ్లు రెండూ ఉంటాయి. ఒక్కో అడుగు ముందుకు వేయండి.",
    conclusionBad:   "ఈ కాలంలో {domain}కు గుర్తించదగిన సవాళ్లు ఉన్నాయి. ఓర్పు మరియు వాస్తవిక అంచనాలతో {planet} దశను నావిగేట్ చేయవచ్చు.",
    cautionDusthana: "{planet} మీ {ordinal} స్థానంలో (దుస్థానం) {sign}లో ఉన్నారు — {domain}లో ఫలితాలకు అదనపు ఓర్పు మరియు కృషి అవసరం.",
    cautionDebil:    "{planet} ప్రస్తుతం {sign}లో నీచంగా ఉన్నారు — ఈ కాలంలో వారి సహజ సామర్థ్యం కొంచెం తక్కువగా ఉంటుంది.",
    cautionMalAspect:"{malefics} {planet}పై నేరుగా దృష్టి వేస్తున్నారు — {domain}లో ఊహించని అడ్డంకులు రావచ్చు.",
    cautionNone:     "{planet} ప్రస్తుత స్థానంలో పెద్ద బలహీనత లేదు, కానీ హఠాత్తు నిర్ణయాలు తీసుకోకండి.",
    adCautionDusthana:" {adPlanet} అంతర్దశ కూడా {ordinal} స్థానంలో ఉంది — రెట్టింపు ఒత్తిడి ఉండవచ్చు, జాగ్రత్తగా అడుగు వేయండి.",
    adCautionWeak:   " {adPlanet} అంతర్దశ కూడా బలహీన స్థానంలో ఉంది — ప్రతి ముఖ్యమైన నిర్ణయాన్ని జాగ్రత్తగా ఆలోచించండి.",
    behaviourCareer: " కార్యాలయ వివాదాలు మరియు రాజకీయాలకు దూరంగా ఉండండి. మీ పనిపై దృష్టి పెట్టండి.",
    behaviourFinance:" పెద్ద ఆర్థిక నిర్ణయాలకు ఎల్లప్పుడూ రెండవ అభిప్రాయం తీసుకోండి. FOMO ద్వారా పెట్టుబడులు పెట్టకండి.",
    behaviourRel:    " ఊహలు వేయకండి — మనసులో ఉన్నది నేరుగా చెప్పండి. అదుపు లేని భావోద్వేగాలు సంబంధాలను దెబ్బతీస్తాయి.",
    behaviourHealth: " శరీరం ఇచ్చే ముందస్తు హెచ్చరికలు పట్టించుకోండి. అతిగా శ్రమించడం మరియు అక్రమ దినచర్యను తప్పనిసరిగా నివారించండి.",
    categoryGood:    "{pdPlanet}–{adPlanet} దశ {domain} కోసం అనుకూలంగా ఉంది. నిరంతర కృషి మంచి ఫలితాలు తెస్తుంది.",
    categoryMixed:   "{pdPlanet}–{adPlanet} దశ {domain}లో మిశ్రమ ఫలితాలు ఇస్తోంది. దృష్టి పెట్టడం ఉత్తమం.",
    categoryBad:     "{pdPlanet}–{adPlanet} దశ {domain}లో సవాళ్లు తెస్తోంది. ఓర్పు మరియు వాస్తవిక విధానం కీలకం.",
    remedies: {
      Sun:     "తెల్లవారుజామున ఉదయిస్తున్న సూర్యునికి జలం అర్పించండి. 'ఓం సూర్యాయ నమః' నిత్యం జపించండి. ఆదివారం రాగి లేదా నారింజ రంగు ధరించండి.",
      Moon:    "నీటి దగ్గర లేదా చంద్రకాంతిలో ధ్యానం చేయండి. 'ఓం సోం సోమాయ నమః' జపించండి. సోమవారం తెలుపు ధరించండి.",
      Mars:    "శిక్షణాబద్ధ శారీరక అభ్యాసంలో శక్తిని వినియోగించండి. హనుమాన్ చాలీసా నియమితంగా పఠించండి. మంగళవారం ఎరుపు ధరించండి.",
      Mercury: "మీ ఆలోచనలను రాయండి. 'ఓం బుధాయ నమః' జపించండి. బుధవారం ఆకుపచ్చ ధరించండి.",
      Jupiter: "ప్రతిరోజూ శాస్త్ర గ్రంథాలు చదవండి. 'ఓం గురవే నమః' జపించండి. గురువారం పసుపు ధరించండి. కృతజ్ఞతను అభ్యసించండి.",
      Venus:   "సృజనాత్మక వ్యక్తీకరణ మరియు స్వ-సంరక్షణలో పెట్టుబడి పెట్టండి. 'ఓం శుక్రాయ నమః' జపించండి. శుక్రవారం తెలుపు లేదా గులాబీ ధరించండి.",
      Saturn:  "రోజువారీ క్రమశిక్షణకు కట్టుబడండి. 'ఓం శనైశ్చరాయ నమః' జపించండి. అవసరమైన వారికి సేవ చేయండి. శనివారం నీలం ధరించండి.",
      Rahu:    "రోజువారీ గ్రౌండింగ్ చేయండి — ఆరుబయట నడక, లోతైన శ్వాస. 'ఓం రాహవే నమః' జపించండి. అనిశ్చితత్వాన్ని స్వీకరించండి.",
      Ketu:    "మీ ధ్యాన అభ్యాసాన్ని లోతుగా చేయండి. 'ఓం కేతవే నమః' జపించండి. కేతు అంతరంగిక ఆధ్యాత్మిక పనిని సమర్థిస్తారు.",
    },
    practicals: {
      career:       "ఈ కాలానికి ఒక స్పష్టమైన వృత్తి లక్ష్యాన్ని నిర్ణయించి నిరంతర రోజువారీ కృషితో దాన్ని సాధించండి.",
      finance:      "ప్రస్తుతం సంప్రదాయ ఆర్థిక ప్రణాళిక ఉత్తమం. మాసిక బడ్జెట్ పాటించండి మరియు అత్యవసర నిధిని నిర్వహించండి.",
      relationship: "చురుకుగా వినడం మరియు నేరుగా సంభాషించడం సంబంధాలను బలపరుస్తుంది. ఊహలు వేయకండి.",
      health:       "నిలకడైన దినచర్య — నాణ్యమైన నిద్ర, సమతుల్య ఆహారం, రోజువారీ వ్యాయామం — కు ప్రాధాన్యత ఇవ్వండి.",
    },
  },

  bn: {
    placement:       "{planet} আপনার জন্মছকে {ordinal} ভাবে {sign} রাশিতে {dignity} অবস্থিত ({houseType})।",
    retrograde:      " বর্তমানে {planet} বক্রচালী।",
    noAspects:       "{planet}-এর উপর এখন কোনো বড় গ্রহ দৃষ্টি নেই — ফল মূলত তাঁর নিজস্ব বলের উপর নির্ভর করবে।",
    beneficOnly:     "{benefics} {planet}-এর উপর শুভ দৃষ্টি দিচ্ছেন, সহায়তা পাওয়া যাচ্ছে।",
    maleficOnly:     "{malefics} {planet}-এর উপর অশুভ দৃষ্টি দিচ্ছেন, কিছু চ্যালেঞ্জ আসতে পারে।",
    bothAspects:     "{benefics} {planet}-এর উপর শুভ দৃষ্টি দিচ্ছেন, একই সাথে {malefics} অশুভ দৃষ্টি দিচ্ছেন। এই গ্রহ প্রভাব এই কালের ফলাফল নির্ধারণ করবে।",
    adStrong:        "{adPlanet} অন্তর্দশা শক্তিশালী অবস্থানে আছে — অতিরিক্ত সহায়তা পাওয়া যাচ্ছে।",
    adModerate:      "{adPlanet} অন্তর্দশা সাধারণ অবস্থানে আছে।",
    adWeak:          "{adPlanet} অন্তর্দশা কিছুটা চ্যালেঞ্জিং অবস্থানে আছে — এর প্রভাবও পড়বে।",
    adVeryWeak:      "{adPlanet} অন্তর্দশা যথেষ্ট চাপে আছে, এই কালের সামগ্রিক শক্তি কমিয়ে দিচ্ছে।",
    conclusionGood:  "সামগ্রিকভাবে {domain} এর জন্য এই সময় অনুকূল। ধারাবাহিক প্রচেষ্টায় ভালো ফল পাওয়ার সম্ভাবনা আছে।",
    conclusionMixed: "এটি একটি মিশ্র পর্যায় — {domain} এ কিছু লাভ ও কিছু চ্যালেঞ্জ দুটোই আসতে পারে। একধাপ একধাপ এগিয়ে যান।",
    conclusionBad:   "এই সময়ে {domain} এ উল্লেখযোগ্য চ্যালেঞ্জ আছে। ধৈর্য ও বাস্তবসম্মত প্রত্যাশায় {planet} এর দশা ভালোভাবে অতিক্রম করা সম্ভব।",
    cautionDusthana: "{planet} আপনার {ordinal} ভাবে (দুস্থান) {sign} রাশিতে আছেন — {domain} এ ফলাফলের জন্য বাড়তি ধৈর্য ও প্রচেষ্টা দরকার।",
    cautionDebil:    "{planet} বর্তমানে {sign} রাশিতে নীচ অবস্থানে — এই সময়ে তাঁর স্বাভাবিক সামর্থ্য কিছুটা কম থাকবে।",
    cautionMalAspect:"{malefics} সরাসরি {planet}-এর উপর দৃষ্টি দিচ্ছেন — {domain} এ অপ্রত্যাশিত বাধা আসতে পারে।",
    cautionNone:     "{planet} এর বর্তমান অবস্থানে বড় কোনো দুর্বলতা নেই, তবে আবেগপ্রবণ সিদ্ধান্ত থেকে দূরে থাকুন।",
    adCautionDusthana:" {adPlanet} অন্তর্দশাও {ordinal} ভাবে আছে — দ্বিগুণ চাপ হতে পারে, তাই সুচিন্তিত পদক্ষেপ নিন।",
    adCautionWeak:   " {adPlanet} অন্তর্দশাও দুর্বল অবস্থানে আছে — প্রতিটি গুরুত্বপূর্ণ সিদ্ধান্ত সতর্কতার সাথে নিন।",
    behaviourCareer: " কর্মক্ষেত্রের বিবাদ ও রাজনীতি থেকে দূরে থাকুন। নিজের কাজে মনোযোগ দিন।",
    behaviourFinance:" বড় আর্থিক সিদ্ধান্তে সর্বদা দ্বিতীয় মতামত নিন। FOMO-চালিত বিনিয়োগ থেকে বিরত থাকুন।",
    behaviourRel:    " অনুমান করবেন না — মনের কথা সরাসরি বলুন। অনিয়ন্ত্রিত আবেগ সম্পর্ককে ক্ষতি করে।",
    behaviourHealth: " শরীরের প্রাথমিক সংকেত উপেক্ষা করবেন না। অতিরিক্ত পরিশ্রম ও অনিয়মিত রুটিন থেকে কঠোরভাবে দূরে থাকুন।",
    categoryGood:    "{pdPlanet}–{adPlanet} দশা {domain} এর জন্য অনুকূল। ধারাবাহিক প্রচেষ্টায় ভালো ফল মিলবে।",
    categoryMixed:   "{pdPlanet}–{adPlanet} দশা {domain} এ মিশ্র ফল দিচ্ছে। মনোযোগী থাকলে উন্নতি হবে।",
    categoryBad:     "{pdPlanet}–{adPlanet} দশা {domain} এ চ্যালেঞ্জ আনছে। ধৈর্য ও বাস্তবমুখী দৃষ্টিভঙ্গি জরুরি।",
    remedies: {
      Sun:     "ভোরবেলা উদীয়মান সূর্যকে জল অর্পণ করুন। প্রতিদিন 'ওম সূর্যায় নমঃ' জপ করুন। রবিবারে তামা বা কমলা রঙ পরুন।",
      Moon:    "জলের কাছে বা জ্যোৎস্নায় ধ্যান করুন। 'ওম সোম সোমায় নমঃ' জপ করুন। সোমবারে সাদা পরুন।",
      Mars:    "সুশৃঙ্খল শারীরিক অনুশীলনে শক্তি দিন। নিয়মিত হনুমান চালিশা পাঠ করুন। মঙ্গলবারে লাল পরুন।",
      Mercury: "আপনার চিন্তা লিখুন। 'ওম বুধায় নমঃ' জপ করুন। বুধবারে সবুজ পরুন।",
      Jupiter: "প্রতিদিন শাস্ত্রীয় গ্রন্থ পড়ুন। 'ওম গুরবে নমঃ' জপ করুন। বৃহস্পতিবারে হলুদ পরুন। কৃতজ্ঞতা অনুশীলন করুন।",
      Venus:   "সৃজনশীল প্রকাশ ও আত্ম-যত্নে বিনিয়োগ করুন। 'ওম শুক্রায় নমঃ' জপ করুন। শুক্রবারে সাদা বা গোলাপি পরুন।",
      Saturn:  "দৈনিক শৃঙ্খলায় প্রতিশ্রুতিবদ্ধ হন। 'ওম শনৈশ্চরায় নমঃ' জপ করুন। প্রয়োজনগ্রস্তদের সেবা করুন। শনিবারে নীল পরুন।",
      Rahu:    "প্রতিদিন গ্রাউন্ডিং করুন — খালি পায়ে হাঁটা, গভীর শ্বাস। 'ওম রাহবে নমঃ' জপ করুন। অনিশ্চয়তাকে স্বীকার করুন।",
      Ketu:    "ধ্যানের অনুশীলন গভীর করুন। 'ওম কেতবে নমঃ' জপ করুন। কেতু অন্তরের আধ্যাত্মিক কাজকে সমর্থন করেন।",
    },
    practicals: {
      career:       "এই কালের জন্য একটি স্পষ্ট ক্যারিয়ার লক্ষ্য নির্ধারণ করুন এবং ধারাবাহিক দৈনিক প্রচেষ্টায় সেটি অর্জন করুন।",
      finance:      "এখন রক্ষণশীল আর্থিক পরিকল্পনা সবচেয়ে ভালো। মাসিক বাজেট মেনে চলুন এবং জরুরি তহবিল রাখুন।",
      relationship: "সক্রিয়ভাবে শোনা এবং খোলাখুলি যোগাযোগ সম্পর্ককে শক্তিশালী করে। অনুমান এড়িয়ে চলুন।",
      health:       "ধারাবাহিক রুটিন — মানসম্পন্ন ঘুম, সুষম খাদ্য এবং দৈনিক ব্যায়াম — কে অগ্রাধিকার দিন।",
    },
  },

  mr: {
    placement:       "{planet} तुमच्या कुंडलीत {ordinal} भावात {sign} राशीत {dignity} आहेत ({houseType}).",
    retrograde:      " सध्या {planet} वक्री अवस्थेत आहेत.",
    noAspects:       "{planet}वर सध्या कोणतीही मोठी ग्रह दृष्टी नाही — फळ मुख्यतः त्यांच्या स्वतःच्या शक्तीवर अवलंबून असेल.",
    beneficOnly:     "{benefics}ची शुभ दृष्टी {planet}ला सहकार्य देत आहे.",
    maleficOnly:     "{malefics}ची अशुभ दृष्टी {planet}वर पडत आहे, काही अडचणी येऊ शकतात.",
    bothAspects:     "{benefics}ची शुभ दृष्टी {planet}ला सहकार्य देत आहे, त्याचबरोबर {malefics}ची अशुभ दृष्टीही पडत आहे. या ग्रहांचा प्रभाव या काळातील परिणामांवर पडेल.",
    adStrong:        "{adPlanet} अंतर्दशा मजबूत स्थितीत आहे — अतिरिक्त सहकार्य मिळत आहे.",
    adModerate:      "{adPlanet} अंतर्दशा सामान्य स्थितीत आहे.",
    adWeak:          "{adPlanet} अंतर्दशा थोडी आव्हानात्मक स्थितीत आहे — त्याचाही परिणाम होईल.",
    adVeryWeak:      "{adPlanet} अंतर्दशा खूप दबावाखाली आहे, या काळाची एकूण शक्ती कमी करत आहे.",
    conclusionGood:  "एकूणच {domain} साठी हा काळ अनुकूल आहे. सातत्यपूर्ण प्रयत्नाने चांगले परिणाम मिळण्याची शक्यता आहे.",
    conclusionMixed: "हा एक मिश्र टप्पा आहे — {domain} मध्ये काही फायदे आणि काही आव्हाने दोन्ही येऊ शकतात. एक-एक पाऊल पुढे टाका.",
    conclusionBad:   "या काळात {domain} मध्ये उल्लेखनीय आव्हाने आहेत. संयम आणि वास्तववादी अपेक्षांनी {planet} दशा चांगल्या प्रकारे पार करता येईल.",
    cautionDusthana: "{planet} तुमच्या {ordinal} भावात (दुस्थान) {sign} मध्ये आहेत — {domain} मध्ये परिणामांसाठी अतिरिक्त संयम आणि प्रयत्न आवश्यक.",
    cautionDebil:    "{planet} सध्या {sign} मध्ये नीच अवस्थेत आहेत — या काळात त्यांची नैसर्गिक क्षमता थोडी कमी असेल.",
    cautionMalAspect:"{malefics}ची सरळ दृष्टी {planet}वर आहे — {domain} मध्ये अनपेक्षित अडथळे येऊ शकतात.",
    cautionNone:     "{planet}च्या सध्याच्या स्थितीत कोणतीही मोठी कमकुवतपणा नाही, परंतु आवेगी निर्णय टाळा.",
    adCautionDusthana:" {adPlanet} अंतर्दशाही {ordinal} भावात आहे — दुहेरी दबाव येऊ शकतो, म्हणून विचारपूर्वक पाऊल टाका.",
    adCautionWeak:   " {adPlanet} अंतर्दशाही कमकुवत स्थितीत आहे — प्रत्येक मोठ्या निर्णयावर काळजीपूर्वक विचार करा.",
    behaviourCareer: " कामाच्या ठिकाणचे वाद आणि राजकारणापासून दूर राहा. स्वतःच्या कामावर लक्ष केंद्रित करा.",
    behaviourFinance:" मोठ्या आर्थिक निर्णयांसाठी नेहमी दुसरे मत घ्या. FOMO-प्रेरित गुंतवणुकीपासून दूर राहा.",
    behaviourRel:    " अंदाज बांधू नका — मनात जे आहे ते थेट सांगा. अनियंत्रित भावना नाती खराब करतात.",
    behaviourHealth: " शरीराचे सुरुवातीचे इशारे दुर्लक्ष करू नका. अतिश्रम आणि अनियमित दिनचर्यापासून कटाक्षाने दूर राहा.",
    categoryGood:    "{pdPlanet}–{adPlanet} दशा {domain} साठी अनुकूल आहे. सातत्यपूर्ण प्रयत्नाने चांगले परिणाम मिळतील.",
    categoryMixed:   "{pdPlanet}–{adPlanet} दशा {domain} मध्ये मिश्र परिणाम देत आहे. लक्ष केंद्रित ठेवल्यास सुधारणा होऊ शकते.",
    categoryBad:     "{pdPlanet}–{adPlanet} दशा {domain} मध्ये आव्हाने आणत आहे. संयम आणि वास्तववादी दृष्टिकोण महत्त्वाचा.",
    remedies: {
      Sun:     "पहाटे उगवत्या सूर्याला जल अर्पण करा. दररोज 'ओम सूर्याय नमः' जप करा. रविवारी तांबे किंवा नारंगी रंग घाला.",
      Moon:    "पाण्याजवळ किंवा चंद्रप्रकाशात ध्यान करा. 'ओम सोम सोमाय नमः' जप करा. सोमवारी पांढरे घाला.",
      Mars:    "शिस्तबद्ध शारीरिक अभ्यासात ऊर्जा खर्च करा. नियमित हनुमान चालीसा वाचा. मंगळवारी लाल घाला.",
      Mercury: "तुमचे विचार लिहा. 'ओम बुधाय नमः' जप करा. बुधवारी हिरवे घाला.",
      Jupiter: "दररोज शास्त्रग्रंथ वाचा. 'ओम गुरवे नमः' जप करा. गुरुवारी पिवळे घाला. कृतज्ञता अभ्यासा.",
      Venus:   "सर्जनशील अभिव्यक्ती आणि स्वत:ची काळजी यात गुंतवणूक करा. 'ओम शुक्राय नमः' जप करा. शुक्रवारी पांढरे किंवा गुलाबी घाला.",
      Saturn:  "दैनिक शिस्तीशी बांधील राहा. 'ओम शनैश्चराय नमः' जप करा. गरजूंची सेवा करा. शनिवारी निळे घाला.",
      Rahu:    "दररोज ग्राउंडिंग करा — अनवाणी चालणे, खोल श्वास. 'ओम राहवे नमः' जप करा. अनिश्चिततेला प्रतिरोध न करता स्वीकारा.",
      Ketu:    "ध्यानाचा अभ्यास खोल करा. 'ओम केतवे नमः' जप करा. केतू अंतरंगाच्या आध्यात्मिक कार्याला प्रोत्साहन देतो.",
    },
    practicals: {
      career:       "या काळासाठी एक स्पष्ट करिअर लक्ष्य ठरवा आणि सातत्यपूर्ण दैनिक प्रयत्नाने ते साध्य करा.",
      finance:      "सध्या पुराणमतवादी आर्थिक नियोजन सर्वोत्तम आहे. मासिक बजेट पाळा आणि आपत्कालीन निधी ठेवा.",
      relationship: "सक्रिय श्रवण आणि मोकळे, थेट संवाद नाती मजबूत करतात. गृहीतके टाळा.",
      health:       "सातत्यपूर्ण दिनचर्या — दर्जेदार झोप, संतुलित आहार आणि दैनिक व्यायाम — ला प्राधान्य द्या.",
    },
  },

  gu: {
    placement:       "{planet} તમારી કુંડળીમાં {ordinal} ભાવમાં {sign} રાશિમાં {dignity} છે ({houseType}).",
    retrograde:      " હાલ {planet} વક્રી ગ્રહ ચાલ કરી રહ્યા છે.",
    noAspects:       "{planet} પર હાલ કોઈ મોટી ગ્રહ દૃષ્ટિ નથી — ફળ મુખ્યત્વે તેમની પોતાની શક્તિ પર આધારિત છે.",
    beneficOnly:     "{benefics}ની શુભ દૃષ્ટિ {planet}ને સહકાર આપી રહી છે.",
    maleficOnly:     "{malefics}ની અશુભ દૃષ્ટિ {planet} પર પડી રહી છે, કેટલીક મુશ્કેલીઓ આવી શકે.",
    bothAspects:     "{benefics}ની શુભ દૃષ્ટિ {planet}ને સહકાર આપી રહી છે, સાથે {malefics}ની અશુભ દૃષ્ટિ પણ પડી રહી છે. આ ગ્રહ-પ્રભાવ આ સમયના પરિણામ નક્કી કરશે.",
    adStrong:        "{adPlanet} અંતર્દશા મજબૂત સ્થિતિમાં છે — વધારાનો સહકાર મળી રહ્યો છે.",
    adModerate:      "{adPlanet} અંતર્દશા સામાન્ય સ્થિતિમાં છે.",
    adWeak:          "{adPlanet} અંતર્દશા થોડી પડકારજનક સ્થિતિમાં છે — તેની પણ અસર થશે.",
    adVeryWeak:      "{adPlanet} અંતર્દશા ઘણા દબાણ હેઠળ છે, આ સમયની સમગ્ર શક્તિ ઘટાડી રહ્યો છે.",
    conclusionGood:  "એકંદરે {domain} માટે આ સમય અનુકૂળ છે. નિરંતર પ્રયત્ન વડે સારા પરિણામ મળવાની સારી શક્યતા છે.",
    conclusionMixed: "આ એક મિશ્ર તબક્કો છે — {domain} માં કેટલાક ફાયદા અને કેટલાક પડકારો બન્ને આવી શકે. એક-એક ડગ આગળ વધો.",
    conclusionBad:   "આ સમયે {domain} માં નોંધપાત્ર પડકારો છે. ધૈર્ય અને વાસ્તવવાદી અપેક્ષાઓ વડે {planet} ની દશા સારી રીતે પસાર કરી શકાય.",
    cautionDusthana: "{planet} તમારા {ordinal} ભાવ (દૂષ્ઠ) માં {sign} રાશિમાં છે — {domain} ના પરિણામ માટે વધારાની ધૈર્ય અને પ્રયત્ન જરૂરી.",
    cautionDebil:    "{planet} હાલ {sign} રાશિમાં નીચ સ્થિતિમાં છે — આ સમય દરમ્યાન તેમની સ્વાભાવિક ક્ષમતા થોડી ઘટે.",
    cautionMalAspect:"{malefics}ની સીધી દૃષ્ટિ {planet} પર છે — {domain} માં અણધારી અડચણો આવી શકે.",
    cautionNone:     "{planet}ની અત્યારની સ્થિતિ મોટી નબળાઈ વિનાની છે, પરંતુ આવેગ-ચાલિત નિર્ણયો ટાળો.",
    adCautionDusthana:" {adPlanet} અંતર્દશા પણ {ordinal} ભાવ માં છે — બેવડું દબાણ આવી શકે, સૂઝ-સમજ વડે આગળ વધો.",
    adCautionWeak:   " {adPlanet} અંતર્દશા પણ નબળી સ્થિતિ માં છે — દરેક મહત્ત્વના નિર્ણય પર કાળજીપૂર્વક વિચાર કરો.",
    behaviourCareer: " કાર્ય-સ્થળ પર ઝઘડા અને રાજકારણ થી દૂર રહો. પોતાના કામ પર ધ્યાન આપો.",
    behaviourFinance:" મોટા આર્થિક નિર્ણયો લેતાં પહેલાં હંમેશા બીજી સલાહ લો. FOMO-ચાલિત રોકાણ ટાળો.",
    behaviourRel:    " ધારણા ન કરો — મનમાં છે તે સ્પષ્ટ રીતે કહો. અનિયંત્રિત ભાવનાઓ સંબંધ બગાડે છે.",
    behaviourHealth: " શરીરના શરૂઆતના સંકેતો અવગણો નહીં. અતિ-શ્રમ અને અનિયમિત દૈનિક ક્રમ ચુસ્ત રીતે ટાળો.",
    categoryGood:    "{pdPlanet}–{adPlanet} દશા {domain} માટે અનુકૂળ છે. નિરંતર પ્રયત્ન સારા ફળ લાવશે.",
    categoryMixed:   "{pdPlanet}–{adPlanet} દશા {domain} માં મિશ્ર પરિણામ આપી રહ્યો છે. ધ્યાન કેન્દ્રિત રાખો.",
    categoryBad:     "{pdPlanet}–{adPlanet} દશા {domain} માં પડકારો લાવી રહ્યો છે. ધૈર્ય અને વાસ્તવવાદી અભિગમ જરૂરી.",
    remedies: {
      Sun:     "સૂ ." ,
      Moon:    "ચ ." ,
      Mars:    "મ ." ,
      Mercury: "બ ." ,
      Jupiter: "ગ ." ,
      Venus:   "શ ." ,
      Saturn:  "શ ." ,
      Rahu:    "ર ." ,
      Ketu:    "ક ." ,
    },
    practicals: {
      career:       "આ સમય માટે એક સ્પષ્ટ કારકિર્દી લક્ષ્ય નક્કી કરો અને નિરંતર દૈનિક પ્રયત્ન વડે તે હાંસલ કરો.",
      finance:      "અત્યારે રૂઢિચુસ્ત આર્થિક આયોજન શ્રેષ્ઠ છે. માસિક બજેટ જાળવો અને કટોકટી ભંડોળ રાખો.",
      relationship: "સક્રિય રીતે સાંભળવું અને ખુલ્લો, સીધો સંવાદ સંબંધ મજબૂત કરે છે. ધારણાઓ ટાળો.",
      health:       "નિયમિત દૈનિક ક્રમ — ગુણવત્તાયુક્ત ઊંઘ, સંતુલિત આહાર અને દૈનિક વ્યાયામ — ને પ્રાધાન્ય આપો.",
    },
  },

  kn: {
    placement:       "{planet} is placed in your {ordinal} house in {sign} — {dignity} ({houseType}).",
    retrograde:      " {planet} is currently in retrograde motion, turning energy inward.",
    noAspects:       "No major planetary aspects fall on {planet} right now — outcomes depend primarily on its own strength.",
    beneficOnly:     "{benefics} cast a favorable aspect on {planet}, providing support.",
    maleficOnly:     "{malefics} aspect {planet} with challenging energy, bringing some friction.",
    bothAspects:     "{benefics} provide favorable aspects on {planet}, while {malefics} also aspect it. These planetary influences shape the outcomes of this period.",
    adStrong:        "{adPlanet} Antardasha is in a strong position — providing additional support.",
    adModerate:      "{adPlanet} Antardasha is in moderate standing.",
    adWeak:          "{adPlanet} Antardasha is in a somewhat challenging position — its influence adds complexity.",
    adVeryWeak:      "{adPlanet} Antardasha is under considerable pressure, reducing the overall strength of this period.",
    conclusionGood:  "Overall, this is a relatively favorable phase for your {domain}. Consistent effort is likely to yield positive results.",
    conclusionMixed: "This is a mixed phase — expect both gains and challenges in your {domain}. Take one step at a time.",
    conclusionBad:   "This period brings notable challenges for your {domain}. Patience and realistic expectations will help you navigate {planet}'s dasha well.",
    cautionDusthana: "{planet} is in your {ordinal} house (a challenging house) in {sign} — extra patience and effort will be needed for results in your {domain}.",
    cautionDebil:    "{planet} is currently debilitated in {sign} — its natural potential is somewhat limited during this period.",
    cautionMalAspect:"{malefics} casts a challenging aspect on {planet} — unexpected obstacles or pressure may arise in your {domain}.",
    cautionNone:     "{planet} shows no major structural weakness in its current position, but avoid impulsive decisions.",
    adCautionDusthana:" {adPlanet} Antardasha is also in the {ordinal} house — this double pressure calls for calculated, deliberate steps.",
    adCautionWeak:   " {adPlanet} Antardasha is also in a weak position — reconsider every major decision carefully before acting.",
    behaviourCareer: " Avoid workplace conflicts and office politics. Stay focused on your own work.",
    behaviourFinance:" Always seek a second opinion for major financial decisions. Avoid FOMO-driven investments.",
    behaviourRel:    " Don't assume — express what's on your mind directly. Unchecked emotions damage relationships.",
    behaviourHealth: " Don't ignore your body's early warning signals. Strictly avoid overexertion and irregular routines.",
    categoryGood:    "{pdPlanet}–{adPlanet} phase is favorable for your {domain}. Consistent effort will bring good results.",
    categoryMixed:   "{pdPlanet}–{adPlanet} phase gives mixed results for your {domain}. Staying focused will help improve outcomes.",
    categoryBad:     "{pdPlanet}–{adPlanet} phase brings challenges to your {domain}. Patience and a realistic approach are key.",
    remedies: {
      Sun:     "Offer water to the rising sun at dawn. Chant 'Om Suryaya Namah' daily. Wear copper or orange on Sundays.",
      Moon:    "Meditate near water or moonlight. Chant 'Om Som Somaya Namah'. Wear white on Mondays.",
      Mars:    "Channel energy into disciplined physical practice. Recite the Hanuman Chalisa regularly. Wear red on Tuesdays.",
      Mercury: "Journal your thoughts. Chant 'Om Budhaya Namah'. Wear green on Wednesdays.",
      Jupiter: "Study sacred texts daily. Chant 'Om Gurave Namah'. Wear yellow on Thursdays. Practice gratitude.",
      Venus:   "Invest in creative expression and self-care. Chant 'Om Shukraya Namah'. Wear white or pink on Fridays.",
      Saturn:  "Commit to daily discipline. Chant 'Om Shanaischaraya Namah'. Serve those in need. Wear blue on Saturdays.",
      Rahu:    "Practice daily grounding — barefoot walks, deep breathing. Chant 'Om Rahave Namah'. Accept uncertainty.",
      Ketu:    "Deepen your meditation practice. Chant 'Om Ketave Namah'. Ketu favors inner spiritual work.",
    },
    practicals: {
      career:       "Set one clear career goal for this period and pursue it with consistent daily effort. Minimize distractions.",
      finance:      "Conservative financial planning serves you best now. Maintain a monthly budget and keep an emergency fund.",
      relationship: "Active listening and open, direct communication strengthen relationships. Avoid assumptions.",
      health:       "Prioritize a consistent routine — quality sleep, balanced diet, and daily movement. Listen to your body early.",
    },
  },

  en: {
    placement:       "{planet} is placed in your {ordinal} house in {sign} — {dignity} ({houseType}).",
    retrograde:      " {planet} is currently in retrograde motion, turning energy inward.",
    noAspects:       "No major planetary aspects fall on {planet} right now — outcomes depend primarily on its own strength.",
    beneficOnly:     "{benefics} cast a favorable aspect on {planet}, providing support.",
    maleficOnly:     "{malefics} aspect {planet} with challenging energy, bringing some friction.",
    bothAspects:     "{benefics} provide favorable aspects on {planet}, while {malefics} also aspect it. These planetary influences shape the outcomes of this period.",
    adStrong:        "{adPlanet} Antardasha is in a strong position — providing additional support.",
    adModerate:      "{adPlanet} Antardasha is in moderate standing.",
    adWeak:          "{adPlanet} Antardasha is in a somewhat challenging position — its influence adds complexity.",
    adVeryWeak:      "{adPlanet} Antardasha is under considerable pressure, reducing the overall strength of this period.",
    conclusionGood:  "Overall, this is a relatively favorable phase for your {domain}. Consistent effort is likely to yield positive results.",
    conclusionMixed: "This is a mixed phase — expect both gains and challenges in your {domain}. Take one step at a time.",
    conclusionBad:   "This period brings notable challenges for your {domain}. Patience and realistic expectations will help you navigate {planet}'s dasha well.",
    cautionDusthana: "{planet} is in your {ordinal} house (a challenging house) in {sign} — extra patience and effort will be needed for results in your {domain}.",
    cautionDebil:    "{planet} is currently debilitated in {sign} — its natural potential is somewhat limited during this period.",
    cautionMalAspect:"{malefics} casts a challenging aspect on {planet} — unexpected obstacles or pressure may arise in your {domain}.",
    cautionNone:     "{planet} shows no major structural weakness in its current position, but avoid impulsive decisions.",
    adCautionDusthana:" {adPlanet} Antardasha is also in the {ordinal} house — this double pressure calls for calculated, deliberate steps.",
    adCautionWeak:   " {adPlanet} Antardasha is also in a weak position — reconsider every major decision carefully before acting.",
    behaviourCareer: " Avoid workplace conflicts and office politics. Stay focused on your own work.",
    behaviourFinance:" Always seek a second opinion for major financial decisions. Avoid FOMO-driven investments.",
    behaviourRel:    " Don't assume — express what's on your mind directly. Unchecked emotions damage relationships.",
    behaviourHealth: " Don't ignore your body's early warning signals. Strictly avoid overexertion and irregular routines.",
    categoryGood:    "{pdPlanet}–{adPlanet} phase is favorable for your {domain}. Consistent effort will bring good results.",
    categoryMixed:   "{pdPlanet}–{adPlanet} phase gives mixed results for your {domain}. Staying focused will help improve outcomes.",
    categoryBad:     "{pdPlanet}–{adPlanet} phase brings challenges to your {domain}. Patience and a realistic approach are key.",
    remedies: {
      Sun:     "Offer water to the rising sun at dawn. Chant 'Om Suryaya Namah' daily. Wear copper or orange on Sundays.",
      Moon:    "Meditate near water or moonlight. Chant 'Om Som Somaya Namah'. Wear white on Mondays.",
      Mars:    "Channel energy into disciplined physical practice. Recite the Hanuman Chalisa regularly. Wear red on Tuesdays.",
      Mercury: "Journal your thoughts. Chant 'Om Budhaya Namah'. Wear green on Wednesdays.",
      Jupiter: "Study sacred texts daily. Chant 'Om Gurave Namah'. Wear yellow on Thursdays. Practice gratitude.",
      Venus:   "Invest in creative expression and self-care. Chant 'Om Shukraya Namah'. Wear white or pink on Fridays.",
      Saturn:  "Commit to daily discipline. Chant 'Om Shanaischaraya Namah'. Serve those in need. Wear blue on Saturdays.",
      Rahu:    "Practice daily grounding — barefoot walks, deep breathing. Chant 'Om Rahave Namah'. Accept uncertainty.",
      Ketu:    "Deepen your meditation practice. Chant 'Om Ketave Namah'. Ketu favors inner spiritual work.",
    },
    practicals: {
      career:       "Set one clear career goal for this period and pursue it with consistent daily effort. Minimize distractions.",
      finance:      "Conservative financial planning serves you best now. Maintain a monthly budget and keep an emergency fund.",
      relationship: "Active listening and open, direct communication strengthen relationships. Avoid assumptions.",
      health:       "Prioritize a consistent routine — quality sleep, balanced diet, and daily movement. Listen to your body early.",
    },
  },
};

// ── Gujarati remedies (using Hindi Devanagari text — understood by Gujarati speakers for Vedic practices) ──
TEMPLATES.gu.remedies = {
  Sun:     "સૂ ...",
  Moon:    "ચ ...",
  Mars:    "મ ...",
  Mercury: "બ ...",
  Jupiter: "ગ ...",
  Venus:   "શ ...",
  Saturn:  "શ ...",
  Rahu:    "ર ...",
  Ketu:    "ક ...",
};

// ── Public helper functions ───────────────────────────────────────────────────
export function signName(lang: LangCode, idx: number): string {
  return SIGNS[lang]?.[idx] ?? SIGNS.en[idx];
}
export function ordinal(lang: LangCode, house: number): string {
  return ORDINALS[lang]?.[house] ?? String(house);
}
export function domainKw(lang: LangCode, domain: string): string {
  return DOMAIN_KW[lang]?.[domain] ?? domain;
}

// ── Main text builder ─────────────────────────────────────────────────────────
export interface InsightTexts {
  howItWillGo: string;
  caution:     string;
  remedy:      string;
  categoryText:string;
}

export function buildInsightTexts(
  lang: LangCode,
  pdPlanet: string,
  adPlanet: string,
  domain: string,
  pdData: { house: number; longitude: number; retrograde?: boolean } | undefined,
  adData: { house: number } | undefined,
  pdBase: number,
  adBase: number,
  finalScore100: number,
  benefics: string[],
  malefics: string[],
  exalt: Record<string,number>,
  debil: Record<string,number>,
  own: Record<string,number[]>,
  signLords: string[],
  friends: Record<string,string[]>,
  enemies: Record<string,string[]>,
): InsightTexts {
  const T   = TEMPLATES[lang] ?? TEMPLATES.en;
  const pl  = (p: string) => pName(lang, p);
  const dKw = domainKw(lang, domain);
  const pdN = pl(pdPlanet);
  const adN = pl(adPlanet);

  // ── How It Will Go ─────────────────────────────────────────────────────────
  let howItWillGo = "";
  if (pdData) {
    const signIdx = Math.floor((pdData.longitude % 360) / 30);
    const sign    = signName(lang, signIdx);
    const dig     = dignityLabel(lang, pdPlanet, signIdx, exalt, debil, own, signLords, friends, enemies);
    const hType   = houseTypeLabel(lang, pdData.house);
    const ord     = ordinal(lang, pdData.house);
    howItWillGo  += fill(T.placement, { planet: pdN, ordinal: ord, sign, dignity: dig, houseType: hType });
    if (pdData.retrograde) howItWillGo += fill(T.retrograde, { planet: pdN });

    const benStr = benefics.map(pl).join(", ");
    const malStr = malefics.map(pl).join(", ");
    if (benefics.length > 0 && malefics.length > 0)
      howItWillGo += " " + fill(T.bothAspects,  { benefics: benStr, malefics: malStr, planet: pdN });
    else if (benefics.length > 0)
      howItWillGo += " " + fill(T.beneficOnly,  { benefics: benStr, planet: pdN });
    else if (malefics.length > 0)
      howItWillGo += " " + fill(T.maleficOnly,  { malefics: malStr, planet: pdN });
    else
      howItWillGo += " " + fill(T.noAspects,    { planet: pdN });
  } else {
    howItWillGo = fill(T.noAspects, { planet: pdN });
  }

  if (adBase >= 15)       howItWillGo += " " + fill(T.adStrong,   { adPlanet: adN });
  else if (adBase >= 0)   howItWillGo += " " + fill(T.adModerate, { adPlanet: adN });
  else if (adBase >= -15) howItWillGo += " " + fill(T.adWeak,     { adPlanet: adN });
  else                    howItWillGo += " " + fill(T.adVeryWeak,  { adPlanet: adN });

  if (finalScore100 >= 65)      howItWillGo += " " + fill(T.conclusionGood,  { domain: dKw });
  else if (finalScore100 >= 45) howItWillGo += " " + fill(T.conclusionMixed, { domain: dKw });
  else                          howItWillGo += " " + fill(T.conclusionBad,   { domain: dKw, planet: pdN });

  // ── Caution ────────────────────────────────────────────────────────────────
  let caution = "";
  if (pdData) {
    const signIdx = Math.floor((pdData.longitude % 360) / 30);
    const sign    = signName(lang, signIdx);
    const ord     = ordinal(lang, pdData.house);
    const malStr  = malefics.map(pl).join("/");
    if ([6,8,12].includes(pdData.house))
      caution = fill(T.cautionDusthana,  { planet: pdN, ordinal: ord, sign, domain: dKw });
    else if (debil[pdPlanet] === signIdx)
      caution = fill(T.cautionDebil,     { planet: pdN, sign });
    else if (malefics.length > 0)
      caution = fill(T.cautionMalAspect, { malefics: malStr, planet: pdN, domain: dKw });
    else
      caution = fill(T.cautionNone,      { planet: pdN });

    if (adData) {
      if ([6,8,12].includes(adData.house))
        caution += fill(T.adCautionDusthana, { adPlanet: adN, ordinal: ordinal(lang, adData.house) });
      else if (adBase < -15)
        caution += fill(T.adCautionWeak, { adPlanet: adN });
    }
  } else {
    caution = fill(T.cautionNone, { planet: pdN });
  }

  const beh: Record<string,string> = {
    career: T.behaviourCareer, finance: T.behaviourFinance,
    relationship: T.behaviourRel, health: T.behaviourHealth,
  };
  caution += beh[domain] ?? "";

  // ── Remedy ─────────────────────────────────────────────────────────────────
  const remedyStr    = T.remedies[pdPlanet] ?? "";
  const practicalStr = T.practicals[domain] ?? "";
  const remedy       = [remedyStr, practicalStr].filter(Boolean).join(" ");

  // ── Category text ──────────────────────────────────────────────────────────
  let categoryText = "";
  if (finalScore100 >= 65)
    categoryText = fill(T.categoryGood,  { pdPlanet: pdN, adPlanet: adN, domain: dKw });
  else if (finalScore100 >= 45)
    categoryText = fill(T.categoryMixed, { pdPlanet: pdN, adPlanet: adN, domain: dKw });
  else
    categoryText = fill(T.categoryBad,   { pdPlanet: pdN, adPlanet: adN, domain: dKw });

  return { howItWillGo, caution, remedy, categoryText };
}
