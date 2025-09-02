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
async def test_create_directory_directory():
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

        # Create a parent directory
        parent_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(parent_directory_id), "name": "parentdirectory", "path": "/path/to/parentdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a child directory
        child_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(child_directory_id), "name": "childdirectory", "path": "/path/to/childdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.post("/api/internal/mongodb/relation/directory_directory", json={"parent_directory_id": parent_directory_id, "child_directory_id": child_directory_id, "position": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["parent_directory_id"] == parent_directory_id
        assert data["child_directory_id"] == child_directory_id
        assert data["position"] == 1
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await db.directory_directory.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.directories.delete_one({"_id": ObjectId(parent_directory_id)})
        await db.directories.delete_one({"_id": ObjectId(child_directory_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_directory_directory():
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

        # Create a parent directory
        parent_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(parent_directory_id), "name": "parentdirectory", "path": "/path/to/parentdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a child directory
        child_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(child_directory_id), "name": "childdirectory", "path": "/path/to/childdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a directory-directory relation
        relation_id = str(ObjectId())
        await db.directory_directory.insert_one({"_id": ObjectId(relation_id), "parent_directory_id": parent_directory_id, "child_directory_id": child_directory_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/directory_directory/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["parent_directory_id"] == parent_directory_id
        assert data["child_directory_id"] == child_directory_id
        assert data["position"] == 1

        # Clean up
        await db.directory_directory.delete_one({"_id": ObjectId(relation_id)})
        await db.directories.delete_one({"_id": ObjectId(parent_directory_id)})
        await db.directories.delete_one({"_id": ObjectId(child_directory_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_directory_directory():
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

        # Create a parent directory
        parent_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(parent_directory_id), "name": "parentdirectory", "path": "/path/to/parentdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a child directory
        child_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(child_directory_id), "name": "childdirectory", "path": "/path/to/childdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a directory-directory relation
        relation_id = str(ObjectId())
        await db.directory_directory.insert_one({"_id": ObjectId(relation_id), "parent_directory_id": parent_directory_id, "child_directory_id": child_directory_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/directory_directory/{relation_id}", json={"parent_directory_id": parent_directory_id, "child_directory_id": child_directory_id, "position": 2}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["parent_directory_id"] == parent_directory_id
        assert data["child_directory_id"] == child_directory_id
        assert data["position"] == 2

        # Clean up
        await db.directory_directory.delete_one({"_id": ObjectId(relation_id)})
        await db.directories.delete_one({"_id": ObjectId(parent_directory_id)})
        await db.directories.delete_one({"_id": ObjectId(child_directory_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_directory_directory():
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

        # Create a parent directory
        parent_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(parent_directory_id), "name": "parentdirectory", "path": "/path/to/parentdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a child directory
        child_directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(child_directory_id), "name": "childdirectory", "path": "/path/to/childdirectory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a directory-directory relation
        relation_id = str(ObjectId())
        await db.directory_directory.insert_one({"_id": ObjectId(relation_id), "parent_directory_id": parent_directory_id, "child_directory_id": child_directory_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/directory_directory/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Directory-Directory relation deleted successfully"}

        # Verify deletion
        relation = await db.directory_directory.find_one({"_id": ObjectId(relation_id)})
        assert relation is None

        # Clean up
        await db.directories.delete_one({"_id": ObjectId(parent_directory_id)})
        await db.directories.delete_one({"_id": ObjectId(child_directory_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
