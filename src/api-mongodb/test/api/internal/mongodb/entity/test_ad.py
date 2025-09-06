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
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

        payload = {"designation": "newtitle", 
                   "description": "vinyl", 
                   "image_name": "00_image_1234.jpg", 
                   "bucket_name": "raw-images", 
                   "category": "Jeu PC"}

        response = client.post("/api/internal/mongodb/entity/ad", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["image_name"] == "00_image_1234.jpg"
        assert data["bucket_name"] == "raw-images"
        assert data["category"] == {"code": 2905, "label": "Jeu PC"}
        assert "ad_id" in data and "created_at" in data
        # Bdd  ads
        ad_id = ObjectId(data["ad_id"])
        ad_doc = await db.ads.find_one({"_id": ad_id})
        assert ad_doc is not None
        # Bdd categories
        cat_doc = await db.categories.find_one({"code": 2905})
        assert cat_doc is not None and cat_doc["label"] == "Jeu PC"
        # Bdd ad_categories
        link = await db.ad_categories.find_one({"ad_id": ad_id})
        assert link is not None and link["category_id"] == cat_doc["_id"]
        # Clean up
        await db.ads.delete_one({"_id": ObjectId(data["ad_id"])})
        await db.ad_categories.delete_many({"ad_id": ad_id})
        await db.ads.delete_one({"_id": ad_id})
        await db.categories.delete_many({"_id": cat_doc["_id"]})
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
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

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
        cat = await db.categories.insert_one({"code": 2905, "label": "Jeu PC"})
        await db.ad_categories.insert_one({"ad_id": ad_id, "category_id": cat.inserted_id})

        response = client.get(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "newtitle"
        assert data["description"] == "vinyl"
        assert data["image_name"] == "00_image_1234.jpg"
        assert data["bucket_name"] == "raw-images"
        assert data["category"] == {"code": 2905, "label": "Jeu PC"}

        # Clean up
        await db.ad_categories.delete_many({"ad_id": ObjectId(ad_id)})
        await db.categories.delete_many({"_id": cat.inserted_id})
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
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

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
        cat1 = await db.categories.insert_one({"code": 2905, "label": "Jeu PC"})
        await db.ad_categories.insert_one({"ad_id": ad_id, "category_id": cat1.inserted_id})

        payload = {
            "designation": "updatedtitle",
            "description": "newvinyl",
            "image_name": "00_image_456.jpg",
            "bucket_name": "images-raw",
            "category": "Accessoire Console"   # ou 50 ou "ACCESSOIRE_CONSOLE"
        }
        response = client.put(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["designation"] == "updatedtitle"
        assert data["description"] == "newvinyl"
        assert data["image_name"] == "00_image_456.jpg"
        assert data["bucket_name"] == "images-raw"
        assert data["category"] == {"code": 50, "label": "Accessoire Console"}

        link = await db.ad_categories.find_one({"ad_id": ad_id})
        cat2 = await db.categories.find_one({"code": 50})
        assert link is not None and cat2 is not None and link["category_id"] == cat2["_id"]

        # Clean up
        await db.ad_categories.delete_many({"ad_id": ad_id})
        await db.categories.delete_many({"_id": {"$in": [cat1.inserted_id, cat2["_id"]]}})
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
        headers = {"Authorization": f"Bearer {token}", "Referer": API_GATEWAY_HOST + PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}

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
        cat = await db.categories.insert_one({"code": 2905, "label": "Jeu PC"})
        await db.ad_categories.insert_one({"ad_id": ad_id, "category_id": cat.inserted_id})


        response = client.delete(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Ad deleted successfully"}

        # Verify deletion
        assert await db.ads.find_one({"_id": ad_id}) is None
        assert await db.ad_categories.find_one({"ad_id": ad_id}) is None
        assert await db.categories.find_one({"_id": cat.inserted_id}) is not None

        # Clean up
        await db.ad_categories.delete_many({"ad_id": ad_id})
        await db.categories.delete_many({"_id": cat.inserted_id})
        await db.users.delete_one({"_id": ObjectId(user_id)})
