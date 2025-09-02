from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleIndex(BaseModel):
    role_id: str
    index_id: str
    permissions: dict

class RoleIndexResponse(BaseModel):
    relation_id: str
    role_id: str
    index_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_index", response_model=RoleIndexResponse)
async def create_role_index(role_index: RoleIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_index_dict = role_index.model_dump()
        role_index_dict["created_at"] = datetime.now(UTC).isoformat()
        role_index_dict["created_by"] = current_user["user_id"]
        result = await db.role_indexes.insert_one(role_index_dict)
        role_index_dict["relation_id"] = str(result.inserted_id)
        return RoleIndexResponse(**role_index_dict)

@router.get("/api/internal/mongodb/relation/role_index/{relation_id}", response_model=RoleIndexResponse)
async def get_role_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_index = await db.role_indexes.find_one({"_id": ObjectId(relation_id)})
        if role_index:
            role_index["relation_id"] = str(role_index["_id"])
            return RoleIndexResponse(**role_index)
        raise HTTPException(status_code=404, detail="Role-Index relation not found")

@router.put("/api/internal/mongodb/relation/role_index/{relation_id}", response_model=RoleIndexResponse)
async def update_role_index(relation_id: str, role_index: RoleIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_index_dict = role_index.model_dump()
        result = await db.role_indexes.update_one({"_id": ObjectId(relation_id)}, {"$set": role_index_dict})
        if result.modified_count == 1:
            role_index = await db.role_indexes.find_one({"_id": ObjectId(relation_id)})
            role_index["relation_id"] = str(role_index["_id"])
            return RoleIndexResponse(**role_index)
        raise HTTPException(status_code=404, detail="Role-Index relation not found")

@router.delete("/api/internal/mongodb/relation/role_index/{relation_id}", response_model=dict)
async def delete_role_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_indexes.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Index relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Index relation not found")
