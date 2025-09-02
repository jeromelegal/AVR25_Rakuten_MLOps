from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class SpaceDirectory(BaseModel):
    space_id: str
    directory_id: str
    position: int

class SpaceDirectoryResponse(BaseModel):
    relation_id: str
    space_id: str
    directory_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/space_directory", response_model=SpaceDirectoryResponse)
async def create_space_directory(space_directory: SpaceDirectory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_directory_dict = space_directory.model_dump()
        space_directory_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_directory_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.space_directory.insert_one(space_directory_dict)
        space_directory_dict["relation_id"] = str(result.inserted_id)
        return SpaceDirectoryResponse(**space_directory_dict)

@router.get("/api/internal/mongodb/relation/space_directory/{relation_id}", response_model=SpaceDirectoryResponse)
async def get_space_directory(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_directory = await db.space_directory.find_one({"_id": ObjectId(relation_id)})
        if space_directory:
            space_directory["relation_id"] = str(space_directory["_id"])
            return SpaceDirectoryResponse(**space_directory)
        raise HTTPException(status_code=404, detail="Space-Directory relation not found")

@router.put("/api/internal/mongodb/relation/space_directory/{relation_id}", response_model=SpaceDirectoryResponse)
async def update_space_directory(relation_id: str, space_directory: SpaceDirectory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_directory_dict = space_directory.model_dump()
        result = await db.space_directory.update_one({"_id": ObjectId(relation_id)}, {"$set": space_directory_dict})
        if result.modified_count == 1:
            space_directory = await db.space_directory.find_one({"_id": ObjectId(relation_id)})
            space_directory["relation_id"] = str(space_directory["_id"])
            return SpaceDirectoryResponse(**space_directory)
        raise HTTPException(status_code=404, detail="Space-Directory relation not found")

@router.delete("/api/internal/mongodb/relation/space_directory/{relation_id}", response_model=dict)
async def delete_space_directory(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.space_directory.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Space-Directory relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Space-Directory relation not found")
