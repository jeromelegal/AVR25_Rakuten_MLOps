import pytest
from fastapi.testclient import TestClient
from main import app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
import uuid
from config.config import API_GATEWAY_HOST, PROTECTED_ENDPOINT_URL

client = TestClient(app)

@pytest.mark.asyncio
async def test_create_index():
    async with get_db_client() as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({"_id": ObjectId(user_id), "username": "testuser", "email": "testuser@example.com", "password": hashed_password, "created_at": "2023-10-01T00:00:00Z", "created_by": "system", "roles": ["superadmin"]})

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token( data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        response = client.post("/api/internal/mongodb/entity/index", json={"name": "newindex", "description": "New index description", "statistics": {"mean": 5.0, "std_dev": 1.5}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newindex"
        assert data["description"] == "New index description"
        assert data["statistics"] == {"mean": 5.0, "std_dev": 1.5}
        assert "index_id" in data
        assert "created_at" in data
        assert "elasticsearch_id" in data

        # Clean up
        await db.indexes.delete_one({"_id": ObjectId(data["index_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_index():
    async with get_db_client() as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({"_id": ObjectId(user_id), "username": "testuser", "email": "testuser@example.com", "password": hashed_password, "created_at": "2023-10-01T00:00:00Z", "created_by": "system", "roles": ["superadmin"]})

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token( data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create an index
        index_id = str(ObjectId())
        elasticsearch_id = str(uuid.uuid4())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": elasticsearch_id})

        response = client.get(f"/api/internal/mongodb/entity/index/{index_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testindex"
        assert data["description"] == "Test index description"
        assert data["statistics"] == {"mean": 5.0, "std_dev": 1.5}
        assert data["elasticsearch_id"] == elasticsearch_id

        # Clean up
        await db.indexes.delete_one({"_id": ObjectId(index_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_index():
    async with get_db_client() as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({"_id": ObjectId(user_id), "username": "testuser", "email": "testuser@example.com", "password": hashed_password, "created_at": "2023-10-01T00:00:00Z", "created_by": "system", "roles": ["superadmin"]})

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token( data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create an index
        index_id = str(ObjectId())
        elasticsearch_id = str(uuid.uuid4())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": elasticsearch_id})

        response = client.put(f"/api/internal/mongodb/entity/index/{index_id}", json={"name": "updatedindex", "description": "Updated index description", "statistics": {"mean": 6.0, "std_dev": 2.0}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updatedindex"
        assert data["description"] == "Updated index description"
        assert data["statistics"] == {"mean": 6.0, "std_dev": 2.0}
        assert data["elasticsearch_id"] == elasticsearch_id

        # Clean up
        await db.indexes.delete_one({"_id": ObjectId(index_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_index():
    async with get_db_client() as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({"_id": ObjectId(user_id), "username": "testuser", "email": "testuser@example.com", "password": hashed_password, "created_at": "2023-10-01T00:00:00Z", "created_by": "system", "roles": ["superadmin"]})

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token( data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create an index
        index_id = str(ObjectId())
        elasticsearch_id = str(uuid.uuid4())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": elasticsearch_id})

        response = client.delete(f"/api/internal/mongodb/entity/index/{index_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Index deleted successfully"}

        # Verify deletion
        index = await db.indexes.find_one({"_id": ObjectId(index_id)})
        assert index is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
