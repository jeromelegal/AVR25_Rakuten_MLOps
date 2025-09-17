import pytest
from fastapi.testclient import TestClient
from main import create_app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings  # Importer depuis le fichier de configuration de test

client = TestClient(create_app(test_settings))  # Utiliser la configuration de test

@pytest.mark.asyncio
async def test_create_ad():
    async with get_db_client(test_settings) as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({
            "_id": ObjectId(user_id),
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

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token
        }

<<<<<<< HEAD
        payload = {
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images"
        }
=======
        payload = {"user": {"id": 1000, "username": "duck"},
                   "designation": "newtitle", 
                   "description": "vinyl", 
                   "category": "musique",
                   "images": ["00_image_1234.jpg", "01_image_456.jpg"], 
                   "created_at": "2023-10-01T00:00:00Z",
                   }
>>>>>>> e4d0804 (Add CRUD on api-mongodb and api-postgresql)

        response = client.post("/api/internal/mongodb/entity/ad", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == 1000
        assert data["user"]["username"] == "duck"
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
<<<<<<< HEAD
        assert data["image_name"] == "00_image_1234.jpg"
        assert data["bucket_name"] == "raw-images"
        assert "ad_id" in data
=======
        assert data["category"] == "musique"
        assert data["image_name"] == ["00_image_1234.jpg", "01_image_456.jpg"]
        assert "ad_id" in data 
>>>>>>> e4d0804 (Add CRUD on api-mongodb and api-postgresql)
        assert "created_at" in data

        # Clean up
        await db.ads.delete_one({"_id": ObjectId(data["ad_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_ad():
    async with get_db_client(test_settings) as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({
            "_id": ObjectId(user_id),
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

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token
        }

        # Create an ad
        ad_id = ObjectId()
        payload = {"_id": ad_id,
            "user": {"id": 1000, "username": "duck"},
            "designation": "newtitle", 
            "description": "vinyl", 
            "category": "musique",
            "images": ["00_image_1234.jpg", "01_image_456.jpg"], 
            "created_at": "2023-10-01T00:00:00Z",
            }
        
        await db.ads.insert_one(payload)

        response = client.get(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == 1000
        assert data["user"]["username"] == "duck"
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["category"] == "musique"
        assert data["image_name"] == ["00_image_1234.jpg", "01_image_456.jpg"]
        assert "ad_id" in data 
        assert "created_at" in data

        # Clean up
        await db.ads.delete_one({"_id": ad_id})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_ad():
    async with get_db_client(test_settings) as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({
            "_id": ObjectId(user_id),
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

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token
        }

        # Create an ad
        ad_id = ObjectId()
        payload = {"_id": ad_id,
            "user": {"id": 1000, "username": "duck"},
            "designation": "newtitle", 
            "description": "vinyl", 
            "category": "musique",
            "images": ["00_image_1234.jpg", "01_image_456.jpg"], 
            "created_at": "2023-10-01T00:00:00Z",
            }
        
        await db.ads.insert_one(payload)

<<<<<<< HEAD
        payload = {
            "designation": "updatedtitle",
            "description": "newvinyl",
            "image_name": "00_image_456.jpg",
            "bucket_name": "images-raw",
        }

        response = client.put(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", json=payload, headers=headers)
=======
        payload_updated = {
            "user": {"id": 1000, "username": "duckyduck"},
            "designation": "newalbum", 
            "description": "cd", 
            "category": "musique_cd",
            "images": ["10_image_1234.jpg", "11_image_456.jpg"], 
            "created_at": "2024-10-01T00:00:00Z",
            }
        response = client.put(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", json=payload_updated, headers=headers)
>>>>>>> e4d0804 (Add CRUD on api-mongodb and api-postgresql)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == 1000
        assert data["user"]["username"] == "duckyduck"
        assert data["designation"] == "newalbum"
        assert data["description"] == "cd"
        assert data["category"] == "musique_cd"
        assert data["image_name"] == ["10_image_1234.jpg", "11_image_456.jpg"]
        assert "ad_id" in data 
        assert "created_at" in data

        # Clean up
        await db.ads.delete_one({"_id": ad_id})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_ad():
    async with get_db_client(test_settings) as db:
        # Create a base user
        user_id = str(ObjectId())
        hashed_password = hash_password("password")
        await db.users.insert_one({
            "_id": ObjectId(user_id),
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

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)

        # Set the Authorization header
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token
        }

        # Create an ad
        ad_id = ObjectId()
        payload = {"_id": ad_id,
            "user": {"id": 1000, "username": "duck"},
            "designation": "newtitle", 
            "description": "vinyl", 
            "category": "musique",
            "images": ["00_image_1234.jpg", "01_image_456.jpg"], 
            "created_at": "2023-10-01T00:00:00Z",
            }
        
        await db.ads.insert_one(payload)

        response = client.delete(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Ad deleted successfully"}

        # Verify deletion
        assert await db.ads.find_one({"_id": ad_id}) is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
