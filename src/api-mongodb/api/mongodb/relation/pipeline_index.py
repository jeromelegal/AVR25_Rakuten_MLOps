from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class PipelineIndex(BaseModel):
    pipeline_id: str
    index_id: str
    position: int

class PipelineIndexResponse(BaseModel):
    relation_id: str
    pipeline_id: str
    index_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/pipeline_index", response_model=PipelineIndexResponse)
async def create_pipeline_index(pipeline_index: PipelineIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_index_dict = pipeline_index.model_dump()
        pipeline_index_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        pipeline_index_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.pipeline_index.insert_one(pipeline_index_dict)
        pipeline_index_dict["relation_id"] = str(result.inserted_id)
        return PipelineIndexResponse(**pipeline_index_dict)

@router.get("/api/internal/mongodb/relation/pipeline_index/{relation_id}", response_model=PipelineIndexResponse)
async def get_pipeline_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_index = await db.pipeline_index.find_one({"_id": ObjectId(relation_id)})
        if pipeline_index:
            pipeline_index["relation_id"] = str(pipeline_index["_id"])
            return PipelineIndexResponse(**pipeline_index)
        raise HTTPException(status_code=404, detail="Pipeline-Index relation not found")

@router.put("/api/internal/mongodb/relation/pipeline_index/{relation_id}", response_model=PipelineIndexResponse)
async def update_pipeline_index(relation_id: str, pipeline_index: PipelineIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        pipeline_index_dict = pipeline_index.model_dump()
        result = await db.pipeline_index.update_one({"_id": ObjectId(relation_id)}, {"$set": pipeline_index_dict})
        if result.modified_count == 1:
            pipeline_index = await db.pipeline_index.find_one({"_id": ObjectId(relation_id)})
            pipeline_index["relation_id"] = str(pipeline_index["_id"])
            return PipelineIndexResponse(**pipeline_index)
        raise HTTPException(status_code=404, detail="Pipeline-Index relation not found")

@router.delete("/api/internal/mongodb/relation/pipeline_index/{relation_id}", response_model=dict)
async def delete_pipeline_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.pipeline_index.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Pipeline-Index relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Pipeline-Index relation not found")
