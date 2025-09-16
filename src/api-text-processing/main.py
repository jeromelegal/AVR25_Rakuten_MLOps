from fastapi import FastAPI
from api import main
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from api.config.config import settings
from api.config.model_loader import (
    load_text_classifier_model,
    load_french_words,
    load_language_detector_model,
    load_translator_model,
)
from api.text_processing import processing
from mlflow.exceptions import RestException
from jose import JWTError, jwt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("internal_access_minio")


class InternalAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Vérifier si l'endpoint est interne
        if request.url.path.startswith(settings.INTERNAL_ENDPOINT_URL):
            referer = request.headers.get("Referer")
            if not referer or not referer.startswith(settings.API_GATEWAY_HOST):
                return JSONResponse(
                    status_code=403, content={"detail": "Forbidden origin"}
                )

            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return JSONResponse(
                    status_code=401, content={"detail": "API key is missing"}
                )

            try:
                payload = jwt.decode(
                    api_key,
                    settings.INTERNAL_SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                if payload.get("scope") != "internal":
                    return JSONResponse(
                        status_code=403, content={"detail": "Invalid scope"}
                    )
            except JWTError:
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Invalid API key",
                    },
                )

        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response


def load_models_and_artifacts_in_cache():
    logging.info("Loading models and artifacts in cache...")
    try:
        text_classifier, classifier_tokenizer = load_text_classifier_model(
            model_name=settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME,
            model_version=settings.MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION,
            server_addr=settings.MLFLOW_ADDR,
        )
        translator, translator_tokenizer = load_translator_model(
            model_name=settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME,
            model_version=settings.MLFLOW_TEXT_CLASSIFIER_MODEL_VERSION,
            server_addr=settings.MLFLOW_ADDR,
            artifact_run_id=settings.MLFLOW_TEXT_TRANSLATOR_ARTIFACT_RUN_ID,
            artifact_path=settings.MLFLOW_TEXT_TRANSLATOR_CACHE_ARTIFACT_PATH,
            destination_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
        )
        language_detector = load_language_detector_model(
            model_name=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME,
            model_version=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_VERSION,
            server_addr=settings.MLFLOW_ADDR,
            artifact_run_id=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_ARTIFACT_RUN_ID,
            artifact_path=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH,
            destination_path=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
        )
        french_words = load_french_words(
            artifact_dir=settings.MLFLOW_LOCAL_ARTIFACT_DIRECTORY_PATH,
            artifact_path=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_INDEX_ARTIFACT_PATH,
        )
        if not None in (
            text_classifier,
            classifier_tokenizer,
            translator,
            translator_tokenizer,
            language_detector,
            french_words,
        ):
            logging.info("Models and artifacts loaded successfully.")
            logging.info(f"Text classifier: {text_classifier}")
            logging.info(f"Translator: {translator}")
            logging.info(f"Language detector: {language_detector}")
            return
        raise ValueError("At least one of the model was not loaded successfully")
    except (RestException, ValueError) as exc:
        error_msg = f"Impossible to load the models: {exc}"
        logging.error(error_msg)
        load_text_classifier_model.cache_clear()
        load_translator_model.cache_clear()
        load_language_detector_model.cache_clear()
        load_french_words.cache_clear()


app = FastAPI()

# Pre-load models and artifacts
load_models_and_artifacts_in_cache()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(InternalAccessMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(main.router)
app.include_router(processing.router)
