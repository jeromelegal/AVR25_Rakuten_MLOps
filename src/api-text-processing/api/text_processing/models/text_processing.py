from fastapi import Depends, FastAPI, HTTPException
import pandas as pd
from api.config.config import get_settings, Settings
from api.config.dependencies import (
    get_text_classifier_model,
    get_language_detector_model,
    get_translator_model,
)
from api.text_processing.models.pipeline import inference
from pydantic import BaseModel
from typing import Annotated, List, Optional

VERSION = "0.0.1"
CATEGORIES = [
    "10",
    "40",
    "50",
    "60",
    "1140",
    "1160",
    "1180",
    "1280",
    "1281",
    "1300",
    "1301",
    "1302",
    "1320",
    "1560",
    "1920",
    "1940",
    "2060",
    "2220",
    "2280",
    "2403",
    "2462",
    "2522",
    "2582",
    "2583",
    "2585",
    "2705",
    "2905",
]

app = FastAPI()


class InputItem(BaseModel):
    designation: str
    description: str


class InputsRequest(BaseModel):
    inputs: List[InputItem]


### answer text
class Output(BaseModel):
    text: str


class Result(BaseModel):
    output: Output
    predicted_category: int
    categories_probabilities: List[float]


class Results(BaseModel):
    category_codes: List[str]
    results: List[Result]


def get_text_categories(
    request: InputsRequest, settings: Annotated[Settings, Depends(get_settings)]
):
    if not request.inputs:
        raise HTTPException(status_code=400, detail="'inputs' is empty")
    df = pd.DataFrame([item.model_dump() for item in request.inputs])
    # verify df
    required = {"designation", "description"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422, detail=f"Missing required fields in payload: {missing}"
        )
    text_classifier, classifier_tokenizer = get_text_classifier_model(settings=settings)
    language_detector = get_language_detector_model(settings=settings)
    translator, translator_tokenizer = get_translator_model(settings=settings)
    if None in (
        text_classifier,
        classifier_tokenizer,
        language_detector,
        translator,
        translator_tokenizer,
    ):
        raise ValueError(
            "Impossible to get text category since at least one model could not be loaded"
        )
    result = inference(
        df=df,
        language_detector=language_detector,
        text_classifier=text_classifier,
        text_tokenizer=classifier_tokenizer,
        translator_model=translator,
        translator_tokenizer=translator_tokenizer,
    )
    return get_texts_predictions(result)


def get_texts_predictions(result) -> Results:
    results = []
    for _, row in result.iterrows():
        output = Output(text=row["text"])
        item = Result(
            output=output,
            predicted_category=int(row["predicted_category"]),
            categories_probabilities=row["categories_probabilities"],
        )
        results.append(item)
    return Results(category_codes=CATEGORIES, results=results)
