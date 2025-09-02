from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging

# Configurer le logger
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Enregistrer les détails de la requête
        logger.info(f"Request: {request.method} {request.url}")

        # Appeler le prochain middleware ou route
        response = await call_next(request)

        # Enregistrer les détails de la réponse
        logger.info(f"Response: {response.status_code}")

        return response
