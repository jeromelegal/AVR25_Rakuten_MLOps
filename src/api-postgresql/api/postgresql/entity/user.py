from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
import asyncpg
from api.auth import get_current_user, hash_password
from datetime import datetime, UTC, timezone  

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
async def create_user(user: User):
    async with get_db_client() as conn:
        user_dict = user.model_dump()
        user_dict["password"] = hash_password(user_dict["password"])  # Hash the password before storing
        user_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)  # Set the creation date
        user_dict["created_by"] = 0  # Assuming the system creates the user

        # Insert the user into the database
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
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        user = await conn.fetchrow(
            "SELECT id as user_id, username, email, created_at, created_by FROM users WHERE id = $1",
            int(user_id)
        )
        if user:
            return UserResponse(**user)
        raise HTTPException(status_code=404, detail="User not found")

@router.put("/api/internal/postgresql/entity/user/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: User, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        user_dict = user.model_dump()
        user_dict["password"] = hash_password(user_dict["password"])  # Hash the password before storing

        await conn.execute(
            "UPDATE users SET username = $1, email = $2, password = $3 WHERE id = $4",
            user_dict["username"],
            user_dict["email"],
            user_dict["password"],
            int(user_id)
        )

        user = await conn.fetchrow(
            "SELECT id as user_id, username, email, created_at, created_by FROM users WHERE id = $1",
            int(user_id)
        )
        if user:
            return UserResponse(**user)
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/api/internal/postgresql/entity/user/{user_id}", response_model=dict)
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        result = await conn.execute(
            "DELETE FROM users WHERE id = $1",
            int(user_id)
        )
        if result == "DELETE 1":
            # Invalidate the user's JWT token
            # This can be done by removing the token from a blacklist or setting an expiration date
            # For simplicity, we'll assume tokens are short-lived and do not implement a blacklist here
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")

