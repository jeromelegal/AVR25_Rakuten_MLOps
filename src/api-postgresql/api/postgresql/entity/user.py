from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import Optional
from datetime import datetime, timezone, timedelta, UTC
from config.settings import Settings
from api.auth import get_current_user, hash_password, create_access_token
import asyncpg
from typing import Dict

router = APIRouter()

class User(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    created_at: datetime
    created_by: int

@router.post("/api/internal/postgresql/entity/user", response_model=UserResponse)
async def create_user(request: Request, user: User):
    settings: Settings = request.app.state.settings
    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_dict["password"])
    user_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    user_dict["created_by"] = 0  # Assuming the system creates the user

    async with get_db_client(settings) as conn:
        user_id = await conn.fetchval(
            "INSERT INTO users (username, email, password, created_at, created_by) VALUES ($1, $2, $3, $4, $5) RETURNING id",
            user_dict["username"],
            user_dict["email"],
            user_dict["password"],
            user_dict["created_at"],
            user_dict["created_by"]
        )
        user_dict["user_id"] = str(user_id)
        return UserResponse(**user_dict)

@router.get("/api/internal/postgresql/entity/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO : manage role
    # if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        user = await conn.fetchrow(
            "SELECT id as user_id, username, email, created_at, created_by FROM users WHERE id = $1",
            int(user_id)
        )
        if user:
            return UserResponse(**user)
        raise HTTPException(status_code=404, detail="User not found")

@router.put("/api/internal/postgresql/entity/user/{user_id}", response_model=Dict)
async def update_user(user_id: int, user: User, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    user_dict = user.model_dump()
    async with get_db_client(settings) as conn:
        await conn.execute(
            "UPDATE users SET username = $1, email = $2, password = $3 WHERE id = $4",
            user_dict["username"],
            user_dict["email"],
            user_dict["password"],
            user_id
        )
        updated_user = await conn.fetchrow(
            "SELECT id as user_id, username, email, created_at, created_by "
            "FROM users WHERE id = $1",
            user_id
        )
        if updated_user:
            # Create a new access token for the updated user
            data = {"user_id": str(updated_user["user_id"]), "sub": updated_user["username"], 'scope': 'internal'}
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data=data, settings=settings, expires_delta=access_token_expires
            )
            # Include the access token in the response
            return {
                "user_id": updated_user["user_id"],
                "username": updated_user["username"],
                "email": updated_user["email"],
                "access_token": access_token,
                "token_type": "bearer"
            }
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/api/internal/postgresql/entity/user/{user_id}", response_model=dict)
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM users WHERE id = $1",
            int(user_id)
        )
        if result == "DELETE 1":
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")
