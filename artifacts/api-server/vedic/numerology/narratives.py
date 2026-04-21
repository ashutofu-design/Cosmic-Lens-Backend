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


_NARRATIVES_HG: Dict[int, Dict[str, Any]] = {

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


# ─── English narratives ────────────────────────────────────────────────
# Pure English translation of _NARRATIVES_HG. Drivers without an entry
# fall back to the Hinglish version (graceful degradation).

_NARRATIVES_EN: Dict[int, Dict[str, Any]] = {

    1: {
        "title": "The Sovereign — Sun-ruled Leader",
        "tagline": "You were born to lead this world.",
        "life_essence": [
            "Your life runs on a single thread — 'I will do it my way.' "
            "Number 1 is ruled by the Sun, and the Sun never walks behind anyone — "
            "it sees only its own path. From childhood you must have felt that you "
            "could not blend into the crowd, because deep inside you are a leader — "
            "not a follower.",

            "Your greatest strength is vision and original thinking. While others "
            "are still asking 'how will this happen', you are already asking 'when "
            "will it happen'. This quality can place you in the top three in any "
            "field. But the same quality can leave you lonely in relationships — "
            "because not everyone can keep up with your pace.",

            "The Sun has one important message: 'brilliance cannot be hidden'. If "
            "you dim your own light to make others comfortable, dimness will enter "
            "your life too. You have to learn to live with your radiance — "
            "politely, but firmly.",
        ],
        "career_pattern": [
            "You are not built for a servile role — you will become a boss or an "
            "independent professional. Best fields: business owner, government "
            "leader, doctor (especially heart/eye specialist), politics, military "
            "officer, civil services, executive coaching, jewellery trade, "
            "construction. You need a role where you can take the final decision.",

            "Common mistake: while in a job you will clash with your boss over ego. "
            "Solution: after age 30 it is right to leave the job and start something "
            "of your own. The Sun's energy suffocates in an 'employee' role.",

            "Growth timing: 22-24 (foundation), 28-32 (first big break), 36-40 "
            "(peak power), 45-50 (legacy phase). Sunday is your power day — hold "
            "important meetings and launches on Sunday morning.",
        ],
        "love_pattern": [
            "In love you are intense — you cannot sustain a half-hearted "
            "relationship. When you love, you love completely; when you break up, "
            "you break completely.",

            "The common reason for break-ups: you start dominating, and your "
            "partner feels suffocated. Or your partner tries to 'change' you — "
            "which a Number 1 will never tolerate.",

            "Ideal partner: Numbers 2, 4, or 7 work best — they ground your energy. "
            "Number 1 + Number 1 is explosive (twin suns burn each other).",
        ],
        "money_pattern":
            "Money comes to you in a zigzag pattern — sometimes a flood, sometimes "
            "a drought. A fixed salary will never satisfy you. Invest in stocks, "
            "business, and real estate. Gold (the Sun's metal) is your lucky "
            "store of value.",
        "health_pattern":
            "Watch the heart, eyes, blood pressure and back — they all fall under "
            "the Sun. Do 7 rounds of Surya Namaskar every morning — a direct "
            "planetary tonic.",
        "spiritual_path":
            "Your dharma is 'awakening others through your own light'. In spiritual "
            "practice the Aditya Hridaya Stotra (on Sundays) gives great strength. "
            "Becoming a guru is your path.",
        "strengths": [
            "Vision — you can see five years ahead",
            "Decision speed — no analysis paralysis",
            "Magnetism — people are naturally drawn to you",
            "Original thinking — you do not copy-paste",
            "Crisis leadership — you stay calm in emergencies",
        ],
        "challenges": [
            "Ego clashes with authority figures (boss, father)",
            "Loneliness at the top — no peer-level company",
            "Impatience with slow people",
            "Tendency to overrule advice",
            "Pride that cannot handle criticism",
        ],
        "risk_alerts": [
            "Conflict with a father-figure between 28-32 is possible — patience is essential",
            "Strict heart-health watch after 40 — annual check-up is mandatory",
            "Avoid partnership business unless the agreement is crystal-clear",
            "'Yes-men' will be magnetised to you — they will eventually betray you",
            "You impulse-buy on Sundays — take big decisions on Tuesdays",
        ],
        "golden_periods":
            "Sun-strong years are your peak. Whenever a Personal Year of 1, 5 or 9 "
            "arrives — that is your launch year. For 2026 specifically: calculate "
            "your Personal Year and decide accordingly. Mid-March to mid-July is "
            "your annual power window (Sun exalted in Aries).",
    },
}


# ─── Hindi (Devanagari) narratives ─────────────────────────────────────
# Drivers without an entry fall back to the Hinglish version.

_NARRATIVES_HI: Dict[int, Dict[str, Any]] = {}


def narrative_for(driver: int, lang: str = "hinglish") -> Dict[str, Any]:
    """Return the narrative pack for a given driver number (1-9), in the
    requested language. Falls back to Hinglish when the requested-language
    entry is not yet populated, so partial translations stay safe."""
    lang = (lang or "hinglish").lower()
    table: Dict[int, Dict[str, Any]]
    if lang == "english":
        table = _NARRATIVES_EN
    elif lang == "hindi":
        table = _NARRATIVES_HI
    else:
        table = _NARRATIVES_HG
    n = table.get(driver)
    if n:
        return n
    # Fallback: Hinglish (always populated)
    return _NARRATIVES_HG.get(driver, {})


# Backwards-compat alias for any external import that still references _NARRATIVES.
_NARRATIVES = _NARRATIVES_HG


def life_summary_block(driver: int, conductor: int, name: str,
                       lang: str = "hinglish") -> Dict[str, str]:
    """Generate a 4-point summary card for the top of premium PDF."""
    n = narrative_for(driver, lang) or {}
    PLANETS = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
               6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"}

    strengths = n.get("strengths") or [""]
    challenges = n.get("challenges") or [""]

    focus = _pick_extra(lang, _FOCUS_2026_EN, _FOCUS_2026_HI,
                        _FOCUS_2026_HG, driver) or "Self-discovery year."

    return {
        "core_personality": n.get("title", "—"),
        "tagline": n.get("tagline", "—"),
        "biggest_strength": strengths[0] if strengths else "—",
        "biggest_challenge": challenges[0] if challenges else "—",
        "2026_focus": focus,
        "primary_planet": PLANETS.get(driver, "—"),
        "secondary_planet": PLANETS.get(conductor, "—"),
        "name_signature": name,
    }


# ─── Why-Impact-Action conversion for number analysis ───────────────────

def why_impact_action_for_number(reduced: int, kind: str,
                                 lang: str = "hinglish") -> Dict[str, str]:
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

    why = _pick_extra(lang, _WHY_EN, _WHY_HI, WHY, (kind, reduced)) \
          or f"Number {reduced} is ruled by {planet}."

    _impact_default = {
        "english": "Its influence is felt slowly and steadily in your daily life.",
        "hindi":   "इसका प्रभाव आपके दैनिक जीवन में धीरे-धीरे महसूस होता है।",
        "hinglish":"Iska prabhav aapki daily life me dheere-dheere mehsoos hota hai.",
    }
    impact = _pick_extra(lang, _IMPACT_EN, _IMPACT_HI, IMPACT, (kind, reduced)) \
             or _impact_default.get((lang or "hinglish").lower(),
                                    _impact_default["hinglish"])

    if kind == "house":
        action = _pick_extra(lang, _HOUSE_ACTION_EN, _HOUSE_ACTION_HI,
                             HOUSE_ACTION, reduced) or ""
    else:
        action = _pick_extra(lang, _ACTION_EN, _ACTION_HI,
                             ACTION, (kind, reduced)) or ""

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


# ─── Planet directory + relationship table (used by all helpers) ───────

_PLANETS = {1: "Sun", 2: "Moon", 3: "Jupiter", 4: "Rahu", 5: "Mercury",
            6: "Venus", 7: "Ketu", 8: "Saturn", 9: "Mars"}

# Vedic planet relationship table — F=Friend, N=Neutral, E=Enemy
# Rows = perspective-of, Cols = target. Score 1 (worst) to 5 (best).
_REL: Dict[int, Dict[int, str]] = {
    1: {1: "T", 2: "F", 3: "F", 4: "E", 5: "N", 6: "E", 7: "E", 8: "E", 9: "F"},
    2: {1: "F", 2: "T", 3: "N", 4: "E", 5: "F", 6: "N", 7: "E", 8: "N", 9: "N"},
    3: {1: "F", 2: "N", 3: "T", 4: "N", 5: "E", 6: "E", 7: "N", 8: "N", 9: "F"},
    4: {1: "E", 2: "E", 3: "N", 4: "T", 5: "F", 6: "F", 7: "N", 8: "F", 9: "E"},
    5: {1: "N", 2: "F", 3: "E", 4: "F", 5: "T", 6: "F", 7: "F", 8: "N", 9: "N"},
    6: {1: "E", 2: "N", 3: "E", 4: "F", 5: "F", 6: "T", 7: "F", 8: "F", 9: "N"},
    7: {1: "E", 2: "E", 3: "N", 4: "N", 5: "F", 6: "F", 7: "T", 8: "F", 9: "E"},
    8: {1: "E", 2: "N", 3: "N", 4: "F", 5: "N", 6: "F", 7: "F", 8: "T", 9: "E"},
    9: {1: "F", 2: "N", 3: "F", 4: "E", 5: "N", 6: "N", 7: "E", 8: "E", 9: "T"},
}

_REL_SCORE = {"T": 95, "F": 80, "N": 60, "E": 30}  # T=Twin, F=Friend, N=Neutral, E=Enemy
_REL_LABEL = {"T": "TWIN",   "F": "FRIEND", "N": "NEUTRAL", "E": "ENEMY"}


def _rel(a: int, b: int) -> str:
    """Return relationship code T/F/N/E from a's perspective."""
    return _REL.get(a, {}).get(b, "N")


# ─── 1. Monthly Forecast pack ────────────────────────────────────────────

def _reduce(n: int) -> int:
    n = abs(int(n))
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


_MONTH_THEMES = {
    1: "🚀 New Beginnings — naya kaam start karne ka mahina. Independent decisions liye jayein. Networking strong.",
    2: "🤝 Patience + Partnership — wait + listen. Doosron ke saath collaborate karein. Avoid forcing decisions.",
    3: "✨ Creativity + Joy — social events, expressing yourself, writing/teaching. Networking phala-phool.",
    4: "🛠️ Hard Work + Foundation — system banayein, paperwork complete karein. Slow but steady.",
    5: "🌪️ Change + Movement — travel, new contacts, sudden opportunities. Flexibility maximum chahiye.",
    6: "❤️ Love + Family — relationship investment, beauty/home projects. Major announcements possible.",
    7: "🧘 Reflection + Spiritual — solo time, study, meditation. Big decisions postpone karein.",
    8: "💼 Power + Money — business deals close hote hain, promotions/contracts. Discipline sabse important.",
    9: "🔥 Completion + Release — old chapters band karein. Donations, forgiveness. Naya aane wala hai.",
}


def monthly_forecast_pack(driver: int, conductor: int, year: int = 2026,
                          lang: str = "hinglish",
                          dob: str | None = None) -> Dict[str, Any]:
    """Return 12-month forecast for given year — personal year/month + theme + best dates.

    Personal-Year formula: canonical numerology = reduce(DOB-month + DOB-day + year).
    Falls back to (driver+conductor+year) only when dob is not supplied (legacy callers).
    This keeps a single Personal-Year value across the whole report (matches Tier 10
    transits.py, career.py, numerology_pdf.py, numerology_pdf_part2.py).
    """
    if dob:
        try:
            _y, _m, _d = (int(x) for x in dob.split("-"))
            personal_year = _reduce(_reduce(_m) + _reduce(_d) + _reduce(year))
        except Exception:
            personal_year = _reduce(driver + conductor + _reduce(year))
    else:
        personal_year = _reduce(driver + conductor + _reduce(year))

    def _theme(pm: int, default: str) -> str:
        return _pick_extra(lang, _MONTH_THEMES_EN, _MONTH_THEMES_HI,
                           _MONTH_THEMES, pm) or default

    months = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for i, mname in enumerate(month_names, start=1):
        pm = _reduce(personal_year + i)
        best_dates = []
        for d in range(1, 32):
            r = _reduce(d)
            if _rel(driver, r) in ("T", "F"):
                best_dates.append(d)
        best5 = best_dates[:5]
        months.append({
            "month": mname,
            "personal_month": pm,
            "theme": _theme(pm, "Steady month."),
            "best_dates": best5,
            "verdict": "EXCELLENT" if pm in (1, 5, 8) else
                       "GOOD"      if pm in (3, 6, 9) else
                       "GENTLE"    if pm in (2, 7) else "WORK",
        })
    return {
        "year": year,
        "personal_year": personal_year,
        "year_theme": _theme(personal_year, "Self-growth year."),
        "months": months,
    }


# ─── 2. Deep Compatibility Matrix (Love / Marriage / Business) ────────────

def deep_compatibility_pack(driver: int) -> Dict[str, Any]:
    """Per-number love / marriage / business compatibility breakdown."""
    rows = []
    for n in range(1, 10):
        code = _rel(driver, n)
        base = _REL_SCORE[code]
        # Slight modulation for context
        love     = base + (5 if n in (2, 6) else 0) - (5 if n == 8 else 0)
        marriage = base + (5 if n in (1, 6) else 0) - (10 if n == 7 else 0)
        business = base + (5 if n in (5, 8) else 0) - (5 if n == 7 else 0)
        rows.append({
            "number": n,
            "planet": _PLANETS[n],
            "label": _REL_LABEL[code],
            "love": max(20, min(100, love)),
            "marriage": max(20, min(100, marriage)),
            "business": max(20, min(100, business)),
        })

    # Top 3 best & worst by average
    sorted_avg = sorted(rows, key=lambda r: -(r["love"] + r["marriage"] + r["business"]))
    return {
        "driver": driver,
        "rows": rows,
        "top3_best": sorted_avg[:3],
        "top3_worst": sorted_avg[-3:][::-1],
    }


# ─── 3. Lucky Numbers pack ─────────────────────────────────────────────

def lucky_numbers_pack(driver: int) -> Dict[str, Any]:
    friends = [n for n in range(1, 10) if _rel(driver, n) in ("T", "F")]
    enemies = [n for n in range(1, 10) if _rel(driver, n) == "E"]

    lucky_dates_of_month = sorted({d for d in range(1, 32) if _reduce(d) in friends})
    unlucky_dates = sorted({d for d in range(1, 32) if _reduce(d) in enemies})

    # Lucky double-digit picks (for PIN/account suffix) — pairs that reduce to friend
    lucky_pairs = []
    for tens in range(1, 10):
        for ones in range(0, 10):
            num = tens * 10 + ones
            if _reduce(num) in friends and num not in lucky_pairs:
                lucky_pairs.append(num)
    lucky_pairs = lucky_pairs[:8]

    LUCKY_DAY = {1: "Sunday", 2: "Monday", 3: "Thursday", 4: "Saturday",
                 5: "Wednesday", 6: "Friday", 7: "Tuesday", 8: "Saturday", 9: "Tuesday"}

    return {
        "single_digit_lucky":  friends,
        "single_digit_avoid":  enemies,
        "lucky_dates":         lucky_dates_of_month,
        "unlucky_dates":       unlucky_dates,
        "lucky_double_digit":  lucky_pairs,
        "lucky_day":           LUCKY_DAY.get(driver, "Sunday"),
        "atm_pin_tip":         f"4-digit PIN ke digits ka sum reduce karke {friends[0] if friends else driver} ya {friends[1] if len(friends)>1 else driver} aaye.",
        "account_tip":         f"Account/locker ke last 2-3 digits ka reduce {friends[0] if friends else driver} ho — bank choice me yeh dhyan rakhein.",
        "lottery_tip":         f"Lottery/contest entries {LUCKY_DAY.get(driver,'Sunday')} ko karein, dates {lucky_dates_of_month[:3]} preferred.",
    }


# ─── 4. Mantras + Remedies pack ────────────────────────────────────────

_MANTRA_PACK: Dict[int, Dict[str, str]] = {
    1: {
        "mantra": "Om Hraam Hreem Hroum Sah Suryaya Namah)",
        "count": "108 times daily, 7000 in 40-day cycle",
        "best_time": "Sunday sunrise (5:30-7:00 AM)",
        "stone": "Manik (Ruby) — gold ring, ring finger, right hand, Sunday sunrise",
        "yantra": "Surya Yantra — gold/copper plate, east wall of pooja room",
        "daan": "Wheat, jaggery, copper, red cloth — Sunday to Brahmin or temple",
        "color_focus": "Wear red/orange on Sunday",
    },
    2: {
        "mantra": "Om Shraam Shreem Shroum Sah Chandramase Namah)",
        "count": "108 times daily, 11000 in 40-day cycle",
        "best_time": "Monday early morning (4:30-6:00 AM)",
        "stone": "Moti (Pearl) — silver ring, little finger, right hand, Monday before sunrise",
        "yantra": "Chandra Yantra — silver, north-west wall",
        "daan": "Rice, milk, white cloth, sugar — Monday at temple",
        "color_focus": "Wear white/silver on Monday",
    },
    3: {
        "mantra": "Om Graam Greem Groum Sah Gurave Namah)",
        "count": "108 times daily, 19000 in 40-day cycle",
        "best_time": "Thursday sunrise",
        "stone": "Pukhraj (Yellow Sapphire) — gold ring, index finger, right hand, Thursday sunrise",
        "yantra": "Brihaspati Yantra — gold or yellow paper, north-east wall",
        "daan": "Yellow lentils (chana dal), turmeric, gold, banana, yellow cloth — Thursday",
        "color_focus": "Wear yellow on Thursday",
    },
    4: {
        "mantra": "Om Bhraam Bhreem Bhroum Sah Rahave Namah)",
        "count": "108 times daily, 18000 in 40-day cycle",
        "best_time": "Saturday twilight (5-7 PM)",
        "stone": "Gomed (Hessonite) — silver ring, middle finger, right hand, Saturday twilight",
        "yantra": "Rahu Yantra — silver/lead plate, south-west",
        "daan": "Black lentils (urad), black sesame, blue cloth — Saturday to needy",
        "color_focus": "Wear electric blue/grey on Saturday",
    },
    5: {
        "mantra": "Om Braam Breem Broum Sah Budhaya Namah)",
        "count": "108 times daily, 9000 in 40-day cycle",
        "best_time": "Wednesday morning",
        "stone": "Panna (Emerald) — gold ring, little finger, right hand, Wednesday morning",
        "yantra": "Budha Yantra — green silk, north wall",
        "daan": "Green moong dal, green vegetables, green cloth — Wednesday",
        "color_focus": "Wear green on Wednesday",
    },
    6: {
        "mantra": "Om Draam Dreem Droum Sah Shukraya Namah)",
        "count": "108 times daily, 16000 in 40-day cycle",
        "best_time": "Friday early morning",
        "stone": "Heera (Diamond) or White Sapphire — silver/platinum, middle finger, Friday morning",
        "yantra": "Shukra Yantra — silver, south-east",
        "daan": "White rice, sugar, white cloth, dairy — Friday",
        "color_focus": "Wear white/pink on Friday",
    },
    7: {
        "mantra": "Om Sraam Sreem Sroum Sah Ketave Namah)",
        "count": "108 times daily, 17000 in 40-day cycle",
        "best_time": "Tuesday/Saturday evening",
        "stone": "Lehsunia (Cat's Eye) — silver ring, middle finger, right hand, Tuesday evening",
        "yantra": "Ketu Yantra — multi-color silk, south-west",
        "daan": "Multi-color blanket, dog feeding, sesame, urad — Tuesday/Saturday",
        "color_focus": "Wear multi-color/grey on Tuesday or Saturday",
    },
    8: {
        "mantra": "Om Praam Preem Proum Sah Shanaishcharaya Namah)",
        "count": "108 times daily, 23000 in 40-day cycle",
        "best_time": "Saturday early morning or twilight",
        "stone": "Neelam (Blue Sapphire) — silver ring, middle finger, right hand, Saturday twilight (TEST 3 days first!)",
        "yantra": "Shani Yantra — iron/lead, west wall",
        "daan": "Black sesame, mustard oil, black cloth, iron, leather shoes to needy — Saturday",
        "color_focus": "Wear deep blue/black on Saturday",
    },
    9: {
        "mantra": "Om Kraam Kreem Kroum Sah Bhaumaya Namah)",
        "count": "108 times daily, 10000 in 40-day cycle",
        "best_time": "Tuesday sunrise",
        "stone": "Moonga (Red Coral) — gold/copper ring, ring finger, right hand, Tuesday sunrise",
        "yantra": "Mangal Yantra — copper plate, south wall",
        "daan": "Red lentils (masoor), red cloth, jaggery, copper — Tuesday at Hanuman temple",
        "color_focus": "Wear red on Tuesday",
    },
}


def mantras_pack(driver: int) -> Dict[str, Any]:
    pack = _MANTRA_PACK.get(driver, {})
    return {
        "planet": _PLANETS.get(driver, "—"),
        **pack,
    }


# ─── 5. Business Launch Calculator ─────────────────────────────────────

_DIRECTION = {1: "East", 2: "North-West", 3: "North-East", 4: "South-West",
              5: "North", 6: "South-East", 7: "South-West", 8: "West", 9: "South"}

# Driver → industries/business lines that amplify the planet's energy.
# (Classical Cheiro + Sepharial industry-planet mapping)
_BEST_BUSINESS_EN = {
    1: ["Leadership / Founder-CEO roles", "Gold &amp; jewellery",
        "Government contracts / PSU tenders", "Solo consulting / personal brand",
        "Luxury goods", "Media ownership / publishing house",
        "Politics-linked ventures"],
    2: ["Dairy &amp; milk products", "Water / beverages / bottled-water",
        "Hospitality &amp; catering", "Textiles &amp; clothing",
        "Cosmetics &amp; personal-care", "Mother-child &amp; baby products",
        "Food processing (liquids, curd, ghee)"],
    3: ["Education / coaching / training", "Publishing &amp; content",
        "Legal / advisory / consulting", "Finance &amp; wealth management",
        "Religious / spiritual products", "HR, recruitment &amp; mentoring",
        "Astrology / counselling"],
    4: ["IT / software / SaaS", "Import-export &amp; foreign trade",
        "Social media / digital platforms", "Disruptive / unconventional products",
        "Cryptocurrency / fintech", "Electronics &amp; gadgets",
        "Research-based startups"],
    5: ["Marketing / advertising agency", "Media, PR, journalism",
        "Sales / trading / affiliate business", "Travel &amp; tourism",
        "Stationery, publishing, printing", "Commission-based brokerage",
        "Communication apps / telecom"],
    6: ["Fashion, apparel &amp; footwear", "Beauty &amp; cosmetics",
        "Entertainment &amp; event planning", "Wedding &amp; luxury weddings",
        "Hotels, restaurants, cafes", "Interior design &amp; décor",
        "Auto &amp; vehicle showroom", "Jewellery &amp; perfumery"],
    7: ["Spiritual retreats / yoga studios", "Research &amp; analytics",
        "Writing, films, photography", "Astrology / tarot / healing",
        "Psychology / therapy", "Alternative medicine (Ayurveda, Reiki)",
        "Philosophical publishing / museums"],
    8: ["Real estate &amp; construction", "Mining, metals &amp; steel",
        "Heavy logistics &amp; warehousing", "Banking, NBFC, insurance",
        "Long-term asset management", "Iron, coal, cement trading",
        "Discipline-heavy manufacturing"],
    9: ["Sports, fitness &amp; gyms", "Defence, security, police-adjacent",
        "Engineering &amp; manufacturing", "Fire, weapons, heavy machinery",
        "Real-estate (construction side)", "Surgery, emergency medicine",
        "Red-industry (meat, spices, iron)"],
}

_BEST_BUSINESS_HI = {
    1: ["नेतृत्व / संस्थापक-सीईओ भूमिकाएँ", "सोना एवं आभूषण",
        "सरकारी ठेके / PSU निविदाएँ", "एकल परामर्श / व्यक्तिगत ब्रांड",
        "विलासिता वस्तुएँ", "मीडिया स्वामित्व / प्रकाशन गृह",
        "राजनीति से जुड़े उद्यम"],
    2: ["डेयरी एवं दुग्ध उत्पाद", "जल / पेय / बोतलबंद पानी",
        "आतिथ्य एवं खानपान", "वस्त्र एवं कपड़ा",
        "सौंदर्य एवं व्यक्तिगत देखभाल", "माँ-शिशु एवं शिशु उत्पाद",
        "खाद्य प्रसंस्करण (तरल, दही, घी)"],
    3: ["शिक्षा / कोचिंग / प्रशिक्षण", "प्रकाशन एवं कंटेंट",
        "विधिक / परामर्श / सलाह", "वित्त एवं धन प्रबंधन",
        "धार्मिक / आध्यात्मिक उत्पाद", "एचआर, भर्ती एवं मार्गदर्शन",
        "ज्योतिष / परामर्श"],
    4: ["आईटी / सॉफ़्टवेयर / SaaS", "आयात-निर्यात एवं विदेश व्यापार",
        "सोशल मीडिया / डिजिटल प्लेटफ़ॉर्म", "अनोखे / असामान्य उत्पाद",
        "क्रिप्टो / फ़िनटेक", "इलेक्ट्रॉनिक्स एवं गैजेट",
        "अनुसंधान आधारित स्टार्टअप"],
    5: ["मार्केटिंग / विज्ञापन एजेंसी", "मीडिया, पीआर, पत्रकारिता",
        "बिक्री / व्यापार / सहबद्ध व्यवसाय", "यात्रा एवं पर्यटन",
        "स्टेशनरी, प्रकाशन, प्रिंटिंग", "कमीशन आधारित दलाली",
        "संचार ऐप्स / टेलीकॉम"],
    6: ["फ़ैशन, वस्त्र एवं जूते", "सौंदर्य एवं प्रसाधन",
        "मनोरंजन एवं इवेंट प्लानिंग", "विवाह एवं विलासिता विवाह",
        "होटल, रेस्तरां, कैफ़े", "आंतरिक सज्जा एवं डेकोर",
        "ऑटो एवं वाहन शोरूम", "आभूषण एवं इत्र"],
    7: ["आध्यात्मिक रिट्रीट / योग स्टूडियो", "शोध एवं विश्लेषण",
        "लेखन, फ़िल्म, फ़ोटोग्राफ़ी", "ज्योतिष / टैरो / हीलिंग",
        "मनोविज्ञान / चिकित्सा", "वैकल्पिक चिकित्सा (आयुर्वेद, रेकी)",
        "दार्शनिक प्रकाशन / संग्रहालय"],
    8: ["रियल एस्टेट एवं निर्माण", "खनन, धातु एवं इस्पात",
        "भारी लॉजिस्टिक्स एवं वेयरहाउसिंग", "बैंकिंग, NBFC, बीमा",
        "दीर्घकालिक संपत्ति प्रबंधन", "लोहा, कोयला, सीमेंट व्यापार",
        "अनुशासन-प्रधान निर्माण"],
    9: ["खेल, फ़िटनेस एवं जिम", "रक्षा, सुरक्षा, पुलिस-संबद्ध",
        "इंजीनियरिंग एवं विनिर्माण", "अग्नि, शस्त्र, भारी मशीनरी",
        "रियल एस्टेट (निर्माण पक्ष)", "सर्जरी, आपातकालीन चिकित्सा",
        "लाल-उद्योग (मांस, मसाले, लोहा)"],
}

_BEST_BUSINESS_HG = {
    1: ["Leadership / founder-CEO roles", "Gold &amp; jewellery business",
        "Government contracts / PSU tenders", "Solo consulting / personal brand",
        "Luxury goods", "Media ownership / publishing house",
        "Politics-linked ventures"],
    2: ["Dairy / milk products", "Paani, beverages, bottled-water",
        "Hospitality aur catering", "Textiles aur kapda",
        "Cosmetics aur personal care", "Mother-child aur baby products",
        "Food processing (liquids, curd, ghee)"],
    3: ["Education / coaching / training", "Publishing aur content",
        "Legal / advisory / consulting", "Finance aur wealth management",
        "Religious / spiritual products", "HR, recruitment aur mentoring",
        "Astrology / counselling"],
    4: ["IT / software / SaaS", "Import-export aur foreign trade",
        "Social media / digital platforms", "Disruptive / unconventional products",
        "Crypto / fintech", "Electronics aur gadgets",
        "Research-based startups"],
    5: ["Marketing / advertising agency", "Media, PR, journalism",
        "Sales / trading / affiliate business", "Travel aur tourism",
        "Stationery, publishing, printing", "Commission-based brokerage",
        "Communication apps / telecom"],
    6: ["Fashion, apparel aur footwear", "Beauty aur cosmetics",
        "Entertainment aur event planning", "Wedding aur luxury weddings",
        "Hotels, restaurants, cafes", "Interior design aur décor",
        "Auto / vehicle showroom", "Jewellery aur perfumery"],
    7: ["Spiritual retreats / yoga studios", "Research aur analytics",
        "Writing, films, photography", "Astrology / tarot / healing",
        "Psychology / therapy", "Ayurveda, Reiki, alternative medicine",
        "Philosophical publishing / museums"],
    8: ["Real estate aur construction", "Mining, metals aur steel",
        "Heavy logistics aur warehousing", "Banking, NBFC, insurance",
        "Long-term asset management", "Iron, coal, cement trading",
        "Discipline-heavy manufacturing"],
    9: ["Sports, fitness aur gyms", "Defence, security, police-adjacent",
        "Engineering aur manufacturing", "Fire, weapons, heavy machinery",
        "Real-estate (construction side)", "Surgery, emergency medicine",
        "Red-industry (meat, spices, iron)"],
}


def business_launch_pack(driver: int, year: int = 2026,
                         lang: str = "hinglish") -> Dict[str, Any]:
    forecast = monthly_forecast_pack(driver, driver, year)  # use driver as conductor stand-in if unknown
    # Actually need real conductor — caller will pass via overload
    # For Part 2 use, we recompute with actual conductor in render
    best_months = [m for m in forecast["months"] if m["verdict"] in ("EXCELLENT", "GOOD")]
    best_months_top = best_months[:6]

    friends = [n for n in range(1, 10) if _rel(driver, n) in ("T", "F")]
    name_numbers = friends[:3] if friends else [driver]
    partner_numbers = friends[:3] if friends else [driver]

    lmap = (lang or "hinglish").lower()
    if lmap == "english":
        biz = _BEST_BUSINESS_EN.get(driver, [])
    elif lmap == "hindi":
        biz = _BEST_BUSINESS_HI.get(driver, [])
    else:
        biz = _BEST_BUSINESS_HG.get(driver, [])

    # Localised tip strings
    if lmap == "english":
        name_tip = (f"Keep your company/brand name so its letter-total reduces "
                    f"to {name_numbers[0] if name_numbers else driver} or "
                    f"{name_numbers[1] if len(name_numbers)>1 else driver} — "
                    f"use Chaldean numerology.")
        logo_tip = (f"Let {_PLANETS.get(driver,'—')}'s colours dominate the logo.")
        invoice_tip = (f"Start your first invoice number from "
                       f"{name_numbers[0] if name_numbers else driver} "
                       f"or a master number (11 / 22).")
    elif lmap == "hindi":
        name_tip = (f"कंपनी/ब्रांड नाम ऐसा रखें कि उसके अक्षरों का कुल योग "
                    f"{name_numbers[0] if name_numbers else driver} या "
                    f"{name_numbers[1] if len(name_numbers)>1 else driver} पर रिड्यूस हो — "
                    f"चाल्डियन अंक-शास्त्र का प्रयोग करें।")
        logo_tip = (f"लोगो में {_PLANETS.get(driver,'—')} के रंग प्रमुख रखें।")
        invoice_tip = (f"पहला इनवॉइस नंबर "
                       f"{name_numbers[0] if name_numbers else driver} "
                       f"या मास्टर संख्या (11 / 22) से शुरू करें।")
    else:
        name_tip = (f"Company/brand name ke letters ka total reduce karke "
                    f"{name_numbers[0] if name_numbers else driver} ya "
                    f"{name_numbers[1] if len(name_numbers)>1 else driver} aaye — "
                    f"Chaldean numerology use karein.")
        logo_tip = (f"Logo me {_PLANETS.get(driver,'—')} ke colours dominate karein.")
        invoice_tip = (f"Pehla invoice number "
                       f"{name_numbers[0] if name_numbers else driver} "
                       f"ya 11/22 (master) se shuru karein.")

    return {
        "driver": driver,
        "office_direction": _DIRECTION.get(driver, "East"),
        "office_facing": "Sit facing your direction — desk should face it.",
        "best_launch_months": [{"month": m["month"], "verdict": m["verdict"]}
                                for m in best_months_top],
        "best_business_types": biz,
        "best_company_name_numbers": name_numbers,
        "best_partner_numbers": partner_numbers,
        "avoid_partner_numbers": [n for n in range(1, 10) if _rel(driver, n) == "E"],
        "name_tip": name_tip,
        "logo_tip": logo_tip,
        "registration_day": {1: "Sunday", 2: "Monday", 3: "Thursday", 4: "Saturday",
                             5: "Wednesday", 6: "Friday", 7: "Tuesday",
                             8: "Saturday", 9: "Tuesday"}.get(driver, "Sunday"),
        "first_invoice_tip": invoice_tip,
    }


# ─── 6. Celebrity Match ────────────────────────────────────────────────

_CELEBRITY_MATCH: Dict[int, List[Dict[str, str]]] = {
    1: [
        {"name": "Mukesh Ambani",   "born": "19 April",     "lesson": "Vision + risk-taking — empire build kiya from scratch."},
        {"name": "Lata Mangeshkar", "born": "28 September", "lesson": "Solo excellence — one voice, decades dominate."},
        {"name": "Ratan Tata",      "born": "28 December",  "lesson": "Quiet authority + ethics — leadership ka best example."},
        {"name": "Bill Gates",      "born": "28 October",   "lesson": "Innovation + philanthropy — wealth ko purpose se jodna."},
    ],
    2: [
        {"name": "Shahrukh Khan",     "born": "2 November",  "lesson": "Charm + emotional intelligence — sab ke saath connect."},
        {"name": "Amitabh Bachchan",  "born": "11 October",  "lesson": "Reinvention + voice — har generation ke saath grow."},
        {"name": "Mahatma Gandhi",    "born": "2 October",   "lesson": "Soft power — non-violence se duniya badli."},
    ],
    3: [
        {"name": "Rajinikanth", "born": "12 December", "lesson": "Authentic style + spiritual core — fame ke baad bhi grounded."},
        {"name": "Anushka Sharma", "born": "1 May (3)", "lesson": "Multi-talent expansion — actor + producer + entrepreneur."},
        {"name": "Generic 3-driver", "born": "3rd / 12th / 21st / 30th", "lesson": "Communication + creativity ka natural gift."},
    ],
    4: [
        {"name": "Barack Obama", "born": "4 August", "lesson": "Disruption + structure — system ko outside-in se badla."},
        {"name": "Generic 4-driver", "born": "4th / 13th / 22nd / 31st", "lesson": "Tech + foreign opportunities, sudden breakthroughs."},
    ],
    5: [
        {"name": "Virat Kohli",       "born": "5 November",  "lesson": "Aggression + adaptability — har format me dominate."},
        {"name": "Aamir Khan",        "born": "14 March",    "lesson": "Versatility + perfectionism — multi-discipline mastery."},
        {"name": "Mark Zuckerberg",   "born": "14 May",      "lesson": "Communication empire — connection ka business."},
        {"name": "Albert Einstein",   "born": "14 March",    "lesson": "Curiosity + intellectual courage — paradigms badle."},
    ],
    6: [
        {"name": "Sachin Tendulkar", "born": "24 April",   "lesson": "Beauty + consistency — record over flash."},
        {"name": "A.R. Rahman",      "born": "6 January",  "lesson": "Art + spiritual depth — music ko sadhana banaya."},
        {"name": "Steve Jobs",       "born": "24 February","lesson": "Aesthetic obsession — design ko religion banaya."},
        {"name": "A.P.J. Kalam",     "born": "15 October", "lesson": "Service + grace — power ko humility se carry kiya."},
    ],
    7: [
        {"name": "M.S. Dhoni", "born": "7 July", "lesson": "Calm under pressure — chaos me solo clarity."},
        {"name": "Generic 7-driver", "born": "7th / 16th / 25th", "lesson": "Mystery + introspection — thinkers + healers."},
    ],
    8: [
        {"name": "Narendra Modi",   "born": "17 September", "lesson": "Discipline + long game — slow but unstoppable rise."},
        {"name": "Saurav Ganguly",  "born": "8 July",       "lesson": "Authority + comeback — kabhi haar nahi maani."},
        {"name": "Roger Federer",   "born": "8 August",     "lesson": "Longevity + structure — graceful empire."},
    ],
    9: [
        {"name": "Salman Khan",   "born": "27 December", "lesson": "Raw energy + loyalty — passion-driven empire."},
        {"name": "Akshay Kumar",  "born": "9 September", "lesson": "Discipline + action — early rise + zero drama."},
        {"name": "Generic 9-driver", "born": "9th / 18th / 27th", "lesson": "Warriors + healers — dono modes available."},
    ],
}


def celebrity_match_pack(driver: int) -> List[Dict[str, str]]:
    return _CELEBRITY_MATCH.get(driver, [])


def lucky_colours_pack(driver: int, lang: str = "hinglish") -> Dict[str, Any]:
    """Return complete lucky colours pack for a driver number — used in Part 2."""
    pack = _LUCKY_COLOURS.get(driver, {})
    extras = _pick_extra(lang, _LUCKY_COLOUR_STRINGS_EN,
                         _LUCKY_COLOUR_STRINGS_HI,
                         {d: {"vehicle": _LUCKY_COLOURS[d].get("vehicle"),
                              "business": _LUCKY_COLOURS[d].get("business"),
                              "gemstone_tone": _LUCKY_COLOURS[d].get("gemstone_tone")}
                          for d in _LUCKY_COLOURS},
                         driver) or {}
    return {
        "primary":     pack.get("primary", []),
        "secondary":   pack.get("secondary", []),
        "avoid":       pack.get("avoid", []),
        "vehicle":     extras.get("vehicle")     or pack.get("vehicle", "—"),
        "business":    extras.get("business")    or pack.get("business", "—"),
        "gemstone_tone": extras.get("gemstone_tone") or pack.get("gemstone_tone", "—"),
        "day_dress":   _DAY_DRESS_COLOURS,
    }


# ─── Auto-generated drivers 2-9 (OpenAI bulk translate, reviewed) ───
_NARRATIVES_EN.update({6: {'title': "The Lover — Venus's Beauty Bringer", 'tagline': 'You are the embodiment of love, art, and beauty.', 'life_essence': ['Number 6 is ruled by Venus. You have come to make this world beautiful. You cannot tolerate anything awkward or ugly — clothes, home, conversation, food — everything must be elegant.', 'You are a natural family person. In relationships, you are the glue. Mother, sister, wife, friend — you invest time with them like no one else. This is both your greatest joy and greatest energy drain.', "Venus's warning: 'over-attachment'. You start loving someone so much that you forget yourself. Learning self-love is a lifelong lesson for those with Number 6. Investing time in yourself is never 'selfish' — it is actually sustainable for the relationship."], 'career_pattern': ['Best fields: arts (music, dance, painting), fashion, beauty/cosmetics, entertainment industry, hospitality, luxury goods, jewellery, interior design, wedding planning, hotels/restaurants, perfumery, photography, vehicle/car industry. Anywhere beauty meets business.', "Common mistake: In the cycle of family responsibility, you compromise your dreams. After 40, there is regret. Solution: family AND personal growth — not 'OR'.", 'Growth timing: 25-30 first phase (often through marriage/partnership), 32-38 peak income, 45-52 luxury phase. Friday is your power day — major launches on Friday.'], 'love_pattern': ['In love, you are a king/queen — romance, gifts, surprises, candlelit dinners — all come naturally to you. Your partner becomes spoiled by you.', "Breakup reason: You give too much, then expect an equal return — when it doesn't come, resentment builds silently. Communication of needs is essential.", "Ideal partner: Numbers 3, 6, 9 — wisdom + beauty match. Number 7 + 6 is interesting (Ketu's detachment vs Venus's attachment) — together on a growth path."], 'money_pattern': "Money comes to you through relationships, beauty, or luxury. You spend more on luxury — it's genetic, don't fight it. Just maintain a strict income > expense ratio. Diamond, white gold, silk, perfume — your lucky assets.", 'health_pattern': 'Reproductive organs, kidneys, throat, skin glow — under Venus. Your skin condition reflects your emotional state — relationship stress = skin issues. Take sweets + ghee in balance.', 'spiritual_path': "Your dharma is 'love through beauty'. Lakshmi sadhana, Devi worship, Krishna devotion suits you. Donate white items on Friday. Bhakti-yoga is your path (not jnana-yoga).", 'strengths': ['Aesthetic sense — you make everything beautiful', 'Relationship maintenance — long friendships', 'Diplomacy — you create peace', 'Generosity — open-hearted giver', 'Charm — leave an impression in the first meeting'], 'challenges': ['Over-spending on luxury', 'Family enmeshment — weak boundaries', 'Avoidance of conflict', 'Vanity (looks-obsessed)', 'Comfort-zone trapped — love of ease'], 'risk_alerts': ['Luxury spending over 40% of income → financial trap', 'Vehicle accidents possible between 26-28 — drive defensively', 'Stuck in a toxic relationship for 7+ years — seek counseling', 'Reproductive health attention for women between 28-32', 'Friday fasting or white donation for 16 weeks — Venus blessings'], 'golden_periods': "Personal Year 6 — relationship + family + beauty all peak. Venus mahadasha (20 years) is a classic 'sukh' phase. April-May Venus exalted in Pisces — creativity peak. Work on art/beauty/relationships at Friday sunrise."}, 7: {'title': "The Mystic — Ketu's Spiritual Researcher", 'tagline': 'You appear in this world yet remain unseen.', 'life_essence': ['Number 7 is ruled by Ketu — the moksha karaka. You are a mystery — even to yourself. You can never be 100% absorbed in the material world, as you are internally searching for something else — meaning, truth, depth.', "Since childhood, you might have enjoyed solitude. Even in a crowd, you remain 'with yourself'. This isolation is not your weakness — it is your research lab. The greatest discoveries have been made by those with Number 7 (Einstein, Tesla, J.K. Rowling — all are 7s).", "Ketu's warning: 'going too far into detachment'. You become so disconnected from relationships, responsibilities, and society that functioning becomes difficult. Ground-rule: spend 1 hour daily in the 'practical world' — bills, family, health."], 'career_pattern': ['Best fields: research, science, philosophy, writing, spirituality/yoga, investigation/forensics, occult, photography, water-related work (marine, import-export), psychology, archaeology, IT R&D, alternative healing. You shine in solo professional roles.', "Common mistake: Ignoring mainstream success as 'shallow' — then realizing at 35 that money is necessary. Solution: spiritual AND practical — both can coexist. Money is also energy, do not reject it.", "Growth timing: Late bloomers — real recognition comes between 35-45. Ketu's mahadasha (7 years) turns life upside-down (good or bad). Tuesday/Saturday are your power days (Ketu connections)."], 'love_pattern': ["In love, you are distant — you do not let your partner 'fully reach' you. A part of you always remains alone. This is frustrating for your partner.", "Breakup reason: 'I don't know what you want' — this is your partner's common complaint. You yourself do not know. Solution: start journaling — discover yourself, then you can tell your partner.", "Ideal partner: Numbers 4, 7, 1 — they respect independence. Marriage may happen late (after 28-30) — accept it, don't rush."], 'money_pattern': "Money comes to you through knowledge — research, writing, consulting, healing. You are more intellectual than material — this makes financial planning challenging. Auto-investment SIP is a life-saver for you. Ketu metals — multi-color (cat's eye after consultation).", 'health_pattern': 'Nervous system, mysterious skin issues, immunity, gas/digestion, eyes — fall under Ketu. You experience random unexplained ailments. Naturopathy + Ayurveda + meditation are better for you than conventional medicine.', 'spiritual_path': "Your dharma is 'the search for inner truth'. Practices related to Ganesha (Ketu's son), Hanuman, Shiva, Kali — all work for you. A 10-day Vipassana course will be life-changing.", 'strengths': ['Deep research ability', 'Intuition — paranormal sensing', 'Self-sufficient', 'Detached judgment — bias-free', 'Mystical experiences come naturally'], 'challenges': ['Risk of depression in loneliness', 'Struggle in the practical world (bills, scheduling)', 'Difficulty with relationship intimacy', 'Tendency for late marriage / no marriage', 'Mismatch with conventional society'], 'risk_alerts': ['Risk of escapism through drugs/alcohol — staying sober is mandatory', 'Sudden unexplained illnesses between 28-32 — get an Ayurveda checkup', 'Loneliness can lead to depression — talk to a therapist', 'Impulsively rejecting material decisions — consult a financial guru', "Recite Hanuman Chalisa 11 times on Tuesday — for Ketu's peace and protection"], 'golden_periods': 'Personal Year 7 — spiritual and research breakthroughs. Ketu mahadasha (7 years) is transformative. Late autumn (Oct-Nov) is the peak for yearly meditation and insight. A solo retreat once a year is mandatory.'}, 2: {'title': 'The Diplomat — Moon-blessed Connector', 'tagline': 'You are the unsung healers of this world.', 'life_essence': ["Number 2 is ruled by Chandra — and Chandra's energy is fluid and reflective. Sit with someone for 5 minutes and you can pick up and imitate their body language. This empathy is your greatest gift and also your greatest burden.", "You attract lonely people — emotional, broken, or confused individuals feel 'safe' with you. This is no accident. You are a natural counselor. But the price is that you often ignore your own emotional needs.", "Chandra's most important lesson is — 'phases'. Every 28 days you go through a complete emotional cycle — one week high, one week medium, one week low, one week recovery. Don't fight this cycle — learn to flow with it."], 'career_pattern': ['Best fields: counseling, HR, nursing, hospitality, food/dairy business, writing (especially fiction/poetry), psychology, social work, navy, marine work, interior design. You shine in public-facing emotional roles.', 'Common mistake: You get drained in aggressive sales or competitive corporate jobs. Burnout occurs in 4-5 years. Long-term work with emotional rewards is what sustains you.', 'Growth timing: Slow burn — your peak comes between 32-38 (not before). Until then, groundwork. Monday is your power day — make major emotional decisions on Monday morning.'], 'love_pattern': ["In love, you give-give-give. Your partner's needs come before your own. This is beautiful but unsustainable.", "Common reason for breakups: You don't express your emotions, you internalize them — and one day you suddenly say 'I'm done'. The partner is shocked because they missed the signals. Lesson: even small things should be spoken.", 'Ideal partner: Numbers 1, 4, or 8 — they provide the structure that the Moon needs. Number 5 + 2 is turbulent (Mercury moves the Moon too much).'], 'money_pattern': 'Money comes and goes like tides for you. Forcefully develop a savings habit — automatic SIP is best. Invest in silver, pearl, and white items. Keep a liquid emergency fund for 6 months — the Moon needs to feel secure.', 'health_pattern': 'Stomach, breast (women), lungs, sleep cycle — under Chandra. Avoid late nights. On a full moon, drink detox water and sleep early — it will reduce swelling in the body.', 'spiritual_path': "Your dharma is 'emotional purification of others'. Mata pooja, Devi worship, Lakshmi sadhana — all are Chandra-friendly. Observe a Monday fast for 16 weeks — transformative.", 'strengths': ['Empathy — you can see inside people', 'Diplomacy — you know how to resolve conflict', 'Adaptability — you adjust to every situation', 'Aesthetic sense — deep understanding of beauty', 'Patience — you win in the long game'], 'challenges': ['Mood swings — 28-day cycle is hard to manage', 'Over-giving leads to resentment', 'Avoidance of confrontation', 'Indecision at critical moments', 'Emotional eating or emotional spending'], 'risk_alerts': ['Pay attention to the health of your mother or female elder — karmic connection is deep', 'Exercise extra caution in water-related travel — water is symbolic on your life path', 'You can be stuck in toxic friendships for 5+ years — conduct an annual relationship audit', 'Tendency to fall into depression — find a counselor who can sympathize', 'Never make late-night decisions — the Moon is weak at night'], 'golden_periods': 'Your life unfolds in Personal Year 2, 4, 6, or 8. Your manifestation power peaks 3 days before and after the full moon — set important wishes or intentions in that window. October-November is your yearly soft power window (Chandra exalted in Taurus).'}, 3: {'title': "The Sage — Jupiter's Wisdom Carrier", 'tagline': 'You are destined to convert knowledge into wealth.', 'life_essence': ["Number 3 is ruled by Brihaspati (Jupiter) — the guru planet. You are an old soul by birth. People might have said in your childhood, 'you are more mature than your age'. This is no accident — your soul has come with wisdom from many lifetimes.", "You excel in teaching, sharing, and expanding. When someone is confused in front of you, you automatically become philosophical — you unconsciously provide a 'look at it this way' framing. This is your true calling.", "Jupiter has a warning — 'over-expansion'. Sometimes you know so much that you speak confidently without deeply verifying. This ego gap can cause you significant harm. Humility + knowledge = your golden combination."], 'career_pattern': ["Best fields: teaching, law, finance/banking, publishing, religion/spirituality, journalism, research, judiciary, advisory roles, content creation, philosophy, venture capital. Wherever the equation 'wisdom = wealth' applies.", 'Common mistake: Neglect towards practical execution — you are content with just giving advice, doing less yourself. Result: people learn from you and move ahead, while you remain stagnant. Solution: fully execute one or two projects yourself, combining theory and practice.', 'Growth timing: 24-27 first wisdom phase, 33-36 peak teaching phase, 45-50 legacy + wealth phase. Thursday is your power day. Work started in Brihaspati hora flourishes.'], 'love_pattern': ["In love, you become a mentor — you 'guide' your partner. This is seductive initially, but in the long term, the partner feels suffocated (who wants a parent as a partner?).", "Breakup reason: the feeling of 'I outgrew you'. Your growth is fast, and the partner lags behind. Solution: give your partner space to grow as well, not just you.", 'Ideal partner: Numbers 6, 9, or 3 — those on the same wisdom wavelength. Number 5 + 3 is intellectually brilliant but emotionally turbulent.'], 'money_pattern': "Money comes to you through knowledge — teaching, advising, writing, consulting. You are a natural mentor — definitely build an income stream from coaching/teaching, even if it's on the side. Yellow gemstones (yellow sapphire) strengthen Jupiter — but only after astrologer confirmation.", 'health_pattern': 'Liver, fat metabolism, hips, ears, nervous system — under Jupiter. Avoid over-eating sweets (Jupiter + sugar = dangerous). Regularly consume yellow foods (turmeric, banana, ghee).', 'spiritual_path': "Your dharma is 'gyan-daan' (wisdom-giving). Guru worship, Brihaspati mantra, Sai-Baba devotion will suit you. Build a habit of reading scriptures daily for 5 minutes — exponential wisdom.", 'strengths': ['Wisdom beyond age', 'Teaching/explaining clarity', 'Optimism — naturally positive', 'Generosity — you give abundantly', 'Long-term strategic thinking'], 'challenges': ['Giving wrong advice due to overconfidence', 'Weakness in execution — only planning', 'Weight gain after 30 — Jupiter expansion is literal', 'Sermonizing — people get tired of unsolicited advice', 'Over-attached to children/students'], 'risk_alerts': ['Strict liver health watch after 35 — limit alcohol and fried food', 'Tendency to become a financial advisor — personal financial loss', 'Risk of getting trapped in religious cults — maintain discernment', "Children/disciples' failures affect you personally — learn detachment", 'Performing Thursday fasts or donating yellow items — keeps Jupiter strong'], 'golden_periods': 'Personal Year 3, 6, 9 — earning through knowledge. In the 12-year cycle of Guru-gochar (Jupiter transit), strongest in signs 1, 5, 9. Writing/teaching during Jupiter hora from 7-9 AM daily is extra blessed.'}, 8: {'title': "The Builder — Saturn's Karmic Magnate", 'tagline': 'You are destined to become a diamond through struggle.', 'life_essence': ['Number 8 is ruled by Saturn. In your life, nothing comes for free — you have either shed sweat for everything or will have to. This is not injustice — it is the chosen path of your soul. You are a karma-yogi.', "Since childhood, you might have been called 'serious' — because you truly are serious. Even in play, you see strategy. This quality makes you very big in the long term — but gives a lot of loneliness at a young age.", "Saturn's most important lesson: 'patience'. Real success for those under 8 begins after 35. First, Saturn prepares you by 'dunking you in water'. Do not fight this process. Discipline and patience are the master keys for 8."], 'career_pattern': ['Best fields: real estate, mining, oil, heavy industry, government job, judiciary, engineering, infrastructure, banking, insurance, social justice work, chronic disease healing, undertaking, archaeology, antiques. Slow + structured + long-term — this is the territory of 8.', 'Common mistake: Wanting quick success — then frustration, then shortcuts, then downfall. Shortcuts are very costly for those under 8. Solution: Make a 10-year plan for every goal. Saturn works in 10-year cycles.', 'Growth timing: 36-42 first big peak (Saturn return), 48-55 wealth crystallization, 58-65 legacy. Saturday is your power day. Late evening (Saturn hora) decisions.'], 'love_pattern': ["In love, you are loyal and committed — until you commit, you are guarded, but once committed, it's forever. This quality is precious but initially not understood by the partner.", "Breakup reason: Coldness — you do not show emotion, and the partner feels 'you do not love me'. Solution: Express love not just through actions but also words — uncomfortable but necessary.", 'Ideal partner: Number 4, 8, 6 — balance of discipline + warmth. Late marriage (after 30) is better. Hasty marriage = lifelong regret.'], 'money_pattern': 'Money comes to you slowly + steadily. The phase from 25-35 is typically a struggle, and wealth crystallizes between 35-50. Real estate, fixed assets, slow compounding investments are perfect for you. Black/dark blue items, iron, blue sapphire (after consultation) strengthen Saturn.', 'health_pattern': 'Bones, joints, knees, teeth, chronic conditions, depression — under Saturn. Discipline in daily exercise (especially walking) is a MUST. Sesame oil, urad dal, iron-rich foods. Saturday fast (only fruits) is very healing.', 'spiritual_path': "Your dharma is 'karma-yoga through service to the underprivileged'. Shani sadhana, Hanuman, Bhairav. Saturday black sesame donation, blanket donation in cold weather. Cleaning toilets/orphanage service — direct Saturn pacification.", 'strengths': ['Discipline — strictly follow schedule', 'Endurance — handle long-term struggles', 'Strategic mind — like a chess player', 'Loyalty — once committed, forever', 'Justice-orientation — fairness matters'], 'challenges': ['Perception of emotional coldness', "Pessimism — 'nothing good will happen' mindset", 'Slow visible progress (frustrating in youth)', 'Workaholism — forget joy', 'Authority issues with father/boss'], 'risk_alerts': ['Conflict or distance with a father-figure — childhood pattern', 'Bone/joint injury possible between 30-32 — yoga is mandatory', 'Depression risk between 28-30 (Saturn return) — take therapy', 'Family neglect due to workaholism — schedule family time', 'Saturday black sesame + mustard oil donation for 21 weeks — balance Saturn'], 'golden_periods': 'Personal Year 8 — wealth + recognition + power all peak. Saturn mahadasha (19 years) — initial test, then rich rewards. December-January yearly Saturn peak. The entire phase of 36-42 is your launchpad — start anything.'}, 9: {'title': "The Warrior — Mars's Soldier of Truth", 'tagline': 'You are destined to fight for your passion.', 'life_essence': ['Number 9 is ruled by Mars. You are a volcano of energy — a fire burns within you. This fire is both your greatest power and greatest danger. Channeled = you will move mountains. Uncontrolled = you will burn yourself.', "Since childhood, you might have been called 'hot-tempered'. This is just the surface. Your real fire is — passion, courage, drive. When you fall in love with a cause, you can fight for it alone.", "Mars's most important lesson: 'where to use your power and where to hold back'. Your energy is not unlimited — use it strategically, not emotionally. Daily 60 minutes of physical exercise is therapy for you, not a luxury."], 'career_pattern': ['Best fields: military, police, sports, surgery (especially trauma), real estate, construction, engineering (mechanical/civil), firefighting, security, mining, butchery, pharma, sports management, fitness training, motivational speaking. Anywhere physical/emotional courage is required.', "Common mistake: Clash with boss/authority. You do not tolerate 'unfair' — you punch or quit. Solution: After 30, self-employment/own business is best — Mars suffocates in employee mode.", 'Growth timing: Early peak (24-28 first surge), 32-36 stabilization, 42-48 legacy phase. Tuesday is your power day. Sunrise time is when you are most powerful.'], 'love_pattern': ['In love, you are intense, possessive, passionate. Often starts with an affair-style romance. Managing jealousy is a major lifelong project.', 'Breakup reason: Anger explosion — you say something that cannot be undone. Solution: When anger rises, follow the 24-hour wait rule — do not say or send anything. Anger is a wave, it will pass.', 'Ideal partner: Numbers 1, 5, 9, 3 — energy match. Number 9 + 9 is explosive (double Mars). Manglik dosha is prevalent in 9s — match before marriage.'], 'money_pattern': 'You earn money by sending energy — physical work, courage-required jobs, high-risk + high-return ventures. You take risks others cannot. Real estate, gold, red items, copper, coral (after consultation) — are your lucky assets.', 'health_pattern': 'Blood, muscles, head, surgery prone — under Mars. Accident risk is higher than average — extra safety in driving/sports. Annual blood-related checkup. Balance spicy food — Mars + chili = ulcer.', 'spiritual_path': "Your dharma is 'fight for truth, protect the weak'. Hanuman sadhana is perfect (Mars's son). Subramanya/Kartikeya devotion. Tuesday + Saturday recite Hanuman Chalisa 11 times. Donate red cloth/red flowers on Tuesday.", 'strengths': ['Courage — you face fear', 'Energy — you can move mountains', 'Passion — you give 200% in what you do', 'Protective instinct — you fight for your loved ones', 'Initiative — you go first, others follow'], 'challenges': ['Anger management is a lifelong project', 'Impulsivity — you act first, think later', 'Jealousy in relationships', 'Prone to physical injury', 'Authority clashes'], 'risk_alerts': ['Accident risk between 24-26 + 32-34 — drive slowly and cautiously', 'Anger can cause permanent damage in relationships — 24-hour rule is a MUST', 'Manglik check before marriage — high probability in 9s', 'Surgery is likely 1+ times in life — get health insurance early', 'Tuesday Hanuman service, sindoor offering — for Mars peace'], 'golden_periods': 'Personal Year 9 — completion + transformation + new cycle. Mars mahadasha (7 years) is intense but life-defining. Mid-March to mid-May (Mars exalted in Capricorn) is your yearly window. Tuesday Brahma muhurat (4-6 AM) for biggest decisions.'}, 5: {'title': "The Communicator — Mercury's Quicksilver", 'tagline': 'You are a master at connecting deals, ideas, and people.', 'life_essence': ["Number 5 is ruled by Mercury. You are 'mobile' and quick. Your brain is active 24/7 — people get exhausted talking to you because you can handle 5 topics simultaneously. This natural multitasking is your greatest asset.", 'You are a born networker — you remember 100 names, 100 phone numbers, 100 contexts. Sales, marketing, deals — they are in your blood. You can extract opportunity from a single conversation.', "Mercury's warning: the risk of becoming 'shallow'. Being so versatile means you do not go deep anywhere. You only skim the surface. To become a master, you need to dedicate 10,000 hours to one field — for Number 5, building this discipline is the hardest, but most essential."], 'career_pattern': ['Best fields: business (especially trade/commerce), sales, marketing, journalism, media, IT, accounting, transport, communication tech, agency work, real estate broking, share market, language teaching. Anything with variety + people + money conversion.', 'Common mistake: Job hopping and business hopping. You get bored in 2 years. Solution: choose an umbrella business (e.g., consulting), create variety within it — same field, new clients/projects.', 'Growth timing: Earliest of all numbers — commercial sense comes by 22-25. 28-32 is the first big money. 35-40 is stabilization. Wednesday is your power day. You are sharpest at sunrise.'], 'love_pattern': ['In love, you are fun and intellectually stimulating — but you avoid emotional depth. You are apprehensive of heavy conversations.', "Breakup reason: Your partner feels you are 'half-present' — phone, work, friendships are all running parallel. Solution: implement a 'phone-free 1 hour daily' rule in the relationship — it's a game-changer.", 'Ideal partner: Numbers 1, 3, 6, or 9 — intellectual peers. Number 2 + 5 is messy (too much movement for the moon).'], 'money_pattern': 'Money comes to you through multiple streams — this is the natural pattern. A single salary will trap you. A side-hustle is MANDATORY for Number 5. Shares, mutual funds, intra-day trading are favorable for you. Green items, emerald (after consultation), copper are your storage.', 'health_pattern': 'Nervous system, skin, hands, lungs, IBS/digestion — fall under Mercury. Anxiety attacks are common for Number 5. Daily 10 minutes of Pranayama — magical effect. Do not multitask while eating.', 'spiritual_path': "Your dharma is 'exchange of ideas'. Vishnu sadhana, Hanuman Chalisa (Mercury-friendly), Saraswati. Wednesday green moong donation. Mind-yoga (Trataka, Vipassana) is game-changing.", 'strengths': ['Multi-tasking — 5 things at once', 'Networking — instant rapport', 'Adaptability — fit in any crowd', 'Negotiation — art of closing deals', 'Speed — fast learner, fast executor'], 'challenges': ['Shallow mastery — no depth anywhere', 'Anxiety, restlessness, sleeplessness', 'Commitment phobia (relationships and projects)', 'Hurting with sarcasm', "Over-commitment — you say 'yes' so much that you cannot deliver"], 'risk_alerts': ['High risk of loss in intra-day share market — strict stop-loss', 'Peace lost to anxiety — do not skip meditation', 'Whatsapp/Insta addiction — 30% productivity loss', 'Temptation of multiple relationships — set boundaries', 'Wednesday fast for 21 weeks — mind stability multiplied'], 'golden_periods': "Personal Year 5 is obviously — the entire year is full of breakthrough opportunities. Mercury's Mahadasha (17 years) is golden. May-June is the yearly power window (Mercury exalted in Virgo). Wednesday + sunrise is your manifestation peak."}, 4: {'title': "The Disruptor — Rahu's Modern Visionary", 'tagline': 'You are destined to break rules and create new ones.', 'life_essence': ["Number 4 is ruled by Rahu — modern, unconventional, electric. You get irritated by tradition — 'why must it be done this way?' is your favorite question. In childhood, your parents might have called you 'stubborn', but the truth is you are not stubborn — you are original. You are an original soul in a copy-paste world.", 'Your life is not linear — sudden jumps, sudden falls, sudden recoveries. You cannot sustain a boring stable career. Tech, innovation, foreign lands, non-traditional paths — this is your energy.', "Rahu's warning: 'illusion'. Sometimes you get trapped in shortcuts — 'quick money', 'easy success'. This is always a trap. Only 'long, patient, ethical work' yields good results with Rahu. Shortcut = self-destruction."], 'career_pattern': ['Best fields: technology, software, AI/data, foreign trade, aviation, electrical engineering, photography/cinema, social media, crypto/fintech, immigration consulting, NGO work, anything cutting-edge. A government job will bore you.', "Common mistake: You change jobs every 2-3 years — you need 'something new'. Result: no deep mastery in any field. Solution: choose one industry and give it 7+ years — then your Rahu-magic will work.", "Growth timing: Erratic — sudden jumps at 26-28, 33-35, 41-44. When Rahu's mahadasha (18 years) comes, life is redefined. Saturday is your power day (Rahu is Saturn's secret partner)."], 'love_pattern': ["In love, you are unpredictable — sometimes obsessive, sometimes cold. Your partner cannot understand what happened. You do not do this intentionally — it is Rahu's energy.", 'Breakup reason: Boredom. A routine relationship suffocates you. You crave thrill, novelty, mystery. Solution: force-create new experiences with your partner — travel, hobbies, surprises.', "Ideal partner: Numbers 1, 5, or 7 — those who respect independence. Number 2 + 4 is a mismatch (moon-rahu antithetical). Inter-caste/inter-cultural marriage is Rahu's signature."], 'money_pattern': 'Money comes to you in waves — sometimes a flood, sometimes zero. In investments, speculation, crypto, foreign equity seem attractive — but Rahu tricks here. 70% safe (FD/index fund), 30% speculative — this is the formula. Foreign currency, electronics, blue items are your lucky storage.', 'health_pattern': "Skin, nervous system, addictions, anxiety, snake-related fears — under Rahu. Meditation and digital detox are a MUST. Sleep 1 hour before using a smartphone — Rahu's direct organ is the phone.", 'spiritual_path': "Your dharma is 'breaking outdated structures'. Saraswati worship, Durga sadhana, Shiv-tandav stotra — Rahu-friendly. Donate black sesame seeds on Saturday, donate blankets in cold weather.", 'strengths': ['Original thinking — unconventional solutions', 'Tech savvy — naturally adopt new tools', 'Foreign affinity — opportunities abroad', 'Crisis innovation — creative in emergencies', 'Networking — build a diverse circle'], 'challenges': ['Restlessness — do not commit long-term', 'Addictions risk (substance, screen, gambling)', 'Sudden anger flares', 'Relationship instability', "Getting trapped in 'get-rich-quick' schemes"], 'risk_alerts': ['Do NOT keep >30% of your portfolio in crypto/speculative investments', 'Karmic risk of snake/insect bites — first-aid knowledge is essential', 'Strict documentation for foreign travel — Rahu loves to lose passports', 'Mahadasha-shift between 28-30 or 41-44, life redefined — seek guidance', 'Stress-eating or night-time scrolling addiction — will drain health'], 'golden_periods': "When Rahu's mahadasha (18 years) activates — it's a game-changer. Personal Year 1, 4, 7 — rapid progress in innovation. February-March (Rahu in Aquarius favored) yearly window. Plan strategy on Saturday night — Rahu is at its peak."}})

_NARRATIVES_HI.update({6: {'title': 'प्रेमी — शुक्र का सौंदर्य लाने वाला', 'tagline': 'आप प्यार, कला और सौंदर्य के अवतार हो।', 'life_essence': ['नंबर 6 का स्वामी शुक्र है। आप इस दुनिया को सुंदर बनाने के लिए आए हो। आपको अजीब या गंदी चीजें बर्दाश्त नहीं होतीं — कपड़े, घर, बातचीत, खाना — सब कुछ सुरुचिपूर्ण चाहिए।', 'आप स्वाभाविक रूप से परिवार-प्रेमी हैं। रिश्तों में आप गोंद की तरह हैं। माँ, बहन, पत्नी, दोस्त — आप उनके साथ समय निवेश करते हैं जैसा कोई नहीं करता। यह आपकी सबसे बड़ी खुशी और सबसे बड़ी ऊर्जा की निकासी दोनों है।', "शुक्र की चेतावनी: 'अति-लगाव'। आप किसी से इतना प्यार करने लगते हैं कि खुद को भूल जाते हैं। आत्म-प्रेम सीखना 6 वालों के लिए जीवनभर का सबक है। खुद के लिए समय निवेश कभी 'स्वार्थी' नहीं होता — यह वास्तव में रिश्ते के लिए स्थायी है।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: कला (संगीत, नृत्य, चित्रकला), फैशन, सौंदर्य/कॉस्मेटिक्स, मनोरंजन उद्योग, आतिथ्य, लक्जरी वस्त्र, आभूषण, इंटीरियर डिजाइन, शादी की योजना, होटल/रेस्तरां, इत्र, फोटोग्राफी, वाहन/कार उद्योग। जहां भी सौंदर्य व्यवसाय से मिलता है।', "सामान्य गलती: पारिवारिक जिम्मेदारी के चक्कर में आप अपने सपनों से समझौता कर लेते हैं। 40 साल के बाद पछतावा होता है। समाधान: परिवार और व्यक्तिगत विकास — 'या' नहीं रखना।", 'विकास का समय: 25-30 पहला चरण (अक्सर विवाह/साझेदारी के माध्यम से), 32-38 आय का शिखर, 45-52 लक्जरी चरण। शुक्रवार आपका शक्ति दिन है — बड़ा लॉन्च शुक्रवार को।'], 'love_pattern': ['प्रेम में आप राजा/रानी हैं — रोमांस, उपहार, आश्चर्य, मोमबत्ती डिनर — सब कुछ आपको स्वाभाविक रूप से आता है। आपका साथी आपसे बिगड़ जाता है।', 'ब्रेकअप का कारण: आप बहुत देते हैं, फिर समान वापसी की उम्मीद करते हैं — जब नहीं मिलता तो चुपचाप नाराजगी बनती है। जरूरतों का संचार जरूरी है।', 'आदर्श साथी: नंबर 3, 6, 9 — ज्ञान + सौंदर्य का मेल। नंबर 7 + 6 दिलचस्प है (केतु का अलगाव बनाम शुक्र का लगाव) — विकास-पथ पर साथ।'], 'money_pattern': 'पैसा आपके पास रिश्तों, सौंदर्य, या लक्जरी के माध्यम से आता है। आप लक्जरी पर अधिक खर्च करते हैं — यह आनुवंशिक है, लड़ाई मत करें। बस आय > खर्च का सख्त अनुपात रखें। हीरा, सफेद सोना, रेशम, इत्र — आपके भाग्यशाली संपत्ति।', 'health_pattern': 'प्रजनन अंग, गुर्दे, गला, त्वचा की चमक — शुक्र के अधीन। आपकी त्वचा की स्थिति आपकी भावनात्मक स्थिति बताती है — रिश्ते का तनाव = त्वचा की समस्याएं। मिठाई + घी संतुलन में लें।', 'spiritual_path': "आपका धर्म 'सौंदर्य के माध्यम से प्रेम' है। लक्ष्मी साधना, देवी पूजा, कृष्ण भक्ति आपको सूट करती है। शुक्रवार को सफेद वस्त्र दान करें। भक्ति-योग आपका मार्ग है (ज्ञान-योग नहीं)।", 'strengths': ['सौंदर्यबोध — आप सब कुछ सुंदर बनाते हैं', 'रिश्तों का रखरखाव — लंबे दोस्ती', 'कूटनीति — आप शांति बनाते हैं', 'उदारता — खुले दिल से देने वाले', 'आकर्षण — पहली मुलाकात में छाप छोड़ देते हैं'], 'challenges': ['लक्जरी पर अधिक खर्च', 'पारिवारिक उलझाव — सीमाएं कमजोर', 'संघर्ष से बचना', 'वैनिटी (दिखावे के प्रति आसक्त)', 'आराम क्षेत्र में फंसे — आराम पसंद'], 'risk_alerts': ['लक्जरी खर्च आय का 40% से अधिक → वित्तीय जाल', 'वाहन दुर्घटनाएं 26-28 के बीच संभव — सावधानी से चलाएं', 'विषाक्त रिश्ते में 7+ साल फंसे — परामर्श लें', 'महिलाओं के लिए प्रजनन स्वास्थ्य 28-32 ध्यान', 'शुक्रवार व्रत या सफेद दान 16 सप्ताह — शुक्र का आशीर्वाद'], 'golden_periods': "व्यक्तिगत वर्ष 6 — रिश्ते + परिवार + सौंदर्य सभी शिखर पर। शुक्र महादशा (20 साल) क्लासिक 'सुख' चरण है। अप्रैल-मई में मीन में शुक्र उच्च — रचनात्मकता शिखर। शुक्रवार सूर्योदय में कला/सौंदर्य/रिश्ते का काम।"}, 7: {'title': 'रहस्यवादी — केतु का आध्यात्मिक शोधकर्ता', 'tagline': 'आप इस दुनिया में दिखते हुए भी नहीं दिख पाते।', 'life_essence': ['नंबर 7 का स्वामी केतु है — मोक्ष कारक। आप एक रहस्य हैं — यहां तक कि खुद के लिए भी। आप कभी भी भौतिक दुनिया में 100% लीन नहीं हो पाते, अंदर से कुछ और खोज रहे होते हैं — अर्थ, सत्य, गहराई।', "बचपन से ही आपको अकेलापन अच्छा लगता होगा। भीड़ में भी आप 'अपने साथ' रहते हैं। यह अलगाव आपकी कमजोरी नहीं है — यह आपकी शोध प्रयोगशाला है। सबसे बड़ी खोजें 7 वालों ने की हैं (आइंस्टीन, टेस्ला, जे.के. रोलिंग — सभी 7 के हैं)।", "केतु की चेतावनी: 'अलगाव में बहुत दूर चले जाना'। आप रिश्तों, जिम्मेदारियों, समाज से इतने अलग हो जाते हैं कि कार्य करना मुश्किल हो जाता है। आधार नियम: रोज 1 घंटा 'व्यावहारिक दुनिया' में बिताएं — बिल, परिवार, स्वास्थ्य।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: शोध, विज्ञान, दर्शन, लेखन, आध्यात्मिकता/योग, जांच/फोरेंसिक्स, गूढ़ विद्या, फोटोग्राफी, जल से संबंधित कार्य (समुद्री, आयात-निर्यात), मनोविज्ञान, पुरातत्व, आईटी अनुसंधान और विकास, वैकल्पिक चिकित्सा। आप एकल पेशेवर भूमिकाओं में चमकते हैं।', "सामान्य गलती: मुख्यधारा की सफलता को 'उथला' समझकर नजरअंदाज कर देते हैं — फिर 35 साल में महसूस होता है कि पैसा तो चाहिए ही। समाधान: आध्यात्मिक और व्यावहारिक — दोनों सह-अस्तित्व में हो सकते हैं। पैसा भी ऊर्जा है, इसे अस्वीकार न करें।", 'विकास का समय: देर से खिलने वाले — वास्तविक पहचान 35-45 के बीच आती है। केतु की महादशा (7 साल) जीवन को उल्टा कर देती है (अच्छा या बुरा)। मंगलवार/शनिवार आपके शक्ति दिन हैं (केतु के संबंध)।'], 'love_pattern': ["प्रेम में आप दूर रहते हैं — अपने साथी को 'पूरी तरह से पहुंचने' नहीं देते। आपका एक हिस्सा हमेशा अकेला रहता है। यह आपके साथी के लिए निराशाजनक है।", "ब्रेकअप का कारण: 'मुझे नहीं पता कि आप क्या चाहते हैं' — यह आपके साथी की सामान्य शिकायत होती है। आप खुद भी नहीं जानते। समाधान: जर्नलिंग करें — खुद को खोजें, फिर अपने साथी को बता सकेंगे।", 'आदर्श साथी: नंबर 4, 7, 1 — वे स्वतंत्रता का सम्मान करते हैं। विवाह देर से हो सकता है (28-30 के बाद) — इसे स्वीकार करें, जल्दबाजी न करें।'], 'money_pattern': 'पैसा आपके पास ज्ञान के माध्यम से आता है — शोध, लेखन, परामर्श, चिकित्सा। आप भौतिक कम, बौद्धिक अधिक होते हैं — यह वित्तीय योजना को चुनौतीपूर्ण बनाता है। ऑटो-निवेश एसआईपी आपके लिए जीवन-रक्षक है। केतु धातु — बहुरंगी (सलाह के बाद कैट्स आई)।', 'health_pattern': 'तंत्रिका तंत्र, रहस्यमय त्वचा समस्याएं, प्रतिरक्षा, गैस/पाचन, आंखें — केतु के अंतर्गत आते हैं। आपको अनियमित अस्पष्ट बीमारियां होती हैं। प्राकृतिक चिकित्सा + आयुर्वेद + ध्यान आपके लिए पारंपरिक चिकित्सा से बेहतर हैं।', 'spiritual_path': "आपका धर्म 'आंतरिक सत्य की खोज' है। गणेश (केतु के पुत्र), हनुमान, शिव, काली से संबंधित साधनाएं — सभी आपके लिए काम करती हैं। 10-दिन का विपश्यना कोर्स आपके जीवन को बदल देगा।", 'strengths': ['गहन शोध क्षमता', 'अंतर्ज्ञान — अलौकिक संवेदन', 'स्वयं-निर्भर', 'अलग निर्णय — पूर्वाग्रह-मुक्त', 'रहस्यमय अनुभव स्वाभाविक रूप से आते हैं'], 'challenges': ['अकेलेपन में अवसाद का जोखिम', 'व्यावहारिक दुनिया में संघर्ष (बिल, समय-निर्धारण)', 'रिश्ते की अंतरंगता मुश्किल', 'देर से विवाह / बिना विवाह की प्रवृत्ति', 'पारंपरिक समाज में असंगति'], 'risk_alerts': ['ड्रग्स / शराब के माध्यम से पलायन का जोखिम — संयमित रहना अनिवार्य है', '28-32 के बीच अचानक अस्पष्ट बीमारियां — आयुर्वेदिक जांच करवाएं', 'अकेलापन अवसाद में जा सकता है — चिकित्सक से बात करें', 'भौतिक निर्णयों को आवेग में अस्वीकार करना — वित्तीय गुरु से सलाह लें', 'मंगलवार को हनुमान चालीसा 11 बार पढ़ें — केतु की शांति और सुरक्षा के लिए'], 'golden_periods': 'व्यक्तिगत वर्ष 7 — आध्यात्मिक और शोध में प्रगति। केतु महादशा (7 साल) परिवर्तनकारी है। देर से शरद ऋतु (अक्टूबर-नवंबर) वार्षिक ध्यान और अंतर्दृष्टि का चरम है। साल में एक बार एकल रिट्रीट अनिवार्य है।'}, 2: {'title': 'The Diplomat — चंद्र-आशीर्वादित कनेक्टर', 'tagline': 'आप इस दुनिया के अनसुने हीलर्स हो।', 'life_essence': ['नंबर 2 का स्वामी चंद्र है — और चंद्र की ऊर्जा तरल और परावर्तक है। किसी के साथ 5 मिनट बैठें और आप उनकी बॉडी लैंग्वेज को उठाकर नकल कर सकते हैं। यह सहानुभूति आपकी सबसे बड़ी उपहार है और सबसे बड़ा बोझ भी।', "आप अकेले लोगों को आकर्षित करते हैं — भावनात्मक, टूटे हुए, या भ्रमित लोग आपके साथ 'सुरक्षित' महसूस करते हैं। यह कोई दुर्घटना नहीं है। आप प्राकृतिक काउंसलर हैं। लेकिन इसकी कीमत यह है कि आप अक्सर अपनी भावनात्मक जरूरतों को नजरअंदाज कर देते हैं।", "चंद्र का सबसे महत्वपूर्ण सबक है — 'चरण'। हर 28 दिन में आप एक पूरी भावनात्मक चक्र से गुजरते हैं — एक सप्ताह उच्च, एक सप्ताह मध्यम, एक सप्ताह निम्न, एक सप्ताह पुनर्प्राप्ति। इस चक्र से लड़ें नहीं — इसके साथ बहना सीखें।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: काउंसलिंग, एचआर, नर्सिंग, आतिथ्य, खाद्य/डेयरी व्यवसाय, लेखन (विशेष रूप से कथा/कविता), मनोविज्ञान, सामाजिक कार्य, नौसेना, समुद्री कार्य, आंतरिक डिजाइन। आप सार्वजनिक-सामना करने वाले भावनात्मक भूमिकाओं में चमकते हैं।', 'सामान्य गलती: आक्रामक बिक्री या प्रतिस्पर्धी कॉर्पोरेट नौकरियों में आप थक जाते हैं। 4-5 साल में बर्नआउट होता है। दीर्घकालिक कार्य जिसमें भावनात्मक पुरस्कार होते हैं, वही आपको टिकता है।', 'विकास समय: धीमी जलन — आपका शिखर 32-38 के बीच आता है (इससे पहले नहीं)। तब तक, आधार कार्य। सोमवार आपका शक्ति दिन है — प्रमुख भावनात्मक निर्णय सोमवार सुबह लें।'], 'love_pattern': ['प्रेम में, आप देते ही रहते हैं। आपके साथी की जरूरतें आपकी जरूरतों से पहले आती हैं। यह सुंदर है लेकिन अस्थिर है।', "ब्रेकअप का सामान्य कारण: आप अपनी भावनाओं को व्यक्त नहीं करते, आप उन्हें आंतरिक करते हैं — और एक दिन अचानक 'मैं कर चुका हूँ' कहते हैं। साथी चौंक जाता है क्योंकि वे संकेत चूक गए। सबक: छोटी बात भी बोलें।", 'आदर्श साथी: नंबर 1, 4, या 8 — वे वह संरचना प्रदान करते हैं जो चंद्र को चाहिए। नंबर 5 + 2 अशांत है (बुध चंद्र को बहुत अधिक हिलाता है)।'], 'money_pattern': 'पैसा आपके पास ज्वार की तरह आता-जाता रहता है। बचत की आदत को जबरदस्ती विकसित करें — स्वचालित एसआईपी सबसे अच्छा है। चांदी, मोती, सफेद वस्तुओं में निवेश करें। 6 महीने के लिए एक तरल आपातकालीन कोष रखें — चंद्र को सुरक्षित महसूस करने की आवश्यकता है।', 'health_pattern': 'पेट, स्तन (महिलाएं), फेफड़े, नींद चक्र — चंद्र के अंतर्गत। देर रात से बचें। पूर्णिमा पर डिटॉक्स पानी पीकर जल्दी सोएं — शरीर में सूजन कम होगी।', 'spiritual_path': "आपका धर्म है 'दूसरों की भावनात्मक शुद्धि'। माता पूजा, देवी पूजा, लक्ष्मी साधना — सभी चंद्र-अनुकूल हैं। सोमवार व्रत 16 सप्ताह करें — परिवर्तनकारी।", 'strengths': ['सहानुभूति — आप लोगों के अंदर देख सकते हैं', 'कूटनीति — आपको संघर्ष को हल करना आता है', 'अनुकूलनशीलता — आप हर स्थिति में ढल जाते हैं', 'सौंदर्यबोध — सुंदरता की गहरी समझ', 'धैर्य — लंबी दौड़ में जीत आपकी है'], 'challenges': ['मूड स्विंग्स — 28-दिन का चक्र प्रबंधित करना कठिन है', 'अधिक देने से नाराजगी होती है', 'संघर्ष से बचना', 'महत्वपूर्ण क्षणों में अनिर्णय', 'भावनात्मक भोजन या भावनात्मक खर्च'], 'risk_alerts': ['अपनी माँ या महिला बुजुर्ग के स्वास्थ्य पर ध्यान दें — कर्मिक संबंध गहरा है', 'पानी से संबंधित यात्रा में अतिरिक्त सावधानी बरतें — आपके जीवन पथ पर पानी प्रतीकात्मक है', 'आप विषाक्त मित्रताओं में 5+ वर्षों तक फंसे रह सकते हैं — वार्षिक संबंध ऑडिट करें', 'अवसाद में जाने की प्रवृत्ति — एक सहानुभूति रखने वाला काउंसलर खोजें', 'देर रात के निर्णय कभी न लें — चंद्र रात में कमजोर होता है'], 'golden_periods': 'व्यक्तिगत वर्ष 2, 4, 6, या 8 में आपकी जीवन unfolds होती है। पूर्णिमा के 3 दिन पहले और बाद में आपकी अभिव्यक्ति शक्ति चरम पर होती है — उस विंडो में महत्वपूर्ण इच्छाएं या इरादे सेट करें। अक्टूबर-नवंबर आपकी वार्षिक सौम्य शक्ति विंडो है (वृषभ में चंद्र उच्च है)।'}, 3: {'title': 'ऋषि — बृहस्पति का ज्ञान वाहक', 'tagline': 'आप ज्ञान को धन में परिवर्तित करने वाले हो।', 'life_essence': ["नंबर 3 का स्वामी बृहस्पति (जुपिटर) है — गुरु ग्रह। आप जन्म से ही पुरानी आत्मा हो। बचपन में लोगों ने कहा होगा 'तू अपनी उम्र से ज्यादा परिपक्व है'। यह कोई दुर्घटना नहीं है — आपकी आत्मा कई जन्मों से ज्ञान के साथ आई है।", "आपको सिखाना, साझा करना, और विस्तार करना आता है। जब कोई आपके सामने भ्रमित होता है, तो आप स्वाभाविक रूप से दार्शनिक बन जाते हो — 'इसे ऐसे देखो' वाला फ्रेमिंग आप अनजाने में देते हो। यह आपका स्वधर्म है।", "बृहस्पति की एक चेतावनी है — 'अति-विस्तार'। कभी-कभी आप इतना जानते हो कि कुछ भी आत्मविश्वास से बोल देते हो — बिना गहराई से सत्यापित किए। यह अहंकार का अंतराल आपको बड़ा नुकसान करा सकता है। विनम्रता + ज्ञान = आपका स्वर्णिम संयोजन।"], 'career_pattern': ["सर्वश्रेष्ठ क्षेत्र: शिक्षण, कानून, वित्त/बैंकिंग, प्रकाशन, धर्म/आध्यात्मिकता, पत्रकारिता, अनुसंधान, न्यायपालिका, सलाहकार भूमिकाएँ, सामग्री निर्माण, दर्शन, उद्यम पूंजी। जहां 'ज्ञान = धन' का समीकरण चलता है।", 'सामान्य गलती: व्यावहारिक निष्पादन की ओर लापरवाही — केवल सलाह देने में खुश रहते हो, खुद करना कम होता है। परिणाम: लोग आपसे सीखकर आगे निकल जाते हैं, आप वहीं के वहीं। समाधान: एक-दो परियोजनाएँ खुद पूरी तरह से निष्पादित करें, सिद्धांत + अभ्यास दोनों।', 'विकास का समय: 24-27 पहला ज्ञान चरण, 33-36 शिखर शिक्षण चरण, 45-50 विरासत + धन चरण। गुरुवार आपका शक्ति दिन है। बृहस्पति होरा में शुरू किया काम फलता है।'], 'love_pattern': ["प्रेम में आप गुरु बन जाते हो — साथी को 'मार्गदर्शन' करते हो। यह शुरू में आकर्षक है, पर लंबे समय में साथी घुटन महसूस करता है (कौन साथी के रूप में माता-पिता चाहता है?).", "ब्रेकअप का कारण: 'मैंने तुम्हें पीछे छोड़ दिया' वाली भावना। आपकी वृद्धि तेज होती है, साथी पीछे रह जाता है। समाधान: साथी को भी बढ़ने का स्थान दें, केवल आप ही नहीं।", 'आदर्श साथी: नंबर 6, 9, या 3 — वही ज्ञान-तरंग पर। नंबर 5 + 3 बौद्धिक रूप से शानदार लेकिन भावनात्मक रूप से अशांत।'], 'money_pattern': 'पैसा आपके पास ज्ञान के माध्यम से आता है — शिक्षण, सलाह, लेखन, परामर्श। आप प्राकृतिक गुरु हो — कोचिंग/शिक्षण का एक आय स्रोत अवश्य बनाएं, भले ही यह साइड में हो। पीले रत्न (पीला नीलम) बृहस्पति को मजबूत करते हैं — लेकिन केवल ज्योतिषी की पुष्टि के बाद।', 'health_pattern': 'जिगर, वसा चयापचय, कूल्हे, कान, तंत्रिका तंत्र — बृहस्पति के अंतर्गत। मिठाई का अधिक सेवन न करें (बृहस्पति + चीनी = खतरनाक)। पीले खाद्य पदार्थ (हल्दी, केला, घी) नियमित रूप से लें।', 'spiritual_path': "आपका धर्म 'ज्ञान-दान' है। गुरु पूजा, बृहस्पति मंत्र, साईं बाबा भक्ति आपके लिए उपयुक्त होगी। प्रतिदिन 5 मिनट के लिए ग्रंथ पढ़ने की आदत बनाएं — घातीय ज्ञान।", 'strengths': ['उम्र से परे ज्ञान', 'शिक्षण/समझाने की स्पष्टता', 'आशावाद — स्वाभाविक रूप से सकारात्मक', 'उदारता — आप खींचकर देते हो', 'दीर्घकालिक रणनीतिक सोच'], 'challenges': ['अति आत्मविश्वास में गलत सलाह दे देते हो', 'निष्पादन में कमजोरी — केवल योजना बनाते रहो', '30 के बाद वजन बढ़ना — बृहस्पति का विस्तार वास्तविक है', 'उपदेश देना — लोग अनचाही सलाह से थक जाते हैं', 'बच्चों/छात्रों के साथ अत्यधिक जुड़ाव'], 'risk_alerts': ['35 के बाद जिगर स्वास्थ्य पर सख्त नजर — शराब और तले भोजन को सीमित करें', 'वित्तीय सलाहकार बनने की प्रवृत्ति — व्यक्तिगत वित्तीय नुकसान', 'धार्मिक पंथों में फंसने का जोखिम — विवेक बनाए रखें', 'बच्चों/शिष्यों की असफलता आपको व्यक्तिगत रूप से प्रभावित करती है — अलगाव सीखें', 'गुरुवार का व्रत या पीली चीजों का दान करना — बृहस्पति को मजबूत रखें'], 'golden_periods': 'व्यक्तिगत वर्ष 3, 6, 9 — ज्ञान से कमाई। गुरु-गोचर (बृहस्पति पारगमन) के 12 साल के चक्र में 1, 5, 9 राशि पर सबसे मजबूत। प्रतिदिन 7-9 बजे बृहस्पति होरा में लिखना/शिक्षण करना — विशेष रूप से आशीर्वादित।'}, 8: {'title': 'निर्माता — शनि का कर्मिक चुम्बक', 'tagline': 'आप संघर्ष से हीरा बनने वाले हो।', 'life_essence': ['अंक 8 का स्वामी शनि है। आपकी जिंदगी में कुछ भी मुफ्त में नहीं मिलता — हर चीज के लिए आपने पसीना बहाया है, या बहाना पड़ेगा। यह अन्याय नहीं है — यह आपकी आत्मा का चुना हुआ मार्ग है। आप कर्मयोगी हो।', "बचपन से आपको 'गंभीर' कहा गया होगा — क्योंकि आप वास्तव में गंभीर हैं। खेल-कूद में भी आपको रणनीति दिखती है। यह गुण आपको लंबे समय में बहुत बड़ा बनाता है — पर छोटी उम्र में बहुत अकेलापन देता है।", "शनि का सबसे महत्वपूर्ण सबक: 'धैर्य'। 8 वालों की वास्तविक सफलता 35 के बाद शुरू होती है। पहले शनि आपको 'पानी में डुबो डुबो के' तैयार करता है। इस प्रक्रिया से लड़ाई मत करो। अनुशासन और धैर्य ही 8 की मास्टर कुंजी है।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: रियल एस्टेट, खनन, तेल, भारी उद्योग, सरकारी नौकरी, न्यायपालिका, इंजीनियरिंग, बुनियादी ढांचा, बैंकिंग, बीमा, सामाजिक न्याय कार्य, पुरानी बीमारी का उपचार, अंत्येष्टि, पुरातत्व, प्राचीन वस्तुएं। धीमा + संरचित + दीर्घकालिक — यही 8 का क्षेत्र है।', 'सामान्य गलती: त्वरित सफलता चाहना — फिर निराशा, फिर शॉर्टकट, फिर पतन। 8 वालों को शॉर्टकट बहुत महंगा पड़ता है। समाधान: हर लक्ष्य के लिए 10-वर्षीय योजना बनाएं। शनि 10-वर्षीय चक्र में काम करता है।', 'विकास का समय: 36-42 पहला बड़ा शिखर (शनि की वापसी), 48-55 धन का क्रिस्टलीकरण, 58-65 विरासत। शनिवार आपका शक्ति दिन है। देर शाम (शनि होरा) निर्णय।'], 'love_pattern': ['प्रेम में आप वफादार और प्रतिबद्ध होते हैं — जब तक प्रतिबद्ध नहीं होते तब तक सतर्क रहते हैं, लेकिन एक बार प्रतिबद्ध हो गए तो हमेशा के लिए। यह गुण कीमती है लेकिन साथी को शुरू में समझ नहीं आता।', "ब्रेकअप का कारण: ठंडापन — आप भावना नहीं दिखाते, साथी को लगता है 'आप मुझसे प्यार नहीं करते'। समाधान: केवल क्रियाओं से नहीं, शब्दों से भी प्यार व्यक्त करें — असुविधाजनक लेकिन आवश्यक।", 'आदर्श साथी: अंक 4, 8, 6 — अनुशासन + गर्मजोशी का संतुलन। देर से विवाह (30 के बाद) बेहतर है। जल्दबाजी में विवाह = जीवनभर का पछतावा।'], 'money_pattern': 'पैसा आपके पास धीरे-धीरे + स्थिरता से आता है। 25-35 का चरण आमतौर पर संघर्ष का होता है, 35-50 में धन का क्रिस्टलीकरण होता है। रियल एस्टेट, स्थिर संपत्तियां, धीमी चक्रवृद्धि निवेश आपके लिए उपयुक्त हैं। काले/गहरे नीले आइटम, लोहा, नीला नीलम (सलाह के बाद) शनि को मजबूत करते हैं।', 'health_pattern': 'हड्डियां, जोड़, घुटने, दांत, पुरानी स्थितियां, अवसाद — शनि के अंतर्गत। दैनिक व्यायाम (विशेष रूप से चलना) में अनुशासन अनिवार्य है। तिल का तेल, उड़द दाल, आयरन युक्त खाद्य पदार्थ। शनिवार का उपवास (केवल फल) बहुत हीलिंग है।', 'spiritual_path': "आपका धर्म 'वंचितों की सेवा के माध्यम से कर्मयोग' है। शनि साधना, हनुमान, भैरव। शनिवार को काले तिल का दान, ठंड के मौसम में कंबल का दान। शौचालय की सफाई/अनाथालय सेवा — शनि का सीधा शमन।", 'strengths': ['अनुशासन — सख्ती से अनुसरण करें', 'धैर्य — दीर्घकालिक संघर्षों को संभालें', 'रणनीतिक दिमाग — शतरंज खिलाड़ी की तरह', 'वफादारी — एक बार प्रतिबद्ध, हमेशा के लिए', 'न्याय-उन्मुखता — निष्पक्षता महत्वपूर्ण है'], 'challenges': ['भावनात्मक ठंडापन की धारणा', "निराशावाद — 'कुछ भी अच्छा नहीं होगा' मानसिकता", 'धीमी प्रगति (युवावस्था में निराशाजनक)', 'काम की लत — आनंद भूल जाते हैं', 'पिता/बॉस के साथ अधिकार मुद्दे'], 'risk_alerts': ['पिता-तुल्य व्यक्ति के साथ संघर्ष या दूरी — बचपन का पैटर्न', 'हड्डी/जोड़ की चोट 30-32 के बीच संभव — योग अनिवार्य है', 'अवसाद का जोखिम 28-30 (शनि की वापसी) — चिकित्सा लें', 'काम की लत में परिवार की उपेक्षा — परिवार के समय का कार्यक्रम बनाएं', 'शनिवार को काले तिल + सरसों तेल का दान 21 सप्ताह — शनि का संतुलन'], 'golden_periods': 'व्यक्तिगत वर्ष 8 — धन + मान्यता + शक्ति सभी शिखर पर। शनि महादशा (19 वर्ष) — प्रारंभिक परीक्षा, फिर समृद्ध पुरस्कार। दिसंबर-जनवरी वार्षिक शनि शिखर। 36-42 का पूरा चरण आपका लॉन्चपैड है — कुछ भी शुरू करें।'}, 9: {'title': 'योद्धा — मंगल का सत्य का सिपाही', 'tagline': 'आप अपनी पैशन के लिए लड़ने वाले हो।', 'life_essence': ['नंबर 9 का स्वामी मंगल है। आप ऊर्जा का ज्वालामुखी हो — अंदर से अग्नि जलती रहती है। यह अग्नि आपकी सबसे बड़ी शक्ति और सबसे बड़ा खतरा दोनों है। नियंत्रित = आप पहाड़ों को हिला देंगे। अनियंत्रित = आप खुद को जला लेंगे।', "बचपन से आपको 'गुस्सेवाला' कहा गया होगा। यह सिर्फ सतह है। आपकी असली अग्नि है — पैशन, साहस, ड्राइव। जब आपको किसी कारण से प्यार हो जाता है, आप उस कारण के लिए अकेले भी लड़ सकते हो।", "मंगल का सबसे महत्वपूर्ण सबक: 'अपनी शक्ति का उपयोग कहाँ करना है और कहाँ रोकना है'। आपकी ऊर्जा असीमित नहीं है — इसे रणनीतिक रूप से उपयोग करें, भावनात्मक रूप से नहीं। दैनिक 60 मिनट का शारीरिक व्यायाम आपके लिए थेरेपी है, विलासिता नहीं।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: सेना, पुलिस, खेल, सर्जरी (विशेष रूप से ट्रॉमा), रियल एस्टेट, निर्माण, इंजीनियरिंग (मैकेनिकल/सिविल), अग्निशमन, सुरक्षा, खनन, कसाई, फार्मा, खेल प्रबंधन, फिटनेस प्रशिक्षण, प्रेरक भाषण। जहाँ कहीं भी शारीरिक/भावनात्मक साहस की आवश्यकता होती है।', "सामान्य गलती: बॉस/प्राधिकरण के साथ टकराव। आप 'अन्याय' सहन नहीं करते — आप पंच या छोड़ देते हैं। समाधान: 30 के बाद स्वरोजगार/अपना व्यवसाय सबसे अच्छा है — मंगल कर्मचारी मोड में घुटता है।", 'विकास समय: प्रारंभिक शिखर (24-28 पहली लहर), 32-36 स्थिरीकरण, 42-48 विरासत चरण। मंगलवार आपका शक्ति दिवस है। सूर्योदय का समय जब आप सबसे शक्तिशाली होते हैं।'], 'love_pattern': ['प्यार में आप तीव्र, अधिकारपूर्ण, पैशनेट होते हैं। अक्सर अफेयर-शैली रोमांस से शुरू होता है। ईर्ष्या का प्रबंधन एक बड़ा जीवनभर का प्रोजेक्ट है।', 'ब्रेकअप का कारण: गुस्से का विस्फोट — आप कुछ ऐसा कह देते हैं जो पूर्ववत नहीं हो सकता। समाधान: जब गुस्सा उठे, 24 घंटे प्रतीक्षा नियम का पालन करें — कुछ भी न कहें, न भेजें। गुस्सा एक लहर है, यह गुजर जाएगी।', 'आदर्श साथी: नंबर 1, 5, 9, 3 — ऊर्जा मेल। नंबर 9 + 9 विस्फोटक है (डबल मंगल)। मंगलीक दोष 9 वालों में प्रचलित है — विवाह से पहले मिलान करें।'], 'money_pattern': 'आप ऊर्जा भेजकर पैसा कमाते हैं — शारीरिक कार्य, साहस-आवश्यक नौकरियां, उच्च जोखिम + उच्च रिटर्न वाले उपक्रम। आप ऐसे जोखिम लेते हैं जो अन्य नहीं ले सकते। रियल एस्टेट, सोना, लाल वस्तुएं, तांबा, मूंगा (सलाह के बाद) — आपके लिए भाग्यशाली संपत्ति हैं।', 'health_pattern': 'रक्त, मांसपेशियां, सिर, सर्जरी प्रवण — मंगल के अंतर्गत। दुर्घटना का जोखिम औसत से अधिक है — ड्राइविंग/खेल में अतिरिक्त सुरक्षा। वार्षिक रक्त-संबंधी जांच। मसालेदार भोजन संतुलित करें — मंगल + मिर्च = अल्सर।', 'spiritual_path': "आपका धर्म 'सत्य के लिए लड़ाई, कमजोर की रक्षा' है। हनुमान साधना उत्तम है (मंगल का पुत्र)। सुब्रमण्यम/कार्तिकेय भक्ति। मंगलवार + शनिवार हनुमान चालीसा 11 बार। मंगलवार को लाल वस्त्र/लाल फूल का दान।", 'strengths': ['साहस — आप डर का सामना करते हैं', 'ऊर्जा — आप पहाड़ हिला सकते हैं', 'पैशन — जिसमें हो उसमें 200%', 'संरक्षण की प्रवृत्ति — अपने लोगों के लिए लड़ते हैं', 'पहल — पहले आप, बाद में सब'], 'challenges': ['गुस्सा प्रबंधन जीवनभर का प्रोजेक्ट है', 'आवेगशीलता — पहले कर लेते हैं, फिर सोचते हैं', 'रिश्तों में ईर्ष्या', 'शारीरिक चोट का खतरा', 'प्राधिकरण के साथ टकराव'], 'risk_alerts': ['दुर्घटना का जोखिम 24-26 + 32-34 के बीच — वाहन धीरे और सावधानी से चलाएं', 'गुस्सा रिश्तों में स्थायी नुकसान कर सकता है — 24 घंटे का नियम अनिवार्य है', 'विवाह से पहले मंगलीक जांच — 9 वालों में उच्च संभावना', 'जीवन में 1+ बार सर्जरी की संभावना — जल्दी स्वास्थ्य बीमा लें', 'मंगल शांति के लिए मंगलवार को हनुमान सेवा, सिंदूर अर्पण'], 'golden_periods': 'व्यक्तिगत वर्ष 9 — पूर्णता + परिवर्तन + नया चक्र। मंगल महादशा (7 वर्ष) तीव्र लेकिन जीवन-परिभाषित है। मध्य मार्च से मध्य मई (मंगल मकर में उच्च) आपकी वार्षिक खिड़की है। मंगलवार ब्रह्म मुहूर्त (4-6 AM) सबसे बड़े निर्णयों के लिए।'}, 5: {'title': 'संचारक — बुध का पारा', 'tagline': 'आप सौदों, विचारों और लोगों को जोड़ने में उस्ताद हैं।', 'life_essence': ["नंबर 5 का स्वामी बुध है। आप 'गतिशील' और तेज हैं। आपका मस्तिष्क 24/7 सक्रिय रहता है — लोग आपसे बात करके थक जाते हैं क्योंकि आप एक साथ 5 विषय संभाल सकते हैं। यह प्राकृतिक मल्टीटास्किंग आपकी सबसे बड़ी संपत्ति है।", 'आप जन्मजात नेटवर्कर हैं — 100 नाम, 100 फोन नंबर, 100 संदर्भ याद रखते हैं। बिक्री, विपणन, सौदे — ये आपके खून में हैं। आप एक बातचीत से अवसर निकाल सकते हैं।', "बुध की चेतावनी: 'उथला' बनने का जोखिम। इतने बहुमुखी होने से आप कहीं भी गहराई में नहीं जाते। आप केवल सतह को छूते हैं। मास्टर बनने के लिए, आपको एक क्षेत्र में 10,000 घंटे समर्पित करने की आवश्यकता है — नंबर 5 के लिए, यह अनुशासन बनाना सबसे कठिन है, लेकिन सबसे आवश्यक।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: व्यापार (विशेष रूप से व्यापार/वाणिज्य), बिक्री, विपणन, पत्रकारिता, मीडिया, आईटी, लेखा, परिवहन, संचार तकनीक, एजेंसी कार्य, रियल एस्टेट ब्रोकरिंग, शेयर बाजार, भाषा शिक्षण। कुछ भी जिसमें विविधता + लोग + धन परिवर्तन हो।', 'सामान्य गलती: नौकरी बदलना और व्यवसाय बदलना। आप 2 साल में बोर हो जाते हैं। समाधान: एक छत्र व्यवसाय चुनें (जैसे, परामर्श), इसके भीतर विविधता बनाएं — एक ही क्षेत्र, नए ग्राहक/प्रोजेक्ट।', 'विकास का समय: सभी नंबरों में सबसे पहले — 22-25 तक व्यावसायिक समझ आ जाती है। 28-32 पहला बड़ा पैसा है। 35-40 स्थिरीकरण है। बुधवार आपका शक्ति दिन है। आप सूर्योदय पर सबसे तेज होते हैं।'], 'love_pattern': ['प्रेम में, आप मजेदार और बौद्धिक रूप से प्रेरक हैं — लेकिन आप भावनात्मक गहराई से बचते हैं। आप भारी बातचीत से घबराते हैं।', "ब्रेकअप का कारण: आपका साथी महसूस करता है कि आप 'आधा उपस्थित' हैं — फोन, काम, दोस्ती सब समानांतर चल रहे होते हैं। समाधान: रिश्ते में 'रोजाना 1 घंटा फोन-मुक्त' नियम लागू करें — यह गेम-चेंजर है।", 'आदर्श साथी: नंबर 1, 3, 6, या 9 — बौद्धिक साथी। नंबर 2 + 5 गड़बड़ है (चंद्रमा के लिए बहुत अधिक आंदोलन)।'], 'money_pattern': 'पैसा आपके पास कई धाराओं में आता है — यही प्राकृतिक पैटर्न है। एकल वेतन आपको फंसा देगा। नंबर 5 के लिए एक साइड-हसल अनिवार्य है। शेयर, म्यूचुअल फंड, इंट्रा-डे ट्रेडिंग आपके लिए अनुकूल हैं। हरे आइटम, पन्ना (सलाह के बाद), तांबा आपका भंडारण है।', 'health_pattern': 'तंत्रिका तंत्र, त्वचा, हाथ, फेफड़े, आईबीएस/पाचन — बुध के अंतर्गत आते हैं। चिंता के दौरे नंबर 5 में आम हैं। दैनिक 10 मिनट प्राणायाम — जादुई प्रभाव। खाते समय मल्टीटास्किंग न करें।', 'spiritual_path': "आपका धर्म 'विचारों का आदान-प्रदान' है। विष्णु साधना, हनुमान चालीसा (बुध-मित्र), सरस्वती। बुधवार हरे मूंग का दान। मन-योग (त्राटक, विपश्यना) गेम-चेंजर है।", 'strengths': ['मल्टीटास्किंग — 5 चीजें एक साथ', 'नेटवर्किंग — त्वरित संबंध', 'अनुकूलता — हर भीड़ में फिट', 'बातचीत — सौदा बंद करने की कला', 'गति — तेज सीखने वाला, तेज निष्पादक'], 'challenges': ['उथली महारत — कहीं गहराई नहीं', 'चिंता, बेचैनी, अनिद्रा', 'प्रतिबद्धता का डर (रिश्ते और प्रोजेक्ट)', 'व्यंग्य में दिल दुखाना', "अधिक-प्रतिबद्धता — आप इतना 'हां' कहते हैं कि आप डिलीवर नहीं कर पाते"], 'risk_alerts': ['शेयर बाजार में इंट्रा-डे में बहुत पैसा नुकसान का जोखिम — सख्त स्टॉप-लॉस', 'चिंता से शांति का नुकसान — ध्यान न छोड़ें', 'व्हाट्सएप/इंस्टा की लत — उत्पादकता में 30% की कमी', 'कई रिश्तों का प्रलोभन — सीमा रखें', 'बुधवार व्रत 21 सप्ताह — मन की स्थिरता कई गुना'], 'golden_periods': 'व्यक्तिगत वर्ष 5 स्पष्ट रूप से — पूरे वर्ष में सफलता के अवसर। बुध की महादशा (17 वर्ष) सुनहरी है। मई-जून वार्षिक शक्ति खिड़की है (बुध कन्या में उच्च है)। बुधवार + सूर्योदय आपका अभिव्यक्ति शिखर है।'}, 4: {'title': 'द डिसरप्टर — राहु का आधुनिक दृष्टा', 'tagline': 'आप नियम तोड़कर नए नियम बनाने वाले हो।', 'life_essence': ["नंबर 4 का स्वामी राहु है — आधुनिक, अपरंपरागत, विद्युत। आप परंपरा से चिढ़ जाते हो — 'क्यों ऐसा ही करना है?' आपका पसंदीदा सवाल है। बचपन में माता-पिता ने आपको 'जिद्दी' कहा होगा, पर सच्चाई यह है कि आप जिद्दी नहीं — मौलिक हो। आप कॉपी-पेस्ट दुनिया में एक मौलिक आत्मा हो।", 'आपकी जिंदगी रेखीय नहीं है — अचानक छलांगें, अचानक गिरावटें, अचानक सुधार। आप बोरिंग स्थिर करियर नहीं निभा सकते। टेक, नवाचार, विदेशी भूमि, गैर-पारंपरिक रास्ते — यही आपकी ऊर्जा है।', "राहु की चेतावनी: 'मोह'। कभी-कभी आप शॉर्टकट्स में फंस जाते हो — 'जल्दी पैसा', 'आसान सफलता'। यह हमेशा एक जाल होता है। राहु से केवल 'लंबा, धैर्यवान, नैतिक कार्य' ही अच्छा फल देता है। शॉर्टकट = आत्म-विनाश।"], 'career_pattern': ['सर्वश्रेष्ठ क्षेत्र: प्रौद्योगिकी, सॉफ्टवेयर, एआई/डेटा, विदेशी व्यापार, विमानन, विद्युत इंजीनियरिंग, फोटोग्राफी/सिनेमा, सोशल मीडिया, क्रिप्टो/फिनटेक, इमिग्रेशन कंसल्टिंग, एनजीओ कार्य, कुछ भी अत्याधुनिक। सरकारी नौकरी आपको बोर करेगी।', "सामान्य गलती: आप हर 2-3 साल में नौकरी बदलते हो — 'कुछ नया' चाहिए। परिणाम: किसी भी क्षेत्र में गहरी महारत नहीं बनती। समाधान: एक उद्योग चुनें और उसमें 7+ साल दें — फिर आपका राहु-जादू काम करेगा।", 'विकास समय: अनियमित — 26-28, 33-35, 41-44 में अचानक छलांगें। जब राहु की महादशा (18 साल) आती है, जीवन पुनः परिभाषित हो जाता है। शनिवार आपका शक्ति दिन है (राहु = शनि का गुप्त साथी)।'], 'love_pattern': ['प्रेम में आप अप्रत्याशित हो — कभी जुनूनी, कभी ठंडे। साथी को समझ नहीं आता क्या हुआ। आप यह जानबूझकर नहीं करते — राहु की ऊर्जा ही ऐसी है।', 'ब्रेकअप का कारण: ऊब। एक नियमित संबंध आपको घुटन देता है। आप रोमांच, नवीनता, रहस्य चाहते हो। समाधान: साथी के साथ नए अनुभव जबरदस्ती बनाएं — यात्रा, शौक, आश्चर्य।', 'आदर्श साथी: नंबर 1, 5, या 7 — जो स्वतंत्रता का सम्मान करते हैं। नंबर 2 + 4 असंगत (चंद्रमा-राहु विरोधी)। अंतरजातीय/अंतर-सांस्कृतिक विवाह राहु की पहचान है।'], 'money_pattern': 'पैसा आपके पास लहरों में आता है — कभी बाढ़, कभी शून्य। निवेश में अटकलें, क्रिप्टो, विदेशी इक्विटी आकर्षक लगती है — लेकिन राहु यहां धोखा देता है। 70% सुरक्षित (एफडी/सूचकांक फंड), 30% अटकलें — यही सूत्र है। विदेशी मुद्रा, इलेक्ट्रॉनिक्स, नीले आइटम आपके लिए भाग्यशाली भंडारण हैं।', 'health_pattern': 'त्वचा, तंत्रिका तंत्र, लत, चिंता, सांप से संबंधित डर — राहु के अंतर्गत। ध्यान और डिजिटल डिटॉक्स अनिवार्य हैं। स्मार्टफोन से 1 घंटे पहले सोएं — राहु का सीधा अंग फोन है।', 'spiritual_path': "आपका धर्म 'पुरानी संरचनाओं को तोड़ना' है। सरस्वती पूजा, दुर्गा साधना, शिव-तांडव स्तोत्र — राहु-मित्र। शनिवार को काले तिल का दान, ठंडे मौसम में कंबल का दान।", 'strengths': ['मौलिक सोच — अपरंपरागत समाधान', 'टेक्नोलॉजी में निपुण — नए उपकरण स्वाभाविक रूप से अपनाते हैं', 'विदेशी झुकाव — विदेश में अवसर मिलते हैं', 'संकट नवाचार — आपात स्थिति में रचनात्मक', 'नेटवर्किंग — विविध सर्कल बनाते हैं'], 'challenges': ['बेचैनी — कुछ भी लंबे समय तक प्रतिबद्ध नहीं करते', 'लत का जोखिम (पदार्थ, स्क्रीन, जुआ)', 'अचानक गुस्से का उबाल', 'संबंधों में अस्थिरता', "'जल्दी अमीर बनो' योजनाओं में फंसना"], 'risk_alerts': ['क्रिप्टो/अटकल निवेश में >30% पोर्टफोलियो न रखें', 'सांप/कीड़े के काटने का कर्मिक जोखिम — प्राथमिक चिकित्सा ज्ञान आवश्यक', 'विदेश यात्रा में दस्तावेज सख्त — राहु पासपोर्ट खोने का शौक रखता है', '28-30 या 41-44 के बीच महादशा-परिवर्तन, जीवन पुनः परिभाषित — मार्गदर्शन लें', 'तनाव-खाना या रात में स्क्रॉलिंग की लत — स्वास्थ्य को नुकसान पहुंचाएगी'], 'golden_periods': 'जब राहु की महादशा (18 साल) सक्रिय होती है — यह खेल-परिवर्तक है। व्यक्तिगत वर्ष 1, 4, 7 — नवाचार में तेजी से प्रगति। फरवरी-मार्च (कुंभ में राहु का पक्षधर) वार्षिक खिड़की। शनिवार रात को रणनीति योजना बनाएं — राहु चरम पर होता है।'}})


# ─── Auto-generated EN/HI extras (OpenAI bulk translate) ───────────

_FOCUS_2026_HG = {
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

_FOCUS_2026_EN = {1: 'Independent venture launch — start something of your own. Reconcile with authority figures.', 2: 'Emotional boundaries strengthen. Pay attention to health (especially mother-related).', 3: 'Build an income stream from teaching/writing. Consider higher education or certification.', 4: 'Capture tech/foreign opportunities. Stop job-hopping — go deep in one field.', 5: 'Multiple income streams crystallize. Expand communication-based business.', 6: 'Balance family and creative projects. Make a long-pending relationship decision.', 7: 'Deepen spiritual study. Solo retreat. Do not ignore the practical world.', 8: 'Foundation work — slow and steady. Build real estate or assets. Heal father-bond.', 9: 'Channel anger constructively — sports/exercise mandatory. Big move possible.'}

_FOCUS_2026_HI = {1: 'स्वतंत्र उद्यम शुरू करें — अपना कुछ शुरू करें। प्राधिकरण के आंकड़ों से सुलह करें।', 2: 'भावनात्मक सीमाएं मजबूत होंगी। स्वास्थ्य (विशेषकर माता-संबंधी) पर ध्यान दें।', 3: 'शिक्षण/लेखन से आय का स्रोत बनाएं। उच्च शिक्षा या प्रमाणन पर विचार करें।', 4: 'तकनीकी/विदेशी अवसरों को पकड़ें। नौकरी बदलना बंद करें — एक क्षेत्र में गहराई से जाएं।', 5: 'कई आय स्रोत स्पष्ट हों। संचार-आधारित व्यवसाय का विस्तार करें।', 6: 'परिवार और रचनात्मक परियोजनाओं का संतुलन। लंबे समय से लंबित संबंध निर्णय लें।', 7: 'आध्यात्मिक अध्ययन को गहरा करें। एकल वापसी। व्यावहारिक दुनिया की अनदेखी न करें।', 8: 'नींव का काम — धीरे और स्थिर। अचल संपत्ति या संपत्ति बनाएं। पिता-संबंध को ठीक करें।', 9: 'क्रोध को रचनात्मक रूप से चैनल करें — खेल/व्यायाम अनिवार्य। बड़ा कदम संभव है।'}

_WHY_EN = {'mobile_1': 'Mobile number carries Surya energy — every call/message transmits leadership vibration.', 'mobile_2': 'Moon energy brings emotional fluctuation — calls with mood swings.', 'mobile_3': 'Jupiter provides wisdom + financial expansion — knowledge-based calls are profitable.', 'mobile_4': 'Rahu causes sudden, unexpected calls — both opportunities + disruptions.', 'mobile_5': 'Mercury offers speed + business — magic in sales, deals, networking.', 'mobile_6': 'Venus brings harmony + relationships — a strong center for love + family.', 'mobile_7': 'Ketu brings mystery + isolation — important calls come but interaction is less.', 'mobile_8': 'Saturn offers slow growth + karmic — favorable for official, government, long-term work.', 'mobile_9': 'Mars provides energy + courage — bold conversations, but risk of anger.', 'vehicle_1': 'Vehicle 1 — leadership feel, but solo travel pattern.', 'vehicle_2': 'Vehicle 2 — emotional, family-friendly, but maintenance demanding.', 'vehicle_3': 'Vehicle 3 — growth-oriented, brings money.', 'vehicle_4': 'Vehicle 4 — sudden tech issues + unexpected breakdowns common. Modern car is okay, classic avoid.', 'vehicle_5': 'Vehicle 5 — versatile, multi-purpose, good for business travel.', 'vehicle_6': 'Vehicle 6 — luxury, beauty, comfort — will impress you.', 'vehicle_7': 'Vehicle 7 — solo-friendly, suits quiet drives.', 'vehicle_8': 'Vehicle 8 — heavy-duty, long-life, but initial repair phase.', 'vehicle_9': 'Vehicle 9 — sports/SUV style suits, but accident risk higher than average.', 'house_1': 'House 1 — leadership family, head of household empowered.', 'house_2': 'House 2 — emotional, strong mother-energy, peace-oriented.', 'house_3': 'House 3 — wealth + wisdom flow.', 'house_4': 'House 4 — frequent sudden changes (renovations, guests, news).', 'house_5': 'House 5 — busy, social, business-friendly home.', 'house_6': 'House 6 — family + romance + beauty — best for relationships.', 'house_7': 'House 7 — quiet, spiritual, suited for study.', 'house_8': 'House 8 — initial struggle phase, later wealth-anchored.', 'house_9': 'House 9 — energy + arguments + passion — pet/sports-friendly.'}

_WHY_HI = {'mobile_1': 'मोबाइल नंबर सूर्य ऊर्जा वहन करता है — हर कॉल/संदेश में नेतृत्व का कंपन जाता है।', 'mobile_2': 'चंद्र ऊर्जा भावनात्मक उतार-चढ़ाव लाती है — मूड स्विंग्स के साथ कॉल्स।', 'mobile_3': 'बृहस्पति ज्ञान + वित्तीय विस्तार देता है — ज्ञान-आधारित कॉल्स लाभदायक होती हैं।', 'mobile_4': 'राहु अचानक, अप्रत्याशित कॉल्स लाता है — अवसर + व्यवधान दोनों।', 'mobile_5': 'बुध गति + व्यापार देता है — बिक्री, सौदे, नेटवर्किंग में जादू।', 'mobile_6': 'शुक्र समरसता + संबंध लाता है — प्रेम + परिवार का मजबूत केंद्र।', 'mobile_7': 'केतु रहस्य + एकांत लाता है — महत्वपूर्ण कॉल्स आती हैं पर बातचीत कम।', 'mobile_8': 'शनि धीमी वृद्धि + कर्मिक देता है — आधिकारिक, सरकारी, दीर्घकालिक कार्यों में अनुकूल।', 'mobile_9': 'मंगल ऊर्जा + साहस देता है — साहसी वार्तालाप, पर क्रोध का जोखिम।', 'vehicle_1': 'वाहन 1 — नेतृत्व का अहसास, पर एकल यात्रा पैटर्न।', 'vehicle_2': 'वाहन 2 — भावनात्मक, परिवार-हितैषी, पर रखरखाव की मांग।', 'vehicle_3': 'वाहन 3 — वृद्धि-उन्मुख, धन लाता है।', 'vehicle_4': 'वाहन 4 — अचानक तकनीकी समस्याएं + अप्रत्याशित ब्रेकडाउन आम। आधुनिक कार ठीक है, क्लासिक से बचें।', 'vehicle_5': 'वाहन 5 — बहुमुखी, बहुउद्देश्यीय, व्यापार यात्रा के लिए अच्छा।', 'vehicle_6': 'वाहन 6 — विलासिता, सुंदरता, आराम — आपको प्रभावित करेगा।', 'vehicle_7': 'वाहन 7 — एकल-हितैषी, शांत ड्राइव्स के लिए उपयुक्त।', 'vehicle_8': 'वाहन 8 — भारी-भरकम, लंबी उम्र, पर प्रारंभिक मरम्मत चरण।', 'vehicle_9': 'वाहन 9 — खेल/एसयूवी शैली उपयुक्त, पर दुर्घटना का जोखिम औसत से अधिक।', 'house_1': 'घर 1 — नेतृत्व परिवार, घर के मुखिया को सशक्त करता है।', 'house_2': 'घर 2 — भावनात्मक, मातृ-ऊर्जा मजबूत, शांति-उन्मुख।', 'house_3': 'घर 3 — धन + ज्ञान का प्रवाह।', 'house_4': 'घर 4 — अचानक परिवर्तन (नवीनीकरण, मेहमान, समाचार) अक्सर।', 'house_5': 'घर 5 — व्यस्त, सामाजिक, व्यापार-हितैषी घर।', 'house_6': 'घर 6 — परिवार + रोमांस + सुंदरता — संबंधों के लिए सर्वश्रेष्ठ।', 'house_7': 'घर 7 — शांत, आध्यात्मिक, अध्ययन के लिए उपयुक्त।', 'house_8': 'घर 8 — प्रारंभिक संघर्ष चरण, बाद में धन-आधारित।', 'house_9': 'घर 9 — ऊर्जा + तर्क + जुनून — पालतू/खेल-हितैषी।'}

_IMPACT_EN = {'mobile_1': "You project a 'me first' vibe in every conversation — this attracts leaders but makes juniors feel exhausted.", 'mobile_2': 'You listen more during calls — people open up about their problems to you, and you become a free counselor.', 'mobile_3': 'Knowledge-based calls come in — people contact you for advice or teaching. Direct income link possible.', 'mobile_4': 'Sudden good or bad news comes over the phone — sometimes a job offer, sometimes an accident — an emotional rollercoaster.', 'mobile_5': 'People bring new opportunities, deals, contacts over the phone — you become a natural networker.', 'mobile_6': 'There is a flow of love + family + creative collaboration over the phone — relationship strengthening.', 'mobile_7': 'You miss important calls — you remain distant on the phone, and people notice.', 'mobile_8': 'There is more official/government communication over the phone — bureaucratic delays, paperwork, court matters connect.', 'mobile_9': 'Arguments are quick, anger explosions easy over the phone — stress in relationships.', 'vehicle_1': "The vehicle keeps you more comfortable as a 'lone driver' — long solo road trips are your favorites.", 'vehicle_2': 'Perfect for family trips — but fuel + maintenance bills are higher than expected.', 'vehicle_3': 'Income generation possible with the vehicle — Uber/cab side or business travel.', 'vehicle_4': 'Hidden electrical/electronic issues are regular — yearly mechanic checkup is a MUST. Comprehensive insurance.', 'vehicle_5': 'Vehicle serves both business + personal use — versatile, serves multiple purposes.', 'vehicle_6': 'The vehicle becomes your personality statement — people judge. Maintenance is a priority.', 'vehicle_7': 'Clarity comes during long drives — solo driving becomes your therapy.', 'vehicle_8': 'Vehicle is long-lasting (easily 10+ years) — but the initial 1-2 years are frustrating.', 'vehicle_9': 'Desire for speed + power — but the risk of over-speeding is higher than average. Defensive driving habit is a MUST.', 'house_1': "You are dominant at home — everyone listens to you. But no 'me-time' — recharging is difficult.", 'house_2': 'Home is an emotional safe-haven for everyone — but boundaries are weak, anyone can come and settle.', 'house_3': 'Wealth flows at home — bills are automatically managed, savings build.', 'house_4': 'Something sudden changes at home every 6-12 months (renovation, member shift, repair).', 'house_5': 'Home becomes a party-house — people come freely. A dedicated quiet space is needed for productivity.', 'house_6': 'Home is the center of romance + family bonding — beautiful interior + happy memories.', 'house_7': 'Home carries spiritual energy — meditation + study are productive here.', 'house_8': 'Initial phase at home involves financial struggle, but wealth crystallizes in 5+ years.', 'house_9': 'There is a lot of energy at home — arguments + makeup cycle. Pet or sport equipment fit.'}

_IMPACT_HI = {'mobile_1': "आप हर बातचीत में 'मैं पहले' वाला अहसास प्रकट करते हैं — यह नेताओं को आकर्षित करता है पर जूनियर्स थके-थके महसूस करते हैं।", 'mobile_2': 'कॉल्स में आप ज्यादा सुनते हैं — लोग अपनी समस्याएँ आपके सामने खोलते हैं, आप मुफ्त काउंसलर बन जाते हैं।', 'mobile_3': 'ज्ञान-आधारित कॉल्स आते हैं — लोग सलाह या शिक्षण के लिए संपर्क करते हैं। सीधा आय लिंक संभव।', 'mobile_4': 'फोन पर अचानक अच्छी या बुरी खबर आती है — कभी नौकरी का प्रस्ताव, कभी दुर्घटना — भावनात्मक रोलरकोस्टर।', 'mobile_5': 'फोन पर लोग नए अवसर, सौदे, संपर्क लाते हैं — आप प्राकृतिक नेटवर्कर बन जाते हैं।', 'mobile_6': 'फोन पर प्रेम + परिवार + रचनात्मक सहयोग का प्रवाह रहता है — संबंध मजबूत होते हैं।', 'mobile_7': 'आप महत्वपूर्ण कॉल्स मिस कर देते हैं — फोन पर आप दूर रहते हैं, लोग ध्यान देते हैं।', 'mobile_8': 'फोन पर आधिकारिक/सरकारी संचार अधिक होता है — नौकरशाही देरी, कागजी कार्यवाही, अदालत के मामले जुड़ते हैं।', 'mobile_9': 'फोन पर तर्क जल्दी होते हैं, गुस्से के विस्फोट आसान होते हैं — संबंधों में तनाव।', 'vehicle_1': "वाहन आपको 'अकेला चालक' में अधिक आरामदायक रखता है — लंबी एकल सड़क यात्राएँ आपकी पसंदीदा हैं।", 'vehicle_2': 'परिवारिक यात्राओं के लिए परफेक्ट — पर ईंधन + रखरखाव बिल अपेक्षा से अधिक।', 'vehicle_3': 'वाहन के साथ आय उत्पन्न करना संभव — उबर/कैब साइड या व्यापार यात्रा।', 'vehicle_4': 'छिपी हुई विद्युत/इलेक्ट्रॉनिक समस्याएँ नियमित होती हैं — वार्षिक मैकेनिक चेकअप अनिवार्य है। बीमा व्यापक।', 'vehicle_5': 'वाहन व्यापार + व्यक्तिगत उपयोग दोनों करता है — बहुमुखी, कई उद्देश्यों की पूर्ति करता है।', 'vehicle_6': 'वाहन आपकी व्यक्तित्व का बयान बनता है — लोग जज करते हैं। रखरखाव प्राथमिकता है।', 'vehicle_7': 'लंबी ड्राइव्स में स्पष्टता मिलती है — एकल ड्राइविंग आपकी थेरेपी बन जाती है।', 'vehicle_8': 'वाहन लंबे समय तक चलता है (10+ साल आसानी से) — पर शुरुआती 1-2 साल निराशाजनक।', 'vehicle_9': 'गति + शक्ति का अहसास चाहिए — पर ओवर-स्पीडिंग का जोखिम औसत से अधिक। रक्षात्मक ड्राइविंग आदत अनिवार्य है।', 'house_1': "घर में आप प्रभावी हैं — सब आपकी मानते हैं। पर 'मे-टाइम' नहीं मिलता — पुनः ऊर्जा प्राप्त करना मुश्किल।", 'house_2': 'घर सभी के लिए भावनात्मक सुरक्षित स्थान है — पर सीमाएँ कमजोर हैं, कोई भी आकर बस सकता है।', 'house_3': 'घर में धन का प्रवाह होता है — बिल अपने आप प्रबंधित होते हैं, बचत बनती है।', 'house_4': 'घर में 6-12 महीने में कुछ न कुछ अचानक परिवर्तन (नवीनीकरण, सदस्य परिवर्तन, मरम्मत) होता रहता है।', 'house_5': 'घर पार्टी-हाउस बन जाता है — लोग स्वतंत्र रूप से आते हैं। उत्पादकता के लिए समर्पित शांत स्थान चाहिए।', 'house_6': 'घर रोमांस + परिवारिक बंधन का केंद्र है — सुंदर इंटीरियर + खुशहाल यादें।', 'house_7': 'घर आध्यात्मिक ऊर्जा वहन करता है — ध्यान + अध्ययन यहाँ उत्पादक हैं।', 'house_8': 'घर में प्रारंभिक चरण में वित्तीय संघर्ष होता है, पर 5+ साल में धन ठोस होता है।', 'house_9': 'घर में ऊर्जा अधिक होती है — तर्क + मेल-मिलाप चक्र। पालतू या खेल उपकरण फिट।'}

_ACTION_EN = {'mobile_1': 'Make important calls on Sunday morning. Use a red mobile cover with the number.', 'mobile_2': 'Make important calls on Monday. Use a white or silver cover. Avoid late-night calls (Moon is weak).', 'mobile_3': 'Important deal calls on Thursday morning. Use a yellow cover. Utilize Hora time.', 'mobile_4': "Put the mobile on 'silent + DND' at night — Rahu disturbs the mind at night. Tech calls on Saturday.", 'mobile_5': 'Deals and sales calls on Wednesday morning. Use a green cover. Avoid multitasking while on the phone.', 'mobile_6': 'Important relationship/love calls on Friday. Use a white or pink cover. Music and harmony tones.', 'mobile_7': 'Important spiritual calls on Tuesday/Saturday. Use a multi-color cover. Solo time is essential.', 'mobile_8': 'Official and government calls on Saturday morning. Use a black cover. Patience and structured talk.', 'mobile_9': 'Strategic calls on Tuesday morning. Use a red cover. Apply a 24-hour rule before responding in anger.', 'vehicle_1': 'Vehicle pooja on Sunday morning. Red ribbon. Red dashboard mat. Owner solo drive priority.', 'vehicle_2': 'Pooja on Monday morning. White flowers. Family trips on Monday/Friday.', 'vehicle_3': 'Pooja on Thursday. Yellow ribbon. Business travel on Thursday is lucky.', 'vehicle_4': 'Pooja on Saturday. Tech check every 6 months. Comprehensive insurance is a MUST.', 'vehicle_5': 'Pooja on Wednesday. Green/yellow ribbon. Long drives on Wednesday are productive.', 'vehicle_6': 'Pooja on Friday. White flowers. Vehicle should always be clean and perfumed.', 'vehicle_7': 'Pooja on Tuesday. Allow solo time in the vehicle.', 'vehicle_8': 'Pooja on Saturday. Keep a black umbrella. Never skip annual full service.', 'vehicle_9': 'Pooja on Tuesday. Red flag/sticker. Defensive driving course recommended.'}

_ACTION_HI = {'mobile_1': 'महत्वपूर्ण कॉल्स रविवार सुबह करें। नंबर के साथ लाल मोबाइल कवर का उपयोग करें।', 'mobile_2': 'महत्वपूर्ण कॉल्स सोमवार को करें। सफेद या सिल्वर कवर का उपयोग करें। देर रात के कॉल्स से बचें (चंद्रमा कमजोर है)।', 'mobile_3': 'गुरुवार सुबह महत्वपूर्ण डील कॉल्स। पीला कवर। होरा समय का उपयोग करें।', 'mobile_4': "मोबाइल को रात में 'साइलेंट + डीएनडी' पर रखें — राहु रात में मन को विचलित करता है। तकनीकी कॉल्स शनिवार को करें।", 'mobile_5': 'बुधवार सुबह डील्स और सेल्स कॉल्स। हरा कवर। फोन करते समय मल्टीटास्किंग से बचें।', 'mobile_6': 'शुक्रवार को महत्वपूर्ण संबंध/प्रेम कॉल्स। सफेद या गुलाबी कवर। संगीत और सामंजस्यपूर्ण धुनें।', 'mobile_7': 'मंगलवार/शनिवार को महत्वपूर्ण आध्यात्मिक कॉल्स। बहुरंगी कवर। अकेले समय जरूरी है।', 'mobile_8': 'शनिवार सुबह आधिकारिक और सरकारी कॉल्स। काला कवर। धैर्य और संरचित वार्तालाप।', 'mobile_9': 'मंगलवार सुबह रणनीतिक कॉल्स। लाल कवर। गुस्से में प्रतिक्रिया देने से पहले २४ घंटे का नियम अपनाएं।', 'vehicle_1': 'रविवार सुबह वाहन पूजा। लाल रिबन। लाल डैशबोर्ड मैट। मालिक की अकेले ड्राइव प्राथमिकता।', 'vehicle_2': 'सोमवार सुबह पूजा। सफेद फूल। परिवारिक यात्राएं सोमवार/शुक्रवार को।', 'vehicle_3': 'गुरुवार को पूजा। पीला रिबन। गुरुवार को व्यापार यात्रा शुभ है।', 'vehicle_4': 'शनिवार को पूजा। हर ६ महीने में तकनीकी जांच। व्यापक बीमा अनिवार्य है।', 'vehicle_5': 'बुधवार को पूजा। हरा/पीला रिबन। बुधवार को लंबी ड्राइव्स उत्पादक होती हैं।', 'vehicle_6': 'शुक्रवार को पूजा। सफेद फूल। वाहन हमेशा साफ और सुगंधित होना चाहिए।', 'vehicle_7': 'मंगलवार को पूजा। वाहन में अकेले समय की अनुमति दें।', 'vehicle_8': 'शनिवार को पूजा। काली छतरी रखें। वार्षिक पूर्ण सेवा कभी न छोड़ें।', 'vehicle_9': 'मंगलवार को पूजा। लाल झंडा/स्टिकर। रक्षात्मक ड्राइविंग कोर्स की सिफारिश की जाती है।'}

_HOUSE_ACTION_EN = {1: 'Sunday morning home prayer, Surya namaskar on the terrace, red rangoli at the entrance.', 2: 'Monday Chandra prayer, white flowers at the entrance, consider a water fountain in the north.', 3: 'Thursday Brihaspati prayer, yellow paint accents, wisdom books visible.', 4: 'Saturday Rahu pacification, tech corner kept clean, avoid blue lights in the bedroom.', 5: 'Wednesday Budha prayer, green plants, dedicated study/work corner.', 6: 'Friday Shukra prayer, fresh flowers daily, art on walls, mirror placement in the north-east.', 7: 'Tuesday/Saturday meditation corner, multi-color decor, quiet zone protected.', 8: 'Saturday Shani prayer, black-stone entrance, structured and minimal interior.', 9: 'Tuesday Mangal prayer, red curtains in the south room, kitchen and fire area in the south-east.'}

_HOUSE_ACTION_HI = {1: 'रविवार सुबह घर पूजा, छत पर सूर्य नमस्कार, प्रवेश द्वार पर लाल रंगोली।', 2: 'सोमवार चंद्र पूजा, प्रवेश द्वार पर सफेद फूल, उत्तर में जल-फव्वारा विचार करें।', 3: 'गुरुवार बृहस्पति पूजा, पीले रंग के पेंट के अक्सेंट, ज्ञान की पुस्तकें दिखाई दें।', 4: 'शनिवार राहु शांति, तकनीकी कोना साफ रखें, शयनकक्ष में नीली लाइट्स से बचें।', 5: 'बुधवार बुध पूजा, हरे पौधे, अध्ययन/कार्य कोना समर्पित।', 6: 'शुक्रवार शुक्र पूजा, ताजे फूल रोजाना, दीवारों पर कला, उत्तर-पूर्व में दर्पण का स्थान।', 7: 'मंगलवार/शनिवार ध्यान कोना, बहुरंगी सजावट, शांत क्षेत्र सुरक्षित।', 8: 'शनिवार शनि पूजा, काले पत्थर का प्रवेश द्वार, संरचित और न्यूनतम इंटीरियर।', 9: 'मंगलवार मंगल पूजा, दक्षिण कक्ष में लाल पर्दे, रसोई और अग्नि क्षेत्र दक्षिण-पूर्व में।'}

_LUCKY_COLOUR_STRINGS_EN = {1: {'vehicle': 'Golden, Cream, Pearl White, Bright Red — colors that reflect the energy of Surya. Avoid: Black, Dark Blue.', 'business': 'Gold + Orange combo in the logo — projects leadership + warmth.', 'gemstone_tone': 'Ruby red, sunstone orange — use in accessories.'}, 2: {'vehicle': 'Pearl White, Silver, Cream, Light Blue — the calming energy of Chandra. Avoid: Bright Red, Black.', 'business': 'Silver + White + Soft Blue in the logo — calming, trustworthy feel.', 'gemstone_tone': 'Pearl + moonstone tones — soft, reflective accessories.'}, 3: {'vehicle': 'Yellow, Cream, Golden Beige — auspicious energy of Brihaspati. Avoid: Dark Green, Black.', 'business': 'Yellow + Purple combo in the logo — wisdom + prosperity feel.', 'gemstone_tone': 'Yellow Sapphire + Topaz tones — gold-rim accessories.'}, 4: {'vehicle': 'Steel Grey, Electric Blue, Khaki, Off-White — modern, Rahu-friendly. Avoid: Pure Black, Deep Red.', 'business': 'Blue + Grey + White in the logo — tech, modern, trustworthy.', 'gemstone_tone': 'Hessonite (gomed) brown-orange tones — minimal accessories.'}, 5: {'vehicle': "Light Green, Turquoise, White, Light Blue — Mercury's lively energy. Avoid: Black.", 'business': 'Green + White in the logo — fresh, agile, communication-friendly.', 'gemstone_tone': 'Emerald green tones — modern, sleek accessories.'}, 6: {'vehicle': 'White, Cream, Pearl, Light Pink, Sky Blue — the beauty energy of Shukra. Avoid: Black, Deep Red.', 'business': 'White + Rose Gold + Soft Pink in the logo — luxury, beauty, premium feel.', 'gemstone_tone': 'Diamond + Crystal clear tones — elegant accessories.'}, 7: {'vehicle': 'Light Grey, Smoke Grey, Multi-tone, Off-White — the mystic energy of Ketu. Avoid: Bright Red.', 'business': 'Grey + Multi-color accent in the logo — unique, mystic, original feel.', 'gemstone_tone': "Cat's eye (lehsunia) — earthy, neutral accessories."}, 8: {'vehicle': 'Black, Deep Blue, Iron Grey, Dark Brown — the serious energy of Shani. Avoid: Bright Yellow, Bright Orange.', 'business': 'Black + Deep Blue + Silver in the logo — authority, structure, longevity.', 'gemstone_tone': 'Blue Sapphire + Onyx — heavy, structured accessories.'}, 9: {'vehicle': 'Red, Maroon, Crimson, Deep Orange — the warrior energy of Mangal. Avoid: Pure Black.', 'business': 'Red + Gold in the logo — bold, action-oriented, energy-packed.', 'gemstone_tone': 'Red Coral (moonga) tones — bold accessories.'}}

_LUCKY_COLOUR_STRINGS_HI = {1: {'vehicle': 'गोल्डन, क्रीम, पर्ल व्हाइट, ब्राइट रेड — सूर्य की ऊर्जा को दर्शाने वाले रंग। बचें: काला, डार्क ब्लू।', 'business': 'लोगो में गोल्ड + ऑरेंज कॉम्बो — नेतृत्व + गर्मजोशी को प्रोजेक्ट करता है।', 'gemstone_tone': 'रूबी रेड, सनस्टोन ऑरेंज — एक्सेसरीज़ में उपयोग करें।'}, 2: {'vehicle': 'पर्ल व्हाइट, सिल्वर, क्रीम, लाइट ब्लू — चंद्र की शांति ऊर्जा। बचें: ब्राइट रेड, काला।', 'business': 'लोगो में सिल्वर + व्हाइट + सॉफ्ट ब्लू — शांत, विश्वसनीय अनुभव।', 'gemstone_tone': 'पर्ल + मूनस्टोन टोन — सॉफ्ट, रिफ्लेक्टिव एक्सेसरीज़।'}, 3: {'vehicle': 'पीला, क्रीम, गोल्डन बेज — बृहस्पति की शुभ ऊर्जा। बचें: डार्क ग्रीन, काला।', 'business': 'लोगो में पीला + पर्पल कॉम्बो — ज्ञान + समृद्धि का अनुभव।', 'gemstone_tone': 'पीला नीलम + पुखराज टोन — गोल्ड-रिम एक्सेसरीज़।'}, 4: {'vehicle': 'स्टील ग्रे, इलेक्ट्रिक ब्लू, खाकी, ऑफ-व्हाइट — आधुनिक राहु-फ्रेंडली। बचें: शुद्ध काला, गहरा लाल।', 'business': 'लोगो में ब्लू + ग्रे + व्हाइट — टेक, आधुनिक, विश्वसनीय।', 'gemstone_tone': 'हेसोनाइट (गोमेद) ब्राउन-ऑरेंज टोन — न्यूनतम एक्सेसरीज़।'}, 5: {'vehicle': 'लाइट ग्रीन, टर्क्वॉइज़, व्हाइट, लाइट ब्लू — बुध की चंचल ऊर्जा। बचें: काला।', 'business': 'लोगो में ग्रीन + व्हाइट — ताज़ा, चुस्त, संचार-फ्रेंडली।', 'gemstone_tone': 'एमराल्ड ग्रीन टोन — आधुनिक, स्लीक एक्सेसरीज़।'}, 6: {'vehicle': 'व्हाइट, क्रीम, पर्ल, लाइट पिंक, स्काई ब्लू — शुक्र की सौंदर्य ऊर्जा। बचें: काला, गहरा लाल।', 'business': 'लोगो में व्हाइट + रोज़ गोल्ड + सॉफ्ट पिंक — लक्ज़री, सुंदरता, प्रीमियम अनुभव।', 'gemstone_tone': 'डायमंड + क्रिस्टल क्लियर टोन — सुरुचिपूर्ण एक्सेसरीज़।'}, 7: {'vehicle': 'लाइट ग्रे, स्मोक ग्रे, मल्टी-टोन, ऑफ-व्हाइट — केतु की रहस्यमयी ऊर्जा। बचें: ब्राइट रेड।', 'business': 'लोगो में ग्रे + मल्टी-कलर एक्सेंट — अनोखा, रहस्यमयी, मौलिक अनुभव।', 'gemstone_tone': 'कैट्स आई (लेहसुनिया) — अर्थी, न्यूट्रल एक्सेसरीज़।'}, 8: {'vehicle': 'काला, गहरा नीला, आयरन ग्रे, डार्क ब्राउन — शनि की गंभीर ऊर्जा। बचें: ब्राइट येलो, ब्राइट ऑरेंज।', 'business': 'लोगो में काला + गहरा नीला + सिल्वर — अधिकार, संरचना, दीर्घायु।', 'gemstone_tone': 'नीलम + ओनेक्स — भारी, संरचित एक्सेसरीज़।'}, 9: {'vehicle': 'लाल, मैरून, क्रिमसन, गहरा नारंगी — मंगल की शूरवीर ऊर्जा। बचें: शुद्ध काला।', 'business': 'लोगो में लाल + गोल्ड — साहसी, क्रियाशील, ऊर्जा से भरपूर।', 'gemstone_tone': 'रेड कोरल (मूंगा) टोन — साहसी एक्सेसरीज़।'}}

_MONTH_THEMES_EN = {1: '🚀 New Beginnings — a month to start new work. Make independent decisions. Strengthen networking.', 2: '🤝 Patience + Partnership — wait and listen. Collaborate with others. Avoid forcing decisions.', 3: '✨ Creativity + Joy — social events, expressing yourself, writing/teaching. Networking flourishes.', 4: '🛠️ Hard Work + Foundation — create systems, complete paperwork. Slow but steady.', 5: '🌪️ Change + Movement — travel, new contacts, sudden opportunities. Maximum flexibility needed.', 6: '❤️ Love + Family — invest in relationships, beauty/home projects. Major announcements possible.', 7: '🧘 Reflection + Spiritual — solo time, study, meditation. Postpone big decisions.', 8: '💼 Power + Money — business deals close, promotions/contracts. Discipline is most important.', 9: '🔥 Completion + Release — close old chapters. Donations, forgiveness. Something new is coming.'}

_MONTH_THEMES_HI = {1: '🚀 नई शुरुआत — नया काम शुरू करने का महीना। स्वतंत्र निर्णय लें। नेटवर्किंग मजबूत करें।', 2: '🤝 धैर्य + साझेदारी — प्रतीक्षा करें और सुनें। दूसरों के साथ सहयोग करें। निर्णय थोपने से बचें।', 3: '✨ रचनात्मकता + आनंद — सामाजिक कार्यक्रम, खुद को व्यक्त करना, लेखन/शिक्षण। नेटवर्किंग फल-फूल रही है।', 4: '🛠️ कड़ी मेहनत + नींव — प्रणाली बनाएं, कागजी कार्य पूरा करें। धीमा लेकिन स्थिर।', 5: '🌪️ परिवर्तन + गति — यात्रा, नए संपर्क, अचानक अवसर। अधिकतम लचीलापन चाहिए।', 6: '❤️ प्रेम + परिवार — संबंधों में निवेश, सौंदर्य/घर परियोजनाएँ। प्रमुख घोषणाएँ संभव हैं।', 7: '🧘 चिंतन + आध्यात्मिक — अकेले समय, अध्ययन, ध्यान। बड़े निर्णय स्थगित करें।', 8: '💼 शक्ति + धन — व्यापार सौदे बंद होते हैं, प्रमोशन/अनुबंध। अनुशासन सबसे महत्वपूर्ण है।', 9: '🔥 पूर्णता + विमोचन — पुराने अध्याय बंद करें। दान, क्षमा। कुछ नया आने वाला है।'}


# Dispatch helpers ──────────────────────────────────────────────────────────
def _pick_extra(lang: str, en_dict, hi_dict, hg_dict, key, kind: str = ""):
    """Generic 3-lang lookup with HG fallback. Supports tuple keys for HG
    (which uses (kind, n) tuples) by translating to flat 'kind_n' for EN/HI."""
    lang = (lang or "hinglish").lower()
    if lang == "english":
        if isinstance(key, tuple):
            flat = f"{key[0]}_{key[1]}"
        else:
            flat = key
        v = en_dict.get(flat)
        if v is not None:
            return v
    elif lang == "hindi":
        if isinstance(key, tuple):
            flat = f"{key[0]}_{key[1]}"
        else:
            flat = key
        v = hi_dict.get(flat)
        if v is not None:
            return v
    return hg_dict.get(key)
