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
async def test_create_stage():
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

        response = client.post("/api/internal/mongodb/entity/stage", json={"name": "newstage", "type": "data_processing", "configuration": {"param": "value"}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newstage"
        assert data["type"] == "data_processing"
        assert data["configuration"] == {"param": "value"}
        assert "stage_id" in data
        assert "created_at" in data

        # Clean up
        await db.stages.delete_one({"_id": ObjectId(data["stage_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_stage():
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

        # Create a stage
        stage_id = str(ObjectId())
        await db.stages.insert_one({"_id": ObjectId(stage_id), "name": "teststage", "type": "data_processing", "configuration": {"param": "value"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/entity/stage/{stage_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "teststage"
        assert data["type"] == "data_processing"
        assert data["configuration"] == {"param": "value"}

        # Clean up
        await db.stages.delete_one({"_id": ObjectId(stage_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_stage():
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

        # Create a stage
        stage_id = str(ObjectId())
        await db.stages.insert_one({"_id": ObjectId(stage_id), "name": "teststage", "type": "data_processing", "configuration": {"param": "value"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/entity/stage/{stage_id}", json={"name": "updatedstage", "type": "data_processing", "configuration": {"param": "newvalue"}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updatedstage"
        assert data["type"] == "data_processing"
        assert data["configuration"] == {"param": "newvalue"}

        # Clean up
        await db.stages.delete_one({"_id": ObjectId(stage_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_stage():
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

        # Create a stage
        stage_id = str(ObjectId())
        await db.stages.insert_one({"_id": ObjectId(stage_id), "name": "teststage", "type": "data_processing", "configuration": {"param": "value"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/entity/stage/{stage_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Stage deleted successfully"}

        # Verify deletion
        stage = await db.stages.find_one({"_id": ObjectId(stage_id)})
        assert stage is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
