import os
import sys

# Try to limit threads before any other imports
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAX_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

print("Env vars set. Importing threadpoolctl...")
try:
    import threadpoolctl
    threadpoolctl.threadpool_limits(limits=1)
    print("Threadpool limited.")
except Exception as e:
    print(f"Threadpool limit failed: {e}")

print("Importing sklearn...")
from sklearn.linear_model import LogisticRegression
print("Sklearn imported. Importing others...")
import joblib
import pandas as pd
from sklearn.metrics import recall_score
from config import BEST_MODEL_PATH, MODELS_DIR
from preprocess import get_train_test_data

def train_minimal():
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("Loading data...")
    X_train, X_test, y_train, y_test, feature_names = get_train_test_data()
    
    print("Training Logistic Regression...")
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    recall = recall_score(y_test, y_pred)
    print(f"Recall: {recall:.4f}")
    
    print(f"Saving model to {BEST_MODEL_PATH}...")
    joblib.dump(model, BEST_MODEL_PATH)
    joblib.dump(list(feature_names), os.path.join(MODELS_DIR, "feature_names.pkl"))
    print("Done!")

if __name__ == "__main__":
    train_minimal()
