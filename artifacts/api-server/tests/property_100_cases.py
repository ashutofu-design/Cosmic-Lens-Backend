"""100 real-life Hindi/Hinglish property/vehicle questions — routing audit cases."""
from __future__ import annotations

PT = frozenset({"property_timing"})
VT = frozenset({"vehicle_timing"})
VS = frozenset({"vehicle_static"})
PS = frozenset({"property_static"})
LLM = frozenset({"llm"})
LIT = frozenset({"litigation"})
FIN = frozenset({"finance_timing"})

PT_LIT = PT | LIT
PT_FIN = PT | FIN
PT_PS = PT | PS
PS_ONLY = PS
VS_ONLY = VS
VT_VS = VT | VS
PS_VS = PS | VS
LIT_PT = LIT | PT

QUESTIONS: list[tuple[str, frozenset[str]]] = [
    # ── 1. Khud Ka Ghar & Registry (30) ─────────────────────────────────────
    (
        "Mera khud ka ghar isi saal banega ya agle saal tak baat talegi?",
        PT,
    ),
    (
        "Kya mujhe bana-banaya flat (ready-to-move) lena chahiye ya khud zameen lekar construction karwaun?",
        PS_ONLY,
    ),
    (
        "Mere naam par property registry karwana shubh rahega ya meri wife/parents ke naam par?",
        PT_PS,
    ),
    (
        "Builder ne possession rok rakha hai, mujhe ghar ki chaabi kab tak milegi?",
        PT,
    ),
    (
        "Ghar lene ke liye bank loan kab tak sanction hoga? Kahin loan reject toh nahi ho jayega?",
        PT_FIN,
    ),
    (
        "Kya ghar lene ke chakkar me main bohot bade karze (debt trap) me toh nahi phas jaunga?",
        PS_ONLY,
    ),
    (
        "Registry ke paper me koi fraud ya legal locha toh nahi ho jayega na?",
        PS_ONLY,
    ),
    (
        "Kya mujhe sarkari housing scheme (jaise DDA, MHADA, Awas Yojna) me ghar milega?",
        PT_PS,
    ),
    (
        "Ghar ka kaam shuru karwate hi ruk jata hai, yeh construction bina rukawat ke kab poora hoga?",
        PT,
    ),
    (
        "Kya mujhe apna janam-sthaan (hometown) chhodkar kisi doosre shehar me ghar khareedna padega?",
        PT_PS,
    ),
    (
        "Kya mujhe out of station ya foreign country me property lene ka mauka milega?",
        PT_PS,
    ),
    (
        "Mera khud ka makaan 30s me banega, 40s me ya retirement ke baad?",
        PT,
    ),
    (
        "Mere paas paise aate hain par property me invest nahi ho paate, yeh paisa zameen me kab badlega?",
        PT_FIN,
    ),
    (
        "Kya mujhe commercial property (shop/office) pehle leni chahiye ya residential (makaan)?",
        PT_PS,
    ),
    (
        "Kya mere jivan me ek se zyada ghar ya properties banane ka yoga hai?",
        PS_ONLY,
    ),
    (
        "Jo naya ghar main le raha hoon, kya woh mere liye lucky rahega ya usme vastu dosh hoga?",
        PT_PS,
    ),
    (
        "Ghar ka token money (bayaana) de diya hai, par deal beech me tootne ke chances toh nahi hain?",
        PS_ONLY,
    ),
    (
        "Kya mujhe kisi disputed property ko saste me khareedna chahiye? Fayda hoga ya nuksan?",
        PT_PS,
    ),
    (
        "Mere paas kab tak itna cash liquid ho jayega ki main down-payment kar sakun?",
        PT_FIN,
    ),
    (
        "Ghar lene ka sabse shubh mahina (months) mere liye kaun sa rahega?",
        PT_PS,
    ),
    (
        "Kya mujhe apni sasural ki taraf se ya dowry me koi property/flat milega?",
        PT_PS,
    ),
    (
        "Joint property me mera naam aayega ya mujhe akele hi mehnat karni padegi?",
        PT_PS,
    ),
    (
        "Kya mujhe koi aisa ghar milega jiska loan adha chuka hua ho (resale property)?",
        PT_PS,
    ),
    (
        "Ghar ke renovation/repairing me mera kitna kharcha hone wala hai aur kab hoga?",
        PT,
    ),
    (
        "Kya main khud ke dum par ghar banaunga ya mujhe family se financial help leni padegi?",
        PS_ONLY,
    ),
    (
        "Mere 4th house me paap grah hain, kya mera kabhi khud ka makaan ho bhi payega ya hamesha rent par rahunga?",
        PT_PS,
    ),
    (
        "Naye ghar me griha pravesh karne ka sahi samay kab ban raha hai?",
        PT,
    ),
    (
        "Kya mujhe naya ghar khareedne ke liye apni koi purani asset ya gold bechna padega?",
        PS_ONLY,
    ),
    (
        "Broker mujhe dhoka toh nahi de raha? Property ke rates sahi hain ya over-priced hain?",
        PT_PS,
    ),
    (
        "Kis rashi ya nakshatra ke chalte meri property lene ki deal final phase me pahuchegi?",
        PT,
    ),
    # ── 2. Nayi Gaadi (25) ────────────────────────────────────────────────────
    (
        "Main apni pehli car/bike kab tak khareed paunga?",
        VT,
    ),
    (
        "Kya mujhe brand new car leni chahiye ya shuruat me second-hand gaadi se kaam chalana chahiye?",
        VS_ONLY,
    ),
    (
        "Gaadi ka loan easily pass ho jayega ya down payment zyada deni padegi?",
        VS_ONLY,
    ),
    (
        "Mere liye car ka kaun sa colour (safed, kala, lal, silver) sabs shubh rahega?",
        VS_ONLY,
    ),
    (
        "Kya gaadi lene ke turant baad mera koi bada accident ya nuksan (loss) toh nahi likha?",
        VS_ONLY,
    ),
    (
        "Kya yeh gaadi mere business ya job me growth lekar aayegi?",
        VS_ONLY,
    ),
    (
        "Kya mujhe luxury car (Audi, BMW etc.) ka sukh milega ya normal budget car hi rahegi?",
        VS_ONLY,
    ),
    (
        "Meri gaadi baar-baar kharab hoti hai aur maintenance me paisa doobta hai, yeh kharcha kab rukega?",
        VT,
    ),
    (
        "Kya mujhe gaadi apne naam par leni chahiye ya business/company ke naam par tax bachane ke liye?",
        VS_ONLY,
    ),
    (
        "Car delivery lene ke liye sabse best din aur mahurat kaun sa rahega?",
        VS_ONLY,
    ),
    (
        "Kya gaadi lene ke baad mujhe koi legal ya challan/police ka chakkar dekhna padega?",
        VS_ONLY,
    ),
    (
        "Kya mujhe commercial vehicle (truck, taxi, loader) ka business shuru karna chahiye?",
        VS_ONLY,
    ),
    (
        "Gaadi khareedne ke liye kaun sa festival (Diwali, Dhanteras, Navratri) mere liye sabse best rahega?",
        VS_ONLY,
    ),
    (
        "Kya meri car chori hone ya kho jaane ka koi yoga toh nahi chal raha kundli me?",
        VS_ONLY,
    ),
    (
        "Meri pehli gaadi 2-wheeler hogi ya seedhe 4-wheeler?",
        VS_ONLY,
    ),
    (
        "Kya mujhe driving seekhne me koi dikkat aayegi ya main asani se chala loonga?",
        VS_ONLY,
    ),
    (
        "Kya mujhe apne shauk ke liye gaadi leni chahiye ya abhi ruk kar paise bachaane chahiye?",
        VS_ONLY,
    ),
    (
        "Gaadi lene ka kharcha kahin mere bache ya pariwar ke doosre zaroori kamo ko toh nahi rokega?",
        VS_ONLY,
    ),
    (
        "Kya mujhe VIP number (fancy plate) ke liye extra kharcha karna chahiye? Woh mere liye lucky hai?",
        VS_ONLY,
    ),
    (
        "Meri kundli me Shukra kharab hai, toh kya gaadi hamesha kisi aur ke naam par hi chalani padegi?",
        VS_ONLY,
    ),
    (
        "Gaadi ka insurance claim lene ki naubat toh nahi aayegi na?",
        VS_ONLY,
    ),
    (
        "Kya mujhe electric vehicle (EV) leni chahiye ya petrol/diesel hi sahi rahegi?",
        VS_ONLY,
    ),
    (
        "Gaadi khareedne ke kitne mahine pehle se mujhe investments shuru karni chahiye?",
        VS_ONLY,
    ),
    (
        "Kya mere paas ek se zyada gaadiyon ka sukh hoga?",
        VS_ONLY,
    ),
    (
        "Gaadi lekar lambi yatra (road trip) par jaane ka sahi samay kab aayega?",
        VT | VS,
    ),
    # ── 3. Pustaini Zameen & Vivaad (25) ─────────────────────────────────────
    (
        "Pustaini zameen (ancestral property) par jo court case chal raha hai, uska faisla kab tak aayega?",
        PT_LIT,
    ),
    (
        "Court case ka faisla mere hit (favour) me aayega ya dushman/bhai baazi maar lenge?",
        LIT_PT,
    ),
    (
        "Kya zameen ke vivaad ko court ke bahar (out-of-court settlement) suljhana sahi rahega?",
        PS_ONLY,
    ),
    (
        "Mere bhai/pariwar wale mera hissa dene se mukar rahe hain, kya mujhe mera haq kabhi milega?",
        PT_LIT,
    ),
    (
        "Ancestral property me se mujhe kitna percent hissa milega (adha ya thoda sa)?",
        PT_PS,
    ),
    (
        "Kya is zameen ke chakar me meri jaan ko khatra ya koi bada jhagda/maar-peet toh nahi hogi?",
        PT_PS,
    ),
    (
        "Parivaar ke log jo dhoka de rahe hain, unka asli chehra kab tak samne aayega?",
        PT_LIT,
    ),
    (
        "Kya mujhe pustaini zameen bech kar shehar me naya ghar le lena chahiye?",
        PS_ONLY,
    ),
    (
        "Zameen par kisi ne najayaz kabza (illegal encroachment) kar rakha hai, woh kabza kab khali hoga?",
        PT,
    ),
    (
        "Kya court case me mera bohot zyada paisa (vakeel ki fees me) barbad hone wala hai?",
        LIT_PT,
    ),
    (
        "Dada-dadi ya nana-nani ki vasiyat (Will) me mera naam hai ya nahi?",
        PS_ONLY,
    ),
    (
        "Kya gair-kanooni tarike se banayi gayi vasiyat ko main court me challenge kar ke jeet sakta hoon?",
        PS_ONLY,
    ),
    (
        "Is zameen ka vivaad khatam hone me kitne saal aur lagenge (1 saal, 5 saal ya isse zyada)?",
        PT,
    ),
    (
        "Kya mujhe is mamle me sarkari afsaron ya police ki madad milegi ya woh bhi bike hue hain?",
        PS_ONLY,
    ),
    (
        "Pustaini zameen par koi purana karza (mortgage) hai, use chukane ki zimmedari kiski hogi?",
        PT_PS,
    ),
    (
        "Kya zameen milne ke baad wahan par koi construction karna sahi rahega ya use bech dena chahiye?",
        PS_ONLY,
    ),
    (
        "Pariwar ka kaun sa sadasya (relative) is poore vivaad ki asli jad (root cause) hai?",
        PS_ONLY,
    ),
    (
        "Kya is disputed zameen par koi shani ya rahu ka dosh (pitra dosh) toh nahi hai?",
        PS_ONLY,
    ),
    (
        "Case ke chalte jo mansik tanaav (mental stress) chal raha hai, usse kab tak rahat milegi?",
        PT_LIT,
    ),
    (
        "Kya mujhe vakeel badalna chahiye? Naya vakeel mujhe case jita payega ya nahi?",
        PS_ONLY | LIT,
    ),
    (
        "Ghar ke bade-budaarg is jhagde ko kab tak aapas me baithkar suljha payenge?",
        PT,
    ),
    (
        "Kya mujhe court se koi stay order (injunction) mil payega?",
        LIT_PT,
    ),
    (
        "Zameen ke papers/documents ghum ho gaye hain, kya woh dobara mil payenge?",
        PT_PS,
    ),
    (
        "Kya dushman thak-haar kar khud mere paas compromise karne aayega?",
        PT_LIT | PS_ONLY,
    ),
    (
        "Meri kundli ka kaun sa grah is property dispute ko badha raha hai aur uski shanti kab hogi?",
        PT,
    ),
    # ── 4. Purana Ghar/Property Bechna (20) ───────────────────────────────────
    (
        "Mera purana ghar/plot pichle kaafi samay se bik nahi raha hai, iska grahak (buyer) kab milega?",
        PT,
    ),
    (
        "Kya mujhe property ke sahi daam (market value) milenge ya saste me bechna padega?",
        PT_PS,
    ),
    (
        "Jo buyer aaya hai, kya woh genuine hai ya uske saath deal karne me paisa phans sakta hai?",
        PS_ONLY,
    ),
    (
        "Property bechne ke baad jo paisa aayega, use kahan invest karun taaki income tax na lage?",
        PS_ONLY,
    ),
    (
        "Kya property bechkar main apna saara purana karza (loan/debt) chuka paunga?",
        PT_PS,
    ),
    (
        "Purane ghar ko bechne ke liye mujhe kisi broker ki madad leni chahiye ya online deal karni chahiye?",
        PS_ONLY,
    ),
    (
        "Deal final hone ke baad buyer paise dene me delay toh nahi karega?",
        PS_ONLY,
    ),
    (
        "Kya mujhe purana ghar bech kar naya ghar lena chahiye ya business me paisa lagana chahiye?",
        PS_ONLY,
    ),
    (
        "Property par koi legal dispute ya paper work me kami hai, kya woh sale hone se pehle theek ho payegi?",
        PT_PS,
    ),
    (
        "Ghar bechne ka agreement (bayaana) kab tak sign hoga?",
        PT,
    ),
    (
        "Kya mujhe apna loss recover karne ke liye abhi thoda aur rukh kar property bechna chahiye?",
        PT_PS,
    ),
    (
        "Buyer baar-baar rate kam kara raha hai, mujhe kis price par deal lock kar deni chahiye?",
        PS_ONLY,
    ),
    (
        "Kya ghar bechne me koi vaastu dosh rukawat ban raha hai (jaise ghar ka bhaari hona)?",
        PS_ONLY,
    ),
    (
        "Purani property bikne ka sabs strong yoga kis mahine me ban raha hai?",
        PT,
    ),
    (
        "Kya pariwar ke baaki sadasya (family members) is ghar ko bechne ke liye raazi honge?",
        PT_PS,
    ),
    (
        "Property sell hone ke baad kya mujhe sudden cash profit (capital gains) ka fayda milega?",
        PT_PS,
    ),
    (
        "Kya kisi purane grahak (old lead) se hi baat dobara banegi ya koi naya buyer aayega?",
        PT,
    ),
    (
        "Kahin property jaldbazi me bechne par mujhe baad me pachtana toh nahi padega?",
        PT_PS,
    ),
    (
        "Token money lene ke baad deal cancel hone ke kitne chances hain?",
        PS_ONLY,
    ),
    (
        "Meri kundli ka kaun sa dasha-period purani assets ko liquidate (bechne) ke liye active ho chuka hai?",
        PT,
    ),
]
