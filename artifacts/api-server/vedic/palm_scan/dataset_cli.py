"""Command-line interface for palm dataset annotation tooling."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .dataset import (
    create_manifest,
    dataset_statistics,
    grouped_split,
    load_manifest,
    rasterize_sample,
    save_manifest,
    line_supervision_weights,
    validate_local_assets,
    validate_manifest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Palm dataset tools (no model accuracy claims).")
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="create an empty versioned manifest")
    init.add_argument("output")
    init.add_argument("--dataset-id", required=True)
    init.add_argument("--version", default="1.0")
    init.add_argument("--force", action="store_true")

    add = commands.add_parser("add", help="validate and append a sample JSON object")
    add.add_argument("manifest")
    add.add_argument("sample")
    add.add_argument("--output")
    add.add_argument("--force", action="store_true")

    validate = commands.add_parser("validate", help="validate a dataset manifest")
    validate.add_argument("manifest")
    validate.add_argument("--assets", action="store_true")
    validate.add_argument("--asset-root")
    validate.add_argument("--reject-remote", action="store_true")

    split = commands.add_parser("split", help="create deterministic subject-grouped splits")
    split.add_argument("manifest")
    split.add_argument("output")
    split.add_argument("--seed", type=int, default=1337)
    split.add_argument("--train", type=float, default=.70)
    split.add_argument("--val", type=float, default=.15)
    split.add_argument("--test", type=float, default=.15)
    split.add_argument("--force", action="store_true")

    stats = commands.add_parser("stats", help="print annotation and split statistics")
    stats.add_argument("manifest")

    raster = commands.add_parser("rasterize", help="export semantic targets as compressed NPZ")
    raster.add_argument("manifest")
    raster.add_argument("output_dir")
    raster.add_argument("--height", type=int, default=256)
    raster.add_argument("--width", type=int, default=256)
    raster.add_argument("--landmark-heatmaps", action="store_true")
    raster.add_argument("--asset-root")
    raster.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "init":
            save_manifest(
                create_manifest(args.dataset_id, args.version),
                args.output,
                overwrite=args.force,
            )
        elif args.command == "add":
            manifest = load_manifest(args.manifest)
            sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
            manifest["samples"].append(sample)
            destination = args.output or args.manifest
            save_manifest(manifest, destination, overwrite=args.force)
        elif args.command == "validate":
            raw = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
            errors = validate_manifest(raw)
            if not errors and args.assets:
                root = args.asset_root or Path(args.manifest).resolve().parent
                errors = validate_local_assets(
                    raw, root, reject_remote=args.reject_remote
                )
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 2
            print("valid")
        elif args.command == "split":
            output = grouped_split(
                load_manifest(args.manifest),
                seed=args.seed,
                train=args.train,
                val=args.val,
                test=args.test,
            )
            save_manifest(output, args.output, overwrite=args.force)
        elif args.command == "stats":
            print(json.dumps(dataset_statistics(load_manifest(args.manifest)), indent=2, sort_keys=True))
        elif args.command == "rasterize":
            manifest = load_manifest(args.manifest)
            asset_root = args.asset_root or Path(args.manifest).resolve().parent
            asset_errors = validate_local_assets(
                manifest, asset_root, reject_remote=False
            )
            if asset_errors:
                raise ValueError(
                    "asset preflight failed: " + "; ".join(asset_errors)
                )
            output_dir = Path(args.output_dir)
            if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
                raise FileExistsError(f"Refusing to write into non-empty directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            for sample in manifest["samples"]:
                targets, classes = rasterize_sample(
                    sample,
                    (args.height, args.width),
                    asset_root=asset_root,
                    include_landmarks=args.landmark_heatmaps,
                )
                destination = output_dir / f"{sample['image']['id']}.npz"
                if destination.exists() and not args.force:
                    raise FileExistsError(f"Refusing to overwrite: {destination}")
                np.savez_compressed(
                    destination,
                    targets=targets,
                    line_supervision=line_supervision_weights(sample),
                    class_order=np.asarray(classes),
                    image_id=np.asarray(sample["image"]["id"]),
                    split=np.asarray(sample["split"]),
                )
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
