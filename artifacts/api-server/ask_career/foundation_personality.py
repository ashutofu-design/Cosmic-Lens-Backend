"""Section 1 — career foundation / personality questions (scope + routing)."""
from __future__ import annotations

import re

# Broad scope anchor — personality/work-style without naming a job sector
FOUNDATION_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"career\s+ki|mere\s+career|core\s+identity|professional\s+banne|"
    r"naturally|bana\s+hoon|banne\s+ke\s+liye|kis\s+type\s+ke\s+work|"
    r"follower|leader|independent\s+work|team\s+work|"
    r"practical\s+hoon|analytical|intuitive|risk[\s-]?tak|risk[\s-]?averse|"
    r"long[\s-]?term\s+planning|pressure\s+me|responsibility|"
    r"authority\s+handle|authority\s+ko|disciplined|consistent|ambitious|competitive|"
    r"natural\s+talents?|hidden\s+talents?|valuable\s+skill|"
    r"skill\s+par\s+focus|skill\s+ko\s+avoid|"
    r"communication\s+me|public\s+speaking|negotiation\s+me|networking\s+me|persuasion\s+me|"
    r"problem\s+solving|decision\s+making|strategic\s+thinking|planning\s+me|execution\s+me|"
    r"detail[\s-]?oriented|big[\s-]?picture|multitasking|specialization|"
    r"management\s+me\s+better|technical\s+role|client[\s-]?facing|backend\s+work|"
    r"research\s+work|field\s+work|office\s+work|remote\s+work|travel[\s-]?based\s+career|"
    r"leadership\s+quality|sabse\s+badi\s+strength|sabse\s+badi\s+weakness|"
    r"innovation\s+me\s+strong|main\s+innovation"
    r")\b"
)

# X vs Y personality — must route before sector "creative" match
_PERSONALITY_COMPARE_RX = re.compile(
    r"(?ix)\b("
    r"practical\s+hoon\s+ya|analytical\s+hoon\s+ya|"
    r"follower\s+zyada|leader\s+zyada|follower.*\b(ya|or)\b.*leader|"
    r"independent\s+work\s+me\s+better\s+ya\s+team"
    r")\b"
)

_STRENGTHS_RX = re.compile(
    r"(?ix)\b("
    r"career\s+ki\s+sabse\s+badi\s+(strength|weakness)|"
    r"natural\s+talents?|hidden\s+talents?|"
    r"valuable\s+skill|skill\s+par\s+focus|skill\s+ko\s+avoid|"
    r"communication\s+me\s+kitna|public\s+speaking\s+me\s+kitna|"
    r"management\s+me\s+better|technical\s+role\s+me\s+better"
    r")\b"
)

_WORK_ENV_RX = re.compile(
    r"(?ix)\b("
    r"remote\s+work\s+me\s+better|travel[\s-]?based\s+career|"
    r"work\s+from\s+home|wfh"
    r")\b"
)

_TRAITS_RX = re.compile(
    r"(?ix)\b("
    r"leadership\s+quality|follower|leader|"
    r"independent\s+work\s+me\s+better|team\s+work\s+me|"
    r"risk[\s-]?tak|risk[\s-]?averse|"
    r"long[\s-]?term\s+planning|pressure\s+me|"
    r"responsibility\s+lene|authority\s+handle|authority\s+ko\s+accept|"
    r"disciplined|consistent|"
    r"negotiation\s+me|networking\s+me|persuasion\s+me|"
    r"strategic\s+thinking|planning\s+me\s+kitna|"
    r"client[\s-]?facing\s+role"
    r")\b"
)

_INNOVATION_RX = re.compile(r"(?ix)\b(innovation\s+me\s+strong|main\s+innovation)\b")


def is_foundation_scope(question: str) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if FOUNDATION_SCOPE_RX.search(q):
        return True
    return bool(_PERSONALITY_COMPARE_RX.search(q))


def classify_foundation_personality(question: str) -> str | None:
    """Route Section-1 style personality questions before sector/job engines."""
    q = (question or "").strip().lower()
    if not q or not is_foundation_scope(q):
        return None

    if _STRENGTHS_RX.search(q):
        return "strengths_skills"

    if _WORK_ENV_RX.search(q):
        return "work_environment"

    if _INNOVATION_RX.search(q):
        return "creativity_innovation"

    if _TRAITS_RX.search(q):
        return "career_traits"

    if _PERSONALITY_COMPARE_RX.search(q):
        if re.search(r"(?ix)\b(practical|analytical)\s+hoon\s+ya\b", q):
            return "general_career"
        return "career_traits"

    return "general_career"
