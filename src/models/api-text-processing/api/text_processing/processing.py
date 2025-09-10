from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from api.config.config import Settings, get_settings
from api.text_processing.models.text_processing import (
    InputsRequest,
    Results,
    get_text_categories,
)

VERSION = "0.0.1"

router = APIRouter()


@router.get("/api/internal/api-text-processing")
def get_version():
    return {
        "message": "Text prediction API - Rakuten Project AVR25",
        "version": VERSION,
    }


@router.post("/api/internal/api-text-processing/predict", response_model=Results)
def get_categories(
    inputs: InputsRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Results:
    try:
        return get_text_categories(request=inputs, settings=settings)
    except Exception as e:
        error_message = f"Impossible to process images. {e}"
        raise HTTPException(status_code=500, detail=error_message) from e
