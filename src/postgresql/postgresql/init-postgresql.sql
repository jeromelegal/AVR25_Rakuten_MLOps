-- Créer un utilisateur root avec tous les privilèges
CREATE USER root WITH PASSWORD 'example';
ALTER USER root WITH SUPERUSER;

-- Créer la base de données file_storage
CREATE DATABASE file_storage;

-- Se connecter à la base de données file_storage
\c file_storage

-- Créer une table roles
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT NOT NULL
    
);

-- Créer une table users avec les colonnes password
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT NOT NULL
);

-- Créer une table de relation user_roles
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);

-- Créer un rôle dbManager avec des privilèges spécifiques
CREATE ROLE dbManager;
GRANT CONNECT ON DATABASE file_storage TO dbManager;
GRANT USAGE ON SCHEMA public TO dbManager;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dbManager;
GRANT SELECT, USAGE ON ALL SEQUENCES IN SCHEMA public TO dbManager;

-- Créer un utilisateur db_manager_user avec le rôle dbManager
CREATE USER db_manager_user WITH PASSWORD 'db_manager_user_password';
GRANT dbManager TO db_manager_user;

-- Créer un rôle userManager avec des privilèges spécifiques sur la table users
CREATE ROLE userManager;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE users TO userManager;

-- Créer un utilisateur user_manager avec le rôle userManager
CREATE USER user_manager WITH PASSWORD 'usermanagerpassword';
GRANT userManager TO user_manager;
