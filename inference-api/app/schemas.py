from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["Low", "Medium", "High"]


class ParameterPredictRequest(BaseModel):
    disease_id: str = Field(..., alias="diseaseId")
    parameters: Dict[str, Any]
    model_config = ConfigDict(populate_by_name=True)


class DiagnosisResponse(BaseModel):
    diagnosis: str
    confidence: int
    risk_level: RiskLevel
    findings: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    recommendations: List[str]
    source_model: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ModelStatusItem(BaseModel):
    disease_id: str
    model_type: Literal["image", "tabular"]
    configured_path: str
    exists: bool
    loaded: bool
    classes: List[str]
    detail: Optional[str] = None


class ModelStatusResponse(BaseModel):
    model_root: str
    models: List[ModelStatusItem]
