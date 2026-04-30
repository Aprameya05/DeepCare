import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import joblib


@dataclass(frozen=True)
class ModelConfig:
    disease_id: str
    model_type: str
    model_path: str
    classes: List[str]


def _default_model_root() -> str:
    return str(Path(__file__).resolve().parents[2] / "Models")


MODEL_ROOT = os.getenv("MODEL_ROOT", _default_model_root())

MODEL_CONFIGS: Dict[str, ModelConfig] = {
    "alzheimers": ModelConfig(
        disease_id="alzheimers",
        model_type="image",
        model_path="Alzheimer/Alzheimer_CNN.h5",
        classes=[
            "Mild Impairment",
            "Moderate Impairment",
            "No Impairment",
            "Very Mild Impairment",
        ],
    ),
    "kidney": ModelConfig(
        disease_id="kidney",
        model_type="image",
        model_path="Kidney/Kidney.h5",
        classes=["Normal", "Cyst", "Tumor", "Stone"],
    ),
    "brain_tumor": ModelConfig(
        disease_id="brain_tumor",
        model_type="image",
        model_path="Brain_Tumor/brain_tumor_model.h5",
        classes=["Glioma", "Meningioma", "No Tumor", "Pituitary Tumor"],
    ),
    "covid": ModelConfig(
        disease_id="covid",
        model_type="image",
        model_path="COVID/covid_model.h5",
        classes=["COVID Positive", "COVID Negative", "Normal"],
    ),
    "pneumonia": ModelConfig(
        disease_id="pneumonia",
        model_type="image",
        model_path="Pneumonia/pneumonia_model.h5",
        classes=["Pneumonia Detected", "Normal"],
    ),
    # Tabular pathways are kept explicit so website integrations are stable.
    # Add real .pkl/.joblib paths once available.
    "diabetes": ModelConfig(
        disease_id="diabetes",
        model_type="tabular",
        model_path="Tabular/diabetes.pkl",
        classes=["Diabetes Positive", "No Diabetes"],
    ),
    "breast_cancer": ModelConfig(
        disease_id="breast_cancer",
        model_type="tabular",
        model_path="Tabular/breast_cancer.pkl",
        classes=["Malignant", "Benign"],
    ),
    "hepatitis": ModelConfig(
        disease_id="hepatitis",
        model_type="tabular",
        model_path="Tabular/hepatitis.pkl",
        classes=["Blood Donor (Normal)", "Hepatitis", "Fibrosis", "Cirrhosis"],
    ),
}

_LOADED_MODELS: Dict[str, object] = {}
_LOCK = threading.Lock()


class ModelRegistryError(RuntimeError):
    pass


def resolve_model_path(config: ModelConfig) -> Path:
    return Path(MODEL_ROOT) / config.model_path


def get_model_config(disease_id: str) -> Optional[ModelConfig]:
    return MODEL_CONFIGS.get(disease_id)


def _load_model(config: ModelConfig) -> object:
    file_path = resolve_model_path(config)
    if not file_path.exists():
        hint = _missing_model_hint(config)
        raise ModelRegistryError(
            f"Model file not found for '{config.disease_id}' at '{file_path}'. {hint}"
        )

    if config.model_type == "image":
        from tensorflow import keras

        return keras.models.load_model(file_path)
    if config.model_type == "tabular":
        return joblib.load(file_path)
    raise ModelRegistryError(f"Unsupported model type '{config.model_type}'.")


def get_loaded_model(disease_id: str) -> object:
    config = get_model_config(disease_id)
    if config is None:
        raise ModelRegistryError(f"Unknown disease_id '{disease_id}'.")

    with _LOCK:
        if disease_id not in _LOADED_MODELS:
            _LOADED_MODELS[disease_id] = _load_model(config)
        return _LOADED_MODELS[disease_id]


def model_status() -> List[dict]:
    statuses = []
    for disease_id, config in MODEL_CONFIGS.items():
        path = resolve_model_path(config)
        detail = None
        if not path.exists():
            detail = _missing_model_hint(config)
        statuses.append(
            {
                "disease_id": disease_id,
                "model_type": config.model_type,
                "configured_path": str(path),
                "exists": path.exists(),
                "loaded": disease_id in _LOADED_MODELS,
                "classes": config.classes,
                "detail": detail,
            }
        )
    return statuses


def _missing_model_hint(config: ModelConfig) -> str:
    root = Path(MODEL_ROOT)
    if config.disease_id == "brain_tumor":
        archive_dir = root / "Brain_Tumor_Compressed"
    elif config.disease_id == "covid":
        archive_dir = root / "COVID_Compressed"
    elif config.disease_id == "pneumonia":
        archive_dir = root / "Pneumonia_Compressed"
    else:
        archive_dir = None

    if archive_dir and archive_dir.exists():
        return (
            f"Found compressed artifacts in '{archive_dir}'. "
            "Extract/restore final model file before enabling this disease."
        )
    return "Ensure the model artifact exists and MODEL_ROOT points to the correct directory."
