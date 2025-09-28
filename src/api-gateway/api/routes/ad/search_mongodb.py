import logging
from typing import Dict, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from pydantic import BaseModel
from starlette.responses import JSONResponse
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager
import base64

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_BUCKET = "raw-images"

class User(BaseModel):
    id: int
    username: str

class ImageInfo(BaseModel):
    image_uuid: str
    bucket_path: str

class AdOut(BaseModel):
    id: str
    ad_id: int
    user: User
    designation: str
    description: Optional[str] = None
    category: str
    images: Optional[List[ImageInfo]] = None
    created_at: str

class SearchResponse(BaseModel):
    items: List[AdOut]
    count: int
    page: int
    page_size: int
    has_more: bool

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

    return token_manager.get_user_data_from_token(authorization)

def _require_token(user_data: Dict, key: str) -> str:
    token = user_data.get("tokens", {}).get(key)
    if not token:
        raise HTTPException(status_code=401, detail=f"Missing {key} token")
    return token


@router.get("/search_ads", response_model=SearchResponse)
async def search_ads(
    request: Request,
    q: Optional[str] = Query(None, description="Recherche texte sur designation/description"),
    category: Optional[str] = Query(None, description="Filtre sur la catégorie exacte"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    user_data: Dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    """
    Proxifie l'endpoint MongoDB /entity/ad/search.
    Retourne en plus un champ has_more pour la pagination Front.
    """
    mongodb_token = _require_token(user_data, "mongodb")
    mongo_client = client_manager.get_client("mongodb")

    skip = (page - 1) * page_size
    try:
        res = mongo_client.search_ads(
            token=mongodb_token,
            q=q,
            category=category,
            skip=skip,
            limit=page_size
        )
        items = res.get("items", [])
        count = res.get("count", len(items))
        has_more = count > (skip + len(items))
        return SearchResponse(items=items, count=count, page=page, page_size=page_size, has_more=has_more)
    except Exception as e:
        logger.exception("Error while searching ads")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ad/{mongo_id}", response_model=AdOut)
async def get_ad_by_id(
    request: Request,
    mongo_id: str,
    user_data: Dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    """
    Lit 1 annonce par son _id MongoDB.
    """
    mongodb_token = _require_token(user_data, "mongodb")
    mongo_client = client_manager.get_client("mongodb")
    try:
        data = mongo_client.read_entity(token=mongodb_token, collection="ad", entity_id=mongo_id)
        return data
    except Exception as e:
        logger.exception("Error while reading ad")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/image/{image_uuid}")
async def get_minio_image(
    request: Request,
    image_uuid: str,
    user_data: Dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    """
    Récupère l'image depuis MinIO (via la gateway MinIO) et renvoie {content: base64, content_type}.
    On passe par JSON (plutôt que streaming) car ton client MinIO renvoie déjà du JSON avec 'content'.
    """
    minio_client = client_manager.get_client("minio")
    try:
        resp = minio_client.read_entity(
            token=None,
            object="image",
            bucket=DEFAULT_BUCKET,
            entity_id=str(image_uuid)
        )

        content = resp.get("content")
        content_type = resp.get("content_type", "image/jpeg")
        if not content:
            raise HTTPException(status_code=404, detail="Image not found or empty")
        return JSONResponse({"content": content, "content_type": content_type})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error while pulling image from MinIO")
        raise HTTPException(status_code=500, detail=str(e))
