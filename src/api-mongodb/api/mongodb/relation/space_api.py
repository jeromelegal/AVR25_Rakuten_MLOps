from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class SpaceApi(BaseModel):
    space_id: str
    api_id: str
    position: int

class SpaceApiResponse(BaseModel):
    relation_id: str
    space_id: str
    api_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/space_api", response_model=SpaceApiResponse)
async def create_space_api(space_api: SpaceApi, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_api_dict = space_api.model_dump()
        space_api_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_api_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.space_api.insert_one(space_api_dict)
        space_api_dict["relation_id"] = str(result.inserted_id)
        return SpaceApiResponse(**space_api_dict)

@router.get("/api/internal/mongodb/relation/space_api/{relation_id}", response_model=SpaceApiResponse)
async def get_space_api(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_api = await db.space_api.find_one({"_id": ObjectId(relation_id)})
        if space_api:
            space_api["relation_id"] = str(space_api["_id"])
            return SpaceApiResponse(**space_api)
        raise HTTPException(status_code=404, detail="Space-Api relation not found")

@router.put("/api/internal/mongodb/relation/space_api/{relation_id}", response_model=SpaceApiResponse)
async def update_space_api(relation_id: str, space_api: SpaceApi, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_api_dict = space_api.model_dump()
        result = await db.space_api.update_one({"_id": ObjectId(relation_id)}, {"$set": space_api_dict})
        if result.modified_count == 1:
            space_api = await db.space_api.find_one({"_id": ObjectId(relation_id)})
            space_api["relation_id"] = str(space_api["_id"])
            return SpaceApiResponse(**space_api)
        raise HTTPException(status_code=404, detail="Space-Api relation not found")

@router.delete("/api/internal/mongodb/relation/space_api/{relation_id}", response_model=dict)
async def delete_space_api(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.space_api.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Space-Api relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Space-Api relation not found")
