"""
numerology/narratives.py — Premium narrative content engine.

Deep, story-style content per driver number (1-9) covering:
  - life_essence       (3-paragraph personality story)
  - career_pattern     (work types, growth timing, common mistakes)
  - love_pattern       (relationship style, breakup triggers)
  - ideal_partner      (what to look for in a partner)
  - money_pattern      (how money flows / blocks)
  - health_pattern     (body weakness areas)
  - spiritual_path     (dharma direction)
  - strengths          (5 hidden powers)
  - challenges         (5 hidden traps)
  - risk_alerts        (5 specific warnings)
  - golden_periods     (when life opens up)
  - 2026_focus         (this year's priority)

100% deterministic — pre-written by classical numerology framework
(Cheiro + Sepharial + L. Ron Roy + Indian numerology school).
"""

from typing import Dict, Any, List


_NARRATIVES: Dict[int, Dict[str, Any]] = {

    1: {
        "title": "The Sovereign — Sun-ruled Leader",
        "tagline": "Aap iss duniya me lead karne ke liye paida hue ho.",
        "life_essence": [
            "Aapka jeevan ek hi sutra par chalta hai — 'Mai apne tareeke se karunga.' "
            "Number 1 ka swami Surya hai, aur Surya kabhi kisi ke peeche nahi chalta — "
            "use sirf khud ka path dikhta hai. Bachpan se aapko mehsoos hua hoga ki aap "
            "bheed me ghul-mil nahi paate, kyunki andar se aap leader ho — follower nahi.",

            "Aapki sabse badi taakat hai — vision aur original thinking. Jab baki log "
            "'kaise hoga' soch rahe hote hain, tab aap 'kab hoga' soch rahe hote ho. "
            "Yeh quality aapko har field me top-3 me le ja sakti hai. Lekin yahi quality "
            "kabhi-kabhi rishton me akela bhi kar deti hai — kyunki har koi aapki speed "
            "par nahi chal sakta.",

            "Surya ka ek important message hai — 'tej (brilliance) chhupayi nahi jaati'. "
            "Agar aap apni light ko damp kar ke baki logo ko comfort dene ki koshish "
            "karoge, toh aapki life me dimness aa jaayegi. Aapko apne tej ke saath jeena "
            "seekhna hai — politely, par firmly.",
        ],
        "career_pattern": [
            "Aap servant nature ke liye nahi bane — boss ya independent professional banoge. "
            "Best fields: business owner, government leader, doctor (especially heart/eye), "
            "politics, military officer, civil services, executive coaching, jewellery trade, "
            "construction. Aapko aisa role chahiye jaha aap final decision le sako.",

            "Common mistake: Job karte waqt aap ego clash me phasoge — boss ke saath. "
            "Solution: 30 ki age ke baad job chodke apna kuch start karna hi sahi hai. "
            "Surya ki energy 'employee' role me suffocate hoti hai.",

            "Growth timing: 22-24 (foundation), 28-32 (first big break), 36-40 (peak power), "
            "45-50 (legacy phase). Sunday aapka power day hai — important meetings/launches "
            "Sunday subah karein.",
        ],
        "love_pattern": [
            "Love me aap intense ho — half-heart relationship aap nahi nibha sakte. "
            "Jab pyar karte ho toh poora karte ho, jab break karte ho toh bhi poora.",

            "Breakup ka common reason: aap dominate karne lagte ho, aur partner suffocate "
            "feel karta hai. Ya partner aapko 'change' karne ki koshish karta hai — jo "
            "Number 1 kabhi tolerate nahi karta.",

            "Ideal partner: Number 2, 4, ya 7 walo ke saath best — woh aapki energy ko "
            "ground karte hain. Number 1 + Number 1 explosive hai (twin sun = burn).",
        ],
        "money_pattern":
            "Paisa aapke paas zigzag pattern me aata hai — kabhi flood, kabhi drought. "
            "Aapko fixed salary kabhi satisfy nahi karegi. Stocks, business, real estate me "
            "invest kare. Gold (Surya ka metal) aapke liye lucky storage hai.",
        "health_pattern":
            "Heart, eyes, blood pressure, aur back ka dhyaan rakhe — Surya ke under aate hain. "
            "Subah surya namaskar 7 baar daily karein — direct planetary tonic.",
        "spiritual_path":
            "Aapka dharma hai 'awakening others through your own light'. Spiritual practice me "
            "Aditya Hridaya Stotra (Sundays) bahut shakti deta hai. Guru ban'na aapka path hai.",
        "strengths": [
            "Vision — aap 5 saal aage dekh sakte ho",
            "Decision speed — analysis paralysis nahi hoti",
            "Magnetism — log aapki taraf naturally khinche aate hain",
            "Original thinking — copy-paste nahi karte",
            "Crisis leadership — emergency me aap calm rehte ho",
        ],
        "challenges": [
            "Ego clashes with authority figures (boss, father)",
            "Loneliness at the top — koi peer level nahi milta",
            "Impatience with slow people",
            "Tendency to overrule advice",
            "Pride me criticism handle nahi kar paate",
        ],
        "risk_alerts": [
            "Father-figure se conflict 28-32 ke beech possible — patience zaruri",
            "Heart health 40 ke baad strict watch — annual check-up mandatory",
            "Partnership business avoid kare jab tak agreement crystal-clear na ho",
            "Aapko 'haan-ji' wale log magnet karte hain — they will betray eventually",
            "Aap Sunday ko impulse buying karte ho — bada decision Tuesday lo",
        ],
        "golden_periods":
            "Sun-strong years aapke peak hain. Jab bhi Personal Year 1, 5, ya 9 aaye — "
            "wahi launch year hai. 2026 specifically: Personal Year calculate kar ke decide. "
            "Mid-March se mid-July aapke liye yearly power window hai (Sun exalted in Aries).",
    },

    2: {
        "title": "The Diplomat — Moon-blessed Connector",
        "tagline": "Aap iss duniya ke unsung healers ho.",
        "life_essence": [
            "Number 2 ka swami Chandra hai — aur Chandra ki energy fluid hai, reflective hai. "
            "Aap kisi ke saath baith ke 5 minute baat karein, aur unki body language uthake "
            "imitate kar sakte ho. Yeh empathy aapki sabse badi gift hai aur sabse bada "
            "burden bhi.",

            "Aap akele logon ko kheech lete ho — emotional, broken, ya confused log "
            "aapko 'safe' feel karte hain. Yeh accident nahi hai. Aap natural counsellor ho. "
            "Lekin iska price ye hai ki aap khud apni emotional needs ko ignore kar dete ho.",

            "Chandra ka sabse important sabaq hai — 'phases'. Aap har 28 din me poori "
            "emotional cycle se gujarte ho — ek week high, ek week medium, ek week low, "
            "ek week recovery. Iss cycle ko fight nahi karna — flow karna seekho.",
        ],
        "career_pattern": [
            "Best fields: counselling, HR, nursing, hospitality, food/dairy business, "
            "writing (especially fiction/poetry), psychology, social work, navy, marine work, "
            "interior design. Public-facing emotional roles me aap shine karte ho.",

            "Common mistake: Aggressive sales ya competitive corporate jobs me aap drain "
            "ho jaate ho. 4-5 saal me burnout hota hai. Aapke liye long-term + emotional "
            "rewards wala kaam hi tikta hai.",

            "Growth timing: Slow burn — 32-38 me aapka peak aata hai (not before). Until "
            "then groundwork. Monday aapka power day — major emotional decisions Monday "
            "subah lo.",
        ],
        "love_pattern": [
            "Love me aap give-give-give karte ho. Partner ki needs aapki needs se pehle "
            "aati hain. Yeh sundar hai but unsustainable.",

            "Breakup ka common reason: Aap apne emotions express nahi karte, internalize "
            "karte ho — aur ek din suddenly 'I'm done' bolte ho. Partner shocked rehta hai "
            "kyunki signals miss the. Lesson: chhoti baat bhi bolo.",

            "Ideal partner: Number 1, 4, ya 8 — woh structure dete hain jo Moon ko chahiye. "
            "Number 5 + 2 turbulent hai (mercury moves moon too much).",
        ],
        "money_pattern":
            "Paisa aapke paas tides ki tarah aata-jaata rehta hai. Savings habit forcefully "
            "develop kare — automatic SIP best hai. Silver, pearl, white items me invest "
            "kare. Liquid emergency fund 6 mahine ka rakho — Moon ko surakshit feel chahiye.",
        "health_pattern":
            "Stomach, breast (women), lungs, sleep cycle — Chandra ke under. Avoid late "
            "nights. Full moon par detox water peeke jaldi sona — body mein swelling kam hogi.",
        "spiritual_path":
            "Aapka dharma hai 'emotional purification of others'. Mata pooja, Devi worship, "
            "Lakshmi sadhana — sab Chandra-friendly. Monday vrat 16 saptah karein — "
            "transformative.",
        "strengths": [
            "Empathy — aap log ke andar dekh lete ho",
            "Diplomacy — conflict ko resolve karna aata hai",
            "Adaptability — har situation me dhal jate ho",
            "Aesthetic sense — beauty ka tek deep samajh",
            "Patience — long game me jeet aapki hai",
        ],
        "challenges": [
            "Mood swings — 28-day cycle hard to manage",
            "Over-giving leads to resentment",
            "Avoidance of confrontation",
            "Indecision at critical moments",
            "Emotional eating ya emotional spending",
        ],
        "risk_alerts": [
            "Mother ya female elder ki health par dhyaan rakho — karmic connection deep",
            "Water-related travel me extra savdhani — life-path par water symbolic",
            "Toxic friendships me 5+ saal stuck ho sakte ho — annual relationship audit",
            "Depression me jaane ki tendency — counsellor se sympathize karne wala milein",
            "Late-night decisions kabhi mat lo — Moon weak hota hai raat ko",
        ],
        "golden_periods":
            "Personal Year 2, 4, 6, ya 8 me aapki life unfold hoti hai. Full moon ke 3 din "
            "pehle aur baad aapki manifestation power peak par hoti hai — important wishes "
            "ya intentions us window me set karein. October-November aapka yearly soft "
            "power window (Chandra exalted in Taurus).",
    },

    3: {
        "title": "The Sage — Jupiter's Wisdom Carrier",
        "tagline": "Aap knowledge ko wealth me convert karne wale ho.",
        "life_essence": [
            "Number 3 ka swami Brihaspati (Jupiter) hai — guru graha. Aap janam se hi old "
            "soul ho. Bachpan me logon ne kaha hoga 'tu apni umar se zyada matured hai'. "
            "Yeh accident nahi hai — aapki soul kayi janma se gyan ke saath aayi hai.",

            "Aapko teaching, sharing, expanding aata hai. Jab koi confused hota hai aapke "
            "saamne, aap automatically philosophical ban jaate ho — 'isko aise dekho' wala "
            "framing aap unconsciously dete ho. Yeh aapka swadharma hai.",

            "Jupiter ki ek warning hai — 'over-expansion'. Aap kabhi-kabhi itna jaante ho "
            "ki kuch bhi confidently bol dete ho — bina deep verify kiye. Yeh ego gap aapko "
            "bada nuksaan kara sakta hai. Humility + knowledge = aapka golden combination.",
        ],
        "career_pattern": [
            "Best fields: teaching, law, finance/banking, publishing, religion/spirituality, "
            "journalism, research, judiciary, advisory roles, content creation, philosophy, "
            "venture capital. Wahan jaha 'wisdom = wealth' equation chalti hai.",

            "Common mistake: Practical execution ki taraf laparvaah — sirf advise dene me "
            "khush rehte ho, khud karna kam hota hai. Result: log aapse seekhke aage "
            "nikal jaate hain, aap waha ke waha. Solution: ek-do projects khud poori "
            "tarah execute karein, theory + practice dono.",

            "Growth timing: 24-27 first wisdom phase, 33-36 peak teaching phase, 45-50 "
            "legacy + wealth phase. Thursday aapka power day. Brihaspati hora me start "
            "kiya kaam phalta hai.",
        ],
        "love_pattern": [
            "Love me aap mentor ban jaate ho — partner ko 'guide' karte ho. Yeh seductive "
            "hai initially, par long-term me partner suffocate hota hai (kaun parent "
            "chahta hai partner ke roop me?).",

            "Breakup reason: 'I outgrew you' wali feeling. Aapki growth fast hoti hai, "
            "partner peeche reh jaata hai. Solution: partner ko bhi grow hone ka space "
            "dijiye, sirf aap hi nahi.",

            "Ideal partner: Number 6, 9, ya 3 — same wisdom-wavelength wale. Number 5 + 3 "
            "intellectually brilliant but emotionally turbulent.",
        ],
        "money_pattern":
            "Paisa aapke paas knowledge ke through aata hai — teaching, advising, writing, "
            "consulting. Aap natural mentor ho — coaching/teaching ka ek income stream "
            "ZARUR build karein, even if it's side. Yellow gemstones (yellow sapphire) "
            "Jupiter ko strengthen karte hain — but only after astrologer confirmation.",
        "health_pattern":
            "Liver, fat metabolism, hips, ears, nervous system — Jupiter ke under. Avoid "
            "over-eating sweets (Jupiter +sugar = dangerous). Yellow foods (turmeric, "
            "banana, ghee) regular lijiye.",
        "spiritual_path":
            "Aapka dharma 'gyan-daan' (wisdom-giving) hai. Guru pooja, Brihaspati mantra, "
            "Sai-Baba devotion suit karega. Pothi/scripture daily 5 minute padhne ki habit "
            "build kare — exponential wisdom.",
        "strengths": [
            "Wisdom beyond age",
            "Teaching/explaining clarity",
            "Optimism — naturally positive",
            "Generosity — aap kheechke dete ho",
            "Long-term strategic thinking",
        ],
        "challenges": [
            "Overconfidence me galat advice de dete ho",
            "Execution weakness — sirf planning karte raho",
            "Weight gain after 30 — Jupiter expansion is literal",
            "Sermonizing — log unsolicited advice se thak jaate hain",
            "Children/students ke saath over-attached",
        ],
        "risk_alerts": [
            "Liver health 35 ke baad strict — daru aur tale food limit",
            "Financial advisor ban'ne ki tendency — apne paise nuksaan",
            "Religious cults me phasne ka risk — discernment rakho",
            "Children/disciples ki failure aapko personally lagti hai — detachment seekho",
            "Thursday vrat ya peeli cheez ka donation karna — Jupiter strong rakho",
        ],
        "golden_periods":
            "Personal Year 3, 6, 9 — knowledge se kamai. Guru-gochar (Jupiter transit) ke "
            "12 saal cycle me 1, 5, 9 sign par sabse strong. Daily 7-9 AM Jupiter hora "
            "me likhna/teaching karna — extra blessed.",
    },

    4: {
        "title": "The Disruptor — Rahu's Modern Visionary",
        "tagline": "Aap rules tod ke naye rules banane wale ho.",
        "life_essence": [
            "Number 4 ka swami Rahu hai — modern, unconventional, electric. Aap tradition "
            "se chid jaate ho — 'kyun aisa hi karna hai?' aapka favourite question hai. "
            "Bachpan me parents ne aapko 'zidi' kaha hoga, par truth ye hai ki aap zidi "
            "nahi — original ho. Aap copy-paste duniya me original soul ho.",

            "Aapki life linear nahi hai — sudden jumps, sudden falls, sudden recoveries. "
            "Boring stable career aap nahi nibha sakte. Tech, innovation, foreign lands, "
            "non-traditional paths — yahi aapki energy hai.",

            "Rahu ka warning: 'illusion'. Aap kabhi-kabhi shortcuts me phas jaate ho — "
            "'jaldi paisa', 'easy success'. Yeh hamesha trap hota hai. Rahu se sirf 'long, "
            "patient, ethical work' hi accha phal deta hai. Shortcut = self-destruction.",
        ],
        "career_pattern": [
            "Best fields: technology, software, AI/data, foreign trade, aviation, electrical "
            "engineering, photography/cinema, social media, crypto/fintech, immigration "
            "consulting, NGO work, anything cutting-edge. Government job aapko bore karega.",

            "Common mistake: Aap har 2-3 saal me job badalte ho — 'something new' chahiye. "
            "Result: koi field me deep mastery nahi banti. Solution: ek industry chuno aur "
            "usi me 7+ saal dijiye — fir aapka Rahu-magic kaam karega.",

            "Growth timing: Erratic — 26-28, 33-35, 41-44 me sudden jumps. Rahu ki "
            "mahadasha (18 saal) jab aati hai life redefine ho jaati hai. Saturday aapka "
            "power day (Rahu = Saturn's secret partner).",
        ],
        "love_pattern": [
            "Love me aap unpredictable ho — kabhi obsessive, kabhi cold. Partner ko samajh "
            "nahi aata kya hua. Yeh aap intentionally nahi karte — Rahu energy hi aisi hai.",

            "Breakup reason: Boredom. Routine relationship aapko suffocate karta hai. Aap "
            "thrill, novelty, mystery chahte ho. Solution: partner ke saath naye experiences "
            "force-create karein — travel, hobbies, surprises.",

            "Ideal partner: Number 1, 5, ya 7 — independence respect karne wale. Number "
            "2 + 4 mismatch (moon-rahu antithetical). Inter-caste/inter-cultural marriage "
            "Rahu ki signature hai.",
        ],
        "money_pattern":
            "Paisa aapke paas waves me aata hai — kabhi flood, kabhi 0. Investment me "
            "speculation, crypto, foreign equity attractive lagti hai — but Rahu yahan "
            "trick karta hai. 70% safe (FD/index fund), 30% speculative — yahi formula. "
            "Foreign currency, electronics, blue items aapke lucky storage.",
        "health_pattern":
            "Skin, nervous system, addictions, anxiety, snake-related fears — Rahu ke under. "
            "Meditation aur digital detox MUST hai. Smartphone se 1 hour pehle sona — Rahu "
            "ka direct organ phone hai.",
        "spiritual_path":
            "Aapka dharma 'breaking outdated structures' hai. Saraswati pooja, Durga "
            "sadhana, Shiv-tandav strotra — Rahu-friendly. Saturday black til donation, "
            "blanket donation cold mausam me.",
        "strengths": [
            "Original thinking — unconventional solutions",
            "Tech savvy — naturally adopt new tools",
            "Foreign affinity — abroad opportunities milti hain",
            "Crisis innovation — emergency me creative",
            "Networking — diverse circle banaate ho",
        ],
        "challenges": [
            "Restlessness — kuch bhi long-term commit nahi karte",
            "Addictions risk (substance, screen, gambling)",
            "Sudden anger flares",
            "Relationship instability",
            "'Get-rich-quick' schemes me phasna",
        ],
        "risk_alerts": [
            "Crypto/speculative investment me >30% portfolio NA RAKHO",
            "Snake/insect bite ka karmic risk — first-aid knowledge zaruri",
            "Foreign land travel me document strict — Rahu loves to lose passport",
            "28-30 ya 41-44 ke beech mahadasha-shift, life redefine — guidance lo",
            "Stress-eating ya night-time scrolling addiction — health drain karega",
        ],
        "golden_periods":
            "Rahu mahadasha (18 saal) jab activate hoti hai — game-changer. Personal Year "
            "1, 4, 7 — innovation me rapid progress. February-March (Rahu in Aquarius "
            "favoured) yearly window. Saturday raat me strategy plan karein — Rahu peak "
            "hota hai.",
    },

    5: {
        "title": "The Communicator — Mercury's Quicksilver",
        "tagline": "Aap deals, ideas aur people ko connect karne ke ustaad ho.",
        "life_essence": [
            "Number 5 ka swami Budha (Mercury) hai. Aap 'gatishil' (mobile, quick) ho. "
            "Aapka brain 24/7 chalu rehta hai — log thakaate hain aap se baat karke "
            "kyunki aap 5 topic ek saath handle kar sakte ho. Yeh natural multi-tasking "
            "aapki greatest asset hai.",

            "Aap born networker ho — 100 logon ke naam, 100 phone numbers, 100 contexts "
            "yaad rakhte ho. Sales, marketing, deals — aapke khoon me hai. Aap ek conversation "
            "se opportunity nikaal lete ho.",

            "Mercury ki warning: 'shallow' ban'ne ka risk. Itna versatile hone se aap "
            "kahin bhi deep nahi jaate. Sirf surface skim karte ho. Master ban'ne ke liye "
            "ek field me 10,000 hours dene padte hain — 5 walo ke liye yeh discipline build "
            "karna sabse mushkil hai, par sabse zaruri.",
        ],
        "career_pattern": [
            "Best fields: business (especially trade/commerce), sales, marketing, journalism, "
            "media, IT, accounting, transport, communication tech, agency work, real estate "
            "broking, share market, language teaching. Kuch bhi jisme variety + people + "
            "money convertible ho.",

            "Common mistake: Job hopping aur business hopping. 2 saal me bored ho jaate "
            "ho. Solution: ek umbrella business chuno (e.g. consulting), uske andar variety "
            "create karo — same field, naye clients/projects.",

            "Growth timing: Earliest of all numbers — 22-25 already commercial sense aata "
            "hai. 28-32 first big money. 35-40 stabilization. Wednesday aapka power day. "
            "Sun rises me aap sharpest.",
        ],
        "love_pattern": [
            "Love me aap fun ho, intellectually stimulating ho — but emotional depth "
            "avoid karte ho. Heavy conversations se ghabraate ho.",

            "Breakup reason: Partner ko aap 'half-present' lagte ho — phone, work, dosti "
            "sab parallel chal raha hota hai. Solution: relationship me 'phone-free 1 hour "
            "daily' rule rakhe — game-changer.",

            "Ideal partner: Number 1, 3, 6, ya 9 — intellectual peers. Number 2 + 5 messy "
            "(too much movement for moon).",
        ],
        "money_pattern":
            "Paisa aapke paas multiple streams me aata hai — yahi natural pattern hai. "
            "Single salary aapko trap karegi. Side-hustle MANDATORY hai 5 walon ke liye. "
            "Shares, mutual funds, intra-day trading aapke liye favourable. Green items, "
            "emerald (after consultation), copper aapke storage.",
        "health_pattern":
            "Nervous system, skin, hands, lungs, IBS/digestion — Mercury ke under. "
            "Anxiety attacks 5 walon me common. Pranayama daily 10 minute — magical effect. "
            "Multi-tasking khaate-waqt mat karein.",
        "spiritual_path":
            "Aapka dharma 'ideas ka aadan-pradaan' hai. Vishnu sadhana, Hanuman chalisa "
            "(Mercury-friendly), Saraswati. Wednesday green moong donation. Mind-yoga "
            "(Trataka, Vipassana) game-changing.",
        "strengths": [
            "Multi-tasking — 5 cheez ek saath",
            "Networking — instant rapport",
            "Adaptability — har crowd me fit",
            "Negotiation — deal close karne ki kala",
            "Speed — fast learner, fast executor",
        ],
        "challenges": [
            "Shallow mastery — kahin deep nahi",
            "Anxiety, restlessness, sleeplessness",
            "Commitment phobia (relationship aur projects)",
            "Sarcasm me dil dukhata ho",
            "Over-commitment — itna 'haan' bolte ho ki deliver nahi kar paate",
        ],
        "risk_alerts": [
            "Share market me intra-day me bahut paisa nuksaan ka risk — strict stop-loss",
            "Anxiety se peace nuksaan — meditation skip mat karein",
            "Whatsapp/Insta addiction — productivity 30% loss",
            "Multiple relationships ka temptation — boundary rakho",
            "Wednesday vrat 21 saptah — mind ki sthirta multiplied",
        ],
        "golden_periods":
            "Personal Year 5 obviously — entire year breakthrough opportunities. Budha "
            "ki mahadasha (17 saal) golden hai. May-June yearly power window (Mercury "
            "exalted in Virgo). Wednesday + sunrise aapka manifestation peak.",
    },

    6: {
        "title": "The Lover — Venus's Beauty Bringer",
        "tagline": "Aap pyaar, kala aur saundarya ke avatar ho.",
        "life_essence": [
            "Number 6 ka swami Shukra (Venus) hai. Aap iss duniya ko sundar banane ke "
            "liye aaye ho. Aapko awkward ya gandi cheez tolerate nahi hoti — clothes, "
            "ghar, conversation, food — sab kuch elegant chahiye.",

            "Aap natural family-person ho. Rishton me aap glue ho. Maa, behen, biwi, "
            "dost — aap unke saath time invest karte ho jaisa koi nahi. Yeh aapki greatest "
            "joy aur greatest energy drain dono hai.",

            "Venus ki warning: 'over-attachment'. Aap kisi se itna pyaar karne lag jaate "
            "ho ki khud ko bhool jaate ho. Self-love seekhna 6 walon ke liye lifelong "
            "lesson hai. Khud ke liye time investment kabhi 'selfish' nahi hai — yeh "
            "actually relationship ke liye sustainable.",
        ],
        "career_pattern": [
            "Best fields: arts (music, dance, painting), fashion, beauty/cosmetics, "
            "entertainment industry, hospitality, luxury goods, jewellery, interior design, "
            "wedding planning, hotels/restaurants, perfumery, photography, vehicle/car "
            "industry. Anywhere beauty meets business.",

            "Common mistake: Family responsibility ke chakkar me apne dreams compromise "
            "kar dete ho. 40 saal ke baad regret hota hai. Solution: family AND personal "
            "growth — 'OR' nahi rakhna.",

            "Growth timing: 25-30 first phase (often through marriage/partnership), 32-38 "
            "peak income, 45-52 luxury phase. Friday aapka power day — bada launch Friday.",
        ],
        "love_pattern": [
            "Love me aap king/queen ho — romance, gifts, surprises, candle dinner — "
            "sab aapko natural aata hai. Partner aapse spoiled ho jaata hai.",

            "Breakup reason: Aap give too much, then expect equal return — jab nahi "
            "milta toh resentment build hota hai silently. Communication of needs zaruri.",

            "Ideal partner: Number 3, 6, 9 — wisdom + beauty match. Number 7 + 6 "
            "interesting (Ketu's detachment vs Venus's attachment) — growth-path par "
            "saath.",
        ],
        "money_pattern":
            "Paisa aapke paas relationships, beauty, ya luxury ke through aata hai. "
            "Aap luxury me kharch zyada karte ho — yeh genetic hai, fight mat karein. "
            "Bas income > expense ka strict ratio rakho. Diamond, white gold, silk, "
            "perfume — aapke lucky asset.",
        "health_pattern":
            "Reproductive organs, kidneys, throat, skin glow — Venus ke under. Aapki "
            "skin condition aapki emotional state batati hai — relationship stress = "
            "skin issues. Sweets + ghee balance me lijiye.",
        "spiritual_path":
            "Aapka dharma 'love through beauty' hai. Lakshmi sadhana, Devi pooja, "
            "Krishna bhakti suit karta hai. Friday white items donation. Bhakti-yoga "
            "aapka path hai (jnana-yoga nahi).",
        "strengths": [
            "Aesthetic sense — sab kuch beautiful banate ho",
            "Relationship maintenance — long friendships",
            "Diplomacy — peace banaate ho",
            "Generosity — open-hearted dene wale",
            "Charm — pehli mulakat me impression chod dete ho",
        ],
        "challenges": [
            "Over-spending on luxury",
            "Family enmeshment — boundaries weak",
            "Avoidance of conflict",
            "Vanity (looks-obsessed)",
            "Comfort-zone trapped — aaram pasand",
        ],
        "risk_alerts": [
            "Luxury kharch 40% income se zyada → financial trap",
            "Vehicle accidents 26-28 ke beech possible — drive defensively",
            "Toxic relationship me 7+ saal stuck — counseling lijiye",
            "Reproductive health women ke liye 28-32 attention",
            "Friday vrat ya white donation 16 saptah — Venus blessings",
        ],
        "golden_periods":
            "Personal Year 6 — relationship + family + beauty all peak. Venus mahadasha "
            "(20 saal) classic 'sukh' phase. April-May Venus exalted in Pisces — "
            "creativity peak. Friday sunrise me art/beauty/relationship work.",
    },

    7: {
        "title": "The Mystic — Ketu's Spiritual Researcher",
        "tagline": "Aap iss duniya me dikh ke bhi nahi dikh paate.",
        "life_essence": [
            "Number 7 ka swami Ketu hai — moksha karak. Aap ek rahasya ho — even khud "
            "ke liye. Aap kabhi material world me 100% absorbed nahi ho paate, andar se "
            "kuch aur khoj rahe hote ho — meaning, truth, depth.",

            "Aapko bachpan se akelapan acha laga hoga. Bheed me bhi aap 'apne saath' rahte "
            "ho. Yeh isolation aapki weakness nahi — aapki research lab hai. Sabse badi "
            "khojen 7 walon ne ki hain (Einstein, Tesla, J.K. Rowling — sab 7 ke).",

            "Ketu ki warning: 'detachment me zyada chala jaana'. Aap relationships, "
            "responsibilities, society se itne disconnect ho jaate ho ki function "
            "karna mushkil ho jaata hai. Ground-rule: roj 1 ghanta 'practical world' me "
            "bitao — bills, family, health.",
        ],
        "career_pattern": [
            "Best fields: research, science, philosophy, writing, spirituality/yoga, "
            "investigation/forensics, occult, photography, water-related work (marine, "
            "import-export), psychology, archeology, IT R&D, alternative healing. Solo "
            "professional roles me aap shine karte ho.",

            "Common mistake: Mainstream success ko 'shallow' samajh ke ignore kar dete ho — "
            "fir 35 saal me realize hota hai paisa to chahiye hi. Solution: spiritual "
            "AND practical — both can co-exist. Money is also energy, reject mat karo.",

            "Growth timing: Late bloomers — 35-45 me real recognition. Ketu's mahadasha "
            "(7 saal) jab aati hai life upside-down ho jaati hai (good or bad). Tuesday/"
            "Saturday aapke power days (Ketu connections).",
        ],
        "love_pattern": [
            "Love me aap distant ho — partner ko 'fully reach' nahi karne dete. Aapka "
            "ek hissa hamesha alone rehta hai. Yeh frustrating hai partner ke liye.",

            "Breakup reason: 'I don't know what you want' — partner ki yahi shikayat "
            "hoti hai. Aap khud bhi nahi jaante. Solution: journaling karein — apne aap "
            "ko discover karein, fir partner ko bata sakoge.",

            "Ideal partner: Number 4, 7, 1 — independence respect karte hain. Marriage "
            "late ho sakti hai (after 28-30) — accept karein, dont rush.",
        ],
        "money_pattern":
            "Paisa aapke paas knowledge ke through aata hai — research, writing, "
            "consulting, healing. Aap material kam, intellectual zyada hote ho — yeh "
            "ulta financial planning ko challenging banata hai. Auto-investment SIP "
            "aapke liye life-saver. Ketu metals — multi-color (cat's eye after consultation).",
        "health_pattern":
            "Nervous system, mysterious skin issues, immunity, gas/digestion, eyes — "
            "Ketu ke under. Random unexplained ailments aapko hote hain. Naturopathy "
            "+ Ayurveda + meditation aapke liye conventional medicine se behtar.",
        "spiritual_path":
            "Aapka dharma 'inner truth ki khoj' hai. Ganesha (Ketu's son) sadhana, "
            "Hanuman, Shiva, Kali — sab work karte hain. Vipassana 10-day course aapki "
            "life-changer hogi.",
        "strengths": [
            "Deep research ability",
            "Intuition — paranormal sensing",
            "Self-sufficient",
            "Detached judgment — bias-free",
            "Mystical experiences naturally aati hain",
        ],
        "challenges": [
            "Loneliness me depression ka risk",
            "Practical world me struggle (bills, scheduling)",
            "Relationship intimacy mushkil",
            "Late marriage / no marriage tendency",
            "Conventional society me mismatch",
        ],
        "risk_alerts": [
            "Drugs / alcohol ka escapism risk — sober rehna mandatory",
            "Sudden unexplained illnesses 28-32 ke beech — Ayurveda checkup karwao",
            "Loneliness depression me ja sakta hai — therapist se baat karein",
            "Material decisions impulsively reject — financial guru se sallah",
            "Tuesday Hanuman Chalisa 11 baar — Ketu peace + protection",
        ],
        "golden_periods":
            "Personal Year 7 — spiritual + research breakthroughs. Ketu mahadasha (7 saal) "
            "transformative. Late autumn (Oct-Nov) yearly meditation + insight peak. "
            "Solo retreat 1 baar yearly mandatory.",
    },

    8: {
        "title": "The Builder — Saturn's Karmic Magnate",
        "tagline": "Aap struggle se diamond banne wale ho.",
        "life_essence": [
            "Number 8 ka swami Shani (Saturn) hai. Aapki life me kuch bhi free me nahi "
            "milta — har cheez ke liye aapne paseena bahaya hai, ya bahana padega. "
            "Yeh injustice nahi hai — yeh aapki soul ka chosen path hai. Aap karma-yogi ho.",

            "Bachpan se aapko 'serious' kaha gaya hoga — kyunki aap waqai serious ho. "
            "Khel-kud me bhi aapko strategy dikhti hai. Yeh quality aapko long-term me "
            "bahut bada banaati hai — par chhoti umar me bahut akelapan deti hai.",

            "Saturn ka sabse important sabaq: 'patience'. 8 walon ki real success 35 ke "
            "baad shuru hoti hai. Pehle aapko 'paani me dubo dubo ke' Saturn taiyaar karta "
            "hai. Iss process ko fight mat karo. Discipline aur patience hi 8 ki master "
            "key hai.",
        ],
        "career_pattern": [
            "Best fields: real estate, mining, oil, heavy industry, government job, judiciary, "
            "engineering, infrastructure, banking, insurance, social justice work, chronic "
            "disease healing, undertaking, archeology, antiques. Slow + structured + "
            "long-term — yahi 8 ka territory.",

            "Common mistake: Quick success chahna — fir frustration, fir shortcuts, fir "
            "downfall. 8 walon ko shortcut bahut maharra padta hai. Solution: 10-year plan "
            "banao har goal ke liye. Saturn 10-year cycles me kaam karta hai.",

            "Growth timing: 36-42 first big peak (Saturn return), 48-55 wealth crystallization, "
            "58-65 legacy. Saturday aapka power day. Late evening (Saturn hora) decisions.",
        ],
        "love_pattern": [
            "Love me aap loyal aur committed ho — jab tak commit nahi karte tab tak guarded, "
            "jab kar diya toh forever. Yeh quality precious hai but partner ko initially "
            "samajh nahi aati.",

            "Breakup reason: Coldness — aap emotion show nahi karte, partner ko lagta "
            "hai 'mujhe pyaar nahi karte'. Solution: action se nahi, words se bhi pyaar "
            "express karein — uncomfortable but necessary.",

            "Ideal partner: Number 4, 8, 6 — discipline + warmth balance. Late marriage "
            "(after 30) better. Hasty marriage = lifelong regret.",
        ],
        "money_pattern":
            "Paisa aapke paas slowly + steadily aata hai. 25-35 ka phase typically struggle, "
            "35-50 me wealth crystallize hoti hai. Real estate, fixed assets, slow "
            "compounding investments aapke liye perfect. Black/dark blue items, iron, "
            "blue sapphire (after consultation) Saturn strengthen.",
        "health_pattern":
            "Bones, joints, knees, teeth, chronic conditions, depression — Saturn ke under. "
            "Discipline daily exercise (especially walking) MUST. Sesame oil, urad dal, "
            "iron-rich foods. Saturday fast (only fruits) very healing.",
        "spiritual_path":
            "Aapka dharma 'karma-yoga through service to underprivileged' hai. Shani sadhana, "
            "Hanuman, Bhairav. Saturday black til donation, blanket donation cold weather "
            "me. Cleaner toilets/orphanage seva — direct Saturn pacification.",
        "strengths": [
            "Discipline — schedule strict follow",
            "Endurance — long-term struggles handle",
            "Strategic mind — chess-player",
            "Loyalty — once committed, forever",
            "Justice-orientation — fairness matter karta hai",
        ],
        "challenges": [
            "Emotional coldness perception",
            "Pessimism — 'kuch bhi accha nahi hoga' mindset",
            "Slow visible progress (frustrating youth me)",
            "Workaholism — joy bhool jaate ho",
            "Authority issues with father/boss",
        ],
        "risk_alerts": [
            "Father-figure ke saath conflict ya distance — childhood pattern",
            "Bone/joint injury 30-32 ke beech possible — yoga mandatory",
            "Depression risk 28-30 (Saturn return) — therapy lijiye",
            "Workaholism me family neglect — schedule family-time",
            "Saturday black til + sarson tel donation 21 weeks — Saturn balance",
        ],
        "golden_periods":
            "Personal Year 8 — wealth + recognition + power all peak. Shani mahadasha "
            "(19 saal) — initial test, then rich rewards. December-January yearly Saturn "
            "peak. 36-42 entire phase aapka launchpad — kuch bhi shuru karein.",
    },

    9: {
        "title": "The Warrior — Mars's Soldier of Truth",
        "tagline": "Aap apni passion ke liye ladne wale ho.",
        "life_essence": [
            "Number 9 ka swami Mangal (Mars) hai. Aap energy ka volcano ho — andar se "
            "agni jalti rehti hai. Yeh fire aapki greatest power aur greatest danger "
            "dono hai. Channeled = aap mountains move karoge. Uncontrolled = aap khud "
            "ko jala loge.",

            "Bachpan se aapko 'gussewala' kaha gaya hoga. Yeh sirf surface hai. Aapka "
            "real fire is — passion, courage, drive. Jab aapko kisi cause se pyaar ho "
            "jata hai, aap us cause ke liye akele bhi lad sakte ho.",

            "Mars ka sabse important sabaq: 'apni shakti ka use kaha karna hai aur kaha "
            "rokna hai'. Aapki energy unlimited nahi hai — strategically use karein, "
            "emotionally nahi. Daily 60 minute physical exercise aapke liye therapy hai, "
            "luxury nahi.",
        ],
        "career_pattern": [
            "Best fields: military, police, sports, surgery (especially trauma), real "
            "estate, construction, engineering (mechanical/civil), firefighting, security, "
            "mining, butchery, pharma, sports management, fitness training, motivational "
            "speaking. Anywhere physical/emotional courage required.",

            "Common mistake: Boss/authority ke saath clash. Aap 'unfair' tolerate nahi "
            "karte — punch ya quit. Solution: 30 ke baad self-employed/own business hi "
            "best — Mars employee-mode me suffocate hota hai.",

            "Growth timing: Early peak (24-28 first surge), 32-36 stabilization, "
            "42-48 legacy phase. Tuesday aapka power day. Sunrise time aap most powerful.",
        ],
        "love_pattern": [
            "Love me aap intense, possessive, passionate ho. Affair-style romance se "
            "shuru hota hai often. Jealousy ka management bada lifelong project hai.",

            "Breakup reason: Anger explosion — kuch keh dete ho jo undo nahi hota. "
            "Solution: Anger uthe toh 24 hour wait rule — kuch bhi mat bolo, mat send karo. "
            "Anger ek wave hai, pass ho jaayegi.",

            "Ideal partner: Number 1, 5, 9, 3 — energy match. Number 9 + 9 explosive "
            "(double Mars). Manglik dosha 9 walon me prevalent — match before marriage.",
        ],
        "money_pattern":
            "Paisa aap energy bhejke kamate ho — physical work, courage-required jobs, "
            "high-risk + high-return ventures. Aap rishk lete ho jo doosre nahi le sakte. "
            "Real estate, gold, red items, copper, coral (after consultation) — aapke "
            "lucky asset.",
        "health_pattern":
            "Blood, muscles, head, surgery prone — Mars ke under. Accidents ka risk avg "
            "se zyada — driving/sports me extra-safety. Annual blood-related checkup. "
            "Spicy food balance kare — Mars + chili = ulcer.",
        "spiritual_path":
            "Aapka dharma 'truth ke liye fight, kamzor ki raksha' hai. Hanuman sadhana "
            "perfect (Mars's son). Subramanya/Kartikeya bhakti. Tuesday + Saturday Hanuman "
            "Chalisa 11 baar. Lal vastra/lal phul donation Tuesday.",
        "strengths": [
            "Courage — fear ko face karte ho",
            "Energy — mountain move kar sakte ho",
            "Passion — jisme ho usme 200%",
            "Protective instinct — apno ke liye ladte ho",
            "Initiative — pehle aap, baad me sab",
        ],
        "challenges": [
            "Anger management lifelong project",
            "Impulsivity — pehle kar lete ho, fir sochte ho",
            "Jealousy in relationships",
            "Physical injury prone",
            "Authority clashes",
        ],
        "risk_alerts": [
            "Accident risk 24-26 + 32-34 ke beech — vehicle slow + cautious",
            "Anger se rishton me permanent damage — 24-hour-rule MUST",
            "Manglik check before marriage — 9 walon me high probability",
            "Surgery jeevan me 1+ likely — health insurance early",
            "Tuesday Hanuman seva, sindoor offering — Mars peace",
        ],
        "golden_periods":
            "Personal Year 9 — completion + transformation + new cycle. Mars mahadasha "
            "(7 saal) intense but life-defining. Mid-March to mid-May (Mars exalted in "
            "Capricorn) yearly window. Tuesday Brahma muhurat (4-6 AM) for biggest "
            "decisions.",
    },
}


