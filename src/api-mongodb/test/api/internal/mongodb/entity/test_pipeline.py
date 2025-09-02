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
async def test_create_pipeline():
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

        response = client.post("/api/internal/mongodb/entity/pipeline", json={"name": "newpipeline", "steps": [{"name": "step1", "type": "type1", "configuration": {"key": "value"}}]}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "newpipeline"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["name"] == "step1"
        assert "pipeline_id" in data
        assert "created_at" in data

        # Clean up
        await db.pipelines.delete_one({"_id": ObjectId(data["pipeline_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_pipeline():
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

        # Create a pipeline
        pipeline_id = str(ObjectId())
        await db.pipelines.insert_one({"_id": ObjectId(pipeline_id), "name": "testpipeline", "steps": [{"name": "step1", "type": "type1", "configuration": {"key": "value"}}], "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/entity/pipeline/{pipeline_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "testpipeline"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["name"] == "step1"

        # Clean up
        await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_pipeline():
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

        # Create a pipeline
        pipeline_id = str(ObjectId())
        await db.pipelines.insert_one({"_id": ObjectId(pipeline_id), "name": "testpipeline", "steps": [{"name": "step1", "type": "type1", "configuration": {"key": "value"}}], "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/entity/pipeline/{pipeline_id}", json={"name": "updatedpipeline", "steps": [{"name": "step2", "type": "type2", "configuration": {"key": "newvalue"}}]}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updatedpipeline"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["name"] == "step2"

        # Clean up
        await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_pipeline():
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

        # Create a pipeline
        pipeline_id = str(ObjectId())
        await db.pipelines.insert_one({"_id": ObjectId(pipeline_id), "name": "testpipeline", "steps": [{"name": "step1", "type": "type1", "configuration": {"key": "value"}}], "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/entity/pipeline/{pipeline_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Pipeline deleted successfully"}

        # Verify deletion
        pipeline = await db.pipelines.find_one({"_id": ObjectId(pipeline_id)})
        assert pipeline is None

        # Clean up
        await db.users.delete_one({"_id": ObjectId(user_id)})
