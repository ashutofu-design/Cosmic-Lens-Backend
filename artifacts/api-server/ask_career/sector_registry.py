"""Single registry for career sector patterns, scope keywords, and archetype hints."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SectorEntry:
    key: str
    label: str
    kind: str  # job | biz | comm
    pattern: re.Pattern[str]
    evidence_hint: str
    answer_words: tuple[str, ...] = ()


def _rx(parts: str) -> re.Pattern[str]:
    return re.compile(rf"(?ix)\b({parts})\b")


# ── Scope / is_career_static anchor words ───────────────────────────────────
CAREER_SCOPE_EXTRA = (
    r"youtuber|youtube|vlogger|influencer|streamer|tiktok|instagram|podcast|"
    r"actor|actress|bollywood|film|filmmaker|singer|musician|dancer|photographer|"
    r"gamer|gaming|esports|pilot|aviation|air\s*host|"
    r"army|defence|defense|police|ips|ias|upsc|ssc|railway|bank\s*exam|govt\s*exam|"
    r"chartered\s*accountant|\bca\b|accountant|architect|interior\s*design|"
    r"fashion|model|salon|spa|beautician|makeup|"
    r"farmer|agriculture|farming|dairy|poultry|"
    r"electrician|plumber|mechanic|carpenter|welder|technician|driver|tailor|"
    r"sports|cricketer|athlete|"
    r"e[\s-]?commerce|amazon|flipkart|dropship|franchise|"
    r"gym|fitness\s*trainer|coach|coaching\s*center|tuition|"
    r"digital\s*marketing|seo|"
    r"jewell?ery|gold\s*business|transport|logistics|trucking|"
    r"garment|textile|pharmacy|chemist|construction|builder|"
    r"food|restaurant|catering|hotel|bakery|cafe|dhaba|cloud\s*kitchen|"
    r"promotion|interview|job\s*change|switch\s*job|side\s*hustle|part\s*time|"
    r"vocational|skilled\s*trade"
)

# ── Creativity / performance careers ────────────────────────────────────────
CREATIVITY_RX = _rx(
    r"youtuber|youtube|vlogger|influencer|content\s*creat\w*|"
    r"tiktok|instagram\s*reels?|streamer|podcast\w*|"
    r"actor|actress|bollywood|film|filmmaker|"
    r"singer|musician|dancer|band|"
    r"photographer|photography|"
    r"gamer|gaming|esports"
)

# ── Milestone / progress question patterns ──────────────────────────────────
PROMOTION_RX = _rx(
    r"promotion|promote|tarakki|senior\s*role|manager\s*ban|"
    r"growth\s*fast|career\s*growth|upward\s*move"
)
INTERVIEW_RX = _rx(
    r"interview|selection|select\s*hoga|clear\s*hoga|pass\s*hoga|"
    r"shortlist|recruiter|hr\s*round"
)
JOB_CHANGE_RX = _rx(
    r"job\s*change|switch\s*job|naukri\s*badlo|company\s*change|"
    r"job\s*switch|career\s*switch|transfer\s*job"
)
GOVT_EXAM_RX = _rx(
    r"upsc|ias|ips|ssc|cgl|railway\s*exam|bank\s*exam|govt\s*exam|"
    r"government\s*exam|competitive\s*exam|civil\s*service|pcs|"
    r"state\s*psc|defence\s*exam|nda|cds"
)

GOVT_EXAM_INTENT_RX = re.compile(
    r"(?ix)\b("
    r"exam|clear|pass|crack|selection|result|prelims|mains|paper|rank|"
    r"topper|qualified|qualify|shortlist|attempt"
    r")\b"
)

GOVT_JOB_RX = _rx(
    r"govt\s*job|government\s*job|sarkari\s*naukri|sarkari\s*job|"
    r"sarkari\s*me\s*(jaau|jau|javu|ban|service)|govt\s*me\s*naukri|"
    r"public\s*sector\s*job|government\s*service|civil\s*service\s*(job|line|career)|"
    r"ias\s*(ban|banna|job|line|career|suit)|ips\s*(ban|job|line|career|suit)|"
    r"police\s*(job|service|line)|railway\s*job|railway\s*service|"
    r"bank\s*po|bank\s*job|ssc\s*job|defence\s*job|army\s*job|"
    r"sarkari\s*field|govt\s*field|government\s*field|sarkari\s*line|govt\s*line"
)
SIDE_HUSTLE_RX = _rx(
    r"side\s*hustle|part\s*time|extra\s*income|side\s*income|"
    r"dusra\s*kaam|second\s*job|parallel\s*income"
)
VOCATIONAL_RX = _rx(
    r"electrician|plumber|mechanic|carpenter|welder|technician|"
    r"driver|tailor|fitter|mason|painter|barber|"
    r"vocational|skilled\s*trade|iti\b"
)

WHICH_BUSINESS_RX = _rx(
    r"konsa\s+business|kaun\s*sa\s+business|kaunsi\s+business|konsi\s+business|"
    r"which\s+business|what\s+business|best\s+business|business\s+best|"
    r"business\s+type|business\s+line|business\s+field|business\s+choose|"
    r"business\s+me\s+(jau|jaau|javu|jao|jaana)|agar\s+business|"
    r"business\s+start\s+kar\w*\s+konsa|sapna\s+business|ideal\s+business|"
    r"suitable\s+business|business\s+suit|business\s+option"
)

SECTOR_REGISTRY: tuple[SectorEntry, ...] = (
    SectorEntry("government", "Government/service", "job", _rx(r"government|govt|sarkari|public\s*sector|ups|ssc\s*job|civil\s*service"), "Sun-Saturn service + job subtype supports government/public roles.", ("government", "sarkari", "public sector", "service")),
    SectorEntry("private", "Private corporate", "job", _rx(r"private\s*sector|corporate|company\s*job|mnc|private\s*company"), "Commercial/professional subtype supports private company growth track.", ("private", "corporate", "company")),
    SectorEntry("banking", "Banking/finance job", "comm", _rx(r"bank\s*job|banking|bank\s*po|bank\s*exam|bank\s*career"), "Jupiter-Mercury finance subtype supports banking/accounting lines.", ("bank", "banking", "finance")),
    SectorEntry("ca", "CA/accountancy", "comm", _rx(r"chartered\s*accountant|\bca\b|accountant|audit|icai"), "Mercury-Saturn analytical subtype supports CA/audit/accountancy.", ("ca", "accountant", "audit", "accountancy")),
    SectorEntry("it", "IT/digital", "comm", _rx(r"it\b|software|tech|developer|coding|digital|programmer|data\s*science"), "Mercury-Rahu digital subtype supports IT/software fields.", ("it", "software", "tech", "digital", "coding")),
    SectorEntry("medical", "Medical/healing", "comm", _rx(r"medical|doctor|healthcare|nurse|hospital|mbbs|clinic|dentist|dental"), "Jupiter healing + service subtype supports medical lines.", ("medical", "doctor", "healthcare", "hospital", "nurse")),
    SectorEntry("pharmacy", "Pharmacy/chemist", "comm", _rx(r"pharmacy|chemist|pharmacist|medical\s*store|dawai"), "Mercury commerce + service subtype supports pharmacy/chemist work.", ("pharmacy", "chemist", "medical store")),
    SectorEntry("law", "Law/advisory", "comm", _rx(r"law|legal|advocate|lawyer|court|llb|litigation"), "Jupiter-Mercury advisory subtype supports law/advocacy.", ("law", "legal", "advocate", "lawyer")),
    SectorEntry("finance", "Finance/commerce", "comm", _rx(r"finance\s*sector|financial\s*analyst|investment\s*bank|wealth\s*advisor"), "2H/11H + commercial subtype supports finance professions.", ("finance", "financial")),
    SectorEntry("teaching", "Teaching/education", "comm", _rx(r"teaching|teacher|professor|education\s*field|tutor|lecturer|coaching\s*teacher"), "Jupiter-Mercury advisory subtype supports teaching/education.", ("teaching", "teacher", "education", "tutor")),
    SectorEntry("coaching", "Coaching/tuition center", "biz", _rx(r"coaching\s*center|tuition\s*center|coaching\s*institute|tuition\s*class"), "Jupiter advisory + commercial subtype supports coaching/tuition business.", ("coaching", "tuition", "institute")),
    SectorEntry("creative", "Creative/design", "comm", _rx(r"creative|design|art|artist|graphic\s*design|animation|fashion\s*design"), "Venus-Mercury creative subtype supports design/art fields.", ("creative", "design", "art", "artist")),
    SectorEntry("technical", "Technical/engineering", "comm", _rx(r"technical|engineering|engineer|mechanical|civil\s*engineer|tech\s*field"), "Mars-Saturn execution subtype supports engineering/technical roles.", ("technical", "engineering", "engineer")),
    SectorEntry("architect", "Architecture/interior", "comm", _rx(r"architect|architecture|interior\s*design|interior\s*decor"), "Venus-Saturn structure + design subtype supports architecture/interior.", ("architect", "architecture", "interior")),
    SectorEntry("management", "Management/administration", "job", _rx(r"management|manager|leadership\s*role|admin|administrator"), "Sun-Saturn authority subtype supports management/admin roles.", ("management", "manager", "admin")),
    SectorEntry("sales", "Sales/marketing", "comm", _rx(r"sales|marketing|business\s*development|digital\s*marketing|seo\b"), "Venus-Mercury people-facing commercial subtype supports sales/marketing.", ("sales", "marketing", "digital marketing")),
    SectorEntry("research", "Research/analysis", "comm", _rx(r"research|analyst|scientist|r\s*&\s*d|data\s*analyst"), "Mercury analytical subtype supports research/analysis roles.", ("research", "analyst", "scientist")),
    SectorEntry("real_estate", "Real estate/commerce", "biz", _rx(r"real\s*estate|property\s*business|builder|construction\s*business|realtor"), "Mars-Saturn asset execution supports property/construction business.", ("real estate", "property", "construction", "builder")),
    SectorEntry("consulting", "Consulting/advisory", "comm", _rx(r"consulting|consultant|advisory|advisor"), "Jupiter-Mercury advisory subtype supports consulting.", ("consulting", "consultant", "advisory")),
    SectorEntry("food", "Food/hospitality business", "biz", _rx(r"food|restaurant|catering|hotel|bakery|cafe|dhaba|cloud\s*kitchen|hospitality"), "Venus-Moon hospitality + service subtype supports food/cafe/catering.", ("food", "restaurant", "catering", "hotel", "hospitality", "cafe")),
    SectorEntry("media", "Media/content", "comm", _rx(r"media|journalism|reporter|news|anchor|presenter"), "Venus-Mercury public-facing subtype supports media/journalism.", ("media", "journalism", "news", "anchor")),
    SectorEntry("film", "Film/acting", "comm", _rx(r"film|acting|actor|actress|bollywood|cinema|director"), "Venus-Rahu creative visibility supports film/acting paths.", ("film", "acting", "actor", "bollywood", "cinema")),
    SectorEntry("music", "Music/performance", "comm", _rx(r"music|musician|singer|band|composer|playback"), "Venus creative + public performance subtype supports music careers.", ("music", "musician", "singer", "band")),
    SectorEntry("ngo", "Social/NGO service", "job", _rx(r"ngo|social\s*work|non[\s-]?profit|charity"), "Jupiter service subtype supports NGO/social work.", ("ngo", "social work", "charity")),
    SectorEntry("politics", "Politics/public influence", "job", _rx(r"politics|political|neta|election|public\s*office"), "Sun-Rahu public influence supports politics/public roles.", ("politics", "political", "election")),
    SectorEntry("defence", "Defence/security", "job", _rx(r"army|navy|air\s*force|defence|defense|military|police|ips\b|paramilitary"), "Mars-Saturn discipline subtype supports defence/security service.", ("army", "defence", "defense", "police", "military")),
    SectorEntry("aviation", "Aviation/pilot", "comm", _rx(r"pilot|aviation|airline|air\s*host|flight\s*attendant|cabin\s*crew"), "Rahu travel + Mercury precision supports aviation careers.", ("pilot", "aviation", "airline", "air host")),
    SectorEntry("sports", "Sports/athletics", "comm", _rx(r"sports|cricketer|athlete|football|fitness\s*career|player\b"), "Mars drive + competitive subtype supports sports/athletics.", ("sports", "cricketer", "athlete", "player")),
    SectorEntry("fitness", "Fitness/gym trainer", "comm", _rx(r"gym|fitness\s*trainer|personal\s*trainer|yoga\s*teacher|gym\s*owner"), "Mars vitality + Venus body-care supports fitness training.", ("gym", "fitness", "trainer", "yoga")),
    SectorEntry("fashion", "Fashion/beauty", "comm", _rx(r"fashion|model|modeling|beauty|salon|spa|beautician|makeup|parlour"), "Venus luxury/commerce subtype supports fashion/beauty lines.", ("fashion", "model", "salon", "beauty", "makeup", "spa")),
    SectorEntry("agriculture", "Agriculture/farming", "biz", _rx(r"agriculture|farming|farmer|kheti|dairy|poultry|livestock"), "Moon earth-care + business execution supports farming/agri lines.", ("agriculture", "farming", "farmer", "dairy", "kheti")),
    SectorEntry("ecommerce", "E-commerce/online selling", "biz", _rx(r"e[\s-]?commerce|amazon|flipkart|online\s*selling|dropship|marketplace\s*seller"), "Mercury-Rahu digital commerce supports e-commerce/online selling.", ("e-commerce", "amazon", "flipkart", "online selling", "dropship")),
    SectorEntry("franchise", "Franchise business", "biz", _rx(r"franchise|franchisee|brand\s*franchise"), "Saturn structure + business subtype supports franchise models.", ("franchise",)),
    SectorEntry("transport", "Transport/logistics", "biz", _rx(r"transport|logistics|trucking|fleet|courier|delivery\s*business|cab\s*business|ola|uber\s*business"), "Mars movement + business execution supports transport/logistics.", ("transport", "logistics", "trucking", "delivery", "cab")),
    SectorEntry("jewellery", "Jewellery/gold business", "biz", _rx(r"jewell?ery|gold\s*business|ornament|jeweller|sona\s*business"), "Venus luxury commerce supports jewellery/gold trade.", ("jewellery", "jewelry", "gold", "ornament")),
    SectorEntry("garment", "Garment/textile business", "biz", _rx(r"garment|textile|boutique|clothing\s*business|kapde\s*ka\s*business|fashion\s*business"), "Venus commerce + trade subtype supports garment/textile business.", ("garment", "textile", "boutique", "clothing")),
    SectorEntry("industry", "Best industry/business type", "comm", _rx(r"industry|field|line|profession|kaunsi|konsa\s+business|best\s+business|which\s+business|business\s+best|business\s+type"), "Read top commercial/business subtypes from chart.", ("industry", "field", "line", "business type")),
)


def detect_sector(question: str) -> SectorEntry | None:
    q = question or ""
    for entry in SECTOR_REGISTRY:
        if entry.pattern.search(q):
            return entry
    return None


def is_govt_exam_milestone_question(question: str, interpretation: str = "") -> bool:
    q = (question or "").strip()
    interp = (interpretation or "").strip()
    if not GOVT_EXAM_RX.search(q):
        return False
    if GOVT_EXAM_INTENT_RX.search(q):
        return True
    return bool(re.search(r"(?ix)(govt exam|government exam|competitive exam)", interp))


def is_govt_job_question(question: str, interpretation: str = "") -> bool:
    q = (question or "").strip()
    interp = (interpretation or "").strip()
    if is_govt_exam_milestone_question(q, interp):
        return False
    if GOVT_JOB_RX.search(q):
        return True
    if re.search(r"(?ix)\b(government|govt|sarkari|public\s*sector)\b", q):
        if re.search(r"(?ix)\b(job|naukri|service|suit|better|career|ban|line|field|banna)\b", q):
            return True
    entry = detect_sector(q)
    if entry and entry.key in ("government", "defence") and not is_govt_exam_milestone_question(q, interp):
        return True
    return bool(re.search(r"(?ix)(government job|sarkari naukri|govt job)", interp))


def sector_answer_words() -> re.Pattern[str]:
    words: list[str] = []
    for entry in SECTOR_REGISTRY:
        words.extend(entry.answer_words)
        words.append(entry.key.replace("_", " "))
        words.append(entry.label.split("/")[0].lower())
    uniq = sorted(set(w for w in words if w), key=len, reverse=True)
    return re.compile(r"(?ix)\b(" + "|".join(re.escape(w) for w in uniq[:80]) + r")\b")


def build_career_core_pattern() -> re.Pattern[str]:
    base = (
        r"career|naukri|job|business|profession|kaam|office|promotion|salary|"
        r"entrepreneur|startup|freelanc\w*|corporate|govt|government|sarkari|dhandha|"
        r"leadership|skills?|workplace|boss|colleagues?|industry|fields?|talents?|"
        r"employee|self[\s-]?employment|consulting|teaching|medical|law|finance|"
        r"technical|management|sales|marketing|research|real\s*estate|trading|"
        r"paisa\s*kama\w*|paisa|wealth|income|abroad|foreign|videsh|fame|recognition|"
        r"creative|content|retirement|legacy|stud(?:y|ies)|padhai|exam|degree|college|"
        r"remote|mnc|multinational|ngo|politics|media|manufacturing|"
        r"import[\s-]?export|network\w*|negotiat\w*|pressure|risk|disciplin\w*|"
        r"strategic|weakness|strength|suitable|suit\s+kare|suit\s+kar|"
        r"private\s*sector|public\s*sector|team|independent|communication|"
        r"public\s*dealing|public\s*speaking|"
        r"investment\w*|commission|higher\s*stud|colleague|interview|"
    )
    return re.compile(rf"(?ix)\b({base}{CAREER_SCOPE_EXTRA})\b")
