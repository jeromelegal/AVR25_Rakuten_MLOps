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
async def test_create_page_widget():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a widget
        widget_id = str(ObjectId())
        await db.widgets.insert_one({"_id": ObjectId(widget_id), "name": "testwidget", "type": "graphique", "configuration": {"data": "mean"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.post("/api/internal/mongodb/relation/page_widget", json={"page_id": page_id, "widget_id": widget_id, "position": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page_id"] == page_id
        assert data["widget_id"] == widget_id
        assert data["position"] == 1
        assert "relation_id" in data
        assert "created_at" in data

        # Clean up
        await db.page_widget.delete_one({"_id": ObjectId(data["relation_id"])})
        await db.pages.delete_one({"_id": ObjectId(page_id)})
        await db.widgets.delete_one({"_id": ObjectId(widget_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_page_widget():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a widget
        widget_id = str(ObjectId())
        await db.widgets.insert_one({"_id": ObjectId(widget_id), "name": "testwidget", "type": "graphique", "configuration": {"data": "mean"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a page-widget relation
        relation_id = str(ObjectId())
        await db.page_widget.insert_one({"_id": ObjectId(relation_id), "page_id": page_id, "widget_id": widget_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.get(f"/api/internal/mongodb/relation/page_widget/{relation_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page_id"] == page_id
        assert data["widget_id"] == widget_id
        assert data["position"] == 1

        # Clean up
        await db.page_widget.delete_one({"_id": ObjectId(relation_id)})
        await db.pages.delete_one({"_id": ObjectId(page_id)})
        await db.widgets.delete_one({"_id": ObjectId(widget_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_update_page_widget():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a widget
        widget_id = str(ObjectId())
        await db.widgets.insert_one({"_id": ObjectId(widget_id), "name": "testwidget", "type": "graphique", "configuration": {"data": "mean"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a page-widget relation
        relation_id = str(ObjectId())
        await db.page_widget.insert_one({"_id": ObjectId(relation_id), "page_id": page_id, "widget_id": widget_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.put(f"/api/internal/mongodb/relation/page_widget/{relation_id}", json={"page_id": page_id, "widget_id": widget_id, "position": 2}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page_id"] == page_id
        assert data["widget_id"] == widget_id
        assert data["position"] == 2

        # Clean up
        await db.page_widget.delete_one({"_id": ObjectId(relation_id)})
        await db.pages.delete_one({"_id": ObjectId(page_id)})
        await db.widgets.delete_one({"_id": ObjectId(widget_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_delete_page_widget():
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

        # Create a page
        page_id = str(ObjectId())
        await db.pages.insert_one({"_id": ObjectId(page_id), "name": "testpage", "content": "Test page content", "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a widget
        widget_id = str(ObjectId())
        await db.widgets.insert_one({"_id": ObjectId(widget_id), "name": "testwidget", "type": "graphique", "configuration": {"data": "mean"}, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        # Create a page-widget relation
        relation_id = str(ObjectId())
        await db.page_widget.insert_one({"_id": ObjectId(relation_id), "page_id": page_id, "widget_id": widget_id, "position": 1, "created_at": "2023-10-01T00:00:00Z", "created_by": user_id})

        response = client.delete(f"/api/internal/mongodb/relation/page_widget/{relation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"message": "Page-Widget relation deleted successfully"}

        # Verify deletion
        relation = await db.page_widget.find_one({"_id": ObjectId(relation_id)})
        assert relation is None

        # Clean up
        await db.pages.delete_one({"_id": ObjectId(page_id)})
        await db.widgets.delete_one({"_id": ObjectId(widget_id)})
        await db.users.delete_one({"_id": ObjectId(user_id)})
