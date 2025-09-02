from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user
from bson import ObjectId
from datetime import datetime, UTC

router = APIRouter()

class Role(BaseModel):
    name: str

class RoleResponse(BaseModel):
    role_id: str
    name: str
    created_at: str
    created_by: str

@router.post("/api/internal/mongodb/entity/role", response_model=RoleResponse)
async def create_role(role: Role, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        role_dict = role.model_dump()
        role_dict["created_at"] = datetime.now(UTC).isoformat()  # Set the creation date
        role_dict["created_by"] = current_user["user_id"]  # Set the creator
        result = await db.roles.insert_one(role_dict)
        role_dict["role_id"] = str(result.inserted_id)
        return RoleResponse(**role_dict)

@router.get("/api/internal/mongodb/entity/role/{role_id}", response_model=RoleResponse)
async def get_role(role_id: str, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        role = await db.roles.find_one({"_id": ObjectId(role_id)})
        if role:
            role["role_id"] = str(role["_id"])
            return RoleResponse(**role)
        raise HTTPException(status_code=404, detail="Role not found")

@router.put("/api/internal/mongodb/entity/role/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, role: Role, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        role_dict = role.model_dump()
        result = await db.roles.update_one({"_id": ObjectId(role_id)}, {"$set": role_dict})
        if result.modified_count == 1:
            role = await db.roles.find_one({"_id": ObjectId(role_id)})
            role["role_id"] = str(role["_id"])
            return RoleResponse(**role)
        raise HTTPException(status_code=404, detail="Role not found")

@router.delete("/api/internal/mongodb/entity/role/{role_id}", response_model=dict)
async def delete_role(role_id: str, current_user: dict = Depends(get_current_user)):
    if "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    async with get_db_client() as db:
        result = await db.roles.delete_one({"_id": ObjectId(role_id)})
        if result.deleted_count == 1:
            return {"message": "Role deleted successfully"}
        raise HTTPException(status_code=404, detail="Role not found")
