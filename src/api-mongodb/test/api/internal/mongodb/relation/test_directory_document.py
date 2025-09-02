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
async def test_create_directory_document():
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

        # Create a directory
        directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(directory_id), "name": "testdirectory", "path": "/path/to/directory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.post("/api/internal/mongodb/relation/directory_document", json={"directory_id": directory_id, "document_id": document_id, "position": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["directory_id"] == directory_id
        assert data["document_id"] == document_id
        assert data["position"] == 1
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await db.directory_document.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.directories.delete_one({"_id": ObjectId(directory_id)})
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_directory_document():
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

        # Create a directory
        directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(directory_id), "name": "testdirectory", "path": "/path/to/directory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a directory-document relation
        relation_id = str(ObjectId())
        await db.directory_document.insert_one({"_id": ObjectId(relation_id), "directory_id": directory_id, "document_id": document_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/directory_document/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["directory_id"] == directory_id
        assert data["document_id"] == document_id
        assert data["position"] == 1

        # Clean up
        await db.directory_document.delete_one({"_id": ObjectId(relation_id)})
        await db.directories.delete_one({"_id": ObjectId(directory_id)})
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_directory_document():
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

        # Create a directory
        directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(directory_id), "name": "testdirectory", "path": "/path/to/directory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a directory-document relation
        relation_id = str(ObjectId())
        await db.directory_document.insert_one({"_id": ObjectId(relation_id), "directory_id": directory_id, "document_id": document_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/directory_document/{relation_id}", json={"directory_id": directory_id, "document_id": document_id, "position": 2}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["directory_id"] == directory_id
        assert data["document_id"] == document_id
        assert data["position"] == 2

        # Clean up
        await db.directory_document.delete_one({"_id": ObjectId(relation_id)})
        await db.directories.delete_one({"_id": ObjectId(directory_id)})
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_directory_document():
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

        # Create a directory
        directory_id = str(ObjectId())
        await db.directories.insert_one({"_id": ObjectId(directory_id), "name": "testdirectory", "path": "/path/to/directory", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a directory-document relation
        relation_id = str(ObjectId())
        await db.directory_document.insert_one({"_id": ObjectId(relation_id), "directory_id": directory_id, "document_id": document_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/directory_document/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Directory-Document relation deleted successfully"}

        # Verify deletion
        relation = await db.directory_document.find_one({"_id": ObjectId(relation_id)})
        assert relation is None

        # Clean up
        await db.directories.delete_one({"_id": ObjectId(directory_id)})
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
