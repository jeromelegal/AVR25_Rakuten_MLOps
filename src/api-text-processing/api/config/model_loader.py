import json
from functools import lru_cache
from typing import Annotated
from api.config.config import Settings, get_settings
from fastapi import Depends
import mlflow


@lru_cache
def get_text_classifier_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)
    classifier_components = mlflow.transformers.load_model(
        model_uri=f"models:/{model_name}/{model_version}",
        return_type="components",
    )
    classifier_tokenizer = classifier_components["tokenizer"]
    text_classifier = classifier_components["model"]
    return text_classifier, classifier_tokenizer


@lru_cache
def get_translator_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_TRANSLATOR_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_TRANSLATOR_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)

    mlflow.artifacts.download_artifacts(
        run_id=settings.MLFLOW_TEXT_TRANSLATOR_ARTIFACT_RUN_ID,
        artifact_path=settings.MLFLOW_TEXT_TRANSLATOR_CACHE_ARTIFACT_PATH,
        dst_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
    )
    translator_components = mlflow.transformers.load_model(
        model_uri=f"models:/{model_name}/{model_version}",
        return_type="components",
    )
    translator_tokenizer = translator_components["tokenizer"]
    translator = translator_components["model"]

    return translator, translator_tokenizer


@lru_cache
def get_language_detector_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_VERSION

    mlflow.set_tracking_uri(settings.MLFLOW_ADDR)

    mlflow.artifacts.download_artifacts(
        run_id=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_ARTIFACT_RUN_ID,
        artifact_path=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH,
        dst_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
    )

    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")


# load french dictionary
@lru_cache
def get_french_words(settings: Annotated[Settings, Depends(get_settings)]):
    artifact_dir = settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH
    filename = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH.rsplit(
        "/", maxsplit=1
    )[-1]
    with open(f"{artifact_dir}/{filename}", "r", encoding="utf-8") as file:
        french_words = set(json.load(file))
    return french_words
