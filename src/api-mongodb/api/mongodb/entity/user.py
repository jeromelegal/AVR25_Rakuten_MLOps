from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from config.db import get_db_client
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from api.auth import get_current_user, hash_password, create_access_token
from bson import ObjectId
from datetime import datetime, UTC, timedelta
from config.settings import Settings

router = APIRouter()

class User(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    created_at: str
    created_by: str

class UserUpdateResponse(UserResponse):
    access_token: str
    token_type: str

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

@router.post("/api/internal/mongodb/entity/user", response_model=UserResponse)
async def create_user(request: Request, user: User):
    settings = get_settings(request)
    async with get_db_client(settings) as db:
        user_dict = user.model_dump()
        user_dict["password"] = hash_password(user_dict["password"])
        user_dict["created_at"] = datetime.now(UTC).isoformat()
        user_dict["created_by"] = "system"
        result = await db.users.insert_one(user_dict)
        user_dict["user_id"] = str(result.inserted_id)
        return UserResponse(**user_dict)

@router.get("/api/internal/mongodb/entity/user/{user_id}", response_model=UserResponse)
async def get_user(request: Request, user_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail=f"Not enough permissions {current_user["user_id"]} != {user_id}")
    async with get_db_client(settings) as db:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["user_id"] = str(user["_id"])
            return UserResponse(**user)
        raise HTTPException(status_code=404, detail="User not found")

@router.put("/api/internal/mongodb/entity/user/{user_id}", response_model=UserUpdateResponse)
async def update_user(request: Request, user_id: str, user: User, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)

    if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail=f"Not enough permissions {current_user["user_id"]} != {user_id}")

    async with get_db_client(settings) as db:
        # Convertir l'objet User en dictionnaire
        user_dict = user.model_dump()

        # Hasher le mot de passe
        user_dict["password"] = hash_password(user_dict["password"])

        # S'assurer que '_id' n'est pas dans le dictionnaire de mise à jour
        if '_id' in user_dict:
            del user_dict['_id']

        # Mettre à jour l'utilisateur dans la base de données
        result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": user_dict})

        if result.modified_count == 1:
            # Récupérer l'utilisateur mis à jour pour le retourner dans la réponse
            user = await db.users.find_one({"_id": ObjectId(user_id)})
            user["user_id"] = str(user["_id"])
            # Créer un nouveau token d'accès après la mise à jour de l'utilisateur
            data = {"user_id": user["user_id"], "sub": user["username"], 'scope': 'internal'}
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data=data, settings=settings, expires_delta=access_token_expires
            )

            # Retourner les détails de l'utilisateur mis à jour et le nouveau token d'accès
            response_data = UserResponse(**user).model_dump()
            response_data["access_token"] = access_token
            response_data["token_type"] = "bearer"
            return response_data

        raise HTTPException(status_code=404, detail="User not found")

@router.delete("/api/internal/mongodb/entity/user/{user_id}", response_model=dict)
async def delete_user(request: Request, user_id: str, current_user: dict = Depends(get_current_user)):
    settings = get_settings(request)
    if current_user["user_id"] != user_id and "superadmin" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail=f"Not enough permissions {current_user["user_id"]} != {user_id}")
    async with get_db_client(settings) as db:
        result = await db.users.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 1:
            return {"message": "User deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")
