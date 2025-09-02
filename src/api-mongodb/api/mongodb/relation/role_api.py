from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleApi(BaseModel):
    role_id: str
    api_id: str
    permissions: dict

class RoleApiResponse(BaseModel):
    relation_id: str
    role_id: str
    api_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_api", response_model=RoleApiResponse)
async def create_role_api(role_api: RoleApi, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_api_dict = role_api.model_dump()
        role_api_dict["created_at"] = datetime.now(UTC).isoformat()
        role_api_dict["created_by"] = current_user["user_id"]
        result = await db.role_apis.insert_one(role_api_dict)
        role_api_dict["relation_id"] = str(result.inserted_id)
        return RoleApiResponse(**role_api_dict)

@router.get("/api/internal/mongodb/relation/role_api/{relation_id}", response_model=RoleApiResponse)
async def get_role_api(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_api = await db.role_apis.find_one({"_id": ObjectId(relation_id)})
        if role_api:
            role_api["relation_id"] = str(role_api["_id"])
            return RoleApiResponse(**role_api)
        raise HTTPException(status_code=404, detail="Role-Api relation not found")

@router.put("/api/internal/mongodb/relation/role_api/{relation_id}", response_model=RoleApiResponse)
async def update_role_api(relation_id: str, role_api: RoleApi, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_api_dict = role_api.model_dump()
        result = await db.role_apis.update_one({"_id": ObjectId(relation_id)}, {"$set": role_api_dict})
        if result.modified_count == 1:
            role_api = await db.role_apis.find_one({"_id": ObjectId(relation_id)})
            role_api["relation_id"] = str(role_api["_id"])
            return RoleApiResponse(**role_api)
        raise HTTPException(status_code=404, detail="Role-Api relation not found")

@router.delete("/api/internal/mongodb/relation/role_api/{relation_id}", response_model=dict)
async def delete_role_api(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_apis.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Api relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Api relation not found")
