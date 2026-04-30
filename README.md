# Breast Cancer Detection System

A production-ready, medically reliable, and optimized machine learning system for breast cancer diagnosis prediction. This repository has been completely refactored to prioritize robustness, high recall, and explainability for clinical decision support.

## Project Structure
- `config.py`: Centralized configuration (paths, hyperparameter grids, target mapping).
- `preprocess.py`: Handles data loading, cleaning, target encoding, and feature scaling.
- `train.py`: Trains and benchmarks 7 different models (Logistic Regression, Random Forest, SVM, XGBoost, LightGBM, CatBoost, Gradient Boosting) utilizing `RandomizedSearchCV`. Optimizes for Recall.
- `evaluate.py`: Generates evaluation metrics (Classification Report, Confusion Matrix, ROC-AUC) and SHAP explainability plots.
- `predict.py`: Command-line inference script for predicting from JSON inputs.
- `app.py`: FastAPI server exposing a robust REST API for inference.
- `requirements.txt`: Project dependencies.
- `/models`: Directory containing the saved scaler and best-performing model.

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Pipeline End-to-End:**
   ```bash
   python train.py
   python evaluate.py
   ```
   *Note: This will output benchmarking results, save the best model and scaler to the `models/` directory, and save evaluation plots.*

## Inference via Command Line

You can run predictions on new diagnostic features saved in a JSON file:

```bash
python predict.py --input sample.json
```

Example `sample.json`:
```json
{
  "radius_mean": 17.99,
  "texture_mean": 10.38,
  "perimeter_mean": 122.8,
  "area_mean": 1001.0,
  "smoothness_mean": 0.1184,
  "compactness_mean": 0.2776,
  "concavity_mean": 0.3001,
  "concave points_mean": 0.1471,
  "symmetry_mean": 0.2419,
  "fractal_dimension_mean": 0.07871,
  "radius_se": 1.095,
  "texture_se": 0.9053,
  "perimeter_se": 8.589,
  "area_se": 153.4,
  "smoothness_se": 0.006399,
  "compactness_se": 0.04904,
  "concavity_se": 0.05373,
  "concave points_se": 0.01587,
  "symmetry_se": 0.03003,
  "fractal_dimension_se": 0.006193,
  "radius_worst": 25.38,
  "texture_worst": 17.33,
  "perimeter_worst": 184.6,
  "area_worst": 2019.0,
  "smoothness_worst": 0.1622,
  "compactness_worst": 0.6656,
  "concavity_worst": 0.7119,
  "concave points_worst": 0.2654,
  "symmetry_worst": 0.4601,
  "fractal_dimension_worst": 0.1189
}
```

## Inference via API

Start the FastAPI server:
```bash
uvicorn app:app --reload
```

Send a POST request to `/predict`:
```bash
curl -X POST "http://127.0.0.1:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"features": {"radius_mean": 17.99, "texture_mean": 10.38, "perimeter_mean": 122.8, "area_mean": 1001.0, "smoothness_mean": 0.1184, "compactness_mean": 0.2776, "concavity_mean": 0.3001, "concave points_mean": 0.1471, "symmetry_mean": 0.2419, "fractal_dimension_mean": 0.07871, "radius_se": 1.095, "texture_se": 0.9053, "perimeter_se": 8.589, "area_se": 153.4, "smoothness_se": 0.006399, "compactness_se": 0.04904, "concavity_se": 0.05373, "concave points_se": 0.01587, "symmetry_se": 0.03003, "fractal_dimension_se": 0.006193, "radius_worst": 25.38, "texture_worst": 17.33, "perimeter_worst": 184.6, "area_worst": 2019.0, "smoothness_worst": 0.1622, "compactness_worst": 0.6656, "concavity_worst": 0.7119, "concave points_worst": 0.2654, "symmetry_worst": 0.4601, "fractal_dimension_worst": 0.1189}}'
```

## Reliability
The system implements strict Pydantic validation enforcing that physical metrics must not be negative. Explainability via SHAP adds an interpretable layer crucial for clinical usage.
