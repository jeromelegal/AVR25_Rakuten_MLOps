from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Dict
from api.clients.client_manager import client_manager
from api.auth.token_manager import get_user_data_from_token  # Import de la fonction centralisée

router = APIRouter()

# Modèle de données pour la suppression (seul l'ID de l'utilisateur est nécessaire)
class UserDeleteRequest(BaseModel):
    user_id: str

async def delete_user_mongodb_action(uid: str, token: str):
    # Obtenir le client MongoDB
    mongodb_client = client_manager.get_mongodb_client()
    # Passer le token spécifique à MongoDB
    mongodb_client.set_token(token)  
    # Supprimer l'utilisateur de la base de données MongoDB
    response = mongodb_client.delete_user(uid)
    return {"message": "User deleted successfully from MongoDB", "response": response}


async def delete_user_postgresql_action( uid: str, token: str):
    # Obtenir le client Postgresql
    postgresql_client = client_manager.get_postgresql_client()
    # Passer le token spécifique à Postgresql
    postgresql_client.set_token(token)
    # Supprimer l'utilisateur de la base de données Postgresql
    response = postgresql_client.delete_user(uid)

    return {"message": "User deleted successfully from PostgreSQL", "response": response}

@router.delete("/delete")
async def delete_user(user_data: dict = Depends(get_user_data_from_token)):
    user_id = user_data.get('user_id')
    mongodb_token = user_data.get('tokens', {}).get('mongodb') 
    postgresql_token = user_data.get('tokens', {}).get('postgresql')
    mongodb_uid = user_data.get('uid', {}).get('mongodb')
    postgresql_uid = user_data.get('uid', {}).get('postgresql')

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token data"
        )

    # Appeler les fonctions de suppression d'utilisateur avec les tokens appropriés
    mongodb_response = await delete_user_mongodb_action(mongodb_uid, mongodb_token)
    postgresql_response = await delete_user_postgresql_action(postgresql_uid, postgresql_token)

    return {
        "message": "User deleted successfully from both databases",
        "mongodb_response": mongodb_response,
        "postgresql_response": postgresql_response
    }

# Optionnel : garder les endpoints séparés pour une utilisation indépendante
@router.delete("/delete/mongodb")
async def delete_user_mongodb(user_data: dict = Depends(get_user_data_from_token)):
    mongodb_token = user_data.get('tokens', {}).get('mongodb')
    mongodb_uid = user_data.get('uid', {}).get('mongodb')
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token data"
        )

    # Appeler les deux fonctions de suppression d'utilisateur
    mongodb_response = await delete_user_mongodb_action(mongodb_uid, mongodb_token)
    return {
        "message": "User deleted successfully from mongodb databases",
        "mongodb_response": mongodb_response
    }


@router.delete("/delete/postgresql")
async def delete_user_postgresql(user_data: dict = Depends(get_user_data_from_token)):
    postgresql_token = user_data.get('tokens', {}).get('postgresql')    
    postgresql_uid = user_data.get('uid', {}).get('postgresql')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token data"
        )

    # Appeler les deux fonctions de suppression d'utilisateur
    postgresql_response = await delete_user_postgresql_action(postgresql_uid,postgresql_token)

    return {
        "message": "User deleted successfully from postgresql databases",
        "postgresql_response": postgresql_response
    }
