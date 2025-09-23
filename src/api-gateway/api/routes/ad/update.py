import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, UploadFile, status
from pydantic import BaseModel
from typing import Optional, Dict, cast
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

DEFAULT_BUCKET = "raw-images"
logger = logging.getLogger(__name__)
router = APIRouter()

class UpdateAd(BaseModel):
    designation: Optional[str] = None
    description: Optional[str] = None
    category_code: Optional[str | int] = None
    category_label: Optional[str] = None

class UpdateAdResponse(BaseModel):
    ad: Dict
    category: Optional[Dict] = None
    image: Optional[Dict] = None
    relations: Dict

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

def insert_psql_table(data, table, client, token, relation=False):
    try:
        logger.debug(f"Write '{table}' in PostgreSQL")
        if relation:
            response = client.create_relation(token=token, 
                                              table=table, relation_data=data)
        else:
            response = client.create_entity(token=token, table=table, 
                                            entity_data=data)
        logger.debug(f"PostgreSQL '{table}' response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in insert '{table}' on PostgreSQL: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error in insert '{table}' on PostgreSQL: {str(e)}"
            )

def update_psql_entity(table, entity_id, data, client, token):
    """ Partial update on PostgreSQL ('ad', 'image', etc.)."""
    try:
        logger.debug(f"Update '{table}' id={entity_id} with {data}")
        response = client.update_entity(token=token, table=table, 
                                        entity_id=entity_id, entity_data=data)
        logger.debug(f"PostgreSQL update '{table}' response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in update '{table}' id={entity_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error in update '{table}' id={entity_id}: {str(e)}")

def replace_relation(table, where, new_data, client, token):
    """ Replace relation """
    try:
        logger.debug(f"Delete relation '{table}' where={where}")
        client.delete_relation(token=token, table=table, relation_id=where)
    except Exception as e:
        logger.warning(f"Delete relation '{table}' where={where} failed or none existed: {e}")

    logger.debug(f"Create relation '{table}' with {new_data}")
    return client.create_relation(token=token, table=table, 
                                  relation_data=new_data)

def insert_image_minio(payload, files, minio_client):
    try:
        logger.debug("Push image to bucket")
        response = minio_client.create_entity(
            token=None, 
            #object="image", 
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

@router.patch("/update_ad/{ad_id}", response_model=UpdateAdResponse)
async def update_ad(
    ad_id: int,
    request: Request,
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    """
    Met à jour une annonce:
      - designation / description (optionnels)
      - recatégorisation (optionnelle): crée category puis ads_cats(ad_id, cat_id)
      - remplacement image (optionnel si 'file' présent dans le multipart)
    """
    logger.info(f"Starting update_ad for ad_id={ad_id}")
    form = await request.form()

    body = UpdateAd(
        designation = form.get("designation"),
        description = form.get("description"),
        category_code = form.get("category_code"),
        category_label = form.get("category_label"),
    )

    ### Auth PostgreSQL ###
    postgresql_uid = user_data.get("uids", {}).get("postgresql")
    if not postgresql_uid:
        raise HTTPException(status_code=400, 
                            detail="User ID not found in token data")
    postgresql_token = user_data.get("tokens", {}).get("postgresql")
    postgresql_client = client_manager.get_client("postgresql")

    # Partial ad update
    updated_ad = {}
    if body.designation is not None:
        updated_ad["designation"] = body.designation
    if body.description is not None:
        updated_ad["description"] = body.description

    if updated_ad:
        update_psql_entity("ad", ad_id, updated_ad, 
                           postgresql_client, postgresql_token)

    # Modifiates category if present
    category_payload = None
    if body.category_code is not None or body.category_label is not None:
        cat_data = {}
        if body.category_code is not None:
            cat_data["code"] = body.category_code
        if body.category_label is not None:
            cat_data["label"] = body.category_label
        print("\n"*20)
        print(cat_data)
        print("\n"*20)
        cat_resp = insert_psql_table(cat_data, "category", postgresql_client, postgresql_token)
        cat_id = cat_resp["id"]

        # Replce ads_cats relation
        replace_relation(
            table="ads_cats",
            where=ad_id,
            new_data={"ad_id": ad_id, "cat_id": cat_id},
            client=postgresql_client,
            token=postgresql_token,
        )
        category_payload = {"id": cat_id, **cat_data}

    # Modifiates image
    image_payload = None
    file: Optional[UploadFile] = None
    if "file" in form:
        try:
            file = cast(UploadFile, form["file"])
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid 'file' in form-data")

    if file:
        minio_client = client_manager.get_client("minio")
        image_bytes = await file.read()
        files = {"file": (file.filename, image_bytes, file.content_type)}
        payload = {"username": postgresql_uid}

        minio_response = insert_image_minio(payload, files, minio_client)

        # Update image data in PostgreSQL
        image_data = {
            "image_name":  minio_response["image_name"],
            "image_uuid":  minio_response["image_id"],
            "bucket_path": minio_response["bucket_path"],
            #"created_at":  minio_response["created_at"],
            "created_by":  int(minio_response["created_by"]),
        }
        image_resp = insert_psql_table(image_data, "image", postgresql_client, postgresql_token)
        image_id = image_resp["id"]

        # Replace image relation
        replace_relation(
            table="ads_images",
            where=ad_id,
            new_data={"ad_id": ad_id, "image_id": image_id},
            client=postgresql_client,
            token=postgresql_token,
        )

        image_payload = {
            "id": image_id,
            "image_name": minio_response["image_name"],
            "image_uuid": minio_response["image_id"],
            "bucket_path": minio_response["bucket_path"],
        }

    # 
    ad_out = {"id": ad_id, **updated_ad} if updated_ad else {"id": ad_id}
    relations_flags = {
        "ad_cat": category_payload is not None,
        "ad_image": image_payload is not None,
    }

    return UpdateAdResponse(
        ad=ad_out,
        category=category_payload,
        image=image_payload,
        relations=relations_flags,
    )
