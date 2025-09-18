from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List
from config.db import get_db_client
from config.settings import Settings
from api.auth import get_current_user
import asyncpg

router = APIRouter()

class RoleUserRelation(BaseModel):
    role_id: int
    user_id: int

class RoleUserResponse(BaseModel):
    user_id: int
    role_id: int

@router.post("/api/internal/postgresql/relation/role_user", response_model=RoleUserResponse)
async def create_role_user(request: Request, relation: RoleUserRelation, current_user: dict = Depends(get_current_user)):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    relation_dict = relation.model_dump()
    async with get_db_client(settings) as conn:
        try:
            # Insertion dans la table user_roles
            await conn.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                relation_dict["user_id"],
                relation_dict["role_id"]
            )
            return RoleUserResponse(**relation_dict)
        except asyncpg.UniqueViolationError:
            raise HTTPException(status_code=400, detail="Role-User relation already exists")

@router.get("/api/internal/postgresql/relation/role_user", response_model=List[RoleUserResponse])
async def get_role_user(user_id: int = None, role_id: int = None, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        if user_id is not None and role_id is not None:
            relation = await conn.fetchrow(
                "SELECT user_id, role_id FROM user_roles WHERE user_id = $1 AND role_id = $2",
                user_id, role_id
            )
            if relation:
                return [RoleUserResponse(**relation)]
            else:
                raise HTTPException(status_code=404, detail="Role-User relation not found")
        else:
            # Récupérer toutes les relations pour un utilisateur ou un rôle spécifique, ou toutes
            query = "SELECT user_id, role_id FROM user_roles"
            params = []
            if user_id is not None:
                query += " WHERE user_id = $1"
                params.append(user_id)
            elif role_id is not None:
                query += " WHERE role_id = $1"
                params.append(role_id)

            relations = await conn.fetch(query, *params)
            return [RoleUserResponse(**relation) for relation in relations]

@router.delete("/api/internal/postgresql/relation/role_user", response_model=dict)
async def delete_role_user(user_id: int, role_id: int, current_user: dict = Depends(get_current_user), request: Request = None):
    settings: Settings = request.app.state.settings
    # TODO SETUP ROLE
    # if "superadmin" not in current_user.get("roles", []):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    async with get_db_client(settings) as conn:
        result = await conn.execute(
            "DELETE FROM user_roles WHERE user_id = $1 AND role_id = $2 RETURNING user_id, role_id",
            user_id, role_id
        )
        if result:
            return {"message": "Role-User relation deleted successfully"}
        raise HTTPException(status_code=404, detail="Role-User relation not found")

