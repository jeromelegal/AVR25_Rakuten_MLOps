from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class PipelineStage(BaseModel):
    pipeline_id: str
    stage_id: str
    position: int

class PipelineStageResponse(BaseModel):
    relation_id: str
    pipeline_id: str
    stage_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/pipeline_stage", response_model=PipelineStageResponse)
async def create_pipeline_stage(pipeline_stage: PipelineStage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_stage_dict = pipeline_stage.model_dump()
        pipeline_stage_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        pipeline_stage_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.pipeline_stage.insert_one(pipeline_stage_dict)
        pipeline_stage_dict["relation_id"] = str(result.inserted_id)
        return PipelineStageResponse(**pipeline_stage_dict)

@router.get("/api/internal/mongodb/relation/pipeline_stage/{relation_id}", response_model=PipelineStageResponse)
async def get_pipeline_stage(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_stage = await db.pipeline_stage.find_one({"_id": ObjectId(relation_id)})
        if pipeline_stage:
            pipeline_stage["relation_id"] = str(pipeline_stage["_id"])
            return PipelineStageResponse(**pipeline_stage)
        raise HTTPException(status_code=404, detail="Pipeline-Stage relation not found")

@router.put("/api/internal/mongodb/relation/pipeline_stage/{relation_id}", response_model=PipelineStageResponse)
async def update_pipeline_stage(relation_id: str, pipeline_stage: PipelineStage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_stage_dict = pipeline_stage.model_dump()
        result = await db.pipeline_stage.update_one({"_id": ObjectId(relation_id)}, {"$set": pipeline_stage_dict})
        if result.modified_count == 1:
            pipeline_stage = await db.pipeline_stage.find_one({"_id": ObjectId(relation_id)})
            pipeline_stage["relation_id"] = str(pipeline_stage["_id"])
            return PipelineStageResponse(**pipeline_stage)
        raise HTTPException(status_code=404, detail="Pipeline-Stage relation not found")

@router.delete("/api/internal/mongodb/relation/pipeline_stage/{relation_id}", response_model=dict)
async def delete_pipeline_stage(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.pipeline_stage.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Pipeline-Stage relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Pipeline-Stage relation not found")
