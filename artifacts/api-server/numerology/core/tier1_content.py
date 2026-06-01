"""
Tier 1 — Core Numerology Numbers (Pythagorean system)
Content dicts for 3-language rendering: english / hindi / hinglish.

Covers:
  • Life Path (1-9, 11, 22, 33)
  • Expression / Destiny (1-9, 11, 22, 33)
  • Soul Urge (Heart's Desire) (1-9)
  • Personality (1-9)
  • Birthday Number (1-31) — short interpretations
  • Maturity Number (1-9) — activates ~35+ age
  • Balance Number (1-9) — crisis-recovery number
  • Karmic Debt Numbers (13, 14, 16, 19) — full 3-lang
  • Karmic Lessons / Missing Numbers (1-9) — for digits missing from name
  • Hidden Passion (1-9) — most repeated letter value
  • Personal Year (1-9) — year-specific theme
  • Pinnacles (1-9) — 4 life-phase peaks
  • Challenges (0-9) — 4 life-phase lessons

Style: crisp, informationally dense; no fluff.
"""
from __future__ import annotations
from typing import Dict, Any, List

# ─── 1. LIFE PATH (main destiny number from DOB) ─────────────────
LIFE_PATH = {
    1: {
        "english": "Natural-born leader, pioneer, and innovator. You incarnated to originate ideas and blaze trails others will follow. Independence is oxygen; being managed crushes you. Challenge: ego, loneliness, impatience with slower minds.",
        "hindi": "जन्मजात नेता, अग्रणी और नवप्रवर्तक। आप विचारों को जन्म देने और नए रास्ते बनाने आए हैं, जिन पर दूसरे चलेंगे। स्वतंत्रता आपकी ऑक्सीजन है; नियंत्रण में रहना आपको कुचल देता है। चुनौती: अहंकार, अकेलापन, धीमे लोगों के प्रति अधीरता।",
        "hinglish": "Natural-born leader, pioneer aur innovator. Aap ideas ko janm dene aur naye raaste banane aaye ho, jin par aur log chalenge. Independence aapki oxygen hai; control me rehna aapko kuchal deta hai. Challenge: ego, akelapan, slow logon ke liye impatience.",
    },
    2: {
        "english": "Diplomat, peacemaker, intuitive partner. You are the glue that binds teams, couples, and families. Behind-the-scenes power — the advisor to kings. Challenge: over-sensitivity, conflict avoidance, losing self in others.",
        "hindi": "कूटनीतिज्ञ, शांतिदूत, सहज सहयोगी। आप टीम, जोड़ों और परिवारों को जोड़ने वाला गोंद हैं। पर्दे के पीछे की शक्ति — राजाओं के सलाहकार। चुनौती: अति-संवेदनशीलता, विवाद से बचना, दूसरों में खुद को खो देना।",
        "hinglish": "Diplomat, peacemaker, intuitive partner. Aap teams, couples aur families ko bind karne wala glue ho. Behind-the-scenes power — rajaaon ke advisor. Challenge: over-sensitivity, conflict se bachna, dusron me khud ko kho dena.",
    },
    3: {
        "english": "Creative communicator, performer, charmer. Words, art, expression flow through you naturally. Joy is your fuel; suppressed creativity turns into depression. Challenge: scattering energy, superficiality, avoiding deep work.",
        "hindi": "रचनात्मक संप्रेषक, कलाकार, आकर्षक व्यक्तित्व। शब्द, कला, अभिव्यक्ति सहज रूप से आपके माध्यम से बहते हैं। आनंद आपका ईंधन है; दबी हुई रचनात्मकता अवसाद बन जाती है। चुनौती: ऊर्जा बिखरना, सतहीपन, गहरे कार्य से बचना।",
        "hinglish": "Creative communicator, performer, charmer. Words, art, expression aapke through naturally flow karte hain. Joy aapka fuel hai; suppressed creativity depression ban jati hai. Challenge: energy scatter, superficiality, deep work se bachna.",
    },
    4: {
        "english": "Builder, organizer, master of systems. Structure and discipline are your superpowers — you turn chaos into reliable machines. Slow-but-certain wealth. Challenge: rigidity, workaholism, resisting change even when obvious.",
        "hindi": "निर्माता, संगठक, व्यवस्थाओं के स्वामी। संरचना और अनुशासन आपकी महाशक्तियाँ हैं — आप अराजकता को विश्वसनीय मशीन में बदल देते हैं। धीमी लेकिन निश्चित समृद्धि। चुनौती: कठोरता, कार्यप्रेम, स्पष्ट होने पर भी बदलाव का विरोध।",
        "hinglish": "Builder, organizer, systems ke master. Structure aur discipline aapke superpowers hain — aap chaos ko reliable machines me badal dete ho. Slow-but-certain wealth. Challenge: rigidity, workaholism, obvious hone par bhi change ka resistance.",
    },
    5: {
        "english": "Freedom-lover, traveller, shape-shifter. You came to taste life's full buffet — variety is non-negotiable. Routine cages you. Challenge: restlessness, addictions, commitment issues, 'grass is greener' syndrome.",
        "hindi": "स्वतंत्रता-प्रेमी, यात्री, रूप-परिवर्तक। आप जीवन के पूरे भोज का स्वाद लेने आए हैं — विविधता अनिवार्य है। दिनचर्या आपको कैद करती है। चुनौती: बेचैनी, व्यसन, प्रतिबद्धता की समस्याएँ, 'दूसरी तरफ़ घास हरी' सिंड्रोम।",
        "hinglish": "Freedom-lover, traveller, shape-shifter. Aap life ke full buffet ka taste lene aaye ho — variety non-negotiable hai. Routine aapko cage karta hai. Challenge: restlessness, addictions, commitment issues, 'dusri taraf grass hari hai' syndrome.",
    },
    6: {
        "english": "Nurturer, healer, guardian of beauty and love. Home, family, and service are your dharma. Natural counsellor — people dump their problems on you. Challenge: over-giving, martyr complex, taking on others' burdens.",
        "hindi": "पोषक, चिकित्सक, सौंदर्य और प्रेम के रक्षक। घर, परिवार, और सेवा आपका धर्म है। स्वाभाविक परामर्शदाता — लोग अपनी समस्याएँ आप पर डालते हैं। चुनौती: अति-देना, शहीद-भाव, दूसरों का बोझ उठाना।",
        "hinglish": "Nurturer, healer, beauty aur love ke guardian. Ghar, family, seva aapka dharma hai. Natural counsellor — log apni problems aap par daalte hain. Challenge: over-giving, martyr complex, dusron ka bojh uthana.",
    },
    7: {
        "english": "Seeker, analyst, mystic. You came to dig beneath surfaces — truth, science, spirit. Solitude is your teacher; small-talk exhausts you. Challenge: isolation, cynicism, spiritual bypassing, trust issues with people.",
        "hindi": "खोजी, विश्लेषक, रहस्यवादी। आप सतह के नीचे खोदने आए हैं — सत्य, विज्ञान, आत्मा। एकांत आपका गुरु है; छोटी-मोटी बातें थका देती हैं। चुनौती: अलगाव, निराशावाद, आध्यात्मिक पलायन, लोगों पर भरोसे की कमी।",
        "hinglish": "Seeker, analyst, mystic. Aap surface ke neeche khodne aaye ho — truth, science, spirit. Solitude aapka teacher hai; small-talk aapko thaka deta hai. Challenge: isolation, cynicism, spiritual bypassing, logon par trust issues.",
    },
    8: {
        "english": "Executive, CEO, material-world master. Money, power, and long-term legacy are your karmic curriculum. Tests are severe — you win big or lose big. Challenge: workaholism, ruthlessness, spiritual-material imbalance.",
        "hindi": "कार्यकारी, सीईओ, भौतिक-संसार के स्वामी। धन, शक्ति, और दीर्घकालिक विरासत आपका कर्म-पाठ्यक्रम है। परीक्षाएँ कठोर — या तो बड़ा जीतेंगे या बड़ा हारेंगे। चुनौती: कार्यप्रेम, निर्दयता, आध्यात्मिक-भौतिक असंतुलन।",
        "hinglish": "Executive, CEO, material-world ke master. Paisa, power, long-term legacy aapka karmic curriculum hai. Tests severe — ya bada jeetoge ya bada haaroge. Challenge: workaholism, ruthlessness, spiritual-material imbalance.",
    },
    9: {
        "english": "Humanitarian, old soul, global citizen. You came to serve the collective — art, activism, healing at scale. Personal attachments often dissolve for the mission. Challenge: emotional detachment, martyr-burnout, inability to receive.",
        "hindi": "मानवतावादी, पुरानी आत्मा, विश्व-नागरिक। आप सामूहिक की सेवा करने आए हैं — कला, सक्रियता, बड़े पैमाने पर उपचार। व्यक्तिगत लगाव अक्सर मिशन के लिए विलीन हो जाते हैं। चुनौती: भावनात्मक वैराग्य, शहीद-थकान, प्राप्त करने में असमर्थता।",
        "hinglish": "Humanitarian, old soul, global citizen. Aap collective ki seva karne aaye ho — art, activism, scale par healing. Personal attachments aksar mission ke liye ghul jaate hain. Challenge: emotional detachment, martyr-burnout, receive karne ki inability.",
    },
    11: {
        "english": "MASTER — intuitive messenger and spiritual catalyst. Higher octave of 2. You download insights that inspire millions. Also carries 2's shadows × 10. Challenge: nervous-system overload, anxiety, struggle between fame and solitude.",
        "hindi": "मास्टर — सहज संदेशवाहक और आध्यात्मिक उत्प्रेरक। 2 का उच्चतर सप्तक। आप ऐसी अंतर्दृष्टि डाउनलोड करते हैं जो लाखों को प्रेरित करती है। 2 की छायाएँ भी 10 गुना। चुनौती: तंत्रिका तंत्र का अधिभार, चिंता, प्रसिद्धि और एकांत के बीच संघर्ष।",
        "hinglish": "MASTER — intuitive messenger aur spiritual catalyst. 2 ka higher octave. Aap aisi insights download karte ho jo millions ko inspire karti hain. 2 ke shadows bhi 10 guna. Challenge: nervous-system overload, anxiety, fame aur solitude ke beech struggle.",
    },
    22: {
        "english": "MASTER BUILDER — turns visions into physical reality on grand scale. Higher octave of 4. Founders, architects, global-scale changemakers. Challenge: pressure of potential, feeling the weight of what you're 'supposed' to build.",
        "hindi": "मास्टर बिल्डर — दृष्टि को भौतिक वास्तविकता में बदलता है, वो भी बड़े पैमाने पर। 4 का उच्चतर सप्तक। संस्थापक, वास्तुकार, वैश्विक परिवर्तन-निर्माता। चुनौती: संभावना का दबाव, 'अपेक्षित' निर्माण का बोझ।",
        "hinglish": "MASTER BUILDER — visions ko physical reality me badalta hai, grand scale par. 4 ka higher octave. Founders, architects, global changemakers. Challenge: potential ka pressure, jo banana 'chahiye' uska weight.",
    },
    33: {
        "english": "MASTER TEACHER — selfless service, divine love, healing humanity. Higher octave of 6. Rarest vibration — Christ-consciousness. Challenge: sacrificing personal life entirely; burnout; being misunderstood by 'normal' people.",
        "hindi": "मास्टर टीचर — निस्वार्थ सेवा, दिव्य प्रेम, मानवता का उपचार। 6 का उच्चतर सप्तक। सबसे दुर्लभ कंपन — क्राइस्ट-चेतना। चुनौती: व्यक्तिगत जीवन को पूरी तरह त्याग देना; थकावट; 'सामान्य' लोगों द्वारा गलत समझा जाना।",
        "hinglish": "MASTER TEACHER — selfless service, divine love, humanity ka healing. 6 ka higher octave. Rarest vibration — Christ-consciousness. Challenge: personal life pura sacrifice, burnout, 'normal' logon dwara galat samjha jaana.",
    },
}

