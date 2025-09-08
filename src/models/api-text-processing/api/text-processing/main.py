from typing import Annotated, Any

from .models.image_processing import get_images_predictions, Results
from fastapi import Depends, FastAPI, File, HTTPException
from api.config.model_loader import get_classifier_model, get_translator_model

VERSION = "0.0.1"

app = FastAPI()


@app.post("/api/internal/api-text-processing/predict")
def get_categories(
    files: Annotated[list[bytes], File(description="Multiple files as bytes")],
    translator_model: Annotated[Any, Depends(get_translator_model)],
    classifier_model: Annotated[Any, Depends(get_classifier_model)],
) -> Results:
    try:
        return get_images_predictions(files=files, model=model)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Impossible to process images. {e}"
        )
