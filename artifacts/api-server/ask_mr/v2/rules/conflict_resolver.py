"""Conflict resolver — merges module signals + fired rules into score."""
from __future__ import annotations

from typing import Any

from ..modules.types import ModuleBundle
from .priority import rule_sort_key
from .types import FiredRule


class ConflictResolver:
    def resolve(
        self,
        bundle: ModuleBundle,
        fired: list[FiredRule],
        *,
        base_score: int = 50,
    ) -> dict[str, Any]:
        score = float(base_score)
        pos: list[str] = []
        neg: list[str] = []
        neu: list[str] = []

        # Module sub-scores (weighted)
        mod_weights = {"d1": 0.30, "d9": 0.25, "ashtakavarga": 0.10, "dasha": 0.12, "transit": 0.10, "kp": 0.08, "bcp": 0.05}
        used_w = 0.0
        mod_blend = 0.0
        for mod_id, res in bundle.modules.items():
            if not res.loaded:
                continue
            w = mod_weights.get(mod_id, 0.05)
            mod_blend += res.score * w
            used_w += w
        if used_w > 0:
            score = 0.55 * score + 0.45 * (mod_blend / used_w)

        for fr in sorted(fired, key=lambda r: rule_sort_key(r.to_dict())):
            delta = fr.weight * (1 if fr.polarity == "positive" else (-1 if fr.polarity == "negative" else 0))
            score += delta * 3
            line = fr.evidence or fr.label
            if fr.polarity == "positive":
                pos.append(line)
            elif fr.polarity == "negative":
                neg.append(line)
            else:
                neu.append(line)

        score_i = max(0, min(100, int(round(score))))
        return {
            "score": score_i,
            "evidence_positive": pos,
            "evidence_negative": neg,
            "evidence_neutral": neu,
        }
