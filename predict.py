"""
Brain Tumor Classification — Inference Pipeline

Clean CLI for predicting brain tumor type from MRI images.
Outputs classification, confidence score, and probability breakdown.

Usage:
    python predict.py --image path/to/mri.jpg
    python predict.py --image path/to/mri.jpg --weights weights/best_model.pth
    python predict.py --image path/to/folder/   (batch mode)
"""
import os
import sys
import argparse
from pathlib import Path

import numpy as np
import torch
from torchvision import transforms
from PIL import Image, ImageFile

from model import (
    load_trained_model,
    IMAGENET_MEAN,
    IMAGENET_STD,
    IMG_SIZE,
    CATEGORY_LABELS,
)

# Allow loading truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# ──────────────────────────────────────────────
# Default paths
# ──────────────────────────────────────────────
DEFAULT_WEIGHTS = Path(__file__).parent / "weights" / "best_model.pth"


def get_inference_transform():
    """Return the preprocessing transform for inference."""
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def validate_image(image_path):
    """
    Validate and load an image file with robustness handling.

    Handles:
      - File existence check
      - Valid image format check
      - Grayscale → RGB conversion
      - RGBA → RGB conversion
      - EXIF orientation correction

    Returns:
        PIL.Image in RGB mode, or None if invalid.
    """
    path = Path(image_path)

    # Check file exists
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return None

    if not path.is_file():
        print(f"[ERROR] Not a file: {path}")
        return None

    # Check file extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    if path.suffix.lower() not in valid_extensions:
        print(f"[WARNING] Unusual file extension: {path.suffix}")
        print(f"         Supported: {', '.join(valid_extensions)}")

    # Try to open the image
    try:
        img = Image.open(path)

        # Apply EXIF orientation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert to RGB if needed
        if img.mode == "L":
            # Grayscale → RGB (replicate to 3 channels)
            img = img.convert("RGB")
            print(f"[INFO] Converted grayscale image to RGB")
        elif img.mode == "RGBA":
            # RGBA → RGB (composite on white background)
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
            print(f"[INFO] Converted RGBA image to RGB")
        elif img.mode == "P":
            img = img.convert("RGB")
            print(f"[INFO] Converted palette image to RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
            print(f"[INFO] Converted {img.mode} image to RGB")

        # Verify the image is valid by loading pixels
        img.load()

        return img

    except Exception as e:
        print(f"[ERROR] Cannot open image '{path}': {e}")
        return None


def predict_single(model, device, image, transform):
    """
    Run prediction on a single PIL Image.

    Returns:
        predicted_class (int), probabilities (numpy array)
    """
    # Apply transform
    input_tensor = transform(image).unsqueeze(0).to(device)

    # Forward pass
    model.eval()
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.softmax(outputs, dim=1).cpu().numpy()[0]

    predicted_class = int(np.argmax(probabilities))
    return predicted_class, probabilities


def format_prediction(image_path, predicted_class, probabilities):
    """Format prediction results as a nice string."""
    label = CATEGORY_LABELS[predicted_class]
    confidence = probabilities[predicted_class] * 100

    # Determine if tumor detected
    if predicted_class == 2:  # no_tumor
        status = "NO TUMOR DETECTED"
        status_color = "[OK]"
    else:
        status = "TUMOR DETECTED"
        status_color = "[!!]"

    lines = []
    lines.append("")
    lines.append("=" * 55)
    lines.append(f"  {status_color}  Brain Tumor Classification Results")
    lines.append("=" * 55)
    lines.append(f"  Input:      {Path(image_path).name}")
    lines.append(f"  Status:     {status}")
    lines.append(f"  Prediction: {label}")
    lines.append(f"  Confidence: {confidence:.1f}%")
    lines.append("")
    lines.append("  Probability Breakdown:")

    # Sort by probability (descending)
    sorted_indices = np.argsort(probabilities)[::-1]
    for idx in sorted_indices:
        prob = probabilities[idx] * 100
        bar_len = int(prob / 5)
        bar = "#" * bar_len
        marker = " <-" if idx == predicted_class else ""
        lines.append(f"    {CATEGORY_LABELS[idx]:<20} {prob:>6.1f}%  {bar}{marker}")

    lines.append("=" * 55)
    lines.append("")

    return "\n".join(lines)


def predict(image_path, weights_path=None, quiet=False):
    """
    Main prediction function.

    Args:
        image_path: Path to image file or directory.
        weights_path: Path to model weights. Auto-detected if None.
        quiet: If True, only print essential output.

    Returns:
        List of (image_path, predicted_class, label, confidence, probabilities) tuples.
    """
    # Find weights
    if weights_path is None:
        weights_path = DEFAULT_WEIGHTS
    weights_path = Path(weights_path)

    if not weights_path.exists():
        print(f"[ERROR] Model weights not found at: {weights_path}")
        print(f"[ERROR] Please train the model first: python train.py")
        sys.exit(1)

    # Load model
    if not quiet:
        print(f"[INFO] Loading model from {weights_path}...")
    model, device = load_trained_model(str(weights_path))
    transform = get_inference_transform()

    # Collect image paths
    image_path = Path(image_path)
    if image_path.is_dir():
        valid_ext = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
        image_paths = sorted([
            p for p in image_path.iterdir()
            if p.is_file() and p.suffix.lower() in valid_ext
        ])
        if not image_paths:
            print(f"[ERROR] No valid images found in {image_path}")
            sys.exit(1)
        print(f"[INFO] Found {len(image_paths)} images in directory")
    else:
        image_paths = [image_path]

    # Run predictions
    results = []
    for img_path in image_paths:
        img = validate_image(img_path)
        if img is None:
            continue

        pred_class, probs = predict_single(model, device, img, transform)
        label = CATEGORY_LABELS[pred_class]
        confidence = probs[pred_class]

        results.append((str(img_path), pred_class, label, confidence, probs))

        if not quiet:
            print(format_prediction(str(img_path), pred_class, probs))
        else:
            status = "TUMOR" if pred_class != 2 else "NO TUMOR"
            print(f"{img_path.name}: {label} ({confidence:.1%}) [{status}]")

    return results


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Brain Tumor Classification — MRI Image Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python predict.py --image scan.jpg
  python predict.py --image scans/ --quiet
  python predict.py --image scan.jpg --weights weights/best_model.pth
        """,
    )
    parser.add_argument("--image", "-i", type=str, required=True,
                        help="Path to MRI image file or directory of images")
    parser.add_argument("--weights", "-w", type=str, default=None,
                        help="Path to model weights (.pth file)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Minimal output (one line per image)")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    results = predict(args.image, args.weights, args.quiet)

    if not results:
        print("[ERROR] No predictions were made.")
        sys.exit(1)
