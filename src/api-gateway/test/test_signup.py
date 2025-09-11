import sys
import os
from fastapi.testclient import TestClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "/app")))

from main import app
from api.config.settings import settings

client = TestClient(app)


def test_signup():
    # Exemple de test pour l'endpoint de signup
    response = client.post(
        f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/signup",
        json={
            "username": "newuser-gateway",
            "email": "newuser-gateway@example.com",
            "password": "newpass",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"
    # assert "user_id" in response.json()  # Vérifier la présence de user_id
