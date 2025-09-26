from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import logging


def say_hello():

    logger = logging.getLogger("airflow.task")
    logger.info("✅ Hello world from Airflow!")


with DAG(
    dag_id="hello_world_dag",
    start_date=datetime(2023, 1, 1),
    schedule=None,
    catchup=False,
    tags=["test", "hello"],
    is_paused_upon_creation=True,
) as dag:

    hello_task = PythonOperator(task_id="say_hello", python_callable=say_hello)
