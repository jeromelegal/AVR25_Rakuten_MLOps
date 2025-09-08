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
async def test_create_category():
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

        response = client.post("/api/internal/mongodb/entity/category", json={"code": 9999, "label": "TEST"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 9999
        assert data["label"] == "TEST"
        assert "category_id" in data
        # Bdd  categories
        category_dict = await db.categories.find_one({"_id": ObjectId(data["category_id"])})
        assert category_dict is not None
        # Bdd categories
        category_dict = await db.categories.find_one({"code": 9999})
        assert category_dict is not None and category_dict["label"] == "TEST"
        # Clean up
        await db.categories.delete_one({"_id": ObjectId(data["category_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_category():
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

        # Create a category
        category_id = ObjectId()
        await db.categories.insert_one({"_id": category_id, "code": 9999, "label": "TEST"})

        response = client.get(f"/api/internal/mongodb/entity/category/{str(category_id)}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 9999
        assert data["label"] == "TEST"

        # Clean up
        await db.categories.delete_one({"_id": ObjectId(data["category_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_category():
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
        category_id = ObjectId()
        await db.categories.insert_one({"_id": category_id, "code": 9999, "label": "TEST"})

        payload = {
            "code": 10000,
            "label": "NEW_TEST"
        }
        response = client.put(f"/api/internal/mongodb/entity/category/{str(category_id)}", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 10000
        assert data["label"] == "NEW_TEST"

        # Clean up
        await db.categories.delete_one({"_id": ObjectId(data["category_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_category():
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
        category_id = ObjectId()
        await db.categories.insert_one({"_id": category_id, "code": 9999, "label": "TEST"})

        response = client.delete(f"/api/internal/mongodb/entity/category/{str(category_id)}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Category deleted successfully"}

        # Verify deletion
        assert await db.categories.find_one({"_id": category_id}) is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
