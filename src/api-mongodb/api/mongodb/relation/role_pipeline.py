from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RolePipeline(BaseModel):
    role_id: str
    pipeline_id: str
    permissions: dict

class RolePipelineResponse(BaseModel):
    relation_id: str
    role_id: str
    pipeline_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_pipeline", response_model=RolePipelineResponse)
async def create_role_pipeline(role_pipeline: RolePipeline, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_pipeline_dict = role_pipeline.model_dump()
        role_pipeline_dict["created_at"] = datetime.now(UTC).isoformat()
        role_pipeline_dict["created_by"] = current_user["user_id"]
        result = await db.role_pipelines.insert_one(role_pipeline_dict)
        role_pipeline_dict["relation_id"] = str(result.inserted_id)
        return RolePipelineResponse(**role_pipeline_dict)

@router.get("/api/internal/mongodb/relation/role_pipeline/{relation_id}", response_model=RolePipelineResponse)
async def get_role_pipeline(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_pipeline = await db.role_pipelines.find_one({"_id": ObjectId(relation_id)})
        if role_pipeline:
            role_pipeline["relation_id"] = str(role_pipeline["_id"])
            return RolePipelineResponse(**role_pipeline)
        raise HTTPException(status_code=404, detail="Role-Pipeline relation not found")

@router.put("/api/internal/mongodb/relation/role_pipeline/{relation_id}", response_model=RolePipelineResponse)
async def update_role_pipeline(relation_id: str, role_pipeline: RolePipeline, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_pipeline_dict = role_pipeline.model_dump()
        result = await db.role_pipelines.update_one({"_id": ObjectId(relation_id)}, {"$set": role_pipeline_dict})
        if result.modified_count == 1:
            role_pipeline = await db.role_pipelines.find_one({"_id": ObjectId(relation_id)})
            role_pipeline["relation_id"] = str(role_pipeline["_id"])
            return RolePipelineResponse(**role_pipeline)
        raise HTTPException(status_code=404, detail="Role-Pipeline relation not found")

@router.delete("/api/internal/mongodb/relation/role_pipeline/{relation_id}", response_model=dict)
async def delete_role_pipeline(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_pipelines.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Pipeline relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Pipeline relation not found")
