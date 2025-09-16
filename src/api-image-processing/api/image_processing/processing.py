from typing import Annotated, Any

from .models.image_processing import get_images_predictions, Results
from fastapi import APIRouter, Depends, File, HTTPException
from api.config.dependencies import get_image_classifier_model
from api.config.config import Settings, get_settings

router = APIRouter()


@router.get("/api/internal/api-image-processing")
def get_version(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "message": "Image prediction API - Rakuten Project AVR25",
        "version": settings.SERVICE_VERSION,
    }


@router.post("/api/internal/api-image-processing/predict")
def get_categories(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
    model: Annotated[Any, Depends(get_image_classifier_model)],
) -> Results:
    if model is None:
        raise HTTPException(
            status_code=500,
            detail="Impossible to classify image since the model is null",
        )
    try:
        return get_images_predictions(files=files, model=model)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Impossible to process images. {e}"
        )
