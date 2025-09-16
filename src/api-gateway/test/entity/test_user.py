import sys
import os
from fastapi.testclient import TestClient
import random
from main import app
from config.config import config  # Importer le fichier de configuration
from config.test_settings import test_settings

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "/app")))

# Générer un entier aléatoire entre config.RANDOM_RANGE_START et config.RANDOM_RANGE_END
nombre_aleatoire = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)

# Variables pour les informations d'identification de l'utilisateur
username = f"{nombre_aleatoire}newuser-gateway-delete"
email = f"{username}@{config.DEFAULT_DOMAIN}"
password = f"{username}"

client = TestClient(app)

def test_delete_user_flow():
    # Inscrire l'utilisateur pour pouvoir le connecter et le supprimer
    signup_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert signup_response.status_code == 200

    # Connexion de l'utilisateur pour obtenir le token d'accès
    login_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Récupérer le token d'accès à partir de la réponse de connexion
    access_token = login_response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": access_token,
    }

    # Supprimer l'utilisateur des deux bases de données
    delete_response = client.delete(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/delete",
        headers=headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted successfully from both databases"

def test_delete_user_mongodb_only():
    # Inscrire l'utilisateur pour pouvoir le connecter et le supprimer
    signup_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup/mongodb",
        json={
            "username": username + "_mongodb",
            "email": email + "_mongodb",
            "password": password + "_mongodb",
        },
    )
    assert signup_response.status_code == 200

    # Connexion de l'utilisateur pour obtenir le token d'accès
    login_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": username + "_mongodb", "password": password + "_mongodb"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Récupérer le token d'accès à partir de la réponse de connexion
    access_token = login_response.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": access_token,
    }

    # Supprimer l'utilisateur seulement de MongoDB
    delete_response = client.delete(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/delete/mongodb",
        headers=headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted successfully from MongoDB"

def test_delete_user_postgresql_only():
    # Inscrire l'utilisateur pour pouvoir le connecter et le supprimer
    signup_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/signup/postgresql",
        json={
            "username": username + "_postgresql",
            "email": email + "_postgresql",
            "password": password + "_postgresql",
        },
    )
    assert signup_response.status_code == 200

    # Connexion de l'utilisateur pour obtenir le token d'accès
    login_response = client.post(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/login",
        data={"username": username + "_postgresql", "password": password + "_postgresql"},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Récupérer le token d'accès à partir de la réponse de connexion
    access_token = login_response.json()["access_token"]
    # En-têtes pour les requêtes authentifiées
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": access_token,
    }

    # Supprimer l'utilisateur seulement de PostgreSQL
    delete_response = client.delete(
        f"{test_settings.PROTECTED_ENDPOINT_URL}/delete/postgresql",
        headers=headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted successfully from PostgreSQL"
