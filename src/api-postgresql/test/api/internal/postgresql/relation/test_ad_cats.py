import pytest
from fastapi.testclient import TestClient
from api.postgresql.relation.ad_cats import router as ad_cat_router
from main import create_app
from config.db import get_db_client
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings

@pytest.fixture(scope="function")
def test_app():
    app = create_app(test_settings)  # Passez test_settings à create_app
    app.include_router(ad_cat_router)
    yield TestClient(app)

def print_response_details(response):
    """Helper function to print response details if status is not 200."""
    if response.status_code != 200:
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

@pytest.mark.asyncio
async def test_create_ad_cat(test_app):
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

        # Test create ad_cat relation
        ad_id = 01234
        cat_id = 56789

        new_ad_cat = {
            "ad_id": ad_id,
            "cat_id": cat_id
        }
        response = test_app.post("/api/internal/postgresql/relation/ad_cat", json=new_ad_cat, headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["ad_id"] == new_ad_cat["ad_id"]
        assert response.json()["cat_id"] == new_ad_cat["cat_id"]

        # Cleanup
        await db.execute("DELETE FROM ad_cats WHERE cat_id = $1 AND ad_id = $2", cat_id, ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_get_ad_cat(test_app):
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

        # Create a ad_cat relation to retrieve
        ad_id = 01234
        cat_id = 56789

        test_app.post("/api/internal/postgresql/relation/ad_cat", json={
            "ad_id": ad_id,
            "cat_id": cat_id
        }, headers=headers)

        # Test get ad_cat relation
        response = test_app.get(f"/api/internal/postgresql/relation/ad_cat?cat_id={cat_id}&ad_id={ad_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()[0]["cat_id"] == cat_id
        assert response.json()[0]["ad_id"] == ad_id

        # Cleanup
        await db.execute("DELETE FROM ad_cats WHERE cat_id = $1 AND ad_id = $2", cat_id, ad_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_delete_ad_cat(test_app):
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
        # Create a ad_cat relation to delete
        ad_id = 01234
        cat_id = 56789

        test_app.post("/api/internal/postgresql/relation/ad_cat", json={
            "ad_id": ad_id,
            "cat_id": cat_id
        }, headers=headers)

        # Test delete ad_cat relation
        response = test_app.delete(f"/api/internal/postgresql/relation/ad_cat?cat_id={cat_id}&ad_id={ad_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["message"] == "Ad-Cat relation deleted successfully"

        # Cleanup
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
