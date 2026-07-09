"""Engine scorecard — multi-axis internal scores."""
from __future__ import annotations

from .modules.types import ModuleBundle
from .rules.types import FiredRule


def build_scorecard(
    engine_id: str,
    bundle: ModuleBundle,
    fired: list[FiredRule],
    *,
    primary_score: int,
) -> dict[str, int]:
    """Return axis scores 0-100 for analytics + narrator."""
    eid = (engine_id or "").strip().lower()

    def _mod(name: str, default: int = 50) -> int:
        m = bundle.modules.get(name)
        return int(m.score) if m and m.loaded else default

    d1, d9 = _mod("d1"), _mod("d9")
    trust = int(round(0.4 * d1 + 0.35 * d9 + 0.25 * primary_score))
    commitment = primary_score if eid == "commitment" else int(round(0.5 * d1 + 0.5 * d9))
    communication = int(round(0.6 * _mod("d1", d1) + 0.4 * _mod("ashtakavarga", 50)))
    chemistry = int(round(0.55 * d1 + 0.45 * d9))
    family = _mod("bcp", int(round(0.5 * d1 + 0.5 * d9)))

    neg_penalty = sum(1 for f in fired if f.polarity == "negative") * 3
    pos_bonus = sum(1 for f in fired if f.polarity == "positive") * 2

    def clamp(v: int) -> int:
        return max(0, min(100, v + pos_bonus - neg_penalty))

    return {
        "trust": clamp(trust),
        "commitment": clamp(commitment),
        "communication": clamp(communication),
        "chemistry": clamp(chemistry),
        "family": clamp(family),
        "primary": clamp(primary_score),
    }
