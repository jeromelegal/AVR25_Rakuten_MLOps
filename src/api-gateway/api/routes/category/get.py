import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel
from typing import List, Dict
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager


# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

router = APIRouter()

class Category(BaseModel):
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

def read_psql_entity(table: str, client, token) -> dict:
    try:
        logger.debug(f"Read '{table}'")
        response = client.read_categories(token=token, table=table)
        data = response
        if not data:
            raise HTTPException(status_code=404, detail=f"{table}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error read '{table}': {e}")
        raise HTTPException(status_code=500, detail=f"Error read '{table}': {e}")


@router.get("/get_categories", response_model=List[Category])
async def read_ad(
    user_data: dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    logger.info("Starting get categories...")
    
    postgresql_token = user_data.get('tokens', {}).get('postgresql') 
    if not postgresql_token:
        raise HTTPException(status_code=401, detail="Missing PostgreSQL token")
    
    postgresql_client = client_manager.get_client("postgresql")

    ### Retrieves categories ###
    data = read_psql_entity("categories", postgresql_client, postgresql_token)
    payload = data.get("categories", data) if isinstance(data, dict) else data

    categories = [Category.model_validate(item) for item in payload]
    return categories