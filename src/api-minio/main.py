from fastapi import FastAPI
from api import main
from api.minio.entity import images, buckets
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from api.config.config import settings

from jose import JWTError, jwt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("internal_access_minio")


class InternalAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # TODO : Finaliser la partie SECURE ou supprimer la partie commentée.
        # Vérifier si l'endpoint est interne
        # if request.url.path.startswith(settings.INTERNAL_ENDPOINT_URL):
        #     referer = request.headers.get("Referer")
        #     if not referer or not referer.startswith(settings.API_GATEWAY_HOST):
        #         return JSONResponse(
        #             status_code=403, content={"detail": "Forbidden origin"}
        #         )

        #     api_key = request.headers.get("X-API-Key")
        #     if not api_key:
        #         return JSONResponse(
        #             status_code=401, content={"detail": "API key is missing"}
        #         )

        #     try:
        #         payload = jwt.decode(
        #             api_key,
        #             settings.INTERNAL_SECRET_KEY,
        #             algorithms=[settings.ALGORITHM],
        #         )
        #         if payload.get("scope") != "internal":
        #             return JSONResponse(
        #                 status_code=403, content={"detail": "Invalid scope"}
        #             )
        #     except JWTError:
        #         return JSONResponse(
        #             status_code=401,
        #             content={
        #                 "detail": "Invalid API key",
        #             },
        #         )

        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(InternalAccessMiddleware)
app.add_middleware(LoggingMiddleware)

app.include_router(main.router)
app.include_router(images.router)
app.include_router(buckets.router)
