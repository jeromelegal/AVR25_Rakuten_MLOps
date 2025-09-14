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
async def test_create_page():
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

        response = client.post("/api/internal/mongodb/entity/page", json={"name": "newpage", "content": "Page content"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newpage"
        assert data["content"] == "Page content"
        assert "page_id" in data
        assert "created_at" in data

        # Clean up
        await db.pages.delete_one({"_id": ObjectId(data["page_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_page():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/entity/page/{page_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testpage"
        assert data["content"] == "Test page content"

        # Clean up
        await db.pages.delete_one({"_id": ObjectId(page_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_page():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/entity/page/{page_id}", json={"name": "updatedpage", "content": "Updated page content"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updatedpage"
        assert data["content"] == "Updated page content"

        # Clean up
        await db.pages.delete_one({"_id": ObjectId(page_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_page():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/entity/page/{page_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Page deleted successfully"}

        # Verify deletion
        page = await db.pages.find_one({"_id": ObjectId(page_id)})
        assert page is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