def narrative_for(driver: int) -> Dict[str, Any]:
    """Return the narrative pack for a given driver number (1-9)."""
    return _NARRATIVES.get(driver, {})


def life_summary_block(driver: int, conductor: int, name: str) -> Dict[str, str]:
    """Generate a 4-point summary card for the top of premium PDF."""
    n = narrative_for(driver) or {}
    PLANETS = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
               6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"}

    # Biggest strength = first item from strengths list
    strengths = n.get("strengths") or [""]
    challenges = n.get("challenges") or [""]

    # 2026 focus — derived from driver+conductor combo
    FOCUS_2026 = {
        1: "Independent venture launch — apna kuch shuru karein. Authority figures se reconcile.",
        2: "Emotional boundaries strengthen. Health (especially mother-link) attention.",
        3: "Teaching/writing income stream build. Higher education ya certification consider.",
        4: "Tech/foreign opportunity capture. Stop job-hopping — ek field me deep go.",
        5: "Multiple income streams crystallize. Communication-based business expand.",
        6: "Family + creative project balance. Long-pending relationship decision.",
        7: "Spiritual study deepen. Solo retreat. Practical world ignore mat karein.",
        8: "Foundation work — slow + steady. Real estate ya asset build. Father-bond heal.",
        9: "Channel anger constructively — sports/exercise mandatory. Big move possible.",
    }

    return {
        "core_personality": n.get("title", "—"),
        "tagline": n.get("tagline", "—"),
        "biggest_strength": strengths[0] if strengths else "—",
        "biggest_challenge": challenges[0] if challenges else "—",
        "2026_focus": FOCUS_2026.get(driver, "Self-discovery year."),
        "primary_planet": PLANETS.get(driver, "—"),
        "secondary_planet": PLANETS.get(conductor, "—"),
        "name_signature": name,
    }


