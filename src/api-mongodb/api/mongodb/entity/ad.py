from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from config.db import get_db_client
from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from datetime import datetime, timezone
from bson import ObjectId
from config.settings import Settings

router = APIRouter()

class User(BaseModel):
    id: int
    username: str

class Images(BaseModel):
    image_uuid: str
    bucket_path: str

class Ad(BaseModel):
    ad_id: int
    user: User
    designation: str
    description: Optional[str] = None
    category: str
    images: Optional[List[Images]] = None
    created_at: datetime

class AdResponse(BaseModel):
    id: str
    ad_id: int
    user: User
    designation: str
    description: Optional[str] = None
    category: str
    images: Optional[List[Images]] = None
    created_at: datetime

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

@router.post("/api/internal/mongodb/entity/ad", response_model=AdResponse)
async def create_ad(request: Request, ad:Ad, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_dict = ad.model_dump()
        # Need datetime on MongoDB
        created_at = ad_dict.get("created_at")
        if isinstance(created_at, str):
            ad_dict["created_at"] = datetime.fromisoformat(
                created_at.replace("Z", "+00:00")).astimezone(timezone.utc)

        response = await db.ads.insert_one(ad_dict)
        ad_dict["id"] = str(response.inserted_id)
        return AdResponse(**ad_dict)

@router.get("/api/internal/mongodb/entity/ad/{id}", response_model=AdResponse)
async def get_ad(request: Request, id: str, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    # if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail=f"Not enough permissions {current_user["user_id"]} != {user_id}")
    async with get_db_client(settings) as db:
        ad = await db.ads.find_one({"_id": ObjectId(id)})
        if ad:
            ad["id"] = str(ad["_id"])
            return AdResponse(**ad)
    raise HTTPException(status_code=404, detail="Ad not found")

@router.put("/api/internal/mongodb/entity/ad/{id}", response_model=AdResponse)
async def update_ad(request: Request, id: str, ad: Ad, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        ad_dict = ad.model_dump()
        result = await db.ads.update_one({"_id": ObjectId(id)}, {"$set": ad_dict})
        if result.modified_count == 1:
            ad = await db.ads.find_one({"_id": ObjectId(id)})
            ad["id"] = str(ad["_id"])
            return AdResponse(**ad)
        raise HTTPException(status_code=404, detail="Ad not found")

@router.delete("/api/internal/mongodb/entity/ad/{id}", response_model=Dict)
async def delete_ad(request: Request, id: str, current_user: Dict = Depends(get_current_user)):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        result = await db.ads.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 1:
            return {"message": "Ad deleted successfully"}
        raise HTTPException(status_code=404, detail="Ad not found")