from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os

SIMULATED_BUCKET_PATH = "/path/to/simulated_minio"

def check_for_new_file():
    files = os.listdir(SIMULATED_BUCKET_PATH)
    if "image.jpg" in files or "produit.json" in files:
        print("Fichier détecté, déclenchement du pipeline.")
        return True
    else:
        raise ValueError("Aucun fichier détecté dans le bucket simulé.")

def simulate_image_pipeline():
    print("Traitement image lancé (simulation MLflow)...")

def simulate_text_pipeline():
    print("Traitement texte lancé (simulation MLflow)...")

def merge_predictions():
    print("Fusion des prédictions image + texte...")

with DAG(
    dag_id="minio_simulated_trigger_dag",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["POC", "MinIO", "ML"],
) as dag:

    sensor_task = PythonOperator(
        task_id="check_minio_simulated",
        python_callable=check_for_new_file,
    )

    image_task = PythonOperator(
        task_id="simulate_image_pipeline",
        python_callable=simulate_image_pipeline,
    )

    text_task = PythonOperator(
        task_id="simulate_text_pipeline",
        python_callable=simulate_text_pipeline,
    )

    merge_task = PythonOperator(
        task_id="merge_predictions",
        python_callable=merge_predictions,
    )

    sensor_task >> [image_task, text_task] >> merge_task
