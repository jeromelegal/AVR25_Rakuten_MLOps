from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from api.middlewares.auth import create_auth_middleware
from api.middlewares.logging import LoggingMiddleware
from api.routes.user.login import router as login_router
from api.routes.user.signup import router as signup_router
from api.routes.user.delete import router as delete_router
from api.routes.ad.create import router as create_router
from api.routes.ad.delete import router as ad_delete_router
from api.routes.ad.read import router as read_router
from api.routes.ad.update import router as update_router
from api.routes.ad.search_mongodb import router as search_router
from api.routes.category.get import router as categories_router
from api.routes.category.get_category_from_image_id import router as cat_image_id_router
from api.routes.image.get import router as get_image_router
from api.routes.image.save import router as save_image_router
from api.routes.replicate.ads_to_mongo import router as replicate_router
from config.settings import Settings
import logging
from fastapi.responses import JSONResponse
from requests import HTTPError

# Configurer le logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("gateway")

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
    app.include_router(create_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["ad_create"])
    app.include_router(ad_delete_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["ad_delete_router"])
    app.include_router(read_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["ad_read"])
    app.include_router(update_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["ad_update"])
    app.include_router(categories_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["categories"])
    app.include_router(cat_image_id_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["cat_image_id"])
    app.include_router(get_image_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["get_image"])
    app.include_router(save_image_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["save_image"])
    app.include_router(search_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["search"])
    app.include_router(replicate_router, prefix=settings.PROTECTED_ENDPOINT_URL, tags=["replicate"])

    # Route racine
    @app.get("/")
    async def root():
        return {"message": "Hello World"}

    return app

# Créer une instance de l'application avec les paramètres
settings = Settings()
app = create_app(settings)
