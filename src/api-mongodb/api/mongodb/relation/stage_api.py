from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class StageApi(BaseModel):
    stage_id: str
    api_id: str
    position: int

class StageApiResponse(BaseModel):
    relation_id: str
    stage_id: str
    api_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/stage_api", response_model=StageApiResponse)
async def create_stage_api(stage_api: StageApi, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        stage_api_dict = stage_api.model_dump()
        stage_api_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        stage_api_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.stage_api.insert_one(stage_api_dict)
        stage_api_dict["relation_id"] = str(result.inserted_id)
        return StageApiResponse(**stage_api_dict)

@router.get("/api/internal/mongodb/relation/stage_api/{relation_id}", response_model=StageApiResponse)
async def get_stage_api(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        stage_api = await db.stage_api.find_one({"_id": ObjectId(relation_id)})
        if stage_api:
            stage_api["relation_id"] = str(stage_api["_id"])
            return StageApiResponse(**stage_api)
        raise HTTPException(status_code=404, detail="Stage-Api relation not found")

@router.put("/api/internal/mongodb/relation/stage_api/{relation_id}", response_model=StageApiResponse)
async def update_stage_api(relation_id: str, stage_api: StageApi, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        stage_api_dict = stage_api.model_dump()
        result = await db.stage_api.update_one({"_id": ObjectId(relation_id)}, {"$set": stage_api_dict})
        if result.modified_count == 1:
            stage_api = await db.stage_api.find_one({"_id": ObjectId(relation_id)})
            stage_api["relation_id"] = str(stage_api["_id"])
            return StageApiResponse(**stage_api)
        raise HTTPException(status_code=404, detail="Stage-Api relation not found")

@router.delete("/api/internal/mongodb/relation/stage_api/{relation_id}", response_model=dict)
async def delete_stage_api(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.stage_api.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Stage-Api relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Stage-Api relation not found")
