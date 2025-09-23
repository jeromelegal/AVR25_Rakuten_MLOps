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

    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers_internal = {
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
        headers=headers_internal,
    )
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    user_id = data["user_id"]

    login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    # --- CREATE ---
    create_payload = {
        "user": {"id": 1000, "username": "duck"},
        "designation": "newtitle",
        "description": "vinyl",
        "category": "musique",
        # New images hierarchy: array of objects {image_uuid, bucket_path}
        "images": [
            {
                "image_uuid": "8a7c5f2e-1b9f-4e8a-9a8b-2b4d6c0f1a23",
                "bucket_path": "raw-images/ads/8a7c5f2e.jpg",
            },
            {
                "image_uuid": "1b2c3d4e-5f60-47a8-9abc-def012345678",
                "bucket_path": "raw-images/ads/1b2c3d4e.jpg",
            },
        ],
        "created_at": "2023-10-01T00:00:00Z",
    }

    response = client.post("/api/internal/mongodb/entity/ad", json=create_payload, headers=headers)
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()

    # Basic field checks
    assert data["user"]["id"] == 1000
    assert data["user"]["username"] == "duck"
    assert data["designation"] == "newtitle"
    assert data["description"] == "vinyl"
    assert data["category"] == "musique"

    # Images structure & values
    assert isinstance(data["images"], list) and len(data["images"]) == 2
    assert {k for k in data["images"][0].keys()} == {"image_uuid", "bucket_path"}
    assert data["images"][0]["image_uuid"] == "8a7c5f2e-1b9f-4e8a-9a8b-2b4d6c0f1a23"
    assert data["images"][0]["bucket_path"] == "raw-images/ads/8a7c5f2e.jpg"

    assert "ad_id" in data
    assert "created_at" in data
    ad_id = data["ad_id"]

    # --- READ ---
    response = client.get(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == 1000
    assert data["user"]["username"] == "duck"
    assert data["designation"] == "newtitle"
    assert data["description"] == "vinyl"
    assert data["category"] == "musique"
    assert isinstance(data["images"], list)
    assert {k for k in data["images"][0].keys()} == {"image_uuid", "bucket_path"}
    assert "ad_id" in data
    assert "created_at" in data

    # --- UPDATE ---
    update_payload = {
        "user": {"id": 1000, "username": "duckyduck"},
        "designation": "newalbum",
        "description": "cd",
        "category": "musique_cd",
        "images": [
            {
                "image_uuid": "10a7c5f2e-1b9f-4e8a-9a8b-2b4d6c0f1a23",
                "bucket_path": "raw-images/ads/10a7c5f2e.jpg",
            },
            {
                "image_uuid": "11b2c3d4e-5f60-47a8-9abc-def012345678",
                "bucket_path": "raw-images/ads/11b2c3d4e.jpg",
            },
        ],
        "created_at": "2024-10-01T00:00:00Z",
    }

    response = client.put(
        f"/api/internal/mongodb/entity/ad/{str(ad_id)}",
        json=update_payload,
        headers=headers,
    )
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == 1000
    assert data["user"]["username"] == "duckyduck"
    assert data["designation"] == "newalbum"
    assert data["description"] == "cd"
    assert data["category"] == "musique_cd"
    assert isinstance(data["images"], list) and len(data["images"]) == 2
    assert data["images"][0]["image_uuid"].startswith("10")
    assert data["images"][1]["image_uuid"].startswith("11")
    assert "ad_id" in data
    assert "created_at" in data

    # --- DELETE ---
    response = client.delete(f"/api/internal/mongodb/entity/ad/{str(ad_id)}", headers=headers)
    print_response_details(response)
    assert response.status_code == 200
    assert response.json() == {"message": "Ad deleted successfully"}

    # Verify deletion in DB
    async with get_db_client(test_settings) as db:
        assert await db.ads.find_one({"_id": ObjectId(ad_id)}) is None

    # Cleanup: delete the user
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