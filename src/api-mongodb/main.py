from fastapi import FastAPI
from api import hello as hello_router, auth as auth_router
from api.mongodb.entity import user, ad, category
from api.mongodb.relation import ad_category
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction
from starlette.responses import JSONResponse
import logging
from jose import JWTError, jwt
from config.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("internal_access_middleware")

PUBLIC_ENDPOINTS = {
    ("POST", "/api/internal/mongodb/entity/user"): True,
    ("POST", "/token"): True,
}

def create_middleware(settings: Settings):
    class InternalAccessMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, settings: Settings):
            super().__init__(app)
            self.settings = settings

        async def dispatch(self, request, call_next):
            # Vérifiez si la requête correspond à un point de terminaison public
            if PUBLIC_ENDPOINTS.get((request.method, request.url.path)):
                return await call_next(request)

            # Vérifiez si la requête commence par un point de terminaison interne
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

    # Retourne une fonction qui prend une application et retourne une instance du middleware
    def middleware(app: FastAPI) -> DispatchFunction:
        return InternalAccessMiddleware(app, settings)

    return middleware

def create_app(settings: Settings):
    app = FastAPI()
    app.state.settings = settings

    # Ajoutez le middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Ajoutez votre middleware personnalisé
    middleware = create_middleware(settings)
    app.add_middleware(middleware)

    # Inclure les routeurs
    app.include_router(hello_router.router)
    app.include_router(auth_router.router)
    app.include_router(ad.router)
    app.include_router(category.router)
    app.include_router(user.router)
    app.include_router(ad_category.router)

    return app

settings = Settings()
app = create_app(settings)
