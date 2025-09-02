from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleSpace(BaseModel):
    role_id: str
    space_id: str
    permissions: dict

class RoleSpaceResponse(BaseModel):
    relation_id: str
    role_id: str
    space_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_space", response_model=RoleSpaceResponse)
async def create_role_space(role_space: RoleSpace, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_space_dict = role_space.model_dump()
        role_space_dict["created_at"] = datetime.now(UTC).isoformat()
        role_space_dict["created_by"] = current_user["user_id"]
        result = await db.role_spaces.insert_one(role_space_dict)
        role_space_dict["relation_id"] = str(result.inserted_id)
        return RoleSpaceResponse(**role_space_dict)

@router.get("/api/internal/mongodb/relation/role_space/{relation_id}", response_model=RoleSpaceResponse)
async def get_role_space(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_space = await db.role_spaces.find_one({"_id": ObjectId(relation_id)})
        if role_space:
            role_space["relation_id"] = str(role_space["_id"])
            return RoleSpaceResponse(**role_space)
        raise HTTPException(status_code=404, detail="Role-Space relation not found")

@router.put("/api/internal/mongodb/relation/role_space/{relation_id}", response_model=RoleSpaceResponse)
async def update_role_space(relation_id: str, role_space: RoleSpace, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_space_dict = role_space.model_dump()
        result = await db.role_spaces.update_one({"_id": ObjectId(relation_id)}, {"$set": role_space_dict})
        if result.modified_count == 1:
            role_space = await db.role_spaces.find_one({"_id": ObjectId(relation_id)})
            role_space["relation_id"] = str(role_space["_id"])
            return RoleSpaceResponse(**role_space)
        raise HTTPException(status_code=404, detail="Role-Space relation not found")

@router.delete("/api/internal/mongodb/relation/role_space/{relation_id}", response_model=dict)
async def delete_role_space(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_spaces.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Space relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Space relation not found")
