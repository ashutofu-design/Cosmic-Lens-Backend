#!/usr/bin/env python3
"""Fetch Noto Sans Devanagari static TTFs from notofonts GitHub releases into fonts/noto/.

Run from repo root or anywhere:

  python artifacts/api-server/scripts/download_noto_indic_for_milan_pdf.py

Requires network. OFL-licensed fonts. Restart the API after download so
register_indic_fonts() picks up new files.

(Compatibility Pro PDF supports Hindi देवनागरी only for native-script rendering.)
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

_API_SERVER_ROOT = Path(__file__).resolve().parents[1]
_DEST = _API_SERVER_ROOT / "fonts" / "noto"

_GITHUB_RELEASE_JSON = "https://api.github.com/repos/notofonts/{repo}/releases/latest"

# notofonts org repo slug → zip basename prefix for NotoSans*.ttf files
_REPOS: tuple[tuple[str, str], ...] = (
    ("devanagari", "NotoSansDevanagari"),
)


def _http_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CosmicLens-MilanPDF-FontFetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def _http_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CosmicLens-MilanPDF-FontFetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read()


def _pick_members(zipf: zipfile.ZipFile, prefix: str) -> tuple[str | None, str | None]:
    """Return (regular_zip_path, bold_zip_path) for ReportLab."""
    reg = med = semi = xbold = bold_exact = None
    for name in zipf.namelist():
        if not name.endswith(".ttf"):
            continue
        base = os.path.basename(name)
        if not base.startswith(prefix):
            continue
        if base.endswith("-Regular.ttf"):
            reg = name
        elif base.endswith("-Medium.ttf"):
            med = name
        elif base.endswith("-Bold.ttf"):
            bold_exact = name
        elif base.endswith("-SemiBold.ttf"):
            semi = name
        elif base.endswith("-ExtraBold.ttf"):
            xbold = name
    reg_use = reg or med
    bold_use = bold_exact or semi or xbold
    return reg_use, bold_use


def main() -> int:
    _DEST.mkdir(parents=True, exist_ok=True)
    print(f"Destination: {_DEST}", flush=True)
    ok = 0
    for repo, prefix in _REPOS:
        meta_url = _GITHUB_RELEASE_JSON.format(repo=repo)
        print(f"Release {repo} …", flush=True)
        try:
            rel = _http_json(meta_url)
        except urllib.error.HTTPError as exc:
            print(f"  FAIL api {meta_url}: {exc}", flush=True)
            continue
        assets = rel.get("assets") or []
        z_url = None
        for a in assets:
            if str(a.get("name", "")).endswith(".zip"):
                z_url = a.get("browser_download_url")
                break
        if not z_url:
            print(f"  SKIP no .zip asset", flush=True)
            continue
        try:
            raw = _http_bytes(z_url)
        except urllib.error.HTTPError as exc:
            print(f"  FAIL download {z_url}: {exc}", flush=True)
            continue
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            reg_m, bold_m = _pick_members(zf, prefix)
            if not reg_m:
                print(f"  SKIP no Regular/Medium for {prefix}", flush=True)
                continue
            written = []
            for member in (reg_m, bold_m):
                if not member:
                    continue
                data = zf.read(member)
                out_path = _DEST / os.path.basename(member)
                out_path.write_bytes(data)
                written.append(str(out_path))
            print(f"  OK wrote {written}", flush=True)
            ok += 1
    print(f"Done repos_ok={ok}/{len(_REPOS)}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
