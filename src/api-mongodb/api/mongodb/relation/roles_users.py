from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleUser(BaseModel):
    role_id: str
    user_id: str
    permissions: dict

class RoleUserResponse(BaseModel):
    relation_id: str
    role_id: str
    user_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_user", response_model=RoleUserResponse)
async def create_role_user(role_user: RoleUser, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_user_dict = role_user.model_dump()
        role_user_dict["created_at"] = datetime.now(UTC).isoformat()
        role_user_dict["created_by"] = current_user["user_id"]
        result = await db.role_users.insert_one(role_user_dict)
        role_user_dict["relation_id"] = str(result.inserted_id)
        return RoleUserResponse(**role_user_dict)

@router.get("/api/internal/mongodb/relation/role_user/{relation_id}", response_model=RoleUserResponse)
async def get_role_user(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_user = await db.role_users.find_one({"_id": ObjectId(relation_id)})
        if role_user:
            role_user["relation_id"] = str(role_user["_id"])
            return RoleUserResponse(**role_user)
        raise HTTPException(status_code=404, detail="Role-User relation not found")

@router.put("/api/internal/mongodb/relation/role_user/{relation_id}", response_model=RoleUserResponse)
async def update_role_user(relation_id: str, role_user: RoleUser, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_user_dict = role_user.model_dump()
        result = await db.role_users.update_one({"_id": ObjectId(relation_id)}, {"$set": role_user_dict})
        if result.modified_count == 1:
            role_user = await db.role_users.find_one({"_id": ObjectId(relation_id)})
            role_user["relation_id"] = str(role_user["_id"])
            return RoleUserResponse(**role_user)
        raise HTTPException(status_code=404, detail="Role-User relation not found")

@router.delete("/api/internal/mongodb/relation/role_user/{relation_id}", response_model=dict)
async def delete_role_user(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_users.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-User relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-User relation not found")
