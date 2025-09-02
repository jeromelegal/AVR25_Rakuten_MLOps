from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user, hash_password
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class User(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/user", response_model=UserResponse)
async def create_user(user: User):
    async with get_db_client() as db:
        user_dict = user.model_dump()
        user_dict["password"] = hash_password(user_dict["password"])  # Hash the password before storing
        user_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        user_dict["created_by"] = "system"  # Assuming the system creates the user
        result = await db.users.insert_one(user_dict)
        user_dict["user_id"] = str(result.inserted_id)
        return UserResponse(**user_dict)

@router.get("/api/internal/mongodb/entity/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["user_id"] = str(user["_id"])
            return UserResponse(**user)
        raise HTTPException(status_code=404, detail="User not found")

@router.put("/api/internal/mongodb/entity/user/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: User, current_user: dict = Depends(get_current_user)):
    if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        user_dict = user.model_dump()
        user_dict["password"] = hash_password(user_dict["password"])  # Hash the password before storing
        result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})
        if result.modified_count == 1:
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            user["user_id"] = str(user["_id"])
            return UserResponse(**user)
        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/api/internal/mongodb/entity/user/{user_id}", response_model=dict)
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        result = await db.users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 1:
            # Invalidate the user's JWT token
            # This can be done by removing the token from a blacklist or setting an expiration date
            # For simplicity, we'll assume tokens are short-lived and do not implement a blacklist here
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")
