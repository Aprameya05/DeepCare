import os
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from config import DATASET_PATH, SCALER_PATH, TARGET_COL, LABEL_MAPPING, DROP_COLS, MODELS_DIR

def load_data(filepath=DATASET_PATH):
    """Loads the dataset from the given filepath."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}")
    return pd.read_csv(filepath)

def clean_data(df):
    """Cleans the dataset by dropping unused columns and handling missing values."""
    # Drop unused columns
    for col in DROP_COLS:
        if col in df.columns:
            df = df.drop(columns=[col])
            
    # Handle missing values
    if df.isnull().sum().sum() > 0:
        print("Missing values detected. Dropping rows with missing values.")
        df = df.dropna()
        
    # Handle duplicate rows
    if df.duplicated().sum() > 0:
        print("Duplicate rows detected. Dropping duplicates.")
        df = df.drop_duplicates()
        
    return df

def preprocess_data(df):
    """Encodes the target variable and splits the data into features and target."""
    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in the dataset.")
        
    # Map target labels
    df[TARGET_COL] = df[TARGET_COL].map(LABEL_MAPPING)
    
    # Check if there are unmapped values (e.g., NaNs introduced by mapping)
    if df[TARGET_COL].isnull().sum() > 0:
        print("Warning: Unmapped target labels found. Dropping these rows.")
        df = df.dropna(subset=[TARGET_COL])
        
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL].astype(int)
    
    return X, y

def get_train_test_data():
    """End-to-end function to load, clean, preprocess, scale, and split the data."""
    # Create models dir if not exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    print("Loading data...")
    df = load_data()
    
    print("Cleaning data...")
    df = clean_data(df)
    
    print("Preprocessing data...")
    X, y = preprocess_data(df)
    
    # Split before scaling to prevent data leakage
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Save the scaler
    joblib.dump(scaler, SCALER_PATH)
    print(f"Scaler saved to {SCALER_PATH}")
    
    return X_train_scaled, X_test_scaled, y_train, y_test, X.columns

if __name__ == "__main__":
    X_train, X_test, y_train, y_test, feature_names = get_train_test_data()
    print(f"Training data shape: {X_train.shape}")
    print(f"Testing data shape: {X_test.shape}")
