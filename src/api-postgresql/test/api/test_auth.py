import sys
import os
import pytest
from fastapi.testclient import TestClient
from api.auth import hash_password
from datetime import datetime

# Ajouter le chemin absolu de l'application
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))
from main import create_app
from test.config.test_settings import test_settings
from config.db import get_db_client  # Assurez-vous que cela correspond à votre configuration PostgreSQL

# Créer une application avec les paramètres de test
app = create_app(test_settings)
client = TestClient(app)

@pytest.mark.asyncio
async def test_login_for_access_token():
    # Utiliser les paramètres de test pour obtenir la base de données
    async with get_db_client(test_settings) as db:
        # Créer un utilisateur pour le test
        hashed_password = hash_password("test_auth_password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_at, created_by) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            "test_auth", "test_auth@example.com", hashed_password, datetime.now(), 0
        )

    # Effectuer le test
    response = client.post("/token", data={"username": "test_auth", "password": "test_auth_password"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Si nécessaire, convertir user_id en chaîne (bien que ce soit fait du côté serveur habituellement)
    assert isinstance(data.get("user_id"), str)  # Assurez-vous que `user_id` est une chaîne

    # Supprimer l'utilisateur après le test
    async with get_db_client(test_settings) as db:
        await db.execute(
            "DELETE FROM users WHERE username = $1",
            "test_auth"
        )

@pytest.mark.asyncio
async def test_invalid_login():
    # Essayer de se connecter avec des informations d'identification incorrectes
    response = client.post("/token", data={"username": "test_auth", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
