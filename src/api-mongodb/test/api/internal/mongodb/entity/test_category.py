import pytest
from fastapi.testclient import TestClient
from main import create_app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings  # Importer depuis le fichier de configuration de test

@pytest.mark.asyncio
async def test_create_user():
    # Utiliser les test_settings importés
    app = create_app(test_settings)
    client = TestClient(app)

    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    response = client.post(
        "/api/internal/mongodb/entity/user",
        json={
            "username": "newuser-mongodb",
            "email": "newuser-mongodb@example.com",
            "password": "newpassword",
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser-mongodb"
    assert data["email"] == "newuser-mongodb@example.com"
    assert "user_id" in data
    assert "created_at" in data

    # Nettoyage
    async with get_db_client(test_settings) as db:
        await db.users.delete_one({"_id": ObjectId(data["user_id"])})

@pytest.mark.asyncio
async def test_get_user():
    # Utiliser les test_settings importés
    app = create_app(test_settings)
    client = TestClient(app)

    async with get_db_client(test_settings) as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one(
            {
                "_id": ObjectId(user_id),
                "username": "testuser",
                "email": "testuser@example.com",
                "password": hashed_password,
                "created_at": "2023-10-01T00:00:00Z",
                "created_by": "system",
                "roles": ["superadmin"],
            }
        )

        # Get token for the base user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.get(
            f"/api/internal/mongodb/entity/user/{user_id}", headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
