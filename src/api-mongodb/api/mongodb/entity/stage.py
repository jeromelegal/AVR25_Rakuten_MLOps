from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Stage(BaseModel):
    name: str
    type: str
    configuration: dict

class StageResponse(BaseModel):
    stage_id: str
    name: str
    type: str
    configuration: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/stage", response_model=StageResponse)
async def create_stage(stage: Stage, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        stage_dict = stage.model_dump()
        stage_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        stage_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.stages.insert_one(stage_dict)
        stage_dict["stage_id"] = str(result.inserted_id)
        return StageResponse(**stage_dict)

@router.get("/api/internal/mongodb/entity/stage/{stage_id}", response_model=StageResponse)
async def get_stage(stage_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        stage = await db.stages.find_one({"_id": ObjectId(stage_id)})
        if stage:
            stage["stage_id"] = str(stage["_id"])
            return StageResponse(**stage)
        raise HTTPException(status_code=404, detail="Stage not found")

@router.put("/api/internal/mongodb/entity/stage/{stage_id}", response_model=StageResponse)
async def update_stage(stage_id: str, stage: Stage, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        stage_dict = stage.model_dump()
        result = await db.stages.update_one({"_id": ObjectId(stage_id)}, {"$set": stage_dict})
        if result.modified_count == 1:
            stage = await db.stages.find_one({"_id": ObjectId(stage_id)})
            stage["stage_id"] = str(stage["_id"])
            return StageResponse(**stage)
        raise HTTPException(status_code=404, detail="Stage not found")

@router.delete("/api/internal/mongodb/entity/stage/{stage_id}", response_model=dict)
async def delete_stage(stage_id: str, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        result = await db.stages.delete_one({"_id": ObjectId(stage_id)})
        if result.deleted_count == 1:
            return {"message": "Stage deleted successfully"}
        raise HTTPException(status_code=404, detail="Stage not found")
