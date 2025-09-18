from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def say_hello():
    print("Hello world from Airflow!")

with DAG(
    dag_id="hello_world_dag",
    start_date=datetime(2023, 1, 1),

    catchup=False,
    tags=["test", "hello"],
) as dag:

    hello_task = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello
    )
