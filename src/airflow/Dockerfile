FROM apache/airflow:2.8.1

USER root
RUN mkdir -p /opt/simulated_minio
COPY simulated_minio/ /opt/simulated_minio/

USER airflow
COPY dags/ /opt/airflow/dags/
