"""
Brain Tumor Classification Model — EfficientNetB3 Transfer Learning

4-class classification:
  0: glioma_tumor
  1: meningioma_tumor
  2: no_tumor
  3: pituitary_tumor
"""
import torch
import torch.nn as nn
from torchvision import models


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
NUM_CLASSES = 4
IMG_SIZE = 224
CATEGORIES = ["glioma_tumor", "meningioma_tumor", "no_tumor", "pituitary_tumor"]
CATEGORY_LABELS = {
    0: "Glioma Tumor",
    1: "Meningioma Tumor",
    2: "No Tumor",
    3: "Pituitary Tumor",
}

# ImageNet normalization stats (used by all torchvision pretrained models)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class BrainTumorClassifier(nn.Module):
    """
    EfficientNetB3-based classifier for brain tumor MRI images.

    Architecture:
        EfficientNetB3 backbone (ImageNet pretrained)
        → AdaptiveAvgPool2d(1)
        → Dropout(0.4)
        → Linear(1536, 512) + ReLU + BatchNorm
        → Dropout(0.3)
        → Linear(512, 4)
    """

    def __init__(self, num_classes=NUM_CLASSES, pretrained=True):
        super().__init__()

        # Load EfficientNetB3 backbone
        if pretrained:
            weights = models.EfficientNet_B3_Weights.IMAGENET1K_V1
        else:
            weights = None

        backbone = models.efficientnet_b3(weights=weights)

        # Extract feature extractor (everything except the classifier)
        self.features = backbone.features
        self.avgpool = nn.AdaptiveAvgPool2d(1)

        # EfficientNetB3 outputs 1536 features
        in_features = 1536

        # Custom classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(p=0.4),
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(512),
            nn.Dropout(p=0.3),
            nn.Linear(512, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

    def freeze_backbone(self):
        """Freeze all backbone layers for initial training."""
        for param in self.features.parameters():
            param.requires_grad = False
        print("[INFO] Backbone frozen — only classifier head will be trained.")

    def unfreeze_backbone(self, unfreeze_from=-2):
        """
        Unfreeze the last N blocks of the backbone for fine-tuning.

        Args:
            unfreeze_from: Number of blocks from the end to unfreeze.
                          -2 means unfreeze the last 2 blocks.
        """
        # First, freeze everything
        for param in self.features.parameters():
            param.requires_grad = False

        # Then unfreeze the last N blocks
        blocks = list(self.features.children())
        for block in blocks[unfreeze_from:]:
            for param in block.parameters():
                param.requires_grad = True

        trainable = sum(p.numel() for p in self.parameters() if p.requires_grad)
        total = sum(p.numel() for p in self.parameters())
        print(f"[INFO] Backbone partially unfrozen. Trainable: {trainable:,} / {total:,} params")


def build_model(pretrained=True, device=None):
    """
    Build and return the model, moved to the specified device.

    Args:
        pretrained: Whether to use ImageNet pretrained weights.
        device: torch.device or None (auto-detect).

    Returns:
        model, device
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = BrainTumorClassifier(pretrained=pretrained)
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"[INFO] Model: EfficientNetB3 + Custom Classifier")
    print(f"[INFO] Total parameters:     {total_params:>12,}")
    print(f"[INFO] Trainable parameters: {trainable_params:>12,}")
    print(f"[INFO] Device: {device}")

    return model, device


def load_trained_model(weights_path, device=None):
    """
    Load a trained model from a checkpoint file.

    Args:
        weights_path: Path to the .pth checkpoint file.
        device: torch.device or None (auto-detect).

    Returns:
        model, device
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = BrainTumorClassifier(pretrained=False)
    checkpoint = torch.load(weights_path, map_location=device, weights_only=False)

    # Handle both full checkpoint and state_dict-only saves
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        print(f"[INFO] Loaded model from checkpoint (epoch {checkpoint.get('epoch', '?')})")
        if "val_accuracy" in checkpoint:
            print(f"[INFO] Checkpoint val accuracy: {checkpoint['val_accuracy']:.2%}")
    else:
        model.load_state_dict(checkpoint)
        print(f"[INFO] Loaded model state dict from {weights_path}")

    model = model.to(device)
    model.eval()
    return model, device


if __name__ == "__main__":
    # Quick test: build model and print summary
    model, device = build_model(pretrained=True)
    print(f"\n[TEST] Forward pass with random input...")
    model.eval()
    x = torch.randn(1, 3, IMG_SIZE, IMG_SIZE).to(device)
    with torch.no_grad():
        out = model(x)
    print(f"[TEST] Output shape: {out.shape}")
    print(f"[TEST] Output: {torch.softmax(out, dim=1).cpu().numpy()}")
    print("[OK] Model is working correctly!")
