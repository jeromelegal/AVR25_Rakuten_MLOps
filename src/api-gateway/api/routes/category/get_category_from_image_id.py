import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel
from typing import List, Dict
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

logger = logging.getLogger("gateway")

router = APIRouter()

class CategoryOut(BaseModel):
    id: int
    code: int
    label: str

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
        
        response = client.read_entity(
            token=token, 
            table=table, 
            entity_id=entity_id
            )
        data = response
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"{table} id={entity_id} not found")
        return data
    
    except Exception as e:
        logger.error(f"Error read '{table}' id={entity_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Error read '{table}': {e}")
    
def read_psql_relation(table: str, relation_filter: int, client, token) -> dict:
    try:
        logger.debug(f"Read relation '{table}' with {relation_filter}")
        
        response = client.read_relation(
            token=token, 
            table=table, 
            relation_id=relation_filter
            )
        data = response
        if not data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"{table} not found for {relation_filter}")
        return data
    
    except Exception as e:
        logger.error(f"Error read relation '{table}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Error read relation '{table}': {e}")


@router.get("/get_categories_from_image_id/{image_id}", response_model=CategoryOut)
async def get_categories_from_image_id(
    image_id: str, 
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    logger.debug("Getting categories from image_id...")
    
    postgresql_token = user_data.get('tokens', {}).get('postgresql') 
    
    if not postgresql_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Missing PostgreSQL token")
    
    postgresql_client = client_manager.get_client("postgresql")

    ### Retrieves image_ad relation ###
    image_ad = read_psql_relation(table="images_ads", relation_filter=image_id, 
                    client=postgresql_client, token=postgresql_token)
    ad_id = image_ad["ad_id"]
    
    if not ad_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Missing image or image_ad relation.")
        
    ### Retrieves ad_cat relation ###
    ad_cat = read_psql_relation(table="ads_cats", relation_filter=ad_id, 
                    client=postgresql_client, token=postgresql_token)
    cat_id = ad_cat[0]["cat_id"]
    
    if not cat_id:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, 
                            detail="No categoy associated.")

    ### Retrieves categories ###
    cat_row = read_psql_entity_by_id(table="category", entity_id=cat_id, 
                                client=postgresql_client, token=postgresql_token)
    if cat_row:
        return cat_row
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                        detail="Error in reading category table.")
        
