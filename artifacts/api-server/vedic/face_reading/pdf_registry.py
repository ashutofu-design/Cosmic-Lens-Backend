"""
L4 PDF artifact registry — true bypass (no assemble, no AI, no rerender).

Wraps face:pdf:{analysis_id}:{lang} with render version + checksum validation.
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from . import face_cache as _fc
from .report_version import PDF_RENDER_VERSION, pdf_render_cache_valid

log = logging.getLogger(__name__)


@dataclass
class PdfArtifact:
    analysis_id: str
    lang: str
    path: str
    filename: str
    ledger_id: str
    size_bytes: int
    checksum: str
    render_version: str
    narration_version: str
    created_at: float
    pdf_bytes: Optional[bytes] = None

    @property
    def cache_tier(self) -> str:
        return "L4-pdf-artifact"


def _file_checksum(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def register(
    analysis_id: str,
    lang: str,
    *,
    ledger_id: str,
    path: str,
    filename: str,
    size_bytes: int,
    narration_version: str = "",
) -> bool:
    """Persist artifact metadata after render."""
    if not os.path.isfile(path):
        return False
    try:
        checksum = _file_checksum(path)
    except Exception:
        checksum = ""
    meta = {
        "ledger_id": ledger_id,
        "path": path,
        "filename": filename,
        "size_bytes": size_bytes,
        "checksum": checksum,
        "render_version": PDF_RENDER_VERSION,
        "narration_version": narration_version,
        "created_at": time.time(),
        "valid": True,
    }
    ok = _fc.put_pdf_meta(
        analysis_id,
        lang,
        ledger_id=ledger_id,
        path=path,
        filename=filename,
        size_bytes=size_bytes,
    )
    if ok:
        _fc.put_pdf_artifact_extras(analysis_id, lang, meta)
        log.info(
            "[pdf_registry] registered %s/%s chk=%s…",
            analysis_id[:8],
            lang,
            checksum[:8],
        )
    return ok


def get_meta(analysis_id: str, lang: str) -> Optional[Dict[str, Any]]:
    base = _fc.get_pdf_meta(analysis_id, lang) or {}
    extra = _fc.get_pdf_artifact_extras(analysis_id, lang) or {}
    return {**base, **extra} if base or extra else None


def is_valid(meta: Dict[str, Any], *, require_file: bool = True) -> bool:
    if not meta or not meta.get("valid", True):
        return False
    if not pdf_render_cache_valid(meta.get("render_version")):
        return False
    path = meta.get("path") or ""
    if require_file and (not path or not os.path.isfile(path)):
        return False
    if meta.get("checksum") and path:
        try:
            if _file_checksum(path) != meta["checksum"]:
                log.warning("[pdf_registry] checksum mismatch %s", path[:48])
                return False
        except Exception:
            return False
    return True


def try_bypass(
    analysis_id: str,
    lang: str,
    *,
    load_bytes: bool = True,
) -> Optional[PdfArtifact]:
    """
    True PDF bypass — stream artifact with zero assemble/AI/render work.
    """
    if not analysis_id:
        return None
    meta = get_meta(analysis_id, lang)
    if not meta or not is_valid(meta):
        return None

    path = meta["path"]
    pdf_bytes = None
    if load_bytes:
        with open(path, "rb") as f:
            pdf_bytes = f.read()

    return PdfArtifact(
        analysis_id=analysis_id,
        lang=lang,
        path=path,
        filename=meta.get("filename") or "cosmic_lens_face_report.pdf",
        ledger_id=meta.get("ledger_id") or "",
        size_bytes=int(meta.get("size_bytes") or 0),
        checksum=meta.get("checksum") or "",
        render_version=meta.get("render_version") or PDF_RENDER_VERSION,
        narration_version=meta.get("narration_version") or "",
        created_at=float(meta.get("created_at") or meta.get("cached_at") or 0),
        pdf_bytes=pdf_bytes,
    )


def invalidate(analysis_id: str, lang: Optional[str] = None) -> None:
    """Drop L4 for analysis (e.g. narration version bump)."""
    if lang:
        _fc.delete_pdf_artifact(analysis_id, lang)
    else:
        for code in ("en", "hi", "hinglish"):
            _fc.delete_pdf_artifact(analysis_id, code)
