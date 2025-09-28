import pytest
from fastapi.testclient import TestClient
from main import create_app
from motor.motor_asyncio import AsyncIOMotorClient
from config.db import get_db_client
from bson import ObjectId
from api.auth import create_internal_api_access_token
from test.config.test_settings import test_settings
from datetime import datetime, UTC, timedelta

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
    date_now = datetime.now(UTC).isoformat()
    create_payload = {
        "ad_id": 50,
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
        "created_at": date_now,
    }

    response = client.post("/api/internal/mongodb/entity/ad", json=create_payload, headers=headers)
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    print("\n"*20)
    print(data)
    print("\n"*20)
    id = data["id"]
   
    # Basic field checks
    # assert data["ad_id"] == 50
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
    assert "created_at" in data

    # --- READ ---
    response = client.get(f"/api/internal/mongodb/entity/ad/{id}", headers=headers)
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    assert data["ad_id"] == 50
    assert data["user"]["id"] == 1000
    assert data["user"]["username"] == "duck"
    assert data["designation"] == "newtitle"
    assert data["description"] == "vinyl"
    assert data["category"] == "musique"
    assert isinstance(data["images"], list)
    assert {k for k in data["images"][0].keys()} == {"image_uuid", "bucket_path"}
    assert "created_at" in data

    # --- UPDATE ---
    update_payload = {
        "ad_id": 100,
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
        f"/api/internal/mongodb/entity/ad/{str(id)}",
        json=update_payload,
        headers=headers,
    )
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    assert data["ad_id"] == 100
    assert data["user"]["id"] == 1000
    assert data["user"]["username"] == "duckyduck"
    assert data["designation"] == "newalbum"
    assert data["description"] == "cd"
    assert data["category"] == "musique_cd"
    assert isinstance(data["images"], list) and len(data["images"]) == 2
    assert data["images"][0]["image_uuid"].startswith("10")
    assert data["images"][1]["image_uuid"].startswith("11")
    assert "created_at" in data

    # --- DELETE ---
    response = client.delete(f"/api/internal/mongodb/entity/ad/{id}", headers=headers)
    print_response_details(response)
    assert response.status_code == 200
    assert response.json() == {"message": "Ad deleted successfully"}

    # Verify deletion in DB
    async with get_db_client(test_settings) as db:
        assert await db.ads.find_one({"_id": ObjectId(id)}) is None

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
        
def _make_client_and_headers():
    app = create_app(test_settings)
    client = TestClient(app)

    internal = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers_internal = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": internal,
    }

    # create user + login
    r = client.post(
        "/api/internal/mongodb/entity/user",
        json={"username": "ad_search_user", "email": "ad_search_user@example.com", "password": "searchpwd"},
        headers=headers_internal,
    )
    assert r.status_code == 200, r.text
    user_id = r.json()["user_id"]

    r = client.post("/token", data={"username": "ad_search_user", "password": "searchpwd"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]

    internal = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": internal,
    }
    return client, headers, user_id


@pytest.mark.asyncio
async def test_ad_search():
    client, headers, user_id = _make_client_and_headers()

    # Clean collection - ONLY FOR FIRST TEST
    async with get_db_client(test_settings) as db:
        await db.ads.delete_many({})

    t0 = datetime.now(UTC)
    ads = [
        {
            "ad_id": 9001,
            "user": {"id": 1, "username": "u"},
            "designation": "Vinyle 1",
            "description": "musique",
            "category": "musique",
            "images": [],
            "created_at": (t0 - timedelta(minutes=2)).isoformat(),
        },
        {
            "ad_id": 9002,
            "user": {"id": 1, "username": "u"},
            "designation": "Lecteur CD",
            "description": "electronique",
            "category": "electronique",
            "images": [],
            "created_at": (t0 - timedelta(minutes=1)).isoformat(),
        },
        {
            "ad_id": 9003,
            "user": {"id": 1, "username": "u"},
            "designation": "Vinyle 2",
            "description": "musique",
            "category": "musique",
            "images": [],
            "created_at": t0.isoformat(),
        },
    ]
    created_ids = []
    for payload in ads:
        r = client.post("/api/internal/mongodb/entity/ad", json=payload, headers=headers)
        assert r.status_code == 200, r.text
        created_ids.append(r.json()["id"])

    # 1) /search sans q
    r = client.get("/api/internal/mongodb/entity/ad/search", headers=headers)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    ids = [it["ad_id"] for it in items[:3]]
    assert ids == [9003, 9002, 9001]

    # 2) filtre category
    r = client.get("/api/internal/mongodb/entity/ad/search", params={"category": "electronique"}, headers=headers)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert all(it["category"] == "electronique" for it in items)
    assert any(it["ad_id"] == 9002 for it in items)

    # 3) pagination
    r = client.get("/api/internal/mongodb/entity/ad/search", params={"skip": 1, "limit": 1}, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["skip"] == 1 and data["limit"] == 1
    assert len(data["items"]) == 1

    # Cleanup
    for _id in created_ids:
        client.delete(f"/api/internal/mongodb/entity/ad/{_id}", headers=headers)
    client.delete(f"/api/internal/mongodb/entity/user/{user_id}", headers=headers)