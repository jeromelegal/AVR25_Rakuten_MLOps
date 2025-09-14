from fastapi import HTTPException, status, Header
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta, timezone
from api.config.settings import settings
from typing import Optional, Dict
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


def create_meta_token(user_data: dict, backend_uid: dict, backend_tokens: dict) -> Dict:
    """Crée le payload du token JWT."""
    now_utc = datetime.now(timezone.utc)
    exp = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_data.get("user_id"),
        "tokens": backend_tokens,
        "uid": backend_uid,
        "exp": exp,
        "iat": now_utc,
        "scope": "access_token"
    }
    return payload

def create_signed_token(payload: Dict) -> str:
    """Crée un JWT signé avec la clé privée."""
    to_encode = payload.copy()
    # return jwt.encode(
    #     to_encode,
    #     settings.INTERNAL_SECRET_KEY,
    #     algorithm="RS256"
    # )
    encoded_jwt = jwt.encode(to_encode, settings.INTERNAL_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict]:
    """Vérifie et décode un JWT avec la clé publique."""
    try:
        decoded = jwt.decode(token, settings.INTERNAL_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_token_from_header(authorization: str) -> str:
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_data_from_token(authorization: str = Header(...)) -> Dict:
    """Récupère les données utilisateur à partir du token JWT."""
    token = get_token_from_header(authorization)
    return verify_token(token)
