"""Dedicated job/profession engines — routes important employment paths away from generic sector_fit."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .sector_registry import WHICH_BUSINESS_RX, detect_sector

_BIZ_ONLY_RX = re.compile(
    r"(?ix)\b("
    r"business\s*start|start\s*up|startup|apna\s*(business|dhandha)|"
    r"online\s*business|trading\s*business|franchise|dropship|"
    r"e[\s-]?commerce|amazon|flipkart|restaurant\s*business|hotel\s*business|"
    r"food\s*business|property\s*business|construction\s*business"
    r")\b"
)


def _rx(parts: str) -> re.Pattern[str]:
    return re.compile(rf"(?ix)\b({parts})\b")


@dataclass(frozen=True)
class JobEngineEntry:
    archetype: str
    label: str
    pattern: re.Pattern[str]
    evidence_hint: str
    subtype_kind: str = "comm"  # job | comm
    subtype_keywords: tuple[str, ...] = ()
    traits: tuple[str, ...] = ("discipline",)
    planet_roles: tuple[tuple[str, str], ...] = ()
    min_job_pct: int | None = None
    min_comm_score: int | None = 28
    min_score: int = 50


# Order = priority (first match wins)
JOB_ENGINE_REGISTRY: tuple[JobEngineEntry, ...] = (
    JobEngineEntry(
        "medical_job",
        "Medical/doctor career",
        _rx(
            r"medical|doctor|mbbs|healthcare|nurse|hospital|clinic|dentist|dental|"
            r"surgeon|physician|medical\s*line|doctor\s*ban"
        ),
        "Jupiter healing + service subtype supports medical/healing professions.",
        subtype_keywords=("healing", "medical", "service", "advisory"),
        traits=("discipline", "persistence"),
        planet_roles=(("Jupiter", "healing/advisory"), ("Moon", "care/service")),
        min_comm_score=30,
    ),
    JobEngineEntry(
        "it_job",
        "IT/software career",
        _rx(
            r"it\b|software|developer|coding|programmer|data\s*science|"
            r"tech\s*job|software\s*engineer|web\s*developer|app\s*developer|"
            r"computer\s*science|cs\s*field"
        ),
        "Mercury-Rahu digital + analytical subtype supports IT/software careers.",
        subtype_keywords=("digital", "tech", "analytical", "software"),
        traits=("adaptability", "discipline"),
        planet_roles=(("Mercury", "skills/logic"), ("Rahu", "digital/innovation")),
        min_comm_score=32,
    ),
    JobEngineEntry(
        "ca_job",
        "CA/accountancy career",
        _rx(r"chartered\s*accountant|\bca\b|accountant|audit|icai|accountancy\s*line"),
        "Mercury-Saturn analytical subtype supports CA/audit/accountancy careers.",
        subtype_keywords=("analytical", "finance", "audit", "account"),
        traits=("discipline", "adaptability"),
        planet_roles=(("Mercury", "analysis"), ("Saturn", "structure/audit")),
        min_comm_score=34,
    ),
    JobEngineEntry(
        "aviation_job",
        "Aviation/pilot career",
        _rx(
            r"pilot|aviation|airline|air\s*host|flight\s*attendant|cabin\s*crew|"
            r"commercial\s*pilot|pilot\s*ban"
        ),
        "Rahu travel + Mercury precision supports aviation/airline careers.",
        subtype_keywords=("travel", "service", "precision"),
        traits=("risk_appetite", "discipline"),
        planet_roles=(("Rahu", "travel/movement"), ("Mercury", "precision/skills")),
        min_comm_score=26,
    ),
    JobEngineEntry(
        "law_job",
        "Law/advocacy career",
        _rx(r"law|legal|advocate|lawyer|court|llb|litigation|bar\s*exam|law\s*line"),
        "Jupiter-Mercury advisory subtype supports law/advocacy careers.",
        subtype_keywords=("advisory", "legal", "law", "debate"),
        traits=("communication", "discipline"),
        planet_roles=(("Jupiter", "advisory/justice"), ("Mercury", "argument/analysis")),
        min_comm_score=30,
    ),
    JobEngineEntry(
        "teaching_job",
        "Teaching/education career",
        _rx(
            r"teaching|teacher|professor|lecturer|tutor|education\s*field|"
            r"padhana|teacher\s*ban|professor\s*ban"
        ),
        "Jupiter-Mercury advisory subtype supports teaching/education careers.",
        subtype_keywords=("advisory", "teaching", "education", "service"),
        traits=("communication", "persistence"),
        planet_roles=(("Jupiter", "guidance/wisdom"), ("Mercury", "communication")),
        min_comm_score=28,
    ),
    JobEngineEntry(
        "defence_job",
        "Defence/security service",
        _rx(
            r"army|navy|air\s*force|defence|defense|military|paramilitary|"
            r"army\s*officer|defence\s*service|fauj"
        ),
        "Mars-Saturn discipline + service subtype supports defence/security careers.",
        subtype_kind="job",
        subtype_keywords=("service", "discipline", "defence", "security"),
        traits=("discipline", "risk_appetite", "persistence"),
        planet_roles=(("Mars", "drive/courage"), ("Saturn", "discipline/tenure")),
        min_job_pct=48,
    ),
    JobEngineEntry(
        "banking_job",
        "Banking/finance job",
        _rx(
            r"bank\s*job|banking\s*career|bank\s*career|investment\s*banker|"
            r"financial\s*analyst|wealth\s*advisor|finance\s*job|finance\s*sector"
        ),
        "Jupiter-Mercury finance subtype supports banking/finance employment.",
        subtype_keywords=("finance", "bank", "commerce", "analytical"),
        traits=("discipline", "communication"),
        planet_roles=(("Jupiter", "finance/growth"), ("Mercury", "analysis/accounts")),
        min_comm_score=30,
    ),
    JobEngineEntry(
        "engineering_job",
        "Engineering/technical career",
        _rx(
            r"engineering|engineer|mechanical|civil\s*engineer|electrical\s*engineer|"
            r"technical\s*job|tech\s*field|core\s*engineering"
        ),
        "Mars-Saturn execution + technical subtype supports engineering careers.",
        subtype_keywords=("technical", "engineering", "execution", "structure"),
        traits=("discipline", "persistence"),
        planet_roles=(("Mars", "execution/build"), ("Saturn", "structure/endurance")),
        min_comm_score=28,
    ),
    JobEngineEntry(
        "architecture_job",
        "Architecture/interior career",
        _rx(r"architect|architecture|interior\s*design|interior\s*decor|architect\s*ban"),
        "Venus-Saturn design + Mercury planning supports architecture/interior careers.",
        subtype_keywords=("design", "structure", "creative", "planning"),
        traits=("adaptability", "discipline"),
        planet_roles=(("Venus", "design/aesthetics"), ("Saturn", "structure")),
        min_comm_score=28,
    ),
    JobEngineEntry(
        "pharma_job",
        "Pharmacy/chemist career",
        _rx(r"pharmacy|chemist|pharmacist|medical\s*store|dawai|b\.?\s*pharm"),
        "Mercury commerce + service subtype supports pharmacy/chemist careers.",
        subtype_keywords=("medical", "commerce", "service", "retail"),
        traits=("discipline", "communication"),
        planet_roles=(("Mercury", "detail/commerce"), ("Jupiter", "healing/service")),
        min_comm_score=26,
    ),
    JobEngineEntry(
        "sales_job",
        "Sales/marketing career",
        _rx(
            r"sales\s*job|sales\s*career|marketing\s*job|marketing\s*career|"
            r"business\s*development|digital\s*marketing|seo\s*career|"
            r"sales\s*field|marketing\s*field"
        ),
        "Venus-Mercury people-facing commercial subtype supports sales/marketing careers.",
        subtype_keywords=("sales", "marketing", "commerce", "public"),
        traits=("communication", "risk_appetite"),
        planet_roles=(("Venus", "people/commerce"), ("Mercury", "persuasion/detail")),
        min_comm_score=26,
    ),
    JobEngineEntry(
        "research_job",
        "Research/analysis career",
        _rx(
            r"research\s*job|research\s*career|scientist|data\s*analyst|"
            r"r\s*&\s*d|analyst\s*job|research\s*field"
        ),
        "Mercury analytical subtype supports research/analysis careers.",
        subtype_keywords=("research", "analytical", "science", "analysis"),
        traits=("discipline", "adaptability"),
        planet_roles=(("Mercury", "analysis/research"), ("Saturn", "deep focus")),
        min_comm_score=30,
    ),
    JobEngineEntry(
        "consulting_job",
        "Consulting/advisory career",
        _rx(r"consulting\s*job|consultant|advisory\s*career|advisor\s*job|consulting\s*field"),
        "Jupiter-Mercury advisory subtype supports consulting/advisory careers.",
        subtype_keywords=("advisory", "consulting", "strategy"),
        traits=("communication", "adaptability"),
        planet_roles=(("Jupiter", "advisory"), ("Mercury", "analysis")),
        min_comm_score=30,
    ),
    JobEngineEntry(
        "sports_job",
        "Sports/athletics career",
        _rx(
            r"sports\s*job|sports\s*career|cricketer|athlete|football\s*career|"
            r"professional\s*player|player\s*ban|sports\s*field"
        ),
        "Mars competitive drive + vitality supports sports/athletics careers.",
        subtype_keywords=("sports", "competitive", "drive"),
        traits=("risk_appetite", "persistence"),
        planet_roles=(("Mars", "drive/competition"), ("Sun", "visibility/leadership")),
        min_comm_score=24,
    ),
    JobEngineEntry(
        "media_job",
        "Media/journalism career",
        _rx(
            r"media\s*job|journalism|journalist|reporter|news\s*anchor|presenter|"
            r"news\s*career|media\s*field"
        ),
        "Venus-Mercury public-facing subtype supports media/journalism careers.",
        subtype_keywords=("media", "public", "communication"),
        traits=("communication", "adaptability"),
        planet_roles=(("Venus", "public presence"), ("Mercury", "communication")),
        min_comm_score=26,
    ),
    JobEngineEntry(
        "ngo_job",
        "NGO/social work career",
        _rx(r"ngo\s*job|social\s*work|non[\s-]?profit|charity\s*work|social\s*service\s*career"),
        "Jupiter service subtype supports NGO/social-work careers.",
        subtype_kind="job",
        subtype_keywords=("service", "social", "ngo", "charity"),
        traits=("emotional_stability", "communication"),
        planet_roles=(("Jupiter", "service/welfare"), ("Moon", "empathy/care")),
        min_job_pct=45,
    ),
    JobEngineEntry(
        "management_job",
        "Management/administration career",
        _rx(
            r"management\s*job|manager\s*role|administrator|admin\s*job|"
            r"leadership\s*role|management\s*career|manager\s*ban"
        ),
        "Sun-Saturn authority + structure supports management/admin careers.",
        subtype_kind="job",
        subtype_keywords=("management", "admin", "leadership", "authority"),
        traits=("leadership", "discipline"),
        planet_roles=(("Sun", "authority"), ("Saturn", "structure/hierarchy")),
        min_job_pct=50,
    ),
    JobEngineEntry(
        "private_job",
        "Private corporate/MNC career",
        _rx(
            r"private\s*sector|corporate\s*job|company\s*job|mnc|multinational|"
            r"private\s*company|corporate\s*career|corporate\s*world|big\s*company"
        ),
        "Commercial/professional subtype + job tilt supports private corporate careers.",
        subtype_kind="job",
        subtype_keywords=("corporate", "professional", "company", "commercial"),
        traits=("discipline", "adaptability"),
        planet_roles=(("Mercury", "professional skills"), ("Saturn", "org structure")),
        min_job_pct=50,
    ),
)

JOB_ENGINE_ARCHETYPES: frozenset[str] = frozenset(e.archetype for e in JOB_ENGINE_REGISTRY)

_SECTOR_TO_JOB: dict[str, str] = {
    "private": "private_job",
    "it": "it_job",
    "medical": "medical_job",
    "banking": "banking_job",
    "ca": "ca_job",
    "law": "law_job",
    "teaching": "teaching_job",
    "technical": "engineering_job",
    "architect": "architecture_job",
    "pharmacy": "pharma_job",
    "sales": "sales_job",
    "research": "research_job",
    "consulting": "consulting_job",
    "defence": "defence_job",
    "aviation": "aviation_job",
    "sports": "sports_job",
    "media": "media_job",
    "ngo": "ngo_job",
    "management": "management_job",
    "finance": "banking_job",
}

_PROFILE_BY_ARCHETYPE: dict[str, JobEngineEntry] = {e.archetype: e for e in JOB_ENGINE_REGISTRY}


def get_job_profile(archetype: str) -> JobEngineEntry | None:
    return _PROFILE_BY_ARCHETYPE.get((archetype or "").strip().lower())


def _is_business_question(q: str) -> bool:
    if WHICH_BUSINESS_RX.search(q):
        return True
    return bool(_BIZ_ONLY_RX.search(q))


def detect_job_archetype(question: str) -> str | None:
    """Return dedicated job engine archetype if question is employment-path suitability."""
    q = (question or "").strip()
    if not q or _is_business_question(q):
        return None
    for entry in JOB_ENGINE_REGISTRY:
        if entry.pattern.search(q):
            return entry.archetype
    entry = detect_sector(q)
    if entry and entry.key in _SECTOR_TO_JOB and entry.kind in ("job", "comm"):
        if entry.key == "banking" and re.search(r"(?ix)\b(bank\s*po|sarkari|govt)\b", q):
            return None
        return _SECTOR_TO_JOB[entry.key]
    return None


def is_dedicated_job_question(question: str, interpretation: str = "") -> bool:
    q = (question or "").strip()
    if detect_job_archetype(q):
        return True
    interp = (interpretation or "").strip()
    return bool(re.search(r"(?ix)(it job|medical career|doctor career|software job|bank job)", interp))
