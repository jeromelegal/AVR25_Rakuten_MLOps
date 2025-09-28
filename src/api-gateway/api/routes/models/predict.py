import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Header, File, UploadFile
from typing import Optional, Dict, List
from pydantic import BaseModel
from config.settings import Settings
from api.auth.clients.manager import ClientManager, create_client_manager
from api.auth.token.manager import TokenManager, create_token_manager

logger = logging.getLogger("gateway")

router = APIRouter()


# ----------------------------
# Dépendances communes
# ----------------------------
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


# ----------------------------
# Modèles de données
# ----------------------------
class Prediction(BaseModel):
    category: Optional[str]
    probability: Optional[float]
    overall_probabilities: Optional[Dict[str, float]]
    image_probabilities: Optional[Dict]
    text_probabilities: Optional[Dict]


# ----------------------------
# Endpoints
# ----------------------------
@router.get("/api-processing")
def get_version(settings: Settings = Depends(get_settings)):
    return {
        "message": "Image and text prediction API - Rakuten Project AVR25",
        "version": settings.SERVICE_VERSION,
    }


@router.post("/api-processing/predict", response_model=Prediction)
async def get_categories(
    description: Optional[str] = None,
    designation: Optional[str] = None,
    files: List[UploadFile] = File(..., description="Multiple files"),
    client_manager: ClientManager = Depends(get_client_manager),
):
    """
    Endpoint de prédiction image + texte.
    Protégé par token JWT (comme tes autres endpoints).
    """
    # Vérification d’un éventuel token spécifique si besoin
    # (ex: token pour accéder à un service interne)
    # Ici on se contente du JWT utilisateur
    logger.debug("Processing prediction request...")
    processing_client = client_manager.get_client("processing")

    try:
    # Lire les fichiers uploadés
        file_bytes = [await f.read() for f in files]
    # Appel du modèle
        prediction = processing_client.predict(
            description,
            designation,
            files=file_bytes,
        )
        return Prediction(**prediction)
    
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Impossible to process the ad. {exc}")
