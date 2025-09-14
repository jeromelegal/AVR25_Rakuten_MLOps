import pytest
from fastapi.testclient import TestClient
from main import app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
# from config.config import API_GATEWAY_HOST, PROTECTED_ENDPOINT_URL
from config.settings import settings 

client = TestClient(app)

@pytest.mark.asyncio
async def test_create_document():
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
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        response = client.post("/api/internal/mongodb/entity/document", json={"name": "newdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newdocument"
        assert data["type"] == "tableau"
        assert data["content"] == "content"
        assert data["variables"] == {"independent": ["var1", "var2"], "dependent": "var3"}
        assert data["path"] == "/path/to/document"
        assert "document_id" in data
        assert "created_at" in data

        # Clean up
        await db.documents.delete_one({"_id": ObjectId(data["document_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_document():
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
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/entity/document/{document_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testdocument"
        assert data["type"] == "tableau"
        assert data["content"] == "content"
        assert data["variables"] == {"independent": ["var1", "var2"], "dependent": "var3"}
        assert data["path"] == "/path/to/document"

        # Clean up
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_document():
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
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/entity/document/{document_id}", json={"name": "updateddocument", "type": "tableau", "content": "updated content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/updated/path/to/document"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updateddocument"
        assert data["type"] == "tableau"
        assert data["content"] == "updated content"
        assert data["variables"] == {"independent": ["var1", "var2"], "dependent": "var3"}
        assert data["path"] == "/updated/path/to/document"

        # Clean up
        await db.documents.delete_one({"_id": ObjectId(document_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_document():
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
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a document
        document_id = str(ObjectId())
        await db.documents.insert_one({"_id": ObjectId(document_id), "name": "testdocument", "type": "tableau", "content": "content", "variables": {"independent": ["var1", "var2"], "dependent": "var3"}, "path": "/path/to/document", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/entity/document/{document_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Document deleted successfully"}

        # Verify deletion
        document = await db.documents.find_one({"_id": ObjectId(document_id)})
        assert document is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
