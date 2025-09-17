import pytest
from fastapi.testclient import TestClient
from main import create_app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings  

def print_response_details(response):
    """Helper function to print response details if status is not 200."""
    if response.status_code != 200:
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")


@pytest.mark.asyncio
async def test_create_ad():
    app = create_app(test_settings)
    client = TestClient(app)

    async with get_db_client(test_settings) as db:
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
        login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        # Set the Authorization header
        headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
        }

        payload = {"user": {"id": 1000, "username": "duck"},
                   "designation": "newtitle", 
                   "description": "vinyl", 
                   "category": "musique",
                   "images": ["00_image_1234.jpg", "01_image_456.jpg"], 
                   "created_at": "2023-10-01T00:00:00Z",
                   }

        response = client.post("/api/internal/mongodb/entity/ad", json=payload, headers=headers)
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
        await db.ads.delete_one({"_id": ObjectId(data["ad_id"])})
        await db.users.delete_one({"_id": ObjectId(user_id)})

@pytest.mark.asyncio
async def test_get_ad():
    app = create_app(test_settings)
    client = TestClient(app)

    async with get_db_client(test_settings) as db:
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
        login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        # Set the Authorization header
        headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
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
    app = create_app(test_settings)
    client = TestClient(app)

    async with get_db_client(test_settings) as db:
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
        login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        # Set the Authorization header
        headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
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
            "created_by": user_id
        }

        await db.ads.insert_one(payload)

        payload_updated = {
            "user": {"id": 1000, "username": "duckyduck"},
            "designation": "newalbum", 
            "description": "cd", 
            "category": "musique_cd",
            "images": ["10_image_1234.jpg", "11_image_456.jpg"], 
            "created_at": "2024-10-01T00:00:00Z",
            }
        
        response = client.put(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", json=payload_updated, headers=headers)
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
    app = create_app(test_settings)
    client = TestClient(app)

    async with get_db_client(test_settings) as db:
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
        login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        # Set the Authorization header
        headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
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
