import pytest
from fastapi.testclient import TestClient
from main import app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
# from config.config import API_GATEWAY_HOST, settings.PROTECTED_ENDPOINT_URL
from config.settings import settings 

client = TestClient(app)

@pytest.mark.asyncio
async def test_create_ad():
    async with get_db_client() as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({"_id": ObjectId(user_id), 
                                   "username": "testuser", 
                                   "email": "testuser@example.com", 
                                   "password": hashed_password, 
                                   "created_at": "2023-10-01T00:00:00Z", 
                                   "created_by": "system", 
                                   "roles": ["superadmin"]})

        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token( data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        payload = {"designation": "newtitle", 
                   "description": "vinyl", 
                   "image_name": "00_image_1234.jpg", 
                   "bucket_name": "raw-images"
                   }

        response = client.post("/api/internal/mongodb/entity/ad", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["image_name"] == "00_image_1234.jpg"
        assert data["bucket_name"] == "raw-images"
        assert "ad_id" in data 
        assert "created_at" in data
        assert "created_by" in data

        # Clean up
        await db.ads.delete_one({"_id": ObjectId(data["ad_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_ad():
    async with get_db_client() as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({"_id": ObjectId(user_id), 
                                   "username": "testuser", 
                                   "email": "testuser@example.com", 
                                   "password": hashed_password, 
                                   "created_at": "2023-10-01T00:00:00Z", 
                                   "created_by": "system", 
                                   "roles": ["superadmin"]
                                   })
        
        # Get token for the base user
        login_response = client.post("/token", data={"username": "testuser", "password": "password"})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token( data={"scope": "internal"})

        # Set the Authorization header
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create an ad
        ad_id = ObjectId()
        await db.ads.insert_one({
            "_id": ad_id,
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        response = client.get(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["image_name"] == "00_image_1234.jpg"
        assert data["bucket_name"] == "raw-images"

        # Clean up
        await db.ads.delete_one({"_id": ad_id})
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
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a ad
        ad_id = ObjectId()
        await db.ads.insert_one({
            "_id": ad_id,
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        payload = {
            "designation": "updatedtitle",
            "description": "newvinyl",
            "image_name": "00_image_456.jpg",
            "bucket_name": "images-raw",
        }
        response = client.put(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "updatedtitle"
        assert data["description"] == "newvinyl"
        assert data["image_name"] == "00_image_456.jpg"
        assert data["bucket_name"] == "images-raw"

        # Clean up
        await db.ads.delete_one({"_id": ad_id})
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
        headers = {"Authorization": f"Bearer {token}", "Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        # Create a ad
        ad_id = ObjectId()
        await db.ads.insert_one({
            "_id": ad_id,
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        response = client.delete(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Ad deleted successfully"}

        # Verify deletion
        assert await db.ads.find_one({"_id": ad_id}) is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
