from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user, hash_password, create_access_token
from bson import ObjectId
from datetime import datetime, UTC, timedelta
from config.settings import Settings

router = APIRouter()

class User(BaseModel):
    id: int
    username: str

class Ad(BaseModel):
    user: User
    designation: str
    description: Optional[str] = None
    category: str
    images: Optional[List[str]] = None
    created_at: str

class AdResponse(BaseModel):
    ad_id: str
    user: User
    designation: str
    description: Optional[str] = None
    category: str
    images: Optional[List[str]] = None
    created_at: str

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

@router.post("/api/internal/mongodb/entity/ad", response_model=AdResponse)
async def create_ad(request: Request, ad:Ad, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_dict = ad.model_dump()
        ad_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        ad_dict["created_by"] = current_user["user_id"]  # Set the creator

        res = await db.ads.insert_one(ad_dict)
        ad_dict["ad_id"] = str(res.inserted_id)
        return AdResponse(**ad_dict)

@router.get("/api/internal/mongodb/entity/ad/{ad_id}", response_model=AdResponse)
async def get_ad(request: Request, ad_id: str, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    # if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail=f"Not enough permissions {current_user["user_id"]} != {user_id}")
    async with get_db_client(settings) as db:
        ad = await db.ads.find_one({"_id": ObjectId(ad_id)})
        if ad:
            ad["ad_id"] = str(ad["_id"])
            return AdResponse(**ad)
        raise HTTPException(status_code=404, detail="Ad not found")

@router.put("/api/internal/mongodb/entity/ad/{ad_id}", response_model=AdResponse)
async def update_ad(request: Request, ad_id: str, ad: Ad, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_dict = ad.model_dump()
        result = await db.ads.update_one({"_id": ObjectId(ad_id)}, {"$set": ad_dict})
        if result.modified_count == 1:
            ad = await db.ads.find_one({"_id": ObjectId(ad_id)})
            ad["ad_id"] = str(ad["_id"])
            return AdResponse(**ad)
        raise HTTPException(status_code=404, detail="Ad not found")

@router.delete("/api/internal/mongodb/entity/ad/{ad_id}", response_model=Dict)
async def delete_ad(request: Request, ad_id: str, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        result = await db.ads.delete_one({"_id": ObjectId(ad_id)})
        if result.deleted_count == 1:
            return {"message": "Ad deleted successfully"}
        raise HTTPException(status_code=404, detail="Ad not found")