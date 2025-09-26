from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from datetime import datetime
import logging


def test_minio_connection():
    logger = logging.getLogger("airflow.task")

    try:
        logger.info("🔍 Initialisation du hook S3")
        hook = S3Hook(aws_conn_id="minio_s3_conn")

        bucket_name = "raw-images"
        logger.info(f"📦 Listing du bucket : {bucket_name}")
        keys = hook.list_keys(bucket_name=bucket_name)

        if keys:
            logger.info(f"✅ Objets trouvés : {keys}")
        else:
            logger.warning("⚠️ Aucun objet trouvé.")
    except Exception as e:
        logger.exception("❌ Erreur pendant l'accès à MinIO")
        raise


with DAG(
    dag_id="test_minio_s3",
    start_date=datetime(2023, 1, 1),
    schedule=None,
    catchup=False,
    is_paused_upon_creation=True,
    tags=["test", "minio"],
) as dag:

    test_task = PythonOperator(
        task_id="list_minio_objects", python_callable=test_minio_connection
    )
