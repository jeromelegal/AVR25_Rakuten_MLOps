from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middlewares.auth import create_auth_middleware
from api.middlewares.logging import LoggingMiddleware
from api.routes.user.login import router as login_router
from api.routes.user.signup import router as signup_router
from api.routes.user.delete import router as delete_router
from api.routes.ad.create import router as create_router
from config.settings import Settings
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(settings: Settings):
    app = FastAPI()

    # Stocker les paramètres dans l'état de l'application pour un accès facile
    app.state.settings = settings

    # Ajouter le middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Autoriser toutes les origines (à ajuster en production)
        allow_credentials=True,
        allow_methods=["*"],  # Autoriser toutes les méthodes
        allow_headers=["*"],  # Autoriser tous les en-têtes
    )

    # Ajouter les middlewares personnalisés
    app.add_middleware(LoggingMiddleware)
    auth_middleware = create_auth_middleware(settings)
    app.add_middleware(auth_middleware)

    # Inclure les routeurs avec le préfixe protégé
    app.include_router(login_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["login"])
    app.include_router(signup_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["signup"])
    app.include_router(delete_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["delete"])
    app.include_router(create_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["create"])

    # Route racine
    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app

# Créer une instance de l'application avec les paramètres
settings = Settings()
app = create_app(settings)
