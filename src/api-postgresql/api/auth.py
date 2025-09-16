from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta, UTC
from config.db import get_db_client
from typing import Optional
import hashlib
from config.settings import Settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    # Convertir la chaîne de caractères du mot de passe en bytes
    password_bytes = password.encode('utf-8')
    # Créer un objet de hachage SHA-256
    hash_object = hashlib.sha256(password_bytes)
    # Retourner le digest hexadécimal du hachage
    hash_val = hash_object.hexdigest()
    return hash_val

class Token(BaseModel):
    user_id: str
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

async def get_user(db, username: str):
    user = await db.fetchrow("SELECT * FROM users WHERE username = $1", username)
    if user:
        # Assurez-vous que tous les champs attendus sont présents dans le retour
        return dict(user)

async def authenticate_user(db, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not hash_password(password) == user["password"]:
        return False
    return user

def create_access_token(data: dict, settings: Settings, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.INTERNAL_SECRET_KEY, algorithm=settings.ALGORITHM)
    create_access_token
    return encoded_jwt

def create_internal_api_access_token(data: dict, settings: Settings, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.INTERNAL_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    settings: Settings = request.app.state.settings
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.INTERNAL_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    async with get_db_client(settings) as db:
        user = await get_user(db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    settings: Settings = request.app.state.settings
    async with get_db_client(settings) as db:
        user = await authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        data = {"user_id": user["id"], "sub": user["username"], 'scope': 'internal'}
        access_token = create_access_token(
            data=data, settings=settings, expires_delta=access_token_expires
        )
        return {"user_id": f"{user["id"]}", "access_token": access_token, "token_type": "bearer"}
