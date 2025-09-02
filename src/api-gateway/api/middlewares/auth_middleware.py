from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from api.config.settings import settings

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Liste des endpoints publics qui ne nécessitent pas d'authentification
        # public_endpoints = ["/auth/login", "/signup"]

        # # Vérifier si l'endpoint est public
        # if request.url.path in public_endpoints:
        #     return await call_next(request)

        # # Vérifier la présence du token d'accès pour les endpoints privés
        # auth_header = request.headers.get("Authorization")
        # if not auth_header or not auth_header.startswith("Bearer "):
        #     raise HTTPException(status_code=401, detail="Missing or invalid token")

        # token = auth_header.split("Bearer ")[1]

        # try:
        #     # Vérifier le token
        #     payload = jwt.decode(token, settings.INTERNAL_SECRET_KEY, algorithms=[settings.ALGORITHM])
        #     request.state.user = payload
        # except JWTError:
        #     raise HTTPException(status_code=401, detail="Invalid token")

        response = await call_next(request)
        return response
