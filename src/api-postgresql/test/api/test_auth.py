import pytest
from fastapi.testclient import TestClient
from main import app
from config.db import get_db
import asyncpg
from api.auth import hash_password, create_internal_api_access_token
# from config.config import settings.API_GATEWAY_HOST, settings.PROTECTED_ENDPOINT_URL
from config.settings import settings 

from datetime import datetime


client = TestClient(app)

@pytest.mark.asyncio
async def test_login_for_access_token():
    db = await get_db()

    api_token = create_internal_api_access_token(data={"scope": "internal"})
    headers = {"Referer": settings.API_GATEWAY_HOST + settings.PROTECTED_ENDPOINT_URL, "X-API-Key": api_token}
    response = client.post("/api/internal/postgresql/entity/user", json={"username": "testuser", "email": "testuser@example.com", "password": "password"}, headers=headers)
    print( "response", response)
    
    data = response.json()
    print("data ", data)
    user_id = data["user_id"]

    response = client.post("/token", data={"username": "testuser", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    await db.execute("DELETE FROM users WHERE id = $1", user_id)
    # Supprimer l'utilisateur et le rôle après le test
    # await db.execute("DELETE FROM user_roles WHERE user_id = $1", user_id)
    # await db.execute("DELETE FROM roles WHERE id = $1", role_id)
    # await db.execute("DELETE FROM users WHERE id = $1", user_id)