# ─── 2. EXPRESSION / DESTINY (from full name) ─────────────────────
EXPRESSION = {
    1: {
        "english": "Your destiny: to lead, originate, and stand alone in front of the pack. You're here to put YOUR name on something — a product, a movement, a brand.",
        "hindi": "आपकी नियति: नेतृत्व, सृजन, और भीड़ के आगे अकेले खड़े होना। आप किसी चीज़ पर अपना नाम लगाने आए हैं — उत्पाद, आंदोलन, या ब्रांड।",
        "hinglish": "Aapki destiny: lead karna, originate karna, bheed ke aage akela khada hona. Aap kisi cheez par APNA naam lagane aaye ho — product, movement, brand.",
    },
    2: {
        "english": "Your destiny: to mediate, partner, and make others great. Behind every '1' is a powerful '2'. You are the peace-keeper and the kingmaker.",
        "hindi": "आपकी नियति: मध्यस्थता करना, साझेदारी करना, दूसरों को महान बनाना। हर '1' के पीछे एक शक्तिशाली '2' होता है। आप शांति-रक्षक और राजा-निर्माता हैं।",
        "hinglish": "Aapki destiny: mediate karna, partner banna, dusron ko great banana. Har '1' ke peeche ek powerful '2' hota hai. Aap peace-keeper aur kingmaker ho.",
    },
    3: {
        "english": "Your destiny: to communicate, inspire, and spread joy. Writing, speaking, performing, creating — these are your dharmic channels.",
        "hindi": "आपकी नियति: संप्रेषण, प्रेरणा, आनंद फैलाना। लेखन, भाषण, प्रदर्शन, सृजन — ये आपके धार्मिक माध्यम हैं।",
        "hinglish": "Aapki destiny: communicate karna, inspire karna, joy spread karna. Writing, speaking, performing, creating — yeh aapke dharmic channels hain.",
    },
    4: {
        "english": "Your destiny: to build what lasts. Institutions, companies, families — you are the foundation stone others stand on. Earn slow, keep forever.",
        "hindi": "आपकी नियति: ऐसा बनाना जो टिके। संस्थाएँ, कंपनियाँ, परिवार — आप वह आधार-शिला हैं जिस पर दूसरे खड़े होते हैं। धीरे कमाइए, सदा के लिए रखिए।",
        "hinglish": "Aapki destiny: aisa banana jo tike. Institutions, companies, families — aap woh foundation stone ho jis par dusre khade hote hain. Slow kamao, hamesha ke liye rakho.",
    },
    5: {
        "english": "Your destiny: to experience, explore, and liberate. You're the one who tastes 100 flavours and reports back. Teacher of freedom.",
        "hindi": "आपकी नियति: अनुभव, अन्वेषण, मुक्ति। आप वह हैं जो 100 स्वाद चखता है और वापस रिपोर्ट करता है। स्वतंत्रता के शिक्षक।",
        "hinglish": "Aapki destiny: experience karna, explore karna, liberate karna. Aap woh ho jo 100 flavours chakh ke wapas report karta hai. Freedom ke teacher.",
    },
    6: {
        "english": "Your destiny: to heal, nurture, and beautify. Home, health, harmony — you leave everything you touch more whole than you found it.",
        "hindi": "आपकी नियति: उपचार, पोषण, सौंदर्यीकरण। घर, स्वास्थ्य, सौहार्द — आप जो छूते हैं उसे पहले से अधिक पूर्ण छोड़ते हैं।",
        "hinglish": "Aapki destiny: heal karna, nurture karna, beautify karna. Ghar, health, harmony — aap jo bhi chhoote ho, use pehle se zyada whole chhodte ho.",
    },
    7: {
        "english": "Your destiny: to seek, study, and reveal hidden truths. Scientist, mystic, analyst — your work is to look where others don't dare.",
        "hindi": "आपकी नियति: खोज, अध्ययन, छिपे सत्य प्रकट करना। वैज्ञानिक, रहस्यवादी, विश्लेषक — आपका कार्य वहाँ देखना है जहाँ दूसरे नहीं जाते।",
        "hinglish": "Aapki destiny: seek karna, study karna, chhupe satya reveal karna. Scientist, mystic, analyst — aapka kaam wahan dekhna hai jahan dusre nahi jaate.",
    },
    8: {
        "english": "Your destiny: to manage money, power, and large-scale resources. CEO energy. Karmic classroom — if you stay clean, you become legendary.",
        "hindi": "आपकी नियति: धन, शक्ति, बड़े संसाधनों का प्रबंधन। सीईओ ऊर्जा। कर्म-कक्षा — शुद्ध रहें तो पौराणिक बनें।",
        "hinglish": "Aapki destiny: paisa, power, bade resources manage karna. CEO energy. Karmic classroom — clean raho to legendary ban jao.",
    },
    9: {
        "english": "Your destiny: to serve the whole, not just your tribe. Global causes, art that moves millions, compassion as profession. The old-soul completer.",
        "hindi": "आपकी नियति: केवल अपने समूह नहीं, पूरे की सेवा। वैश्विक कारण, कला जो लाखों को छूती है, करुणा पेशे के रूप में। पुरानी-आत्मा पूर्णकर्ता।",
        "hinglish": "Aapki destiny: sirf apne tribe nahi, pure collective ki seva. Global causes, art jo millions ko chhuti hai, compassion as profession. Old-soul completer.",
    },
    11: {
        "english": "MASTER destiny: intuitive messenger. You are meant to inspire, not just speak. Channel deep insight into popular forms.",
        "hindi": "मास्टर नियति: अंतर्ज्ञानी संदेशवाहक। आप प्रेरित करने के लिए हैं, केवल बोलने के लिए नहीं। गहन अंतर्दृष्टि को लोकप्रिय रूपों में चैनल करें।",
        "hinglish": "MASTER destiny: intuitive messenger. Aap inspire karne ke liye ho, sirf bolne ke liye nahi. Deep insight ko popular forms me channel karo.",
    },
    22: {
        "english": "MASTER destiny: builder of large-scale reality. Institutions, cities, movements bearing your stamp for generations.",
        "hindi": "मास्टर नियति: बड़े पैमाने की वास्तविकता के निर्माता। पीढ़ियों तक आपकी छाप वाले संस्थान, शहर, आंदोलन।",
        "hinglish": "MASTER destiny: bade scale ki reality ke builder. Institutions, cities, movements — peedhiyon tak aapki chaap.",
    },
    33: {
        "english": "MASTER destiny: healer-teacher of humanity. Your life IS the lesson — lived openly for others to learn from.",
        "hindi": "मास्टर नियति: मानवता के उपचारक-शिक्षक। आपका जीवन ही पाठ है — खुले रूप से जिया गया ताकि दूसरे सीख सकें।",
        "hinglish": "MASTER destiny: humanity ke healer-teacher. Aapki life HI lesson hai — openly jiya gaya taaki dusre seekh sakein.",
    },
}

