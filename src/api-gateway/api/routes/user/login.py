import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from api.auth.authenticator import create_backend_authenticator
from api.auth.token.manager import create_token_manager
from config.settings import Settings

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

def get_settings(request: Request) -> Settings:
    return request.app.state.settings

class InvalidCredentials(Exception):
    """Raised when supplied credentials are invalid."""
    pass

@router.post("/login")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # Log le début de la requête de login
    logger.debug("Login attempt initiated...")

    # Récupérer les paramètres de configuration spécifiques à la requête
    settings = get_settings(request)
    logger.debug("Retrieved settings for the request")

    # Créer des instances de BackendAuthenticator et TokenManager avec les paramètres de cette requête
    authenticator = create_backend_authenticator(settings)
    token_manager = create_token_manager(settings)

    # Préparer les informations d'authentification
    credentials = {
        "username": form_data.username,
        "password": form_data.password,
        "grant_type": "password"
    }
    logger.debug(f"Attempting authentication for user: {form_data.username}")

    try:
        # Authentifier l'utilisateur sur plusieurs API backend
        user_data, backend_tokens, backend_uid = authenticator.authenticate(credentials)

        # Logs détaillés pour user_data, backend_tokens, et backend_uid
        logger.debug(f"User Data: {user_data}")
        logger.debug(f"Backend Tokens: {backend_tokens}")
        logger.debug(f"Backend UIDs: {backend_uid}")

        # STRONG SUCCESS CRITERIA
        user_id = (user_data or {}).get("user_id") or (user_data or {}).get("id")
        if not user_id:
            logger.warning(f"No valid user_id for user: {form_data.username}")
            raise InvalidCredentials()

        if not backend_tokens or len(backend_tokens) == 0:
            logger.warning(f"No backend tokens for user: {form_data.username}")
            raise InvalidCredentials()

        if any(not t or not isinstance(t, str) for t in backend_tokens.values()):
            logger.warning(f"Invalid backend token values for user: {form_data.username}")
            raise InvalidCredentials()

        # Vérifier si l'authentification a échoué
        if not user_data or any(token is None for token in backend_tokens.values()):
            logger.warning(f"Authentication failed for user: {form_data.username}")
            raise InvalidCredentials()

        logger.debug(f"Authentication successful for user: {form_data.username}")

        # Créer un payload de méta-token
        meta_token_payload = token_manager.create_meta_token(user_data, backend_tokens, backend_uid)
        logger.debug(f"Meta-token payload created for user: {form_data.username}")

        # Créer un méta-token signé et chiffré
        meta_token = token_manager.create_signed_token(meta_token_payload)
        logger.debug(f"Meta-token generated for user: {form_data.username}")

        return {
            "username": form_data.username,
            "access_token": meta_token,
            "token_type": "bearer"
        }
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )
