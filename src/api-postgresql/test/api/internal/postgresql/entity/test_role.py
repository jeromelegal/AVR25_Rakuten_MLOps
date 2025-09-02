import pytest
from fastapi.testclient import TestClient
from main import app
from config.db import get_db_client
import asyncpg
from api.auth import hash_password, create_internal_api_access_token
from config.config import API_GATEWAY_HOST, PROTECTED_ENDPOINT_URL
from datetime import datetime, UTC, timezone


client = TestClient(app)

@pytest.mark.asyncio
async def test_create_role():
    async with get_db_client() as conn:
        # Create a base user
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {"Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}
        response = client.post("/api/internal/postgresql/entity/user", json={"username": "testuser", "email": "testuser@example.com", "password": "password"}, headers=headers)
        data = response.json()
        user_id = data["user_id"]


        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        response = client.post("/api/internal/postgresql/entity/role", json={"name": "newrole"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newrole"
        assert "role_id" in data
        assert "created_at" in data

        # Clean up
        await conn.execute("DELETE FROM roles WHERE id = $1", data["role_id"])
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_get_role():
    async with get_db_client() as conn:
        # Create a base user
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {"Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}
        response = client.post("/api/internal/postgresql/entity/user", json={"username": "testuser", "email": "testuser@example.com", "password": "password"}, headers=headers)
        data = response.json()
        user_id = data["user_id"]


        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", datetime.now(), user_id
        )

        response = client.get(f"/api/internal/postgresql/entity/role/{role_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testrole"

        # Clean up
        await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_update_role():
    async with get_db_client() as conn:
        # Create a base user
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {"Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}
        response = client.post("/api/internal/postgresql/entity/user", json={"username": "testuser", "email": "testuser@example.com", "password": "password"}, headers=headers)
        data = response.json()
        user_id = data["user_id"]

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", datetime.now(), user_id
        )

        response = client.put(f"/api/internal/postgresql/entity/role/{role_id}", json={"name": "updatedrole"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updatedrole"

        # Clean up
        await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_delete_role():
    async with get_db_client() as conn:
        # Create a base user
        api_token = create_internal_api_access_token(data={"scope": "internal"})
        headers = {"Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}
        response = client.post("/api/internal/postgresql/entity/user", json={"username": "testuser", "email": "testuser@example.com", "password": "password"}, headers=headers)
        data = response.json()
        user_id = data["user_id"]

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", datetime.now(), user_id
        )

        response = client.delete(f"/api/internal/postgresql/entity/role/{role_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Role deleted successfully"}

        # Verify deletion
        role = await conn.fetchrow("SELECT * FROM roles WHERE id = $1", role_id)
        assert role is None

        # Clean up
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
