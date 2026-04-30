from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, root_validator
from typing import Dict, Any, List
import joblib
import pandas as pd
import os
from config import SCALER_PATH, BEST_MODEL_PATH

app = FastAPI(
    title="Breast Cancer Detection API",
    description="API for predicting breast cancer diagnosis (Benign/Malignant) based on diagnostic features.",
    version="1.0.0"
)

# Load model and scaler at startup
try:
    model = joblib.load(BEST_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    feature_names_path = os.path.join(os.path.dirname(BEST_MODEL_PATH), "feature_names.pkl")
    feature_names = joblib.load(feature_names_path) if os.path.exists(feature_names_path) else None
except Exception as e:
    print(f"Warning: Could not load model or scaler. {e}")
    model = None
    scaler = None
    feature_names = None

class PredictRequest(BaseModel):
    features: Dict[str, float]

    @root_validator(pre=True)
    def check_features(cls, values):
        features = values.get('features')
        if not features:
            raise ValueError("features dictionary is missing")
            
        # Basic validation: ensure no negative values for physical measurements
        for k, v in features.items():
            if k != "id" and v < 0:
                raise ValueError(f"Feature '{k}' cannot be negative. Got {v}.")
                
        # If feature names are known, ensure all are present
        if feature_names is not None:
            missing = [f for f in feature_names if f not in features]
            if missing:
                raise ValueError(f"Missing required features: {missing}")
                
        return values

@app.post("/predict")
def predict_diagnosis(request: PredictRequest):
    if model is None or scaler is None:
        raise HTTPException(status_code=500, detail="Model not loaded. Please train the model first.")
        
    df = pd.DataFrame([request.features])
    
    if "id" in df.columns:
        df = df.drop(columns=["id"])
        
    if feature_names is not None:
        df = df[feature_names]
        
    try:
        df_scaled = scaler.transform(df)
        pred = model.predict(df_scaled)[0]
        prob = model.predict_proba(df_scaled)[0][1] if hasattr(model, "predict_proba") else -1.0
        
        diagnosis = "Malignant" if pred == 1 else "Benign"
        confidence = prob if pred == 1 else (1 - prob)
        
        return {
            "prediction": diagnosis,
            "probability_malignant": float(prob),
            "confidence": float(confidence)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    status = "healthy" if model is not None else "model_missing"
    return {"status": status}
