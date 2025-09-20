from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List
from config.db import get_db_client
from config.settings import Settings
from api.auth import get_current_user
import asyncpg


router = APIRouter()

class UserAdRelation(BaseModel):
    user_id: int
    ad_id: int

class UserAdResponse(BaseModel):
    user_id: int
    ad_id: int

@router.post("/api/internal/postgresql/relation/users_ads", response_model=UserAdResponse)
async def create_user_ad(request: Request, relation: UserAdRelation, current_user: dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    relation_dict = relation.model_dump()
    async with get_db_client(settings) as conn:
        try:
            # Insertion dans la table users_ads
            await conn.execute(
                "INSERT INTO users_ads (user_id, ad_id) VALUES ($1, $2) ON CONFLICT (user_id, ad_id) DO NOTHING RETURNING user_id, ad_id",
                relation_dict["user_id"],
                relation_dict["ad_id"]
            )
            return UserAdResponse(**relation_dict)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="User-Ad relation already exists")

@router.get("/api/internal/postgresql/relation/users_ads", response_model=List[UserAdResponse])
async def get_user_ad(user_id: int=None, ad_id: int=None, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        if user_id is not None and ad_id is not None:
            relation = await conn.fetchrow(
                "SELECT user_id, ad_id FROM users_ads WHERE user_id = $1 AND ad_id = $2",
                user_id, ad_id
            )
            if relation:
                return [UserAdResponse(**relation)]
            else:
                raise HTTPException(status_code=404, detail="User-Ad relation not found")
        else:
            # Récupérer toutes les relations pour un utilisateur ou une annonce spécifique, ou toutes
            query = "SELECT user_id, ad_id FROM users_ads"
            params = []
            if user_id is not None:
                query += " WHERE user_id = $1"
                params.append(user_id)
            elif ad_id is not None:
                query += " WHERE ad_id = $1"
                params.append(ad_id)

            relations = await conn.fetch(query, *params)
            return [UserAdResponse(**relation) for relation in relations]

@router.delete("/api/internal/postgresql/relation/users_ads", response_model=Dict)
async def delete_user_ad(user_id: int, ad_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM users_ads WHERE user_id = $1 AND ad_id = $2 RETURNING user_id, ad_id",
            user_id, ad_id
        )
        if result:
            return {"message": "User-Ad relation deleted successfully"}
        raise HTTPException(status_code=404, detail="User-Ad relation not found")