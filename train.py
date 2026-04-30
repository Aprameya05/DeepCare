import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import recall_score, accuracy_score, f1_score, roc_auc_score
from config import PARAM_GRIDS, BEST_MODEL_PATH, MODELS_DIR
from preprocess import get_train_test_data

def train_and_benchmark():
    # Ensure models directory exists
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    print("Fetching preprocessed data...")
    X_train, X_test, y_train, y_test, feature_names = get_train_test_data()
    
    models = {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(random_state=42),
        "Support Vector Machine": SVC(probability=True, random_state=42),
        "XGBoost": XGBClassifier(random_state=42, eval_metric="logloss"),
        "LightGBM": LGBMClassifier(random_state=42, verbose=-1),
        "CatBoost": CatBoostClassifier(random_state=42, verbose=0),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42)
    }

    best_model = None
    best_recall = -1
    best_model_name = ""
    results = []

    for name, model in models.items():
        print(f"Training and tuning {name}...")
        param_grid = PARAM_GRIDS.get(name, {})
        
        # Use RandomizedSearchCV for faster tuning, optimizing for recall
        # Setting n_jobs=1 for stability on Windows environments
        search = RandomizedSearchCV(
            model, param_distributions=param_grid, n_iter=5, 
            scoring="recall", cv=3, random_state=42, n_jobs=1, error_score=0
        )
        
        try:
            search.fit(X_train, y_train)
            tuned_model = search.best_estimator_
            
            # Evaluate on test set
            y_pred = tuned_model.predict(X_test)
            y_prob = tuned_model.predict_proba(X_test)[:, 1] if hasattr(tuned_model, "predict_proba") else None
            
            recall = recall_score(y_test, y_pred)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else 0.0
            
            print(f"  -> {name} Results: Recall: {recall:.4f}, Accuracy: {accuracy:.4f}")
            
            results.append({
                "Model": name,
                "Recall": recall,
                "Accuracy": accuracy,
                "F1-Score": f1,
                "ROC-AUC": roc_auc
            })
            
            # Priority: Recall for malignant class
            if recall > best_recall:
                best_recall = recall
                best_model = tuned_model
                best_model_name = name
                
        except Exception as e:
            print(f"  !! Failed to tune/train {name}: {e}")

    print("\n" + "="*50)
    print("Benchmarking Results (sorted by Recall):")
    results_df = pd.DataFrame(results).sort_values(by="Recall", ascending=False)
    print(results_df.to_string(index=False))
    print("="*50)

    if best_model:
        print(f"\nBest Model selected based on Recall: {best_model_name} (Recall: {best_recall:.4f})")
        # Save the best model
        joblib.dump(best_model, BEST_MODEL_PATH)
        print(f"Best model saved to {BEST_MODEL_PATH}")
        
        # Save feature names for inference validation
        joblib.dump(list(feature_names), os.path.join(MODELS_DIR, "feature_names.pkl"))
    else:
        print("No model was successfully trained.")

if __name__ == "__main__":
    train_and_benchmark()
