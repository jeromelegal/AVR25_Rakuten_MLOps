import pytest
from fastapi.testclient import TestClient
from main import create_app
from config.db import get_db_client
from api.auth import create_internal_api_access_token, hash_password
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

    # Setup: create a user and get token
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    hashed_password = hash_password("password")
    async with get_db_client(test_settings) as db:
        # Insert a test user with created_by set to a dummy value
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Assuming 0 as a dummy value for created_by
        )

        # Get token for the user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers["Authorization"] = f"Bearer {token}"

        # Test create ad
        ad_payload = {
            "designation": "Vinyl GRIMA",
            "description": "Album 'The Nightside'"
            }
        create_response = client.post(
            "/api/internal/postgresql/entity/ad",
            json=ad_payload,
            headers=headers
        )
        print_response_details(create_response)
        assert create_response.status_code == 200
        ad_data = create_response.json()
        assert ad_data["designation"] == "Vinyl GRIMA"
        assert ad_data["description"] == "Album 'The Nightside'"
        ad_id = ad_data["ad_id"]

        # Cleanup
        await db.execute("DELETE FROM ads WHERE id = $1", ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_get_ad():
    app = create_app(test_settings)
    client = TestClient(app)

    # Setup: create a user and get token
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    hashed_password = hash_password("password")
    async with get_db_client(test_settings) as db:
        # Insert a test user with created_by set to a dummy value
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Assuming 0 as a dummy value for created_by
        )

        # Get token for the user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers["Authorization"] = f"Bearer {token}"

        # Pre-insert a ad for the GET test
        ad_id = await db.fetchval(
            "INSERT INTO ads (designation, description, create_at, create_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testdesign", "testdesc", "2023-10-01T00:00:00Z", user_id
        )

        # Test get ad
        response = client.get(
            f"/api/internal/postgresql/entity/ad/{ad_id}",
            headers=headers
        )
        print_response_details(response)
        assert response.status_code == 200
        ad_data = response.json()
        assert ad_data["designation"] == "testdesign"
        assert ad_data["description"] == "testdesc"
        assert ad_data["created_at"] == "2023-10-01T00:00:00Z"
        assert ad_data["ad_id"] == ad_id

        # Cleanup
        await db.execute("DELETE FROM ads WHERE id = $1", ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_update_ad():
    app = create_app(test_settings)
    client = TestClient(app)

    # Setup: create a user and get token
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    hashed_password = hash_password("password")
    async with get_db_client(test_settings) as db:
        # Insert a test user with created_by set to a dummy value
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Assuming 0 as a dummy value for created_by
        )

        # Get token for the user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers["Authorization"] = f"Bearer {token}"

        # Pre-insert a ad for the UPDATE test
        ad_id = await db.fetchval(
            "INSERT INTO ads (designation, description, create_at, create_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testdesign", "testdesc", "2023-10-01T00:00:00Z", user_id
        )

        # Test update ad
        update_payload = {"designation": "updated_testad"}
        update_response = client.put(
            f"/api/internal/postgresql/entity/ad/{ad_id}",
            json=update_payload,
            headers=headers
        )
        print_response_details(update_response)
        assert update_response.status_code == 200
        ad_data = update_response.json()
        assert ad_data["designation"] == "updated_testad"

        # Cleanup
        await db.execute("DELETE FROM ads WHERE id = $1", ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_delete_ad():
    app = create_app(test_settings)
    client = TestClient(app)

    # Setup: create a user and get token
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    hashed_password = hash_password("password")
    async with get_db_client(test_settings) as db:
        # Insert a test user with created_by set to a dummy value
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Assuming 0 as a dummy value for created_by
        )

        # Get token for the user
        login_response = client.post(
            "/token", data={"username": "testuser", "password": "password"}
        )
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers["Authorization"] = f"Bearer {token}"

        # Pre-insert a ad for the DELETE test
        ad_id = await db.fetchval(
            "INSERT INTO ads (designation, description, create_at, create_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testdesign", "testdesc", "2023-10-01T00:00:00Z", user_id
        )

        # Test delete ad
        delete_response = client.delete(
            f"/api/internal/postgresql/entity/ad/{ad_id}",
            headers=headers
        )
        print_response_details(delete_response)
        assert delete_response.status_code == 200
        assert delete_response.json() == {"message": "Ad deleted successfully"}

        # Verify ad deletion
        deleted_ad_in_db = await db.fetchrow("SELECT * FROM ads WHERE id = $1", ad_id)
        assert deleted_ad_in_db is None, "Ad was not deleted from the database"

        # Cleanup
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
