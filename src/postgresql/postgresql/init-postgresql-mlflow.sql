-- MLFLOW
\echo Creating database :mlflow_db and user :mlflow_user

-- Create the MLflow database
CREATE DATABASE :"mlflow_db";

-- Create the MLflow user
CREATE USER :"mlflow_user" WITH ENCRYPTED PASSWORD :'mlflow_user_password';

-- Grant privileges
GRANT CONNECT ON DATABASE :"mlflow_db" TO :"mlflow_user";
GRANT ALL PRIVILEGES ON DATABASE :"mlflow_db" TO :"mlflow_user";