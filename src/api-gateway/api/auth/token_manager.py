from datetime import datetime, timedelta, timezone
from jose import jwt
from api.config.settings import settings
from cryptography.fernet import Fernet
from typing import Optional

# Initialiser cipher_suite avec une clé générée
cipher_suite = Fernet(Fernet.generate_key())

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.INTERNAL_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_meta_token(user_data: dict, backend_tokens: dict):
    # Chiffrer les tokens des backends
    encrypted_tokens = {backend: encrypt_token(token) for backend, token in backend_tokens.items() if token is not None}

    # Ajouter des informations supplémentaires au payload du token
    payload = {
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "user_id": user_data.get("user_id"),
        "tokens": encrypted_tokens,  # Tokens des backends chiffrés
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
        "scope": "access_token"
    }

    # Retourner le payload structuré
    return payload

def encrypt_token(token: Optional[str]) -> Optional[str]:
    # Vérifier si le token est None
    if token is None:
        return None

    # Chiffrer le token
    return cipher_suite.encrypt(token.encode()).decode()
