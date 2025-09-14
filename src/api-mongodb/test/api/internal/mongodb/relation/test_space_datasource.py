import pytest
from fastapi.testclient import TestClient
from main import app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
# from config.config import settings.API_GATEWAY_HOST, settings.PROTECTED_ENDPOINT_URL
from config.settings import settings 

client = TestClient(app)

@pytest.mark.asyncio
async def test_create_space_datasource():
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

        # Create a space
        space_id = str(ObjectId())
        await db.spaces.insert_one({"_id": ObjectId(space_id), "name": "testspace", "description": "Test space description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a datasource
        datasource_id = str(ObjectId())
        await db.datasources.insert_one({"_id": ObjectId(datasource_id), "name": "testdatasource", "type": "GraphQL", "configuration": {"url": "https://example.com/graphql"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.post("/api/internal/mongodb/relation/space_datasource", json={"space_id": space_id, "datasource_id": datasource_id, "position": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["space_id"] == space_id
        assert data["datasource_id"] == datasource_id
        assert data["position"] == 1
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await db.space_datasource.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.spaces.delete_one({"_id": ObjectId(space_id)})
        await db.datasources.delete_one({"_id": ObjectId(datasource_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_space_datasource():
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

        # Create a space
        space_id = str(ObjectId())
        await db.spaces.insert_one({"_id": ObjectId(space_id), "name": "testspace", "description": "Test space description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a datasource
        datasource_id = str(ObjectId())
        await db.datasources.insert_one({"_id": ObjectId(datasource_id), "name": "testdatasource", "type": "GraphQL", "configuration": {"url": "https://example.com/graphql"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a space-datasource relation
        relation_id = str(ObjectId())
        await db.space_datasource.insert_one({"_id": ObjectId(relation_id), "space_id": space_id, "datasource_id": datasource_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/space_datasource/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["space_id"] == space_id
        assert data["datasource_id"] == datasource_id
        assert data["position"] == 1

        # Clean up
        await db.space_datasource.delete_one({"_id": ObjectId(relation_id)})
        await db.spaces.delete_one({"_id": ObjectId(space_id)})
        await db.datasources.delete_one({"_id": ObjectId(datasource_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_space_datasource():
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

        # Create a space
        space_id = str(ObjectId())
        await db.spaces.insert_one({"_id": ObjectId(space_id), "name": "testspace", "description": "Test space description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a datasource
        datasource_id = str(ObjectId())
        await db.datasources.insert_one({"_id": ObjectId(datasource_id), "name": "testdatasource", "type": "GraphQL", "configuration": {"url": "https://example.com/graphql"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a space-datasource relation
        relation_id = str(ObjectId())
        await db.space_datasource.insert_one({"_id": ObjectId(relation_id), "space_id": space_id, "datasource_id": datasource_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/space_datasource/{relation_id}", json={"space_id": space_id, "datasource_id": datasource_id, "position": 2}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["space_id"] == space_id
        assert data["datasource_id"] == datasource_id
        assert data["position"] == 2

        # Clean up
        await db.space_datasource.delete_one({"_id": ObjectId(relation_id)})
        await db.spaces.delete_one({"_id": ObjectId(space_id)})
        await db.datasources.delete_one({"_id": ObjectId(datasource_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_space_datasource():
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

        # Create a space
        space_id = str(ObjectId())
        await db.spaces.insert_one({"_id": ObjectId(space_id), "name": "testspace", "description": "Test space description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a datasource
        datasource_id = str(ObjectId())
        await db.datasources.insert_one({"_id": ObjectId(datasource_id), "name": "testdatasource", "type": "GraphQL", "configuration": {"url": "https://example.com/graphql"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a space-datasource relation
        relation_id = str(ObjectId())
        await db.space_datasource.insert_one({"_id": ObjectId(relation_id), "space_id": space_id, "datasource_id": datasource_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/space_datasource/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Space-Datasource relation deleted successfully"}

        # Verify deletion
        relation = await db.space_datasource.find_one({"_id": ObjectId(relation_id)})
        assert relation is None

        # Clean up
        await db.spaces.delete_one({"_id": ObjectId(space_id)})
        await db.datasources.delete_one({"_id": ObjectId(datasource_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
