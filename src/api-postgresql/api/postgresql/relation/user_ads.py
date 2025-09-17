from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
import asyncpg
from api.auth import get_current_user


router = APIRouter()

class UserAd(BaseModel):
    user_id: str
    ad_id: str

class UserAdResponse(BaseModel):
    user_id: str
    ad_id: str

class GetAdUserResponse(BaseModel):
    user_id: str

@router.post("/api/internal/postgresql/relation/user_ad", response_model=UserAdResponse)
async def create_user_ad(user_ad: UserAd, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("user_ads", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        user_ad_dict = user_ad.model_dump()

        # Insert the user_ad into the database
        relation = await conn.fetchval(
            "INSERT INTO user_ads (user_id, ad_id) VALUES ($1, $2) ON CONFLICT (user_id, ad_id) DO NOTHING RETURNING user_id, ad_id",
            user_ad_dict["user_id"],
            user_ad_dict["ad_id"]
        )
        if relation is None:
            # Already exists
            raise HTTPException(status_code=409, detail="Relation already exists")
        return UserAdResponse(**user_ad_dict)

@router.get("/api/internal/postgresql/relation/user_ad/{user_id}", response_model=List[UserAdResponse])
async def get_user_ads(user_id: int, current_user: dict = Depends(get_current_user)):
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        relations = await conn.fetchrow(
            "SELECT user_id, ad_id FROM user_ads WHERE user_id = $1",
            user_id
        )
        if relations:
            return [UserAdResponse(user_id=r["user_id"], ad_id=r["ad_id"]) for r in relations]
        raise HTTPException(status_code=404, detail=f"Relations from user_id:{user_id} not found")
    
@router.get("/api/internal/postgresql/relation/ad_user/{ad_id}", response_model=GetAdUserResponse)
async def get_ad_user(ad_id: int, current_user: dict = Depends(get_current_user)):
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        relation = await conn.fetchrow(
            "SELECT user_id FROM user_ads WHERE ad_id = $1",
            ad_id
        )
        if relation:
            return GetAdUserResponse(**relation)
        raise HTTPException(status_code=404, detail="relation not found")

@router.delete("/api/internal/postgresql/relation/user_ad/{user_id}/{ad_id}", response_model=dict)
async def delete_user_ad(user_id: int, ad_id: int, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("user_ads", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        result = await conn.execute(
            "DELETE FROM user_ads WHERE (user_id, ad_id) VALUES ($1, $2)",
            user_id, ad_id
        )
        if result == "DELETE 1":
            return {"message": "Relation deleted successfully"}
        raise HTTPException(status_code=404, detail=f"Relation user_id:{user_id} / ad_id:{ad_id} not found")
