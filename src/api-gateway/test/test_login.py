import sys
import os
from fastapi.testclient import TestClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

from main import app
from api.config.settings import settings

client = TestClient(app)

def test_login():
    # Exemple de test pour l'endpoint de login
    response = client.post(f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/login", data={"username": "newuser", "password": "newpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()
