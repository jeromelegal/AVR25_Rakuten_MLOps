from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class PipelineStep(BaseModel):
    name: str
    type: str
    configuration: dict

class Pipeline(BaseModel):
    name: str
    steps: List[PipelineStep]

class PipelineResponse(BaseModel):
    pipeline_id: str
    name: str
    steps: List[PipelineStep]
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/pipeline", response_model=PipelineResponse)
async def create_pipeline(pipeline: Pipeline, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_dict = pipeline.model_dump()
        pipeline_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        pipeline_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.pipelines.insert_one(pipeline_dict)
        pipeline_dict["pipeline_id"] = str(result.inserted_id)
        return PipelineResponse(**pipeline_dict)

@router.get("/api/internal/mongodb/entity/pipeline/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline = await db.pipelines.find_one({"_id": ObjectId(pipeline_id)})
        if pipeline:
            pipeline["pipeline_id"] = str(pipeline["_id"])
            return PipelineResponse(**pipeline)
        raise HTTPException(status_code=404, detail="Pipeline not found")

@router.put("/api/internal/mongodb/entity/pipeline/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline(pipeline_id: str, pipeline: Pipeline, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_dict = pipeline.model_dump()
        result = await db.pipelines.update_one({"_id": ObjectId(pipeline_id)}, {"$set": pipeline_dict})
        if result.modified_count == 1:
            pipeline = await db.pipelines.find_one({"_id": ObjectId(pipeline_id)})
            pipeline["pipeline_id"] = str(pipeline["_id"])
            return PipelineResponse(**pipeline)
        raise HTTPException(status_code=404, detail="Pipeline not found")

@router.delete("/api/internal/mongodb/entity/pipeline/{pipeline_id}", response_model=dict)
async def delete_pipeline(pipeline_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.pipelines.delete_one({"_id": ObjectId(pipeline_id)})
        if result.deleted_count == 1:
            return {"message": "Pipeline deleted successfully"}
        raise HTTPException(status_code=404, detail="Pipeline not found")