# ─── 3. SOUL URGE / HEART'S DESIRE (from vowels) ──────────────────
SOUL_URGE = {
    1: {
        "english": "Deep down, you crave to be #1, to stand out, to be recognized for originality. Anonymity suffocates your soul.",
        "hindi": "गहराई में, आप #1 बनना, अलग दिखना, मौलिकता के लिए पहचाने जाना चाहते हैं। गुमनामी आपकी आत्मा का दम घोंटती है।",
        "hinglish": "Deep down, aap #1 banna, stand-out karna, originality ke liye pehchaane jana chahte ho. Anonymity aapki soul ka dam ghotti hai.",
    },
    2: {
        "english": "Your heart craves harmony, partnership, and deep emotional connection. Loneliness hurts you more than most.",
        "hindi": "आपका हृदय सामंजस्य, साझेदारी, गहरा भावनात्मक जुड़ाव चाहता है। अकेलापन अधिकांश से अधिक आपको कष्ट देता है।",
        "hinglish": "Aapka dil harmony, partnership, deep emotional connection chahta hai. Akelapan aapko logon se zyada takleef deta hai.",
    },
    3: {
        "english": "Your soul wants to express, entertain, and share joy. Without creative outlet, your inner light dims fast.",
        "hindi": "आपकी आत्मा अभिव्यक्त करना, मनोरंजन करना, आनंद बाँटना चाहती है। रचनात्मक माध्यम के बिना आपकी भीतरी रोशनी जल्दी मंद पड़ जाती है।",
        "hinglish": "Aapki soul express karna, entertain karna, joy share karna chahti hai. Creative outlet ke bina aapki inner light jaldi dim ho jati hai.",
    },
    4: {
        "english": "Your heart wants security, order, and a solid base. Uncertainty and mess deeply unsettle you.",
        "hindi": "आपका हृदय सुरक्षा, व्यवस्था, ठोस आधार चाहता है। अनिश्चितता और अव्यवस्था आपको गहराई से अस्थिर करती है।",
        "hinglish": "Aapka dil security, order, solid base chahta hai. Uncertainty aur mess aapko deeply unsettle karte hain.",
    },
    5: {
        "english": "Your soul craves freedom, variety, and adventure. Being tied down — emotionally or physically — feels like prison.",
        "hindi": "आपकी आत्मा स्वतंत्रता, विविधता, साहसिक अनुभव चाहती है। बँधा होना — भावनात्मक या शारीरिक — जेल जैसा लगता है।",
        "hinglish": "Aapki soul freedom, variety, adventure chahti hai. Bandhe hona — emotional ya physical — jail jaisa lagta hai.",
    },
    6: {
        "english": "Your heart wants to love, be loved, and create beauty around you. Home is sacred; ugly environments wound you.",
        "hindi": "आपका हृदय प्रेम करना, प्रेम पाना, अपने चारों ओर सौंदर्य रचना चाहता है। घर पवित्र है; कुरूप वातावरण आपको घायल करते हैं।",
        "hinglish": "Aapka dil love karna, love paana, apne aas-paas beauty create karna chahta hai. Ghar sacred hai; ugly environments aapko ghayal karte hain.",
    },
    7: {
        "english": "Your soul wants truth, solitude, and depth. Shallow people and small-talk drain you instantly.",
        "hindi": "आपकी आत्मा सत्य, एकांत, गहराई चाहती है। सतही लोग और छोटी-मोटी बातें तुरंत थका देती हैं।",
        "hinglish": "Aapki soul truth, solitude, depth chahti hai. Shallow log aur small-talk aapko instantly drain kar dete hain.",
    },
    8: {
        "english": "Your heart wants power, respect, and material achievement. Being broke or ignored hurts more than you admit.",
        "hindi": "आपका हृदय शक्ति, सम्मान, भौतिक उपलब्धि चाहता है। गरीब होना या अनदेखा किया जाना जितना आप स्वीकारते हैं उससे अधिक कष्ट देता है।",
        "hinglish": "Aapka dil power, respect, material achievement chahta hai. Broke hona ya ignore kiya jaana aap jitna admit karte ho usse zyada takleef deta hai.",
    },
    9: {
        "english": "Your soul wants to serve humanity, heal wounds, leave the world better. Personal happiness alone feels empty.",
        "hindi": "आपकी आत्मा मानवता की सेवा करना, घाव भरना, दुनिया को बेहतर छोड़ना चाहती है। केवल व्यक्तिगत सुख खाली लगता है।",
        "hinglish": "Aapki soul humanity ki seva, wounds heal karna, duniya ko better chhodna chahti hai. Sirf personal happiness khaali lagti hai.",
    },
}

