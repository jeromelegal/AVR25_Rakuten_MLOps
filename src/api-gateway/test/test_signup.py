import sys
import os
from fastapi.testclient import TestClient
from config import config  # Importer le fichier de configuration
import random

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "/app")))
from main import app
from api.config.settings import settings

# Générer un entier aléatoire dans la plage spécifiée dans le fichier de configuration
nombre_aleatoire = random.randint(config.RANDOM_RANGE_START, config.RANDOM_RANGE_END)

# Variables pour les informations de connexion
PROTECTED_ENDPOINT_URL = settings.API_GATEWAY_PROTECTED_ENDPOINT_URL
USERNAME = f"{nombre_aleatoire}newuser-gateway-signup"
EMAIL = f"{USERNAME}@{config.DEFAULT_DOMAIN}"
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
