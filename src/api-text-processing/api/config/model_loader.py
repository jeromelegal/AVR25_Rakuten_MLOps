import json
from functools import lru_cache
import mlflow


@lru_cache
def load_text_classifier_model(model_name: str, model_version: str, server_addr: str):

    mlflow.set_tracking_uri(server_addr)
    classifier_components = mlflow.transformers.load_model(
        model_uri=f"models:/{model_name}/{model_version}",
        return_type="components",
    )
    classifier_tokenizer = classifier_components["tokenizer"]
    text_classifier = classifier_components["model"]
    return text_classifier, classifier_tokenizer


@lru_cache
def load_translator_model(
    model_name: str,
    model_version: str,
    server_addr: str,
    artifact_run_id: str,
    artifact_path: str,
    destination_path: str,
):

    mlflow.set_tracking_uri(server_addr)

    mlflow.artifacts.download_artifacts(
        run_id=artifact_run_id,
        artifact_path=artifact_path,
        dst_path=destination_path,
    )
    translator_components = mlflow.transformers.load_model(
        model_uri=f"models:/{model_name}/{model_version}",
        return_type="components",
    )
    translator_tokenizer = translator_components["tokenizer"]
    translator = translator_components["model"]

    return translator, translator_tokenizer


@lru_cache
def load_language_detector_model(
    model_name: str,
    model_version: str,
    server_addr: str,
    artifact_run_id: str,
    artifact_path: str,
    destination_path: str,
):

    mlflow.set_tracking_uri(server_addr)

    mlflow.artifacts.download_artifacts(
        run_id=artifact_run_id,
        artifact_path=artifact_path,
        dst_path=destination_path,
    )

    return mlflow.pyfunc.load_model(model_uri=f"models:/{model_name}/{model_version}")


# load french dictionary
@lru_cache
def load_french_words(artifact_dir: str, artifact_path: str):
    filename = artifact_path.rsplit("/", maxsplit=1)[-1]
    with open(f"{artifact_dir}/{filename}", "r", encoding="utf-8") as file:
        french_words = set(json.load(file))
    return french_words
