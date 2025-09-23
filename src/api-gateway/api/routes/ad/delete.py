from typing import Optional, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request, Header
import logging
from pydantic import BaseModel
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

router = APIRouter()
logger = logging.getLogger(__name__)
DEFAULT_BUCKET = "raw-images"

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

def get_relations(client, token, table: str, relation_id: str) -> List[Dict]:
    try:
        return client.read_relation(token=token, table=table, relation_id=relation_id)
    except Exception as e:
        logger.warning(f"[get_relations] table={table} relation_id={relation_id} -> {e}")
        return []

def delete_relation(client, token, table: str, relation_id: int) -> bool:
    try:
        client.delete_relation(token=token, table=table, relation_id=relation_id)
        return True
    except Exception as e:
        logger.warning(f"[delete_relation] table={table} relation_id={relation_id} -> {e}")
        return False

def get_entity(client, token, table: str, entity_id: int) -> Optional[Dict]:
    try:
        return client.read_entity(token=token, table=table, entity_id=entity_id)
    except Exception as e:
        logger.warning(f"[get_entity] table={table} id={entity_id} -> {e}")
        return None

def delete_entity(client, token, table: str, entity_id: int) -> bool:
    try:
        client.delete_entity(token=token, table=table, entity_id=entity_id)
        return True
    except Exception as e:
        logger.warning(f"[delete_entity] table={table} id={entity_id} -> {e}")
        return False

def minio_delete_image(minio_client, bucket: str, image_uuid: str) -> bool:
    try:
        minio_client.delete_entity(
            token=None,
            object="image",
            bucket=bucket,
            entity_id=str(image_uuid),
        )
        return True
    except Exception as e:
        logger.warning(f"[minio_delete_image] uuid={image_uuid} -> {e}")
        return False

class DeleteAdResponse(BaseModel):
    ad_id: int
    deleted_relations: Dict
    deleted_images: List[Dict]
    ad_deleted: bool

@router.delete("/delete_ad/{ad_id}", response_model=DeleteAdResponse)
async def delete_ad(
    ad_id: int,
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager = Depends(get_client_manager),
):
    logger.info(f"[DELETE] ad_id={ad_id}")

    # Clients
    postgresql_token = user_data.get("tokens", {}).get("postgresql")
    if not postgresql_token:
        raise HTTPException(status_code=400, detail="PostgreSQL token missing in user data")
    postgresql_client = client_manager.get_client("postgresql")
    minio = client_manager.get_client("minio")

    # Relations
    image_relations = get_relations(postgresql_client, postgresql_token, 
                                    "ads_images", ad_id)
    cat_relation = get_relations(postgresql_client, postgresql_token, 
                                    "ads_cats", ad_id)
    
    # Delete all relations
    rel_flags = {
        "ads_images": delete_relation(postgresql_client, postgresql_token, "ads_images", ad_id),
        "ads_cats":   delete_relation(postgresql_client, postgresql_token, "ads_cats", ad_id),
        "users_ads":  delete_relation(postgresql_client, postgresql_token, "ads_users", ad_id),
    }

    image_ids = []
    for r in image_relations:
        iid = r.get("image_id")
        if iid is not None:
            image_ids.append(iid)

    deleted_images: List[Dict] = []

    # Delete each images
    for image_id in image_ids:
        img = get_entity(postgresql_client, postgresql_token, "image", image_id)
        if not img:
            continue

        image_uuid = img.get("image_uuid")
        bucket_path = img.get("bucket_path")
        image_name = img.get("image_name")

        minio_ok = False
        if image_uuid:
            minio_ok = minio_delete_image(minio, DEFAULT_BUCKET, image_uuid)

        pg_img_ok = delete_entity(postgresql_client, postgresql_token, "image", image_id)

        deleted_images.append({
            "image_id": image_id,
            "image_uuid": image_uuid,
            "image_name": image_name,
            "bucket_path": bucket_path,
            "minio_deleted": bool(minio_ok),
            "image_row_deleted": bool(pg_img_ok),
        })

    # Delete ad and category
    cat_id = cat_relation[0]["cat_id"]
    cat_deleted = delete_entity(postgresql_client, postgresql_token, "category", cat_id)
    ad_deleted = delete_entity(postgresql_client, postgresql_token, "ad", ad_id)

    return DeleteAdResponse(
        ad_id=ad_id,
        deleted_relations=rel_flags,
        deleted_images=deleted_images,
        cat_deleted=bool(cat_deleted),
        ad_deleted=bool(ad_deleted),
    )