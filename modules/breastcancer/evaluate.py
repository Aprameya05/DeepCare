import os
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, roc_auc_score
import shap
from config import SCALER_PATH, BEST_MODEL_PATH
from preprocess import get_train_test_data

def evaluate_model():
    X_train, X_test, y_train, y_test, feature_names = get_train_test_data()
    
    if not os.path.exists(BEST_MODEL_PATH):
        print(f"Error: Best model not found at {BEST_MODEL_PATH}. Run train.py first.")
        return
        
    print(f"Loading best model from {BEST_MODEL_PATH}...")
    model = joblib.load(BEST_MODEL_PATH)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    
    # Classification Report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Benign", "Malignant"]))
    
    # Ensure plots directory exists
    plots_dir = os.path.join(os.path.dirname(BEST_MODEL_PATH), "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Benign", "Malignant"], yticklabels=["Benign", "Malignant"])
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    cm_path = os.path.join(plots_dir, "confusion_matrix.png")
    plt.savefig(cm_path)
    print(f"Saved confusion matrix to {cm_path}")
    plt.close()
    
    # ROC Curve Plot
    if y_prob is not None:
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        auc = roc_auc_score(y_test, y_prob)
        plt.figure(figsize=(6, 4))
        plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {auc:.4f})")
        plt.plot([0, 1], [0, 1], "k--")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("Receiver Operating Characteristic (ROC)")
        plt.legend(loc="lower right")
        plt.tight_layout()
        roc_path = os.path.join(plots_dir, "roc_curve.png")
        plt.savefig(roc_path)
        print(f"Saved ROC curve to {roc_path}")
        plt.close()
    
    # Explainability: SHAP values
    print("Generating SHAP feature importance plot...")
    try:
        # Use a sample of background data to speed up SHAP
        explainer = shap.Explainer(model, X_train[:100])
        shap_values = explainer(X_test)
        
        plt.figure()
        shap.summary_plot(shap_values, X_test, feature_names=feature_names, show=False)
        shap_path = os.path.join(plots_dir, "shap_summary.png")
        plt.savefig(shap_path, bbox_inches='tight')
        print(f"Saved SHAP summary to {shap_path}")
        plt.close()
    except Exception as e:
        print(f"Failed to generate SHAP plots: {e}")
        print("Note: SHAP may not fully support all model types easily without tree explainer.")

if __name__ == "__main__":
    evaluate_model()
