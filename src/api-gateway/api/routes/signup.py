from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Dict
from api.clients.client_manager import client_manager
from api.auth.token_manager import get_user_data_from_token, create_meta_token, create_signed_token
from datetime import datetime, timedelta, timezone
from jose import jwt
import secrets

router = APIRouter()

class User(BaseModel):
    username: str
    email: str
    password: str

async def signup_mongodb_action(user: User):
    mongodb_client = client_manager.get_mongodb_client()
    user_data = {
        "username": user.username,
        "email": user.email,
        "password": user.password
    }
    response = mongodb_client.create_user(user_data)
    return {"message": "User created successfully in MongoDB", "user_id": response.get("user_id")}

async def signup_postgresql_action(user: User):
    postgresql_client = client_manager.get_postgresql_client()
    user_data = {
        "username": user.username,
        "email": user.email,
        "password": user.password
    }
    response = postgresql_client.create_user(user_data)
    return {"message": "User created successfully in PostgreSQL", "user_id": response.get("user_id")}

@router.post("/signup")
async def signup(user: User):
    # Effectuer les inscriptions dans MongoDB et PostgreSQL
    mongodb_response = await signup_mongodb_action(user)
    postgresql_response = await signup_postgresql_action(user)

    # Récupérer le user_id généré (ici, on suppose que les deux bases de données génèrent le même user_id pour simplification)
    user_id = mongodb_response.get("user_id")

    # Créer un meta token pour l'utilisateur avec une clé publique
    user_data = {
        "username": user.username,
        "email": user.email,
        "user_id": user_id
    }

    return {
        "message": "User created successfully",
    }

@router.post("/signup/mongodb")
async def signup_mongodb_endpoint(user: User):
    return await signup_mongodb_action(user)

@router.post("/signup/postgresql")
async def signup_postgresql_endpoint(user: User):
    return await signup_postgresql_action(user)
