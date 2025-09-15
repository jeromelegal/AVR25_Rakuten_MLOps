-- MLFLOW
\echo Creating database :mlflow_db and user :mlflow_user

-- Create the MLflow database
CREATE DATABASE :"mlflow_db";

\c :"mlflow_db";

-- Create the MLflow user
CREATE USER :"mlflow_user" WITH ENCRYPTED PASSWORD :'mlflow_user_password';
ALTER ROLE :"mlflow_user" SET client_encoding TO 'utf8';
ALTER ROLE :"mlflow_user" SET default_transaction_isolation TO 'read committed';
ALTER ROLE :"mlflow_user" SET timezone TO 'UTC';


-- Grant privileges
GRANT CONNECT ON DATABASE :"mlflow_db" TO :"mlflow_user";
GRANT ALL PRIVILEGES ON DATABASE :"mlflow_db" TO :"mlflow_user";
GRANT USAGE ON SCHEMA public TO :"mlflow_user";
GRANT CREATE ON SCHEMA public TO :"mlflow_user";
ALTER SCHEMA public OWNER TO :"mlflow_user";
ALTER ROLE :"mlflow_user" CREATEDB;