from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class DatasourceIndex(BaseModel):
    datasource_id: str
    index_id: str
    position: int

class DatasourceIndexResponse(BaseModel):
    relation_id: str
    datasource_id: str
    index_id: str
    position: int
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/datasource_index", response_model=DatasourceIndexResponse)
async def create_datasource_index(datasource_index: DatasourceIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        datasource_index_dict = datasource_index.model_dump()
        datasource_index_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        datasource_index_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.datasource_index.insert_one(datasource_index_dict)
        datasource_index_dict["relation_id"] = str(result.inserted_id)
        return DatasourceIndexResponse(**datasource_index_dict)

@router.get("/api/internal/mongodb/relation/datasource_index/{relation_id}", response_model=DatasourceIndexResponse)
async def get_datasource_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        datasource_index = await db.datasource_index.find_one({"_id": ObjectId(relation_id)})
        if datasource_index:
            datasource_index["relation_id"] = str(datasource_index["_id"])
            return DatasourceIndexResponse(**datasource_index)
        raise HTTPException(status_code=404, detail="Datasource-Index relation not found")

@router.put("/api/internal/mongodb/relation/datasource_index/{relation_id}", response_model=DatasourceIndexResponse)
async def update_datasource_index(relation_id: str, datasource_index: DatasourceIndex, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        datasource_index_dict = datasource_index.model_dump()
        result = await db.datasource_index.update_one({"_id": ObjectId(relation_id)}, {"$set": datasource_index_dict})
        if result.modified_count == 1:
            datasource_index = await db.datasource_index.find_one({"_id": ObjectId(relation_id)})
            datasource_index["relation_id"] = str(datasource_index["_id"])
            return DatasourceIndexResponse(**datasource_index)
        raise HTTPException(status_code=404, detail="Datasource-Index relation not found")

@router.delete("/api/internal/mongodb/relation/datasource_index/{relation_id}", response_model=dict)
async def delete_datasource_index(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.datasource_index.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Datasource-Index relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Datasource-Index relation not found")
