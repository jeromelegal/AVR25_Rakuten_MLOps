from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from api.config.config import Settings, get_settings
from api.text_processing.models.text_processing import (
    InputsRequest,
    Results,
    get_text_categories,
)


router = APIRouter()


@router.get("/api/internal/api-text-processing")
def get_version(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "message": "Text prediction API - Rakuten Project AVR25",
        "version": settings.SERVICE_VERSION,
    }


@router.post("/api/internal/api-text-processing/predict", response_model=Results)
def get_categories(
    inputs: InputsRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Results:
    try:
        return get_text_categories(request=inputs, settings=settings)
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        error_message = f"Impossible to process texts. {exc}"
        raise HTTPException(status_code=500, detail=error_message) from exc
