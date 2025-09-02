from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from api.clients.client_manager import client_manager  # Mise à jour de l'import

router = APIRouter()

# Modèle de données pour l'utilisateur
class User(BaseModel):
    username: str
    email: str
    password: str

@router.post("/signup/mongodb")
async def signup_mongodb(user: User):
    # Obtenir le client MongoDB
    mongodb_client = client_manager.get_mongodb_client()

    # Enregistrer l'utilisateur dans la base de données sans hacher le mot de passe
    user_data = {
        "username": user.username,
        "email": user.email,
        "password": user.password  # Le mot de passe est envoyé tel quel
    }

    # Envoyer les données de l'utilisateur à l'API MongoDB
    response = mongodb_client.create_user(user_data)

    return {"message": "User created successfully", "user_id": response.get("user_id")}

@router.post("/signup/postgresql")
async def signup_postgresql(user: User):
    # Obtenir le client PostgreSQL
    postgresql_client = client_manager.get_postgresql_client()

    # Enregistrer l'utilisateur dans la base de données sans hacher le mot de passe
    user_data = {
        "username": user.username,
        "email": user.email,
        "password": user.password  # Le mot de passe est envoyé tel quel
    }

    # Envoyer les données de l'utilisateur à l'API PostgreSQL
    response = postgresql_client.create_user(user_data)

    return {"message": "User created successfully", "user_id": response.get("user_id")}



@router.post("/signup")
async def signup(user: User):
    # Appeler les deux fonctions de création d'utilisateur
    mongodb_response = await signup_mongodb(user)
    postgresql_response = await signup_postgresql(user)

    return {
        "message": "User created successfully",
        "mongodb_response": mongodb_response,
        "postgresql_response": postgresql_response
    }