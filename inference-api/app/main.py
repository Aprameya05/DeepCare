import os
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
from .adapters import (
    maybe_retrieval_evidence,
    predict_image_via_adapter,
    predict_tabular_via_adapter,
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
ENABLE_RETRIEVAL_METADATA = os.getenv("ENABLE_RETRIEVAL_METADATA", "false").lower() == "true"
ALLOWED_DISEASE_IDS = {"alzheimers", "brain_tumor", "covid", "breast_cancer", "diabetes"}

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


def _with_retrieval_metadata(
    disease_id: str,
    diagnosis: str,
    payload: DiagnosisResponse,
) -> DiagnosisResponse:
    if not ENABLE_RETRIEVAL_METADATA:
        return payload

    evidence = maybe_retrieval_evidence(disease_id=disease_id, diagnosis=diagnosis)
    if not evidence:
        return payload

    metadata = payload.metadata or {}
    metadata["retrieval_evidence"] = evidence
    payload.metadata = metadata
    return payload


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "service": "NexioraDx Inference API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/models/status", response_model=ModelStatusResponse)
def models_status() -> ModelStatusResponse:
    only_allowed = [item for item in model_status() if item["disease_id"] in ALLOWED_DISEASE_IDS]
    return ModelStatusResponse(model_root=MODEL_ROOT, models=only_allowed)


@app.post("/predict/image", response_model=DiagnosisResponse)
async def predict_image(
    disease_id: str = Form(..., alias="diseaseId"),
    image: UploadFile = File(...),
) -> DiagnosisResponse:
    if disease_id not in ALLOWED_DISEASE_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Disease '{disease_id}' is not enabled in this Vector-DB merged-model release.",
        )

    config = get_model_config(disease_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown diseaseId '{disease_id}'.")
    if config.model_type != "image":
        raise HTTPException(
            status_code=400, detail=f"Disease '{disease_id}' is not an image model."
        )

    image_bytes = await image.read()
    try:
        if disease_id in {"brain_tumor", "alzheimers", "covid"}:
            adapter = predict_image_via_adapter(disease_id, image_bytes, image.filename or "upload")
            response = DiagnosisResponse(
                diagnosis=adapter.diagnosis,
                confidence=adapter.confidence,
                risk_level=derive_risk_level(adapter.confidence),
                findings=adapter.findings or [f"Predicted class from {disease_id} image model."],
                recommendations=adapter.recommendations or _recommendations(adapter.diagnosis),
                source_model=str(adapter.metadata.get("source_model")) if adapter.metadata else None,
                metadata=adapter.metadata or None,
            )
            return _with_retrieval_metadata(disease_id, adapter.diagnosis, response)

        model = get_loaded_model(disease_id)
        tensor = preprocess_image(image_bytes, model)
        diagnosis, confidence = infer_image(model, config.classes, tensor)
    except ModelRegistryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    response = DiagnosisResponse(
        diagnosis=diagnosis,
        confidence=confidence,
        risk_level=derive_risk_level(confidence),  # simple level from model certainty
        findings=[f"Predicted class from {disease_id} image model."],
        recommendations=_recommendations(diagnosis),
        source_model="keras_registry_model",
    )
    return _with_retrieval_metadata(disease_id, diagnosis, response)


@app.post("/predict/params", response_model=DiagnosisResponse)
def predict_params(request: ParameterPredictRequest) -> DiagnosisResponse:
    disease_id = request.disease_id
    if disease_id not in ALLOWED_DISEASE_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Disease '{disease_id}' is not enabled in this Vector-DB merged-model release.",
        )

    config = get_model_config(disease_id)
    if config is None:
        raise HTTPException(status_code=404, detail=f"Unknown diseaseId '{disease_id}'.")
    if config.model_type != "tabular":
        raise HTTPException(
            status_code=400, detail=f"Disease '{disease_id}' is not a tabular model."
        )

    try:
        if disease_id in {"breast_cancer", "diabetes"}:
            adapter = predict_tabular_via_adapter(disease_id, request.parameters)
            response = DiagnosisResponse(
                diagnosis=adapter.diagnosis,
                confidence=adapter.confidence,
                risk_level=derive_risk_level(adapter.confidence),
                risk_factors=adapter.risk_factors or [f"Predicted from tabular model for {disease_id}."],
                recommendations=adapter.recommendations or _recommendations(adapter.diagnosis),
                source_model=str(adapter.metadata.get("source_model")) if adapter.metadata else None,
                metadata=adapter.metadata or None,
            )
            return _with_retrieval_metadata(disease_id, adapter.diagnosis, response)

        model = get_loaded_model(disease_id)
        features = preprocess_tabular(config, request.parameters)
        diagnosis, confidence = infer_tabular(model, config.classes, features)
    except ModelRegistryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    response = DiagnosisResponse(
        diagnosis=diagnosis,
        confidence=confidence,
        risk_level=derive_risk_level(confidence),
        risk_factors=[f"Predicted from tabular model for {disease_id}."],
        recommendations=_recommendations(diagnosis),
        source_model="tabular_registry_model",
    )
    return _with_retrieval_metadata(disease_id, diagnosis, response)
