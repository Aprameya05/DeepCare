# COVID-19 Chest X-Ray Classifier & Explainable AI

This repository contains a modular, production-ready implementation of a Deep Learning pipeline designed to classify COVID-19, Viral Pneumonia, and Normal lungs from Chest X-Ray images.

Originally conceptualized in a Jupyter Notebook using ResNet152V2, this codebase has been completely refactored into a standardized Python software architecture, complete with advanced Transfer Learning methodologies, dynamic Grad-CAM (Feature CAM) mapping, and robust data pipelining.

## 🚀 Features

- **Modular Architecture**: Code is split logically across `config.py` (hyperparameters), `utils.py` (data/model utilities), `train.py` (model building & execution), and `predict.py` (CLI inference).
- **Multiple Model Evaluation**: Automatically builds, trains, and evaluates three powerful architectures (`ResNet152V2`, `DenseNet121`, `EfficientNetB4`), ultimately selecting the best-performing model based on Validation Accuracy.
- **Explainable AI (Feature CAM)**: The `predict.py` script features an optional `--gradcam` flag that overlays a heatmap on the input X-ray, highlighting the specific spatial regions the CNN relied upon to make its diagnosis.
- **Robust Preprocessing**: Gracefully handles invalid images, enforces deterministic cross-validation splits, and strips out verified data leakage from the test dataset before training.
- **Modern Keras Saving**: Model weights are exported in native `.keras` and `.h5` formats for optimal downstream deployment in TensorFlow Serving or edge devices.

## 📁 Repository Structure

```text
├── config.py             # Global constants, hyper-parameters, and directory paths.
├── predict.py            # CLI Tool for running inference on isolated images.
├── train.py              # End-to-end multi-model training and evaluation script.
├── utils.py              # Data cleaning, augmentation, and Feature-CAM heatmap logic.
├── requirements.txt      # Python dependencies.
├── .gitignore            # Git exclusion settings.
├── model.keras           # Final best-performing model in Keras Native format.
├── model.h5              # Final best-performing model in H5 format.
└── weights/              # Training checkpoints for ResNet, DenseNet, and EfficientNet.
```

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Aprameya05/DeepCare.git
   cd DeepCare
   git checkout covid
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🧠 Training the Models

To execute the data preparation, data augmentation, multi-model transfer learning, and final selection process:

```bash
python train.py
```

The script will iterate through the models, executing Phase 1 (Dense Head Fine-Tuning) and Phase 2 (Unfreezing top backbone layers), then serialize the winner to `model.keras`.

## 🔍 Running Inference (Prediction)

To diagnose a specific chest X-ray image from the command line, use the `predict.py` script. 

```bash
python predict.py --image path/to/your/xray.jpeg --gradcam
```

**Output Example:**
```text
========================================
      DIAGNOSIS REPORT
========================================
Condition:        COVID detected
Primary Class:    Covid
Confidence:       77.87%
----------------------------------------
Probabilities:
 - Covid: 77.87%
 - Normal: 22.09%
 - Viral Pneumonia: 0.04%
========================================

[EXPLAIN] Calculating Grad-CAM activation heatmap...
[GRAD-CAM] Saved explainability mapping to: grad_cam_output.jpg
```
*If `--gradcam` is used, a visual heatmap (`grad_cam_output.jpg`) will be saved to the root directory.*