# ─── 4. PERSONALITY NUMBER (how world sees you) ────────────────────
PERSONALITY = {
    1: {"english": "World sees: confident, independent, 'alpha' energy. First impression: leader.",
        "hindi": "दुनिया देखती है: आत्मविश्वासी, स्वतंत्र, 'अल्फ़ा' ऊर्जा। पहली छाप: नेता।",
        "hinglish": "Duniya dekhti hai: confident, independent, 'alpha' energy. First impression: leader."},
    2: {"english": "World sees: gentle, approachable, diplomatic. First impression: safe, warm, trustworthy.",
        "hindi": "दुनिया देखती है: सौम्य, सुलभ, कूटनीतिक। पहली छाप: सुरक्षित, गर्मजोशी, भरोसेमंद।",
        "hinglish": "Duniya dekhti hai: gentle, approachable, diplomatic. First impression: safe, warm, trustworthy."},
    3: {"english": "World sees: witty, charming, expressive. First impression: fun, social magnet.",
        "hindi": "दुनिया देखती है: चतुर, आकर्षक, अभिव्यंजक। पहली छाप: मज़ेदार, सामाजिक आकर्षण।",
        "hinglish": "Duniya dekhti hai: witty, charming, expressive. First impression: fun, social magnet."},
    4: {"english": "World sees: reliable, serious, steady. First impression: competent, 'gets things done'.",
        "hindi": "दुनिया देखती है: विश्वसनीय, गंभीर, स्थिर। पहली छाप: सक्षम, 'काम पूरा करने वाला'।",
        "hinglish": "Duniya dekhti hai: reliable, serious, steady. First impression: competent, 'kaam kar deta hai'."},
    5: {"english": "World sees: energetic, unpredictable, magnetic. First impression: fun, can't-be-boxed.",
        "hindi": "दुनिया देखती है: ऊर्जावान, अप्रत्याशित, चुंबकीय। पहली छाप: मज़ेदार, किसी खाँचे में नहीं।",
        "hinglish": "Duniya dekhti hai: energetic, unpredictable, magnetic. First impression: fun, box me nahi aata."},
    6: {"english": "World sees: caring, responsible, warm. First impression: 'this person looks after everyone'.",
        "hindi": "दुनिया देखती है: देखभाल करने वाला, उत्तरदायी, गर्मजोश। पहली छाप: 'यह सबका ध्यान रखता है'।",
        "hinglish": "Duniya dekhti hai: caring, responsible, warm. First impression: 'yeh har kisi ka dhyan rakhta hai'."},
    7: {"english": "World sees: quiet, deep, slightly aloof. First impression: intelligent, hard to read.",
        "hindi": "दुनिया देखती है: शांत, गहरा, थोड़ा अलग। पहली छाप: बुद्धिमान, पढ़ना मुश्किल।",
        "hinglish": "Duniya dekhti hai: quiet, deep, thoda aloof. First impression: intelligent, padhna mushkil."},
    8: {"english": "World sees: powerful, ambitious, intimidating. First impression: boss-energy, 'don't waste my time'.",
        "hindi": "दुनिया देखती है: शक्तिशाली, महत्वाकांक्षी, प्रभावशाली। पहली छाप: बॉस-ऊर्जा, 'समय बर्बाद मत करो'।",
        "hinglish": "Duniya dekhti hai: powerful, ambitious, intimidating. First impression: boss-energy, 'time waste mat karo'."},
    9: {"english": "World sees: wise, compassionate, slightly distant. First impression: 'old soul', universal lover.",
        "hindi": "दुनिया देखती है: बुद्धिमान, करुणामय, थोड़ा दूर। पहली छाप: 'पुरानी आत्मा', सार्वभौमिक प्रेमी।",
        "hinglish": "Duniya dekhti hai: wise, compassionate, thoda distant. First impression: 'old soul', universal lover."},
}

# ─── 5. BIRTHDAY NUMBER (day of month 1-31) — short ─────────────────
# Each interpretation is 1 sentence in each lang.
def _bday(en: str, hi: str, hg: str) -> Dict[str, str]:
    return {"english": en, "hindi": hi, "hinglish": hg}

BIRTHDAY = {
    1: _bday("Born leader — independent, pioneering, forceful.",
             "जन्मजात नेता — स्वतंत्र, अग्रणी, प्रभावशाली।",
             "Born leader — independent, pioneering, forceful."),
    2: _bday("Diplomat — sensitive, cooperative, musical.",
             "कूटनीतिज्ञ — संवेदनशील, सहयोगी, संगीतप्रेमी।",
             "Diplomat — sensitive, cooperative, musical."),
    3: _bday("Performer — creative, witty, socially magnetic.",
             "कलाकार — रचनात्मक, चतुर, सामाजिक रूप से चुंबकीय।",
             "Performer — creative, witty, socially magnetic."),
    4: _bday("Builder — methodical, loyal, slow-but-certain.",
             "निर्माता — व्यवस्थित, वफ़ादार, धीमे पर निश्चित।",
             "Builder — methodical, loyal, slow-but-certain."),
    5: _bday("Explorer — restless, versatile, communicator.",
             "अन्वेषक — बेचैन, बहुमुखी, संप्रेषक।",
             "Explorer — restless, versatile, communicator."),
    6: _bday("Nurturer — responsible, beauty-lover, family-focused.",
             "पोषक — उत्तरदायी, सौंदर्य-प्रेमी, परिवार-केंद्रित।",
             "Nurturer — responsible, beauty-lover, family-focused."),
    7: _bday("Thinker — analytical, spiritual, solitary.",
             "विचारक — विश्लेषणात्मक, आध्यात्मिक, एकाकी।",
             "Thinker — analytical, spiritual, solitary."),
    8: _bday("Achiever — ambitious, business-minded, karmic.",
             "उपलब्धिकर्ता — महत्वाकांक्षी, व्यावसायिक, कार्मिक।",
             "Achiever — ambitious, business-minded, karmic."),
    9: _bday("Humanitarian — generous, artistic, old-soul.",
             "मानवतावादी — उदार, कलात्मक, पुरानी-आत्मा।",
             "Humanitarian — generous, artistic, old-soul."),
    10: _bday("Strong leader with creative streak (1+0=1 amplified).",
              "रचनात्मक धारा वाले सशक्त नेता (1+0=1 प्रबल)।",
              "Strong leader with creative streak (1+0=1 amplified)."),
    11: _bday("⭐ Master intuitive — higher-octave 2.",
              "⭐ मास्टर सहज-ज्ञानी — 2 का उच्चतर सप्तक।",
              "⭐ Master intuitive — higher-octave 2."),
    12: _bday("Creative communicator with discipline (1+2=3).",
              "अनुशासन के साथ रचनात्मक संप्रेषक (1+2=3)।",
              "Creative communicator with discipline (1+2=3)."),
    13: _bday("⚠ Karmic-debt 13 — hard work, no shortcuts; diligence rewards.",
              "⚠ कर्म-ऋण 13 — कठोर परिश्रम, कोई शॉर्टकट नहीं; लगन पुरस्कृत।",
              "⚠ Karmic-debt 13 — hard work, no shortcuts; diligence rewards."),
    14: _bday("⚠ Karmic-debt 14 — freedom-discipline balance; moderation lesson.",
              "⚠ कर्म-ऋण 14 — स्वतंत्रता-अनुशासन संतुलन; संयम का पाठ।",
              "⚠ Karmic-debt 14 — freedom-discipline balance; moderation lesson."),
    15: _bday("Magnetic charmer with family karma (1+5=6).",
              "पारिवारिक कर्म के साथ चुंबकीय आकर्षण (1+5=6)।",
              "Magnetic charmer with family karma (1+5=6)."),
    16: _bday("⚠ Karmic-debt 16 — ego/love-triangle karma; humility heals.",
              "⚠ कर्म-ऋण 16 — अहंकार/प्रेम-त्रिकोण कर्म; विनम्रता चंगा करती है।",
              "⚠ Karmic-debt 16 — ego/love-triangle karma; humility heals."),
    17: _bday("Business leader with reflective depth (1+7=8 with 7 flavour).",
              "चिंतनशील गहराई वाला व्यावसायिक नेता (1+7=8 में 7 की झलक)।",
              "Business leader with reflective depth (1+7=8 with 7 flavour)."),
    18: _bday("Humanitarian executive (1+8=9 with 8 drive).",
              "मानवतावादी कार्यकारी (1+8=9 में 8 की प्रेरणा)।",
              "Humanitarian executive (1+8=9 with 8 drive)."),
    19: _bday("⚠ Karmic-debt 19 — misuse-of-power lesson; learn interdependence.",
              "⚠ कर्म-ऋण 19 — शक्ति के दुरुपयोग का पाठ; पारस्परिकता सीखें।",
              "⚠ Karmic-debt 19 — misuse-of-power lesson; learn interdependence."),
    20: _bday("Hyper-sensitive diplomat (2+0=2 amplified).",
              "अति-संवेदनशील कूटनीतिज्ञ (2+0=2 प्रबल)।",
              "Hyper-sensitive diplomat (2+0=2 amplified)."),
    21: _bday("Creative partner — joy through cooperation (2+1=3).",
              "रचनात्मक सहयोगी — सहयोग के माध्यम से आनंद (2+1=3)।",
              "Creative partner — joy through cooperation (2+1=3)."),
    22: _bday("⭐ Master builder — grand-scale construction.",
              "⭐ मास्टर बिल्डर — भव्य-स्तरीय निर्माण।",
              "⭐ Master builder — grand-scale construction."),
    23: _bday("Royal Star of Lion — help from high places (2+3=5).",
              "सिंह का राजकीय तारा — ऊँचे स्थानों से सहायता (2+3=5)।",
              "Royal Star of Lion — high places se help (2+3=5)."),
    24: _bday("Love & gain through partnership (2+4=6).",
              "साझेदारी के माध्यम से प्रेम और लाभ (2+4=6)।",
              "Love & gain through partnership (2+4=6)."),
    25: _bday("Wisdom from observation (2+5=7).",
              "अवलोकन से बुद्धि (2+5=7)।",
              "Wisdom from observation (2+5=7)."),
    26: _bday("Karma of advisors — choose partners with care (2+6=8).",
              "सलाहकारों का कर्म — साझेदार सावधानी से चुनें (2+6=8)।",
              "Karma of advisors — partners carefully choose karo (2+6=8)."),
    27: _bday("Sceptre — command & authority (2+7=9).",
              "राजदंड — आदेश और अधिकार (2+7=9)।",
              "Sceptre — command & authority (2+7=9)."),
    28: _bday("Beware misplaced trust (2+8=10/1).",
              "गलत भरोसे से सावधान (2+8=10/1)।",
              "Misplaced trust se saavdhan (2+8=10/1)."),
    29: _bday("⭐ Master intuitive (2+9=11) — high sensitivity.",
              "⭐ मास्टर सहज-ज्ञानी (2+9=11) — उच्च संवेदनशीलता।",
              "⭐ Master intuitive (2+9=11) — high sensitivity."),
    30: _bday("Mental creativity — thinker-communicator (3+0=3).",
              "मानसिक रचनात्मकता — विचारक-संप्रेषक (3+0=3)।",
              "Mental creativity — thinker-communicator (3+0=3)."),
    31: _bday("Creative worker — art meets discipline (3+1=4).",
              "रचनात्मक कार्यकर्ता — कला अनुशासन से मिलती है (3+1=4)।",
              "Creative worker — art meets discipline (3+1=4)."),
}

