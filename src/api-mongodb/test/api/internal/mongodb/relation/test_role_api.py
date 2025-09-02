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
async def test_create_role_api():
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

        # Create a role
        role_id = str(ObjectId())
        await db.roles.insert_one({"_id": ObjectId(role_id), "name": "testrole", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create an api
        api_id = str(ObjectId())
        await db.apis.insert_one({"_id": ObjectId(api_id), "name": "testapi", "endpoint": "/testapi", "description": "Test API description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.post("/api/internal/mongodb/relation/role_api", json={"role_id": role_id, "api_id": api_id, "permissions": {"read": True, "write": False}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == role_id
        assert data["api_id"] == api_id
        assert data["permissions"] == {"read": True, "write": False}
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await db.role_apis.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.roles.delete_one({"_id": ObjectId(role_id)})
        await db.apis.delete_one({"_id": ObjectId(api_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_role_api():
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

        # Create a role
        role_id = str(ObjectId())
        await db.roles.insert_one({"_id": ObjectId(role_id), "name": "testrole", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create an api
        api_id = str(ObjectId())
        await db.apis.insert_one({"_id": ObjectId(api_id), "name": "testapi", "endpoint": "/testapi", "description": "Test API description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a role-api relation
        relation_id = str(ObjectId())
        await db.role_apis.insert_one({"_id": ObjectId(relation_id), "role_id": role_id, "api_id": api_id, "permissions": {"read": True, "write": False}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/role_api/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == role_id
        assert data["api_id"] == api_id
        assert data["permissions"] == {"read": True, "write": False}

        # Clean up
        await db.role_apis.delete_one({"_id": ObjectId(relation_id)})
        await db.roles.delete_one({"_id": ObjectId(role_id)})
        await db.apis.delete_one({"_id": ObjectId(api_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_role_api():
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

        # Create a role
        role_id = str(ObjectId())
        await db.roles.insert_one({"_id": ObjectId(role_id), "name": "testrole", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create an api
        api_id = str(ObjectId())
        await db.apis.insert_one({"_id": ObjectId(api_id), "name": "testapi", "endpoint": "/testapi", "description": "Test API description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a role-api relation
        relation_id = str(ObjectId())
        await db.role_apis.insert_one({"_id": ObjectId(relation_id), "role_id": role_id, "api_id": api_id, "permissions": {"read": True, "write": False}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/role_api/{relation_id}", json={"role_id": role_id, "api_id": api_id, "permissions": {"read": True, "write": True}}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role_id"] == role_id
        assert data["api_id"] == api_id
        assert data["permissions"] == {"read": True, "write": True}

        # Clean up
        await db.role_apis.delete_one({"_id": ObjectId(relation_id)})
        await db.roles.delete_one({"_id": ObjectId(role_id)})
        await db.apis.delete_one({"_id": ObjectId(api_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_role_api():
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

        # Create a role
        role_id = str(ObjectId())
        await db.roles.insert_one({"_id": ObjectId(role_id), "name": "testrole", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create an api
        api_id = str(ObjectId())
        await db.apis.insert_one({"_id": ObjectId(api_id), "name": "testapi", "endpoint": "/testapi", "description": "Test API description", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a role-api relation
        relation_id = str(ObjectId())
        await db.role_apis.insert_one({"_id": ObjectId(relation_id), "role_id": role_id, "api_id": api_id, "permissions": {"read": True, "write": False}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/role_api/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Role-Api relation deleted successfully"}

        # Verify deletion
        role_api = await db.role_apis.find_one({"_id": ObjectId(relation_id)})
        assert role_api is None

        # Clean up
        await db.roles.delete_one({"_id": ObjectId(role_id)})
        await db.apis.delete_one({"_id": ObjectId(api_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
