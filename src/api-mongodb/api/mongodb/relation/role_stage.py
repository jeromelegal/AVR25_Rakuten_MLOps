from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleStage(BaseModel):
    role_id: str
    stage_id: str
    permissions: dict

class RoleStageResponse(BaseModel):
    relation_id: str
    role_id: str
    stage_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_stage", response_model=RoleStageResponse)
async def create_role_stage(role_stage: RoleStage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_stage_dict = role_stage.model_dump()
        role_stage_dict["created_at"] = datetime.now(UTC).isoformat()
        role_stage_dict["created_by"] = current_user["user_id"]
        result = await db.role_stages.insert_one(role_stage_dict)
        role_stage_dict["relation_id"] = str(result.inserted_id)
        return RoleStageResponse(**role_stage_dict)

@router.get("/api/internal/mongodb/relation/role_stage/{relation_id}", response_model=RoleStageResponse)
async def get_role_stage(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_stage = await db.role_stages.find_one({"_id": ObjectId(relation_id)})
        if role_stage:
            role_stage["relation_id"] = str(role_stage["_id"])
            return RoleStageResponse(**role_stage)
        raise HTTPException(status_code=404, detail="Role-Stage relation not found")

@router.put("/api/internal/mongodb/relation/role_stage/{relation_id}", response_model=RoleStageResponse)
async def update_role_stage(relation_id: str, role_stage: RoleStage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_stage_dict = role_stage.model_dump()
        result = await db.role_stages.update_one({"_id": ObjectId(relation_id)}, {"$set": role_stage_dict})
        if result.modified_count == 1:
            role_stage = await db.role_stages.find_one({"_id": ObjectId(relation_id)})
            role_stage["relation_id"] = str(role_stage["_id"])
            return RoleStageResponse(**role_stage)
        raise HTTPException(status_code=404, detail="Role-Stage relation not found")

@router.delete("/api/internal/mongodb/relation/role_stage/{relation_id}", response_model=dict)
async def delete_role_stage(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_stages.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Stage relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Stage relation not found")
