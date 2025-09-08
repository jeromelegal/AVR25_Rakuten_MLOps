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
async def test_create_ad_category():
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

        # Create an ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({
            "_id": ObjectId(ad_id),
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        # Create a category
        category_id = str(ObjectId())
        await db.categories.insert_one({"_id": ObjectId(category_id), "code": 9999, "label": "TEST"})

        response = client.post("/api/internal/mongodb/relation/ad_category", json={"ad_id": ad_id, "category_id": category_id}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ad_id"] == ad_id
        assert data["category_id"] == category_id
        #assert data["position"] == 1
        assert "relation_id" in data
        assert "created_at" in data
        assert "created_by" in data

        # Clean up
        await db.ad_category.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.ads.delete_one({"_id": ObjectId(ad_id)})
        await db.categories.delete_one({"_id": ObjectId(category_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_ad_category():
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

        # Create an ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({
            "_id": ObjectId(ad_id),
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        # Create a category
        category_id = str(ObjectId())
        await db.categories.insert_one({"_id": ObjectId(category_id), "code": 9999, "label": "TEST"})

        # Create an ad-category relation
        relation_id = str(ObjectId())
        await db.ad_category.insert_one({"_id": ObjectId(relation_id), "ad_id": ad_id, "category_id": category_id, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/ad_category/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ad_id"] == ad_id
        assert data["category_id"] == category_id
        assert "relation_id" in data
        assert "created_at" in data
        assert "created_by" in data
        # assert data["position"] == 1

        # Clean up
        await db.ad_category.delete_one({"_id": ObjectId(relation_id)})
        await db.ads.delete_one({"_id": ObjectId(ad_id)})
        await db.categories.delete_one({"_id": ObjectId(category_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_ad_category():
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

        # Create an ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({
            "_id": ObjectId(ad_id),
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        # Create a category
        category_id = str(ObjectId())
        await db.categories.insert_one({"_id": ObjectId(category_id), "code": 9999, "label": "TEST"})

        # Create an ad-category relation
        relation_id = str(ObjectId())
        await db.ad_category.insert_one({"_id": ObjectId(relation_id), "ad_id": ObjectId(ad_id), "category_id": ObjectId(category_id), "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/ad_category/{relation_id}", json={"ad_id": ad_id, "category_id": category_id}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ad_id"] == ad_id
        assert data["category_id"] == category_id

        # Clean up
        await db.ad_category.delete_one({"_id": ObjectId(relation_id)})
        await db.ads.delete_one({"_id": ObjectId(ad_id)})
        await db.categories.delete_one({"_id": ObjectId(category_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_ad_category():
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

        # Create an ad
        ad_id = str(ObjectId())
        await db.ads.insert_one({
            "_id": ObjectId(ad_id),
            "designation": "newtitle",
            "description": "vinyl",
            "image_name": "00_image_1234.jpg",
            "bucket_name": "raw-images",
            "created_at": "2023-10-01T00:00:00Z",
            "created_by": user_id
        })

        # Create a category
        category_id = str(ObjectId())
        await db.categories.insert_one({"_id": ObjectId(category_id), "code": 9999, "label": "TEST"})

        # Create an ad-category relation
        relation_id = str(ObjectId())
        await db.ad_category.insert_one({"_id": ObjectId(relation_id), "ad_id": ObjectId(ad_id), "category_id": ObjectId(category_id), "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/ad_category/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Ad-Category relation deleted successfully"}

        # Verify deletion
        relation = await db.ad_category.find_one({"_id": ObjectId(relation_id)})
        assert relation is None

        # Clean up
        await db.ads.delete_one({"_id": ObjectId(ad_id)})
        await db.categories.delete_one({"_id": ObjectId(category_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
