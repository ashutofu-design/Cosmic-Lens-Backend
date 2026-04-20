"""
numerology/meanings.py — Classical personality data for numbers 1-9.

100% deterministic lookup tables (no AI). Used by the PDF renderer to give
the report a "premium ₹500-2000" feel by adding:
  - Detailed personality narrative ("X number wale kaise hote hain")
  - Strengths / weaknesses
  - Famous personalities (social proof)
  - Career style, love style, health watch
  - Detailed remedy how-to (mantra + count + day + direction + items)
  - Best / avoid compatibility

Data compiled from classical Indian numerology (Cheiro, Sepharial,
Bansilal Jumaani, K.N. Rao corpus).
"""
from __future__ import annotations

from typing import Dict, Any


NUMBER_PERSONALITY: Dict[int, Dict[str, Any]] = {
    1: {
        "title": "The Born Leader · Sun (Surya)",
        "headline": "Independent · Authoritative · Pioneer",
        "narrative": (
            "1 number wale log paida hi leader hote hain. Inka swabhav strong, "
            "self-confident aur dominating hota hai — ye doosron ki ungli pakad ke "
            "chalna pasand nahi karte. Sun (Surya) inka ruling planet hai, isiliye "
            "inme natural authority, command aur shine karne ki tendency hoti hai. "
            "Yeh log apne field me top tak jaate hain — chahe business ho, politics "
            "ho, ya creative line. Inka ego strong hota hai, isiliye criticism "
            "bardasht nahi hoti, par jab koi inko follow karta hai to ye usko "
            "dil se support karte hain."
        ),
        "strengths": [
            "Strong willpower aur decision-making",
            "Natural leadership aur command",
            "Original thinker — naye ideas ke janak",
            "Honest aur straightforward",
            "Ambitious — bade goals set karte hain",
        ],
        "weaknesses": [
            "Ego aur stubbornness",
            "Doosron ki advice nahi sunte",
            "Authority ke saath conflict ho jata hai",
            "Critical aur impatient ho jaate hain",
        ],
        "famous": [
            "Mukesh Ambani (industrialist)",
            "Narendra Modi (PM)",
            "A.R. Rahman (composer)",
            "Steve Jobs (Apple)",
            "Walt Disney",
        ],
        "career": "Business owner, politician, CEO, defence officer, creative director, government high-post — koi bhi field jahan command karne ka mauka mile.",
        "love": "Loyal aur protective partner, par dominating ho jaate hain. Best match: 1, 2, 4, 7. Avoid: 8.",
        "health": "Heart, blood pressure, eyes aur upper back ka khayal rakhe — Sun se related body parts.",
        "best_match": [1, 2, 4, 7],
        "avoid_match": [8],
        "remedy": {
            "mantra": "Om Suryaya Namah",
            "count": "108 baar",
            "day": "Sunday subah",
            "time": "Sunrise ke baad pehle 1 ghante me",
            "direction": "East face karke",
            "items": "Tambe ka glass, gud, gehu — Sunday ko daan kare",
            "gem": "Ruby (Manik) — gold ring me right ring finger",
        },
        "daily": "Suryanamaskar 12 baar kare aur subah Sun ko jal arpan kare tambe ke lote se.",
    },
    2: {
        "title": "The Diplomat · Moon (Chandra)",
        "headline": "Sensitive · Cooperative · Intuitive",
        "narrative": (
            "2 number wale log soft, emotional aur deeply intuitive hote hain. Moon "
            "inka swami hai, isiliye inka mood pani ki tarah change hota rehta hai — "
            "kabhi bahut khush, kabhi bahut udaas. Ye natural peacemaker hain, "
            "har situation me balance lana inka talent hai. Doosron ke feelings "
            "samajhna inko aata hai isiliye counsellor, teacher, healer banne ke "
            "liye perfect hote hain. Akele rehne se inko depression aata hai — "
            "ye log relationships me hi pankhs khol pate hain. Decision lete waqt "
            "thode confused ho jate hain kyuki har angle dekhna chahte hain."
        ),
        "strengths": [
            "Bahut high emotional intelligence",
            "Diplomatic aur peace-maker",
            "Strong intuition — sapne aksar sach hote hain",
            "Loyal aur caring partner",
            "Detail-oriented aur patient",
        ],
        "weaknesses": [
            "Mood swings aur over-sensitivity",
            "Decisions me time lagate hain",
            "Confidence ki kami",
            "Emotionally manipulate ho jate hain",
        ],
        "famous": [
            "Mahatma Gandhi",
            "Rabindranath Tagore",
            "Madonna",
            "Barack Obama",
            "Shah Rukh Khan",
        ],
        "career": "Counsellor, psychologist, nurse, teacher, hotel/hospitality, diplomat, HR — jahan logon ke saath deal karna ho.",
        "love": "Romantic, devoted partner — emotional support sabse zaruri. Best match: 1, 2, 4, 7. Avoid: 5, 9.",
        "health": "Stomach, chest, fluid retention, anxiety — Moon-related issues. Pani jyada piye.",
        "best_match": [1, 2, 4, 7],
        "avoid_match": [5, 9],
        "remedy": {
            "mantra": "Om Chandraya Namah",
            "count": "108 baar",
            "day": "Monday raat ko",
            "time": "Moonrise ke time ya raat 8-10 baje",
            "direction": "North-West face karke",
            "items": "Chandi (silver), chawal, doodh, safed kapde — Monday ko daan",
            "gem": "Pearl (Moti) — silver ring me right small finger",
        },
        "daily": "Chand ko dekh ke pranam kare; safed phool ya kapur jalaye Monday ko.",
    },
    3: {
        "title": "The Optimist · Jupiter (Guru)",
        "headline": "Wise · Expressive · Lucky",
        "narrative": (
            "3 number wale log knowledge, wisdom aur expression ke master hote hain. "
            "Jupiter (Guru) inka grah hai isiliye natural teachers, philosophers aur "
            "lucky people hote hain. Inka communication zabardast hota hai — chahe "
            "writing ho, speaking ho ya teaching. Bahut optimistic aur cheerful, "
            "har samasya me solution dhundh lete hain. Spiritual interest jaldi aata "
            "hai inhe — religion, philosophy, jyotish, shastra padhna pasand karte "
            "hain. Senior log aur gurus inhe protect karte hain. Money easily aati "
            "hai, par easily chali bhi jati hai kyuki ye generous hote hain."
        ),
        "strengths": [
            "Excellent communication aur teaching skill",
            "Optimistic aur cheerful nature",
            "Lucky — Jupiter blessing always with them",
            "Wise aur philosophical thinker",
            "Generous aur giving heart",
        ],
        "weaknesses": [
            "Over-confident ho jate hain",
            "Detail miss kar dete hain",
            "Money management weak — kharch jyada",
            "Promises bahut karte hain, deliver kam",
        ],
        "famous": [
            "Amitabh Bachchan",
            "Sachin Tendulkar",
            "Albert Einstein",
            "Bill Gates",
            "Oprah Winfrey",
        ],
        "career": "Teacher, professor, writer, lawyer, judge, advisor, banker, religious leader, jyotish, motivational speaker.",
        "love": "Friendly, fun, adventurous partner. Communication strong. Best match: 1, 3, 6, 9. Avoid: 4, 8.",
        "health": "Liver, hips, weight gain, sciatica — Jupiter ke organs. Yellow food khaye.",
        "best_match": [1, 3, 6, 9],
        "avoid_match": [4, 8],
        "remedy": {
            "mantra": "Om Brihaspataye Namah",
            "count": "108 baar",
            "day": "Thursday subah",
            "time": "Subah 6-9 baje",
            "direction": "North-East face karke",
            "items": "Pita kapda, chana dal, haldi, kesar — Thursday ko mandir me daan",
            "gem": "Yellow Sapphire (Pukhraj) — gold ring me right index finger",
        },
        "daily": "Guru ya elder se aashirvad le, Thursday ko vrat rakhe ya kele ka ped puja kare.",
    },
    4: {
        "title": "The Builder · Rahu",
        "headline": "Practical · Disciplined · Unconventional",
        "narrative": (
            "4 number wale log practical, hard-working aur thode unconventional "
            "hote hain. Rahu inka swami hai isiliye inki life me sudden ups-downs "
            "aate hain — ek din top pe, doosre din neeche. Ye log foundation banate "
            "hain — koi bhi system, structure, organization khada karne me expert "
            "hain. Soch alag aur out-of-the-box hoti hai isiliye log kabhi-kabhi "
            "samajh nahi pate. Honest aur reliable hote hain par stubborn bhi. "
            "Friends kam hote hain par jo hote hain wo lifelong. Foreign connection "
            "strong — videshi land, foreign business, technology me success milti hai."
        ),
        "strengths": [
            "Bahut hard-working aur disciplined",
            "Foundation banane ka master skill",
            "Honest aur loyal",
            "Out-of-the-box thinker",
            "Foreign / technology luck strong",
        ],
        "weaknesses": [
            "Stubborn aur rigid",
            "Sudden losses ka risk",
            "Friends kam, isolation feel hota hai",
            "Anxiety aur worry jyada karte hain",
        ],
        "famous": [
            "Bill Gates",
            "Lal Bahadur Shastri",
            "Elon Musk",
            "Madhuri Dixit",
            "Steven Spielberg",
        ],
        "career": "Engineer, IT/software, technology, contractor, real estate, scientist, foreign trade, electrical, machine industry.",
        "love": "Loyal but reserved — emotions express karna mushkil. Best match: 1, 2, 7, 8. Avoid: 3, 5.",
        "health": "Nervous system, anxiety, mysterious illness, allergies — Rahu effects. Meditation kare.",
        "best_match": [1, 2, 7, 8],
        "avoid_match": [3, 5],
        "remedy": {
            "mantra": "Om Rahave Namah",
            "count": "108 baar",
            "day": "Saturday raat ko",
            "time": "Raat 10 baje ke baad",
            "direction": "South-West face karke",
            "items": "Neel kapda, urad dal, sarso ka tel — Saturday ko gareeb ko daan",
            "gem": "Hessonite (Gomedh) — silver ring me right middle finger",
        },
        "daily": "Hanuman Chalisa padhe Saturday ko; ghar me clutter na rakhe — Rahu ko gandagi se nafrat hai.",
    },
    5: {
        "title": "The Communicator · Mercury (Budh)",
        "headline": "Smart · Versatile · Restless",
        "narrative": (
            "5 number wale log sabse popular, versatile aur smart hote hain. Mercury "
            "(Budh) inka grah hai — communication, business, intelligence ka karak. "
            "Inko ek jagah baith ke kaam karna pasand nahi — travel, change, variety "
            "chahiye. Friends ki kami nahi — har caste, religion, country ke log inke "
            "saath hote hain. Sales, marketing, networking, content creation me top "
            "hote hain. Money jaldi banate hain par jaldi kharch bhi karte hain. "
            "Decision lene me bahut quick — kabhi-kabhi haste me galat bhi karte hain. "
            "Sex appeal natural hota hai. Restlessness inka biggest enemy hai."
        ),
        "strengths": [
            "Sabse high communication skill",
            "Sharp intellect aur quick thinker",
            "Versatile — kuch bhi sikh lete hain",
            "Friend banane me expert",
            "Sales / marketing / business me natural",
        ],
        "weaknesses": [
            "Restless aur unstable",
            "Patience bilkul nahi",
            "Promise tod dete hain",
            "Nervous tension aur insomnia",
        ],
        "famous": [
            "Ratan Tata",
            "Akshay Kumar",
            "Mark Zuckerberg",
            "Vivekananda",
            "Aryabhata",
        ],
        "career": "Sales, marketing, media, journalism, content creator, stock trading, consulting, travel, public relations, business.",
        "love": "Charming aur flirty — variety chahiye. Best match: 1, 5, 6, 9. Avoid: 2, 4.",
        "health": "Nervous system, skin, hands, insomnia — Mercury ke organs. Pranayam kare.",
        "best_match": [1, 5, 6, 9],
        "avoid_match": [2, 4],
        "remedy": {
            "mantra": "Om Budhaya Namah",
            "count": "108 baar",
            "day": "Wednesday subah",
            "time": "Subah 7-10 baje",
            "direction": "North face karke",
            "items": "Hara kapda, mung dal, palak, hari sabzi — Wednesday ko daan",
            "gem": "Emerald (Panna) — gold ring me right small finger",
        },
        "daily": "Wednesday ko kanyaon ko mithai khilaye; Vishnu (Krishna) ki puja kare.",
    },
    6: {
        "title": "The Lover · Venus (Shukra)",
        "headline": "Beautiful · Artistic · Family-oriented",
        "narrative": (
            "6 number wale log beauty, love aur luxury ke devoted hote hain. Venus "
            "(Shukra) inka grah hai isiliye natural attractive personality, soft "
            "voice, aur artistic sense rakhte hain. Family inke liye sab kuch hai — "
            "parents, spouse, children sab par jaan deti hain. Ghar ko sundar banana, "
            "decorate karna, party host karna pasand karte hain. Bahut romantic — "
            "love marriage ka strong yog hota hai. Comforts, fashion, jewellery, "
            "perfume, food ka shauk. Hospitality industry, fashion, beauty, music, "
            "wedding industry me top jaate hain. Lazy ho jaate hain comfort ki wajah se."
        ),
        "strengths": [
            "Naturally beautiful aur attractive",
            "Loving, caring, family-devoted",
            "Artistic — music, painting, design",
            "Diplomatic aur charming",
            "Material wealth easily attract karte hain",
        ],
        "weaknesses": [
            "Comfort-loving — lazy ho jate hain",
            "Possessive aur jealous",
            "Money waste karte hain luxuries pe",
            "Conflict avoid karne ke liye sach chupate hain",
        ],
        "famous": [
            "Aishwarya Rai Bachchan",
            "Aamir Khan",
            "Mother Teresa",
            "John Lennon",
            "Albert Einstein",
        ],
        "career": "Fashion, beauty, hotels, restaurant, interior design, jewellery, cosmetics, music, arts, wedding planner, hospitality.",
        "love": "Sabse romantic number — love-marriage ka yog. Best match: 3, 6, 9. Avoid: 7, 8.",
        "health": "Throat, kidney, reproductive system, diabetes — Venus organs. Sweets kam khaye.",
        "best_match": [3, 6, 9],
        "avoid_match": [7, 8],
        "remedy": {
            "mantra": "Om Shukraya Namah",
            "count": "108 baar",
            "day": "Friday subah",
            "time": "Subah 6-9 baje",
            "direction": "South-East face karke",
            "items": "Safed kapda, chawal, mishri, ghee — Friday ko Lakshmi mandir me",
            "gem": "Diamond (Heera) ya White Sapphire — gold ring me right middle finger",
        },
        "daily": "Friday ko Lakshmi puja, sundar safed phool ghar me rakhe; partner ya maa ko gift de.",
    },
    7: {
        "title": "The Mystic · Ketu",
        "headline": "Spiritual · Philosophical · Mysterious",
        "narrative": (
            "7 number wale log sabse spiritual aur mysterious hote hain. Ketu inka "
            "swami hai — moksha-karak. Ye log alag duniya me jeete hain — books, "
            "research, meditation, philosophy, occult inka favourite area hota hai. "
            "Crowd se door rehte hain, akele me peace milti hai. Bahut deep thinker — "
            "surface pe nahi rukte, har cheez ki root cause dhundhte hain. Healing, "
            "astrology, spiritual teaching, research, writing me top jaate hain. "
            "Money inke liye motivation nahi par fame easily mil jati hai. "
            "Marriage me delays ya complications aate hain. Sapne aur intuition "
            "bahut strong — premonitions hote hain."
        ),
        "strengths": [
            "Sabse spiritual aur intuitive",
            "Deep researcher aur thinker",
            "Original creative — unique work karte hain",
            "Detached — material loss jhel lete hain",
            "Healing aur counselling power natural",
        ],
        "weaknesses": [
            "Loner — relationships me distance",
            "Marriage me delay/complications",
            "Depression ya mood-darkness ka risk",
            "Practical/financial decisions weak",
        ],
        "famous": [
            "Princess Diana",
            "Marilyn Monroe",
            "Sri Aurobindo",
            "Swami Vivekananda",
            "Stephen Hawking",
        ],
        "career": "Research, writing, occult/jyotish, healing, psychology, IT/coding, monk/saint, scientist, investigator.",
        "love": "Reserved, deep partner — surface se ghazab nahi hote. Best match: 1, 2, 4, 7. Avoid: 6, 9.",
        "health": "Mental health, joint pain, mysterious illness, vata-related — Ketu effects. Yoga zaruri.",
        "best_match": [1, 2, 4, 7],
        "avoid_match": [6, 9],
        "remedy": {
            "mantra": "Om Ketave Namah",
            "count": "108 baar",
            "day": "Tuesday raat ko",
            "time": "Raat 8 baje ke baad",
            "direction": "South face karke",
            "items": "Mishrit kapda, kala til, kambal — Tuesday ko sadhu ko daan",
            "gem": "Cat's Eye (Lehsunia) — silver ring me right middle finger",
        },
        "daily": "Ganesh aur Hanuman ki puja, meditation 20 min daily, kutta ko khana khilaye.",
    },
    8: {
        "title": "The Karmic · Saturn (Shani)",
        "headline": "Ambitious · Disciplined · Karma-driven",
        "narrative": (
            "8 number wale log sabse misunderstood hote hain — par sabse powerful "
            "bhi. Saturn (Shani) inka swami hai — karma ka raja. Inki life me bahut "
            "struggle hota hai, par jab success aati hai to permanent hoti hai. "
            "Bahut serious, disciplined aur ambitious. Kabhi shortcut nahi lete — "
            "sab kuch mehnat se kamana pasand hai. Authority position me jaate hain "
            "— politics, judiciary, large business, mining, oil, real estate. Older "
            "logo se inhe support milti hai. Middle age ke baad real success aati "
            "hai. Marriage me struggle, par loyal partner. Material aur spiritual "
            "dono extreme me jaa sakte hain."
        ),
        "strengths": [
            "Iron willpower aur discipline",
            "Material success ka master",
            "Honest, just aur fair",
            "Late-life me bahut bada uthna",
            "Saturn ka direct blessing — karma-shudhi",
        ],
        "weaknesses": [
            "Bachpan aur youth me struggle",
            "Misunderstood by friends/family",
            "Pessimistic ho jate hain",
            "Marriage delays aur problems",
        ],
        "famous": [
            "Dhirubhai Ambani",
            "Indira Gandhi",
            "Pablo Picasso",
            "Nelson Mandela",
            "Lata Mangeshkar",
        ],
        "career": "Politics, judiciary, mining, oil, real estate, large industry, contractor, government high-post, philosopher, monk.",
        "love": "Loyal but emotionally distant — long-term commitment strong. Best match: 4, 5, 6, 8. Avoid: 1, 2.",
        "health": "Bones, joints, knees, depression, chronic illness — Saturn effects. Tel ki maalish kare.",
        "best_match": [4, 5, 6, 8],
        "avoid_match": [1, 2],
        "remedy": {
            "mantra": "Om Shanaye Namah",
            "count": "108 baar",
            "day": "Saturday subah",
            "time": "Sunset ke pehle ya raat 8 baje",
            "direction": "West face karke",
            "items": "Kala kapda, kala til, sarso tel, urad dal — Saturday ko gareeb/labour ko daan",
            "gem": "Blue Sapphire (Neelam) — silver ring me right middle finger (test 3 din)",
        },
        "daily": "Hanuman Chalisa Saturday ko, Shani Stotra padhe; servant aur labour ko respect de.",
    },
    9: {
        "title": "The Warrior · Mars (Mangal)",
        "headline": "Brave · Energetic · Fierce",
        "narrative": (
            "9 number wale log sabse energetic, brave aur action-oriented hote hain. "
            "Mars (Mangal) inka swami hai — yodha, senapati ka karak. Bahut courage "
            "aur fighter spirit hota hai — zindagi me chunautiyon se darte nahi. "
            "Defence, sports, surgery, engineering, fire-related fields me natural "
            "success. Anger inka biggest dushman hai — sambhalna seekhe. Honest, "
            "outspoken, aur direct — bina politics ke baat karte hain. Family ke "
            "liye sab kuch chhod sakte hain — ultra-protective. Marriage me Mangal "
            "dosha ki problem aati hai — jaldi kundli match karwaye. Foreign land "
            "me settle hone ka yog. Land, property aur immovable wealth strong."
        ),
        "strengths": [
            "Sabse high energy aur stamina",
            "Brave aur fearless",
            "Honest aur direct",
            "Family-protective warrior",
            "Sports / defence me natural",
        ],
        "weaknesses": [
            "Anger aur impulsiveness",
            "Aggression ka over-show",
            "Mangal dosha — marriage delays",
            "Accidents aur injury ka risk",
        ],
        "famous": [
            "Sardar Patel",
            "Mahendra Singh Dhoni",
            "Hrithik Roshan",
            "Mukesh Khanna",
            "Mike Tyson",
        ],
        "career": "Defence (army/navy/airforce), police, surgery, engineering, sports, real estate, fire-fighting, contractor, builder.",
        "love": "Passionate, intense, protective — anger control jaruri. Best match: 3, 5, 6, 9. Avoid: 2, 7.",
        "health": "Blood pressure, accidents, fever, head injuries, surgery — Mars effects. Workout kare.",
        "best_match": [3, 5, 6, 9],
        "avoid_match": [2, 7],
        "remedy": {
            "mantra": "Om Mangalaya Namah",
            "count": "108 baar",
            "day": "Tuesday subah",
            "time": "Subah 6-9 baje",
            "direction": "South face karke",
            "items": "Lal kapda, masoor dal, gud, tambe ka item — Tuesday ko Hanuman mandir",
            "gem": "Red Coral (Moonga) — gold/copper ring me right ring finger",
        },
        "daily": "Hanuman Chalisa Tuesday ko, Sundarkand padhe; physical workout 30 min daily.",
    },
}


