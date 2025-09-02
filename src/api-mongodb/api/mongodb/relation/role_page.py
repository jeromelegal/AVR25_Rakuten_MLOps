from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class RolePage(BaseModel):
    role_id: str
    page_id: str
    permissions: dict

class RolePageResponse(BaseModel):
    relation_id: str
    role_id: str
    page_id: str
    permissions: dict
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/relation/role_page", response_model=RolePageResponse)
async def create_role_page(role_page: RolePage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_page_dict = role_page.model_dump()
        role_page_dict["created_at"] = datetime.now(UTC).isoformat()
        role_page_dict["created_by"] = current_user["user_id"]
        result = await db.role_pages.insert_one(role_page_dict)
        role_page_dict["relation_id"] = str(result.inserted_id)
        return RolePageResponse(**role_page_dict)

@router.get("/api/internal/mongodb/relation/role_page/{relation_id}", response_model=RolePageResponse)
async def get_role_page(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_page = await db.role_pages.find_one({"_id": ObjectId(relation_id)})
        if role_page:
            role_page["relation_id"] = str(role_page["_id"])
            return RolePageResponse(**role_page)
        raise HTTPException(status_code=404, detail="Role-Page relation not found")

@router.put("/api/internal/mongodb/relation/role_page/{relation_id}", response_model=RolePageResponse)
async def update_role_page(relation_id: str, role_page: RolePage, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        role_page_dict = role_page.model_dump()
        result = await db.role_pages.update_one({"_id": ObjectId(relation_id)}, {"$set": role_page_dict})
        if result.modified_count == 1:
            role_page = await db.role_pages.find_one({"_id": ObjectId(relation_id)})
            role_page["relation_id"] = str(role_page["_id"])
            return RolePageResponse(**role_page)
        raise HTTPException(status_code=404, detail="Role-Page relation not found")

@router.delete("/api/internal/mongodb/relation/role_page/{relation_id}", response_model=dict)
async def delete_role_page(relation_id: str, current_user: dict = Depends(get_current_user)):
    async with get_db_client() as db:
        result = await db.role_pages.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Role-Page relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-Page relation not found")
