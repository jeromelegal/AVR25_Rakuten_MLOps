from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List
from config.db import get_db_client
from config.settings import Settings
from api.auth import get_current_user
import asyncpg

router = APIRouter()

class AdCatRelation(BaseModel):
    ad_id: int
    cat_id: int

class AdCatResponse(BaseModel):
    ad_id: int
    cat_id: int

@router.post("/api/internal/postgresql/relation/ads_cats", response_model=AdCatResponse)
async def create_ad_cat(request: Request, relation: AdCatRelation, current_user: dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    relation_dict = relation.model_dump()
    async with get_db_client(settings) as conn:
        try:
            # Insertion dans la table ads_cats
            await conn.fetchval(
                "INSERT INTO ads_cats (ad_id, cat_id) VALUES ($1, $2) ON CONFLICT (ad_id, cat_id) DO NOTHING RETURNING ad_id, cat_id",
                relation_dict["ad_id"],
                relation_dict["cat_id"]
            )
            return AdCatResponse(**relation_dict)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Ad-Cat relation already exists")


@router.get("/api/internal/postgresql/relation/ads_cats/{ad_id}", response_model=List[AdCatResponse])
async def get_ad_cat(ad_id: int=None, cat_id: int=None, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        if ad_id is not None and cat_id is not None:
            relation = await conn.fetchrow(
                "SELECT ad_id, cat_id FROM ads_cats WHERE ad_id = $1 AND cat_id = $2",
                ad_id, cat_id
            )
            if relation:
                return [AdCatResponse(**relation)]
            else:
                raise HTTPException(status_code=404, detail="Ad-Cat relation not found")
        else:
            # Récupérer toutes les relations pour un utilisateur ou une annonce spécifique, ou toutes
            query = "SELECT ad_id, cat_id FROM ads_cats"
            params = []
            if ad_id is not None:
                query += " WHERE ad_id = $1"
                params.append(ad_id)
            elif cat_id is not None:
                query += " WHERE ad_id = $1"
                params.append(cat_id)

            relations = await conn.fetch(query, *params)
            return [AdCatResponse(**relation) for relation in relations]

@router.delete("/api/internal/postgresql/relation/ads_cats/{ad_id}", response_model=Dict)
async def delete_ad_cat(ad_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM ads_cats WHERE ad_id = $1 RETURNING ad_id",
            ad_id
        )
        if result:
            return {"message": "Ad-Cat relation deleted successfully"}
        raise HTTPException(status_code=404, detail="User-Ad relation not found")