# ─── Why-Impact-Action conversion for number analysis ───────────────────

def why_impact_action_for_number(reduced: int, kind: str) -> Dict[str, str]:
    """Convert a reduced number + kind into Why/Impact/Action narrative.

    kind ∈ {'mobile', 'vehicle', 'house', 'name'}
    """
    PLANETS = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
               6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"}
    planet = PLANETS.get(reduced, "—")

    # Why: planet meaning in this kind context
    WHY = {
        ("mobile", 1): "Mobile number Surya energy carry karta hai — har call/message me leadership vibration jaati hai.",
        ("mobile", 2): "Moon energy emotional fluctuation laata hai — mood swings ke saath calls.",
        ("mobile", 3): "Jupiter wisdom + financial expansion deta hai — knowledge-based calls profitable.",
        ("mobile", 4): "Rahu sudden, unexpected calls — opportunities + disruptions dono.",
        ("mobile", 5): "Mercury speed + business — sales, deals, networking me magic.",
        ("mobile", 6): "Venus harmony + relationships — love + family ka strong center.",
        ("mobile", 7): "Ketu mystery + isolation — important calls aati hain par interaction kam.",
        ("mobile", 8): "Saturn slow growth + karmic — official, government, long-term work me favourable.",
        ("mobile", 9): "Mars energy + courage — bold conversations, but anger ka risk.",

        ("vehicle", 1): "Vehicle 1 — leadership feel, par solo travel pattern.",
        ("vehicle", 2): "Vehicle 2 — emotional, family-friendly, par maintenance demanding.",
        ("vehicle", 3): "Vehicle 3 — growth-oriented, money brings.",
        ("vehicle", 4): "Vehicle 4 — sudden tech issues + unexpected breakdowns common. Modern car tho ok, classic avoid.",
        ("vehicle", 5): "Vehicle 5 — versatile, multi-purpose, business travel acha.",
        ("vehicle", 6): "Vehicle 6 — luxury, beauty, comfort — aapko impress karega.",
        ("vehicle", 7): "Vehicle 7 — solo-friendly, quiet drives suit.",
        ("vehicle", 8): "Vehicle 8 — heavy-duty, long-life, par initial repair phase.",
        ("vehicle", 9): "Vehicle 9 — sports/SUV style suit, par accident risk avg se zyada.",

        ("house", 1): "Ghar 1 — leadership family, head of household empowered.",
        ("house", 2): "Ghar 2 — emotional, mother-energy strong, peace-oriented.",
        ("house", 3): "Ghar 3 — wealth + wisdom flow karta hai.",
        ("house", 4): "Ghar 4 — sudden changes (renovations, guests, news) frequent.",
        ("house", 5): "Ghar 5 — busy, social, business-friendly home.",
        ("house", 6): "Ghar 6 — family + romance + beauty — best for relationships.",
        ("house", 7): "Ghar 7 — quiet, spiritual, study-suited.",
        ("house", 8): "Ghar 8 — initial struggle phase, baad me wealth-anchored.",
        ("house", 9): "Ghar 9 — energy + arguments + passion — pet/sports-friendly.",
    }

    IMPACT = {
        ("mobile", 1): "Aap har conversation me 'main pehle' wala feel project karte ho — yeh leaders attract karta hai par juniors thake-thake feel karte hain.",
        ("mobile", 2): "Calls me aap zyada listen karte ho — log apni problems aapke saamne kholte hain, aap free counsellor ban jaate ho.",
        ("mobile", 3): "Knowledge-based calls aate hain — log advice ya teaching ke liye contact karte hain. Direct income link possible.",
        ("mobile", 4): "Phone par sudden good ya bad news aati hai — kabhi job offer, kabhi accident — emotional rollercoaster.",
        ("mobile", 5): "Phone par log naye opportunities, deals, contacts laate hain — aap natural networker ban jaate ho.",
        ("mobile", 6): "Phone par love + family + creative collaboration ka flow rehta hai — relationship strengthening.",
        ("mobile", 7): "Important calls miss kar dete ho — phone par aap distant rehte ho, log notice karte hain.",
        ("mobile", 8): "Phone par official/government communication zyada — bureaucratic delays, paperwork, court matters connect.",
        ("mobile", 9): "Phone par arguments quick, anger explosions easy — relationship me stress.",

        ("vehicle", 1): "Vehicle aapko 'lone driver' me zyada comfortable rakhta hai — long solo road trips aapke favourites.",
        ("vehicle", 2): "Family trips ke liye perfect — par fuel + maintenance bill expected se zyada.",
        ("vehicle", 3): "Vehicle ke saath income generation possible — Uber/cab side ya business travel.",
        ("vehicle", 4): "Hidden electrical/electronic issues regular — yearly mech checkup MUST. Insurance comprehensive.",
        ("vehicle", 5): "Vehicle business + personal use dono — versatile, multiple purpose serve karta hai.",
        ("vehicle", 6): "Vehicle aapki personality statement banti hai — log judge karte hain. Maintenance priority.",
        ("vehicle", 7): "Long drives me clarity milti hai — solo driving aapki therapy ban jaati hai.",
        ("vehicle", 8): "Vehicle long lasting (10+ saal easily) — par initial 1-2 saal frustrating.",
        ("vehicle", 9): "Speed + power feel chahiye — par over-speeding ka risk avg se zyada. Defensive driving habit MUST.",

        ("house", 1): "Ghar me aap dominant ho — sab aapki maante hain. Par 'me-time' nahi milta — recharge mushkil.",
        ("house", 2): "Ghar emotional safe-haven hai sabke liye — par boundaries weak, koi bhi aake bana sakta hai.",
        ("house", 3): "Ghar me wealth flow hota hai — bills automatically manage, savings build.",
        ("house", 4): "Ghar me 6-12 mahine me kuch na kuch sudden change (renovation, member shift, repair) hota rehta hai.",
        ("house", 5): "Ghar party-house ban jaata hai — log freely aate hain. Productivity ke liye dedicated quiet space chahiye.",
        ("house", 6): "Ghar romance + family bonding ka center hai — sundar interior + happy memories.",
        ("house", 7): "Ghar spiritual energy carry karta hai — meditation + study yahan productive.",
        ("house", 8): "Ghar me initial phase financial struggle, par 5+ saal me wealth crystallize.",
        ("house", 9): "Ghar me energy zyada hoti hai — arguments + makeup cycle. Pet ya sport equipment fit.",
    }

    ACTION = {
        ("mobile", 1): "Important calls Sunday subah karein. Number ke saath red mobile cover use kare.",
        ("mobile", 2): "Important calls Monday karein. White ya silver cover. Late-night calls avoid (Moon weak).",
        ("mobile", 3): "Thursday subah important deal calls. Yellow cover. Hora time use karein.",
        ("mobile", 4): "Mobile ko 'silent + DND' raat me — Rahu raat me mind disturb karta hai. Tech calls Saturday.",
        ("mobile", 5): "Wednesday subah deals + sales calls. Green cover. Multi-tasking phone karte waqt avoid.",
        ("mobile", 6): "Friday important relationship/love calls. White ya pink cover. Music + harmony tones.",
        ("mobile", 7): "Tuesday/Saturday important spiritual calls. Multi-color cover. Solo time jaroori.",
        ("mobile", 8): "Saturday subah official + government calls. Black cover. Patience + structured talk.",
        ("mobile", 9): "Tuesday subah strategic calls. Red cover. 24-hour rule before angry response.",

        ("vehicle", 1): "Sunday subah vehicle pooja. Red ribbon. Red dashboard mat. Owner solo drive priority.",
        ("vehicle", 2): "Monday subah pooja. White flowers. Family trips Monday/Friday.",
        ("vehicle", 3): "Thursday pooja. Yellow ribbon. Business travel Thursday lucky.",
        ("vehicle", 4): "Saturday pooja. Tech check har 6 mahine. Comprehensive insurance MUST.",
        ("vehicle", 5): "Wednesday pooja. Green/yellow ribbon. Long drives Wednesday productive.",
        ("vehicle", 6): "Friday pooja. White flowers. Vehicle clean + perfumed always.",
        ("vehicle", 7): "Tuesday pooja. Solo time vehicle me allow karein.",
        ("vehicle", 8): "Saturday pooja. Black umbrella keep. Annual full service NEVER skip.",
        ("vehicle", 9): "Tuesday pooja. Red flag/sticker. Defensive driving course recommended.",
    }

    # House same as mobile/vehicle for action — abbreviated common advice
    HOUSE_ACTION = {
        1: "Sunday subah ghar pooja, Surya namaskar terrace par, red rangoli at entrance.",
        2: "Monday Chandra pooja, white flowers entrance par, water-fountain (north) consider.",
        3: "Thursday Brihaspati pooja, yellow paint accents, wisdom books visible.",
        4: "Saturday Rahu pacification, tech corner kept clean, blue lights bedroom avoid.",
        5: "Wednesday Budha pooja, green plants, study/work corner dedicated.",
        6: "Friday Shukra pooja, fresh flowers daily, art on walls, mirror placement north-east.",
        7: "Tuesday/Saturday meditation corner, multi-color decor, quiet zone protected.",
        8: "Saturday Shani pooja, black-stone entrance, structured + minimal interior.",
        9: "Tuesday Mangal pooja, red curtains south-room, kitchen + fire-area south-east.",
    }

    why = WHY.get((kind, reduced), f"Number {reduced} is ruled by {planet}.")
    impact = IMPACT.get((kind, reduced), "Iska prabhav aapki daily life me dheere-dheere mehsoos hota hai.")

    if kind == "house":
        action = HOUSE_ACTION.get(reduced, "")
    else:
        action = ACTION.get((kind, reduced), "")

    return {"why": why, "impact": impact, "action": action, "planet": planet}


