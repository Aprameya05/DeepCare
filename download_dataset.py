"""
Download and validate the Brain Tumor Classification dataset.
Clones the dataset from GitHub, verifies integrity, and removes corrupted images.
"""
import os
import sys
import subprocess
from pathlib import Path
from PIL import Image
from collections import Counter

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
DATASET_REPO = "https://github.com/SartajBhuvaji/Brain-Tumor-Classification-DataSet.git"
DATASET_DIR = Path(__file__).parent / "dataset"
CLONE_TARGET = DATASET_DIR / "Brain-Tumor-Classification-DataSet"

CATEGORIES = ["glioma_tumor", "meningioma_tumor", "no_tumor", "pituitary_tumor"]
SPLITS = ["Training", "Testing"]


def clone_dataset():
    """Clone the dataset repository if not already present."""
    if CLONE_TARGET.exists():
        print(f"[INFO] Dataset already exists at {CLONE_TARGET}")
        return True

    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Cloning dataset from {DATASET_REPO}...")
    print(f"[INFO] This may take a few minutes (~80MB)...")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", DATASET_REPO, str(CLONE_TARGET)],
            check=True,
            capture_output=True,
            text=True,
        )
        print("[OK] Dataset cloned successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to clone dataset: {e.stderr}")
        return False
    except FileNotFoundError:
        print("[ERROR] 'git' is not installed. Please install git and try again.")
        return False


def verify_structure():
    """Verify that the expected folder structure exists."""
    print("\n[INFO] Verifying dataset structure...")
    all_ok = True

    for split in SPLITS:
        split_dir = CLONE_TARGET / split
        if not split_dir.exists():
            print(f"  [ERROR] Missing: {split_dir}")
            all_ok = False
            continue

        for category in CATEGORIES:
            cat_dir = split_dir / category
            if not cat_dir.exists():
                print(f"  [ERROR] Missing: {cat_dir}")
                all_ok = False
            else:
                count = len(list(cat_dir.glob("*")))
                print(f"  [OK] {split}/{category}: {count} files")

    return all_ok


def check_and_remove_corrupted():
    """Scan all images and remove any corrupted files."""
    print("\n[INFO] Scanning for corrupted images...")
    corrupted = []
    total = 0
    valid = 0

    for split in SPLITS:
        for category in CATEGORIES:
            cat_dir = CLONE_TARGET / split / category
            if not cat_dir.exists():
                continue

            for img_path in cat_dir.iterdir():
                if img_path.is_file():
                    total += 1
                    try:
                        with Image.open(img_path) as img:
                            img.verify()
                        valid += 1
                    except Exception:
                        corrupted.append(img_path)

    if corrupted:
        print(f"  [WARNING] Found {len(corrupted)} corrupted images:")
        for p in corrupted:
            print(f"    - {p}")
            p.unlink()
            print(f"      [REMOVED]")
    else:
        print(f"  [OK] All {total} images are valid.")

    return len(corrupted)


def report_class_balance():
    """Print class distribution report."""
    print("\n" + "=" * 60)
    print("  DATASET SUMMARY")
    print("=" * 60)

    for split in SPLITS:
        print(f"\n  {split}:")
        print(f"  {'Category':<25} {'Count':>8} {'Percentage':>12}")
        print(f"  {'-'*45}")

        counts = {}
        total = 0
        for category in CATEGORIES:
            cat_dir = CLONE_TARGET / split / category
            if cat_dir.exists():
                count = len([f for f in cat_dir.iterdir() if f.is_file()])
                counts[category] = count
                total += count

        for category in CATEGORIES:
            count = counts.get(category, 0)
            pct = (count / total * 100) if total > 0 else 0
            bar = "#" * int(pct / 2)
            print(f"  {category:<25} {count:>8} {pct:>10.1f}%  {bar}")

        print(f"  {'TOTAL':<25} {total:>8}")

    print("\n" + "=" * 60)


def get_data_paths():
    """Return the training and testing directory paths."""
    return CLONE_TARGET / "Training", CLONE_TARGET / "Testing"


if __name__ == "__main__":
    print("=" * 60)
    print("  Brain Tumor Classification — Dataset Setup")
    print("=" * 60)

    if not clone_dataset():
        sys.exit(1)

    if not verify_structure():
        print("\n[ERROR] Dataset structure is invalid. Please check the repository.")
        sys.exit(1)

    check_and_remove_corrupted()
    report_class_balance()

    train_dir, test_dir = get_data_paths()
    print(f"\n  Training directory: {train_dir}")
    print(f"  Testing directory:  {test_dir}")
    print(f"\n[OK] Dataset is ready for training!")
