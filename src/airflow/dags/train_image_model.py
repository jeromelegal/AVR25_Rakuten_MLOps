from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import random
import subprocess
from typing import Dict, List, Optional
from airflow.sdk import DAG, Asset
from airflow.decorators import task, task_group


from utils.mock.api_gateway_client import MockAPIGatewayClient as APIGatewayClient
from utils.s3_client import S3Client


# Constants
CONN_ID = "minio_s3_conn"
TRAIN_BUCKET = "train-images"
TEST_BUCKET = "test-images"
METADATA_BUCKET = "airflow"
LOCAL_TRAIN_FOLDER = os.path.join("images", "train")
LOCAL_TEST_FOLDER = os.path.join("images", "test")
IMAGE_DIMENSIONS = (500, 500)

"""
The training state file is a JSON file which is used to record:
- The name of all files used for the training and the testing phases
- The date of the last update of these set of filenames
- The last metric (here F1-score)
On peut alors utiliser les noms des fichiers utilisés pour déterminer s'il faut 
"""
IMAGE_TRAINING_METADATA = "training_state.json"

DATETIME_FORMAT = "%Y%m%D - %H:%M:%S"

MLFLOW_SERVICE_NAME = os.getenv("MLFLOW_SERVICE_NAME")
MLFLOW_SERVICE_PORT = os.getenv("MLFLOW_SERVICE_PORT")
MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME: str = os.getenv(
    "MLFLOW_IMAGE_CLASSIFIER_EXPERIMENT_NAME",
    default="Train image processing model",
)
MLFLOW_IMAGE_MODEL_NAME = "image_classifier_model"

train_images_asset = Asset(f"s3://{TRAIN_BUCKET}")
test_images_asset = Asset(f"s3://{TEST_BUCKET}")
train_processing_model_asset = Asset(
    f"https://{MLFLOW_SERVICE_NAME}:{MLFLOW_SERVICE_PORT}/#/models/image_classifier_model"
)


def get_dataset_metadata(s3_client: S3Client, bucket: str, filename: str):
    try:
        dataset_metadata = json.loads(
            s3_client.get_object(bucket=bucket, filename=filename)
        )
        print(f"dataset_metadata for {filename}: {dataset_metadata}")
    except s3_client.exceptions.NoSuchKey:
        dataset_metadata = {
            "last_updated_at": datetime.now().strftime(DATETIME_FORMAT),
            "last_metric": None,
            "train_images": [],
            "test_images": [],
        }
        print(f"No previous dataset metadata found for {filename}.")
    return dataset_metadata


# ----- DAG -----
default_args = {
    "owner": "airflow",
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime.now(),
}


s3_client = S3Client(connection_id=CONN_ID)

