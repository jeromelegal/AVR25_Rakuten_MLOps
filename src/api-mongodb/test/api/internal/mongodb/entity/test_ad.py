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
async def test_create_ad():
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

        response = client.post("/api/internal/mongodb/entity/ad", json={"designation": "newtitle", "description": "vinyl", "image": "00_image_1234.jpg"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["image"] == "00_image_1234.jpg"
        assert "ad_id" in data
        assert "created_at" in data

        # Clean up
        await db.ads.delete_one({"_id": ObjectId(data["ad_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_ad():
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

        # Create a ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({"_id": ObjectId(ad_id), "designation": "newtitle", "description": "vinyl", "image": "00_image_1234.jpg", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/entity/ad/{ad_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["image"] == "00_image_1234.jpg"

        # Clean up
        await db.ads.delete_one({"_id": ObjectId(ad_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_ad():
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

        # Create a ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({"_id": ObjectId(ad_id), "designation": "newtitle", "description": "vinyl", "image": "00_image_1234.jpg", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/entity/ad/{ad_id}", json={"designation": "updatedtitle", "description": "newvinyl", "image": "00_image_456.jpg"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "updatedtitle"
        assert data["description"] == "newvinyl"
        assert data["image"] == "00_image_456.jpg"

        # Clean up
        await db.ads.delete_one({"_id": ObjectId(ad_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_ad():
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

        # Create a ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({"_id": ObjectId(ad_id), "designation": "newtitle", "description": "vinyl", "image": "00_image_1234.jpg", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/entity/ad/{ad_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Ad deleted successfully"}

        # Verify deletion
        ad = await db.ads.find_one({"_id": ObjectId(ad_id)})
        assert ad is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
