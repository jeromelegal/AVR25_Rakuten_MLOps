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
username = f"{nombre_aleatoire}newuser-gateway-delete"
email = f"{username}@example.com"
password = f"{username}"

client = TestClient(app)

def test_delete_user():
    # Inscrire l'utilisateur pour pouvoir le connecter et le supprimer
    signup_response = client.post(
        f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/signup",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert signup_response.status_code == 200

    # Connexion de l'utilisateur pour obtenir le token d'accès
    login_response = client.post(
        f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

    # Récupérer le token d'accès à partir de la réponse de connexion
    access_token = login_response.json()["access_token"]
    # En-têtes pour les requêtes authentifiées
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Supprimer l'utilisateur des deux bases de données
    delete_response = client.delete(
        f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/delete",
        headers=headers
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User deleted successfully from both databases"

