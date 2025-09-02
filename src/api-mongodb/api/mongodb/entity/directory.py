from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Directory(BaseModel):
    name: str
    path: str
    parent_directory_id: Optional[str] = None

class DirectoryResponse(BaseModel):
    directory_id: str
    name: str
    path: str
    parent_directory_id: Optional[str] = None
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/directory", response_model=DirectoryResponse)
async def create_directory(directory: Directory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_dict = directory.model_dump()
        directory_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        directory_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.directories.insert_one(directory_dict)
        directory_dict["directory_id"] = str(result.inserted_id)
        return DirectoryResponse(**directory_dict)

@router.get("/api/internal/mongodb/entity/directory/{directory_id}", response_model=DirectoryResponse)
async def get_directory(directory_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory = await db.directories.find_one({"_id": ObjectId(directory_id)})
        if directory:
            directory["directory_id"] = str(directory["_id"])
            directory["parent_directory_id"] = directory.get("parent_directory_id", None)
            return DirectoryResponse(**directory)
        raise HTTPException(status_code=404, detail="Directory not found")

@router.put("/api/internal/mongodb/entity/directory/{directory_id}", response_model=DirectoryResponse)
async def update_directory(directory_id: str, directory: Directory, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        directory_dict = directory.model_dump()
        result = await db.directories.update_one({"_id": ObjectId(directory_id)}, {"$set": directory_dict})
        if result.modified_count == 1:
            directory = await db.directories.find_one({"_id": ObjectId(directory_id)})
            directory["directory_id"] = str(directory["_id"])
            directory["parent_directory_id"] = directory.get("parent_directory_id", None)
            return DirectoryResponse(**directory)
        raise HTTPException(status_code=404, detail="Directory not found")

@router.delete("/api/internal/mongodb/entity/directory/{directory_id}", response_model=dict)
async def delete_directory(directory_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.directories.delete_one({"_id": ObjectId(directory_id)})
        if result.deleted_count == 1:
            return {"message": "Directory deleted successfully"}
        raise HTTPException(status_code=404, detail="Directory not found")
