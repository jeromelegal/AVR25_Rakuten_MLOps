from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from api.auth.backend_authenticator import BackendAuthenticator
from api.auth.token_manager import create_meta_token, create_signed_encrypted_token
router = APIRouter()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authentifier l'utilisateur sur plusieurs API backend
    authenticator = BackendAuthenticator()
    credentials = {
        "username": form_data.username,
        "password": form_data.password,
        "grant_type": "password"
    }
    user_data, backend_tokens, backend_uid = authenticator.authenticate(credentials)

    # Vérifier si l'authentification a échoué
    if user_data is None or any(token is None for token in backend_tokens.values()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Créer un payload de méta-token
    meta_token_payload = create_meta_token(user_data, backend_uid, backend_tokens)

    # Créer un méta-token signé et chiffré
    meta_token = create_signed_encrypted_token(meta_token_payload)

    return {
        "username": form_data.username,
        "access_token": meta_token,
        "token_type": "bearer"
    }
