from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from datetime import datetime
from config.settings import Settings
from api.auth import get_current_user
from typing import Dict, List

router = APIRouter()

class Category(BaseModel):
    code: int
    label: str

class CategoriesResponse(BaseModel):
    categories: List[Category]

@router.get("/api/internal/postgresql/entity/categories", response_model=CategoriesResponse)
async def get_category(current_user: Dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    
    #TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        rows = await conn.fetch("SELECT code, label FROM categories ORDER BY code")
        categories = [Category(**dict(r)).model_dump() for r in rows]
        if categories:
            return CategoriesResponse(categories=categories)

        raise HTTPException(status_code=404, detail="Categories not found")
    