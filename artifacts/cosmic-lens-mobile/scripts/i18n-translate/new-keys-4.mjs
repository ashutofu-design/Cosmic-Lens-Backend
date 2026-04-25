// Tier-3 NEW i18n keys (legal + business-vastu + astrovastu-pro + astrovastu-pro-result).
// Each entry: key -> [EN, HN (Hinglish), HI (Devanagari)]
export const KEYS = {
  // ════════════════════════════ legal.tsx ════════════════════════════
  lg_title:           ["Legal & Policies",                            "Legal & Policies",                                  "क़ानूनी और नीतियाँ"],
  lg_subtitle:        ["Privacy, terms, refunds & disclaimer",        "Privacy, terms, refund aur disclaimer",             "गोपनीयता, शर्तें, रिफंड और अस्वीकरण"],
  lg_lastUpdated:     ["17 April 2026",                               "17 April 2026",                                     "17 अप्रैल 2026"],

  // ── Privacy Policy ──
  lg_h_privacy:       ["Privacy Policy",                              "Privacy Policy",                                    "गोपनीयता नीति"],
  lg_p_privacyIntro:  ["Cosmic Lens (\"we\", \"us\", \"our\") respects your privacy. This Privacy Policy explains what personal information we collect when you use our mobile application and related services (the \"Service\"), how we use it, and the choices you have. By using Cosmic Lens you agree to the practices described below.",
                       "Cosmic Lens (\"we\", \"us\", \"our\") aapki privacy ka samman karta hai. Ye Privacy Policy bataati hai ki jab aap hamari mobile application aur related services (\"Service\") use karte ho, hum kaunsi personal information collect karte hain, use kaise istemal karte hain, aur aapke paas kya choices hain. Cosmic Lens use karke aap niche likhi practices se sahmat hote ho.",
                       "Cosmic Lens (\"हम\", \"हमें\", \"हमारा\") आपकी गोपनीयता का सम्मान करता है। यह गोपनीयता नीति बताती है कि जब आप हमारे मोबाइल ऐप और संबंधित सेवाओं (\"सेवा\") का उपयोग करते हैं, तो हम कौन-सी व्यक्तिगत जानकारी एकत्र करते हैं, उसका उपयोग कैसे करते हैं, और आपके पास क्या विकल्प हैं। Cosmic Lens का उपयोग करके आप नीचे वर्णित प्रथाओं से सहमत होते हैं।"],
  lg_callout_privacy: ["We do NOT sell your personal data. We do not share your kundli, birth details, or chat history with advertisers.",
                       "Hum aapka personal data NAHI bechte. Hum aapki kundli, birth details, ya chat history advertisers ke saath share nahi karte.",
                       "हम आपका व्यक्तिगत डेटा नहीं बेचते। हम आपकी कुंडली, जन्म विवरण या चैट इतिहास विज्ञापनदाताओं के साथ साझा नहीं करते।"],

  lg_s1_title:        ["1. Information We Collect",                   "1. Hum kaunsi Information collect karte hain",      "1. हम कौन-सी जानकारी एकत्र करते हैं"],
  lg_s1_a:            ["(a) Account information — name, email address, mobile number (if you sign up with phone), Google account ID (if you use Google Sign-In). Stored securely with hashed passwords (scrypt).",
                       "(a) Account information — naam, email address, mobile number (agar phone se signup karein), Google account ID (agar Google Sign-In use karein). Hashed passwords (scrypt) ke saath surakshit store kiya jaata hai.",
                       "(क) खाता जानकारी — नाम, ईमेल पता, मोबाइल नंबर (फ़ोन से साइन अप करने पर), Google खाता ID (Google साइन-इन के साथ)। पासवर्ड scrypt से हैश करके सुरक्षित रूप से संग्रहीत।"],
  lg_s1_b:            ["(b) Birth & profile data — full name, date of birth, time of birth, place of birth, gender, and language preference. This is the minimum required to compute your Vedic kundli.",
                       "(b) Birth aur profile data — poora naam, janma tithi, janma samay, janma sthal, gender, aur language preference. Ye aapki Vedic kundli ki ganana ke liye minimum zaroori hai.",
                       "(ख) जन्म एवं प्रोफ़ाइल डेटा — पूरा नाम, जन्म तिथि, जन्म समय, जन्म स्थान, लिंग, और भाषा वरीयता। यह आपकी वैदिक कुंडली गणना के लिए न्यूनतम आवश्यक है।"],
  lg_s1_c:            ["(c) Generated content — your kundli charts, dashas, compatibility reports, Jyotish question/answer history, and saved profiles.",
                       "(c) Generated content — aapki kundli charts, dashas, compatibility reports, Jyotish question/answer history, aur saved profiles.",
                       "(ग) उत्पन्न सामग्री — आपकी कुंडली चार्ट, दशाएँ, अनुकूलता रिपोर्ट, ज्योतिष प्रश्न/उत्तर इतिहास, और सहेजी गई प्रोफ़ाइलें।"],
  lg_s1_d:            ["(d) Payment information — handled entirely by our payment processor Cashfree Payments. We only store the order ID, plan, amount, and success/failure status. We never store card numbers, UPI PINs, CVVs, or banking credentials.",
                       "(d) Payment information — poori tarah hamare payment processor Cashfree Payments ke through handle hoti hai. Hum sirf order ID, plan, amount aur success/failure status store karte hain. Hum kabhi card numbers, UPI PINs, CVVs ya banking credentials store nahi karte.",
                       "(घ) भुगतान जानकारी — पूरी तरह हमारे भुगतान प्रोसेसर Cashfree Payments द्वारा संभाली जाती है। हम केवल ऑर्डर ID, प्लान, राशि और सफलता/विफलता स्थिति संग्रहीत करते हैं। हम कभी कार्ड नंबर, UPI PIN, CVV या बैंकिंग क्रेडेंशियल संग्रहीत नहीं करते।"],
  lg_s1_e:            ["(e) Device & technical information — device model, OS version, app version, language, time zone, and crash logs. Used purely for diagnostics.",
                       "(e) Device aur technical information — device model, OS version, app version, language, time zone, aur crash logs. Sirf diagnostics ke liye use karte hain.",
                       "(ङ) डिवाइस एवं तकनीकी जानकारी — डिवाइस मॉडल, OS संस्करण, ऐप संस्करण, भाषा, समय क्षेत्र, और क्रैश लॉग। केवल डायग्नोस्टिक्स के लिए।"],

  lg_s2_title:        ["2. How We Use Your Information",              "2. Hum aapki Information kaise use karte hain",     "2. हम आपकी जानकारी का उपयोग कैसे करते हैं"],
  lg_s2_b1:           ["To create and maintain your account.",        "Aapka account banane aur maintain karne ke liye.",  "आपका खाता बनाने और बनाए रखने के लिए।"],
  lg_s2_b2:           ["To compute your kundli, dashas, doshas, compatibility, and other astrological reports.","Aapki kundli, dashas, doshas, compatibility aur dusri astrological reports compute karne ke liye.","आपकी कुंडली, दशाएँ, दोष, अनुकूलता और अन्य ज्योतिषीय रिपोर्ट गणना के लिए।"],
  lg_s2_b3:           ["To provide Jyotish-based answers to your questions using only your kundli data — not your identity.","Aapke sawalon ke Jyotish-based jawab dene ke liye, sirf aapki kundli data se — aapki identity se nahi.","आपके प्रश्नों के ज्योतिष-आधारित उत्तर देने के लिए, केवल आपकी कुंडली डेटा से — आपकी पहचान से नहीं।"],
  lg_s2_b4:           ["To process subscription payments through Cashfree.","Cashfree ke through subscription payments process karne ke liye.","Cashfree के माध्यम से सदस्यता भुगतान संसाधित करने के लिए।"],
  lg_s2_b5:           ["To enforce daily question limits and fair-usage rules.","Daily question limits aur fair-usage rules lagaane ke liye.","दैनिक प्रश्न सीमाएँ और उचित-उपयोग नियम लागू करने के लिए।"],
  lg_s2_b6:           ["To send you optional notifications (daily horoscope, panchang, muhurat reminders) — you can disable these in Settings.","Optional notifications bhejne ke liye (daily horoscope, panchang, muhurat reminders) — Settings me disable kar sakte ho.","वैकल्पिक सूचनाएँ भेजने के लिए (दैनिक राशिफल, पंचांग, मुहूर्त रिमाइंडर) — सेटिंग्स में बंद कर सकते हैं।"],
  lg_s2_b7:           ["To prevent fraud, debug crashes, and improve service quality.","Fraud rokne, crashes debug karne aur service quality improve karne ke liye.","धोखाधड़ी रोकने, क्रैश डीबग करने और सेवा गुणवत्ता सुधारने के लिए।"],
  lg_s2_b8:           ["To comply with legal obligations.",            "Legal obligations poori karne ke liye.",            "क़ानूनी दायित्वों का पालन करने के लिए।"],

  lg_s3_title:        ["3. Third-Party Services",                     "3. Third-Party Services",                           "3. तृतीय-पक्ष सेवाएँ"],
  lg_s3_intro:        ["We share the minimum necessary data with these trusted partners:","Hum in trusted partners ke saath sirf zaroori minimum data share karte hain:","हम इन विश्वसनीय भागीदारों के साथ केवल आवश्यक न्यूनतम डेटा साझा करते हैं:"],
  lg_s3_b1:           ["Google Sign-In — verifies your identity if you choose Google login. We receive your name, email, and Google ID.","Google Sign-In — agar aap Google login chunte ho to aapki identity verify karta hai. Humein aapka naam, email aur Google ID milti hai.","Google Sign-In — Google लॉगिन चुनने पर पहचान सत्यापित करता है। हमें आपका नाम, ईमेल और Google ID मिलती है।"],
  lg_s3_b2:           ["Cashfree Payments (India) — processes UPI, card, and net-banking transactions. PCI-DSS Level 1 compliant.","Cashfree Payments (India) — UPI, card aur net-banking transactions process karta hai. PCI-DSS Level 1 compliant.","Cashfree Payments (भारत) — UPI, कार्ड और नेट-बैंकिंग लेनदेन संसाधित करता है। PCI-DSS Level 1 अनुपालक।"],
  lg_s3_b3:           ["Expo / Google Play Services — push notification delivery only. No content is read by them.","Expo / Google Play Services — sirf push notification delivery. Wo koi content nahi padhte.","Expo / Google Play Services — केवल पुश नोटिफिकेशन डिलीवरी। वे कोई सामग्री नहीं पढ़ते।"],
  lg_s3_b4:           ["Cloud hosting (Replit / AWS) — encrypted database storage in India region where possible.","Cloud hosting (Replit / AWS) — jahan possible ho India region me encrypted database storage.","क्लाउड होस्टिंग (Replit / AWS) — जहाँ संभव हो भारत क्षेत्र में एन्क्रिप्टेड डेटाबेस स्टोरेज।"],
  lg_s3_outro:        ["These services have their own privacy policies which we encourage you to read.","In services ki apni privacy policies hain jo aap padhne ke liye encourage karte hain.","इन सेवाओं की अपनी गोपनीयता नीतियाँ हैं जिन्हें आप पढ़ें — हम प्रोत्साहित करते हैं।"],

  lg_s4_title:        ["4. Data Retention",                           "4. Data Retention",                                 "4. डेटा प्रतिधारण"],
  lg_s4_p:            ["We retain your account and kundli data for as long as your account is active. If you delete your account (see Section 7) we permanently erase your personal data within 30 days, except where retention is legally required (e.g. tax invoices for 7 years under Indian law).","Jab tak aapka account active hai tab tak aapka account aur kundli data retain karte hain. Account delete karne par (Section 7 dekho) aapka personal data 30 din me permanently mita diya jaata hai, jahan retention legally zaroori ho (jaise Indian law ke under tax invoices 7 saal) usko chhodkar.","जब तक आपका खाता सक्रिय है तब तक हम आपका खाता और कुंडली डेटा बनाए रखते हैं। यदि आप खाता हटाते हैं (अनुभाग 7 देखें) तो हम 30 दिन के भीतर आपका व्यक्तिगत डेटा स्थायी रूप से मिटा देते हैं, सिवाय जहाँ कानूनी रूप से प्रतिधारण आवश्यक हो (जैसे भारतीय कानून के तहत कर चालान 7 वर्ष)।"],

  lg_s5_title:        ["5. Data Security",                            "5. Data Security",                                  "5. डेटा सुरक्षा"],
  lg_s5_b1:           ["All API traffic is encrypted with TLS 1.2+.", "Sara API traffic TLS 1.2+ se encrypted hai.",       "सारा API ट्रैफ़िक TLS 1.2+ से एन्क्रिप्टेड है।"],
  lg_s5_b2:           ["Passwords are hashed with scrypt (never stored in plain text).","Passwords scrypt se hashed hote hain (kabhi plain text me store nahi hote).","पासवर्ड scrypt से हैश किए जाते हैं (कभी प्लेन टेक्स्ट में संग्रहीत नहीं)।"],
  lg_s5_b3:           ["API access requires a per-user API key validated on every request.","API access har request par per-user API key validate karta hai.","API पहुँच के लिए हर अनुरोध पर प्रति-उपयोगकर्ता API key सत्यापित होती है।"],
  lg_s5_b4:           ["Database backups are encrypted at rest.",     "Database backups rest par encrypted hote hain.",    "डेटाबेस बैकअप विश्राम पर एन्क्रिप्टेड हैं।"],
  lg_s5_b5:           ["Access to production data is restricted to authorised engineers.","Production data ka access sirf authorised engineers tak limited hai.","प्रोडक्शन डेटा तक पहुँच केवल अधिकृत इंजीनियरों तक सीमित है।"],

  lg_s6_title:        ["6. Your Rights",                              "6. Aapke Rights",                                   "6. आपके अधिकार"],
  lg_s6_intro:        ["Under the Digital Personal Data Protection Act, 2023 (India) and comparable laws, you have the right to:","Digital Personal Data Protection Act, 2023 (India) aur similar laws ke under, aapke paas ye rights hain:","Digital Personal Data Protection Act, 2023 (भारत) और समान कानूनों के तहत, आपके पास ये अधिकार हैं:"],
  lg_s6_b1:           ["Access the personal data we hold about you.", "Hum aapke baare me jo personal data rakhte hain use access karna.","आपके बारे में हमारे पास मौजूद व्यक्तिगत डेटा तक पहुँच।"],
  lg_s6_b2:           ["Correct inaccurate or outdated information.", "Galat ya purani information correct karna.",        "ग़लत या पुरानी जानकारी सुधारना।"],
  lg_s6_b3:           ["Withdraw consent and delete your account.",   "Consent withdraw karna aur account delete karna.",  "सहमति वापस लेना और खाता हटाना।"],
  lg_s6_b4:           ["Receive an export of your kundli data in JSON format.","Apni kundli data ka JSON format me export lena.","अपनी कुंडली डेटा का JSON प्रारूप में निर्यात प्राप्त करना।"],
  lg_s6_b5:           ["Lodge a complaint with the Data Protection Board of India.","Data Protection Board of India me shikayat darj karwana.","भारत के डेटा प्रोटेक्शन बोर्ड में शिकायत दर्ज करना।"],
  lg_s6_outro:        ["To exercise any of these rights, email us at support@cosmiclens.app.","In rights ka istemal karne ke liye, support@cosmiclens.app par email karein.","इनमें से किसी अधिकार का प्रयोग करने के लिए, support@cosmiclens.app पर ईमेल करें।"],

  lg_s7_title:        ["7. Account Deletion",                         "7. Account Delete karna",                           "7. खाता हटाना"],
  lg_s7_p:            ["You can delete your account at any time from Profile → Delete Account. Deletion is permanent and removes all profiles, kundlis, chat history, and personal data within 30 days.","Aap kabhi bhi Profile → Delete Account se account delete kar sakte ho. Deletion permanent hai aur 30 din ke andar saari profiles, kundlis, chat history aur personal data hata deta hai.","आप कभी भी Profile → Delete Account से खाता हटा सकते हैं। हटाना स्थायी है और 30 दिन के भीतर सभी प्रोफ़ाइल, कुंडलियाँ, चैट इतिहास और व्यक्तिगत डेटा हटा देता है।"],

  lg_s8_title:        ["8. Children",                                 "8. Bachche",                                        "8. बच्चे"],
  lg_s8_p:            ["Cosmic Lens is not directed to children under 13. We do not knowingly collect personal data from children. If you believe a child has created an account, please contact us and we will delete it promptly.","Cosmic Lens 13 saal se kam ke bachchon ke liye nahi hai. Hum jaan-bujhkar bachchon ka personal data collect nahi karte. Agar lagta hai kisi bachche ne account banaya hai, hamse contact karein, hum turant delete kar denge.","Cosmic Lens 13 वर्ष से कम के बच्चों के लिए नहीं है। हम जानबूझकर बच्चों का व्यक्तिगत डेटा एकत्र नहीं करते। यदि किसी बच्चे ने खाता बनाया है, हमसे संपर्क करें, हम तुरंत हटा देंगे।"],

  lg_s9_title:        ["9. International Users",                      "9. International Users",                            "9. अंतर्राष्ट्रीय उपयोगकर्ता"],
  lg_s9_p:            ["Cosmic Lens is operated from India. If you access the Service from outside India, your information will be transferred to and processed in India where data-protection laws may differ from your country.","Cosmic Lens India se operate hota hai. Agar aap Service ko India ke bahar se access karte ho, aapki information India me transfer aur process hogi, jahan data-protection laws aapke desh se alag ho sakte hain.","Cosmic Lens भारत से संचालित है। यदि आप भारत के बाहर से Service उपयोग करते हैं, तो आपकी जानकारी भारत में स्थानांतरित और संसाधित होगी, जहाँ डेटा-संरक्षण कानून आपके देश से भिन्न हो सकते हैं।"],

  lg_s10_title:       ["10. Changes to This Policy",                  "10. Is Policy me Badlav",                           "10. इस नीति में परिवर्तन"],
  lg_s10_p:           ["We may update this Privacy Policy from time to time. The \"Last updated\" date at the top will reflect the most recent changes. Material changes will be communicated in-app at least 7 days in advance.","Hum is Privacy Policy ko samay-samay par update kar sakte hain. Top par \"Last updated\" date latest changes dikhayegi. Material changes in-app me kam se kam 7 din pehle batayi jaayengi.","हम इस गोपनीयता नीति को समय-समय पर अपडेट कर सकते हैं। शीर्ष पर \"अंतिम अद्यतन\" तिथि नवीनतम परिवर्तन दिखाएगी। महत्वपूर्ण परिवर्तन ऐप में कम से कम 7 दिन पहले बताए जाएँगे।"],

  lg_s11_title:       ["11. Contact Us",                              "11. Humse Contact karein",                          "11. हमसे संपर्क करें"],
  lg_s11_intro:       ["For privacy-related questions, requests, or grievances:","Privacy se related questions, requests ya grievances ke liye:","गोपनीयता-संबंधी प्रश्न, अनुरोध या शिकायतों के लिए:"],
  lg_s11_b1:          ["Email: support@cosmiclens.app",               "Email: support@cosmiclens.app",                     "ईमेल: support@cosmiclens.app"],
  lg_s11_b2:          ["Grievance Officer: Available within 30 days of complaint receipt","Grievance Officer: shikayat milne ke 30 din ke andar uplabdh","शिकायत अधिकारी: शिकायत प्राप्ति के 30 दिन के भीतर उपलब्ध"],

  // ── Terms of Service ──
  lg_h_terms:         ["Terms of Service",                            "Terms of Service",                                  "सेवा की शर्तें"],
  lg_p_termsIntro:    ["These Terms of Service (\"Terms\") govern your access to and use of the Cosmic Lens mobile application and related services (the \"Service\"). By creating an account, downloading, or using the Service, you accept these Terms. If you do not agree, please do not use the Service.","Ye Terms of Service (\"Terms\") Cosmic Lens mobile application aur related services (\"Service\") ke aapke access aur use ko govern karti hain. Account banakar, download karke ya Service use karke aap in Terms ko accept karte ho. Agar sahmat nahi ho, to Service istemal na karein.","ये Terms of Service (\"शर्तें\") Cosmic Lens मोबाइल ऐप और संबंधित सेवाओं (\"सेवा\") तक आपकी पहुँच और उपयोग को नियंत्रित करती हैं। खाता बनाकर, डाउनलोड करके या सेवा उपयोग करके आप इन शर्तों को स्वीकार करते हैं। यदि सहमत नहीं हैं, तो कृपया सेवा का उपयोग न करें।"],

  lg_t1_title:        ["1. Eligibility",                              "1. Eligibility",                                    "1. पात्रता"],
  lg_t1_b1:           ["You must be at least 13 years old to use Cosmic Lens.","Cosmic Lens use karne ke liye aap kam se kam 13 saal ke hone chahiye.","Cosmic Lens उपयोग के लिए आप कम से कम 13 वर्ष के होने चाहिए।"],
  lg_t1_b2:           ["If you are under 18, you must have permission from a parent or guardian.","Agar 18 saal se kam ho, to maa-baap ya guardian ki permission honi chahiye.","यदि 18 वर्ष से कम हैं, तो माता-पिता या अभिभावक की अनुमति होनी चाहिए।"],
  lg_t1_b3:           ["You confirm that the information you provide (name, date, time, place of birth) is true and accurate. Inaccurate birth data will produce inaccurate astrological results.","Aap confirm karte hain ki di gayi information (naam, janma tithi, samay, sthal) sahi aur accurate hai. Galat birth data se galat astrological results milenge.","आप पुष्टि करते हैं कि आपके द्वारा दी गई जानकारी (नाम, जन्म तिथि, समय, स्थान) सत्य और सटीक है। ग़लत जन्म डेटा से ग़लत ज्योतिषीय परिणाम मिलेंगे।"],

  lg_t2_title:        ["2. Account & Security",                       "2. Account aur Security",                           "2. खाता और सुरक्षा"],
  lg_t2_b1:           ["You are responsible for keeping your login credentials safe.","Login credentials safe rakhne ki zimmedari aapki hai.","लॉगिन क्रेडेंशियल सुरक्षित रखने की ज़िम्मेदारी आपकी है।"],
  lg_t2_b2:           ["You may not share your account or use someone else's account.","Aap apna account share nahi kar sakte ya kisi aur ka account use nahi kar sakte.","आप अपना खाता साझा नहीं कर सकते या किसी और का खाता उपयोग नहीं कर सकते।"],
  lg_t2_b3:           ["Notify us immediately of any unauthorised access.","Kisi bhi unauthorised access ke baare me hamein turant batayein.","किसी भी अनधिकृत पहुँच के बारे में हमें तुरंत सूचित करें।"],
  lg_t2_b4:           ["We reserve the right to suspend accounts engaged in fraud, abuse, or violation of these Terms.","Hum un accounts ko suspend karne ka right rakhte hain jo fraud, abuse ya in Terms ka violation karte hain.","हम उन खातों को निलंबित करने का अधिकार रखते हैं जो धोखाधड़ी, दुरुपयोग या इन शर्तों के उल्लंघन में संलग्न हैं।"],

  lg_t3_title:        ["3. The Service",                              "3. Service",                                        "3. सेवा"],
  lg_t3_p:            ["Cosmic Lens provides Vedic-astrology computations including kundli, dashas, doshas, marriage compatibility, panchang, muhurat, numerology, vastu, lucky elements, and Jyotish-based question answering. Calculations follow traditional Vedic principles (Lahiri ayanamsa) using accurate ephemeris data.","Cosmic Lens Vedic-astrology computations deta hai jaise kundli, dashas, doshas, vivah compatibility, panchang, muhurat, numerology, vastu, lucky elements, aur Jyotish-based question answering. Calculations traditional Vedic principles (Lahiri ayanamsa) follow karte hain accurate ephemeris data ke saath.","Cosmic Lens वैदिक-ज्योतिष गणनाएँ देता है — कुंडली, दशाएँ, दोष, विवाह अनुकूलता, पंचांग, मुहूर्त, अंक ज्योतिष, वास्तु, शुभ तत्व और ज्योतिष-आधारित प्रश्नोत्तर। गणनाएँ पारंपरिक वैदिक सिद्धांतों (लाहिरी अयनांश) का सटीक एफेमेरिस डेटा के साथ पालन करती हैं।"],

  lg_t4_title:        ["4. Subscription Plans",                       "4. Subscription Plans",                             "4. सदस्यता योजनाएँ"],
  lg_t4_intro:        ["Cosmic Lens offers the following plans:",     "Cosmic Lens ye plans deta hai:",                    "Cosmic Lens निम्न योजनाएँ प्रदान करता है:"],
  lg_t4_b1:           ["Free — limited features, 1 Jyotish question/day","Free — limited features, 1 Jyotish question/din","Free — सीमित सुविधाएँ, 1 ज्योतिष प्रश्न/दिन"],
  lg_t4_b2:           ["7-day Free Trial — Basic features for new users, one-time only, no payment required","7-din Free Trial — naye users ke liye Basic features, ek baar, koi payment nahi","7-दिवसीय फ़्री ट्रायल — नए उपयोगकर्ताओं के लिए Basic सुविधाएँ, एकमात्र, कोई भुगतान नहीं"],
  lg_t4_b3:           ["Basic — ₹199/month or ₹1,799/year, includes 10 Jyotish questions/day and basic analysis","Basic — ₹199/maah ya ₹1,799/saal, 10 Jyotish questions/din aur basic analysis","Basic — ₹199/माह या ₹1,799/वर्ष, 10 ज्योतिष प्रश्न/दिन और बुनियादी विश्लेषण"],
  lg_t4_b4:           ["Pro — ₹399/month or ₹2,999/year, includes unlimited Jyotish questions, full deep analysis, 6-month timeline, karmic insights, PDF reports","Pro — ₹399/maah ya ₹2,999/saal, unlimited Jyotish questions, full deep analysis, 6-maah timeline, karmic insights, PDF reports","Pro — ₹399/माह या ₹2,999/वर्ष, असीमित ज्योतिष प्रश्न, पूर्ण गहन विश्लेषण, 6-माह टाइमलाइन, कार्मिक अंतर्दृष्टि, PDF रिपोर्ट"],
  lg_t4_outro:        ["Subscriptions auto-renew at the end of each billing period unless cancelled at least 24 hours before renewal. You can cancel any time from Profile → Subscription → Cancel or by contacting support.","Subscriptions har billing period ke end par auto-renew hoti hain, jab tak renewal se kam se kam 24 ghante pehle cancel na ki jaayein. Aap Profile → Subscription → Cancel se ya support se contact karke kabhi bhi cancel kar sakte ho.","सदस्यताएँ हर बिलिंग अवधि के अंत में स्वतः नवीनीकृत होती हैं, जब तक नवीनीकरण से कम से कम 24 घंटे पहले रद्द न की जाएँ। आप Profile → Subscription → Cancel से या सहायता से संपर्क करके कभी भी रद्द कर सकते हैं।"],

  lg_t5_title:        ["5. Payments",                                 "5. Payments",                                       "5. भुगतान"],
  lg_t5_p:            ["Payments are processed by Cashfree Payments. By making a purchase you agree to Cashfree's terms in addition to ours. All prices are in Indian Rupees (₹) and inclusive of applicable GST.","Payments Cashfree Payments dwara process hote hain. Purchase karke aap hamari aur Cashfree dono ki terms se sahmat hote ho. Saari prices Indian Rupees (₹) me hain aur applicable GST sahit.","भुगतान Cashfree Payments द्वारा संसाधित होते हैं। खरीदारी करके आप हमारी और Cashfree दोनों की शर्तों से सहमत होते हैं। सभी मूल्य भारतीय रुपये (₹) में और लागू GST सहित हैं।"],

  lg_t6_title:        ["6. Refund Policy",                            "6. Refund Policy",                                  "6. रिफंड नीति"],
  lg_t6_p:            ["Please review our Refund & Cancellation section below for full details. In summary, all sales are generally final, but refunds may be granted for technical failures, double-charges, or unused service within 7 days of payment.","Poori details ke liye niche Refund & Cancellation section dekhein. Summary me, saari sales generally final hain, lekin technical failures, double-charges ya payment ke 7 din ke andar unused service ke liye refunds mil sakte hain.","कृपया पूर्ण विवरण के लिए नीचे रिफंड एवं रद्दीकरण अनुभाग देखें। सारांश में, सभी बिक्री सामान्यतः अंतिम हैं, लेकिन तकनीकी विफलताओं, दोहरे शुल्कों या भुगतान के 7 दिनों के भीतर अप्रयुक्त सेवा के लिए रिफंड दिए जा सकते हैं।"],

  lg_t7_title:        ["7. User Conduct — You agree NOT to",          "7. User Conduct — Aap NAHI karenge",                "7. उपयोगकर्ता आचरण — आप ये नहीं करेंगे"],
  lg_t7_b1:           ["Use the Service for any illegal or fraudulent purpose.","Service ka koi illegal ya fraudulent kaam ke liye use karna.","सेवा का कोई अवैध या धोखाधड़ी उद्देश्य के लिए उपयोग।"],
  lg_t7_b2:           ["Reverse-engineer, decompile, or scrape the Service.","Service ko reverse-engineer, decompile ya scrape karna.","सेवा को रिवर्स-इंजीनियर, डीकंपाइल या स्क्रैप करना।"],
  lg_t7_b3:           ["Use bots, scripts, or automated tools to abuse free or trial features.","Bots, scripts ya automated tools se free ya trial features ka galat istemal karna.","फ़्री या ट्रायल सुविधाओं के दुरुपयोग के लिए बॉट्स, स्क्रिप्ट्स या स्वचालित उपकरण।"],
  lg_t7_b4:           ["Resell, sublicense, or republish content from the Service.","Service ka content resell, sublicense ya republish karna.","सेवा से सामग्री को पुनः बेचना, सबलाइसेंस या पुनः प्रकाशित करना।"],
  lg_t7_b5:           ["Submit false birth data on behalf of another person without consent.","Bina consent ke kisi aur ke birth data ko galat tarah submit karna.","सहमति के बिना किसी अन्य व्यक्ति के झूठे जन्म डेटा प्रस्तुत करना।"],
  lg_t7_b6:           ["Harass, threaten, or impersonate others.",    "Doosron ko harass, threaten ya impersonate karna.","दूसरों को परेशान, धमकाना या प्रतिरूपण करना।"],

  lg_t8_title:        ["8. Intellectual Property",                    "8. Intellectual Property",                          "8. बौद्धिक संपदा"],
  lg_t8_p:            ["All content, design, code, branding, algorithms, and computed reports in the Service are the intellectual property of Cosmic Lens or its licensors. You receive a limited, non-exclusive, non-transferable licence to use the Service for personal, non-commercial purposes only.","Service me saara content, design, code, branding, algorithms aur computed reports Cosmic Lens ya uske licensors ki intellectual property hain. Aapko sirf personal, non-commercial use ke liye limited, non-exclusive, non-transferable licence milta hai.","सेवा में सभी सामग्री, डिज़ाइन, कोड, ब्रांडिंग, एल्गोरिदम और गणित रिपोर्ट Cosmic Lens या इसके लाइसेंसकर्ताओं की बौद्धिक संपदा हैं। आपको केवल व्यक्तिगत, गैर-वाणिज्यिक उपयोग के लिए सीमित, गैर-अनन्य, गैर-हस्तांतरणीय लाइसेंस मिलता है।"],

  lg_t9_title:        ["9. Engine-Generated Answers",                 "9. Engine-Generated Answers",                       "9. इंजन-जनित उत्तर"],
  lg_t9_p:            ["The \"Ask\" feature uses rule-based and generative analysis of your kundli. Jyotish answers are produced by software and may contain errors, ambiguities, or contradictions. They are NOT a substitute for professional advice.","\"Ask\" feature aapki kundli ka rule-based aur generative analysis use karta hai. Jyotish answers software dwara banaye jaate hain aur unme errors, ambiguities ya contradictions ho sakte hain. Ye professional advice ka substitute NAHI hain.","\"Ask\" सुविधा आपकी कुंडली का नियम-आधारित और जनरेटिव विश्लेषण उपयोग करती है। ज्योतिष उत्तर सॉफ़्टवेयर द्वारा उत्पन्न होते हैं और उनमें त्रुटियाँ, अस्पष्टताएँ या विरोधाभास हो सकते हैं। वे पेशेवर सलाह का विकल्प नहीं हैं।"],

  lg_t10_title:       ["10. No Professional Advice",                  "10. Professional Advice nahi hai",                  "10. कोई पेशेवर सलाह नहीं"],
  lg_t10_callout:     ["Cosmic Lens is for spiritual and entertainment purposes only. Astrological insights are NOT a substitute for professional medical, legal, financial, psychological, or relationship advice. Always consult qualified professionals for important life decisions.","Cosmic Lens sirf spiritual aur entertainment purposes ke liye hai. Astrological insights professional medical, legal, financial, psychological ya relationship advice ka substitute NAHI hain. Important life decisions ke liye hamesha qualified professionals se consult karein.","Cosmic Lens केवल आध्यात्मिक और मनोरंजन उद्देश्यों के लिए है। ज्योतिषीय अंतर्दृष्टि पेशेवर चिकित्सा, क़ानूनी, वित्तीय, मनोवैज्ञानिक या संबंध सलाह का विकल्प नहीं है। महत्वपूर्ण जीवन निर्णयों के लिए हमेशा योग्य पेशेवरों से परामर्श करें।"],

  lg_t11_title:       ["11. Disclaimers",                             "11. Disclaimers",                                   "11. अस्वीकरण"],
  lg_t11_p:           ["The Service is provided \"as is\" and \"as available\" without warranties of any kind, express or implied. We do not guarantee that astrological predictions will come true, that the Service will be error-free, or that it will be available at all times. Past performance of any prediction does not indicate future results.","Service \"as is\" aur \"as available\" ke roop me di jaati hai, koi express ya implied warranties ke bina. Hum guarantee nahi dete ki astrological predictions sach hongi, Service error-free hogi ya hamesha available hogi. Kisi prediction ki past performance future results indicate nahi karti.","सेवा \"जैसी है\" और \"जैसी उपलब्ध है\" के रूप में बिना किसी प्रत्यक्ष या निहित वारंटी के प्रदान की जाती है। हम गारंटी नहीं देते कि ज्योतिषीय भविष्यवाणियाँ सच होंगी, सेवा त्रुटि-मुक्त होगी या हमेशा उपलब्ध होगी। किसी भविष्यवाणी का पिछला प्रदर्शन भविष्य के परिणामों का संकेत नहीं देता।"],

  lg_t12_title:       ["12. Limitation of Liability",                 "12. Liability ki Seema",                            "12. दायित्व की सीमा"],
  lg_t12_p:           ["To the maximum extent permitted by law, Cosmic Lens, its officers, employees, and partners shall not be liable for any indirect, incidental, consequential, or punitive damages arising from your use of the Service. Our total liability for any claim is limited to the amount you paid us in the 12 months preceding the claim, or ₹1,000, whichever is greater.","Law dwara maximum extent tak, Cosmic Lens, iske officers, employees aur partners aapke Service use se utpann kisi indirect, incidental, consequential ya punitive damages ke liye liable nahi honge. Kisi claim ke liye hamari total liability claim se 12 maah pehle aapne hamein jo paid kiya, ya ₹1,000, jo zyada ho, tak limited hai.","कानून द्वारा अधिकतम सीमा तक, Cosmic Lens, इसके अधिकारी, कर्मचारी और भागीदार आपके सेवा उपयोग से उत्पन्न किसी अप्रत्यक्ष, आकस्मिक, परिणामी या दंडात्मक हानि के लिए उत्तरदायी नहीं होंगे। किसी दावे के लिए हमारी कुल देयता दावे से 12 माह पहले आपने हमें भुगतान की राशि, या ₹1,000, जो भी अधिक हो, तक सीमित है।"],

  lg_t13_title:       ["13. Termination",                             "13. Termination",                                   "13. समाप्ति"],
  lg_t13_p:           ["You may stop using the Service at any time by deleting your account. We may suspend or terminate your access immediately if you violate these Terms or engage in conduct harmful to other users or the Service.","Aap kabhi bhi account delete karke Service use karna band kar sakte ho. Agar aap in Terms ka violation karte ho ya doosre users ya Service ke liye harmful conduct karte ho, hum aapka access turant suspend ya terminate kar sakte hain.","आप कभी भी खाता हटाकर सेवा का उपयोग बंद कर सकते हैं। यदि आप इन शर्तों का उल्लंघन करते हैं या अन्य उपयोगकर्ताओं या सेवा के लिए हानिकारक आचरण में संलग्न होते हैं, तो हम आपकी पहुँच तुरंत निलंबित या समाप्त कर सकते हैं।"],

  lg_t14_title:       ["14. Changes to Terms",                        "14. Terms me Badlav",                               "14. शर्तों में परिवर्तन"],
  lg_t14_p:           ["We may update these Terms periodically. Continued use of the Service after changes become effective constitutes acceptance of the new Terms. Material changes will be notified in-app at least 7 days in advance.","Hum in Terms ko periodically update kar sakte hain. Changes effective hone ke baad Service use jaari rakhna nayi Terms ka acceptance maana jaayega. Material changes in-app me kam se kam 7 din pehle notify ki jaayengi.","हम इन शर्तों को समय-समय पर अपडेट कर सकते हैं। परिवर्तन प्रभावी होने के बाद सेवा का निरंतर उपयोग नई शर्तों की स्वीकृति माना जाएगा। महत्वपूर्ण परिवर्तन ऐप में कम से कम 7 दिन पहले सूचित किए जाएँगे।"],

  lg_t15_title:       ["15. Governing Law & Jurisdiction",            "15. Governing Law aur Jurisdiction",                "15. शासी क़ानून और क्षेत्राधिकार"],
  lg_t15_p:           ["These Terms are governed by the laws of India. Any disputes arising out of or related to these Terms or the Service shall be subject to the exclusive jurisdiction of the courts in your registered city, India.","Ye Terms India ke laws se govern hoti hain. In Terms ya Service se utpann ya related koi bhi disputes aapke registered city, India ke courts ke exclusive jurisdiction me honge.","ये शर्तें भारत के कानूनों द्वारा शासित हैं। इन शर्तों या सेवा से उत्पन्न या संबंधित कोई भी विवाद आपके पंजीकृत शहर, भारत के न्यायालयों के विशेष क्षेत्राधिकार के अधीन होंगे।"],

  lg_t16_title:       ["16. Contact",                                 "16. Contact",                                       "16. संपर्क"],
  lg_t16_p:           ["For questions about these Terms, email support@cosmiclens.app.","In Terms ke baare me sawaalon ke liye, support@cosmiclens.app par email karein.","इन शर्तों के बारे में प्रश्नों के लिए, support@cosmiclens.app पर ईमेल करें।"],

  // ── Refund & Cancellation ──
  lg_h_refund:        ["Refund & Cancellation",                       "Refund aur Cancellation",                           "रिफंड और रद्दीकरण"],
  lg_p_refundIntro:   ["At Cosmic Lens we want every member to have a great experience. This policy explains when subscription fees are refundable and how to cancel your subscription.","Cosmic Lens me hum chahte hain har member ka achha experience ho. Ye policy bataati hai ki subscription fees kab refundable hain aur subscription kaise cancel karein.","Cosmic Lens में हम चाहते हैं हर सदस्य का अच्छा अनुभव हो। यह नीति बताती है कि सदस्यता शुल्क कब रिफंडेबल हैं और सदस्यता कैसे रद्द करें।"],
  lg_callout_refund:  ["Use the 7-day Free Trial before subscribing — it lets you experience Basic features at no cost so you can decide before paying.","Subscribe karne se pehle 7-day Free Trial use karein — ye aapko Basic features ka experience bina koi cost ke deta hai, taaki paise dene se pehle aap decide kar sako.","सदस्यता लेने से पहले 7-दिवसीय फ़्री ट्रायल का उपयोग करें — यह आपको Basic सुविधाओं का अनुभव बिना कोई शुल्क के देता है ताकि भुगतान से पहले आप निर्णय ले सकें।"],

  lg_r1_title:        ["1. Subscription Cancellation",                "1. Subscription Cancellation",                      "1. सदस्यता रद्दीकरण"],
  lg_r1_intro:        ["You can cancel your monthly or yearly subscription at any time:","Aap monthly ya yearly subscription kabhi bhi cancel kar sakte ho:","आप मासिक या वार्षिक सदस्यता कभी भी रद्द कर सकते हैं:"],
  lg_r1_b1:           ["Open Profile → Subscription and tap \"Cancel Subscription\".","Profile → Subscription kholein aur \"Cancel Subscription\" tap karein.","Profile → Subscription खोलें और \"Cancel Subscription\" टैप करें।"],
  lg_r1_b2:           ["Or email support@cosmiclens.app from your registered email.","Ya apni registered email se support@cosmiclens.app par email karein.","या अपनी पंजीकृत ईमेल से support@cosmiclens.app पर ईमेल करें।"],
  lg_r1_outro:        ["After cancellation, you keep premium access until the end of the current billing period. No further charges will be made.","Cancellation ke baad current billing period ke end tak premium access milta rahega. Aage koi charges nahi liye jaayenge.","रद्दीकरण के बाद, वर्तमान बिलिंग अवधि के अंत तक प्रीमियम पहुँच बनी रहेगी। आगे कोई शुल्क नहीं लिया जाएगा।"],

  lg_r2_title:        ["2. When Refunds Are Granted",                 "2. Refunds kab milte hain",                         "2. रिफंड कब दिए जाते हैं"],
  lg_r2_intro:        ["We will issue a full or pro-rated refund in these situations:","In situations me hum full ya pro-rated refund denge:","इन स्थितियों में हम पूर्ण या आनुपातिक रिफंड देंगे:"],
  lg_r2_b1:           ["Double charge / duplicate payment — full refund of the duplicate amount, processed within 5–7 business days.","Double charge / duplicate payment — duplicate amount ka full refund, 5–7 business days me process.","दोहरा शुल्क / डुप्लीकेट भुगतान — डुप्लीकेट राशि का पूर्ण रिफंड, 5–7 कार्य दिवसों में संसाधित।"],
  lg_r2_b2:           ["Payment succeeded but plan not activated — full refund or manual plan activation, your choice.","Payment successful par plan activate nahi hua — full refund ya manual plan activation, aapki choice.","भुगतान सफल पर प्लान सक्रिय नहीं हुआ — पूर्ण रिफंड या मैन्युअल प्लान सक्रियण, आपकी पसंद।"],
  lg_r2_b3:           ["Technical failure preventing access for more than 72 hours — pro-rated refund for unused days.","Technical failure jiski wajah se 72 ghante se zyada access nahi mila — unused days ka pro-rated refund.","तकनीकी विफलता जो 72 घंटे से अधिक पहुँच रोकती है — अप्रयुक्त दिनों का आनुपातिक रिफंड।"],
  lg_r2_b4:           ["Cancellation within 7 days of first paid subscription if you have used fewer than 5 paid features — full refund (one-time per user).","Pehle paid subscription ke 7 din ke andar cancellation, agar 5 se kam paid features use kiye hain — full refund (per user ek baar).","पहली सशुल्क सदस्यता के 7 दिनों के भीतर रद्द करने पर यदि 5 से कम सशुल्क सुविधाएँ उपयोग की हैं — पूर्ण रिफंड (प्रति उपयोगकर्ता एक बार)।"],

  lg_r3_title:        ["3. When Refunds Are NOT Granted",             "3. Refunds kab NAHI milte",                         "3. रिफंड कब नहीं दिए जाते"],
  lg_r3_b1:           ["Change of mind after the 7-day window.",      "7-din window ke baad change of mind.",              "7-दिन की अवधि के बाद विचार बदलना।"],
  lg_r3_b2:           ["Astrological prediction did not come true — predictions are interpretive guidance, not guarantees (see Disclaimer).","Astrological prediction sach nahi nikli — predictions interpretive guidance hain, guarantee nahi (Disclaimer dekho).","ज्योतिषीय भविष्यवाणी सच नहीं हुई — भविष्यवाणियाँ व्याख्यात्मक मार्गदर्शन हैं, गारंटी नहीं (अस्वीकरण देखें)।"],
  lg_r3_b3:           ["You forgot to cancel before auto-renewal — but we will cancel future renewals immediately on request.","Auto-renewal se pehle cancel karna bhool gaye — par hum request par future renewals turant cancel kar denge.","ऑटो-नवीनीकरण से पहले रद्द करना भूल गए — परंतु हम अनुरोध पर भविष्य के नवीनीकरण तुरंत रद्द कर देंगे।"],
  lg_r3_b4:           ["Partial-month refunds for monthly plans cancelled mid-cycle.","Mid-cycle me cancel ki gayi monthly plans ke partial-month refunds.","मासिक योजनाओं के मध्य-चक्र में रद्द होने पर आंशिक-माह रिफंड।"],
  lg_r3_b5:           ["Refunds for the Free or Trial plans (no payment was made).","Free ya Trial plans ke refunds (koi payment hi nahi hua).","Free या Trial योजनाओं के लिए रिफंड (कोई भुगतान नहीं हुआ था)।"],
  lg_r3_b6:           ["Refunds requested more than 30 days after payment.","Payment ke 30 din se zyada baad refund request.","भुगतान के 30 दिनों के बाद अनुरोधित रिफंड।"],

  lg_r4_title:        ["4. How to Request a Refund",                  "4. Refund Request Kaise Karein",                    "4. रिफंड का अनुरोध कैसे करें"],
  lg_r4_intro:        ["Email support@cosmiclens.app with:",          "support@cosmiclens.app par ye saath bhejein:",      "support@cosmiclens.app पर इसके साथ ईमेल करें:"],
  lg_r4_b1:           ["Your registered email address or mobile number","Aapki registered email address ya mobile number","आपका पंजीकृत ईमेल पता या मोबाइल नंबर"],
  lg_r4_b2:           ["The order ID (visible in Profile → Subscription → Payment History)","Order ID (Profile → Subscription → Payment History me dikhti hai)","ऑर्डर ID (Profile → Subscription → Payment History में दिखती है)"],
  lg_r4_b3:           ["Reason for the refund request",               "Refund request ka reason",                          "रिफंड अनुरोध का कारण"],
  lg_r4_outro:        ["We respond to all refund requests within 3 business days. Approved refunds are processed by Cashfree to your original payment method within 5–10 business days.","Hum saari refund requests ka 3 business days me jawab dete hain. Approved refunds Cashfree dwara aapke original payment method par 5–10 business days me process hote hain.","हम सभी रिफंड अनुरोधों का 3 कार्य दिवसों के भीतर उत्तर देते हैं। स्वीकृत रिफंड Cashfree द्वारा आपकी मूल भुगतान विधि पर 5–10 कार्य दिवसों में संसाधित होते हैं।"],

  lg_r5_title:        ["5. Failed Payments",                          "5. Failed Payments",                                "5. विफल भुगतान"],
  lg_r5_p:            ["If a payment fails, no charge is made. If your bank shows a \"pending\" charge, it is automatically reversed within 5–7 business days per RBI guidelines. You do not need to contact us for these.","Agar payment fail ho jaaye, koi charge nahi hota. Agar bank \"pending\" charge dikhata hai, to RBI guidelines ke according 5–7 business days me automatically reverse ho jaata hai. Inke liye humse contact karne ki zaroorat nahi.","यदि कोई भुगतान विफल हो, तो कोई शुल्क नहीं लिया जाता। यदि बैंक \"लंबित\" शुल्क दिखाता है, तो RBI दिशानिर्देशों के अनुसार 5–7 कार्य दिवसों में स्वतः उलट जाता है। इनके लिए हमसे संपर्क करने की आवश्यकता नहीं है।"],

  lg_r6_title:        ["6. Subscription Auto-Renewal",                "6. Subscription Auto-Renewal",                      "6. सदस्यता ऑटो-नवीनीकरण"],
  lg_r6_p:            ["Monthly and yearly plans renew automatically. We will send a reminder via email or in-app notification before each renewal. To stop renewal, simply cancel before the renewal date — no action will be charged.","Monthly aur yearly plans automatically renew hote hain. Hum har renewal se pehle email ya in-app notification se reminder bhejenge. Renewal rokne ke liye, bas renewal date se pehle cancel karein — koi charge nahi hoga.","मासिक और वार्षिक योजनाएँ स्वतः नवीनीकृत होती हैं। हम हर नवीनीकरण से पहले ईमेल या ऐप सूचना द्वारा रिमाइंडर भेजेंगे। नवीनीकरण रोकने के लिए, बस नवीनीकरण तिथि से पहले रद्द करें — कोई शुल्क नहीं लिया जाएगा।"],

  lg_r7_title:        ["7. Chargebacks",                              "7. Chargebacks",                                    "7. चार्जबैक"],
  lg_r7_p:            ["If you initiate a chargeback through your bank instead of contacting us first, your account will be suspended pending investigation. We always prefer to resolve issues directly — please email us first.","Agar aap pehle humse contact karne ki jagah seedha bank ke through chargeback initiate karte ho, to aapka account investigation pending suspend ho jaayega. Hum hamesha issues directly resolve karna prefer karte hain — pehle hamein email karein.","यदि आप पहले हमसे संपर्क करने के बजाय सीधे बैंक के माध्यम से चार्जबैक शुरू करते हैं, तो आपका खाता जाँच लंबित रहने तक निलंबित कर दिया जाएगा। हम हमेशा सीधे समस्याओं को हल करना पसंद करते हैं — पहले हमें ईमेल करें।"],

  lg_r8_title:        ["8. Contact for Refunds",                      "8. Refunds ke liye Contact",                        "8. रिफंड के लिए संपर्क"],
  lg_r8_b1:           ["Email: support@cosmiclens.app",               "Email: support@cosmiclens.app",                     "ईमेल: support@cosmiclens.app"],
  lg_r8_b2:           ["Subject line: \"Refund Request — [Order ID]\"","Subject line: \"Refund Request — [Order ID]\"",   "विषय पंक्ति: \"Refund Request — [Order ID]\""],
  lg_r8_b3:           ["Response time: within 3 business days",       "Response time: 3 business days me",                 "प्रतिक्रिया समय: 3 कार्य दिवसों के भीतर"],

  // ── Astrology Disclaimer ──
  lg_h_disclaimer:    ["Astrology Disclaimer",                        "Astrology Disclaimer",                              "ज्योतिष अस्वीकरण"],
  lg_callout_disc:    ["Cosmic Lens is intended for spiritual exploration, self-reflection, and entertainment purposes only. It is not a substitute for professional medical, legal, financial, psychological, or relationship advice.","Cosmic Lens sirf spiritual exploration, self-reflection aur entertainment purposes ke liye hai. Ye professional medical, legal, financial, psychological ya relationship advice ka substitute nahi hai.","Cosmic Lens केवल आध्यात्मिक अन्वेषण, आत्म-चिंतन और मनोरंजन उद्देश्यों के लिए है। यह पेशेवर चिकित्सा, क़ानूनी, वित्तीय, मनोवैज्ञानिक या संबंध सलाह का विकल्प नहीं है।"],

  lg_d1_title:        ["1. Nature of Astrology",                      "1. Astrology ka Swaroop",                           "1. ज्योतिष की प्रकृति"],
  lg_d1_p:            ["Vedic astrology (Jyotish) is an ancient art and philosophical tradition. The interpretations, predictions, dashas, doshas, muhurats, and remedies provided in Cosmic Lens reflect classical principles and modern algorithmic analysis. They are interpretive in nature and not scientifically verifiable.","Vedic astrology (Jyotish) ek pracheen kala aur philosophical parampara hai. Cosmic Lens me di gayi interpretations, predictions, dashas, doshas, muhurats aur remedies classical principles aur modern algorithmic analysis ko reflect karti hain. Ye nature me interpretive hain aur scientifically verifiable nahi hain.","वैदिक ज्योतिष (Jyotish) एक प्राचीन कला और दार्शनिक परंपरा है। Cosmic Lens में दी गई व्याख्याएँ, भविष्यवाणियाँ, दशाएँ, दोष, मुहूर्त और उपाय शास्त्रीय सिद्धांतों और आधुनिक एल्गोरिथमिक विश्लेषण को प्रतिबिंबित करते हैं। ये प्रकृति में व्याख्यात्मक हैं और वैज्ञानिक रूप से सत्यापन योग्य नहीं हैं।"],

  lg_d2_title:        ["2. No Guaranteed Outcomes",                   "2. Koi Guaranteed Outcomes nahi",                   "2. कोई गारंटीकृत परिणाम नहीं"],
  lg_d2_p:            ["No astrological prediction or insight is guaranteed to come true. Outcomes in life depend on many factors — your free will, choices, actions, environment, and circumstances — that astrology cannot fully capture.","Koi bhi astrological prediction ya insight sach hone ki guarantee nahi hai. Jeevan me outcomes kayi factors par depend karte hain — aapki free will, choices, actions, environment aur circumstances — jise astrology poori tarah nahi pakad sakti.","कोई भी ज्योतिषीय भविष्यवाणी या अंतर्दृष्टि सच होने की गारंटी नहीं देती। जीवन में परिणाम कई कारकों पर निर्भर करते हैं — आपकी स्वतंत्र इच्छा, विकल्प, कर्म, परिवेश और परिस्थितियाँ — जिन्हें ज्योतिष पूरी तरह नहीं पकड़ सकता।"],

  lg_d3_title:        ["3. Not a Substitute for Professionals",       "3. Professionals ka Substitute Nahi",               "3. पेशेवरों का विकल्प नहीं"],
  lg_d3_intro:        ["Cosmic Lens content must NEVER be used as the sole basis for important life decisions. Always consult appropriately qualified professionals:","Cosmic Lens content ko important life decisions ke liye sole basis ke roop me KABHI use nahi karna chahiye. Hamesha appropriate qualified professionals se consult karein:","Cosmic Lens सामग्री का उपयोग महत्वपूर्ण जीवन निर्णयों के एकमात्र आधार के रूप में कभी नहीं किया जाना चाहिए। हमेशा उपयुक्त योग्य पेशेवरों से परामर्श करें:"],
  lg_d3_b1:           ["Health concerns — see a registered medical doctor. Do not stop or alter medication based on astrological readings.","Health concerns — registered medical doctor se milein. Astrological readings ke aadhar par medication band ya badlein nahi.","स्वास्थ्य संबंधी चिंताएँ — पंजीकृत चिकित्सक से मिलें। ज्योतिषीय पठन के आधार पर दवा बंद या परिवर्तित न करें।"],
  lg_d3_b2:           ["Mental health — speak to a licensed psychologist or psychiatrist. If you are in crisis, call iCall (India) at 9152987821 or your local helpline.","Mental health — licensed psychologist ya psychiatrist se baat karein. Crisis me ho to iCall (India) 9152987821 ya apni local helpline call karein.","मानसिक स्वास्थ्य — लाइसेंस प्राप्त मनोवैज्ञानिक या मनोचिकित्सक से बात करें। यदि संकट में हैं, तो iCall (भारत) 9152987821 या अपनी स्थानीय हेल्पलाइन कॉल करें।"],
  lg_d3_b3:           ["Legal matters — consult a qualified lawyer.", "Legal matters — qualified lawyer se consult karein.","क़ानूनी मामले — योग्य वकील से परामर्श करें।"],
  lg_d3_b4:           ["Financial / investment decisions — consult a SEBI-registered investment advisor.","Financial / investment decisions — SEBI-registered investment advisor se consult karein.","वित्तीय / निवेश निर्णय — SEBI-पंजीकृत निवेश सलाहकार से परामर्श करें।"],
  lg_d3_b5:           ["Relationship & marriage — consult a counsellor; compatibility scores should never replace open communication and consent.","Relationship aur marriage — counsellor se consult karein; compatibility scores kabhi bhi open communication aur consent ko replace nahi karne chahiye.","संबंध और विवाह — काउंसलर से परामर्श करें; अनुकूलता स्कोर कभी भी खुले संवाद और सहमति का स्थान नहीं ले सकते।"],

  lg_d4_title:        ["4. Engine-Generated Content",                 "4. Engine-Generated Content",                       "4. इंजन-जनित सामग्री"],
  lg_d4_p:            ["The \"Ask\" feature uses automated software (rule-based engine) to analyse your kundli. Answers are generated by code and may contain errors, omissions, contradictions, or culturally inappropriate phrasing. They are not endorsed by any individual astrologer.","\"Ask\" feature aapki kundli analyse karne ke liye automated software (rule-based engine) use karta hai. Answers code dwara generate hote hain aur unme errors, omissions, contradictions ya culturally inappropriate phrasing ho sakti hai. Ye kisi individual astrologer dwara endorsed nahi hain.","\"Ask\" सुविधा आपकी कुंडली का विश्लेषण करने के लिए स्वचालित सॉफ़्टवेयर (नियम-आधारित इंजन) का उपयोग करती है। उत्तर कोड द्वारा उत्पन्न होते हैं और उनमें त्रुटियाँ, चूक, विरोधाभास या सांस्कृतिक रूप से अनुपयुक्त शब्दावली हो सकती है। ये किसी व्यक्तिगत ज्योतिषी द्वारा समर्थित नहीं हैं।"],

  lg_d5_title:        ["5. Remedies",                                 "5. Upay (Remedies)",                                "5. उपाय"],
  lg_d5_p:            ["Suggested remedies (mantras, gemstones, donations, fasting, pujas) are drawn from classical texts. We do not guarantee any specific result from following them. Consult a qualified Vedic astrologer or guru before adopting any remedy, especially gemstones and mantras with seed-syllables (beej mantras).","Suggest kiye gaye upay (mantras, ratan, daan, vrat, pujas) classical granthon se liye gaye hain. Inko follow karne se kisi specific result ki guarantee hum nahi dete. Koi bhi upay apnaane se pehle qualified Vedic astrologer ya guru se consult karein, khaaskar ratan aur beej mantras.","सुझाए गए उपाय (मंत्र, रत्न, दान, व्रत, पूजा) शास्त्रीय ग्रंथों से लिए गए हैं। उन्हें अपनाने से किसी विशिष्ट परिणाम की हम गारंटी नहीं देते। किसी भी उपाय को अपनाने से पहले किसी योग्य वैदिक ज्योतिषी या गुरु से परामर्श करें, विशेष रूप से रत्न और बीज मंत्र।"],

  lg_d6_title:        ["6. Birth-Data Accuracy",                      "6. Birth-Data Sahi hona",                           "6. जन्म-डेटा की सटीकता"],
  lg_d6_p:            ["Astrological calculations are highly sensitive to your time and place of birth. Even a 4-minute error in birth time can change your ascendant. We recommend verifying your birth time from a hospital record or birth certificate. Inaccurate input will produce inaccurate results.","Astrological calculations aapke janma samay aur sthal ke prati bahut sensitive hain. Sirf 4-minute ki error bhi aapka ascendant badal sakti hai. Hum recommend karte hain ki janma samay hospital record ya birth certificate se verify karein. Galat input se galat results aayenge.","ज्योतिषीय गणनाएँ आपके जन्म समय और स्थान के प्रति अत्यंत संवेदनशील हैं। केवल 4-मिनट की त्रुटि भी आपका लग्न बदल सकती है। हम सलाह देते हैं कि अस्पताल रिकॉर्ड या जन्म प्रमाण पत्र से जन्म समय सत्यापित करें। ग़लत इनपुट से ग़लत परिणाम उत्पन्न होंगे।"],

  lg_d7_title:        ["7. Cultural & Regional Differences",          "7. Cultural aur Regional Antar",                    "7. सांस्कृतिक और क्षेत्रीय भिन्नताएँ"],
  lg_d7_p:            ["Cosmic Lens uses traditional Vedic (Lahiri / Chitrapaksha) ayanamsa. Western, Tropical, KP, Krishnamurti, and Tantric astrologers may use different systems and arrive at different conclusions. None of these systems is \"wrong\" — they are different lenses.","Cosmic Lens traditional Vedic (Lahiri / Chitrapaksha) ayanamsa use karta hai. Western, Tropical, KP, Krishnamurti aur Tantric astrologers alag systems use kar sakte hain aur alag conclusions nikal sakte hain. Inme se koi bhi system \"galat\" nahi hai — ye alag lenses hain.","Cosmic Lens पारंपरिक वैदिक (लाहिरी / चित्रपक्ष) अयनांश का उपयोग करता है। पाश्चात्य, उष्णकटिबंधीय, KP, कृष्णमूर्ति और तांत्रिक ज्योतिषी विभिन्न प्रणालियों का उपयोग कर सकते हैं और भिन्न निष्कर्ष पर पहुँच सकते हैं। इनमें से कोई भी प्रणाली \"ग़लत\" नहीं है — ये भिन्न लेंस हैं।"],

  lg_d8_title:        ["8. Emergency Situations",                     "8. Emergency Situations",                           "8. आपातकालीन स्थितियाँ"],
  lg_d8_callout:      ["If you are experiencing a medical emergency or thoughts of self-harm, please call your local emergency services immediately. Do not rely on this app for crisis support. India: 112 (emergency), iCall 9152987821 (mental health).","Agar aap medical emergency ya self-harm ke vicharon ka anubhav kar rahe hain, kripaya turant apni local emergency services call karein. Crisis support ke liye is app par bharosa na karein. India: 112 (emergency), iCall 9152987821 (mental health).","यदि आप किसी चिकित्सा आपातकाल या आत्म-हानि के विचारों का अनुभव कर रहे हैं, कृपया तुरंत अपनी स्थानीय आपातकालीन सेवाओं को कॉल करें। संकट सहायता के लिए इस ऐप पर निर्भर न रहें। भारत: 112 (आपातकाल), iCall 9152987821 (मानसिक स्वास्थ्य)।"],

  lg_d9_title:        ["9. Acceptance",                               "9. Sweekriti",                                      "9. स्वीकृति"],
  lg_d9_p:            ["By using Cosmic Lens you acknowledge that you have read and understood this disclaimer and agree to use the Service responsibly.","Cosmic Lens use karke aap acknowledge karte hain ki aapne ye disclaimer padhi aur samjhi hai aur Service ko responsibly use karne ke liye sahmat hain.","Cosmic Lens का उपयोग करके आप स्वीकार करते हैं कि आपने यह अस्वीकरण पढ़ और समझ लिया है तथा सेवा का जिम्मेदारी से उपयोग करने हेतु सहमत हैं।"],

  // ════════════════════════════ business-vastu.tsx ════════════════════════════
  bv_headerTitle:     ["Business Vastu",                              "Business Vastu",                                    "बिज़नेस वास्तु"],
  bv_cardTitle:       ["Premium Business Vastu",                      "Premium Business Vastu",                            "प्रीमियम बिज़नेस वास्तु"],
  bv_cardBody:        ["Combine your premise layout with the owner Kundli + active Mahadasha to get a personalised, lifetime priority plan.","Apne premise layout ko owner Kundli aur active Mahadasha ke saath jodkar ek personalised lifetime priority plan paayein.","अपने स्थल लेआउट को स्वामी की कुंडली और चल रही महादशा के साथ मिलाकर एक व्यक्तिगत, आजीवन प्राथमिकता योजना प्राप्त करें।"],
  bv_cardBodySmall:   ["Aapke vyapar sthal ko swami ki Kundli aur chal rahi Mahadasha ke saath milakar ek vyaktigat sudhar yojana banayi jaati hai.","Aapke vyapar sthal ko swami ki Kundli aur chal rahi Mahadasha ke saath milakar ek vyaktigat sudhar yojana banayi jaati hai.","आपके व्यापार स्थल को स्वामी की कुंडली और चल रही महादशा के साथ मिलाकर एक व्यक्तिगत सुधार योजना बनाई जाती है।"],

  bv_secBizType:      ["Business Type",                               "Business Type",                                     "व्यवसाय प्रकार"],
  bv_secPremiseName:  ["Premise Name",                                "Sthal ka Naam",                                     "स्थल का नाम"],
  bv_phPremiseName:   ["e.g. Andheri Shop, Powai HQ",                 "jaise Andheri Shop, Powai HQ",                      "जैसे अंधेरी दुकान, पवई HQ"],
  bv_premiseHint:     ["Required — your one-time unlock is matched to this premise name.","Zaroori hai — aapka one-time unlock isi premise name se match hota hai.","आवश्यक — आपका एक-बार-अनलॉक इसी स्थल नाम से मिलाया जाता है।"],

  bv_refineRooms:     ["Optional: Refine Rooms",                      "Optional: Rooms Refine karein",                     "वैकल्पिक: रूम्स परिष्कृत करें"],
  bv_premiseLayout:   ["Premise Layout",                              "Sthal Layout",                                      "स्थल लेआउट"],
  bv_engineWillDetect:["Photo Engine will detect rooms from your upload. You can also list rooms here to override.","Photo Engine aapke upload se rooms detect karega. Aap yahan rooms list karke override bhi kar sakte ho.","Photo Engine आपके अपलोड से रूम्स पहचानेगा। आप यहाँ रूम्स सूचीबद्ध करके ओवरराइड भी कर सकते हैं।"],
  bv_lblDirection:    ["Direction:",                                  "Disha:",                                            "दिशा:"],
  bv_selectDirection: ["Select direction",                            "Disha chunein",                                     "दिशा चुनें"],
  bv_addRoom:         ["Add Room (★ = critical)",                     "Room joden (★ = critical)",                         "रूम जोड़ें (★ = महत्वपूर्ण)"],
  bv_runScanPrefix:   ["Run",                                         "Chalaayein",                                        "चलाएँ"],
  bv_runScanSuffix:   ["Vastu Scan",                                  "Vastu Scan",                                        "वास्तु स्कैन"],

  // Business types (BIZ_OPTIONS)
  bv_biz_shop:        ["Shop",                                        "Dukaan",                                            "दुकान"],
  bv_biz_office:      ["Office",                                      "Office",                                            "कार्यालय"],
  bv_biz_factory:     ["Factory",                                     "Karkhana",                                          "कारख़ाना"],

  // Direction options (DIRECTION_OPTIONS) — short codes are universal (N, NE, ...)
  bv_dir_N:           ["North",                                       "Uttar",                                             "उत्तर"],
  bv_dir_NE:          ["North-East",                                  "Ishan",                                             "ईशान"],
  bv_dir_E:           ["East",                                        "Poorv",                                             "पूर्व"],
  bv_dir_SE:          ["South-East",                                  "Agneya",                                            "आग्नेय"],
  bv_dir_S:           ["South",                                       "Dakshin",                                           "दक्षिण"],
  bv_dir_SW:          ["South-West",                                  "Nairutya",                                          "नैऋत्य"],
  bv_dir_W:           ["West",                                        "Paschim",                                           "पश्चिम"],
  bv_dir_NW:          ["North-West",                                  "Vayavya",                                           "वायव्य"],

  // Room types (ROOM_BY_BIZ — superset across shop/office/factory)
  bv_room_entrance:       ["Entrance",                                "Pravesh",                                           "प्रवेश"],
  bv_room_owner_seat:     ["Owner Seat",                              "Swami Sthaan",                                      "स्वामी स्थान"],
  bv_room_cash_counter:   ["Cash Counter",                            "Golak",                                             "गोलक"],
  bv_room_vault:          ["Vault",                                   "Tijori",                                            "तिजोरी"],
  bv_room_stock_storage:  ["Stock Storage",                           "Bhandaar",                                          "भंडार"],
  bv_room_display:        ["Display Area",                            "Pradarshan",                                        "प्रदर्शन क्षेत्र"],
  bv_room_toilet:         ["Toilet",                                  "Shauchalaya",                                       "शौचालय"],
  bv_room_owner_cabin:    ["Owner Cabin",                             "Swami Cabin",                                       "स्वामी केबिन"],
  bv_room_reception:      ["Reception",                               "Swagat",                                            "स्वागत"],
  bv_room_conference:     ["Conference",                              "Sammelan",                                          "सम्मेलन"],
  bv_room_accounts:       ["Accounts",                                "Lekha",                                             "लेखा"],
  bv_room_server_room:    ["Server Room",                             "Server Kaksh",                                      "सर्वर कक्ष"],
  bv_room_pantry:         ["Pantry",                                  "Pantry",                                            "पेंट्री"],
  bv_room_machinery:      ["Machinery",                               "Yantra",                                            "यंत्र"],
  bv_room_heavy_machine:  ["Heavy Machine",                           "Bhari Yantra",                                      "भारी यंत्र"],
  bv_room_raw_storage:    ["Raw Storage",                             "Kachcha Maal",                                      "कच्चा माल"],
  bv_room_finished_goods: ["Finished Goods",                          "Tayar Maal",                                        "तैयार माल"],
  bv_room_boiler:         ["Boiler",                                  "Boiler",                                            "बॉयलर"],
  bv_room_labour_quarter: ["Labour Quarter",                          "Shramik",                                           "श्रमिक क्वार्टर"],

  // Errors
  bv_errAuthRequired: ["Please log in to run a Business Vastu scan.", "Business Vastu scan chalaane ke liye kripaya login karein.","Business Vastu स्कैन चलाने के लिए कृपया लॉगिन करें।"],
  bv_errValidationRooms:["Add at least one room with a direction, or upload a floor plan.","Kam se kam ek room disha ke saath joden, ya floor plan upload karein.","कम से कम एक रूम दिशा सहित जोड़ें, या एक फ़्लोर प्लान अपलोड करें।"],
  bv_errValidationName:["Naam your premise (e.g. 'Andheri Shop') — needed to match your unlock.","Apne sthal ka naam dein (jaise 'Andheri Shop') — unlock match karne ke liye zaroori hai.","अपने स्थल का नाम दें (जैसे 'अंधेरी दुकान') — अनलॉक मिलाने के लिए आवश्यक।"],
  bv_errUnlockTitle:  ["Unlock Required",                             "Unlock Zaroori",                                    "अनलॉक आवश्यक"],
  bv_errProfileTitle: ["Complete your profile",                       "Apni profile poori karein",                         "अपनी प्रोफ़ाइल पूरी करें"],
  bv_errValidTitle:   ["Check your inputs",                           "Apne inputs check karein",                          "अपने इनपुट जाँचें"],
  bv_errScanFailed:   ["Scan failed",                                 "Scan fail ho gaya",                                 "स्कैन विफल"],
  bv_errTryAgain:     ["Please try again.",                           "Kripaya phir se try karein.",                       "कृपया पुनः प्रयास करें।"],
  bv_btnCompleteProfile:["Complete Profile",                          "Profile Poori Karein",                              "प्रोफ़ाइल पूरी करें"],
  bv_walletHintPrefix:["Use the wallet above to unlock",              "Upar wallet se unlock karein",                      "ऊपर वॉलेट से अनलॉक करें"],
  bv_walletHintSuffix:["Vastu (lifetime).",                           "Vastu (lifetime).",                                 "वास्तु (आजीवन)।"],

  // Result labels
  bv_overallScore:    ["OVERALL PREMISE SCORE",                       "OVERALL PREMISE SCORE",                             "समग्र स्थल अंक"],
  bv_grade:           ["Grade",                                       "Grade",                                             "ग्रेड"],
  bv_pdfReady:        ["Detailed PDF Report Ready",                   "Detailed PDF Report Tayyar",                        "विस्तृत PDF रिपोर्ट तैयार"],
  bv_pdfBodyHi:       ["Aapka full Business Vastu report PDF me ready hai — room-by-room verdict, Mahadasha alert, stakeholder synergy, priority actions sab kuch.","Aapka full Business Vastu report PDF me ready hai — room-by-room verdict, Mahadasha alert, stakeholder synergy, priority actions sab kuch.","आपकी पूरी Business Vastu रिपोर्ट PDF में तैयार है — कमरा-दर-कमरा निर्णय, महादशा अलर्ट, हितधारक सामंजस्य, प्राथमिकता क्रियाएँ सब कुछ।"],
  bv_pdfBodyEn:       ["Your full Business Vastu report is available as a PDF — open, save, or share it.","Aapki full Business Vastu report PDF ke roop me available hai — kholein, save karein ya share karein.","आपकी पूरी Business Vastu रिपोर्ट PDF के रूप में उपलब्ध है — खोलें, सहेजें या साझा करें।"],
  bv_btnOpenPdf:      ["Open PDF Report",                             "PDF Report Kholein",                                "PDF रिपोर्ट खोलें"],
  bv_footerBrand:     ["Powered by Advanced Cosmic Intelligence",     "Powered by Advanced Cosmic Intelligence",           "Advanced Cosmic Intelligence द्वारा संचालित"],
  bv_lblIdeal:        ["Ideal",                                       "Ideal",                                             "आदर्श"],
  bv_lblAcceptable:   ["Acceptable",                                  "Acceptable",                                        "स्वीकार्य"],
  bv_lblAdjust:       ["Adjust",                                      "Adjust",                                            "समायोजन"],
  bv_lblAvoid:        ["Avoid",                                       "Avoid",                                             "टालें"],
  bv_lblOwnerMd:      ["Owner Mahadasha",                             "Owner Mahadasha",                                   "स्वामी महादशा"],
  bv_lblStakeholder:  ["Stakeholder Synergy",                         "Stakeholder Sahyog",                                "हितधारक सामंजस्य"],
  bv_lblMuhuratAlign: ["Muhurat Alignment",                           "Muhurat Alignment",                                 "मुहूर्त संरेखण"],
  bv_secPriority:     ["Priority Actions",                            "Priority Actions",                                  "प्राथमिकता क्रियाएँ"],
  bv_lblCritical:     ["★ CRITICAL",                                  "★ CRITICAL",                                        "★ महत्वपूर्ण"],
  bv_secRoomByRoom:   ["Room-by-room",                                "Kamra-dar-Kamra",                                   "कमरा-दर-कमरा"],
  bv_lblZone:         ["Zone:",                                       "Kshetra:",                                          "क्षेत्र:"],
  bv_secClassicalRefs:["CLASSICAL REFERENCES",                        "CLASSICAL REFERENCES",                              "शास्त्रीय संदर्भ"],

  // ════════════════════════════ astrovastu-pro.tsx ════════════════════════════
  avp_headerTitle:    ["AstroVastu PRO",                              "AstroVastu PRO",                                    "AstroVastu PRO"],
  avp_heroTitle:      ["Smart Scan",                                  "Smart Scan",                                        "स्मार्ट स्कैन"],
  avp_heroBody:       ["Choose how you want to scan. Each method runs a personalised Vastu × Kundli analysis.","Scan ka tareeka chunein. Har method ek personalised Vastu × Kundli analysis chalata hai.","स्कैन का तरीका चुनें। हर विधि एक व्यक्तिगत वास्तु × कुंडली विश्लेषण चलाती है।"],

  avp_modeCameraTitle:["Smart Scan",                                  "Smart Scan",                                        "स्मार्ट स्कैन"],
  avp_modeCameraSub:  ["Open camera",                                 "Camera kholein",                                    "कैमरा खोलें"],
  avp_modeSingleTitle:["Individual Room",                             "Ek Room",                                           "एक रूम"],
  avp_modeSingleSub:  ["Photo / PDF",                                 "Photo / PDF",                                       "फ़ोटो / PDF"],
  avp_modeWholeTitle: ["Full Plan",                                   "Poora Plan",                                        "पूरा प्लान"],
  avp_modeWholeSub:   ["Architect PDF",                               "Architect PDF",                                     "आर्किटेक्ट PDF"],

  avp_introCameraTitle:["Smart Scan — Live Camera",                   "Smart Scan — Live Camera",                          "स्मार्ट स्कैन — लाइव कैमरा"],
  avp_introCameraBody:["Step 1 — Tell us which room you're going to photograph. Step 2 — Tap the camera and stand inside that room. The built-in compass will lock the direction at shutter time.","Step 1 — Batayein kis room ki photo lenge. Step 2 — Camera tap karein aur us room ke andar khade hon. Shutter time par built-in compass disha lock kar dega.","चरण 1 — बताएँ कि आप किस रूम की फ़ोटो लेंगे। चरण 2 — कैमरा टैप करें और उस रूम के अंदर खड़े हों। शटर के समय बिल्ट-इन कम्पास दिशा लॉक कर देगा।"],
  avp_pickerLabel:    ["Which room is this photo of?",                "Ye photo kis room ki hai?",                         "यह फ़ोटो किस रूम की है?"],
  avp_pickerHint:     ["Pick a room above to enable the camera.",    "Camera enable karne ke liye upar room chunein.",    "कैमरा सक्षम करने के लिए ऊपर रूम चुनें।"],
  avp_camHintPrefix:  ["Camera + compass · Photographing",            "Camera + compass · Photo le rahe",                  "कैमरा + कम्पास · फ़ोटो ले रहे"],
  avp_camHintNoRoom:  ["Pick a room first",                           "Pehle room chunein",                                "पहले रूम चुनें"],

  avp_introSingleTitle:["Individual Room — Photo or PDF",             "Ek Room — Photo ya PDF",                            "एक रूम — फ़ोटो या PDF"],
  avp_introSingleBody:["Not at home? Pick a photo or PDF from your gallery and tag the room + direction manually. Best when you want to check one specific room.","Ghar par nahi ho? Gallery se photo ya PDF chunein aur room + direction manually tag karein. Tab best jab aap kisi ek room ko check karna chahte ho.","घर पर नहीं हैं? गैलरी से फ़ोटो या PDF चुनें और रूम + दिशा मैन्युअल रूप से टैग करें। तब सर्वोत्तम जब आप किसी एक विशिष्ट रूम की जाँच करना चाहते हैं।"],

  avp_introWholeTitle:["Full Plan — Smart Scan Photo Engine",         "Poora Plan — Smart Scan Photo Engine",              "पूरा प्लान — स्मार्ट स्कैन Photo Engine"],
  avp_introWholeBody: ["Got the entire floor plan from your architect (PDF or image — bedroom, kitchen, bathroom, all of it)? Upload here. Photo Engine will detect every room and give you one consolidated direction-wise report, personalised to your kundli.","Architect se poora floor plan mila (PDF ya image — bedroom, kitchen, bathroom sab)? Yahan upload karein. Photo Engine har room detect karega aur aapki kundli ke hisaab se ek consolidated disha-wise report dega.","अपने आर्किटेक्ट से पूरा फ़्लोर प्लान मिला (PDF या छवि — बेडरूम, रसोई, स्नानघर सब)? यहाँ अपलोड करें। Photo Engine हर रूम पहचानेगा और आपकी कुंडली के अनुसार एक संकलित दिशा-वार रिपोर्ट देगा।"],
  avp_btnRunWhole:    ["Run Whole-Floor Vastu Scan",                  "Poori Manzil Vastu Scan Chalayein",                 "पूरी मंज़िल वास्तु स्कैन चलाएँ"],
  avp_btnAnalysing:   ["Analysing…",                                  "Analyse ho raha hai…",                              "विश्लेषण हो रहा है…"],

  // Camera room labels (CAMERA_ROOMS)
  avp_room_bedroom:   ["Bedroom",                                     "Bedroom",                                           "शयन कक्ष"],
  avp_room_kitchen:   ["Kitchen",                                     "Kitchen",                                           "रसोई"],
  avp_room_pooja:     ["Pooja",                                       "Pooja",                                             "पूजा"],
  avp_room_living:    ["Living",                                      "Baithak",                                           "बैठक"],
  avp_room_bathroom:  ["Bathroom",                                    "Bathroom",                                          "स्नानघर"],
  avp_room_entrance:  ["Entrance",                                    "Pravesh",                                           "प्रवेश"],
  avp_room_study:     ["Study",                                       "Adhyayan",                                          "अध्ययन कक्ष"],
  avp_room_store:     ["Store",                                       "Bhandaar",                                          "भंडार"],

  // Errors
  avp_errAuthRequired:["Please log in to run a Smart Scan.",          "Smart Scan chalaane ke liye kripaya login karein.","Smart Scan चलाने के लिए कृपया लॉगिन करें।"],
  avp_errMonthlyLimit:["Monthly limit reached",                       "Maasik limit poori",                                "मासिक सीमा पूरी"],
  avp_errUpgradeReq:  ["Upgrade required",                            "Upgrade zaroori",                                   "अपग्रेड आवश्यक"],
  avp_errProfile:     ["Complete your profile",                       "Apni profile poori karein",                         "अपनी प्रोफ़ाइल पूरी करें"],
  avp_errVisionNoRoom:["Couldn't read this photo",                    "Ye photo padhi nahi ja saki",                       "यह फ़ोटो पढ़ी नहीं जा सकी"],
  avp_errScanFailed:  ["Smart Scan failed",                           "Smart Scan fail ho gaya",                           "स्मार्ट स्कैन विफल"],
  avp_errBodyDefault: ["Please try a clearer photo of your floor plan or the full room.","Apne floor plan ya poore room ki saaf photo try karein.","अपने फ़्लोर प्लान या पूरे रूम की स्पष्ट फ़ोटो आज़माएँ।"],
  avp_btnCompleteProfile:["Complete Profile",                         "Profile Poori Karein",                              "प्रोफ़ाइल पूरी करें"],
  avp_btnUpgradePro:  ["Upgrade to Pro — Unlimited",                  "Pro me Upgrade — Unlimited",                        "Pro में अपग्रेड — असीमित"],

  // Result
  avp_overallScore:   ["OVERALL HOUSE SCORE",                         "OVERALL HOUSE SCORE",                               "समग्र घर अंक"],
  avp_pdfReady:       ["Detailed PDF Report Ready",                   "Detailed PDF Report Tayyar",                        "विस्तृत PDF रिपोर्ट तैयार"],
  avp_pdfBody:        ["Aapka full AstroVastu PRO report PDF me ready hai — har room ka deep verdict, Mahadasha layer, priority actions aur classical references.","Aapka full AstroVastu PRO report PDF me ready hai — har room ka deep verdict, Mahadasha layer, priority actions aur classical references.","आपकी पूरी AstroVastu PRO रिपोर्ट PDF में तैयार है — हर रूम का गहन निर्णय, महादशा परत, प्राथमिकता क्रियाएँ और शास्त्रीय संदर्भ।"],
  avp_btnOpenPdf:     ["Open PDF Report",                             "PDF Report Kholein",                                "PDF रिपोर्ट खोलें"],
  avp_footerBrand:    ["Powered by Advanced Cosmic Intelligence",     "Powered by Advanced Cosmic Intelligence",           "Advanced Cosmic Intelligence द्वारा संचालित"],
  avp_secPriority:    ["PRIORITY ACTIONS",                            "PRIORITY ACTIONS",                                  "प्राथमिकता क्रियाएँ"],
  avp_secRoomByRoom:  ["ROOM-BY-ROOM BREAKDOWN",                      "KAMRA-DAR-KAMRA BREAKDOWN",                         "कमरा-दर-कमरा विवरण"],
  avp_lblMdAlert:     ["Mahadasha Alert",                             "Mahadasha Alert",                                   "महादशा अलर्ट"],
  avp_quotaUnlimited: ["Unlimited PRO scans (Pro plan)",              "Unlimited PRO scans (Pro plan)",                    "असीमित PRO स्कैन (Pro योजना)"],
  avp_quotaPrefix:    ["Scan",                                        "Scan",                                              "स्कैन"],
  avp_quotaThisMonth: ["this month",                                  "is maah",                                           "इस माह"],
  avp_brandFooter:    ["✨ Powered by Advanced Cosmic Intelligence",  "✨ Powered by Advanced Cosmic Intelligence",        "✨ Advanced Cosmic Intelligence द्वारा संचालित"],
  avp_brandFooterSub: ["Cosmic AstroVastu Drishti — PRO Engine v1.0", "Cosmic AstroVastu Drishti — PRO Engine v1.0",       "Cosmic AstroVastu Drishti — PRO Engine v1.0"],
  avp_lblIdeal:       ["Ideal",                                       "Ideal",                                             "आदर्श"],
  avp_lblAcceptable:  ["Acceptable",                                  "Acceptable",                                        "स्वीकार्य"],
  avp_lblAdjust:      ["Adjust",                                      "Adjust",                                            "समायोजन"],
  avp_lblAvoid:       ["Avoid",                                       "Avoid",                                             "टालें"],

  // ════════════════════════════ astrovastu-pro-result.tsx ════════════════════════════
  avr_emptyTitle:     ["No report loaded",                            "Koi report load nahi hui",                          "कोई रिपोर्ट लोड नहीं हुई"],
  avr_emptyBody:      ["Please run a Smart Scan first to view the result here.","Yahaan result dekhne ke liye pehle Smart Scan chalayein.","यहाँ परिणाम देखने के लिए पहले Smart Scan चलाएँ।"],
  avr_btnOpenPro:     ["Open AstroVastu PRO",                         "AstroVastu PRO Kholein",                            "AstroVastu PRO खोलें"],
  avr_headerTitle:    ["Your AstroVastu Report",                      "Aapki AstroVastu Report",                           "आपकी AstroVastu रिपोर्ट"],
  avr_outOf100:       ["OUT OF 100",                                  "100 me se",                                         "100 में से"],
  avr_grade:          ["Grade",                                       "Grade",                                             "ग्रेड"],
  avr_btnOpenPdf:     ["Open PDF",                                    "PDF Kholein",                                       "PDF खोलें"],
  avr_btnWhatsApp:    ["WhatsApp",                                    "WhatsApp",                                          "WhatsApp"],
  avr_secPriorityHi:  ["SABSE PEHLE YE 3 CHEEZEIN THEEK KARO",        "SABSE PEHLE YE 3 CHEEZEIN THEEK KARO",              "सबसे पहले ये 3 चीज़ें ठीक करें"],
  avr_secRoomByRoom:  ["ROOM-BY-ROOM",                                "KAMRA-DAR-KAMRA",                                   "कमरा-दर-कमरा"],
  avr_brandFooter:    ["✨ Powered by Advanced Cosmic Intelligence",  "✨ Powered by Advanced Cosmic Intelligence",        "✨ Advanced Cosmic Intelligence द्वारा संचालित"],
  avr_shareTitle:     ["🪔 *AstroVastu PRO Report*",                  "🪔 *AstroVastu PRO Report*",                        "🪔 *AstroVastu PRO रिपोर्ट*"],
  avr_shareScoreLbl:  ["📊 Score:",                                   "📊 Score:",                                         "📊 अंक:"],
  avr_shareOpenLbl:   ["📄 Open report:",                             "📄 Report kholein:",                                "📄 रिपोर्ट खोलें:"],
  avr_shareBrandLbl:  ["_Powered by Advanced Cosmic Intelligence_",   "_Powered by Advanced Cosmic Intelligence_",         "_Advanced Cosmic Intelligence द्वारा संचालित_"],
  avr_alertShareErr:  ["Couldn't share",                              "Share nahi ho saka",                                "साझा नहीं हो सका"],
};
