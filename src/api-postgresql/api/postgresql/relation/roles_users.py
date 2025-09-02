from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
import asyncpg
from api.auth import get_current_user
from datetime import datetime, UTC

router = APIRouter()

class Role(BaseModel):
    name: str

class RoleResponse(BaseModel):
    role_id: int
    name: str
    created_at: str
    created_by: str

@router.post("/api/internal/postgresql/entity/role", response_model=RoleResponse)
async def create_role(role: Role, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        role_dict = role.model_dump()
        role_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        role_dict["created_by"] = current_user["user_id"]  # Set the creator

        # Insert the role into the database
        role_id = await conn.fetchval(
            "INSERT INTO roles (name, created_at, created_by) VALUES ($1, $2, $3) RETURNING id",
            role_dict["name"],
            role_dict["created_at"],
            role_dict["created_by"]
        )

        role_dict["role_id"] = role_id
        return RoleResponse(**role_dict)

@router.get("/api/internal/postgresql/entity/role/{role_id}", response_model=RoleResponse)
async def get_role(role_id: int, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        role = await conn.fetchrow(
            "SELECT id as role_id, name, created_at, created_by FROM roles WHERE id = $1",
            role_id
        )
        if role:
            return RoleResponse(**role)
        raise HTTPException(status_code=404, detail="Role not found")

@router.put("/api/internal/postgresql/entity/role/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role: Role, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        role_dict = role.model_dump()

        await conn.execute(
            "UPDATE roles SET name = $1 WHERE id = $2",
            role_dict["name"],
            role_id
        )

        role = await conn.fetchrow(
            "SELECT id as role_id, name, created_at, created_by FROM roles WHERE id = $1",
            role_id
        )
        if role:
            return RoleResponse(**role)
        raise HTTPException(status_code=404, detail="Role not found")

@router.delete("/api/internal/postgresql/entity/role/{role_id}", response_model=dict)
async def delete_role(role_id: int, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as conn:
        result = await conn.execute(
            "DELETE FROM roles WHERE id = $1",
            role_id
        )
        if result == "DELETE 1":
            return {"message": "Role deleted successfully"}
        raise HTTPException(status_code=404, detail="Role not found")
