import os
import argparse
import numpy as np
import tensorflow as tf
import config
import utils

def parse_args():
    parser = argparse.ArgumentParser(description="COVID-19 Chest X-Ray Predictor API")
    parser.add_argument('--image', type=str, required=True, help="Absolute path to target chest X-ray image")
    parser.add_argument('--gradcam', action='store_true', help="Set to save Grad-CAM activation map visualization")
    return parser.parse_args()

def predict():
    args = parse_args()
    
    if not os.path.exists(config.FINAL_MODEL_H5):
        print(f"[FATAL] Model binary missing at {config.FINAL_MODEL_H5}. Please run train.py first.")
        return
        
    print(f"[LOAD] Extracting parameters from compiled model...")
    try:
        model = tf.keras.models.load_model(config.FINAL_MODEL_H5)
    except Exception as e:
        print(f"[ERROR] Loading .h5 failed. Attempting to fall back to SavedModel format: {e}")
        model = tf.keras.models.load_model(config.SAVED_MODEL_DIR)

    # Preprocess incoming test query
    print(f"[PREPROCESS] Validating and normalizing image dimensions...")
    try:
        img_arr = utils.load_and_preprocess_image(args.image)
    except Exception as e:
        print(f"[ABORT] Preprocessing validation failed: {e}")
        return

    # Infer
    preds = model.predict(img_arr)
    class_idx = np.argmax(preds[0])
    confidence = preds[0][class_idx]
    class_label = config.CLASSES[class_idx]
    
    # Check binary definition requirement: COVID detected / Not COVID
    condition = "COVID detected" if class_label == 'Covid' else "Not COVID"
    
    print("\n" + "="*40)
    print("      DIAGNOSIS REPORT")
    print("="*40)
    print(f"Condition:        {condition}")
    print(f"Primary Class:    {class_label}")
    print(f"Confidence:       {confidence * 100:.2f}%")
    print("-" * 40)
    print("Probabilities:")
    for label, prob in zip(config.CLASSES, preds[0]):
        print(f" - {label}: {prob * 100:.2f}%")
    print("="*40)
    
    if args.gradcam:
        print("\n[EXPLAIN] Calculating Grad-CAM activation heatmap...")
        try:
            heatmap = utils.make_gradcam_heatmap(img_arr, model)
            out_path = os.path.join(config.BASE_DIR, "grad_cam_output.jpg")
            utils.save_gradcam_overlay(args.image, heatmap, output_path=out_path)
            print(f"[GRAD-CAM] Saved explainability mapping to: {out_path}")
        except Exception as e:
            print(f"[EXPLAIN ERROR] Could not finalize Grad-CAM maps: {e}")

if __name__ == '__main__':
    predict()
