import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

logger = logging.getLogger(__name__)
router = APIRouter()


# TODO : 
# ajout cat_code dans mongodb
# ne pas passer par la gateway pour la replication, créer un container dédié


def get_settings(request: Request) -> Settings:
    return request.app.state.settings

def get_token_manager(request: Request) -> TokenManager:
    return create_token_manager(get_settings(request))

def get_client_manager(request: Request) -> ClientManager:
    return create_client_manager(get_settings(request))

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

def _read_psql_entity(client, token, table: str, entity_id: int) -> Dict[str, Any]:
    return client.read_entity(token=token, table=table, entity_id=entity_id)

def _read_psql_relation_ids(client, token, table: str, ad_id: int) -> List[Dict[str, Any]]:
    return client.read_relation(token=token, table=table, relation_id=ad_id)

def _list_psql_ids(client, token, table: str) -> List[int]:
    return client.get_ids(token=token, table=table)

# Test pour éviter d'écrire un None dans mongodb et échouer l'insertion
def _safe_get(d: Dict[str, Any], *keys, default=None):
    for k in keys:
        if isinstance(d, dict) and k in d:
            return d[k]
    return default

def _to_iso(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val
    iso = getattr(val, "isoformat", None)
    return iso() if callable(iso) else str(val)

def _build_mongo_doc_for_ad(ad_id: int, pg_client, pg_token) -> Dict[str, Any]:
    
    ad_row = _read_psql_entity(pg_client, pg_token, "ad", ad_id)
    if not ad_row:
        raise ValueError(f"ad_id={ad_id} not found")
    
    ad_cat_rel = _read_psql_relation_ids(pg_client, pg_token, "ads_cats",   ad_id)
    if not ad_cat_rel :
        raise ValueError(f"Missing 'ad_cat_rel' relation for ad_id={ad_id}")
    cat_id  = ad_cat_rel[0]["cat_id"]
    
    ad_user_rel = _read_psql_relation_ids(pg_client, pg_token, "ads_users",  ad_id)
    if not ad_user_rel :
        raise ValueError(f"Missing 'ad_user_rel' relation for ad_id={ad_id}")  
    user_id = ad_user_rel["user_id"]

    cat_row  = _read_psql_entity(pg_client, pg_token, "category", cat_id)
    if not cat_row :
        raise ValueError(f"Missing 'cat_row' entity for cat_id={cat_id}")  
    
    user_row = _read_psql_entity(pg_client, pg_token, "user", user_id)
    if not user_row :
        raise ValueError(f"Missing 'user_row' entity for user_id={user_id}")

    images = []
    try:
        rels = _read_psql_relation_ids(pg_client, pg_token, "ads_images", ad_id) or []
        for r in rels:
            try:
                img = _read_psql_entity(pg_client, pg_token, "image", int(_safe_get(r, "image_id")))
                images.append({
                    "image_uuid": str(_safe_get(img, "image_uuid", default="")),
                    "bucket_path": str(_safe_get(img, "bucket_path", default="")),
                })
            except Exception:
                continue
    except Exception:
        pass
    
    created_at = _to_iso(ad_row.get("created_at"))
    
    doc = {
        "ad_id": ad_id,
        "user": {"id": user_row.get("user_id"), "username": user_row.get("username")},
        "designation": ad_row["designation"],
        "description": ad_row["description"],
        "category": cat_row["label"],
        "images": images if images else [],
        "created_at": created_at,
    }
    return doc

@router.post("/replicate/ads_to_mongo")
async def replicate_ads_to_mongo(
    request: Request,
    table: str = Query("ads", description="Table source dans PostgreSQL"),
    limit: int = Query(1000, ge=1, le=100000, description="Nombre max d'ads à traiter"),
    batch_size: int = Query(100, ge=1, le=1000, description="Taille de lot"),
    user_data: Dict = Depends(get_user_data_from_token),
    client_manager: ClientManager = Depends(get_client_manager),
):
    """
    Réplication Postgres -> Mongo
      - récupère les ad.id
      - assemble les relations (user, category, images)
      - insère en Mongo si absent (unicité par ad_id côté Mongo)
      - par batch + report
    """
    pg_token     = _require_token(user_data, "postgresql")
    mongo_token  = _require_token(user_data, "mongodb")
    pg_client    = client_manager.get_client("postgresql")
    mongo_client = client_manager.get_client("mongodb")

    try:
        all_ids = _list_psql_ids(pg_client, pg_token, table)
    except Exception as e:
        logger.exception("Failed to list ids from PostgreSQL")
        raise HTTPException(status_code=500, detail=f"List ids failure: {e}")

    ids = list(all_ids)[:limit]
    total = len(ids)

    inserted = 0
    duplicates = 0
    errors: List[Dict[str, Any]] = []

    for start in range(0, total, batch_size):
        chunk = ids[start:start+batch_size]
        for ad_id in chunk:
            try:
                doc = _build_mongo_doc_for_ad(ad_id, pg_client, pg_token)
                try:
                    mongo_client.create_entity(token=mongo_token, collection="ad", entity_data=doc)
                    logger.info("Mongo INSERT OK ad_id=%s", ad_id)
                    inserted += 1
                except Exception as me:
                    msg = str(me)
                    if "duplicate" in msg.lower() or "e11000" in msg.lower():
                        duplicates += 1
                        logger.info("Mongo DUPLICATE ad_id=%s", ad_id)
                    else:
                        logger.error("Mongo INSERT FAIL ad_id=%s | error=%s | doc=%s", ad_id, msg, doc)
                        errors.append({"ad_id": ad_id, "error": msg})

            except Exception as e:
                logger.warning("Build doc error on ad_id=%s: %s", ad_id, e)
                errors.append({"ad_id": ad_id, "error": str(e)})

    return {
        "source": "postgresql",
        "target": "mongodb",
        "table": table,
        "requested": limit,
        "processed": total,
        "inserted": inserted,
        "duplicates": duplicates,
        "errors_count": len(errors),
        "errors_sample": errors[:10],
        "batch_size": batch_size,
    }
