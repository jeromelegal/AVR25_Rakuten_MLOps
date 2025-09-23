import pytest
from fastapi.testclient import TestClient
from main import create_app
from config.db import get_db_client
from api.auth import create_internal_api_access_token
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

    # Step 1: Create a new ad
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }
    response = client.post(
        "/api/internal/postgresql/entity/user",
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

    # Step 2: Get the access token for the created user
    login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
    )
    print_response_details(login_response)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Prepare headers with the access token
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

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
    ad_id = ad_data["id"]

    # Test get ad
    response = client.get(
        f"/api/internal/postgresql/entity/ad/{ad_id}",
        headers=headers
    )
    print_response_details(response)
    assert response.status_code == 200
    ad_data = response.json()
    assert ad_data["designation"] == "Vinyl GRIMA"
    assert ad_data["description"] == "Album 'The Nightside'"

    # Test update ad
    update_payload = {
        "designation": "Vinyl Sleep Token",
        "description": "Album 'Sundowning'"
        }
    update_response = client.put(
        f"/api/internal/postgresql/entity/ad/{ad_id}",
        json=update_payload,
        headers=headers
    )
    print_response_details(update_response)
    assert update_response.status_code == 200
    update_data = update_response.json()
    assert update_data["designation"] == "Vinyl Sleep Token"
    assert update_data["description"] == "Album 'Sundowning'"

    # Test delete ad
    delete_response = client.delete(
        f"/api/internal/postgresql/entity/ad/{ad_id}",
        headers=headers
    )
    print_response_details(delete_response)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Ad deleted successfully"}

    # Verify ad deletion
    async with get_db_client(test_settings) as db:
        deleted_ad_in_db = await db.fetchrow("SELECT * FROM ads WHERE id = $1", ad_id)
        assert deleted_ad_in_db is None, "Ad was not deleted from the database"

        # Cleanup
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
