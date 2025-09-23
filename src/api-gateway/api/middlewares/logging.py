import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from datetime import datetime, UTC

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Configurer le logger
        logger = logging.getLogger("api_logger")
        logger.setLevel(logging.INFO)

        # Créer un format et un handler pour les logs
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Log des détails de la requête
        content_type = request.headers.get("content-type", "")
        request_body = await request.body()
        logger.info(f"Request: {request.method} {request.url}")
        logger.info(f"Request Headers: {dict(request.headers)}")
        if "multipart/form-data" in content_type:
            logger.info(f"Request Body: <multipart; {len(request_body)} bytes; omitted>")
        else:
            if request_body:
                logger.info(f"Request Body: {request_body.decode('utf-8', errors='replace')}")

        start_time = datetime.now(UTC)

        # Appeler la prochaine fonction de middleware ou la route
        response = await call_next(request)

        # Calculer le temps de traitement de la requête
        process_time = (datetime.now(UTC) - start_time).total_seconds()

        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Process Time: {process_time:.4f} seconds")

        return response

def create_logging_middleware() -> DispatchFunction:
    """Crée et retourne une instance de LoggingMiddleware"""
    return LoggingMiddleware
