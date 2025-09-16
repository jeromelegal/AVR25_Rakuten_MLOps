import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Header
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Dict, Optional
from api.config.settings import Settings

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

class TokenManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        logger.debug("TokenManager initialized.")

    def create_meta_token(self, user_data: Dict, backend_tokens: Dict, backend_uids: Dict) -> Dict:
        """Crée le payload du token JWT."""
        now_utc = datetime.now(timezone.utc)
        exp = now_utc + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "user_id": user_data.get("user_id"),
            "tokens": backend_tokens,
            "uids": backend_uids,
            "exp": int(exp.timestamp()),
            "iat": int(now_utc.timestamp()),
            "scope": "access_token"
        }

        logger.debug(f"Meta-token payload created: {payload}")
        return payload

    def create_signed_token(self, payload: Dict) -> str:
        """Crée un JWT signé avec la clé secrète."""
        logger.debug(f"Encoding JWT payload: {payload}")
        try:
            to_encode = payload.copy()  # Utilisez payload directement sans conversion en string
            encoded_jwt = jwt.encode(to_encode, self.settings.INTERNAL_SECRET_KEY, algorithm=self.settings.ALGORITHM)
            logger.debug("Successfully created signed token.")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Failed to encode JWT: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create token: {str(e)}"
            )

    def verify_token(self, token: str) -> Dict:
        """Vérifie et décode un JWT avec la clé secrète."""
        logger.debug(f"Attempting to verify token... (token: {token})")
        try:
            decoded = jwt.decode(token, self.settings.INTERNAL_SECRET_KEY, algorithms=[self.settings.ALGORITHM])
            logger.debug(f"Token successfully verified and decoded. (decoded: {decoded})")
            return decoded
        except ExpiredSignatureError:
            logger.error("Token has expired.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.error(f"Invalid token encountered: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_token_from_header(self, authorization: str) -> str:
        """Extrait le token de l'en-tête d'autorisation."""
        logger.debug("Extracting token from authorization header...")
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            logger.debug("Token successfully extracted from header.")
            return token
        except ValueError:
            logger.error("Invalid authorization header format.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def get_user_data_from_token(self, authorization: str = Header(...)) -> Dict:
        """Récupère les données utilisateur à partir du token JWT."""
        logger.debug("Retrieving user data from token...")
        token = self.get_token_from_header(authorization)
        return self.verify_token(token)

def create_token_manager(settings: Settings) -> TokenManager:
    """Crée une instance de TokenManager avec les paramètres fournis."""
    logger.debug("Creating TokenManager instance...")
    return TokenManager(settings)
