import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, UploadFile
from pydantic import BaseModel
from typing import Dict, cast
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

DEFAULT_BUCKET = "raw-images"

# Configurer le logger pour ce module
logger = logging.getLogger("gateway")

router = APIRouter()

class ImageCreated(BaseModel):
    image_id: str

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


def insert_image_minio(payload, files, minio_client):
    try:
        logger.debug("Push image to bucket")
        response = minio_client.create_entity(
            token=None,  
            object="image-multipart",
            params={"bucket": DEFAULT_BUCKET}, 
            payload=payload, 
            files=files,
        )
        logger.debug(f"Minio response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in api-minio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in copy image on Minio: {str(e)}"
        )

@router.post("/save_image", response_model=ImageCreated)
async def save_image(
    request: Request,
    user_data: Dict = Depends(get_user_data_from_token),
    client_manager = Depends(get_client_manager),
):
    form = await request.form()
    try:
        file = cast(UploadFile, form["file"])
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Form : {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid Form: {e}")

    minio_client = client_manager.get_client("minio")
    user_uid = user_data.get('uids', {}).get('postgresql')

    image_bytes = await file.read()
    files = {"file": (file.filename, image_bytes, file.content_type)}
    payload = {"username": user_uid}

    minio_response = insert_image_minio(payload, files, minio_client)

    return {"image_id": minio_response["image_id"]}
    