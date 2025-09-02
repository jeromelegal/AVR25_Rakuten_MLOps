from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class SpacePipeline(BaseModel):
    space_id: str
    pipeline_id: str
    position: int

class SpacePipelineResponse(BaseModel):
    relation_id: str
    space_id: str
    pipeline_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/space_pipeline", response_model=SpacePipelineResponse)
async def create_space_pipeline(space_pipeline: SpacePipeline, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_pipeline_dict = space_pipeline.model_dump()
        space_pipeline_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_pipeline_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.space_pipeline.insert_one(space_pipeline_dict)
        space_pipeline_dict["relation_id"] = str(result.inserted_id)
        return SpacePipelineResponse(**space_pipeline_dict)

@router.get("/api/internal/mongodb/relation/space_pipeline/{relation_id}", response_model=SpacePipelineResponse)
async def get_space_pipeline(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_pipeline = await db.space_pipeline.find_one({"_id": ObjectId(relation_id)})
        if space_pipeline:
            space_pipeline["relation_id"] = str(space_pipeline["_id"])
            return SpacePipelineResponse(**space_pipeline)
        raise HTTPException(status_code=404, detail="Space-Pipeline relation not found")

@router.put("/api/internal/mongodb/relation/space_pipeline/{relation_id}", response_model=SpacePipelineResponse)
async def update_space_pipeline(relation_id: str, space_pipeline: SpacePipeline, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_pipeline_dict = space_pipeline.model_dump()
        result = await db.space_pipeline.update_one({"_id": ObjectId(relation_id)}, {"$set": space_pipeline_dict})
        if result.modified_count == 1:
            space_pipeline = await db.space_pipeline.find_one({"_id": ObjectId(relation_id)})
            space_pipeline["relation_id"] = str(space_pipeline["_id"])
            return SpacePipelineResponse(**space_pipeline)
        raise HTTPException(status_code=404, detail="Space-Pipeline relation not found")

@router.delete("/api/internal/mongodb/relation/space_pipeline/{relation_id}", response_model=dict)
async def delete_space_pipeline(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.space_pipeline.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Space-Pipeline relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Space-Pipeline relation not found")
