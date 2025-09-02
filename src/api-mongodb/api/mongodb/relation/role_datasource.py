from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RoleDatasource(BaseModel):
    role_id: str
    datasource_id: str
    permissions: dict

class RoleDatasourceResponse(BaseModel):
    relation_id: str
    role_id: str
    datasource_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_datasource", response_model=RoleDatasourceResponse)
async def create_role_datasource(role_datasource: RoleDatasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_datasource_dict = role_datasource.model_dump()
        role_datasource_dict["created_at"] = datetime.now(UTC).isoformat()
        role_datasource_dict["created_by"] = current_user["user_id"]
        result = await db.role_datasources.insert_one(role_datasource_dict)
        role_datasource_dict["relation_id"] = str(result.inserted_id)
        return RoleDatasourceResponse(**role_datasource_dict)

@router.get("/api/internal/mongodb/relation/role_datasource/{relation_id}", response_model=RoleDatasourceResponse)
async def get_role_datasource(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_datasource = await db.role_datasources.find_one({"_id": ObjectId(relation_id)})
        if role_datasource:
            role_datasource["relation_id"] = str(role_datasource["_id"])
            return RoleDatasourceResponse(**role_datasource)
        raise HTTPException(status_code=404, detail="Role-Datasource relation not found")

@router.put("/api/internal/mongodb/relation/role_datasource/{relation_id}", response_model=RoleDatasourceResponse)
async def update_role_datasource(relation_id: str, role_datasource: RoleDatasource, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_datasource_dict = role_datasource.model_dump()
        result = await db.role_datasources.update_one({"_id": ObjectId(relation_id)}, {"$set": role_datasource_dict})
        if result.modified_count == 1:
            role_datasource = await db.role_datasources.find_one({"_id": ObjectId(relation_id)})
            role_datasource["relation_id"] = str(role_datasource["_id"])
            return RoleDatasourceResponse(**role_datasource)
        raise HTTPException(status_code=404, detail="Role-Datasource relation not found")

@router.delete("/api/internal/mongodb/relation/role_datasource/{relation_id}", response_model=dict)
async def delete_role_datasource(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_datasources.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Datasource relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Datasource relation not found")