# ─── 6. MATURITY NUMBER (activates after ~35 years) ──────────────────
MATURITY = {
    1: {"english": "After 35+: you step fully into leadership and original voice. Midlife-career shift to front-of-stage.",
        "hindi": "35+ के बाद: आप पूरी तरह नेतृत्व और मौलिक आवाज़ में आते हैं। मध्य-जीवन करियर मंच के सामने आता है।",
        "hinglish": "35+ ke baad: aap fully leadership aur original voice me aate ho. Midlife-career front-of-stage shift."},
    2: {"english": "After 35+: life softens you into mediator, healer, or quiet power. Peace becomes priority.",
        "hindi": "35+ के बाद: जीवन आपको मध्यस्थ, उपचारक, या शांत शक्ति में बदलता है। शांति प्राथमिकता बनती है।",
        "hinglish": "35+ ke baad: life aapko mediator, healer, quiet power me soften karti hai. Peace priority ban jati hai."},
    3: {"english": "After 35+: your creative voice finally finds mass audience. Late-bloom artists, authors, entertainers.",
        "hindi": "35+ के बाद: आपकी रचनात्मक आवाज़ अंततः बड़े दर्शकों तक पहुँचती है। देर से खिलने वाले कलाकार, लेखक।",
        "hinglish": "35+ ke baad: aapki creative voice finally mass audience pati hai. Late-bloom artists, authors."},
    4: {"english": "After 35+: you become the institution-builder, the steady hand people rely on for decades.",
        "hindi": "35+ के बाद: आप संस्था-निर्माता बनते हैं, वह स्थिर हाथ जिस पर लोग दशकों तक भरोसा करते हैं।",
        "hinglish": "35+ ke baad: aap institution-builder bante ho, woh steady haath jis par log dashakon bharosa karte hain."},
    5: {"english": "After 35+: freedom deepens into wisdom of many lives. You become the teacher of adaptability.",
        "hindi": "35+ के बाद: स्वतंत्रता कई जीवनों की बुद्धिमत्ता में गहराती है। आप अनुकूलनशीलता के शिक्षक बनते हैं।",
        "hinglish": "35+ ke baad: freedom kai lives ki wisdom me deep hoti hai. Aap adaptability ke teacher ban jaate ho."},
    6: {"english": "After 35+: family/community leadership intensifies. You become the elder everyone runs to.",
        "hindi": "35+ के बाद: परिवार/समुदाय नेतृत्व तीव्र होता है। आप वह बुज़ुर्ग बनते हैं जिसके पास सब दौड़ते हैं।",
        "hinglish": "35+ ke baad: family/community leadership intensify hoti hai. Aap woh elder bante ho jiske paas sab bhagte hain."},
    7: {"english": "After 35+: deep spiritual awakening, scholarly peak, or retreat into contemplation.",
        "hindi": "35+ के बाद: गहरी आध्यात्मिक जागृति, विद्वत्ता का शिखर, या चिंतन में वापसी।",
        "hinglish": "35+ ke baad: deep spiritual awakening, scholarly peak, ya contemplation me retreat."},
    8: {"english": "After 35+: peak wealth-power years. Business empire, political clout, financial mastery.",
        "hindi": "35+ के बाद: चरम धन-शक्ति वर्ष। व्यावसायिक साम्राज्य, राजनीतिक प्रभाव, वित्तीय महारत।",
        "hinglish": "35+ ke baad: peak wealth-power years. Business empire, political clout, financial mastery."},
    9: {"english": "After 35+: full humanitarian dharma kicks in. Charity, global causes, teacher-of-teachers.",
        "hindi": "35+ के बाद: पूर्ण मानवतावादी धर्म सक्रिय होता है। दान, वैश्विक कारण, शिक्षकों के शिक्षक।",
        "hinglish": "35+ ke baad: full humanitarian dharma activate hota hai. Charity, global causes, teacher-of-teachers."},
}

# ─── 7. BALANCE NUMBER (crisis-recovery) ─────────────────────────────
BALANCE = {
    1: {"english": "In crisis, claim your own power. Stop seeking permission — act alone.",
        "hindi": "संकट में, अपनी शक्ति का दावा करें। अनुमति माँगना बंद करें — अकेले कार्य करें।",
        "hinglish": "Crisis me, apni power claim karo. Permission maangna band karo — akele act karo."},
    2: {"english": "In crisis, slow down. Seek counsel. Cooperate instead of confronting.",
        "hindi": "संकट में, धीमे हों। सलाह लें। टकराने के बजाय सहयोग करें।",
        "hinglish": "Crisis me, slow down karo. Counsel lo. Confront karne ki jagah cooperate karo."},
    3: {"english": "In crisis, express — write, talk, create. Bottled emotions will break you.",
        "hindi": "संकट में, व्यक्त करें — लिखें, बोलें, रचें। दबी भावनाएँ तोड़ देंगी।",
        "hinglish": "Crisis me, express karo — likho, bolo, create karo. Bottled emotions tod denge."},
    4: {"english": "In crisis, build routine. Small daily steps. Stop reacting — structure your way out.",
        "hindi": "संकट में, दिनचर्या बनाएँ। रोज़ के छोटे कदम। प्रतिक्रिया बंद करें — संरचना से बाहर निकलें।",
        "hinglish": "Crisis me, routine banao. Small daily steps. React karna band karo — structure se bahar niklo."},
    5: {"english": "In crisis, change environment. Travel, pivot, try something new — stuck is worse than wrong.",
        "hindi": "संकट में, वातावरण बदलें। यात्रा करें, बदलें, कुछ नया करें — फँसना ग़लत से बुरा है।",
        "hinglish": "Crisis me, environment change karo. Travel, pivot, naya kuch try karo — stuck hona galat se bura hai."},
    6: {"english": "In crisis, serve someone else. Helping others resets your own pain.",
        "hindi": "संकट में, किसी और की सेवा करें। दूसरों की सहायता आपके अपने दर्द को रीसेट करती है।",
        "hinglish": "Crisis me, kisi aur ki seva karo. Dusron ki help aapke apne pain ko reset karti hai."},
    7: {"english": "In crisis, retreat, reflect, research. Solitude is medicine — 7-day silence resets everything.",
        "hindi": "संकट में, पीछे हटें, चिंतन करें, शोध करें। एकांत औषधि है — 7-दिन मौन सब रीसेट करता है।",
        "hinglish": "Crisis me, retreat karo, reflect karo, research karo. Solitude medicine hai — 7-din silence sab reset karta hai."},
    8: {"english": "In crisis, take control. Audit finances, cut dead weight, rebuild with executive discipline.",
        "hindi": "संकट में, नियंत्रण लें। वित्त ऑडिट करें, मृत-वज़न काटें, कार्यकारी अनुशासन से पुनर्निर्माण करें।",
        "hinglish": "Crisis me, control lo. Finances audit karo, dead weight cut karo, executive discipline se rebuild karo."},
    9: {"english": "In crisis, let go. Forgive, release, give away. What leaves makes room for what's coming.",
        "hindi": "संकट में, छोड़ दें। क्षमा करें, मुक्त करें, दान दें। जो जाता है, वह आने वाले के लिए स्थान बनाता है।",
        "hinglish": "Crisis me, let go karo. Forgive karo, release karo, daan do. Jo jaata hai, woh aane waale ke liye jagah banata hai."},
}

