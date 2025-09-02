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
async def test_create_pipeline_index():
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

        # Create an index
        index_id = str(ObjectId())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": "test_elasticsearch_id"})

        response = client.post("/api/internal/mongodb/relation/pipeline_index", json={"pipeline_id": pipeline_id, "index_id": index_id, "position": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == pipeline_id
        assert data["index_id"] == index_id
        assert data["position"] == 1
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await db.pipeline_index.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        await db.indexes.delete_one({"_id": ObjectId(index_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_pipeline_index():
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

        # Create an index
        index_id = str(ObjectId())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": "test_elasticsearch_id"})

        # Create a pipeline-index relation
        relation_id = str(ObjectId())
        await db.pipeline_index.insert_one({"_id": ObjectId(relation_id), "pipeline_id": pipeline_id, "index_id": index_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/pipeline_index/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == pipeline_id
        assert data["index_id"] == index_id
        assert data["position"] == 1

        # Clean up
        await db.pipeline_index.delete_one({"_id": ObjectId(relation_id)})
        await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        await db.indexes.delete_one({"_id": ObjectId(index_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_pipeline_index():
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

        # Create an index
        index_id = str(ObjectId())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": "test_elasticsearch_id"})

        # Create a pipeline-index relation
        relation_id = str(ObjectId())
        await db.pipeline_index.insert_one({"_id": ObjectId(relation_id), "pipeline_id": pipeline_id, "index_id": index_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/pipeline_index/{relation_id}", json={"pipeline_id": pipeline_id, "index_id": index_id, "position": 2}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_id"] == pipeline_id
        assert data["index_id"] == index_id
        assert data["position"] == 2

        # Clean up
        await db.pipeline_index.delete_one({"_id": ObjectId(relation_id)})
        await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        await db.indexes.delete_one({"_id": ObjectId(index_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_pipeline_index():
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

        # Create an index
        index_id = str(ObjectId())
        await db.indexes.insert_one({"_id": ObjectId(index_id), "name": "testindex", "description": "Test index description", "statistics": {"mean": 5.0, "std_dev": 1.5}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id, "elasticsearch_id": "test_elasticsearch_id"})

        # Create a pipeline-index relation
        relation_id = str(ObjectId())
        await db.pipeline_index.insert_one({"_id": ObjectId(relation_id), "pipeline_id": pipeline_id, "index_id": index_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/pipeline_index/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Pipeline-Index relation deleted successfully"}

        # Verify deletion
        relation = await db.pipeline_index.find_one({"_id": ObjectId(relation_id)})
        assert relation is None

        # Clean up
        await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        await db.indexes.delete_one({"_id": ObjectId(index_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
