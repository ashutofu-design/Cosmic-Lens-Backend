"""100 real-life foreign education / visa / PR / settlement questions — routing audit."""
from __future__ import annotations

FE = frozenset({"foreign_education_timing"})
ED = frozenset({"education_timing"})
CA = frozenset({"career_timing"})
FI = frozenset({"finance_timing"})
TR = frozenset({"travel_timing"})
MA = frozenset({"marriage_timing"})
LLM = frozenset({"llm"})

FE_ED = FE | ED
FE_CA = FE | CA
FE_FI = FE | FI
FE_TR = FE | TR
FE_MA = FE | MA
LLM_FE = LLM | FE
LLM_CA = LLM | CA

QUESTIONS: list[tuple[str, frozenset[str], str]] = [
    # ── 1. Higher Studies & College Admission (20) ───────────────────────────
    (
        "Mera manpasand college ya university me admission isi saal ho jayega ya saal barbad hoga?",
        FE,
        "admission",
    ),
    (
        "Kya mujhe top-tier college milega ya kisi average institute se hi degree karni padegi?",
        FE_ED,
        "admission",
    ),
    (
        "College admission ki shortlist me mera naam kab tak aayega?",
        FE,
        "admission",
    ),
    (
        "Mujhe graduation/post-graduation ke liye apne hometown se door kisi doosre state me jaana padega kya?",
        FE_ED,
        "admission",
    ),
    (
        "Kya mujhe higher education ke liye scholarship milegi? Kab tak sanction hogi?",
        FE,
        "admission",
    ),
    (
        "Stream ya subject selection (Science, Commerce, Arts/Tech) ko lekar jo confusion hai, woh kab tak door hoga?",
        FE_ED,
        "admission",
    ),
    (
        "Kya dasha aisi chal rahi hai ki mujhe padhai ke liye bank se education loan lena padega? Loan kab pass hoga?",
        FE_FI,
        "admission",
    ),
    (
        "Padhai ke beech me jo baar-baar break ya rukawat (gap year) aa rahi hai, woh kab khatam hogi?",
        FE,
        "admission",
    ),
    (
        "Kya mujhe PhD ya Research work ke liye kisi bade professor ka guidance aur approval kab tak milega?",
        FE,
        "admission",
    ),
    (
        "Kya main apni degree beech me hi chhod doonga ya yeh safely poori ho jayegi?",
        FE_ED,
        "admission",
    ),
    (
        "College badalne ka yoga kab ban raha hai? Kya college change karna mere liye lucky rahega?",
        FE,
        "admission",
    ),
    (
        "Kya padhai ke sath-sath mujhe part-time job ka mauka isi semester me mil jayega?",
        FE_CA,
        "admission",
    ),
    (
        "College ke dosto ya mahaul ki vajah se meri padhai kharab toh nahi hogi na?",
        LLM_FE,
        "admission",
    ),
    (
        "Meri kundli ka Rahu active hai, toh kya mujhe koi naya ya unconventional course (jaise AI, Data, UI/UX) chunna chahiye?",
        LLM_FE,
        "admission",
    ),
    (
        "College ki counseling list me mera naam pehli baar me aayega ya wait karna padega?",
        FE_ED,
        "admission",
    ),
    (
        "Padhai me dhyan (concentration) lagna kab se shuru hoga? Abhi bohot distraction chal raha hai.",
        FE_ED,
        "admission",
    ),
    (
        "Kya mujhe campus placement ke zariye college khatam hote hi job mil jayegi?",
        FE_CA,
        "admission",
    ),
    (
        "Merit-basis par admission kab tak final hoga?",
        FE,
        "admission",
    ),
    (
        "Kya college administration ya documents me koi dikkat aane wali hai admission ke time?",
        LLM_FE,
        "admission",
    ),
    (
        "College me admission lene ke liye sabse shubh mahina aur date kaun si ban rahi hai?",
        FE,
        "admission",
    ),
    # ── 2. Competitive Exams, Selection & Job Exams (20) ─────────────────────
    (
        "Jis competitive exam (IIT, NEET, UPSC, Bank PO, GMAT, IELTS) ki taiyari kar raha hoon, uska result kab tak aayega?",
        FE_CA,
        "exam_selection",
    ),
    (
        "Kya mera pehle attempt me selection ho jayega ya mujhe dobara exam dena padega?",
        FE_ED,
        "exam_selection",
    ),
    (
        "Cut-off clear karne me kitne nambaron ki kami reh sakti hai aur yeh luck kab paltega?",
        FE,
        "exam_selection",
    ),
    (
        "Government job ke competitive exam me interview round kab tak hoga aur clear hoga kya?",
        FE_CA,
        "exam_selection",
    ),
    (
        "Sarkari naukri (Govt Job) ka joining letter mujhe kab tak milega?",
        CA,
        "exam_selection",
    ),
    (
        "Exam ke darr (exam anxiety) se mujhe kab tak mukti milegi? Padhne ke baad sab bhool jata hoon.",
        FE,
        "exam_selection",
    ),
    (
        "Kya mujhe coaching badalni chahiye? Naye teacher ke aane se selection ka yoga banega kya?",
        LLM_FE,
        "exam_selection",
    ),
    (
        "Answer key aane ke baad kya mere marks badhenge ya kam honge?",
        LLM,
        "exam_selection",
    ),
    (
        "Kya exam me koi legal locha, paper leak ya postpone hone ke chances hain?",
        LLM,
        "exam_selection",
    ),
    (
        "Rank list me meri position top 100 ya top 500 me kab tak aane ka yoga hai?",
        FE,
        "exam_selection",
    ),
    (
        "Agar is exam me selection nahi hua, toh kya mujhe backup career option par turant shift ho jana chahiye?",
        LLM_CA,
        "exam_selection",
    ),
    (
        "Competitive exam clear karne ka sabse strong dasha-period kab active ho raha hai?",
        FE,
        "exam_selection",
    ),
    (
        "Dusron ke muqable meri taiyari (preparation) sahi direction me kab pahuchegi?",
        FE,
        "exam_selection",
    ),
    (
        "Kya mujhe technical exam me zyada fayda milega ya management/administrative exam me?",
        LLM,
        "exam_selection",
    ),
    (
        "Ghar ka tanaav aur financial problem meri taiyari ko kab tak mutasir (affect) karti rahegi?",
        FE_FI,
        "exam_selection",
    ),
    (
        "Kya mujhe kisi competitive exam ke liye re-evaluation ya re-checking ka form bharna chahiye?",
        LLM,
        "exam_selection",
    ),
    (
        "Final selection list aane me kitne mahino ka delay aur dikh raha hai?",
        FE,
        "exam_selection",
    ),
    (
        "Kya dushman ya baki competitors mere khilaf koi conspiracy karenge exam center ya court me?",
        LLM,
        "exam_selection",
    ),
    (
        "Mujhe apni mehnat ka phal (reward) 6th ya 10th house ke active hote hi kab milega?",
        FE_CA | LLM,
        "exam_selection",
    ),
    (
        "Kis mahine me diya gaya exam mere career ko hamesha ke liye badal dega?",
        FE_ED | FE_CA,
        "exam_selection",
    ),
    # ── 3. Foreign Visa & Approval Timing (20) ───────────────────────────────
    (
        "Mera student visa/work visa kab tak approve hokar mere haath me aayega?",
        FE,
        "visa",
    ),
    (
        "Visa interview ki date kab ki milegi aur interview clear hoga ya nahi?",
        FE,
        "visa",
    ),
    (
        "Kya mera visa pehli baar me hi reject ho jayega? Agar haan, toh re-apply kab karun?",
        FE,
        "visa",
    ),
    (
        "Visa processing me jo delay chal raha hai, woh administrative check kab tak clear hoga?",
        FE,
        "visa",
    ),
    (
        "Kya visa ke documents ya bank balance (funds show karne me) koi fraud ya error pakda jayega?",
        LLM_FE,
        "visa",
    ),
    (
        "Tourist visa par jaakar use work visa me convert karane ka sahi samay kab banega?",
        FE,
        "visa",
    ),
    (
        "Sponsor karne wale (company/relative) ki taraf se visa papers kab tak bhej diye jayenge?",
        FE,
        "visa",
    ),
    (
        "Biometrics aur medical test ke liye appointment kab tak final hogi?",
        FE,
        "visa",
    ),
    (
        "Kya embassy se mujhe koi query ya additional document submit karne ka mail aayega?",
        FE_ED,
        "visa",
    ),
    (
        "Passport ghum hone ya passport renewal me koi delay hone ka yoga toh nahi hai na?",
        FE,
        "visa",
    ),
    (
        "Agent mujhe dhoka toh nahi de raha? Mera visa sach me apply hua hai ya nahi?",
        LLM,
        "visa",
    ),
    (
        "Flight ki tickets book karne ka sabse shubh aur safe mahurat kab ka nikal raha hai?",
        FE_TR,
        "visa",
    ),
    (
        "Kya visa reject hone par mera poora paisa (fees) doob jayega?",
        LLM_FE,
        "visa",
    ),
    (
        "Spousal visa (wife/husband ke sath) apply karne par kab tak approval milta hai?",
        FE,
        "visa",
    ),
    (
        "Business visa ya investor visa ke zariye videsh jaane ka mauka kab tak banega?",
        FE,
        "visa",
    ),
    (
        "Rahu ki antardasha me visa milne ke kitne percent chances hain?",
        FE,
        "visa",
    ),
    (
        "Embassy ke chakkar kaatna kab band hoga aur passport par visa stamp kab lagega?",
        FE,
        "visa",
    ),
    (
        "Kya visa clearance ke liye mujhe kisi sarkari sifarish ya political help ki zaroorat padegi?",
        LLM_FE,
        "visa",
    ),
    (
        "Immigration center (airport) par mujhe roka ya pareshan toh nahi kiya jayega na?",
        LLM | MA | FE,
        "visa",
    ),
    (
        "Kis specific date ya week me mera visa status online 'Approved' dikhayega?",
        FE,
        "visa",
    ),
    # ── 4. PR (Permanent Residency) & Green Card Timing (20) ───────────────────
    (
        "Mujhe is desh ki PR (Permanent Residency) ya Green Card kab tak milega?",
        FE,
        "pr_residency",
    ),
    (
        "PR points (CRS score) badhne ka yoga kab ban raha hai? Score kab tak clear hoga?",
        FE,
        "pr_residency",
    ),
    (
        "Kya PR ke chakkar me mujhe apna employer (company) badalna padega? Kab badlun?",
        FE,
        "pr_residency",
    ),
    (
        "Green Card ki priority date kab tak current hogi? Kitne saal ka intezar aur hai?",
        FE,
        "pr_residency",
    ),
    (
        "PR file karne ke baad kya mujhe back-home (India) aane ka mauka milega ya fasa rahunga?",
        FE,
        "pr_residency",
    ),
    (
        "Kya shaadi (marriage with a citizen) ke zariye mujhe jaldi PR milne ka yoga hai?",
        FE_MA,
        "pr_residency",
    ),
    (
        "PR application me koi legal objection ya query (RFE - Request for Evidence) kab tak aayegi?",
        FE,
        "pr_residency",
    ),
    (
        "H1B visa se PR/Green Card ka process kab shuru karwana sahi rahega?",
        FE,
        "pr_residency",
    ),
    (
        "Kya meri company meri PR file karne ke liye raazi ho jayegi ya mana karegi?",
        FE,
        "pr_residency",
    ),
    (
        "PR na milne ki vajah se kya mujhe wapas apne desh (India) lautna padega?",
        FE,
        "pr_residency",
    ),
    (
        "Citizenship (videshi nagrikta) ke liye test aur oath (shapath) kab tak hogi?",
        FE,
        "pr_residency",
    ),
    (
        "Kya dasha ke anusar PR milte hi meri financial growth double ho jayegi?",
        LLM_FE,
        "pr_residency",
    ),
    (
        "PR milne ke baad kya main apni family (parents) ko bhi wahan permanent bula paunga?",
        FE,
        "pr_residency",
    ),
    (
        "Green Card milne me jo lagatar rukawat aa rahi hai, kya woh kisi grah dosh (jaise Shani) ki vajah se hai?",
        LLM_FE,
        "pr_residency",
    ),
    (
        "Kya mujhe PR ke liye kisi doosre province ya state me shift hona padega jahan points kam chahiye?",
        FE,
        "pr_residency",
    ),
    (
        "File processing ka status 'In Progress' se 'Decision Made' kab tak hoga?",
        FE,
        "pr_residency",
    ),
    (
        "Kya mujhe PR lene ke liye koi bada investment ya business option choose karna padega?",
        LLM_FE,
        "pr_residency",
    ),
    (
        "Meri kundli ka 9th aur 12th lord kab ek sath gochar me aakar PR approve karwayenge?",
        FE,
        "pr_residency",
    ),
    (
        "PR card physically mere ghar ke address par kis mahine tak deliver ho jayega?",
        FE,
        "pr_residency",
    ),
    (
        "PR milne ka sabse safe aur confirmed period meri life me kaun sa hai?",
        FE,
        "pr_residency",
    ),
    # ── 5. Permanent Foreign Settlement (20) ───────────────────────────────────
    (
        "Kya main hamesha ke liye videsh (foreign) me settle ho jaunga ya aakhiri me India hi wapas aana padega?",
        FE,
        "settlement",
    ),
    (
        "Videsh me khud ka ghar khareedne aur wahan settle hone ka yoga kab ban raha hai?",
        FE,
        "settlement",
    ),
    (
        "Kya videsh jaate hi meri kismat chamkegi ya shuruat me bohot zyada struggle (recession/jobs ki dikkat) rahega?",
        FE,
        "settlement",
    ),
    (
        "Mujhe kis desh me settlement milega (USA, Canada, UK, Australia, Europe ya Gulf)?",
        FE,
        "settlement",
    ),
    (
        "Padhai khatam hone ke baad wahan work-permit kab tak extend hoga?",
        FE,
        "settlement",
    ),
    (
        "Kya mujhe foreign land par apna business shuru karke settle hona chahiye ya job hi sahi hai?",
        LLM,
        "settlement",
    ),
    (
        "Videsh me settlement ke baad kya meri shadi kisi videshi (foreigner) se hi hone ka yoga hai?",
        FE_MA,
        "settlement",
    ),
    (
        "Ghar se door (foreign me) rehne par jo akelapan aur depression hota hai, usse kab tak rahat milegi?",
        FE | TR,
        "settlement",
    ),
    (
        "Kya videsh me settlement ke baad mujhe parivaar se doori ka dukh hamesha jhelna padega?",
        LLM_FE,
        "settlement",
    ),
    (
        "Meri kundli me 12th house (foreign) ka lord strong hai ya 4th house (motherland) ka? Settle kahan hoon?",
        LLM_FE,
        "settlement",
    ),
    (
        "Kya mujhe foreign settlement ke baad wahan ki sarkari naukri ya badha pad (position) milega?",
        FE_CA,
        "settlement",
    ),
    (
        "Videsh me settle hone ke baad kya mera koi bada accident ya health issue ka yoga toh nahi chal raha?",
        LLM,
        "settlement",
    ),
    (
        "Videsh me mere naye dosto aur network kab tak banega jo mujhe settle hone me madad karega?",
        FE,
        "settlement",
    ),
    (
        "Kya mujhe foreign me settle hone ke liye apna dharam ya lifestyle poori tarah badalna padega?",
        LLM_FE,
        "settlement",
    ),
    (
        "India ki saari assets aur property bechkar foreign me invest karne ka sahi samay kab hai?",
        FE_FI,
        "settlement",
    ),
    (
        "Rahu aur Guru ka double transit mere foreign settlement ko kab trigger kar raha hai?",
        FE,
        "settlement",
    ),
    (
        "Kya videsh me settlement ke baad mujhe kisi bade naye scam ya tax fraud me fasaaya ja sakta hai?",
        LLM,
        "settlement",
    ),
    (
        "Mujhe videsh me hamesha rent ke ghar me rehna padega ya mera khud ka bada aashiyan hoga?",
        LLM_FE,
        "settlement",
    ),
    (
        "Videsh me permanent rehne ke liye meri bhasha (language skills) kab tak improve ho jayegi?",
        FE,
        "settlement",
    ),
    (
        "Meri life ka woh kaun sa turning point saal (year) hoga jab main poori tarah foreign citizen ban jaunga?",
        FE,
        "settlement",
    ),
]

assert len(QUESTIONS) == 100
