from typing import Dict

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .model_registry import (
    MODEL_ROOT,
    ModelRegistryError,
    get_loaded_model,
    get_model_config,
    model_status,
)
from .preprocessing import (
    derive_risk_level,
    infer_image,
    infer_tabular,
    preprocess_image,
    preprocess_tabular,
)
from .schemas import DiagnosisResponse, ModelStatusResponse, ParameterPredictRequest

app = FastAPI(title="NexioraDx Inference API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _recommendations(diagnosis: str) -> list[str]:
    return [
        f"Discuss {diagnosis} findings with a qualified clinician.",
        "Correlate this prediction with labs/imaging and clinical history.",
        "Escalate care if severe symptoms are present.",
    ]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/models/status", response_model=ModelStatusResponse)
def models_status() -> ModelStatusResponse:
    return ModelStatusResponse(model_root=MODEL_ROOT, models=model_status())


@app.post("/predict/image", response_model=DiagnosisResponse)
async def predict_image(
    disease_id: str = Form(..., alias="diseaseId"),
    image: UploadFile = File(...),
) -> DiagnosisResponse:
    config = get_model_config(disease_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown diseaseId '{disease_id}'.")
    if config.model_type != "image":
        raise HTTPException(
            status_code=400, detail=f"Disease '{disease_id}' is not an image model."
        )

    try:
        model = get_loaded_model(disease_id)
        image_bytes = await image.read()
        tensor = preprocess_image(image_bytes, model)
        diagnosis, confidence = infer_image(model, config.classes, tensor)
    except ModelRegistryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    return DiagnosisResponse(
        diagnosis=diagnosis,
        confidence=confidence,
        risk_level=derive_risk_level(confidence),  # simple level from model certainty
        findings=[f"Predicted class from {disease_id} image model."],
        recommendations=_recommendations(diagnosis),
    )


@app.post("/predict/params", response_model=DiagnosisResponse)
def predict_params(request: ParameterPredictRequest) -> DiagnosisResponse:
    disease_id = request.disease_id
    config = get_model_config(disease_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown diseaseId '{disease_id}'.")
    if config.model_type != "tabular":
        raise HTTPException(
            status_code=400, detail=f"Disease '{disease_id}' is not a tabular model."
        )

    try:
        model = get_loaded_model(disease_id)
        features = preprocess_tabular(config, request.parameters)
        diagnosis, confidence = infer_tabular(model, config.classes, features)
    except ModelRegistryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    return DiagnosisResponse(
        diagnosis=diagnosis,
        confidence=confidence,
        risk_level=derive_risk_level(confidence),
        risk_factors=[f"Predicted from tabular model for {disease_id}."],
        recommendations=_recommendations(diagnosis),
    )
