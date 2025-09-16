import json
from typing import Annotated
import logging
from api.config.config import Settings, get_settings
from fastapi import Depends
import mlflow
from mlflow.exceptions import RestException
from api.config.model_loader import load_classifier


def get_classifier(settings: Annotated[Settings, Depends(get_settings)]):
    text_api_url = (
        f"https://{settings.API_TEXT_PROCESSING_SERVICE_NAME}:"
        f"{settings.API_TEXT_PROCESSING_SERVICE_PORT}"
    )
    image_api_url = (
        f"https://{settings.API_IMAGE_PROCESSING_SERVICE_NAME}:"
        f"{settings.API_IMAGE_PROCESSING_SERVICE_PORT}"
    )
    try:
        return load_classifier(text_api_url=text_api_url, image_api_url=image_api_url)
    except ValueError as exc:
        error_msg = f"Impossible to load the image classifier model: {exc}"
        logging.error(error_msg)
        load_classifier.cache_clear()
        return None


def get_text_classifier_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION
    server_addr = settings.MLFLOW_ADDR

    try:
        return load_text_classifier_model(
            model_name=model_name,
            model_version=model_version,
            server_addr=server_addr,
        )
    except (KeyError, RestException) as exc:
        error_msg = f"Impossible to load the text classifier model: {exc}"
        logging.error(error_msg)
        load_text_classifier_model.cache_clear()
        return None, None


def get_translator_model(settings: Annotated[Settings, Depends(get_settings)]):
    model_name = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION
    server_addr = settings.MLFLOW_ADDR
    artifact_run_id = settings.MLFLOW_TEXT_TRANSLATOR_ARTIFACT_RUN_ID
    artifact_path = settings.MLFLOW_TEXT_TRANSLATOR_CACHE_ARTIFACT_PATH
    destination_path = settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH

    try:
        return load_translator_model(
            model_name=model_name,
            model_version=model_version,
            server_addr=server_addr,
            artifact_run_id=artifact_run_id,
            artifact_path=artifact_path,
            destination_path=destination_path,
        )
    except (KeyError, RestException) as exc:
        error_msg = f"Impossible to load the translator model: {exc}"
        logging.error(error_msg)
        load_translator_model.cache_clear()
        return None, None


def get_language_detector_model(settings: Annotated[Settings, Depends(get_settings)]):

    model_name = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME
    model_version = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_VERSION
    server_addr = settings.MLFLOW_ADDR
    artifact_run_id = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_ARTIFACT_RUN_ID
    artifact_path = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH
    destination_path = settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH

    try:
        return load_language_detector_model(
            model_name=model_name,
            model_version=model_version,
            server_addr=server_addr,
            artifact_run_id=artifact_run_id,
            artifact_path=artifact_path,
            destination_path=destination_path,
        )
    except (KeyError, RestException) as exc:
        error_msg = f"Impossible to load the language detector model: {exc}"
        logging.error(error_msg)
        load_language_detector_model.cache_clear()
        return None


# load french dictionary
def get_french_words(settings: Annotated[Settings, Depends(get_settings)]):
    artifact_dir = settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH
    artifact_path = settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH

    try:
        return load_french_words(
            artifact_dir=artifact_dir,
            artifact_path=artifact_path,
        )
    except (KeyError, FileNotFoundError, RestException) as exc:
        error_msg = f"Impossible to load the french dictionary: {exc}"
        logging.error(error_msg)
        load_french_words.cache_clear()
        return None