with DAG(
    dag_id="train_image_model",
    dag_display_name="Train image processing model",
    default_args=default_args,
    description="Split the processed images between train and test sets",
    catchup=False,
    tags=["s3", "images", "assets", "split"],
    schedule="15 2 * * *",  # Executed once a day at 2:15am
    is_paused_upon_creation=False,
) as dag:

    @task(
        task_display_name="List training data",
        multiple_outputs=True,
    )
    def list_training_files():
        current_train_images = s3_client.list_files_from_bucket(bucket=TRAIN_BUCKET)
        training_metadata = get_dataset_metadata(
            s3_client=s3_client,
            bucket=METADATA_BUCKET,
            filename=IMAGE_TRAINING_METADATA,
        )
        print(f"training_metadata: {training_metadata}")
        return {
            "current_train_images": current_train_images,
            "training_metadata": training_metadata,
        }

    @task.branch(
        task_display_name="Check for changes in training data",
    )
    def check_for_update(images: List[str], metadata: Dict):
        if sorted(images) != sorted([metadata["train_images"]]):
            return "create_temporary_folders"
        return ""

    @task(
        task_display_name="Create local temporary folders",
    )
    def create_temporary_folders():
        Path(LOCAL_TRAIN_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(LOCAL_TEST_FOLDER).mkdir(parents=True, exist_ok=True)

    @task(
        task_display_name="Get train images",
    )
    def get_train_images_files() -> List:
        s3_client.download_bucket(bucket=TRAIN_BUCKET, local_dir=LOCAL_TRAIN_FOLDER)

    @task(
        task_display_name="Get test images",
    )
    def get_test_images_files() -> List:
        s3_client.download_bucket(bucket=TEST_BUCKET, local_dir=LOCAL_TEST_FOLDER)

    @task_group(
        group_display_name="Get the train/test image files",
    )
    def get_images_files():
        get_train_images_files()
        get_test_images_files()

    @task.virtualenv(
        task_id="train_image_model",
        task_display_name="Train the image model",
        requirements=[
            "mlflow==3.4.0",
            "tensorflow",
            "numpy",
            "scikit-learn==1.7.2",
            "pandas",
            "boto3",
        ],
        system_site_packages=True,
    )
    def train_image_model(
        aws_access_key_id: str,
        aws_secret_access_key: str,
        airflow_conn_minio_s3_conn: str,
        mlflow_s3_endpoint_url: str,
    ):
        """
        Example function that will be performed in a virtual environment.

        Importing at the module level ensures that it will not attempt to import the
        library before it is installed.
        """
        import os
        from dataclasses import dataclass
        import mlflow
        import certifi
        from uuid import uuid4
        from mlflow.client import MlflowClient
        from mlflow.exceptions import RestException
        from mlflow.models import infer_signature
        import tensorflow as tf
        from tensorflow.keras.preprocessing import image_dataset_from_directory
        import numpy as np
        from sklearn.metrics import (
            f1_score,
            accuracy_score,
            recall_score,
            precision_score,
        )
        import pandas as pd

        # TODO: find a way to pass env. variables

        @dataclass
        class Metric:
            name: str
            value: str

        @dataclass
        class Artifact:
            name: str
            local_path: str

        def get_tracking_uri():
            return f"https://{os.getenv('MLFLOW_SERVICE_NAME')}:{os.getenv('MLFLOW_SERVICE_PORT')}"

        def get_lastest_mlflow_model_version(model_name: str):
            tracking_uri = get_tracking_uri()
            client = MlflowClient(tracking_uri=tracking_uri)
            try:
                mlflow_model = client.get_registered_model(model_name)
            except RestException:
                info_msg = (
                    f"Impossible to get model {model_name}. It will be retried later."
                )
                print(info_msg)
                return None
            return mlflow_model.latest_versions[-1]

        def load_image_datasets(train_dir: str, test_dir: str):
            train_ds = image_dataset_from_directory(
                train_dir,
                validation_split=None,
                label_mode="categorical",
                image_size=(500, 500),
            )
            val_ds = image_dataset_from_directory(
                test_dir,
                validation_split=None,
                label_mode="categorical",
                image_size=(500, 500),
            )
            return train_ds, val_ds

        def to_class(y):
            return y.argmax(axis=1)

        def get_performances(y_true, predicted_probs):
            y_pred = to_class(predicted_probs)
            y_true = to_class(y_true)

            accuracy = accuracy_score(y_true=y_true, y_pred=y_pred, normalize=True)
            f1 = f1_score(y_true=y_true, y_pred=y_pred, average="weighted")
            recall = recall_score(y_true=y_true, y_pred=y_pred, average="weighted")
            precision = precision_score(
                y_true=y_true, y_pred=y_pred, average="weighted"
            )

            return accuracy, f1, recall, precision

        def get_predictions(model, dataset):
            predictions = np.empty(shape=(0, 27))
            y_true = np.empty(shape=(0, 27))

            for x, y in dataset:
                predictions = np.concatenate([predictions, model.predict(x, verbose=0)])
                y_true = np.concatenate([y_true, y.numpy()])
            return y_true, predictions

        def _get_dataset(path: str, name: str):
            categories = []
            images = []
            for category in os.listdir(path):
                for filename in os.listdir(os.path.join(path, category)):
                    categories += [category]
                    images += [filename]
            df = pd.DataFrame({"category": categories, "filename": images})
            return mlflow.data.from_pandas(df, name=name, targets="category")

        def get_datasets_used():
            train_dataset = _get_dataset(
                path="images/train", name="image-model-training"
            )
            test_dataset = _get_dataset(path="images/test", name="image-model-testing")
            return train_dataset, test_dataset

        def train_and_register_image_classifier_model(
            name: str,
            registered_name: str,
            run_name: str,
            experiment_name: str,
            artifacts: List[Artifact],
        ):
            tracking_uri = get_tracking_uri()
            mlflow.set_tracking_uri(uri=tracking_uri)
            mlflow.set_experiment(experiment_name=experiment_name)

            print("Getting last registered image model version...")
            model_metadata = get_lastest_mlflow_model_version(
                model_name=registered_name
            )
            print(f"model_metadata: {model_metadata}")
            if model_metadata is None:
                raise ValueError(
                    f"Impossible to get the model version of {registered_name}"
                )
            print(
                f"Last registered model version for {registered_name} is {model_metadata.version}"
            )

            print("Defining callbacks...")
            early_stopping = tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                min_delta=0.001,
                patience=5,
                verbose=0,
                mode="auto",
                baseline=None,
                restore_best_weights=True,
                start_from_epoch=2,
            )

            reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.1,
                patience=3,
                verbose=0,
                mode="auto",
                min_delta=0.01,
                cooldown=2,
                min_lr=0.0,
            )

            print("Loading datasets...")
            train_ds, val_ds = load_image_datasets(
                train_dir=os.path.join("images", "train"),
                test_dir=os.path.join("images", "test"),
            )
            print(f"Nombre de batch dans train_ds: {train_ds.cardinality().numpy()}")
            print(f"Nombre de batch dans val_ds: {val_ds.cardinality().numpy()}")

            with mlflow.start_run(run_name=run_name) as run:
                # set tags
                mlflow.set_tag("run_id", run.info.run_id)

                print("Loading image classifier model...")
                model = mlflow.tensorflow.load_model(
                    model_uri=f"models:/{registered_name}/{model_metadata.version}"
                )

                print("Compiling model...")
                model.compile(
                    optimizer="adam",
                    loss="categorical_crossentropy",
                    metrics=["accuracy", "f1_score"],
                )

                print("Training model...")
                history = model.fit(
                    train_ds,
                    validation_data=val_ds,
                    epochs=20,
                    callbacks=[reduce_lr, early_stopping],
                )

                print("Evaluating signature...")
                x = np.array([np.zeros(shape=(500, 500, 3))])
                signature = infer_signature(x, model.predict(x))

                print("Evaluating metrics...")
                y_true, predictions = get_predictions(model=model, dataset=val_ds)
                accuracy, f1, recall, precision = get_performances(
                    y_true=y_true, predicted_probs=predictions
                )
                metrics: List[Metric] = [
                    Metric(name="f1-score", value=f1),
                    Metric(name="accuracy", value=accuracy),
                    Metric(name="recall", value=recall),
                    Metric(name="precision", value=precision),
                ]

                print("Logging image classifier model...")
                mlflow.tensorflow.log_model(model=model, name=name, signature=signature)

                print("Logging datasets...")
                train_dataset, test_dataset = get_datasets_used()
                mlflow.log_input(train_dataset, context="training")
                mlflow.log_input(test_dataset, context="testing")

                if artifacts is not None and len(artifacts) > 0:
                    print(
                        "Uploading image classifier artifacts (run_id: %s)...",
                        run.info.run_id,
                    )
                    for artifact in artifacts:
                        mlflow.log_artifact(
                            local_path=artifact.local_path, artifact_path=artifact.name
                        )

                if metrics is not None and len(metrics) > 0:
                    print("Uploading image classifier metrics...")
                    for metric in metrics:
                        mlflow.log_metric(key=metric.name, value=metric.value)

                if (
                    model_metadata.metrics
                    and model_metadata.metrics.get("f1-score")
                    and model_metadata.metrics["f1-score"] <= f1
                ):
                    no_registring_message = (
                        "The performance of the newly trained model is not better"
                        " than the previous one registered."
                        "Resgitration is skipped."
                    )
                    print(no_registring_message)
                    return
                print("Registering image classifier model...")
                model_uri = f"runs:/{run.info.run_id}/{name}"
                mv = mlflow.register_model(model_uri, registered_name)
                print("Model name: %s", mv.name)
                print("Model version: %s", mv.version)

        def load_certificate_issuer(certificate_path: str):
            print(f"Loading certificate {certificate_path}")
            with open(certificate_path, "r", encoding="utf-8") as cert:
                certificate = cert.read()
            with open(certifi.where(), "+a", encoding="utf-8") as cert:
                cert.write(certificate)

        # Copy certificate issuer for mlflow and minio
        print("Copy certificate issuers...")
        load_certificate_issuer(certificate_path="mlflow_ca.crt")
        load_certificate_issuer(certificate_path="minio_ca.crt")
        load_certificate_issuer(certificate_path=os.getenv("MINIO_AIRFLOW_CA_PATH"))
        load_certificate_issuer(certificate_path=os.getenv("MLFLOW_AIRFLOW_CA_PATH"))
        load_certificate_issuer(certificate_path="redis_ca.crt")
        load_certificate_issuer(
            certificate_path=f"{os.getenv('VAULT_USERNAME')}_ca.crt"
        )
        os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key
        os.environ["AIRFLOW_CONN_MINIO_S3_CONN"] = airflow_conn_minio_s3_conn
        os.environ["AIRFLOW_S3_ENDPOINT_URL"] = (
            f"https://{os.getenv('MINIO_SERVICE_NAME')}:{os.getenv('MINIO_SERVICE_PORT')}"
        )
        os.environ["AWS_CA_BUNDLE"] = certifi.where()
        os.environ["MLFLOW_S3_ENDPOINT_URL"] = mlflow_s3_endpoint_url
        print(os.environ)

        run_name = f"run_{uuid4()}"
        train_and_register_image_classifier_model(
            name="image_classifier_model",
            registered_name="image_classifier_model",
            run_name=run_name,
            experiment_name="Train image processing model",
            artifacts=[],
        )

    @task(
        task_display_name="Clean up local train and test images folders",
        trigger_rule="all_done",
    )
    def clean_up_local_folders():
        print("Deleting elements from train and test folders...")
        subprocess.run(
            "rm -r /app/images/train/*", check=True, shell=True, executable="/bin/bash"
        )
        subprocess.run(
            "rm -r /app/images/test/*", check=True, shell=True, executable="/bin/bash"
        )

    train_task = train_image_model(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        airflow_conn_minio_s3_conn=os.getenv("AIRFLOW_CONN_MINIO_S3_CONN"),
        mlflow_s3_endpoint_url=f"https://{os.getenv('MINIO_SERVICE_NAME')}:{os.getenv('MINIO_SERVICE_PORT')}",
    )
    training_files = list_training_files()
    (
        check_for_update(
            images=training_files["current_train_images"],
            metadata=training_files["training_metadata"],
        )
        >> [create_temporary_folders()]
        >> get_images_files()
        >> train_task
        >> clean_up_local_folders()
    )


