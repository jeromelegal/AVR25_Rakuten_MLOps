from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleDirectory(BaseModel):
    role_id: str
    directory_id: str
    permissions: dict

class RoleDirectoryResponse(BaseModel):
    relation_id: str
    role_id: str
    directory_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_directory", response_model=RoleDirectoryResponse)
async def create_role_directory(role_directory: RoleDirectory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_directory_dict = role_directory.model_dump()
        role_directory_dict["created_at"] = datetime.now(UTC).isoformat()
        role_directory_dict["created_by"] = current_user["user_id"]
        result = await db.role_directories.insert_one(role_directory_dict)
        role_directory_dict["relation_id"] = str(result.inserted_id)
        return RoleDirectoryResponse(**role_directory_dict)

@router.get("/api/internal/mongodb/relation/role_directory/{relation_id}", response_model=RoleDirectoryResponse)
async def get_role_directory(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_directory = await db.role_directories.find_one({"_id": ObjectId(relation_id)})
        if role_directory:
            role_directory["relation_id"] = str(role_directory["_id"])
            return RoleDirectoryResponse(**role_directory)
        raise HTTPException(status_code=404, detail="Role-Directory relation not found")

@router.put("/api/internal/mongodb/relation/role_directory/{relation_id}", response_model=RoleDirectoryResponse)
async def update_role_directory(relation_id: str, role_directory: RoleDirectory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_directory_dict = role_directory.model_dump()
        result = await db.role_directories.update_one({"_id": ObjectId(relation_id)}, {"$set": role_directory_dict})
        if result.modified_count == 1:
            role_directory = await db.role_directories.find_one({"_id": ObjectId(relation_id)})
            role_directory["relation_id"] = str(role_directory["_id"])
            return RoleDirectoryResponse(**role_directory)
        raise HTTPException(status_code=404, detail="Role-Directory relation not found")

@router.delete("/api/internal/mongodb/relation/role_directory/{relation_id}", response_model=dict)
async def delete_role_directory(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_directories.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Directory relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Directory relation not found")
