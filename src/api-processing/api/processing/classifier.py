from dataclasses import dataclass
from typing import Annotated, Dict, List, Optional, Tuple
from fastapi import File, UploadFile
import requests
import logging
from threading import Lock
from api.processing.utils import ThreadWithReturnValue

DEFAULT_TIMEOUT = 10.0

# TODO: call MongoDB to get dynamically the categories
RAKUTEN_CATEGORIES = {
    10: "Livre occasion",
    40: "Jeu vidéo, accessoire tech.",
    50: "Accessoire Console",
    60: "Console de jeu",
    1140: "Figurine",
    1160: "Carte Collection",
    1180: "Jeu Plateau",
    1280: "Jouet enfant, déguisement",
    1281: "Jeu de société",
    1300: "Jouet tech",
    1301: "Paire de chaussettes",
    1302: "Jeu extérieur, vêtement",
    1320: "Autour du bébé",
    1560: "Mobilier intérieur",
    1920: "Chambre",
    1940: "Cuisine",
    2060: "Décoration intérieure",
    2220: "Animal",
    2280: "Revues et journaux",
    2403: "Magazines, livres et BDs",
    2462: "Jeu occasion",
    2522: "Bureautique et papeterie",
    2582: "Mobilier extérieur",
    2583: "Autour de la piscine",
    2585: "Bricolage",
    2705: "Livre neuf",
    2905: "Jeu PC",
}


@dataclass
class APIPredictions:
    category: Optional[str]
    probabilities: Optional[Dict[str, float]]


@dataclass
class Prediction:
    category: Optional[str]
    probability: Optional[float]
    overall_probabilities: Optional[Dict[str, float]]
    image_probabilities: Optional[Dict]
    text_probabilities: Optional[Dict]

    def to_dict(self):
        return {
            "category": self.category,
            "probability": self.probability,
            "overall_probabilities": self.overall_probabilities,
            "image_probabilities": self.image_probabilities,
            "text_probabilities": self.text_probabilities,
        }


class ImageTextClassifier:
    _text_api_url: str
    _image_api_url: str
    _text_classifier_weight: float
    _timeout: float
    _thread_image: ThreadWithReturnValue
    _thread_text: ThreadWithReturnValue
    _lock_image: Lock
    _lock_text: Lock

    def __init__(
        self,
        text_api_url: str,
        image_api_url: str,
        text_classifier_weight: float = 0.7,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._validate_text_weight(text_classifier_weight=text_classifier_weight)
        self._image_api_url = image_api_url
        self._text_api_url = text_api_url
        self._text_classifier_weight = text_classifier_weight
        self._timeout = timeout
        self._init_threads()

    def _validate_text_weight(self, text_classifier_weight: float):
        if text_classifier_weight < 0 or text_classifier_weight > 1:
            raise ValueError(
                f"Argument text_classifier_weight must be in [0, 1]. Got {text_classifier_weight}"
            )

    def _init_threads(self):
        self._lock_image = Lock()
        self._lock_text = Lock()
        self._thread_image = None
        self._thread_text = None

    def change_text_weight(self, text_classifier_weight: float):
        logging.info(f"Weight: {text_classifier_weight}")
        self._validate_text_weight(text_classifier_weight=text_classifier_weight)
        self._text_classifier_weight = text_classifier_weight

    def predict(
        self,
        description: Optional[str] = None,
        designation: Optional[str] = None,
        files: Annotated[
            List[UploadFile], File(description="Multiple files as bytes")
        ] = None,
    ):
        with self._lock_image:
            self._thread_image = ThreadWithReturnValue(
                target=self._predict_image, kwargs={"files": files}
            )
            self._thread_image.start()
        with self._lock_text:
            self._thread_text = ThreadWithReturnValue(
                target=self._predict_text,
                kwargs={"description": description, "designation": designation},
            )
            self._thread_text.start()
        image_predictions = self._thread_image.join()
        text_predictions = self._thread_text.join()
        logging.debug(f"image_predictions: {image_predictions}")
        logging.debug(f"text_predictions: {text_predictions}")

        return self._combine_probabilities(
            image_predictions=image_predictions, text_predictions=text_predictions
        )

    def _get_api_result(self, url, data=None, files=None):
        r = requests.post(
            url=url,
            data=data,
            files=files,
            timeout=self._timeout,
        )
        if r.status_code != 200:
            logging.debug(f"url: {url} - code: {r.status_code} - text: {r.text}")
            return None
        return r.json()

    def _predict_image(
        self,
        files: Annotated[List[UploadFile], File(description="Multiple files as bytes")],
    ):
        if files is None or self._text_classifier_weight == 1:
            return None

        files_payload = []
        for f in files:
            content = f.file.read()
            files_payload.append(("files", (f.filename, content, f.content_type)))

        data = self._get_api_result(url=self._image_api_url, files=files_payload)
        if data is None:
            return None

        classifier_categories_codes = data["category_codes"]
        data = data["results"][
            0
        ]  # TODO: Change this if we want to process multiple images
        predicted_category_code = classifier_categories_codes[
            data["predicted_category"]
        ]

        probabilities = {
            RAKUTEN_CATEGORIES[int(classifier_categories_codes[idx])]: value
            for idx, value in enumerate(data["categories_probabilities"])
        }

        return APIPredictions(
            category=RAKUTEN_CATEGORIES[int(predicted_category_code)],
            probabilities=probabilities,
        )

    def _predict_text(self, description: Optional[str], designation: Optional[str]):
        if designation is None or self._text_classifier_weight == 0:
            return None

        data = {}
        if description is None:
            description = ""

        data.update({"description": description})
        data.update({"designation": designation})

        data = self._get_api_result(url=self._text_api_url, data={"inputs": [data]})
        if data is None:
            return None

        classifier_categories_codes = data["category_codes"]
        data = data["results"][
            0
        ]  # TODO: Change this if we want to process multiple images
        predicted_category_code = classifier_categories_codes[
            data["predicted_category"]
        ]

        probabilities = {
            RAKUTEN_CATEGORIES[int(classifier_categories_codes[idx])]: value
            for idx, value in enumerate(data["categories_probabilities"])
        }

        return APIPredictions(
            category=RAKUTEN_CATEGORIES[int(predicted_category_code)],
            probabilities=probabilities,
        )

    def _combine_probabilities(
        self,
        image_predictions: Optional[APIPredictions],
        text_predictions: Optional[APIPredictions],
    ) -> Prediction:
        if image_predictions is None and text_predictions is None:
            return None

        if image_predictions is None:
            # Doing so we know that the weight will only take text predictions
            image_probabilities = text_predictions.probabilities
        else:
            image_probabilities = image_predictions.probabilities

        if text_predictions is None:
            # Doing so we know that the weight will only take image predictions
            text_probabilities = image_predictions.probabilities
        else:
            text_probabilities = text_predictions.probabilities

        # Combine probabilities
        probability = 0.0
        category = ""
        overall_probabilities = {}
        for category_name in RAKUTEN_CATEGORIES.values():
            current_probability = (
                1 - self._text_classifier_weight
            ) * image_probabilities[
                category_name
            ] + self._text_classifier_weight * text_probabilities[
                category_name
            ]
            overall_probabilities.update({category_name: current_probability})

            # Update category with max probability if needed
            if current_probability >= probability:
                probability = current_probability
                category = category_name

        return Prediction(
            category=category,
            probability=probability,
            overall_probabilities=overall_probabilities,
            image_probabilities=(
                image_predictions.probabilities
                if image_predictions is not None
                else None
            ),
            text_probabilities=(
                text_predictions.probabilities if text_predictions is not None else None
            ),
        )