# import mlflow
# import tensorflow as tf
# from uuid import uuid4
# import numpy as np
# from image_processing import _get_image_from_bytes

# MODEL_PATH = "./combined_trained_model_no_output.keras"
# MODEL_NAME = "image-processing"
# REGISTERED_MODEL_NAME = "image-processing"
# IMAGE = "./demo.jpg"

# print("Setting MLFlow URI")
# mlflow.set_tracking_uri("http://mlflow:5000")

# print("Defining experiment")
# mlflow.set_experiment("Store image models")

# with mlflow.start_run(run_name=f"run_{uuid4()}") as run:
#     # set tags
#     mlflow.set_tag("run_id", run.info.run_id)

#     model = tf.keras.models.load_model(MODEL_PATH)

#     with open(IMAGE, "rb") as f:
#         img_bytes = f.read()
#         _, img = _get_image_from_bytes(img_bytes)
#         print(f"shape: {img.shape}")

#         predictions = model.predict(np.array([img]))[0]

#     mlflow.tensorflow.log_model(
#         model=model, name=MODEL_NAME, input_example=np.array([img])
#     )

#     model_uri = f"runs:/{run.info.run_id}/{MODEL_NAME}"
#     mv = mlflow.register_model(model_uri, REGISTERED_MODEL_NAME)
#     print(f"Name: {mv.name}")
#     print(f"Version: {mv.version}")
