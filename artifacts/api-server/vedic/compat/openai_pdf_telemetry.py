"""
OpenAI token + USD cost telemetry for premium PDF generation (chat.completions).

Pricing:
- Merged table = built-in defaults (updated from public OpenAI list prices) +
  optional remote JSON overrides from ``COMPAT_OPENAI_PRICES_JSON_URL`` (GET, short timeout).
- Per-call cost uses each response's ``model`` field when present, else requested model.

Last-run snapshot is stored for operators / Flask prints (``get_last_pdf_generation_telemetry``).
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any

log = logging.getLogger(__name__)

_LAST_PDF_GEN_TELEMETRY: dict[str, Any] | None = None
_LAST_LOCK = threading.Lock()

# USD per 1M tokens (input, output) — public Chat Completions list pricing (standard tier).
# Remote JSON (same keys) overrides / extends. Unknown models fall back to gpt-4o.
_DEFAULT_USD_PER_1M: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-4": (30.00, 60.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "gpt-5": (1.25, 10.00),  # placeholder — override via URL when exact
    "gpt-5-mini": (0.25, 2.00),
    "gpt-5-nano": (0.05, 0.40),
}

_PRICES_CACHE: dict[str, tuple[float, float]] | None = None
_PRICES_CACHE_AT: float = 0.0
_PRICES_TTL_SEC = float(os.environ.get("COMPAT_OPENAI_PRICES_CACHE_SEC", "3600") or "3600")
_PRICES_SOURCE = "defaults"


def get_last_pdf_generation_telemetry() -> dict[str, Any] | None:
    with _LAST_LOCK:
        return None if _LAST_PDF_GEN_TELEMETRY is None else dict(_LAST_PDF_GEN_TELEMETRY)


def set_last_pdf_generation_telemetry(meta: dict[str, Any] | None) -> None:
    global _LAST_PDF_GEN_TELEMETRY
    with _LAST_LOCK:
        _LAST_PDF_GEN_TELEMETRY = None if meta is None else dict(meta)


def update_last_pdf_generation_fields(**fields: Any) -> None:
    """Mutate last telemetry snapshot (e.g. after PDF render completes)."""
    global _LAST_PDF_GEN_TELEMETRY
    with _LAST_LOCK:
        if _LAST_PDF_GEN_TELEMETRY is None:
            return
        base = dict(_LAST_PDF_GEN_TELEMETRY)
        base.update(fields)
        _LAST_PDF_GEN_TELEMETRY = base


def republish_last_telemetry_summary(*, log_json: bool = False) -> None:
    """Re-print the human-readable block for the last run (no duplicate JSON log by default)."""
    with _LAST_LOCK:
        if _LAST_PDF_GEN_TELEMETRY is None:
            return
        d = dict(_LAST_PDF_GEN_TELEMETRY)
    print(format_pdf_generation_lines(d), flush=True)
    if log_json:
        try:
            log.info("[openai_pdf_telemetry] pdf_generation_refresh=%s", json.dumps(d, default=str))
        except Exception:
            pass


def _fetch_remote_price_overrides() -> dict[str, tuple[float, float]]:
    """GET JSON from ``COMPAT_OPENAI_PRICES_JSON_URL`` if set.

    Expected shape::
        { "gpt-4o": {"input_usd_per_1m": 2.5, "output_usd_per_1m": 10.0}, ... }
    or::
        { "models": { "gpt-4o": { ... } } }
    """
    url = (os.environ.get("COMPAT_OPENAI_PRICES_JSON_URL") or "").strip()
    if not url:
        return {}
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CosmicLens-Backend/telemetry"},
            method="GET",
        )
        to = float(os.environ.get("COMPAT_OPENAI_PRICES_FETCH_TIMEOUT", "8") or "8")
        with urllib.request.urlopen(req, timeout=to) as resp:  # noqa: S310
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except Exception as exc:
        log.warning("[openai_pdf_telemetry] price fetch failed url=%s err=%s", url, exc)
        return {}
    out: dict[str, tuple[float, float]] = {}
    if isinstance(data.get("models"), dict):
        data = data["models"]
    if not isinstance(data, dict):
        return {}
    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, dict):
            continue
        try:
            inp = float(v.get("input_usd_per_1m", v.get("input", 0)))
            outp = float(v.get("output_usd_per_1m", v.get("output", 0)))
        except (TypeError, ValueError):
            continue
        if inp > 0 and outp >= 0:
            out[k.strip()] = (inp, outp)
    return out


def get_effective_usd_per_1m_table() -> tuple[dict[str, tuple[float, float]], str]:
    """Return (merged_table, source_label). Thread-safe cache with TTL."""
    global _PRICES_CACHE, _PRICES_CACHE_AT, _PRICES_SOURCE
    now = time.monotonic()
    if _PRICES_CACHE is not None and (now - _PRICES_CACHE_AT) < _PRICES_TTL_SEC:
        return _PRICES_CACHE, _PRICES_SOURCE

    merged = dict(_DEFAULT_USD_PER_1M)
    src = "defaults"
    remote = _fetch_remote_price_overrides()
    if remote:
        merged.update(remote)
        src = (
            "defaults+COMPAT_OPENAI_PRICES_JSON_URL"
            if os.environ.get("COMPAT_OPENAI_PRICES_JSON_URL")
            else "defaults+remote"
        )
    _PRICES_CACHE = merged
    _PRICES_CACHE_AT = now
    _PRICES_SOURCE = src
    return merged, src


def resolve_usd_per_1m_for_model(model: str | None, table: dict[str, tuple[float, float]]) -> tuple[float, float, str]:
    """Return (input_per_1m, output_per_1m, matched_key)."""
    m = (model or "gpt-4o").strip().lower()
    if m in table:
        return table[m][0], table[m][1], m
    # Longest-prefix match (handles gpt-4o-2024-08-06, gpt-5-chat-latest, …)
    best_k = ""
    for k in table:
        kl = k.lower()
        if m.startswith(kl) and len(kl) > len(best_k):
            best_k = k
    if best_k:
        t = table[best_k]
        return t[0], t[1], best_k
    t0 = table.get("gpt-4o", (2.5, 10.0))
    return t0[0], t0[1], "gpt-4o(fallback)"


def estimate_call_cost_usd(
    model: str | None,
    prompt_tokens: int,
    completion_tokens: int,
    table: dict[str, tuple[float, float]],
) -> float:
    inp_m, out_m, _mk = resolve_usd_per_1m_for_model(model, table)
    return (max(0, prompt_tokens) / 1_000_000.0) * inp_m + (max(0, completion_tokens) / 1_000_000.0) * out_m


def usage_triplet(response: Any) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0, 0
    pt = int(getattr(usage, "prompt_tokens", 0) or 0)
    ct = int(getattr(usage, "completion_tokens", 0) or 0)
    tt = int(getattr(usage, "total_tokens", 0) or 0)
    if tt <= 0:
        tt = pt + ct
    return pt, ct, tt


_REGEN_PHASES = frozenset(
    {
        "p64_structure_regen",
        "p65_struct_regen",
        "p66_depth_regen",
        "depth_regen",
        "sdp_depth_regen",
    }
)
_RETRY_PHASES = frozenset({"json_retry", "primary_empty_body_retry"})


def _usd_inr_rate() -> float:
    try:
        return float(os.environ.get("COMPAT_USD_INR_RATE", "83") or "83")
    except (TypeError, ValueError):
        return 83.0


class PdfGenOpenAITelemetry:
    """Accumulates chat.completions usage across primary + retries + regens."""

    def __init__(self, model_requested: str) -> None:
        self.model_requested = (model_requested or "gpt-4o").strip()
        self._table, self.pricing_source = get_effective_usd_per_1m_table()
        self.phases: list[dict[str, Any]] = []

    def record(self, response: Any, phase: str) -> None:
        rm = getattr(response, "model", None) or self.model_requested
        pt, ct, tt = usage_triplet(response)
        cost = estimate_call_cost_usd(rm, pt, ct, self._table)
        row = {
            "phase": phase,
            "model": rm,
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": tt,
            "estimated_cost_usd": round(cost, 6),
        }
        self.phases.append(row)
        log.info(
            "[openai_pdf_telemetry] phase=%s model=%s prompt_tokens=%s "
            "completion_tokens=%s total_tokens=%s est_cost_usd=%.6f",
            phase,
            rm,
            pt,
            ct,
            tt,
            cost,
        )

    @property
    def prompt_tokens_total(self) -> int:
        return sum(int(p.get("prompt_tokens") or 0) for p in self.phases)

    @property
    def completion_tokens_total(self) -> int:
        return sum(int(p.get("completion_tokens") or 0) for p in self.phases)

    @property
    def total_tokens_reported(self) -> int:
        return sum(int(p.get("total_tokens") or 0) for p in self.phases)

    @property
    def estimated_cost_usd_total(self) -> float:
        return float(sum(float(p.get("estimated_cost_usd") or 0) for p in self.phases))

    @property
    def openai_call_count(self) -> int:
        return len(self.phases)

    @property
    def regen_count(self) -> int:
        return sum(1 for p in self.phases if p.get("phase") in _REGEN_PHASES)

    @property
    def retry_count(self) -> int:
        return sum(1 for p in self.phases if p.get("phase") in _RETRY_PHASES)

    def build_meta(
        self,
        *,
        fallback_used: bool,
        final_status: str,
        validator_attempts: int,
        cache_hit: bool = False,
        openai_skipped: bool = False,
        last_validator_reason: str | None = None,
        pdf_render_status: str | None = None,
    ) -> dict[str, Any]:
        primary_model = self.model_requested
        if self.phases:
            primary_model = str(self.phases[0].get("model") or primary_model)
        out: dict[str, Any] = {
            "model": primary_model,
            "model_requested": self.model_requested,
            "input_tokens": self.prompt_tokens_total,
            "output_tokens": self.completion_tokens_total,
            "total_tokens": self.total_tokens_reported,
            "estimated_cost_usd": round(self.estimated_cost_usd_total, 4),
            "estimated_cost_inr": round(self.estimated_cost_usd_total * _usd_inr_rate(), 2),
            "usd_inr_rate": _usd_inr_rate(),
            "openai_call_count": self.openai_call_count,
            "regen_count": self.regen_count,
            "retry_count": self.retry_count,
            "validator_attempts": int(validator_attempts),
            "fallback_used": bool(fallback_used),
            "final_status": final_status,
            "cache_hit": bool(cache_hit),
            "openai_skipped": bool(openai_skipped),
            "pricing_source": self.pricing_source,
            "phases": list(self.phases),
        }
        if last_validator_reason is not None:
            out["last_validator_reason"] = last_validator_reason
        if pdf_render_status is not None:
            out["pdf_render_status"] = pdf_render_status
        return out


def stub_meta(
    model: str,
    *,
    final_status: str,
    fallback_used: bool,
    openai_skipped: bool,
    cache_hit: bool = False,
    reason: str | None = None,
    validator_attempts: int = 0,
) -> dict[str, Any]:
    m: dict[str, Any] = {
        "model": model,
        "model_requested": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "estimated_cost_inr": 0.0,
        "usd_inr_rate": _usd_inr_rate(),
        "openai_call_count": 0,
        "regen_count": 0,
        "retry_count": 0,
        "validator_attempts": validator_attempts,
        "fallback_used": fallback_used,
        "final_status": final_status,
        "cache_hit": cache_hit,
        "openai_skipped": openai_skipped,
        "pricing_source": "n/a",
        "phases": [],
    }
    if reason:
        m["skip_reason"] = reason
    return m


def merge_pdf_generation_into_meta(meta_root: dict[str, Any], pdf_gen: dict[str, Any]) -> None:
    meta_root["pdf_generation"] = dict(pdf_gen)


def publish_and_log_pdf_generation(
    pdf_gen: dict[str, Any],
    *,
    log_json: bool = True,
) -> None:
    set_last_pdf_generation_telemetry(pdf_gen)
    lines = format_pdf_generation_lines(pdf_gen)
    print(lines, flush=True)
    if log_json:
        try:
            log.info("[openai_pdf_telemetry] pdf_generation=%s", json.dumps(pdf_gen, default=str))
        except Exception:
            log.info("[openai_pdf_telemetry] pdf_generation=(unserializable)")
    if _premium_telemetry_json_enabled():
        _write_telemetry_json_file(pdf_gen)


def _premium_telemetry_json_enabled() -> bool:
    return os.environ.get("COMPAT_PREMIUM_PDF_TELEMETRY_JSON", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _telemetry_json_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "_premium_pdf_telemetry_last.json")


def _write_telemetry_json_file(pdf_gen: dict[str, Any]) -> None:
    path = _telemetry_json_path()
    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(pdf_gen, fh, indent=2, ensure_ascii=False, default=str)
    except Exception as exc:
        log.warning("[openai_pdf_telemetry] debug json write fail path=%s err=%s", path, exc)


def format_pdf_generation_lines(pdf_gen: dict[str, Any]) -> str:
    fb = "YES" if pdf_gen.get("fallback_used") else "NO"
    sk = "YES" if pdf_gen.get("openai_skipped") else "NO"
    ch = "YES" if pdf_gen.get("cache_hit") else "NO"
    pdf_st = pdf_gen.get("pdf_render_status") or "UNKNOWN"
    return (
        "──────── PDF / OPENAI GENERATION TELEMETRY ────────\n"
        f"MODEL: {pdf_gen.get('model')}\n"
        f"INPUT TOKENS: {pdf_gen.get('input_tokens')}\n"
        f"OUTPUT TOKENS: {pdf_gen.get('output_tokens')}\n"
        f"TOTAL TOKENS: {pdf_gen.get('total_tokens')}\n"
        f"ESTIMATED COST: ${float(pdf_gen.get('estimated_cost_usd') or 0):.4f} USD\n"
        f"ESTIMATED COST: ₹{float(pdf_gen.get('estimated_cost_inr') or 0):.2f} INR "
        f"(rate {float(pdf_gen.get('usd_inr_rate') or _usd_inr_rate()):.2f} INR/USD)\n"
        f"OPENAI CALLS: {pdf_gen.get('openai_call_count')}\n"
        f"RETRY COUNT: {pdf_gen.get('retry_count')}\n"
        f"REGEN COUNT: {pdf_gen.get('regen_count')}\n"
        f"VALIDATOR ATTEMPTS: {pdf_gen.get('validator_attempts')}\n"
        f"CACHE HIT: {ch}\n"
        f"OPENAI SKIPPED: {sk}\n"
        f"FALLBACK USED: {fb}\n"
        f"PRICING SOURCE: {pdf_gen.get('pricing_source')}\n"
        f"PDF RENDER STATUS: {pdf_st}\n"
        f"FINAL STATUS: {pdf_gen.get('final_status')}\n"
        "──────────────────────────────────────────────────"
    )


def response_telemetry_headers(pdf_gen: dict[str, Any]) -> dict[str, str]:
    """Optional HTTP headers for PDF responses (safe ASCII)."""
    try:
        cost = float(pdf_gen.get("estimated_cost_usd") or 0.0)
    except (TypeError, ValueError):
        cost = 0.0
    return {
        "X-Cosmic-PDF-Gen-Cost-USD": f"{cost:.6f}",
        "X-Cosmic-PDF-Gen-Model": str(pdf_gen.get("model") or "")[:80],
        "X-Cosmic-PDF-Gen-Total-Tokens": str(int(pdf_gen.get("total_tokens") or 0)),
        "X-Cosmic-PDF-Gen-Final-Status": str(pdf_gen.get("final_status") or "")[:80],
    }