# ─── Lucky Colours pack (Part 2 only) ──────────────────────────────────

_LUCKY_COLOURS: Dict[int, Dict[str, Any]] = {
    1: {
        "primary":   ["Golden", "Bright Orange", "Deep Yellow"],
        "secondary": ["Copper", "Bronze", "Royal Red"],
        "avoid":     ["Black", "Dark Blue", "Grey"],
        "vehicle":   "Golden, Cream, Pearl White, Bright Red — Surya ki energy reflect karne wale colours. Avoid: Black, Dark Blue.",
        "business":  "Logo me Gold + Orange combo — leadership + warmth project karta hai.",
        "gemstone_tone": "Ruby red, sunstone orange — accessories me use karein.",
    },
    2: {
        "primary":   ["Pearl White", "Cream", "Silver"],
        "secondary": ["Sea Green", "Light Blue", "Soft Pink"],
        "avoid":     ["Black", "Bright Red", "Dark Brown"],
        "vehicle":   "Pearl White, Silver, Cream, Light Blue — Chandra ki shanti energy. Avoid: Bright Red, Black.",
        "business":  "Logo me Silver + White + Soft Blue — calming, trustworthy feel.",
        "gemstone_tone": "Pearl + moonstone tones — soft, reflective accessories.",
    },
    3: {
        "primary":   ["Bright Yellow", "Saffron", "Golden Yellow"],
        "secondary": ["Light Pink", "Light Purple", "Cream"],
        "avoid":     ["Dark Green", "Black", "Steel Grey"],
        "vehicle":   "Yellow, Cream, Golden Beige — Brihaspati ki shubh energy. Avoid: Dark Green, Black.",
        "business":  "Logo me Yellow + Purple combo — wisdom + prosperity feel.",
        "gemstone_tone": "Yellow Sapphire + Topaz tones — gold-rim accessories.",
    },
    4: {
        "primary":   ["Electric Blue", "Steel Grey", "Khaki"],
        "secondary": ["Light Green", "Off-White", "Beige"],
        "avoid":     ["Black", "Dark Red", "Deep Maroon"],
        "vehicle":   "Steel Grey, Electric Blue, Khaki, Off-White — modern Rahu-friendly. Avoid: Pure Black, Deep Red.",
        "business":  "Logo me Blue + Grey + White — tech, modern, trustworthy.",
        "gemstone_tone": "Hessonite (gomed) brown-orange tones — minimal accessories.",
    },
    5: {
        "primary":   ["Light Green", "Parrot Green", "Turquoise"],
        "secondary": ["White", "Light Blue", "Light Yellow"],
        "avoid":     ["Black", "Dark Brown", "Deep Maroon"],
        "vehicle":   "Light Green, Turquoise, White, Light Blue — Mercury ki chanchal energy. Avoid: Black.",
        "business":  "Logo me Green + White — fresh, agile, communication-friendly.",
        "gemstone_tone": "Emerald green tones — modern, sleek accessories.",
    },
    6: {
        "primary":   ["Pure White", "Light Pink", "Sky Blue"],
        "secondary": ["Cream", "Light Purple", "Pastel Green"],
        "avoid":     ["Black", "Deep Red", "Dark Brown"],
        "vehicle":   "White, Cream, Pearl, Light Pink, Sky Blue — Shukra ki saundarya energy. Avoid: Black, Deep Red.",
        "business":  "Logo me White + Rose Gold + Soft Pink — luxury, beauty, premium feel.",
        "gemstone_tone": "Diamond + Crystal clear tones — elegant accessories.",
    },
    7: {
        "primary":   ["Light Grey", "Smoke Grey", "Multi-color"],
        "secondary": ["Off-White", "Soft Lavender", "Pale Yellow"],
        "avoid":     ["Bright Red", "Pitch Black", "Deep Orange"],
        "vehicle":   "Light Grey, Smoke Grey, Multi-tone, Off-White — Ketu ki mystic energy. Avoid: Bright Red.",
        "business":  "Logo me Grey + Multi-color accent — unique, mystic, original feel.",
        "gemstone_tone": "Cat's eye (lehsunia) — earthy, neutral accessories.",
    },
    8: {
        "primary":   ["Deep Blue", "Black", "Dark Purple"],
        "secondary": ["Iron Grey", "Deep Brown", "Maroon"],
        "avoid":     ["Bright Yellow", "Bright Red", "Bright Orange"],
        "vehicle":   "Black, Deep Blue, Iron Grey, Dark Brown — Shani ki gambheer energy. Avoid: Bright Yellow, Bright Orange.",
        "business":  "Logo me Black + Deep Blue + Silver — authority, structure, longevity.",
        "gemstone_tone": "Blue Sapphire + Onyx — heavy, structured accessories.",
    },
    9: {
        "primary":   ["Bright Red", "Crimson", "Maroon"],
        "secondary": ["Saffron", "Deep Orange", "Coral"],
        "avoid":     ["Pure Black", "Steel Grey"],
        "vehicle":   "Red, Maroon, Crimson, Deep Orange — Mangal ki shoorveer energy. Avoid: Pure Black.",
        "business":  "Logo me Red + Gold — bold, action-oriented, energy-packed.",
        "gemstone_tone": "Red Coral (moonga) tones — bold accessories.",
    },
}


