from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException
from pydantic import BaseModel
from api.config.config import Settings, get_settings
from api.config.model_loader import get_classifier
from api.processing.classifier import ImageTextClassifier

router = APIRouter()


class AdToClassify(BaseModel):
    description: Optional[str]
    designation: Optional[str]
    file: Annotated[list[bytes], File(description="Multiple files as bytes")]


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
    ad: AdToClassify,
    model: Annotated[ImageTextClassifier, Depends(get_classifier)],
) -> Prediction:
    try:
        prediction = model.predict(
            description=ad.description, designation=ad.designation, files=[ad.file]
        )
        return Prediction(**prediction)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Impossible to process the ad. {e}"
        )
