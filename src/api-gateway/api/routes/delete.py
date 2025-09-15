from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Dict
from api.clients.client_manager import client_manager
from api.auth.token_manager import get_user_data_from_token  # Import de la fonction centralisée

router = APIRouter()

# Modèle de données pour la suppression (seul l'ID de l'utilisateur est nécessaire)
class UserDeleteRequest(BaseModel):
    user_id: str

async def delete_user_mongodb_action(token: str, uid: str):
    # Obtenir le client MongoDB
    mongodb_client = client_manager.get_mongodb_client()
    # Supprimer l'utilisateur de la base de données MongoDB
    response = mongodb_client.delete_user(token=token, user_id=uid)
    return {"message": "User deleted successfully from MongoDB", "response": response}


async def delete_user_postgresql_action(token: str, uid: str):
    # Obtenir le client Postgresql
    postgresql_client = client_manager.get_postgresql_client()
    # Supprimer l'utilisateur de la base de données Postgresql
    response = postgresql_client.delete_user(token=token, user_id=uid)
    return {"message": "User deleted successfully from PostgreSQL", "response": response}

@router.delete("/delete")
async def delete_user(user_data: dict = Depends(get_user_data_from_token)):

    user_id = user_data.get('user_id')
    mongodb_token = user_data.get('tokens', {}).get('mongodb') 
    postgresql_token = user_data.get('tokens', {}).get('postgresql')
    mongodb_uid = user_data.get('uids', {}).get('mongodb')
    postgresql_uid = user_data.get('uids', {}).get('postgresql')

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID not found in token data"
        )

    # Appeler les fonctions de suppression d'utilisateur avec les tokens appropriés
    mongodb_response = await delete_user_mongodb_action(token=mongodb_token, uid=mongodb_uid)
    postgresql_response = await delete_user_postgresql_action(token=postgresql_token, uid=postgresql_uid)

    return {
        "message": "User deleted successfully from both databases",
        "mongodb_response": mongodb_response,
        "postgresql_response": postgresql_response
    }
