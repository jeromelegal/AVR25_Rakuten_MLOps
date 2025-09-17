from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
import asyncpg
from api.auth import get_current_user


router = APIRouter()

class AdCat(BaseModel):
    ad_id: str
    cat_id: str

class AdCatResponse(BaseModel):
    ad_id: str
    cat_id: str

class GetCatAdResponse(BaseModel):
    ad_id: str

@router.post("/api/internal/postgresql/relation/user_ad", response_model=AdCatResponse)
async def create_user_ad(user_ad: AdCat, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("ad_cats", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        user_ad_dict = user_ad.model_dump()

        # Insert the user_ad into the database
        relation = await conn.fetchval(
            "INSERT INTO ad_cats (ad_id, cat_id) VALUES ($1, $2) ON CONFLICT (ad_id, cat_id) DO NOTHING RETURNING ad_id, cat_id",
            user_ad_dict["ad_id"],
            user_ad_dict["cat_id"]
        )
        if relation is None:
            # Already exists
            raise HTTPException(status_code=409, detail="Relation already exists")
        return AdCatResponse(**user_ad_dict)

@router.get("/api/internal/postgresql/relation/user_ad/{ad_id}", response_model=List[AdCatResponse])
async def get_ad_cats(ad_id: int, current_user: dict = Depends(get_current_user)):
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        relations = await conn.fetchrow(
            "SELECT ad_id, cat_id FROM ad_cats WHERE ad_id = $1",
            ad_id
        )
        if relations:
            return [AdCatResponse(ad_id=r["ad_id"], cat_id=r["cat_id"]) for r in relations]
        raise HTTPException(status_code=404, detail=f"Relations from ad_id:{ad_id} not found")
    
@router.get("/api/internal/postgresql/relation/cat_ad/{cat_id}", response_model=GetCatAdResponse)
async def get_cat_ad(cat_id: int, current_user: dict = Depends(get_current_user)):
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        relation = await conn.fetchrow(
            "SELECT ad_id FROM ad_cats WHERE cat_id = $1",
            cat_id
        )
        if relation:
            return GetCatAdResponse(**relation)
        raise HTTPException(status_code=404, detail="relation not found")

@router.delete("/api/internal/postgresql/relation/user_ad/{ad_id}/{cat_id}", response_model=dict)
async def delete_user_ad(ad_id: int, cat_id: int, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("ad_cats", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        result = await conn.execute(
            "DELETE FROM ad_cats WHERE (ad_id, cat_id) VALUES ($1, $2)",
            ad_id, cat_id
        )
        if result == "DELETE 1":
            return {"message": "Relation deleted successfully"}
        raise HTTPException(status_code=404, detail=f"Relation ad_id:{ad_id} / cat_id:{cat_id} not found")
