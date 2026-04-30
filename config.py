import os

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# File Paths
DATASET_PATH = os.path.join(DATA_DIR, "Brest Cancer Dataset.csv")
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
BEST_MODEL_PATH = os.path.join(MODELS_DIR, "best_model.pkl")

# Target Variable Configuration
TARGET_COL = "diagnosis"
LABEL_MAPPING = {"M": 1, "B": 0}

# Drop Columns
DROP_COLS = ["id"]

# Hyperparameter Tuning Grid
PARAM_GRIDS = {
    "Logistic Regression": {
        "C": [0.01, 0.1, 1, 10, 100],
        "solver": ["liblinear", "lbfgs"]
    },
    "Random Forest": {
        "n_estimators": [50, 100, 200],
        "max_depth": [None, 10, 20, 30],
        "min_samples_split": [2, 5, 10]
    },
    "Support Vector Machine": {
        "C": [0.1, 1, 10, 100],
        "gamma": [1, 0.1, 0.01, 0.001],
        "kernel": ["rbf", "linear"]
    },
    "XGBoost": {
        "learning_rate": [0.01, 0.1, 0.2],
        "max_depth": [3, 5, 7],
        "n_estimators": [50, 100, 200]
    },
    "LightGBM": {
        "learning_rate": [0.01, 0.1, 0.2],
        "max_depth": [3, 5, 7],
        "n_estimators": [50, 100, 200]
    },
    "CatBoost": {
        "learning_rate": [0.01, 0.1, 0.2],
        "depth": [4, 6, 8],
        "iterations": [50, 100, 200]
    },
    "Gradient Boosting": {
        "learning_rate": [0.01, 0.1, 0.2],
        "max_depth": [3, 5, 7],
        "n_estimators": [50, 100, 200]
    }
}
