import pytest
from fastapi.testclient import TestClient
from api.postgresql.relation.ads_images import router as ads_images_router
from main import create_app
from config.db import get_db_client
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings
from datetime import datetime, timezone

@pytest.fixture(scope="function")
def test_app():
    app = create_app(test_settings)  # Passez test_settings à create_app
    app.include_router(ads_images_router)
    yield TestClient(app)

def print_response_details(response):
    """Helper function to print response details if status is not 200."""
    if response.status_code != 200:
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

@pytest.mark.asyncio
async def test_flow_ad_image(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user, ad and image for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )
        test_date = datetime.now(timezone.utc).replace(tzinfo=None)
        ad_id = await db.fetchval(
            "INSERT INTO ads (designation, description, created_at, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "test", "testdescription", test_date, 0
        )
        image_id = await db.fetchval(
            "INSERT INTO images (image_name, bucket_name, created_at, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "00_image_test.jpg", "bucket-test", test_date, 0
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
        new_ad_image = {
            "ad_id": ad_id,
            "image_id": image_id
        }
        response = test_app.post("/api/internal/postgresql/relation/ads_images", json=new_ad_image, headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["ad_id"] == new_ad_image["ad_id"]
        assert response.json()["image_id"] == new_ad_image["image_id"]

        # Test get ad_image relation
        response = test_app.get(f"/api/internal/postgresql/relation/ads_images?image_id={image_id}&ad_id={ad_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()[0]["image_id"] == image_id
        assert response.json()[0]["ad_id"] == ad_id

        # Test delete ad_image relation
        response = test_app.delete(f"/api/internal/postgresql/relation/ads_images?image_id={image_id}&ad_id={ad_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["message"] == "Ad-Image relation deleted successfully"

        # Cleanup
        await db.execute("DELETE FROM ads_images WHERE image_id = $1 AND ad_id = $2", image_id, ad_id)
        await db.execute("DELETE FROM ads WHERE id = $1", ad_id)
        await db.execute("DELETE FROM images WHERE id = $1", image_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)