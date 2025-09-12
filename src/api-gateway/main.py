from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.middlewares.auth_middleware import AuthMiddleware
from api.middlewares.logging_middleware import LoggingMiddleware
from api.routes.login import router as login_router
from api.routes.signup import router as signup_router
from api.routes.delete import router as delete_router
from api.config.settings import settings
import logging

# Configurer le logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Ajouter le middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autoriser toutes les origines (à ajuster en production)
    allow_credentials=True,
    allow_methods=["*"],  # Autoriser toutes les méthodes
    allow_headers=["*"],  # Autoriser tous les en-têtes
)

# Ajouter le middleware de journalisation
app.add_middleware(LoggingMiddleware)

# Ajouter le middleware d'authentification personnalisé
app.add_middleware(AuthMiddleware)

# Inclure les routeurs avec le préfixe protégé
app.include_router(login_router, prefix=settings.API_GATEWAY_PROTECTED_ENDPOINT_URL, tags=["login"])
app.include_router(signup_router, prefix=settings.API_GATEWAY_PROTECTED_ENDPOINT_URL, tags=["signup"])
app.include_router(delete_router, prefix=settings.API_GATEWAY_PROTECTED_ENDPOINT_URL, tags=["delete"])

@app.get("/")
async def root():
    return {"message": "Hello World"}
