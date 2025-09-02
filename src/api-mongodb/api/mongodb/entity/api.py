from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class API(BaseModel):
    name: str
    endpoint: str
    description: str

class APIResponse(BaseModel):
    api_id: str
    name: str
    endpoint: str
    description: str
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/api", response_model=APIResponse)
async def create_api(api: API, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        api_dict = api.model_dump()
        api_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        api_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.apis.insert_one(api_dict)
        api_dict["api_id"] = str(result.inserted_id)
        return APIResponse(**api_dict)

@router.get("/api/internal/mongodb/entity/api/{api_id}", response_model=APIResponse)
async def get_api(api_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        api = await db.apis.find_one({"_id": ObjectId(api_id)})
        if api:
            api["api_id"] = str(api["_id"])
            return APIResponse(**api)
        raise HTTPException(status_code=404, detail="API not found")

@router.put("/api/internal/mongodb/entity/api/{api_id}", response_model=APIResponse)
async def update_api(api_id: str, api: API, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        api_dict = api.model_dump()
        result = await db.apis.update_one({"_id": ObjectId(api_id)}, {"$set": api_dict})
        if result.modified_count == 1:
            api = await db.apis.find_one({"_id": ObjectId(api_id)})
            api["api_id"] = str(api["_id"])
            return APIResponse(**api)
        raise HTTPException(status_code=404, detail="API not found")

@router.delete("/api/internal/mongodb/entity/api/{api_id}", response_model=dict)
async def delete_api(api_id: str, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        result = await db.apis.delete_one({"_id": ObjectId(api_id)})
        if result.deleted_count == 1:
            return {"message": "API deleted successfully"}
        raise HTTPException(status_code=404, detail="API not found")
