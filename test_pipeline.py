"""
Brain Tumor Classification — End-to-End Pipeline Test

Verifies:
  1. Dataset integrity
  2. Model architecture builds correctly
  3. Forward pass works
  4. Training runs (1 epoch smoke test)
  5. Weights save/load cycle
  6. Inference produces valid predictions
  7. Predictions match expected format
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import numpy as np
import torch
from torchvision import transforms, datasets

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from model import (
    build_model,
    load_trained_model,
    BrainTumorClassifier,
    IMG_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    CATEGORIES,
    CATEGORY_LABELS,
)


def test_passed(name):
    print(f"  [PASS]: {name}")
    return True


def test_failed(name, error=""):
    print(f"  [FAIL]: {name}")
    if error:
        print(f"         {error}")
    return False


def run_tests():
    """Run all pipeline tests."""
    print("=" * 60)
    print("  Brain Tumor Classification — Pipeline Tests")
    print("=" * 60)

    results = []
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n  Device: {device}")

    # ── Test 1: Dataset exists ─────────────────
    print(f"\n{'─' * 50}")
    print("  Test 1: Dataset Integrity")
    print(f"{'─' * 50}")

    base = Path(__file__).parent
    dataset_candidates = [
        base / "dataset" / "Brain-Tumor-Classification-DataSet",
        base / "Brain-Tumor-Classification-DataSet",
    ]

    dataset_dir = None
    for candidate in dataset_candidates:
        if (candidate / "Training").exists():
            dataset_dir = candidate
            break

    if dataset_dir is None:
        results.append(test_failed("Dataset found", "Run 'python download_dataset.py' first"))
    else:
        results.append(test_passed("Dataset found"))

        # Check structure
        train_dir = dataset_dir / "Training"
        test_dir = dataset_dir / "Testing"

        for split_name, split_dir in [("Training", train_dir), ("Testing", test_dir)]:
            if split_dir.exists():
                categories = [d.name for d in split_dir.iterdir() if d.is_dir()]
                total = sum(len(list((split_dir / c).glob("*"))) for c in categories)
                results.append(test_passed(f"{split_name} directory ({total} images, {len(categories)} classes)"))
            else:
                results.append(test_failed(f"{split_name} directory", "Missing"))

    # ── Test 2: Model Architecture ─────────────
    print(f"\n{'─' * 50}")
    print("  Test 2: Model Architecture")
    print(f"{'─' * 50}")

    try:
        model = BrainTumorClassifier(pretrained=False)
        total_params = sum(p.numel() for p in model.parameters())
        results.append(test_passed(f"Model builds ({total_params:,} params)"))
    except Exception as e:
        results.append(test_failed("Model builds", str(e)))
        model = None

    # ── Test 3: Forward Pass ───────────────────
    print(f"\n{'─' * 50}")
    print("  Test 3: Forward Pass")
    print(f"{'─' * 50}")

    if model is not None:
        try:
            model = model.to(device)
            x = torch.randn(2, 3, IMG_SIZE, IMG_SIZE).to(device)
            with torch.no_grad():
                out = model(x)
            assert out.shape == (2, 4), f"Expected (2, 4), got {out.shape}"
            probs = torch.softmax(out, dim=1)
            assert torch.allclose(probs.sum(dim=1), torch.ones(2).to(device), atol=1e-5)
            results.append(test_passed(f"Forward pass (output shape: {out.shape})"))
        except Exception as e:
            results.append(test_failed("Forward pass", str(e)))

    # ── Test 4: Freeze/Unfreeze ────────────────
    print(f"\n{'─' * 50}")
    print("  Test 4: Backbone Freeze/Unfreeze")
    print(f"{'─' * 50}")

    if model is not None:
        try:
            model.freeze_backbone()
            frozen_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

            model.unfreeze_backbone(-2)
            partial_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)

            assert frozen_trainable < partial_trainable, "Unfreeze should increase trainable params"
            results.append(test_passed(f"Freeze ({frozen_trainable:,}) → Unfreeze ({partial_trainable:,})"))
        except Exception as e:
            results.append(test_failed("Backbone freeze/unfreeze", str(e)))

    # ── Test 5: Save/Load Cycle ────────────────
    print(f"\n{'─' * 50}")
    print("  Test 5: Weight Save/Load Cycle")
    print(f"{'─' * 50}")

    if model is not None:
        try:
            # Save
            tmp_dir = base / "weights" / "_test_temp"
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / "test_model.pth"

            torch.save({
                "epoch": 0,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": {},
                "val_loss": 0.5,
                "val_accuracy": 0.85,
            }, tmp_path)

            results.append(test_passed(f"Weights saved ({tmp_path.stat().st_size / 1e6:.1f}MB)"))

            # Load
            loaded_model, _ = load_trained_model(str(tmp_path), device=device)

            # Compare outputs
            x = torch.randn(1, 3, IMG_SIZE, IMG_SIZE).to(device)
            with torch.no_grad():
                model.eval()
                out1 = model(x)
                out2 = loaded_model(x)

            assert torch.allclose(out1, out2, atol=1e-5), "Loaded model produces different output"
            results.append(test_passed("Weights loaded and verified"))

            # Cleanup
            shutil.rmtree(tmp_dir)

        except Exception as e:
            results.append(test_failed("Save/Load cycle", str(e)))

    # ── Test 6: Inference Transform ────────────
    print(f"\n{'─' * 50}")
    print("  Test 6: Inference Transform Pipeline")
    print(f"{'─' * 50}")

    try:
        from predict import validate_image, get_inference_transform, predict_single
        from PIL import Image

        # Create a dummy RGB image
        dummy_img = Image.fromarray(np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8))
        transform = get_inference_transform()
        tensor = transform(dummy_img)
        assert tensor.shape == (3, IMG_SIZE, IMG_SIZE), f"Expected (3, {IMG_SIZE}, {IMG_SIZE}), got {tensor.shape}"
        results.append(test_passed(f"Transform pipeline (output: {tensor.shape})"))

        # Test grayscale conversion
        gray_img = Image.fromarray(np.random.randint(0, 255, (300, 300), dtype=np.uint8), mode="L")
        gray_rgb = gray_img.convert("RGB")
        tensor_gray = transform(gray_rgb)
        assert tensor_gray.shape == (3, IMG_SIZE, IMG_SIZE)
        results.append(test_passed("Grayscale → RGB conversion"))

        # Test prediction with dummy
        if model is not None:
            pred_class, probs = predict_single(model, device, dummy_img, transform)
            assert 0 <= pred_class <= 3
            assert abs(sum(probs) - 1.0) < 1e-5
            assert pred_class in CATEGORY_LABELS
            results.append(test_passed(f"Prediction: {CATEGORY_LABELS[pred_class]} ({probs[pred_class]:.2%})"))

    except Exception as e:
        results.append(test_failed("Inference transform", str(e)))

    # ── Test 7: Smoke Training (1 epoch) ───────
    print(f"\n{'─' * 50}")
    print("  Test 7: Smoke Training (1 epoch)")
    print(f"{'─' * 50}")

    if dataset_dir is not None:
        try:
            from train import create_data_loaders, train_one_epoch, validate

            test_model = BrainTumorClassifier(pretrained=False).to(device)
            test_model.freeze_backbone()

            train_loader, val_loader, test_loader, class_weights, class_names = create_data_loaders(
                str(dataset_dir / "Training"),
                str(dataset_dir / "Testing"),
                batch_size=8, val_split=0.2, seed=42, num_workers=0,
            )

            criterion = torch.nn.CrossEntropyLoss(weight=class_weights.to(device))
            optimizer = torch.optim.Adam(
                filter(lambda p: p.requires_grad, test_model.parameters()),
                lr=1e-3,
            )

            train_loss, train_acc = train_one_epoch(
                test_model, train_loader, criterion, optimizer, device,
            )
            val_loss, val_acc = validate(test_model, val_loader, criterion, device)

            results.append(test_passed(
                f"1-epoch train: loss={train_loss:.4f} acc={train_acc:.4f} | "
                f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
            ))

        except Exception as e:
            results.append(test_failed("Smoke training", str(e)))
    else:
        results.append(test_failed("Smoke training", "Dataset not available"))

    # ── Test 8: Trained Weights Exist ──────────
    print(f"\n{'─' * 50}")
    print("  Test 8: Trained Model Weights")
    print(f"{'─' * 50}")

    weights_path = base / "weights" / "best_model.pth"
    if weights_path.exists():
        try:
            ckpt = torch.load(weights_path, map_location="cpu", weights_only=False)
            epoch = ckpt.get("epoch", "?")
            val_acc = ckpt.get("val_accuracy", 0)
            results.append(test_passed(f"best_model.pth exists (epoch {epoch}, val_acc: {val_acc:.4f})"))
        except Exception as e:
            results.append(test_failed("Load best_model.pth", str(e)))
    else:
        results.append(test_failed("best_model.pth exists", "Run 'python train.py' to train"))

    # ── Summary ────────────────────────────────
    print(f"\n{'=' * 60}")
    passed = sum(results)
    total = len(results)
    status = "ALL PASSED" if passed == total else f"{passed}/{total} PASSED"
    print(f"  Results: {status}")
    print(f"{'=' * 60}")

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
