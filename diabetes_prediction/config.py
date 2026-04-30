"""Paths and canonical feature definitions."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "pima-data.csv"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_PATH = MODELS_DIR / "model.pkl"
SCALER_PATH = MODELS_DIR / "scaler.pkl"
METADATA_PATH = MODELS_DIR / "metadata.json"

RAW_COLUMNS = [
    "num_preg",
    "glucose_conc",
    "diastolic_bp",
    "thickness",
    "insulin",
    "bmi",
    "diab_pred",
    "age",
    "skin",
    "diabetes",
]

CANONICAL_FEATURES = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]

RAW_TO_CANONICAL = {
    "num_preg": "Pregnancies",
    "glucose_conc": "Glucose",
    "diastolic_bp": "BloodPressure",
    "thickness": "SkinThickness",
    "insulin": "Insulin",
    "bmi": "BMI",
    "diab_pred": "DiabetesPedigreeFunction",
    "age": "Age",
}

# Clinical zeros treated as missing (not recorded); same mask at inference time.
ZERO_AS_MISSING_COLS_CANONICAL = [
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
]

# Soft bounds for API validation (warnings only).
RANGE_HINTS = {
    "Pregnancies": (0, 20),
    "Glucose": (1, 300),
    "BloodPressure": (1, 200),
    "SkinThickness": (1, 100),
    "Insulin": (0, 900),
    "BMI": (10.0, 70.0),
    "DiabetesPedigreeFunction": (0.0, 3.0),
    "Age": (16, 120),
}

RANDOM_STATE = 42
