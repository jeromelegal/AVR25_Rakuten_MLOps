from dataclasses import dataclass
import os
import logging
from typing import Callable, List, Optional
import mlflow
from mlflow.client import MlflowClient
from mlflow.exceptions import RestException
from mlflow.entities.model_registry import RegisteredModel
from mlflow.models import infer_signature
import boto3
from botocore.exceptions import ClientError
import time
from config.config import Settings, get_settings
import tensorflow as tf
import numpy as np
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
)
from fasttext_model import LANGUAGE_DETECTOR_ARTIFACT_NAME

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class S3FileToDownload:
    bucket_name: str
    file_name_on_bucket: str
    destination_dir: str
    destination_file_name: str

    @property
    def local_path(self):
        return os.path.join(self.destination_dir, self.destination_file_name)


class S3Client:
    def __init__(
        self,
        url: str,
        access_key_id: str,
        secret_access_key: str,
    ):
        self._client = boto3.client(
            "s3",
            endpoint_url=url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    def download_files(self, files_to_download: List[S3FileToDownload]):
        error = False
        for file in files_to_download:
            if not os.path.exists(file.destination_dir):
                logging.info(f"Creating folder {file.destination_dir}...")
                os.makedirs(file.destination_dir, exist_ok=False)

            logging.info(f"Downloading {file.file_name_on_bucket}...")
            dest_file_path = file.local_path
            try:
                self._client.download_file(
                    Bucket=file.bucket_name,
                    Key=file.file_name_on_bucket,
                    Filename=dest_file_path,
                )
            except ClientError as exc:
                error_msg = f"Impossible to download file {file.file_name_on_bucket} from {file.bucket_name}: {exc}"
                logging.error(error_msg)
                error = True
        return error


@dataclass
class LogConfiguration:
    experiment_name: str
    run_id: str


@dataclass
class Metric:
    name: str
    value: str


@dataclass
class Artifact:
    name: str
    local_path: str


@dataclass
class ModelToProcess:
    name: str
    register_name: str
    files_to_download_from_bucket: List[S3FileToDownload]
    log_configuration: LogConfiguration
    registering_model_function: Callable
    metrics: Optional[Metric] = None
    artifacts: Optional[List[Artifact]] = None

    def get_last_mlflow_version(self, client: MlflowClient):
        try:
            mlflow_model: RegisteredModel = client.get_registered_model(self.name)
        except RestException as exc:
            error_msg = f"Impossible to get model {self.name}: {exc}"
            logging.error(error_msg)
            return None
        return mlflow_model.latest_versions

    def download_files_from_bucket(self, s3_client: S3Client):
        return s3_client.download_files(
            files_to_download=self.files_to_download_from_bucket
        )

    def register_model_and_artifacts(self, client: MlflowClient):
        error = False
        self.registering_model_function(
            name=self.name,
            registered_name=self.register_name,
            run_id=self.log_configuration.run_id,
            experiment_name=self.log_configuration.experiment_name,
            artifacts=self.artifacts,
            metrics=self.metrics,
        )
        return error

    def cleanup(self):
        for file in self.files_to_download_from_bucket:
            if os.path.exists(file.local_path):
                os.remove(file.local_path)


def register_image_classifier_model(
    name: str,
    registered_name: str,
    run_id: str,
    experiment_name: str,
    artifacts: List[Artifact],
    metrics=List[Metric],
):
    mlflow.set_tracking_uri(uri="https://127.0.0.1:5000")
    mlflow.set_experiment(experiment_name=experiment_name)
    with mlflow.start_run(run_name=run_id) as run:
        # set tags
        mlflow.set_tag("run_id", run.info.run_id)

        logging.info("\tLoading image classifier model...")
        model = tf.keras.models.load_model(
            "/app/data/image_model/combined_trained_model_no_output.keras"
        )

        logging.info("\tEvaluating signature...")
        x = np.array([np.zeros(shape=(500, 500, 3))])
        signature = infer_signature(x, model.predict(x))

        logging.info("\tLogging image classifier model...")
        mlflow.tensorflow.log_model(model=model, name=name, signature=signature)

        if artifacts is not None and len(artifacts) > 0:
            logging.info(
                f"\tUploading image classifier artifacts (run_id: {run.info.run_id})..."
            )
            for artifact in artifacts:
                mlflow.log_artifact(
                    local_path=artifact.local_path, artifact_path=artifact.name
                )

        if metrics is not None and len(metrics) > 0:
            logging.info("\tUploading image classifier metrics...")
            for metric in metrics:
                mlflow.log_metric(key=metric.name, value=metric.value)

        logging.info("\tRegistering image classifier model...")
        model_uri = f"runs:/{run.info.run_id}/{name}"
        mv = mlflow.register_model(model_uri, registered_name)
        logging.info(f"\tModel name: {mv.name}")
        logging.info(f"\tModel version: {mv.version}")


def register_text_classifier_model(
    name: str,
    registered_name: str,
    run_id: str,
    experiment_name: str,
    artifacts: List[Artifact],
    metrics=List[Metric],
):
    mlflow.set_tracking_uri(uri="https://127.0.0.1:5000")
    mlflow.set_experiment(experiment_name=experiment_name)
    with mlflow.start_run(run_name=run_id) as run:
        # set tags
        mlflow.set_tag("run_id", run.info.run_id)

        logging.info("\tLoading text classifier model...")
        tokenizer, model = load_text_classifier_model(
            model_dir="/app/data/text_classifier_model"
        )

        logging.info("\tLogging text classifier model...")
        components = {
            "model": model,
            "tokenizer": tokenizer,
        }
        mlflow.transformers.log_model(
            transformers_model=components,
            name=name,
            task="text-classification",
        )

        if artifacts is not None and len(artifacts) > 0:
            logging.info(f"\tUploading text classifier (run_id: {run.info.run_id})...")
            for artifact in artifacts:
                mlflow.log_artifact(
                    local_path=artifact.local_path, artifact_path=artifact.name
                )

        if metrics is not None and len(metrics) > 0:
            logging.info("\tUploading text classifier metrics...")
            for metric in metrics:
                mlflow.log_metric(key=metric.name, value=metric.value)

        logging.info("\tRegistering text classifier model...")
        model_uri = f"runs:/{run.info.run_id}/{name}"
        mv = mlflow.register_model(model_uri, registered_name)
        logging.info(f"\tModel name: {mv.name}")
        logging.info(f"\tModel version: {mv.version}")


def load_text_classifier_model(model_dir: str):
    model = AutoModelForSequenceClassification.from_pretrained(
        model_dir, local_files_only=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model.to("cpu")
    return tokenizer, model


def register_text_translator_model(
    name: str,
    registered_name: str,
    run_id: str,
    experiment_name: str,
    artifacts: List[Artifact],
    metrics=List[Metric],
):
    mlflow.set_tracking_uri(uri="https://127.0.0.1:5000")
    mlflow.set_experiment(experiment_name=experiment_name)
    with mlflow.start_run(run_name=run_id) as run:
        # set tags
        mlflow.set_tag("run_id", run.info.run_id)

        logging.info("\tLoading text translator model...")
        tokenizer, model, _ = load_text_translator_model(
            model_dir="/app/data/text_translator_model"
        )

        logging.info("\tLogging text translator model...")
        components = {
            "model": model,
            "tokenizer": tokenizer,
        }
        mlflow.transformers.log_model(
            transformers_model=components,
            name=name,
            task="translation",
        )

        if artifacts is not None and len(artifacts) > 0:
            logging.info(
                f"\tUploading text translator artifacts (run_id: {run.info.run_id})..."
            )
            for artifact in artifacts:
                mlflow.log_artifact(
                    local_path=artifact.local_path, artifact_path=artifact.name
                )

        if metrics is not None and len(metrics) > 0:
            logging.info("\tUploading text translator metrics...")
            for metric in metrics:
                mlflow.log_metric(key=metric.name, value=metric.value)

        logging.info("\tRegistering text translator model...")
        model_uri = f"runs:/{run.info.run_id}/{name}"
        mv = mlflow.register_model(model_uri, registered_name)
        logging.info(f"\tModel name: {mv.name}")
        logging.info(f"\tModel version: {mv.version}")


def load_text_translator_model(model_dir: str):
    device = "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir, local_files_only=True).to(
        device
    )
    return tokenizer, model, device


def register_language_detector_model(
    name: str,
    registered_name: str,
    run_id: str,
    experiment_name: str,
    artifacts: List[Artifact],
    metrics=List[Metric],
):
    mlflow.set_tracking_uri(uri="https://127.0.0.1:5000")
    mlflow.set_experiment(experiment_name=experiment_name)
    with mlflow.start_run(run_name=run_id) as run:
        # set tags
        mlflow.set_tag("run_id", run.info.run_id)

        logging.info("Logging FastText model to mlflow")
        model_path = "init/fasttext_model.py"
        mlflow.pyfunc.log_model(
            python_model=model_path,  # Define the model as the path to the Python file
            name=name,
            artifacts={
                LANGUAGE_DETECTOR_ARTIFACT_NAME: "/app/data/text_language_detector_model/lid.176.bin"
            },
        )

        if artifacts is not None and len(artifacts) > 0:
            logging.info(
                f"\tUploading text language detector artifacts (run_id: {run.info.run_id})..."
            )
            for artifact in artifacts:
                mlflow.log_artifact(
                    local_path=artifact.local_path, artifact_path=artifact.name
                )

        if metrics is not None and len(metrics) > 0:
            logging.info("\tUploading text language detector metrics...")
            for metric in metrics:
                mlflow.log_metric(key=metric.name, value=metric.value)

        logging.info("Registering FastText model in mlflow")
        model_uri = f"runs:/{run.info.run_id}/{name}"
        mv = mlflow.register_model(model_uri, registered_name)
        logging.info(f"\tName: {mv.name}")
        logging.info(f"\tVersion: {mv.version}")


# TODO: Get name, files_to_download_from_bucket, bucket_name from env variables
def get_models_to_upload(settings: Settings):
    models_to_upload: List[ModelToProcess] = [
        ModelToProcess(
            name=settings.MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME,
            register_name=settings.MLFLOW_IMAGE_CLASSIFIER_MODEL_NAME,
            log_configuration=LogConfiguration(
                experiment_name=settings.MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME,
                run_id=settings.MLFLOW_IMAGE_RUN_ID,
            ),
            files_to_download_from_bucket=[
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="combined_trained_model_no_output.keras",
                    destination_dir="/app/data/image_model",
                    destination_file_name="combined_trained_model_no_output.keras",
                ),
            ],
            metrics=[
                Metric(
                    name=settings.MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_NAME,
                    value=settings.MLFLOW_IMAGE_CLASSIFIER_INITIAL_F1SCORE_VALUE,
                )
            ],
            registering_model_function=register_image_classifier_model,
        ),
        ModelToProcess(
            name=settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME,
            register_name=settings.MLFLOW_TEXT_CLASSIFIER_MODEL_NAME,
            log_configuration=LogConfiguration(
                experiment_name=settings.MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME,
                run_id=settings.MLFLOW_TEXT_RUN_ID,
            ),
            files_to_download_from_bucket=[
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-config.json",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="config.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-model.safetensors",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="model.safetensors",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-special_tokens_map.json",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="special_tokens_map.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-tokenizer_config.json",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="tokenizer_config.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-tokenizer.json",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="tokenizer.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-training_args.bin",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="training_args.bin",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-distilbert-vocab.txt",
                    destination_dir="/app/data/text_classifier_model",
                    destination_file_name="vocab.txt",
                ),
            ],
            metrics=[
                Metric(
                    name=settings.MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_NAME,
                    value=settings.MLFLOW_TEXT_CLASSIFIER_INITIAL_F1SCORE_VALUE,
                )
            ],
            registering_model_function=register_text_classifier_model,
        ),
        ModelToProcess(
            name=settings.MLFLOW_TEXT_TRANSLATOR_MODEL_NAME,
            register_name=settings.MLFLOW_TEXT_TRANSLATOR_MODEL_NAME,
            log_configuration=LogConfiguration(
                experiment_name=settings.MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME,
                run_id=settings.MLFLOW_TEXT_RUN_ID,
            ),
            files_to_download_from_bucket=[
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-config.json",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="config.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-generation_config.json",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="generation_config.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-model.safetensors",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="model.safetensors",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-sentencepiece.bpe.model",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="sentencepiece.bpe.model",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-special_tokens_map.json",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="special_tokens_map.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-tokenizer_config.json",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="tokenizer_config.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-nllb-200-tokenizer.json",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="tokenizer.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="index.json",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="index.json",
                ),
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="translation_cache_english.pkl",
                    destination_dir="/app/data/text_translator_model",
                    destination_file_name="translation_cache_english.pkl",
                ),
            ],
            artifacts=[
                Artifact(
                    name="french_words",
                    local_path="/app/data/text_translator_model/index.json",
                ),
                Artifact(
                    name="translation_cache",
                    local_path="/app/data/text_translator_model/translation_cache_english.pkl",
                ),
            ],
            registering_model_function=register_text_translator_model,
        ),
        ModelToProcess(
            name=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME,
            register_name=settings.MLFLOW_TEXT_LANGUAGE_DETECTOR_MODEL_NAME,
            log_configuration=LogConfiguration(
                experiment_name=settings.MLFLOW_TEXT_CLASSIFIER_EXPERIMENT_NAME,
                run_id=settings.MLFLOW_TEXT_RUN_ID,
            ),
            files_to_download_from_bucket=[
                S3FileToDownload(
                    bucket_name="raw-models",
                    file_name_on_bucket="models-lid.176.bin",
                    destination_dir="/app/data/text_language_detector_model",
                    destination_file_name="lid.176.bin",
                ),
            ],
            registering_model_function=register_language_detector_model,
        ),
    ]
    return models_to_upload


