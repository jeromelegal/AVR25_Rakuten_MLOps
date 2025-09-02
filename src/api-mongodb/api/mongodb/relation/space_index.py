from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class SpaceIndex(BaseModel):
    space_id: str
    index_id: str
    position: int

class SpaceIndexResponse(BaseModel):
    relation_id: str
    space_id: str
    index_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/space_index", response_model=SpaceIndexResponse)
async def create_space_index(space_index: SpaceIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_index_dict = space_index.model_dump()
        space_index_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_index_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.space_index.insert_one(space_index_dict)
        space_index_dict["relation_id"] = str(result.inserted_id)
        return SpaceIndexResponse(**space_index_dict)

@router.get("/api/internal/mongodb/relation/space_index/{relation_id}", response_model=SpaceIndexResponse)
async def get_space_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_index = await db.space_index.find_one({"_id": ObjectId(relation_id)})
        if space_index:
            space_index["relation_id"] = str(space_index["_id"])
            return SpaceIndexResponse(**space_index)
        raise HTTPException(status_code=404, detail="Space-Index relation not found")

@router.put("/api/internal/mongodb/relation/space_index/{relation_id}", response_model=SpaceIndexResponse)
async def update_space_index(relation_id: str, space_index: SpaceIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_index_dict = space_index.model_dump()
        result = await db.space_index.update_one({"_id": ObjectId(relation_id)}, {"$set": space_index_dict})
        if result.modified_count == 1:
            space_index = await db.space_index.find_one({"_id": ObjectId(relation_id)})
            space_index["relation_id"] = str(space_index["_id"])
            return SpaceIndexResponse(**space_index)
        raise HTTPException(status_code=404, detail="Space-Index relation not found")

@router.delete("/api/internal/mongodb/relation/space_index/{relation_id}", response_model=dict)
async def delete_space_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.space_index.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Space-Index relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Space-Index relation not found")