# ─── 8. KARMIC DEBT — 13/14/16/19 (from extended.py but richer 3-lang) ──
KARMIC_DEBT_DETAIL = {
    13: {
        "english": "Past-life karma: you cut corners, took shortcuts. This life: your success will come ONLY through sustained, unglamorous hard work. Impatience is the biggest trap. Build one brick at a time; refuse get-rich-quick schemes; finish what you start.",
        "hindi": "पूर्व-जन्म कर्म: आपने शॉर्टकट लिए, कोने काटे। इस जीवन: सफलता केवल निरंतर, बिना चमक-दमक के कठोर परिश्रम से आएगी। अधीरता सबसे बड़ा जाल है। एक-एक ईंट रखें; जल्दी-अमीर-बनो योजनाएँ छोड़ें; जो शुरू किया पूरा करें।",
        "hinglish": "Past-life karma: aapne shortcuts liye, corners kaate. Iss life: success SIRF sustained, bina glamour ke hard work se aayegi. Impatience sabse bada trap hai. Ek-ek brick rakho; get-rich-quick schemes se bacho; jo shuru kiya woh poora karo.",
    },
    14: {
        "english": "Past-life karma: you misused freedom — addictions, unfaithfulness, excess. This life: you'll face temptations repeatedly. Moderation is your curriculum. Do NOT escape through alcohol, drugs, constant novelty. Anchor yourself; commit.",
        "hindi": "पूर्व-जन्म कर्म: आपने स्वतंत्रता का दुरुपयोग किया — व्यसन, बेवफ़ाई, अति। इस जीवन: प्रलोभन बार-बार सामने आएँगे। संयम आपका पाठ्यक्रम है। शराब, ड्रग्स, निरंतर नवीनता से पलायन मत करें। स्वयं को स्थिर करें; प्रतिबद्ध हों।",
        "hinglish": "Past-life karma: aapne freedom ka misuse kiya — addictions, unfaithfulness, excess. Iss life: temptations baar-baar aayenge. Moderation aapka curriculum hai. Alcohol, drugs, constant novelty se escape mat karo. Khud ko anchor karo; commit karo.",
    },
    16: {
        "english": "Past-life karma: ego-abuse, love-triangles, falls from high places. This life: sudden dramatic upheavals are likely — breakups, firings, scandals. Each fall is a chance to rebuild on humility. Avoid vanity; admit mistakes fast; forgive others fast.",
        "hindi": "पूर्व-जन्म कर्म: अहंकार-दुरुपयोग, प्रेम-त्रिकोण, ऊँचाई से गिरना। इस जीवन: अचानक नाटकीय उलट-पुलट संभव — रिश्ते टूटना, नौकरी जाना, घोटाले। हर गिरावट विनम्रता पर पुनर्निर्माण का अवसर है। घमंड से बचें; गलतियाँ तुरंत स्वीकारें; तुरंत क्षमा करें।",
        "hinglish": "Past-life karma: ego-abuse, love-triangles, falls from high places. Iss life: sudden dramatic upheavals likely — breakups, firings, scandals. Har fall humility par rebuild ka chance hai. Vanity se bacho; galtiyan turant admit karo; turant forgive karo.",
    },
    19: {
        "english": "Past-life karma: misused power, isolated yourself, refused help. This life: you'll be FORCED to ask for help, learn interdependence. Don't be the 'lone wolf' hero — build teams, accept mentorship, share credit.",
        "hindi": "पूर्व-जन्म कर्म: शक्ति का दुरुपयोग, स्वयं को अलग किया, मदद से इनकार। इस जीवन: आपको मदद माँगने, पारस्परिकता सीखने के लिए मजबूर किया जाएगा। 'अकेले भेड़िए' हीरो मत बनें — टीम बनाएँ, मार्गदर्शन स्वीकारें, श्रेय बाँटें।",
        "hinglish": "Past-life karma: power ka misuse, khud ko isolate kiya, help refuse ki. Iss life: aap help maangne, interdependence seekhne ke liye FORCED honge. 'Lone wolf' hero mat bano — teams banao, mentorship accept karo, credit share karo.",
    },
}

# ─── 9. KARMIC LESSONS (missing numbers from full name) ──────────────
KARMIC_LESSON = {
    1: {"english": "No 1 in name: learn independence, self-assertion, standing alone when needed.",
        "hindi": "नाम में 1 नहीं: स्वतंत्रता, आत्म-प्रतिपादन, अकेले खड़े होना सीखें।",
        "hinglish": "Naam me 1 nahi: independence, self-assertion, zarurat par akele khade hona seekho."},
    2: {"english": "No 2 in name: learn patience, cooperation, emotional attunement, sharing power.",
        "hindi": "नाम में 2 नहीं: धैर्य, सहयोग, भावनात्मक संलग्नता, शक्ति साझा करना सीखें।",
        "hinglish": "Naam me 2 nahi: patience, cooperation, emotional attunement, power share karna seekho."},
    3: {"english": "No 3 in name: learn to express joy, communicate openly, embrace creativity.",
        "hindi": "नाम में 3 नहीं: आनंद व्यक्त करना, खुलकर संप्रेषण, रचनात्मकता अपनाना सीखें।",
        "hinglish": "Naam me 3 nahi: joy express karna, openly communicate karna, creativity embrace karna seekho."},
    4: {"english": "No 4 in name: learn discipline, organization, finishing what you start.",
        "hindi": "नाम में 4 नहीं: अनुशासन, संगठन, जो शुरू किया पूरा करना सीखें।",
        "hinglish": "Naam me 4 nahi: discipline, organization, jo shuru kiya poora karna seekho."},
    5: {"english": "No 5 in name: learn adaptability, letting go, embracing change and travel.",
        "hindi": "नाम में 5 नहीं: अनुकूलन, छोड़ना, बदलाव और यात्रा अपनाना सीखें।",
        "hinglish": "Naam me 5 nahi: adaptability, let go karna, change aur travel embrace karna seekho."},
    6: {"english": "No 6 in name: learn responsibility, caring for family, committing to service.",
        "hindi": "नाम में 6 नहीं: उत्तरदायित्व, परिवार की देखभाल, सेवा में प्रतिबद्धता सीखें।",
        "hinglish": "Naam me 6 nahi: responsibility, family ki care, seva me commitment seekho."},
    7: {"english": "No 7 in name: learn introspection, study, trusting inner wisdom over external noise.",
        "hindi": "नाम में 7 नहीं: अंतर्मुखता, अध्ययन, बाहरी शोर से ऊपर भीतरी ज्ञान पर भरोसा करना सीखें।",
        "hinglish": "Naam me 7 nahi: introspection, study, bahari noise se upar inner wisdom par trust karna seekho."},
    8: {"english": "No 8 in name: learn money management, owning power, refusing to play small.",
        "hindi": "नाम में 8 नहीं: धन-प्रबंधन, शक्ति का स्वामित्व, छोटा खेलने से इनकार सीखें।",
        "hinglish": "Naam me 8 nahi: money management, power ka ownership, chhota khelne se inkaar seekho."},
    9: {"english": "No 9 in name: learn compassion, letting go of personal attachments for larger service.",
        "hindi": "नाम में 9 नहीं: करुणा, बड़ी सेवा के लिए व्यक्तिगत लगाव छोड़ना सीखें।",
        "hinglish": "Naam me 9 nahi: compassion, bigger seva ke liye personal attachments let-go karna seekho."},
}

