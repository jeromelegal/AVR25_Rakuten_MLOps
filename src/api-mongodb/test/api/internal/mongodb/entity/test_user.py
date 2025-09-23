import pytest
from fastapi.testclient import TestClient
from main import create_app
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
async def test_user_flow():
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

    # Verify user exists in the database
    async with get_db_client(test_settings) as db:
        user_in_db = await db.users.find_one({"_id": ObjectId(user_id)})
        assert user_in_db is not None, "User was not created in the database"
        assert user_in_db["username"] == "testuser"
        assert user_in_db["email"] == "testuser@example.com"

    # Step 2: Get the access token for the created user
    login_response = client.post(
        "/token", data={"username": "testuser", "password": "testpassword"}
    )
    print_response_details(login_response)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Prepare headers with the access token
    api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
        "X-API-Key": api_token,
    }

    # Step 3: Retrieve the user details
    response = client.get(
        f"/api/internal/mongodb/entity/user/{user_id}", headers=headers
    )
    print_response_details(response)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"

    # Step 4: Update the user details
    update_response = client.put(
        f"/api/internal/mongodb/entity/user/{user_id}",
        json={
            "username": "updateduser",
            "email": "updateduser@example.com",
            "password": "newpassword",
        },
        headers=headers,
    )
    print_response_details(update_response)
    assert update_response.status_code == 200
    updated_data = update_response.json()

    # Verify user was updated in the database
    assert updated_data["username"] == "updateduser"
    assert updated_data["email"] == "updateduser@example.com"
    new_token = updated_data["access_token"]  # Retrieve the new token from the response

    async with get_db_client(test_settings) as db:
        updated_user_in_db = await db.users.find_one({"_id": ObjectId(user_id)})
        assert updated_user_in_db is not None, "User was not found in the database after update"
        assert updated_user_in_db["username"] == "updateduser"
        assert updated_user_in_db["email"] == "updateduser@example.com"

    # Update headers with the new access token
    headers["Authorization"] = f"Bearer {new_token}"

    # Step 5: Delete the user
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