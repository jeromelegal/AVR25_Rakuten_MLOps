import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, cast
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager
from pathlib import Path

DEFAULT_BUCKET = "raw-images"

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

router = APIRouter()

class CreateAd(BaseModel):
    designation: str
    description: Optional[str]

class CreateAdResponse(BaseModel):
    ad: dict
    category: dict
    image: dict
    relations: dict

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

def get_id_category(code, table, client, token):
    response = client.get_category_id(token=token, table=table, code=code)
    logger.debug(f"PostgreSQL get id_category '{table}' response: {response}")
    return response

def insert_psql_table(data, table, client, token, relation=False):
    """ Insert data in PostgreSQL """
    try:
        # Insert in '{table}' on PostgreSQL
        logger.debug(f"Write '{table}' in PostgreSQL")
        if relation:
            response = client.create_relation(token=token, 
                                              table=table, relation_data=data)
        else:
            response = client.create_entity(token=token, 
                                            table=table, entity_data=data)
        logger.debug(f"PostgreSQL '{table}' response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in insert '{table}' on PostgreSQL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in insert '{table}' on PostgreSQL: {str(e)}"
        )
    
def insert_entities(ad_data, cat_data, image_data, 
                    postgresql_client, postgresql_token):
    # Insert in 'ads' on PostgreSQL
    ad_response = insert_psql_table(ad_data, "ad", 
                                    postgresql_client, postgresql_token)
    ad_id = ad_response["id"]
    # Get 'category' ID on PostgreSQL
    cat_response = get_id_category(int(cat_data["code"]), "by-code", 
                                     postgresql_client, postgresql_token)
    cat_id = cat_response["id"]
    # Insert in 'image' on PostgreSQL
    image_response = insert_psql_table(image_data, "image", 
                                       postgresql_client, postgresql_token)
    image_id = image_response["id"]
    return ad_id, cat_id, image_id 

def insert_relations(ad_cat, user_ad, ad_image, postgresql_client, 
                     postgresql_token):
    # Insert 'ad_cats' relation in PostgreSQL
    insert_psql_table(ad_cat, "ads_cats", postgresql_client, 
                      postgresql_token, relation=True)
    # Insert 'user_ads' relation in PostgreSQL
    insert_psql_table(user_ad, "users_ads", postgresql_client, 
                      postgresql_token, relation=True)
    # Insert 'ad_image' relation in PostgreSQL
    insert_psql_table(ad_image, "ads_images", postgresql_client, 
                      postgresql_token, relation=True)

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

@router.post("/create_ad", response_model=CreateAdResponse)
async def create_ad(
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    logger.info("Starting create ad.")
    # Retrieve 'form' from FRONT
    form = await request.form()
    try:
        ad_data = {
            "designation": form.get("designation"),
            "description": form.get("description")
        }
        cat_data = {
            "code": form.get("category_code"),
            "label": form.get("category_label")
        }
        file = cast(UploadFile, form["file"])
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Form : {str(e)}")
        raise HTTPException(status_code=422, detail=f"Invalid Form: {e}")
        
    ### Auth PostgreSQL ###
    postgresql_uid = user_data.get('uids', {}).get('postgresql')
    if not postgresql_uid:
        raise HTTPException(status_code=400, 
                            detail="User ID not found in token data")
    postgresql_token = user_data.get('tokens', {}).get('postgresql')
    postgresql_client = client_manager.get_client("postgresql")

    ### Minio ###
    minio_client = client_manager.get_client("minio")
    # Transform image in bytes
    image_bytes = await file.read()
    files = {"file": (file.filename, image_bytes, file.content_type)}
    payload = {"username": postgresql_uid}
    # Copy image in bucket
    
    minio_response = insert_image_minio(payload, files, minio_client)

    ### PostgreSQL ###  
    try:
        image_data = {
            "image_name":  minio_response["image_name"],
            "image_uuid":  minio_response["image_id"],
            "bucket_path": minio_response["bucket_path"],
            #"created_at":  minio_response["created_at"],
            "created_by":  int(minio_response["created_by"]),
        }
    except KeyError as e:
        logger.error(f"Minio response missing key: {e}; got: {minio_response}")
        raise HTTPException(status_code=502, detail=f"Minio response incomplete: {e}")
        
    ### Insert entities ###
    ad_id, cat_id, image_id = insert_entities(
        ad_data, 
        cat_data, 
        image_data, 
        postgresql_client, 
        postgresql_token)

    ### Insert relations ###
    ad_cat = {
        "ad_id": ad_id,
        "cat_id": cat_id
    }
    user_ad = {
        "user_id": postgresql_uid,
        "ad_id": ad_id
    }
    ad_image = {
        "ad_id": ad_id,
        "image_id": image_id
    }
    insert_relations(ad_cat, 
                     user_ad, 
                     ad_image, 
                     postgresql_client, 
                     postgresql_token)

    return CreateAdResponse(
        ad={"id": ad_id, **ad_data},
        category={"id": cat_id, **cat_data},
        image={
            "id": image_id,
            "image_name":  minio_response["image_name"],
            "image_uuid":  minio_response["image_id"],
            "bucket_path": minio_response["bucket_path"],
        },
        relations={"ad_cat": True, "user_ad": True, "ad_image": True},
    )

