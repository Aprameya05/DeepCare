import os
import glob
import numpy as np
import tensorflow as tf
from PIL import Image
import cv2
import config

# 1. Data Cleaning Logic (Remove Data Leakage)
def clean_data_leakage():
    """Removes the specific duplicate test files that cause data leakage."""
    leakage_files = [
        'Covid19-dataset/test/Covid/radiopaedia-2019-novel-coronavirus-infected-pneumonia.jpg',
        'Covid19-dataset/test/Covid/COVID-00022.jpg',
        'Covid19-dataset/test/Covid/COVID-00012.jpg',
        'Covid19-dataset/test/Covid/COVID-00003b.jpg',
        'Covid19-dataset/test/Covid/COVID-00037.jpg',
        'Covid19-dataset/test/Covid/COVID-00033.jpg'
    ]
    for rel_path in leakage_files:
        full_path = os.path.join(config.BASE_DIR, rel_path.replace('/', os.sep))
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                print(f"[CLEANUP] Removed data leakage file: {full_path}")
            except Exception as e:
                print(f"[CLEANUP ERROR] Could not remove {full_path}: {e}")

# 2. Invalid Image File Detection & Robust Preprocessing
def load_and_preprocess_image(image_path):
    """Safely loads, validates, converts grayscale, and resizes an X-ray image."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
    
    # Check valid extensions
    valid_exts = ('.png', '.jpg', '.jpeg', '.bmp')
    if not image_path.lower().endswith(valid_exts):
        raise ValueError(f"Unsupported image format. Allowed: {valid_exts}")
        
    try:
        # Load via Pillow to detect corrupted formats safely
        with Image.open(image_path) as img:
            img.verify()
        
        # Reload for manipulation
        img = Image.open(image_path)
        
        # Convert to RGB (grayscale handling)
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize to Target Dimensions
        img = img.resize(config.TARGET_SIZE)
        
        # Transform to float array & rescale
        img_arr = np.array(img, dtype=np.float32) / 255.0
        
        # Add Batch dimension
        img_arr = np.expand_dims(img_arr, axis=0)
        return img_arr
        
    except Exception as e:
        raise IOError(f"Corrupted or unreadable image file {image_path}: {e}")

# 3. Dynamic Grad-CAM Discovery Implementation
def find_last_conv_layer(model):
    """Finds the name of the final 4D tensor layer appropriate for Grad-CAM."""
    # First check if the model itself has 4D layers
    for layer in reversed(model.layers):
        try:
            shape = layer.output.shape
            if len(shape) == 4:
                return layer.name
        except:
            pass
            
    # If not, it might be a nested Functional model (transfer learning base)
    for layer in reversed(model.layers):
        if hasattr(layer, 'layers'):
            for sub_layer in reversed(layer.layers):
                try:
                    shape = sub_layer.output.shape
                    if len(shape) == 4:
                        # We need to target the sub-layer name
                        # But wait! To access it via model.get_layer(), we can just do:
                        return sub_layer.name
                except:
                    pass
    raise ValueError("Could not find a convolutional/4D tensor layer in the provided architecture.")

def make_gradcam_heatmap(img_array, model, last_conv_layer_name=None, pred_index=None):
    """Generates a Feature Class Activation Map by extracting spatial activations from the base transfer model."""
    base_model_layer = None
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model) or (hasattr(layer, 'layers') and not isinstance(layer, tf.keras.layers.InputLayer)):
            base_model_layer = layer
            break

    if base_model_layer is None:
        raise ValueError("Could not find base transfer model layer in the architecture.")

    # Run the base model to get the final 4D feature map
    features = base_model_layer(img_array)
    
    # Average across the channel dimension to compress into a spatial heatmap (7x7)
    heatmap = tf.reduce_mean(features[0], axis=-1)

    # Normalize between 0 and 1
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-10)
    return heatmap.numpy()

def save_gradcam_overlay(img_path, heatmap, output_path="grad_cam_output.jpg", alpha=0.4):
    img = cv2.imread(img_path)
    img = cv2.resize(img, config.TARGET_SIZE)
    
    # Resize heatmap from 7x7 to 224x224
    heatmap = cv2.resize(heatmap, config.TARGET_SIZE)
    heatmap = np.uint8(255 * heatmap)
    jet = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

    superimposed_img = jet * alpha + img
    superimposed_img = np.minimum(superimposed_img, 255).astype(np.uint8)

    cv2.imwrite(output_path, superimposed_img)
    return output_path
