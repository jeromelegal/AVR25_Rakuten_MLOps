-- AIRFLOW
\echo Creating database :airflow_db and user :airflow_user

-- Create the Airflow database
CREATE DATABASE :"airflow_db";

\c :"airflow_db";

-- Create the Airflow user
CREATE USER :"airflow_user" WITH ENCRYPTED PASSWORD :'airflow_user_password';
ALTER ROLE :"airflow_user" SET client_encoding TO 'utf8';
ALTER ROLE :"airflow_user" SET default_transaction_isolation TO 'read committed';
ALTER ROLE :"airflow_user" SET timezone TO 'UTC';


-- Grant privileges
GRANT CONNECT ON DATABASE :"airflow_db" TO :"airflow_user";
GRANT ALL PRIVILEGES ON DATABASE :"airflow_db" TO :"airflow_user";
CREATE SCHEMA :"airflow_schema"; 
GRANT USAGE ON SCHEMA :"airflow_schema" TO :"airflow_user";
GRANT CREATE ON SCHEMA :"airflow_schema" TO :"airflow_user";
ALTER SCHEMA :"airflow_schema" OWNER TO :"airflow_user";
GRANT USAGE ON SCHEMA public TO :"airflow_user";
GRANT CREATE ON SCHEMA public TO :"airflow_user";
ALTER SCHEMA public OWNER TO :"airflow_user";
ALTER ROLE :"airflow_user" CREATEDB;
-- ALTER ROLE :"airflow_user" CREATEDB;