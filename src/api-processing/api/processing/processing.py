import logging
from typing import Annotated, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from api.config.config import Settings, get_settings
from api.config.dependencies import get_classifier
from api.processing.classifier import ImageTextClassifier

router = APIRouter()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Configurez le niveau de logging approprié


class Prediction(BaseModel):
    category: Optional[str]
    probability: Optional[float]
    overall_probabilities: Optional[Dict[str, float]]
    image_probabilities: Optional[Dict]
    text_probabilities: Optional[Dict]


@router.get("/api/internal/api-processing")
def get_version(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "message": "Image and text prediction API - Rakuten Project AVR25",
        "version": settings.SERVICE_VERSION,
    }


@router.post("/api/internal/api-processing/predict")
async def get_categories(
    files: Annotated[List[UploadFile], File(description="Multiple files as bytes")],
    model: Annotated[ImageTextClassifier, Depends(get_classifier)],
    designation: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
) -> Prediction:
    try:
        prediction = model.predict(
            description=description,
            designation=designation,
            files=files,
        )
        return Prediction(
            category=prediction.category,
            probability=prediction.probability,
            overall_probabilities=prediction.overall_probabilities,
            image_probabilities=prediction.image_probabilities,
            text_probabilities=prediction.text_probabilities,
        )
    except Exception as exc:
        error_msg = f"Impossible to process the ad. {exc}"
        raise HTTPException(status_code=500, detail=error_msg) from exc
