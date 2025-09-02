from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class DirectoryDirectory(BaseModel):
    parent_directory_id: str
    child_directory_id: str
    position: int

class DirectoryDirectoryResponse(BaseModel):
    relation_id: str
    parent_directory_id: str
    child_directory_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/directory_directory", response_model=DirectoryDirectoryResponse)
async def create_directory_directory(directory_directory: DirectoryDirectory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_directory_dict = directory_directory.model_dump()
        directory_directory_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        directory_directory_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.directory_directory.insert_one(directory_directory_dict)
        directory_directory_dict["relation_id"] = str(result.inserted_id)
        return DirectoryDirectoryResponse(**directory_directory_dict)

@router.get("/api/internal/mongodb/relation/directory_directory/{relation_id}", response_model=DirectoryDirectoryResponse)
async def get_directory_directory(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_directory = await db.directory_directory.find_one({"_id": ObjectId(relation_id)})
        if directory_directory:
            directory_directory["relation_id"] = str(directory_directory["_id"])
            return DirectoryDirectoryResponse(**directory_directory)
        raise HTTPException(status_code=404, detail="Directory-Directory relation not found")

@router.put("/api/internal/mongodb/relation/directory_directory/{relation_id}", response_model=DirectoryDirectoryResponse)
async def update_directory_directory(relation_id: str, directory_directory: DirectoryDirectory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_directory_dict = directory_directory.model_dump()
        result = await db.directory_directory.update_one({"_id": ObjectId(relation_id)}, {"$set": directory_directory_dict})
        if result.modified_count == 1:
            directory_directory = await db.directory_directory.find_one({"_id": ObjectId(relation_id)})
            directory_directory["relation_id"] = str(directory_directory["_id"])
            return DirectoryDirectoryResponse(**directory_directory)
        raise HTTPException(status_code=404, detail="Directory-Directory relation not found")

@router.delete("/api/internal/mongodb/relation/directory_directory/{relation_id}", response_model=dict)
async def delete_directory_directory(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.directory_directory.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Directory-Directory relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Directory-Directory relation not found")