# Day-wise dress colour (universal — Vedic planetary day)
_DAY_DRESS_COLOURS: List[Dict[str, str]] = [
    {"day": "Monday",    "planet": "Chandra (Moon)",   "colour": "Pearl White / Silver / Cream",
     "purpose": "Mental peace, family harmony, emotional calm. Mother-related work auspicious."},
    {"day": "Tuesday",   "planet": "Mangal (Mars)",    "colour": "Red / Maroon / Crimson",
     "purpose": "Courage, victory in disputes, sports/competition. Avoid soft pastels."},
    {"day": "Wednesday", "planet": "Budha (Mercury)",  "colour": "Green / Light Green / Turquoise",
     "purpose": "Communication, business deals, education. Sales calls strong."},
    {"day": "Thursday",  "planet": "Brihaspati (Jupiter)", "colour": "Yellow / Saffron / Golden",
     "purpose": "Wisdom, prosperity, teaching, spiritual study. Best for finance decisions."},
    {"day": "Friday",    "planet": "Shukra (Venus)",   "colour": "White / Light Pink / Sky Blue",
     "purpose": "Love, marriage, beauty, luxury, art. Date night / wedding events ideal."},
    {"day": "Saturday",  "planet": "Shani (Saturn)",   "colour": "Deep Blue / Black / Dark Purple",
     "purpose": "Hard work, discipline, dealing with elders/government. Long-term commitments."},
    {"day": "Sunday",    "planet": "Surya (Sun)",      "colour": "Golden / Orange / Bright Yellow",
     "purpose": "Authority, leadership, government work, father-related matters. Power day."},
]


def lucky_colours_pack(driver: int) -> Dict[str, Any]:
    """Return complete lucky colours pack for a driver number — used in Part 2."""
    pack = _LUCKY_COLOURS.get(driver, {})
    return {
        "primary":     pack.get("primary", []),
        "secondary":   pack.get("secondary", []),
        "avoid":       pack.get("avoid", []),
        "vehicle":     pack.get("vehicle", "—"),
        "business":    pack.get("business", "—"),
        "gemstone_tone": pack.get("gemstone_tone", "—"),
        "day_dress":   _DAY_DRESS_COLOURS,
    }
