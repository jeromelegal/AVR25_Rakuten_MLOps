from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.responses import JSONResponse
from jose import JWTError, jwt
from config.settings import Settings
from fastapi import FastAPI

PUBLIC_ENDPOINTS = {
    ("POST", "/api/internal/mongodb/entity/user"): True,
    ("POST", "/token"): True,
}

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request, call_next):
        if PUBLIC_ENDPOINTS.get((request.method, request.url.path)):
            return await call_next(request)

        if request.url.path.startswith(self.settings.INTERNAL_ENDPOINT_URL):
            referer = request.headers.get("Referer")
            if not referer or not referer.startswith(self.settings.API_GATEWAY_HOST):
                return JSONResponse(status_code=403, content={"detail": "Forbidden origin"})

            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return JSONResponse(status_code=401, content={"detail": "API key is missing"})

            try:
                payload = jwt.decode(api_key, self.settings.INTERNAL_SECRET_KEY, algorithms=[self.settings.ALGORITHM])
                if payload.get("scope") != "internal":
                    return JSONResponse(status_code=403, content={"detail": "Invalid scope"})
            except JWTError:
                return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

        response = await call_next(request)
        return response

def create_auth_middleware(settings: Settings) -> DispatchFunction:
    def middleware(app: FastAPI):
        return AuthMiddleware(app, settings)
    return middleware