def initialize_models(
    mlflow_client: MlflowClient,
    s3_client: S3Client,
    models: List[ModelToProcess],
):
    global_error = False
    for model in models:
        if not model.get_last_mlflow_version(client=mlflow_client) is None:
            logging.info(f"Model {model.name} already registered to MLFlow")
            continue
        error = model.download_files_from_bucket(s3_client=s3_client)
        if error:
            error_msg = (
                f"An error occured when trying to get files for model {model.name}. "
                "Model registering aborted."
            )
            logging.error(error_msg)
            global_error = True
            model.cleanup()
            continue
        logging.info(f"Registering model {model.name} and its potential artifacts...")
        error = model.register_model_and_artifacts(client=mlflow_client)
        if error:
            error_msg = (
                f"An error occured when trying to register model {model.name} "
                "or upload its artifacts"
            )
            logging.error(error_msg)
            global_error = True
            model.cleanup()
            continue
        logging.info(f"Model {model.name} registered successfully")
        model.cleanup()
    return global_error


def main(settings: Settings):
    tracking_uri = settings.MLFLOW_TRACKING_URI

    logger.info(f"Connecting to MLFlow client with URI: {tracking_uri}")
    mlflow_client = MlflowClient(tracking_uri=tracking_uri)
    s3_client = S3Client(
        url=f"https://{settings.MINIO_SERVICE_NAME}:{settings.MINIO_SERVICE_PORT}",
        access_key_id=settings.MINIO_USER,
        secret_access_key=settings.MINIO_PASSWORD,
    )

    models_to_upload = get_models_to_upload(settings=settings)
    logger.info(f"Checking if MLFlow models need to be initialized...")
    while initialize_models(
        mlflow_client=mlflow_client, s3_client=s3_client, models=models_to_upload
    ):
        error_msg = (
            "An error occurred while trying to initialize the MLFlow models. "
            f"Retrying in {settings.DELAY_BETWEEN_RETRIES_IN_SECONDS} second(s)."
        )
        logging.error(error_msg)
        time.sleep(settings.DELAY_BETWEEN_RETRIES_IN_SECONDS)
    logger.info(f"MLFlow models initialization successfully done.")


if __name__ == "__main__":
    settings = get_settings()
    main(settings=settings)
