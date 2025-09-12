from fastapi import FastAPI
from api import main, auth
from api.mongodb.entity import user, space, role, document, page, widget, ad, directory, index, pipeline, datasource, api, stage
from api.mongodb.entity import category
from api.mongodb.relation import roles_users, role_document, role_space, role_page, role_widget, role_directory, role_index, role_pipeline, role_datasource, role_api, role_stage
from api.mongodb.relation import space_page, space_directory, space_index, space_datasource, space_pipeline, space_api
from api.mongodb.relation import directory_directory, directory_document
from api.mongodb.relation import pipeline_document, pipeline_stage, pipeline_index
from api.mongodb.relation import stage_api
from api.mongodb.relation import page_widget
from api.mongodb.relation import widget_datasource
from api.mongodb.relation import datasource_index
from api.mongodb.relation import ad_category

from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from config.config import API_GATEWAY_HOST, INTERNAL_SECRET_KEY, ALGORITHM, PROTECTED_ENDPOINT_URL, INTERNAL_ENDPOINT_URL

from api.auth import create_internal_api_access_token

from jose import JWTError, jwt


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("internal_access_middleware")

# Chemins d'endpoints qui ne nécessitent pas de token
PUBLIC_ENDPOINTS = {
    ("POST", "/api/internal/mongodb/entity/user"): True,
    ("POST", "/token"): True,
}
class InternalAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):

        # Vérifier si l'endpoint est public
        if PUBLIC_ENDPOINTS.get((request.method, request.url.path)):
            return await call_next(request)

        # Vérifier si l'endpoint est interne
        if request.url.path.startswith(INTERNAL_ENDPOINT_URL):
            referer = request.headers.get("Referer")
            if not referer or not referer.startswith(API_GATEWAY_HOST) :
                return JSONResponse(status_code=403, content={"detail": "Forbidden origin"})

            api_key = request.headers.get("X-API-Key")
            if not api_key:
                return JSONResponse(status_code=401, content={"detail": "API key is missing"})

            try:
                payload = jwt.decode(api_key, INTERNAL_SECRET_KEY, algorithms=[ALGORITHM])
                if payload.get("scope") != "internal":
                    return JSONResponse(status_code=403, content={"detail": "Invalid scope"})
            except JWTError:
                return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

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
app.include_router(auth.router)
app.include_router(ad.router)
app.include_router(category.router)
app.include_router(user.router)
app.include_router(space.router)
app.include_router(role.router)
app.include_router(document.router)
app.include_router(page.router)
app.include_router(widget.router)
app.include_router(directory.router)
app.include_router(index.router)
app.include_router(pipeline.router)
app.include_router(datasource.router)
app.include_router(api.router)
app.include_router(stage.router)

app.include_router(roles_users.router)
app.include_router(role_document.router)
app.include_router(role_space.router)
app.include_router(role_page.router)
app.include_router(role_widget.router)
app.include_router(role_directory.router)
app.include_router(role_index.router)
app.include_router(role_pipeline.router)
app.include_router(role_datasource.router)
app.include_router(role_api.router)
app.include_router(role_stage.router)

app.include_router(space_page.router)
app.include_router(space_directory.router)
app.include_router(space_index.router)
app.include_router(space_pipeline.router)
app.include_router(space_datasource.router)
app.include_router(space_api.router)

app.include_router(directory_directory.router)
app.include_router(directory_document.router)

app.include_router(pipeline_document.router)
app.include_router(pipeline_stage.router)
app.include_router(pipeline_index.router)

app.include_router(stage_api.router)

app.include_router(page_widget.router)

app.include_router(widget_datasource.router)

app.include_router(datasource_index.router)

app.include_router(ad_category.router)