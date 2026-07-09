"""Shared ModuleLoader — loads per-engine module matrix."""
from __future__ import annotations

from typing import Any

from .modules.ashtakavarga import load_ashtakavarga
from .modules.bcp import load_bcp
from .modules.d1 import load_d1
from .modules.d9 import load_d9
from .modules.dasha import load_dasha
from .modules.jaimini import load_jaimini
from .modules.kp import load_kp
from .modules.transit import load_transit
from .modules.types import ModuleBundle
from .registry import modules_for_engine

_LOADERS = {
    "d1": load_d1,
    "d9": load_d9,
    "dasha": load_dasha,
    "transit": load_transit,
    "kp": load_kp,
    "ashtakavarga": load_ashtakavarga,
    "jaimini": load_jaimini,
    "bcp": load_bcp,
}


class ModuleLoader:
    """Load chart modules for an engine + question."""

    def load(
        self,
        engine_id: str,
        question: str,
        kundli: dict,
        *,
        extra: dict[str, Any] | None = None,
    ) -> ModuleBundle:
        requested = modules_for_engine(engine_id, question)
        bundle = ModuleBundle(engine_id=engine_id, modules_requested=requested)
        for mod_id in requested:
            fn = _LOADERS.get(mod_id)
            if not fn:
                continue
            try:
                bundle.modules[mod_id] = fn(kundli, engine_id=engine_id)
            except Exception as exc:
                from .modules.types import ChartModuleResult

                bundle.modules[mod_id] = ChartModuleResult(
                    module_id=mod_id,
                    loaded=False,
                    error=str(exc),
                )
        return bundle
