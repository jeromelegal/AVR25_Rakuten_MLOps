import pytest
from fastapi.testclient import TestClient
from api.postgresql.relation.ad_images import router as ad_image_router
from main import create_app
from config.db import get_db_client
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings

@pytest.fixture(scope="function")
def test_app():
    app = create_app(test_settings)  # Passez test_settings à create_app
    app.include_router(ad_image_router)
    yield TestClient(app)

def print_response_details(response):
    """Helper function to print response details if status is not 200."""
    if response.status_code != 200:
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

@pytest.mark.asyncio
async def test_create_ad_image(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user and a role for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )

        # Login and get token
        login_response = test_app.post("/token", data={"username": "testuser", "password": "password"})
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }

        # Test create ad_image relation
        ad_id = 01234
        image_id = 56789

        new_ad_image = {
            "ad_id": ad_id,
            "image_id": image_id
        }
        response = test_app.post("/api/internal/postgresql/relation/ad_image", json=new_ad_image, headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["ad_id"] == new_ad_image["ad_id"]
        assert response.json()["image_id"] == new_ad_image["image_id"]

        # Cleanup
        await db.execute("DELETE FROM ad_images WHERE image_id = $1 AND ad_id = $2", image_id, ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_get_ad_image(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user and a role for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )

        # Login and get token
        login_response = test_app.post("/token", data={"username": "testuser", "password": "password"})
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        # headers = {"Authorization": f"Bearer {token}"}
        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }        

        # Create a ad_image relation to retrieve
        ad_id = 01234
        image_id = 56789

        test_app.post("/api/internal/postgresql/relation/ad_image", json={
            "ad_id": ad_id,
            "image_id": image_id
        }, headers=headers)

        # Test get ad_image relation
        response = test_app.get(f"/api/internal/postgresql/relation/ad_image?image_id={image_id}&ad_id={ad_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()[0]["image_id"] == image_id
        assert response.json()[0]["ad_id"] == ad_id

        # Cleanup
        await db.execute("DELETE FROM ad_images WHERE image_id = $1 AND ad_id = $2", image_id, ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_delete_ad_image(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user and a role for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )

        # Login and get token
        login_response = test_app.post("/token", data={"username": "testuser", "password": "password"})
        print_response_details(login_response)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        # headers = {"Authorization": f"Bearer {token}"}
        api_token = create_internal_api_access_token(data={"scope": "internal"}, settings=test_settings)
        headers = {
            "Authorization": f"Bearer {token}",
            "Referer": test_settings.API_GATEWAY_HOST + test_settings.PROTECTED_ENDPOINT_URL,
            "X-API-Key": api_token,
        }
        # Create a ad_image relation to delete
        ad_id = 01234
        image_id = 56789

        test_app.post("/api/internal/postgresql/relation/ad_image", json={
            "ad_id": ad_id,
            "image_id": image_id
        }, headers=headers)

        # Test delete ad_image relation
        response = test_app.delete(f"/api/internal/postgresql/relation/ad_image?image_id={image_id}&ad_id={ad_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["message"] == "Ad-Image relation deleted successfully"

        # Cleanup
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
