from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
import asyncpg
from api.auth import get_current_user


router = APIRouter()

class AdImage(BaseModel):
    ad_id: str
    image_id: str

class AdImageResponse(BaseModel):
    ad_id: str
    image_id: str

class GetImageAdResponse(BaseModel):
    ad_id: str

@router.post("/api/internal/postgresql/relation/user_ad", response_model=AdImageResponse)
async def create_user_ad(user_ad: AdImage, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("ad_images", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        user_ad_dict = user_ad.model_dump()

        # Insert the user_ad into the database
        relation = await conn.fetchval(
            "INSERT INTO ad_images (ad_id, image_id) VALUES ($1, $2) ON CONFLICT (ad_id, image_id) DO NOTHING RETURNING ad_id, image_id",
            user_ad_dict["ad_id"],
            user_ad_dict["image_id"]
        )
        if relation is None:
            # Already exists
            raise HTTPException(status_code=409, detail="Relation already exists")
        return AdImageResponse(**user_ad_dict)

@router.get("/api/internal/postgresql/relation/user_ad/{ad_id}", response_model=List[AdImageResponse])
async def get_ad_images(ad_id: int, current_user: dict = Depends(get_current_user)):
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        relations = await conn.fetchrow(
            "SELECT ad_id, image_id FROM ad_images WHERE ad_id = $1",
            ad_id
        )
        if relations:
            return [AdImageResponse(ad_id=r["ad_id"], image_id=r["image_id"]) for r in relations]
        raise HTTPException(status_code=404, detail=f"Relations from ad_id:{ad_id} not found")
    
@router.get("/api/internal/postgresql/relation/image_ad/{image_id}", response_model=GetImageAdResponse)
async def get_image_ad(image_id: int, current_user: dict = Depends(get_current_user)):
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        relation = await conn.fetchrow(
            "SELECT ad_id FROM ad_images WHERE image_id = $1",
            image_id
        )
        if relation:
            return GetImageAdResponse(**relation)
        raise HTTPException(status_code=404, detail="relation not found")

@router.delete("/api/internal/postgresql/relation/user_ad/{ad_id}/{image_id}", response_model=dict)
async def delete_user_ad(ad_id: int, image_id: int, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("ad_images", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        result = await conn.execute(
            "DELETE FROM ad_images WHERE (ad_id, image_id) VALUES ($1, $2)",
            ad_id, image_id
        )
        if result == "DELETE 1":
            return {"message": "Relation deleted successfully"}
        raise HTTPException(status_code=404, detail=f"Relation ad_id:{ad_id} / image_id:{image_id} not found")
