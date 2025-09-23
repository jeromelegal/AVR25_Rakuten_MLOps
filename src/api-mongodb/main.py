from fastapi import FastAPI
from api import hello as hello_router, auth as auth_router
from api.mongodb.entity import user, ad
from fastapi.middleware.cors import CORSMiddleware
from middleware.auth import create_auth_middleware
from middleware.logging import create_logging_middleware
from config.settings import Settings

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

    # Ajoutez les middlewares
    log_middleware = create_logging_middleware()
    auth_middleware = create_auth_middleware(settings)
    app.add_middleware(log_middleware)
    app.add_middleware(auth_middleware)

    # Inclure les routeurs
    app.include_router(hello_router.router)
    app.include_router(auth_router.router)
    app.include_router(ad.router)
    app.include_router(user.router)

    return app

settings = Settings()
app = create_app(settings)
