"""Copy user-provided Pukhraj gallery photos into app bundle + API media."""
from __future__ import annotations

import os
import subprocess
import sys

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image

SRC = r"C:\Users\HP\.cursor\projects\d-Cosmic-Lens-Backend\assets"
# User order: 1 hero, 2 cushion, 3 wear, 4 lifestyle
GALLERY: list[tuple[str, str, str | None]] = [
    ("3a7ea633-50e7-40f9-bf92-bdfea5c3b766", "pukhraj-hero.png", "4796d852-8044-4544-a563-e1c7cbc77000"),
    ("0ecbfeaa-9ce2-47f9-a207-3e71ff4a2e35", "pukhraj-cushion.png", None),
    ("4796d852-8044-4544-a563-e1c7cbc77000", "pukhraj-wear.png", None),
    ("14a75558-946c-4185-a751-15d72f7c34b5", "pukhraj-lifestyle.png", None),
]
DESTS = [
    r"d:\Cosmic-Lens-Backend\artifacts\cosmic-lens-mobile\assets\gemstones",
    r"d:\Cosmic-Lens-Backend\artifacts\api-server\gemstone_media",
]


def win_path(path: str) -> str:
    if os.name == "nt":
        abs_path = os.path.abspath(path)
        if not abs_path.startswith("\\\\?\\"):
            return "\\\\?\\" + abs_path
    return path


def find_src(suffix: str) -> str | None:
    if not os.path.isdir(SRC):
        return None
    for dirpath, _, files in os.walk(SRC):
        for name in files:
            if suffix in name:
                full = os.path.join(dirpath, name)
                if os.path.isfile(full):
                    return full
    return None


def resolve_src(suffix: str, fallback: str | None) -> str:
    src = find_src(suffix)
    if src:
        return src
    if fallback:
        src = find_src(fallback)
        if src:
            return src
    raise FileNotFoundError(f"No file matching *{suffix}* in {SRC}")


def write_png(src: str, dst: str) -> None:
    with Image.open(win_path(src)) as im:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
        im.save(win_path(dst), format="PNG")


def main() -> None:
    for dest_root in DESTS:
        os.makedirs(dest_root, exist_ok=True)

    for suffix, out_name, fallback in GALLERY:
        src = resolve_src(suffix, fallback)
        for dest_root in DESTS:
            dst = os.path.join(dest_root, out_name)
            write_png(src, dst)
            print(f"{os.path.basename(src)} -> {dst} ({os.path.getsize(dst)} bytes)")

    print("done", len(GALLERY), "gallery images")


if __name__ == "__main__":
    main()
