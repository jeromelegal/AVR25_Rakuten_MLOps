import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, UUID4
from typing import Optional, Dict
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

DEFAULT_BUCKET = "raw-images"

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

router = APIRouter()

class CategoryOut(BaseModel):
    id: int
    code: int
    label: str

class UserOut(BaseModel):
    id: int
    username: str

class ImageOut(BaseModel):
    id: int
    image_name: str
    image_uuid: UUID4
    bucket_path: str
    content: bytes

class AdOut(BaseModel):
    id: int
    designation: str
    description: Optional[str] = None
    created_at: str

class ReadAdResponse(BaseModel):
    ad: AdOut
    category: CategoryOut
    user: UserOut
    image: ImageOut

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

def read_psql_entity_by_id(table: str, entity_id: int, client, token) -> dict:
    try:
        logger.debug(f"Read '{table}' id={entity_id}")
        response = client.read_entity(token=token, table=table, entity_id=entity_id)
        data = response
        if not data:
            raise HTTPException(status_code=404, detail=f"{table} id={entity_id} not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error read '{table}' id={entity_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error read '{table}': {e}")

def read_psql_relation(table: str, relation_filter: dict, client, token) -> dict:
    try:
        logger.debug(f"Read relation '{table}' with {relation_filter}")
        response = client.read_relation(token=token, table=table, relation_id=relation_filter)
        data = response
        if not data:
            raise HTTPException(status_code=404, detail=f"{table} not found for {relation_filter}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error read relation '{table}': {e}")
        raise HTTPException(status_code=500, detail=f"Error read relation '{table}': {e}")

def read_image_minio(entity_id, minio_client):
    try:
        logger.debug(f"Pull image to bucket")
        response = minio_client.read_entity(token=None,
                                            object="image",
                                            bucket=DEFAULT_BUCKET,
                                            entity_id=str(entity_id),
                                            )
        logger.debug(f"Minio response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in api-minio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in copy image on Minio: {str(e)}"
        )
    
@router.get("/read_ad_psql/{ad_id}", response_model=ReadAdResponse)
async def read_ad(
    ad_id: int,
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    logger.info("Starting read ad.")
    
    postgresql_token = user_data.get('tokens', {}).get('postgresql') 
    if not postgresql_token:
        raise HTTPException(status_code=401, detail="Missing PostgreSQL token")
    
    postgresql_client = client_manager.get_client("postgresql")

    ### Reads ids ###
    ad_cat = read_psql_relation("ads_cats", ad_id, postgresql_client, postgresql_token)
    user_ad = read_psql_relation("ads_users", ad_id, postgresql_client, postgresql_token)
    ad_image = read_psql_relation("ads_images", ad_id, postgresql_client, postgresql_token)
    cat_id = ad_cat[0]["cat_id"]
    user_id = user_ad[0]["user_id"]
    image_id = ad_image[0]["image_id"] 

    ### Retrieves data ###
    ad_row = read_psql_entity_by_id("ad", ad_id, postgresql_client, postgresql_token)
    cat_row = read_psql_entity_by_id("category", cat_id, postgresql_client, postgresql_token)
    user_row = read_psql_entity_by_id("user", user_id, postgresql_client, postgresql_token)
    image_row = read_psql_entity_by_id("image", image_id, postgresql_client, postgresql_token)

    ### Retrieves image ###
    minio_image_id = image_row["image_uuid"]
    minio_client = client_manager.get_client("minio")
    minio_response = read_image_minio(minio_image_id, minio_client)

    return ReadAdResponse(
        ad=AdOut(
            id=ad_id,
            designation=ad_row["designation"],
            description=ad_row.get("description"),
            created_at=ad_row["created_at"],
        ),
        category=CategoryOut(
            id=cat_id,
            code=cat_row["code"],
            label=cat_row["label"],
        ),
        user=UserOut(
            id=user_id,
            username=user_row["username"],
        ),
        image=ImageOut(
            id=image_id,
            image_name=image_row["image_name"],
            image_uuid=image_row["image_uuid"],
            bucket_path=image_row["bucket_path"],
            content=minio_response["content"]
        ),
    )

@router.get("/list_ids/{table}", response_model=ReadAdResponse)
async def get_list(
    table: str,
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    logger.info("Getting ids list.")
    
    postgresql_token = user_data.get('tokens', {}).get('postgresql') 
    if not postgresql_token:
        raise HTTPException(status_code=401, detail="Missing PostgreSQL token")
    
    postgresql_client = client_manager.get_client("postgresql")
    
