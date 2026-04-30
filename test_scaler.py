import joblib
import os
from config import SCALER_PATH

print(f"Loading scaler from {SCALER_PATH}...")
if os.path.exists(SCALER_PATH):
    try:
        scaler = joblib.load(SCALER_PATH)
        print(f"Scaler loaded! Type: {type(scaler)}")
    except Exception as e:
        print(f"Error loading scaler: {e}")
else:
    print("Scaler not found!")
