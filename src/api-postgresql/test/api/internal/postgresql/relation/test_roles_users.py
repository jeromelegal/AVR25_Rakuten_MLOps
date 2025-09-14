import pytest
from fastapi.testclient import TestClient
from main import app
from config.db import get_db_client
import asyncpg
from api.auth import hash_password, create_internal_api_access_token
# from config.config import settings.API_GATEWAY_HOST, settings.PROTECTED_ENDPOINT_URL
from config.settings import settings 


client = TestClient(app)

@pytest.mark.asyncio
async def test_create_role_user():
    async with get_db_client() as conn:
        # Create a base user
        user_id = await conn.fetchval(
            "INSERT INTO users (username, email, password, created_at, created_by, roles) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "testuser", "testuser@example.com", hash_password("password"), "2023-10-01T00:00:00Z", "system", ["superadmin"]
        )

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", "2023-10-01T00:00:00Z", user_id
        )

        response = client.post("/api/internal/postgresql/relation/role_user", json={"role_id": role_id, "user_id": user_id, "permissions": {"read": True, "write": False}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == role_id
        assert data["user_id"] == user_id
        assert data["permissions"] == {"read": True, "write": False}
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await conn.execute("DELETE FROM role_users WHERE id = $1", data["relation_id"])
        await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_get_role_user():
    async with get_db_client() as conn:
        # Create a base user
        user_id = await conn.fetchval(
            "INSERT INTO users (username, email, password, created_at, created_by, roles) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "testuser", "testuser@example.com", hash_password("password"), "2023-10-01T00:00:00Z", "system", ["superadmin"]
        )

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", "2023-10-01T00:00:00Z", user_id
        )

        # Create a role-user relation
        relation_id = await conn.fetchval(
            "INSERT INTO role_users (role_id, user_id, permissions, created_at, created_by) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            role_id, user_id, {"read": True, "write": False}, "2023-10-01T00:00:00Z", user_id
        )

        response = client.get(f"/api/internal/postgresql/relation/role_user/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == role_id
        assert data["user_id"] == user_id
        assert data["permissions"] == {"read": True, "write": False}

        # Clean up
        await conn.execute("DELETE FROM role_users WHERE id = $1", relation_id)
        await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_update_role_user():
    async with get_db_client() as conn:
        # Create a base user
        user_id = await conn.fetchval(
            "INSERT INTO users (username, email, password, created_at, created_by, roles) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "testuser", "testuser@example.com", hash_password("password"), "2023-10-01T00:00:00Z", "system", ["superadmin"]
        )

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", "2023-10-01T00:00:00Z", user_id
        )

        # Create a role-user relation
        relation_id = await conn.fetchval(
            "INSERT INTO role_users (role_id, user_id, permissions, created_at, created_by) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            role_id, user_id, {"read": True, "write": False}, "2023-10-01T00:00:00Z", user_id
        )

        response = client.put(f"/api/internal/postgresql/relation/role_user/{relation_id}", json={"role_id": role_id, "user_id": user_id, "permissions": {"read": True, "write": True}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == role_id
        assert data["user_id"] == user_id
        assert data["permissions"] == {"read": True, "write": True}

        # Clean up
        await conn.execute("DELETE FROM role_users WHERE id = $1", relation_id)
        await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_delete_role_user():
    async with get_db_client() as conn:
        # Create a base user
        user_id = await conn.fetchval(
            "INSERT INTO users (username, email, password, created_at, created_by, roles) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id",
            "testuser", "testuser@example.com", hash_password("password"), "2023-10-01T00:00:00Z", "system", ["superadmin"]
        )

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a role
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            "testrole", "2023-10-01T00:00:00Z", user_id
        )

        # Create a role-user relation
        relation_id = await conn.fetchval(
            "INSERT INTO role_users (role_id, user_id, permissions, created_at, created_by) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            role_id, user_id, {"read": True, "write": False}, "2023-10-01T00:00:00Z", user_id
        )

        response = client.delete(f"/api/internal/postgresql/relation/role_user/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Role-User relation deleted successfully"}

        # Verify deletion
        role_user = await conn.fetchrow("SELECT * FROM role_users WHERE id = $1", relation_id)
        assert role_user is None

        # Clean up
        await conn.execute("DELETE FROM roles WHERE id = $1", role_id)
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
