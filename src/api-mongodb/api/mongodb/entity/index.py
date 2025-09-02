from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC
import uuid

router = APIRouter()

class Index(BaseModel):
    name: str
    description: str
    statistics: dict

class IndexResponse(BaseModel):
    index_id: str
    name: str
    description: str
    statistics: dict
    created_at: str
    created_by: str
    elasticsearch_id: str

@router.post("/api/internal/mongodb/entity/index", response_model=IndexResponse)
async def create_index(index: Index, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        index_dict = index.model_dump()
        index_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        index_dict["created_by"] = current_user["user_id"]  # Set the creator
        index_dict["elasticsearch_id"] = str(uuid.uuid4())  # Generate a unique Elasticsearch ID
        result = await db.indexes.insert_one(index_dict)
        index_dict["index_id"] = str(result.inserted_id)
        return IndexResponse(**index_dict)

@router.get("/api/internal/mongodb/entity/index/{index_id}", response_model=IndexResponse)
async def get_index(index_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        index = await db.indexes.find_one({"_id": ObjectId(index_id)})
        if index:
            index["index_id"] = str(index["_id"])
            return IndexResponse(**index)
        raise HTTPException(status_code=404, detail="Index not found")

@router.put("/api/internal/mongodb/entity/index/{index_id}", response_model=IndexResponse)
async def update_index(index_id: str, index: Index, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        index_dict = index.model_dump()
        result = await db.indexes.update_one({"_id": ObjectId(index_id)}, {"$set": index_dict})
        if result.modified_count == 1:
            index = await db.indexes.find_one({"_id": ObjectId(index_id)})
            index["index_id"] = str(index["_id"])
            return IndexResponse(**index)
        raise HTTPException(status_code=404, detail="Index not found")

@router.delete("/api/internal/mongodb/entity/index/{index_id}", response_model=dict)
async def delete_index(index_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.indexes.delete_one({"_id": ObjectId(index_id)})
        if result.deleted_count == 1:
            return {"message": "Index deleted successfully"}
        raise HTTPException(status_code=404, detail="Index not found")
