import pytest
from fastapi.testclient import TestClient
from main import app
from config.db import get_db_client
import asyncpg
from api.auth import hash_password, create_internal_api_access_token
# from config.config import settings.API_GATEWAY_HOST, settings.PROTECTED_ENDPOINT_URL
from config.settings import settings 

from datetime import datetime


client = TestClient(app)


@pytest.mark.asyncio
async def test_create_user():
    async with get_db_client() as conn:
        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.post(
            "/api/internal/postgresql/entity/user",
            json={
                "username": "newuser-postgres",
                "email": "newuser-postgres@example.com",
                "password": "newpassword",
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser-postgres"
        assert data["email"] == "newuser-postgres@example.com"
        assert "user_id" in data
        assert "created_at" in data

        # Clean up
        await conn.execute("DELETE FROM users WHERE id = $1", data["user_id"])


@pytest.mark.asyncio
async def test_get_user():
    async with get_db_client() as conn:
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }
        response = client.post(
            "/api/internal/postgresql/entity/user",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "password",
            },
            headers=headers,
        )
        data = response.json()
        user_id = data["user_id"]

        # Get token for the base user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.get(
            f"/api/internal/postgresql/entity/user/{user_id}", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "testuser@example.com"

        # Clean up
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest.mark.asyncio
async def test_update_user():
    async with get_db_client() as conn:
        # Create a base user
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }
        response = client.post(
            "/api/internal/postgresql/entity/user",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "password",
            },
            headers=headers,
        )
        data = response.json()
        user_id = data["user_id"]

        # Get token for the base user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.put(
            f"/api/internal/postgresql/entity/user/{user_id}",
            json={
                "username": "updateduser",
                "email": "updateduser@example.com",
                "password": "newpassword",
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updateduser@example.com"

        # Clean up
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)


@pytest.mark.asyncio
async def test_delete_user():
    async with get_db_client() as conn:
        # Create a base user
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }
        response = client.post(
            "/api/internal/postgresql/entity/user",
            json={
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "password",
            },
            headers=headers,
        )
        data = response.json()
        user_id = data["user_id"]

        # Get token for the base user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.delete(
            f"/api/internal/postgresql/entity/user/{user_id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json() == {"message": "User deleted successfully"}

        # Verify deletion
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        assert user is None
