from io import BytesIO
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from .model_registry import ModelConfig


def _target_image_size(input_shape: Tuple[int, ...]) -> Tuple[int, int]:
    # Keras image models are usually [None, H, W, C]
    if len(input_shape) >= 3 and input_shape[1] and input_shape[2]:
        return int(input_shape[1]), int(input_shape[2])
    return 224, 224


def preprocess_image(image_bytes: bytes, model) -> np.ndarray:
    pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    target_h, target_w = _target_image_size(model.input_shape)
    pil_image = pil_image.resize((target_w, target_h))
    array = np.asarray(pil_image, dtype=np.float32) / 255.0
    return np.expand_dims(array, axis=0)


def infer_image(model, classes: List[str], image_tensor: np.ndarray) -> Tuple[str, int]:
    predictions = model.predict(image_tensor, verbose=0)[0]
    class_idx = int(np.argmax(predictions))
    confidence = int(round(float(predictions[class_idx]) * 100))
    return classes[class_idx], confidence


def preprocess_tabular(config: ModelConfig, parameters: Dict[str, object]) -> np.ndarray:
    # Keep explicit feature order for reproducibility per disease.
    feature_map = {
        "diabetes": [
            "gender",
            "age",
            "hypertension",
            "heart_disease",
            "smoking",
            "bmi",
            "hba1c",
            "glucose",
        ],
        "breast_cancer": ["radius", "texture", "perimeter", "area", "smoothness"],
        "hepatitis": [
            "age",
            "sex",
            "alb",
            "alp",
            "alt",
            "ast",
            "bil",
            "che",
            "chol",
            "crea",
            "ggt",
            "prot",
        ],
    }
    required_features = feature_map.get(config.disease_id, [])
    missing = [field for field in required_features if field not in parameters]
    if missing:
        raise ValueError(f"Missing parameters for {config.disease_id}: {', '.join(missing)}")

    encoders: Dict[str, Dict[str, float]] = {
        "gender": {"female": 0.0, "male": 1.0, "other": 2.0},
        "hypertension": {"no": 0.0, "yes": 1.0},
        "heart_disease": {"no": 0.0, "yes": 1.0},
        "smoking": {"never": 0.0, "former": 1.0, "current": 2.0, "no info": 3.0},
        "sex": {"m": 1.0, "f": 0.0},
    }

    vector: List[float] = []
    for field in required_features:
        value = parameters[field]
        if isinstance(value, str):
            mapped = encoders.get(field, {}).get(value.strip().lower())
            if mapped is not None:
                vector.append(mapped)
                continue
            try:
                vector.append(float(value))
            except ValueError as exc:
                raise ValueError(f"Invalid categorical value for '{field}': {value}") from exc
        else:
            try:
                vector.append(float(value))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value for '{field}': {value}") from exc

    return np.array([vector], dtype=np.float32)


def infer_tabular(model, classes: List[str], features: np.ndarray) -> Tuple[str, int]:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)[0]
        class_idx = int(np.argmax(probabilities))
        confidence = int(round(float(probabilities[class_idx]) * 100))
    else:
        prediction = model.predict(features)[0]
        class_idx = int(prediction) if isinstance(prediction, (int, np.integer)) else 0
        confidence = 75

    class_idx = max(0, min(class_idx, len(classes) - 1))
    return classes[class_idx], confidence


def derive_risk_level(confidence: int) -> str:
    if confidence >= 85:
        return "High"
    if confidence >= 60:
        return "Medium"
    return "Low"
