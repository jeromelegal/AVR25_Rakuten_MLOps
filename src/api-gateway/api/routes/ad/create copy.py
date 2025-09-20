import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, cast
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

DEFAULT_BUCKET = "raw-images"

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

router = APIRouter()

class CreateAd(BaseModel):
    designation: str
    description: Optional[str]

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

def insert_psql(data, table, client, token, relation=False):
    """ Insert data in PostgreSQL """
    try:
        # Insert in '{table}' on PostgreSQL
        logger.debug(f"Write '{table}' in PostgreSQL")
        if relation:
            response = client.create_relation(token=token, table=table, relation_data=data)
        else:
            response = client.create_entity(token=token, table=table, entity_data=data)
        logger.debug(f"PostgreSQL '{table}' response: {response}")
        
    except Exception as e:
        logger.error(f"Error in insert '{table}' on PostgreSQL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in insert '{table}' on PostgreSQL: {str(e)}"
        )
    return response

@router.post("/create_ad")
async def create_ad(
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    logger.info("Starting create ad.")
    # Retrieve 'form' from FRONT
    form = await request.form()
    try:
        designation = form.get("designation")
        description = form.get("description")
        category_code = form.get("category_code")
        category_label = form.get("category_label")
        file = cast(UploadFile, form["file"])
        image_name = file.filename
        # Transform image in bytes
        image_bytes = await file.read()

    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Form : {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid Form: {e}")
        
    user_id = user_data.get('user_id')
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User ID not found in token data")
    
    postgresql_token = user_data.get('tokens', {}).get('postgresql') 
    postgresql_client = client_manager.get_client("postgresql")

    ### Insert entities ###
    # Insert in 'ads' on PostgreSQL
    ad_data = {
            "designation": designation,
            "description": description
        }
    ad_response = insert_psql(ad_data, "ad", postgresql_client, postgresql_token)
    ad_id = ad_response["id"]
    
    # Insert in 'categories' on PostgreSQL
    cat_data = {
            "code": category_code,
            "label": category_label
        }
    cat_response = insert_psql(cat_data, "category", postgresql_client, postgresql_token)
    cat_id = cat_response["id"]

    # Insert in 'image' on PostgreSQL
    image_data = {
            "image_name": image_name,
            "bucket_name": DEFAULT_BUCKET
        }
    image_response = insert_psql(image_data, "image", postgresql_client, postgresql_token)
    image_id = image_response["id"]

    ### Insert relations ###
    # Insert 'ad_cats' relation in PostgreSQL
    ad_cat = {
        "ad_id": ad_id,
        "cat_id": cat_id
    }
    insert_psql(ad_cat, "ad_cats", postgresql_client, postgresql_token, relation=True)

    # Insert 'user_ads' relation in PostgreSQL
    user_ad = {
        "user_id": user_id,
        "ad_id": ad_id
    }
    insert_psql(user_ad, "user_ads", postgresql_client, postgresql_token, relation=True)

    # Insert 'ad_image' relation in PostgreSQL
    ad_image = {
        "ad_id": ad_id,
        "image_id": image_id
    }
    insert_psql(ad_image, "ad_images", postgresql_client, postgresql_token, relation=True)

    ### Minio ###
    minio_token = user_data.get('tokens', {}).get('minio') 
    minio_client = client_manager.get_client("minio")
    # Copy image in bucket
    try:
        logger.debug(f"Push image to bucket")
        response = minio_client.create_entity(token=minio_token, object=DEFAULT_BUCKET, entity_data=image_bytes)
        logger.debug(f"Minio response: {response}")
        
    except Exception as e:
        logger.error(f"Error in api-minio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in copy image on Minio: {str(e)}"
        )
