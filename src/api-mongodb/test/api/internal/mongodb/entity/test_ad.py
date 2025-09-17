import pytest
from fastapi.testclient import TestClient
from main import create_app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import create_internal_api_access_token
from test.config.test_settings import test_settings

def print_response_details(response):
    """Helper function to print response details if status is not 200."""
    if response.status_code != 200:
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

@pytest.mark.asyncio
async def test_ad_flow():
    # Setup the app with test settings
    app = create_app(test_settings)
    client = TestClient(app)

    # Step 1: Create a new user
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }
    response = client.post(
        "/api/internal/mongodb/entity/user",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpassword",
        },
        headers=headers,
    )
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    user_id = data["user_id"]  # Get the user_id from the response

    login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    # Test create_ad
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
    assert data["images"] == ["00_image_1234.jpg", "01_image_456.jpg"]
    assert "ad_id" in data 
    assert "created_at" in data
    ad_id = data["ad_id"]

    # Test get_ad
    response = client.get(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == 1000
    assert data["user"]["username"] == "duck"
    assert data["designation"] == "newtitle"
    assert data["description"] == "vinyl"
    assert data["category"] == "musique"
    assert data["images"] == ["00_image_1234.jpg", "01_image_456.jpg"]
    assert "ad_id" in data 
    assert "created_at" in data

    # Test update_ad
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
    assert data["images"] == ["10_image_1234.jpg", "11_image_456.jpg"]
    assert "ad_id" in data 
    assert "created_at" in data

    # Test deletion
    response = client.delete(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Ad deleted successfully"}

    # Verify deletion
    async with get_db_client(test_settings) as db:
        assert await db.ads.find_one({"_id": ad_id}) is None

    # Delete the user
    delete_response = client.delete(
        f"/api/internal/mongodb/entity/user/{user_id}", headers=headers
    )
    print_response_details(delete_response)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "User deleted successfully"}

    # Verify user was deleted from the database
    async with get_db_client(test_settings) as db:
        deleted_user_in_db = await db.users.find_one({"_id": ObjectId(user_id)})
        assert deleted_user_in_db is None, "User was not deleted from the database"