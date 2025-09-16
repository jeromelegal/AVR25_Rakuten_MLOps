from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC
from config.settings import Settings

router = APIRouter()

class Category(BaseModel):
    code: int
    label: str

class CategoryResponse(BaseModel):
    category_id: str
    code: int
    label: str

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

@router.post("/api/internal/mongodb/entity/category", response_model=CategoryResponse)
async def create_ad(request: Request, category: Category, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        category_dict = category.model_dump()
        category_dict["created_at"] = datetime.now(UTC).isoformat()
        res = await db.categories.insert_one(category_dict)
        category_dict["category_id"] = str(res.inserted_id)
        return CategoryResponse(**category_dict)

@router.get("/api/internal/mongodb/entity/category/{category_id}", response_model=CategoryResponse)
async def get_ad(request: Request, category_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        category = await db.categories.find_one({"_id": ObjectId(category_id)})
        if category:
            category["category_id"] = str(category["_id"])
            return CategoryResponse(**category)
        raise HTTPException(status_code=404, detail="Category not found")

@router.put("/api/internal/mongodb/entity/category/{category_id}", response_model=CategoryResponse)
async def update_ad(request: Request, category_id: str, category: Category, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        category_dict = category.model_dump()
        result = await db.categories.update_one({"_id": ObjectId(category_id)}, {"$set": category_dict})
        if result.modified_count == 1:
            category = await db.categories.find_one({"_id": ObjectId(category_id)})
            category["category_id"] = str(category["_id"])
            return CategoryResponse(**category)
        raise HTTPException(status_code=404, detail="Category not found")

@router.delete("/api/internal/mongodb/entity/category/{category_id}", response_model=dict)
async def delete_ad(request: Request, category_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        result = await db.categories.delete_one({"_id": ObjectId(category_id)})
        if result.deleted_count == 1:
            return {"message": "Category deleted successfully"}
        raise HTTPException(status_code=404, detail="Category not found")
