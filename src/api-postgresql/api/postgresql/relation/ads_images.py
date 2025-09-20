from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List
from config.db import get_db_client
from config.settings import Settings
from api.auth import get_current_user
import asyncpg


router = APIRouter()

class AdImageRelation(BaseModel):
    ad_id: int
    image_id: int

class AdImageResponse(BaseModel):
    ad_id: int
    image_id: int

@router.post("/api/internal/postgresql/relation/ads_images", response_model=AdImageResponse)
async def create_ad_image(request: Request, relation: AdImageRelation, current_user: dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    relation_dict = relation.model_dump()
    async with get_db_client(settings) as conn:
        try:
            # Insertion dans la table ads_images
            await conn.execute(
                "INSERT INTO ads_images (ad_id, image_id) VALUES ($1, $2) ON CONFLICT (ad_id, image_id) DO NOTHING RETURNING ad_id, image_id",
                relation_dict["ad_id"],
                relation_dict["image_id"]
            )
            return AdImageResponse(**relation_dict)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Ad-Image relation already exists")


@router.get("/api/internal/postgresql/relation/ads_images", response_model=List[AdImageResponse])
async def get_ad_image(ad_id: int=None, image_id: int=None, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        if ad_id is not None and image_id is not None:
            relation = await conn.fetchrow(
                "SELECT ad_id, image_id FROM ads_images WHERE ad_id = $1 AND image_id = $2",
                ad_id, image_id
            )
            if relation:
                return [AdImageResponse(**relation)]
            else:
                raise HTTPException(status_code=404, detail="Ad-Image relation not found")
        else:
            # Récupérer toutes les relations pour un utilisateur ou une annonce spécifique, ou toutes
            query = "SELECT ad_id, image_id FROM ads_images"
            params = []
            if ad_id is not None:
                query += " WHERE user_id = $1"
                params.append(ad_id)
            elif image_id is not None:
                query += " WHERE ad_id = $1"
                params.append(image_id)

            relations = await conn.fetch(query, *params)
            return [AdImageResponse(**relation) for relation in relations]

@router.delete("/api/internal/postgresql/relation/ads_images", response_model=Dict)
async def delete_ad_image(ad_id: int, image_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM ads_images WHERE ad_id = $1 AND image_id = $2 RETURNING ad_id, image_id",
            ad_id, image_id
        )
        if result:
            return {"message": "Ad-Image relation deleted successfully"}
        raise HTTPException(status_code=404, detail="User-Ad relation not found")