# ─── 10. HIDDEN PASSION (most-repeated letter value in name) ─────────
HIDDEN_PASSION = {
    1: {"english": "Secret drive: leadership and originality. You REALLY want to be first — even when you pretend otherwise.",
        "hindi": "गुप्त प्रेरणा: नेतृत्व और मौलिकता। आप वास्तव में पहले बनना चाहते हैं — भले ही दिखावा कुछ और करें।",
        "hinglish": "Secret drive: leadership aur originality. Aap REALLY first banna chahte ho — chahe dikhava kuch aur ho."},
    2: {"english": "Secret drive: deep partnership and peace. You'd trade almost anything for emotional harmony.",
        "hindi": "गुप्त प्रेरणा: गहरी साझेदारी और शांति। आप भावनात्मक सौहार्द के लिए लगभग कुछ भी बदल देंगे।",
        "hinglish": "Secret drive: deep partnership aur peace. Aap emotional harmony ke liye lagbhag kuch bhi trade kar doge."},
    3: {"english": "Secret drive: to be seen, celebrated, adored. Stage-love is in your blood, even if shy outwardly.",
        "hindi": "गुप्त प्रेरणा: देखे जाना, मनाया जाना, सराहा जाना। मंच-प्रेम आपके रक्त में है, भले ही बाहर से शर्मीले।",
        "hinglish": "Secret drive: dekhe jaana, celebrated hona, adored hona. Stage-love aapke blood me hai, chahe outwardly shy ho."},
    4: {"english": "Secret drive: build an unshakeable fortress. Security, order, permanence obsess you quietly.",
        "hindi": "गुप्त प्रेरणा: अटल किला बनाना। सुरक्षा, व्यवस्था, स्थायित्व चुपचाप आपको ग्रस्त करते हैं।",
        "hinglish": "Secret drive: unshakeable fortress banana. Security, order, permanence aapko chupke obsess karte hain."},
    5: {"english": "Secret drive: taste everything. You fear a boring life more than you fear failure.",
        "hindi": "गुप्त प्रेरणा: सब कुछ चखना। आप असफलता से अधिक उबाऊ जीवन से डरते हैं।",
        "hinglish": "Secret drive: sab kuch chakhna. Aap failure se zyada boring life se darte ho."},
    6: {"english": "Secret drive: to love and be loved unconditionally. Family/home is your sanctuary.",
        "hindi": "गुप्त प्रेरणा: बिना शर्त प्रेम करना और पाया जाना। परिवार/घर आपकी शरणस्थली है।",
        "hinglish": "Secret drive: unconditional love karna aur paana. Family/home aapka sanctuary hai."},
    7: {"english": "Secret drive: uncover THE truth. You'd walk through fire to understand something no one else gets.",
        "hindi": "गुप्त प्रेरणा: 'वह' सत्य उजागर करना। आप आग से गुज़रेंगे ऐसी बात समझने को जो कोई और नहीं समझता।",
        "hinglish": "Secret drive: 'THE' truth uncover karna. Aap aag se guzar jaoge kuch aisa samajhne ko jo aur koi nahi samajhta."},
    8: {"english": "Secret drive: power, money, legacy. You want to control your own empire — period.",
        "hindi": "गुप्त प्रेरणा: शक्ति, धन, विरासत। आप अपने साम्राज्य को नियंत्रित करना चाहते हैं — बस।",
        "hinglish": "Secret drive: power, paisa, legacy. Aap apna empire control karna chahte ho — bas."},
    9: {"english": "Secret drive: heal the world. Personal problems feel small compared to collective pain.",
        "hindi": "गुप्त प्रेरणा: संसार का उपचार। व्यक्तिगत समस्याएँ सामूहिक पीड़ा की तुलना में छोटी लगती हैं।",
        "hinglish": "Secret drive: duniya ko heal karna. Personal problems collective pain ke saamne chhoti lagti hain."},
}

# ─── 11. PERSONAL YEAR THEMES (deep version of extended.py's short map) ──
PERSONAL_YEAR = {
    1: {"english": "NEW BEGINNINGS. Plant seeds. Start ventures, change jobs, move cities. Avoid waiting — this is launch year. Keyword: INITIATE.",
        "hindi": "नई शुरुआत। बीज बोएँ। उद्यम शुरू करें, नौकरी बदलें, शहर बदलें। इंतज़ार न करें — यह शुभारंभ वर्ष है। कीवर्ड: आरंभ।",
        "hinglish": "NEW BEGINNINGS. Seeds plant karo. Ventures start karo, jobs change karo, cities move karo. Wait mat karo — yeh launch year hai. Keyword: INITIATE."},
    2: {"english": "PARTNERSHIP. Patience, cooperation, behind-the-scenes work. Don't force outcomes. Strengthen relationships; details matter. Keyword: WAIT & WEAVE.",
        "hindi": "साझेदारी। धैर्य, सहयोग, परदे के पीछे का कार्य। परिणाम थोपें नहीं। रिश्ते मज़बूत करें; विवरण मायने रखते हैं। कीवर्ड: प्रतीक्षा और बुनाई।",
        "hinglish": "PARTNERSHIP. Patience, cooperation, behind-the-scenes work. Outcomes force mat karo. Rishte strengthen karo; details matter karte hain. Keyword: WAIT & WEAVE."},
    3: {"english": "EXPRESSION. Creative year — write, publish, perform, socialize. Travel, romance, joy expand. Avoid scattering energy. Keyword: EXPRESS.",
        "hindi": "अभिव्यक्ति। रचनात्मक वर्ष — लिखें, प्रकाशित करें, प्रदर्शन करें, सामाजिक बनें। यात्रा, प्रेम, आनंद बढ़ेंगे। ऊर्जा बिखरने से बचें। कीवर्ड: अभिव्यक्त।",
        "hinglish": "EXPRESSION. Creative year — likho, publish karo, perform karo, socialize karo. Travel, romance, joy expand. Energy scatter mat karo. Keyword: EXPRESS."},
    4: {"english": "FOUNDATION. Build structure. Work hard, save money, fix health, create systems. Boring but pivotal. Keyword: BUILD.",
        "hindi": "आधार। संरचना बनाएँ। कठोर परिश्रम, बचत, स्वास्थ्य सुधारें, प्रणालियाँ बनाएँ। उबाऊ पर महत्वपूर्ण। कीवर्ड: निर्माण।",
        "hinglish": "FOUNDATION. Structure banao. Hard work, savings, health fix, systems create. Boring par pivotal. Keyword: BUILD."},
    5: {"english": "CHANGE. Travel, pivot careers, end what doesn't serve. Surprises abound — embrace. Avoid addictions. Keyword: SHIFT.",
        "hindi": "परिवर्तन। यात्रा, करियर परिवर्तन, जो सेवा न करे उसे समाप्त करें। आश्चर्यों से भरा — अपनाएँ। व्यसनों से बचें। कीवर्ड: परिवर्तन।",
        "hinglish": "CHANGE. Travel, careers pivot, jo serve na kare woh end. Surprises abound — embrace karo. Addictions se bacho. Keyword: SHIFT."},
    6: {"english": "RESPONSIBILITY. Family, home, marriage, service come to the fore. Big decisions about relationships and home. Keyword: COMMIT.",
        "hindi": "उत्तरदायित्व। परिवार, घर, विवाह, सेवा सामने आते हैं। रिश्तों और घर के बारे में बड़े निर्णय। कीवर्ड: प्रतिबद्धता।",
        "hinglish": "RESPONSIBILITY. Family, home, marriage, seva saamne aate hain. Relationships aur ghar ke baare me bade decisions. Keyword: COMMIT."},
    7: {"english": "INTROSPECTION. Study, retreat, research, spirituality. Avoid forcing career or relationship changes. Go inside. Keyword: REFLECT.",
        "hindi": "अंतर्मुखता। अध्ययन, एकांत, शोध, आध्यात्मिकता। करियर या रिश्ते में परिवर्तन थोपने से बचें। भीतर जाएँ। कीवर्ड: चिंतन।",
        "hinglish": "INTROSPECTION. Study, retreat, research, spirituality. Career ya relationship changes force mat karo. Andar jao. Keyword: REFLECT."},
    8: {"english": "HARVEST. Money, power, recognition, business expansion peak. Do deals. Ask for promotion. Collect what you've sown. Keyword: COLLECT.",
        "hindi": "फसल। धन, शक्ति, पहचान, व्यावसायिक विस्तार चरम पर। सौदे करें। पदोन्नति माँगें। जो बोया है उसे इकट्ठा करें। कीवर्ड: संग्रह।",
        "hinglish": "HARVEST. Paisa, power, recognition, business expansion peak. Deals karo. Promotion maango. Jo boya hai woh collect karo. Keyword: COLLECT."},
    9: {"english": "COMPLETION. Endings, letting go, charity, release. Clear out what's done — year of transition. New 9-year cycle begins next year. Keyword: RELEASE.",
        "hindi": "समापन। अंत, छोड़ना, दान, मुक्ति। जो पूरा हो गया उसे साफ़ करें — संक्रमण वर्ष। अगले वर्ष नया 9-वर्षीय चक्र शुरू। कीवर्ड: मुक्ति।",
        "hinglish": "COMPLETION. Endings, let-go, charity, release. Jo done hai clear karo — transition year. Agle saal naya 9-year cycle shuru. Keyword: RELEASE."},
}

