import sys
import os
import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import hash_password
# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from main import create_app
from test.config.test_settings import test_settings
from config.db import get_db

# Créer une application avec les paramètres de test
app = create_app(test_settings)
client = TestClient(app)

@pytest.mark.asyncio
async def test_login_for_access_token():
    # Utiliser les paramètres de test pour obtenir la base de données
    db: AsyncIOMotorClient = await get_db(test_settings)

    # Créer un utilisateur pour le test
    await db.users.insert_one({
        "username": "test_auth",
        "email": "test_auth@example.com",
        "password": f"{hash_password("test_auth_password")}",  # hash de 'password'
        "roles": []
    })

    # Effectuer le test
    response = client.post("/token", data={"username": "test_auth", "password": "test_auth_password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Supprimer l'utilisateur après le test
    await db.users.delete_one({"username": "test_auth"})
