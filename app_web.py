"""
Brain Tumor Classification — Web App Interface (FastAPI)

Runs a local web server with an image upload portal for brain tumor classification.
"""
import os
import sys
import io
import traceback
from pathlib import Path

import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from model import (
    load_trained_model,
    IMG_SIZE,
    CATEGORY_LABELS,
)
from predict import get_inference_transform

app = FastAPI(title="Brain Tumor Classification API")

# ──────────────────────────────────────────────
# Setup & Global Model Loading
# ──────────────────────────────────────────────
DEFAULT_WEIGHTS = Path(__file__).parent / "weights" / "best_model.pth"

# Setup global variables for lazy-loading
model = None
device = None
transform = None


def get_model():
    """Lazy load the model to avoid issues during startup."""
    global model, device, transform
    if model is None:
        if not DEFAULT_WEIGHTS.exists():
            raise RuntimeError(f"Weights not found at {DEFAULT_WEIGHTS}. Please train the model first.")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[WEB] Loading model onto {device}...")
        model, device = load_trained_model(str(DEFAULT_WEIGHTS), device=device)
        transform = get_inference_transform()
    return model, device, transform


# Create static folder if it doesn't exist
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the single-page application."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found in static folder.")
    return FileResponse(str(index_path))


@app.post("/api/predict")
async def predict_mri(file: UploadFile = File(...)):
    """Upload an MRI image and receive classification probabilities."""
    try:
        # Load model
        net, dev, trans = get_model()

        # Read uploaded image bytes
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))

        # Convert to RGB (predict logic expects RGB)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Transform and predict
        input_tensor = trans(img).unsqueeze(0).to(dev)

        net.eval()
        with torch.no_grad():
            outputs = net(input_tensor)
            probabilities = torch.softmax(outputs, dim=1).cpu().numpy()[0]

        predicted_class = int(np.argmax(probabilities))
        label = CATEGORY_LABELS[predicted_class]
        confidence = float(probabilities[predicted_class])

        # Determine if tumor detected
        has_tumor = predicted_class != 2  # 2 is no_tumor

        # Probability breakdown
        breakdown = []
        for idx, prob in enumerate(probabilities):
            breakdown.append({
                "class_id": idx,
                "label": CATEGORY_LABELS[idx],
                "probability": float(prob),
            })

        # Sort breakdown by highest probability
        breakdown = sorted(breakdown, key=lambda x: x["probability"], reverse=True)

        return {
            "success": True,
            "filename": file.filename,
            "prediction": {
                "class_id": predicted_class,
                "label": label,
                "confidence": confidence,
                "has_tumor": has_tumor,
            },
            "breakdown": breakdown,
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn
    print("[WEB] Launching web server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
