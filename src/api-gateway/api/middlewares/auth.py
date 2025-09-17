import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from config.settings import Settings

# Configurer le logger pour ce module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)  # Configurez le niveau de logging approprié

PUBLIC_ENDPOINTS = {
    ("POST", "/signup"): True,
    ("POST", "/login"): True,
}

def create_auth_middleware(settings: Settings) -> DispatchFunction:
    class AuthMiddleware(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)
            self.settings = settings

        async def dispatch(self, request: Request, call_next):
            # Log le début de la requête
            logger.debug(f"Request: {request.method} {request.url.path}")

            # Vérifier si l'URL de la requête est un endpoint public
            if PUBLIC_ENDPOINTS.get((request.method, request.url.path)):
                logger.debug("Public endpoint accessed")
                return await call_next(request)

            # Vérifier si l'URL de la requête commence par un endpoint protégé
            if request.url.path.startswith(self.settings.INTERNAL_ENDPOINT_URL):
                logger.debug("Protected endpoint accessed")

                referer = request.headers.get("Referer")
                logger.debug(f"Referer header: {referer}")

                if not referer or not referer.startswith(self.settings.API_GATEWAY_HOST):
                    logger.warning("Forbidden origin detected")
                    return JSONResponse(status_code=403, content={"detail": "Forbidden origin"})

                api_key = request.headers.get("X-API-Key")
                if not api_key:
                    logger.warning("API key is missing")
                    return JSONResponse(status_code=401, content={"detail": "API key is missing"})

                try:
                    payload = jwt.decode(api_key, self.settings.INTERNAL_SECRET_KEY, algorithms=[self.settings.ALGORITHM])
                    logger.debug(f"Decoded payload: {payload}")

                    if payload.get("scope") != "internal":
                        logger.warning("Invalid scope detected")
                        return JSONResponse(status_code=403, content={"detail": "Invalid scope"})
                except JWTError as e:
                    logger.error(f"Invalid API key: {e}")
                    return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

            response = await call_next(request)
            logger.debug(f"Response: {response}")
            logger.debug(f"Response status: {response.status_code}")
            return response

    return AuthMiddleware
