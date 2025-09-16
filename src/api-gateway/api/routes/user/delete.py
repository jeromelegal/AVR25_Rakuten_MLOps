import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from typing import Dict
from api.auth.clients.manager import ClientManager, create_client_manager
from config.settings import Settings
from api.auth.token.manager import TokenManager, create_token_manager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

def get_client_manager(request: Request) -> ClientManager:
    settings = get_settings(request)
    return create_client_manager(settings)

def get_token_manager(request: Request) -> TokenManager:
    settings = get_settings(request)
    return create_token_manager(settings)

def get_user_data_from_token(
    token_manager: TokenManager = Depends(get_token_manager),
    authorization: str = Header(...)
) -> Dict:
    """Récupère les données utilisateur à partir du token JWT."""
    logger.info("Extracting user data from token...")
    return token_manager.get_user_data_from_token(authorization)

@router.delete("/delete")
async def delete_user(
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
    token_manager: TokenManager = Depends(get_token_manager)
):
    logger.info("Starting deletion of user from all databases...")
    try:
        user_id = user_data.get('user_id')
        mongodb_token = user_data.get('tokens', {}).get('mongodb')
        postgresql_token = user_data.get('tokens', {}).get('postgresql')
        mongodb_uid = user_data.get('uids', {}).get('mongodb')
        postgresql_uid = user_data.get('uids', {}).get('postgresql')

        if not user_id:
            logger.error("User ID not found in token data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID not found in token data"
            )

        mongodb_client = client_manager.get_client("mongodb")
        postgresql_client = client_manager.get_client("postgresql")

        logger.info("Deleting user from MongoDB...")
        mongodb_response = mongodb_client.delete_entity(token=mongodb_token, collection="user", entity_id=mongodb_uid)

        logger.info("Deleting user from PostgreSQL...")
        postgresql_response = postgresql_client.delete_entity(token=postgresql_token, table="user", entity_id=postgresql_uid)

        if mongodb_response and postgresql_response:
            logger.info("User deleted successfully from both databases.")
            return {"message": "User deleted successfully from both databases"}
        else:
            logger.error("Failed to delete user from one of the databases")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user from one of the databases"
            )
    except Exception as e:
        logger.error(f"Error during user deletion process: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete error: {str(e)}"
        )

@router.delete("/delete/mongodb")
async def delete_user_mongodb(
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager)
):
    logger.info("Starting deletion of user from MongoDB...")
    try:
        mongodb_token = user_data.get('tokens', {}).get('mongodb')
        mongodb_uid = user_data.get('uids', {}).get('mongodb')
        if not mongodb_uid:
            logger.error("MongoDB User ID not found in token data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MongoDB User ID not found in token data"
            )

        mongodb_client = client_manager.get_client("mongodb")
        logger.info("Deleting user from MongoDB...")
        response = mongodb_client.delete_entity(token=mongodb_token, collection="user", entity_id=mongodb_uid)
        logger.info("User deleted successfully from MongoDB.")
        return {"message": "User deleted successfully from MongoDB", "response": response}
    except Exception as e:
        logger.error(f"Error during user deletion from MongoDB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete error in MongoDB: {str(e)}"
        )

@router.delete("/delete/postgresql")
async def delete_user_postgresql(
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager)
):
    logger.info("Starting deletion of user from PostgreSQL...")
    try:
        postgresql_token = user_data.get('tokens', {}).get('postgresql')
        postgresql_uid = user_data.get('uids', {}).get('postgresql')
        if not postgresql_uid:
            logger.error("PostgreSQL User ID not found in token data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PostgreSQL User ID not found in token data"
            )

        postgresql_client = client_manager.get_client("postgresql")
        logger.info("Deleting user from PostgreSQL...")
        response = postgresql_client.delete_entity(token=postgresql_token, table="user", entity_id=postgresql_uid)
        logger.info("User deleted successfully from PostgreSQL.")
        return {"message": "User deleted successfully from PostgreSQL", "response": response}
    except Exception as e:
        logger.error(f"Error during user deletion from PostgreSQL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete error in PostgreSQL: {str(e)}"
        )
