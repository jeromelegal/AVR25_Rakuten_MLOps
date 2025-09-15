from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.requests import Request
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("log_middleware")

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Outgoing response: {response.status_code}")
        return response

def create_log_middleware() -> DispatchFunction:
    def middleware(app):
        return LogMiddleware(app)
    return middleware