# ─── 12. PINNACLES (short phrase per number) ─────────────────────────
PINNACLE = {
    1: {"english": "Era of independence, self-starting, bold leadership.",
        "hindi": "स्वतंत्रता, आत्म-प्रारंभ, साहसी नेतृत्व का युग।",
        "hinglish": "Independence, self-starting, bold leadership ka era."},
    2: {"english": "Era of partnership, emotional growth, behind-scenes influence.",
        "hindi": "साझेदारी, भावनात्मक विकास, पर्दे-के-पीछे प्रभाव का युग।",
        "hinglish": "Partnership, emotional growth, behind-scenes influence ka era."},
    3: {"english": "Era of creativity, expression, social visibility, romance.",
        "hindi": "रचनात्मकता, अभिव्यक्ति, सामाजिक दृश्यता, प्रेम का युग।",
        "hinglish": "Creativity, expression, social visibility, romance ka era."},
    4: {"english": "Era of hard work, foundation-building, discipline, slow gains.",
        "hindi": "कठोर परिश्रम, आधार-निर्माण, अनुशासन, धीमे लाभ का युग।",
        "hinglish": "Hard work, foundation-building, discipline, slow gains ka era."},
    5: {"english": "Era of change, travel, freedom, variety, learning.",
        "hindi": "परिवर्तन, यात्रा, स्वतंत्रता, विविधता, सीखने का युग।",
        "hinglish": "Change, travel, freedom, variety, learning ka era."},
    6: {"english": "Era of family, love, responsibility, home-focus.",
        "hindi": "परिवार, प्रेम, उत्तरदायित्व, घर-केंद्र का युग।",
        "hinglish": "Family, love, responsibility, home-focus ka era."},
    7: {"english": "Era of study, inner work, spirituality, specialization.",
        "hindi": "अध्ययन, आंतरिक कार्य, आध्यात्मिकता, विशेषज्ञता का युग।",
        "hinglish": "Study, inner work, spirituality, specialization ka era."},
    8: {"english": "Era of peak wealth, power, authority, recognition.",
        "hindi": "चरम धन, शक्ति, प्राधिकार, पहचान का युग।",
        "hinglish": "Peak wealth, power, authority, recognition ka era."},
    9: {"english": "Era of completion, humanitarian work, releasing the old.",
        "hindi": "समापन, मानवतावादी कार्य, पुराने से मुक्ति का युग।",
        "hinglish": "Completion, humanitarian work, purane se mukti ka era."},
    11: {"english": "⭐ Era of spiritual awakening, master-intuition, inspiring others.",
         "hindi": "⭐ आध्यात्मिक जागृति, मास्टर-सहज-ज्ञान, दूसरों को प्रेरित करने का युग।",
         "hinglish": "⭐ Spiritual awakening, master-intuition, dusron ko inspire karne ka era."},
    22: {"english": "⭐ Era of master-building, large-scale construction, legacy.",
         "hindi": "⭐ मास्टर-निर्माण, बड़े-स्तर निर्माण, विरासत का युग।",
         "hinglish": "⭐ Master-building, bade scale construction, legacy ka era."},
    33: {"english": "⭐ Era of master-teaching, selfless service, divine healing.",
         "hindi": "⭐ मास्टर-शिक्षण, निस्वार्थ सेवा, दिव्य उपचार का युग।",
         "hinglish": "⭐ Master-teaching, selfless seva, divine healing ka era."},
}

# ─── 13. CHALLENGES (short lesson per number, incl 0) ────────────────
CHALLENGE = {
    0: {"english": "Open challenge — choose your own lesson; highest freedom & highest risk.",
        "hindi": "खुली चुनौती — अपना पाठ स्वयं चुनें; सर्वोच्च स्वतंत्रता व उच्चतम जोखिम।",
        "hinglish": "Open challenge — apna lesson khud choose karo; highest freedom & highest risk."},
    1: {"english": "Lesson: stand on your own feet; stop waiting for permission.",
        "hindi": "पाठ: अपने पैरों पर खड़े हों; अनुमति का इंतज़ार बंद करें।",
        "hinglish": "Lesson: apne pairon par khade ho; permission ka wait band karo."},
    2: {"english": "Lesson: stop over-reacting to criticism; develop emotional thickness.",
        "hindi": "पाठ: आलोचना पर अति-प्रतिक्रिया बंद करें; भावनात्मक मोटाई विकसित करें।",
        "hinglish": "Lesson: criticism par over-react mat karo; emotional thickness develop karo."},
    3: {"english": "Lesson: stop scattering; finish one creative project deeply.",
        "hindi": "पाठ: बिखराव बंद करें; एक रचनात्मक परियोजना गहराई से पूरी करें।",
        "hinglish": "Lesson: scatter mat karo; ek creative project deeply finish karo."},
    4: {"english": "Lesson: stop rigidity; learn to flex when facts change.",
        "hindi": "पाठ: कठोरता त्यागें; तथ्य बदलने पर मोड़ना सीखें।",
        "hinglish": "Lesson: rigidity chhodo; facts change hone par flex karna seekho."},
    5: {"english": "Lesson: stop running; commit to ONE thing long enough to see results.",
        "hindi": "पाठ: भागना बंद करें; एक बात के लिए इतनी देर प्रतिबद्ध हों कि परिणाम दिखें।",
        "hinglish": "Lesson: bhagna band karo; ek cheez ko itna commit karo ki results dikhen."},
    6: {"english": "Lesson: stop over-giving; set boundaries; receive as much as you give.",
        "hindi": "पाठ: अति-देना बंद करें; सीमाएँ तय करें; जितना देते हैं उतना पाएँ।",
        "hinglish": "Lesson: over-giving band karo; boundaries set karo; jitna do utna receive bhi karo."},
    7: {"english": "Lesson: stop isolating; open up — share your analysis with others.",
        "hindi": "पाठ: अलगाव बंद करें; खुलें — अपना विश्लेषण दूसरों से बाँटें।",
        "hinglish": "Lesson: isolate karna band karo; open up — apna analysis dusron se share karo."},
    8: {"english": "Lesson: stop equating worth with money; balance material with spiritual.",
        "hindi": "पाठ: धन से मूल्य जोड़ना बंद करें; भौतिक को आध्यात्मिक से संतुलित करें।",
        "hinglish": "Lesson: worth ko paise se equate karna band karo; material ko spiritual se balance karo."},
    9: {"english": "Lesson: stop martyring; remember you are worthy of receiving too.",
        "hindi": "पाठ: शहीद बनना बंद करें; याद रखें आप भी पाने के योग्य हैं।",
        "hinglish": "Lesson: martyr banna band karo; yaad rakho aap bhi receive karne ke worthy ho."},
}


# ── Helper: safe-get with fallback to hinglish ──────────────────────
def t1_get(table: Dict[Any, Dict[str, str]], key: Any, lang: str) -> str:
    lang = (lang or "hinglish").lower()
    row = table.get(key)
    if not row:
        return ""
    return row.get(lang) or row.get("hinglish") or row.get("english") or ""
