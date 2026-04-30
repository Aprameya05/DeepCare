import os
import json
import argparse
import joblib
import pandas as pd
from config import SCALER_PATH, BEST_MODEL_PATH

def predict(input_data):
    """
    Makes a prediction based on input_data.
    input_data should be a dictionary or a list of dictionaries with features matching the training data.
    """
    if not os.path.exists(BEST_MODEL_PATH) or not os.path.exists(SCALER_PATH):
        raise FileNotFoundError("Model or scaler not found. Please train the model first.")
        
    model = joblib.load(BEST_MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    
    # Try to load feature names to reorder columns if they are present
    feature_names_path = os.path.join(os.path.dirname(BEST_MODEL_PATH), "feature_names.pkl")
    feature_names = None
    if os.path.exists(feature_names_path):
        feature_names = joblib.load(feature_names_path)
    
    if isinstance(input_data, dict):
        df = pd.DataFrame([input_data])
    elif isinstance(input_data, list):
        df = pd.DataFrame(input_data)
    else:
        raise ValueError("Input data must be a dictionary or a list of dictionaries.")
        
    # Drop id if present
    if "id" in df.columns:
        df = df.drop(columns=["id"])
        
    # Reorder columns to match training
    if feature_names is not None:
        # Check for missing features
        missing_cols = set(feature_names) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns in input data: {missing_cols}")
        df = df[feature_names]
        
    # Scale features
    df_scaled = scaler.transform(df)
    
    # Predict
    preds = model.predict(df_scaled)
    probs = model.predict_proba(df_scaled) if hasattr(model, "predict_proba") else None
    
    results = []
    for i in range(len(preds)):
        diagnosis = "Malignant" if preds[i] == 1 else "Benign"
        prob_malignant = float(probs[i][1]) if probs is not None else -1.0
        confidence = prob_malignant if preds[i] == 1 else (1 - prob_malignant)
        
        results.append({
            "Prediction": diagnosis,
            "Probability_Malignant": prob_malignant,
            "Confidence": confidence
        })
        
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict breast cancer diagnosis from JSON input.")
    parser.add_argument("--input", required=True, help="Path to JSON file containing input features.")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        exit(1)
        
    with open(args.input, "r") as f:
        data = json.load(f)
        
    results = predict(data)
    print(json.dumps(results, indent=2))
