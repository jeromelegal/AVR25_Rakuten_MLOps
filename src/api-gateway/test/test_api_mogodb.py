import sys
import os
from fastapi.testclient import TestClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

from main import app
from api.config.settings import settings

client = TestClient(app)

# Test de la création d'annonce
def test_create_ad():
    response = client.post(f"{settings.API_GATEWAY_PROTECTED_ENDPOINT_URL}/api/internal/mongodb/entity/ad", json={
            "ad_id": "test",
            "designation": "test",
            "description": "test",
            "image": "test",
            "created_at": "test",
            "created_by": "test",
         })
    assert response.status_code == 200
    assert response.json() == {
        "ad_id": "test",
        "designation": "test",
        "description": "test",
        "image": "test",
        "created_at": "test",
        "created_by": "test",
        }
