import sys
import os
from fastapi.testclient import TestClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "/app")))
from main import app
from api.config.settings import settings

import random

# Générer un entier aléatoire entre 1 et 100
nombre_aleatoire = random.randint(1, 100000)

# Variables pour les informations d'identification de l'utilisateur
PROTECTED_ENDPOINT_URL = settings.API_GATEWAY_PROTECTED_ENDPOINT_URL
USERNAME = f"{nombre_aleatoire}newuser-gateway-login"
EMAIL = f"{USERNAME}@example.com"
PASSWORD = f"{USERNAME}"

client = TestClient(app)

def test_login():
    # Inscrire l'utilisateur pour pouvoir se connecter
    signup_response = client.post(
        f"{PROTECTED_ENDPOINT_URL}/signup",
        json={
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
        },
    )
    assert signup_response.status_code == 200

    # Exemple de test pour l'endpoint de login
    login_response = client.post(
        f"{PROTECTED_ENDPOINT_URL}/login",
        data={"username": USERNAME, "password": PASSWORD},
    )
    assert login_response.status_code == 200
    response_data = login_response.json()
    assert "access_token" in response_data

    # Vérification de la structure du méta-token
    access_token = response_data["access_token"]
    assert "." in access_token  # Vérifier que le token a un format signé avec des parties séparées par des '.'

    print("Test passed: Login successful and meta token received.")
