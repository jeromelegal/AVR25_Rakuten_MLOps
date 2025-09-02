from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Space(BaseModel):
    name: str
    description: str

class SpaceResponse(BaseModel):
    space_id: str
    name: str
    description: str
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/space", response_model=SpaceResponse)
async def create_space(space: Space, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_dict = space.model_dump()
        space_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.spaces.insert_one(space_dict)
        space_dict["space_id"] = str(result.inserted_id)
        return SpaceResponse(**space_dict)

@router.get("/api/internal/mongodb/entity/space/{space_id}", response_model=SpaceResponse)
async def get_space(space_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space = await db.spaces.find_one({"_id": ObjectId(space_id)})
        if space:
            space["space_id"] = str(space["_id"])
            return SpaceResponse(**space)
        raise HTTPException(status_code=404, detail="Space not found")

@router.put("/api/internal/mongodb/entity/space/{space_id}", response_model=SpaceResponse)
async def update_space(space_id: str, space: Space, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_dict = space.model_dump()
        result = await db.spaces.update_one({"_id": ObjectId(space_id)}, {"$set": space_dict})
        if result.modified_count == 1:
            space = await db.spaces.find_one({"_id": ObjectId(space_id)})
            space["space_id"] = str(space["_id"])
            return SpaceResponse(**space)
        raise HTTPException(status_code=404, detail="Space not found")

@router.delete("/api/internal/mongodb/entity/space/{space_id}", response_model=dict)
async def delete_space(space_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.spaces.delete_one({"_id": ObjectId(space_id)})
        if result.deleted_count == 1:
            return {"message": "Space deleted successfully"}
        raise HTTPException(status_code=404, detail="Space not found")
