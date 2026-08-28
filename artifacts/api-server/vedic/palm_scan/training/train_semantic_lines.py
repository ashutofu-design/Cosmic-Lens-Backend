"""Train a small semantic palm-line U-Net (optional PyTorch dependency).

This script reports validation measurements only when run against a real,
user-supplied manifest. It does not ship weights or auto-enable a model.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from ..dataset import (
    DEFAULT_FAINT_WEIGHT,
    LINE_CLASSES,
    PREPROCESSING_VERSION,
    calibrate_thresholds_numpy,
    line_supervision_weights,
    load_manifest,
    manifest_hash,
    rasterize_sample,
    resolve_asset_path,
    semantic_metrics_numpy,
    validate_local_assets,
)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.backends.cudnn.benchmark = False


class PalmLineDataset(Dataset):
    def __init__(
        self, manifest: dict, manifest_path: Path, split: str,
        size: int = 256, augment: bool = False,
        faint_weight: float = DEFAULT_FAINT_WEIGHT,
    ):
        self.samples = [sample for sample in manifest["samples"] if sample["split"] == split]
        self.root = manifest_path.resolve().parent
        self.size = size
        self.augment = augment
        self.faint_weight = faint_weight

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        sample = self.samples[index]
        relative = sample["image"].get("path")
        if relative is None:
            raise ValueError(
                "offline training rejects URI samples; materialize a local image.path"
            )
        image_path = resolve_asset_path(self.root, relative)
        bgr = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if bgr is None:
            raise OSError(f"unable to read image: {image_path}")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (self.size, self.size), interpolation=cv2.INTER_AREA)
        target, _ = rasterize_sample(
            sample, (self.size, self.size), asset_root=self.root
        )
        target = target[:len(LINE_CLASSES)]
        supervision = line_supervision_weights(
            sample, faint_weight=self.faint_weight
        )
        if self.augment:
            # Photometric-only augmentation preserves handedness and all geometry.
            gain = float(np.random.uniform(.88, 1.12))
            bias = float(np.random.uniform(-10, 10))
            rgb = np.uint8(np.clip(rgb.astype(np.float32) * gain + bias, 0, 255))
            if np.random.random() < .35:
                rgb = cv2.GaussianBlur(rgb, (3, 3), float(np.random.uniform(.1, .7)))
        image = rgb.astype(np.float32) / 255.0
        image = (image - np.asarray((.485, .456, .406), np.float32)) / np.asarray(
            (.229, .224, .225), np.float32
        )
        return (
            torch.from_numpy(np.transpose(image, (2, 0, 1))).float(),
            torch.from_numpy(target).float(),
            torch.from_numpy(supervision).float(),
        )


class ConvBlock(nn.Module):
    def __init__(self, input_channels: int, output_channels: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Conv2d(input_channels, output_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(output_channels, output_channels, 3, padding=1, bias=False),
            nn.BatchNorm2d(output_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return self.layers(value)


class SmallUNet(nn.Module):
    def __init__(self, classes: int = len(LINE_CLASSES), base: int = 24):
        super().__init__()
        self.enc1 = ConvBlock(3, base)
        self.enc2 = ConvBlock(base, base * 2)
        self.enc3 = ConvBlock(base * 2, base * 4)
        self.pool = nn.MaxPool2d(2)
        self.bottleneck = ConvBlock(base * 4, base * 8)
        self.up3 = nn.ConvTranspose2d(base * 8, base * 4, 2, 2)
        self.dec3 = ConvBlock(base * 8, base * 4)
        self.up2 = nn.ConvTranspose2d(base * 4, base * 2, 2, 2)
        self.dec2 = ConvBlock(base * 4, base * 2)
        self.up1 = nn.ConvTranspose2d(base * 2, base, 2, 2)
        self.dec1 = ConvBlock(base * 2, base)
        self.output = nn.Conv2d(base, classes, 1)

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        first = self.enc1(value)
        second = self.enc2(self.pool(first))
        third = self.enc3(self.pool(second))
        center = self.bottleneck(self.pool(third))
        value = self.dec3(torch.cat((self.up3(center), third), dim=1))
        value = self.dec2(torch.cat((self.up2(value), second), dim=1))
        value = self.dec1(torch.cat((self.up1(value), first), dim=1))
        return self.output(value)


def bce_dice_loss(
    logits: torch.Tensor, targets: torch.Tensor, supervision: torch.Tensor
) -> torch.Tensor:
    weights = supervision.to(logits.dtype)
    denominator_weight = weights.sum()
    if float(denominator_weight.detach().cpu()) == 0:
        return logits.sum() * 0.0
    bce_per_pixel = nn.functional.binary_cross_entropy_with_logits(
        logits, targets, reduction="none"
    )
    bce_per_class = bce_per_pixel.mean(dim=(2, 3))
    bce = (bce_per_class * weights).sum() / denominator_weight
    probabilities = torch.sigmoid(logits)
    intersection = (probabilities * targets).sum(dim=(2, 3))
    denominator = probabilities.sum(dim=(2, 3)) + targets.sum(dim=(2, 3))
    dice_per_class = 1.0 - (2.0 * intersection + 1.0) / (denominator + 1.0)
    dice_loss = (dice_per_class * weights).sum() / denominator_weight
    return bce + dice_loss


def _validate(
    model: nn.Module, loader: DataLoader, device: torch.device
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    probabilities, targets, supervision = [], [], []
    model.eval()
    with torch.no_grad():
        for images, truth, weights in loader:
            probabilities.append(torch.sigmoid(model(images.to(device))).cpu().numpy())
            targets.append(truth.numpy())
            supervision.append(weights.numpy())
    return (
        np.concatenate(probabilities),
        np.concatenate(targets),
        np.concatenate(supervision),
    )


def train(args: argparse.Namespace) -> dict:
    seed_everything(args.seed)
    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    asset_root = Path(args.asset_root).resolve() if args.asset_root else manifest_path.resolve().parent
    asset_errors = validate_local_assets(
        manifest, asset_root, reject_remote=True,
        require_training_consent=True,
    )
    if asset_errors:
        raise ValueError("asset preflight failed: " + "; ".join(asset_errors))
    train_data = PalmLineDataset(
        manifest, manifest_path, "train", args.size, augment=True,
        faint_weight=args.faint_weight,
    )
    val_data = PalmLineDataset(
        manifest, manifest_path, "val", args.size, augment=False,
        faint_weight=args.faint_weight,
    )
    train_data.root = val_data.root = asset_root
    if not train_data or not val_data:
        raise ValueError("manifest requires non-empty grouped train and val splits")
    if not any(np.any(
        line_supervision_weights(sample, faint_weight=args.faint_weight) > 0
    ) for sample in train_data.samples):
        raise ValueError(
            "train split has no supervised clear/faint semantic line labels"
        )
    if not any(np.any(
        line_supervision_weights(sample, faint_weight=args.faint_weight) > 0
    ) for sample in val_data.samples):
        raise ValueError(
            "validation split has no supervised clear/faint semantic line labels"
        )
    generator = torch.Generator().manual_seed(args.seed)
    train_loader = DataLoader(
        train_data, batch_size=args.batch_size, shuffle=True,
        num_workers=args.workers, generator=generator,
    )
    val_loader = DataLoader(val_data, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)
    device = torch.device(args.device)
    model = SmallUNet(base=args.base_channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    best_loss = float("inf")
    checkpoint = output / "best.pt"
    for epoch in range(args.epochs):
        model.train()
        losses = []
        for images, targets, supervision in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = bce_dice_loss(
                model(images.to(device)), targets.to(device), supervision.to(device)
            )
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        probabilities, targets, supervision = _validate(model, val_loader, device)
        logits = np.log(np.clip(probabilities, 1e-7, 1 - 1e-7) / np.clip(1 - probabilities, 1e-7, 1))
        val_loss = float(bce_dice_loss(
            torch.from_numpy(logits),
            torch.from_numpy(targets),
            torch.from_numpy(supervision),
        ))
        print(json.dumps({"epoch": epoch + 1, "train_loss": float(np.mean(losses)), "val_loss": val_loss}))
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save({"model": model.state_dict(), "epoch": epoch + 1, "val_loss": val_loss}, checkpoint)
    state = torch.load(checkpoint, map_location=device)
    model.load_state_dict(state["model"])
    probabilities, targets, supervision = _validate(model, val_loader, device)
    calibration = calibrate_thresholds_numpy(
        probabilities, targets, supervision
    )
    thresholds = {
        name: (
            float(calibration[name]["threshold"])
            if calibration[name]["status"] == "evaluated" else .5
        )
        for name in LINE_CLASSES
    }
    validation_metrics = semantic_metrics_numpy(
        probabilities, targets, supervision, thresholds
    )
    model.eval()
    onnx_path = output / "semantic_palm_lines.onnx"
    torch.onnx.export(
        model,
        torch.zeros(1, 3, args.size, args.size, device=device),
        onnx_path,
        input_names=["rgb"], output_names=["line_logits"],
        dynamic_axes={"rgb": {0: "batch"}, "line_logits": {0: "batch"}},
        opset_version=17,
    )
    metadata = {
        "model_version": args.model_version,
        "trained": True,
        "class_order": list(LINE_CLASSES),
        "preprocessing_version": PREPROCESSING_VERSION,
        "dataset_manifest_sha256": manifest_hash(manifest),
        "thresholds": thresholds,
        "calibration": "held_out_validation_dice_threshold_grid",
        "calibration_by_class": calibration,
        "validation_metrics": validation_metrics,
        "validation_sample_count": len(val_data),
        "seed": args.seed,
        "onnx_opset": 17,
        "output_activation": "logits",
        "input": {
            "width": args.size, "height": args.size, "channels": 3,
            "color_order": "RGB",
        },
        "normalization": {
            "scale": 1.0 / 255.0,
            "mean": [.485, .456, .406],
            "std": [.229, .224, .225],
        },
        "class_weights": {name: 1.0 for name in LINE_CLASSES},
        "supervision_policy": {
            "clear": 1.0,
            "faint": args.faint_weight,
            "unknown": 0.0,
            "occluded": 0.0,
            "occluded_policy": "ignored_no_complete_visible_partial_policy",
        },
        "note": "Metrics describe this supplied validation split only; they are not a production accuracy claim.",
    }
    metadata_path = onnx_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("output_dir")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--size", type=int, default=256)
    parser.add_argument("--base-channels", type=int, default=24)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--model-version", default="semantic-palm-lines/1.0")
    parser.add_argument("--faint-weight", type=float, default=DEFAULT_FAINT_WEIGHT)
    parser.add_argument("--asset-root")
    args = parser.parse_args()
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    train(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
