import base64
from typing import Annotated, List
from PIL import Image
import io

from fastapi import Depends
import numpy as np
from pydantic import BaseModel

IMAGE_DIMENSION = (500, 500)

CATEGORIES = [
    "10",
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
    "40",
    "50",
    "60",
]


class Input(BaseModel):
    image_name: str


class Result(BaseModel):
    input: Input
    predicted_category: int
    categories_probabilities: List[float]


class Results(BaseModel):
    category_codes: List[str]
    results: List[Result]


def _get_image_from_bytes(file: bytes) -> np.ndarray:
    stream = io.BytesIO(file)
    img = Image.open(stream)
    filename = img.filename
    img = img.resize(IMAGE_DIMENSION)
    return filename, np.array(img)


def _get_predictions(
    name: str,
    img: np.ndarray,
    model,
) -> Result:
    predictions = model.predict(np.array([img]))[0]
    return Result(
        input=Input(image_name=name),
        categories_probabilities=predictions,
        predicted_category=np.argmax(predictions),
    )


def get_images_predictions(files: list[bytes], model):
    results = []
    for file in files:
        name, img = _get_image_from_bytes(file=file)
        result = _get_predictions(name=name, img=img, model=model)
        results.append(result)
    return Results(category_codes=CATEGORIES, results=results)
