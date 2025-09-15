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

class AdCategory(BaseModel):
    ad_id: str
    category_id: str
    #position: int

class AdCategoryResponse(BaseModel):
    relation_id: str
    ad_id: str
    category_id: str
    created_at: str
    created_by: str
    #position: int

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

@router.post("/api/internal/mongodb/relation/ad_category", response_model=AdCategoryResponse)
async def create_ad_category(request: Request, ad_category: AdCategory, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_category_dict = ad_category.model_dump()
        ad_category_dict["created_at"] = datetime.now(UTC).isoformat()
        ad_category_dict["created_by"] = current_user["user_id"]
        ad_category_dict["ad_id"] = ObjectId(ad_category_dict["ad_id"])
        ad_category_dict["category_id"] = ObjectId(ad_category_dict["category_id"])
        result = await db.ad_category.insert_one(ad_category_dict)
        ad_category_dict["relation_id"] = str(result.inserted_id)
        ad_category_dict["ad_id"] = str(ad_category_dict["ad_id"])
        ad_category_dict["category_id"] = str(ad_category_dict["category_id"])
        return AdCategoryResponse(**ad_category_dict)

@router.get("/api/internal/mongodb/relation/ad_category/{relation_id}", response_model=AdCategoryResponse)
async def get_ad_category(request: Request, relation_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_category = await db.ad_category.find_one({"_id": ObjectId(relation_id)})
        if ad_category:
            ad_category["relation_id"] = str(ad_category["_id"])
            return AdCategoryResponse(**ad_category)
        raise HTTPException(status_code=404, detail="Ad-Category relation not found")

@router.put("/api/internal/mongodb/relation/ad_category/{relation_id}", response_model=AdCategoryResponse)
async def update_ad_category(request: Request, relation_id: str, ad_category: AdCategory, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_category_dict = ad_category.model_dump()
        result = await db.ad_category.update_one({"_id": ObjectId(relation_id)}, {"$set": ad_category_dict})
        if result.modified_count == 1:
            ad_category = await db.ad_category.find_one({"_id": ObjectId(relation_id)})
            ad_category["relation_id"] = str(ad_category["_id"])
            return AdCategoryResponse(**ad_category)
        raise HTTPException(status_code=404, detail="Ad-Category relation not found")

@router.delete("/api/internal/mongodb/relation/ad_category/{relation_id}", response_model=dict)
async def delete_ad_category(request: Request, relation_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        result = await db.ad_category.delete_one({"_id": ObjectId(relation_id)})
        if result.deleted_count == 1:
            return {"message": "Ad-Category relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Ad-Category relation not found")
