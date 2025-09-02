from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Datasource(BaseModel):
    name: str
    type: str
    configuration: dict

class DatasourceResponse(BaseModel):
    datasource_id: str
    name: str
    type: str
    configuration: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/datasource", response_model=DatasourceResponse)
async def create_datasource(datasource: Datasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        datasource_dict = datasource.model_dump()
        datasource_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        datasource_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.datasources.insert_one(datasource_dict)
        datasource_dict["datasource_id"] = str(result.inserted_id)
        return DatasourceResponse(**datasource_dict)

@router.get("/api/internal/mongodb/entity/datasource/{datasource_id}", response_model=DatasourceResponse)
async def get_datasource(datasource_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
        if datasource:
            datasource["datasource_id"] = str(datasource["_id"])
            return DatasourceResponse(**datasource)
        raise HTTPException(status_code=404, detail="Datasource not found")

@router.put("/api/internal/mongodb/entity/datasource/{datasource_id}", response_model=DatasourceResponse)
async def update_datasource(datasource_id: str, datasource: Datasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        datasource_dict = datasource.model_dump()
        result = await db.datasources.update_one({"_id": ObjectId(datasource_id)}, {"$set": datasource_dict})
        if result.modified_count == 1:
            datasource = await db.datasources.find_one({"_id": ObjectId(datasource_id)})
            datasource["datasource_id"] = str(datasource["_id"])
            return DatasourceResponse(**datasource)
        raise HTTPException(status_code=404, detail="Datasource not found")

@router.delete("/api/internal/mongodb/entity/datasource/{datasource_id}", response_model=dict)
async def delete_datasource(datasource_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.datasources.delete_one({"_id": ObjectId(datasource_id)})
        if result.deleted_count == 1:
            return {"message": "Datasource deleted successfully"}
        raise HTTPException(status_code=404, detail="Datasource not found")
