"""
Brain Tumor Classification — Training Pipeline

Complete training script with:
  - EfficientNetB3 transfer learning (2-phase: frozen → fine-tune)
  - Data augmentation (RandomResizedCrop, flip, rotation, color jitter)
  - Class-weighted loss for handling class imbalance
  - Learning rate scheduling (ReduceLROnPlateau)
  - Early stopping
  - Best model checkpoint saving
  - Classification report on test set
  - Training history plots
"""
import os
import sys
import time
import argparse
import json
from pathlib import Path
from collections import Counter

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import classification_report, confusion_matrix

from model import (
    build_model,
    IMAGENET_MEAN,
    IMAGENET_STD,
    IMG_SIZE,
    CATEGORIES,
    CATEGORY_LABELS,
)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DEFAULTS = {
    "train_dir": None,  # Auto-detected
    "test_dir": None,  # Auto-detected
    "weights_dir": "weights",
    "batch_size": 16,
    "epochs_phase1": 10,  # Frozen backbone
    "epochs_phase2": 25,  # Fine-tuning
    "lr_phase1": 1e-3,
    "lr_phase2": 1e-4,
    "patience": 7,
    "val_split": 0.2,
    "num_workers": 0,  # Windows-compatible default
    "seed": 42,
}


def get_data_dirs():
    """Auto-detect dataset directories."""
    base = Path(__file__).parent
    candidates = [
        base / "dataset" / "Brain-Tumor-Classification-DataSet",
        base / "Brain-Tumor-Classification-DataSet",
        base / "dataset",
    ]

    for candidate in candidates:
        train = candidate / "Training"
        test = candidate / "Testing"
        if train.exists() and test.exists():
            return str(train), str(test)

    return None, None


def get_transforms():
    """Return training and validation/test transforms."""
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(IMG_SIZE, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.3),
        transforms.RandomRotation(20),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1), shear=10),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
        transforms.RandomGrayscale(p=0.1),
        transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.1)),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    return train_transform, val_transform


def create_data_loaders(train_dir, test_dir, batch_size, val_split, seed, num_workers):
    """
    Create train, validation, and test data loaders.
    Validation set is split from training data using stratified sampling.
    """
    train_transform, val_transform = get_transforms()

    # Load full training dataset (with val transform to get labels for stratification)
    full_dataset = datasets.ImageFolder(train_dir, transform=train_transform)

    # Get labels for stratified split
    labels = [sample[1] for sample in full_dataset.samples]

    # Stratified split
    sss = StratifiedShuffleSplit(n_splits=1, test_size=val_split, random_state=seed)
    train_idx, val_idx = next(sss.split(np.zeros(len(labels)), labels))

    # Create train subset (with augmentation)
    train_subset = Subset(full_dataset, train_idx)

    # Create validation subset (without augmentation)
    val_dataset = datasets.ImageFolder(train_dir, transform=val_transform)
    val_subset = Subset(val_dataset, val_idx)

    # Test dataset
    test_dataset = datasets.ImageFolder(test_dir, transform=val_transform)

    # Data loaders
    train_loader = DataLoader(
        train_subset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True,
    )
    val_loader = DataLoader(
        val_subset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )

    # Compute class weights for imbalanced data
    train_labels = [labels[i] for i in train_idx]
    class_counts = Counter(train_labels)
    total = sum(class_counts.values())
    class_weights = torch.tensor(
        [total / (len(class_counts) * class_counts[i]) for i in range(len(class_counts))],
        dtype=torch.float32,
    )

    print(f"\n[DATA] Training samples:   {len(train_subset)}")
    print(f"[DATA] Validation samples: {len(val_subset)}")
    print(f"[DATA] Test samples:       {len(test_dataset)}")
    print(f"[DATA] Classes:            {full_dataset.classes}")
    print(f"[DATA] Class distribution (train):")
    for i, cat in enumerate(full_dataset.classes):
        count = class_counts[i]
        print(f"       {cat}: {count} ({count/len(train_idx)*100:.1f}%)")
    print(f"[DATA] Class weights:      {class_weights.numpy()}")

    return train_loader, val_loader, test_loader, class_weights, full_dataset.classes


