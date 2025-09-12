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

# Variables pour les informations de connexion
PROTECTED_ENDPOINT_URL = settings.API_GATEWAY_PROTECTED_ENDPOINT_URL
USERNAME = f"{nombre_aleatoire}newuser-gateway-signup"
EMAIL = f"{USERNAME}@example.com"
PASSWORD = f"{USERNAME}"

client = TestClient(app)

def test_signup():
    # Exemple de test pour l'endpoint de signup
    response = client.post(
        f"{PROTECTED_ENDPOINT_URL}/signup",
        json={
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD,
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"

