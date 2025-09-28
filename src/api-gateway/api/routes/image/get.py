import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Response
from pydantic import BaseModel
from typing import Dict
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

# Configurer le logger pour ce module
logger = logging.getLogger("gateway")

router = APIRouter()

class ImageContent(BaseModel):
    image_id: str
    content: bytes

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

def get_token_manager(request: Request) -> TokenManager:
    settings = get_settings(request)
    return create_token_manager(settings)

def get_client_manager(request: Request) -> ClientManager:
    settings = get_settings(request)
    return create_client_manager(settings)

def get_user_data_from_token(
    token_manager: TokenManager = Depends(get_token_manager),
    authorization: str = Header(...)
) -> Dict:
    """Récupère les données utilisateur à partir du token JWT."""
    logger.info("Extracting user data from token...")
    return token_manager.get_user_data_from_token(authorization)


def get_image_minio(bucket, entity_id, minio_client):
    try:
        logger.debug("Push image to bucket")
        response = minio_client.read_entity(
            token=None, 
            object="image", 
            bucket=bucket, 
            entity_id=entity_id,
        )
        logger.debug(f"Minio response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in api-minio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in copy image on Minio: {str(e)}"
        )

@router.get("/get_image/{bucket}/{image_uuid}", response_model=ImageContent)
def get_image(
    request: Request,
    image_uuid: str,
    bucket: str,
    user_data: Dict = Depends(get_user_data_from_token),
    client_manager = Depends(get_client_manager),
):

    minio_client = client_manager.get_client("minio")
    
    response = get_image_minio(bucket, image_uuid, minio_client)

    # resp devrait contenir les bytes (ou un stream). Si c’est un bytes:
    return response
