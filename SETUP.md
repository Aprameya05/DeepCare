# Brain Tumor Classification — Setup & Usage Guide

## Prerequisites
- Python 3.10+
- NVIDIA GPU (recommended) with CUDA drivers
- Git

## Quick Start (3 commands)

```bash
# 1. Download dataset (~80MB)
python download_dataset.py

# 2. Train model (~20 min on GPU)
python train.py

# 3. Predict on an image
python predict.py --image path/to/mri_scan.jpg
```

---

## Detailed Setup

### 1. Install Dependencies

**With GPU (recommended):**
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
pip install -r requirements.txt
```

**CPU only (slower training):**
```bash
pip install torch torchvision
pip install -r requirements.txt
```

### 2. Download Dataset

```bash
python download_dataset.py
```

This clones the [Brain Tumor Classification Dataset](https://github.com/SartajBhuvaji/Brain-Tumor-Classification-DataSet) from GitHub (~80MB). The dataset contains:
- **Training**: ~2870 MRI images (4 classes)
- **Testing**: ~394 MRI images (4 classes)

Classes: `glioma_tumor`, `meningioma_tumor`, `no_tumor`, `pituitary_tumor`

### 3. Train the Model

```bash
python train.py
```

Training runs in 2 phases:
1. **Phase 1** (10 epochs): Frozen backbone — trains only the classifier head
2. **Phase 2** (up to 25 epochs): Fine-tunes the last 3 blocks of EfficientNetB3

**Custom training options:**
```bash
python train.py --batch-size 8 --epochs-phase1 5 --epochs-phase2 15 --patience 5
```

**All options:**
```
--train-dir       Path to training data (auto-detected)
--test-dir        Path to testing data (auto-detected)
--weights-dir     Where to save weights (default: weights/)
--batch-size      Batch size (default: 16, reduce if OOM)
--epochs-phase1   Frozen backbone epochs (default: 10)
--epochs-phase2   Fine-tuning epochs (default: 25)
--lr-phase1       Phase 1 learning rate (default: 0.001)
--lr-phase2       Phase 2 learning rate (default: 0.0001)
--patience        Early stopping patience (default: 7)
--val-split       Validation split ratio (default: 0.2)
--seed            Random seed (default: 42)
```

### 4. Run Predictions

**Single image:**
```bash
python predict.py --image scan.jpg
```

**Directory of images:**
```bash
python predict.py --image scans/
```

**Quiet mode (one line per image):**
```bash
python predict.py --image scans/ --quiet
```

**Custom weights:**
```bash
python predict.py --image scan.jpg --weights weights/best_model.pth
```

### 5. Run Tests

```bash
python test_pipeline.py
```

This runs an end-to-end pipeline test covering:
- Dataset integrity
- Model architecture
- Forward pass
- Save/load cycle
- Inference transform
- Smoke training (1 epoch)
- Trained weights verification

---

## File Structure

```
├── model.py              # EfficientNetB3 model architecture
├── train.py              # Training pipeline
├── predict.py            # Inference pipeline
├── download_dataset.py   # Dataset downloader
├── test_pipeline.py      # End-to-end tests
├── requirements.txt      # Dependencies
├── SETUP.md              # This file
├── weights/
│   ├── best_model.pth    # Best checkpoint (by val accuracy)
│   ├── final_model.pth   # Final epoch checkpoint
│   └── training_history.json
└── dataset/
    └── Brain-Tumor-Classification-DataSet/
        ├── Training/
        │   ├── glioma_tumor/
        │   ├── meningioma_tumor/
        │   ├── no_tumor/
        │   └── pituitary_tumor/
        └── Testing/
            ├── glioma_tumor/
            ├── meningioma_tumor/
            ├── no_tumor/
            └── pituitary_tumor/
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `CUDA out of memory` | Reduce `--batch-size` to 8 or 4 |
| `No module named 'torch'` | Run `pip install torch torchvision` |
| `Dataset not found` | Run `python download_dataset.py` |
| `Weights not found` | Run `python train.py` first |
| `Git not found` | Install Git: https://git-scm.com/ |

---

## Model Details

| Property | Value |
|----------|-------|
| Backbone | EfficientNetB3 (ImageNet pretrained) |
| Input Size | 224×224 RGB |
| Classes | 4 (glioma, meningioma, no tumor, pituitary) |
| Output | Softmax probabilities |
| Weights Format | PyTorch `.pth` checkpoint |
| Expected Test Accuracy | >90% |
