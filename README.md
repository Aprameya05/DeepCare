# Diabetes Prediction System

A production-ready, medically-oriented diabetes screening system using the PIMA Indians Diabetes dataset. This system is designed for high-recall screening support, ensuring that potential cases are captured for clinical review.

## Features

- **Robust Preprocessing**: Handles medically invalid zeros (e.g., Glucose=0, BMI=0) using KNN and Median imputation.
- **Multiple Model Benchmarking**: Compares Logistic Regression, Random Forest, SVM, XGBoost, and LightGBM.
- **Recall Priority**: Decision thresholds are automatically tuned using the F2-score to minimize false negatives.
- **Production API**: Flask-based REST API with input validation and medical range checking.
- **Explainability**: Integrated SHAP (SHapley Additive exPlanations) for both global model behavior and individual prediction feature attribution.
- **CLI Tool**: Quick inference from the command line using JSON inputs.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/krishnaik06/Diabetes-Prediction
   cd Diabetes-Prediction
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Training the Model

To run the full training pipeline, including benchmarking and hyperparameter optimization:

```bash
python -m diabetes_prediction.training
```

Artifacts (model, scaler, metadata, and plots) will be saved in the `models/` directory.

### Running the API

Start the Flask production-ready API:

```bash
python -m diabetes_prediction.app
```

The API will be available at `http://localhost:5000`.

**Endpoints:**
- `GET /health`: Health check.
- `POST /predict`: Predict diabetes from patient health parameters.

### CLI Prediction

You can also use the CLI for quick predictions:

```bash
python predict_cli.py --json '{"Pregnancies":6, "Glucose":148, "BloodPressure":72, "SkinThickness":35, "Insulin":0, "BMI":33.6, "DiabetesPedigreeFunction":0.627, "Age":50}'
```

## Model Reliability & Disclaimer

> [!WARNING]
> This model is intended as an **educational screening aid only**. It is **not a medical device** and should not be used for definitive diagnosis.
> 
> All predictions must be interpreted by a qualified clinician and confirmed with laboratory tests. The model is optimized for **Recall** (currently ~94% on holdout), which means it will produce some false positives to ensure that potential diabetic patients are not overlooked during screening.

## Metrics (Latest Run)

- **Selected Model**: SVM (RBF Kernel)
- **Recall (Diabetic Class)**: 0.94
- **Precision (Diabetic Class)**: 0.53
- **ROC-AUC**: 0.82
- **F1 Score**: 0.67

## License

MIT License. See `LICENSE` for details.