# Single-digit fallback meanings for Cheiro compounds beyond the 52-table.
SINGLE_DIGIT_SHORT: Dict[int, str] = {
    1: "Sun energy — leadership, recognition, fresh start; favourable for action.",
    2: "Moon energy — partnership, sensitivity, slow gains; favours diplomacy.",
    3: "Jupiter energy — wisdom, expansion, teaching, money flow; very favourable.",
    4: "Rahu energy — sudden change, hard work, foreign luck; mixed but karmically rewarding.",
    5: "Mercury energy — business, communication, travel, popularity; favourable.",
    6: "Venus energy — love, beauty, comforts, creative success; very favourable.",
    7: "Ketu energy — spiritual depth, research, isolation; mixed but mystical.",
    8: "Saturn energy — discipline, karma, late but lasting success; cautious favourable.",
    9: "Mars energy — courage, action, victory after struggle; favourable for warriors.",
}


def get_personality(num: int) -> Dict[str, Any] | None:
    """Return the full personality block for a number 1-9, else None."""
    try:
        return NUMBER_PERSONALITY.get(int(num))
    except (TypeError, ValueError):
        return None


def cheiro_compound_fallback(compound: int) -> str:
    """When a compound number is not in the 52-table, derive a meaningful
    fallback by reducing to single digit and citing its planetary energy.
    """
    try:
        n = int(compound)
    except (TypeError, ValueError):
        return ""
    # Reduce to single digit
    while n > 9:
        n = sum(int(d) for d in str(n))
    short = SINGLE_DIGIT_SHORT.get(n, "")
    return f"reduces to {n} — {short}" if short else f"reduces to {n}."
