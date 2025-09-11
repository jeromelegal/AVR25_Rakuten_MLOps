import pytest
from fastapi.testclient import TestClient
from main import app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
from config.config import API_GATEWAY_HOST, PROTECTED_ENDPOINT_URL


client = TestClient(app)


@pytest.mark.asyncio
async def test_create_user():
    async with get_db_client() as db:

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL,
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

        # Clean up
        await db.users.delete_one({"_id": ObjectId(data["user_id"])})


@pytest.mark.asyncio
async def test_get_user():
    async with get_db_client() as db:
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

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL,
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


@pytest.mark.asyncio
async def test_update_user():
    async with get_db_client() as db:
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

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.put(
            f"/api/internal/mongodb/entity/user/{user_id}",
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
        await db.users.delete_one({"_id": ObjectId(user_id)})


@pytest.mark.asyncio
async def test_delete_user():
    async with get_db_client() as db:
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

        api_token = create_internal_api_access_token(data={"scope": "internal"})

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        response = client.delete(
            f"/api/internal/mongodb/entity/user/{user_id}", headers=headers
        )
        assert response.status_code == 200
        assert response.json() == {"message": "User deleted successfully"}

        # Verify deletion
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        assert user is None
