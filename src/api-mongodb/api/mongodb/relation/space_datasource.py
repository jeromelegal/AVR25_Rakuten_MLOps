from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class SpaceDatasource(BaseModel):
    space_id: str
    datasource_id: str
    position: int

class SpaceDatasourceResponse(BaseModel):
    relation_id: str
    space_id: str
    datasource_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/space_datasource", response_model=SpaceDatasourceResponse)
async def create_space_datasource(space_datasource: SpaceDatasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_datasource_dict = space_datasource.model_dump()
        space_datasource_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        space_datasource_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.space_datasource.insert_one(space_datasource_dict)
        space_datasource_dict["relation_id"] = str(result.inserted_id)
        return SpaceDatasourceResponse(**space_datasource_dict)

@router.get("/api/internal/mongodb/relation/space_datasource/{relation_id}", response_model=SpaceDatasourceResponse)
async def get_space_datasource(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_datasource = await db.space_datasource.find_one({"_id": ObjectId(relation_id)})
        if space_datasource:
            space_datasource["relation_id"] = str(space_datasource["_id"])
            return SpaceDatasourceResponse(**space_datasource)
        raise HTTPException(status_code=404, detail="Space-Datasource relation not found")

@router.put("/api/internal/mongodb/relation/space_datasource/{relation_id}", response_model=SpaceDatasourceResponse)
async def update_space_datasource(relation_id: str, space_datasource: SpaceDatasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        space_datasource_dict = space_datasource.model_dump()
        result = await db.space_datasource.update_one({"_id": ObjectId(relation_id)}, {"$set": space_datasource_dict})
        if result.modified_count == 1:
            space_datasource = await db.space_datasource.find_one({"_id": ObjectId(relation_id)})
            space_datasource["relation_id"] = str(space_datasource["_id"])
            return SpaceDatasourceResponse(**space_datasource)
        raise HTTPException(status_code=404, detail="Space-Datasource relation not found")

@router.delete("/api/internal/mongodb/relation/space_datasource/{relation_id}", response_model=dict)
async def delete_space_datasource(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.space_datasource.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Space-Datasource relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Space-Datasource relation not found")
