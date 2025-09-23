import pytest
from fastapi.testclient import TestClient
from api.postgresql.relation.roles_users import router as role_user_router
from main import create_app
from config.db import get_db_client
from api.auth import hash_password, create_internal_api_access_token
from test.config.test_settings import test_settings

@pytest.fixture(scope="function")
def test_app():
    app = create_app(test_settings)  # Passez test_settings à create_app
    app.include_router(role_user_router)
    yield TestClient(app)

def print_response_details(response):
    """Helper function to print response details if status is not 200."""
    if response.status_code != 200:
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")

@pytest.mark.asyncio
async def test_create_role_user(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user and a role for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )
        role_id = await db.fetchval(
            "INSERT INTO roles (name, created_by) VALUES ($1, $2) RETURNING id",
            "testrole", 0  # Placeholder for created_by
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

        # Test create role_user relation
        new_role_user = {
            "role_id": role_id,
            "user_id": user_id
        }
        response = test_app.post("/api/internal/postgresql/relation/role_user", json=new_role_user, headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["role_id"] == new_role_user["role_id"]
        assert response.json()["user_id"] == new_role_user["user_id"]

        # Cleanup
        await db.execute("DELETE FROM user_roles WHERE user_id = $1 AND role_id = $2", user_id, role_id)
        await db.execute("DELETE FROM roles WHERE id = $1", role_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_get_role_user(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user and a role for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )
        role_id = await db.fetchval(
            "INSERT INTO roles (name, created_by) VALUES ($1, $2) RETURNING id",
            "testrole", 0  # Placeholder for created_by
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

        # Create a role_user relation to retrieve
        test_app.post("/api/internal/postgresql/relation/role_user", json={
            "role_id": role_id,
            "user_id": user_id
        }, headers=headers)

        # Test get role_user relation
        response = test_app.get(f"/api/internal/postgresql/relation/role_user/{user_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()[0]["user_id"] == user_id
        assert response.json()[0]["role_id"] == role_id

        # Cleanup
        await db.execute("DELETE FROM user_roles WHERE user_id = $1 AND role_id = $2", user_id, role_id)
        await db.execute("DELETE FROM roles WHERE id = $1", role_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)

@pytest.mark.asyncio
async def test_delete_role_user(test_app):
    async with get_db_client(test_settings) as db:
        # Create a user and a role for testing
        hashed_password = hash_password("password")
        user_id = await db.fetchval(
            "INSERT INTO users (username, email, password, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            "testuser", "testuser@example.com", hashed_password, 0  # Placeholder for created_by
        )
        role_id = await db.fetchval(
            "INSERT INTO roles (name, created_by) VALUES ($1, $2) RETURNING id",
            "testrole", 0  # Placeholder for created_by
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
        # Create a role_user relation to delete
        test_app.post("/api/internal/postgresql/relation/role_user", json={
            "role_id": role_id,
            "user_id": user_id
        }, headers=headers)

        # Test delete role_user relation
        response = test_app.delete(f"/api/internal/postgresql/relation/role_user/{user_id}", headers=headers)
        print_response_details(response)
        assert response.status_code == 200
        assert response.json()["message"] == "Role-User relation deleted successfully"

        # Cleanup
        await db.execute("DELETE FROM roles WHERE id = $1", role_id)
        await db.execute("DELETE FROM users WHERE id = $1", user_id)
