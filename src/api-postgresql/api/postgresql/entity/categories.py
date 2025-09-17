from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import Optional
from datetime import datetime, timezone, timedelta, UTC
from config.settings import Settings
from api.auth import get_current_user, hash_password, create_access_token
import asyncpg
from typing import Dict

router = APIRouter()

class Category(BaseModel):
    code: str
    label: str

class CategoryResponse(BaseModel):
    id: int
    code: str
    label: str
    created_at: datetime
    created_by: int

@router.post("/api/internal/postgresql/entity/category", response_model=CategoryResponse)
async def create_category(request: Request, data: Category):
    settings: Settings = request.app.state.settings
    data_dict = data.model_dump()
    data_dict["created_at"] = datetime.now(timezone.utc).replace(tzinfo=None)
    data_dict["created_by"] = 0  # Assuming the system creates the user

    async with get_db_client(settings) as conn:
        category_id = await conn.fetchval(
            "INSERT INTO ads (designation, label, created_at, created_by) VALUES ($1, $2, $3, $4) RETURNING id",
            data_dict["code"],
            data_dict["label"],
            data_dict["created_at"],
            data_dict["created_by"]
        )
        data_dict["id"] = str(category_id)
        return CategoryResponse(**data_dict)

@router.get("/api/internal/postgresql/entity/category/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # if current_user["id"] != user_id and "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        category = await conn.fetchrow(
            "SELECT id as category_id, code, label, created_at, created_by FROM categories WHERE id = $1",
            int(category_id)
        )
        if category:
            return CategoryResponse(**category)
        raise HTTPException(status_code=404, detail="Category not found")

@router.put("/api/internal/postgresql/entity/category/{category_id}", response_model=dict)
async def update_category(category_id: int, data: Category, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # print("\n"*20)
    # print(f"{current_user["id"]} != {user_id}")
    # print("\n"*20)
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    data_dict = data.model_dump()
    async with get_db_client(settings) as conn:
        await conn.execute(
            "UPDATE categories SET code = $1, label = $2 WHERE id = $3",
            data_dict["code"],
            data_dict["label"],
            category_id
        )
        updated_ad = await conn.fetchrow(
            "SELECT id as category_id, code, label, created_at, created_by "
            "FROM categories WHERE id = $1",
            category_id
        )
        if updated_ad:
            if updated_ad["code"] == data_dict["code"]:
                if updated_ad["label"] == data_dict["label"]:
                    return {"message": "Category updated successfully"}
                raise HTTPException(status_code=500, detail="Error during update 'label'")
            raise HTTPException(status_code=500, detail="Error during update 'code'")
        raise HTTPException(status_code=404, detail="Category not found to update")

@router.delete("/api/internal/postgresql/entity/category/{category_id}", response_model=dict)
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # print("\n"*20)
    # print(f"{current_user["id"]} != {user_id}")
    # print("\n"*20)
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM categories WHERE id = $1",
            int(category_id)
        )
        if result == "DELETE 1":
            return {"message": "Category deleted successfully"}
        raise HTTPException(status_code=404, detail="Category not found")