def train_one_epoch(model, loader, criterion, optimizer, device, scaler=None):
    """Train for one epoch. Returns average loss and accuracy."""
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for batch_idx, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()

        if scaler is not None:
            with torch.amp.autocast("cuda"):
                outputs = model(images)
                loss = criterion(outputs, labels)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

        running_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def validate(model, loader, criterion, device):
    """Validate the model. Returns average loss and accuracy."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return epoch_loss, epoch_acc


def evaluate_test_set(model, loader, device, class_names):
    """Run full evaluation on test set with classification report."""
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            outputs = model(images)
            _, predicted = outputs.max(1)
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())

    # Classification report
    report = classification_report(
        all_labels, all_preds,
        target_names=class_names,
        digits=4,
    )

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)

    return report, cm, all_preds, all_labels


def save_checkpoint(model, optimizer, epoch, val_loss, val_acc, path):
    """Save model checkpoint."""
    torch.save({
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "val_loss": val_loss,
        "val_accuracy": val_acc,
    }, path)


def train(args):
    """Main training function."""
    # ── Setup ──────────────────────────────────
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    # Auto-detect data dirs if not specified
    if args.train_dir is None or args.test_dir is None:
        auto_train, auto_test = get_data_dirs()
        if auto_train is None:
            print("[ERROR] Could not find dataset. Run 'python download_dataset.py' first.")
            sys.exit(1)
        args.train_dir = args.train_dir or auto_train
        args.test_dir = args.test_dir or auto_test

    # Create weights directory
    weights_dir = Path(args.weights_dir)
    weights_dir.mkdir(parents=True, exist_ok=True)

    # ── Data ───────────────────────────────────
    train_loader, val_loader, test_loader, class_weights, class_names = create_data_loaders(
        args.train_dir, args.test_dir, args.batch_size,
        args.val_split, args.seed, args.num_workers,
    )

    # ── Model ──────────────────────────────────
    model, device = build_model(pretrained=True)

    # Move class weights to device
    class_weights = class_weights.to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights, label_smoothing=0.1)

    # Mixed precision scaler (GPU only)
    scaler = torch.amp.GradScaler("cuda") if device.type == "cuda" else None

    # ── Phase 1: Train classifier head only ────
    print("\n" + "=" * 60)
    print("  PHASE 1: Training Classifier Head (backbone frozen)")
    print("=" * 60)

    model.freeze_backbone()
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr_phase1,
        weight_decay=1e-4,
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3,
    )

    best_val_acc = 0.0
    best_val_loss = float("inf")
    patience_counter = 0
    history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": [], "phase": []}

    for epoch in range(1, args.epochs_phase1 + 1):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, scaler,
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step(val_loss)
        elapsed = time.time() - t0

        print(
            f"  Epoch {epoch:>2}/{args.epochs_phase1} | "
            f"Train Loss: {train_loss:.4f}  Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f}  Acc: {val_acc:.4f} | "
            f"Time: {elapsed:.1f}s"
        )

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["phase"].append(1)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
            save_checkpoint(
                model, optimizer, epoch, val_loss, val_acc,
                weights_dir / "best_model.pth",
            )
            print(f"         * Best model saved (val_acc: {val_acc:.4f})")
            patience_counter = 0
        else:
            patience_counter += 1

    # ── Phase 2: Fine-tune backbone ────────────
    print("\n" + "=" * 60)
    print("  PHASE 2: Fine-tuning (backbone partially unfrozen)")
    print("=" * 60)

    model.unfreeze_backbone(unfreeze_from=-3)
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr_phase2,
        weight_decay=1e-5,
    )
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=3,
    )
    patience_counter = 0

    for epoch in range(1, args.epochs_phase2 + 1):
        t0 = time.time()

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device, scaler,
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)

        scheduler.step(val_loss)
        elapsed = time.time() - t0

        print(
            f"  Epoch {epoch:>2}/{args.epochs_phase2} | "
            f"Train Loss: {train_loss:.4f}  Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f}  Acc: {val_acc:.4f} | "
            f"Time: {elapsed:.1f}s"
        )

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["phase"].append(2)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_val_loss = val_loss
            save_checkpoint(
                model, optimizer, epoch + args.epochs_phase1, val_loss, val_acc,
                weights_dir / "best_model.pth",
            )
            print(f"         * Best model saved (val_acc: {val_acc:.4f})")
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"\n  [EARLY STOPPING] No improvement for {args.patience} epochs.")
                break

    # ── Save final model ───────────────────────
    save_checkpoint(
        model, optimizer, epoch, val_loss, val_acc,
        weights_dir / "final_model.pth",
    )
    print(f"\n[INFO] Final model saved to {weights_dir / 'final_model.pth'}")

    # ── Evaluate on test set ───────────────────
    print("\n" + "=" * 60)
    print("  TEST SET EVALUATION")
    print("=" * 60)

    # Load best model for evaluation
    checkpoint = torch.load(weights_dir / "best_model.pth", map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    print(f"\n[INFO] Loaded best model (epoch {checkpoint['epoch']}, val_acc: {checkpoint['val_accuracy']:.4f})")

    report, cm, preds, labels = evaluate_test_set(model, test_loader, device, class_names)

    print(f"\n{report}")
    print(f"Confusion Matrix:")
    print(cm)

    # ── Save history ───────────────────────────
    history_path = weights_dir / "training_history.json"
    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)
    print(f"\n[INFO] Training history saved to {history_path}")

    # ── Summary ────────────────────────────────
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Best validation accuracy: {best_val_acc:.4f}")
    print(f"  Best model weights:       {weights_dir / 'best_model.pth'}")
    print(f"  Final model weights:      {weights_dir / 'final_model.pth'}")
    print(f"  Training history:         {history_path}")
    print("=" * 60)

    return best_val_acc


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Train Brain Tumor Classification Model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--train-dir", type=str, default=None,
                        help="Path to training data directory")
    parser.add_argument("--test-dir", type=str, default=None,
                        help="Path to test data directory")
    parser.add_argument("--weights-dir", type=str, default=DEFAULTS["weights_dir"],
                        help="Directory to save model weights")
    parser.add_argument("--batch-size", type=int, default=DEFAULTS["batch_size"],
                        help="Batch size for training")
    parser.add_argument("--epochs-phase1", type=int, default=DEFAULTS["epochs_phase1"],
                        help="Number of epochs for phase 1 (frozen backbone)")
    parser.add_argument("--epochs-phase2", type=int, default=DEFAULTS["epochs_phase2"],
                        help="Number of epochs for phase 2 (fine-tuning)")
    parser.add_argument("--lr-phase1", type=float, default=DEFAULTS["lr_phase1"],
                        help="Learning rate for phase 1")
    parser.add_argument("--lr-phase2", type=float, default=DEFAULTS["lr_phase2"],
                        help="Learning rate for phase 2")
    parser.add_argument("--patience", type=int, default=DEFAULTS["patience"],
                        help="Early stopping patience")
    parser.add_argument("--val-split", type=float, default=DEFAULTS["val_split"],
                        help="Validation split ratio")
    parser.add_argument("--num-workers", type=int, default=DEFAULTS["num_workers"],
                        help="Number of data loading workers")
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"],
                        help="Random seed for reproducibility")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Convert namespace to use underscores for attribute access
    args_dict = vars(args)
    for key in list(args_dict.keys()):
        new_key = key.replace("-", "_")
        if new_key != key:
            args_dict[new_key] = args_dict.pop(key)

    args = argparse.Namespace(**args_dict)

    train(args)
