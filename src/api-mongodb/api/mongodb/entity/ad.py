<<<<<<< HEAD
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
=======
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
>>>>>>> e4d0804 (Add CRUD on api-mongodb and api-postgresql)
from config.db import get_db_client
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC
from config.settings import Settings

router = APIRouter()

class Ad(BaseModel):
    user: dict[int, str]
    designation: str
    description: Optional[str]
    categories: str
    images: Optional[List]
    created_at: datetime

class AdResponse(BaseModel):
    ad_id: str
    user: dict[int, str]
    designation: str
    description: Optional[str]
    categories: str
    images: Optional[List]
    created_at: datetime

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

@router.post("/api/internal/mongodb/entity/ad", response_model=AdResponse)
async def create_ad(request: Request, ad: Ad, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_dict = ad.model_dump()
<<<<<<< HEAD
        ad_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        ad_dict["created_by"] = current_user["user_id"]  # Set the creator
=======
        ad_dict["created_at"] = datetime.now(UTC).isoformat() # Set the creation date
>>>>>>> e4d0804 (Add CRUD on api-mongodb and api-postgresql)
        res = await db.ads.insert_one(ad_dict)
        ad_dict["ad_id"] = str(res.inserted_id)
        return AdResponse(**ad_dict)

@router.get("/api/internal/mongodb/entity/ad/{ad_id}", response_model=AdResponse)
async def get_ad(request: Request, ad_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad = await db.ads.find_one({"_id": ObjectId(ad_id)})
        if ad:
            ad["ad_id"] = str(ad["_id"])
            return AdResponse(**ad)
        raise HTTPException(status_code=404, detail="Ad not found")

@router.put("/api/internal/mongodb/entity/ad/{ad_id}", response_model=AdResponse)
async def update_ad(request: Request, ad_id: str, ad: Ad, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_dict = ad.model_dump()
        result = await db.ads.update_one({"_id": ObjectId(ad_id)}, {"$set": ad_dict})
        if result.modified_count == 1:
            ad = await db.ads.find_one({"_id": ObjectId(ad_id)})
            ad["ad_id"] = str(ad["_id"])
            return AdResponse(**ad)
        raise HTTPException(status_code=404, detail="Ad not found")

@router.delete("/api/internal/mongodb/entity/ad/{ad_id}", response_model=dict)
async def delete_ad(request: Request, ad_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        result = await db.ads.delete_one({"_id": ObjectId(ad_id)})
        if result.deleted_count == 1:
            return {"message": "Ad deleted successfully"}
        raise HTTPException(status_code=404, detail="Ad not found")
