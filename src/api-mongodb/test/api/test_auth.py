import sys
import os
import pytest
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '/app')))

from main import app
from config.db import get_db

client = TestClient(app)

@pytest.mark.asyncio
async def test_login_for_access_token():
    db: AsyncIOMotorClient = await get_db()
    # Créer un utilisateur pour le test
    await db.users.insert_one({
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # hash de 'password'
        "roles": []
    })

    response = client.post("/token", data={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Supprimer l'utilisateur après le test
    await db.users.delete_one({"username": "testuser"})
