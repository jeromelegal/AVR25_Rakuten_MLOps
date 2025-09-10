from typing import Annotated, Any

from .models.image_processing import get_images_predictions, Results
from fastapi import APIRouter, Depends, File, HTTPException
from api.config.model_loader import get_image_classifier_model

VERSION = "0.0.1"

router = APIRouter()


@router.get("/api/internal/api-image-processing")
def get_version():
    return {
        "message": "Image prediction API - Rakuten Project AVR25",
        "version": VERSION,
    }


@router.post("/api/internal/api-image-processing/predict")
def get_categories(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
    model: Annotated[Any, Depends(get_image_classifier_model)],
) -> Results:
    try:
        return get_images_predictions(files=files, model=model)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Impossible to process images. {e}"
        )
